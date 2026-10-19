"""Run with /isaac-sim/python.sh demo.py --allow-root [--validate] [--headless]."""
import argparse,json,sys,time,subprocess
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('--headless',action='store_true')
parser.add_argument('--validate',action='store_true')
parser.add_argument('--cycles',type=int,default=3)
parser.add_argument('--auto',action='store_true',help='Start the GUI repeated-cycle demonstration')
parser.add_argument('--keep-open',action='store_true',help='Keep the GUI running after successful validation')
parser.add_argument('--port-row',action='store_true',help='16 functional RJ45 ports and port-to-port transfers')
args,_=parser.parse_known_args()
if args.keep_open and args.headless: parser.error('--keep-open requires the GUI')
from isaacsim import SimulationApp
app=SimulationApp({'headless':args.headless,'width':1280,'height':800,
                   'window_width':1600,'window_height':1000,'multi_gpu':False,
                   'renderer':'RaytracedLighting','anti_aliasing':3})
import omni.usd
from pxr import Usd,UsdGeom,UsdPhysics,Gf,Sdf
from isaacsim.core.api import World
from rack_sim.config import CFG
from rack_sim.scene import build,camera
from rack_sim.visualization import Viewer
from rack_sim.row_demo import RowDemo,validate_row
from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport

out=Path('/workspace/artifacts')/('latch-row' if args.port_row else 'latch-single'); out.mkdir(exist_ok=True)
stage=omni.usd.get_context().get_stage()
interaction,cable=build(stage,port_row=args.port_row)
world=World(physics_dt=CFG.physics_dt,rendering_dt=1/60,stage_units_in_meters=1,
            physics_prim_path='/World/Physics')
camera(stage,'handoff' if args.port_row and args.validate else 'row' if args.port_row else 'connector')
asset_dir=Path('/workspace/assets')/('latch-row' if args.port_row else 'latch-single'); asset_dir.mkdir(exist_ok=True)
stage.GetRootLayer().Export(str(asset_dir/'dell_rack.usda'))
# Standalone inspectable component snapshots, including their material definitions.
for name,prim_path in [('rack','/World/Rack'),('servers','/World/Servers'),
                       ('rj45_socket','/World/PortRow' if args.port_row else '/World/Socket'),('rj45_plug','/World/Plug'),('cable','/World/Cable')]:
    component=Usd.Stage.CreateNew(str(asset_dir/f'{name}.usda'))
    component.DefinePrim('/World','Xform'); component.SetDefaultPrim(component.GetPrimAtPath('/World'))
    UsdGeom.SetStageMetersPerUnit(component,1); UsdGeom.SetStageUpAxis(component,'Z')
    extras=('/World/Latch','/World/LatchHinge','/World/ClipPress','/World/ClipPressSlide') if name=='rj45_plug' else ()
    for path in ('/World/Materials',prim_path,*extras):
        Sdf.CopySpec(stage.GetRootLayer(),path,component.GetRootLayer(),path)
    component.GetRootLayer().Save()
world.reset()
row_demo=RowDemo(interaction) if args.port_row else None
viewer=None if args.headless else Viewer(stage,interaction,row_demo)
if viewer: viewer.auto=args.auto
frame=0
recording=False
record_index=0
record_dir=out/('frames-'+time.strftime('%Y%m%d-%H%M%S'))

def record(enabled):
    global recording
    recording=enabled
    if enabled: record_dir.mkdir(exist_ok=True)

def step(n=1):
    global frame,record_index
    for _ in range(n):
        # Exactly one physics tick. world.step(render=True) can advance multiple
        # physics ticks when rendering_dt differs, which would skew dwell/video time.
        world.step(render=False)
        if frame%4==0: world.render()
        if world.is_playing(): interaction.update(CFG.physics_dt)
        if frame%4==0:
            cable.update()
            if viewer: viewer.update()
        if recording and frame%8==0:
            capture_viewport_to_file(get_active_viewport(),str(record_dir/f'{record_index:05d}.png'))
            record_index+=1
        frame+=1

def move(offset,seconds=1.,angles=(0,0,0)):
    start=list(interaction.target)
    n=int(seconds/CFG.physics_dt)
    for i in range(n):
        a=(i+1)/n; a=a*a*(3-2*a)
        interaction.set_target([s+(t-s)*a for s,t in zip(start,offset)],angles)
        step()

def capture(name):
    task=capture_viewport_to_file(get_active_viewport(),str(out/(name+'.png')))
    step(16)

try:
    step(240)
    print('DELL_RACK_READY',flush=True)
    if args.validate:
        from rack_sim.validation import validate
        report=(validate_row(interaction,cable,move,step,capture,record) if args.port_row else
                validate(interaction,cable,move,step,capture,args.cycles,record))
        report['run_source']=str(Path(__file__).parent)
        report['scene_file']=str(asset_dir/'dell_rack.usda')
        (out/'validation.json').write_text(json.dumps(report,indent=2))
        get_active_viewport().set_texture_resolution((1920,1200))
        for name in (('rear','row','handoff') if args.port_row else ('front','rear','rear_detail','connector')):
            camera(stage,name); step(100); capture(name)
        if record_index:
            subprocess.run(['ffmpeg','-y','-framerate','30','-i',str(record_dir/'%05d.png'),
                            '-c:v','libx264','-pix_fmt','yuv420p','-crf','19','-movflags','+faststart',
                            str(out/'demo.mp4')],check=True)
        print('VALIDATION',json.dumps(report),flush=True)
        if not report['passed']: raise RuntimeError('Physical acceptance checks failed; see validation.json')
    if not args.validate or args.keep_open:
        if row_demo:
            camera(stage,'row')
            if args.auto: row_demo.start()
        auto_step=0
        stop_seen=False
        next_tick=time.monotonic()
        while app.is_running():
            if world.is_stopped(): stop_seen=True
            elif world.is_playing() and stop_seen:
                interaction.reset(); world.reset()
                auto_step=0; stop_seen=False
                if row_demo:
                    row_demo.stop()
                    if viewer.auto: row_demo.start()
            if row_demo and world.is_playing(): row_demo.tick(CFG.physics_dt)
            if not row_demo and viewer.auto and world.is_playing():
                t=(auto_step%2880)/240
                if t<2: interaction.release(False); interaction.set_target((0,.05-(.0498*t/2),0))
                elif t<4: interaction.set_target((0,.0002,0))
                elif t<6: interaction.set_target((0,.035,0))
                elif t<7: interaction.set_target((0,.0002,0))
                elif t<9: interaction.release(True); interaction.set_target((0,.0002+.0498*(t-7)/2,0))
                else: interaction.set_target((0,.05,0)); interaction.release(False)
                auto_step+=1
            step()
            # Pace the interactive demonstration at real time when hardware can
            # keep up; validation remains unrestricted for reproducibility.
            next_tick+=CFG.physics_dt
            delay=next_tick-time.monotonic()
            if delay>0: time.sleep(delay)
            elif delay<-.1: next_tick=time.monotonic()
except Exception:
    import traceback
    traceback.print_exc()
    app.close()
    raise
app.close()
