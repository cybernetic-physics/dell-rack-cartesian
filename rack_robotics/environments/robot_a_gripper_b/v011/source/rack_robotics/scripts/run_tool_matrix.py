"""Test corrected frames with a frozen, predeclared set of grippers.

No retries or timeout-driven restarts. Every failed/runtime-error case remains
in the matrix. A completed matrix is not a claim that every design works.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time

DEFAULT_DESIGNS='AC,BC,CC,AB,BB,CB'
FRAME_FLAGS={'A':'--open-screw-frame','B':'--open-telescoping-frame','C':'--open-gantry-frame'}


def select_designs(value):
    labels=value.split(',')
    if (not labels or len(labels)!=len(set(labels))
            or any(len(label)!=2 or any(c not in 'ABC' for c in label) for label in labels)):
        raise ValueError('Use unique comma-separated two-letter A/B/C design labels')
    return labels


def build_arguments(label,hz):
    select_designs(label)
    if len(label)!=2:raise ValueError('Expected one design label')
    if hz not in (240,480,960): raise ValueError('Unsupported solver rate')
    flags=['--robot',label[0],'--gripper',label[1],'--physics-hz',str(hz),
           '--hardware-detail','--open-insertion-stage',FRAME_FLAGS[label[0]],
           '--service-carriers','--motor-brakes','--rearward-insertion-support',
           '--cable-clearance-front-support']
    if label[1]=='A': flags.append('--forward-latch-neck')
    return flags


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def result_summary(path):
    if not path.exists():return {'outcome':'runtime_error','error':'No results.json produced'}
    result=json.loads(path.read_text())
    complete=all(result.get(k) is True for k in
                 ('passed','initial_retained_without_hand','unplug_success','replug_success'))
    physical=result.get('scope')=='full_rack' and result.get('topology_audit',{}).get('passed') is True
    return {'outcome':'passed' if complete and physical else 'failed',
            'reported_passed':result.get('passed'),'full_cycle_evidence':complete and physical,
            'cycle_time_s':result.get('cycle_time_s'),'error':result.get('error'),
            'recoveries':len(result.get('recoveries') or []),'results_sha256':sha(path)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--designs',default=DEFAULT_DESIGNS)
    parser.add_argument('--physics-hz',type=int,choices=(240,480,960),default=480)
    parser.add_argument('--workers',type=int,choices=(1,2),default=1)
    parser.add_argument('--isaac-python',default='/isaac-sim/python.sh')
    parser.add_argument('--usd-python',default='/opt/rack-usd-tools/bin/python3')
    args=parser.parse_args();labels=select_designs(args.designs)
    root=Path(__file__).resolve().parents[2]
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    snapshot=output/'source'
    for source in (root/'rack_robotics').rglob('*.py'):
        relative=source.relative_to(root)
        if any(p in relative.parts for p in ('assets','research','experiments','environments','__pycache__')):continue
        target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    if any(label[1]=='B' for label in labels):
        vendor=Path('rack_robotics/research/sources/onrobot-isaacsim')
        shutil.copytree(root/vendor/'assets/rg2',snapshot/vendor/'assets/rg2')
        shutil.copy2(root/vendor/'LICENSE',snapshot/vendor/'LICENSE')
    hashes={str(p.relative_to(output)):sha(p) for p in snapshot.rglob('*') if p.is_file()}
    baseline=root/'rack_robotics/assets/shared_rack/baseline-001'
    arguments={label:build_arguments(label,args.physics_hz) for label in labels}
    manifest={'schema':'corrected_frame_tool_matrix_v1','designs':labels,'arguments':arguments,
        'source_and_vendor_sha256':hashes,'baseline_manifest_sha256':sha(baseline/'manifest.json'),
        'scope':'Nominal full-rack feasibility on corrected frames, not randomized reliability or complete mechanical qualification',
        'rules':['All predeclared cases attempted once; failures are retained.',
                 'Identical frozen source/rate across cases; no case-specific tuning within this matrix.',
                 'Supported-box sweep is separate from task success and omits rack/non-box/tool articulation.']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    state={'complete':False,'cases':{label:{'status':'pending'} for label in labels}}
    lock=threading.Lock()
    def save():
        temporary=output/'state.tmp';temporary.write_text(json.dumps(state,indent=2)+'\n')
        temporary.replace(output/'state.json')
    def verify():
        for name,digest in hashes.items():
            if sha(output/name)!=digest:raise ValueError('Frozen source/vendor changed: '+name)
    save()

    def run(label):
        verify();destination=output/label
        command=[args.isaac_python,'-u',str(snapshot/'rack_robotics/scripts/run_reference.py'),
            '--baseline',str(baseline),'--output',str(destination),*arguments[label],'--allow-root']
        with (output/(label+'.log')).open('x') as log:
            child=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT)
            with lock:state['cases'][label].update(status='running',pid=child.pid,command=command);save()
            code=child.wait()
        row={'execution_exit_code':code,**result_summary(destination/'results.json')}
        if code!=0:row['outcome']='runtime_error'
        if (destination/'scene.usda').exists():
            audit_command=[args.usd_python,str(snapshot/'rack_robotics/scripts/audit_carrier_mounts.py'),
                '--scene',str(destination/'scene.usda'),'--output',str(destination/'robot_box_sweep001.json'),
                '--sweep','--robot-boxes','--all-robot-box-pairs']
            with (output/(label+'-box.log')).open('x') as log:
                audit=subprocess.Popen(audit_command,stdout=log,stderr=subprocess.STDOUT)
                with lock:state['cases'][label].update(status='auditing',audit_pid=audit.pid);save()
                row['box_audit_exit_code']=audit.wait()
            path=destination/'robot_box_sweep001.json'
            if path.exists():
                report=json.loads(path.read_text())
                row['box_sweep']={'passed':report['passed'],'pairs':report['distinct_body_pairs_checked'],
                                  'overlaps':len(report['possible_overlaps']),'sha256':sha(path)}
        verify()
        with lock:
            state['cases'][label].update(status='finished',finished_utc_epoch=time.time(),**row);save()
        print('TOOL_MATRIX_CASE',label,json.dumps(row),flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:list(pool.map(run,labels))
    verify();state['complete']=all(row['status']=='finished' for row in state['cases'].values());save()
    print('TOOL_MATRIX_COMPLETE',state['complete'],flush=True)


if __name__=='__main__':main()
