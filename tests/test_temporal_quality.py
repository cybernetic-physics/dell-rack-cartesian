import unittest
from PIL import Image
from rack_robotics.temporal_quality import frame_metrics, screen_flags, inspection_indices, phase_spans, validate_timestamps
from rack_robotics.scripts.screen_video_temporal import read_frame
from io import BytesIO


class TemporalQualityTests(unittest.TestCase):
    def textured(self, offset=0):
        frame = Image.new('RGB', (20, 20), (40+offset,)*3)
        for x in range(10):
            for y in range(20): frame.putpixel((x, y), (100+offset,)*3)
        return frame

    def test_blank_and_uniform_frames_flagged(self):
        for value in (0, 120, 255):
            rows = [frame_metrics(Image.new('RGB', (20, 20), (value,)*3))]
            self.assertIn('blank_or_nearly_uniform', screen_flags(rows)[0]['reasons'])

    def test_brightness_jump_and_declared_cut_distinguished(self):
        first = self.textured(); second = self.textured(80)
        rows = [frame_metrics(first), frame_metrics(second, first)]
        self.assertEqual(screen_flags(rows)[0]['frame'], 1)
        self.assertEqual(screen_flags(rows, camera_cuts=[1]), [])
        self.assertEqual(screen_flags([frame_metrics(first), frame_metrics(first, first)]), [])

    def test_every_phase_and_duration_covered_with_denser_latch_sampling(self):
        samples = [{'phase': p} for p in ['initialize']*16+['approach']*60+['release_latch']*21+['withdraw']*75]
        overview = inspection_indices(samples)
        detailed = inspection_indices(samples, True)
        self.assertTrue(set(overview) <= set(detailed))
        self.assertIn(79, detailed); self.assertNotIn(79, overview)
        for span in phase_spans(samples):
            self.assertIn(span['start_frame'], overview)
            self.assertIn(span['end_frame_exclusive']-1, overview)
        self.assertLessEqual(max(b-a for a, b in zip(overview, overview[1:])), 30)

    def test_partial_decode_rejected(self):
        self.assertEqual(read_frame(BytesIO(b'abcdef'), 6), b'abcdef')
        self.assertIsNone(read_frame(BytesIO(b''), 6))
        with self.assertRaises(ValueError): read_frame(BytesIO(b'abc'), 6)

    def test_all_presentation_timestamps_must_match_real_frame_rate(self):
        self.assertEqual(validate_timestamps([0., .033333, .066667], 3)['frames'], 3)
        for values in ([0., .033333], [0., .033333, .033333], [0., .05, .066667],
                       [0., float('nan'), .066667], [.1, .133333, .166667]):
            with self.assertRaises(ValueError): validate_timestamps(values, 3)


if __name__ == '__main__': unittest.main()
