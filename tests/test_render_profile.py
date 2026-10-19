from pathlib import Path
import tempfile
import unittest
from pxr import Sdf, Usd, UsdGeom, UsdRender
from rack_robotics.render_profile import apply_profile, create_replay_product, verify_profile


class RenderProfileTests(unittest.TestCase):
    def test_explicit_spatial_aa_is_verified(self):
        stage = Usd.Stage.CreateInMemory()
        product = UsdRender.Product.Define(stage, '/Render/Test')
        report = apply_profile(stage, product.GetPath(), 'RealTimePathTracing', 64, False, 'fxaa')
        self.assertEqual(report['resolved']['omni:rtx:post:aa:op'], 'fxaa')
        product.GetPrim().GetAttribute('omni:rtx:post:aa:op').Set('dlss')
        with self.assertRaises(ValueError): verify_profile(stage, report)
        with self.assertRaises(ValueError):
            apply_profile(stage, product.GetPath(), 'RealTimePathTracing', 64, False, 'invented')

    def test_inherited_mode_is_overridden_without_changing_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Usd.Stage.CreateNew(str(Path(directory)/'source.usda'))
            p = UsdRender.Product.Define(source, '/Render/Product').GetPrim()
            p.CreateAttribute('omni:rtx:rendermode', Sdf.ValueTypeNames.Token).Set('RealTimePathTracing')
            p.CreateAttribute('omni:rtx:post:registeredCompositing:invertToneMap', Sdf.ValueTypeNames.Bool).Set(True)
            source.GetRootLayer().Save(); original = source.GetRootLayer().ExportToString()
            derived = Usd.Stage.CreateInMemory()
            derived.GetRootLayer().subLayerPaths = [source.GetRootLayer().identifier]
            result = apply_profile(derived, '/Render/Product', 'PathTracing', 64)
            self.assertEqual(result['before']['omni:rtx:rendermode'], 'RealTimePathTracing')
            self.assertEqual(result['resolved']['omni:rtx:rendermode'], 'PathTracing')
            self.assertFalse(result['resolved']['omni:rtx:post:motionblur:enabled'])
            self.assertTrue(result['before']['omni:rtx:post:registeredCompositing:invertToneMap'])
            self.assertFalse(result['resolved']['omni:rtx:post:registeredCompositing:invertToneMap'])
            self.assertEqual(source.GetRootLayer().ExportToString(), original)
            fallback = apply_profile(derived, '/Render/Product', 'PathTracing', 256, denoiser=False)
            self.assertFalse(fallback['resolved']['omni:rtx:pt:denoising:enabled'])
            self.assertEqual(fallback['resolved']['omni:rtx:pt:samplesPerPixel'], 256)

    def test_missing_render_product_fails(self):
        with self.assertRaises(ValueError): apply_profile(Usd.Stage.CreateInMemory(), '/Missing', 'PathTracing', 64)

    def test_isolated_product_has_camera_color_resolution_but_not_ui_overrides(self):
        stage = Usd.Stage.CreateInMemory()
        old = UsdRender.Product.Define(stage, '/Render/Original').GetPrim()
        old.CreateAttribute('omni:rtx:rendermode', Sdf.ValueTypeNames.Token).Set('RealTimePathTracing')
        original = old.GetAttribute('omni:rtx:rendermode').Get()
        UsdGeom.Camera.Define(stage, '/World/Camera')
        path = create_replay_product(stage, '/World/Camera', 1920, 1080)
        product = UsdRender.Product(stage.GetPrimAtPath(path))
        self.assertEqual(tuple(product.GetResolutionAttr().Get()), (1920, 1080))
        self.assertEqual(product.GetCameraRel().GetTargets(), [Sdf.Path('/World/Camera')])
        self.assertEqual(product.GetOrderedVarsRel().GetTargets(), [Sdf.Path('/Render/ReplayColor')])
        self.assertFalse(product.GetPrim().GetAttribute('omni:rtx:rendermode'))
        apply_profile(stage, path, 'PathTracing', 256, False)
        self.assertEqual(old.GetAttribute('omni:rtx:rendermode').Get(), original)
        with self.assertRaises(ValueError): create_replay_product(stage, '/World/Camera', 1920, 1080)

    def test_isolated_product_requires_camera(self):
        with self.assertRaises(ValueError):
            create_replay_product(Usd.Stage.CreateInMemory(), '/Missing', 1920, 1080)

    def test_runtime_renderer_fallback_is_rejected(self):
        stage = Usd.Stage.CreateInMemory()
        product = UsdRender.Product.Define(stage, '/Render/Test')
        profile = apply_profile(stage, product.GetPath(), 'RealTimePathTracing', 64, False)
        self.assertEqual(verify_profile(stage, profile), profile['resolved'])
        product.GetPrim().GetAttribute('omni:rtx:rendermode').Set('PathTracing')
        with self.assertRaises(ValueError): verify_profile(stage, profile)
