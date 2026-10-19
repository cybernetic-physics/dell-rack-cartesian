import unittest
from rack_robotics.jaw_geometry import guide_vertical_profile


class JawGeometryTests(unittest.TestCase):
    def test_default_preserves_original_shoes(self):
        land,section=guide_vertical_profile(True)
        self.assertEqual(land,.00395)
        self.assertEqual(section,(.00315,.00395,.00475,.00475))
        self.assertAlmostEqual(guide_vertical_profile(False)[0],-.00495)

    def test_wider_variant_preserves_lands_and_centre(self):
        upper,_=guide_vertical_profile(True,.0076)
        lower,_=guide_vertical_profile(False,.0076)
        # Each flat bearing land remains 1.6 mm thick.
        gap=(upper-.0008)-(lower+.0008)
        self.assertAlmostEqual(gap,.0076)
        self.assertAlmostEqual((gap-.0072)/2,.0002)
        self.assertAlmostEqual((upper+lower)/2,-.0005)

    def test_profile_mirroring_and_invalid_dimensions(self):
        for throat in (.0073,.0076):
            top=guide_vertical_profile(True,throat)[1]
            bottom=guide_vertical_profile(False,throat)[1]
            for a,b in zip(top,bottom): self.assertAlmostEqual(a+b,-.001)
        for throat in (0,.0071,.0091,float('nan')):
            with self.assertRaises(ValueError): guide_vertical_profile(True,throat)
