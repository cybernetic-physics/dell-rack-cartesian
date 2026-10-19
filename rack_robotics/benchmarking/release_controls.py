"""Matched open-command hold/move follow-up; campaign001 is not reclassified.

Both arms use identical physical extraction and two seconds of opening. The
transport request is delivered even if measured aperture remains insufficient;
that condition is a failed diagnostic, not a reason to skip the experiment.
"""
import gzip
import hashlib
import json
import math

from .physical_controls import PhysicalTrace as BaseTrace, task_class as base_task_class
from .physical_controls import summarize as base_summarize

MODES = ('released_hold', 'released_transport')
PROTOCOL = {'schema': 'matched_release_challenge_v1', 'open_settle_s': 2.,
            'transport_advance_m': .040, 'transport_ramp_s': 1.5, 'transport_hold_s': .5,
            'minimum_open_aperture_m': .013, 'minimum_tool_transport_m': .035,
            'maximum_hold_motion_m': .001, 'minimum_released_separation_m': .020,
            'maximum_matched_housing_difference_m': .001}


def validate_request(mode, role, cycles, occupied, load_threshold, force_trace, actuator_control):
    if (mode not in MODES or role != 'control' or cycles != 1 or occupied
            or load_threshold is not None or force_trace or actuator_control):
        raise ValueError('Matched release requires separate one-cycle nominal conditions')


def jaw_targets(drives):
    return {k: float(drives[k].GetTargetPositionAttr().Get()) for k in ('left','right','servo') if k in drives}


def task_class(base_class, mode, drives):
    if mode not in MODES: raise ValueError(mode)
    parent = base_task_class(base_class, 'nominal', drives)

    class ReleaseChallengeTask(parent):
        release_open_targets = None

        def enter(self, phase, target, duration):
            if phase == 'separate':
                self.challenge_reference = self.reference()
                self.gripper.grasp(False); self.gripper.press_latch(False)
                self.release_open_targets = jaw_targets(drives)
                return super().enter('challenge_open', self.robot.target, PROTOCOL['open_settle_s'])
            return super().enter(phase, target, duration)

        def tick(self, dt):
            if not self.phase.startswith('challenge_'): return super().tick(dt)
            if self.done: return
            self.elapsed += dt; self.time += dt
            if hasattr(self.gripper, 'step'): self.gripper.step(dt)
            u = min(1., self.elapsed/self.duration); u = u*u*(3-2*u)
            self.robot.command([a+(b-a)*u for a,b in zip(self.start,self.target)])
            if self.phase == 'challenge_open':
                if self.elapsed < self.duration: return
                self.transport_reference = self.reference()
                p = self.transport_reference['tcp_m']
                advance = PROTOCOL['transport_advance_m'] if mode == 'released_transport' else 0.
                if p[1]+advance > .55:
                    return self.fail('Matched release exceeds existing insertion workspace')
                # No aperture interlock: record an incomplete opening as FAIL,
                # but actually test the response to the bounded motion request.
                self.enter('challenge_transport', (p[0],p[1]+advance,p[2]), PROTOCOL['transport_ramp_s'])
            elif self.elapsed >= self.duration+PROTOCOL['transport_hold_s']:
                self.challenge_completed = True; self.done = True

    return ReleaseChallengeTask


def reference_matches(reference, samples, phase):
    index = next((i for i,s in enumerate(samples) if s['phase']==phase),0)
    if not reference or index<1: return False
    prior = samples[index-1]
    return (abs(reference['time_s']-samples[index]['time_s'])<1e-7
            and all(reference[k]==prior[k] for k in
                    ('plug_position_m','tcp_m','depth_m','hook_clear','aperture_m'))
            and reference['original_y_force_cap_n']==prior['y_force_cap_n'])


def summarize(mode, samples, result):
    if mode not in MODES: raise ValueError(mode)
    common = base_summarize('nominal', samples, result)['checks']
    checks = {k:v for k,v in common.items() if k not in ('full_cycle','full_sequence','final_retained')}
    dt = result['physics_dt']; reference = result.get('physical_challenge_reference')
    transport = result.get('physical_transport_reference')
    opened = [s for s in samples if s['phase']=='challenge_open']
    rows = [s for s in samples if s['phase']=='challenge_transport']
    targets = result.get('release_open_targets')
    advance = rows[-1]['tcp_m'][1]-transport['tcp_m'][1] if rows and transport else None
    separation = min((math.dist(s['plug_position_m'],s['tcp_m']) for s in rows),default=None)
    tool_rows = sum(any(a.startswith('/World/Robot/') for a in c['actors']) for s in rows for c in s['contacts'])
    max_hold_motion = max((math.dist(s['tcp_m'],transport['tcp_m']) for s in rows),default=None) if transport else None
    checks.update(challenge_finished=result.get('physical_challenge_completed') is True,
        finite_jaw_commands=bool(samples) and all(math.isfinite(v) for s in samples for v in s.get('jaw_drive_targets',{}).values()),
        not_claimed_full_cycle=result.get('passed') is False and result.get('full_cycle_attempted') is False,
        reference_recorded=reference_matches(reference,samples,'challenge_open'),
        transport_reference_recorded=reference_matches(transport,samples,'challenge_transport'),
        extracted_before_open=bool(reference) and reference['depth_m']<-.035,
        full_open_duration=PROTOCOL['open_settle_s']-dt<=len(opened)*dt<=PROTOCOL['open_settle_s']+2*dt,
        full_challenge_duration=2.-dt<=len(rows)*dt<=2.+2*dt,
        open_command_maintained=bool(targets) and bool(rows) and all(s.get('jaw_drive_targets')==targets for s in opened+rows),
        latch_command_retracted=bool(rows) and all(abs(s['latch_target_m'])<1e-12 for s in opened+rows),
        original_force_cap_preserved=bool(reference) and bool(rows) and all(s['y_force_cap_n']==reference['original_y_force_cap_n'] for s in opened+rows),
        socket_stays_clear=bool(rows) and all(s['depth_m']<-.025 for s in rows),
        jaws_physically_open=bool(rows) and all(s['aperture_m']>=PROTOCOL['minimum_open_aperture_m'] for s in rows),
        requested_motion_delivered=(advance is not None and advance>=PROTOCOL['minimum_tool_transport_m']
            if mode=='released_transport' else max_hold_motion is not None and max_hold_motion<=PROTOCOL['maximum_hold_motion_m']),
        housing_separated_from_tool=separation is not None and separation>=PROTOCOL['minimum_released_separation_m'],
        no_direct_tool_connector_contacts=bool(rows) and tool_rows==0)
    return {'schema':'matched_release_verdict_v1','mode':mode,'passed':all(checks.values()),
        'checks':checks,'sample_count':len(samples),'protocol':PROTOCOL,
        'metrics':{'open_duration_s':len(opened)*dt,'challenge_duration_s':len(rows)*dt,
                   'tool_advance_m':advance,'maximum_tool_displacement_m':max_hold_motion,
                   'minimum_housing_tool_separation_m':separation,'tool_connector_contact_rows':tool_rows,
                   'minimum_challenge_aperture_m':min((s['aperture_m'] for s in rows),default=None)},
        'scope':'Open-command matched follow-up; actual opening and separation separately gated; no hardware rating or randomized sample'}


def compare_pair(hold, moved):
    """Pair causality is evaluated only with identical pre-intervention evidence."""
    before = lambda rows: [s for s in rows if s['phase']!='challenge_transport']
    h = [s for s in hold if s['phase']=='challenge_transport']
    m = [s for s in moved if s['phase']=='challenge_transport']
    matched = bool(before(hold)) and before(hold)==before(moved)
    aligned = bool(h) and len(h)==len(m) and all(a['time_s']==b['time_s'] for a,b in zip(h,m))
    delta = max((math.dist(a['plug_position_m'],b['plug_position_m']) for a,b in zip(h,m)),default=None) if aligned else None
    return {'identical_pre_intervention_trace':matched,'aligned_challenge_samples':aligned,
            'maximum_matched_housing_difference_m':delta,
            'no_measurable_transport_effect':bool(matched and aligned and delta<=PROTOCOL['maximum_matched_housing_difference_m']),
            'scope':'Matched housing positions within1 mm over the bounded challenge, not proof of zero force or universal causality'}


class PhysicalTrace(BaseTrace):
    def sample(self, time, task, gripper, observer, robot, stage, drives):
        super().sample(time,task,gripper,observer,robot,stage,drives)
        self.samples[-1]['jaw_drive_targets'] = jaw_targets(drives)

    def close(self, mode, result):
        with gzip.open(self.path,'xt') as stream:
            for sample in self.samples: stream.write(json.dumps(sample,allow_nan=False)+'\n')
        return {**summarize(mode,self.samples,result),'trace_sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()}
