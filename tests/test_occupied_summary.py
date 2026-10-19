import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPTS=Path(__file__).resolve().parents[1]/'rack_robotics/scripts'
sys.path.insert(0,str(SCRIPTS))
spec=importlib.util.spec_from_file_location('occupied_summary',SCRIPTS/'summarize_occupied_screen.py')
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class OccupiedSummaryTest(unittest.TestCase):
    def test_task_and_contact_failures_are_not_dropped(self):
        base={'design':'AA','port':4,'timed_trial_started':True,'fixture_stable':True}
        rows=[dict(base,condition='one',task_passed=True,clearance_passed=True,robot_neighbor_contact_pair_count=0),
              dict(base,condition='two',task_passed=True,clearance_passed=False,robot_neighbor_contact_pair_count=1),
              dict(base,condition='three',task_passed=False,clearance_passed=False,robot_neighbor_contact_pair_count=0)]
        result=module.summarize_rows(rows,['AA'])['AA']
        self.assertEqual((result['cases'],result['task_passes'],result['clearance_passes']),(3,2,1))
        self.assertEqual(result['cases_with_robot_neighbor_contact'],1)
        with self.assertRaises(ValueError): module.summarize_rows(rows+[rows[0]],['AA'])


if __name__=='__main__': unittest.main()
