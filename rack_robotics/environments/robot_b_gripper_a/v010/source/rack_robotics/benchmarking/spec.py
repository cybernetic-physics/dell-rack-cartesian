"""Deterministic, paired conditions. Bounds are experiments, not hardware ratings."""
import hashlib
import math
import random
import re

SCHEMA='rack_benchmark_conditions_v1'
PORTS=(1,4,8,12,16)


def select_designs(entries, defaults):
    """Explicit version selection without permitting path escapes or ID swaps."""
    if not entries: return dict(defaults)
    selected={}
    for entry in entries:
        if '=' not in entry: raise ValueError('Use DESIGN=robot_x_gripper_y/vNNN')
        design,relative=entry.split('=',1)
        match=re.fullmatch(r'robot_([abc])_gripper_([abc])/v[0-9]{3,}',relative)
        if not match or design!=''.join(match.groups()).upper() or design in selected:
            raise ValueError('Invalid or duplicate design/version selection: '+entry)
        selected[design]=relative
    return selected


def control():
    return {'schema':SCHEMA,'role':'control','seed':None,'index':None,'port':1,
        'initial_robot_offset_m':[0.,0.,0.], 'calibration_offset_m':[0.,0.,0.],
        'connector_offset_m':[0.,0.,0.], 'connector_angles_deg':[0.,0.,0.],
        'cable_yaw_deg':0.,'cable_bend_start':5,'approach_time_scale':1.,
        'friction_scale':1.,'contact_offset_scale':1.}


def conditions(seed,count=10):
    if type(seed) is not int or type(count) is not int or count<10:
        raise ValueError('Benchmark requires an integer seed and at least 10 trials')
    output=[]; ports=[]
    for index in range(count):
        derived=int.from_bytes(hashlib.sha256(f'{seed}:{index}'.encode()).digest(),'big')
        rng=random.Random(derived)
        if index%len(PORTS)==0:
            ports=list(PORTS); rng.shuffle(ports)
        row=control()
        row.update(role='randomized',seed=seed,index=index,port=ports[index%len(PORTS)],
            initial_robot_offset_m=[rng.uniform(-.002,.002),rng.uniform(-.001,0),rng.uniform(-.002,0)],
            calibration_offset_m=[rng.uniform(-.0001,.0001),0.,rng.uniform(-.0001,.0001)],
            connector_offset_m=[rng.uniform(-.00008,.00008),rng.uniform(-.00005,.00005),rng.uniform(-.00008,.00008)],
            connector_angles_deg=[rng.uniform(-.5,.5),rng.uniform(-.25,.25),rng.uniform(-.5,.5)],
            cable_yaw_deg=rng.uniform(-12.,12.),cable_bend_start=rng.choice([4,5,6]),
            approach_time_scale=rng.uniform(.85,1.15),friction_scale=rng.uniform(.9,1.1),
            contact_offset_scale=rng.uniform(.9,1.1))
        validate(row); output.append(row)
    return output


def validate(row):
    template=control()
    if set(row)!=set(template) or row['schema']!=SCHEMA or row['role'] not in ('control','randomized'):
        raise ValueError('Unknown or incomplete benchmark condition schema')
    if type(row['port']) is not int or row['port'] not in PORTS:
        raise ValueError('Unsupported benchmark port')
    bounds={'initial_robot_offset_m':(.002,.001,.002),'calibration_offset_m':(.0001,0.,.0001),
            'connector_offset_m':(.00008,.00005,.00008),'connector_angles_deg':(.5,.25,.5)}
    for name,limits in bounds.items():
        values=row[name]
        if len(values)!=3 or any(not math.isfinite(v) or abs(v)>limit+1e-12 for v,limit in zip(values,limits)):
            raise ValueError(f'Invalid {name}')
    if any(row['initial_robot_offset_m'][i]>0 for i in (1,2)):
        raise ValueError('Initial robot Y/Z offset would exceed park travel')
    for name,lo,hi in [('cable_yaw_deg',-12,12),('approach_time_scale',.85,1.15),
                       ('friction_scale',.9,1.1),('contact_offset_scale',.9,1.1)]:
        if not math.isfinite(row[name]) or not lo<=row[name]<=hi: raise ValueError(name)
    if row['cable_bend_start'] not in (4,5,6): raise ValueError('cable_bend_start')
    if row['role']=='control' and row!=template: raise ValueError('Control conditions must be nominal')
    if row['role']=='randomized' and (type(row['seed']) is not int or type(row['index']) is not int or row['index']<0):
        raise ValueError('Randomized condition needs seed and index')
    return row


def cable_route(origin,yaw_deg,bend_start,segments=36,length=.015):
    """Coincident initial endpoints and unit quaternions (w,x,y,z), before physics."""
    endpoint=list(origin); result=[]
    for i in range(segments):
        fall=math.radians(min(90,max(0,(i-bend_start)*15)))
        yaw=math.radians(yaw_deg)*math.sin(math.pi*min(i/12,1)/2)
        d=(-math.sin(yaw)*math.cos(fall),math.cos(yaw)*math.cos(fall),-math.sin(fall))
        q=(1+d[1],d[2],0.,-d[0]); norm=math.sqrt(sum(v*v for v in q))
        q=tuple(v/norm for v in q)
        centre=tuple(v+a*length/2 for v,a in zip(endpoint,d))
        endpoint=[v+a*length for v,a in zip(endpoint,d)]
        result.append({'position':centre,'quaternion':q,'direction':d,'end':tuple(endpoint)})
    return result


def can_nudge_preseat(metrics,position,mouth):
    """Bounded fixture recovery for a hook resting on the lip, never a bypass."""
    return (len(position)==3 and all(math.isfinite(v) for v in position)
        and .0103<=metrics.get('depth_m',-1)<.0115
        and metrics.get('angle_deg',float('inf'))<2
        and all(abs(position[i]-mouth[i])<.00022 for i in (0,2))
        and not metrics.get('hook_behind_lip',False))
