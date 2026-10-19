"""Physics-step adapter: passive brake torques, never positions or velocities.

All robot joint drive gains are zeroed on loss of motor power. CoreXZ's
external motor/feedforward efforts are independently disabled. Efforts are
summed in joint coordinates so the transmission cannot overwrite the brakes.
"""
from rack_robotics.brakes import BrakeBank


class BrakeRuntime:
    def __init__(self,stage,drives,architecture,transmission=None):
        import numpy as np
        from isaacsim.core.prims import SingleArticulation
        self.np=np; self.bank=BrakeBank(architecture); self.drives=drives
        self.transmission=transmission; self.powered=True; self.latest={}
        self.articulation=(transmission.articulation if transmission else
                           SingleArticulation(prim_path='/World/Robot',name='brake_probe'))
        if not transmission: self.articulation.initialize()
        self.indices=np.array([self.articulation.get_dof_index(n) for n in self.bank.joints])
        self.original_gains={n:(d.GetStiffnessAttr().Get(),d.GetDampingAttr().Get()) for n,d in drives.items()}

    def power(self,enabled):
        self.powered=bool(enabled)
        for name,drive in self.drives.items():
            k,d=self.original_gains[name] if enabled else (0.,0.)
            drive.GetStiffnessAttr().Set(k);drive.GetDampingAttr().Set(d)
        if self.transmission: self.transmission.enabled=(bool(enabled),bool(enabled))

    def state(self):
        return (self.articulation.get_joint_positions(joint_indices=self.indices).tolist(),
                self.articulation.get_joint_velocities(joint_indices=self.indices).tolist())

    def step(self,dt,release=True,x_force_limit_n=None):
        q,v=self.state()
        passive=self.bank.step(q,v,dt,release)
        motor=[0.]*len(q)
        if self.transmission:
            self.transmission.step(x_force_limit_n=x_force_limit_n)
            motor=list(self.transmission.latest['joint_force_n'])
        effort=[a+b for a,b in zip(passive['joint_effort_n'],motor)]
        self.articulation.set_joint_efforts(self.np.array(effort),joint_indices=self.indices)
        self.latest={'position_m':q,'velocity_m_s':v,'motor_power_enabled':self.powered,
                     'drive_gains':{n:[d.GetStiffnessAttr().Get(),d.GetDampingAttr().Get()] for n,d in self.drives.items()},
                     'external_motor_effort_n':motor,'applied_effort_n':effort,'brakes':passive}
        return self.latest
