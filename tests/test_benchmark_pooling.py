import copy
import unittest
from rack_robotics.benchmarking.pooling import pool_campaigns


def bundle(seed, count=10):
    rows = [dict(design='AA', condition=f'trial-{i:03d}', port=1,
                 admissible_initial_state=True, complete_cycle=True, fixture_failure=False,
                 unplug_success=True, replug_success=True, cycle_time_s=20) for i in range(count)]
    return {
        'manifest': {'harness_sha256': {'source.py': 'abc'}, 'designs': ['AA']},
        'plan': {'environments': {'AA': {'manifest_sha256': 'env'}}, 'count_per_environment': count},
        'conditions': {f'trial-{i:03d}': {'role': 'randomized', 'seed': seed, 'index': i}
                       for i in range(count)},
        'summary': {'campaign_directory': f'campaign{seed}', 'evidence_hashes_valid': True,
                    'errors': [], 'controls': {'AA': {'complete_cycle': True}}, 'trials': rows}}


class PoolingTests(unittest.TestCase):
    def test_twenty_disjoint_trials_excludes_controls(self):
        result = pool_campaigns([bundle(1), bundle(2)])['designs']['AA']
        self.assertEqual(result['admissible_manipulation_trials'], 20)
        self.assertTrue(result['minimum_twenty_valid_trials_met'])
        self.assertAlmostEqual(result['wilson_95_interval'][0], .83887484)

    def test_changed_protocol_and_environment_are_rejected(self):
        for section, key, value in [('manifest', 'harness_sha256', {'source.py': 'different'}),
                                    ('plan', 'environments', {'AA': {'manifest_sha256': 'changed'}})]:
            altered = bundle(2); altered[section][key] = value
            with self.assertRaises(ValueError): pool_campaigns([bundle(1), altered])

    def test_same_seed_is_rejected_even_with_another_campaign_name(self):
        altered = bundle(1); altered['summary']['campaign_directory'] = 'duplicate'
        with self.assertRaises(ValueError): pool_campaigns([bundle(1), altered])

    def test_fixture_failures_do_not_meet_twenty_trial_requirement(self):
        altered = bundle(2)
        altered['summary']['trials'][0].update(admissible_initial_state=False,
            complete_cycle=False, fixture_failure=True, unplug_success=False, replug_success=False)
        result = pool_campaigns([bundle(1), altered])['designs']['AA']
        self.assertEqual(result['admissible_manipulation_trials'], 19)
        self.assertFalse(result['minimum_twenty_valid_trials_met'])
        self.assertEqual(result['fixture_failures'], 1)
        self.assertEqual(result['complete_cycle_rate'], 1)
        self.assertEqual(result['protocol_success_rate_including_fixture'], .95)

    def test_pending_trials_withhold_rates_and_requirement_claims(self):
        altered = bundle(2); altered['summary']['trials'].pop()
        result = pool_campaigns([bundle(1), altered])['designs']['AA']
        self.assertIsNone(result['complete_cycle_rate'])
        self.assertFalse(result['minimum_twenty_valid_trials_met'])
        self.assertEqual(len(result['missing']), 1)

    def test_evidence_errors_and_control_failure_cannot_look_complete(self):
        altered = bundle(1); altered['summary']['errors'] = ['hash mismatch']
        with self.assertRaises(ValueError): pool_campaigns([altered])
        altered = bundle(1); altered['summary']['controls']['AA']['complete_cycle'] = False
        result = pool_campaigns([altered])['designs']['AA']
        self.assertFalse(result['complete'])
        self.assertIsNone(result['complete_cycle_rate'])

    def test_duplicate_observations_and_control_contamination_rejected(self):
        altered = bundle(1)
        altered['summary']['trials'].append(copy.deepcopy(altered['summary']['trials'][0]))
        with self.assertRaises(ValueError): pool_campaigns([altered])
        altered = bundle(1); altered['conditions']['trial-000']['role'] = 'control'
        with self.assertRaises(ValueError): pool_campaigns([altered])
