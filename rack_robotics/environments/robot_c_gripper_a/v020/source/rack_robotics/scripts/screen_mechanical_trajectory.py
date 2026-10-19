"""Calculate model envelopes and gravity loads from preserved measured motion."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from rack_robotics.mechanical_screen import screen
from rack_robotics.mechanical_evidence import verify_identity


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--properties',type=Path,required=True)
p.add_argument('--attempt',type=Path,required=True)
p.add_argument('--environment',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
args=p.parse_args()
props=json.loads(args.properties.read_text())
result=json.loads((args.attempt/'results.json').read_text())
environment_digest=sha(args.environment/'manifest.json')
identity_mode=verify_identity(props,args.attempt,args.environment)
with (args.attempt/'trajectory.jsonl').open() as stream:
    header=json.loads(next(stream)); samples=[json.loads(line) for line in stream]
report=screen(props,header,samples)
report.update(robot=props['robot'],gripper=props['gripper'],source_task_passed=result['passed'],
    trajectory_identity_mode=identity_mode,
    motion_scope='Completed recorded task cycle' if result['passed'] else 'Partial failed task only; not a full-cycle workspace',
    environment_manifest_sha256=environment_digest,
    evidence_sha256={'properties':sha(args.properties),'trajectory':sha(args.attempt/'trajectory.jsonl'),
                     'results':sha(args.attempt/'results.json')},
    analysis_sha256=sha(Path(__file__).resolve().parents[1]/'mechanical_screen.py'))
with args.output.open('x') as stream: stream.write(json.dumps(report,indent=2)+'\n')
print(json.dumps({key:report[key] for key in ('total_modeled_mass_kg','moving_mass_kg',
    'maximum_sampled_overhang','largest_sampled_gravity_mount_moment','telescoping_joint_gravity_loads')},indent=2))
