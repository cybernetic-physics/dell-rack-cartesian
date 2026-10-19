"""Stationary-motor CoreXZ prototype with passive X/Z guide joints.

Original dimensioned geometry, not a Festo digital twin. The belt is a lumped
elastic transmission (corexz.py), not a collision-enabled toothed belt model.
Polyline centerlines are diagnostic routing, not production pulley-wrap CAD.
"""
from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema, UsdShade
from rack_sim.geometry import xform, box, cylinder
from rack_robotics.mechanics import ROOT, body, joint, robot_materials, build_tool, pose


def belt_paths(x,z):
    left,right,bottom,top=-.245,.245,1.035,1.865
    return [
        [(x-.015,.765,z),(left,.765,z),(left,.765,bottom),
         (right,.765,bottom),(right,.765,top),(right,.765,z),(x+.015,.765,z)],
        [(x-.015,.785,z),(left,.785,z),(left,.785,top),
         (right,.785,top),(right,.785,bottom),(right,.785,z),(x+.015,.785,z)],
    ]


def update_belt_visuals(stage,x,z,time=None):
    for index,points in enumerate(belt_paths(x,z)):
        attr=UsdGeom.BasisCurves(stage.GetPrimAtPath(ROOT+f'/Belt{index}')).GetPointsAttr()
        values=[Gf.Vec3f(*p) for p in points]
        if time is None: attr.Set(values)
        else: attr.Set(values,time)


def build_belt_robot(stage,gripper='A',gripper_asset=None):
    xform(stage,ROOT)
    mats=robot_materials(stage)
    steel,dark,blue,orange=(mats[k] for k in ('steel','anodized','blue','orange'))
    base=ROOT+'/Frame'; bridge=ROOT+'/Bridge'; carriage=ROOT+'/Carriage'; mount=ROOT+'/ToolMount'
    body(stage,base,(0,0,0),4.2)
    root=UsdPhysics.FixedJoint.Define(stage,ROOT+'/Joints/RackMount')
    root.CreateBody1Rel().SetTargets([base])
    UsdPhysics.ArticulationRootAPI.Apply(root.GetPrim())
    api=PhysxSchema.PhysxArticulationAPI.Apply(root.GetPrim())
    api.CreateSolverPositionIterationCountAttr(128); api.CreateSolverVelocityIterationCountAttr(8)
    api.CreateEnabledSelfCollisionsAttr(True)
    for side,x in enumerate((-.26,.26)):
        box(stage,base+f'/Upright{side}',(x,.735,1.45),(.04,.04,.98),dark,True)
        box(stage,base+f'/Guide{side}',(x,.710,1.45),(.012,.008,.92),steel,True)
        for k,z in enumerate((1.01,1.90)):
            box(stage,base+f'/Standoff{side}_{k}',(x,.655,z),(.05,.16,.008),steel,True)
            box(stage,base+f'/PostClamp{side}_{k}',((-.285,.285)[side],.593,z),(.04,.006,.05),steel,True)
            for b,dz in enumerate((-.016,.016)):
                cylinder(stage,base+f'/RackBolt{side}_{k}_{b}',((-.285,.285)[side],.598,z+dz),.003,.006,steel)
        for k,z in enumerate((1.075,1.831)):
            box(stage,base+f'/Stop{side}_{k}',(x,.698,z),(.023,.016,.008),orange,True)
    for k,z in enumerate((.98,1.94)):
        box(stage,base+f'/CrossMember{k}',(0,.735,z),(.56,.04,.04),dark,True)
    for index,z in enumerate((1.035,1.865)):
        box(stage,base+f'/StationaryMotor{index}',(-.245,.818,z),(.042,.040,.042),blue,True)
        box(stage,base+f'/MotorPlate{index}',(-.245,.793,z),(.06,.006,.065),steel,True)
        cylinder(stage,base+f'/MotorShaft{index}',(-.245,.783,z),.0025,.045,steel,'Y')
    for layer,y in enumerate((.765,.785)):
        for side,x in enumerate((-.245,.245)):
            for k,z in enumerate((1.035,1.865)):
                cylinder(stage,base+f'/Pulley{layer}_{side}_{k}',(x,y,z),.006366,.009,steel,'Y')
    body(stage,bridge,(0,.72,1.80),.9)
    box(stage,bridge+'/Beam',(0,0,0),(.54,.032,.04),dark,True)
    box(stage,bridge+'/XGuide',(0,-.021,0),(.48,.008,.012),steel,True)
    for side,x in enumerate((-.26,.26)):
        box(stage,bridge+f'/GuideBlock{side}',(x,-.011,0),(.027,.013,.0454),steel,True)
        box(stage,bridge+f'/IdlerTab{side}',((-.22,.22)[side],.030,-.012),(.012,.060,.006),steel,True)
        box(stage,bridge+f'/IdlerBracket{side}',((-.2325,.2325)[side],.050,-.012),(.040,.030,.006),steel,True)
        for layer,y in enumerate((.045,.065)):
            cylinder(stage,bridge+f'/MovingPulley{side}_{layer}',((-.245,.245)[side],y,0),.006366,.009,steel,'Y')
    body(stage,carriage,(.15,.68,1.8),.38)
    box(stage,carriage+'/Plate',(0,0,0),(.055,.012,.06),blue,True)
    box(stage,carriage+'/BeltClampSpacer',(0,.020,.026),(.020,.040,.005),steel,True)
    box(stage,carriage+'/BeltClampPlate',(0,.075,.026),(.05,.09,.005),steel,True)
    for i,x in enumerate((-.015,.015)):
        box(stage,carriage+f'/BeltClamp{i}',(x,.095,.012),(.008,.028,.024),steel,True)
    for k,x in enumerate((-.022,.022)):
        box(stage,carriage+f'/DepthRail{k}',(x,-.055,0),(.012,.16,.008),steel,True)
    cylinder(stage,carriage+'/DepthScrew',(0,-.055,.014),.003,.16,steel,'Y')
    box(stage,carriage+'/DepthMotor',(0,.037,.014),(.028,.035,.028),blue,True)
    drives={
        'z':joint(stage,'Lift',base,bridge,(0,.72,1.8),'Z',(-.70,0),0,0,0,0),
        'x':joint(stage,'Traverse',bridge,carriage,(0,-.04,0),'X',(-.21,.21),.15,0,0,0),
        'y':joint(stage,'Insertion',carriage,mount,(0,0,0),'Y',(-.125,0),0,8,15000,35),
    }
    for i in range(2):
        curve=UsdGeom.BasisCurves.Define(stage,ROOT+f'/Belt{i}')
        curve.CreateTypeAttr('linear'); curve.CreateCurveVertexCountsAttr([7])
        curve.CreateWidthsAttr([.003]); curve.SetWidthsInterpolation('constant')
        UsdShade.MaterialBindingAPI.Apply(curve.GetPrim()).Bind(dark)
    update_belt_visuals(stage,.15,1.8)
    return build_tool(stage,drives,mats,gripper,gripper_asset=gripper_asset)


class CoreXZTransmission:
    """Apply motor-coupled generalized efforts, never body pose assignments."""
    def __init__(self,stage,drives):
        import numpy as np
        from isaacsim.core.prims import SingleArticulation
        from rack_robotics.corexz import BeltParameters
        self.np=np; self.stage=stage; self.drives=drives; self.parameters=BeltParameters()
        self.articulation=SingleArticulation(prim_path=ROOT,name='corexz_transmission')
        self.articulation.initialize()
        self.indices=np.array([self.articulation.get_dof_index(n) for n in ('Traverse','Lift')])
        self.enabled=(True,True); self.latest={}
        self.lift_mass=sum(UsdPhysics.MassAPI(prim).GetMassAttr().Get() or 0.
            for prim in stage.Traverse() if str(prim.GetPath()).startswith(ROOT+'/')
            and str(prim.GetPath())!=ROOT+'/Frame' and prim.HasAPI(UsdPhysics.MassAPI))
        for name in ('x','z'):
            drive=drives[name]
            if drive.GetStiffnessAttr().Get()!=0 or drive.GetDampingAttr().Get()!=0:
                raise ValueError('CoreXZ cannot coexist with independent X/Z drive gains')

    def step(self,x_force_limit_n=None):
        from rack_robotics.corexz import transmission_efforts
        position=self.articulation.get_joint_positions(joint_indices=self.indices)
        velocity=self.articulation.get_joint_velocities(joint_indices=self.indices)
        target=tuple(self.drives[n].GetTargetPositionAttr().Get() for n in ('x','z'))
        self.latest=transmission_efforts(target,position,velocity,self.lift_mass*9.81,
                                         self.parameters,self.enabled,x_force_limit_n)
        self.articulation.set_joint_efforts(self.np.array(self.latest['joint_force_n']),joint_indices=self.indices)

    def update_visuals(self):
        p=pose(self.stage,ROOT+'/Carriage')
        update_belt_visuals(self.stage,p[0],p[2])
