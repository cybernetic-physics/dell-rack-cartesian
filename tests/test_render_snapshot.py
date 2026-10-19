import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH=Path(__file__).resolve().parents[1]/'rack_robotics/scripts/export_render_snapshot.py'
SPEC=importlib.util.spec_from_file_location('render_snapshot',PATH)
module=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(module)


class RenderSnapshotTest(unittest.TestCase):
    def fixture(self,root):
        (root/'manifest.json').write_text(json.dumps({'source_sha256':{}}))
        folder=root/'CA/wide';(folder/'frames').mkdir(parents=True)
        (folder/'demo.mp4').write_bytes(b'video fixture')
        for i in range(5):(folder/'frames'/f'{i:05d}.png').write_bytes(b'png fixture')
        (folder/'manifest.json').write_text(json.dumps({'video_sha256':module.sha(folder/'demo.mp4'),'frames':5}))
        return {'complete':False,'cases':{'CA/wide':{'status':'captured','manifest_sha256':module.sha(folder/'manifest.json')},
                                        'CA/macro':{'status':'running'}}}

    def test_partial_batch_exports_only_completed_views(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);state=self.fixture(root)
            files,selected=module.select_files(root,state,3)
            self.assertEqual(set(selected),{'CA/wide'})
            self.assertEqual(selected['CA/wide']['original_png_frame_indices'],[0,2,4])
            self.assertFalse(any('macro' in str(p) for p in files))

    def test_changed_completed_video_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);state=self.fixture(root)
            (root/'CA/wide/demo.mp4').write_bytes(b'changed')
            with self.assertRaises(ValueError):module.select_files(root,state)

    def test_sample_selection_covers_ends_and_short_recordings(self):
        self.assertEqual(module.frame_indices(1,9),[0])
        self.assertEqual(module.frame_indices(5,3),[0,2,4])
        for args in [(0,9),(5,1),(-1,3)]:
            with self.assertRaises(ValueError):module.frame_indices(*args)

    def test_frozen_phase_camera_input_is_included(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);state=self.fixture(root)
            mapping=root/'phase_cameras_input.json'
            mapping.write_text('{"withdraw":"macro"}')
            (root/'manifest.json').write_text(json.dumps({'source_sha256':{},
                'phase_cameras_input_sha256':module.sha(mapping)}))
            files,_=module.select_files(root,state)
            self.assertIn(mapping.resolve(),files)
            mapping.write_text('{"withdraw":"rear"}')
            with self.assertRaisesRegex(ValueError,'phase-camera'):module.select_files(root,state)

    def test_missing_or_external_phase_camera_input_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary, tempfile.TemporaryDirectory() as external:
            root=Path(temporary);state=self.fixture(root)
            other=Path(external)/'mapping.json';other.write_text('{}')
            (root/'manifest.json').write_text(json.dumps({'source_sha256':{},
                'phase_cameras_input_sha256':module.sha(other)}))
            with self.assertRaisesRegex(ValueError,'phase-camera'):module.select_files(root,state)
            (root/'phase_cameras_input.json').symlink_to(other)
            with self.assertRaisesRegex(ValueError,'phase-camera'):module.select_files(root,state)


if __name__=='__main__':unittest.main()
