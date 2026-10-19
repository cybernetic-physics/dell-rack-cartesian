"""Reconcile every saved version with immutable package and actual reload evidence.

Runs without Isaac. Dependency resolution is historical evidence from the named
validator reports, not claimed as a new local USD dependency-resolution run.
"""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def local_path(value, root):
    path = Path(value)
    if path.is_relative_to('/workspace'):
        path = root/path.relative_to('/workspace')
    elif not path.is_absolute():
        path = root/path
    path = path.resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError('Evidence escapes project: '+value)
    return path


def audit_environment(environment, reports, root):
    root = root.resolve(); environment = environment.resolve()
    manifest = json.loads((environment/'manifest.json').read_text())
    config = json.loads((environment/'config.json').read_text())
    errors = []
    for name, digest in manifest['packaged_file_sha256'].items():
        path = local_path(str(environment/name), root)
        if not path.is_file() or sha(path) != digest: errors.append('Changed package file: '+name)
    baseline = (environment/config['baseline']).resolve()/'manifest.json'
    if not baseline.is_file() or sha(baseline) != manifest['baseline_manifest_sha256']:
        errors.append('Changed baseline manifest')
    evidence = []
    for report_path in reports:
        report_path = report_path.resolve()
        report = json.loads(report_path.read_text())
        if local_path(report['environment'], root) != environment.resolve(): continue
        result_path = local_path(report['reload_results'], root)
        valid_digest = result_path.is_file() and sha(result_path) == report['reload_results_sha256']
        result = json.loads(result_path.read_text()) if valid_digest else {}
        loaded = bool(valid_digest and result.get('loaded_scene')
                      and local_path(result['loaded_scene'], root) == environment/'scene.usda'
                      and result.get('scope') == 'full_rack')
        dependencies = (report.get('unresolved_dependencies') == []
                        and report.get('dependency_layers', 0) > 0
                        and report.get('dependency_assets', 0) > 0
                        and report.get('hashes_checked') == len(manifest['packaged_file_sha256']))
        expected = (result.get('passed') is False if config['status'] == 'failed_feasibility'
                    else result.get('passed') is True)
        evidence.append({'report': str(report_path.relative_to(root)), 'report_sha256': sha(report_path),
            'result': str(result_path.relative_to(root)), 'result_digest_valid': valid_digest,
            'saved_scene_loaded': loaded, 'dependency_report_complete': dependencies,
            'validator_passed': report.get('passed') is True,
            'task_passed': result.get('passed'),
            'declared_outcome_reproduced': bool(expected and report.get('passed')),
            'original_trial_source_matches': report.get('packaged_source_matches_original_trial'),
            'original_trial_source_mismatches': report.get('original_trial_source_mismatches', []),
            'validator_errors': report.get('errors', [])})
    return {'environment': str(environment.relative_to(root)), 'status': config['status'],
        'manifest_sha256': sha(environment/'manifest.json'), 'package_errors': errors,
        'package_hashes_checked': len(manifest['packaged_file_sha256']), 'evidence': evidence,
        'independent_scene_load_verified': not errors and any(e['saved_scene_loaded'] and
            e['dependency_report_complete'] for e in evidence),
        'declared_outcome_verified': not errors and any(e['declared_outcome_reproduced'] and
            e['saved_scene_loaded'] and e['dependency_report_complete'] for e in evidence)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    reports = []
    for name in ('reload_verification.json', 'verification.json'):
        reports.extend((root/'rack_robotics/environments').glob('*/*/'+name))
    reports.extend((root/'rack_robotics/experiments').glob('*reload*/asset_validation*.json'))
    reports.extend((root/'rack_robotics/experiments').glob('reload-campaign*/*/asset_validation.json'))
    environments = sorted(p.parent for p in (root/'rack_robotics/environments').glob('*/*/manifest.json'))
    rows = [audit_environment(env, reports, root) for env in environments]
    summary = {'schema': 'saved_environment_preservation_audit_v1', 'versions': len(rows),
        'independent_scene_loads_verified': sum(r['independent_scene_load_verified'] for r in rows),
        'declared_outcomes_verified': sum(r['declared_outcome_verified'] for r in rows), 'environments': rows,
        'scope': 'Current package/result hashes and historical fresh-session/dependency evidence; not new physics, reliability, or new local dependency resolution'}
    with args.output.open('x') as target: target.write(json.dumps(summary, indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k != 'environments'}, indent=2))


if __name__ == '__main__': main()
