from pathlib import Path
import unittest
from pxr import Sdf, Usd, UsdGeom, UsdPhysics
from rack_robotics.screw_frame import complete_screw_frame,REVISION
from rack_robotics.carrier_mount_screen import screen_carrier_mount_sweep


class ScrewFrameTest(unittest.TestCase):
    def stage(self):
        # Use the actual preserved A/A v014 robot opinions, without loading
        # its large external rack assets. No original file is edited.
        source=Path(__file__).resolve().parents[1]/'rack_robotics/environments/robot_a_gripper_a/v014/scene.usda'
        layer=Sdf.Layer.CreateAnonymous(); layer.TransferContent(Sdf.Layer.FindOrOpen(str(source)))
        layer.subLayerPaths=[]
        stage=Usd.Stage.Open(layer)
        UsdGeom.Xform.Define(stage,'/World')
        return stage

    def test_actual_saved_assembly_full_sweep(self):
        stage=self.stage()
        before=screen_carrier_mount_sweep(stage,True,True)
        self.assertFalse(before['passed'])
        complete_screw_frame(stage,'A')
        after=screen_carrier_mount_sweep(stage,True,True)
        self.assertTrue(after['passed'],after['possible_overlaps'])

    def test_retains_all_joints_and_tcp_bodies(self):
        stage=self.stage()
        joints={str(p.GetPath()):[(a.GetName(),a.Get()) for a in p.GetAttributes()]
                for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)}
        poses={name:UsdGeom.Xformable(stage.GetPrimAtPath('/World/Robot/'+name)).ComputeLocalToWorldTransform(0)
               for name in ('Frame','Bridge','Carriage','ToolMount','LeftJaw','RightJaw','LatchTongue')}
        report=complete_screw_frame(stage,'A')
        self.assertEqual(report['revision'],REVISION)
        self.assertEqual(joints,{str(p.GetPath()):[(a.GetName(),a.Get()) for a in p.GetAttributes()]
                                for p in stage.Traverse() if p.IsA(UsdPhysics.Joint)})
        for name,matrix in poses.items():
            self.assertEqual(UsdGeom.Xformable(stage.GetPrimAtPath('/World/Robot/'+name)).ComputeLocalToWorldTransform(0),matrix)
        self.assertTrue(all(UsdPhysics.MassAPI(stage.GetPrimAtPath(p)).GetMassAttr().Get()>0
                            for p in report['mass_delta_kg_by_body']))

    def test_guards(self):
        with self.assertRaises(ValueError): complete_screw_frame(self.stage(),'C')
        stage=self.stage();complete_screw_frame(stage,'A')
        with self.assertRaises(ValueError): complete_screw_frame(stage,'A')

    def test_carrier_mounts_clear_full_joint_intervals(self):
        from rack_robotics.service_carriers import complete_service_carriers
        stage=self.stage();complete_screw_frame(stage,'A')
        report=complete_service_carriers(stage,'A',open_frame=True)
        self.assertEqual(report['revision'],'passive_service_carriers_screw_open_v1')
        audit=screen_carrier_mount_sweep(stage,True,True)
        self.assertTrue(audit['passed'],audit['possible_overlaps'])

    def test_symmetric_lift_screw_and_brake_axes(self):
        stage=self.stage();complete_screw_frame(stage,'A')
        cache=UsdGeom.BBoxCache(0,['default'])
        for i,x in enumerate((-.278,.278)):
            for name in (f'Screw{i}',f'Motor{i}',f'Brakes/Lift{i}/Housing',f'Brakes/Lift{i}/OutputShaft'):
                bounds=cache.ComputeWorldBound(stage.GetPrimAtPath('/World/Robot/Frame/'+name)).ComputeAlignedRange()
                self.assertAlmostEqual(bounds.GetMidpoint()[0],x,places=6)
