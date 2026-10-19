"""Reuse baseline pose/latch observation, without creating its actuators."""
from pxr import Gf
from rack_sim.connector import Interaction


class ConnectorObserver(Interaction):
    def __init__(self,stage,ports,previous=None):
        self.stage=stage; self.ports=ports
        self.origin=Gf.Vec3d(*ports[0][1]); self.mouth=self.origin
        self.port_index=0; self.visited_ports=set()
        self.state='unplugged'; self.clip_pressed=False; self.dwell=0.; self.cycles=0
        self.events=[]; self.time=0.; self.last_position=None; self.metrics={}
        # Controller ownership changes, not the physical connector. Preserve the
        # measured observer state and baseline hysteresis across that handoff.
        # Every subsequent tick still checks actual hook clearance/escape.
        if previous is not None:
            self.port_index=previous.port_index; self.mouth=previous.mouth
            self.state=previous.state; self.dwell=previous.dwell
            self.last_position=previous.last_position; self.time=previous.time
            self.metrics=dict(previous.metrics)
            self.visited_ports=set(previous.visited_ports)
            self.events=list(previous.events); self.cycles=previous.cycles

    def set_target(self,*args,**kwargs):
        raise RuntimeError('Observer cannot move the connector')

    def set_grasp(self,*args,**kwargs):
        raise RuntimeError('Observer cannot attach the connector')

    def release(self,*args,**kwargs):
        raise RuntimeError('Observer cannot actuate the latch')
