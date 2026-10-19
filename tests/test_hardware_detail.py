import math
import unittest
from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdShade
from rack_robotics.hardware_detail import complete_drive_connections, Hardware, ROOT


class HardwareDetailTest(unittest.TestCase):
    def stage(self):
        stage=Usd.Stage.CreateInMemory()
        UsdGeom.Xform.Define(stage,ROOT)
        UsdShade.Material.Define(stage,'/World/Materials/RobotSteel')
        for name in ('Frame','Bridge','Carriage','ToolMount'):
            prim=UsdGeom.Xform.Define(stage,ROOT+'/'+name).GetPrim()
            UsdPhysics.RigidBodyAPI.Apply(prim); UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(1.)
        for path in ('Frame/Motor0','Frame/Motor1','Bridge/XMotor','Bridge/XGuide',
                     'Carriage/DepthRail0','Carriage/DepthRail1'):
            cube=UsdGeom.Cube.Define(stage,ROOT+'/'+path)
            cube.AddTranslateOp().Set(Gf.Vec3d(0)); cube.AddScaleOp().Set(Gf.Vec3f(1))
        # A sentinel verifies the extension never touches the connector/latch.
        UsdGeom.Xform.Define(stage,'/World/Plug').AddTranslateOp().Set(Gf.Vec3d(1,2,3))
        return stage

    def test_new_hardware_has_mass_and_rigid_ownership(self):
        stage=self.stage(); result=complete_drive_connections(stage,'A')
        self.assertGreater(len(result['parts']),40)
        for body,mass in result['added_mass_kg_by_body'].items():
            self.assertAlmostEqual(UsdPhysics.MassAPI(stage.GetPrimAtPath(body)).GetMassAttr().Get(),1+mass,places=6)
        self.assertEqual(stage.GetPrimAtPath('/World/Plug').GetAttribute('xformOp:translate').Get(),Gf.Vec3d(1,2,3))
        actual=stage.GetPrimAtPath(ROOT+'/Frame/Motor0').GetAttribute('xformOp:translate').Get()
        self.assertLess((actual-Gf.Vec3d(-.242,.704,1.9145)).GetLength(),1e-12)
        for part in result['parts']:
            if part['collision']:
                self.assertAlmostEqual(stage.GetPrimAtPath(part['path']).GetAttribute('physxCollision:contactOffset').Get(),.00005)
        with self.assertRaises(ValueError): complete_drive_connections(stage,'A')

    def test_guide_stroke_envelopes_fit_complete_blocks(self):
        for origin in (-.21,.21):
            for block in (-.025,.025):
                self.assertLessEqual(abs(origin+block)+.0454/2,.520/2)
        for insertion in (-.125,0):
            lo=insertion-.010-.0454/2; hi=insertion-.010+.0454/2
            self.assertGreaterEqual(lo,-.070-.180/2)
            self.assertLessEqual(hi,-.070+.180/2)

    def test_depth_bearings_clear_bridge_guide_at_retracted_stop(self):
        stage=self.stage(); complete_drive_connections(stage,'A')
        # Relative to carriage: bridge-front guide is40-21-4=15 mm aft.
        guide_front=.040-.021-.004
        for name in ('DepthBlock0','DepthBlock1','DepthBearingPlate'):
            prim=stage.GetPrimAtPath(ROOT+'/ToolMount/'+name)
            center=prim.GetAttribute('xformOp:translate').Get()
            size=prim.GetAttribute('xformOp:scale').Get()
            self.assertLess(center[1]+size[1]/2+.0001,guide_front)

    def test_traverse_blocks_clear_frame_guides_and_front_hanger_clears_tool(self):
        stage=self.stage(); result=complete_drive_connections(stage,'C')
        for index in range(2):
            prim=stage.GetPrimAtPath(ROOT+f'/Carriage/TraverseBlock{index}')
            c=prim.GetAttribute('xformOp:translate').Get(); s=prim.GetAttribute('xformOp:scale').Get()
            # Frame-guide front Y=.706; carriage Y=.680, any X/Z position.
            self.assertLess(.680+c[1]+s[1]/2+.0001,.706)
        for part in result['parts']:
            if '/DepthFrontBearing' not in part['path'] or not part['collision']: continue
            prim=stage.GetPrimAtPath(part['path'])
            c=prim.GetAttribute('xformOp:translate').Get(); s=prim.GetAttribute('xformOp:scale').Get()
            # Conservative A-tool passage, including latch arm:±12 mm X,
            # max18 mm Z relative to the insertion-carriage datum.
            self.assertTrue(abs(c[0])-s[0]/2>.0121 or c[2]-s[2]/2>.0181)

    def test_wide_backplate_clears_a_upper_lift_stops(self):
        stage=self.stage(); complete_drive_connections(stage,'A')
        prim=stage.GetPrimAtPath(ROOT+'/Carriage/TraverseBackPlate')
        c=prim.GetAttribute('xformOp:translate').Get(); s=prim.GetAttribute('xformOp:scale').Get()
        self.assertLess(1.80+c[2]+s[2]/2+.0001,1.82-.008/2)

    def test_sleeve_has_open_bore_and_is_not_solid_collision(self):
        stage=self.stage(); hardware=Hardware(stage)
        path=ROOT+'/Frame/Annulus'
        hardware.sleeve(path,(0,0,0),.010,.004,.020,'Z')
        mesh=UsdGeom.Mesh(stage.GetPrimAtPath(path))
        self.assertEqual(len(mesh.GetPointsAttr().Get()),128)
        self.assertFalse(mesh.GetPrim().HasAPI(UsdPhysics.CollisionAPI))
        for point in mesh.GetPointsAttr().Get():
            self.assertGreaterEqual(math.hypot(point[0],point[1]),.0039999)

    def test_shared_depth_revision_for_other_architectures(self):
        for architecture in ('B','C'):
            result=complete_drive_connections(self.stage(),architecture)
            self.assertEqual(result['architecture'],architecture)
            blocks=[p for p in result['parts'] if '/DepthBlock' in p['path']]
            self.assertEqual([p['estimated_mass_kg'] for p in blocks],[.054,.054])


if __name__=='__main__': unittest.main()
