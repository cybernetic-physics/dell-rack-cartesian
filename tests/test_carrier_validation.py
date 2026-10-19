import unittest
from rack_robotics.carrier_validation import carrier_integrity_checks


class CarrierValidationTest(unittest.TestCase):
    def sample(self,**changes):
        s={'maximum_anchor_gap_m':.00003,'minimum_hinge_deg':-.7,
           'maximum_hinge_deg':30.3,'errors':[]}
        s.update(changes);return s

    def test_accepts_only_when_both_intervals_pass(self):
        self.assertTrue(all(carrier_integrity_checks([self.sample()],[self.sample()]).values()))

    def test_cannot_hide_startup_violation_behind_clean_task(self):
        checks=carrier_integrity_checks([self.sample()],[self.sample(minimum_hinge_deg=-1.4935)])
        self.assertTrue(checks['sampled_hinge_limits_within_one_degree'])
        self.assertFalse(checks['startup_sampled_hinge_limits_within_one_degree'])
        self.assertFalse(all(checks.values()))

    def test_missing_nonfinite_and_inconsistent_samples_fail(self):
        for samples in ([],[self.sample(maximum_anchor_gap_m=float('nan'))],
                        [self.sample(errors=['bad'])],[self.sample(minimum_hinge_deg=31)],
                        [self.sample(maximum_anchor_gap_m=-.001)]):
            self.assertFalse(all(carrier_integrity_checks(samples,[self.sample()]).values()))
            self.assertFalse(all(carrier_integrity_checks([self.sample()],samples).values()))
