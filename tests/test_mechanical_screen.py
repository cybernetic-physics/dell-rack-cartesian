import math
import unittest
from rack_robotics.mechanical_screen import transform_point,gravity_wrench,box_corners,envelope,rack_overhang,descendants,screen


class MechanicalScreenTests(unittest.TestCase):
    def test_body_frame_com_rotation_and_translation(self):
        s=math.sqrt(.5)
        p=transform_point([1,2,3,s,0,0,s],[.2,0,0])
        for a,b in zip(p,[1,2.2,3]): self.assertAlmostEqual(a,b)
        with self.assertRaises(ValueError): transform_point([0,0,0,2,0,0,0],[0,0,0])

    def test_gravity_moment_uses_com_not_body_origin(self):
        r=gravity_wrench([(2,[.3,.4,99])],[0,0,1],gravity=10)
        self.assertEqual(r['force_n'],[0,0,-20])
        self.assertEqual(r['moment_nm'],[-8,6,0])

    def test_union_and_overhang_not_a_clearance_claim(self):
        b=envelope(box_corners([-.55,.4,1],[.31,.85,2]))
        r=rack_overhang(b)
        self.assertAlmostEqual(r['left_m'],.25)
        self.assertAlmostEqual(r['right_m'],.01)
        self.assertAlmostEqual(r['rear_m'],.25)

    def test_load_subtree_does_not_double_count_loops(self):
        joints=[{'body0':['a'],'body1':['b']},{'body0':['b'],'body1':['c']},{'body0':['c'],'body1':['b']}]
        self.assertEqual(descendants('b',joints,{'a','b','c'}),['b','c'])

    def test_sampled_screen_and_missing_pose_rejection(self):
        body={'mass_kg':2,'com_local_xyz_xyzw':[.1,0,0,0,0,0,1],
              'geometry':[{'lower_m':[-.1,-.1,-.1],'upper_m':[.1,.1,.1]}]}
        props={'passed':True,'bodies':{'/World/Robot/Frame':body},'joints':[],
               'mount_centres_m':[[0,.6,1],[0,.6,2]]}
        header={'format':'measured_world_poses_v1','body_paths':['/World/Robot/Frame']}
        rows=[{'time':0,'phase':'initialize','poses':[[0,.7,1,1,0,0,0]]},
              {'time':1,'phase':'park','poses':[[.3,.7,1,1,0,0,0]]}]
        result=screen(props,header,rows)
        self.assertAlmostEqual(result['maximum_sampled_overhang']['right_m'],.1)
        self.assertEqual(result['largest_sampled_gravity_mount_moment']['time_s'],1)
        self.assertIsNone(result['rated_load_pass'])
        self.assertEqual(result['moving_mass_kg'],0)
        with self.assertRaises(ValueError): screen(props,dict(header,body_paths=[]),rows)
