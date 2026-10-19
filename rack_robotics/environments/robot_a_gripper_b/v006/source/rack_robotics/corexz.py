"""Power-consistent lumped CoreXZ transmission, in SI units.

Two ideal position-controlled motor/belt coordinates a=x+z, b=x-z act
through elastic transmissions. Forces are limited in MOTOR coordinates,
then mapped through J^T. No independent X/Z position drive is permitted.
Motor rotor inertia, tooth contact, pretension/slack and thermal behavior
are omitted; stiffness/damping and torque caps are uncalibrated assumptions.
"""
from dataclasses import dataclass
import math


def motor_coordinates(x,z):
    x,z=float(x),float(z)
    return (x+z,x-z)


def carriage_coordinates(a,b):
    a,b=float(a),float(b)
    return ((a+b)/2,(a-b)/2)


def generalized_forces(a,b):
    a,b=float(a),float(b)
    return (a+b,a-b)


@dataclass(frozen=True)
class BeltParameters:
    stiffness_n_m: float=8000.
    damping_ns_m: float=90.
    motor_force_limit_n: float=25.
    pitch_radius_m: float=20*.002/(2*math.pi)


def transmission_efforts(target,position,velocity,lift_weight_n,parameters=None,
                         enabled=(True,True),x_force_limit_n=None):
    p=parameters or BeltParameters()
    values=(*target,*position,*velocity,lift_weight_n)
    if len(target)!=2 or len(position)!=2 or len(velocity)!=2 or not all(map(math.isfinite,values)):
        raise ValueError('CoreXZ requires finite X/Z position, velocity and lift load')
    desired=motor_coordinates(*target)
    measured=motor_coordinates(*position)
    speed=motor_coordinates(*velocity)
    # Gravity compensation is also motor-limited; it is not a separate lift force.
    feedforward=(lift_weight_n/2,-lift_weight_n/2)
    unconstrained=tuple(p.stiffness_n_m*(t-q)-p.damping_ns_m*v+g
                        for t,q,v,g in zip(desired,measured,speed,feedforward))
    motor=tuple(max(-p.motor_force_limit_n,min(p.motor_force_limit_n,f)) if on else 0.
                for f,on in zip(unconstrained,enabled))
    transverse_limited=False
    if x_force_limit_n is not None:
        if not math.isfinite(x_force_limit_n) or x_force_limit_n<0:
            raise ValueError('Transverse force limit must be finite and nonnegative')
        fx,fz=generalized_forces(*motor)
        if abs(fx)>x_force_limit_n:
            transverse_limited=True
            if all(enabled):
                # Reduce net transverse force while retaining lift support.
                # This shrinks |Fx|+|Fz|, so neither motor cap can be exceeded.
                motor=carriage_coordinates(math.copysign(x_force_limit_n,fx),fz)
            else:
                # Do not recreate a failed motor through force allocation.
                motor=tuple(f*x_force_limit_n/abs(fx) for f in motor)
    return {'motor_target_m':desired,'motor_position_m':measured,
            'motor_velocity_m_s':speed,'motor_force_n':motor,
            'motor_torque_nm':tuple(f*p.pitch_radius_m for f in motor),
            'motor_saturated':tuple(abs(f)>p.motor_force_limit_n for f in unconstrained),
            'transverse_force_limited':transverse_limited,
            'joint_force_n':generalized_forces(*motor)}
