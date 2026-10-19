import ast
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

from rack_robotics.benchmarking.physical_controls import PROTOCOL,connector_impulses,summarize,task_class,validate_request
from rack_robotics.benchmarking.spec import control
from rack_robotics.scripts.screen_physical_controls import LEGACY_FAST_SHUTDOWN_RUNNER,process_exit_policy,verify_case


class Value:
    def __init__(self,value): self.value=value
    def Get(self): return self.value
    def Set(self,value): self.value=value


class BaseTask:
    def __init__(self):
        self.time=0.;self.done=False;self.error=None
        self.robot=SimpleNamespace(target=(0.,.49,1.),tcp=lambda:(0.,.49,1.))
        self.commands=[]
        self.gripper=SimpleNamespace(aperture=lambda:.016,
            grasp=lambda v:self.commands.append(('grasp',v)),press_latch=lambda v:self.commands.append(('latch',v)))
        self.observer=SimpleNamespace(pose=lambda:((0.,.49,1.),None),metrics={'depth_m':-.04,'hook_clear':True})
        self.robot.command=lambda p:self.commands.append(('target',p))
    def enter(self,phase,target,duration):
        self.phase=phase;self.target=tuple(target);self.start=self.robot.target;self.duration=duration;self.elapsed=0.
    def tick(self,dt):self.commands.append(('base_tick',dt))
    def fail(self,message):self.error=message;self.done=True


class PhysicalControlsTest(unittest.TestCase):
    def test_process_exit_policy_never_promotes_failed_diagnostic(self):
        for digest in ('future-runner',LEGACY_FAST_SHUTDOWN_RUNNER):
            for code,passed in ((0,True),(1,False)):
                self.assertEqual(process_exit_policy(code,passed,digest),'exit_matches_diagnostic')
        self.assertEqual(process_exit_policy(0,False,LEGACY_FAST_SHUTDOWN_RUNNER),
                         'legacy_fast_shutdown_zero_on_failed_diagnostic')
        for code,passed,digest in ((0,False,'unknown'),(1,True,LEGACY_FAST_SHUTDOWN_RUNNER),
                (-9,False,LEGACY_FAST_SHUTDOWN_RUNNER),(None,False,LEGACY_FAST_SHUTDOWN_RUNNER),
                (True,False,LEGACY_FAST_SHUTDOWN_RUNNER),(0,None,LEGACY_FAST_SHUTDOWN_RUNNER)):
            with self.assertRaises(ValueError):process_exit_policy(code,passed,digest)

    def test_runner_delivers_verdict_before_fast_shutdown(self):
        path=Path(__file__).resolve().parents[1]/'rack_robotics/scripts/run_benchmark_trial.py'
        tree=ast.parse(path.read_text())
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
               and isinstance(n.func.value,ast.Name) and n.func.value.id=='app' and n.func.attr=='close']
        self.assertEqual(len(calls),1)
        supplied={k.arg:k.value for k in calls[0].keywords}['exit_code']
        for verdict,expected in ((True,0),(False,1)):
            expression=ast.Expression(body=supplied)
            self.assertEqual(eval(compile(expression,str(path),'eval'),{'verdict':verdict}),expected)
        assignments=[n for n in ast.walk(tree) if isinstance(n,ast.Assign)
                     and any(isinstance(t,ast.Name) and t.id=='verdict' for t in n.targets)]
        self.assertEqual(len(assignments),1)
        self.assertLess(assignments[0].lineno,calls[0].lineno)

    def test_reference_runner_passes_failure_status_inside_close(self):
        path=Path(__file__).resolve().parents[1]/'rack_robotics/scripts/run_reference.py'
        tree=ast.parse(path.read_text());final=tree.body[-1].finalbody
        for report,error,expected in (({'passed':True},None,0),({'passed':False},None,1),
                                      ({},None,1),({'passed':True},ValueError,1)):
            codes=[]
            env={'report':report,'sys':SimpleNamespace(exc_info=lambda:(error,None,None)),
                 'app':SimpleNamespace(close=lambda **kw:codes.append(kw['exit_code']))}
            exec(compile(ast.Module(body=final,type_ignores=[]),str(path),'exec'),env)
            self.assertEqual(codes,[expected])

    def task(self,mode):
        cap=Value(8.)
        drives={'y':SimpleNamespace(GetMaxForceAttr=lambda:cap)}
        return task_class(BaseTask,mode,drives)(),cap

    def test_pull_transition_retracts_before_physics_and_caps_only_axis(self):
        task,cap=self.task('unpressed_pull');task.enter('release_latch',(0.,.49,1.),.7)
        self.assertEqual(task.commands,[('latch',False)])
        self.assertEqual(cap.Get(),5.)
        self.assertEqual(task.phase,'challenge_pull');self.assertEqual(task.target,(0.,.5,1.))
        for _ in range(16):task.tick(.1)
        self.assertTrue(task.done);self.assertTrue(task.challenge_completed)
        self.assertEqual(task.commands[-1],('target',[0.,.5,1.]))

    def test_open_transport_begins_only_after_normal_extraction(self):
        task,cap=self.task('open_transport');task.enter('withdraw',(0.,.49,1.),2.5)
        self.assertEqual(task.phase,'withdraw');self.assertEqual(task.commands,[])
        task.tick(.002);self.assertEqual(task.commands,[('base_tick',.002)])
        task.enter('separate',(0.,.51,1.),1.2)
        self.assertEqual(task.phase,'challenge_open');self.assertEqual(cap.Get(),8.)
        self.assertEqual(task.commands[-2:],[('grasp',False),('latch',False)])
        task.tick(.7);self.assertEqual(task.phase,'challenge_transport')
        self.assertAlmostEqual(task.target[1],.53)

    def test_nominal_does_not_change_commands_or_force_cap(self):
        task,cap=self.task('nominal');task.enter('release_latch',(0.,.49,1.),.7);task.tick(.01)
        self.assertEqual(task.phase,'release_latch');self.assertEqual(task.commands,[('base_tick',.01)])
        self.assertEqual(cap.Get(),8.)

    def test_full_impulses_keep_friction_and_actor_order(self):
        rows=[{'actors':['/World/Plug','/World/Robot/LeftJaw'],
               'normal_impulse_actor0_ns':[1.,0.,0.],'friction_impulse_actor0_ns':[0.,.1,0.]},
              {'actors':['/World/PortRow/Port01','/World/Latch'],
               'normal_impulse_actor0_ns':[0.,.2,0.],'friction_impulse_actor0_ns':[0.,.03,0.]}]
        totals=connector_impulses(rows)
        self.assertEqual(totals['tool'],[1.,.1,0.]);self.assertAlmostEqual(totals['socket'][1],-.23)

    def evidence(self,mode='unpressed_pull'):
        result=dict(physics_dt=.01,timed_trial_started=True,initial_retained_without_hand=True,
            topology_audit={'passed':True},service_carrier_checks={'ok':True},physical_contact_reporting_errors=[],
            randomized_reliability_sample=False,passed=False,full_cycle_attempted=False,
            physical_challenge_completed=True,
            physical_challenge_reference={'plug_position_m':[0.,.4,1.],'tcp_m':[0.,.4,1.],'depth_m':-.04},
            physical_transport_reference={'plug_position_m':[0.,.4,1.],'tcp_m':[0.,.4,1.]})
        rows=[]
        for i in range(150 if mode=='unpressed_pull' else 200):
            rows.append(dict(time_s=(i+1)*.01,phase='challenge_pull',plug_position_m=[0.,.4,1.],
                tcp_m=[0.,.4,1.],target_m=[0.,.41,1.],aperture_m=.012,depth_m=.0108,
                latch_target_m=0.,y_force_cap_n=5.,helpers_disabled=True,hook_clear=False,retained=True,
                contacts=[{'actors':['/World/Plug','/World/Robot/LeftJaw'],
                           'normal_impulse_actor0_ns':[0.,0.,0.],'friction_impulse_actor0_ns':[0.,.01,0.]},
                          {'actors':['/World/Latch','/World/PortRow/Port01'],
                           'normal_impulse_actor0_ns':[0.,-.01,0.],'friction_impulse_actor0_ns':[0.,0.,0.]}]))
        if mode=='open_transport':
            for r in rows:r.update(phase='challenge_transport',tcp_m=[0.,.44,1.],target_m=[0.,.44,1.],
                                  aperture_m=.016,depth_m=-.04,contacts=[],y_force_cap_n=8.)
        prior=copy.deepcopy(rows[0]);prior.update(phase='grasp' if mode=='unpressed_pull' else 'withdraw',
            tcp_m=[0.,.4,1.],target_m=[0.,.4,1.],aperture_m=.012,y_force_cap_n=8.)
        def reference(row,time):
            return {**{k:row[k] for k in ('plug_position_m','tcp_m','depth_m','hook_clear','aperture_m')},
                    'time_s':time,'original_y_force_cap_n':row['y_force_cap_n']}
        result['physical_challenge_reference']=reference(prior,.02)
        if mode=='open_transport':
            opened=copy.deepcopy(prior);opened.update(phase='challenge_open',aperture_m=.016)
            result['physical_transport_reference']=reference(opened,.72)
            rows=[prior]+[copy.deepcopy(opened) for _ in range(70)]+rows
        else:rows=[prior]+rows
        for i,row in enumerate(rows):row['time_s']=(i+1)*.01
        return rows,result

    def test_real_pull_required_not_just_command_or_retention(self):
        rows,result=self.evidence();self.assertTrue(summarize('unpressed_pull',rows,result)['passed'])
        for field,value in [('contacts',[]),('latch_target_m',.003),('hook_clear',True),('depth_m',0.),
                            ('target_m',[0.,.4,1.]),('y_force_cap_n',8.),('helpers_disabled',False)]:
            changed=copy.deepcopy(rows)
            for row in changed:row[field]=value
            self.assertFalse(summarize('unpressed_pull',changed,result)['passed'],field)

    def test_open_tool_must_move_without_socket_retention_or_housing_transport(self):
        rows,result=self.evidence('open_transport');self.assertTrue(summarize('open_transport',rows,result)['passed'])
        for field,value in [('tcp_m',[0.,.4,1.]),('plug_position_m',[0.,.44,1.]),('aperture_m',.012),('depth_m',.01)]:
            changed=copy.deepcopy(rows)
            for row in changed:row[field]=value
            self.assertFalse(summarize('open_transport',changed,result)['passed'],field)

    def test_request_is_separate_from_other_protocols(self):
        validate_request('unpressed_pull','control',1,False,None,False,None)
        args=['unpressed_pull','control',1,False,None,False,None]
        for i,v in [(0,'bad'),(1,'randomized'),(2,3),(3,True),(4,5.),(5,True),(6,'nominal')]:
            bad=list(args);bad[i]=v
            with self.assertRaises(ValueError):validate_request(*bad)

    def test_verifier_recomputes_trace_and_rejects_changed_source(self):
        rows,result=self.evidence()
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);source=root/'source.py';source.write_text('# fixture')
            sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
            (root/'source_manifest.json').write_text(json.dumps({'source.py':sha(source)}))
            (root/'contacts.json').write_text(json.dumps({'reporting_errors':[]}))
            with gzip.open(root/'physical_trace.jsonl.gz','wt') as f:
                for row in rows:f.write(json.dumps(row)+'\n')
            result.update(environment_manifest_sha256='env',condition=control(),runner='physical_challenge_diagnostic_v1',
                          physical_control='unpressed_pull',physical_protocol=PROTOCOL)
            result['physical_challenge']={**summarize('unpressed_pull',rows,result),'trace_sha256':sha(root/'physical_trace.jsonl.gz')}
            (root/'results.json').write_text(json.dumps(result))
            self.assertTrue(verify_case(root,'env','unpressed_pull')['diagnostic_passed'])
            source.write_text('# changed')
            with self.assertRaises(ValueError):verify_case(root,'env','unpressed_pull')


if __name__=='__main__':unittest.main()
