import json
import unittest
from decimal import Decimal
from rack_robotics.corexz import motor_coordinates,carriage_coordinates,generalized_forces,transmission_efforts


class CoreXZTests(unittest.TestCase):
    def test_observations_normalized_to_json_scalars(self):
        result=transmission_efforts((.15,0),(Decimal('.15'),Decimal('0')),
                                    (Decimal('0'),Decimal('0')),20)
        decoded=json.loads(json.dumps(result))
        self.assertEqual(decoded['joint_force_n'],[0,20])

    def test_coordinates_round_trip(self):
        for x,z in ((.15,-.14),(-.2,-.7),(0,0)):
            measured=carriage_coordinates(*motor_coordinates(x,z))
            self.assertAlmostEqual(measured[0],x); self.assertAlmostEqual(measured[1],z)

    def test_power_is_conserved_by_jacobian(self):
        for vx,vz in ((.1,.2),(-.3,.05)):
            va,vb=motor_coordinates(vx,vz)
            fx,fz=generalized_forces(8,-3)
            self.assertAlmostEqual(8*va-3*vb,fx*vx+fz*vz)

    def test_gravity_is_compensated_through_motors(self):
        r=transmission_efforts((0,0),(0,0),(0,0),20)
        self.assertEqual(r['motor_force_n'],(10,-10))
        self.assertEqual(r['joint_force_n'],(0,20))

    def test_motor_caps_couple_available_axis_forces(self):
        r=transmission_efforts((1,1),(0,0),(0,0),0)
        self.assertEqual(r['motor_force_n'],(25,0))
        self.assertEqual(r['joint_force_n'],(25,25))
        self.assertEqual(r['motor_saturated'],(True,False))

    def test_transverse_contact_limit_preserves_lift_within_motor_caps(self):
        raw=transmission_efforts((1,.1),(0,0),(0,0),20)
        limited=transmission_efforts((1,.1),(0,0),(0,0),20,x_force_limit_n=5)
        self.assertLessEqual(abs(limited['joint_force_n'][0]),5)
        self.assertEqual(limited['joint_force_n'][1],raw['joint_force_n'][1])
        self.assertTrue(limited['transverse_force_limited'])
        self.assertTrue(all(abs(v)<=25 for v in limited['motor_force_n']))

    def test_contact_limit_does_not_revive_failed_motor(self):
        r=transmission_efforts((0,0),(0,0),(0,0),20,enabled=(False,True),x_force_limit_n=5)
        self.assertEqual(r['motor_force_n'],(0,-5))
        self.assertEqual(r['joint_force_n'],(-5,5))

    def test_one_motor_loss_affects_both_axes(self):
        r=transmission_efforts((0,0),(0,0),(0,0),20,enabled=(False,True))
        self.assertEqual(r['joint_force_n'],(-10,10))

    def test_overload_cannot_bypass_motor_limits(self):
        r=transmission_efforts((0,0),(0,0),(0,0),100)
        self.assertEqual(r['joint_force_n'],(0,50))

    def test_invalid_measurements_are_rejected(self):
        with self.assertRaises(ValueError):
            transmission_efforts((0,0),(float('nan'),0),(0,0),20)


if __name__=='__main__': unittest.main()
