"""Static design screens only; not substitutes for cooked-shape collision tests."""
import unittest
from rack_robotics.rg2_parameters import (
    BASE_OFFSET, SHOE_RISE, SHOE_FORWARD, REFERENCE_ANGLE,
    MOUNT_MASS, SHOE_MASS, TELESCOPING_PARK_X, clearance_screens,
)
from rack_robotics.rg2_kinematics import tip_geometry


class RG2MountTests(unittest.TestCase):
    def test_side_lift_park_uses_real_stages_with_clearance(self):
        from rack_robotics.kinematics import joint_coordinates
        coordinates=joint_coordinates('B',(TELESCOPING_PARK_X,.55,1.8))
        self.assertAlmostEqual(coordinates['x_outer'],.030)
        self.assertAlmostEqual(coordinates['x_inner'],.030)
        gaps=clearance_screens()
        self.assertGreater(gaps['telescoping_park_cradle_to_guide_m'],.04)
        self.assertGreater(gaps['telescoping_park_flange_to_lift_plate_m'],.03)

    def test_flange_has_clearance_to_both_bridge_and_carriage(self):
        gaps=clearance_screens()
        self.assertGreater(gaps['rear_flange_to_carriage_m'], .010)
        self.assertGreater(gaps['rear_flange_to_bridge_m'], .010)

    def test_vendor_base_has_margin_beyond_failed_visual_gap(self):
        self.assertGreater(clearance_screens()['base_visual_top_to_carriage_m'], .008)

    def test_rightmost_port_does_not_intersect_upright_statically(self):
        self.assertGreater(clearance_screens()['rightmost_port_cradle_to_frame_m'], .005)

    def test_side_supports_clear_central_vendor_housing(self):
        self.assertGreater(clearance_screens()['side_drop_to_rg2_housing_m'], .003)

    def test_open_shoulders_fit_between_depth_rails(self):
        self.assertGreater(clearance_screens()['open_shoulder_to_depth_rail_m'], .002)

    def test_lowering_base_does_not_change_nominal_tcp(self):
        self.assertAlmostEqual(BASE_OFFSET[2]-.0003+SHOE_RISE, 0.)
        extension=tip_geometry(REFERENCE_ANGLE)[1]
        self.assertAlmostEqual(BASE_OFFSET[1]-extension-SHOE_FORWARD, -.13)

    def test_lumped_masses_cover_plate_and_riser_envelopes(self):
        # Aluminum cradle alone; steel riser alone. Hardware adds more mass.
        self.assertGreater(MOUNT_MASS, .094*.126*.006*2700)
        self.assertGreater(SHOE_MASS, SHOE_RISE*.010*.0045*7850)


if __name__=='__main__': unittest.main()
