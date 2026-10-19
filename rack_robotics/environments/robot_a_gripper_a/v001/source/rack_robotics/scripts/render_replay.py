"""Render recorded PHYSICS observations; never run a task using replay poses.

Input is an experiment's scene.usda + measured trajectory.jsonl. Physics stays
stopped. The output is explicitly marked as replay in its manifest and video.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument('--attempt',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--view',choices=['wide','rear','macro','side'],default='macro')
parser.add_argument('--max-frames',type=int,default=0,help='Diagnostic subset only; 0 renders the whole recording')
args,_=parser.parse_known_args()
args.attempt=args.attempt.resolve(); args.output=args.output.resolve()
args.output.mkdir(parents=True,exist_ok=False)
frames=args.output/'frames'; frames.mkdir()
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'rack_robotics/assets/shared_rack/baseline-001'))
with (args.attempt/'trajectory.jsonl').open() as source:
    header=json.loads(next(source)); samples=[json.loads(line) for line in source]
assert header['format']=='measured_world_poses_v1'
if args.max_frames: samples=samples[:args.max_frames]
report=json.loads((args.attempt/'results.json').read_text())

from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':1920,'height':1080,
                   'renderer':'RaytracedLighting','anti_aliasing':3})
try:
    import omni.usd
    import omni.timeline
    from pxr import Gf, UsdGeom, UsdPhysics
    from isaacsim.core.utils.viewports import set_camera_view,set_active_viewport_camera
    from isaacsim.core.simulation_manager import SimulationManager
    from isaacsim.core.experimental.utils.stage import get_stage_id
    from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport
    from rack_sim.config import ROW_PORTS
    from rack_sim.cable import Cable
    from rack_sim.config import CFG
    assert omni.usd.get_context().open_stage(str(args.attempt/'scene.usda'))
    for _ in range(30): app.update()
    while omni.usd.get_context().get_stage_loading_status()[2]>0: app.update()
    stage=omni.usd.get_context().get_stage()
    omni.timeline.get_timeline_interface().stop()
    SimulationManager.enable_usd_notice_handler(True)
    SimulationManager.enable_fabric_usd_notice_handler(get_stage_id(stage),True)
    for path in ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress'):
        stage.GetPrimAtPath(path).SetActive(False)
    operations={}
    for path in header['body_paths']:
        prim=stage.GetPrimAtPath(path)
        # Replay is a separate non-simulating visualization, never trial input.
        UsdPhysics.RigidBodyAPI(prim).GetRigidBodyEnabledAttr().Set(False)
        xf=UsdGeom.Xformable(prim)
        translate=prim.GetAttribute('xformOp:translate')
        orient=prim.GetAttribute('xformOp:orient')
        t=UsdGeom.XformOp(translate) if translate else xf.AddTranslateOp()
        q=UsdGeom.XformOp(orient) if orient else xf.AddOrientOp()
        xf.SetXformOpOrder([t,q])
        operations[path]=(t,q)
    cable=Cable(stage,[f'/World/Cable/Link{i:02d}' for i in range(CFG.cable_segments)],
                UsdGeom.BasisCurves(stage.GetPrimAtPath('/World/Cable/Jacket')))
    focus=ROW_PORTS[0]
    views={'wide':((1.2,3.4,2.1),(0,.3,1.25)),
           'rear':((.50,1.25,1.98),(0,.55,1.68)),
           'macro':((focus[0]+.045,focus[1]+.16,focus[2]+.06),focus),
           'side':((.9,1.15,1.95),(0,.65,1.55))}
    set_active_viewport_camera('/OmniverseKit_Persp')
    set_camera_view(eye=list(views[args.view][0]),target=list(views[args.view][1]))
    UsdGeom.Camera(stage.GetPrimAtPath('/OmniverseKit_Persp')).GetClippingRangeAttr().Set(Gf.Vec2f(.001,1000))
    for _ in range(60): app.update()
    for index,sample in enumerate(samples):
        assert not omni.timeline.get_timeline_interface().is_playing()
        for path,values in zip(header['body_paths'],sample['poses']):
            p=Gf.Vec3d(*values[:3]); q=Gf.Quatd(values[3],Gf.Vec3d(*values[4:]))
            matrix=Gf.Matrix4d(1); matrix.SetRotate(Gf.Rotation(q)); matrix.SetTranslateOnly(p)
            parent=stage.GetPrimAtPath(path).GetParent()
            parent_world=UsdGeom.Xformable(parent).ComputeLocalToWorldTransform(0)
            local=matrix*parent_world.GetInverse()
            translate,orient=operations[path]
            translate.Set(local.ExtractTranslation())
            local_q=local.ExtractRotationQuat()
            orient.Set(Gf.Quatf(local_q) if orient.GetPrecision()==UsdGeom.XformOp.PrecisionFloat else local_q)
            actual=UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(0)
            assert (actual.ExtractTranslation()-p).GetLength()<1e-6,path
        cable.update()
        for _ in range(3): app.update()
        target=frames/f'{index:05d}.png'
        capture=capture_viewport_to_file(get_active_viewport(),str(target))
        started=time.monotonic()
        while not target.exists():
            app.update()
            if time.monotonic()-started>60: raise TimeoutError(f'RTX capture timed out at {index}')
        if index%30==0: print('REPLAY_FRAME',index,len(samples),flush=True)
        if index==0: stage.GetRootLayer().Export(str(args.output/'first_frame_debug.usda'))
    label=('PASS' if report['passed'] else 'FAILED')+' PHYSICS TRIAL - RECORDED REPLAY'
    subprocess.run(['ffmpeg','-nostdin','-y','-framerate','30','-i',str(frames/'%05d.png'),
        '-vf',f"drawtext=text='{label}':fontcolor=white:fontsize=24:x=20:y=20:box=1:boxcolor=black@0.6",
        '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(args.output/'demo.mp4')],check=True)
    (args.output/'manifest.json').write_text(json.dumps({'source_attempt':str(args.attempt),
        'source_passed':report['passed'],'replay_only':True,'physics_running':False,
        'view':args.view,'frames':len(samples),'fps':30,'resolution':[1920,1080],
        'full_trajectory':not args.max_frames,'camera':views[args.view]},indent=2)+'\n')
finally:
    app.close()
