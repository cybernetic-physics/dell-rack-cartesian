import unittest
from pxr import Gf, Usd, UsdGeom, UsdPhysics
from rack_robotics.carrier_mount_screen import screen_carrier_mounts,screen_carrier_mount_sweep


class CarrierMountScreenTest(unittest.TestCase):
    def sweep_stage(self):
        stage=Usd.Stage.CreateInMemory()
        for name,x in [('Frame',0.),('Carriage',.1)]:
            body=UsdGeom.Xform.Define(stage,'/World/Robot/'+name)
            body.AddTranslateOp().Set(Gf.Vec3d(x,0,0));UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
            cube=UsdGeom.Cube.Define(stage,str(body.GetPath())+'/CarrierMounts/Bracket');cube.CreateSizeAttr(.008)
            cube.AddTranslateOp().Set(Gf.Vec3d(.2 if name=='Frame' else 0,0,0))
        j=UsdPhysics.PrismaticJoint.Define(stage,'/World/Robot/Joints/Traverse')
        j.CreateBody0Rel().SetTargets(['/World/Robot/Frame']);j.CreateBody1Rel().SetTargets(['/World/Robot/Carriage'])
        j.CreateLocalPos0Attr(Gf.Vec3f(0));j.CreateLocalPos1Attr(Gf.Vec3f(0))
        j.CreateAxisAttr('X');j.CreateLowerLimitAttr(.1);j.CreateUpperLimitAttr(.3)
        j.CreateCollisionEnabledAttr(False)
        return stage

    def test_sweep_finds_interior_collision_even_with_disjoint_start(self):
        stage=self.sweep_stage();before=stage.GetRootLayer().ExportToString()
        self.assertTrue(screen_carrier_mounts(stage)['passed'])
        report=screen_carrier_mount_sweep(stage)
        self.assertFalse(report['passed']);self.assertEqual(len(report['possible_overlaps']),1)
        self.assertEqual(report['possible_overlaps'][0]['varying_joints'],['Traverse'])
        self.assertEqual(stage.GetRootLayer().ExportToString(),before)

    def test_sweep_accepts_separated_parallel_tracks(self):
        stage=self.sweep_stage()
        stage.GetPrimAtPath('/World/Robot/Frame/CarrierMounts/Bracket').GetAttribute('xformOp:translate').Set(Gf.Vec3d(.2,.01,0))
        self.assertTrue(screen_carrier_mount_sweep(stage)['passed'])

    def test_sweep_rejects_unsupported_owner_path(self):
        stage=self.sweep_stage();stage.RemovePrim('/World/Robot/Joints/Traverse')
        report=screen_carrier_mount_sweep(stage)
        self.assertFalse(report['passed']);self.assertTrue(report['errors'])

    def test_optional_robot_boxes_find_filtered_interior_collision(self):
        stage=self.sweep_stage()
        stage.GetPrimAtPath('/World/Robot/Frame/CarrierMounts/Bracket').GetAttribute('xformOp:translate').Set(Gf.Vec3d(.2,.05,0))
        obstacle=UsdGeom.Cube.Define(stage,'/World/Robot/Frame/Motor')
        obstacle.CreateSizeAttr(.008);obstacle.AddTranslateOp().Set(Gf.Vec3d(.2,0,0))
        before=stage.GetRootLayer().ExportToString()
        self.assertTrue(screen_carrier_mount_sweep(stage)['passed'])
        report=screen_carrier_mount_sweep(stage,include_robot_boxes=True)
        self.assertFalse(report['passed']);self.assertEqual(len(report['possible_overlaps']),1)
        self.assertIn(str(obstacle.GetPath()),report['possible_overlaps'][0]['parts'])
        self.assertEqual(stage.GetRootLayer().ExportToString(),before)

    def test_optional_robot_boxes_reports_unsupported_shapes_and_owners(self):
        stage=self.sweep_stage()
        UsdGeom.Cylinder.Define(stage,'/World/Robot/Frame/Screw')
        body=UsdGeom.Xform.Define(stage,'/World/Robot/Jaw')
        UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
        UsdGeom.Cube.Define(stage,'/World/Robot/Jaw/Pad')
        report=screen_carrier_mount_sweep(stage,include_robot_boxes=True)
        self.assertEqual({r['reason'] for r in report['omitted_geometry']},
                         {'unsupported rigid owner','non-box geometry'})

    def test_optional_robot_boxes_reject_rotated_obstacle(self):
        stage=self.sweep_stage()
        box=UsdGeom.Cube.Define(stage,'/World/Robot/Frame/Motor')
        box.AddRotateZOp().Set(20.)
        report=screen_carrier_mount_sweep(stage,include_robot_boxes=True)
        self.assertFalse(report['passed']);self.assertTrue(report['errors'])

    def test_all_box_pairs_exposes_non_mount_stage_interference(self):
        stage=self.sweep_stage()
        for body,center in [('Frame',(.2,.1,0)),('Carriage',(0,.1,0))]:
            box=UsdGeom.Cube.Define(stage,'/World/Robot/'+body+'/Solid')
            box.CreateSizeAttr(.01);box.AddTranslateOp().Set(Gf.Vec3d(*center))
        narrow=screen_carrier_mount_sweep(stage,include_robot_boxes=True)
        broad=screen_carrier_mount_sweep(stage,include_robot_boxes=True,all_robot_box_pairs=True)
        self.assertEqual(len(broad['possible_overlaps']),len(narrow['possible_overlaps'])+1)
        self.assertTrue(any(all(p.endswith('/Solid') for p in pair['parts']) for pair in broad['possible_overlaps']))

    def test_all_box_pairs_requires_explicit_geometry_scope(self):
        with self.assertRaises(ValueError):screen_carrier_mount_sweep(self.sweep_stage(),all_robot_box_pairs=True)

    def stage(self,offset):
        stage=Usd.Stage.CreateInMemory()
        for name,x in [('A',0),('B',offset)]:
            body=UsdGeom.Xform.Define(stage,'/World/Robot/'+name)
            body.AddTranslateOp().Set(Gf.Vec3d(x,0,0)); UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
            cube=UsdGeom.Cube.Define(stage,str(body.GetPath())+'/CarrierMounts/Bracket')
            cube.CreateSizeAttr(.008); UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
        return stage

    def test_overlap_is_not_excused_by_connected_pair_collision_filter(self):
        stage=self.stage(.005)
        j=UsdPhysics.PrismaticJoint.Define(stage,'/World/Robot/Joints/Slide')
        j.CreateBody0Rel().SetTargets(['/World/Robot/A']); j.CreateBody1Rel().SetTargets(['/World/Robot/B'])
        j.CreateCollisionEnabledAttr(False)
        report=screen_carrier_mounts(stage)
        self.assertFalse(report['passed']); self.assertEqual(len(report['overlaps']),1)
        self.assertAlmostEqual(report['overlaps'][0]['overlap_depths_m'][0],.003)

    def test_disjoint_mounts_pass_narrow_screen(self):
        self.assertTrue(screen_carrier_mounts(self.stage(.01))['passed'])

    def test_rotated_bracket_requires_different_geometric_test(self):
        stage=self.stage(.01)
        UsdGeom.Xformable(stage.GetPrimAtPath('/World/Robot/B')).AddRotateZOp().Set(15.)
        report=screen_carrier_mounts(stage)
        self.assertFalse(report['passed']); self.assertTrue(report['errors'])
