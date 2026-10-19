"""Task guards only; these mocks do not establish physical feasibility."""
import unittest
from types import SimpleNamespace
from rack_robotics.controllers.rj45_task import RJ45Task


class Robot:
    def __init__(self):
        self.target=(.15,.55,1.80)
    def command(self,target): self.target=tuple(target)
    def tcp(self): return self.target
    def error(self): return 0.


class Gripper:
    def __init__(self): self.closed=False; self.pressed=False; self.gap=.0117
    def grasp(self,value): self.closed=value
    def press_latch(self,value): self.pressed=value
    def aperture(self): return self.gap


class RobotTaskTests(unittest.TestCase):
    def test_measured_pickup_is_bounded_and_does_not_change_reinsertion_goal(self):
        self.gripper.align_to_measured_housing=True
        nominal=self.task.nominal_seat
        measured=(nominal[0],nominal[1]+.00001,nominal[2]-.0001)
        self.observer.pose=lambda:(measured,None)
        self.observer.metrics['angle_deg']=.1
        self.task.tick(.6)
        self.assertEqual(self.task.seat,measured)
        self.assertEqual(self.task.nominal_seat,nominal)
        self.task.enter('withdraw',(measured[0],measured[1]+.065,measured[2]),1.)
        self.observer.metrics['depth_m']=-.05
        self.observer.pose=lambda:(self.robot.tcp(),None)
        self.task.tick(1.1)
        self.assertTrue(self.task.unplugged)
        self.assertEqual(self.task.seat,nominal)

    def test_unbounded_measured_pickup_is_rejected(self):
        self.gripper.align_to_measured_housing=True
        self.observer.metrics['angle_deg']=.1
        self.observer.pose=lambda:((0,0,0),None)
        self.task.tick(.6)
        self.assertIn('outside bounded pickup',self.task.error)

    def test_task_steps_optional_actuator_setpoint_profile(self):
        steps=[]
        self.gripper.step=steps.append
        self.task.tick(.01)
        self.assertEqual(steps,[.01])
        self.task.done=True
        self.task.tick(.01)
        self.assertEqual(steps,[.01])

    def test_release_duration_comes_from_tool_interface(self):
        self.gripper.release_duration=1.8
        task=RJ45Task(self.robot,self.gripper,self.observer)
        task.enter('seat_and_latch',task.seat,1.)
        task.tick(1.1)
        self.assertEqual(task.phase,'release_gripper')
        self.assertEqual(task.duration,1.8)
        task.tick(.8)
        self.assertEqual(task.phase,'release_gripper')

    def test_initial_trajectory_starts_from_actual_tcp(self):
        self.robot.tcp=lambda:(.15,.55,1.799)
        task=RJ45Task(self.robot,self.gripper,self.observer)
        self.assertEqual(task.start,(.15,.55,1.799))
        self.assertEqual(task.target,task.park)

    def test_fixed_shoe_clearance_is_shared_interface(self):
        self.gripper.approach_offset=(-.002,0,0)
        task=RJ45Task(self.robot,self.gripper,self.observer)
        task.enter('approach',task.clear,.1); task.tick(.2)
        self.assertEqual(task.phase,'align')
        self.assertAlmostEqual(task.target[0],task.seat[0]-.002)
        task.tick(3.1)
        self.assertEqual(task.phase,'align_datum')
        self.assertFalse(self.gripper.closed)
        task.tick(1.5)
        self.assertTrue(self.gripper.closed)
        self.assertEqual(task.phase,'grasp')

    def test_shared_phase_policy_notifies_robot_before_motion(self):
        phases=[]
        self.robot.set_task_phase=phases.append
        self.task.enter('align_datum',self.task.seat,1.4)
        self.assertEqual(phases,['align_datum'])
        self.task.tick(1.5)
        self.assertEqual(phases,['align_datum','grasp'])

    def test_grasp_duration_comes_from_tool_interface(self):
        self.gripper.grasp_duration=1.4
        task=RJ45Task(self.robot,self.gripper,self.observer)
        task.enter('align_datum',task.seat,1.4)
        task.tick(1.5)
        self.assertEqual(task.duration,1.4)
        task.tick(.8)
        self.assertEqual(task.phase,'grasp')
        self.assertFalse(self.gripper.pressed)

    def test_datum_capture_uses_actual_housing_and_bounded_nominal_error(self):
        self.robot.error=lambda:.0007
        self.observer.pose=lambda:((self.robot.tcp()[0],self.robot.tcp()[1],self.robot.tcp()[2]-.00025),None)
        self.task.enter('align_datum',self.task.seat,1.4)
        self.task.tick(1.5)
        self.assertEqual(self.task.phase,'grasp')

    def test_datum_does_not_close_on_missing_or_displaced_housing(self):
        self.observer.pose=lambda:((0,0,0),None)
        self.task.enter('align_datum',self.task.seat,1.4)
        self.task.tick(1.5)
        self.assertEqual(self.task.phase,'align_datum')
        self.assertFalse(self.gripper.closed)

    def test_lip_edge_seating_nudge_is_bounded_and_measured(self):
        self.observer.connected_port=None
        self.observer.metrics.update(depth_m=.0108,angle_deg=.9,hook_behind_lip=False)
        self.task.enter('seat_and_latch',self.task.seat,1)
        for expected in range(1,3):
            before=self.task.seat[1]
            self.task.tick(1.4)
            self.assertEqual(self.task.phase,'seat_nudge')
            self.assertAlmostEqual(self.task.seat[1],before-.00015)
            self.assertEqual(self.task.seating_nudges,expected)
            self.task.tick(.7)
            self.assertEqual(self.task.phase,'seat_and_latch')
        self.task.tick(1.4)
        self.assertEqual(self.task.phase,'seat_and_latch')
        self.assertFalse(self.task.replugged)

    def test_no_seating_nudge_with_lost_grasp(self):
        self.observer.connected_port=None
        self.observer.metrics.update(depth_m=.0108,angle_deg=.9,hook_behind_lip=False)
        self.gripper.gap=.015
        self.task.enter('seat_and_latch',self.task.seat,1)
        self.task.tick(1.4)
        self.assertEqual(self.task.phase,'seat_and_latch')
        self.assertEqual(self.task.seating_nudges,0)

    def test_compliant_seating_uses_aligned_housing_without_claiming_success(self):
        self.gripper.compliant_seating=True
        self.observer.connected_port=None
        self.observer.metrics.update(depth_m=.0108,angle_deg=.9,hook_behind_lip=False,lateral_m=.00014)
        self.robot.error=lambda:.00056
        self.task.enter('seat_and_latch',self.task.seat,1.)
        self.task.tick(1.4)
        self.assertEqual(self.task.phase,'seat_nudge')
        self.assertFalse(self.task.replugged)
        self.task.tick(.7)
        self.assertEqual(self.task.phase,'seat_and_latch')
        self.assertFalse(self.task.replugged)

    def test_compliant_seating_rejects_missing_misaligned_or_excess_error(self):
        self.gripper.compliant_seating=True
        self.observer.connected_port=None
        self.observer.metrics.update(depth_m=.0108,angle_deg=.9,hook_behind_lip=False)
        self.robot.error=lambda:.00056
        self.task.enter('seat_and_latch',self.task.seat,1.)
        for lateral in (None,float('nan'),-.0001,.00023):
            if lateral is None:self.observer.metrics.pop('lateral_m',None)
            else:self.observer.metrics['lateral_m']=lateral
            self.task.elapsed=0
            self.task.tick(1.4)
            self.assertEqual(self.task.phase,'seat_and_latch')
        self.observer.metrics['lateral_m']=.00014
        self.robot.error=lambda:.00071
        self.task.elapsed=0;self.task.tick(1.4)
        self.assertEqual(self.task.phase,'seat_and_latch')

    def test_noncompliant_tool_keeps_original_target_gate(self):
        self.observer.connected_port=None
        self.observer.metrics.update(depth_m=.0108,angle_deg=.9,hook_behind_lip=False,lateral_m=.00014)
        self.robot.error=lambda:.00056
        self.task.enter('seat_and_latch',self.task.seat,1.)
        self.task.tick(1.4)
        self.assertEqual(self.task.phase,'seat_and_latch')

    def setUp(self):
        self.robot=Robot(); self.gripper=Gripper()
        self.observer=SimpleNamespace(ports=[('port',(-.1875,.429,1.66))],
            connected_port=0, state='retained', metrics={'depth_m':.0108,'hook_clear':False},
            pose=lambda:(self.robot.tcp(),None))
        self.task=RJ45Task(self.robot,self.gripper,self.observer,max_retries=0)

    def test_initial_unlatched_is_rejected(self):
        self.observer.connected_port=None
        self.task.tick(.6)
        self.assertTrue(self.task.done)
        self.assertIn('initially latched',self.task.error)

    def test_no_withdraw_before_measured_latch_clearance(self):
        self.task.enter('release_latch',self.task.seat,.7)
        self.task.tick(.8)
        self.assertEqual(self.task.phase,'release_latch')
        self.observer.metrics['hook_clear']=True
        self.task.tick(.01)
        self.assertEqual(self.task.phase,'withdraw')

    def test_empty_grasp_is_rejected(self):
        self.gripper.gap=.010
        self.task.enter('grasp',self.task.seat,.7)
        self.task.tick(.8)
        self.assertTrue(self.task.error)
        self.assertFalse(self.gripper.pressed)

    def test_tool_motion_without_plug_is_not_unplug_success(self):
        self.task.enter('withdraw',(-.1875,.4942,1.66),1)
        self.task.tick(1.1)
        self.assertFalse(self.task.unplugged)
        self.assertIn('without the connector',self.task.error)

    def test_dropped_plug_is_not_secure_withdrawal(self):
        self.observer.metrics['depth_m']=-.05
        self.observer.pose=lambda:((0,0,0),None)
        self.task.enter('withdraw',(-.1875,.4942,1.66),1)
        self.task.tick(1.1)
        self.assertIn('slipped',self.task.error)

    def test_wrong_port_is_not_replug_success(self):
        self.observer.connected_port=1
        self.task.enter('seat_and_latch',self.task.seat,1)
        self.task.tick(1.1)
        self.assertFalse(self.task.replugged)
        self.assertEqual(self.task.phase,'seat_and_latch')

    def test_park_without_retention_is_not_cycle_success(self):
        self.observer.connected_port=None
        self.task.enter('park',self.task.park,1)
        self.task.tick(1.1)
        self.assertTrue(self.task.done)
        self.assertTrue(self.task.error)

    def test_failed_latch_release_times_out(self):
        self.task.enter('release_latch',self.task.seat,.7)
        self.task.tick(3.8)
        self.assertTrue(self.task.error)
        self.assertFalse(self.task.unplugged)

    def test_latch_retry_resets_press_and_still_waits_for_clearance(self):
        self.task.max_retries=1
        self.task.enter('release_latch',self.task.seat,.7)
        self.task.tick(3.8)
        self.assertEqual(self.task.phase,'recover_latch_reset')
        self.assertFalse(self.gripper.pressed)
        self.task.tick(.6)
        self.assertTrue(self.gripper.pressed)
        self.task.tick(.8)
        self.assertEqual(self.task.phase,'release_latch')
        self.task.tick(3)
        self.assertTrue(self.task.error)
        self.assertEqual(self.task.retry_counts,{'release_latch':1})

    def test_grasp_recovery_requires_retained_connector(self):
        self.task.max_retries=2; self.gripper.gap=.014
        self.observer.connected_port=None
        self.task.enter('grasp',self.task.seat,.7)
        self.task.tick(.8)
        self.assertIn('retention is lost',self.task.error)

    def test_insert_recovery_cannot_pull_against_latch(self):
        self.task.max_retries=1
        self.task.enter('insert',self.task.seat,1)
        self.task.tick(4.1)
        self.assertEqual(self.task.phase,'recover_insert_release')
        before=self.robot.target
        self.task.tick(.8)
        self.assertEqual(self.task.phase,'recover_insert_release')
        self.assertEqual(self.robot.target,before)
        self.observer.metrics['hook_clear']=True
        self.task.tick(.01)
        self.assertEqual(self.task.phase,'recover_insert_retreat')


if __name__=='__main__': unittest.main()
