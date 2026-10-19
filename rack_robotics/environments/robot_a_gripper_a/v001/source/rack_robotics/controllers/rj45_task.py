"""Measured-state task controller, shared across interchangeable tool interfaces.

First feasibility version. Pose feedback is simulator ground truth (not vision).
Failures preserve their trajectory; bounded recovery is added after feasibility.
"""
import math


class RJ45Task:
    def __init__(self,robot,gripper,observer,port=0):
        self.robot=robot; self.gripper=gripper; self.observer=observer; self.port=port
        self.mouth=tuple(observer.ports[port][1])
        self.seat=(self.mouth[0],self.mouth[1]+.0002,self.mouth[2])
        self.clear=(self.mouth[0],.55,self.mouth[2])
        self.park=(.15,.55,1.80)
        self.phase='initialize'; self.elapsed=0.; self.time=0.
        self.events=[]; self.error=None; self.done=False; self.unplugged=False; self.replugged=False
        self.enter('initialize',self.park,.5)

    def enter(self,phase,target,duration):
        self.phase=phase; self.elapsed=0.; self.start=tuple(self.robot.target)
        self.target=tuple(target); self.duration=duration
        self.events.append({'time':self.time,'phase':phase,'target':self.target})
        print('ROBOT_PHASE',phase,flush=True)

    def fail(self,reason):
        self.error=reason; self.done=True
        print('ROBOT_FAILURE',self.phase,reason,flush=True)

    def tick(self,dt):
        if self.done: return
        self.elapsed+=dt; self.time+=dt
        u=min(1.,self.elapsed/self.duration); u=u*u*(3-2*u)
        self.robot.command([a+(b-a)*u for a,b in zip(self.start,self.target)])
        if self.elapsed<self.duration: return
        i=self.observer; m=i.metrics
        at_target=self.robot.error()<.0005
        if self.elapsed>self.duration+3:
            return self.fail(f'Timeout; robot error={self.robot.error():.6f}m; connector={i.state}; metrics={m}')
        if self.phase=='initialize':
            if i.connected_port!=self.port: return self.fail('Connector not initially latched')
            self.gripper.grasp(False); self.gripper.press_latch(False)
            self.enter('approach',self.clear,2)
        elif self.phase=='approach' and at_target:
            self.enter('align',self.seat,3)
        elif self.phase=='align' and at_target:
            self.gripper.grasp(True); self.enter('grasp',self.seat,.7)
        elif self.phase=='grasp':
            gap=self.gripper.aperture()
            if not .0105<gap<.013: return self.fail(f'Unexpected grasp aperture {gap}')
            self.gripper.press_latch(True)
            self.enter('release_latch',self.seat,.7)
        elif self.phase=='release_latch':
            if m.get('hook_clear'):
                self.enter('withdraw',(self.seat[0],self.seat[1]+.065,self.seat[2]),2.5)
        elif self.phase=='withdraw' and at_target:
            if m['depth_m']>-.035: return self.fail('Tool withdrew without the connector')
            p,_=i.pose()
            if math.dist(p,self.robot.tcp())>.002: return self.fail('Connector slipped in grasp')
            self.unplugged=True
            self.enter('separate',(self.seat[0]-.012,self.seat[1]+.080,self.seat[2]+.012),1.2)
        elif self.phase=='separate' and at_target:
            self.enter('realign',(self.seat[0],self.seat[1]+.065,self.seat[2]),1.2)
        elif self.phase=='realign' and at_target:
            self.enter('insert',self.seat,3.)
        elif self.phase=='insert' and at_target:
            if m['depth_m']>=.0103:
                self.gripper.press_latch(False)
                self.enter('seat_and_latch',self.seat,1.)
        elif self.phase=='seat_and_latch':
            if i.connected_port==self.port:
                self.replugged=True
                self.gripper.grasp(False); self.enter('release_gripper',self.seat,.7)
        elif self.phase=='release_gripper':
            if i.connected_port!=self.port: return self.fail('Retention lost when jaws opened')
            self.enter('retract',self.clear,3.)
        elif self.phase=='retract' and at_target:
            self.enter('park',self.park,2.)
        elif self.phase=='park' and at_target:
            if i.connected_port!=self.port: return self.fail('Connector did not remain seated')
            self.done=True
            print('ROBOT_CYCLE_PASS',flush=True)
