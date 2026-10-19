import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from rack_robotics.benchmarking.actuator_controls import ActuatorControl, summarize, validate_request
from rack_robotics.benchmarking.spec import control
from rack_robotics.scripts.screen_actuator_controls import verify_case


class Tool:
    compliant_seating = True
    approach_offset = (.001, 0., 0.)
    grasp_duration = 1.4

    def __init__(self):
        self.commands = []

    def grasp(self, value): self.commands.append(('grasp', value))
    def press_latch(self, value): self.commands.append(('latch', value))
    def aperture(self): return .016
    def step(self, dt): self.commands.append(('step', dt))


class ActuatorControlsTest(unittest.TestCase):
    def test_permanent_latch_suppression_preserves_real_tool(self):
        tool = Tool(); wrapper = ActuatorControl(tool, 'latch_disabled')
        for _ in range(3): wrapper.press_latch(True)
        wrapper.grasp(True); wrapper.step(.002)
        self.assertEqual(tool.commands, [('latch', False)]*3+[('grasp', True), ('step', .002)])
        self.assertTrue(wrapper.compliant_seating)
        self.assertEqual(wrapper.approach_offset, tool.approach_offset)
        self.assertEqual(wrapper.grasp_duration, 1.4)
        self.assertEqual(wrapper.aperture(), .016)
        self.assertEqual(sum(e['suppressed'] for e in wrapper.events), 3)

    def test_open_grasp_does_not_disable_latch(self):
        tool = Tool(); wrapper = ActuatorControl(tool, 'grasp_open')
        wrapper.grasp(True); wrapper.grasp(False); wrapper.press_latch(True)
        self.assertEqual(tool.commands, [('grasp', False), ('grasp', False), ('latch', True)])

    def test_nominal_delivers_identical_commands(self):
        tool = Tool(); wrapper = ActuatorControl(tool, 'nominal')
        wrapper.grasp(True); wrapper.press_latch(True)
        self.assertEqual(tool.commands, [('grasp', True), ('latch', True)])
        self.assertFalse(any(e['suppressed'] for e in wrapper.events))

    def test_diagnostics_cannot_enter_randomized_or_combined_protocol(self):
        validate_request('latch_disabled', 'control', 1, False, None, False)
        for args in [('bad', 'control', 1, False, None, False),
                     ('nominal', 'randomized', 1, False, None, False),
                     ('nominal', 'control', 3, False, None, False),
                     ('nominal', 'control', 1, True, None, False),
                     ('nominal', 'control', 1, False, 5., False),
                     ('nominal', 'control', 1, False, None, True)]:
            with self.assertRaises(ValueError): validate_request(*args)

    def evidence(self):
        result = dict(physics_dt=.002, timed_trial_started=True, initial_retained_without_hand=True,
                      topology_audit={'passed': True}, service_carrier_checks={'ok': True},
                      actuator_contact_reporting_errors=[], randomized_reliability_sample=False,
                      measured_initial_pose={'position': [0., .4, 1.]}, passed=False,
                      error='Latch release timed out', recoveries=[{}, {}],
                      actuator_final_phase='release_latch', unplug_success=False)
        samples = [dict(time_s=.002*(i+1), phase='release_latch', aperture_m=.012,
                        latch_target_m=0., depth_m=.0108, plug_position_m=[0., .4, 1.],
                        tcp_m=[0., .4, 1.], helpers_disabled=True, hook_clear=False,
                        retained=True) for i in range(3)]
        tool = ActuatorControl(Tool(), 'latch_disabled')
        for _ in range(3): tool.press_latch(True)
        return samples, tool.events, result

    def test_expected_task_failure_is_separate_diagnostic_pass(self):
        samples, events, result = self.evidence()
        self.assertTrue(summarize('latch_disabled', samples, events, result)['passed'])
        self.assertFalse(result['passed'])

    def test_failure_alone_does_not_prove_interlock(self):
        samples, events, result = self.evidence()
        for key, value in [('failure_stage', 'task_exception'), ('initial_retained_without_hand', False),
                           ('actuator_final_phase', 'approach'), ('recoveries', []),
                           ('actuator_contact_reporting_errors', ['missing']), ('unplug_success', True)]:
            changed = dict(result, **{key: value})
            self.assertFalse(summarize('latch_disabled', samples, events, changed)['passed'], key)
        self.assertFalse(summarize('latch_disabled', samples, [], result)['passed'])

    def test_physical_counterevidence_fails_diagnostic(self):
        samples, events, result = self.evidence()
        for key, value in [('depth_m', 0.), ('latch_target_m', .005), ('hook_clear', True),
                           ('helpers_disabled', False), ('retained', False), ('time_s', .5),
                           ('plug_position_m', [0., .41, 1.]), ('aperture_m', float('nan'))]:
            changed = copy.deepcopy(samples); changed[-1][key] = value
            self.assertFalse(summarize('latch_disabled', changed, events, result)['passed'], key)

    def test_verifier_binds_raw_trace_sources_and_verdict(self):
        samples, events, result = self.evidence()
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            result.update(environment_manifest_sha256='environment', condition=control(),
                          runner='actuator_interlock_diagnostic_v1', actuator_control='latch_disabled')
            trace = directory/'actuator_trace.jsonl.gz'
            with gzip.open(trace, 'wt') as stream:
                for row in samples: stream.write(json.dumps(row)+'\n')
            result['actuator_interlock'] = dict(summarize('latch_disabled', samples, events, result),
                events=events, trace_sha256=hashlib.sha256(trace.read_bytes()).hexdigest())
            source = directory/'source.py'; source.write_text('# Unit-test source fixture\n')
            (directory/'source_manifest.json').write_text(json.dumps({'source.py': hashlib.sha256(source.read_bytes()).hexdigest()}))
            (directory/'contacts.json').write_text(json.dumps({'reporting_errors': []}))
            path = directory/'results.json'; path.write_text(json.dumps(result))
            self.assertTrue(verify_case(directory, 'environment', 'latch_disabled')['diagnostic_passed'])
            with self.assertRaises(ValueError): verify_case(directory, 'other', 'latch_disabled')
            with self.assertRaises(ValueError): verify_case(directory, 'environment', 'grasp_open')
            result['actuator_interlock']['passed'] = False
            path.write_text(json.dumps(result))
            with self.assertRaises(ValueError): verify_case(directory, 'environment', 'latch_disabled')
            result['actuator_interlock']['passed'] = True
            path.write_text(json.dumps(result))
            trace.write_bytes(trace.read_bytes()+b'changed')
            with self.assertRaises(ValueError): verify_case(directory, 'environment', 'latch_disabled')
            source.write_text('# Changed source\n')
            with self.assertRaises(ValueError): verify_case(directory, 'environment', 'latch_disabled')


if __name__ == '__main__': unittest.main()
