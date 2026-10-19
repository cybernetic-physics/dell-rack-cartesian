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


def camera_arguments(view,profile,gpu):
    if view not in VIEWS or profile not in CAMERA_PROFILES:
        raise ValueError('Unknown camera view/profile')
    if not isinstance(gpu,int) or isinstance(gpu,bool) or gpu<0:
        raise ValueError('GPU index must be a nonnegative integer')
    return ['--gpu',str(gpu),*CAMERA_PROFILES[profile][view]]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


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
    parser.add_argument('--camera-profile',choices=tuple(CAMERA_PROFILES),default='legacy')
    args=parser.parse_args(); attempts=select_attempts(args.attempt)
    cameras={view:camera_arguments(view,args.camera_profile,args.gpu) for view in VIEWS}
    root=Path(__file__).resolve().parents[2]
    evidence={}
    for label,path in attempts.items():
        result=json.loads((path/'results.json').read_text())
        if not result.get('passed') or result.get('scope')!='full_rack':
            raise ValueError('Only successful full-rack trajectories: '+label)
        if result['robot'][0]+result['gripper'][0]!=label: raise ValueError('Wrong design label')
        evidence[label]={'attempt':str(path),'source_sha256':{n:sha(path/n) for n in
            ('scene.usda','results.json','trajectory.jsonl')}}
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=False)
    frozen=output/'source/rack_robotics'; (frozen/'scripts').mkdir(parents=True)
    for source in (root/'rack_robotics').glob('*.py'): shutil.copy2(source,frozen/source.name)
    for name in ('render_replay.py','edit_multi_angle.py','render_demos.py'):
        shutil.copy2(root/'rack_robotics/scripts'/name,frozen/'scripts'/name)
    baseline=root/'rack_robotics/assets/shared_rack/baseline-001'
    hashes={str(p.relative_to(output)):sha(p) for p in (output/'source').rglob('*.py')}
    manifest={'schema':'four_camera_render_batch_v1','attempts':evidence,'source_sha256':hashes,
        'baseline_manifest_sha256':sha(baseline/'manifest.json'),'cameras':cameras,'views':VIEWS,
        'camera_profile':args.camera_profile,'requested_gpu_index':args.gpu,
        'settings':{'renderer':'RealTimePathTracing','resolution':[1920,1080],'fps':30,
                    'reset_render_history':True,'render_subframes':16},
        'scope':'Recorded physical full-cycle replays; camera composition and temporal quality need manual review'}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    state={'complete':False,'cases':{label+'/'+view:{'status':'pending'} for label in attempts for view in VIEWS},'edits':{}}
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
            '--reset-render-history','--render-subframes','16',*cameras[view],'--allow-root']
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
                        and sha(destination/'demo.mp4')==report['video_sha256']):
                    record.update(status='captured',manifest_sha256=sha(result))
                else: record['status']='invalid_capture'
            else: record['status']='failed_capture'
            save(); print('DEMO_CAPTURE',key,record['status'],flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(capture,list(state['cases'])))
    for label,path in attempts.items():
        if not all(state['cases'][label+'/'+view]['status']=='captured' for view in VIEWS): continue
        command=[sys.executable,str(frozen/'scripts/edit_multi_angle.py'),'--attempt',str(path),
                 '--output',str(output/label/'multi_angle')]
        for view in VIEWS: command+=['--'+view,str(output/label/view)]
        with (output/label/'multi_angle.log').open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            state['edits'][label]={'status':'running','pid':child.pid}; save()
            code=child.wait()
        report_path=output/label/'multi_angle/manifest.json'
        state['edits'][label].update(exit_code=code,status='edited' if code==0 and report_path.exists() else 'failed')
        save()
    if any(sha(output/name)!=digest for name,digest in hashes.items()): raise ValueError('Frozen render source changed')
    state['complete']=(all(r['status']=='captured' for r in state['cases'].values())
                       and all(state['edits'].get(label,{}).get('status')=='edited' for label in attempts))
    save(); print('DEMO_BATCH_COMPLETE',state['complete'],flush=True)
    if not state['complete']: raise SystemExit(1)


if __name__=='__main__': main()
