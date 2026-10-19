"""Original dimensioned BCD42-envelope brake packages, authored before physics.

42 mm chamfered square within a54 mm circle,45.5 mm body,24 mm output shaft.
Outer-hull collisions and .28 kg complete-package mass. Not vendor CAD, a
qualified motor/brake assembly, or physical friction-disc/shaft dynamics.
"""
import math
from pxr import Gf,Sdf,Usd,UsdGeom,UsdPhysics
from rack_robotics.hardware_detail import Hardware

ROOT='/World/Robot'
LENGTH=.0455
MASS=.28


def add_brake_hardware(stage,architecture):
    if architecture not in ('A','B','C'): raise ValueError('Unknown architecture')
    robot=stage.GetPrimAtPath(ROOT); frame=ROOT+'/Frame'
    if not robot or not robot.GetCustomDataByKey('hardware_revision'):
        raise ValueError('Drive-connected robot required')
    if robot.GetCustomDataByKey('brake_revision'): raise ValueError('Brakes already modeled')
    h=Hardware(stage); cases=[]; reworked=[]

    def collision(prim,mesh=False):
        UsdPhysics.CollisionAPI.Apply(prim)
        if mesh: UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr('convexHull')
        prim.AddAppliedSchema('PhysxCollisionAPI')
        prim.CreateAttribute('physxCollision:contactOffset',Sdf.ValueTypeNames.Float).Set(.00005)
        prim.CreateAttribute('physxCollision:restOffset',Sdf.ValueTypeNames.Float).Set(0.)

    def plate(old,label,center,size,axis):
        prim=stage.GetPrimAtPath(old)
        if not prim: raise ValueError('Missing existing motor plate: '+old)
        cubes=[p for p in Usd.PrimRange(prim) if p.IsA(UsdGeom.Cube)]
        volume=sum(math.prod(p.GetAttribute('xformOp:scale').Get())*
                   UsdGeom.Cube(p).GetSizeAttr().Get()**3 for p in cubes)
        prim.SetActive(False) # Stronger new scene layer only; original stays immutable.
        h.added_mass[frame]=h.added_mass.get(frame,0.)-volume*2700
        reworked.append({'old_plate':old,'assumed_removed_aluminum_mass_kg':volume*2700})
        h.plate(frame+'/Brakes/'+label+'/MountPlate',center,size,axis,.023)

    def package(label,motor,face,axis):
        path=frame+'/Brakes/'+label; axial='XYZ'.index(axis)
        cross=[i for i in range(3) if i!=axial]
        # Clip the square corners at the drawing's54 mm circumscribed circle.
        a=.021; b=math.sqrt(.027**2-a*a)
        ring=[(a,b),(b,a),(-b,a),(-a,b),(-a,-b),(-b,-a),(b,-a),(a,-b)]
        points=[]
        for depth in (0,LENGTH):
            for u,v in ring:
                p=list(face); p[axial]+=depth; p[cross[0]]+=u; p[cross[1]]+=v
                points.append(Gf.Vec3f(*p))
        faces=[tuple(reversed(range(8))),tuple(range(8,16))]
        faces += [(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
        # X/Z transverse ordering has opposite handedness when extruded along Y.
        if axis=='Y': faces=[tuple(reversed(f)) for f in faces]
        mesh=UsdGeom.Mesh.Define(stage,path+'/Housing')
        mesh.CreatePointsAttr(points); mesh.CreateFaceVertexCountsAttr([len(f) for f in faces])
        mesh.CreateFaceVertexIndicesAttr([v for f in faces for v in f]); mesh.CreateSubdivisionSchemeAttr('none')
        h.bind(mesh.GetPrim()); collision(mesh.GetPrim(),True)
        h.record(str(mesh.GetPath()),0.,0.,True,reference_mass=MASS)
        h.parts[-1]['mass_basis']='Nanotec BCD42 complete brake package drawing mass'
        center=list(face);center[axial]-=.012
        shaft=UsdGeom.Cylinder.Define(stage,path+'/OutputShaft')
        shaft.CreateAxisAttr(axis);shaft.CreateHeightAttr(.024);shaft.CreateRadiusAttr(.0025)
        shaft.AddTranslateOp().Set(Gf.Vec3d(*center));h.bind(shaft.GetPrim())
        # Connector is part of the .28 kg package, not additional lumped mass.
        connector_axis='Y' if axis=='Z' and architecture=='A' else 'X'
        ci='XYZ'.index(connector_axis)
        center=list(face);center[axial]+=LENGTH/2;center[ci]+=.027
        connector=UsdGeom.Cylinder.Define(stage,path+'/M8ConnectorEnvelope')
        connector.CreateAxisAttr(connector_axis);connector.CreateHeightAttr(.012);connector.CreateRadiusAttr(.006)
        connector.AddTranslateOp().Set(Gf.Vec3d(*center));h.bind(connector.GetPrim());collision(connector.GetPrim())
        # Move the modeled motor, not the robot or connector, before physics.
        prim=stage.GetPrimAtPath(motor)
        old=Gf.Vec3d(prim.GetAttribute('xformOp:translate').Get())
        half=prim.GetAttribute('xformOp:scale').Get()[axial]/2
        moved=Gf.Vec3d(old);moved[axial]=face[axial]+LENGTH+half
        prim.GetAttribute('xformOp:translate').Set(moved)
        for i,u in enumerate((-.0155,.0155)):
            for j,v in enumerate((-.0155,.0155)):
                p=list(face);p[axial]-=.004;p[cross[0]]+=u;p[cross[1]]+=v
                h.bolt(path+f'/MountBolt{i}_{j}',p,axis,.0015,.014)
        cases.append({'path':path,'motor':motor,'motor_original_center_m':list(old),
                      'motor_new_center_m':list(moved),'axis':axis,'mount_face_m':list(face),
                      'body_length_m':LENGTH,'shaft_projection_m':.024,'package_mass_kg':MASS})

    if architecture=='A':
        for i,x in enumerate((-.242,.278)):
            plate(frame+f'/LiftMotorPlate{i}',f'Lift{i}',(x,.704,1.889),(.065,.065,.006),'Z')
            package(f'Lift{i}',frame+f'/Motor{i}',(x,.704,1.892),'Z')
            h.sleeve(frame+f'/Brakes/Lift{i}/CouplerReducer',(x,.704,1.879),.0041,.00255,.010,'Z')
    elif architecture=='B':
        plate(frame+'/MotorPlate','Lift',(-.26,.775,1.955),(.065,.075,.006),'Z')
        package('Lift',frame+'/LiftMotor',(-.26,.775,1.958),'Z')
    else:
        for i,z in enumerate((1.035,1.865)):
            plate(frame+f'/MotorPlate{i}',f'Motor{i}',(-.245,.795,z),(.060,.006,.065),'Y')
            package(f'Motor{i}',frame+f'/StationaryMotor{i}',(-.245,.798,z),'Y')
    for owner,mass in h.added_mass.items():
        attr=UsdPhysics.MassAPI(stage.GetPrimAtPath(owner)).GetMassAttr();attr.Set(attr.Get()+mass)
    revision='passive_motor_brakes_v1'
    robot.SetCustomDataByKey('brake_revision',revision)
    return {'revision':revision,'architecture':architecture,'brakes':cases,'parts':h.parts,
            'reworked_plates':reworked,'added_mass_kg_by_body':h.added_mass,
            'reference':'https://www.nanotec.com/fileadmin/files/Datenblaetter/Bremsen/BCD/BRAKE-BCD42-0_4-5.pdf',
            'limitations':['Original dimensioned outer envelopes, not vendor CAD or an approved motor/brake assembly.',
                           'Vendor offers brakes with motors; selected complete motor assembly still requires verification.',
                           'Brake outer hull is solid collision proxy; bearing/disc/shaft/friction contact is not simulated.',
                           'M3 drawing interface used; mounting strength, cable routing and dynamic stopping are unqualified.',
                           'Replacement-plate mass delta assumes aluminum; baseline lumped masses remain estimates.']}
