import unittest
from rack_robotics.benchmarking.cable_load import validate_request, CableLoadMonitor


class CableLoadTests(unittest.TestCase):
    def test_threshold_validation_and_cohort_exclusion(self):
        validate_request(None, 'randomized', 1, True)
        validate_request(1., 'control')
        for value in (0., -1., float('nan'), float('inf'), True):
            with self.assertRaises(ValueError): validate_request(value, 'control')
        for role, cycles, occupied in [('randomized', 1, False), ('control', 2, False), ('control', 1, True)]:
            with self.assertRaises(ValueError): validate_request(1., role, cycles, occupied)

    def monitor(self):
        monitor=CableLoadMonitor.__new__(CableLoadMonitor)
        monitor.threshold_n=1.;monitor.paths=['/World/Cable/Joint00']
        monitor.events=[];monitor.errors=[]
        return monitor

    def test_event_aborts_and_cannot_be_a_success(self):
        monitor=self.monitor();monitor.events=[{'joint':monitor.paths[0]}]
        with self.assertRaises(RuntimeError): monitor.assert_intact()
        self.assertFalse(monitor.report(True,1/30)['task_complete_without_threshold_event'])

    def test_reporting_error_cannot_be_a_pass(self):
        monitor=self.monitor();monitor.errors=['decode failed']
        with self.assertRaises(RuntimeError): monitor.assert_intact()
        self.assertFalse(monitor.report(True,1/30)['task_complete_without_threshold_event'])

    def test_incomplete_trial_cannot_bound_full_cycle(self):
        monitor=self.monitor();monitor.assert_intact()
        self.assertFalse(monitor.report(False,1/30)['task_complete_without_threshold_event'])
        self.assertTrue(monitor.report(True,1/30)['task_complete_without_threshold_event'])
