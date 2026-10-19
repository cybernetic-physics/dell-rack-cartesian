"""Bounded actuator setpoint changes; these do not assign physical joint poses."""
import math


def slew_target(current, target, rate, dt):
    if not all(math.isfinite(v) for v in (current, target, rate, dt)):
        raise ValueError('Actuator setpoint inputs must be finite')
    if rate <= 0 or dt <= 0:
        raise ValueError('Actuator setpoint rate and timestep must be positive')
    return current + max(-rate*dt, min(rate*dt, target-current))
