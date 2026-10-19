"""Snapshot complete and missing campaign evidence without ranking partial results."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from rack_robotics.benchmarking.metrics import trial_metrics,wilson,cable_displacement


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def summarize(campaign):
    manifest=json.loads((campaign/'campaign_manifest.json').read_text())
    state_bytes=(campaign/'campaign_state.json').read_bytes()
    state=json.loads(state_bytes)
    plan=json.loads((campaign/'plan/plan.json').read_text())
    errors=[]
    if digest(campaign/'plan/plan.json')!=manifest['plan_sha256']: errors.append('Plan hash mismatch')
    for name,expected in manifest['harness_sha256'].items():
        if digest(campaign/name)!=expected: errors.append(f'Harness changed: {name}')
    for name,expected in plan['condition_sha256'].items():
        if digest(campaign/'plan'/name)!=expected: errors.append(f'Condition changed: {name}')
    rows=[]; controls={}; summaries={}
    for design in manifest['designs']:
        observations=[]; missing=[]
        for name in ['control']+[f'trial-{i:03d}' for i in range(plan['count_per_environment'])]:
            key=design+'/'+name; task=state['tasks'].get(key,{})
            if task.get('status')!='finished':
                if name=='control': controls[design]={'status':task.get('status','not_started')}
                else: missing.append(name)
                continue
            directory=campaign/task['directory']; result_path=directory/'results.json'
            if digest(result_path)!=task['results_sha256']: errors.append(f'Result changed: {key}')
            result=json.loads(result_path.read_text())
            expected=json.loads((campaign/'plan'/(name+'.json')).read_text())
            if result.get('condition')!=expected: errors.append(f'Wrong conditions: {key}')
            if result.get('environment_manifest_sha256')!=plan['environments'][design]['manifest_sha256']:
                errors.append(f'Wrong environment: {key}')
            sources=json.loads((directory/'source_manifest.json').read_text())
            for source,expected_hash in sources.items():
                if digest(directory/source)!=expected_hash: errors.append(f'Changed trial source: {key}/{source}')
            contacts_path=directory/'contacts.json'
            contacts=json.loads(contacts_path.read_text()) if contacts_path.exists() else None
            metrics=trial_metrics(result,contacts)
            trajectory_path=directory/'trajectory.jsonl'
            if trajectory_path.exists():
                with trajectory_path.open() as stream:
                    header=json.loads(next(stream)); samples=[json.loads(line) for line in stream]
                metrics['cable_displacement']=cable_displacement(header,samples)
            row={'design':design,'condition':name,'port':result['condition']['port'],
                 'directory':str(directory),'results_sha256':digest(result_path),**metrics}
            if name=='control': controls[design]=row
            else: observations.append(row); rows.append(row)
        successes=sum(row['complete_cycle'] for row in observations)
        admissible=sum(row['admissible_initial_state'] for row in observations)
        times=[r['cycle_time_s'] for r in observations if r['complete_cycle'] and r['cycle_time_s'] is not None]
        complete=len(observations)==plan['count_per_environment'] and controls.get(design,{}).get('complete_cycle',False)
        summaries[design]={'planned':plan['count_per_environment'],'finished':len(observations),
            'complete_cycles':successes,'unplug_successes':sum(r['unplug_success'] for r in observations),
            'admissible_manipulation_trials':admissible,
            'fixture_failures':sum(r['fixture_failure'] for r in observations),
            'minimum_ten_valid_trials_met':admissible>=10,
            'replug_successes':sum(r['replug_success'] for r in observations),
            'missing':missing,'complete':complete,
            'protocol_success_rate_including_fixture':successes/len(observations) if complete else None,
            'complete_cycle_rate':successes/admissible if complete and admissible>=10 else None,
            'wilson_95_interval':wilson(successes,admissible) if complete and admissible>=10 else None,
            'mean_successful_cycle_s':sum(times)/len(times) if times else None,
            'port_counts':{str(p):{'trials':sum(r['port']==p for r in observations),
                                 'complete_cycles':sum(r['port']==p and r['complete_cycle'] for r in observations)}
                           for p in (1,4,8,12,16)}}
    return {'schema':'rack_benchmark_summary_v2','campaign_directory':str(campaign),
        'campaign_manifest_sha256':digest(campaign/'campaign_manifest.json'),
        'campaign_state_snapshot_sha256':hashlib.sha256(state_bytes).hexdigest(),
        'evidence_hashes_valid':not errors,'errors':errors,
        'campaign_complete':not errors and all(row['complete'] for row in summaries.values()),
        'minimum_valid_trial_requirement_met':not errors and all(row['complete'] and row['minimum_ten_valid_trials_met'] for row in summaries.values()),
        'designs':summaries,'controls':controls,'trials':rows,'ranking':None,
        'limitations':['No final ranking: rack load, dense cabling, buildability, cost and ≥20 trials for best are still required.',
                       'All contact peaks are collider-pair impulse/dt estimates, not net insertion force or calibrated safety loads.',
                       'Cable displacement and joint gap are not cable tensile force.',
                       'Retained-state hysteresis does not guarantee the final pose satisfies seating-entry tolerances.']}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--campaign',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    report=summarize(args.campaign)
    with args.output.open('x') as output: output.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'campaign_complete':report['campaign_complete'],'errors':report['errors'],'designs':report['designs']},indent=2))
    if report['errors']: raise SystemExit(1)
