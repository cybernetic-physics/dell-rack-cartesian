import json,tempfile,unittest
from pathlib import Path
from rack_robotics.scripts.summarize_trials import summarize


class TrialSummaryTests(unittest.TestCase):
    def test_retained_label_does_not_hide_final_alignment(self):
        row=self.summarize_result({'robot':'A','passed':True,
            'trace':[{'depth_m':.011,'lateral_m':.00045,'angle_deg':4.4,'hook_behind_lip':True}],
            'physics_hz':480})
        self.assertEqual(row['final_angle_deg'],4.4)
        self.assertEqual(row['final_lateral_m'],.00045)
        self.assertEqual(row['physics_hz'],480)
        self.assertFalse(row['complete_cycle_evidence'])

    def summarize_result(self,result):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'results.json'
            path.write_text(json.dumps(result))
            return summarize(path)

    def test_reported_green_without_physical_evidence_is_not_complete(self):
        row=self.summarize_result({'robot':'A','passed':True,'scope':'full_rack'})
        self.assertTrue(row['reported_pass'])
        self.assertFalse(row['complete_cycle_evidence'])

    def test_reload_not_counted_as_randomized_reliability(self):
        row=self.summarize_result({'robot':'A','passed':True,'loaded_scene':'saved.usda',
            'initial_retained_without_hand':True,'unplug_success':True,'replug_success':True,
            'topology_audit':{'passed':True}})
        self.assertTrue(row['complete_cycle_evidence'])
        self.assertEqual(row['role'],'reload')
        self.assertFalse(row['randomized_reliability_sample'])
        self.assertEqual(len(row['results_sha256']),64)

    def test_exception_is_preserved_without_inventing_time_or_force(self):
        row=self.summarize_result({'robot':'B','passed':False,'error':'Traceback\nValueError: guard'})
        self.assertEqual(row['error'],'ValueError: guard')
        self.assertEqual(row['cycle_time_s'],'')
        self.assertEqual(row['peak_pair_contact_estimate_n'],'')

    def test_non_robot_probe_is_excluded(self):
        self.assertIsNone(self.summarize_result({'passed':True,'scope':'isolated transmission'}))
