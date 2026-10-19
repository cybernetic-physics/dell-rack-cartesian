"""Run a predeclared campaign without dropping failures or mutating saved designs.

Use --resume only after checking any interrupted processes. An inherited flock
prevents another evaluator from starting while a child simulation is alive.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import threading
import time


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_frozen_harness(campaign,output):
    """Extend an existing protocol without incorporating working-tree changes."""
    manifest=json.loads((campaign/'campaign_manifest.json').read_text())
    expected=manifest['harness_sha256']
    actual={str(f.relative_to(campaign)):sha(f) for f in (campaign/'harness').rglob('*.py')}
    if not expected or actual!=expected:
        raise ValueError('Source campaign harness is missing, changed, or has extra sources')
    shutil.copytree(campaign/'harness',output/'harness',ignore=shutil.ignore_patterns('__pycache__'))
    copied={str(f.relative_to(output)):sha(f) for f in (output/'harness').rglob('*.py')}
    if copied!=expected: raise ValueError('Copied harness differs from verified source')
    return {'directory':str(campaign.resolve()),'campaign_manifest_sha256':sha(campaign/'campaign_manifest.json')}


def checked_result(directory,expected_condition,environment_digest,expected_result_digest=None):
    """Validate a persisted result before accepting it, including orphaned results."""
    path=directory/'results.json'
    if expected_result_digest is not None and sha(path)!=expected_result_digest:
        raise ValueError(f'Completed result changed: {path}')
    result=json.loads(path.read_text())
    if (result.get('condition')!=expected_condition
            or result.get('environment_manifest_sha256')!=environment_digest
            or type(result.get('passed')) is not bool):
        raise ValueError(f'Result provenance mismatch: {path}')
    sources=json.loads((directory/'source_manifest.json').read_text())
    if not sources: raise ValueError(f'Missing source evidence: {directory}')
    for name,digest in sources.items():
        source=(directory/name).resolve()
        if not source.is_relative_to(directory.resolve()) or sha(source)!=digest:
            raise ValueError(f'Trial source changed: {name}')
    return result


def adopt_persisted_result(record,output,condition,environment_digest):
    """After liveness checks, adopt completed evidence without repeating physics."""
    if not record.get('directory'): return None
    directory=output/record['directory']
    if not (directory/'results.json').exists(): return None
    result=checked_result(directory,condition,environment_digest)
    record.update(status='finished',results_sha256=sha(directory/'results.json'),
                  passed=result['passed'],adopted_after_interruption=True,
                  adopted_utc_epoch=time.time())
    # Do not invent an exit code or finish time for a process we did not reap.
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--designs',default='AA,AC,BA,BC,CA,CC,AB,CB')
    p.add_argument('--workers',type=int,choices=(1,2),default=2)
    p.add_argument('--isaac-python',type=Path,default=Path('/isaac-sim/python.sh'))
    p.add_argument('--resume',action='store_true')
    p.add_argument('--project-root',type=Path,help='Required when executing a frozen evaluator outside the project scripts directory')
    p.add_argument('--harness-from',type=Path,help='For a new campaign, copy an existing verified frozen protocol exactly')
    args=p.parse_args()
    if args.resume and args.harness_from: p.error('Resume uses its own frozen harness; omit --harness-from')
    root=args.project_root.resolve() if args.project_root else Path(__file__).resolve().parents[2]
    if not (root/'rack_robotics/benchmarking').is_dir():
        raise ValueError('Project root not found; supply --project-root')
    output=args.output.resolve(); plan_path=args.plan.resolve()
    plan=json.loads(plan_path.read_text()); designs=args.designs.split(',')
    if not designs or len(set(designs))!=len(designs) or any(d not in plan['environments'] for d in designs):
        raise ValueError('Designs must be distinct entries in the predeclared plan')
    for name,digest in plan['condition_sha256'].items():
        if sha(plan_path.parent/name)!=digest: raise ValueError(f'Condition changed: {name}')
    for design in designs:
        entry=plan['environments'][design]
        if sha(root/entry['environment_relative_to_project']/'manifest.json')!=entry['manifest_sha256']:
            raise ValueError(f'Environment changed: {design}')
    if not args.isaac_python.is_file(): raise ValueError('Isaac Python launcher missing')
    output.mkdir(parents=True,exist_ok=args.resume)
    lock=(output/'.campaign.lock').open('a+')
    try: fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError: raise RuntimeError('Campaign or inherited simulation is still running; do not restart it')
    manifest_path=output/'campaign_manifest.json'
    if not args.resume:
        frozen=output/'harness'
        harness_source=None
        if args.harness_from:
            harness_source=copy_frozen_harness(args.harness_from.resolve(),output)
        else:
            shutil.copytree(root/'rack_robotics/benchmarking',frozen/'benchmarking',ignore=shutil.ignore_patterns('__pycache__'))
            for source,target in [('controllers/rj45_task.py','task.py'),('controllers/connector_observer.py','observer.py'),
                                  ('contacts.py','contacts.py'),('recording.py','recording.py'),('integrity.py','integrity.py'),
                                  ('experiment_timing.py','timing.py'),('carrier_validation.py','carrier_validation.py')]:
                shutil.copy2(root/'rack_robotics'/source,frozen/'benchmarking'/target)
            shutil.copy2(root/'rack_robotics/scripts/run_benchmark_trial.py',frozen/'run_benchmark_trial.py')
            shutil.copy2(__file__,frozen/'evaluate_all.py')
        shutil.copytree(plan_path.parent,output/'plan')
        manifest={'schema':'rack_benchmark_campaign_v1','plan_sha256':sha(plan_path),'designs':designs,
            'harness_sha256':{str(f.relative_to(output)):sha(f) for f in frozen.rglob('*.py')},
            'harness_source_campaign':harness_source,
            'created_utc_epoch':time.time(),'project_root':str(root),
            'rules':'Every predeclared condition is retained. Control failures stop that design; missing results leave campaign incomplete.'}
        manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')
    else:
        manifest=json.loads(manifest_path.read_text())
        if manifest['designs']!=designs or manifest['plan_sha256']!=sha(plan_path):
            raise ValueError('Resume requested with a different plan or design selection')
        for name,digest in manifest['harness_sha256'].items():
            if sha(output/name)!=digest: raise ValueError(f'Frozen harness changed: {name}')
    for name,digest in plan['condition_sha256'].items():
        if sha(output/'plan'/name)!=digest: raise ValueError(f'Frozen condition changed: {name}')
    frozen=output/'harness'; state_path=output/'campaign_state.json'
    state=json.loads(state_path.read_text()) if state_path.exists() else {'tasks':{},'complete':False}
    mutex=threading.Lock()

    def save():
        state['updated_utc_epoch']=time.time()
        temporary=state_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(state,indent=2)+'\n'); temporary.replace(state_path)

    def run(design,name):
        key=design+'/'+name
        expected=json.loads((output/'plan'/(name+'.json')).read_text())
        environment_digest=plan['environments'][design]['manifest_sha256']
        with mutex:
            previous=state['tasks'].get(key,{})
            if previous.get('status')=='finished':
                return checked_result(output/previous['directory'],expected,environment_digest,previous['results_sha256'])
            pid=previous.get('pid')
            if pid:
                cmdline=Path(f'/proc/{pid}/cmdline')
                if cmdline.exists() and str(output/previous['directory']).encode() in cmdline.read_bytes():
                    raise RuntimeError(f'Previous task is still alive: {key}, PID {pid}')
            adopted=adopt_persisted_result(previous,output,expected,environment_digest)
            if adopted is not None:
                save()
                print('CAMPAIGN_ADOPTED_RESULT',key,'pass' if adopted['passed'] else 'FAIL',flush=True)
                return adopted
            attempt=previous.get('attempt',0)+1
            directory=Path(design)/(name+f'-attempt{attempt:03d}')
            destination=output/directory
            destination.parent.mkdir(exist_ok=True)
            record={'attempt':attempt,'directory':str(directory),'status':'starting','history':previous}
            state['tasks'][key]=record; save()
        env=root/plan['environments'][design]['environment_relative_to_project']
        log_path=destination.with_suffix('.log')
        command=[str(args.isaac_python),'-u',str(frozen/'run_benchmark_trial.py'),
            '--environment',str(env),'--condition',str(output/'plan'/(name+'.json')),
            '--output',str(destination),'--allow-root']
        with log_path.open('xb') as log:
            process=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,pass_fds=(lock.fileno(),))
            with mutex:
                record.update(status='running',pid=process.pid,command=command); save()
            code=process.wait()  # No wall-time timeout: callers inspect the actual process.
        result_path=destination/'results.json'
        with mutex:
            record.update(exit_code=code,finished_utc_epoch=time.time())
            if not result_path.exists():
                record['status']='missing_result'; save(); return None
            try:
                result=checked_result(destination,expected,environment_digest)
            except (ValueError,OSError):
                record['status']='invalid_provenance'; save(); raise
            record.update(status='finished',results_sha256=sha(result_path),passed=result['passed']); save()
        print('CAMPAIGN_TRIAL',key,'pass' if result['passed'] else 'FAIL',flush=True)
        return result

    def run_design(design):
        result=run(design,'control')
        if result is None or not result.get('passed'):
            print('CAMPAIGN_CONTROL_FAILED',design,flush=True); return
        for index in range(plan['count_per_environment']):
            run(design,f'trial-{index:03d}')

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run_design,designs))
    with mutex:
        expected=[d+'/'+name for d in designs for name in
                  ['control']+[f'trial-{i:03d}' for i in range(plan['count_per_environment'])]]
        state['complete']=all(state['tasks'].get(key,{}).get('status')=='finished' for key in expected)
        state['missing_tasks']=[key for key in expected if state['tasks'].get(key,{}).get('status')!='finished']
        save()
    print('CAMPAIGN_COMPLETE',state['complete'],flush=True)
    if not state['complete']: raise SystemExit(1)


if __name__=='__main__': main()
