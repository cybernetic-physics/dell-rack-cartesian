"""Open guides and separated screw-drive interfaces for architecture A.

Authored before physics only. Retains all joint anchors, travel and drive
parameters. Custom machined brackets, not vendor CAD or strength certification.
"""
import math
from pxr import Gf, UsdGeom, UsdPhysics
from rack_robotics.hardware_detail import Hardware, ROOT
from rack_robotics.gantry_frame import open_mgn12h

REVISION = 'dual_screw_open_guide_frame_v1'


def complete_screw_frame(stage, architecture):
    robot = stage.GetPrimAtPath(ROOT)
    if architecture != 'A': raise ValueError('Dual screw frame requires architecture A')
    if not robot or not robot.GetCustomDataByKey('insertion_revision') or not robot.GetCustomDataByKey('brake_revision'):
        raise ValueError('Open insertion stage and installed motor brakes required')
    if robot.GetCustomDataByKey('screw_frame_revision') or robot.GetCustomDataByKey('service_carrier_revision'):
        raise ValueError('Frame already revised or carriers already installed')
    frame=ROOT+'/Frame'; bridge=ROOT+'/Bridge'; carriage=ROOT+'/Carriage'
    h=Hardware(stage); changes=[]; delta={}

    def owner(prim):
        while prim and not prim.HasAPI(UsdPhysics.RigidBodyAPI): prim=prim.GetParent()
        if not prim: raise ValueError('Missing rigid owner')
        return str(prim.GetPath())

    def resize(path, center, size, density=2700.):
        prim=stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdGeom.Cube): raise ValueError('Missing box: '+path)
        old=[v*UsdGeom.Cube(prim).GetSizeAttr().Get() for v in prim.GetAttribute('xformOp:scale').Get()]
        mass=(math.prod(size)-math.prod(old))*density
        body=owner(prim); delta[body]=delta.get(body,0.)+mass
        prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*center))
        prim.GetAttribute('xformOp:scale').Set(Gf.Vec3f(*size)); UsdGeom.Cube(prim).GetSizeAttr().Set(1.)
        changes.append({'path':path,'new_center_m':list(center),'new_size_m':list(size),'mass_delta_kg':mass})

    def shift(path, vector):
        prim=stage.GetPrimAtPath(path)
        if not prim: raise ValueError('Missing shifted part: '+path)
        if not prim.IsA(UsdGeom.Xformable):
            if prim.GetTypeName(): raise ValueError('Nontransformable part: '+path)
            prim.SetTypeName('Xform')
        attr=prim.GetAttribute('xformOp:translate')
        if attr: attr.Set(attr.Get()+Gf.Vec3d(*vector))
        else: UsdGeom.Xformable(prim).AddTranslateOp().Set(Gf.Vec3d(*vector))
        changes.append({'path':path,'translation_delta_m':list(vector),'mass_delta_kg':0.})

    def replace_box(path):
        prim=stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdGeom.Cube): raise ValueError('Missing replaced box: '+path)
        volume=math.prod(prim.GetAttribute('xformOp:scale').Get())*UsdGeom.Cube(prim).GetSizeAttr().Get()**3
        body=owner(prim); delta[body]=delta.get(body,0.)-volume*2700.
        prim.SetActive(False)
        changes.append({'path':path,'replaced':True,'mass_delta_kg':-volume*2700.})

    resize(bridge+'/Beam',(0,0,0),(.470,.032,.040))
    h.box(bridge+'/GuideInterfaces/TraverseRailShim',(0,-.0165,0),(.470,.001,.012))
    for i,x in enumerate((-.26,.26)):
        resize(frame+f'/Upright{i}',(x,.735,1.45),(.040,.040,.980))
        resize(frame+f'/Guide{i}',(x,.710,1.45),(.012,.008,.920),7850.)
        h.box(frame+f'/GuideInterfaces/RailShim{i}',(x,.7145,1.45),(.012,.001,.920))
        stage.GetPrimAtPath(bridge+f'/GuideBlock{i}').SetActive(False)
        open_mgn12h(h,bridge+f'/GuideInterfaces/LiftBlock{i}',(x,-.006,.050),2,1,-1)
        sign=(-1,1)[i]
        h.box(bridge+f'/GuideInterfaces/LowerArm{i}',(sign*.24675,-.0185,.0305),(.0535,.007,.006))
        h.box(bridge+f'/GuideInterfaces/ArmRiser{i}',(sign*.2305,-.0135,.0175),(.009,.005,.035))
        h.box(bridge+f'/GuideInterfaces/BlockPlate{i}',(x,-.022,.050),(.027,.006,.0454))
        for r,dz in enumerate((-.010,.010)):
            for c,dx in enumerate((-.010,.010)):
                h.bolt(bridge+f'/GuideInterfaces/BlockBolt{i}_{r}_{c}',(x+dx,-.02025,.050+dz),'Y',.0015,.0095)
        for k,z in enumerate((1.1223,1.8777)):
            resize(frame+f'/Stop{i}_{k}',(x,.709,z),(.012,.010,.008))
        for name in (f'Bracket{i}_1',f'PostClamp{i}_1',f'Bolt{i}_1_0',f'Bolt{i}_1_1'):
            shift(frame+'/'+name,(0,0,.085))
        for name in (f'Bracket{i}_0',f'PostClamp{i}_0',f'Bolt{i}_0_0',f'Bolt{i}_0_1'):
            shift(frame+'/'+name,(0,0,-.050))

        # The complete motor/brake stack moves above the raised insertion
        # stage. Extend its screw, not the robot travel or controller limits.
        # Put both lift screws OUTBOARD of their rails. The original left
        # screw was inboard, crowding the traverse and insertion carrier.
        dx=-.036 if i==0 else 0.
        lead_x=x+sign*.018
        shift(frame+f'/Brakes/Lift{i}',(dx,0,.060))
        shift(frame+f'/Motor{i}',(dx,0,.060))
        shift(frame+f'/LiftCoupler{i}',(dx,0,.060))
        for k,dz in ((0,0.),(1,.050)):
            shift(frame+f'/LiftBearing{i}_{k}',(dx,0,dz))
            shift(frame+f'/LiftBearingSupport{i}_{k}',(dx,0,dz))
        resize(frame+f'/DriveUprightExtension{i}',(x,.735,1.943),(.040,.040,.006))
        screw=UsdGeom.Cylinder(stage.GetPrimAtPath(frame+f'/Screw{i}'))
        mass=math.pi*screw.GetRadiusAttr().Get()**2*(.890-screw.GetHeightAttr().Get())*7850.
        delta[frame]=delta.get(frame,0.)+mass
        screw.GetHeightAttr().Set(.890)
        screw.GetPrim().GetAttribute('xformOp:translate').Set(Gf.Vec3d(lead_x,.704,1.455))
        changes.append({'path':str(screw.GetPath()),'new_length_m':.890,'mass_delta_kg':mass})
        # Brake hardware already supplies the four mounting bolts; remove
        # the superseded overlapping motor-plate bolts, accounting for mass.
        for r in range(2):
            for c in range(2):
                p=stage.GetPrimAtPath(frame+f'/LiftMotorBolt{i}_{r}_{c}')
                old=UsdGeom.Cylinder(p)
                removed=math.pi*old.GetRadiusAttr().Get()**2*old.GetHeightAttr().Get()*7850.
                delta[frame]-=removed; p.SetActive(False)
                changes.append({'path':str(p.GetPath()),'replaced_by':'Brake MountBolt','mass_delta_kg':-removed})

        # Lift nut stays coaxial with its original screw. A forward arm
        # reaches around the guide rail instead of passing through it.
        shift(bridge+f'/LiftNut{i}',(dx,0,-.025))
        replace_box(bridge+f'/LiftNutBracket{i}')
        h.plate(bridge+f'/ScrewInterfaces/LiftNutBlock{i}',(lead_x,-.016,-.025),(.022,.020,.018),'Z',.0162)
        inner=sign*.225; nut=lead_x
        h.box(bridge+f'/ScrewInterfaces/LiftNutArm{i}',((inner+nut)/2,-.029,-.025),(abs(nut-inner)+.010,.006,.006))
        h.box(bridge+f'/ScrewInterfaces/LiftNutShoulder{i}',(inner,-.0215,-.026),(.016,.021,.012))

    for i,x in enumerate((-.025,.025)):
        stage.GetPrimAtPath(carriage+f'/TraverseBlock{i}').SetActive(False)
        open_mgn12h(h,carriage+f'/GuideInterfaces/TraverseBlock{i}',(x,.023,0),0,1,-1)

    # Put the horizontal screw below the beam and in front of the uprights.
    # The full-size motor and mount then clear both the rack mounts and guides.
    vector=(0,-.007,-.098)
    for name in ('XScrew','XMotor','TraverseCoupler','TraverseMotorPlate'):
        shift(bridge+'/'+name,vector)
    for name in ('XMotor','TraverseCoupler','TraverseMotorPlate'):
        shift(bridge+'/'+name,(.006,0,0))
    shaft=UsdGeom.Cylinder(stage.GetPrimAtPath(bridge+'/XScrew'))
    old_length=shaft.GetHeightAttr().Get()
    shaft.GetHeightAttr().Set(.498)
    shaft.GetPrim().GetAttribute('xformOp:translate').Set(Gf.Vec3d(.009,-.030,-.080))
    mass=math.pi*shaft.GetRadiusAttr().Get()**2*(.498-old_length)*7850.
    delta[bridge]=delta.get(bridge,0.)+mass
    changes.append({'path':str(shaft.GetPath()),'new_length_m':.498,'mass_delta_kg':mass})
    h.bolt(bridge+'/ScrewInterfaces/TraverseMotorShaft',(.266,-.030,-.080),'X',.0025,.015)
    h.sleeve(bridge+'/ScrewInterfaces/TraverseCouplerReducer',(.2645,-.030,-.080),.0041,.00255,.012,'X')
    # Narrow the motor plate's transverse extent to48 mm (31 mm bolt pattern
    # remains available), leaving1 mm nominal clearance to the upright.
    replace_box(bridge+'/TraverseMotorPlate/U0')
    replace_box(bridge+'/TraverseMotorPlate/U2')
    replace_box(bridge+'/TraverseMotorPlate/V0')
    replace_box(bridge+'/TraverseMotorPlate/V2')
    h.plate(bridge+'/ScrewInterfaces/TraverseMotorPlate',(.2705,-.030,-.080),(.006,.048,.050),'X',.012)
    h.box(bridge+'/ScrewInterfaces/TraverseMotorBrace',(.230,-.026,-.060),(.012,.012,.080))
    h.box(bridge+'/ScrewInterfaces/TraverseMotorBraceCap',(.230,-.022,-.026),(.012,.020,.012))
    h.box(bridge+'/ScrewInterfaces/TraverseMotorFoot',(.25025,-.026,-.100),(.0525,.014,.008))
    for r,dy in enumerate((-.0155,.0155)):
        for c,dz in enumerate((-.0155,.0155)):
            h.bolt(bridge+f'/ScrewInterfaces/TraverseMotorBolt{r}_{c}',(.2735,-.030+dy,-.080+dz),'X',.0015,.012)
    for i,x in enumerate((-.234,.234)):
        shift(bridge+f'/TraverseBearing{i}',vector)
        replace_box(bridge+f'/TraverseBearingSupport{i}')
        h.plate(bridge+f'/ScrewInterfaces/TraverseBearingBlock{i}',(x,-.030,-.080),(.016,.032,.032),'X',.022)
        h.box(bridge+f'/ScrewInterfaces/TraverseBearingWeb{i}',(x,-.012,-.042),(.016,.008,.044))
    shift(carriage+'/TraverseNut',vector)
    replace_box(carriage+'/TraverseNutBracket')
    h.plate(carriage+'/ScrewInterfaces/TraverseNutBlock',(0,.010,-.080),(.025,.028,.028),'X',.0162)
    h.box(carriage+'/ScrewInterfaces/TraverseNutWeb',(0,0,-.047),(.025,.010,.038))

    for body,mass in h.added_mass.items(): delta[body]=delta.get(body,0.)+mass
    for body,mass in delta.items():
        attr=UsdPhysics.MassAPI(stage.GetPrimAtPath(body)).GetMassAttr()
        if attr.Get()+mass<=0: raise ValueError('Nonpositive revised mass')
        attr.Set(attr.Get()+mass)
    robot.SetCustomDataByKey('screw_frame_revision',REVISION)
    return {'revision':REVISION,'architecture':architecture,'changes':changes,'parts':h.parts,
            'mass_delta_kg_by_body':delta,'scope':'Geometry/mass-only dual screw guide, nut, motor and mounting correction',
            'limitations':['Open guide channels reuse the documented MGN12H envelope; races/preload remain abstract.',
                'Square housing bores, nut attachment, shaft shoulders and motor coupling are custom mechanical abstractions.',
                'Mass deltas use aluminum/steel volume against original lumped masses; no stiffness or fastener rating.',
                'Requires independent full-rack, non-box, carrier, payload and repeated-task qualification.']}
