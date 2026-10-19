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
                         enabled=(True,True)):
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
    return {'motor_target_m':desired,'motor_position_m':measured,
            'motor_velocity_m_s':speed,'motor_force_n':motor,
            'motor_torque_nm':tuple(f*p.pitch_radius_m for f in motor),
            'motor_saturated':tuple(abs(f)>p.motor_force_limit_n for f in unconstrained),
            'joint_force_n':generalized_forces(*motor)}
