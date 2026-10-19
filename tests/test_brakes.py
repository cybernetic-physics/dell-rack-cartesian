import math
import unittest
from rack_robotics.brakes import BrakeParameters,PassiveBrake,BrakeBank


class BrakeTest(unittest.TestCase):
    def test_delayed_engagement_and_release(self):
        b=PassiveBrake(); dt=.001
        for i in range(29): self.assertFalse(b.step(i*.01,10,dt,False)['engaged'])
        self.assertTrue(b.step(.29,10,dt,False)['engaged'])
        self.assertAlmostEqual(b.anchor,.29)
        for _ in range(49): self.assertTrue(b.step(.29,0,dt,True)['engaged'])
        self.assertFalse(b.step(.29,0,dt,True)['engaged'])

    def test_released_brake_never_creates_hold_force(self):
        b=PassiveBrake()
        for q in (-100,0,100): self.assertEqual(b.step(q,100,.01,True)['torque_nm'],0.)

    def test_backlash_and_passive_torque_cap(self):
        b=PassiveBrake(BrakeParameters(engagement_delay_s=0))
        b.step(0,0,.001,False)
        self.assertEqual(b.step(math.radians(.4),0,.001,False)['torque_nm'],0.)
        for q,v in ((100,100),(-100,-100),(100,-100)):
            s=b.step(q,v,.001,False)
            self.assertLessEqual(abs(s['torque_nm']),.4+1e-12)
            self.assertLessEqual(s['damping_torque_nm']*v,0.)
        self.assertGreater(b.plastic_dissipation_j,0.)

    def test_elastic_energy_cannot_grow_without_applied_work(self):
        b=PassiveBrake(BrakeParameters(engagement_delay_s=0,damping_nms_rad=0))
        previous=b.step(0,0,.001,False); previous_q=0.; work=0.
        # Monotone loading/unloading, with yielding and reverse slip.
        for q in [i*.001 for i in range(1,10001)]+[10-i*.001 for i in range(1,20001)]:
            current=b.step(q,(q-previous_q)/.001,.001,False)
            work-=.5*(previous['torque_nm']+current['torque_nm'])*(q-previous_q)
            self.assertGreaterEqual(work-current['elastic_energy_j'],-1e-7)
            previous=current;previous_q=q

    def test_virtual_work_and_motor_torque_limits(self):
        for architecture in ('A','B','C'):
            b=BrakeBank(architecture); q=[0.]*len(b.joints)
            b.step(q,q,.03,False)
            v=[.3]*len(q); q=[.01]*len(q)
            s=b.step(q,v,.001,False)
            self.assertAlmostEqual(s['joint_power_w'],s['motor_power_w'])
            self.assertTrue(all(abs(m['torque_nm'])<=.40000001 for m in s['motors']))

    def test_corexz_requires_both_motor_brakes_for_full_rank_hold(self):
        b=BrakeBank('C')
        a,c=b.jacobian
        self.assertNotEqual(a[0]*c[1]-a[1]*c[0],0.)
        b.step([0,0],[0,0],.03,[False,True])
        s=b.step([.01,0],[0,0],.001,[False,True])
        self.assertNotEqual(s['joint_effort_n'][0],0.)
        self.assertAlmostEqual(s['joint_effort_n'][0],s['joint_effort_n'][1])

    def test_invalid_parameters_rejected(self):
        with self.assertRaises(ValueError): BrakeParameters(torque_cap_nm=-1)
        with self.assertRaises(ValueError): PassiveBrake().step(0,0,0,False)
