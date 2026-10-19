"""Full-size vendor RG2 with an original offset mount and RJ45 contact shoes.

All vendor bodies and collision meshes are preserved. Vendor internal-link
filtering remains, but new shoes/adapter/tongue have normal contact with the
rack, cable and plug. Custom fingers are rigid prototypes, not validated CAD.
"""
import os
from pathlib import Path
from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema, UsdShade
from rack_sim.geometry import box, cylinder
from rack_robotics.mechanics import ROOT, body, joint, jaw_guide
from rack_robotics.rg2_parameters import (
    OPEN_ANGLE, CLOSED_ANGLE, BASE_OFFSET, SHOE_INWARD, SHOE_RISE, SHOE_FORWARD,
    MOUNT_MASS, SHOE_MASS, CRADLE_WIDTH, SIDE_DROP_X, REAR_FLANGE_Z,
    REAR_FLANGE_HEIGHT, SHOULDER_OFFSET_X, SHOULDER_WIDTH, MOTOR_TORQUE_CAP_NM, GUIDE_THROAT,
)


def build_rg2_tool(stage, drives, mats, start_x, asset_path):
    if asset_path is None or not Path(asset_path).is_file():
        raise ValueError('RG2 requires an explicit preserved vendor asset path')
    steel, dark, blue, orange, pad = (mats[k] for k in ('steel','anodized','blue','orange','pad'))
    mount = ROOT + '/ToolMount'
    # Cradle/support aluminum envelopes plus tongue actuator and fasteners:
    # rounded to a 0.48 kg design estimate, not a measured assembly mass.
    body(stage, mount, (start_x, .68, 1.8), MOUNT_MASS)
    # Front flange, drop bracket and rear cradle physically connect the
    # original gripper flange below the depth rails, without scaling its body.
    box(stage, mount+'/Flange', (0,-.010,0), (.030,.006,.033), steel, True)
    # Route the cradle around the full gripper, not through its central motor
    # housing. The first central drop plate collided with that housing.
    box(stage, mount+'/CrossHead', (0,-.010,.035), (CRADLE_WIDTH,.008,.006), steel, True)
    for k,x in enumerate((-SIDE_DROP_X,SIDE_DROP_X)):
        box(stage,mount+f'/SideDrop{k}',(x,-.010,-.045),(.006,.008,.160),steel,True)
    box(stage, mount+'/Cradle', (0,.048,-.125), (CRADLE_WIDTH,.126,.006), steel, True)
    # Clear both bridge and carriage. The vendor base uses cooked convex
    # decomposition; a 1.5 mm VISUAL gap still contacted the carriage in PhysX.
    # Keep the original collision meshes and provide more physical clearance.
    box(stage, mount+'/RearFlange', (0,.107,REAR_FLANGE_Z), (.065,.008,REAR_FLANGE_HEIGHT), steel, True)
    for side, x in enumerate((-.020,.020)):
        for k,z in enumerate((-.095,-.055)):
            cylinder(stage, mount+f'/FlangeBolt{side}_{k}', (x,.113,z), .0025,.008,steel,'Y')

    rg2 = stage.DefinePrim(ROOT+'/RG2', 'Xform')
    layer_dir = Path(stage.GetRootLayer().realPath).parent
    rg2.GetReferences().AddReference(os.path.relpath(Path(asset_path).resolve(), layer_dir))
    rg2.GetVariantSets().GetVariantSet('Physics').SetVariantSelection('physx_parallel_grip')
    transform = UsdGeom.Xformable(rg2)
    transform.AddTranslateOp().Set(Gf.Vec3d(start_x+BASE_OFFSET[0], .68+BASE_OFFSET[1], 1.8+BASE_OFFSET[2]))
    transform.AddRotateXOp().Set(90)
    # Merge with the actual robot articulation. Do not apply vendor
    # self-collision disabling to the combined robot.
    rg2.RemoveAPI(UsdPhysics.ArticulationRootAPI)
    rg2.RemoveAPI(PhysxSchema.PhysxArticulationAPI)
    root_api = PhysxSchema.PhysxArticulationAPI(stage.GetPrimAtPath(ROOT+'/Joints/RackMount'))
    root_api.CreateSolverVelocityIterationCountAttr().Set(4)
    fixed = UsdPhysics.FixedJoint.Get(stage, ROOT+'/RG2/Physics/root_joint')
    fixed.GetBody0Rel().SetTargets([mount])
    fixed.GetLocalPos0Attr().Set(Gf.Vec3f(*BASE_OFFSET))
    fixed.GetLocalRot0Attr().Set(Gf.Quatf(Gf.Rotation(Gf.Vec3d(1,0,0),90).GetQuat()))
    fixed.CreateCollisionEnabledAttr(False)
    drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath(ROOT+'/RG2/Physics/finger_joint'), 'angular')
    # Preserve the vendor's approximately 60-degree authored startup pose.
    # The runner first extends the depth stage, then closes to the narrow
    # operating range in free space, then returns to park using joint drives.
    drive.GetTargetPositionAttr().Set(60.)
    drive.GetMaxForceAttr().Set(MOTOR_TORQUE_CAP_NM)
    drives['servo'] = drive

    # Each new shoe has its own mass and a physical fixed joint to the original
    # fingertip. Initial transforms are authored once, before World.reset().
    for side, sign in (('Left',-1), ('Right',1)):
        tip = ROOT+f'/RG2/Geometry/{side.lower()}_finger_tip_link'
        matrix = UsdGeom.Xformable(stage.GetPrimAtPath(tip)).ComputeLocalToWorldTransform(0)
        p = matrix.ExtractTranslation()
        origin = Gf.Vec3d(p[0]-sign*SHOE_INWARD, p[1]-SHOE_FORWARD, p[2]+SHOE_RISE)
        path = ROOT+'/'+side+'Jaw'
        # 75.3 x 10 x 4.5 mm steel riser alone is about 27 g; include the
        # shoulder, narrow shoe and guides in the 36 g lumped estimate.
        body(stage,path,origin,SHOE_MASS)
        # The original finger base occupies the OUTER side of the fingertip
        # origin. Keep this support 3 mm inward of that origin; an origin-
        # centred riser intersects the grandparent link and jams closure.
        box(stage,path+'/Riser',(sign*.001,SHOE_FORWARD,-SHOE_RISE/2),
            (.0045,.010,SHOE_RISE),steel,True)
        box(stage,path+'/Shoulder',(sign*SHOULDER_OFFSET_X,.014,-.0005),(SHOULDER_WIDTH,.010,.006),steel,True)
        box(stage,path+'/Finger',(sign*.00125,.011,-.0005),(.0045,.018,.006),steel,True)
        contact=box(stage,path+'/Pad',(0,.006,-.0005),(.002,.008,.006),pad,True)
        UsdShade.MaterialBindingAPI.Apply(contact.GetPrim()).Bind(pad,materialPurpose='physics')
        jaw_guide(stage,path+'/UpperGuide',sign,True,steel,throat=GUIDE_THROAT)
        jaw_guide(stage,path+'/LowerGuide',sign,False,steel,throat=GUIDE_THROAT)
        attachment=UsdPhysics.FixedJoint.Define(stage,ROOT+'/Joints/'+side+'Shoe')
        attachment.CreateBody0Rel().SetTargets([tip]); attachment.CreateBody1Rel().SetTargets([path])
        attachment.CreateLocalPos0Attr(Gf.Vec3f(matrix.GetInverse().Transform(origin)))
        attachment.CreateLocalRot0Attr(Gf.Quatf(matrix.GetInverse().ExtractRotationQuat()))
        attachment.CreateCollisionEnabledAttr(False)

    # Independently actuated latch tongue; its support clears the central depth
    # screw and its neck ends before the taller cable boot.
    for k,x in enumerate((-.010,.010)):
        box(stage,mount+f'/TongueSupport{k}',(x,-.012,.035),(.004,.006,.050),steel,True)
    box(stage,mount+'/TongueSpine',(0,-.054,.057),(.026,.090,.005),dark,True)
    box(stage,mount+'/PQ12Envelope',(0,-.095,.03325),(.0215,.015,.0365),blue,True)
    cylinder(stage,mount+'/TongueRod',(0,-.095,.012),.0015,.006,steel,'Z')
    tongue=ROOT+'/LatchTongue'
    body(stage,tongue,(start_x,.556,1.809),.004)
    box(stage,tongue+'/Tip',(0,0,0),(.003,.002,.001),orange,True)
    box(stage,tongue+'/Neck',(0,.0005,.003),(.003,.0015,.007),steel,True)
    box(stage,tongue+'/RaisedArm',(0,.016,.006),(.003,.030,.002),steel,True)
    drives['latch']=joint(stage,'LatchPress',mount,tongue,(0,-.124,.009),
                          'Z',(-.0055,.001),0,4,12000,8)
    PhysxSchema.PhysxJointAPI.Apply(drives['latch'].GetPrim()).CreateMaxJointVelocityAttr(.020)
    return drives


def prepare_rg2_park(stage, drives, architecture, park, step, dt):
    """Physically prepare wide vendor fingers clear of insertion guide rails.

    This is initialization, recorded separately from the autonomous connector
    trial. Never set rigid-body poses or articulation joint positions.
    """
    from rack_robotics.mechanics import pose, TOOL_OFFSET
    from rack_robotics.kinematics import joint_coordinates
    start = pose(stage, ROOT+'/ToolMount')
    current = (start[0], start[1]-TOOL_OFFSET, start[2])
    drives['servo'].GetTargetPositionAttr().Set(60.)

    def move(target, seconds):
        nonlocal current
        initial = current
        count = round(seconds/dt)
        for k in range(count):
            u = (k+1)/count; u = u*u*(3-2*u)
            nominal = tuple(a+(b-a)*u for a,b in zip(initial,target))
            for key,value in joint_coordinates(architecture,nominal).items():
                drives[key].GetTargetPositionAttr().Set(value)
            step()
        current = target

    # Lower the bulky cradle away from the top rack brackets, and put the
    # finger guides forward of the depth rails before closing across them.
    move((current[0],.505,1.75),1.0)
    drives['servo'].GetTargetPositionAttr().Set(OPEN_ANGLE)
    move(current,2.5)
    move(park,1.8)
    move(park,.5)
