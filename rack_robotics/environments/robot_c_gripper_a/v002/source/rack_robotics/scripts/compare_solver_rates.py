"""Compare an exact-source 240/480 Hz pair without treating agreement as convergence."""
import argparse
import hashlib
import json
from pathlib import Path


def inspect_trial(path):
    result=json.loads((path/'results.json').read_text())
    contacts=json.loads((path/'contacts.json').read_text())
    manifest=json.loads((path/'source_manifest.json').read_text())
    valid=bool(manifest) and all((path/'source'/name).is_file() and
              hashlib.sha256((path/'source'/name).read_bytes()).hexdigest()==digest
              for name,digest in manifest.items())
    phases={}
    for pair in contacts['pairs']:
        for phase,force in pair.get('phase_peaks_n',{}).items():
            phases[phase]=max(phases.get(phase,0.),force)
    return result,contacts,manifest,valid,phases


def compare(low,high):
    trials=[inspect_trial(path) for path in (low,high)]
    a,b=trials
    problems=[]
    if a[2]!=b[2]: problems.append('Frozen source manifests differ')
    if not all(t[3] for t in trials): problems.append('A frozen source file does not match its manifest')
    for key in ('robot','gripper','scope','gripper_control','lift_gravity_bias_m'):
        if a[0].get(key)!=b[0].get(key): problems.append(f'Configuration differs: {key}')
    for hz,(r,c,_,_,_) in zip((240,480),trials):
        if r.get('physics_hz')!=hz or r.get('physics_dt')!=1/hz or c['physics_dt']!=1/hz:
            problems.append(f'Missing/inconsistent {hz} Hz timing evidence')
        if c['reporting_errors']: problems.append(f'{hz} Hz contact reporting errors')
    summaries=[]
    for path,(r,c,_,_,peaks) in zip((low,high),trials):
        summaries.append({'attempt':str(path),'passed':r['passed'],
            'physics_hz':r.get('physics_hz'),'cycle_time_s':r.get('cycle_time_s'),
            'error':r.get('error'),'recoveries':r.get('recoveries',[]),
            'phase_peak_pair_contact_estimate_n':peaks,
            'final_aperture_m':(r.get('trace') or [{}])[-1].get('aperture_m'),
            'results_sha256':hashlib.sha256((path/'results.json').read_bytes()).hexdigest()})
    return {'paired_setup_verified':not problems,'errors':problems,'trials':summaries,
        'convergence_established':False,
        'scope':'One matched-source solver-rate sensitivity pair, not reliability or convergence. Impulse/dt peaks are timestep-dependent, uncalibrated contact estimates.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--low',type=Path,required=True)
    p.add_argument('--high',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    report=compare(args.low,args.high)
    with args.output.open('x') as output: output.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if report['errors']: raise SystemExit(1)
