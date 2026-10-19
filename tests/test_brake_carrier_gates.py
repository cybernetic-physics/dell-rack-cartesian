import unittest

from rack_robotics.carrier_validation import brake_carrier_checks


class BrakeCarrierGateTest(unittest.TestCase):
    def sample(self, phase, **overrides):
        return dict(phase=phase, errors=[], maximum_anchor_gap_m=.00001,
                    minimum_hinge_deg=0., maximum_hinge_deg=30., **overrides)

    def test_both_intervals_required(self):
        initial=self.sample('initial_settle')
        task=self.sample('motor_power_off_brakes_engage')
        self.assertTrue(all(brake_carrier_checks([initial,task]).values()))
        for rows in ([],[initial],[task]):
            self.assertFalse(all(brake_carrier_checks(rows).values()))

    def test_startup_hinge_violation_is_not_discarded(self):
        initial=self.sample('initial_settle')
        initial['minimum_hinge_deg']=-1.01
        checks=brake_carrier_checks([initial,self.sample('powered_hold')])
        self.assertFalse(checks['startup_sampled_hinge_limits_within_one_degree'])
        self.assertTrue(checks['sampled_hinge_limits_within_one_degree'])

    def test_nonfinite_gap_fails(self):
        task=self.sample('powered_recovery_hold')
        task['maximum_anchor_gap_m']=float('nan')
        checks=brake_carrier_checks([self.sample('initial_settle'),task])
        self.assertFalse(checks['finite_state'])


if __name__=='__main__': unittest.main()
