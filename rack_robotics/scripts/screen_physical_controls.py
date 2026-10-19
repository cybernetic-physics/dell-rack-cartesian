"""Matched nominal and physical pull/open-transport challenges, separate from reliability.

New output only. Every declared case runs once in a fresh Isaac session. A failed
diagnostic remains evidence, never an automatic retry. No process timeout.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import threading
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from rack_robotics.benchmarking.physical_controls import MODES, PROTOCOL, summarize
from rack_robotics.benchmarking.spec import control


def suite_definition(suite):
    if suite == 'original':
        from rack_robotics.benchmarking import physical_controls as module
        return module, 'physical_challenge_protocol001.md'
    if suite == 'release':
        from rack_robotics.benchmarking import release_controls as module
        return module, 'matched_release_protocol001.md'
    raise ValueError('Unknown physical challenge suite')

DESIGNS = {'AA': 'robot_a_gripper_a/v016', 'BA': 'robot_b_gripper_a/v014',
           'CA': 'robot_c_gripper_a/v021', 'AC': 'robot_a_gripper_c/v005',
           'BC': 'robot_b_gripper_c/v004'}
COMMON = (('controllers/rj45_task.py', 'task.py'),
          ('controllers/connector_observer.py', 'observer.py'), ('contacts.py', 'contacts.py'),
          ('recording.py', 'recording.py'), ('integrity.py', 'integrity.py'),
          ('experiment_timing.py', 'timing.py'), ('carrier_validation.py', 'carrier_validation.py'))

# This exact frozen campaign001 runner checked its verdict after app.close().
# Installed Kit fast shutdown exits inside close(), yielding zero even on a
# failed diagnostic. Accept the completed evidence, never promote its verdict.
LEGACY_FAST_SHUTDOWN_RUNNER = '77d4ca701af7ed07d0f2693a1afb92d857897666dc3db67e91702edb40bdf7e6'


def process_exit_policy(exit_code, diagnostic_passed, runner_sha256):
    if type(exit_code) is not int or type(diagnostic_passed) is not bool:
        raise ValueError('Missing or malformed process/verdict evidence')
    if exit_code == (0 if diagnostic_passed else 1):
        return 'exit_matches_diagnostic'
    if (not diagnostic_passed and exit_code == 0
            and runner_sha256 == LEGACY_FAST_SHUTDOWN_RUNNER):
        return 'legacy_fast_shutdown_zero_on_failed_diagnostic'
    raise ValueError('Process exit does not match diagnostic verdict')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verdict_matches(actual, saved, allow_distance_roundoff=False):
    """Do not relax verdicts/gates; Python3.9/3.12 math.dist can differ by1 ULP."""
    if not allow_distance_roundoff: return actual == saved
    if {k:v for k,v in actual.items() if k!='metrics'} != {k:v for k,v in saved.items() if k!='metrics'}:
        return False
    a, b = actual.get('metrics',{}), saved.get('metrics',{})
    if a.keys() != b.keys(): return False
    distances = {'maximum_tool_displacement_m','minimum_housing_tool_separation_m'}
    for key in a:
        if a[key] == b[key]: continue
        if (key not in distances or type(a[key]) is not float or type(b[key]) is not float
                or not math.isfinite(a[key]) or not math.isfinite(b[key])
                or abs(a[key]-b[key]) > 4*max(math.ulp(a[key]),math.ulp(b[key]))):
            return False
    return True


def verify_case(directory, environment_digest, mode):
    module, _ = suite_definition('original' if mode in MODES else 'release')
    if mode not in module.MODES: raise ValueError('Unknown physical challenge mode')
    result = json.loads((directory/'results.json').read_text())
    if (result.get('environment_manifest_sha256') != environment_digest
            or result.get('condition') != control()
            or result.get('runner') != 'physical_challenge_diagnostic_v1'
            or result.get('physical_control') != mode
            or result.get('physical_protocol') != module.PROTOCOL
            or result.get('randomized_reliability_sample') is not False):
        raise ValueError('Diagnostic provenance mismatch')
    sources = json.loads((directory/'source_manifest.json').read_text())
    if not sources:
        raise ValueError('Missing source manifest')
    for name, digest in sources.items():
        path = (directory/name).resolve()
        if directory.resolve() not in path.parents or sha(path) != digest:
            raise ValueError('Changed or escaped source: '+name)
    trace_path = directory/'physical_trace.jsonl.gz'
    saved = result['physical_challenge']
    if sha(trace_path) != saved['trace_sha256']:
        raise ValueError('Actuator trace changed')
    with gzip.open(trace_path, 'rt') as stream:
        samples = [json.loads(line) for line in stream]
    actual = module.summarize(mode, samples, result)
    if not verdict_matches(actual, {k:v for k,v in saved.items() if k!='trace_sha256'},
                           allow_distance_roundoff=mode in ('released_hold','released_transport')):
        raise ValueError('Diagnostic verdict differs from step-by-step evidence')
    contacts = json.loads((directory/'contacts.json').read_text())
    if any(e not in result['physical_contact_reporting_errors'] for e in contacts['reporting_errors']):
        raise ValueError('Contact-report status mismatch')
    return {'diagnostic_passed': actual['passed'], 'task_passed': result['passed'],
            'task_error': result.get('error'), 'duration_s': result.get('cycle_time_s'),
            'checks': actual['checks'], 'results_sha256': sha(directory/'results.json'),
            'trace_sha256': saved['trace_sha256']}


def verify_campaign(output, references=None):
    manifest = json.loads((output/'manifest.json').read_text())
    state = json.loads((output/'state.json').read_text())
    module, _ = suite_definition(manifest.get('suite','original'))
    if manifest.get('protocol') != module.PROTOCOL or manifest.get('modes') != list(module.MODES):
        raise ValueError('Changed physical challenge protocol')
    if state.get('complete') is not True:
        raise ValueError('Campaign is not terminal with every result collected')
    for name, digest in manifest['frozen_sha256'].items():
        if sha(output/name) != digest:
            raise ValueError('Frozen campaign source/condition changed: '+name)
    checks = {}
    for design in manifest['designs']:
        for mode in module.MODES:
            directory = output/design/mode
            checks[design+'/'+mode] = verify_case(directory,
                manifest['environments'][design]['manifest_sha256'], mode)
            record = state['cases'][design+'/'+mode]
            if (record.get('status') != 'finished'
                    or record.get('results_sha256') != checks[design+'/'+mode]['results_sha256']):
                raise ValueError('Process/result completion evidence mismatch: '+design+'/'+mode)
            for name, digest in manifest['frozen_sha256'].items():
                if name.startswith('harness/') and sha(directory/name) != digest:
                    raise ValueError('Trial harness differs from predeclared campaign: '+design+'/'+mode+'/'+name)
            checks[design+'/'+mode].update(process_exit_code=record.get('exit_code'),
                process_exit_policy=process_exit_policy(record.get('exit_code'),
                    checks[design+'/'+mode]['diagnostic_passed'],
                    manifest['frozen_sha256']['harness/run_benchmark_trial.py']))
    nominal_comparisons = {}
    if references and 'nominal' in module.MODES:
        from rack_robotics.scripts.summarize_cable_force import compare_trajectory
        for design in manifest['designs']:
            nominal_comparisons[design] = compare_trajectory(output/design/'nominal/trajectory.jsonl',
                references/('continuous-'+design.lower()+'001')/'trajectory.jsonl',
                checks[design+'/nominal']['duration_s'])
    pairs = {}
    if manifest.get('suite') == 'release':
        for design in manifest['designs']:
            traces = []
            for mode in module.MODES:
                with gzip.open(output/design/mode/'physical_trace.jsonl.gz','rt') as stream:
                    traces.append([json.loads(line) for line in stream])
            pairs[design] = module.compare_pair(*traces)
    report = {'schema': 'physical_challenge_verification_v1', 'cases': checks,
            'passed': all(c['diagnostic_passed'] for c in checks.values())
                      and all(p['no_measurable_transport_effect'] for p in pairs.values()),
            'campaign_manifest_sha256': sha(output/'manifest.json'),
            'verification_source_sha256': sha(Path(__file__)),
            'nominal_recorded_motion_comparison': nominal_comparisons,
            'scope': 'Bounded current-tool physical challenges; not hardware ratings or randomized samples'}
    if pairs:
        report['matched_release_comparisons'] = pairs
        report['numeric_verification_policy'] = 'All gates/verdicts exact; two math.dist metrics allow at most4 ULP across Python3.9/3.12'
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--designs', default='AA,BA,CA,AC,BC')
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--suite', choices=('original','release'), default='original')
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
    module, protocol_document = suite_definition(args.suite)
    from rack_robotics.benchmarking.cable_force_trace import validate_calibration
    calibration_path=ROOT/'rack_robotics/experiments/cable-balance-probe003/results.json'
    validate_calibration(json.loads(calibration_path.read_text()),
                         sha(ROOT/'rack_robotics/benchmarking/cable_balance.py'),1/480)
    shutil.copy2(calibration_path,output/'contact_convention_calibration.json')
    shutil.copy2(ROOT/'rack_robotics/research'/protocol_document,output/'protocol.md')
    frozen = output/'harness'
    shutil.copytree(ROOT/'rack_robotics/benchmarking', frozen/'benchmarking',
                    ignore=shutil.ignore_patterns('__pycache__'))
    for source, target in COMMON:
        shutil.copy2(ROOT/'rack_robotics'/source, frozen/'benchmarking'/target)
    shutil.copy2(ROOT/'rack_robotics/scripts/run_benchmark_trial.py', frozen/'run_benchmark_trial.py')
    shutil.copy2(__file__, output/'screen_source.py')
    (output/'condition.json').write_text(json.dumps(control(), indent=2)+'\n')
    manifest = {'schema': 'physical_challenge_campaign_v1', 'designs': designs,
        'suite': args.suite, 'modes': list(module.MODES), 'protocol': module.PROTOCOL, 'randomized_reliability_sample': False,
        'created_utc_epoch': time.time(),
        'environments': {d: {'path': str(ROOT/'rack_robotics/environments'/DESIGNS[d]),
            'manifest_sha256': sha(ROOT/'rack_robotics/environments'/DESIGNS[d]/'manifest.json')} for d in designs},
        'frozen_sha256': {str(p.relative_to(output)): sha(p) for p in output.rglob('*') if p.is_file()}}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    state = {'complete': False, 'cases': {d+'/'+m: {'status': 'pending'} for d in designs for m in module.MODES}}
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
                   '--physical-control', mode, '--allow-root']
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
            print('PHYSICAL_CHALLENGE', key, record['status'], record.get('diagnostic_passed'), flush=True)

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run, state['cases']))
    state['complete'] = all(r['status'] == 'finished' for r in state['cases'].values())
    save()
    print('PHYSICAL_CHALLENGE_CAMPAIGN_COMPLETE', state['complete'], flush=True)


if __name__ == '__main__':
    main()
