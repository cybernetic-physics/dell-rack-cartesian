"""Open guide and screw interfaces for the two-stage side boom.

Custom dimensioned hardware, authored before physics. Joint anchors, body
poses, drive parameters and both 200 mm extension travels are unchanged.
"""
import math
from pxr import Gf, UsdGeom, UsdPhysics
from rack_robotics.hardware_detail import Hardware, ROOT
from rack_robotics.gantry_frame import open_mgn12h

REVISION = 'telescoping_open_guide_frame_v1'


def complete_telescoping_frame(stage, architecture):
    robot=stage.GetPrimAtPath(ROOT)
    if architecture!='B': raise ValueError('Telescoping frame requires architecture B')
    if not robot or not robot.GetCustomDataByKey('insertion_revision') or not robot.GetCustomDataByKey('brake_revision'):
        raise ValueError('Open insertion stage and motor brake required')
    if robot.GetCustomDataByKey('telescoping_frame_revision') or robot.GetCustomDataByKey('service_carrier_revision'):
        raise ValueError('Frame already revised or carriers already installed')
    h=Hardware(stage);changes=[];delta={}
    frame=ROOT+'/Frame';lift=ROOT+'/LiftCarriage';middle=ROOT+'/MiddleBoom';carriage=ROOT+'/Carriage'

    def owner(prim):
        while prim and not prim.HasAPI(UsdPhysics.RigidBodyAPI): prim=prim.GetParent()
        if not prim: raise ValueError('Missing rigid owner')
        return str(prim.GetPath())

    def resize(path,center,size,density=2700.):
        prim=stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdGeom.Cube): raise ValueError('Missing box: '+path)
        old=[v*UsdGeom.Cube(prim).GetSizeAttr().Get() for v in prim.GetAttribute('xformOp:scale').Get()]
        mass=(math.prod(size)-math.prod(old))*density;body=owner(prim)
        delta[body]=delta.get(body,0.)+mass
        prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*center))
        prim.GetAttribute('xformOp:scale').Set(Gf.Vec3f(*size));UsdGeom.Cube(prim).GetSizeAttr().Set(1.)
        changes.append({'path':path,'center_m':list(center),'size_m':list(size),'mass_delta_kg':mass})

    def shift(path,vector):
        prim=stage.GetPrimAtPath(path)
        if not prim: raise ValueError('Missing shifted part: '+path)
        if not prim.IsA(UsdGeom.Xformable):
            if prim.GetTypeName(): raise ValueError('Nontransformable part: '+path)
            prim.SetTypeName('Xform')
        attr=prim.GetAttribute('xformOp:translate')
        if attr: attr.Set(attr.Get()+Gf.Vec3d(*vector))
        else: UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(*vector))
        changes.append({'path':path,'translation_delta_m':list(vector)})

    def replace_box(path):
        prim=stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdGeom.Cube): raise ValueError('Missing replaced box: '+path)
        mass=math.prod(prim.GetAttribute('xformOp:scale').Get())*UsdGeom.Cube(prim).GetSizeAttr().Get()**3*2700.
        body=owner(prim);delta[body]=delta.get(body,0.)-mass;prim.SetActive(False)
        changes.append({'path':path,'replaced':True,'mass_delta_kg':-mass})

    def replace_cylinder(path):
        prim=stage.GetPrimAtPath(path);cylinder=UsdGeom.Cylinder(prim)
        if not cylinder: raise ValueError('Missing replaced cylinder: '+path)
        mass=math.pi*cylinder.GetRadiusAttr().Get()**2*cylinder.GetHeightAttr().Get()*7850.
        body=owner(prim);delta[body]=delta.get(body,0.)-mass;prim.SetActive(False)
        changes.append({'path':path,'replaced':True,'mass_delta_kg':-mass})

    def shaft(path,center,length):
        prim=stage.GetPrimAtPath(path);cylinder=UsdGeom.Cylinder(prim)
        if not cylinder: raise ValueError('Missing shaft: '+path)
        mass=math.pi*cylinder.GetRadiusAttr().Get()**2*(length-cylinder.GetHeightAttr().Get())*7850.
        body=owner(prim);delta[body]=delta.get(body,0.)+mass
        cylinder.GetHeightAttr().Set(length)
        prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*center))
        changes.append({'path':path,'center_m':list(center),'length_m':length,'mass_delta_kg':mass})

    # Move the fixed spine rearward, not the moving booms/TCP. The rail
    # mounting plane is Y=.813; the new plate meets the block crowns at .800.
    shift(frame+'/Upright',(0,.020,0))
    resize(lift+'/VerticalPlate',(-.060,.017,.030),(.100,.006,.160))
    for i,x in enumerate((-.28,-.24)):
        shift(frame+f'/VerticalGuide{i}',(0,.020,0))
        h.box(frame+f'/GuideInterfaces/RailShim{i}',(x,.814,1.47),(.012,.002,.940))
        for j,z in enumerate((-.030,.070)):
            stage.GetPrimAtPath(lift+f'/LiftBlock{i}_{j}').SetActive(False)
            open_mgn12h(h,lift+f'/GuideInterfaces/LiftBlock{i}_{j}',(x+.20,.033,z),2,1,-1)
            for r,dz in enumerate((-.010,.010)):
                for c,dx in enumerate((-.010,.010)):
                    h.bolt(lift+f'/GuideInterfaces/BlockBolt{i}_{j}_{r}_{c}',
                           (x+.20+dx,.01875,z+dz),'Y',.0015,.0095)
        for j,z in enumerate((1.0423,1.8977)):
            h.box(frame+f'/GuideInterfaces/VerticalStop{i}_{j}',(x,.809,z),(.012,.010,.008))
    for i,z in enumerate((1.01,1.92)):
        # Extend the same standoff to the relocated upright, retaining the
        # rack-side clamp/bolt coordinates.
        resize(frame+f'/RackStandoff{i}',(-.275,.710,z),(.040,.270,.008))
    # Outboard lift screw clears the solid boom and both vertical rails.
    for name in ('LiftMotor','Brakes/Lift'):
        shift(frame+'/'+name,(-.060,.040,.014))
    shaft(frame+'/LiftScrew',(-.320,.815,1.473),.946)
    replace_cylinder(frame+'/LiftCoupler')
    h.sleeve(frame+'/ScrewInterfaces/LiftCoupler',(-.320,.815,1.949),.007,.0041,.018,'Z')
    h.sleeve(frame+'/ScrewInterfaces/LiftReducer',(-.320,.815,1.953),.0041,.00255,.010,'Z')
    h.box(frame+'/ScrewInterfaces/MotorBridge',(-.2925,.835,1.958),(.105,.040,.016))
    for i,z in enumerate((1.012,1.930)):
        h.sleeve(frame+f'/ScrewInterfaces/LiftBearing{i}',(-.320,.815,z),.011,.0042,.012,'Z')
        h.plate(frame+f'/ScrewInterfaces/LiftBearingBlock{i}',(-.320,.815,z),(.028,.028,.016),'Z',.0222)
        h.box(frame+f'/ScrewInterfaces/LiftBearingArm{i}',(-.299,.835,z),(.078,.016,.016))
    h.sleeve(lift+'/ScrewInterfaces/LiftNut',(-.120,.035,.030),.008,.0041,.016,'Z')
    h.plate(lift+'/ScrewInterfaces/LiftNutBlock',(-.120,.035,.030),(.022,.022,.020),'Z',.0162)
    h.box(lift+'/ScrewInterfaces/LiftNutArm',(-.109,.025,.030),(.028,.022,.012))

    for parent,child in ((lift,middle),(middle,carriage)):
        # The extra10 mm rail/bed supports the complete leading block at
        # full200 mm travel; no software travel is shortened to fit the rail.
        resize(parent+'/Boom',(-.145,0,.050),(.310,.032,.040))
        resize(parent+'/HorizontalGuide',(-.145,-.021,.050),(.310,.008,.012),7850.)
        h.box(parent+'/GuideInterfaces/RailShim',(-.145,-.0165,.050),(.310,.001,.012))
        for i,x in enumerate((-.270,-.220)):
            stage.GetPrimAtPath(child+f'/Bearing{i}').SetActive(False)
            open_mgn12h(h,child+f'/GuideInterfaces/HorizontalBlock{i}',(x,.033,.050),0,1,-1)
            for r,dx in enumerate((-.010,.010)):
                for c,dz in enumerate((-.010,.010)):
                    h.bolt(child+f'/GuideInterfaces/HorizontalBolt{i}_{r}_{c}',
                           (x+dx,.01975,.050+dz),'Y',.0015,.0075)
        h.box(child+'/GuideInterfaces/HorizontalBackPlate',(-.245,.018,.050),(.100,.004,.028))
        for i,x in enumerate((-.2967,.0067)):
            resize(parent+f'/EndStop{i}',(x,-.024,.050),(.006,.012,.012))
        # Place the drive below the beam, clear of the next insertion motor
        # and the top rack standoff throughout independent extension travel.
        shift(parent+'/Motor',(0,0,-.138))
        shaft(parent+'/Screw',(-.154,-.023,-.060),.288)
        replace_cylinder(parent+'/Coupler')
        h.sleeve(parent+'/ScrewInterfaces/Coupler',(-.300,-.023,-.060),.007,.0041,.020,'X')
        h.sleeve(parent+'/ScrewInterfaces/CouplerReducer',(-.306,-.023,-.060),.0041,.00255,.008,'X')
        replace_box(parent+'/MotorPlate')
        h.plate(parent+'/ScrewInterfaces/MotorPlate',(-.307,-.023,-.060),(.006,.048,.050),'X',.012)
        h.box(parent+'/ScrewInterfaces/MotorFoot',(-.295,-.013,-.006),(.030,.030,.072))
        h.bolt(parent+'/ScrewInterfaces/MotorShaft',(-.3075,-.023,-.060),'X',.0025,.011)
        for r,dy in enumerate((-.0155,.0155)):
            for c,dz in enumerate((-.0155,.0155)):
                h.bolt(parent+f'/ScrewInterfaces/MotorBolt{r}_{c}',(-.310,-.023+dy,-.060+dz),'X',.0015,.012)
        for i,x in enumerate((-.280,-.020)):
            h.sleeve(parent+f'/ScrewInterfaces/Bearing{i}',(x,-.023,-.060),.009,.0042,.010,'X')
            h.plate(parent+f'/ScrewInterfaces/BearingBlock{i}',(x,-.023,-.060),(.014,.026,.026),'X',.0182)
            h.box(parent+f'/ScrewInterfaces/BearingWeb{i}',(x,-.015,-.0085),(.014,.030,.077))
        replace_box(child+'/LeadNut')
        h.sleeve(child+'/ScrewInterfaces/LeadNut',(-.245,.027,-.060),.009,.0041,.022,'X')
        h.plate(child+'/ScrewInterfaces/NutBlock',(-.245,.027,-.060),(.026,.024,.024),'X',.0182)
        h.box(child+'/ScrewInterfaces/NutWeb',(-.245,.018,-.009),(.026,.030,.078))

    for body,mass in h.added_mass.items():delta[body]=delta.get(body,0.)+mass
    for body,mass in delta.items():
        attr=UsdPhysics.MassAPI(stage.GetPrimAtPath(body)).GetMassAttr()
        if attr.Get()+mass<=0:raise ValueError('Nonpositive revised mass')
        attr.Set(attr.Get()+mass)
    robot.SetCustomDataByKey('telescoping_frame_revision',REVISION)
    return {'revision':REVISION,'architecture':architecture,'changes':changes,'parts':h.parts,
            'mass_delta_kg_by_body':delta,'scope':'Geometry/mass-only open nested-boom interfaces; unchanged joints and TCP',
            'limitations':['Custom dimensions and volume-based lumped masses, not rated vendor stages or manufacturing drawings.',
                'Bearing races, preload, screw rotation/thread contacts, structural compliance and fastener strength remain abstract.',
                'Needs full-rack, non-box, compatible carrier, payload, power-loss and repeated-task qualification.']}
