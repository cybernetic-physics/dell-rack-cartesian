import unittest

from rack_robotics.scripts.verify_video_temporal import same_render_identity


class TemporalProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.recorded = dict(video_sha256='abc', source_task_passed=True,
                             source_attempt='rack_robotics/experiments/source',
                             full_trajectory=True, source_hashes_verified=True,
                             mac_playback_verified=False,
                             preserved_playback_tooling_failures=[])

    def test_later_playback_evidence_does_not_change_render(self):
        current = dict(self.recorded, mac_playback_verified=True,
                       preserved_playback_tooling_failures=['preserved note'])
        self.assertTrue(same_render_identity(current, self.recorded))

    def test_each_render_identity_field_is_required(self):
        for key in ('video_sha256', 'source_task_passed', 'source_attempt',
                    'full_trajectory', 'source_hashes_verified'):
            current = dict(self.recorded)
            current.pop(key)
            self.assertFalse(same_render_identity(current, self.recorded), key)

    def test_changed_render_or_physics_evidence_rejects(self):
        for key in ('video_sha256', 'source_task_passed', 'source_attempt',
                    'full_trajectory', 'source_hashes_verified'):
            current = dict(self.recorded)
            current[key] = False if isinstance(current[key], bool) else 'changed'
            self.assertFalse(same_render_identity(current, self.recorded), key)


if __name__ == '__main__':
    unittest.main()
