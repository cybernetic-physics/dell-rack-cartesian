"""Task-only perturbations; no connector, body-pose or joint-state writes."""
import inspect
import math


def construct(factory,stage,drives,architecture,gripper,control_dt=1/240):
    if not math.isfinite(control_dt) or control_dt<=0:
        raise ValueError('Control timestep must be finite and positive')
    parameters=inspect.signature(factory).parameters
    if 'control_dt' not in parameters and abs(control_dt-1/240)>1e-12:
        raise ValueError('Saved controller lacks a configurable timestep')
    optional={'architecture':architecture,'gripper':gripper,'control_dt':control_dt}
    return factory(stage,drives,**{k:v for k,v in optional.items() if k in parameters})


def bind_transmission_step(transmission,robot):
    """Adapt old saved transmission signatures without dropping a requested cap."""
    supports_limit='x_force_limit_n' in inspect.signature(transmission.step).parameters
    def step():
        limit=getattr(robot,'transverse_force_limit',None)
        if supports_limit: return transmission.step(x_force_limit_n=limit)
        if limit is not None:
            raise ValueError('Saved transmission cannot enforce the requested transverse force limit')
        return transmission.step()
    return step


class PerturbedRobot:
    def __init__(self,base,condition,architecture):
        self.base=base; self.condition=condition; self.architecture=architecture
        self.target=tuple(base.target); self.phase='initialize'
        self.park=getattr(base,'park',(.15,.55,1.8))

    def __getattr__(self,name): return getattr(self.base,name)

    def set_task_phase(self,phase):
        self.phase=phase
        if hasattr(self.base,'set_task_phase'): self.base.set_task_phase(phase)

    def command(self,target):
        self.target=tuple(target)
        offset=(0.,0.,0.) if self.phase in ('initialize','park') else self.condition['calibration_offset_m']
        shifted=[v+d for v,d in zip(target,offset)]
        # Saturate only at the existing Cartesian travel, never the error test.
        xlimit=.2 if self.architecture=='B' else .21
        bounds=((-xlimit,xlimit),(.425,.55),(1.1,1.8))
        shifted=[min(hi,max(lo,v)) for v,(lo,hi) in zip(shifted,bounds)]
        self.base.command(shifted)

    def tcp(self): return self.base.tcp()

    def error(self): return max(abs(a-b) for a,b in zip(self.tcp(),self.target))


def varied_task_class(task_class):
    class VariedTask(task_class):
        def __init__(self,*args,condition,**kwargs):
            self.condition=condition
            super().__init__(*args,**kwargs)

        def enter(self,phase,target,duration):
            if phase in ('approach','align'):
                duration*=self.condition['approach_time_scale']
            return super().enter(phase,target,duration)
    return VariedTask
