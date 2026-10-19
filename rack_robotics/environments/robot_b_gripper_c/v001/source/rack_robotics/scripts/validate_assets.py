"""Verify packaged hashes, USD dependency resolution, and actual reload evidence."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--environment',type=Path,required=True)
parser.add_argument('--reload-results',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args,_=parser.parse_known_args()
try:
    from pxr import UsdUtils
except ModuleNotFoundError:
    from isaacsim import SimulationApp
    import atexit
    app=SimulationApp({'headless':True,'multi_gpu':False,'width':640,'height':480})
    atexit.register(app.close)
    from pxr import UsdUtils
env=args.environment.resolve()
manifest=json.loads((env/'manifest.json').read_text())
errors=[]
source_mismatches=[]
for name,expected in manifest.get('tested_source',{}).items():
    path=env/'source'/name
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        source_mismatches.append(name)
# A later fresh-session reload can validate a deliberately updated controller,
# but that must not be misrepresented as the originally tested source snapshot.
for name,expected in manifest['packaged_file_sha256'].items():
    path=env/name
    if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
        errors.append(f'Packaged file missing or modified: {name}')
config=json.loads((env/'config.json').read_text())
baseline=(env/config['baseline']).resolve()/'manifest.json'
if hashlib.sha256(baseline.read_bytes()).hexdigest()!=manifest['baseline_manifest_sha256']:
    errors.append('Baseline manifest changed')
layers,assets,unresolved=UsdUtils.ComputeAllDependencies(str(env/'scene.usda'))
if unresolved: errors.append(f'Unresolved USD dependencies: {unresolved}')
reload=json.loads(args.reload_results.read_text())
if not all((reload.get('passed'),reload.get('scope')=='full_rack',
            reload.get('initial_retained_without_hand'),reload.get('unplug_success'),
            reload.get('replug_success'),reload.get('topology_audit',{}).get('passed'),
            reload.get('loaded_scene')==str(env/'scene.usda'))):
    errors.append('Reload evidence does not prove a complete physical cycle in this saved scene')
report={'passed':not errors,'errors':errors,'environment':str(env),
        'packaged_source_matches_original_trial':not source_mismatches,
        'original_trial_source_mismatches':source_mismatches,
        'hashes_checked':len(manifest['packaged_file_sha256']),
        'dependency_layers':len(layers),'dependency_assets':len(assets),
        'unresolved_dependencies':list(unresolved),
        'reload_results':str(args.reload_results.resolve()),
        'reload_results_sha256':hashlib.sha256(args.reload_results.read_bytes()).hexdigest(),
        'cycle_time_s':reload.get('cycle_time_s'),
        'scope':'File integrity, resolved USD assets and one fresh-session physical reload cycle; NOT reliability'}
with args.output.open('x') as target: target.write(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if errors: raise SystemExit(1)
