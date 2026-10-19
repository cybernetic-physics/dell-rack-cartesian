"""Measured-state task controller, shared across interchangeable tool interfaces.

Pose feedback is simulator ground truth (not vision). Recovery is bounded and
never bypasses physical hook clearance or attaches to the connector.
"""
import math


class RJ45Task:
    def __init__(self,robot,gripper,observer,port=0,max_retries=2):
        self.robot=robot; self.gripper=gripper; self.observer=observer; self.port=port
        self.mouth=tuple(observer.ports[port][1])
        self.seat=(self.mouth[0],self.mouth[1]+.0002,self.mouth[2])
        self.nominal_seat=self.seat
        self.approach_offset=tuple(getattr(gripper,'approach_offset',(0.,0.,0.)))
        self.grasp_duration=getattr(gripper,'grasp_duration',.7)
        self.release_duration=getattr(gripper,'release_duration',.7)
        self.clear=tuple(a+b for a,b in zip((self.mouth[0],.55,self.mouth[2]),self.approach_offset))
        self.park=getattr(robot,'park',(.15,.55,1.80))
        self.phase='initialize'; self.elapsed=0.; self.time=0.
        self.events=[]; self.error=None; self.done=False; self.unplugged=False; self.replugged=False
        self.max_retries=max_retries; self.retry_counts={}; self.recoveries=[]
        self.seating_nudges=0
        self.enter('initialize',self.park,.5)
        # Start the first trajectory at the measured, settled TCP. A compliant
        # tool's park target need not equal its authored initial flange pose.
        self.start=tuple(robot.tcp())

    def enter(self,phase,target,duration):
        self.phase=phase; self.elapsed=0.; self.start=tuple(self.robot.target)
        if hasattr(self.robot,'set_task_phase'): self.robot.set_task_phase(phase)
        self.target=tuple(target); self.duration=duration
        self.events.append({'time':self.time,'phase':phase,'target':self.target})
        print('ROBOT_PHASE',phase,flush=True)

    def fail(self,reason):
        self.error=reason; self.done=True
        print('ROBOT_FAILURE',self.phase,reason,flush=True)

    def recover(self,reason):
        """Recover only while retention or a physically plausible grasp exists."""
        key=self.phase
        if key in ('insert','seat_and_latch'): key='insertion'
        if self.retry_counts.get(key,0)>=self.max_retries: return self.fail(reason)
        if key not in ('grasp','release_latch','insertion'): return self.fail(reason)
        i=self.observer
        if key=='grasp' and i.connected_port!=self.port:
            return self.fail(reason+'; cannot retry grasp because connector retention is lost')
        if key=='insertion':
            p,_=i.pose()
            if math.dist(p,self.robot.tcp())>.002 or not .0105<self.gripper.aperture()<.013:
                return self.fail(reason+'; cannot retry insertion because grasp is not secure')
            if i.connected_port is not None and i.connected_port!=self.port:
                return self.fail(reason+'; unexpectedly retained in a different socket')
        self.retry_counts[key]=self.retry_counts.get(key,0)+1
        self.recoveries.append({'time':self.time,'failure_phase':self.phase,'reason':reason,
                                'attempt':self.retry_counts[key]})
        if key=='grasp':
            self.gripper.grasp(False); self.gripper.press_latch(False)
            self.enter('recover_grasp_open',self.robot.target,max(.5,self.release_duration))
        elif key=='release_latch':
            self.gripper.press_latch(False)
            self.enter('recover_latch_reset',self.robot.target,.5)
        else:
            self.gripper.press_latch(True)
            self.enter('recover_insert_release',self.robot.target,.7)

    def tick(self,dt):
        if self.done: return
        self.elapsed+=dt; self.time+=dt
        if hasattr(self.gripper,'step'): self.gripper.step(dt)
        u=min(1.,self.elapsed/self.duration); u=u*u*(3-2*u)
        self.robot.command([a+(b-a)*u for a,b in zip(self.start,self.target)])
        if self.elapsed<self.duration: return
        i=self.observer; m=i.metrics
        at_target=self.robot.error()<.0005
        seating_at_target=at_target
        if (not at_target and self.phase in ('seat_and_latch','seat_nudge')
                and getattr(self.gripper,'compliant_seating',False)):
            # A compliant wrist can be offset while the HELD housing itself is
            # aligned. Permit only the existing bounded axial seating nudge,
            # not general approach/grasp motion or a relaxed retention verdict.
            # The norm bound is stricter than the observer's per-axis 0.22 mm.
            tcp=self.robot.tcp()
            seating_at_target=(m.get('lateral_m',float('inf'))<.00022
                and m.get('lateral_m',-1)>=0
                and self.robot.error()<.0007
                and abs(tcp[1]-self.target[1])<.0005)
        if self.elapsed>self.duration+3:
            return self.recover(f'Timeout; robot error={self.robot.error():.6f}m; connector={i.state}; metrics={m}')
        if self.phase=='initialize':
            if i.connected_port!=self.port: return self.fail('Connector not initially latched')
            if getattr(self.gripper,'align_to_measured_housing',False):
                p,_=i.pose()
                if (any(not math.isfinite(v) or abs(v-n)>.001 for v,n in zip(p,self.nominal_seat))
                        or m.get('angle_deg',float('inf'))>2):
                    return self.fail('Initial measured housing outside bounded pickup alignment')
                # Ground-truth pose feedback, not perception. Align the tool
                # to the retained housing instead of assuming its centre is
                # exactly at the nominal socket centre. No body pose is set.
                self.seat=tuple(p)
            self.gripper.grasp(False); self.gripper.press_latch(False)
            self.enter('approach',self.clear,2)
        elif self.phase=='approach' and at_target:
            self.enter('align',tuple(a+b for a,b in zip(self.seat,self.approach_offset)),3)
        elif self.phase=='align' and at_target:
            if any(self.approach_offset):
                self.enter('align_datum',self.seat,1.4)
            else:
                self.gripper.grasp(True); self.enter('grasp',self.seat,self.grasp_duration)
        elif self.phase=='align_datum':
            # A passive wrist may yield against the initially tilted housing.
            # Judge capture against the measured housing, not nominal socket Z.
            # Z stays inside the 0.8 mm guide lead-in; X permits a 1 mm gap to
            # the fixed datum shoe while the opposite jaw closes. Axial capture
            # remains within 0.5 mm. These are capture, not seating tolerances.
            p,_=i.pose()
            if (i.connected_port==self.port and self.robot.error()<.001
                    and all(abs(a-b)<limit for a,b,limit in
                            zip(p,self.robot.tcp(),(.001,.0005,.0007)))):
                self.gripper.grasp(True); self.enter('grasp',self.seat,self.grasp_duration)
        elif self.phase=='grasp':
            gap=self.gripper.aperture()
            if not .0105<gap<.013: return self.recover(f'Unexpected grasp aperture {gap}')
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
            self.seat=self.nominal_seat
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
                self.gripper.grasp(False); self.enter('release_gripper',self.seat,self.release_duration)
            elif self.elapsed>1.3 and self.seating_nudges<2 and seating_at_target:
                # A released hook can rest on the lip edge despite sufficient
                # insertion depth. Advance the held connector by a bounded
                # 0.15 mm with the same force-limited axis; never move the latch.
                p,_=i.pose()
                if (i.connected_port is None and .0103<=m.get('depth_m',0)<.0115 and m.get('angle_deg',180)<2
                        and not m.get('hook_behind_lip',False)
                        and math.dist(p,self.robot.tcp())<.002
                        and .0105<self.gripper.aperture()<.013):
                    self.seating_nudges+=1
                    self.seat=(self.seat[0],self.seat[1]-.00015,self.seat[2])
                    self.enter('seat_nudge',self.seat,.6)
        elif self.phase=='seat_nudge' and seating_at_target:
            self.enter('seat_and_latch',self.seat,1.)
        elif self.phase=='release_gripper':
            if i.connected_port!=self.port: return self.fail('Retention lost when jaws opened')
            if any(self.approach_offset):
                self.enter('release_datum',tuple(a+b for a,b in zip(self.seat,self.approach_offset)),.7)
            else: self.enter('retract',self.clear,3.)
        elif self.phase=='release_datum' and at_target:
            if i.connected_port!=self.port: return self.fail('Retention lost while clearing fixed jaw')
            self.enter('retract',self.clear,3.)
        elif self.phase=='retract' and at_target:
            self.enter('park',self.park,2.)
        elif self.phase=='park' and at_target:
            if i.connected_port!=self.port: return self.fail('Connector did not remain seated')
            self.done=True
            print('ROBOT_CYCLE_PASS',flush=True)
        elif self.phase=='recover_grasp_open':
            if i.connected_port!=self.port: return self.fail('Retention lost during grasp recovery')
            if any(self.approach_offset):
                self.enter('recover_grasp_clear_datum',tuple(a+b for a,b in zip(self.seat,self.approach_offset)),.7)
            else: self.enter('recover_grasp_retreat',self.clear,2.)
        elif self.phase=='recover_grasp_clear_datum' and at_target:
            if i.connected_port!=self.port: return self.fail('Retention lost while clearing failed grasp')
            self.enter('recover_grasp_retreat',self.clear,2.)
        elif self.phase=='recover_grasp_retreat' and at_target:
            self.enter('align',tuple(a+b for a,b in zip(self.seat,self.approach_offset)),3.)
        elif self.phase=='recover_latch_reset':
            self.gripper.press_latch(True)
            self.enter('release_latch',self.robot.target,.7)
        elif self.phase=='recover_insert_release':
            if m.get('hook_clear'):
                p=self.robot.tcp()
                self.enter('recover_insert_retreat',(p[0],min(.55,p[1]+.065),p[2]),2.5)
        elif self.phase=='recover_insert_retreat' and at_target:
            p,_=i.pose()
            if m['depth_m']>-.025 or math.dist(p,self.robot.tcp())>.002:
                return self.fail('Insertion recovery did not withdraw a securely held connector')
            # Include static axis deflection as well as tool-to-plug offset.
            offset=[t-v for t,v in zip(self.robot.target,p)]
            if max(abs(v) for v in offset)>.0012:
                return self.fail('Measured grasp offset exceeds bounded alignment correction')
            self.seat=tuple(s+v for s,v in zip(self.nominal_seat,offset))
            self.enter('realign',(self.seat[0],self.seat[1]+.065,self.seat[2]),1.2)
