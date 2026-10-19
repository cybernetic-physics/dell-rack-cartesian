"""Export preserved robot trial outcomes; not a randomized benchmark or ranking.

Includes every results.json one directory below experiments that identifies
a robot. Isolated probes and baseline tests without a robot ID are excluded.
Development iterations and reloads must not be pooled as reliability samples.
"""
import argparse,csv,hashlib,json
from pathlib import Path


def summarize(path):
    result=json.loads(path.read_text())
    if 'robot' not in result: return None
    contacts_path=path.parent/'contacts.json'
    contacts=json.loads(contacts_path.read_text()) if contacts_path.exists() else None
    startup_path=path.parent/'initialization_contacts.json'
    startup=json.loads(startup_path.read_text()) if startup_path.exists() else None
    final=(result.get('trace') or [{}])[-1]
    physical_pass=all((result.get('passed'),result.get('initial_retained_without_hand'),
        result.get('unplug_success'),result.get('replug_success'),result.get('topology_audit',{}).get('passed')))
    mode=result.get('fault_injection',{}).get('mode','none')
    role=('reload' if result.get('loaded_scene') else 'fault_injection' if mode!='none' else 'development')
    return {'attempt':path.parent.name,'robot':result['robot'],'gripper':result.get('gripper',''),
        'scope':result.get('scope',''),'role':role,'randomized_reliability_sample':False,
        'reported_pass':result.get('passed',False),'complete_cycle_evidence':physical_pass,
        'cycle_time_s':result.get('cycle_time_s',''),'cable_max_gap_m':result.get('cable_max_gap_m',''),
        'physics_hz':result.get('physics_hz',''),
        'final_depth_m':final.get('depth_m',''),
        'final_lateral_m':final.get('lateral_m',''),
        'final_angle_deg':final.get('angle_deg',''),
        'final_hook_behind_lip':final.get('hook_behind_lip',''),
        'grasp_peak_pair_contact_estimate_n':max((p.get('phase_peaks_n',{}).get('grasp',0.) for p in contacts['pairs']),default=0.) if contacts else '',
        'startup_peak_pair_contact_estimate_n':max((p['peak_pair_contact_force_n'] for p in startup['pairs']),default=0.) if startup else '',
        'peak_pair_contact_estimate_n':max((p['peak_pair_contact_force_n'] for p in contacts['pairs']),default=0.) if contacts else '',
        'contact_reporting_errors':len(contacts['reporting_errors']) if contacts else '',
        'error':str(result.get('error') or '').strip().splitlines()[-1] if result.get('error') else '',
        'results_file':str(path),'results_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiments',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    rows=[row for path in sorted(args.experiments.glob('*/results.json')) if (row:=summarize(path)) is not None]
    if not rows: raise ValueError('No robot trial results found')
    with args.output.open('x',newline='') as target:
        writer=csv.DictWriter(target,fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    print(f'Exported {len(rows)} development/reload/fault rows; no reliability ranking is inferred.')


if __name__=='__main__': main()
