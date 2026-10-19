"""Static solid-bracket interference, including collision-filtered body pairs.

Restricted to axis-aligned carrier mount cubes at the authored initial pose.
This does not prove dynamic/full-stroke clearance or audit the rest of the rack.
"""
import math
from pxr import Gf, UsdGeom, UsdPhysics


def mount_parts(stage):
    bounds=UsdGeom.BBoxCache(0,['default']); transforms=UsdGeom.XformCache()
    parts=[]; errors=[]
    for prim in stage.Traverse():
        path=str(prim.GetPath())
        if '/Robot/' not in path or '/CarrierMounts/' not in path or not prim.IsA(UsdGeom.Cube): continue
        owner=prim.GetParent()
        while owner and not owner.HasAPI(UsdPhysics.RigidBodyAPI): owner=owner.GetParent()
        if not owner: errors.append('No rigid owner: '+path); continue
        matrix=transforms.GetLocalToWorldTransform(prim)
        rows=[list(matrix[i])[:3] for i in range(3)]
        if any(sum(abs(v)>1e-8 for v in row)!=1 for row in rows):
            errors.append('Rotated/skewed bracket outside exact-box screen: '+path); continue
        parts.append((path,str(owner.GetPath()),bounds.ComputeWorldBound(prim).ComputeAlignedRange()))
    return parts,errors


def screen_carrier_mounts(stage):
    parts,errors=mount_parts(stage)
    overlaps=[]; checked=0
    for index,(path0,owner0,a) in enumerate(parts):
        for path1,owner1,b in parts[index+1:]:
            if owner0==owner1: continue # Same rigid welded assembly may overlap.
            checked+=1
            depths=[min(a.GetMax()[i],b.GetMax()[i])-max(a.GetMin()[i],b.GetMin()[i]) for i in range(3)]
            if all(d>1e-6 for d in depths):
                overlaps.append({'parts':[path0,path1],'owners':[owner0,owner1],
                                 'overlap_depths_m':depths})
    return {'passed':bool(parts) and not errors and not overlaps,'parts':len(parts),
            'distinct_body_pairs_checked':checked,'overlaps':overlaps,'errors':errors,
            'scope':'Initial axis-aligned carrier mount solids only, regardless of collision filters; not full-stroke, carrier-link, rack, fastener or strength acceptance'}


def screen_carrier_mount_sweep(stage,include_robot_boxes=False,all_robot_box_pairs=False):
    """Exact interval test for axis-aligned mount cubes on Cartesian sliders.

    Joint limits are independent intervals; each slider changes one WORLD
    coordinate only. Relative center intervals therefore give an exact box
    overlap-existence test, without a sampled-pose gap or a physics pose write.
    Rotated/skewed mounts and non-axis-aligned sliders fail closed. Carrier
    links, rack geometry, fasteners and elastic deflection remain outside scope.
    """
    if all_robot_box_pairs and not include_robot_boxes:
        raise ValueError('All robot box pairs requires include_robot_boxes')
    parts,errors=mount_parts(stage);cache=UsdGeom.XformCache();joints=[];parents={}
    root='/World/Robot';frame=root+'/Frame'
    for name in ('Lift','Traverse','OuterExtension','InnerExtension','Insertion'):
        prim=stage.GetPrimAtPath(root+'/Joints/'+name)
        if not prim:continue
        if not prim.IsA(UsdPhysics.PrismaticJoint):
            errors.append('Expected prismatic joint: '+name);continue
        j=UsdPhysics.PrismaticJoint(prim)
        ends=[j.GetBody0Rel().GetTargets(),j.GetBody1Rel().GetTargets()]
        if any(len(paths)!=1 or not stage.GetPrimAtPath(paths[0]) for paths in ends):
            errors.append('Expected one existing body per joint end: '+name);continue
        a,b=[str(paths[0]) for paths in ends]
        mats=[cache.GetLocalToWorldTransform(stage.GetPrimAtPath(p)) for p in (a,b)]
        anchors=[m.Transform(Gf.Vec3d(getattr(j,f'GetLocalPos{i}Attr')().Get())) for i,m in enumerate(mats)]
        axis=Gf.Vec3d(*(1 if token==j.GetAxisAttr().Get() else 0 for token in 'XYZ'))
        axis=mats[0].TransformDir(Gf.Rotation(Gf.Quatd(j.GetLocalRot0Attr().Get())).TransformDir(axis)).GetNormalized()
        dimension=max(range(3),key=lambda i:abs(axis[i]));sign=1 if axis[dimension]>0 else -1
        if abs(abs(axis[dimension])-1)>1e-8 or any(abs(axis[i])>1e-8 for i in range(3) if i!=dimension):
            errors.append('Non-axis-aligned Cartesian joint: '+name);continue
        delta=anchors[1]-anchors[0];initial=Gf.Dot(delta,axis)
        lower=j.GetLowerLimitAttr().Get();upper=j.GetUpperLimitAttr().Get()
        if (not all(math.isfinite(v) for v in (lower,upper,initial)) or lower>upper
                or initial<lower-1e-6 or initial>upper+1e-6 or (delta-initial*axis).GetLength()>1e-6):
            errors.append('Invalid initial coordinate or limits: '+name);continue
        if b in parents:
            errors.append('Multiple Cartesian parents: '+b);continue
        parents[b]=(a,len(joints))
        joints.append({'name':name,'parent':a,'child':b,'axis':'XYZ'[dimension],
                       'dimension':dimension,'sign':sign,'initial_m':initial,'limits_m':[lower,upper]})
    omitted=[]
    mount_count=len(parts)
    if include_robot_boxes:
        # Check mount-to-stage solids even where adjacent-body contact is
        # disabled. Tool joints, dynamic chain links and non-box geometry need
        # separate checks; list those omissions rather than treating them clear.
        bounds=UsdGeom.BBoxCache(0,['default'])
        supported={frame,*parents}
        for prim in stage.Traverse():
            path=str(prim.GetPath())
            if not path.startswith(root+'/') or '/CarrierMounts/' in path:continue
            if not prim.IsA(UsdGeom.Gprim):continue
            owner=prim.GetParent()
            while owner and not owner.HasAPI(UsdPhysics.RigidBodyAPI):owner=owner.GetParent()
            owner_path=str(owner.GetPath()) if owner else None
            if owner_path not in supported or not prim.IsA(UsdGeom.Cube):
                omitted.append({'path':path,'owner':owner_path,
                    'reason':'unsupported rigid owner' if owner_path not in supported else 'non-box geometry'})
                continue
            matrix=cache.GetLocalToWorldTransform(prim)
            if any(sum(abs(matrix[i][j])>1e-8 for j in range(3))!=1 for i in range(3)):
                errors.append('Rotated/skewed robot box outside exact-box screen: '+path);continue
            parts.append((path,owner_path,bounds.ComputeWorldBound(prim).ComputeAlignedRange()))
    influences={}
    for _,owner,_ in parts:
        if owner in influences:continue
        chain=[];seen=set();body=owner
        while body!=frame:
            if body in seen or body not in parents:
                errors.append('Mount lacks a supported Cartesian path to Frame: '+owner);break
            seen.add(body);body,index=parents[body];chain.append(index)
        influences[owner]=set(chain)
    overlaps=[];checked=0
    if not errors:
        for index,(p0,o0,a) in enumerate(parts):
            for p1,o1,b in parts[index+1:]:
                if o0==o1:continue
                if not all_robot_box_pairs and '/CarrierMounts/' not in p0 and '/CarrierMounts/' not in p1:continue
                checked+=1
                center=a.GetMidpoint();other=b.GetMidpoint()
                half=(a.GetSize()+b.GetSize())/2
                intervals=[[other[i]-center[i],other[i]-center[i]] for i in range(3)]
                relevant=[]
                for k,j in enumerate(joints):
                    coefficient=(int(k in influences[o1])-int(k in influences[o0]))*j['sign']
                    if not coefficient:continue
                    shifts=[coefficient*(q-j['initial_m']) for q in j['limits_m']]
                    axis=j['dimension'];intervals[axis][0]+=min(shifts);intervals[axis][1]+=max(shifts)
                    relevant.append(j['name'])
                if all(lo<half[i]-1e-6 and hi>-half[i]+1e-6 for i,(lo,hi) in enumerate(intervals)):
                    overlaps.append({'parts':[p0,p1],'owners':[o0,o1],'varying_joints':relevant,
                        'relative_center_intervals_m':intervals,'sum_half_extents_m':list(half)})
    return {'passed':bool(parts if all_robot_box_pairs else mount_count) and bool(joints) and not errors and not overlaps,
            'parts':len(parts),'distinct_body_pairs_checked':checked,'joints':joints,
            'mount_parts':mount_count,'include_robot_boxes':include_robot_boxes,
            'all_robot_box_pairs':all_robot_box_pairs,
            'omitted_geometry':omitted,
            'possible_overlaps':overlaps,'errors':errors,
            'scope':('All independent Cartesian joint limits, '+
                     ('all supported Cartesian-body robot box pairs' if all_robot_box_pairs else
                      'axis-aligned carrier mount cubes'+(' versus each other and supported Cartesian-body robot boxes' if include_robot_boxes else ' only'))+
                     '; no pose writes, irrespective of collision filtering. Not dynamic links, rack, non-box or omitted geometry, deflection, fastener or strength acceptance.')}
