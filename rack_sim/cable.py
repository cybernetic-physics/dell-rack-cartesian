"""PhysX capsule/D6 rope following NVIDIA's rigid-body rope example technique."""
import math
from pxr import UsdGeom, UsdPhysics, Gf
from .geometry import xform, collision, rigid, bind, curve
from .config import CFG

def create_cable(stage,plug_pos,mat):
    xform(stage,'/World/Cable')
    length=CFG.cable_segment_length
    paths=[]
    endpoint=Gf.Vec3d(plug_pos[0],plug_pos[1]+.019,plug_pos[2])
    for i in range(CFG.cable_segments):
        path=f'/World/Cable/Link{i:02d}'
        p=UsdGeom.Capsule.Define(stage,path)
        p.CreateAxisAttr('Y'); p.CreateRadiusAttr(CFG.cable_radius)
        p.CreateHeightAttr(length-2*CFG.cable_radius)
        # Route beyond the recessed I/O/fan cage, then hang with slack. Starting
        # 54 cm of cable horizontally suspended creates an avoidable whipping
        # transient, unrelated to insertion. Every joint starts coincident.
        angle=min(90,max(0,(i-5)*15))
        rotation=Gf.Rotation(Gf.Vec3d(1,0,0),-angle)
        direction=rotation.TransformDir(Gf.Vec3d(0,1,0))
        p.AddTranslateOp().Set(endpoint+direction*(length/2))
        p.AddOrientOp().Set(Gf.Quatf(rotation.GetQuat()))
        endpoint+=direction*length
        bind(p.GetPrim(),mat); collision(p.GetPrim(),.0001); rigid(p.GetPrim(),.0007)
        # Hide segmented shapes from rendering; the jacket follows simulated endpoints.
        p.CreatePurposeAttr('guide')
        paths.append(path)
        j=UsdPhysics.Joint.Define(stage,f'/World/Cable/Joint{i:02d}')
        j.CreateBody0Rel().SetTargets([paths[i-1] if i else '/World/Plug'])
        j.CreateBody1Rel().SetTargets([path])
        j.CreateLocalPos0Attr(Gf.Vec3f(0,length/2 if i else .019,0))
        j.CreateLocalPos1Attr(Gf.Vec3f(0,-length/2,0))
        j.CreateCollisionEnabledAttr(False)
        for axis in ('transX','transY','transZ'):
            lim=UsdPhysics.LimitAPI.Apply(j.GetPrim(),axis)
            lim.CreateLowAttr(1); lim.CreateHighAttr(-1)
        for axis in ('rotX','rotY','rotZ'):
            lim=UsdPhysics.LimitAPI.Apply(j.GetPrim(),axis)
            lim.CreateLowAttr(-40); lim.CreateHighAttr(40)
            d=UsdPhysics.DriveAPI.Apply(j.GetPrim(),axis)
            d.CreateTypeAttr('force'); d.CreateStiffnessAttr(.0002); d.CreateDampingAttr(.00008)
    c=curve(stage,'/World/Cable/Jacket',[(0,0,0)]*(len(paths)+1),CFG.cable_radius,mat)
    return Cable(stage,paths,c)

class Cable:
    def __init__(self,stage,paths,curve):
        self.stage=stage; self.paths=paths; self.curve=curve; self.max_gap=0; self.updates=0; self.worst={}

    def update(self):
        mats=[UsdGeom.Xformable(self.stage.GetPrimAtPath(p)).ComputeLocalToWorldTransform(0) for p in self.paths]
        half=CFG.cable_segment_length/2
        first=UsdGeom.Xformable(self.stage.GetPrimAtPath('/World/Plug')).ComputeLocalToWorldTransform(0).Transform(Gf.Vec3d(0,.019,0))
        points=[first]
        gap=0.
        previous=first
        worst_index=0
        for i,m in enumerate(mats):
            start=m.Transform(Gf.Vec3d(0,-half,0)); end=m.Transform(Gf.Vec3d(0,half,0))
            error=(start-previous).GetLength()
            if error>gap: gap=error; worst_index=i
            previous=end; points.append(end)
        self.curve.GetPointsAttr().Set([Gf.Vec3f(*p) for p in points])
        if gap>self.max_gap:
            self.max_gap=gap; self.worst={'update':self.updates,'joint':worst_index,'gap_m':gap}
        self.updates+=1
        return gap
