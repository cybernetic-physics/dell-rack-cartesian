import unittest
from pxr import Gf,Usd,UsdGeom,UsdPhysics
from rack_robotics.latch_tool_detail import forward_latch_neck


class LatchToolDetailTest(unittest.TestCase):
    def stage(self):
        s=Usd.Stage.CreateInMemory();UsdGeom.Xform.Define(s,'/World/Robot')
        for name,center,size in [('Neck',(0,.002,.003),(.003,.002,.007)),
                                 ('Tip',(0,0,0),(.003,.002,.001)),
                                 ('RaisedArm',(0,.016,.006),(.003,.030,.002))]:
            p=UsdGeom.Cube.Define(s,'/World/Robot/LatchTongue/'+name)
            p.CreateSizeAttr(1);p.AddTranslateOp().Set(Gf.Vec3d(*center));p.AddScaleOp().Set(Gf.Vec3f(*size))
            UsdPhysics.CollisionAPI.Apply(p.GetPrim())
        return s

    def test_moves_neck_only_and_preserves_solid_connections(self):
        s=self.stage();forward_latch_neck(s,'A')
        bounds=UsdGeom.BBoxCache(0,['default']);base='/World/Robot/LatchTongue/'
        neck=bounds.ComputeWorldBound(s.GetPrimAtPath(base+'Neck')).ComputeAlignedRange()
        # TCP->tongue Y is +6 mm; the corrected neck ends at7.5 mm,
        # before the boot's +9 mm front. No boot collision is disabled.
        self.assertAlmostEqual(.006+neck.GetMax()[1],.0075,places=8)
        for name in ('Tip','RaisedArm'):
            prim=s.GetPrimAtPath(base+name)
            self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
            r=bounds.ComputeWorldBound(prim).ComputeAlignedRange()
            self.assertTrue(all(min(r.GetMax()[i],neck.GetMax()[i])-max(r.GetMin()[i],neck.GetMin()[i])>0 for i in range(3)))
        self.assertEqual(s.GetPrimAtPath(base+'RaisedArm').GetAttribute('xformOp:translate').Get(),Gf.Vec3d(0,.016,.006))

    def test_guards_wrong_tool_unknown_geometry_and_duplicate(self):
        with self.assertRaises(ValueError):forward_latch_neck(self.stage(),'C')
        s=self.stage();forward_latch_neck(s,'A')
        with self.assertRaises(ValueError):forward_latch_neck(s,'A')
        s=self.stage();s.GetPrimAtPath('/World/Robot/LatchTongue/Neck').GetAttribute('xformOp:translate').Set(Gf.Vec3d(0))
        with self.assertRaises(ValueError):forward_latch_neck(s,'A')
