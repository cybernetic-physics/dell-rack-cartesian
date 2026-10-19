"""Deterministic joint-space travel probes; no simulator or pose-writing code.

Retracted travel is a necessary rack-clearance test, not a claim that arbitrary
extended poses are free space. A finite raster does not prove volume clearance.
"""
import math

REVISION = 'retracted_joint_raster_v1'


def fixture_architecture(config):
    """Select a supported precision-tool fixture, not a clearance certificate."""
    architecture = config.get('robot', '').split('_')[0]
    if architecture not in ('A', 'C') or config.get('gripper', '').split('_')[0] != 'A':
        raise ValueError('Workspace probe supports A/A and C/A precision-tool assemblies only')
    if not config.get('brake_revision') or not config.get('service_carrier_revision'):
        raise ValueError('Saved motor brakes and service carriers are required')
    return architecture


def retracted_raster(limits, rows=5):
    if set(limits) != {'x', 'y', 'z'} or rows < 2 or not isinstance(rows, int):
        raise ValueError('Expected x/y/z limits and at least two rows')
    for lo, hi in limits.values():
        if not all(math.isfinite(v) for v in (lo, hi)) or lo >= hi:
            raise ValueError('Invalid travel interval')
    xs = [limits['x'][0], sum(limits['x'])/2, limits['x'][1]]
    lo, hi = limits['z']
    points = []
    for row in range(rows):
        z = hi + (lo-hi)*row/(rows-1)
        for col, x in enumerate(xs if row % 2 == 0 else xs[::-1]):
            points.append({'name':f'row_{row:02d}_stop_{col:02d}',
                           'target':{'x':x, 'y':limits['y'][1], 'z':z}})
    # Return up the far edge, then along the upper edge. This complements the
    # descending raster; the caller finally returns to its authored start.
    points.append({'name':'return_upper_edge',
                   'target':{'x':points[-1]['target']['x'], 'y':limits['y'][1], 'z':hi}})
    return points


def move_duration(start, target, max_speed=.06):
    if set(start) != set(target) or not start or not math.isfinite(max_speed) or max_speed <= 0:
        raise ValueError('Invalid movement specification')
    if not all(math.isfinite(v) for mapping in (start, target) for v in mapping.values()):
        raise ValueError('Nonfinite coordinate')
    # Quintic easing has maximum derivative 1.875; cap each joint's speed.
    return max(.5, 1.875*max(abs(target[k]-start[k]) for k in start)/max_speed)


def interpolate(start, target, u):
    if not math.isfinite(u) or not 0 <= u <= 1 or set(start) != set(target):
        raise ValueError('Invalid interpolation')
    s = u*u*u*(10 + u*(-15 + 6*u))
    return {k:start[k] + (target[k]-start[k])*s for k in start}


def robot_contact_violations(pairs, threshold=.1):
    """No allowlist: both robot-self and robot-rack/tool/cable contacts count."""
    return [p for p in pairs if any(c.startswith('/World/Robot/') for c in p['colliders'])
            and (not math.isfinite(p['peak_pair_contact_force_n'])
                 or p['peak_pair_contact_force_n'] > threshold)]
