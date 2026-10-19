import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/'rack_robotics/scripts/render_demos.py'
SPEC=importlib.util.spec_from_file_location('render_demos',PATH)
module=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(module)


class RenderBatchTest(unittest.TestCase):
    def test_native_render_quality_arguments(self):
        self.assertEqual(module.render_settings(2560,1440,32),
                         ['--width','2560','--height','1440','--render-subframes','32'])
        self.assertEqual(module.render_settings(1920,1080,16)[1],'1920')
        self.assertEqual(module.render_settings(3840,2160,64)[3],'2160')

    def test_bad_native_render_quality_rejected(self):
        for values in [(1280,720,32),(2561,1440,32),(2560,1080,32),
                       (2560,1440,0),(2560,1440,True),(2560.,1440,32)]:
            with self.assertRaises(ValueError):module.render_settings(*values)

    def test_safe_unique_labels(self):
        self.assertEqual(set(module.select_attempts(['AA=one','CA=two'])),{'AA','CA'})
        for rows in [['../../AA=one'],['AA=one','AA=two'],['AA'],['AA=']]:
            with self.assertRaises(ValueError): module.select_attempts(rows)

    def test_four_required_camera_roles(self):
        self.assertEqual(set(module.CAMERAS),{'wide','rear','macro','side'})
        self.assertIn('--macro-offset',module.CAMERAS['macro'])

    def test_open_frame_profile_and_explicit_gpu(self):
        self.assertEqual(set(module.CAMERA_PROFILES['open-frame-v1']),set(module.VIEWS))
        for view in module.VIEWS:
            args=module.camera_arguments(view,'open-frame-v1',1)
            self.assertEqual(args[:2],['--gpu','1'])
        self.assertIn('--macro-fill-intensity',module.camera_arguments('macro','open-frame-v1',1))
        self.assertEqual(module.camera_arguments('wide','legacy',0),['--gpu','0'])

    def test_reviewed_latch_profile_preserves_four_views(self):
        self.assertEqual(set(module.CAMERA_PROFILES['latch-inspection-v2']),set(module.VIEWS))
        self.assertIn('--view-fill-intensity',module.camera_arguments('rear','latch-inspection-v2',1))
        self.assertIn('8000',module.camera_arguments('macro','latch-inspection-v2',1))
        self.assertNotIn('--view-fill-intensity',module.camera_arguments('rear','open-frame-v1',1))

    def test_invalid_selection_rejected(self):
        for view,profile,gpu in [('wide','unknown',0),('unknown','legacy',0),
                                 ('wide','legacy',-1),('wide','legacy',True)]:
            with self.assertRaises(ValueError):module.camera_arguments(view,profile,gpu)

    def test_arguments_do_not_mutate_profile(self):
        args=module.camera_arguments('side','open-frame-v1',1)
        args.clear()
        self.assertIn('--eye',module.camera_arguments('side','open-frame-v1',1))

    def test_failure_diagnostics_cannot_be_mislabeled_as_success(self):
        result=dict(passed=False,scope='full_rack',robot='A_robot',gripper='B_tool')
        module.validate_attempt(result,'AB',True)
        with self.assertRaises(ValueError):module.validate_attempt(result,'AB')
        with self.assertRaises(ValueError):module.validate_attempt(result,'CA',True)
        with self.assertRaises(ValueError):module.validate_attempt(dict(result,passed=True),'AB',True)
        with self.assertRaises(ValueError):module.validate_attempt(dict(result,passed=None),'AB',True)


if __name__=='__main__': unittest.main()
