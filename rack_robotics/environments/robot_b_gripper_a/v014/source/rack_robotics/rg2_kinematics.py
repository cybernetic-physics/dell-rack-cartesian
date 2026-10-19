"""RG2 vendor-linkage geometry, not a hardware force/timing calibration.

Coordinates are in the vendor base frame (+Z extension, X closing). Constants
come from the original joint anchors; probe_rg2 verifies the equations against
actual articulated motion. Tip origins are not the standard pad surfaces.
"""
import math

ARM_LENGTH = .05494315
ARM_OFFSET = .0025
EXTENSION_ORIGIN = .15984
TIP_CENTER_X = -.00005
MIN_ANGLE_DEG = 0.
MAX_ANGLE_DEG = 70.06


def tip_geometry(angle_deg):
    """Return (tip-origin separation, mean axial extension), in metres."""
    if not math.isfinite(angle_deg) or not MIN_ANGLE_DEG <= angle_deg <= MAX_ANGLE_DEG:
        raise ValueError('RG2 angle is outside its physical joint range')
    q = math.radians(angle_deg)
    half_width = ARM_LENGTH * math.sin(q) + ARM_OFFSET * (1 - math.cos(q))
    extension = EXTENSION_ORIGIN + ARM_LENGTH * math.cos(q) + ARM_OFFSET * math.sin(q)
    return 2 * half_width, extension


def angle_for_tip_separation(separation):
    """Invert the monotone physical range; reject impossible openings."""
    maximum, _ = tip_geometry(MAX_ANGLE_DEG)
    if not math.isfinite(separation) or not 0 <= separation <= maximum:
        raise ValueError('RG2 tip-origin separation is outside its physical range')
    low, high = MIN_ANGLE_DEG, MAX_ANGLE_DEG
    for _ in range(55):
        mid = (low + high) / 2
        if tip_geometry(mid)[0] < separation:
            low = mid
        else:
            high = mid
    return (low + high) / 2


def ideal_force_per_jaw(angle_deg, torque_nm):
    """Static virtual-work estimate, ignoring losses, friction and compliance.

    The one driven coordinate moves two jaws. Do not confuse this estimate
    with measured pad contact force or the product's selectable grip force.
    """
    tip_geometry(angle_deg)
    if not math.isfinite(torque_nm) or torque_nm < 0:
        raise ValueError('Torque must be finite and nonnegative')
    q = math.radians(angle_deg)
    derivative = 2 * (ARM_LENGTH * math.cos(q) + ARM_OFFSET * math.sin(q))
    return torque_nm / derivative
