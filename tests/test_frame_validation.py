from pathlib import Path
import tempfile
import unittest
from PIL import Image
from rack_robotics.frame_validation import check_frame


class FrameValidationTests(unittest.TestCase):
    def test_black_and_flat_white_are_not_valid_scene_captures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'frame.png'
            for color in (0, 255):
                Image.new('L', (100, 100), color).save(path)
                with self.assertRaises(ValueError): check_frame(path)

    def test_nonblank_is_not_a_visual_quality_claim(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'frame.png'
            frame = Image.new('L', (100, 100), 0)
            frame.paste(100, (20, 20, 80, 80)); frame.save(path)
            self.assertGreater(check_frame(path)['visible_fraction_above_15'], .3)
