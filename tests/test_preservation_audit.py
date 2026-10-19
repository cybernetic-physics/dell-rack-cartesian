import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1]/'rack_robotics/scripts/audit_preservation.py'
SPEC = importlib.util.spec_from_file_location('preservation_audit', PATH)
audit = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(audit)


class PreservationTest(unittest.TestCase):
    def test_failed_cycle_can_load_but_cannot_verify_claimed_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); env = root/'env'; env.mkdir(); base = root/'baseline'; base.mkdir()
            (base/'manifest.json').write_text('{}')
            (env/'config.json').write_text(json.dumps({'baseline': '../baseline', 'status': 'single_feasibility_pass'}))
            (env/'scene.usda').write_text('#usda 1.0')
            (env/'manifest.json').write_text(json.dumps({'baseline_manifest_sha256': audit.sha(base/'manifest.json'),
                'packaged_file_sha256': {n: audit.sha(env/n) for n in ('config.json', 'scene.usda')}}))
            result = root/'result.json'
            result.write_text(json.dumps({'passed': False, 'scope': 'full_rack', 'loaded_scene': '/workspace/env/scene.usda'}))
            report = root/'report.json'
            report.write_text(json.dumps({'environment': '/workspace/env', 'reload_results': '/workspace/result.json',
                'reload_results_sha256': audit.sha(result), 'passed': False, 'hashes_checked': 2,
                'dependency_layers': 1, 'dependency_assets': 1, 'unresolved_dependencies': []}))
            row = audit.audit_environment(env, [report], root)
            self.assertTrue(row['independent_scene_load_verified'])
            self.assertFalse(row['declared_outcome_verified'])
            result.write_text('{}')
            self.assertFalse(audit.audit_environment(env, [report], root)['independent_scene_load_verified'])

    def test_rejects_paths_outside_project(self):
        with self.assertRaises(ValueError): audit.local_path('/elsewhere/result.json', Path('/project'))


if __name__ == '__main__': unittest.main()
