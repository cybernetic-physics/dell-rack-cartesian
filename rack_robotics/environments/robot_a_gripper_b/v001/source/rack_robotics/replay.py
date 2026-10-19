"""Bake measured poses into a separate non-physical USD visualization layer.

The original scene and physics trajectory are read-only inputs. This derived
layer cannot establish task success and must never be used as a physics trial.
"""
import os
from pxr import Gf, Usd, UsdGeom, UsdPhysics, UsdLux


def bake_replay(source_scene,output,header,samples,view,views,focus):
    stage=Usd.Stage.CreateNew(str(output))
    stage.GetRootLayer().subLayerPaths=[os.path.relpath(source_scene,output.parent)]
    UsdGeom.SetStageUpAxis(stage,'Z'); UsdGeom.SetStageMetersPerUnit(stage,1)
    stage.SetTimeCodesPerSecond(30); stage.SetFramesPerSecond(30)
    stage.SetStartTimeCode(0); stage.SetEndTimeCode(len(samples)-1)
    camera=UsdGeom.Camera.Define(stage,'/World/ReplayCamera')
    camera.CreateClippingRangeAttr(Gf.Vec2f(.001,1000))
    camera.CreateHorizontalApertureAttr(36); camera.CreateVerticalApertureAttr(20.25)
    camera.CreateFocalLengthAttr(50 if view=='macro' else 30 if view=='wide' else 35)
    camera_op=camera.AddTransformOp()
    # A soft inspection light makes the actual latch contact readable under the
    # housing. This changes lighting only, not geometry or the recorded motion.
    if view=='macro':
        light=UsdLux.RectLight.Define(stage,'/World/ReplayInspectionLight')
        light.CreateWidthAttr(.08); light.CreateHeightAttr(.08)
        light.CreateIntensityAttr(4500)
        eye=Gf.Vec3d(focus[0]-.08,focus[1]+.05,focus[2]+.08)
        light.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(eye,Gf.Vec3d(*focus),Gf.Vec3d(0,0,1)).GetInverse())
    for prim in list(stage.Traverse()):
        if prim.IsA(UsdPhysics.Joint) or prim.IsA(UsdPhysics.Scene): prim.SetActive(False)
        elif prim.HasAPI(UsdPhysics.RigidBodyAPI):
            prim.RemoveAPI(UsdPhysics.RigidBodyAPI)
            # This is a render-only layer, built BEFORE Kit opens it. Removing
            # physics ownership prevents stale cached simulation transforms.
            from pxr import PhysxSchema
            prim.RemoveAPI(PhysxSchema.PhysxRigidBodyAPI)
    stage.GetPrimAtPath('/World/ClipPress').SetActive(False)
    operations={}; parents={}
    for path in header['body_paths']:
        prim=stage.GetPrimAtPath(path); xf=UsdGeom.Xformable(prim)
        t=prim.GetAttribute('xformOp:translate'); q=prim.GetAttribute('xformOp:orient')
        t=UsdGeom.XformOp(t) if t else xf.AddTranslateOp()
        q=UsdGeom.XformOp(q) if q else xf.AddOrientOp()
        xf.SetXformOpOrder([t,q]); operations[path]=(t,q)
        parents[path]=UsdGeom.Xformable(prim.GetParent()).ComputeLocalToWorldTransform(0)
    curve=UsdGeom.BasisCurves(stage.GetPrimAtPath('/World/Cable/Jacket'))
    links=sorted(p for p in header['body_paths'] if p.startswith('/World/Cable/Link'))
    for index,sample in enumerate(samples):
        eye,target=views[view]
        if view=='macro':
            plug=sample['poses'][header['body_paths'].index('/World/Plug')][:3]
            target=[(a+b)/2 for a,b in zip(focus,plug)]; target[2]+=.003
            eye=[a+b for a,b in zip(target,(-.075,.09,.045))]
        camera_matrix=Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye),Gf.Vec3d(*target),Gf.Vec3d(0,0,1)).GetInverse()
        camera_op.Set(camera_matrix,index)
        if index==0: camera_op.Set(camera_matrix)
        matrices={}
        for path,values in zip(header['body_paths'],sample['poses']):
            world=Gf.Matrix4d(1)
            world.SetRotate(Gf.Rotation(Gf.Quatd(values[3],Gf.Vec3d(*values[4:]))))
            world.SetTranslateOnly(Gf.Vec3d(*values[:3])); matrices[path]=world
            local=world*parents[path].GetInverse(); translate,orient=operations[path]
            q=local.ExtractRotationQuat()
            q=Gf.Quatf(q) if orient.GetPrecision()==UsdGeom.XformOp.PrecisionFloat else q
            translate.Set(local.ExtractTranslation(),index); orient.Set(q,index)
            if index==0:
                translate.Set(local.ExtractTranslation()); orient.Set(q)
        points=[matrices['/World/Plug'].Transform(Gf.Vec3d(0,.019,0))]
        points += [matrices[path].Transform(Gf.Vec3d(0,.0075,0)) for path in links]
        curve.GetPointsAttr().Set([Gf.Vec3f(p) for p in points],index)
        if index==0: curve.GetPointsAttr().Set([Gf.Vec3f(p) for p in points])
        if stage.GetPrimAtPath('/World/Robot/Belt0'):
            from rack_robotics.belt_gantry import update_belt_visuals
            p=matrices['/World/Robot/Carriage'].ExtractTranslation()
            update_belt_visuals(stage,p[0],p[2],index)
            if index==0: update_belt_visuals(stage,p[0],p[2])
    stage.GetRootLayer().customLayerData={'replay_only':True,'source':'Measured physics trajectory; no hand-authored motion'}
    stage.GetRootLayer().Save()
