import unittest
from types import SimpleNamespace
from rack_robotics.benchmarking.cable_balance import residual_forces, distal_reactions, axial_component, FullContactImpulses


class CableBalanceTests(unittest.TestCase):
    def test_static_weight_and_free_fall(self):
        dt=.01;g=[0.,0.,-10.]
        r=residual_forces([.1,.1],[[0.,0.,0.]]*2,[[0.,0.,0.],[0.,0.,-.1]],[[0.,0.,0.]]*2,dt,g,[0.,0.])
        self.assertAlmostEqual(r[0][2],1.)
        self.assertEqual(r[1],[0.,0.,0.])

    def test_contact_support_is_not_joint_tension(self):
        r=residual_forces([.1],[[0.,0.,0.]],[[0.,0.,0.]],[[0.,0.,.01]],.01,[0.,0.,-10.],[0.])
        self.assertAlmostEqual(r[0][2],0.)

    def test_damping_and_friction_are_not_joint_forces(self):
        dt=.01;vfree=(1.-.5*dt);impulse=-.002;vnext=vfree+impulse/.1
        r=residual_forces([.1],[[1.,0.,0.]],[[vnext,0.,0.]],[[impulse,0.,0.]],dt,[0.,0.,0.],[.5])
        self.assertAlmostEqual(r[0][0],0.)

    def test_distal_sum_and_signed_projection(self):
        self.assertEqual(distal_reactions([[1.,0.,2.],[-1.,0.,3.]]),[[0.,0.,5.],[-1.,0.,3.]])
        self.assertEqual(axial_component([1.,2.,3.],[0.,0.,2.]),3.)
        self.assertEqual(axial_component([1.,2.,3.],[0.,0.,-1.]),-3.)

    def test_invalid_data_rejected(self):
        with self.assertRaises(ValueError):axial_component([0.,0.,0.],[0.,0.,0.])
        with self.assertRaises(ValueError):distal_reactions([[float('nan'),0.,0.]])
        for dt in (0.,-1.,float('nan')):
            with self.assertRaises(ValueError):residual_forces([1.],[[0.]*3],[[0.]*3],[[0.]*3],dt,[0.]*3,[0.])

    def test_normal_and_friction_impulses_cancel_for_internal_contact(self):
        collector=FullContactImpulses.__new__(FullContactImpulses)
        collector.paths=['A','B'];collector.decode=lambda p:p;collector.errors=[];collector.begin()
        header=SimpleNamespace(actor0='A',actor1='B',contact_data_offset=0,num_contact_data=1,
                               friction_anchors_offset=0,num_friction_anchors_data=1)
        collector.on_contacts([header],[SimpleNamespace(impulse=[0.,0.,2.])],
                              [SimpleNamespace(impulse=[-.5,0.,0.])])
        self.assertEqual(collector.totals(),[[-.5,0.,2.],[.5,0.,-2.]])
        self.assertEqual(distal_reactions(collector.totals())[0],[0.,0.,0.])
        self.assertEqual(collector.anchors,1)
        collector.begin();self.assertEqual(collector.totals(),[[0.]*3,[0.]*3])

    def test_callback_error_is_not_silent_missing_force(self):
        collector=FullContactImpulses.__new__(FullContactImpulses)
        collector.paths=['A'];collector.decode=lambda p:p;collector.errors=[];collector.begin()
        collector.on_contacts([object()],[],[])
        with self.assertRaises(RuntimeError):collector.totals()
