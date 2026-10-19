from pathlib import Path
from pxr import Usd, UsdGeom, UsdPhysics, UsdLux, PhysxSchema, Gf
from .geometry import material,box,xform,bind,curve
from .hardware import server,rack_frame,switches
from .connector import create_socket,create_plug,Interaction
from .cable import create_cable
from .config import CFG,PORT,SERVER_Z,ROW_PORTS
from .labels import label

ASSETS=Path('/workspace/assets')
PACK=ASSETS/'vendor/datacenter/Assets/DigitalTwin/Assets/Datacenter'

def reference_asset(stage,path,file,pos,rotation=0):
    source=Usd.Stage.Open(str(file))
    p=xform(stage,path,pos)
    p.AddRotateZOp().Set(rotation)
    if UsdGeom.GetStageUpAxis(source)=='Y': p.AddRotateXOp().Set(90)
    units=UsdGeom.GetStageMetersPerUnit(source)
    bounds=UsdGeom.BBoxCache(0,['default','render']).ComputeWorldBound(source.GetPseudoRoot()).ComputeAlignedRange()
    print('ASSET',file,'units',units,'up',UsdGeom.GetStageUpAxis(source),'bounds',bounds,flush=True)
    p.AddScaleOp().Set(Gf.Vec3f(units))
    center=bounds.GetMidpoint()
    xform(stage,path+'/Normalize',(-center[0],-center[1],-bounds.GetMin()[2]))
    child=stage.DefinePrim(path+'/Normalize/Model','Xform')
    child.GetReferences().AddReference(str(file))
    return p

def build(stage,port_row=False):
    UsdGeom.SetStageUpAxis(stage,'Z'); UsdGeom.SetStageMetersPerUnit(stage,1)
    xform(stage,'/World'); stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
    mats={}
    specs={'steel':((.39,.43,.48),.85,.28), 'black':((.019,.023,.028),.35,.36),
           'dark':((.055,.065,.078),.65,.4),'blue':((.018,.17,.46),.0,.35),
           'orange':((.94,.19,.025),.0,.4),'gold':((.75,.48,.12),.9,.22),
           'rubber':((.015,.018,.023),0,.68),'plug':((.55,.68,.72),.0,.18),
           'green':((.02,.8,.16),.0,.28),'tile':((.25,.28,.32),.1,.55)}
    for name,(col,metal,rough) in specs.items():
        mats[name]=material(stage,name,col,metal,rough,(.04,1,.15) if name=='green' else None)
    physics=UsdPhysics.Scene.Define(stage,'/World/Physics')
    physics.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1)); physics.CreateGravityMagnitudeAttr(9.81)
    px=PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim())
    px.CreateEnableCCDAttr(True); px.CreateTimeStepsPerSecondAttr(240)
    px.CreateSolverTypeAttr('TGS'); px.CreateEnableGPUDynamicsAttr(False)
    # CPU PhysX is intentional for small, tightly constrained contact geometry; RTX remains GPU accelerated.
    box(stage,'/World/Floor',(0,0,-.025),(16,14,.05),mats['tile'],True)
    for i in range(-12,13):
        box(stage,f'/World/Seams/X{i}'.replace('-','n'),(i*.6,0,.0001),(.003,14,.0002),mats['black'])
        box(stage,f'/World/Seams/Y{i}'.replace('-','n'),(0,i*.6,.0001),(16,.003,.0002),mats['black'])
    rack_frame(stage,'/World/Rack',mats)
    for i,z in enumerate(SERVER_Z): server(stage,f'/World/Servers/XE9680_{i+1}',z,mats,active=i==2 and not port_row)
    switches(stage,'/World/Network',mats,functional_row=port_row)
    rackfile=PACK/'Racks/Rack_42U_A/Rack_42U_A_01.usd'
    if not rackfile.exists(): raise FileNotFoundError('Download and extract the NVIDIA datacenter asset pack first')
    for i,x in enumerate((-2.1,-1.4,-.7,.7,1.4,2.1)):
        reference_asset(stage,f'/World/Environment/Rack{i}',rackfile,(x,-.1,0),90)
    switchfile=PACK/'Network_Switches/NVIDIA/SN2700/SN2700C_01.usd'
    reference_asset(stage,'/World/Network/NVIDIA_SN2700',switchfile,(0,0,1.84),90)
    trayfile=PACK/'Facilities/Cable_Tray/Cable_Tray_61x299x5cm_A01_01.usd'
    reference_asset(stage,'/World/Environment/CableTray',trayfile,(-1.5,.2,2.5))
    box(stage,'/World/BackWall',(0,-3.8,1.7),(14,.1,3.4),mats['tile'])
    dome=UsdLux.DomeLight.Define(stage,'/World/Lighting/Fill'); dome.CreateIntensityAttr(1100)
    dome.CreateColorAttr(Gf.Vec3f(.68,.78,1))
    for i,(pos,power) in enumerate([((0,1.3,2.8),2200),((-2,0,2.8),1700),((2,0,2.8),1700),((0,-1.7,2.8),2200)]):
        l=UsdLux.RectLight.Define(stage,f'/World/Lighting/Panel{i}')
        l.AddTranslateOp().Set(Gf.Vec3d(*pos)); l.CreateWidthAttr(1.4); l.CreateHeightAttr(.35)
        l.CreateIntensityAttr(power); l.CreateColorTemperatureAttr(5000); l.CreateEnableColorTemperatureAttr(True)
    for i,(pos,target) in enumerate([((0,2.5,1.8),(0,.3,1.1)),((0,-2.5,1.8),(0,-.3,1.1))]):
        light=UsdLux.RectLight.Define(stage,f'/World/Lighting/Inspection{i}')
        matrix=Gf.Matrix4d().SetLookAt(Gf.Vec3d(*pos),Gf.Vec3d(*target),Gf.Vec3d(0,0,1)).GetInverse()
        light.AddTransformOp().Set(matrix); light.CreateWidthAttr(2); light.CreateHeightAttr(1.5)
        light.CreateIntensityAttr(1500)
    ports=None
    mouth=ROW_PORTS[0] if port_row else PORT
    if port_row:
        xform(stage,'/World/PortRow')
        ports=[]
        for i,pos in enumerate(ROW_PORTS):
            path=f'/World/PortRow/Port{i+1:02d}'
            create_socket(stage,pos,mats,path); ports.append((path,pos))
            label(stage,path+'/Number',f'{i+1:02d}',(pos[0],pos[1]+.001,pos[2]-.012),.018,.006)
            if i<15:
                box(stage,f'/World/PortRow/Divider{i}',(pos[0]-.0125,pos[1]-.004,pos[2]),
                    (.0088,.008,.0131),mats['dark'],True)
        for sign in (-1,1):
            box(stage,f'/World/PortRow/Rail{sign}'.replace('-','n'),(0,.425,1.66+sign*.009),
                (.42,.008,.005),mats['dark'],True)
    else: create_socket(stage,PORT,mats)
    plugpos=(mouth[0],mouth[1]+.05,mouth[2])
    create_plug(stage,plugpos,mats)
    cable=create_cable(stage,plugpos,mats['blue'])
    interaction=Interaction(stage,mouth,ports)
    return interaction,cable

CAMERAS={
    'rear':((.85,3.5,1.8),(0,.2,1.08)),
    'front':((-.85,-3.5,1.8),(0,-.2,1.05)),
    'connector':((PORT[0]+.048,PORT[1]+.145,PORT[2]+.064),PORT),
    'rear_detail':((.48,1.15,1.45),(0,.40,1.10)),
    'row':((.025,1.03,1.79),(0,.429,1.66)),
    'handoff':((.175,.56,1.71),(.175,.429,1.664)),
    'latch':((ROW_PORTS[0][0]+.025,.484,1.688),ROW_PORTS[0]),
}

def camera(stage,name,focus=None):
    from isaacsim.core.utils.viewports import set_camera_view,set_active_viewport_camera
    # A user can select an orthographic camera from the viewport toolbar.
    # Moving the perspective prim alone does not switch the displayed camera.
    set_active_viewport_camera('/OmniverseKit_Persp')
    eye,target=CAMERAS[name]
    if focus is not None:
        target=focus
        offset=(.025,.055,.028) if name=='latch' else (.035,.18,.06)
        eye=tuple(a+b for a,b in zip(focus,offset))
    set_camera_view(eye=list(eye),target=list(target))
    # Millimetre-scale connector is inside the default 1 cm clipping plane.
    p=stage.GetPrimAtPath('/OmniverseKit_Persp')
    if p: UsdGeom.Camera(p).GetClippingRangeAttr().Set(Gf.Vec2f(.001,1000))
