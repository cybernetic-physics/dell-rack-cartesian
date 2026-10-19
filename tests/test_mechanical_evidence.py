import json
from pathlib import Path
import tempfile
import unittest
from rack_robotics.mechanical_evidence import sha, verify_identity


class MechanicalEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.env = Path(self.temp.name)/'env'; self.env.mkdir()
        (self.env/'trajectory.jsonl').write_text('preserved motion')
        (self.env/'results.json').write_text(json.dumps({'passed': False}))
        (self.env/'manifest.json').write_text(json.dumps({'packaged_file_sha256': {
            name: sha(self.env/name) for name in ('trajectory.jsonl', 'results.json')}}))
        self.props = {'passed': True, 'environment_manifest_sha256': sha(self.env/'manifest.json')}

    def test_packaged_failed_motion_is_accepted_without_relabeling_success(self):
        self.assertEqual(verify_identity(self.props, self.env, self.env), 'manifest_verified_packaged_trajectory')

    def test_unrelated_motion_is_rejected(self):
        attempt = Path(self.temp.name)/'attempt'; attempt.mkdir()
        (attempt/'results.json').write_text((self.env/'results.json').read_text())
        with self.assertRaises(ValueError): verify_identity(self.props, attempt, self.env)

    def test_changed_package_or_failed_query_is_rejected(self):
        with self.assertRaises(ValueError): verify_identity(dict(self.props, passed=False), self.env, self.env)
        (self.env/'trajectory.jsonl').write_text('changed')
        with self.assertRaises(ValueError): verify_identity(self.props, self.env, self.env)

    def test_matching_benchmark_environment_is_accepted(self):
        attempt = Path(self.temp.name)/'attempt'; attempt.mkdir()
        (attempt/'results.json').write_text(json.dumps({
            'environment_manifest_sha256': sha(self.env/'manifest.json'), 'passed': True}))
        self.assertEqual(verify_identity(self.props, attempt, self.env), 'benchmark_environment_identity')
