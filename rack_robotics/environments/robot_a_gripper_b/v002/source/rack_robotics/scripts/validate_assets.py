"""Verify packaged hashes, USD dependency resolution, and actual reload evidence."""
import argparse
import hashlib
import json
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--environment',type=Path,required=True)
parser.add_argument('--reload-results',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--expect-failure',action='store_true',help='Verify a preserved failed design reproduces its failure; never claims task success')
parser.add_argument('--asset-search-path',type=Path,action='append',default=[],
                    help='Explicit installed asset library, e.g. Isaac Kit MDL core directory for USD-only tools')
args,_=parser.parse_known_args()
try:
    from pxr import UsdUtils
except ModuleNotFoundError:
    from isaacsim import SimulationApp
    import atexit
    app=SimulationApp({'headless':True,'multi_gpu':False,'width':640,'height':480})
    atexit.register(app.close)
    from pxr import UsdUtils
from pxr import Ar, Usd
for path in args.asset_search_path:
    if not path.is_dir(): raise ValueError(f'Asset library does not exist: {path}')
if args.asset_search_path:
    Ar.DefaultResolver.SetDefaultSearchPath([str(path.resolve()) for path in args.asset_search_path])
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
failure_reproduced=False
if args.expect_failure:
    original=json.loads((env/'results.json').read_text())
    def final_phase(path):
        if not path.exists(): return None
        with path.open() as stream:
            values=[json.loads(line) for line in stream]
        return values[-1].get('phase') if len(values)>1 else None
    original_phase=final_phase(env/'trajectory.jsonl')
    reload_phase=final_phase(args.reload_results.parent/'trajectory.jsonl')
    topology=args.reload_results.parent/'physics_integrity.json'
    audit=json.loads(topology.read_text()) if topology.exists() else {}
    def error_kind(result):
        lines=str(result.get('error') or '').strip().splitlines()
        return lines[-1].split(':')[0] if lines else None
    original_kind=error_kind(original)
    reload_kind=error_kind(reload)
    failure_reproduced=all((config['status']=='failed_feasibility',
        original.get('passed') is False,reload.get('passed') is False,
        reload.get('scope')=='full_rack',reload.get('loaded_scene')==str(env/'scene.usda'),
        audit.get('passed'),original_phase is not None,original_phase==reload_phase,
        original_kind is not None,original_kind==reload_kind))
    if not failure_reproduced: errors.append('Expected failed physical trial was not reproduced in this saved scene')
elif not all((reload.get('passed'),reload.get('scope')=='full_rack',
              reload.get('initial_retained_without_hand'),reload.get('unplug_success'),
              reload.get('replug_success'),reload.get('topology_audit',{}).get('passed'),
              reload.get('loaded_scene')==str(env/'scene.usda'))):
    errors.append('Reload evidence does not prove a complete physical cycle in this saved scene')
report={'passed':not errors,'errors':errors,'environment':str(env),
        'usd_version':list(Usd.GetVersion()),
        'asset_search_paths':[str(path.resolve()) for path in args.asset_search_path],
        'packaged_source_matches_original_trial':not source_mismatches,
        'original_trial_source_mismatches':source_mismatches,
        'hashes_checked':len(manifest['packaged_file_sha256']),
        'dependency_layers':len(layers),'dependency_assets':len(assets),
        'unresolved_dependencies':list(unresolved),
        'reload_results':str(args.reload_results.resolve()),
        'reload_results_sha256':hashlib.sha256(args.reload_results.read_bytes()).hexdigest(),
        'task_passed':reload.get('passed'),
        'expected_failure_reproduced':failure_reproduced,
        'cycle_time_s':reload.get('cycle_time_s'),
        'scope':('File integrity, resolved USD assets and reproduction of a FAILED physical trial; NOT task success or reliability'
                 if args.expect_failure else
                 'File integrity, resolved USD assets and one fresh-session physical reload cycle; NOT reliability')}
with args.output.open('x') as target: target.write(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
if errors: raise SystemExit(1)
