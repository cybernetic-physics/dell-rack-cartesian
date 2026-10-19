"""Static solid-bracket interference, including collision-filtered body pairs.

Restricted to axis-aligned carrier mount cubes at the authored initial pose.
This does not prove dynamic/full-stroke clearance or audit the rest of the rack.
"""
from pxr import UsdGeom, UsdPhysics


def screen_carrier_mounts(stage):
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
