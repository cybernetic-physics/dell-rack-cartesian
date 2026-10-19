import math
import unittest
from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade
from rack_robotics.service_carriers import (
    ROOT,PITCH,SEPARATION,LINK_MASS,u_link_points,orientation,
    complete_service_carriers,carrier_metrics,initialize_cartesian_states,initialize_prismatic_states)


class ServiceCarrierTest(unittest.TestCase):
    def test_explicit_tool_startup_uses_geometry_without_pose_or_target_change(self):
        stage=self.stage()
        mount=ROOT+'/ToolMount'
        for name,q in [('LeftJaw',-.0093),('RightJaw',.0093)]:
            body=UsdGeom.Xform.Define(stage,ROOT+'/'+name)
            body.AddTranslateOp().Set(Gf.Vec3d(.15+q,.68,1.8))
            j=UsdPhysics.PrismaticJoint.Define(stage,ROOT+'/Joints/'+name)
            j.CreateBody0Rel().SetTargets([mount]);j.CreateBody1Rel().SetTargets([body.GetPath()])
            j.CreateLocalPos0Attr(Gf.Vec3f(0));j.CreateLocalPos1Attr(Gf.Vec3f(0))
            j.CreateAxisAttr('X');j.CreateLowerLimitAttr(-.01);j.CreateUpperLimitAttr(.01)
        before={name:stage.GetPrimAtPath(ROOT+'/'+name).GetAttribute('xformOp:translate').Get()
                for name in ('LeftJaw','RightJaw')}
        reports=initialize_prismatic_states(stage,['LeftJaw','RightJaw'])
        self.assertAlmostEqual(reports[0]['position_m'],-.0093)
        self.assertAlmostEqual(reports[1]['position_m'],.0093)
        for name,p in before.items():self.assertEqual(stage.GetPrimAtPath(ROOT+'/'+name).GetAttribute('xformOp:translate').Get(),p)

    def joint_stage(self):
        stage=self.stage()
        for name,a,b,anchor,axis in [('Lift','Frame','Bridge',(0,.72,1.8),'Z'),
                                   ('Traverse','Bridge','Carriage',(0,-.04,0),'X'),
                                   ('Insertion','Carriage','ToolMount',(0,0,0),'Y')]:
            j=UsdPhysics.PrismaticJoint.Define(stage,ROOT+'/Joints/'+name)
            j.CreateBody0Rel().SetTargets([ROOT+'/'+a]); j.CreateBody1Rel().SetTargets([ROOT+'/'+b])
            j.CreateLocalPos0Attr(Gf.Vec3f(*anchor)); j.CreateLocalPos1Attr(Gf.Vec3f(0))
            j.CreateAxisAttr(axis); j.CreateLowerLimitAttr(-.7); j.CreateUpperLimitAttr(.7)
        return stage

    def test_startup_state_matches_authored_geometry_not_drive_targets(self):
        stage=self.joint_stage(); original=stage.GetRootLayer().ExportToString()
        drive=UsdPhysics.DriveAPI.Apply(stage.GetPrimAtPath(ROOT+'/Joints/Traverse'),'linear')
        drive.CreateTargetPositionAttr(-.2)
        reports=initialize_cartesian_states(stage,'A')
        self.assertAlmostEqual(reports[-1]['position_m'],.15)
        self.assertAlmostEqual(drive.GetTargetPositionAttr().Get(),-.2)
        for report in reports:
            prim=stage.GetPrimAtPath(report['joint'])
            self.assertEqual(prim.GetAttribute('state:linear:physics:velocity').Get(),0.)
            self.assertIn('PhysicsJointStateAPI:linear',prim.GetMetadata('apiSchemas').GetAddedOrExplicitItems())
        self.assertEqual(stage.GetPrimAtPath(ROOT+'/Carriage').GetAttribute('xformOp:translate').Get(),Gf.Vec3d(.15,.68,1.8))
        self.assertEqual(stage.GetPrimAtPath('/World/Plug').GetAttribute('xformOp:translate').Get(),Gf.Vec3d(1,2,3))

    def test_startup_rejects_inconsistent_geometry_before_any_state_write(self):
        stage=self.joint_stage()
        stage.GetPrimAtPath(ROOT+'/ToolMount').GetAttribute('xformOp:translate').Set(Gf.Vec3d(.17,.68,1.8))
        with self.assertRaisesRegex(ValueError,'Inconsistent'): initialize_cartesian_states(stage,'A')
        self.assertFalse(stage.GetPrimAtPath(ROOT+'/Joints/Lift').GetAttribute('state:linear:physics:position'))

    def test_startup_respects_rotated_joint_axis(self):
        stage=self.joint_stage(); joint=UsdPhysics.PrismaticJoint(stage.GetPrimAtPath(ROOT+'/Joints/Traverse'))
        joint.CreateAxisAttr('Y')
        joint.CreateLocalRot0Attr(Gf.Quatf(Gf.Rotation(Gf.Vec3d(0,0,1),-90).GetQuat()))
        reports=initialize_cartesian_states(stage,'C')
        self.assertAlmostEqual(reports[-1]['position_m'],.15)

    def stage(self,architecture='A'):
        stage=Usd.Stage.CreateInMemory()
        root=UsdGeom.Xform.Define(stage,ROOT).GetPrim()
        root.SetCustomDataByKey('hardware_revision','test')
        for name in ('RobotSteel','RobotAnodized'):
            UsdShade.Material.Define(stage,'/World/Materials/'+name)
        poses={'Frame':(0,0,0),'Bridge':(0,.72,1.8),'Carriage':(.15,.68,1.8),'ToolMount':(.15,.68,1.8)}
        if architecture=='B': poses.update(LiftCarriage=(-.20,.78,1.8),MiddleBoom=(-.195,.73,1.8),Carriage=(-.19,.68,1.8),ToolMount=(-.19,.68,1.8))
        for name,position in poses.items():
            body=UsdGeom.Xform.Define(stage,ROOT+'/'+name); body.AddTranslateOp().Set(Gf.Vec3d(*position))
            UsdPhysics.RigidBodyAPI.Apply(body.GetPrim()); UsdPhysics.MassAPI.Apply(body.GetPrim()).CreateMassAttr(1.)
        UsdGeom.Xform.Define(stage,'/World/Plug').AddTranslateOp().Set(Gf.Vec3d(1,2,3))
        return stage

    def test_polygon_exact_pitch_endpoints_and_minimum_radius(self):
        points,angles=u_link_points((0,0,0),(1,0,0),(0,0,1),15,7)
        self.assertEqual(len(angles),28)
        for a,b in zip(points,points[1:]): self.assertAlmostEqual((b-a).GetLength(),PITCH)
        self.assertAlmostEqual(points[-1][0],.16)
        self.assertAlmostEqual(points[-1][2],SEPARATION)
        self.assertGreaterEqual(SEPARATION/2,.038)
        self.assertAlmostEqual(math.degrees(max(b-a for a,b in zip(angles,angles[1:]))),30)

    def test_frame_orientation_follows_plane(self):
        for travel,normal in [((1,0,0),(0,0,1)),((0,0,1),(0,1,0)),((0,-1,0),(0,0,1))]:
            for angle in (0,.5,math.pi):
                q=orientation(travel,normal,angle)
                actual=Gf.Rotation(Gf.Quatd(q)).TransformDir(Gf.Vec3d(1,0,0))
                expected=math.cos(angle)*Gf.Vec3d(*travel)+math.sin(angle)*Gf.Vec3d(*normal)
                self.assertLess((actual-expected).GetLength(),1e-6)

    def test_all_architectures_are_attached_dynamic_and_undriven(self):
        for architecture,count in [('A',3),('B',4),('C',3)]:
            stage=self.stage(architecture); report=complete_service_carriers(stage,architecture)
            self.assertEqual(len(report['chains']),count)
            for chain in report['chains']:
                self.assertAlmostEqual(chain['mass_kg'],chain['links']*LINK_MASS)
                for path in chain['body_paths']:
                    body=stage.GetPrimAtPath(path)
                    self.assertFalse(UsdPhysics.RigidBodyAPI(body).GetKinematicEnabledAttr().Get())
                for suffix in ('FixedEnd','MovingEnd'):
                    joint=UsdPhysics.FixedJoint(stage.GetPrimAtPath(chain['path']+'/'+suffix))
                    self.assertTrue(joint.GetBody0Rel().GetTargets())
                    self.assertTrue(joint.GetBody1Rel().GetTargets())
            for prim in stage.Traverse():
                if str(prim.GetPath()).startswith(ROOT+'/ServiceCarriers'):
                    self.assertFalse(any(s.startswith('PhysicsDriveAPI') for s in prim.GetAppliedSchemas()))
            metrics=carrier_metrics(stage)
            self.assertLess(metrics['maximum_anchor_gap_m'],1e-6)
            self.assertGreater(metrics['minimum_hinge_deg'],-1e-4)
            self.assertLess(metrics['maximum_hinge_deg'],30.0001)
            self.assertEqual(stage.GetPrimAtPath('/World/Plug').GetAttribute('xformOp:translate').Get(),Gf.Vec3d(1,2,3))
            with self.assertRaises(ValueError): complete_service_carriers(stage,architecture)

    def test_crossbars_leave_real_open_wire_passage(self):
        stage=self.stage(); report=complete_service_carriers(stage,'A')
        for chain in report['chains']:
            for prim in stage.GetPrimAtPath(chain['body_paths'][0]).GetChildren():
                c=prim.GetAttribute('xformOp:translate').Get(); s=prim.GetAttribute('xformOp:scale').Get()
                # Origin is not inside any of the four wall collision boxes.
                self.assertTrue(any(abs(c[i])>s[i]/2 for i in range(3)))
                self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))

    def test_insertion_moving_mount_clears_fixed_leg_over_entire_stroke(self):
        stage=self.stage(); complete_service_carriers(stage,'A')
        mount=stage.GetPrimAtPath(ROOT+'/ToolMount')
        fixed=stage.GetPrimAtPath(ROOT+'/ServiceCarriers/Insertion/Link000')
        def overlaps(a,b):
            return all(a.GetMin()[i]<b.GetMax()[i]-1e-6 and b.GetMin()[i]<a.GetMax()[i]-1e-6 for i in range(3))
        for step in range(126):
            mount.GetAttribute('xformOp:translate').Set(Gf.Vec3d(.15,.68-step*.001,1.8))
            cache=UsdGeom.BBoxCache(0,['default']); fixed_box=cache.ComputeWorldBound(fixed).ComputeAlignedRange()
            for prim in stage.GetPrimAtPath(ROOT+'/ToolMount/CarrierMounts').GetChildren():
                self.assertFalse(overlaps(cache.ComputeWorldBound(prim).ComputeAlignedRange(),fixed_box),str(prim.GetPath()))

    def test_traverse_moving_mount_clears_crossmembers_over_lift_stroke(self):
        stage=self.stage('C'); complete_service_carriers(stage,'C')
        carriage=stage.GetPrimAtPath(ROOT+'/Carriage')
        crossmembers=[Gf.Range3d(Gf.Vec3d(-.28,.715,z-.02),Gf.Vec3d(.28,.755,z+.02)) for z in (.98,1.94)]
        for step in range(71):
            carriage.GetAttribute('xformOp:translate').Set(Gf.Vec3d(.15,.68,1.8-step*.01))
            cache=UsdGeom.BBoxCache(0,['default'])
            for prim in stage.GetPrimAtPath(ROOT+'/Carriage/CarrierMounts').GetChildren():
                if not prim.GetName().startswith('TraverseMoving'): continue
                box=cache.ComputeWorldBound(prim).ComputeAlignedRange()
                for obstacle in crossmembers:
                    self.assertFalse(all(box.GetMin()[i]<obstacle.GetMax()[i]-1e-6 and obstacle.GetMin()[i]<box.GetMax()[i]-1e-6 for i in range(3)))

    def test_telescoping_mounts_avoid_fixed_upright_and_other_chain(self):
        stage=self.stage('B'); complete_service_carriers(stage,'B')
        cache=UsdGeom.BBoxCache(0,['default'])
        upright=Gf.Range3d(Gf.Vec3d(-.285,.795,.95),Gf.Vec3d(-.235,.835,1.95))
        def overlaps(a,b):
            return all(a.GetMin()[i]<b.GetMax()[i]-1e-6 and b.GetMin()[i]<a.GetMax()[i]-1e-6 for i in range(3))
        for body in ('LiftCarriage','MiddleBoom','Carriage'):
            for prim in stage.GetPrimAtPath(ROOT+'/'+body+'/CarrierMounts').GetChildren():
                name=prim.GetName()
                if not name.startswith(('Outer','Inner')): continue
                box=cache.ComputeWorldBound(prim).ComputeAlignedRange()
                self.assertFalse(overlaps(box,upright),str(prim.GetPath()))
                other='Inner' if name.startswith('Outer') else 'Outer'
                for link in stage.GetPrimAtPath(ROOT+'/ServiceCarriers/'+other).GetChildren():
                    if not link.GetName().startswith('Link'): continue
                    self.assertFalse(overlaps(box,cache.ComputeWorldBound(link).ComputeAlignedRange()),(str(prim.GetPath()),str(link.GetPath())))

    def test_telescoping_initial_mount_crossings_are_staggered(self):
        stage=self.stage('B'); complete_service_carriers(stage,'B')
        cache=UsdGeom.BBoxCache(0,['default']); parts=[]
        for body in ('LiftCarriage','MiddleBoom','Carriage'):
            for prim in stage.GetPrimAtPath(ROOT+'/'+body+'/CarrierMounts').GetChildren():
                if prim.GetName().startswith(('Outer','Inner')):
                    parts.append((body,str(prim.GetPath()),cache.ComputeWorldBound(prim).ComputeAlignedRange()))
        for index,(owner0,path0,a) in enumerate(parts):
            for owner1,path1,b in parts[index+1:]:
                if owner0==owner1: continue
                self.assertFalse(all(a.GetMin()[i]<b.GetMax()[i]-1e-6 and b.GetMin()[i]<a.GetMax()[i]-1e-6 for i in range(3)),(path0,path1))

    def test_telescoping_rearward_crossings_leave_chain_sag_clearance(self):
        stage=self.stage('B');complete_service_carriers(stage,'B')
        for body,prefix in [('MiddleBoom','OuterMoving'),('Carriage','InnerMoving')]:
            crossings=[]
            for p in stage.GetPrimAtPath(ROOT+'/'+body+'/CarrierMounts').GetChildren():
                if not p.GetName().startswith(prefix):continue
                size=p.GetAttribute('xformOp:scale').Get();c=p.GetAttribute('xformOp:translate').Get()
                if size[1]>.10:
                    crossings.append(p)
                    self.assertGreaterEqual(c[2]-size[2]/2,.0709)
                    self.assertLessEqual(c[2]+size[2]/2,.080)
            self.assertEqual(len(crossings),1)

    def test_telescoping_brackets_clear_for_all_independent_joint_limits(self):
        from rack_robotics.carrier_mount_screen import screen_carrier_mount_sweep
        stage=self.stage('B')
        definitions=[('Lift','Frame','LiftCarriage',(-.20,.78,1.8),'Z',(-.7,0)),
                     ('OuterExtension','LiftCarriage','MiddleBoom',(0,-.05,0),'X',(0,.2)),
                     ('InnerExtension','MiddleBoom','Carriage',(0,-.05,0),'X',(0,.2)),
                     ('Insertion','Carriage','ToolMount',(0,0,0),'Y',(-.125,0))]
        for name,a,b,anchor,axis,limits in definitions:
            j=UsdPhysics.PrismaticJoint.Define(stage,ROOT+'/Joints/'+name)
            j.CreateBody0Rel().SetTargets([ROOT+'/'+a]);j.CreateBody1Rel().SetTargets([ROOT+'/'+b])
            j.CreateLocalPos0Attr(Gf.Vec3f(*anchor));j.CreateLocalPos1Attr(Gf.Vec3f(0))
            j.CreateAxisAttr(axis);j.CreateLowerLimitAttr(limits[0]);j.CreateUpperLimitAttr(limits[1])
        complete_service_carriers(stage,'B')
        report=screen_carrier_mount_sweep(stage)
        self.assertTrue(report['passed'],report)

    def test_gantry_brackets_clear_for_all_independent_joint_limits(self):
        from rack_robotics.carrier_mount_screen import screen_carrier_mount_sweep
        for architecture in ('A','C'):
            stage=self.joint_stage()
            limits={'Lift':(-.7,0),'Traverse':(-.21,.21),'Insertion':(-.125,0)}
            for name,(lower,upper) in limits.items():
                j=UsdPhysics.PrismaticJoint(stage.GetPrimAtPath(ROOT+'/Joints/'+name))
                j.GetLowerLimitAttr().Set(lower);j.GetUpperLimitAttr().Set(upper)
            complete_service_carriers(stage,architecture)
            report=screen_carrier_mount_sweep(stage)
            self.assertTrue(report['passed'],report)


if __name__=='__main__': unittest.main()
