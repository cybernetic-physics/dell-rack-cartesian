"""First dimensioned robot/tool prototype; all lengths in metres.

Custom guide/screw gantry, EGP25-envelope parallel tool and independent tongue.
CAD detail, motor transmission and coverage audits are still development work.
No function in this module moves or constrains the connector.
"""
from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema, UsdShade
from rack_sim.geometry import xform, box, cylinder, rigid, material, collision

ROOT = '/World/Robot'
TOOL_OFFSET = .13


def reference_drives(stage,architecture='A',gripper='A'):
    """Bind existing saved joints without rebuilding or moving the assembly."""
    names={'z':'Lift','x':'Traverse','y':'Insertion','left':'LeftJaw',
           'right':'RightJaw','latch':'LatchPress'}
    if architecture=='B':
        del names['x']
        names.update(x_outer='OuterExtension',x_inner='InnerExtension')
    if gripper in ('B','C'):
        del names['left']; del names['right']
        names['servo']='JawServo'
    drives={}
    for key,name in names.items():
        prim=stage.GetPrimAtPath(ROOT+'/RG2/Physics/finger_joint' if gripper=='B' and key=='servo' else ROOT+'/Joints/'+name)
        angular=key=='servo'
        kind=UsdPhysics.RevoluteJoint if angular else UsdPhysics.PrismaticJoint
        if not prim or not prim.IsA(kind):
            raise ValueError(f'Saved environment is missing joint {name}')
        drives[key]=UsdPhysics.DriveAPI(prim,'angular' if angular else 'linear')
    return drives


def body(stage, path, position, mass):
    prim = xform(stage, path, position).GetPrim()
    rigid(prim, mass)
    return prim


def joint(stage, name, parent, child, anchor, axis, limits, target, force,
          stiffness=40000, damping=150):
    j = UsdPhysics.PrismaticJoint.Define(stage, ROOT+'/Joints/'+name)
    j.CreateBody0Rel().SetTargets([parent])
    j.CreateBody1Rel().SetTargets([child])
    j.CreateLocalPos0Attr(Gf.Vec3f(*anchor))
    j.CreateLocalPos1Attr(Gf.Vec3f(0))
    j.CreateAxisAttr(axis)
    j.CreateLowerLimitAttr(limits[0]); j.CreateUpperLimitAttr(limits[1])
    j.CreateCollisionEnabledAttr(False)
    d = UsdPhysics.DriveAPI.Apply(j.GetPrim(), 'linear')
    d.CreateTypeAttr('force'); d.CreateTargetPositionAttr(target)
    d.CreateStiffnessAttr(stiffness); d.CreateDampingAttr(damping)
    d.CreateMaxForceAttr(force)
    return d


def pose(stage, path):
    return UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(0).ExtractTranslation()


def jaw_guide(stage,path,sign,upper,mat,throat=.0073):
    """Chamfered housing shoe: closing jaws mechanically correct pitch.

    The 7.3 mm throat fits the 7.2 mm shell. A 0.8 mm lead-in over 1.2 mm
    admits a sagged plug; flat lands constrain pitch without touching the latch.
    Mirrored convex prisms remain real collision shapes, not orientation locks.
    """
    inner=-sign
    from rack_robotics.jaw_geometry import guide_vertical_profile
    land_z,section_z=guide_vertical_profile(upper,throat)
    # Use an analytic box for the flat bearing land so sub-millimetre support
    # does not depend on convex-hull cooking simplification.
    box(stage,path+'Land',(inner*.0005,.00525,land_z),
        (.0026,.0065,.0016),mat,True)
    section=list(zip((.0018,.0030,.0030,.0018),section_z))
    # End before the boot begins at Y=+9 mm; its 9 mm height must not be
    # squeezed into the 7.3 mm shell throat.
    points=[Gf.Vec3f(inner*x,y,z) for y in (.002,.0085) for x,z in section]
    n=len(section)
    mesh=UsdGeom.Mesh.Define(stage,path)
    mesh.CreatePointsAttr(points)
    mesh.CreateFaceVertexCountsAttr([n,n]+[4]*n)
    mesh.CreateFaceVertexIndicesAttr(list(reversed(range(n)))+list(range(n,2*n))+
        [v for i in range(n) for v in (i,(i+1)%n,(i+1)%n+n,i+n)])
    mesh.CreateSubdivisionSchemeAttr('none')
    UsdShade.MaterialBindingAPI.Apply(mesh.GetPrim()).Bind(mat)
    collision(mesh.GetPrim())
    UsdPhysics.MeshCollisionAPI.Apply(mesh.GetPrim()).CreateApproximationAttr('convexHull')


def robot_materials(stage):
    steel = material(stage, 'RobotSteel', (.48,.54,.60), .85, .23)
    anodized = material(stage, 'RobotAnodized', (.07,.12,.16), .7, .3)
    blue = material(stage, 'RobotBlue', (.03,.21,.36), .5, .28)
    orange = material(stage, 'RobotTongue', (.94,.32,.03), .2, .3)
    pad = material(stage, 'RobotPad', (.03,.035,.04), 0, .7)
    friction = UsdPhysics.MaterialAPI.Apply(pad.GetPrim())
    friction.CreateStaticFrictionAttr(.7); friction.CreateDynamicFrictionAttr(.6)
    friction.CreateRestitutionAttr(0)
    return {'steel':steel,'anodized':anodized,'blue':blue,'orange':orange,'pad':pad}


def build_reference_robot(stage,gripper='A',gripper_asset=None):
    xform(stage, ROOT)
    mats=robot_materials(stage)
    steel,anodized,blue,orange,pad=(mats[k] for k in ('steel','anodized','blue','orange','pad'))
    base = ROOT+'/Frame'; bridge = ROOT+'/Bridge'; carriage = ROOT+'/Carriage'
    mount = ROOT+'/ToolMount'
    body(stage, base, (0,0,0), 5.)
    root_joint = UsdPhysics.FixedJoint.Define(stage, ROOT+'/Joints/RackMount')
    root_joint.CreateBody1Rel().SetTargets([base])
    # The existing rack is static; this fixed root idealizes the bolted rack
    # connection. Stand-offs below physically bridge to its rear frame posts.
    UsdPhysics.ArticulationRootAPI.Apply(root_joint.GetPrim())
    px = PhysxSchema.PhysxArticulationAPI.Apply(root_joint.GetPrim())
    px.CreateSolverPositionIterationCountAttr(128)
    px.CreateSolverVelocityIterationCountAttr(8)
    px.CreateEnabledSelfCollisionsAttr(True)
    for side, x in enumerate((-.26,.26)):
        box(stage, f'{base}/Upright{side}', (x,.735,1.425), (.04,.04,.89), anodized, True)
        box(stage, f'{base}/Guide{side}', (x,.710,1.425), (.012,.008,.85), steel, True)
        cylinder(stage, f'{base}/Screw{side}', (x+.018,.704,1.425), .004,.83,steel,'Z')
        for k,z in enumerate((1.01,1.84)):
            # Bracket runs from the fixed rack rear post (Y=.575) to gantry.
            box(stage,f'{base}/Bracket{side}_{k}',(x,.655,z),(.05,.16,.008),steel,True)
            box(stage,f'{base}/PostClamp{side}_{k}',((-.285,.285)[side],.593,z),(.04,.006,.05),steel,True)
            for n,dz in enumerate((-.016,.016)):
                cylinder(stage,f'{base}/Bolt{side}_{k}_{n}',((-.285,.285)[side],.598,z+dz),.003,.006,steel)
        box(stage,f'{base}/Motor{side}',(x,.735,1.915),(.042,.042,.045),blue,True)
        for k,z in enumerate((1.03,1.82)):
            box(stage,f'{base}/Stop{side}_{k}',(x,.698,z),(.023,.016,.008),orange,True)
    body(stage, bridge, (0,.72,1.80), 1.3)
    box(stage,bridge+'/Beam',(0,0,0),(.54,.032,.04),anodized,True)
    box(stage,bridge+'/XGuide',(0,-.021,0),(.48,.008,.012),steel,True)
    cylinder(stage,bridge+'/XScrew',(0,-.023,.018),.004,.48,steel,'X')
    for side,x in enumerate((-.26,.26)):
        box(stage,bridge+f'/GuideBlock{side}',(x,-.011,0),(.027,.013,.0454),steel,True)
    box(stage,bridge+'/XMotor',(.29,0,0),(.045,.042,.042),blue,True)
    body(stage,carriage,(.15,.68,1.80),.38)
    box(stage,carriage+'/Plate',(0,0,0),(.055,.012,.06),blue,True)
    for k,x in enumerate((-.022,.022)):
        box(stage,carriage+f'/DepthRail{k}',(x,-.055,0),(.012,.16,.008),steel,True)
    cylinder(stage,carriage+'/DepthScrew',(0,-.055,.014),.003,.16,steel,'Y')
    box(stage,carriage+'/DepthMotor',(0,.037,.014),(.028,.035,.028),blue,True)
    drives = {
        'z': joint(stage,'Lift',base,bridge,(0,.72,1.80),'Z',(-.70,0),0,100,100000,500),
        'x': joint(stage,'Traverse',bridge,carriage,(0,-.04,0),'X',(-.21,.21),.15,50),
        'y': joint(stage,'Insertion',carriage,mount,(0,0,0),'Y',(-.125,0),0,8,15000,35),
    }
    return build_tool(stage,drives,mats,gripper,gripper_asset=gripper_asset)


def build_tool(stage,drives,mats,gripper='A',start_x=.15,gripper_asset=None):
    if gripper=='A': return build_precision_tool(stage,drives,mats,start_x)
    if gripper=='B':
        from rack_robotics.rg2_tool import build_rg2_tool
        return build_rg2_tool(stage,drives,mats,start_x,gripper_asset)
    if gripper=='C':
        from rack_robotics.specialized_tool import build_specialized_tool
        return build_specialized_tool(stage,drives,mats,start_x)
    raise ValueError(f'Unsupported gripper: {gripper}')


def build_precision_tool(stage,drives,mats,start_x=.15):
    """The same physical tool can mount to different articulated architectures."""
    steel,anodized,blue,orange,pad=(mats[k] for k in ('steel','anodized','blue','orange','pad'))
    mount=ROOT+'/ToolMount'
    body(stage,mount,(start_x,.68,1.80),.18)
    box(stage,mount+'/Adapter',(0,0,0),(.045,.008,.033),steel,True)
    box(stage,mount+'/Housing',(0,-.05965,0),(.0265,.0727,.018),anodized,True)
    box(stage,mount+'/TailBracket',(0,-.013,0),(.025,.020,.018),steel,True)
    for k,x in enumerate((-.009,.009)):
        cylinder(stage,mount+f'/MountBolt{k}',(x,-.006,0),.002,.005,steel)
    for side,sign in (('Left',-1),('Right',1)):
        path=ROOT+'/'+side+'Jaw'
        body(stage,path,(start_x+sign*.0093,.55,1.80),.014)
        box(stage,path+'/Finger',(0,.020,-.0005),(.002,.028,.006),steel,True)
        tip=box(stage,path+'/Pad',(0,.006,-.0005),(.002,.008,.006),pad,True)
        UsdShade.MaterialBindingAPI.Apply(tip.GetPrim()).Bind(pad,materialPurpose='physics')
        jaw_guide(stage,path+'/UpperGuide',sign,True,steel)
        jaw_guide(stage,path+'/LowerGuide',sign,False,steel)
        limits=(-.0093,-.0063) if sign<0 else (.0063,.0093)
        drives[side.lower()]=joint(stage,side+'Jaw',mount,path,(0,-TOOL_OFFSET,0),
                                  'X',limits,sign*.0093,10,20000,8)
    tongue=ROOT+'/LatchTongue'
    body(stage,tongue,(start_x,.556,1.809),.004)
    box(stage,tongue+'/Tip',(0,0,0),(.003,.002,.001),orange,True)
    box(stage,tongue+'/Neck',(0,.002,.003),(.003,.002,.007),steel,True)
    box(stage,tongue+'/RaisedArm',(0,.016,.006),(.003,.030,.002),steel,True)
    box(stage,mount+'/TongueActuator',(0,-.095,.028),(.015,.025,.035),blue,True)
    drives['latch']=joint(stage,'LatchPress',mount,tongue,(0,-.124,.009),
                          'Z',(-.0055,.001),0,4,12000,8)
    return drives
