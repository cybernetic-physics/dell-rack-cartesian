import unittest
from types import SimpleNamespace
from rack_sim.camera_guard import protect_perspective,PERSPECTIVE

class CameraGuardTests(unittest.TestCase):
    def test_side_view_is_restored(self):
        for name in ('Right','Front','Top'):
            view=SimpleNamespace(camera_path='/OmniverseKit_'+name)
            self.assertEqual(protect_perspective(view),'/OmniverseKit_'+name)
            self.assertEqual(view.camera_path,PERSPECTIVE)

    def test_perspective_navigation_is_untouched(self):
        view=SimpleNamespace(camera_path=PERSPECTIVE,transform='user orbit/zoom')
        self.assertIsNone(protect_perspective(view))
        self.assertEqual(view.transform,'user orbit/zoom')

    def test_opt_out_and_missing_viewport(self):
        view=SimpleNamespace(camera_path='/OmniverseKit_Right')
        self.assertIsNone(protect_perspective(view,False))
        self.assertEqual(view.camera_path,'/OmniverseKit_Right')
        self.assertIsNone(protect_perspective(None))
