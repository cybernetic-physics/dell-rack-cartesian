import math
import unittest
from rack_robotics.command_profiles import slew_target,latch_press_target
from rack_robotics.rg2_parameters import OPEN_ANGLE, CLOSED_ANGLE, COMMAND_RATE_DEG_S


class CommandProfileTests(unittest.TestCase):
    def test_latch_target_preserves_default_and_obeys_existing_travel(self):
        self.assertEqual(latch_press_target(None,-.0055,.001),-.005)
        self.assertEqual(latch_press_target(-.0055,-.0055,.001),-.0055)
        self.assertEqual(latch_press_target(-.0055,-.00549999997,.001),-.00549999997)
        for target in (-.006,0.,.001,math.nan,math.inf):
            with self.assertRaises(ValueError):latch_press_target(target,-.0055,.001)

    def test_narrow_closure_is_rate_bounded_and_finishes_before_grasp_dwell(self):
        value=OPEN_ANGLE
        for _ in range(round(1.8*240)):
            new=slew_target(value,CLOSED_ANGLE,COMMAND_RATE_DEG_S,1/240)
            self.assertLessEqual(abs(new-value),COMMAND_RATE_DEG_S/240+1e-12)
            self.assertGreaterEqual(new,CLOSED_ANGLE)
            value=new
        self.assertEqual(value,CLOSED_ANGLE)

    def test_opening_and_reversing_do_not_jump(self):
        value=slew_target(CLOSED_ANGLE,OPEN_ANGLE,3.,.1)
        self.assertAlmostEqual(value,CLOSED_ANGLE+.3)
        self.assertEqual(slew_target(value,CLOSED_ANGLE,3.,.1),CLOSED_ANGLE)

    def test_no_overshoot_or_drift(self):
        self.assertEqual(slew_target(13.99,14.,3.,.1),14.)
        self.assertEqual(slew_target(14.,14.,3.,.1),14.)

    def test_invalid_inputs_fail(self):
        for values in [(0,1,0,.1),(0,1,-1,.1),(0,1,1,0),(0,1,1,-.1),
                       (math.nan,1,1,.1),(0,math.inf,1,.1),(0,1,math.inf,.1),
                       (0,1,1,math.nan)]:
            with self.assertRaises(ValueError): slew_target(*values)
