import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from rack_robotics.scripts.compare_solver_rates import compare


class SolverComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.paths=[]
        for hz in (240,480):
            p=Path(self.temp.name)/str(hz)
            (p/'source').mkdir(parents=True)
            source=b'# fixture, not a physical trial\n'
            (p/'source/runner.py').write_bytes(source)
            (p/'source_manifest.json').write_text(json.dumps({'runner.py':hashlib.sha256(source).hexdigest()}))
            (p/'results.json').write_text(json.dumps({'passed':False,'robot':'A','gripper':'B',
                'scope':'test_fixture','physics_hz':hz,'physics_dt':1/hz}))
            (p/'contacts.json').write_text(json.dumps({'pairs':[],'reporting_errors':[],'physics_dt':1/hz}))
            self.paths.append(p)

    def test_matched_failed_pair_is_not_convergence(self):
        r=compare(*self.paths)
        self.assertTrue(r['paired_setup_verified'])
        self.assertFalse(r['convergence_established'])
        self.assertFalse(any(t['passed'] for t in r['trials']))

    def test_modified_source_is_rejected(self):
        (self.paths[1]/'source/runner.py').write_text('changed')
        self.assertFalse(compare(*self.paths)['paired_setup_verified'])

    def test_inconsistent_contact_timestep_is_rejected(self):
        (self.paths[1]/'contacts.json').write_text(json.dumps({'pairs':[],
            'reporting_errors':[],'physics_dt':1/240}))
        self.assertFalse(compare(*self.paths)['paired_setup_verified'])

    def test_empty_manifests_are_not_verified(self):
        for p in self.paths: (p/'source_manifest.json').write_text('{}')
        self.assertFalse(compare(*self.paths)['paired_setup_verified'])
