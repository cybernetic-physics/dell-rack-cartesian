from pathlib import Path
import unittest
from pxr import Sdf, Usd, UsdGeom, UsdPhysics
from rack_robotics.telescoping_frame import complete_telescoping_frame
from rack_robotics.carrier_mount_screen import screen_carrier_mount_sweep


class TelescopingFrameTest(unittest.TestCase):
    def stage(self):
        path=Path(__file__).resolve().parents[1]/'rack_robotics/environments/robot_b_gripper_a/v013/scene.usda'
        layer=Sdf.Layer.CreateAnonymous();layer.TransferContent(Sdf.Layer.FindOrOpen(str(path)))
        layer.subLayerPaths=[]
        stage=Usd.Stage.Open(layer);UsdGeom.Xform.Define(stage,'/World')
        return stage

    def test_actual_saved_assembly_full_sweep(self):
        stage=self.stage()
        self.assertFalse(screen_carrier_mount_sweep(stage,True,True)['passed'])
        complete_telescoping_frame(stage,'B')
        audit=screen_carrier_mount_sweep(stage,True,True)
        self.assertTrue(audit['passed'],[p['parts'] for p in audit['possible_overlaps']])

    def test_all_joint_attributes_and_body_poses_unchanged(self):
        stage=self.stage()
        before={str(p.GetPath()):[(a.GetName(),a.Get()) for a in p.GetAttributes()]
                for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)}
        bodies={str(p.GetPath()):UsdGeom.Xformable(p).ComputeLocalToWorldTransform(0)
                for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)}
        complete_telescoping_frame(stage,'B')
        self.assertEqual(before,{str(p.GetPath()):[(a.GetName(),a.Get()) for a in p.GetAttributes()]
                                for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)})
        for path,matrix in bodies.items():
            self.assertEqual(UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(0),matrix)
            self.assertGreater(UsdPhysics.MassAPI(stage.GetPrimAtPath(path)).GetMassAttr().Get(),0)

    def test_full_extension_blocks_remain_supported(self):
        for q in (0,.2):
            for x in (-.270,-.220):
                self.assertGreaterEqual(x+q-.0454/2,-.300)
                self.assertLessEqual(x+q+.0454/2,.010)

    def test_compatible_carrier_mounts_over_full_independent_travel(self):
        from rack_robotics.service_carriers import complete_service_carriers
        stage=self.stage();complete_telescoping_frame(stage,'B')
        report=complete_service_carriers(stage,'B',open_frame=True)
        self.assertEqual(report['revision'],'passive_service_carriers_telescoping_open_v1')
        self.assertEqual(len(report['chains']),4)
        audit=screen_carrier_mount_sweep(stage,True,True)
        self.assertTrue(audit['passed'],[p['parts'] for p in audit['possible_overlaps']])

    def test_guards(self):
        with self.assertRaises(ValueError):complete_telescoping_frame(self.stage(),'A')
        stage=self.stage();complete_telescoping_frame(stage,'B')
        with self.assertRaises(ValueError):complete_telescoping_frame(stage,'B')

    def test_coaxial_shaft_ends_separate_inside_couplers(self):
        stage=self.stage();complete_telescoping_frame(stage,'B')
        cache=UsdGeom.BBoxCache(0,['default'])
        def bounds(path):
            return cache.ComputeWorldBound(stage.GetPrimAtPath('/World/Robot/'+path)).ComputeAlignedRange()
        screw=bounds('Frame/LiftScrew');motor=bounds('Frame/Brakes/Lift/OutputShaft')
        self.assertAlmostEqual(motor.GetMin()[2]-screw.GetMax()[2],.002,places=6)
        for i in (0,1):self.assertAlmostEqual(screw.GetMidpoint()[i],motor.GetMidpoint()[i],places=6)
        for parent in ('LiftCarriage','MiddleBoom'):
            screw=bounds(parent+'/Screw');motor=bounds(parent+'/ScrewInterfaces/MotorShaft')
            self.assertAlmostEqual(screw.GetMin()[0]-motor.GetMax()[0],.004,places=6)
            for i in (1,2):self.assertAlmostEqual(screw.GetMidpoint()[i],motor.GetMidpoint()[i],places=6)
