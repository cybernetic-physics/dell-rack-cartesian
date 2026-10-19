"""Measured-state-gated RJ45 handoff. Only spring-drive targets are commanded."""
from .config import CFG

class RowDemo:
    def __init__(self,interaction):
        self.i=interaction; self.running=False; self.repeat=False
        self.phase='idle'; self.error=None; self.destination=0; self.direction=1
        self.transfers=0

    def start(self,repeat=True,destination=None):
        self.repeat=repeat; self.error=None; self.running=True
        self.i.set_grasp(True)
        current=self.i.connected_port
        self.source=self.i.port_index
        self.destination=(self.next_port(current) if current is not None else self.source) if destination is None else destination
        if current==self.destination:
            self.enter('hold',self.i.port_target(current,.0002),1.2)
        elif current is not None:
            self.enter('unload',self.i.port_target(current,.0002),.5)
        else:
            self.i.release(True)
            self.enter('extract',self.i.port_target(self.source,.065),1.2)

    def next_port(self,current):
        result=current+self.direction
        if not 0<=result<len(self.i.ports):
            self.direction*=-1; result=current+self.direction
        return result

    def stop(self):
        self.running=False; self.phase='manual'
        if self.i.connected_port is not None:
            self.i.set_target(self.i.port_target(self.i.connected_port,.0002))

    def enter(self,phase,target,duration):
        self.phase=phase; self.elapsed=0.; self.start_target=list(self.i.target)
        self.end_target=target; self.duration=duration

    def tick(self,dt):
        if not self.running: return
        self.elapsed+=dt
        t=min(1,self.elapsed/self.duration); t=t*t*(3-2*t)
        self.i.set_target([a+(b-a)*t for a,b in zip(self.start_target,self.end_target)])
        if self.elapsed<self.duration: return
        if self.phase=='unload':
            self.i.release(True)
            self.enter('press',self.i.port_target(self.source,.0002),.35)
        elif self.phase=='press':
            if self.i.connected_port is None and self.i.metrics.get('hook_clear',False):
                self.enter('extract',self.i.port_target(self.source,.065),1.2)
        elif self.phase=='extract':
            if self.i.metrics['depth_m']<-.035:
                target=self.i.port_target(self.destination,.065)
                duration=max(1.,abs(target[0]-self.i.target[0])/.035)
                self.enter('traverse',target,duration)
        elif self.phase=='traverse':
            p,_=self.i.pose(); mouth=self.i.ports[self.destination][1]
            if abs(p[0]-mouth[0])<.0003 and self.i.metrics['depth_m']<-.035:
                self.i.release(False)
                self.enter('insert',self.i.port_target(self.destination,.0002),1.8)
        elif self.phase=='insert':
            if self.i.connected_port==self.destination:
                self.transfers+=1
                self.enter('hold',self.i.port_target(self.destination,.0002),1.2)
        elif self.phase=='hold':
            if self.i.connected_port!=self.destination: return self.fail('Lost retention during hold')
            self.enter('pull',self.i.port_target(self.destination,.03),.8)
        elif self.phase=='pull':
            if self.i.connected_port!=self.destination: return self.fail('Cable detached without clip release')
            if not self.repeat: return self.stop()
            self.source=self.destination; self.destination=self.next_port(self.source)
            self.enter('unload',self.i.port_target(self.source,.0002),.5)
        if self.elapsed>self.duration+3: self.fail('Timed out waiting for '+self.phase)

    def fail(self,message):
        self.error=message; self.running=False; self.phase='error'
        print('ROW_DEMO_ERROR',message,flush=True)

def validate_row(interaction,cable,move,step,capture,record):
    """Exercise every socket and the reverse edge; preserve one handoff video."""
    checks=[]
    def check(name,ok,**evidence):
        result={'name':name,'passed':bool(ok),**evidence}; checks.append(result)
        print('CHECK',result,flush=True)
    # Deliberate insertion into the divider between ports 1 and 2.
    middle=interaction.port_target(0,.0002); middle[0]-=.0125
    move([middle[0],.065,0]); move(middle,1.5); step(120)
    check('between_ports_rejected',interaction.connected_port is None and interaction.metrics['depth_m']<.003,**interaction.metrics)
    move([middle[0],.065,0]); move(interaction.port_target(0,.065))
    previous=None
    # Traverse the entire row, then prove a reverse handoff without scene reset.
    for index in [*range(len(interaction.ports)),len(interaction.ports)-2]:
        if previous==0: record(True)  # begins already plugged in port 1
        if previous is not None:
            interaction.release(True)
            step(120)  # A physical pad needs time to depress the spring-loaded clip.
            check(f'port_{previous+1}_clip_release_to_{index+1}',interaction.state=='released' and interaction.metrics['hook_clear'],**interaction.metrics)
            move(interaction.port_target(previous,.065),1.2); step(60)
            check(f'port_{previous+1}_extracted_to_{index+1}',interaction.connected_port is None and interaction.metrics['depth_m']<-.035)
        move(interaction.port_target(index,.065),1.2)
        check(f'clear_traverse_to_{index+1}',interaction.metrics['depth_m']<-.035 and interaction.connected_port is None)
        interaction.release(False)
        move(interaction.port_target(index,.0002),1.8); step(120)
        connected=[i for i,(path,_) in enumerate(interaction.ports)
                   if interaction.stage.GetPrimAtPath(path).GetAttribute('connector:connected').Get()]
        check(f'port_{index+1}_seated',interaction.connected_port==index,**interaction.metrics)
        check(f'port_{index+1}_hook_engaged',interaction.metrics['hook_behind_lip'],**interaction.metrics)
        check(f'port_{index+1}_exclusive_indicator',connected==[index],connected_ports=[i+1 for i in connected])
        p,_=interaction.pose(); move(interaction.port_target(index,.035),.7); step(120)
        q,_=interaction.pose()
        check(f'port_{index+1}_retention',interaction.connected_port==index and (q-p).GetLength()<.0005,
              drift_m=(q-p).GetLength(),pull_limit_n=CFG.drive_max_force)
        move(interaction.port_target(index,.0002),.4)
        if index in (0,1): capture(f'port-{index+1:02d}-seated')
        if previous==0: record(False)
        previous=index
    check('every_port_functional',len(interaction.visited_ports)==len(interaction.ports),
          ports_tested=[i+1 for i in sorted(interaction.visited_ports)])
    check('all_handoffs_counted',interaction.cycles==len(interaction.ports),actual=interaction.cycles)
    check('cable_joints_remain_attached',cable.max_gap<.0015,max_joint_gap_m=cable.max_gap,worst=cable.worst)
    return {'passed':all(c['passed'] for c in checks),'checks':checks,'events':interaction.events,
            'port_count':len(interaction.ports),'physics_dt':CFG.physics_dt,
            'approximations':['Retention comes from latch/socket collision, with a spring-loaded revolute clip and physical press pad; no socket retention joint.',
                              'Latch is a rigid-link compliance approximation inspired by Newton, not FEM or calibrated plastic deformation.',
                              'Functional means mechanical insertion/retention; no electrical network traffic is simulated.']}
