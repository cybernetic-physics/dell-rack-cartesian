"""Matched nominal / actuator-disabled controls, separate from reliability.

New output only. Every declared case runs once in a fresh Isaac session. A failed
diagnostic remains evidence, never an automatic retry. No process timeout.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from rack_robotics.benchmarking.actuator_controls import MODES, summarize
from rack_robotics.benchmarking.spec import control

DESIGNS = {'AA': 'robot_a_gripper_a/v016', 'BA': 'robot_b_gripper_a/v014',
           'CA': 'robot_c_gripper_a/v021', 'AC': 'robot_a_gripper_c/v005',
           'BC': 'robot_b_gripper_c/v004'}
COMMON = (('controllers/rj45_task.py', 'task.py'),
          ('controllers/connector_observer.py', 'observer.py'), ('contacts.py', 'contacts.py'),
          ('recording.py', 'recording.py'), ('integrity.py', 'integrity.py'),
          ('experiment_timing.py', 'timing.py'), ('carrier_validation.py', 'carrier_validation.py'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_case(directory, environment_digest, mode):
    result = json.loads((directory/'results.json').read_text())
    if (result.get('environment_manifest_sha256') != environment_digest
            or result.get('condition') != control()
            or result.get('runner') != 'actuator_interlock_diagnostic_v1'
            or result.get('actuator_control') != mode
            or result.get('randomized_reliability_sample') is not False):
        raise ValueError('Diagnostic provenance mismatch')
    sources = json.loads((directory/'source_manifest.json').read_text())
    if not sources:
        raise ValueError('Missing source manifest')
    for name, digest in sources.items():
        path = (directory/name).resolve()
        if directory.resolve() not in path.parents or sha(path) != digest:
            raise ValueError('Changed or escaped source: '+name)
    trace_path = directory/'actuator_trace.jsonl.gz'
    saved = result['actuator_interlock']
    if sha(trace_path) != saved['trace_sha256']:
        raise ValueError('Actuator trace changed')
    with gzip.open(trace_path, 'rt') as stream:
        samples = [json.loads(line) for line in stream]
    actual = summarize(mode, samples, saved['events'], result)
    if actual != {k: v for k, v in saved.items() if k not in ('events', 'trace_sha256')}:
        raise ValueError('Diagnostic verdict differs from step-by-step evidence')
    contacts = json.loads((directory/'contacts.json').read_text())
    if contacts['reporting_errors'] != result['actuator_contact_reporting_errors']:
        raise ValueError('Contact-report status mismatch')
    return {'diagnostic_passed': actual['passed'], 'task_passed': result['passed'],
            'task_error': result.get('error'), 'duration_s': result.get('cycle_time_s'),
            'checks': actual['checks'], 'results_sha256': sha(directory/'results.json'),
            'trace_sha256': saved['trace_sha256']}


def verify_campaign(output, references=None):
    manifest = json.loads((output/'manifest.json').read_text())
    state = json.loads((output/'state.json').read_text())
    if state.get('complete') is not True:
        raise ValueError('Campaign is not terminal with every result collected')
    for name, digest in manifest['frozen_sha256'].items():
        if sha(output/name) != digest:
            raise ValueError('Frozen campaign source/condition changed: '+name)
    checks = {}
    for design in manifest['designs']:
        for mode in MODES:
            directory = output/design/mode
            checks[design+'/'+mode] = verify_case(directory,
                manifest['environments'][design]['manifest_sha256'], mode)
            record = state['cases'][design+'/'+mode]
            if (record.get('status') != 'finished'
                    or record.get('exit_code') != (0 if checks[design+'/'+mode]['diagnostic_passed'] else 1)
                    or record.get('results_sha256') != checks[design+'/'+mode]['results_sha256']):
                raise ValueError('Process/result completion evidence mismatch: '+design+'/'+mode)
            for name, digest in manifest['frozen_sha256'].items():
                if name.startswith('harness/') and sha(directory/name) != digest:
                    raise ValueError('Trial harness differs from predeclared campaign: '+design+'/'+mode+'/'+name)
    nominal_comparisons = {}
    if references:
        from rack_robotics.scripts.summarize_cable_force import compare_trajectory
        for design in manifest['designs']:
            nominal_comparisons[design] = compare_trajectory(output/design/'nominal/trajectory.jsonl',
                references/('continuous-'+design.lower()+'001')/'trajectory.jsonl',
                checks[design+'/nominal']['duration_s'])
    return {'schema': 'actuator_interlock_verification_v1', 'cases': checks,
            'passed': all(c['diagnostic_passed'] for c in checks.values()),
            'campaign_manifest_sha256': sha(output/'manifest.json'),
            'verification_source_sha256': sha(Path(__file__)),
            'nominal_recorded_motion_comparison': nominal_comparisons,
            'scope': 'Normal-controller interlocks only; not forced-pull or open-grasp transport proof'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--designs', default='AA,BA,CA,AC,BC')
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--reference-experiments', type=Path,
                        help='Also require nominal recorded poses to match previous continuous first cycles')
    args = parser.parse_args()
    output = args.output.resolve()
    if args.verify_only:
        report = verify_campaign(output, args.reference_experiments)
        if args.report:
            with args.report.open('x') as stream:
                json.dump(report, stream, indent=2)
        print(json.dumps(report, indent=2))
        if not report['passed']:
            raise SystemExit(1)
        return
    designs = args.designs.split(',')
    if not designs or len(set(designs)) != len(designs) or any(d not in DESIGNS for d in designs):
        raise ValueError('Choose distinct current working designs')
    output.mkdir(parents=True, exist_ok=False)
    frozen = output/'harness'
    shutil.copytree(ROOT/'rack_robotics/benchmarking', frozen/'benchmarking',
                    ignore=shutil.ignore_patterns('__pycache__'))
    for source, target in COMMON:
        shutil.copy2(ROOT/'rack_robotics'/source, frozen/'benchmarking'/target)
    shutil.copy2(ROOT/'rack_robotics/scripts/run_benchmark_trial.py', frozen/'run_benchmark_trial.py')
    shutil.copy2(__file__, output/'screen_source.py')
    (output/'condition.json').write_text(json.dumps(control(), indent=2)+'\n')
    manifest = {'schema': 'actuator_interlock_campaign_v1', 'designs': designs,
        'modes': list(MODES), 'randomized_reliability_sample': False,
        'created_utc_epoch': time.time(),
        'environments': {d: {'path': str(ROOT/'rack_robotics/environments'/DESIGNS[d]),
            'manifest_sha256': sha(ROOT/'rack_robotics/environments'/DESIGNS[d]/'manifest.json')} for d in designs},
        'frozen_sha256': {str(p.relative_to(output)): sha(p) for p in output.rglob('*') if p.is_file()}}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    state = {'complete': False, 'cases': {d+'/'+m: {'status': 'pending'} for d in designs for m in MODES}}
    lock = threading.Lock()

    def save():
        (output/'state.tmp').write_text(json.dumps(state, indent=2)+'\n')
        (output/'state.tmp').replace(output/'state.json')

    save()

    def run(key):
        design, mode = key.split('/')
        destination = output/design/mode
        destination.parent.mkdir(exist_ok=True)
        command = ['/isaac-sim/python.sh', '-u', str(frozen/'run_benchmark_trial.py'),
                   '--environment', manifest['environments'][design]['path'],
                   '--condition', str(output/'condition.json'), '--output', str(destination),
                   '--actuator-control', mode, '--allow-root']
        record = state['cases'][key]
        with destination.with_suffix('.log').open('xb') as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
            with lock:
                record.update(status='running', pid=process.pid, command=command)
                save()
            code = process.wait()
        with lock:
            record.update(exit_code=code, finished_utc_epoch=time.time())
            try:
                record.update(verify_case(destination, manifest['environments'][design]['manifest_sha256'], mode))
                record.update(status='finished')
            except (ValueError, OSError, KeyError) as error:
                record.update(status='invalid_or_missing_result', evidence_error=str(error))
            save()
            print('ACTUATOR_CONTROL', key, record['status'], record.get('diagnostic_passed'), flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run, state['cases']))
    state['complete'] = all(r['status'] == 'finished' for r in state['cases'].values())
    save()
    print('ACTUATOR_CAMPAIGN_COMPLETE', state['complete'], flush=True)


if __name__ == '__main__':
    main()
