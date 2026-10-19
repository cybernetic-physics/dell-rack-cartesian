"""Ordinary-D6 constraint-load threshold diagnostic, not a tension transducer."""
import math


def validate_request(threshold, role, cycles=1, occupied=False):
    if threshold is None:
        return
    if isinstance(threshold, bool) or not math.isfinite(threshold) or threshold <= 0:
        raise ValueError('Cable constraint threshold must be finite and positive in newtons')
    if role != 'control' or cycles != 1 or occupied:
        raise ValueError('Cable-load threshold screen requires a separate one-cycle nominal control')


class CableLoadMonitor:
    def __init__(self, stage, threshold_n, count):
        from pxr import UsdPhysics, PhysicsSchemaTools
        from omni.physx import get_physx_interface
        from omni.physx.bindings._physx import SimulationEvent
        validate_request(threshold_n, 'control')
        self.threshold_n = threshold_n
        self.paths = [f'/World/Cable/Joint{i:02d}' for i in range(count)]
        self.events = []
        self.errors = []
        self.context = {'interval': 'initialization', 'time_s': 0., 'phase': 'startup'}
        for path in self.paths:
            joint = UsdPhysics.Joint(stage.GetPrimAtPath(path))
            if not joint:
                raise ValueError('Missing cable D6 joint: ' + path)
            # Only author the diagnostic threshold in the experiment's overlay.
            # No joint/collider disabling or drive/pose changes are made here.
            joint.CreateBreakForceAttr(threshold_n)

        def on_event(event):
            if event.type != int(SimulationEvent.JOINT_BREAK):
                return
            try:
                path = str(PhysicsSchemaTools.decodeSdfPath(*event.payload['jointPath']))
                if path in self.paths:
                    self.events.append({'joint': path, **self.context})
            except Exception as error:
                self.errors.append(str(error))
        self.subscription = get_physx_interface().get_simulation_event_stream_v2().create_subscription_to_pop(on_event)

    def assert_intact(self):
        if self.errors:
            raise RuntimeError('Cable constraint-load event reporting failed: ' + str(self.errors))
        if self.events:
            raise RuntimeError('Cable constraint-load threshold crossed; diagnostic stopped: ' + str(self.events[0]))

    def report(self, task_complete, callback_interval_s):
        return {'threshold_n': self.threshold_n, 'joint_paths': self.paths,
                'events': self.events, 'reporting_errors': self.errors,
                'task_complete_without_threshold_event': bool(task_complete and not self.events and not self.errors),
                'event_poll_interval_s': callback_interval_s,
                'scope': 'Constraint resultant-load threshold, including startup, not axial tension or a calibrated material limit',
                'limitations': ['Angular drive forces excluded from PhysX break accounting.',
                               'Breakage changes the model; task aborts at the first delivered event.',
                               'Events are delivered at render/update boundaries, not necessarily the exact solver step.',
                               'No actual peak-force value or manufacturer safe-load rating is inferred.']}
