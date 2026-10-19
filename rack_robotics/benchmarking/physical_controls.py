"""Diagnostic-only physical challenges; commands actuators, never body poses.

Normal approach/grasp and (for open transport) extraction use the shared task.
The diagnostic then deliberately delivers a bounded motion request instead of
asking the normal task's interlock whether it would permit that request.
"""
import gzip
import hashlib
import json
import math

MODES = ('nominal', 'unpressed_pull', 'open_transport')
PROTOCOL = {'schema': 'physical_challenge_protocol_v1', 'pull_force_cap_n': 5.,
            'pull_target_advance_m': .010, 'pull_ramp_s': .5, 'pull_hold_s': 1.,
            'open_settle_s': .7, 'transport_advance_m': .040,
            'transport_ramp_s': 1.5, 'transport_hold_s': .5,
            'minimum_pull_contact_n': .5, 'minimum_pull_contact_duration_s': .2,
            'maximum_retained_axial_drift_m': .001,
            'minimum_open_aperture_m': .013, 'minimum_tool_transport_m': .035,
            'maximum_open_housing_forward_transport_m': .010,
            'minimum_final_axial_shortfall_m': .025}


def validate_request(mode, role, cycles, occupied, load_threshold, force_trace, actuator_control):
    if mode is not None and (mode not in MODES or role != 'control' or cycles != 1 or occupied
                            or load_threshold is not None or force_trace or actuator_control):
        raise ValueError('Physical challenges require a separate one-cycle nominal condition')


def task_class(base_class, mode, drives):
    """Nominal execution is unchanged; challenge transitions precede physics."""
    if mode not in MODES: raise ValueError(mode)

    class PhysicalChallengeTask(base_class):
        challenge_reference = None
        challenge_completed = False

        def reference(self):
            p, _ = self.observer.pose()
            return {'time_s': self.time, 'plug_position_m': list(p), 'tcp_m': list(self.robot.tcp()),
                    'depth_m': self.observer.metrics['depth_m'],
                    'hook_clear': self.observer.metrics['hook_clear'],
                    'aperture_m': self.gripper.aperture(),
                    'original_y_force_cap_n': drives['y'].GetMaxForceAttr().Get()}

        def enter(self, phase, target, duration):
            if mode == 'unpressed_pull' and phase == 'release_latch':
                # The base grasp transition requested pressing, but no physics
                # step has occurred. Retract before delivering the pull.
                self.gripper.press_latch(False)
                self.challenge_reference = self.reference()
                drives['y'].GetMaxForceAttr().Set(min(PROTOCOL['pull_force_cap_n'],
                    self.challenge_reference['original_y_force_cap_n']))
                p = self.challenge_reference['tcp_m']
                return super().enter('challenge_pull', (p[0], p[1]+PROTOCOL['pull_target_advance_m'], p[2]),
                                     PROTOCOL['pull_ramp_s'])
            if mode == 'open_transport' and phase == 'separate':
                # Base withdraw has already checked housing extraction AND a
                # secure measured grasp, so the socket cannot retain it here.
                self.challenge_reference = self.reference()
                self.gripper.grasp(False)
                self.gripper.press_latch(False)
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
                if self.gripper.aperture() < PROTOCOL['minimum_open_aperture_m']:
                    return self.fail('Physical challenge precondition: jaws did not open')
                self.transport_reference = self.reference()
                p = self.transport_reference['tcp_m']
                if p[1]+PROTOCOL['transport_advance_m'] > .55:
                    return self.fail('Physical challenge exceeds existing insertion workspace')
                self.enter('challenge_transport', (p[0],p[1]+PROTOCOL['transport_advance_m'],p[2]),
                           PROTOCOL['transport_ramp_s'])
            else:
                hold = PROTOCOL['pull_hold_s'] if self.phase == 'challenge_pull' else PROTOCOL['transport_hold_s']
                if self.elapsed >= self.duration+hold:
                    self.challenge_completed = True; self.done = True

    return PhysicalChallengeTask


def connector_impulses(rows):
    """Signed impulse on housing+latch, grouped by external contacting actor."""
    totals = {'tool': [0.,0.,0.], 'socket': [0.,0.,0.]}
    for row in rows:
        actors = row['actors']
        for index, actor in enumerate(actors):
            if actor not in ('/World/Plug','/World/Latch'): continue
            other = actors[1-index]
            group = 'tool' if other.startswith('/World/Robot/') else 'socket' if other.startswith('/World/PortRow/') else None
            if group is None: continue
            sign = 1. if index == 0 else -1.
            for axis in range(3):
                totals[group][axis] += sign*(row['normal_impulse_actor0_ns'][axis]+row['friction_impulse_actor0_ns'][axis])
    return totals


class ConnectorContacts:
    def __init__(self):
        from pxr import PhysicsSchemaTools
        from omni.physx import get_physx_simulation_interface
        self.decode = PhysicsSchemaTools.intToSdfPath
        self.errors = []; self.begin()
        self.subscription = get_physx_simulation_interface().subscribe_full_contact_report_events(self.on_contacts)

    def begin(self): self.rows = []

    def on_contacts(self, headers, data, anchors):
        try:
            for h in headers:
                actors = [str(self.decode(h.actor0)),str(self.decode(h.actor1))]
                if not any(p in ('/World/Plug','/World/Latch') for p in actors): continue
                if not any(p.startswith(('/World/Robot/','/World/PortRow/')) for p in actors): continue
                normal = [0.,0.,0.]; friction = [0.,0.,0.]
                for c in data[h.contact_data_offset:h.contact_data_offset+h.num_contact_data]:
                    normal = [a+float(b) for a,b in zip(normal,c.impulse)]
                for c in anchors[h.friction_anchors_offset:h.friction_anchors_offset+h.num_friction_anchors_data]:
                    friction = [a+float(b) for a,b in zip(friction,c.impulse)]
                self.rows.append({'actors':actors,'colliders':[str(self.decode(h.collider0)),str(self.decode(h.collider1))],
                    'normal_impulse_actor0_ns':normal,'friction_impulse_actor0_ns':friction})
        except Exception as error: self.errors.append(repr(error))


def summarize(mode, samples, result):
    if mode not in MODES: raise ValueError(mode)
    dt = result['physics_dt']; reference = result.get('physical_challenge_reference')
    phases = [s['phase'] for s in samples]
    finite = all(math.isfinite(v) for s in samples for v in
                 [s['time_s'],s['aperture_m'],s['depth_m'],s['latch_target_m'],s['y_force_cap_n'],
                  *s['plug_position_m'],*s['tcp_m'],*s['target_m']])
    finite_contacts = all(math.isfinite(v) for s in samples for row in s['contacts']
                          for v in row['normal_impulse_actor0_ns']+row['friction_impulse_actor0_ns'])
    checks = {'trial_started':result.get('timed_trial_started') is True,
        'initial_retained':result.get('initial_retained_without_hand') is True,
        'helpers_disabled':bool(samples) and all(s['helpers_disabled'] for s in samples),
        'finite_state':bool(samples) and finite and finite_contacts,
        'contiguous_steps':bool(samples) and all(abs(s['time_s']-(i+1)*dt)<1e-7 for i,s in enumerate(samples)),
        'topology_intact':result.get('topology_audit',{}).get('passed') is True,
        'carriers_intact':bool(result.get('service_carrier_checks')) and all(result['service_carrier_checks'].values()),
        'contact_reporting_valid':result.get('physical_contact_reporting_errors') == [],
        'no_exception':not result.get('failure_stage'),
        'not_randomized':result.get('randomized_reliability_sample') is False}
    metrics = {}
    def reference_matches(reference, phase):
        index = next((i for i,s in enumerate(samples) if s['phase']==phase),0)
        if not reference or index<1: return False
        prior=samples[index-1]
        return (abs(reference['time_s']-samples[index]['time_s'])<1e-7
                and all(reference[k]==prior[k] for k in
                        ('plug_position_m','tcp_m','depth_m','hook_clear','aperture_m'))
                and reference['original_y_force_cap_n']==prior['y_force_cap_n'])
    if mode == 'nominal':
        checks.update(full_cycle=result.get('passed') is True,
            full_sequence=all(p in phases for p in ('grasp','release_latch','withdraw','insert','release_gripper','park')),
            final_retained=bool(samples) and samples[-1]['retained'])
    else:
        checks.update(challenge_finished=result.get('physical_challenge_completed') is True,
                      not_claimed_full_cycle=result.get('passed') is False and result.get('full_cycle_attempted') is False,
                      reference_recorded=reference_matches(reference,
                          'challenge_pull' if mode=='unpressed_pull' else 'challenge_open'))
        rows = [s for s in samples if s['phase']==('challenge_pull' if mode=='unpressed_pull' else 'challenge_transport')]
        checks['challenge_observed'] = bool(rows)
        duration = (PROTOCOL['pull_ramp_s']+PROTOCOL['pull_hold_s'] if mode=='unpressed_pull'
                    else PROTOCOL['transport_ramp_s']+PROTOCOL['transport_hold_s'])
        checks['full_bounded_challenge_duration'] = duration-dt<=len(rows)*dt<=duration+2*dt
        metrics['challenge_duration_s'] = len(rows)*dt
        if mode == 'unpressed_pull':
            drift = max((abs(s['plug_position_m'][1]-reference['plug_position_m'][1]) for s in rows),default=None) if reference else None
            loaded = sum(connector_impulses(s['contacts'])['tool'][1]/dt >= PROTOCOL['minimum_pull_contact_n']
                         for s in rows)*dt
            opposed = sum(connector_impulses(s['contacts'])['socket'][1]/dt <= -.25 for s in rows)*dt
            metrics.update(maximum_absolute_axial_drift_m=drift,tool_pull_loaded_duration_s=loaded,
                           socket_opposing_duration_s=opposed)
            checks.update(pull_request_delivered=bool(rows) and bool(reference)
                          and rows[-1]['target_m'][1]-reference['tcp_m'][1] >= .0099,
                force_cap_bounded=bool(rows) and all(0<s['y_force_cap_n']<=5 for s in rows),
                actual_tool_pull_contact=loaded>=PROTOCOL['minimum_pull_contact_duration_s'],
                actual_socket_opposition=opposed>=PROTOCOL['minimum_pull_contact_duration_s'],
                grasp_maintained=bool(rows) and all(.0105<s['aperture_m']<.013 for s in rows),
                latch_unpressed=bool(rows) and all(abs(s['latch_target_m'])<1e-12 for s in rows),
                hook_blocked=bool(rows) and all(not s['hook_clear'] for s in rows),
                housing_retained=bool(rows) and all(s['depth_m']>=.0103 for s in rows),
                axial_drift_bounded=drift is not None and drift<PROTOCOL['maximum_retained_axial_drift_m'])
        else:
            transport = result.get('physical_transport_reference')
            advance = rows[-1]['tcp_m'][1]-transport['tcp_m'][1] if rows and transport else None
            housing = max((s['plug_position_m'][1]-transport['plug_position_m'][1] for s in rows),default=None) if transport else None
            shortfall = ((rows[-1]['tcp_m'][1]-transport['tcp_m'][1])
                         -(rows[-1]['plug_position_m'][1]-transport['plug_position_m'][1])) if rows and transport else None
            metrics.update(tool_advance_m=advance,maximum_housing_forward_advance_m=housing,final_axial_shortfall_m=shortfall)
            checks.update(extracted_before_open=bool(reference) and reference['depth_m']<-.035,
                transport_reference_recorded=reference_matches(transport,'challenge_transport'),
                socket_stays_clear=bool(rows) and all(s['depth_m']<-.025 for s in rows),
                jaws_stay_open=bool(rows) and all(s['aperture_m']>=PROTOCOL['minimum_open_aperture_m'] for s in rows),
                tool_physically_moves=advance is not None and advance>=PROTOCOL['minimum_tool_transport_m'],
                housing_not_carried_forward=housing is not None and housing<PROTOCOL['maximum_open_housing_forward_transport_m'],
                housing_does_not_follow=shortfall is not None and shortfall>=PROTOCOL['minimum_final_axial_shortfall_m'])
    return {'schema':'physical_challenge_verdict_v1','mode':mode,'passed':all(checks.values()),
            'checks':checks,'metrics':metrics,'sample_count':len(samples),'protocol':PROTOCOL,
            'scope':'Bounded simulated actuator/contact challenge, not a full-cycle task pass, hardware load rating or randomized trial'}


class PhysicalTrace:
    def __init__(self, path):
        self.path=path; self.samples=[]; self.contacts=ConnectorContacts()

    def before(self): self.contacts.begin()

    def sample(self, time, task, gripper, observer, robot, stage, drives):
        p,_=observer.pose()
        self.samples.append({'time_s':time,'phase':task.phase,'plug_position_m':list(p),
            'tcp_m':list(robot.tcp()),'target_m':list(robot.target),'aperture_m':gripper.aperture(),
            'depth_m':observer.metrics['depth_m'],'hook_clear':observer.metrics['hook_clear'],
            'retained':observer.connected_port==0 and observer.metrics.get('hook_behind_lip',False),
            'latch_target_m':drives['latch'].GetTargetPositionAttr().Get(),
            'y_force_cap_n':drives['y'].GetMaxForceAttr().Get(),'contacts':list(self.contacts.rows),
            'helpers_disabled':all(not stage.GetPrimAtPath(p).IsActive() for p in
                ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress'))})

    def close(self, mode, result):
        with gzip.open(self.path,'xt') as stream:
            for sample in self.samples: stream.write(json.dumps(sample,allow_nan=False)+'\n')
        return {**summarize(mode,self.samples,result),'trace_sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()}
