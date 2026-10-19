"""Compare preserved fixture revisions; this is not a reliability experiment."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from rack_robotics.benchmarking.metrics import trial_metrics


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(directory):
    result=json.loads((directory/'results.json').read_text())
    sources=json.loads((directory/'source_manifest.json').read_text())
    changed=[name for name,digest in sources.items() if sha(directory/name)!=digest]
    if changed: raise ValueError(f'Changed source evidence: {changed}')
    contacts=json.loads((directory/'initialization_contacts.json').read_text())
    self_contacts=[pair for pair in contacts['pairs']
                   if all(p.startswith('/World/Robot/') for p in pair['colliders'])]
    authored=json.loads((directory/'authored_conditions.json').read_text())
    return result,{'directory':str(directory),'runner':result['runner'],
        'evidence_sha256':{name:sha(directory/name) for name in
            ('results.json','source_manifest.json','initialization_contacts.json','authored_conditions.json')},
        'metrics':trial_metrics(result),'initial_robot_joint_states':authored.get('initial_robot_joint_states',[]),
        'initialization_adjustments':result.get('physical_initialization_adjustments',[]),
        'initial_self_contact_pairs':self_contacts,
        'initial_peak_pair_estimate_n':max((p['peak_pair_contact_force_n'] for p in contacts['pairs']),default=0.),
        'initial_contact_reporting_errors':contacts.get('reporting_errors'),
        'source_sha256':sources}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--before',type=Path,required=True)
    p.add_argument('--after',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    before,b=inspect(args.before); after,a=inspect(args.after)
    same_conditions=before['condition']==after['condition']
    same_environment=before['environment_manifest_sha256']==after['environment_manifest_sha256']
    if not same_conditions or not same_environment:
        raise ValueError('Cannot attribute fixture comparison across different conditions or environments')
    report={'same_conditions':same_conditions,'same_saved_environment':same_environment,
        'condition':before['condition'],'before':b,'after':a,
        'changed_source_files':[name for name in sorted(set(b['source_sha256'])|set(a['source_sha256']))
             if b['source_sha256'].get(name)!=a['source_sha256'].get(name)],
        'limitations':['Single-seed development comparison, not a reliability estimate.',
                      'Multiple fixture changes; no isolated causal attribution between those changes.',
                      'Pair impulse/dt is not a calibrated load; final retention does not prove pose precision.']}
    with args.output.open('x') as stream: stream.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'same_conditions':same_conditions,'same_saved_environment':same_environment,
        'before_complete':b['metrics']['complete_cycle'],'after_complete':a['metrics']['complete_cycle'],
        'before_self_contact_pairs':len(b['initial_self_contact_pairs']),
        'after_self_contact_pairs':len(a['initial_self_contact_pairs'])},indent=2))


if __name__=='__main__': main()
