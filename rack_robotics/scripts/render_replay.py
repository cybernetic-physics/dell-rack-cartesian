"""Render recorded PHYSICS observations; never run a task using replay poses.

Input is an experiment's scene.usda + measured trajectory.jsonl. Physics stays
stopped. The output is explicitly marked as replay in its manifest and video.
"""
import argparse
import hashlib
import math
import json
from pathlib import Path
import subprocess
import shutil
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument('--attempt',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--baseline',type=Path,help='Explicit immutable rack code for a separately frozen renderer source tree')
parser.add_argument('--view',choices=['wide','rear','macro','side','tool'],default='macro')
parser.add_argument('--max-frames',type=int,default=0,help='Diagnostic subset only; 0 renders the whole recording')
parser.add_argument('--start-frame',type=int,default=0,help='Diagnostic subset offset')
parser.add_argument('--initialization',action='store_true',help='Diagnostic startup recording, NOT the autonomous task cycle')
parser.add_argument('--macro-fill-intensity',type=float,default=0.,help='Optional 60 mm camera-side inspection fill; render-only, macro view only')
parser.add_argument('--view-fill-intensity',type=float,default=0.,help='Optional 250 mm camera-side soft fill; render-only, non-macro views')
parser.add_argument('--renderer',choices=['RealTimePathTracing','RaytracedLighting','PathTracing'],default='RealTimePathTracing')
parser.add_argument('--width',type=int,default=1920)
parser.add_argument('--height',type=int,default=1080)
parser.add_argument('--gpu',type=int,default=0,help='Renderer GPU index; explicit installed SimulationApp active_gpu setting')
parser.add_argument('--samples-per-pixel',type=int,default=64)
parser.add_argument('--no-denoiser',action='store_true',help='Use more samples when optional OptiX denoiser weights are unavailable')
parser.add_argument('--isolated-product',action='store_true',help='Diagnostic clean render product without inherited UI settings')
parser.add_argument('--capture-backend',choices=['viewport','replicator'],default='replicator')
parser.add_argument('--render-subframes',type=int,default=8)
parser.add_argument('--anti-aliasing',choices=['none','taa','fxaa','dlss','rtxaa'],help='Explicit supported RTX AA token; fxaa avoids DLSS/TAA frame history')
parser.add_argument('--reset-render-history',action='store_true',help='Reset RTX temporal accumulation immediately before each recorded capture')
parser.add_argument('--eye',type=float,nargs=3,help='Static camera eye override (not tracked macro)')
parser.add_argument('--target',type=float,nargs=3,help='Static camera target override')
parser.add_argument('--macro-offset',type=float,nargs=3,default=(-.075,.09,.045))
parser.add_argument('--focal-length',type=float,help='Camera focal length in mm')
args,_=parser.parse_known_args()
if args.gpu<0:parser.error('GPU index must be nonnegative')
if not math.isfinite(args.macro_fill_intensity) or args.macro_fill_intensity < 0 or (args.macro_fill_intensity and args.view!='macro'):
    parser.error('Macro fill must be finite, nonnegative and used only with --view macro')
if not math.isfinite(args.view_fill_intensity) or args.view_fill_intensity < 0 or (args.view_fill_intensity and args.view=='macro'):
    parser.error('View fill must be finite, nonnegative and used only with non-macro views')
requested_renderer=args.renderer
if args.renderer=='RaytracedLighting': args.renderer='RealTimePathTracing'
if args.render_subframes<1: parser.error('Render subframes must be positive')
if args.width<640 or args.height<360 or args.width%2 or args.height%2 or args.samples_per_pixel<1:
    parser.error('Use positive even video dimensions >=640x360 and positive sample count')
if args.focal_length is not None and args.focal_length<=0: parser.error('Focal length must be positive')
if args.view=='macro' and (args.eye or args.target): parser.error('Tracked macro uses --macro-offset')
args.attempt=args.attempt.resolve(); args.output=args.output.resolve()
args.output.mkdir(parents=True,exist_ok=False)
shutil.copy2(__file__,args.output/'render_source.py')
frames=args.output/'frames'; frames.mkdir()
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
sys.path.insert(0,str((args.baseline or root/'rack_robotics/assets/shared_rack/baseline-001').resolve()))
from rack_robotics.replay_validation import validate_recording,rotation_error_rad,validate_capture_camera
from rack_robotics.frame_validation import check_frame
shutil.copy2(root/'rack_robotics/replay_validation.py',args.output/'validation_source.py')
shutil.copy2(root/'rack_robotics/macro_camera.py',args.output/'camera_source.py')
shutil.copy2(root/'rack_robotics/mechanical_screen.py',args.output/'camera_math_source.py')
shutil.copy2(root/'rack_robotics/render_profile.py',args.output/'profile_source.py')
shutil.copy2(root/'rack_robotics/frame_validation.py',args.output/'frame_validation_source.py')
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
trajectory_name='initialization_trajectory.jsonl' if args.initialization else 'trajectory.jsonl'
source_hashes={name:sha(args.attempt/name) for name in ('scene.usda','results.json',trajectory_name)}
with (args.attempt/trajectory_name).open() as source:
    header=json.loads(next(source)); samples=[json.loads(line) for line in source]
recording_validation=validate_recording(header,samples)
samples=samples[args.start_frame:]
if args.max_frames: samples=samples[:args.max_frames]
if not samples: raise ValueError('Requested frame range is empty')
report=json.loads((args.attempt/'results.json').read_text())

from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':args.width,'height':args.height,
                   'active_gpu':args.gpu,
                   'renderer':args.renderer,'samples_per_pixel_per_frame':args.samples_per_pixel,
                   'denoiser':not args.no_denoiser,'anti_aliasing':0 if args.renderer=='PathTracing' else 3})
try:
    import carb
    active_gpu_setting=carb.settings.get_settings().get('/renderer/activeGpu')
    if active_gpu_setting!=args.gpu:raise ValueError('Renderer did not retain requested active GPU')
    import omni.usd
    import omni.timeline
    from pxr import Gf, UsdGeom, UsdPhysics
    from isaacsim.core.utils.viewports import set_camera_view,set_active_viewport_camera
    from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport
    from rack_sim.config import ROW_PORTS
    from rack_robotics.replay import bake_replay
    from rack_robotics.render_profile import apply_profile,create_replay_product,verify_profile
    shutil.copy2(root/'rack_robotics/replay.py',args.output/'bake_source.py')
    replay_file=args.output/'replay.usda'
    port=report.get('condition',{}).get('port',1)
    focus=ROW_PORTS[port-1]
    views={'wide':((.95,3.9,2.0),(0,.35,1.05)),
           'rear':((.50,1.25,1.98),(0,.55,1.68)),
           'macro':((focus[0]-.075,focus[1]+.09,focus[2]+.045),focus),
           'side':((.9,1.15,1.95),(0,.65,1.55)),
           'tool':((.10,.49,1.94),(.15,.61,1.76))}
    if args.eye: views[args.view]=(tuple(args.eye),views[args.view][1])
    if args.target: views[args.view]=(views[args.view][0],tuple(args.target))
    bake_replay(args.attempt/'scene.usda',replay_file,header,samples,args.view,views,focus,
                args.macro_offset,args.focal_length,args.macro_fill_intensity,args.view_fill_intensity)
    assert omni.usd.get_context().open_stage(str(replay_file))
    for _ in range(30): app.update()
    while omni.usd.get_context().get_stage_loading_status()[2]>0: app.update()
    stage=omni.usd.get_context().get_stage()
    omni.timeline.get_timeline_interface().stop()
    set_active_viewport_camera('/World/ReplayCamera')
    app.reset_render_settings()
    viewport=get_active_viewport()
    if args.capture_backend=='replicator':
        import omni.replicator.core as rep
        rep.orchestrator.set_capture_on_play(False)
        product=rep.create.render_product('/World/ReplayCamera',(args.width,args.height),
            force_new=True,name='RecordedReplay',write_to_session_layer=False)
        product_path=product if isinstance(product,str) else product.path
        rgb=rep.AnnotatorRegistry.get_annotator('rgb')
        rgb.attach([product])
        camera_params=rep.AnnotatorRegistry.get_annotator('CameraParams')
        camera_params.attach([product])
    elif args.isolated_product:
        product_path=create_replay_product(stage,'/World/ReplayCamera',args.width,args.height)
        viewport.render_product_path=product_path
        viewport.camera_path='/World/ReplayCamera'
        assert str(viewport.render_product_path)==product_path
    else:
        product_path=viewport.render_product_path
    viewport.resolution=(args.width,args.height)
    render_profile=apply_profile(stage,product_path,args.renderer,args.samples_per_pixel,not args.no_denoiser,args.anti_aliasing)
    stage.GetRootLayer().Save()
    print('REPLAY_RENDER_PROFILE',json.dumps(render_profile),flush=True)
    for _ in range(60): app.update()
    verify_profile(stage,render_profile)
    largest_position_error=0.; largest_rotation_error=0.; minimum_visible_fraction=1.; largest_camera_error=0.
    for index,sample in enumerate(samples):
        assert not omni.timeline.get_timeline_interface().is_playing()
        omni.timeline.get_timeline_interface().set_current_time(index/30)
        for path,values in zip(header['body_paths'],sample['poses']):
            actual=UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(index)
            position_error=(actual.ExtractTranslation()-Gf.Vec3d(*values[:3])).GetLength()
            q=actual.ExtractRotationQuat()
            rotation_error=rotation_error_rad([q.GetReal(),*q.GetImaginary()],values[3:])
            largest_position_error=max(largest_position_error,position_error)
            largest_rotation_error=max(largest_rotation_error,rotation_error)
            assert position_error<1e-6,(path,position_error)
            assert rotation_error<1e-4,(path,rotation_error)
        for _ in range(3): app.update()
        target=frames/f'{index:05d}.png'
        if args.capture_backend=='replicator':
            from PIL import Image
            if args.reset_render_history:
                omni.usd.get_context().reset_renderer_accumulation()
            rep.orchestrator.step(rt_subframes=args.render_subframes,delta_time=0.,pause_timeline=True,wait_for_render=True)
            assert abs(omni.timeline.get_timeline_interface().get_current_time()-index/30)<1e-8
            assert not omni.timeline.get_timeline_interface().is_playing()
            data=rgb.get_data()
            if data.shape[:2]!=(args.height,args.width): raise ValueError(f'Invalid RGB shape: {data.shape}')
            params=camera_params.get_data()
            captured_view=Gf.Matrix4d(*params['cameraViewTransform'].reshape(-1).tolist())
            Image.fromarray(data[:,:,:3]).save(target)
        else:
            if args.reset_render_history:
                omni.usd.get_context().reset_renderer_accumulation()
            capture=capture_viewport_to_file(get_active_viewport(),str(target))
            started=time.monotonic()
            import asyncio
            completion=asyncio.ensure_future(capture.wait_for_result())
            while not completion.done():
                app.update()
                if time.monotonic()-started>60: raise TimeoutError(f'RTX capture did not finish at {index}')
            completion.result()
            captured_view=Gf.Matrix4d(capture.view)
        expected_view=UsdGeom.Xformable(stage.GetPrimAtPath('/World/ReplayCamera')).ComputeLocalToWorldTransform(index).GetInverse()
        camera_error=validate_capture_camera(captured_view,expected_view)
        largest_camera_error=max(largest_camera_error,camera_error)
        verify_profile(stage,render_profile)
        frame_check=check_frame(target)
        minimum_visible_fraction=min(minimum_visible_fraction,frame_check['visible_fraction_above_15'])
        if index%30==0: print('REPLAY_FRAME',index,len(samples),flush=True)
        if index==0: stage.GetRootLayer().Export(str(args.output/'first_frame_debug.usda'))
    label=('PASS' if report['passed'] else 'FAILED')+' PHYSICS TRIAL - RECORDED REPLAY'
    if args.initialization: label+=' - STARTUP ONLY'
    subprocess.run(['ffmpeg','-nostdin','-y','-framerate','30','-i',str(frames/'%05d.png'),
        '-vf',f"drawtext=text='{label}':fontcolor=white:fontsize=24:x=20:y=20:box=1:boxcolor=black@0.6",
        '-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(args.output/'demo.mp4')],check=True)
    if source_hashes!={name:sha(args.attempt/name) for name in source_hashes}:
        raise ValueError('Recorded evidence changed during rendering')
    (args.output/'manifest.json').write_text(json.dumps({'source_attempt':str(args.attempt),
        'source_sha256':source_hashes,'video_sha256':sha(args.output/'demo.mp4'),
        'render_sources_sha256':{name:sha(args.output/name) for name in ('render_source.py','bake_source.py','validation_source.py','camera_source.py','camera_math_source.py','profile_source.py','frame_validation_source.py')},
        'nonblank_frames':{'checked':len(samples),'minimum_visible_fraction_above_15':minimum_visible_fraction,
                           'scope':'Blank-frame rejection only; visual/temporal quality needs separate review'},
        'resolved_render_profile':render_profile,
        'isolated_render_product':args.isolated_product,
        'capture_backend':args.capture_backend,
        'render_subframes':args.render_subframes,
        'reset_renderer_accumulation_before_each_capture':args.reset_render_history,
        'capture_camera_validation':{'maximum_view_matrix_element_error':largest_camera_error,'checked':len(samples)},
        'recording_validation':recording_validation,
        'pose_replay_validation':{'maximum_translation_error_m':largest_position_error,
                                  'maximum_rotation_error_rad':largest_rotation_error,
                                  'body_sample_checks':len(samples)*len(header['body_paths'])},
        'source_passed':report['passed'],'replay_only':True,'physics_running':False,
        'view':args.view,'frames':len(samples),'fps':30,'resolution':[args.width,args.height],
        'renderer':args.renderer,'requested_renderer':requested_renderer,
        'requested_gpu_index':args.gpu,'active_gpu_setting':active_gpu_setting,
        'pathtracing_samples_per_pixel_setting':args.samples_per_pixel,
        'denoiser':not args.no_denoiser,'focal_length_override_mm':args.focal_length,
        'macro_camera_fill':{'intensity':args.macro_fill_intensity,'size_m':[.06,.06],
                             'render_only':True,'tracks_camera':bool(args.macro_fill_intensity)},
        'view_camera_fill':{'intensity':args.view_fill_intensity,'size_m':[.25,.25],
                            'render_only':True,'tracks_camera':bool(args.view_fill_intensity)},
        'full_trajectory':not args.initialization and not args.max_frames and not args.start_frame,
        'trajectory_file':trajectory_name,'initialization_only':args.initialization,
        'start_frame':args.start_frame,'camera':views[args.view],
        'macro_tracking':{'target':'Mean of measured plug center and socket mouth plus 3 mm Z',
                          'framing':'Adaptive camera distance fits socket/plug inspection envelopes in vertical FOV with 12% margin',
                          'eye_offset':args.macro_offset,'focal_length_mm':args.focal_length or 50} if args.view=='macro' else None},indent=2)+'\n')
except BaseException:
    # SimulationApp.close can terminate Kit before Python prints the exception.
    # Preserve failures before closing; a process exit alone is not render success.
    import traceback
    error=traceback.format_exc()
    print('REPLAY_FAILED',error,flush=True)
    (args.output/'failure.json').write_text(json.dumps({'passed':False,'error':error,
        'source_sha256':source_hashes,'view':args.view,'renderer':args.renderer,
        'start_frame':args.start_frame,'requested_frames':args.max_frames},indent=2)+'\n')
    raise
finally:
    app.close()
