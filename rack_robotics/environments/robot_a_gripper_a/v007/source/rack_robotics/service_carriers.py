"""Passive, collision-enabled service-carrier links, authored before physics.

Original simplified geometry based on Series06.20.038.0 envelopes, not vendor
CAD. Six30-degree links give a38.637 mm polygonal bend radius. Link mass uses
the catalog0.17 kg/m plus an explicit assumed0.04 kg/m service-wire fill.
No runtime pose writes, motorized carrier joints, or connector attachments.
"""
import math
from pxr import Gf, Sdf, Usd, UsdGeom, UsdPhysics, UsdShade
from rack_robotics.hardware_detail import Hardware

ROOT='/World/Robot'
PITCH=.020
WIDTH=.027
HEIGHT=.015
INNER_WIDTH=.020
INNER_HEIGHT=.0105
BEND_LINKS=6
LIMIT_DEG=30.
LINK_MASS=(.17+.04)*PITCH
SEPARATION=PITCH/math.sin(math.pi/(2*BEND_LINKS))


def initialize_cartesian_states(stage, architecture):
    """Author ONLY startup joint coordinates from the existing body geometry.

    Reduced-coordinate articulations otherwise initialize unspecified DOFs at
    zero, which can tear an already attached closed carrier loop. Call before
    physics starts; never use this as a runtime pose correction. Tool and plug
    state are deliberately outside this function's scope.
    """
    names=['Lift','Insertion']+(['OuterExtension','InnerExtension'] if architecture=='B' else ['Traverse'])
    if architecture not in ('A','B','C'): raise ValueError('Unknown architecture')
    cache=UsdGeom.XformCache(); pending=[]
    for name in names:
        path=ROOT+'/Joints/'+name; prim=stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdPhysics.PrismaticJoint):
            raise ValueError('Missing Cartesian prismatic joint: '+path)
        joint=UsdPhysics.PrismaticJoint(prim); mats=[]; anchors=[]
        for index in (0,1):
            bodies=getattr(joint,f'GetBody{index}Rel')().GetTargets()
            if len(bodies)!=1 or not stage.GetPrimAtPath(bodies[0]):
                raise ValueError('Expected one existing body per Cartesian joint end')
            matrix=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(bodies[0])); mats.append(matrix)
            anchors.append(matrix.Transform(Gf.Vec3d(getattr(joint,f'GetLocalPos{index}Attr')().Get())))
        local_axis=Gf.Vec3d(*(1 if a==joint.GetAxisAttr().Get() else 0 for a in 'XYZ'))
        rotation=Gf.Rotation(Gf.Quatd(joint.GetLocalRot0Attr().Get()))
        axis=mats[0].TransformDir(rotation.TransformDir(local_axis)).GetNormalized()
        delta=anchors[1]-anchors[0]; position=Gf.Dot(delta,axis)
        residual=(delta-position*axis).GetLength()
        lower=joint.GetLowerLimitAttr().Get(); upper=joint.GetUpperLimitAttr().Get()
        if residual>1e-6 or not math.isfinite(position):
            raise ValueError('Inconsistent Cartesian joint geometry: '+path)
        if position<lower-1e-6 or position>upper+1e-6:
            raise ValueError('Initial Cartesian position outside limits: '+path)
        position=min(upper,max(lower,position)) # Authored float anchor roundoff only.
        pending.append((prim,{'joint':path,'position_m':position,'off_axis_residual_m':residual,
                              'previous_position_m':prim.GetAttribute('state:linear:physics:position').Get()}))
    for prim,report in pending:
        prim.AddAppliedSchema('PhysicsJointStateAPI:linear')
        prim.CreateAttribute('state:linear:physics:position',Sdf.ValueTypeNames.Float).Set(report['position_m'])
        prim.CreateAttribute('state:linear:physics:velocity',Sdf.ValueTypeNames.Float).Set(0.)
    return [report for _,report in pending]


def u_link_points(start, travel, normal, outbound, returning):
    if min(outbound,returning)<1: raise ValueError('Both straight legs require links')
    t=Gf.Vec3d(*travel); n=Gf.Vec3d(*normal)
    if abs(t.GetLength()-1)>1e-9 or abs(n.GetLength()-1)>1e-9 or abs(Gf.Dot(t,n))>1e-9:
        raise ValueError('Travel and bend-normal must be orthonormal')
    angles=([0.]*outbound+[(i+.5)*math.pi/BEND_LINKS for i in range(BEND_LINKS)]
            +[math.pi]*returning)
    points=[Gf.Vec3d(*start)]
    for angle in angles: points.append(points[-1]+PITCH*(math.cos(angle)*t+math.sin(angle)*n))
    return points,angles


def orientation(t,n,angle):
    x=math.cos(angle)*Gf.Vec3d(*t)+math.sin(angle)*Gf.Vec3d(*n)
    y=-math.sin(angle)*Gf.Vec3d(*t)+math.cos(angle)*Gf.Vec3d(*n)
    z=Gf.Cross(x,y)
    matrix=Gf.Matrix3d(x[0],x[1],x[2],y[0],y[1],y[2],z[0],z[1],z[2])
    return Gf.Quatf(matrix.ExtractRotation().GetQuat())


def collision(prim):
    UsdPhysics.CollisionAPI.Apply(prim)
    prim.AddAppliedSchema('PhysxCollisionAPI')
    prim.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.00005)
    prim.CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(0.)


def fixed_attachment(stage,path,body0,body1,point):
    cache=UsdGeom.XformCache(); j=UsdPhysics.FixedJoint.Define(stage,path)
    for index,body in enumerate((body0,body1)):
        matrix=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(body)); inv=matrix.GetInverse()
        getattr(j,f'CreateBody{index}Rel')().SetTargets([body])
        getattr(j,f'CreateLocalPos{index}Attr')(Gf.Vec3f(inv.Transform(Gf.Vec3d(*point))))
        getattr(j,f'CreateLocalRot{index}Attr')(Gf.Quatf(inv.ExtractRotationQuat()))
    j.CreateCollisionEnabledAttr(False) # Only the directly connected pair.
    j.CreateExcludeFromArticulationAttr(True)
    return j


def build_chain(stage,name,start,travel,normal,outbound,returning,body0,body1):
    path=ROOT+'/ServiceCarriers/'+name
    if stage.GetPrimAtPath(path): raise ValueError('Carrier already authored')
    points,angles=u_link_points(start,travel,normal,outbound,returning)
    mat=UsdShade.Material.Get(stage,'/World/Materials/RobotAnodized')
    if not mat: raise ValueError('Missing robot material')
    paths=[]
    for index,(p0,p1,angle) in enumerate(zip(points,points[1:],angles)):
        body=path+f'/Link{index:03d}'; paths.append(body)
        xform=UsdGeom.Xform.Define(stage,body)
        xform.AddTranslateOp().Set((p0+p1)/2)
        xform.AddOrientOp().Set(orientation(travel,normal,angle))
        prim=xform.GetPrim(); rigid=UsdPhysics.RigidBodyAPI.Apply(prim)
        rigid.CreateRigidBodyEnabledAttr(True); rigid.CreateKinematicEnabledAttr(False)
        UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(LINK_MASS)
        prim.AddAppliedSchema('PhysxRigidBodyAPI')
        for key,value in [('solverPositionIterationCount',128),('solverVelocityIterationCount',8)]:
            prim.CreateAttribute('physxRigidBody:'+key,Sdf.ValueTypeNames.Int).Set(value)
        prim.CreateAttribute('physxRigidBody:sleepThreshold',Sdf.ValueTypeNames.Float).Set(0.)
        prim.CreateAttribute('physxRigidBody:enableCCD',Sdf.ValueTypeNames.Bool).Set(True)
        # Four separate walls leave a real20 x10.5 mm wire passage.
        side=(WIDTH-INNER_WIDTH)/2; cross=(HEIGHT-INNER_HEIGHT)/2
        pieces=[]
        for sign in (-1,1):
            pieces += [(f'Side{sign+1}',(0,0,sign*(INNER_WIDTH+side)/2),(.016,HEIGHT,side)),
                       (f'Crossbar{sign+1}',(0,sign*(INNER_HEIGHT+cross)/2,0),(.008,cross,INNER_WIDTH))]
        for label,center,size in pieces:
            cube=UsdGeom.Cube.Define(stage,body+'/'+label); cube.CreateSizeAttr(1)
            cube.AddTranslateOp().Set(Gf.Vec3d(*center)); cube.AddScaleOp().Set(Gf.Vec3f(*size))
            collision(cube.GetPrim()); UsdShade.MaterialBindingAPI.Apply(cube.GetPrim()).Bind(mat)
        if index:
            j=UsdPhysics.RevoluteJoint.Define(stage,path+f'/Hinge{index:03d}')
            j.CreateBody0Rel().SetTargets([paths[index-1]]); j.CreateBody1Rel().SetTargets([body])
            j.CreateLocalPos0Attr(Gf.Vec3f(PITCH/2,0,0)); j.CreateLocalPos1Attr(Gf.Vec3f(-PITCH/2,0,0))
            j.CreateAxisAttr('Z'); j.CreateLowerLimitAttr(0.); j.CreateUpperLimitAttr(LIMIT_DEG)
            j.CreateCollisionEnabledAttr(False)
            j.CreateExcludeFromArticulationAttr(True)
    fixed_attachment(stage,path+'/FixedEnd',body0,paths[0],points[0])
    fixed_attachment(stage,path+'/MovingEnd',paths[-1],body1,points[-1])
    return {'name':name,'path':path,'body_paths':paths,'attachments':[body0,body1],
            'initial_endpoints_m':[list(points[0]),list(points[-1])],
            'links':len(paths),'pitch_m':PITCH,'length_m':len(paths)*PITCH,
            'joint_limits_deg':[0,LIMIT_DEG],'polygon_bend_radius_m':SEPARATION/2,
            'outer_width_m':WIDTH,'outer_height_m':HEIGHT,
            'inner_width_m':INNER_WIDTH,'inner_height_m':INNER_HEIGHT,
            'mass_kg':len(paths)*LINK_MASS,'catalog_chain_mass_kg_m':.17,'assumed_fill_mass_kg_m':.04}


def complete_service_carriers(stage,architecture):
    if architecture not in ('A','B','C'): raise ValueError('Unknown architecture')
    robot=stage.GetPrimAtPath(ROOT)
    if robot.GetCustomDataByKey('service_carrier_revision'): raise ValueError('Already has service carriers')
    # This revision is added only to the developed drive-connected assemblies.
    if not robot.GetCustomDataByKey('hardware_revision'): raise ValueError('Drive connections required first')
    cache=UsdGeom.XformCache(); h=Hardware(stage); reports=[]
    def world(body,point):
        return cache.GetLocalToWorldTransform(stage.GetPrimAtPath(body)).Transform(Gf.Vec3d(*point))
    def support(body,label,start,end):
        # Custom dimensioned8x8 mm aluminum struts, collision-enabled, with
        # additive volume-derived mass. Ordered Z/X/Y routing clears the tool.
        previous=list(start)
        for axis in (2,0,1):
            current=list(previous); current[axis]=end[axis]
            length=abs(current[axis]-previous[axis])
            if length>1e-6:
                size=[.008,.008,.008]; size[axis]=length+.008
                h.box(body+'/CarrierMounts/'+label+str(axis),[(a+b)/2 for a,b in zip(previous,current)],size)
            previous=current
    def add(name,owner0,owner1,start_local,travel,normal,n0,n1,attach0,attach1):
        start=world(owner0,start_local)
        points,_=u_link_points(start,travel,normal,n0,n1)
        end_local=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(owner1)).GetInverse().Transform(points[-1])
        support(owner0,name+'Fixed',attach0,start_local)
        support(owner1,name+'Moving',attach1,end_local)
        reports.append(build_chain(stage,name,start,travel,normal,n0,n1,owner0,owner1))
    frame=ROOT+'/Frame'; bridge=ROOT+'/Bridge'; carriage=ROOT+'/Carriage'; mount=ROOT+'/ToolMount'
    # Vertical carrier lies outside the left upright, with its fold above the
    # moving endpoint. Fixed and moving ends are actually attached rigid bodies.
    moving=ROOT+'/LiftCarriage' if architecture=='B' else bridge
    x=-.33 if architecture=='B' else -.31
    y=.91 if architecture=='B' else .86
    add('Lift',frame,moving,(x,y,1.44),(0,0,1),(0,1,0),25,7,
        (-.26,.815 if architecture=='B' else .735,1.44),(-.06,0,.08) if architecture=='B' else (-.26,0,.025))
    if architecture in ('A','C'):
        add('Traverse',bridge,carriage,(-.01,.14,.06),(1,0,0),(0,0,1),15,7,
            (-.01,0,.025),(0,0,.025))
    else:
        # One carrier for EACH independently moving telescopic stage.
        for name,a,b,y in [('Outer',ROOT+'/LiftCarriage',ROOT+'/MiddleBoom',.91),
                           ('Inner',ROOT+'/MiddleBoom',carriage,.86)]:
            fixed=world(b,(0,0,0)); fixed[0]-=.08; fixed[1]=y; fixed[2]+=.12
            local=cache.GetLocalToWorldTransform(stage.GetPrimAtPath(a)).GetInverse().Transform(fixed)
            add(name,a,b,local,(1,0,0),(0,0,1),10,6,(-.075,0,.075),(0,0,.075))
    # This fold faces the rack, above the short insertion slide; placing it
    # behind the slide would intersect uprights at edge ports.
    add('Insertion',carriage,mount,(0,-.02,.06),(0,-1,0),(0,0,1),4,5,
        (0,-.02,.025),(0,0,.025))
    for body,mass in h.added_mass.items():
        attr=UsdPhysics.MassAPI(stage.GetPrimAtPath(body)).GetMassAttr(); attr.Set(attr.Get()+mass)
    revision='passive_service_carriers_v2'
    robot.SetCustomDataByKey('service_carrier_revision',revision)
    return {'revision':revision,'architecture':architecture,'chains':reports,
            'brackets':h.parts,'bracket_added_mass_kg_by_body':h.added_mass,
            'scope':'Passive rigid-link service carriers; attached ends, joint bending stops, self/environment collisions and estimated fill mass',
            'limitations':['Original simplified geometry, not vendor CAD or qualified carrier installation.',
                'Wire fill is lumped mass; independent wire bending, friction, pull forces and electrical routing are not modeled.',
                'Ideal revolute stops have no measured pin friction, camber, wear or strength.',
                'Neighboring connected-link and end-attachment collision pairs only are excluded.',
                'Full-stroke clearance, powered-off support and repeated task validation remain separate gates.']}


def carrier_metrics(stage):
    root=stage.GetPrimAtPath(ROOT+'/ServiceCarriers')
    if not root: return None
    cache=UsdGeom.XformCache(); gaps=[]; hinges=[]; errors=[]
    for prim in Usd.PrimRange(root):
        if not prim.IsA(UsdPhysics.Joint): continue
        joint=UsdPhysics.Joint(prim)
        bodies=[joint.GetBody0Rel().GetTargets()[0],joint.GetBody1Rel().GetTargets()[0]]
        mats=[cache.GetLocalToWorldTransform(stage.GetPrimAtPath(p)) for p in bodies]
        anchors=[m.Transform(Gf.Vec3d(getattr(joint,f'GetLocalPos{i}Attr')().Get())) for i,m in enumerate(mats)]
        gaps.append((anchors[0]-anchors[1]).GetLength())
        if prim.IsA(UsdPhysics.RevoluteJoint):
            # Both link frames share local Z as the physical hinge axis.
            x0=mats[0].TransformDir(Gf.Vec3d(1,0,0)); x1=mats[1].TransformDir(Gf.Vec3d(1,0,0))
            axis=mats[0].TransformDir(Gf.Vec3d(0,0,1))
            angle=math.degrees(math.atan2(Gf.Dot(axis,Gf.Cross(x0,x1)),Gf.Dot(x0,x1)))
            hinges.append(angle)
    values=gaps+hinges
    if not values or not all(math.isfinite(v) for v in values): errors.append('Missing/non-finite carrier state')
    return {'maximum_anchor_gap_m':max(gaps,default=0.),'minimum_hinge_deg':min(hinges,default=0.),
            'maximum_hinge_deg':max(hinges,default=0.),'hinges':len(hinges),'errors':errors}
