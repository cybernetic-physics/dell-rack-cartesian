"""SI-unit inverse position maps; these produce joint commands, never poses."""
import math


def gravity_position_bias(moving_mass,stiffness,force_limit,gravity=9.81):
    """Equivalent static position-drive preload, still subject to its force cap."""
    if not all(math.isfinite(v) and v>0 for v in (moving_mass,stiffness,force_limit,gravity)):
        raise ValueError('Gravity compensation requires finite positive parameters')
    weight=moving_mass*gravity
    if weight>=force_limit:
        raise ValueError('Lift drive cannot statically support the modeled moving mass')
    return weight/stiffness


def compensate_deflection(target,nominal_tcp,measured_tcp,limit=.0025):
    offset=tuple(a-b for a,b in zip(nominal_tcp,measured_tcp))
    if len(offset)!=3 or not all(math.isfinite(v) and abs(v)<=limit for v in offset):
        raise ValueError(f'Compliant tool deflection exceeds {limit} m or is invalid: {offset}')
    return tuple(a+b for a,b in zip(target,offset))


class DeflectionFilter:
    """Slow equilibrium compensation; do not cancel the passive wrist dynamics."""
    def __init__(self,time_constant=.15,max_rate=.003):
        self.time_constant=time_constant; self.max_rate=max_rate; self.offset=None

    def update(self,nominal_tcp,measured_tcp,dt,adapt=True):
        raw=compensate_deflection((0,0,0),nominal_tcp,measured_tcp)
        if self.offset is None: self.offset=raw
        elif adapt:
            alpha=dt/(self.time_constant+dt); step=self.max_rate*dt
            self.offset=tuple(old+max(-step,min(step,alpha*(new-old))) for old,new in zip(self.offset,raw))
        return self.offset


def compliant_joint_coordinates(architecture,target,nominal_tcp,measured_tcp,tool_offset=.13):
    adjusted=compensate_deflection(target,nominal_tcp,measured_tcp)
    travel=.20 if architecture=='B' else .21
    bounds=((-travel,travel),(.55-.125,.55),(1.10,1.80))
    if any(not math.isfinite(v) or v<lo-.0025 or v>hi+.0025
           for v,(lo,hi) in zip(target,bounds)):
        raise ValueError(f'TCP outside bounded compliant workspace: {target}')
    # Saturate actuator targets at physical joint limits, not the task's
    # measured success/error test. Compensation cannot create extra travel.
    adjusted=tuple(min(hi,max(lo,v)) for v,(lo,hi) in zip(adjusted,bounds))
    return joint_coordinates(architecture,adjusted,tool_offset)


def joint_coordinates(architecture,tcp,tool_offset=.13):
    if architecture not in ('A','B','C'): raise ValueError(architecture)
    x,y,z=map(float,tcp)
    q={'x':x,'y':y+tool_offset-.68,'z':z-1.80}
    travel=.20 if architecture=='B' else .21
    if not (-travel<=x<=travel and -.125<=q['y']<=.000001 and -.70<=q['z']<=.000001):
        raise ValueError(f'TCP outside {architecture} joint limits: {tcp}')
    if architecture=='B':
        del q['x']
        q.update(x_outer=(x+.20)/2,x_inner=(x+.20)/2)
    return q
