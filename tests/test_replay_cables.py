import unittest
from pxr import Usd, UsdGeom
from rack_robotics.replay import recorded_cables


class ReplayCablesTest(unittest.TestCase):
    def test_target_and_neighbors_are_required(self):
        stage = Usd.Stage.CreateInMemory(); bodies = []
        for root in ('/World', '/World/OccupiedNeighbors/Port03', '/World/OccupiedNeighbors/Port05'):
            UsdGeom.Xform.Define(stage, root+'/Plug'); bodies.append(root+'/Plug')
            UsdGeom.BasisCurves.Define(stage, root+'/Cable/Jacket')
            for i in range(36):
                path = root+f'/Cable/Link{i:02d}'
                UsdGeom.Capsule.Define(stage, path); bodies.append(path)
        cables = recorded_cables(stage, bodies)
        self.assertEqual(len(cables), 3)
        self.assertTrue(all(len(links) == 36 for _, _, links in cables))
        self.assertEqual(cables[1][1], '/World/OccupiedNeighbors/Port03/Plug')
        with self.assertRaises(ValueError): recorded_cables(stage, bodies[:-1])

    def test_no_cable_is_not_silently_accepted(self):
        with self.assertRaises(ValueError): recorded_cables(Usd.Stage.CreateInMemory(), [])


if __name__ == '__main__': unittest.main()
