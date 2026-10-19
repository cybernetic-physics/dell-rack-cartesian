"""Passive motor-coordinate holding brakes, SI units; no active pose servo.

BCD42-envelope candidate: .4 Nm static holding torque,30 ms engagement,
50 ms release. Dynamic friction capacity, mounting compliance and damping
are explicit modeling assumptions, NOT a manufacturer stopping rating.
The anchor is internal friction memory, never a robot/plug position command.
"""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class BrakeParameters:
    torque_cap_nm: float=.4
    engagement_delay_s: float=.030
    release_delay_s: float=.050
    backlash_rad: float=math.radians(1.) # Conservative total play for spec <1°.
    stiffness_nm_rad: float=.06
    damping_nms_rad: float=.0008

    def __post_init__(self):
        values=(self.torque_cap_nm,self.engagement_delay_s,self.release_delay_s,
                self.backlash_rad,self.stiffness_nm_rad,self.damping_nms_rad)
        if not all(math.isfinite(v) and v>=0 for v in values) or min(self.torque_cap_nm,self.stiffness_nm_rad)<=0:
            raise ValueError('Invalid brake parameters')


class PassiveBrake:
    def __init__(self,parameters=None):
        self.parameters=parameters or BrakeParameters()
        self.engaged=False; self.request_release=True; self.elapsed=0.
        self.anchor=None; self.plastic_dissipation_j=0.

    def step(self,theta,omega,dt,release):
        p=self.parameters
        if not all(math.isfinite(v) for v in (theta,omega,dt)) or dt<=0:
            raise ValueError('Finite brake state and positive timestep required')
        release=bool(release)
        if release!=self.request_release:
            self.request_release=release; self.elapsed=0.
        self.elapsed+=dt
        if not release and not self.engaged and self.elapsed+1e-12>=p.engagement_delay_s:
            self.engaged=True; self.anchor=theta
        elif release and self.engaged and self.elapsed+1e-12>=p.release_delay_s:
            self.engaged=False; self.anchor=None
        if not self.engaged:
            return {'engaged':False,'torque_nm':0.,'spring_torque_nm':0.,
                    'damping_torque_nm':0.,'elastic_energy_j':0.,'slip_rad':0.,
                    'plastic_dissipation_j':self.plastic_dissipation_j}
        displacement=theta-self.anchor
        elastic=math.copysign(max(0.,abs(displacement)-p.backlash_rad/2),displacement)
        yield_angle=p.torque_cap_nm/p.stiffness_nm_rad
        slip=max(0.,abs(elastic)-yield_angle)
        if slip:
            self.anchor+=math.copysign(slip,elastic)
            elastic=math.copysign(yield_angle,elastic)
            self.plastic_dissipation_j+=slip*p.torque_cap_nm
        spring=-p.stiffness_nm_rad*elastic
        # Reserve the remaining torque budget for a strictly dissipative damper.
        budget=max(0.,p.torque_cap_nm-abs(spring))
        damping=max(-budget,min(budget,-p.damping_nms_rad*omega))
        return {'engaged':True,'torque_nm':spring+damping,'spring_torque_nm':spring,
                'damping_torque_nm':damping,'elastic_energy_j':.5*p.stiffness_nm_rad*elastic**2,
                'slip_rad':slip,'plastic_dissipation_j':self.plastic_dissipation_j}


class BrakeBank:
    """Virtual-work mapping from motor torques to real prismatic joint efforts."""
    def __init__(self,architecture):
        screw=2*math.pi/.008
        belt=1/(20*.002/(2*math.pi))
        if architecture=='A':
            self.joints=('Lift',); self.jacobian=((screw,),(screw,))
            parameters=BrakeParameters(stiffness_nm_rad=.03,damping_nms_rad=.0004)
        elif architecture=='B':
            self.joints=('Lift',); self.jacobian=((screw,),)
            parameters=BrakeParameters()
        elif architecture=='C':
            self.joints=('Traverse','Lift'); self.jacobian=((belt,belt),(belt,-belt))
            parameters=BrakeParameters(stiffness_nm_rad=.4,damping_nms_rad=.004)
        else: raise ValueError('Unknown brake architecture')
        self.brakes=[PassiveBrake(parameters) for _ in self.jacobian]

    def step(self,position,velocity,dt,release=True):
        if len(position)!=len(self.joints) or len(velocity)!=len(self.joints):
            raise ValueError('Wrong brake joint vector')
        commands=[release]*len(self.brakes) if isinstance(release,bool) else list(release)
        if len(commands)!=len(self.brakes): raise ValueError('Wrong brake command vector')
        theta=[sum(a*b for a,b in zip(row,position)) for row in self.jacobian]
        omega=[sum(a*b for a,b in zip(row,velocity)) for row in self.jacobian]
        motors=[brake.step(q,v,dt,r) for brake,q,v,r in zip(self.brakes,theta,omega,commands)]
        effort=[sum(row[i]*motor['torque_nm'] for row,motor in zip(self.jacobian,motors))
                for i in range(len(self.joints))]
        return {'motor_angle_rad':theta,'motor_speed_rad_s':omega,'motors':motors,
                'joint_effort_n':effort,'joint_power_w':sum(f*v for f,v in zip(effort,velocity)),
                'motor_power_w':sum(m['torque_nm']*v for m,v in zip(motors,omega))}
