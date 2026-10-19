"""Paired occupied-neighbor diagnostics, deliberately separate from reliability.

Freezes the common harness and conditions before launching fresh Isaac sessions.
Every declared case is retained, including initialization and task failures.
New output directories only; no implicit retries or process timeouts.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time

from evaluate_all import checked_result

COMMON_HARNESS_FILES=(('controllers/rj45_task.py','task.py'),
    ('controllers/connector_observer.py','observer.py'),('contacts.py','contacts.py'),
    ('recording.py','recording.py'),('integrity.py','integrity.py'),
    ('experiment_timing.py','timing.py'),('carrier_validation.py','carrier_validation.py'))


def freeze_harness(root,frozen):
    """Include the timing and startup gates required by the current runner."""
    shutil.copytree(root/'rack_robotics/benchmarking',frozen/'benchmarking',
                    ignore=shutil.ignore_patterns('__pycache__'))
    for source,target in COMMON_HARNESS_FILES:
        shutil.copy2(root/'rack_robotics'/source,frozen/'benchmarking'/target)
    for name in ('run_benchmark_trial.py','evaluate_all.py','screen_occupied_ports.py'):
        shutil.copy2(root/'rack_robotics/scripts'/name,frozen/name)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_diagnostic(result):
    if (result.get('fixture') != 'occupied_neighbors_v1'
            or result.get('randomized_reliability_sample') is not False):
        raise ValueError('Not an excluded occupied-neighbor diagnostic')
    neighbor = result.get('occupied_neighbors', {})
    expected = bool(result['passed'] and result.get('timed_trial_started')
                    and neighbor.get('metric_interval') == 'timed_robotic_trial'
                    and neighbor.get('fixture_stable') is True
                    and neighbor.get('no_reported_robot_neighbor_contact') is True
                    and neighbor.get('contact_reporting_errors') == [])
    if result.get('crowded_port_clearance_passed', False) != expected:
        raise ValueError('Clearance verdict does not match recorded evidence')
    return {'task_passed': result['passed'], 'clearance_passed': expected,
            'timed_trial_started': result.get('timed_trial_started', False),
            'fixture_stable': neighbor.get('fixture_stable'),
            'robot_neighbor_contact_pair_count': len(neighbor.get('robot_neighbor_contact_pairs', [])),
            'maximum_neighbor_cable_gap_m': neighbor.get('maximum_cable_joint_gap_m'),
            'error': result.get('error')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--conditions', default='trial-000,trial-001,trial-002,trial-003,trial-004')
    parser.add_argument('--designs', default='AA,AC,BA,BC,CA,CC,AB,CB')
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--isaac-python', type=Path, default=Path('/isaac-sim/python.sh'))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    plan = json.loads(args.plan.read_text())
    designs = args.designs.split(','); names = args.conditions.split(',')
    if len(set(designs)) != len(designs) or len(set(names)) != len(names):
        raise ValueError('Duplicate design or condition')
    for design in designs:
        entry = plan['environments'][design]
        if sha(root/entry['environment_relative_to_project']/'manifest.json') != entry['manifest_sha256']:
            raise ValueError('Changed environment: '+design)
    for name in names:
        if sha(args.plan.parent/(name+'.json')) != plan['condition_sha256'][name+'.json']:
            raise ValueError('Changed condition: '+name)
    if not args.isaac_python.is_file(): raise ValueError('Missing Isaac launcher')
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    frozen = output/'harness'
    freeze_harness(root,frozen)
    shutil.copytree(args.plan.parent, output/'plan')
    hashes = {str(p.relative_to(output)): sha(p) for p in frozen.rglob('*.py')}
    manifest = {'schema': 'occupied_neighbor_screen_v1', 'designs': designs,
                'conditions': names, 'plan_sha256': sha(args.plan), 'harness_sha256': hashes,
                'created_utc_epoch': time.time(), 'randomized_reliability_sample': False,
                'scope': 'Restrained adjacent housings and free-ended cables; no all-row, retention-force or tension certification'}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    state = {'complete': False, 'cases': {d+'/'+n: {'status': 'pending'} for d in designs for n in names}}
    mutex = threading.Lock()

    def save():
        temporary = output/'state.tmp'
        temporary.write_text(json.dumps(state, indent=2)+'\n')
        temporary.replace(output/'state.json')

    save()

    def run(key):
        design, name = key.split('/'); destination = output/design/name
        destination.parent.mkdir(exist_ok=True)
        entry = plan['environments'][design]
        command = [str(args.isaac_python), '-u', str(frozen/'run_benchmark_trial.py'),
                   '--environment', str(root/entry['environment_relative_to_project']),
                   '--condition', str(output/'plan'/(name+'.json')), '--output', str(destination),
                   '--occupied-neighbors', '--allow-root']
        record = state['cases'][key]
        with destination.with_suffix('.log').open('xb') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            with mutex:
                record.update(status='running', pid=process.pid, command=command); save()
            code = process.wait()
        with mutex:
            record.update(exit_code=code, finished_utc_epoch=time.time())
            try:
                result = checked_result(destination, json.loads((output/'plan'/(name+'.json')).read_text()),
                                        entry['manifest_sha256'])
                record.update(validate_diagnostic(result))
                record.update(status='finished', results_sha256=sha(destination/'results.json'))
            except (ValueError, OSError, KeyError) as error:
                record.update(status='invalid_or_missing_result', evidence_error=str(error))
            save()
            print('NEIGHBOR_CASE', key, record['status'], record.get('clearance_passed'), flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run, list(state['cases'])))
    if any(sha(output/name) != digest for name, digest in hashes.items()):
        raise ValueError('Frozen harness changed during screen')
    state['complete'] = all(r['status'] == 'finished' for r in state['cases'].values())
    save()
    print('NEIGHBOR_SCREEN_COMPLETE', state['complete'], flush=True)
    if not state['complete']: raise SystemExit(1)


if __name__ == '__main__': main()
