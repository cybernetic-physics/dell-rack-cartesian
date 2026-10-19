"""Summarize verified nominal cable diagnostics without rescoring reliability.

Thresholds describe exposure durations, not manufacturer-approved safe loads.
Recorded-trajectory equality is a 30 Hz observation, not every-step equality.
"""
import argparse
import gzip
import json
from pathlib import Path

from rack_robotics.scripts.verify_cable_force import sha, verify


DESIGNS = ('AA', 'BA', 'CA', 'AC', 'BC')


def exposure(rows, dt, thresholds=(1., 5., 10.)):
    stats = {str(t): {'steps': 0, 'longest_consecutive_steps': 0} for t in thresholds}
    runs = {str(t): 0 for t in thresholds}
    for row in rows:
        peak = max(row['axial_force_n'])
        for t in thresholds:
            key = str(t)
            if peak > t:
                stats[key]['steps'] += 1
                runs[key] += 1
                stats[key]['longest_consecutive_steps'] = max(stats[key]['longest_consecutive_steps'], runs[key])
            else:
                runs[key] = 0
    for value in stats.values():
        value['total_duration_s'] = value['steps'] * dt
        value['longest_duration_s'] = value['longest_consecutive_steps'] * dt
    return stats


def compare_trajectory(measured, reference, end_time):
    count = 0
    with measured.open() as first, reference.open() as second:
        header = json.loads(next(first))
        if header != json.loads(next(second)):
            raise ValueError('Trajectory body order, format or rate differs')
        for line in first:
            row = json.loads(line)
            other = next(second, None)
            if other is None or row != json.loads(other) or row['time'] > end_time:
                raise ValueError('Recorded nominal trajectory differs')
            count += 1
        following = next(second, None)
        if following is not None and json.loads(following)['time'] <= end_time:
            raise ValueError('Measured trajectory omits part of first cycle')
    if count < 2:
        raise ValueError('Insufficient recorded trajectory')
    return {'equal_recorded_frames': count, 'body_count': len(header['body_paths']),
            'fps': header['fps'], 'measured_sha256': sha(measured), 'reference_sha256': sha(reference),
            'scope': 'Exact recorded frame records for first continuous cycle, not every physics-step pose'}


def summarize(root):
    products = {}
    for label in DESIGNS:
        directory = root / ('cable-force-' + label.lower() + '001')
        reference = root / ('continuous-' + label.lower() + '001')
        verified = verify(directory)
        result = json.loads((directory / 'results.json').read_text())
        boundaries = json.loads((reference / 'cycle_boundaries.json').read_text())
        if not result['passed'] or not boundaries[0]['done'] or boundaries[0]['end_time_s'] != result['cycle_time_s']:
            raise ValueError('Not a completed matching nominal cycle: ' + label)
        summary = result['cable_momentum']
        with gzip.open(directory / 'cable_force_trace.jsonl.gz', 'rt') as stream:
            header = json.loads(next(stream))
            durations = exposure((json.loads(line) for line in stream), header['physics_dt_s'])
        products[label] = {
            'directory': directory.name, 'verification': verified,
            'cycle_time_s': result['cycle_time_s'], 'peak_tension': summary['peak_tension'],
            'plug_joint_peak_tension_n': summary['per_joint_peak_tension_n'][0],
            'peak_resultant': summary['peak_resultant'], 'exposure_above_n': durations,
            'trajectory_comparison': compare_trajectory(directory / 'trajectory.jsonl', reference / 'trajectory.jsonl', result['cycle_time_s']),
            'continuous_boundaries_sha256': sha(reference / 'cycle_boundaries.json'),
        }
    return {'schema': 'nominal_cable_force_comparison_v1', 'designs': products,
            'randomized_reliability_samples_added': 0, 'historical_scores_changed': False,
            'thresholds_are_hardware_safety_limits': False, 'source_sha256': sha(Path(__file__)),
            'scope': __doc__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--experiments', type=Path, default=Path('rack_robotics/experiments'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = summarize(args.experiments)
    with args.output.open('x') as target:
        target.write(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
