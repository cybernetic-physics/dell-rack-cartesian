"""Read-only geometric/gravity screening of measured robot trajectories.

No simulation control, body pose writes, hardware ratings or safety conclusions.
"""
import itertools
import math


def transform_point(pose,point):
    """Recorded pose is xyz,wxyz; point is in the rigid-body frame."""
    if len(pose)!=7 or len(point)!=3 or not all(math.isfinite(v) for v in (*pose,*point)):
        raise ValueError('Invalid pose or point')
    w,x,y,z=pose[3:]
    norm=w*w+x*x+y*y+z*z
    if abs(norm-1)>1e-4: raise ValueError('Non-unit recorded quaternion')
    # q*v*q^-1, with normalization only for floating-point recording noise.
    scale=1/math.sqrt(norm); w,x,y,z=(v*scale for v in (w,x,y,z))
    px,py,pz=point
    cross=(y*pz-z*py,z*px-x*pz,x*py-y*px)
    second=(y*cross[2]-z*cross[1],z*cross[0]-x*cross[2],x*cross[1]-y*cross[0])
    return tuple(pose[i]+point[i]+2*(w*cross[i]+second[i]) for i in range(3))


def gravity_wrench(mass_centres,reference,gravity=9.81):
    """Gravity load on the mount; support reaction has the opposite sign."""
    rows=list(mass_centres)
    if not rows or len(reference)!=3 or not all(math.isfinite(v) for v in reference):
        raise ValueError('Missing or invalid load/reference')
    if not math.isfinite(gravity) or gravity<=0: raise ValueError('Invalid gravity')
    if any(m<=0 or not math.isfinite(m) or len(p)!=3 or not all(math.isfinite(v) for v in p) for m,p in rows):
        raise ValueError('Invalid mass or centre')
    mass=sum(m for m,_ in rows)
    com=[sum(m*p[i] for m,p in rows)/mass for i in range(3)]
    return {'mass_kg':mass,'com_world_m':com,'force_n':[0.,0.,-mass*gravity],
            'moment_nm':[-mass*gravity*(com[1]-reference[1]),mass*gravity*(com[0]-reference[0]),0.]}


def box_corners(lower,upper):
    if len(lower)!=3 or len(upper)!=3 or any(not math.isfinite(v) for v in (*lower,*upper)) or any(a>b for a,b in zip(lower,upper)):
        raise ValueError('Invalid bounds')
    return list(itertools.product(*zip(lower,upper)))


def envelope(points):
    points=list(points)
    if not points: raise ValueError('Empty envelope')
    lo=[min(p[i] for p in points) for i in range(3)]
    hi=[max(p[i] for p in points) for i in range(3)]
    return {'lower_m':lo,'upper_m':hi,'dimensions_m':[b-a for a,b in zip(lo,hi)]}


def rack_overhang(bounds,half_width=.3,rear_plane=.6):
    return {'left_m':max(0.,-half_width-bounds['lower_m'][0]),
            'right_m':max(0.,bounds['upper_m'][0]-half_width),
            'rear_m':max(0.,bounds['upper_m'][1]-rear_plane)}


def descendants(start,joints,bodies):
    found=set(); pending=[start]
    while pending:
        parent=pending.pop()
        if parent in found: continue
        if parent not in bodies: raise ValueError(f'Joint names unknown body: {parent}')
        found.add(parent)
        for joint in joints:
            if joint['body0']==[parent]: pending.extend(joint['body1'])
    return sorted(found)


def screen(properties,header,samples):
    if not properties.get('passed'): raise ValueError('No validated cooked properties')
    if header.get('format')!='measured_world_poses_v1' or not samples: raise ValueError('Missing measured trajectory')
    bodies=properties['bodies']; paths=header['body_paths']
    if len(set(paths))!=len(paths): raise ValueError('Duplicate recorded body paths')
    indices={p:paths.index(p) for p in bodies}  # Missing measured body is an error.
    mounts=properties['mount_centres_m']
    if not mounts: raise ValueError('Missing rack mount geometry')
    reference=[sum(p[i] for p in mounts)/len(mounts) for i in range(3)]
    corners={}
    for path,body in bodies.items():
        corners[path]=[p for shape in body['geometry'] for p in box_corners(shape['lower_m'],shape['upper_m'])]
        if not corners[path]: raise ValueError(f'Missing geometry: {path}')
    boom_joints=[j for j in properties['joints'] if j['path'].rsplit('/',1)[-1] in ('OuterExtension','InnerExtension')]
    downstream={j['path']:descendants(j['body1'][0],properties['joints'],bodies) for j in boom_joints}
    swept=[]; worst_moment=None; initial=None; final=None; boom_max={}; moving_mass=None
    for row in samples:
        if len(row['poses'])!=len(paths): raise ValueError('Incomplete recorded pose sample')
        poses={path:row['poses'][index] for path,index in indices.items()}
        centres={path:transform_point(poses[path],body['com_local_xyz_xyzw'][:3]) for path,body in bodies.items()}
        bound=envelope(transform_point(poses[path],point) for path in bodies for point in corners[path])
        swept.extend((bound['lower_m'],bound['upper_m']))
        load=gravity_wrench(((body['mass_kg'],centres[path]) for path,body in bodies.items()),reference)
        load.update(time_s=row['time'],phase=row['phase'],moment_norm_nm=math.dist(load['moment_nm'],(0,0,0)))
        if worst_moment is None or load['moment_norm_nm']>worst_moment['moment_norm_nm']: worst_moment=load
        if initial is None: initial={'time_s':row['time'],'phase':row['phase'],'bounds':bound,'overhang':rack_overhang(bound)}
        final={'time_s':row['time'],'phase':row['phase'],'bounds':bound,'overhang':rack_overhang(bound)}
        moving_mass=sum(b['mass_kg'] for p,b in bodies.items() if p!='/World/Robot/Frame')
        for joint in boom_joints:
            anchor=transform_point(poses[joint['body0'][0]],joint['anchor_in_body0_m'])
            wrench=gravity_wrench(((bodies[p]['mass_kg'],centres[p]) for p in downstream[joint['path']]),anchor)
            wrench.update(time_s=row['time'],phase=row['phase'],anchor_world_m=list(anchor),
                moment_norm_nm=math.dist(wrench['moment_nm'],(0,0,0)))
            if joint['path'] not in boom_max or wrench['moment_norm_nm']>boom_max[joint['path']]['moment_norm_nm']:
                boom_max[joint['path']]=wrench
    full=envelope(swept)
    return {'scope':'30 Hz recorded-trajectory geometry and quasi-static gravity only',
        'sample_count':len(samples),'time_range_s':[samples[0]['time'],samples[-1]['time']],
        'total_modeled_mass_kg':sum(b['mass_kg'] for b in bodies.values()),'moving_mass_kg':moving_mass,
        'mount_reference_m':reference,'mount_reference_definition':'Centroid of authored PostClamp centres',
        'rigid_geometry_swept_bounds':full,'maximum_sampled_overhang':rack_overhang(full),
        'initial_envelope':initial,'final_envelope':final,
        'largest_sampled_gravity_mount_moment':worst_moment,'telescoping_joint_gravity_loads':boom_max,
        'telescoping_supported_bodies':downstream,
        'prismatic_joint_limits':[j for j in properties['joints'] if 'limits_m' in j],
        'rated_load_pass':None,'dense_cable_clearance_pass':None,'rear_door_clearance_pass':None,
        'limitations':['Not continuous swept-volume collision checking; gaps between 30 Hz samples remain.',
                      'Bounding boxes conservatively bound authored visual/collision geometry, not exact surfaces.',
                      'Gravity only: no inertial, plug/cable, external contact or fault/braking loads.',
                      'Modeled lumped masses and cooked COMs are not weighed or certified hardware properties.',
                      'Nominal 600 mm rack width and rear Y=600 mm are model references, not a door survey.',
                      'Root fixed joint is an ideal mount; bolt reactions, stiffness and rack ratings remain unverified.',
                      'Unowned decorative geometry and absent cable carriers are not included in rigid-body bounds.']}
