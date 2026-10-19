import unittest
from rack_robotics.benchmarking.metrics import trial_metrics,wilson,cable_displacement


class BenchmarkMetricsTests(unittest.TestCase):
    def test_verified_completion_requires_measured_admissible_initial_state(self):
        result={'passed':True,'initial_retained_without_hand':True,'timed_trial_started':True,
                'unplug_success':True,'replug_success':True,'topology_audit':{'passed':True}}
        self.assertFalse(trial_metrics(result)['complete_cycle'])
        result['measured_initial_pose']={'metrics':{'hook_behind_lip':True,'depth_m':.0106}}
        self.assertTrue(trial_metrics(result)['complete_cycle'])
        result['measured_initial_pose']['metrics']['hook_behind_lip']=False
        self.assertFalse(trial_metrics(result)['complete_cycle'])

    def test_unlatched_fixture_is_not_a_valid_robot_manipulation_trial(self):
        m=trial_metrics({'passed':False,'failure_stage':'initialization_exception'})
        self.assertTrue(m['fixture_failure'])
        self.assertFalse(m['admissible_initial_state'])

    def test_retention_lost_after_hand_release_is_a_fixture_failure(self):
        m=trial_metrics({'passed':False,'timed_trial_started':True,
            'initial_retained_without_hand':False,
            'measured_initial_pose':{'metrics':{'hook_behind_lip':False,'depth_m':.0106}}})
        self.assertTrue(m['fixture_failure'])
        self.assertFalse(m['admissible_initial_state'])

    def test_reported_pass_without_measured_cycle_is_not_verified(self):
        self.assertFalse(trial_metrics({'passed':True})['complete_cycle'])
        self.assertIsNone(trial_metrics({'passed':False})['robot_rack_contact_pair_count'])

    def test_missing_evidence_is_not_zero_error(self):
        m=trial_metrics({'passed':False})
        self.assertIsNone(m['final_angle_deg'])
        self.assertIsNone(m['cable_max_gap_m'])
        self.assertIsNone(m['contact_reporting_errors'])

    def test_wilson_interval_does_not_claim_certainty_from_ten_passes(self):
        lo,hi=wilson(10,10)
        self.assertGreater(lo,.72); self.assertLess(lo,.73)
        self.assertAlmostEqual(hi,1.)
        self.assertIsNone(wilson(0,0))
        with self.assertRaises(ValueError): wilson(11,10)

    def test_contacts_are_separated_from_intended_housing_grasp(self):
        c={'reporting_errors':[],'pairs':[
            {'colliders':['/World/Robot/LeftJaw/Pad','/World/Plug/Body'],'peak_pair_contact_force_n':10,'phase_peaks_n':{'grasp':10}},
            {'colliders':['/World/Robot/ToolMount/Cradle','/World/Rack/Post'],'peak_pair_contact_force_n':20,'phase_peaks_n':{'approach':20}}]}
        m=trial_metrics({},c)
        self.assertEqual(m['robot_rack_contact_pair_count'],1)
        self.assertEqual(m['robot_rack_peak_pair_estimate_n'],20)
        self.assertEqual(m['phase_peak_pair_contact_estimate_n']['grasp'],10)

    def test_cable_displacement_uses_measured_samples_only(self):
        h={'body_paths':['/World/Plug','/World/Cable/Link00']}
        rows=[{'poses':[[0,0,0],[1,2,3]]},{'poses':[[99,0,0],[1,2,3.5]]}]
        self.assertEqual(cable_displacement(h,rows)['max_segment_centre_displacement_m'],.5)
