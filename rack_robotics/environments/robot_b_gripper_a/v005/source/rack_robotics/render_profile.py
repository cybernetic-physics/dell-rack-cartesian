"""Override inherited viewport settings in the derived replay layer only.

Names/types follow the installed omni.usd.schema.render_settings.rtx 1.0.2
generatedSchema.usda, rather than only deprecated global carb defaults.
"""
from pxr import Gf, Sdf, UsdGeom, UsdRender


def create_replay_product(stage, camera_path, width, height):
    """Create a clean product in the derived layer, not a copy of UI settings."""
    path = '/Render/ReplayProduct'
    if stage.GetPrimAtPath(path):
        raise ValueError('Replay product already exists')
    camera = stage.GetPrimAtPath(camera_path)
    if not camera or not camera.IsA(UsdGeom.Camera):
        raise ValueError('Replay product requires a real camera')
    if width < 1 or height < 1:
        raise ValueError('Resolution must be positive')
    product = UsdRender.Product.Define(stage, path)
    product.CreateCameraRel().SetTargets([camera_path])
    product.CreateResolutionAttr(Gf.Vec2i(width, height))
    variable = UsdRender.Var.Define(stage, '/Render/ReplayColor')
    variable.CreateSourceNameAttr('LdrColor')
    variable.CreateSourceTypeAttr('raw')
    product.CreateOrderedVarsRel().SetTargets([variable.GetPath()])
    return str(product.GetPath())


def apply_profile(stage, product_path, renderer, samples_per_pixel, denoiser=True, anti_aliasing=None):
    if renderer not in ('RealTimePathTracing', 'PathTracing') or samples_per_pixel < 1:
        raise ValueError('Unsupported renderer or sample count')
    if anti_aliasing not in (None, 'none', 'taa', 'fxaa', 'dlss', 'rtxaa'):
        raise ValueError('Unsupported anti-aliasing mode')
    prim = stage.GetPrimAtPath(product_path)
    if not prim or not prim.IsA(UsdRender.Product):
        raise ValueError(f'Viewport has no USD render product: {product_path}')
    settings = {
        'omni:rtx:rendermode': (Sdf.ValueTypeNames.Token, renderer),
        'omni:rtx:pt:samplesPerPixel': (Sdf.ValueTypeNames.Int, samples_per_pixel),
        'omni:rtx:pt:samplesPerIteration': (Sdf.ValueTypeNames.Int, samples_per_pixel),
        'omni:rtx:pt:clampSpp': (Sdf.ValueTypeNames.Int, samples_per_pixel),
        'omni:rtx:pt:denoising:enabled': (Sdf.ValueTypeNames.Bool, denoiser),
        'omni:rtx:pt:denoising:optix:temporal': (Sdf.ValueTypeNames.Bool, False),
        'omni:rtx:post:motionblur:enabled': (Sdf.ValueTypeNames.Bool, False),
        # The source interactive viewport inverts these for its compositor.
        # Replay PNGs are display-referred captures, not compositor inputs.
        'omni:rtx:post:registeredCompositing:invertColorCorrection': (Sdf.ValueTypeNames.Bool, False),
        'omni:rtx:post:registeredCompositing:invertToneMap': (Sdf.ValueTypeNames.Bool, False),
        'omni:rtx:dlss:frameGeneration': (Sdf.ValueTypeNames.Bool, False)}
    if anti_aliasing is not None:
        settings['omni:rtx:post:aa:op'] = (Sdf.ValueTypeNames.Token, anti_aliasing)
    before = {name: prim.GetAttribute(name).Get() for name in settings}
    for name, (kind, value) in settings.items():
        prim.CreateAttribute(name, kind, custom=False).Set(value)
    after = {name: prim.GetAttribute(name).Get() for name in settings}
    if after != {name: value for name, (_, value) in settings.items()}:
        raise ValueError('Viewport render product did not accept the requested profile')
    return {'render_product_path': str(product_path), 'before': before, 'resolved': after}


def verify_profile(stage, report):
    """Detect runtime fallbacks after renderer initialization, not just authorship."""
    prim = stage.GetPrimAtPath(report['render_product_path'])
    actual = {name: prim.GetAttribute(name).Get() for name in report['resolved']}
    if actual != report['resolved']:
        raise ValueError(f'Render profile changed after initialization: {actual}')
    return actual
