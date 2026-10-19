"""Bounded actuator setpoint changes; these do not assign physical joint poses."""
import math


def latch_press_target(override, lower, upper):
    """Validate a tool-joint command, never alter the connector or its gate."""
    target = -.005 if override is None else override
    if (not all(math.isfinite(v) for v in (target,lower,upper))
            or not lower-1e-9 <= target < 0 <= upper or lower>=0):
        raise ValueError('Latch press target must be negative and within the existing joint limits')
    # USD stores joint limits as float32; clamp only sub-nanometre conversion
    # roundoff, never extend the authored physical travel.
    return max(lower,target)


def slew_target(current, target, rate, dt):
    if not all(math.isfinite(v) for v in (current, target, rate, dt)):
        raise ValueError('Actuator setpoint inputs must be finite')
    if rate <= 0 or dt <= 0:
        raise ValueError('Actuator setpoint rate and timestep must be positive')
    return current + max(-rate*dt, min(rate*dt, target-current))
