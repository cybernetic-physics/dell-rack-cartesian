"""Runtime topology checks before a real robot trial (not used for replay)."""
from pxr import UsdPhysics


def audit_trial(stage,ports,cable_segments):
    inactive=['/World/HandDrive','/World/ClipPressSlide','/World/ClipPress']
    errors=[]
    for path in inactive:
        if stage.GetPrimAtPath(path).IsActive(): errors.append(f'Demo actuator remains active: {path}')
    dynamic=['/World/Plug','/World/Latch']+[f'/World/Cable/Link{i:02d}' for i in range(cable_segments)]
    for path in dynamic:
        prim=stage.GetPrimAtPath(path)
        if not prim or not prim.IsActive() or not prim.HasAPI(UsdPhysics.RigidBodyAPI):
            errors.append(f'Missing dynamic body: {path}')
            continue
        api=UsdPhysics.RigidBodyAPI(prim)
        if not api.GetRigidBodyEnabledAttr().Get() or api.GetKinematicEnabledAttr().Get():
            errors.append(f'Connector/cable body is not freely dynamic: {path}')
    roots=['/World/Plug/','/World/Latch/']+[path+'/' for path,_ in ports]
    collider_count=0; plug_joints=[]
    for prim in stage.Traverse():
        path=str(prim.GetPath())
        if any(path.startswith(root) for root in roots) and prim.HasAPI(UsdPhysics.CollisionAPI):
            collider_count+=1
            if not UsdPhysics.CollisionAPI(prim).GetCollisionEnabledAttr().Get():
                errors.append(f'Disabled connector/socket collider: {path}')
        if prim.IsA(UsdPhysics.Joint):
            j=UsdPhysics.Joint(prim)
            targets=[str(p) for p in [*j.GetBody0Rel().GetTargets(),*j.GetBody1Rel().GetTargets()]]
            if '/World/Plug' in targets:
                plug_joints.append({'path':path,'bodies':targets,'type':prim.GetTypeName()})
                if set(targets) not in ({'/World/Plug','/World/Latch'},
                                        {'/World/Plug','/World/Cable/Link00'}):
                    errors.append(f'Unauthorized connector attachment: {path} -> {targets}')
    for socket,_ in ports:
        lip=stage.GetPrimAtPath(socket+'/LatchLip')
        if not lip or not lip.IsActive() or not lip.HasAPI(UsdPhysics.CollisionAPI):
            errors.append(f'Missing physical retention lip: {socket}')
    hinge=stage.GetPrimAtPath('/World/LatchHinge')
    if not hinge or not hinge.IsA(UsdPhysics.RevoluteJoint):
        errors.append('Missing passive latch hinge')
    else:
        target=UsdPhysics.DriveAPI(hinge,'angular').GetTargetPositionAttr().Get()
        if target!=8.0: errors.append(f'Latch rest spring was commanded: {target}')
    return {'passed':not errors,'errors':errors,'inactive_demo_actuators':inactive,
            'dynamic_connector_and_cable_bodies':len(dynamic),
            'active_connector_socket_colliders':collider_count,'plug_joints':plug_joints}
