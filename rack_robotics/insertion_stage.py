"""Open insertion-stage cross-section; geometry-only revision before physics.

The TCP, joint anchors/travel, gripper and connector are unchanged. Dimensions
are an original manufactured interface, not commercial stage CAD. Carrier
attachments need a separate compatible revision; old brackets are rejected.
"""
import math
from pxr import Gf, UsdGeom, UsdPhysics
from rack_robotics.hardware_detail import Hardware,ROOT

REVISION='open_insertion_stage_v2'
FRONT_SUPPORT_REVISION='rearward_insertion_front_support_v1'
CABLE_SUPPORT_REVISION='cable_clearance_insertion_front_support_v2'


def move_front_support_rearward(stage, cable_clearance=False):
    """Move the entire support 6 mm (or explicitly 11 mm) aft before physics.

    v2's support protrudes into a server fan even at full tool retraction.
    Moving the complete assembly retains the same shaft, nut, rails, stroke,
    masses, collision geometry and tool poses. The shaft now protrudes 2 mm
    beyond the 8 mm bearing, instead of ending at its center. The optional
    11 mm revision adds hanging-cable clearance while retaining 1 mm nominal
    separation from the bearing plate at full insertion. Both need physical
    travel qualification; neither changes the acceptance contact threshold.
    """
    robot=stage.GetPrimAtPath(ROOT)
    if not robot or robot.GetCustomDataByKey('insertion_revision') not in (
            REVISION,'open_insertion_stage_v3_rg2'):
        raise ValueError('Supported open insertion stage required')
    if robot.GetCustomDataByKey('front_support_revision'):
        raise ValueError('Front support already revised')
    names=['DepthSupportBearing','DepthFrontBearingHanger','DepthFrontBearingCrossbar',
           'DepthFrontBearingPost0','DepthFrontBearingPost1',
           'DepthFrontBearingBolt0','DepthFrontBearingBolt1']
    pending=[]
    for name in names:
        prim=stage.GetPrimAtPath(ROOT+'/Carriage/'+name)
        if not prim or not prim.IsA(UsdGeom.Xformable) or not prim.GetAttribute('xformOp:translate'):
            raise ValueError('Missing transformable support part: '+name)
        attr=prim.GetAttribute('xformOp:translate')
        pending.append((prim,attr,attr.Get()))
    distance=.011 if cable_clearance else .006
    revision=CABLE_SUPPORT_REVISION if cable_clearance else FRONT_SUPPORT_REVISION
    changes=[]
    for prim,attr,before in pending:
        attr.Set(before+Gf.Vec3d(0,distance,0))
        changes.append({'path':str(prim.GetPath()),'translation_delta_m':[0,distance,0]})
    robot.SetCustomDataByKey('front_support_revision',revision)
    return {'revision':revision,'changes':changes,'mass_delta_kg':0.,
            'setback_m':distance,
            'scope':f'Entire front bearing/support shifted aft {distance*1000:g} mm; all physical travel and other geometry retained',
            'limitations':['Custom interface; bearing axial retention and shaft machining remain engineering assumptions.',
                'Corrects the measured GPUFan10 interference locally; full-rack travel must be retested.']}


def complete_insertion_stage(stage,architecture):
    robot=stage.GetPrimAtPath(ROOT)
    if architecture not in ('A','B','C'):raise ValueError('Unknown architecture')
    if not robot or not robot.GetCustomDataByKey('hardware_revision'):
        raise ValueError('Drive-connected hardware required')
    if robot.GetCustomDataByKey('insertion_revision'):raise ValueError('Insertion stage already revised')
    if robot.GetCustomDataByKey('service_carrier_revision'):
        raise ValueError('Existing carrier brackets are not compatible with the open insertion stage')
    h=Hardware(stage);changes=[];delta={}
    carriage=ROOT+'/Carriage';mount=ROOT+'/ToolMount'
    wide_tool=bool(stage.GetPrimAtPath(mount+'/CrossHead'))
    side_x=.053 if wide_tool else .0475
    frame_width=.116 if wide_tool else .105
    revision='open_insertion_stage_v3_rg2' if wide_tool else REVISION

    def resize(path,center,size,density=2700.):
        prim=stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdGeom.Cube):raise ValueError('Missing stage box: '+path)
        before=list(prim.GetAttribute('xformOp:scale').Get())
        cube_size=UsdGeom.Cube(prim).GetSizeAttr().Get()
        before=[s*cube_size for s in before]
        owner=prim.GetParent()
        while not owner.HasAPI(UsdPhysics.RigidBodyAPI):owner=owner.GetParent()
        change=(math.prod(size)-math.prod(before))*density
        delta[str(owner.GetPath())]=delta.get(str(owner.GetPath()),0.)+change
        changes.append({'path':path,'old_size_m':before,'new_size_m':list(size),
                        'mass_delta_kg':change,'density_kg_m3':density})
        prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*center))
        UsdGeom.Cube(prim).GetSizeAttr().Set(1.)
        prim.GetAttribute('xformOp:scale').Set(Gf.Vec3f(*size))

    def shift(path,translation):
        prim=stage.GetPrimAtPath(path)
        if not prim:raise ValueError('Missing stage part: '+path)
        # Hardware.plate creates typeless grouping prims. Merely authoring
        # xformOp attributes there does not make USD evaluate a transform.
        if not prim.IsA(UsdGeom.Xformable):
            if prim.GetTypeName():raise ValueError('Part is not transformable: '+path)
            prim.SetTypeName('Xform')
        xf=UsdGeom.Xformable(prim)
        attr=prim.GetAttribute('xformOp:translate')
        if attr:attr.Set(attr.Get()+Gf.Vec3d(*translation))
        else:xf.AddTranslateOp().Set(Gf.Vec3d(*translation))
        changes.append({'path':path,'translation_delta_m':list(translation),'mass_delta_kg':0.})

    # Replace the closed plate, rather than disabling its collision while
    # leaving intersecting visible geometry. Original base lumped mass is
    # adjusted by the explicit aluminum volume proxy; calibration is pending.
    old=carriage+('/ToolSupport' if architecture=='B' else '/Plate')
    prim=stage.GetPrimAtPath(old)
    if not prim or not prim.IsA(UsdGeom.Cube):raise ValueError('Missing closed carriage plate')
    volume=math.prod(prim.GetAttribute('xformOp:scale').Get())*UsdGeom.Cube(prim).GetSizeAttr().Get()**3
    delta[carriage]=-volume*2700.
    changes.append({'path':old,'replaced_by':'OpenInsertionFrame','mass_delta_kg':-volume*2700.})
    prim.SetActive(False)
    for index,x in enumerate((-side_x,side_x)):
        h.box(carriage+f'/OpenInsertionFrame/Side{index}',(x,-.004,.021),(.010,.018,.110))
        if architecture in ('A','C'):
            h.box(carriage+f'/OpenInsertionFrame/GuideFoot{index}',(x,.005,-.0115),(.010,.010,.009))
    for name,z in [('Bottom',-.028),('Top',.070)]:
        # The full-size RG2 crosshead and side drops need a wider opening;
        # the bottom crossbar also sits aft of their entire insertion sweep.
        y=.004 if wide_tool and name=='Bottom' else -.004
        h.box(carriage+'/OpenInsertionFrame/'+name,(0,y,z),(frame_width,.018,.012))
    if architecture in ('A','C'):
        resize(carriage+'/TraverseBackPlate',(0,.010,0),(.116 if wide_tool else .100,.008,.028))
    if architecture=='A':
        resize(carriage+'/TraverseNutBracket',(0,.014,.018),(.025,.010,.016))

    # 200 mm rails carry the entire45.4 mm block over125 mm travel. Raising
    # them80 mm clears all three tool roots without shortening the workspace.
    for index,x in enumerate((-.030,.030)):
        resize(carriage+f'/DepthRail{index}',(x,-.100,.080),(.012,.200,.008),7850.)
        shift(mount+f'/DepthBlock{index}',(x-(-.022,.022)[index],-.030,.080))
        h.box(carriage+f'/OpenInsertionFrame/RailBed{index}',(x,-.100,.070),(.014,.200,.012))
    resize(mount+'/DepthBearingPlate',(0,-.040,.1005),(.090,.048,.009))
    for index,x in enumerate((-.019,.019)):
        h.box(mount+f'/InsertionRiser/Foot{index}',(x,-.020,.013),(.006,.048,.008))
        h.box(mount+f'/InsertionRiser/Post{index}',(x,-.040,.056),(.006,.008,.080))
        h.bolt(mount+f'/InsertionRiser/PlateBolt{index}',(x,-.040,.1005),'Z',.0015,.014)

    # Coaxial screw, nut, motor and open front support. The front hanger is
    # beyond the most extended bearing plate, not inside its swept volume.
    screw=stage.GetPrimAtPath(carriage+'/DepthScrew')
    if not screw or not screw.IsA(UsdGeom.Cylinder):raise ValueError('Missing insertion screw')
    cylinder=UsdGeom.Cylinder(screw)
    old_length=cylinder.GetHeightAttr().Get();radius=cylinder.GetRadiusAttr().Get()
    screw.GetAttribute('xformOp:translate').Set(Gf.Vec3d(0,-.0945,.094))
    cylinder.GetHeightAttr().Set(.221)
    change=math.pi*radius**2*(.221-old_length)*7850.;delta[carriage]+=change
    changes.append({'path':str(screw.GetPath()),'new_length_m':.221,'mass_delta_kg':change})
    shift(mount+'/DepthNut',(0,-.040,.080))
    shift(carriage+'/DepthMotor',(0,0,.080))
    for name in ('DepthMotorPlate','DepthCoupler'):shift(carriage+'/'+name,(0,0,.080))
    shift(carriage+'/DepthSupportBearing',(0,-.073,.080))
    resize(carriage+'/DepthFrontBearingHanger',(0,-.205,.108),(.018,.008,.014))
    resize(carriage+'/DepthFrontBearingCrossbar',(0,-.205,.118),(.090,.005,.006))
    for index,x in enumerate((-.040,.040)):
        resize(carriage+f'/DepthFrontBearingPost{index}',(x,-.205,.094),(.006,.008,.048))
        shift(carriage+f'/DepthFrontBearingBolt{index}',(x-(-.031,.031)[index],-.070,.080))

    for body,mass in h.added_mass.items():delta[body]=delta.get(body,0.)+mass
    for body,mass in delta.items():
        attr=UsdPhysics.MassAPI(stage.GetPrimAtPath(body)).GetMassAttr()
        if attr.Get()+mass<=0:raise ValueError('Nonpositive revised body mass')
        attr.Set(attr.Get()+mass)
    robot.SetCustomDataByKey('insertion_revision',revision)
    return {'revision':revision,'architecture':architecture,'wide_tool_frame':wide_tool,
            'changes':changes,'new_parts':h.parts,
            'mass_delta_kg_by_body':delta,'joint_travel_m':.125,'rail_length_m':.200,
            'scope':'Open insertion-stage geometry before physics; unchanged TCP, joints, controllers and connector',
            'limitations':['Custom dimensions, not vendor CAD or rated hardware.',
                'Removed base plate mass uses an aluminum volume proxy against the original lumped mass.',
                'Bearing blocks remain catalog envelopes; rail raceway and screw thread contact are abstracted.',
                'Carrier attachments, whole-robot/rack clearance, stiffness and fastener qualification remain separate gates.']}
