"""Predeclare paired conditions and frozen design identities before trials run."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from rack_robotics.benchmarking.spec import conditions,control,select_designs

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--seed',type=int,default=20261017)
p.add_argument('--count',type=int,default=10)
p.add_argument('--output',type=Path,required=True)
p.add_argument('--environment',action='append',help='Explicit cohort member, e.g. AA=robot_a_gripper_a/v005; repeat for each design')
args=p.parse_args()
rows=conditions(args.seed,args.count)
args.output.mkdir(parents=True,exist_ok=False)
designs={'AA':'robot_a_gripper_a/v001','AC':'robot_a_gripper_c/v002',
         'BA':'robot_b_gripper_a/v002','BC':'robot_b_gripper_c/v003',
         'CA':'robot_c_gripper_a/v001','CC':'robot_c_gripper_c/v001',
         'AB':'robot_a_gripper_b/v003','CB':'robot_c_gripper_b/v001'}
designs=select_designs(args.environment,designs)
environments={}
for name,relative in designs.items():
    env=root/'rack_robotics/environments'/relative
    manifest=env/'manifest.json'
    if not manifest.exists(): raise ValueError(f'Missing saved design {env}')
    result=json.loads((env/'results.json').read_text())
    if result.get('passed') is not True: raise ValueError(f'Design lacks basic feasibility: {env}')
    environments[name]={'environment_relative_to_project':'rack_robotics/environments/'+relative,
        'manifest_sha256':hashlib.sha256(manifest.read_bytes()).hexdigest()}
for name,row in [('control',control())]+[(f'trial-{i:03d}',row) for i,row in enumerate(rows)]:
    (args.output/(name+'.json')).write_text(json.dumps(row,indent=2)+'\n')
plan={'schema':'rack_benchmark_plan_v1','seed':args.seed,'count_per_environment':args.count,
    'environments':environments,'excluded':({'BB':'No full-cycle feasibility pass; preserve diagnostic failures separately'} if not args.environment else {}),
    'selection':'Explicit versioned cohort' if args.environment else 'Original eight-design feasibility cohort',
    'condition_sha256':{path.name:hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(args.output.glob('*.json'))},
    'rules':['Run all predeclared trials; no dropping failed starts or failed manipulations.',
             'Control trials verify the harness and are excluded from randomized rates.',
             'Same conditions across all listed designs; do not tune within a campaign.',
             'Ten declared conditions do not guarantee ten valid manipulation starts; fixture failures never satisfy the minimum.',
             'Every feasibility-passing design requires at least ten admissible manipulation trials; top designs require at least twenty.',
             'Force, electrical behavior, dense-cable clearance and buildability need separate evidence.']}
(args.output/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print(args.output/'plan.json')
