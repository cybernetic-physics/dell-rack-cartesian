"""Momentum-balance estimator primitives; physics validation required before use.

For an unbranched free-ended chain, summing each distal body's momentum residual
gives the proximal joint reaction, provided ALL other impulses are accounted for.
This module never writes body poses, velocities, or forces.
"""
import math


def residual_forces(masses, before, after, impulses, dt, gravity, damping):
    n = len(masses)
    if not n or any(len(a) != n for a in (before, after, impulses, damping)):
        raise ValueError('Mismatched or empty body arrays')
    if not math.isfinite(dt) or dt <= 0 or len(gravity) != 3:
        raise ValueError('Invalid timestep or gravity')
    rows = []
    for mass, v0, v1, impulse, drag in zip(masses, before, after, impulses, damping):
        if any(len(v) != 3 for v in (v0, v1, impulse)):
            raise ValueError('Expected three-vector inputs')
        values = [mass, drag, *gravity, *v0, *v1, *impulse]
        if not all(math.isfinite(float(x)) for x in values) or mass <= 0 or drag < 0:
            raise ValueError('Nonfinite or invalid body inputs')
        # PhysX unconstrained velocity integration: gravity, then linear damping.
        # Explicit isolated controls test this ordering against installed runtime.
        attenuation = max(0., 1. - drag * dt)
        free = [(v + g * dt) * attenuation for v, g in zip(v0, gravity)]
        rows.append([(mass * (v - expected) - j) / dt
                     for v, expected, j in zip(v1, free, impulse)])
    return rows


def distal_reactions(residuals):
    total = [0., 0., 0.]
    reactions = []
    for row in reversed(residuals):
        if len(row) != 3 or not all(math.isfinite(v) for v in row):
            raise ValueError('Invalid residual force')
        total = [a + b for a, b in zip(total, row)]
        reactions.append(list(total))
    return list(reversed(reactions))


def axial_component(force, toward_parent):
    if len(force) != 3 or len(toward_parent) != 3:
        raise ValueError('Expected three-vectors')
    if not all(math.isfinite(v) for v in [*force, *toward_parent]):
        raise ValueError('Nonfinite axial projection')
    norm = math.sqrt(sum(v * v for v in toward_parent))
    if norm < 1e-12:
        raise ValueError('Undefined cable axis')
    return sum(a * b for a, b in zip(force, toward_parent)) / norm


class FullContactImpulses:
    """Accumulate normal AND friction impulses on each tracked body per step."""
    def __init__(self, paths):
        from pxr import PhysicsSchemaTools
        from omni.physx import get_physx_simulation_interface
        self.paths = list(paths)
        self.decode = PhysicsSchemaTools.intToSdfPath
        self.errors = []
        self.begin()
        self.subscription = get_physx_simulation_interface().subscribe_full_contact_report_events(self.on_contacts)

    def begin(self):
        self.normal = {p: [0., 0., 0.] for p in self.paths}
        self.friction = {p: [0., 0., 0.] for p in self.paths}
        self.headers = 0
        self.anchors = 0

    def on_contacts(self, headers, data, anchors):
        try:
            for h in headers:
                actors = [str(self.decode(h.actor0)), str(self.decode(h.actor1))]
                if not any(p in self.normal for p in actors):
                    continue
                self.headers += 1
                normal = [0., 0., 0.]
                friction = [0., 0., 0.]
                for c in data[h.contact_data_offset:h.contact_data_offset + h.num_contact_data]:
                    normal = [a + float(b) for a, b in zip(normal, c.impulse)]
                for c in anchors[h.friction_anchors_offset:h.friction_anchors_offset + h.num_friction_anchors_data]:
                    friction = [a + float(b) for a, b in zip(friction, c.impulse)]
                    self.anchors += 1
                # Native contact normal/impulse orientation is checked by the
                # independent resting/sliding controls; never fit sign per trial.
                for p, sign in zip(actors, (1., -1.)):
                    if p in self.normal:
                        self.normal[p] = [a + sign*b for a,b in zip(self.normal[p],normal)]
                        self.friction[p] = [a + sign*b for a,b in zip(self.friction[p],friction)]
        except Exception as error:
            self.errors.append(repr(error))

    def totals(self):
        if self.errors:
            raise RuntimeError('Full-contact reporting failed: ' + str(self.errors))
        return [[a+b for a,b in zip(self.normal[p],self.friction[p])] for p in self.paths]
