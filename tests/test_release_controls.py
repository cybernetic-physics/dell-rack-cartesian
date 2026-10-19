import copy
import math
import unittest
from types import SimpleNamespace

from rack_robotics.benchmarking.release_controls import compare_pair,summarize,task_class,validate_request
from rack_robotics.scripts.screen_physical_controls import verdict_matches
from tests import test_physical_controls as fixtures
from tests.test_physical_controls import BaseTask,Value


class ReleaseControlsTest(unittest.TestCase):
    def test_cross_python_distance_roundoff_never_changes_gates(self):
        rows,result=self.evidence('released_hold');actual=summarize('released_hold',rows,result)
        saved=copy.deepcopy(actual);saved['metrics']['maximum_tool_displacement_m']=.0003465502943035319
        actual['metrics']['maximum_tool_displacement_m']=math.nextafter(saved['metrics']['maximum_tool_displacement_m'],0.)
        self.assertTrue(verdict_matches(actual,saved,True))
        self.assertFalse(verdict_matches(actual,saved,False))
        changed=copy.deepcopy(saved);changed['checks']['jaws_physically_open']=False
        self.assertFalse(verdict_matches(actual,changed,True))
        changed=copy.deepcopy(saved);changed['metrics']['maximum_tool_displacement_m']+=1e-9
        self.assertFalse(verdict_matches(actual,changed,True))
        changed=copy.deepcopy(saved);changed['metrics']['tool_advance_m']+=1e-16
        self.assertFalse(verdict_matches(actual,changed,True))

    def test_open_command_delivers_transport_even_below_aperture_gate(self):
        drives={'y':SimpleNamespace(GetMaxForceAttr=lambda:Value(8.)),
                'servo':SimpleNamespace(GetTargetPositionAttr=lambda:Value(0.))}
        task=task_class(BaseTask,'released_transport',drives)()
        task.gripper.aperture=lambda:.0127
        task.enter('separate',(0.,.51,1.),1.2)
        self.assertEqual(task.phase,'challenge_open')
        self.assertEqual(task.duration,2.)
        self.assertEqual(task.release_open_targets,{'servo':0.})
        task.tick(2.)
        self.assertEqual(task.phase,'challenge_transport')
        self.assertAlmostEqual(task.target[1],.53)
        task.tick(2.)
        self.assertTrue(task.challenge_completed)
        self.assertIsNone(task.error)

    def test_hold_has_no_requested_translation(self):
        drives={'y':SimpleNamespace(GetMaxForceAttr=lambda:Value(8.))}
        task=task_class(BaseTask,'released_hold',drives)()
        task.enter('separate',(0.,.51,1.),1.2);task.tick(2.)
        self.assertEqual(task.target,(0.,.49,1.))
        self.assertEqual(task.commands[:2],[('grasp',False),('latch',False)])

    def evidence(self,mode):
        # Reuse the original recorder's state shape, not its verdict/gates.
        seed,result=fixtures.PhysicalControlsTest().evidence('open_transport')
        prior=copy.deepcopy(seed[0]);prior['jaw_drive_targets']={'servo':0.}
        opened=copy.deepcopy(prior);opened.update(phase='challenge_open',aperture_m=.016,
                                                plug_position_m=[0.,.4,.8])
        moved=copy.deepcopy(opened);moved.update(phase='challenge_transport',
            tcp_m=[0.,.44 if mode=='released_transport' else .4,1.])
        rows=[prior]+[copy.deepcopy(opened) for _ in range(200)]+[copy.deepcopy(moved) for _ in range(200)]
        for i,row in enumerate(rows):row['time_s']=(i+1)*.01
        result['release_open_targets']={'servo':0.}
        result['physical_transport_reference'].update(time_s=2.02,plug_position_m=[0.,.4,.8])
        return rows,result

    def test_release_requires_actual_opening_separation_and_valid_contact(self):
        rows,result=self.evidence('released_transport')
        self.assertTrue(summarize('released_transport',rows,result)['passed'])
        for field,value in [('aperture_m',.0127),('plug_position_m',[0.,.44,1.]),
                            ('jaw_drive_targets',{'servo':5.}),('latch_target_m',.003),
                            ('y_force_cap_n',9.),('depth_m',.01),('tcp_m',[0.,.4,1.])]:
            changed=copy.deepcopy(rows)
            for r in changed[201:]:r[field]=value
            self.assertFalse(summarize('released_transport',changed,result)['passed'],field)
        changed=copy.deepcopy(rows)
        changed[-1]['contacts']=[{'actors':['/World/Robot/LeftJaw','/World/Plug'],
            'normal_impulse_actor0_ns':[0.,0.,0.],'friction_impulse_actor0_ns':[0.,0.,0.]}]
        self.assertFalse(summarize('released_transport',changed,result)['passed'])

    def test_followup_cannot_turn_incomplete_opening_into_pass(self):
        rows,result=self.evidence('released_transport')
        for row in rows[201:]:row['aperture_m']=.0127
        verdict=summarize('released_transport',rows,result)
        self.assertTrue(verdict['checks']['requested_motion_delivered'])
        self.assertFalse(verdict['checks']['jaws_physically_open'])
        self.assertFalse(verdict['passed'])

    def test_pair_requires_matched_prefix_and_all_challenge_samples(self):
        h,_=self.evidence('released_hold');m,_=self.evidence('released_transport')
        self.assertTrue(compare_pair(h,m)['no_measurable_transport_effect'])
        changed=copy.deepcopy(m);changed[210]['plug_position_m'][1]+=.01
        self.assertFalse(compare_pair(h,changed)['no_measurable_transport_effect'])
        changed=copy.deepcopy(m);changed[0]['aperture_m']+=.001
        self.assertFalse(compare_pair(h,changed)['no_measurable_transport_effect'])
        self.assertFalse(compare_pair(h,m[:-1])['no_measurable_transport_effect'])

    def test_hold_motion_and_duration_are_bounded(self):
        rows,result=self.evidence('released_hold')
        self.assertTrue(summarize('released_hold',rows,result)['passed'])
        rows[-1]['tcp_m'][0]=.002
        self.assertFalse(summarize('released_hold',rows,result)['checks']['requested_motion_delivered'])
        rows,result=self.evidence('released_transport')
        self.assertFalse(summarize('released_transport',rows[:-10],result)['checks']['full_challenge_duration'])

    def test_request_cannot_mix_with_other_diagnostics(self):
        args=['released_hold','control',1,False,None,False,None]
        validate_request(*args)
        for index,value in [(0,'open_transport'),(1,'randomized'),(2,3),(3,True),(4,5.),(5,True),(6,'nominal')]:
            changed=list(args);changed[index]=value
            with self.assertRaises(ValueError):validate_request(*changed)


if __name__=='__main__':unittest.main()
