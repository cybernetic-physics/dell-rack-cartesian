"""Run with /isaac-sim/python.sh scripts/asset_bounds.py --allow-root."""
from isaacsim import SimulationApp
app=SimulationApp({'headless':True})
from pathlib import Path
from pxr import Usd,UsdGeom
root=Path('/workspace/assets/vendor/datacenter/Assets/DigitalTwin/Assets/Datacenter')
for rel in ['Racks/Rack_42U_A/Rack_42U_A_01.usd','Network_Switches/NVIDIA/SN2700/SN2700C_01.usd']:
    s=Usd.Stage.Open(str(root/rel))
    print(rel,'up',UsdGeom.GetStageUpAxis(s),'units',UsdGeom.GetStageMetersPerUnit(s),'default',s.GetDefaultPrim())
    print('BOUND',UsdGeom.BBoxCache(0,['default','render']).ComputeWorldBound(s.GetPseudoRoot()).ComputeAlignedRange())
app.close()
