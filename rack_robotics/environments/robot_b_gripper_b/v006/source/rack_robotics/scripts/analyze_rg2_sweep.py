"""Compare measured RG2 sweeps against joint-anchor geometry, never task success."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rack_robotics.rg2_kinematics import tip_geometry

parser = argparse.ArgumentParser()
parser.add_argument('--attempts', type=Path, nargs='+', required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error('Output exists; preserve previous analysis')
reports = []
for attempt in args.attempts:
    source = attempt / 'results.json'
    result = json.loads(source.read_text())
    if not result.get('passed') or not result.get('samples'):
        raise ValueError(f'No passing physical sweep in {attempt}')
    errors = []
    for sample in result['samples']:
        # PhysX may go a negligible amount past a hard stop. Preserve and
        # separately report any excursion instead of treating a large one as valid.
        q = sample['joint_deg']
        clamped = max(0., min(70.06, q))
        separation, extension = tip_geometry(clamped)
        errors.append((abs(separation-sample['tip_origin_separation_m']),
                       abs(extension-sample['tip_extension_m']), abs(q-clamped)))
    maxima = [max(e[i] for e in errors) for i in range(3)]
    hashes = json.loads((attempt/'source_manifest.json').read_text())
    hash_errors = [name for name, expected in hashes.items()
                   if not (attempt/name).is_file() or hashlib.sha256((attempt/name).read_bytes()).hexdigest()!=expected]
    reports.append({'attempt':str(attempt), 'results_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                    'hz':result['hz'], 'samples':len(errors), 'preserved_hash_errors':hash_errors,
                    'max_separation_residual_m':maxima[0], 'max_extension_residual_m':maxima[1],
                    'max_limit_excursion_deg':maxima[2],
                    'passed':not hash_errors and max(maxima[:2])<.00005 and maxima[2]<.01})
report={'passed':all(r['passed'] for r in reports),
        'scope':'Unloaded linkage geometry and file integrity only; no rack/contact-force/reliability verdict',
        'model_sha256':hashlib.sha256((Path(__file__).resolve().parents[1]/'rg2_kinematics.py').read_bytes()).hexdigest(),
        'attempts':reports}
args.output.parent.mkdir(parents=True,exist_ok=True)
args.output.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if not report['passed']:
    raise SystemExit(1)
