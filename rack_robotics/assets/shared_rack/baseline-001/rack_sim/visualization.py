"""RTX readback fallback for VNC environments that omit Vulkan viewport surfaces."""
import time,json
from pathlib import Path
import omni.ui as ui
from pxr import UsdGeom
from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport
from .scene import camera
from .camera_guard import protect_perspective

class Viewer:
    def __init__(self,stage,interaction,row_demo=None):
        self.stage=stage; self.interaction=interaction
        self.row_demo=row_demo; self.manual_port=0; self.setting_models=False
        self.last=0.; self.pending=None; self.frame=0
        self.auto=False; self.paused=False
        self.camera_recoveries=0; self.last_rejected_camera=None
        self.perspective_lock=ui.SimpleBoolModel(True)
        self.window=ui.Window('Dell rack controls',width=470,height=650 if row_demo else 520)
        self.window.position_x=1110; self.window.position_y=80
        with self.window.frame:
            with ui.VStack(spacing=5):
                self.status=ui.Label('Starting PhysX…',height=26)
                with ui.HStack(height=28):
                    for name in (('row','handoff','rear') if row_demo else ('front','rear','rear_detail','connector')):
                        ui.Button(name,clicked_fn=lambda n=name:camera(stage,n))
                    if row_demo: ui.Button('Latch close',clicked_fn=lambda:camera(stage,'latch',focus=interaction.mouth))
                with ui.HStack(height=28):
                    ui.Button('Run repeated cycle',clicked_fn=self.start_auto)
                    ui.Button('Manual control',clicked_fn=self.stop_auto)
                with ui.HStack(height=28):
                    import omni.timeline
                    timeline=omni.timeline.get_timeline_interface()
                    ui.Button('Pause physics',clicked_fn=timeline.pause)
                    ui.Button('Resume physics',clicked_fn=timeline.play)
                    ui.Button('Stop / reset',clicked_fn=timeline.stop)
                with ui.HStack(height=28):
                    ui.Button('Press clip',clicked_fn=lambda:interaction.release(True))
                    ui.Button('Release clip',clicked_fn=lambda:interaction.release(False))
                if row_demo:
                    ui.Label('Transfer cable to port (releases and moves physically)',height=24)
                    for row in range(2):
                        with ui.HStack(height=28):
                            for index in range(row*8,(row+1)*8):
                                ui.Button(f'{index+1:02d}',clicked_fn=lambda n=index:self.transfer(n))
                ui.Label('Hand target offsets from socket (mm)',height=24)
                self.models=[]
                for i,(name,start) in enumerate(zip(('X','Y — extract / insert','Z'),(0,50,0))):
                    with ui.HStack(height=24):
                        ui.Label(name,width=180)
                        model=ui.SimpleFloatModel(start)
                        ui.FloatDrag(model,min=-100,max=150,step=.1)
                        model.add_value_changed_fn(lambda _,i=i:self.move())
                        self.models.append(model)
                self.angles=[]
                for name in ('Pitch X','Roll Y','Yaw Z'):
                    with ui.HStack(height=24):
                        ui.Label(name+' (degrees)',width=180)
                        model=ui.SimpleFloatModel(0)
                        ui.FloatDrag(model,min=-180,max=180,step=.2)
                        model.add_value_changed_fn(lambda _:self.move())
                        self.angles.append(model)
                with ui.HStack(height=28):
                    ui.Button('Let go of plug',clicked_fn=lambda:interaction.set_grasp(False))
                    ui.Button('Grasp plug',clicked_fn=lambda:interaction.set_grasp(True))
                ui.Label('Spring-hinge clip + socket lip: contact-driven retention.',height=24)
                ui.Label('Live renders: http://127.0.0.1:18080/',height=24)
                with ui.HStack(height=24):
                    ui.CheckBox(self.perspective_lock,width=24)
                    ui.Label('Keep 3D perspective (prevent flat side views)')

    def start_auto(self):
        self.auto=True
        if self.row_demo: self.row_demo.start()
    def stop_auto(self):
        self.auto=False
        if self.row_demo: self.row_demo.stop()
    def transfer(self,index):
        self.auto=False; self.manual_port=index
        self.row_demo.start(False,index)
    def move(self):
        if not self.setting_models and len(self.models)==3:
            self.stop_auto()
            offset=[m.as_float*.001 for m in self.models]
            if self.row_demo:
                base=self.interaction.port_target(self.manual_port,0)
                offset=[a+b for a,b in zip(base,offset)]
            self.interaction.set_target(offset,
                [m.as_float for m in self.angles] if hasattr(self,'angles') and len(self.angles)==3 else (0,0,0))

    def update(self):
        rejected=protect_perspective(get_active_viewport(),self.perspective_lock.as_bool)
        if rejected is not None:
            self.camera_recoveries+=1; self.last_rejected_camera=rejected
            print('CAMERA_RECOVERED',rejected,'-> /OmniverseKit_Persp',flush=True)
        self.status.text=f'{self.interaction.state.upper()}   |   cycles: {self.interaction.cycles}   |   depth: {self.interaction.metrics.get("depth_m",0)*1000:.2f} mm'
        if self.row_demo:
            connected=self.interaction.connected_port
            self.status.text=f'Port {connected+1 if connected is not None else "--"} | {self.interaction.state} | {self.row_demo.phase} -> {self.row_demo.destination+1:02d} | clip {self.interaction.metrics.get("latch_angle_deg",0):.1f} deg'
            if self.row_demo.error: self.status.text=self.row_demo.error
            if self.row_demo.running:
                self.manual_port=self.row_demo.destination
                base=self.interaction.port_target(self.manual_port,0)
                self.setting_models=True
                for model,value,origin in zip(self.models,self.interaction.target,base): model.set_value((value-origin)*1000)
                self.setting_models=False
        now=time.monotonic()
        if now-self.last>.5:
            import omni.timeline
            timeline=omni.timeline.get_timeline_interface()
            active_camera=str(get_active_viewport().camera_path)
            matrix=UsdGeom.Xformable(self.stage.GetPrimAtPath(active_camera)).ComputeLocalToWorldTransform(0)
            Path('/workspace/artifacts/live-state.json').write_text(json.dumps({
                'state':self.interaction.state,'cycles':self.interaction.cycles,
                'time':self.interaction.time,'auto':self.auto,
                'port_count':len(self.interaction.ports),
                'connected_port':self.interaction.connected_port+1 if self.interaction.connected_port is not None else None,
                'visited_ports':[i+1 for i in sorted(self.interaction.visited_ports)],
                'transfer':{'phase':self.row_demo.phase,'destination':self.row_demo.destination+1,
                            'running':self.row_demo.running,'error':self.row_demo.error} if self.row_demo else None,
                'playing':timeline.is_playing(),'stopped':timeline.is_stopped(),
                'active_camera':active_camera,
                'perspective_lock':self.perspective_lock.as_bool,
                'camera_recoveries':self.camera_recoveries,
                'last_rejected_camera':self.last_rejected_camera,
                'camera_transform':[v for row in matrix for v in row],
                'metrics':self.interaction.metrics}))
            # Alternate filenames to force UI texture reload without stale texture caching.
            file=f'/workspace/artifacts/live-{self.frame%2}.png'
            self.pending=capture_viewport_to_file(get_active_viewport(),file)
            previous=f'/workspace/artifacts/live-{(self.frame+1)%2}.png'
            if Path(previous).exists():
                # Copy the completed previous render for HTTP clients.
                import shutil
                shutil.copyfile(previous,'/workspace/artifacts/live.png')
            self.frame+=1; self.last=now
