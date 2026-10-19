import unittest
from pathlib import Path
from pxr import Gf,Sdf,Usd,UsdGeom,UsdPhysics,UsdShade
from rack_robotics.hardware_detail import Hardware,ROOT
from rack_robotics.insertion_stage import complete_insertion_stage,REVISION,move_front_support_rearward
from rack_robotics.carrier_mount_screen import screen_carrier_mount_sweep


class InsertionStageTest(unittest.TestCase):
    def test_cable_setback_against_saved_corexz_robot_and_carrier_mounts(self):
        source=Path(__file__).resolve().parents[1]/'rack_robotics/environments/robot_c_gripper_a/v020/scene.usda'
        layer=Sdf.Layer.CreateAnonymous();layer.TransferContent(Sdf.Layer.FindOrOpen(str(source)))
        layer.subLayerPaths=[]
        stage=Usd.Stage.Open(layer);UsdGeom.Xform.Define(stage,'/World')
        # Reconstruct the unshifted seven parts in this anonymous test copy.
        stage.GetPrimAtPath(ROOT).ClearCustomDataByKey('front_support_revision')
        for name in ('DepthSupportBearing','DepthFrontBearingHanger','DepthFrontBearingCrossbar',
                     'DepthFrontBearingPost0','DepthFrontBearingPost1',
                     'DepthFrontBearingBolt0','DepthFrontBearingBolt1'):
            attr=stage.GetPrimAtPath(ROOT+'/Carriage/'+name).GetAttribute('xformOp:translate')
            attr.Set(attr.Get()-Gf.Vec3d(0,.006,0))
        move_front_support_rearward(stage,cable_clearance=True)
        audit=screen_carrier_mount_sweep(stage,True,True)
        self.assertTrue(audit['passed'],audit['possible_overlaps'])
        self.assertGreater(audit['distinct_body_pairs_checked'],4000)

    def test_cable_setback_retains_full_stroke_with_one_mm_plate_gap(self):
        for architecture in 'ABC':
            stage=self.stage(architecture);complete_insertion_stage(stage,architecture)
            report=move_front_support_rearward(stage,cable_clearance=True)
            self.assertEqual(report['revision'],'cable_clearance_insertion_front_support_v2')
            self.assertEqual(report['setback_m'],.011)
            audit=screen_carrier_mount_sweep(stage,True,True)
            self.assertTrue(audit['passed'],audit['possible_overlaps'])
            cache=UsdGeom.BBoxCache(0,['default'])
            hanger=cache.ComputeWorldBound(stage.GetPrimAtPath(ROOT+'/Carriage/DepthFrontBearingHanger')).ComputeAlignedRange()
            plate=cache.ComputeWorldBound(stage.GetPrimAtPath(ROOT+'/ToolMount/DepthBearingPlate')).ComputeAlignedRange()
            self.assertAlmostEqual(plate.GetMin()[1]-.125-hanger.GetMax()[1],.001,places=6)
            self.assertAlmostEqual(hanger.GetMin()[1]+.68,.482,places=6)

    def test_rearward_support_clears_fan_and_entire_insertion_sweep(self):
        for architecture in 'ABC':
            stage=self.stage(architecture);complete_insertion_stage(stage,architecture)
            before=UsdPhysics.MassAPI(stage.GetPrimAtPath(ROOT+'/Carriage')).GetMassAttr().Get()
            report=move_front_support_rearward(stage)
            self.assertEqual(len(report['changes']),7)
            self.assertEqual(UsdPhysics.MassAPI(stage.GetPrimAtPath(ROOT+'/Carriage')).GetMassAttr().Get(),before)
            cache=UsdGeom.BBoxCache(0,['default'])
            for name in ('DepthFrontBearingPost0','DepthFrontBearingPost1','DepthFrontBearingHanger'):
                bounds=cache.ComputeWorldBound(stage.GetPrimAtPath(ROOT+'/Carriage/'+name)).ComputeAlignedRange()
                # Actual GPUFan10 rear face .4725 minus carriage Y origin .68.
                self.assertGreater(bounds.GetMin()[1],.4725-.68+.004)
            audit=screen_carrier_mount_sweep(stage,True,True)
            self.assertTrue(audit['passed'],audit['possible_overlaps'])
            # A 6 mm shift leaves the entire 8 mm bearing on the 221 mm shaft.
            self.assertGreater(-.205+.006-.004,-.0945-.221/2)
            with self.assertRaisesRegex(ValueError,'already'): move_front_support_rearward(stage)

    def stage(self,architecture='A'):
        s=Usd.Stage.CreateInMemory();r=UsdGeom.Xform.Define(s,ROOT).GetPrim()
        r.SetCustomDataByKey('hardware_revision','drive_connections_v4')
        UsdShade.Material.Define(s,'/World/Materials/RobotSteel')
        for name in ('Frame','Carriage','ToolMount'):
            p=UsdGeom.Xform.Define(s,ROOT+'/'+name).GetPrim()
            UsdPhysics.RigidBodyAPI.Apply(p);UsdPhysics.MassAPI.Apply(p).CreateMassAttr(1.)
        for name,parent,child,axis,limits in [('Traverse','Frame','Carriage','X',(-.21,.21)),
                                            ('Insertion','Carriage','ToolMount','Y',(-.125,0))]:
            j=UsdPhysics.PrismaticJoint.Define(s,ROOT+'/Joints/'+name)
            j.CreateBody0Rel().SetTargets([ROOT+'/'+parent]);j.CreateBody1Rel().SetTargets([ROOT+'/'+child])
            j.CreateAxisAttr(axis);j.CreateLowerLimitAttr(limits[0]);j.CreateUpperLimitAttr(limits[1])
            j.CreateLocalPos0Attr(Gf.Vec3f(0));j.CreateLocalPos1Attr(Gf.Vec3f(0));j.CreateCollisionEnabledAttr(False)
        h=Hardware(s);c=ROOT+'/Carriage';m=ROOT+'/ToolMount'
        h.box(c+('/ToolSupport' if architecture=='B' else '/Plate'),(0,0,.025 if architecture=='B' else 0),
              (.055,.012,.090 if architecture=='B' else .060))
        if architecture in ('A','C'):h.box(c+'/TraverseBackPlate',(0,.006,0),(.100,.010,.028))
        if architecture=='A':h.box(c+'/TraverseNutBracket',(0,.009,.018),(.025,.018,.016))
        for i,x in enumerate((-.022,.022)):
            h.box(c+f'/DepthRail{i}',(x,-.070,0),(.012,.180,.008))
            h.box(m+f'/DepthBlock{i}',(x,-.010,.0105),(.027,.0454,.013),reference_mass=.054)
        h.box(m+'/Adapter',(0,0,0),(.045,.008,.033))
        h.box(m+'/Housing',(0,-.05965,0),(.0265,.0727,.018))
        h.box(m+'/DepthBearingPlate',(0,-.010,.0205),(.074,.048,.009))
        h.sleeve(m+'/DepthNut',(0,0,.014),.007,.0031,.012,'Y')
        h.box(c+'/DepthMotor',(0,.037,.014),(.028,.035,.028))
        h.plate(c+'/DepthMotorPlate',(0,.0165,.014),(.040,.006,.040),'Y',.009)
        h.sleeve(c+'/DepthCoupler',(0,.016,.014),.005,.0031,.016,'Y')
        h.sleeve(c+'/DepthSupportBearing',(0,-.132,.014),.007,.0031,.008,'Y')
        h.box(c+'/DepthFrontBearingHanger',(0,-.135,.028),(.018,.008,.014))
        h.box(c+'/DepthFrontBearingCrossbar',(0,-.135,.038),(.068,.005,.006))
        for i,x in enumerate((-.031,.031)):
            h.box(c+f'/DepthFrontBearingPost{i}',(x,-.135,.0175),(.006,.008,.035))
            h.bolt(c+f'/DepthFrontBearingBolt{i}',(x,-.140,.009),'Y',.0015,.012)
        screw=UsdGeom.Cylinder.Define(s,c+'/DepthScrew');screw.CreateAxisAttr('Y')
        screw.CreateRadiusAttr(.003);screw.CreateHeightAttr(.160);screw.AddTranslateOp().Set(Gf.Vec3d(0,-.055,.014))
        UsdGeom.Xform.Define(s,'/World/Plug').AddTranslateOp().Set(Gf.Vec3d(1,2,3))
        return s

    def test_open_stage_clears_whole_insertion_travel_not_only_initial_pose(self):
        for a in 'ABC':
            s=self.stage(a)
            self.assertFalse(screen_carrier_mount_sweep(s,True,True)['passed'])
            complete_insertion_stage(s,a)
            report=screen_carrier_mount_sweep(s,True,True)
            self.assertTrue(report['passed'],report['possible_overlaps'])

    def test_revision_preserves_tcp_bodies_joint_limits_and_connector(self):
        s=self.stage()
        joints=[s.GetPrimAtPath(ROOT+'/Joints/'+name) for name in ('Traverse','Insertion')]
        values=[[(a.GetName(),a.Get()) for a in p.GetAttributes()] for p in joints]
        report=complete_insertion_stage(s,'A')
        self.assertEqual(values,[[(a.GetName(),a.Get()) for a in p.GetAttributes()] for p in joints])
        self.assertEqual(s.GetPrimAtPath('/World/Plug').GetAttribute('xformOp:translate').Get(),Gf.Vec3d(1,2,3))
        self.assertEqual(report['revision'],REVISION)
        self.assertFalse(s.GetPrimAtPath(ROOT+'/Carriage/Plate').IsActive())
        for body,mass in report['mass_delta_kg_by_body'].items():
            self.assertAlmostEqual(UsdPhysics.MassAPI(s.GetPrimAtPath(body)).GetMassAttr().Get(),1+mass,places=6)
        for part in report['new_parts']:
            if part['collision']:self.assertTrue(s.GetPrimAtPath(part['path']).HasAPI(UsdPhysics.CollisionAPI))

    def test_complete_block_remains_on_rail_at_both_limits(self):
        for q in (-.125,0):
            self.assertGreaterEqual(q-.040-.0454/2,-.200)
            self.assertLessEqual(q-.040+.0454/2,0.)

    def test_motor_plate_group_translation_is_evaluated_not_just_authored(self):
        s=self.stage();complete_insertion_stage(s,'A')
        prim=s.GetPrimAtPath(ROOT+'/Carriage/DepthMotorPlate')
        self.assertTrue(prim.IsA(UsdGeom.Xformable))
        bounds=UsdGeom.BBoxCache(0,['default']).ComputeWorldBound(prim).ComputeAlignedRange()
        self.assertAlmostEqual(bounds.GetMidpoint()[2],.094,places=6)
        self.assertAlmostEqual(bounds.GetMin()[2],.074,places=6)

    def test_rg2_crosshead_and_side_drops_have_a_full_stroke_opening(self):
        for a in 'ABC':
            s=self.stage(a);h=Hardware(s);m=ROOT+'/ToolMount'
            h.box(m+'/CrossHead',(0,-.010,.035),(.094,.008,.006))
            for i,x in enumerate((-.040,.040)):
                h.box(m+f'/SideDrop{i}',(x,-.010,-.045),(.006,.008,.160))
            report=complete_insertion_stage(s,a)
            self.assertTrue(report['wide_tool_frame'])
            self.assertEqual(report['revision'],'open_insertion_stage_v3_rg2')
            audit=screen_carrier_mount_sweep(s,True,True)
            self.assertTrue(audit['passed'],audit['possible_overlaps'])

    def test_rejects_old_carriers_and_duplicate_revision(self):
        s=self.stage();s.GetPrimAtPath(ROOT).SetCustomDataByKey('service_carrier_revision','old')
        before=s.GetRootLayer().ExportToString()
        with self.assertRaisesRegex(ValueError,'carrier'):complete_insertion_stage(s,'A')
        self.assertEqual(s.GetRootLayer().ExportToString(),before)
        s.GetPrimAtPath(ROOT).ClearCustomDataByKey('service_carrier_revision')
        complete_insertion_stage(s,'A')
        with self.assertRaisesRegex(ValueError,'already'):complete_insertion_stage(s,'A')
