import importlib.util
import ast
import json
from pathlib import Path
import tempfile
import unittest

PATH=Path(__file__).resolve().parents[1]/'rack_robotics/scripts/edit_multi_angle.py'
SPEC=importlib.util.spec_from_file_location('edit_multi_angle',PATH)
edit=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(edit)


class MultiAngleTest(unittest.TestCase):
    def test_native_higher_resolution_without_upscaling(self):
        for resolution in ([1920,1080],[2560,1440],[3840,2160]):
            self.assertEqual(edit.native_resolution(resolution),tuple(resolution))
        for resolution in (None,[1280,720],[2560,1080],[2561,1440],[2560.,1440],[]):
            with self.assertRaises(ValueError): edit.native_resolution(resolution)

    def test_reviewed_camera_choices_preserve_phase_and_every_frame(self):
        samples=[{'phase':p} for p in ('initialize','withdraw','withdraw','insert','park')]
        original=edit.shot_list(samples)
        revised=edit.shot_list(samples,{'withdraw':'macro'})
        self.assertEqual(revised[1]['view'],'macro')
        for before,after in zip(original,revised):
            self.assertEqual({k:v for k,v in before.items() if k!='view'},
                             {k:v for k,v in after.items() if k!='view'})
        self.assertEqual(edit.PHASE_VIEW['withdraw'],'side')

    def test_camera_choices_cannot_inject_unverified_views_or_phases(self):
        for mapping in ([],{'imagined_phase':'macro'},{'withdraw':'nonexistent'},
                        {'withdraw':"macro;movie=unrelated.mp4"}):
            with self.assertRaises(ValueError): edit.phase_cameras(mapping)

    def test_every_controller_phase_has_an_explicit_camera(self):
        controller=PATH.parents[1]/'controllers/rj45_task.py'
        tree=ast.parse(controller.read_text())
        phases={'initialize'}
        for node in ast.walk(tree):
            if (isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute)
                    and node.func.attr=='enter' and node.args and isinstance(node.args[0],ast.Constant)):
                phases.add(node.args[0].value)
        self.assertFalse(phases-set(edit.PHASE_VIEW))
        self.assertEqual(edit.shot_list([{'phase':'release_datum'}])[0]['view'],'macro')

    def test_every_frame_once_in_phase_order(self):
        samples=[{'phase':p} for p in ('initialize','approach','approach','grasp','release_latch','withdraw','park')]
        shots=edit.shot_list(samples)
        frames=[i for shot in shots for i in range(shot['start_frame'],shot['end_frame_exclusive'])]
        self.assertEqual(frames,list(range(len(samples))))
        self.assertEqual(shots[3]['view'],'macro')
        with self.assertRaises(ValueError): edit.shot_list([{'phase':'unknown'}])

    def test_rejects_mixed_or_changed_replays(self):
        with tempfile.TemporaryDirectory() as tmp:
            paths={v:Path(tmp)/v for v in edit.VIEWS}
            for view,path in paths.items():
                path.mkdir(); (path/'demo.mp4').write_bytes(b'test fixture, not video')
                report={'view':view,'full_trajectory':True,'source_passed':True,'fps':30,'frames':3,
                    'start_frame':0,'initialization_only':False,'physics_running':False,'replay_only':True,
                    'recording_validation':{'samples':3},'resolution':[1920,1080],
                    'video_sha256':edit.sha(path/'demo.mp4'),'source_sha256':{'trajectory':'same'},'trajectory_file':'trajectory.jsonl'}
                (path/'manifest.json').write_text(json.dumps(report))
            self.assertEqual(len(edit.verify_inputs(paths)),4)
            for view,path in paths.items():
                report=json.loads((path/'manifest.json').read_text())
                report['resolution']=[2560,1440]
                (path/'manifest.json').write_text(json.dumps(report))
            self.assertEqual(edit.verify_inputs(paths)['wide']['resolution'],[2560,1440])
            report=json.loads((paths['side']/'manifest.json').read_text())
            report['resolution']=[1920,1080]
            (paths['side']/'manifest.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError): edit.verify_inputs(paths)
            report['resolution']=[2560,1440]
            report['source_sha256']['trajectory']='different'
            (paths['side']/'manifest.json').write_text(json.dumps(report))
            with self.assertRaises(ValueError): edit.verify_inputs(paths)
            report['source_sha256']['trajectory']='same'
            (paths['side']/'manifest.json').write_text(json.dumps(report))
            (paths['side']/'demo.mp4').write_bytes(b'changed')
            with self.assertRaises(ValueError): edit.verify_inputs(paths)


if __name__=='__main__': unittest.main()
