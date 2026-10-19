"""Render recorded PHYSICS observations; never run a task using replay poses.

Input is an experiment's scene.usda + measured trajectory.jsonl. Physics stays
stopped. The output is explicitly marked as replay in its manifest and video.
"""
import argparse
import json
from pathlib import Path
import subprocess
import shutil
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument('--attempt',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--view',choices=['wide','rear','macro','side'],default='macro')
parser.add_argument('--max-frames',type=int,default=0,help='Diagnostic subset only; 0 renders the whole recording')
parser.add_argument('--start-frame',type=int,default=0,help='Diagnostic subset offset')
parser.add_argument('--initialization',action='store_true',help='Diagnostic startup recording, NOT the autonomous task cycle')
args,_=parser.parse_known_args()
args.attempt=args.attempt.resolve(); args.output=args.output.resolve()
args.output.mkdir(parents=True,exist_ok=False)
shutil.copy2(__file__,args.output/'render_source.py')
frames=args.output/'frames'; frames.mkdir()
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
sys.path.insert(0,str(root/'rack_robotics/assets/shared_rack/baseline-001'))
trajectory_name='initialization_trajectory.jsonl' if args.initialization else 'trajectory.jsonl'
with (args.attempt/trajectory_name).open() as source:
    header=json.loads(next(source)); samples=[json.loads(line) for line in source]
assert header['format']=='measured_world_poses_v1'
samples=samples[args.start_frame:]
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
    from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport
    from rack_sim.config import ROW_PORTS
    from rack_robotics.replay import bake_replay
    shutil.copy2(root/'rack_robotics/replay.py',args.output/'bake_source.py')
    replay_file=args.output/'replay.usda'
    focus=ROW_PORTS[0]
    views={'wide':((1.2,3.4,2.1),(0,.3,1.25)),
           'rear':((.50,1.25,1.98),(0,.55,1.68)),
           'macro':((focus[0]-.075,focus[1]+.09,focus[2]+.045),focus),
           'side':((.9,1.15,1.95),(0,.65,1.55))}
    bake_replay(args.attempt/'scene.usda',replay_file,header,samples,args.view,views,focus)
    assert omni.usd.get_context().open_stage(str(replay_file))
    for _ in range(30): app.update()
    while omni.usd.get_context().get_stage_loading_status()[2]>0: app.update()
    stage=omni.usd.get_context().get_stage()
    omni.timeline.get_timeline_interface().stop()
    set_active_viewport_camera('/World/ReplayCamera')
    for _ in range(60): app.update()
    for index,sample in enumerate(samples):
        assert not omni.timeline.get_timeline_interface().is_playing()
        omni.timeline.get_timeline_interface().set_current_time(index/30)
        for path,values in zip(header['body_paths'],sample['poses']):
            actual=UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(index)
            assert (actual.ExtractTranslation()-Gf.Vec3d(*values[:3])).GetLength()<1e-6,path
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
    if args.initialization: label+=' - STARTUP ONLY'
    subprocess.run(['ffmpeg','-nostdin','-y','-framerate','30','-i',str(frames/'%05d.png'),
        '-vf',f"drawtext=text='{label}':fontcolor=white:fontsize=24:x=20:y=20:box=1:boxcolor=black@0.6",
        '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(args.output/'demo.mp4')],check=True)
    (args.output/'manifest.json').write_text(json.dumps({'source_attempt':str(args.attempt),
        'source_passed':report['passed'],'replay_only':True,'physics_running':False,
        'view':args.view,'frames':len(samples),'fps':30,'resolution':[1920,1080],
        'full_trajectory':not args.initialization and not args.max_frames and not args.start_frame,
        'trajectory_file':trajectory_name,'initialization_only':args.initialization,
        'start_frame':args.start_frame,'camera':views[args.view],
        'macro_tracking':{'target':'Mean of measured plug center and socket mouth plus 3 mm Z',
                          'eye_offset':[-.075,.09,.045],'focal_length_mm':50} if args.view=='macro' else None},indent=2)+'\n')
finally:
    app.close()
