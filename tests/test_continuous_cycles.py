import unittest

from rack_robotics.benchmarking.repetition import CycleLedger, validate_request


class ContinuousCycleTests(unittest.TestCase):
    def setUp(self):
        self.state={'retained':True,'initialization_helpers_disabled':True,'pose':[1.,2.,3.]}
        self.outcome={'done':True,'error':None,'duration_s':2.,'unplug_success':True,'replug_success':True}

    def test_requires_all_requested_cycles(self):
        ledger=CycleLedger(2)
        ledger.begin(self.state);ledger.finish(self.outcome,self.state)
        self.assertFalse(ledger.passed)
        ledger.begin(self.state);ledger.finish(self.outcome,self.state)
        self.assertTrue(ledger.passed)
        self.assertEqual(ledger.elapsed,4.)
        self.assertEqual(ledger.records[1]['start_time_s'],2.)

    def test_records_measured_boundaries_without_mutating_or_resetting_them(self):
        ledger=CycleLedger(2);ledger.begin(self.state)
        self.state['pose'][0]=4.
        ledger.finish(self.outcome,self.state)
        self.assertEqual(ledger.records[0]['initial_state']['pose'][0],1.)
        self.assertEqual(ledger.records[0]['final_state']['pose'][0],4.)
        self.assertEqual(self.state['pose'][0],4.)

    def test_retention_loss_stops_repetition(self):
        ledger=CycleLedger(2);ledger.begin(self.state)
        self.state['retained']=False
        self.assertFalse(ledger.finish(self.outcome,self.state)['passed'])
        with self.assertRaises(ValueError):ledger.begin(self.state)

    def test_no_fixture_help_between_cycles(self):
        ledger=CycleLedger(2)
        self.state['initialization_helpers_disabled']=False
        self.assertFalse(ledger.begin(self.state))
        self.assertFalse(ledger.finish(self.outcome,self.state)['passed'])

    def test_task_failure_cannot_be_hidden_by_retained_final_pose(self):
        ledger=CycleLedger(2);ledger.begin(self.state)
        self.outcome.update(error='failed insertion',replug_success=False)
        self.assertFalse(ledger.finish(self.outcome,self.state)['passed'])
        self.assertFalse(ledger.passed)

    def test_repetition_cannot_enter_randomized_or_occupied_cohort(self):
        validate_request(1,'randomized',True)
        validate_request(3,'control')
        for n,role,occupied in [(2,'randomized',False),(2,'control',True),(0,'control',False),
                                (101,'control',False),(True,'control',False)]:
            with self.assertRaises(ValueError):validate_request(n,role,occupied)

    def test_order_and_invalid_durations_rejected(self):
        ledger=CycleLedger(2)
        with self.assertRaises(ValueError):ledger.finish(self.outcome,self.state)
        ledger.begin(self.state)
        with self.assertRaises(ValueError):ledger.begin(self.state)
        self.outcome['duration_s']=float('nan')
        with self.assertRaises(ValueError):ledger.finish(self.outcome,self.state)
