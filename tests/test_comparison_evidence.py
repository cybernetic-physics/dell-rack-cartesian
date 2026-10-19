import unittest
from rack_robotics.scripts.compare_designs import identity, workspace_verdict, replay_verdict


class ComparisonEvidenceTest(unittest.TestCase):
    def workspace(self):
        keys=('samples_present','finite_state','sampled_anchor_gap_below_1p5mm',
            'sampled_hinge_limits_within_one_degree','startup_samples_present','startup_finite_state',
            'startup_sampled_anchor_gap_below_1p5mm','startup_sampled_hinge_limits_within_one_degree',
            'all_waypoints_reached','no_runtime_error','no_robot_contact_violations')
        return {'passed':True,'checks':dict.fromkeys(keys,True),'error':None,
                'contact_violations':[],'waypoints_reached':[{},{}],'planned_waypoint_count':2}
    def test_exact_version_binding(self):
        identity({'environment_manifest_sha256':'a'},'a')
        with self.assertRaises(ValueError):identity({'environment_manifest_sha256':'b'},'a')
    def test_workspace_gate_and_complete_path(self):
        self.assertTrue(workspace_verdict(self.workspace()))
        r=self.workspace();r['waypoints_reached'].pop()
        with self.assertRaises(ValueError):workspace_verdict(r)
        r=self.workspace();r['checks']['startup_samples_present']=False
        with self.assertRaises(ValueError):workspace_verdict(r)
        r['passed']=False;self.assertFalse(workspace_verdict(r))
    def test_missing_or_nonboolean_gates_are_not_a_pass(self):
        for change in ('missing','none','numeric'):
            r=self.workspace()
            if change=='missing':del r['checks']['finite_state']
            else:r['checks']['finite_state']=None if change=='none' else 1
            with self.assertRaises(ValueError):workspace_verdict(r)
    def test_replay_requires_all_recorded_pose_and_camera_checks(self):
        r={'source_passed':True,'full_trajectory':True,'physics_running':False,'frames':10,
           'recording_validation':{'samples':10,'body_count':20},
           'pose_replay_validation':{'body_sample_checks':200,'maximum_translation_error_m':0.,'maximum_rotation_error_rad':1e-8},
           'capture_camera_validation':{'checked':10,'maximum_view_matrix_element_error':1e-14}}
        replay_verdict(r)
        r['capture_camera_validation']['checked']=9
        with self.assertRaises(ValueError):replay_verdict(r)
        r['capture_camera_validation']['checked']=10;r['pose_replay_validation']['maximum_rotation_error_rad']=float('nan')
        with self.assertRaises(ValueError):replay_verdict(r)


if __name__=='__main__':unittest.main()
