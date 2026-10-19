"""Author trial-specific initial USD opinions BEFORE World.reset(), never mid-task."""


def apply_conditions(stage,condition,ports):
    from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf
    from benchmarking.spec import cable_route
    target=ports[condition['port']-1][1]
    origin=ports[0][1]
    delta=Gf.Vec3d(*(a-b for a,b in zip(target,origin)))
    moved=[]
    # The loose connector starts 50 mm in front of its target port. Its latch
    # and temporary pre-seat pad follow the same initial translation.
    for path in ('/World/Plug','/World/Latch','/World/ClipPress'):
        prim=stage.GetPrimAtPath(path)
        attr=prim.GetAttribute('xformOp:translate')
        if not attr: raise ValueError(f'Missing initial translation: {path}')
        attr.Set(attr.Get()+delta); moved.append(path)
    plug=UsdGeom.Xformable(stage.GetPrimAtPath('/World/Plug')).ComputeLocalToWorldTransform(0)
    endpoint=plug.Transform(Gf.Vec3d(0,.019,0))
    route=cable_route(endpoint,condition['cable_yaw_deg'],condition['cable_bend_start'])
    for index,row in enumerate(route):
        path=f'/World/Cable/Link{index:02d}'; prim=stage.GetPrimAtPath(path)
        prim.GetAttribute('xformOp:translate').Set(Gf.Vec3d(*row['position']))
        w,x,y,z=row['quaternion']
        prim.GetAttribute('xformOp:orient').Set(Gf.Quatf(w,Gf.Vec3f(x,y,z)))
        moved.append(path)
    changes=[]
    initial_joints=[]
    for prim in stage.Traverse():
        if (str(prim.GetPath()).startswith('/World/Robot/Joints/')
                and prim.IsA(UsdPhysics.PrismaticJoint)
                and 'PhysicsDriveAPI:linear' in prim.GetAppliedSchemas()):
            # Reduced-coordinate articulations otherwise start at zero, even
            # when their authored bodies and drive targets describe open jaws.
            # Initial-state authoring only: never called after World.reset().
            q=UsdPhysics.DriveAPI(prim,'linear').GetTargetPositionAttr().Get()
            joint=UsdPhysics.PrismaticJoint(prim)
            if not joint.GetLowerLimitAttr().Get()-1e-7<=q<=joint.GetUpperLimitAttr().Get()+1e-7:
                raise ValueError(f'Initial drive target outside joint limits: {prim.GetPath()}')
            state=PhysxSchema.JointStateAPI.Apply(prim,'linear')
            state.CreatePositionAttr(q); state.CreateVelocityAttr(0.)
            initial_joints.append({'joint':str(prim.GetPath()),'position_m':q,'velocity_m_s':0.})
        if prim.HasAPI(UsdPhysics.MaterialAPI):
            material=UsdPhysics.MaterialAPI(prim)
            for attr in (material.GetStaticFrictionAttr(),material.GetDynamicFrictionAttr()):
                before=attr.Get()
                if before is not None:
                    after=before*condition['friction_scale']; attr.Set(after)
                    changes.append({'attribute':str(attr.GetPath()),'before':before,'after':after})
        if prim.HasAPI(UsdPhysics.CollisionAPI) and str(prim.GetPath()).startswith(('/World/Robot/','/World/Plug/','/World/Latch/','/World/PortRow/')):
            api=PhysxSchema.PhysxCollisionAPI(prim)
            attr=api.GetContactOffsetAttr()
            if attr and attr.HasAuthoredValueOpinion():
                before=attr.Get()
                if before>0:
                    after=before*condition['contact_offset_scale']; attr.Set(after)
                    changes.append({'attribute':str(attr.GetPath()),'before':before,'after':after})
    return {'initial_pose_paths':moved,'initial_robot_joint_states':initial_joints,'material_and_contact_changes':changes,
        'target_port':condition['port'],'scope':'Authored initial conditions before physics; no runtime body pose changes'}
