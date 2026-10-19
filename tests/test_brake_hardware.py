import unittest
from pxr import Gf,Usd,UsdGeom,UsdPhysics,UsdShade
from rack_robotics.brake_hardware import add_brake_hardware,ROOT,LENGTH


class BrakeHardwareTest(unittest.TestCase):
    def stage(self,architecture):
        s=Usd.Stage.CreateInMemory()
        r=UsdGeom.Xform.Define(s,ROOT).GetPrim()
        r.SetCustomDataByKey('hardware_revision','drive_connections_v4')
        frame=UsdGeom.Xform.Define(s,ROOT+'/Frame').GetPrim()
        UsdPhysics.RigidBodyAPI.Apply(frame)
        UsdPhysics.MassAPI.Apply(frame).CreateMassAttr(5.)
        UsdShade.Material.Define(s,'/World/Materials/RobotSteel')
        definitions={
            'A':[(f'Motor{i}',(x,.704,1.9145),(.042,.042,.045)) for i,x in enumerate((-.242,.278))]+
                [(f'LiftMotorPlate{i}',(x,.704,1.889),(.065,.065,.006)) for i,x in enumerate((-.242,.278))],
            'B':[('LiftMotor',(-.26,.775,1.98),(.042,.042,.045)),('MotorPlate',(-.26,.798,1.955),(.065,.075,.006))],
            'C':[(f'StationaryMotor{i}',(-.245,.823,z),(.042,.040,.042)) for i,z in enumerate((1.035,1.865))]+
                [(f'MotorPlate{i}',(-.245,.793,z),(.060,.006,.065)) for i,z in enumerate((1.035,1.865))]}
        for name,center,size in definitions[architecture]:
            c=UsdGeom.Cube.Define(s,ROOT+'/Frame/'+name)
            c.CreateSizeAttr(1.);c.AddTranslateOp().Set(Gf.Vec3d(*center));c.AddScaleOp().Set(Gf.Vec3f(*size))
        for name in ('Plug','Robot/Carriage'):
            UsdGeom.Xform.Define(s,'/World/'+name).AddTranslateOp().Set(Gf.Vec3d(1,2,3))
        return s

    def test_body_shaft_dimensions_and_motor_faces(self):
        for arch in 'ABC':
            s=self.stage(arch); report=add_brake_hardware(s,arch)
            self.assertEqual(len(report['brakes']),1 if arch=='B' else 2)
            for b in report['brakes']:
                axis='XYZ'.index(b['axis']); face=b['mount_face_m'][axis]
                mesh=UsdGeom.Mesh(s.GetPrimAtPath(b['path']+'/Housing'))
                points=mesh.GetPointsAttr().Get()
                self.assertAlmostEqual(min(p[axis] for p in points),face,places=6)
                self.assertAlmostEqual(max(p[axis] for p in points),face+LENGTH,places=6)
                motor=s.GetPrimAtPath(b['motor'])
                self.assertAlmostEqual(motor.GetAttribute('xformOp:translate').Get()[axis]-motor.GetAttribute('xformOp:scale').Get()[axis]/2,face+LENGTH)
                shaft=UsdGeom.Cylinder(s.GetPrimAtPath(b['path']+'/OutputShaft'))
                self.assertAlmostEqual(shaft.GetHeightAttr().Get(),.024)
                self.assertAlmostEqual(shaft.GetPrim().GetAttribute('xformOp:translate').Get()[axis]-.012,face-.024)
                self.assertTrue(mesh.GetPrim().HasAPI(UsdPhysics.CollisionAPI))

    def test_mass_and_no_dynamic_pose_changes(self):
        for arch in 'ABC':
            s=self.stage(arch); report=add_brake_hardware(s,arch)
            delta=report['added_mass_kg_by_body']
            self.assertEqual(list(delta),[ROOT+'/Frame'])
            self.assertGreater(delta[ROOT+'/Frame'],.25*(1 if arch=='B' else 2))
            self.assertAlmostEqual(UsdPhysics.MassAPI(s.GetPrimAtPath(ROOT+'/Frame')).GetMassAttr().Get(),5+delta[ROOT+'/Frame'],places=6)
            for name in ('Plug','Robot/Carriage'):
                self.assertEqual(s.GetPrimAtPath('/World/'+name).GetAttribute('xformOp:translate').Get(),Gf.Vec3d(1,2,3))
            for p in report['reworked_plates']: self.assertFalse(s.GetPrimAtPath(p['old_plate']).IsActive())
            with self.assertRaises(ValueError): add_brake_hardware(s,arch)

    def test_outward_mesh_winding(self):
        for arch in 'ABC':
            s=self.stage(arch); report=add_brake_hardware(s,arch)
            for b in report['brakes']:
                m=UsdGeom.Mesh(s.GetPrimAtPath(b['path']+'/Housing'))
                points=m.GetPointsAttr().Get(); center=sum(points,Gf.Vec3f(0))/len(points)
                ids=m.GetFaceVertexIndicesAttr().Get();offset=0
                for count in m.GetFaceVertexCountsAttr().Get():
                    face=[points[i] for i in ids[offset:offset+count]];offset+=count
                    normal=Gf.Cross(face[1]-face[0],face[2]-face[1])
                    self.assertGreater(Gf.Dot(normal,face[0]-center),0)

    def test_requires_drive_connected_assembly(self):
        s=self.stage('A');s.GetPrimAtPath(ROOT).ClearCustomDataByKey('hardware_revision')
        with self.assertRaises(ValueError):add_brake_hardware(s,'A')
