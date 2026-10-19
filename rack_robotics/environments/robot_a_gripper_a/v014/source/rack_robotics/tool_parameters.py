"""Dimensioned custom rack-jaw transmission; not a vendor digital twin."""
import math

PINION_RADIUS=.006
FIXED_JAW_X=-.0069
OPEN_JAW_X=.0120
CLOSED_JAW_X=.0063
PAD_THICKNESS=.002
APPROACH_OFFSET_X=-.0025


def rack_servo_target(closed):
    # Positive Z pinion rotation drives a rack on its +Y tangent toward -X.
    travel=OPEN_JAW_X-CLOSED_JAW_X if closed else 0.
    return math.degrees(travel/PINION_RADIUS)
