import copy
import math
import unittest
from collections import Counter
from rack_robotics.benchmarking.spec import conditions,control,validate,cable_route,can_nudge_preseat
from rack_robotics.benchmarking.adapters import PerturbedRobot,varied_task_class,bind_transmission_step,construct


class BenchmarkConditionsTests(unittest.TestCase):
    def test_constructor_respects_saved_rate_and_rejects_incompatible_legacy(self):
        def modern(stage,drives,architecture,gripper,control_dt):
            return architecture,gripper,control_dt
        self.assertEqual(construct(modern,None,None,'C','A',1/480),('C','A',1/480))
        def old(stage,drives): return 'old'
        self.assertEqual(construct(old,None,None,'A','A'),'old')
        with self.assertRaises(ValueError): construct(old,None,None,'A','A',1/480)
        for dt in (0,-1,float('nan')):
            with self.assertRaises(ValueError): construct(modern,None,None,'C','A',dt)

    def test_legacy_transmission_signature_preserved_without_ignoring_force_cap(self):
        class Transmission:
            def step(self): return 'legacy-step'
        class Robot: pass
        robot=Robot(); step=bind_transmission_step(Transmission(),robot)
        self.assertEqual(step(),'legacy-step')
        robot.transverse_force_limit=5.
        with self.assertRaises(ValueError): step()

    def test_new_transmission_receives_each_live_force_limit(self):
        class Transmission:
            def step(self,x_force_limit_n=None): return x_force_limit_n
        class Robot: transverse_force_limit=None
        robot=Robot(); step=bind_transmission_step(Transmission(),robot)
        self.assertIsNone(step())
        robot.transverse_force_limit=5.
        self.assertEqual(step(),5.)

    def test_preseat_nudge_is_only_for_near_seated_aligned_lip_edge(self):
        m={'depth_m':.0108,'angle_deg':.5,'hook_behind_lip':False}
        self.assertTrue(can_nudge_preseat(m,(0,.0002,0),(0,0,0)))
        for change in ({'depth_m':.009},{'depth_m':.012},{'angle_deg':3},{'hook_behind_lip':True}):
            self.assertFalse(can_nudge_preseat(dict(m,**change),(0,.0002,0),(0,0,0)))
        self.assertFalse(can_nudge_preseat(m,(.001,.0002,0),(0,0,0)))

    def test_seed_is_repeatable_and_ports_balanced(self):
        a=conditions(20261017,10)
        self.assertEqual(a,conditions(20261017,10))
        self.assertNotEqual(a,conditions(20261018,10))
        self.assertEqual(Counter(v['port'] for v in a),{1:2,4:2,8:2,12:2,16:2})
        self.assertTrue(all(validate(v) for v in a))

    def test_twenty_trials_extend_the_same_first_ten(self):
        self.assertEqual(conditions(10,20)[:10],conditions(10,10))
        self.assertEqual(Counter(v['port'] for v in conditions(10,20)),{1:4,4:4,8:4,12:4,16:4})

    def test_explicit_bounds_reject_uncontrolled_changes(self):
        for key,value in [('friction_scale',0),('port',2),('calibration_offset_m',[0,.001,0]),
                          ('connector_angles_deg',[float('nan'),0,0]),('initial_robot_offset_m',[0,0,.001])]:
            row=copy.deepcopy(conditions(10)[0]); row[key]=value
            with self.assertRaises(ValueError): validate(row)
        with self.assertRaises(ValueError): conditions(10,9)
        with self.assertRaises(ValueError): validate(dict(control(),friction_scale=.9))

    def test_cable_endpoints_remain_coincident_and_orientations_unit(self):
        origin=(.1,.5,1.6)
        for yaw in (-12,0,12):
            previous=origin
            route=cable_route(origin,yaw,5)
            self.assertEqual(len(route),36)
            for row in route:
                start=[p-d*.015/2 for p,d in zip(row['position'],row['direction'])]
                self.assertLess(math.dist(start,previous),1e-12)
                self.assertAlmostEqual(math.dist(previous,row['end']),.015)
                self.assertAlmostEqual(sum(q*q for q in row['quaternion']),1.)
                # Quaternion rotation of local +Y must equal capsule direction.
                w,x,y,z=row['quaternion']
                rotated=(2*(x*y-z*w),1-2*(x*x+z*z),2*(y*z+x*w))
                self.assertLess(math.dist(rotated,row['direction']),1e-12)
                previous=row['end']

    def test_command_bias_is_real_and_not_hidden_in_error(self):
        class Base:
            target=(.15,.55,1.8)
            def command(self,p): self.target=tuple(p)
            def tcp(self): return self.target
        condition=control(); condition['calibration_offset_m']=[.0001,0,-.0001]
        base=Base(); robot=PerturbedRobot(base,condition,'A')
        robot.set_task_phase('grasp'); robot.command((.1,.45,1.6))
        self.assertAlmostEqual(robot.error(),.0001)
        self.assertEqual(robot.target,(.1,.45,1.6))
        robot.set_task_phase('park'); robot.command((.15,.55,1.8))
        self.assertEqual(robot.error(),0)

    def test_approach_scale_does_not_shorten_latch_dwell(self):
        class Task:
            def __init__(self): pass
            def enter(self,phase,target,duration): return duration
        varied=varied_task_class(Task)(condition=dict(control(),approach_time_scale=.85))
        self.assertAlmostEqual(varied.enter('approach',None,2),1.7)
        self.assertEqual(varied.enter('release_latch',None,.7),.7)
