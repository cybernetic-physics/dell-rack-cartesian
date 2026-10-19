"""Permanent command faults; real observations and all tool properties survive.

These test the normal controller's interlocks, not retention under a forced pull.
No body, joint state, collision, force limit, or observer value is overridden.
"""
import gzip
import hashlib
import json
import math

MODES = ('nominal', 'latch_disabled', 'grasp_open')


def validate_request(mode, role, cycles, occupied, load_threshold, force_trace):
    if mode is None:
        return
    if (mode not in MODES or role != 'control' or cycles != 1 or occupied
            or load_threshold is not None or force_trace):
        raise ValueError('Actuator controls require a separate one-cycle nominal condition')


class ActuatorControl:
    def __init__(self, gripper, mode):
        if mode not in MODES:
            raise ValueError(mode)
        self.gripper = gripper
        self.mode = mode
        self.time = 0.
        self.phase = 'initialize'
        self.events = []

    def __getattr__(self, name):
        # Preserve compliant_seating, offset, durations, optional step, etc.
        return getattr(self.gripper, name)

    def _deliver(self, name, requested, disabled):
        delivered = False if disabled else requested
        self.events.append({'time_s': self.time, 'phase': self.phase,
                            'command': name, 'requested': requested,
                            'delivered': delivered, 'suppressed': requested and disabled})
        return getattr(self.gripper, name)(delivered)

    def grasp(self, closed):
        return self._deliver('grasp', closed, self.mode == 'grasp_open')

    def press_latch(self, pressed):
        return self._deliver('press_latch', pressed, self.mode == 'latch_disabled')


def summarize(mode, samples, events, result):
    """Recomputable gates, deliberately distinct from ordinary task success."""
    if mode not in MODES:
        raise ValueError(mode)
    initial = result.get('measured_initial_pose', {}).get('position')
    phases = [s['phase'] for s in samples]
    blocking_phase = {'latch_disabled': 'release_latch', 'grasp_open': 'grasp'}.get(mode)
    blocked = [s for s in samples if s['phase'] == blocking_phase]
    suppressed = [e for e in events if e['suppressed']]
    dt = result['physics_dt']
    finite = all(math.isfinite(v) for s in samples for v in
                 [s['time_s'], s['aperture_m'], s['latch_target_m'], s['depth_m'],
                  *s['plug_position_m'], *s['tcp_m']])
    checks = {
        'timed_trial_started': result.get('timed_trial_started') is True,
        'initial_retained_without_hand': result.get('initial_retained_without_hand') is True,
        'initialization_helpers_disabled': bool(samples) and all(s['helpers_disabled'] for s in samples),
        'finite_samples': bool(samples) and finite,
        'contiguous_physics_steps': bool(samples) and all(
            abs(s['time_s'] - (i + 1) * dt) < 1e-7 for i, s in enumerate(samples)),
        'final_topology_intact': result.get('topology_audit', {}).get('passed') is True,
        'carrier_gates_pass': bool(result.get('service_carrier_checks')) and all(result['service_carrier_checks'].values()),
        'no_contact_reporting_errors': result.get('actuator_contact_reporting_errors') == [],
        'no_runner_exception': not result.get('failure_stage'),
        'separate_from_reliability': result.get('randomized_reliability_sample') is False,
    }
    displacement = max((abs(s['plug_position_m'][1] - initial[1]) for s in samples), default=0.) if initial else None
    if mode == 'nominal':
        checks.update(task_completed=result.get('passed') is True,
                      no_commands_suppressed=not suppressed,
                      full_sequence_observed=all(p in phases for p in
                          ('grasp', 'release_latch', 'withdraw', 'insert', 'release_gripper', 'park')),
                      retained_after_opening=bool(samples) and samples[-1]['retained'])
    else:
        checks.update(task_failed_as_expected=result.get('passed') is False and bool(result.get('error')),
                      fault_exercised_at_least_three_times=len(suppressed) >= 3,
                      bounded_retries_exhausted=len(result.get('recoveries', [])) == 2,
                      stopped_in_expected_phase=result.get('actuator_final_phase') == blocking_phase,
                      blocking_phase_observed=bool(blocked),
                      no_withdrawal_command='withdraw' not in phases,
                      no_unplug_success=result.get('unplug_success') is False,
                      housing_stayed_within_1mm_axially=displacement is not None and displacement < .001,
                      housing_never_extracted=bool(samples) and all(s['depth_m'] >= .0103 for s in samples),
                      final_retained=bool(samples) and samples[-1]['retained'])
        if mode == 'latch_disabled':
            checks.update(latch_drive_target_retracted=bool(blocked) and all(abs(s['latch_target_m']) < 1e-12 for s in blocked),
                          hook_never_clear_while_release_requested=bool(blocked) and not any(s['hook_clear'] for s in blocked))
        else:
            checks['open_aperture_observed_during_grasp'] = bool(blocked) and all(s['aperture_m'] >= .013 for s in blocked)
    return {'schema': 'actuator_interlock_control_v1', 'mode': mode,
            'passed': all(checks.values()), 'checks': checks, 'sample_count': len(samples),
            'sample_hz': round(1 / dt), 'suppressed_command_count': len(suppressed),
            'maximum_absolute_axial_displacement_m': displacement,
            'blocked_phase_min_aperture_m': min((s['aperture_m'] for s in blocked), default=None),
            'scope': 'Normal-controller actuator-disabled interlock test; no forced withdrawal, force-capacity, or open-grasp transport claim'}


class ActuatorTrace:
    def __init__(self, path):
        self.path = path
        self.samples = []

    def sample(self, time, phase, gripper, observer, robot, stage, drives):
        position, _ = observer.pose()
        self.samples.append({'time_s': time, 'phase': phase,
            'plug_position_m': list(position), 'tcp_m': list(robot.tcp()),
            'aperture_m': gripper.aperture(),
            'latch_target_m': drives['latch'].GetTargetPositionAttr().Get(),
            'depth_m': observer.metrics['depth_m'], 'hook_clear': observer.metrics['hook_clear'],
            'retained': observer.connected_port == 0 and observer.metrics.get('hook_behind_lip', False),
            'helpers_disabled': all(not stage.GetPrimAtPath(p).IsActive() for p in
                ('/World/HandDrive', '/World/ClipPressSlide', '/World/ClipPress'))})

    def close(self, mode, events, result):
        with gzip.open(self.path, 'xt') as stream:
            for sample in self.samples:
                stream.write(json.dumps(sample, allow_nan=False) + '\n')
        summary = summarize(mode, self.samples, events, result)
        summary['trace_sha256'] = hashlib.sha256(self.path.read_bytes()).hexdigest()
        summary['events'] = events
        return summary
