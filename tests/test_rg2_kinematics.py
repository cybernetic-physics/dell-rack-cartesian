import math
import unittest

from rack_robotics.rg2_kinematics import (
    angle_for_tip_separation, ideal_force_per_jaw, tip_geometry,
)


class RG2KinematicsTests(unittest.TestCase):
    def test_closed_origin_and_authored_pose(self):
        separation, extension = tip_geometry(0)
        self.assertEqual(separation, 0)
        self.assertAlmostEqual(extension, .21478315, places=8)
        separation, extension = tip_geometry(60)
        self.assertAlmostEqual(separation, .0976642, delta=2e-7)
        self.assertAlmostEqual(extension, .18947664, delta=2e-7)

    def test_inverse(self):
        for angle in (0, 10.8, 11.3, 14, 30, 60, 70.06):
            self.assertAlmostEqual(angle_for_tip_separation(tip_geometry(angle)[0]), angle, places=10)

    def test_invalid_inputs(self):
        for angle in (-1, 71, math.nan, math.inf):
            with self.assertRaises(ValueError):
                tip_geometry(angle)
        for opening in (-.001, .12, math.nan, math.inf):
            with self.assertRaises(ValueError):
                angle_for_tip_separation(opening)
        for torque in (-1, math.nan, math.inf):
            with self.assertRaises(ValueError):
                ideal_force_per_jaw(10, torque)

    def test_two_jaws_share_one_motor_work(self):
        angle, delta = 11.3, 1e-4
        derivative = (tip_geometry(angle+delta)[0] - tip_geometry(angle-delta)[0]) / math.radians(2*delta)
        self.assertAlmostEqual(ideal_force_per_jaw(angle, 1), 1/derivative, places=7)

    def test_narrow_custom_shoes_still_need_depth_compensation(self):
        # Proposed 4 mm inward offset per shoe + two 1 mm pad half-widths.
        closed = tip_geometry(10.8)
        opened = tip_geometry(14)
        self.assertLess(closed[0] - .010, .01168)
        self.assertGreater(opened[0] - .010, .016)
        self.assertGreater(closed[1] - opened[1], .0004)
        self.assertLess(closed[1] - opened[1], .001)

    def test_insertion_compensation_preserves_contact_target(self):
        from rack_robotics.kinematics import compliant_joint_coordinates
        _, reference = tip_geometry(11.3)
        for architecture in ('A','B','C'):
            for angle in (10.8,11.3,14):
                _, extension = tip_geometry(angle)
                shift = reference-extension
                q = compliant_joint_coordinates(architecture,(.1875,.4292,1.66),
                    (.1875,.50,1.66),(.1875,.50+shift,1.66))
                actual_tip_y = .68+q['y']-.13+shift
                self.assertAlmostEqual(actual_tip_y,.4292)


if __name__ == '__main__':
    unittest.main()
