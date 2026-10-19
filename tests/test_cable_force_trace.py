import copy
import math
import unittest
from rack_robotics.benchmarking.cable_force_trace import negative_y_axis,validate_calibration


class CableForceTraceTests(unittest.TestCase):
    def test_child_local_axis_tracks_orientation(self):
        self.assertEqual(negative_y_axis([0.,0.,0.,1.]),[0.,-1.,0.])
        axis=negative_y_axis([-math.sqrt(.5),0.,0.,math.sqrt(.5)])
        for a,b in zip(axis,[0.,0.,1.]):self.assertAlmostEqual(a,b)
        for q in ([0.]*4,[float('nan'),0.,0.,1.]):
            with self.assertRaises(ValueError):negative_y_axis(q)

    def test_every_independent_calibration_control_is_required(self):
        names=['free_fall_residual_below_1mn','held_weight_within_1mn',
               'resting_contact_residual_below_10mn','sliding_contact_residual_below_10mn',
               'friction_anchors_present','chain_root_weight_within_2mn',
               'chain_distal_weight_within_1mn','all_finite','reporting_errors_absent']
        report={'passed':True,'checks':dict.fromkeys(names,True),
                'source_sha256':{'balance_source.py':'test_digest'},'physics_dt_s':1/480}
        validate_calibration(report,'test_digest',1/480)
        for name in names:
            bad=copy.deepcopy(report);del bad['checks'][name]
            with self.assertRaises(ValueError):validate_calibration(bad,'test_digest',1/480)
            bad=copy.deepcopy(report);bad['checks'][name]=False
            with self.assertRaises(ValueError):validate_calibration(bad,'test_digest',1/480)
        with self.assertRaises(ValueError):validate_calibration(report,'changed_digest',1/480)
        with self.assertRaises(ValueError):validate_calibration(report,'test_digest',1/240)
