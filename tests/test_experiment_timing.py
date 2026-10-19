import unittest
from rack_robotics.experiment_timing import ExperimentTiming


class ExperimentTimingTests(unittest.TestCase):
    def test_default_preserves_reference_durations(self):
        t=ExperimentTiming()
        self.assertEqual(t.dt,1/240)
        self.assertEqual([t.steps(s) for s in (1.,2.,3.,32/240)],[240,480,720,32])
        self.assertEqual((t.recording_stride,t.visual_stride),(8,4))

    def test_sensitivity_steps_preserve_physical_time_and_recording_fps(self):
        for hz in (240,480,960):
            t=ExperimentTiming(hz)
            self.assertEqual(t.steps(3.)*t.dt,3.)
            self.assertEqual(t.steps(3.)//t.recording_stride,90)
            self.assertEqual(t.steps(3.)//t.visual_stride,180)

    def test_invalid_rate_and_duration(self):
        for hz in (0,60,239,481):
            with self.assertRaises(ValueError): ExperimentTiming(hz)
        for seconds in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): ExperimentTiming().steps(seconds)
