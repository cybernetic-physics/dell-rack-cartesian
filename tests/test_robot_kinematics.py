import unittest
from rack_robotics.kinematics import joint_coordinates, compensate_deflection, compliant_joint_coordinates, DeflectionFilter, gravity_position_bias


class KinematicsTests(unittest.TestCase):
    def test_gravity_preload_matches_lift_weight_without_changing_cap(self):
        mass=2.9528110294486396
        bias=gravity_position_bias(mass,100000,100)
        self.assertAlmostEqual(bias,.00028967076198891156)
        self.assertAlmostEqual(bias*100000,mass*9.81)

    def test_gravity_preload_rejects_overloaded_or_invalid_lifts(self):
        for values in [(20,100000,100),(1,0,100),(float('nan'),100,100),(-1,100,100)]:
            with self.assertRaises(ValueError): gravity_position_bias(*values)

    def test_contact_freezes_compensation_but_not_deflection_guard(self):
        f=DeflectionFilter()
        free=f.update((0,0,1),(0,0,.9995),1/240)
        for _ in range(240):
            self.assertEqual(f.update((0,0,1),(0,0,.998),1/240,adapt=False),free)
        with self.assertRaises(ValueError):
            f.update((0,0,1),(0,0,.997),1/240,adapt=False)
        self.assertGreater(f.update((0,0,1),(0,0,.998),1/240)[2],free[2])

    def test_deflection_filter_initializes_to_static_sag(self):
        f=DeflectionFilter()
        value=f.update((0,0,1),(0,0,.999),1/240)
        self.assertAlmostEqual(value[2],.001)

    def test_deflection_filter_does_not_chase_fast_spring_motion(self):
        f=DeflectionFilter()
        f.update((0,0,1),(0,0,1),1/240)
        value=f.update((0,0,1),(0,0,.998),1/240)
        self.assertGreater(value[2],0)
        self.assertLessEqual(value[2],.003/240)

    def test_filter_preserves_raw_deflection_safety_guard(self):
        f=DeflectionFilter()
        f.update((0,0,1),(0,0,1),1/240)
        with self.assertRaises(ValueError): f.update((0,0,1),(0,0,.99),1/240)

    def test_compensation_saturates_at_real_joint_stop(self):
        q=compliant_joint_coordinates('A',(.15,.55,1.7995),(.15,.55,1.7998),(.15,.55,1.799))
        self.assertEqual(q['z'],0)
        self.assertAlmostEqual(q['y'],0)

    def test_saturation_does_not_accept_unbounded_requests(self):
        with self.assertRaises(ValueError):
            compliant_joint_coordinates('A',(.15,.55,1.9),(.15,.55,1.7998),(.15,.55,1.799))

    def test_compensation_raises_mount_for_downward_sag(self):
        result=compensate_deflection((.1,.5,1.66),(.1,.5,1.7),(.1,.5,1.699))
        self.assertAlmostEqual(result[2],1.661)
        self.assertEqual(result[:2],(.1,.5))

    def test_compensation_is_not_accumulated(self):
        first=compensate_deflection((.1,.5,1.66),(.1,.5,1.7),(.1,.5,1.699))
        second=compensate_deflection((.1,.5,1.66),(.1,.5,1.701),(.1,.5,1.7))
        self.assertAlmostEqual(first[2],second[2])

    def test_excessive_or_invalid_deflection_rejected(self):
        for z in (1.69,float('nan'),float('inf')):
            with self.assertRaises(ValueError):
                compensate_deflection((.1,.5,1.66),(.1,.5,1.7),(.1,.5,z))

    def test_a_direct_axis(self):
        q=joint_coordinates('A',(.1875,.4292,1.66))
        self.assertAlmostEqual(q['x'],.1875)
        self.assertAlmostEqual(q['y'],-.1208)
        self.assertAlmostEqual(q['z'],-.14)

    def test_c_passive_guide_targets_use_same_cartesian_workspace(self):
        self.assertEqual(joint_coordinates('C',(.1875,.4292,1.66)),
                         joint_coordinates('A',(.1875,.4292,1.66)))

    def test_b_compact_park(self):
        q=joint_coordinates('B',(-.19,.55,1.8))
        self.assertAlmostEqual(q['x_outer'],.005)
        self.assertAlmostEqual(q['x_inner'],.005)

    def test_b_all_ports_and_separation(self):
        for i in range(16):
            x=(7.5-i)*.025
            for offset in (0,-.012):
                q=joint_coordinates('B',(x+offset,.5,1.66))
                self.assertAlmostEqual(-.2+q['x_outer']+q['x_inner'],x+offset)
                self.assertTrue(0<=q['x_outer']<=.2)
                self.assertTrue(0<=q['x_inner']<=.2)

    def test_b_rejects_beyond_nested_travel(self):
        with self.assertRaises(ValueError): joint_coordinates('B',(.205,.5,1.66))

    def test_rejects_overinsertion(self):
        for architecture in ('A','B'):
            with self.assertRaises(ValueError): joint_coordinates(architecture,(0,.42,1.66))

    def test_unknown_architecture_is_not_silently_a(self):
        with self.assertRaises(ValueError): joint_coordinates('unknown',(0,.5,1.66))


if __name__=='__main__': unittest.main()
