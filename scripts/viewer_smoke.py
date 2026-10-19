"""Run with Isaac Sim python.sh; leaves a rendered physics scene in the GUI."""
from isaacsim import SimulationApp
app = SimulationApp({"headless": False, "width": 1600, "height": 1000,
                     "renderer": "RaytracedLighting", "multi_gpu": False})
import omni.usd
from pxr import UsdGeom, UsdPhysics, UsdLux, Gf
from isaacsim.core.api import World
from isaacsim.core.utils.viewports import set_camera_view
world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()
stage = omni.usd.get_context().get_stage()
cube = UsdGeom.Cube.Define(stage, "/World/ViewerSmokeCube")
cube.CreateSizeAttr(.3)
cube.AddTranslateOp().Set(Gf.Vec3d(0, 0, 1))
cube.CreateDisplayColorAttr([(.05, .35, .8)])
UsdPhysics.CollisionAPI.Apply(cube.GetPrim())
UsdPhysics.RigidBodyAPI.Apply(cube.GetPrim())
UsdPhysics.MassAPI.Apply(cube.GetPrim()).CreateMassAttr(1)
light = UsdLux.DomeLight.Define(stage, "/World/Light")
light.CreateIntensityAttr(1000)
set_camera_view(eye=[2, 2, 1.5], target=[0, 0, .2])
world.reset()
for i in range(240):
    world.step(render=True)
print("VIEWER_SMOKE_PHYSICS", UsdGeom.Xformable(cube).ComputeLocalToWorldTransform(0).ExtractTranslation(), flush=True)
from omni.kit.viewport.utility import get_active_viewport, capture_viewport_to_file
capture_viewport_to_file(get_active_viewport(), '/workspace/artifacts/viewer-native.png')
import omni.ui as ui
preview = ui.Window('RTX Preview', width=820, height=570)
with preview.frame:
    picture = ui.Image('/workspace/artifacts/viewer-native.png')
import time
last_capture = 0
while app.is_running():
    world.step(render=True)
    if time.monotonic() - last_capture > 1:
        capture_viewport_to_file(get_active_viewport(), '/workspace/artifacts/live.png')
        last_capture = time.monotonic()
app.close()
