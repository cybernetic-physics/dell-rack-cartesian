"""Frozen-source, four-camera full-cycle render batch, followed by exact edits.

Output directories must be new. Failures remain in the batch; no timeout/retry.
This establishes captured artifacts, not automatic visual-quality acceptance.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import threading
import time


VIEWS=('wide','rear','macro','side')
CAMERAS={'wide':[], 'rear':['--eye','-.20','1.3','1.88','--target','.08','.5','1.69'],
         'macro':['--macro-offset','-.065','.04','.035','--focal-length','35'],
         'side':['--eye','-.8','1.2','1.95','--target','.05','.60','1.65']}
CAMERA_PROFILES={'legacy':CAMERAS,
    'open-frame-v1':{
        'wide':[],
        'rear':['--eye','-.25','1.6','1.93','--target','.02','.6','1.7','--focal-length','24'],
        'macro':['--macro-offset','-.085','.040','.015','--focal-length','35',
                 '--macro-fill-intensity','3000'],
        'side':['--eye','-.95','2.7','1.85','--target','0','.7','1.5','--focal-length','24']}}
CAMERA_PROFILES['latch-inspection-v2']={
    **CAMERA_PROFILES['open-frame-v1'],
    'rear':['--eye','-.08','.66','1.70','--target','.16','.45','1.67',
            '--focal-length','18','--view-fill-intensity','4000'],
    'macro':['--macro-offset','-.035','.018','.02','--focal-length','18',
             '--macro-fill-intensity','8000']}


def camera_arguments(view,profile,gpu):
    if view not in VIEWS or profile not in CAMERA_PROFILES:
        raise ValueError('Unknown camera view/profile')
    if not isinstance(gpu,int) or isinstance(gpu,bool) or gpu<0:
        raise ValueError('GPU index must be a nonnegative integer')
    return ['--gpu',str(gpu),*CAMERA_PROFILES[profile][view]]


def validate_attempt(result,label,failed_diagnostics=False):
    if (result.get('passed') is not (False if failed_diagnostics else True)
            or result.get('scope')!='full_rack'):
        raise ValueError('Expected '+('failed' if failed_diagnostics else 'successful')+' full-rack trajectory: '+label)
    if result['robot'][0]+result['gripper'][0]!=label:
        raise ValueError('Wrong design label')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def render_settings(width, height, subframes):
    if (any(type(v) is not int for v in (width,height,subframes))
            or width<1920 or height<1080 or width%2 or height%2
            or width*9!=height*16 or subframes<1):
        raise ValueError('Use even native16:9 dimensions >=1920x1080 and positive subframes')
    return ['--width',str(width),'--height',str(height),'--render-subframes',str(subframes)]


def select_attempts(entries):
    selected={}
    for entry in entries:
        label,separator,path=entry.partition('=')
        if not separator or not re.fullmatch('[A-C]{2}',label) or label in selected or not path:
            raise ValueError('Use distinct AA=ATTEMPT_DIRECTORY entries')
        selected[label]=Path(path).resolve()
    return selected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--attempt',action='append',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--workers',type=int,choices=(1,2),default=2)
    parser.add_argument('--isaac-python',default='/isaac-sim/python.sh')
    parser.add_argument('--gpu',type=int,default=0)
    parser.add_argument('--width',type=int,default=1920)
    parser.add_argument('--height',type=int,default=1080)
    parser.add_argument('--render-subframes',type=int,default=16)
    parser.add_argument('--phase-cameras',type=Path,
                        help='Freeze optional edit phase:view choices; native frames are never retimed')
    parser.add_argument('--camera-profile',choices=tuple(CAMERA_PROFILES),default='legacy')
    parser.add_argument('--failed-diagnostics',action='store_true',
                        help='Failed trials only: one complete rear-view diagnostic each, no success edit')
    args=parser.parse_args(); attempts=select_attempts(args.attempt)
    quality=render_settings(args.width,args.height,args.render_subframes)
    mapping_bytes=args.phase_cameras.read_bytes() if args.phase_cameras else None
    if mapping_bytes is not None:
        from edit_multi_angle import phase_cameras
        phase_cameras(json.loads(mapping_bytes))
    views=('rear',) if args.failed_diagnostics else VIEWS
    cameras={view:camera_arguments(view,args.camera_profile,args.gpu) for view in views}
    root=Path(__file__).resolve().parents[2]
    evidence={}
    for label,path in attempts.items():
        result=json.loads((path/'results.json').read_text())
        validate_attempt(result,label,args.failed_diagnostics)
        evidence[label]={'attempt':str(path),'source_sha256':{n:sha(path/n) for n in
            ('scene.usda','results.json','trajectory.jsonl')}}
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=False)
    if mapping_bytes is not None: (output/'phase_cameras_input.json').write_bytes(mapping_bytes)
    frozen=output/'source/rack_robotics'; (frozen/'scripts').mkdir(parents=True)
    for source in (root/'rack_robotics').glob('*.py'): shutil.copy2(source,frozen/source.name)
    for name in ('render_replay.py','edit_multi_angle.py','render_demos.py'):
        shutil.copy2(root/'rack_robotics/scripts'/name,frozen/'scripts'/name)
    baseline=root/'rack_robotics/assets/shared_rack/baseline-001'
    hashes={str(p.relative_to(output)):sha(p) for p in (output/'source').rglob('*.py')}
    manifest={'schema':'failed_diagnostic_render_batch_v1' if args.failed_diagnostics else 'four_camera_render_batch_v1',
        'failed_diagnostics':args.failed_diagnostics,'attempts':evidence,'source_sha256':hashes,
        'baseline_manifest_sha256':sha(baseline/'manifest.json'),'cameras':cameras,'views':views,
        'camera_profile':args.camera_profile,'requested_gpu_index':args.gpu,
        'phase_cameras_input_sha256':hashlib.sha256(mapping_bytes).hexdigest() if mapping_bytes is not None else None,
        'settings':{'renderer':'RealTimePathTracing','resolution':[args.width,args.height],'fps':30,
                    'reset_render_history':True,'render_subframes':args.render_subframes},
        'scope':('Complete recorded failed attempts, not successful cycles; visual review required' if args.failed_diagnostics
                 else 'Recorded physical full-cycle replays; camera composition and temporal quality need manual review')}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    state={'complete':False,'cases':{label+'/'+view:{'status':'pending'} for label in attempts for view in views},'edits':{}}
    mutex=threading.Lock()

    def save():
        temp=output/'state.tmp'; temp.write_text(json.dumps(state,indent=2)+'\n'); temp.replace(output/'state.json')

    save()

    def capture(key):
        label,view=key.split('/'); destination=output/label/view
        destination.parent.mkdir(exist_ok=True)
        command=[args.isaac_python,'-u',str(frozen/'scripts/render_replay.py'),
            '--attempt',str(attempts[label]),'--output',str(destination),'--baseline',str(baseline),
            '--view',view,'--renderer','RealTimePathTracing','--no-denoiser',
            '--reset-render-history',*quality,*cameras[view],'--allow-root']
        record=state['cases'][key]
        with destination.with_suffix('.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            with mutex: record.update(status='running',pid=child.pid,command=command); save()
            code=child.wait()
        with mutex:
            record.update(exit_code=code,finished_utc_epoch=time.time())
            result=destination/'manifest.json'
            if result.exists():
                report=json.loads(result.read_text())
                if (code==0 and report['source_sha256']==evidence[label]['source_sha256'] and report['full_trajectory']
                        and report.get('active_gpu_setting')==args.gpu
                        and report.get('resolution')==[args.width,args.height]
                        and report.get('render_subframes')==args.render_subframes
                        and sha(destination/'demo.mp4')==report['video_sha256']):
                    record.update(status='captured',manifest_sha256=sha(result))
                else: record['status']='invalid_capture'
            else: record['status']='failed_capture'
            save(); print('DEMO_CAPTURE',key,record['status'],flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(capture,list(state['cases'])))
    for label,path in ([] if args.failed_diagnostics else attempts.items()):
        if not all(state['cases'][label+'/'+view]['status']=='captured' for view in VIEWS): continue
        command=[sys.executable,str(frozen/'scripts/edit_multi_angle.py'),'--attempt',str(path),
                 '--output',str(output/label/'multi_angle')]
        for view in VIEWS: command+=['--'+view,str(output/label/view)]
        if mapping_bytes is not None: command+=['--phase-cameras',str(output/'phase_cameras_input.json')]
        with (output/label/'multi_angle.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            state['edits'][label]={'status':'running','pid':child.pid}; save()
            code=child.wait()
        report_path=output/label/'multi_angle/manifest.json'
        state['edits'][label].update(exit_code=code,status='edited' if code==0 and report_path.exists() else 'failed')
        save()
    if any(sha(output/name)!=digest for name,digest in hashes.items()): raise ValueError('Frozen render source changed')
    if mapping_bytes is not None and (output/'phase_cameras_input.json').read_bytes()!=mapping_bytes:
        raise ValueError('Frozen phase-camera choices changed')
    state['complete']=(all(r['status']=='captured' for r in state['cases'].values())
                       and (args.failed_diagnostics or all(state['edits'].get(label,{}).get('status')=='edited' for label in attempts)))
    save(); print('DEMO_BATCH_COMPLETE',state['complete'],flush=True)
    if not state['complete']: raise SystemExit(1)


if __name__=='__main__': main()
