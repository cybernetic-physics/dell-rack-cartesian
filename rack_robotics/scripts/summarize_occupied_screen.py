"""Verify and summarize a terminal crowded-port screen, retaining every failure."""
import argparse
import json
from pathlib import Path
from evaluate_all import checked_result, sha
from screen_occupied_ports import validate_diagnostic


def summarize_rows(rows, designs):
    if len({(r['design'],r['condition']) for r in rows}) != len(rows):
        raise ValueError('Duplicate diagnostic case')
    output={}
    for design in designs:
        selected=[r for r in rows if r['design']==design]
        output[design]={'cases':len(selected),'task_passes':sum(r['task_passed'] for r in selected),
            'clearance_passes':sum(r['clearance_passed'] for r in selected),
            'cases_with_robot_neighbor_contact':sum(r['robot_neighbor_contact_pair_count']>0 for r in selected),
            'cases_without_stable_timed_fixture':sum(not r['timed_trial_started'] or not r['fixture_stable'] for r in selected),
            'ports':[r['port'] for r in selected]}
    return output


def summarize(screen):
    screen=screen.resolve()
    manifest=json.loads((screen/'manifest.json').read_text())
    state=json.loads((screen/'state.json').read_text())
    if not state.get('complete'): raise ValueError('Screen is not terminal/complete; do not infer outcomes')
    for name,digest in manifest['harness_sha256'].items():
        if sha(screen/name)!=digest: raise ValueError('Changed frozen harness: '+name)
    plan_path=screen/'plan/plan.json'
    if sha(plan_path)!=manifest['plan_sha256']: raise ValueError('Changed frozen plan')
    plan=json.loads(plan_path.read_text())
    expected={d+'/'+n for d in manifest['designs'] for n in manifest['conditions']}
    if set(state['cases'])!=expected: raise ValueError('Missing or extra declared cases')
    rows=[]
    for key in sorted(expected):
        design,name=key.split('/'); record=state['cases'][key]
        if record['status']!='finished': raise ValueError('Unfinished case: '+key)
        condition_path=screen/'plan'/(name+'.json')
        if sha(condition_path)!=plan['condition_sha256'][name+'.json']: raise ValueError('Changed condition')
        condition=json.loads(condition_path.read_text())
        result=checked_result(screen/key,condition,plan['environments'][design]['manifest_sha256'],record['results_sha256'])
        fields=validate_diagnostic(result)
        if any(record.get(k)!=v for k,v in fields.items()): raise ValueError('State/result verdict disagreement: '+key)
        neighbors=result.get('occupied_neighbors',{})
        row={'design':design,'condition':name,'port':condition['port'],**fields,
            'results_sha256':record['results_sha256'],'result_relative_to_screen':key+'/results.json',
            'cycle_time_s':result.get('cycle_time_s'),
            'final_phase':(result.get('trace') or [{}])[-1].get('phase'),
            'robot_neighbor_contacts':neighbors.get('robot_neighbor_contact_pairs',[])}
        # Contact of the target plug/latch/cable with adjacent occupied hardware
        # is additional evidence, not silently included in the robot-only gate.
        contacts_path=screen/key/'contacts.json'
        row['target_neighbor_contacts']=[]
        if contacts_path.exists():
            contacts=json.loads(contacts_path.read_text())
            for pair in contacts['pairs']:
                paths=pair['colliders']
                target=any(p.startswith(('/World/Plug/','/World/Latch/','/World/Cable/')) for p in paths)
                adjacent=any(p.startswith('/World/OccupiedNeighbors/') for p in paths)
                if target and adjacent and pair['peak_pair_contact_force_n']>0:
                    row['target_neighbor_contacts'].append(pair)
            row['contacts_sha256']=sha(contacts_path)
        rows.append(row)
    summary={'schema':'occupied_neighbor_screen_summary_v1','complete':True,
        'screen_manifest_sha256':sha(screen/'manifest.json'),'screen_state_sha256':sha(screen/'state.json'),
        'environment_manifest_sha256':{d:plan['environments'][d]['manifest_sha256'] for d in manifest['designs']},
        'designs':summarize_rows(rows,manifest['designs']),'cases':rows,
        'scope':'Paired five-port restrained-neighbor diagnostic, not randomized reliability, full-density cabling, retention-force or tension certification',
        'gate':'Task success, stable timed fixture and zero reported robot-neighbor contact; target-neighbor contacts reported separately'}
    return summary


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--screen',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    summary=summarize(args.screen)
    with args.output.open('x') as target: target.write(json.dumps(summary,indent=2)+'\n')
    print(json.dumps(summary['designs'],indent=2))


if __name__=='__main__': main()
