import math
import unittest
from rack_robotics.macro_camera import fit_macro_camera, inspection_points


class MacroCameraTests(unittest.TestCase):
    def test_grasp_separation_and_park_envelopes_stay_in_front_and_in_frame(self):
        focus = [.1875, .429, 1.66]
        for position in (focus, [.1875, .55, 1.66], [.15, .55, 1.80]):
            pose = [*position, 1, 0, 0, 0]
            eye, target = fit_macro_camera(focus, pose, [-.065, .04, .035], 35)
            forward = [b-a for a, b in zip(eye, target)]
            length = math.sqrt(sum(v*v for v in forward)); forward = [v/length for v in forward]
            for point in inspection_points(focus, pose):
                delta = [p-e for p, e in zip(point, eye)]
                depth = sum(a*b for a, b in zip(delta, forward))
                perpendicular = math.sqrt(max(0, sum(v*v for v in delta)-depth*depth))
                self.assertGreater(depth, 0)
                self.assertLess(perpendicular/depth, 10.125/35)

    def test_invalid_camera_direction_is_rejected(self):
        with self.assertRaises(ValueError): fit_macro_camera([0, 0, 0], [0, 0, 0, 1, 0, 0, 0], [0, 0, 0])
