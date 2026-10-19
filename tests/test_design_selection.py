import unittest
from rack_robotics.benchmarking.spec import select_designs


class DesignSelectionTest(unittest.TestCase):
    def test_explicit_versions_do_not_mutate_defaults(self):
        old={'AA':'robot_a_gripper_a/v001'}
        self.assertEqual(select_designs(['AA=robot_a_gripper_a/v005'],old),{'AA':'robot_a_gripper_a/v005'})
        self.assertEqual(select_designs(None,old),old)
        self.assertEqual(old['AA'],'robot_a_gripper_a/v001')

    def test_rejects_escape_id_swap_and_duplicate(self):
        for rows in [['AA=../../file'],['AA=robot_b_gripper_a/v001'],['AA'],
                     ['AA=robot_a_gripper_a/v005','AA=robot_a_gripper_a/v006']]:
            with self.assertRaises(ValueError): select_designs(rows,{})


if __name__=='__main__': unittest.main()
