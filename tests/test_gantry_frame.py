import unittest
from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade
from rack_robotics.hardware_detail import Hardware, ROOT
from rack_robotics.gantry_frame import complete_gantry_frame, open_mgn12h, REVISION
from rack_robotics.carrier_mount_screen import screen_carrier_mount_sweep


class GantryFrameTest(unittest.TestCase):
    def stage(self):
        s=Usd.Stage.CreateInMemory();robot=UsdGeom.Xform.Define(s,ROOT).GetPrim()
        robot.SetCustomDataByKey('insertion_revision','open_insertion_stage_v2')
        UsdShade.Material.Define(s,'/World/Materials/RobotSteel')
        UsdShade.Material.Define(s,'/World/Materials/RobotAnodized')
        robot.SetCustomDataByKey('hardware_revision','drive_connections_v4')
        for name,position,mass in [('Frame',(0,0,0),4.2),('Bridge',(0,.72,1.8),.9),
                                    ('Carriage',(.15,.68,1.8),.5),('ToolMount',(.15,.68,1.8),.5)]:
            p=UsdGeom.Xform.Define(s,ROOT+'/'+name);p.AddTranslateOp().Set(Gf.Vec3d(*position))
            UsdPhysics.RigidBodyAPI.Apply(p.GetPrim());UsdPhysics.MassAPI.Apply(p.GetPrim()).CreateMassAttr(mass)
        for name,parent,child,anchor,axis,limits in [('Lift','Frame','Bridge',(0,.72,1.8),'Z',(-.7,0)),
                ('Traverse','Bridge','Carriage',(0,-.04,0),'X',(-.21,.21)),
                ('Insertion','Carriage','ToolMount',(0,0,0),'Y',(-.125,0))]:
            j=UsdPhysics.PrismaticJoint.Define(s,ROOT+'/Joints/'+name)
            j.CreateBody0Rel().SetTargets([ROOT+'/'+parent]);j.CreateBody1Rel().SetTargets([ROOT+'/'+child])
            j.CreateAxisAttr(axis);j.CreateLowerLimitAttr(limits[0]);j.CreateUpperLimitAttr(limits[1])
            j.CreateLocalPos0Attr(Gf.Vec3f(*anchor));j.CreateLocalPos1Attr(Gf.Vec3f(0))
            j.CreateCollisionEnabledAttr(False)
        h=Hardware(s);f=ROOT+'/Frame';b=ROOT+'/Bridge';c=ROOT+'/Carriage'
        for i,x in enumerate((-.26,.26)):
            h.box(f+f'/Upright{i}',(x,.735,1.45),(.04,.04,.98))
            h.box(f+f'/Guide{i}',(x,.710,1.45),(.012,.008,.92))
            h.box(b+f'/GuideBlock{i}',(x,-.011,0),(.027,.013,.0454))
            for k,z in enumerate((1.075,1.831)):h.box(f+f'/Stop{i}_{k}',(x,.698,z),(.023,.016,.008))
            h.box(f+f'/Standoff{i}_1',(x,.655,1.90),(.05,.16,.008))
            h.box(f+f'/PostClamp{i}_1',((-.285,.285)[i],.593,1.90),(.04,.006,.05))
            for k,z in enumerate((1.884,1.916)):h.bolt(f+f'/RackBolt{i}_1_{k}',((-.285,.285)[i],.598,z))
        h.box(b+'/Beam',(0,0,0),(.54,.032,.04))
        h.box(b+'/XGuide',(0,-.021,0),(.52,.008,.012))
        for i,x in enumerate((-.025,.025)):h.box(c+f'/TraverseBlock{i}',(x,.0125,0),(.0454,.013,.027))
        h.box(c+'/TraverseBackPlate',(0,.010,0),(.100,.008,.028))
        h.box(c+'/BeltClampSpacer',(0,.020,.026),(.020,.040,.005))
        h.box(c+'/BeltClampPlate',(0,.075,.026),(.05,.09,.005))
        return s

    def test_full_limits_reject_old_and_clear_new_interfaces(self):
        s=self.stage()
        self.assertFalse(screen_carrier_mount_sweep(s,True,True)['passed'])
        complete_gantry_frame(s,'C')
        r=screen_carrier_mount_sweep(s,True,True)
        self.assertTrue(r['passed'],r['possible_overlaps'])

    def test_preserves_joint_parameters_and_collision_filters(self):
        s=self.stage()
        joints=[p for p in s.Traverse() if p.IsA(UsdPhysics.Joint)]
        old=[[(a.GetName(),a.Get()) for a in p.GetAttributes()] for p in joints]
        complete_gantry_frame(s,'C')
        self.assertEqual(old,[[(a.GetName(),a.Get()) for a in p.GetAttributes()] for p in joints])

    def test_raceway_has_real_opening_and_collision_enabled_solids(self):
        s=self.stage();h=Hardware(s)
        open_mgn12h(h,ROOT+'/Carriage/TestGuide',(0,0,0),0,1,-1)
        bounds=UsdGeom.BBoxCache(0,['default'])
        rail=Gf.Range3d(Gf.Vec3d(-.1,-.008,-.006),Gf.Vec3d(.1,0,.006))
        for p in h.parts:
            prim=s.GetPrimAtPath(p['path']);r=bounds.ComputeWorldBound(prim).ComputeAlignedRange()
            self.assertTrue(prim.HasAPI(UsdPhysics.CollisionAPI))
            self.assertTrue(any(r.GetMax()[i]<=rail.GetMin()[i] or r.GetMin()[i]>=rail.GetMax()[i] for i in range(3)))
        self.assertEqual(h.added_mass,{})
        self.assertAlmostEqual(sum(p['estimated_mass_kg'] for p in h.parts),.054)

    def test_recorded_mass_delta_and_duplicate_guard(self):
        s=self.stage();old={str(p.GetPath()):UsdPhysics.MassAPI(p).GetMassAttr().Get()
                           for p in s.Traverse() if p.HasAPI(UsdPhysics.MassAPI)}
        r=complete_gantry_frame(s,'C');self.assertEqual(r['revision'],REVISION)
        for owner,delta in r['mass_delta_kg_by_body'].items():
            self.assertAlmostEqual(UsdPhysics.MassAPI(s.GetPrimAtPath(owner)).GetMassAttr().Get(),old[owner]+delta,places=6)
        with self.assertRaisesRegex(ValueError,'already'):complete_gantry_frame(s,'C')

    def test_lift_mount_bolts_reach_the_catalog_pattern_above_traverse_sweep(self):
        s=self.stage();complete_gantry_frame(s,'C')
        for side,x in enumerate((-.26,.26)):
            for row,dz in enumerate((-.010,.010)):
                for col,dx in enumerate((-.010,.010)):
                    prim=s.GetPrimAtPath(ROOT+f'/Bridge/GuideInterfaces/BlockBolt{side}_{row}_{col}')
                    p=prim.GetAttribute('xformOp:translate').Get()
                    self.assertAlmostEqual(p[0],x+dx)
                    self.assertAlmostEqual(p[2],.05+dz)
                    # Bolt begins at the bracket front and enters 3.5 mm of
                    # the block crown; the nominal M3 tapped depth is 3.5 mm.
                    self.assertAlmostEqual(p[1]-.0095/2,-.025)
                    self.assertAlmostEqual(p[1]+.0095/2,-.0155)
        # Whole block stays on the vertical rail at both software limits.
        self.assertGreater(1.8-.7+.05-.0454/2,.99)
        self.assertLess(1.8+.05+.0454/2,1.91)

    def test_rejects_other_architectures_and_old_carriers(self):
        for arch in ('A','B'):
            with self.assertRaisesRegex(ValueError,'specific'):complete_gantry_frame(self.stage(),arch)
        s=self.stage();s.GetPrimAtPath(ROOT).SetCustomDataByKey('service_carrier_revision','old')
        with self.assertRaisesRegex(ValueError,'carrier'):complete_gantry_frame(s,'C')

    def test_open_frame_carriers_require_explicit_compatible_revision(self):
        from rack_robotics.service_carriers import complete_service_carriers,carrier_metrics
        s=self.stage()
        with self.assertRaisesRegex(ValueError,'v2'):complete_service_carriers(s,'C',open_frame=True)
        complete_gantry_frame(s,'C')
        with self.assertRaisesRegex(ValueError,'separately'):complete_service_carriers(s,'C')
        r=complete_service_carriers(s,'C',open_frame=True)
        self.assertEqual(r['revision'],'passive_service_carriers_corexz_open_v1')
        self.assertEqual(sum(c['links'] for c in r['chains']),81)
        self.assertLess(carrier_metrics(s)['maximum_anchor_gap_m'],1e-6)
        audit=screen_carrier_mount_sweep(s,True,True)
        self.assertTrue(audit['passed'],audit['possible_overlaps'])
