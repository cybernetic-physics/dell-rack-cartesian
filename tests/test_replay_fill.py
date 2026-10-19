import hashlib
from pathlib import Path
import tempfile
import unittest
from pxr import Usd, UsdGeom, UsdLux
from rack_robotics.replay import bake_replay


class ReplayFillTest(unittest.TestCase):
    def test_fill_tracks_camera_without_changing_inputs_or_body_poses(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            source = directory/'input.usda'
            stage = Usd.Stage.CreateNew(str(source))
            paths = ['/World/Plug','/World/Cable/Link00']
            for path in paths+['/World/ClipPress']:
                UsdGeom.Xform.Define(stage,path)
            UsdGeom.BasisCurves.Define(stage,'/World/Cable/Jacket')
            stage.GetRootLayer().Save()
            before = hashlib.sha256(source.read_bytes()).hexdigest()
            poses = [[0,.5,1.6,1,0,0,0],[0,.52,1.6,1,0,0,0]]
            samples = [{'poses':poses},{'poses':[[0,.55,1.6,1,0,0,0],poses[1]]}]
            for view,intensity in (('macro',0.),('macro',3000.),('rear',0.),('rear',4000.)):
                output = directory/f'output{view}{intensity}.usda'
                bake_replay(source,output,{'body_paths':paths},samples,view,
                            {view:((-.08,.60,1.65),(0,.5,1.6))},(0,.5,1.6),
                            **{('macro_fill_intensity' if view=='macro' else 'view_fill_intensity'):intensity})
                rendered = Usd.Stage.Open(str(output))
                fill = rendered.GetPrimAtPath('/World/ReplayCameraFill')
                self.assertEqual(bool(fill),bool(intensity))
                if intensity:
                    self.assertEqual(UsdLux.RectLight(fill).GetIntensityAttr().Get(),intensity)
                    self.assertAlmostEqual(UsdLux.RectLight(fill).GetWidthAttr().Get(),.06 if view=='macro' else .25)
                    for i in range(2):
                        self.assertEqual(UsdGeom.Xformable(fill).ComputeLocalToWorldTransform(i),
                            UsdGeom.Xformable(rendered.GetPrimAtPath('/World/ReplayCamera')).ComputeLocalToWorldTransform(i))
                for i,sample in enumerate(samples):
                    for path,pose in zip(paths,sample['poses']):
                        actual = UsdGeom.Xformable(rendered.GetPrimAtPath(path)).ComputeLocalToWorldTransform(i)
                        self.assertEqual(tuple(actual.ExtractTranslation()),tuple(pose[:3]))
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(),before)

    def test_invalid_fill_rejected_before_creating_output(self):
        for value,view in ((-1.,'macro'),(float('nan'),'macro'),(3000.,'wide')):
            with self.assertRaises(ValueError):
                bake_replay(None,None,None,None,view,None,None,macro_fill_intensity=value)

    def test_invalid_non_macro_fill_rejected(self):
        for value,view in ((-1.,'rear'),(float('nan'),'rear'),(4000.,'macro'),(4000.,'unknown')):
            with self.assertRaises(ValueError):
                bake_replay(None,None,None,None,view,None,None,view_fill_intensity=value)
