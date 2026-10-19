"""Fresh-session reload audit; preserves failed designs as failures.

The output directory must be new. A stopped or interrupted batch is evidence,
not permission to overwrite/relaunch it. Inspect its PIDs and results first.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys


def verify_package(environment):
    manifest = json.loads((environment/'manifest.json').read_text())
    for name, expected in manifest['packaged_file_sha256'].items():
        path = environment/name
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'Changed packaged input: {path}')
    return hashlib.sha256((environment/'manifest.json').read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--isaac-python', default='/isaac-sim/python.sh')
    parser.add_argument('--usd-python', default='/opt/rack-usd-tools/bin/python3')
    parser.add_argument('--asset-search-path', default='/isaac-sim/kit/mdl/core/Base')
    args = parser.parse_args()
    environments = [path.resolve() for path in args.environment]
    keys = [f'{path.parent.name}-{path.name}' for path in environments]
    if len(set(keys)) != len(keys):
        parser.error('Environment output names must be unique')
    hashes = [verify_package(path) for path in environments]
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    validator = output/'validate_assets_source.py'
    shutil.copy2(Path(__file__).with_name('validate_assets.py'), validator)
    shutil.copy2(__file__, output/'reload_source.py')
    manifest = {'environments': [{'path': str(path), 'manifest_sha256': digest}
                for path, digest in zip(environments, hashes)],
                'validator_sha256': hashlib.sha256(validator.read_bytes()).hexdigest(),
                'scope': 'Fresh-session physical reload and dependency audit, not new reliability trials'}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    results = []
    for environment, key, digest in zip(environments, keys, hashes):
        trial = output/key
        command = [args.isaac_python, '-u', str(environment/'demo.py'),
                   '--output', str(trial), '--allow-root']
        with (output/f'{key}.log').open('x') as log:
            child = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            print('RELOAD_CHILD', key, child.pid, flush=True)
            execution_code = child.wait()
        row = {'environment': str(environment), 'execution_exit_code': execution_code,
               'validation_exit_code': None, 'verified': False}
        if verify_package(environment) != digest:
            raise ValueError(f'Environment manifest changed during reload: {environment}')
        if (trial/'results.json').exists():
            command = [args.usd_python, str(validator), '--environment', str(environment),
                       '--reload-results', str(trial/'results.json'),
                       '--output', str(trial/'asset_validation.json'),
                       '--asset-search-path', args.asset_search_path]
            config = json.loads((environment/'config.json').read_text())
            if config['status'] == 'failed_feasibility':
                command.append('--expect-failure')
            with (output/f'{key}-validation.log').open('x') as log:
                row['validation_exit_code'] = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode
            validation_path = trial/'asset_validation.json'
            if validation_path.exists():
                validation = json.loads(validation_path.read_text())
                row['verified'] = validation.get('passed') is True and row['validation_exit_code'] == 0
                row['task_passed'] = validation.get('task_passed')
        results.append(row)
        # Separate numbered checkpoints: no successful/failed evidence overwritten.
        (output/f'checkpoint-{len(results):03d}.json').write_text(json.dumps(results, indent=2)+'\n')
        print('RELOAD_RESULT', json.dumps(row), flush=True)
    complete = all(row['verified'] for row in results)
    (output/'summary.json').write_text(json.dumps({'verified': complete, 'results': results}, indent=2)+'\n')
    print('RELOAD_BATCH_COMPLETE', complete, flush=True)
    return 0 if complete else 1


if __name__ == '__main__':
    sys.exit(main())
