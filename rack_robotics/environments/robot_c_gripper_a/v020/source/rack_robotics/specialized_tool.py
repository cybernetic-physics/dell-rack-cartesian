"""Reis-inspired fixed/moving jaw, physical rack drive and passive wrist.

Original parametric geometry, not a reproduction of the paper's unavailable CAD.
HS-422/PQ12-sized envelopes; torque, spring and friction settings are explicitly
uncalibrated design assumptions. The rack joint idealizes tooth contact/backlash,
but couples real angular and linear DOFs. No linear jaw actuator is installed.
"""
import math
from pxr import Gf, UsdPhysics, PhysxSchema, UsdShade
from rack_sim.geometry import box, cylinder, collision
from rack_robotics.mechanics import ROOT, body, joint, jaw_guide
from rack_robotics.tool_parameters import PINION_RADIUS, FIXED_JAW_X, OPEN_JAW_X, CLOSED_JAW_X


def revolute(stage,name,parent,child,anchor,axis,limits,stiffness,damping,torque):
    """Input spring constants are SI per radian; USD angular drives use degrees."""
    j=UsdPhysics.RevoluteJoint.Define(stage,ROOT+'/Joints/'+name)
    j.CreateBody0Rel().SetTargets([parent]); j.CreateBody1Rel().SetTargets([child])
    j.CreateLocalPos0Attr(Gf.Vec3f(*anchor)); j.CreateLocalPos1Attr(Gf.Vec3f(0))
    j.CreateAxisAttr(axis); j.CreateLowerLimitAttr(limits[0]); j.CreateUpperLimitAttr(limits[1])
    j.CreateCollisionEnabledAttr(False)
    d=UsdPhysics.DriveAPI.Apply(j.GetPrim(),'angular')
    d.CreateTypeAttr('force'); d.CreateTargetPositionAttr(0)
    d.CreateStiffnessAttr(stiffness*math.pi/180)
    d.CreateDampingAttr(damping*math.pi/180); d.CreateMaxForceAttr(torque)
    return d


def build_specialized_tool(stage,drives,mats,start_x):
    steel,dark,blue,orange,pad=(mats[k] for k in ('steel','anodized','blue','orange','pad'))
    mount=ROOT+'/ToolMount'; slider=ROOT+'/WristSlide'; frame=ROOT+'/ToolFrame'
    body(stage,mount,(start_x,.68,1.8),.03)
    box(stage,mount+'/Flange',(0,0,0),(.045,.008,.033),steel,True)
    for k,x in enumerate((-.016,.016)):
        box(stage,mount+f'/WristGuide{k}',(x,-.007,0),(.005,.006,.025),steel,True)
        cylinder(stage,mount+f'/FlangeBolt{k}',(x,.005,0),.002,.005,steel)
    body(stage,slider,(start_x,.68,1.8),.012)
    box(stage,slider+'/Slide',(0,-.010,0),(.026,.006,.022),blue,True)
    # Passive centred spring, never commanded by the controller. Hard stops
    # bound vertical displacement to 0.8 mm and pitch to 3 degrees.
    joint(stage,'WristComplianceZ',mount,slider,(0,0,0),'Z',(-.0008,.0008),0,40,10000,25)
    body(stage,frame,(start_x,.68,1.8),.105)
    revolute(stage,'WristPitch',slider,frame,(0,0,0),'X',(-3,3),80,.3,2)
    box(stage,frame+'/BackPlate',(0,-.018,0),(.03,.008,.028),steel,True)
    cylinder(stage,frame+'/PitchAxle',(0,-.014,0),.003,.032,steel,'X')
    box(stage,frame+'/UpperSpine',(0,-.057,.016),(.026,.075,.005),dark,True)
    # Full-size servo envelope, shaft vertical; 45.5 g included in frame mass.
    box(stage,frame+'/HS422Envelope',(0,-.060,-.0403),(.0198,.0406,.0366),dark,True)
    box(stage,frame+'/ServoBracket',(0,-.060,-.020),(.030,.050,.003),steel,True)
    cylinder(stage,frame+'/ServoShaft',(0,-.060,-.019),.0025,.006,steel,'Z')
    # Rack guide at the +Y tangent of the 6 mm pitch-radius pinion.
    box(stage,frame+'/RackGuide',(0,-.054,-.021),(.034,.008,.003),steel,True)
    for k,x in enumerate((-.0227,.017)):
        box(stage,frame+f'/RackStop{k}',(x,-.052,-.014),(.003,.007,.008),orange,True)
    left=ROOT+'/LeftJaw'; right=ROOT+'/RightJaw'
    for path,x in ((left,FIXED_JAW_X),(right,OPEN_JAW_X)):
        body(stage,path,(start_x+x,.55,1.8),.018)
        sign=-1 if path==left else 1
        # Thicken outward, keeping the inner face clear of the cable boot.
        # A 2 mm-wide 70 mm steel arm would be too flexible for a 10 N grip;
        # the 4.5 mm root retains a narrow 2 mm contact tip and clears the
        # insertion rails at the larger jaw opening.
        box(stage,path+'/Finger',(sign*.00125,.041,-.0005),(.0045,.070,.006),steel,True)
        tip=box(stage,path+'/Pad',(0,.006,-.0005),(.002,.008,.006),pad,True)
        UsdShade.MaterialBindingAPI.Apply(tip.GetPrim()).Bind(pad,materialPurpose='physics')
        jaw_guide(stage,path+'/UpperGuide',sign,True,steel)
        jaw_guide(stage,path+'/LowerGuide',sign,False,steel)
    # Fixed datum jaw is mechanically bolted to the compliant tool frame.
    weld=UsdPhysics.FixedJoint.Define(stage,ROOT+'/Joints/FixedDatumJaw')
    weld.CreateBody0Rel().SetTargets([frame]); weld.CreateBody1Rel().SetTargets([left])
    weld.CreateLocalPos0Attr(Gf.Vec3f(FIXED_JAW_X,-.13,0))
    weld.CreateCollisionEnabledAttr(False)
    box(stage,left+'/Root',(0,.090,.005),(.005,.032,.018),steel,True)
    box(stage,right+'/Rack',(-OPEN_JAW_X,.0775,-.016),(.030,.003,.004),steel,True)
    box(stage,right+'/RackBracket',(0,.076,-.0075),(.005,.006,.021),steel,True)
    rack=UsdPhysics.PrismaticJoint.Define(stage,ROOT+'/Joints/MovingJaw')
    rack.CreateBody0Rel().SetTargets([frame]); rack.CreateBody1Rel().SetTargets([right])
    rack.CreateLocalPos0Attr(Gf.Vec3f(OPEN_JAW_X,-.13,0))
    rack.CreateAxisAttr('X'); rack.CreateLowerLimitAttr(CLOSED_JAW_X-OPEN_JAW_X); rack.CreateUpperLimitAttr(0)
    rack.CreateCollisionEnabledAttr(False)
    pinion=ROOT+'/JawPinion'
    body(stage,pinion,(start_x,.620,1.784),.004)
    gear=cylinder(stage,pinion+'/Gear',(0,0,0),PINION_RADIUS,.004,steel,'Z')
    collision(gear.GetPrim())
    # Ideal transmission, not two independent servo targets. Body-pair contact
    # is disabled only for the meshing gear/rack, whose coupling replaces teeth.
    drives['servo']=revolute(stage,'JawServo',frame,pinion,(0,-.060,-.016),
                             'Z',(-2,60),.35,.003,.06)
    # Slower closure reduces impact; the torque cap and passive rack are unchanged.
    PhysxSchema.PhysxJointAPI.Apply(drives['servo'].GetPrim()).CreateMaxJointVelocityAttr(60.)
    coupling=PhysxSchema.PhysxPhysicsRackAndPinionJoint.Define(stage,ROOT+'/Joints/JawTransmission')
    coupling.CreateBody0Rel().SetTargets([pinion]); coupling.CreateBody1Rel().SetTargets([right])
    coupling.CreateHingeRel().SetTargets([ROOT+'/Joints/JawServo'])
    coupling.CreatePrismaticRel().SetTargets([ROOT+'/Joints/MovingJaw'])
    coupling.CreateRatioAttr(-math.degrees(1/PINION_RADIUS))
    coupling.CreateExcludeFromArticulationAttr(True); coupling.CreateCollisionEnabledAttr(False)
    tongue=ROOT+'/LatchTongue'
    body(stage,tongue,(start_x,.556,1.809),.004)
    box(stage,tongue+'/Tip',(0,0,0),(.003,.002,.001),orange,True)
    # Keep the neck forward of the boot even when the housing seats a few
    # tenths of a millimetre deeper than the nominal tool TCP.
    box(stage,tongue+'/Neck',(0,.0005,.003),(.003,.0015,.007),steel,True)
    box(stage,tongue+'/RaisedArm',(0,.016,.006),(.003,.030,.002),steel,True)
    # PQ12-P envelope. Only 5 mm of its 20 mm stroke is commanded. The 4 N
    # force cap is a compliant-force-limiter assumption, not its motor rating.
    box(stage,frame+'/PQ12Envelope',(0,-.095,.03325),(.0215,.015,.0365),blue,True)
    cylinder(stage,frame+'/TongueRod',(0,-.095,.012),.0015,.006,steel,'Z')
    drives['latch']=joint(stage,'LatchPress',frame,tongue,(0,-.124,.009),
                          'Z',(-.0055,.001),0,4,12000,8)
    PhysxSchema.PhysxJointAPI.Apply(drives['latch'].GetPrim()).CreateMaxJointVelocityAttr(.020)
    return drives
