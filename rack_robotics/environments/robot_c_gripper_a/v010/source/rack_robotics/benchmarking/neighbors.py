"""Occupied adjacent-port fixture, authored before physics only.

Geometry, passive latch and cable joints reference the unchanged baseline
objects. Only neighboring housings are fixed to their sockets: a deliberately
restrained-obstacle test, not a test of neighboring connectors' retention force.
The target connector and every target collision/constraint remain unchanged.
"""
import math
from .spec import cable_route


class OccupiedNeighbors:
    def __init__(self, stage, port, ports, segments=36, length=.015):
        from pxr import Gf, UsdGeom, UsdPhysics
        self.stage = stage; self.length = length; self.rows = []
        self.maximum_gap = 0.; self.maximum_housing_drift = 0.
        root = '/World/OccupiedNeighbors'
        if stage.GetPrimAtPath(root): raise ValueError('Neighbor fixture already exists')
        if not 1 <= port <= len(ports): raise ValueError('Invalid target port')
        for source in ('/World/Plug', '/World/Latch', '/World/LatchHinge', '/World/Cable'):
            if not stage.GetPrimAtPath(source): raise ValueError(f'Missing source geometry: {source}')
        UsdGeom.Xform.Define(stage, root)
        pivot = UsdPhysics.Joint(stage.GetPrimAtPath('/World/LatchHinge')).GetLocalPos0Attr().Get()
        rest = UsdPhysics.DriveAPI(stage.GetPrimAtPath('/World/LatchHinge'), 'angular').GetTargetPositionAttr().Get()
        for index in (port-2, port):
            if index < 0 or index >= len(ports): continue
            prefix = f'{root}/Port{index+1:02d}'
            UsdGeom.Xform.Define(stage, prefix)
            for name in ('Plug', 'Latch', 'LatchHinge', 'Cable'):
                prim = stage.DefinePrim(f'{prefix}/{name}')
                prim.GetReferences().AddInternalReference(f'/World/{name}')
            position = Gf.Vec3d(*ports[index][1])
            plug = stage.GetPrimAtPath(prefix+'/Plug')
            xf = UsdGeom.Xformable(plug)
            t = plug.GetAttribute('xformOp:translate'); t.Set(position)
            q = plug.GetAttribute('xformOp:orient')
            qop = UsdGeom.XformOp(q) if q else xf.AddOrientOp()
            qop.Set(Gf.Quatf(1)); xf.SetXformOpOrder([UsdGeom.XformOp(t), qop])
            latch = stage.GetPrimAtPath(prefix+'/Latch')
            latch.GetAttribute('xformOp:translate').Set(position+Gf.Vec3d(pivot))
            latch.GetAttribute('xformOp:orient').Set(Gf.Quatf(Gf.Rotation(Gf.Vec3d(1,0,0), rest).GetQuat()))
            hinge = UsdPhysics.Joint(stage.GetPrimAtPath(prefix+'/LatchHinge'))
            hinge.GetBody0Rel().SetTargets([prefix+'/Plug'])
            hinge.GetBody1Rel().SetTargets([prefix+'/Latch'])
            hold = UsdPhysics.FixedJoint.Define(stage, prefix+'/HousingFixture')
            hold.CreateBody1Rel().SetTargets([prefix+'/Plug'])
            hold.CreateLocalPos0Attr(Gf.Vec3f(position)); hold.CreateLocalPos1Attr(Gf.Vec3f(0))
            route = cable_route(position+Gf.Vec3d(0,.019,0), 0., 5, segments, length)
            paths = []
            for number, row in enumerate(route):
                path = f'{prefix}/Cable/Link{number:02d}'; link = stage.GetPrimAtPath(path)
                if not link: raise ValueError(f'Missing referenced cable segment: {path}')
                link.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*row['position']))
                w,x,y,z = row['quaternion']
                link.GetAttribute('xformOp:orient').Set(Gf.Quatf(w, Gf.Vec3f(x,y,z)))
                joint = UsdPhysics.Joint(stage.GetPrimAtPath(f'{prefix}/Cable/Joint{number:02d}'))
                joint.GetBody0Rel().SetTargets([paths[-1] if paths else prefix+'/Plug'])
                joint.GetBody1Rel().SetTargets([path])
                paths.append(path)
            self.rows.append({'port': index+1, 'prefix': prefix, 'housing_origin': list(position), 'links': paths})
        self.refresh_visuals()

    def reset_metrics(self):
        self.maximum_gap = 0.; self.maximum_housing_drift = 0.

    def refresh_visuals(self):
        from pxr import Gf, UsdGeom
        for row in self.rows:
            plug = UsdGeom.Xformable(self.stage.GetPrimAtPath(row['prefix']+'/Plug')).ComputeLocalToWorldTransform(0)
            self.maximum_housing_drift = max(self.maximum_housing_drift,
                math.dist(plug.ExtractTranslation(), row['housing_origin']))
            previous = plug.Transform(Gf.Vec3d(0,.019,0)); points = [previous]
            for path in row['links']:
                matrix = UsdGeom.Xformable(self.stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(0)
                start = matrix.Transform(Gf.Vec3d(0,-self.length/2,0))
                end = matrix.Transform(Gf.Vec3d(0,self.length/2,0))
                self.maximum_gap = max(self.maximum_gap, (start-previous).GetLength())
                points.append(end); previous = end
            curve = UsdGeom.BasisCurves(self.stage.GetPrimAtPath(row['prefix']+'/Cable/Jacket'))
            curve.GetPointsAttr().Set([Gf.Vec3f(p) for p in points])

    def report(self, contacts=None, metric_interval='initial_geometry_before_physics'):
        pairs = []
        for pair in (contacts or {}).get('pairs', []):
            paths = pair['colliders']
            if (any(p.startswith('/World/Robot/') for p in paths)
                    and any(p.startswith('/World/OccupiedNeighbors/') for p in paths)
                    and pair['peak_pair_contact_force_n'] > 0):
                pairs.append(pair)
        stable = self.maximum_gap <= .0015 and self.maximum_housing_drift <= .0005
        return {'schema': 'occupied_neighbors_v1', 'ports': [row['port'] for row in self.rows],
            'fixtures': self.rows, 'maximum_cable_joint_gap_m': self.maximum_gap,
            'maximum_housing_drift_m': self.maximum_housing_drift, 'metric_interval': metric_interval,
            'fixture_stable': stable, 'robot_neighbor_contact_pairs': pairs,
            'no_reported_robot_neighbor_contact': not pairs if contacts is not None else None,
            'contact_reporting_errors': (contacts or {}).get('reporting_errors'),
            'scope': 'Adjacent occupied ports with restrained housings, passive latch hinges and dynamic free-ended cables; not calibrated retention, cable tension, or all-row routing coverage.'}
