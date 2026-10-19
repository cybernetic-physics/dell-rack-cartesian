import copy
import math
import unittest

from rack_robotics.cable_screen import screen_cable


class CableScreenTests(unittest.TestCase):
    def setUp(self):
        self.geometry = {'attachment_body': 'plug', 'attachment_local': [0, 0, 0],
                         'links': [{'path': 'one', 'proximal': [0, -.5, 0], 'distal': [0, .5, 0]},
                                   {'path': 'two', 'proximal': [0, -.5, 0], 'distal': [0, .5, 0]}]}
        self.header = {'body_paths': ['plug', 'one', 'two'], 'fps': 30}
        self.sample = {'time': 0., 'phase': 'withdraw',
                       'poses': [[0, 0, 0, 1, 0, 0, 0], [0, .5, 0, 1, 0, 0, 0],
                                 [0, 1.5, 0, 1, 0, 0, 0]]}

    def test_straight_cable_is_not_proof_of_excessive_tension(self):
        result = screen_cable(self.geometry, self.header, [self.sample])
        self.assertEqual(result['maxima']['endpoint_chord_fraction']['value'], 1.)
        self.assertEqual(result['maxima']['joint_anchor_gap_m']['value'], 0.)
        self.assertIsNone(result['tensile_force_n'])
        self.assertEqual(result['excessive_tension_assessment'], 'unmeasured')

    def test_rigid_translation_is_displacement_not_strain(self):
        shifted = copy.deepcopy(self.sample); shifted['time'] = 1/30
        for pose in shifted['poses']: pose[0] += .2
        result = screen_cable(self.geometry, self.header, [self.sample, shifted])
        self.assertAlmostEqual(result['maxima']['free_end_displacement_m']['value'], .2)
        self.assertEqual(result['maxima']['joint_anchor_gap_m']['value'], 0.)

    def test_bend_uses_rotated_anchors(self):
        bent = copy.deepcopy(self.sample)
        bent['poses'][2] = [.5, 1, 0, math.sqrt(.5), 0, 0, -math.sqrt(.5)]
        result = screen_cable(self.geometry, self.header, [bent])
        self.assertAlmostEqual(result['maxima']['adjacent_segment_bend_deg']['value'], 90.)
        self.assertAlmostEqual(result['maxima']['joint_anchor_gap_m']['value'], 0.)
        self.assertAlmostEqual(result['maxima']['endpoint_chord_fraction']['value'], math.sqrt(.5))

    def test_open_joint_is_flagged_without_becoming_tension(self):
        self.sample['poses'][2][1] += .002
        result = screen_cable(self.geometry, self.header, [self.sample])
        self.assertFalse(result['sampled_attachment_gap_below_1_5mm'])
        self.assertEqual(result['maxima']['joint_anchor_gap_m']['joint'], 1)

    def test_bad_pose_time_and_missing_link_rejected(self):
        with self.assertRaises(ValueError):
            screen_cable(self.geometry, self.header, [self.sample, self.sample])
        self.sample['poses'][2][3] = 2
        with self.assertRaises(ValueError):
            screen_cable(self.geometry, self.header, [self.sample])
        with self.assertRaises(ValueError):
            screen_cable(self.geometry, {'body_paths': ['plug', 'one']}, [self.sample])
