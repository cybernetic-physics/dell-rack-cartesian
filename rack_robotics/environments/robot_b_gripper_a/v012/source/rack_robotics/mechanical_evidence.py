"""Bind read-only mechanical screens to their saved scene and measured motion."""
import hashlib
import json


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_identity(properties, attempt, environment):
    identity = sha(environment/'manifest.json')
    if not properties.get('passed') or properties.get('environment_manifest_sha256') != identity:
        raise ValueError('Property query did not pass for this saved environment')
    manifest = json.loads((environment/'manifest.json').read_text())
    for name, digest in manifest['packaged_file_sha256'].items():
        path = (environment/name).resolve()
        if not path.is_relative_to(environment.resolve()) or sha(path) != digest:
            raise ValueError(f'Changed saved environment: {name}')
    result = json.loads((attempt/'results.json').read_text())
    if result.get('environment_manifest_sha256') == identity:
        return 'benchmark_environment_identity'
    # Development versions may contain their original failed trajectory instead
    # of a benchmark result. Accept only the actual immutable package, with both
    # files explicitly covered by its verified manifest. No arbitrary fallback.
    if (attempt.resolve() == environment.resolve()
            and {'trajectory.jsonl', 'results.json'} <= manifest['packaged_file_sha256'].keys()):
        return 'manifest_verified_packaged_trajectory'
    raise ValueError('Trajectory is not tied to this saved environment')
