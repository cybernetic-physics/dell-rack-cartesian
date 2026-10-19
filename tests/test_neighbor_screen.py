import importlib.util
from pathlib import Path
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1]/'rack_robotics/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('neighbor_screen', SCRIPTS/'screen_occupied_ports.py')
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)


class NeighborScreenTest(unittest.TestCase):
    def fixture(self):
        return {'fixture': 'occupied_neighbors_v1', 'randomized_reliability_sample': False,
                'passed': True, 'timed_trial_started': True, 'crowded_port_clearance_passed': True,
                'occupied_neighbors': {'metric_interval': 'timed_robotic_trial', 'fixture_stable': True,
                    'no_reported_robot_neighbor_contact': True, 'contact_reporting_errors': []}}

    def test_rejects_reliability_contamination(self):
        value = self.fixture(); value['randomized_reliability_sample'] = True
        with self.assertRaises(ValueError): module.validate_diagnostic(value)

    def test_clearance_requires_more_than_task_success(self):
        value = self.fixture()
        self.assertTrue(module.validate_diagnostic(value)['clearance_passed'])
        value['occupied_neighbors']['fixture_stable'] = False
        with self.assertRaises(ValueError): module.validate_diagnostic(value)
        value['crowded_port_clearance_passed'] = False
        self.assertFalse(module.validate_diagnostic(value)['clearance_passed'])

    def test_preserves_failed_initialization(self):
        value = self.fixture(); value.update(passed=False, timed_trial_started=False,
                                            crowded_port_clearance_passed=False)
        value.pop('occupied_neighbors')
        self.assertFalse(module.validate_diagnostic(value)['task_passed'])


if __name__ == '__main__': unittest.main()
