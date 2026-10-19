"""Acceptance checks use measured simulated poses; commands alone never imply success."""
import math
from .config import CFG

def validate(interaction,cable,move,step,capture,cycles,record):
    checks=[]
    def check(name,ok,**evidence):
        checks.append({'name':name,'passed':bool(ok),**evidence})
        print('CHECK',checks[-1],flush=True)
    # First push with lateral error: plug must contact the rim, not reach the target.
    move((.006,.045,0)); move((.006,.0002,0),2); step(120)
    check('misaligned_insertion_rejected',interaction.state!='retained' and interaction.metrics['depth_m']<.003,**interaction.metrics)
    capture('misaligned')
    move((.006,.05,0)); move((0,.05,0))
    # Keyed orientation rejects an inverted connector.
    move((0,.05,0),angles=(0,180,0)); step(120)
    move((0,.0002,0),2,angles=(0,180,0)); step(120)
    check('inverted_insertion_rejected',interaction.state!='retained' and interaction.metrics['depth_m']<.003,**interaction.metrics)
    move((0,.05,0),angles=(0,180,0)); move((0,.05,0),angles=(0,0,0)); step(240)
    for cycle in range(cycles):
        if cycle==0: record(True)
        interaction.release(False)
        move((0,.0002,0),2); step(240)
        check(f'cycle_{cycle+1}_seated',interaction.state=='retained',**interaction.metrics)
        capture(f'cycle-{cycle+1}-seated')
        p,_=interaction.pose()
        move((0,.05,0),1); step(240)
        q,_=interaction.pose(); drift=(q-p).GetLength()
        check(f'cycle_{cycle+1}_retention',interaction.state=='retained' and drift<.0005,drift_m=drift,pull_limit_n=CFG.drive_max_force)
        # Remove pull load before releasing; then extract with bounded force.
        move((0,.0002,0),.5); interaction.release(True)
        step(120)
        check(f'cycle_{cycle+1}_clip_release',interaction.state=='released' and interaction.metrics['hook_clear'])
        move((0,.05,0),2); step(120)
        check(f'cycle_{cycle+1}_removed',interaction.state=='unplugged' and interaction.metrics['depth_m']<-.02,**interaction.metrics)
        capture(f'cycle-{cycle+1}-removed')
        if cycle==0: record(False)
    check('repeat_count',interaction.cycles==cycles,actual=interaction.cycles,expected=cycles)
    check('cable_joints_remain_attached',math.isfinite(cable.max_gap) and cable.max_gap<.0015,max_joint_gap_m=cable.max_gap,worst=cable.worst)
    return {'passed':all(c['passed'] for c in checks),'checks':checks,'events':interaction.events,
            'approximations':['spring-hinge latch and socket lip retain through contact; a force-limited pad physically releases the clip',
                              'rigid-link latch compliance, not FEM, calibrated plastic deformation or fracture',
                              'cable uses a discrete capsule/D6 chain; no electrical or material failure model',
                              'hand manipulation uses force-limited spring drives; no robot arm'],
            'physics_dt':CFG.physics_dt}
