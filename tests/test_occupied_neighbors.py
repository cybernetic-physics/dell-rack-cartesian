import unittest
from pxr import Gf, Usd, UsdGeom, UsdPhysics
from rack_robotics.benchmarking.neighbors import OccupiedNeighbors


def source_stage():
    stage = Usd.Stage.CreateInMemory()
    UsdGeom.Xform.Define(stage, '/World')
    for name in ('Plug', 'Latch'):
        body = UsdGeom.Xform.Define(stage, '/World/'+name)
        body.AddTranslateOp().Set(Gf.Vec3d(.2,.479,1.66))
        body.AddOrientOp().Set(Gf.Quatf(1))
        UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
        shape = UsdGeom.Cube.Define(stage, '/World/'+name+'/Body')
        UsdPhysics.CollisionAPI.Apply(shape.GetPrim())
    hinge = UsdPhysics.RevoluteJoint.Define(stage, '/World/LatchHinge')
    hinge.CreateBody0Rel().SetTargets(['/World/Plug'])
    hinge.CreateBody1Rel().SetTargets(['/World/Latch'])
    hinge.CreateLocalPos0Attr(Gf.Vec3f(0,-.009,.0036))
    UsdPhysics.DriveAPI.Apply(hinge.GetPrim(), 'angular').CreateTargetPositionAttr(8.)
    UsdGeom.Xform.Define(stage, '/World/Cable')
    UsdGeom.BasisCurves.Define(stage, '/World/Cable/Jacket').CreatePointsAttr([])
    for i in range(2):
        path = f'/World/Cable/Link{i:02d}'
        link = UsdGeom.Capsule.Define(stage, path)
        link.AddTranslateOp().Set(Gf.Vec3d(0)); link.AddOrientOp().Set(Gf.Quatf(1))
        UsdPhysics.RigidBodyAPI.Apply(link.GetPrim()); UsdPhysics.CollisionAPI.Apply(link.GetPrim())
        joint = UsdPhysics.Joint.Define(stage, f'/World/Cable/Joint{i:02d}')
        joint.CreateBody0Rel().SetTargets(['/World/Plug' if i==0 else '/World/Cable/Link00'])
        joint.CreateBody1Rel().SetTargets([path])
    return stage


class OccupiedNeighborTests(unittest.TestCase):
    def setUp(self):
        self.stage = source_stage()
        self.ports = [(f'/World/Port{i+1}', (.2-i*.025,.429,1.66)) for i in range(5)]

    def test_adjacent_geometry_and_joints_do_not_attach_to_target(self):
        initial = self.stage.GetPrimAtPath('/World/Plug').GetAttribute('xformOp:translate').Get()
        fixture = OccupiedNeighbors(self.stage, 3, self.ports, segments=2)
        self.assertEqual(fixture.report()['ports'], [2,4])
        self.assertLess(fixture.maximum_gap, 1e-9)
        self.assertEqual(self.stage.GetPrimAtPath('/World/Plug').GetAttribute('xformOp:translate').Get(), initial)
        for row in fixture.rows:
            prefix = row['prefix']
            for name, targets in [('LatchHinge', [prefix+'/Plug',prefix+'/Latch']),
                                  ('Cable/Joint00', [prefix+'/Plug',prefix+'/Cable/Link00']),
                                  ('Cable/Joint01', [prefix+'/Cable/Link00',prefix+'/Cable/Link01'])]:
                joint = UsdPhysics.Joint(self.stage.GetPrimAtPath(prefix+'/'+name))
                self.assertEqual([str(p) for p in joint.GetBody0Rel().GetTargets()+joint.GetBody1Rel().GetTargets()], targets)
            self.assertTrue(UsdPhysics.CollisionAPI(self.stage.GetPrimAtPath(prefix+'/Plug/Body')).GetCollisionEnabledAttr().Get())
        with self.assertRaises(ValueError): OccupiedNeighbors(self.stage, 3, self.ports, segments=2)

    def test_edge_port_only_has_one_neighbor_and_no_missing_contact_claim(self):
        fixture = OccupiedNeighbors(self.stage, 1, self.ports, segments=2)
        self.assertEqual(fixture.report()['ports'], [2])
        self.assertIsNone(fixture.report()['no_reported_robot_neighbor_contact'])
        self.assertTrue(fixture.report({'pairs': [], 'reporting_errors': []})['no_reported_robot_neighbor_contact'])
        pair = {'colliders': ['/World/Robot/Finger', '/World/OccupiedNeighbors/Port02/Plug/Body'],
                'peak_pair_contact_force_n': .01}
        self.assertFalse(fixture.report({'pairs': [pair]})['no_reported_robot_neighbor_contact'])

    def test_metrics_reset_and_drift_gate(self):
        fixture = OccupiedNeighbors(self.stage, 1, self.ports, segments=2)
        fixture.maximum_housing_drift = .001
        self.assertFalse(fixture.report()['fixture_stable'])
        fixture.reset_metrics()
        self.assertTrue(fixture.report()['fixture_stable'])
