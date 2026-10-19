import copy
import math
import unittest
from rack_robotics.replay_validation import rotation_error_rad, validate_recording, validate_capture_camera


class ReplayValidationTests(unittest.TestCase):
    def setUp(self):
        self.header = {'format': 'measured_world_poses_v1', 'fps': 30,
                       'body_paths': ['/World/Plug', '/World/Latch']}
        self.samples = [{'time': i/30, 'poses': [[0, 0, 0, 1, 0, 0, 0]]*2} for i in range(3)]

    def test_quaternion_sign_and_normalization(self):
        self.assertEqual(rotation_error_rad([1, 0, 0, 0], [-1, 0, 0, 0]), 0)
        self.assertEqual(rotation_error_rad([1, 0, 0, 0], [1.0000001, 0, 0, 0]), 0)
        self.assertAlmostEqual(rotation_error_rad([1, 0, 0, 0], [math.sqrt(.5), 0, 0, math.sqrt(.5)]), math.pi/2)

    def test_valid_recording(self):
        self.assertEqual(validate_recording(self.header, self.samples)['samples'], 3)

    def test_dropped_frames_and_missing_bodies_rejected(self):
        with self.assertRaises(ValueError): validate_recording(self.header, [self.samples[0], self.samples[2]])
        altered = copy.deepcopy(self.samples); altered[0]['poses'].pop()
        with self.assertRaises(ValueError): validate_recording(self.header, altered)

    def test_invalid_quaternion_rejected(self):
        altered = copy.deepcopy(self.samples); altered[1]['poses'][0] = [0, 0, 0, 2, 0, 0, 0]
        with self.assertRaises(ValueError): validate_recording(self.header, altered)
        with self.assertRaises(ValueError): rotation_error_rad([0, 0, 0, 0], [1, 0, 0, 0])

    def test_wrong_capture_camera_and_nan_are_rejected(self):
        expected = [[float(i==j) for j in range(4)] for i in range(4)]
        self.assertEqual(validate_capture_camera(expected, expected), 0.)
        different = copy.deepcopy(expected); different[3][1] = 2.
        with self.assertRaises(ValueError): validate_capture_camera(different, expected)
        different[3][1] = float('nan')
        with self.assertRaises(ValueError): validate_capture_camera(different, expected)
