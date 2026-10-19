import math
import unittest
from rack_robotics.tool_parameters import rack_servo_target, PINION_RADIUS, OPEN_JAW_X, CLOSED_JAW_X, FIXED_JAW_X, APPROACH_OFFSET_X


class RackToolTests(unittest.TestCase):
    def test_open_left_shoe_clears_housing_in_offset_approach(self):
        self.assertLess(FIXED_JAW_X+APPROACH_OFFSET_X+.003,-.01168/2-.0001)

    def test_open_right_shoe_clears_housing_in_offset_approach(self):
        self.assertGreater(OPEN_JAW_X+APPROACH_OFFSET_X-.003,.01168/2+.0001)

    def test_open_is_zero_relative_pinion_rotation(self):
        self.assertEqual(rack_servo_target(False),0)

    def test_travel_matches_six_mm_pitch_radius(self):
        angle=rack_servo_target(True)
        self.assertAlmostEqual(angle,54.4309905374)
        self.assertAlmostEqual(math.radians(angle)*PINION_RADIUS,OPEN_JAW_X-CLOSED_JAW_X)

    def test_nominal_pad_gaps_admit_and_compress_housing(self):
        self.assertGreater(OPEN_JAW_X-FIXED_JAW_X-.002,.01168)
        self.assertLess(CLOSED_JAW_X-FIXED_JAW_X-.002,.01168)
