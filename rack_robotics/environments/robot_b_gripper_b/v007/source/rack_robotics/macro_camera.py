"""Read-only camera framing of measured RJ45 motion, including separation."""
import math
from .mechanical_screen import box_corners, transform_point


def inspection_points(focus, plug_pose):
    # Inspection envelopes in metres: socket opening/lip and the shared plug's
    # housing, boot and raised latch. They affect framing only, never collisions.
    socket = [tuple(a+b for a, b in zip(focus, corner)) for corner in
              box_corners((-.013, -.014, -.012), (.013, .004, .016))]
    plug = [transform_point(plug_pose, corner) for corner in
            box_corners((-.010, -.013, -.009), (.010, .032, .016))]
    return socket+plug


def fit_macro_camera(focus, plug_pose, offset, focal_length=35, margin=1.12):
    if focal_length <= 0 or margin < 1 or len(offset) != 3:
        raise ValueError('Invalid framing parameters')
    length = math.sqrt(sum(v*v for v in offset))
    if not math.isfinite(length) or length < 1e-6:
        raise ValueError('Invalid camera direction')
    target = [(a+b)/2 for a, b in zip(focus, plug_pose[:3])]
    target[2] += .003
    radius = max(math.dist(p, target) for p in inspection_points(focus, plug_pose))
    # The sphere must fit in the narrower (vertical) half field of view of the
    # 36 x 20.25 mm sensor. Moving back also keeps both bodies in front of lens.
    half_angle = math.atan(10.125/focal_length)
    distance = max(length, margin*radius/math.sin(half_angle))
    eye = [a+v*distance/length for a, v in zip(target, offset)]
    return eye, target
