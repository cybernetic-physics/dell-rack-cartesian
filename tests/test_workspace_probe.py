import math
import unittest
from rack_robotics.workspace_probe import fixture_architecture, retracted_raster, telescoping_retracted_raster, move_duration, interpolate, robot_contact_violations


class WorkspaceProbeTest(unittest.TestCase):
    limits = {'x':(-.21,.21), 'y':(-.125,0.), 'z':(-.7,0.)}

    def test_supported_fixture_selection(self):
        config = dict(gripper='A_precision_parallel', brake_revision='saved', service_carrier_revision='saved')
        for robot, expected in [('A_dual_supported_screw','A'), ('B_side_telescoping','B'), ('C_CoreXZ','C')]:
            self.assertEqual(fixture_architecture(dict(config, robot=robot)), expected)
            self.assertEqual(fixture_architecture(dict(config, robot=robot,gripper='C_rack_jaw')), expected)
        for overrides in [dict(robot='D_unknown'), dict(robot='A', gripper='B'),
                          dict(robot='A', brake_revision=None), dict(robot='C', service_carrier_revision=None)]:
            with self.assertRaises(ValueError): fixture_architecture(dict(config, **overrides))

    def test_telescoping_grid_preserves_independent_extension_coverage(self):
        limits={'x_outer':(0.,.2),'x_inner':(0.,.2),'y':(-.125,0.),'z':(-.7,0.)}
        points=telescoping_retracted_raster(limits)
        self.assertEqual(len(points),46)
        expected={(a,b) for a in (0.,.1,.2) for b in (0.,.1,.2)}
        for row in range(5):
            samples=points[row*9:(row+1)*9]
            self.assertEqual({(p['target']['x_outer'],p['target']['x_inner']) for p in samples},expected)
            self.assertEqual(len({p['target']['z'] for p in samples}),1)
        for point in points:
            self.assertEqual(point['target']['y'],0.)
            for key,value in point['target'].items():
                self.assertLessEqual(limits[key][0],value);self.assertLessEqual(value,limits[key][1])
        for a,b in zip(points,points[1:]):
            self.assertLessEqual(sum(a['target'][k]!=b['target'][k] for k in limits),1)
        for invalid in ({},dict(limits,x_inner=(0.,0.)),dict(limits,z=(math.nan,0.))):
            with self.assertRaises(ValueError):telescoping_retracted_raster(invalid)

    def test_raster_covers_boundaries_without_extending_tool(self):
        points = retracted_raster(self.limits)
        self.assertEqual(len(points),16)
        self.assertEqual({p['target']['z'] for p in points},{0.,-.175,-.35,-.5249999999999999,-.7})
        self.assertEqual({p['target']['x'] for p in points},{-.21,0.,.21})
        for p in points:
            self.assertEqual(p['target']['y'],0)
            for k,v in p['target'].items():
                self.assertLessEqual(self.limits[k][0],v)
                self.assertGreaterEqual(self.limits[k][1],v)
        for a,b in zip(points,points[1:]):
            self.assertLessEqual(sum(a['target'][k]!=b['target'][k] for k in self.limits),1)

    def test_quintic_endpoints_and_speed_bound(self):
        start = {'x':.15,'y':0.,'z':0.}
        target = {'x':-.21,'y':0.,'z':-.7}
        duration = move_duration(start,target)
        self.assertEqual(interpolate(start,target,0),start)
        self.assertEqual(interpolate(start,target,1),target)
        prior = start
        for i in range(1,1001):
            current = interpolate(start,target,i/1000)
            self.assertLessEqual(max(abs(current[k]-prior[k]) for k in start)/(duration/1000),.0600001)
            prior = current

    def test_fail_closed_inputs(self):
        for limits in ({},dict(self.limits,x=(0,0)),dict(self.limits,z=(float('nan'),0))):
            with self.assertRaises(ValueError): retracted_raster(limits)
        with self.assertRaises(ValueError): move_duration({'x':math.inf},{'x':0})
        with self.assertRaises(ValueError): interpolate({'x':0},{'x':1},1.1)

    def test_contacts_include_self_carrier_rack_and_plug(self):
        pairs = [{'colliders':['/World/Robot/ToolMount/Part', other],
                  'peak_pair_contact_force_n':.11} for other in
                 ('/World/Robot/ServiceCarriers/Lift/Link000/Wall','/World/Rack/Panel','/World/Plug/Boot')]
        pairs.append({'colliders':['/World/Plug/Housing','/World/PortRow/Port01/Lip'],
                      'peak_pair_contact_force_n':10.})
        self.assertEqual(robot_contact_violations(pairs),pairs[:3])
        pairs[0]['peak_pair_contact_force_n'] = float('nan')
        self.assertEqual(len(robot_contact_violations(pairs)),3)
