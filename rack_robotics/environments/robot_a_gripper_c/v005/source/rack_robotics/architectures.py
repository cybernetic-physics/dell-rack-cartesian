"""Mechanically distinct Cartesian assemblies sharing a physical tool flange."""
from pxr import UsdPhysics, PhysxSchema
from rack_sim.geometry import xform, box, cylinder
from rack_robotics.mechanics import ROOT, body, joint, robot_materials, build_tool
from rack_robotics.rg2_parameters import TELESCOPING_PARK_X


def build_telescoping_robot(stage,gripper='A',gripper_asset=None):
    """Side lift + two 200 mm screw-driven stages with 100 mm overlap.

    Guide blocks use the researched MGN12H envelope, not an exact vendor CAD
    digital twin. Beam sections are custom 300 mm members. Parked leftward
    overhang and rigid-beam approximation are explicit evaluation limitations.
    """
    xform(stage,ROOT)
    mats=robot_materials(stage)
    steel,blue,dark,orange=(mats[k] for k in ('steel','blue','anodized','orange'))
    base=ROOT+'/Frame'; lift=ROOT+'/LiftCarriage'
    middle=ROOT+'/MiddleBoom'; carriage=ROOT+'/Carriage'; mount=ROOT+'/ToolMount'
    start_x=TELESCOPING_PARK_X if gripper=='B' else -.19
    extension=(start_x+.20)/2
    body(stage,base,(0,0,0),4.)
    root_joint=UsdPhysics.FixedJoint.Define(stage,ROOT+'/Joints/RackMount')
    root_joint.CreateBody1Rel().SetTargets([base])
    UsdPhysics.ArticulationRootAPI.Apply(root_joint.GetPrim())
    px=PhysxSchema.PhysxArticulationAPI.Apply(root_joint.GetPrim())
    px.CreateSolverPositionIterationCountAttr(128); px.CreateSolverVelocityIterationCountAttr(8)
    px.CreateEnabledSelfCollisionsAttr(True)
    box(stage,base+'/Upright',(-.26,.815,1.45),(.05,.04,1.),dark,True)
    for k,x in enumerate((-.28,-.24)):
        box(stage,base+f'/VerticalGuide{k}',(x,.789,1.47),(.012,.008,.94),steel,True)
    cylinder(stage,base+'/LiftScrew',(-.26,.775,1.47),.004,.94,steel,'Z')
    cylinder(stage,base+'/LiftCoupler',(-.26,.775,1.949),.007,.018,steel,'Z')
    box(stage,base+'/LiftMotor',(-.26,.775,1.98),(.042,.042,.045),blue,True)
    box(stage,base+'/MotorPlate',(-.26,.798,1.955),(.065,.075,.006),steel,True)
    for k,z in enumerate((1.01,1.92)):
        box(stage,base+f'/RackStandoff{k}',(-.275,.70,z),(.04,.25,.008),steel,True)
        box(stage,base+f'/PostClamp{k}',(-.285,.593,z),(.04,.006,.06),steel,True)
        for b,dz in enumerate((-.02,.02)):
            cylinder(stage,base+f'/RackBolt{k}_{b}',(-.285,.598,z+dz),.003,.006,steel)
    body(stage,lift,(-.20,.78,1.8),.8)
    box(stage,lift+'/VerticalPlate',(-.06,.004,.03),(.1,.012,.16),blue,True)
    for k,x in enumerate((-.08,-.04)):
        for b,z in enumerate((-.03,.07)):
            box(stage,lift+f'/LiftBlock{k}_{b}',(x,.005,z),(.027,.013,.0454),steel,True)
    body(stage,middle,(-.20+extension,.73,1.8),.75)
    body(stage,carriage,(start_x,.68,1.8),.65)
    for index,path in enumerate((lift,middle,carriage)):
        # The tip is the body origin. Each member extends 300 mm behind it.
        box(stage,path+'/Boom',(-.15,0,.05),(.30,.032,.04),dark,True)
        if index<2:
            box(stage,path+'/HorizontalGuide',(-.15,-.021,.05),(.30,.008,.012),steel,True)
            cylinder(stage,path+'/Screw',(-.15,-.023,.078),.004,.28,steel,'X')
            cylinder(stage,path+'/Coupler',(-.30,-.023,.078),.007,.020,steel,'X')
            box(stage,path+'/Motor',(-.329,-.023,.078),(.038,.042,.042),blue,True)
            box(stage,path+'/MotorPlate',(-.307,-.008,.065),(.006,.07,.065),steel,True)
            for stop,x in enumerate((-.29,-.01)):
                box(stage,path+f'/EndStop{stop}',(x,-.032,.05),(.006,.014,.018),orange,True)
        if index>0:
            for block,x in enumerate((-.27,-.22)):
                box(stage,path+f'/Bearing{block}',(x,.0255,.05),(.0454,.013,.027),steel,True)
            box(stage,path+'/LeadNut',(-.245,.027,.078),(.022,.02,.022),steel,True)
    box(stage,carriage+'/ToolSupport',(0,0,.025),(.055,.012,.09),blue,True)
    for k,x in enumerate((-.022,.022)):
        box(stage,carriage+f'/DepthRail{k}',(x,-.055,0),(.012,.16,.008),steel,True)
    cylinder(stage,carriage+'/DepthScrew',(0,-.055,.014),.003,.16,steel,'Y')
    box(stage,carriage+'/DepthMotor',(0,.037,.014),(.028,.035,.028),blue,True)
    drives={
        'z':joint(stage,'Lift',base,lift,(-.20,.78,1.8),'Z',(-.70,0),0,100,200000,700),
        'x_outer':joint(stage,'OuterExtension',lift,middle,(0,-.05,0),'X',(0,.20),extension,35,100000,300),
        'x_inner':joint(stage,'InnerExtension',middle,carriage,(0,-.05,0),'X',(0,.20),extension,35,100000,300),
        'y':joint(stage,'Insertion',carriage,mount,(0,0,0),'Y',(-.125,0),0,8,15000,35),
    }
    if gripper=='B':
        # Initial conditions only, BEFORE World.reset(): a USD body transform
        # and a drive target do not initialize reduced-coordinate joint state.
        # Without these, PhysX collapses both stages to zero and the full-size
        # RG2 cradle overlaps the lift before any controller can move it clear.
        for name in ('x_outer','x_inner'):
            state=PhysxSchema.JointStateAPI.Apply(drives[name].GetPrim(),'linear')
            state.CreatePositionAttr(extension); state.CreateVelocityAttr(0.)
    return build_tool(stage,drives,mats,gripper,start_x=start_x,gripper_asset=gripper_asset)
