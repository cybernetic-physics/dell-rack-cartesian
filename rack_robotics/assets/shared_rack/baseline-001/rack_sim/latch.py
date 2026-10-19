"""Contact-driven RJ45 latch: a compliant hinge, ramp, shoulder and press pad.

Mechanical approach follows Newton's contacts_rj45_plug example (spring-loaded
rigid latch), not an FEM plastic model. No joint ever connects plug to socket.
All distances SI; USD angular drive stiffness/damping are per degree.
"""
import math
from pxr import UsdGeom,UsdPhysics,Gf
from .geometry import xform,box,rigid,collision,bind

PIVOT=(0,-.009,.0036)
REST_DEG=8.0
SPRING_NM_RAD=.15
DAMPING_NMS_RAD=.003
LIP_INNER_Y=-.0013
LIP_UNDERSIDE=.0048
TOOTH_REAR=(0,.0075,.0011)

def frictionless(stage,prim):
    from pxr import UsdShade
    mat=UsdShade.Material.Define(stage,'/World/Materials/LatchContact')
    api=UsdPhysics.MaterialAPI.Apply(mat.GetPrim())
    api.CreateStaticFrictionAttr(0); api.CreateDynamicFrictionAttr(0)
    api.CreateRestitutionAttr(0)
    UsdShade.MaterialBindingAPI.Apply(prim).Bind(mat,materialPurpose='physics')

def create_lip(stage,root,mats):
    lip=box(stage,root+'/LatchLip',(0,-.00055,.0059),(.0054,.0015,.0022),mats['steel'],True)
    frictionless(stage,lip.GetPrim())

def create_latch(stage,plug_pos,mats):
    pivot=Gf.Vec3d(*plug_pos)+Gf.Vec3d(*PIVOT)
    body=xform(stage,'/World/Latch',pivot)
    body.AddOrientOp().Set(Gf.Quatf(Gf.Rotation(Gf.Vec3d(1,0,0),REST_DEG).GetQuat()))
    rigid(body.GetPrim(),.0006)
    arm=box(stage,'/World/Latch/Arm',(0,.0085,0),(.0045,.017,.0006),mats['plug'],True)
    frictionless(stage,arm.GetPrim())
    # Convex tooth: low leading ramp on entry, steep back shoulder on withdrawal.
    section=[(.0045,-.0003),(.0075,-.0003),(.0075,.0011),(.0045,.0003)]
    mesh=UsdGeom.Mesh.Define(stage,'/World/Latch/Tooth')
    mesh.CreatePointsAttr([Gf.Vec3f(x,y,z) for x in (-.00225,.00225) for y,z in section])
    mesh.CreateFaceVertexCountsAttr([4]*6)
    mesh.CreateFaceVertexIndicesAttr([0,3,2,1,4,5,6,7,0,1,5,4,1,2,6,5,2,3,7,6,3,0,4,7])
    mesh.CreateSubdivisionSchemeAttr('none'); bind(mesh.GetPrim(),mats['plug'])
    collision(mesh.GetPrim(),.00002)
    UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr('convexHull')
    frictionless(stage,mesh.GetPrim())
    hinge=UsdPhysics.RevoluteJoint.Define(stage,'/World/LatchHinge')
    hinge.CreateBody0Rel().SetTargets(['/World/Plug']); hinge.CreateBody1Rel().SetTargets(['/World/Latch'])
    hinge.CreateLocalPos0Attr(Gf.Vec3f(*PIVOT)); hinge.CreateLocalPos1Attr(Gf.Vec3f(0))
    hinge.CreateAxisAttr('X'); hinge.CreateLowerLimitAttr(-6); hinge.CreateUpperLimitAttr(12)
    hinge.CreateCollisionEnabledAttr(False)
    spring=UsdPhysics.DriveAPI.Apply(hinge.GetPrim(),'angular')
    spring.CreateTypeAttr('force'); spring.CreateTargetPositionAttr(REST_DEG)
    spring.CreateStiffnessAttr(SPRING_NM_RAD*math.pi/180)
    spring.CreateDampingAttr(DAMPING_NMS_RAD*math.pi/180)
    spring.CreateMaxForceAttr(.1)
    # A small force-limited pad represents a fingertip pressing the free end.
    # The command moves this pad, NEVER the latch or its return-spring target.
    finger=box(stage,'/World/ClipPress',Gf.Vec3d(*plug_pos)+Gf.Vec3d(0,.006,.009),
               (.003,.002,.001),mats['orange'],True)
    rigid(finger.GetPrim(),.002); frictionless(stage,finger.GetPrim())
    slide=UsdPhysics.PrismaticJoint.Define(stage,'/World/ClipPressSlide')
    slide.CreateBody0Rel().SetTargets(['/World/Plug']); slide.CreateBody1Rel().SetTargets(['/World/ClipPress'])
    slide.CreateLocalPos0Attr(Gf.Vec3f(0,.006,.009)); slide.CreateLocalPos1Attr(Gf.Vec3f(0))
    slide.CreateAxisAttr('Z'); slide.CreateLowerLimitAttr(-.0055); slide.CreateUpperLimitAttr(.001)
    slide.CreateCollisionEnabledAttr(False)
    drive=UsdPhysics.DriveAPI.Apply(slide.GetPrim(),'linear')
    drive.CreateTypeAttr('force'); drive.CreateTargetPositionAttr(0)
    drive.CreateStiffnessAttr(12000); drive.CreateDampingAttr(8); drive.CreateMaxForceAttr(4)

def measured_latch(stage,plug_matrix,mouth):
    matrix=UsdGeom.Xformable(stage.GetPrimAtPath('/World/Latch')).ComputeLocalToWorldTransform(0)
    inverse=plug_matrix.GetInverse()
    local0=inverse.Transform(matrix.Transform(Gf.Vec3d(0)))
    local1=inverse.Transform(matrix.Transform(Gf.Vec3d(0,.01,0)))
    direction=local1-local0
    tooth=matrix.Transform(Gf.Vec3d(*TOOTH_REAR))-mouth
    angle=math.degrees(math.atan2(direction[2],direction[1]))
    return {'latch_angle_deg':angle,'hook_y_m':float(tooth[1]),'hook_z_m':float(tooth[2]),
            'hook_clear':bool(tooth[2]<LIP_UNDERSIDE-.00004),
            'hook_behind_lip':bool(tooth[1]<LIP_INNER_Y+.00012 and tooth[2]>LIP_UNDERSIDE+.00004)}
