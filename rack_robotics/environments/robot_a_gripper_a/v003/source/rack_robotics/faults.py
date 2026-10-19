"""Explicit actuator-command faults for recovery tests; observations stay real."""


class SingleActuatorFault:
    def __init__(self,gripper,mode):
        if mode not in ('grasp_once','latch_once'): raise ValueError(mode)
        self.gripper=gripper; self.mode=mode; self.armed=True; self.time=0.; self.events=[]
        self.approach_offset=getattr(gripper,'approach_offset',(0.,0.,0.))
        self.grasp_duration=getattr(gripper,'grasp_duration',.7)
        self.release_duration=getattr(gripper,'release_duration',.7)
        self.align_to_measured_housing=getattr(gripper,'align_to_measured_housing',False)

    def step(self,dt):
        if hasattr(self.gripper,'step'): self.gripper.step(dt)

    def aperture(self): return self.gripper.aperture()

    def grasp(self,closed):
        if closed and self.armed and self.mode=='grasp_once':
            self.armed=False
            self.events.append({'time':self.time,'requested':'close_jaws','delivered':'keep_open'})
            return self.gripper.grasp(False)
        return self.gripper.grasp(closed)

    def press_latch(self,pressed):
        if pressed and self.armed and self.mode=='latch_once':
            self.armed=False
            self.events.append({'time':self.time,'requested':'press_latch','delivered':'keep_retracted'})
            return self.gripper.press_latch(False)
        return self.gripper.press_latch(pressed)
