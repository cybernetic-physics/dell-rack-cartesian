import json
from pathlib import Path
import tempfile
import unittest
from rack_robotics.dependency_inventory import Files, digest, inventory


class DependencyInventoryTest(unittest.TestCase):
    def fixture(self, temp):
        project=Path(temp)/'project'; runtime=Path(temp)/'runtime'
        project.mkdir(); runtime.mkdir()
        env=project/'rack_robotics/environments/robot_a_gripper_a/v001'; env.mkdir(parents=True)
        baseline=project/'baseline'; baseline.mkdir()
        (baseline/'code.py').write_text('immutable code')
        shared=project/'texture.png'; shared.write_bytes(b'texture')
        (baseline/'manifest.json').write_text(json.dumps({'files':{'code.py':digest(baseline/'code.py')},
            'shared_dependencies':{'texture.png':digest(shared)},'vendor_recovery':{'url':'https://example.invalid/pinned'}}))
        (env/'scene.usda').write_text('#usda 1.0')
        (env/'config.json').write_text(json.dumps({'baseline':str(baseline),'scene':'scene.usda'}))
        (env/'manifest.json').write_text(json.dumps({'packaged_file_sha256':{n:digest(env/n) for n in ('config.json','scene.usda')},
            'baseline_manifest_sha256':digest(baseline/'manifest.json')}))
        audit=project/'audit.json'; audit.write_text(json.dumps({'versions':1,'environments':[
            {'environment':str(env.relative_to(project)),'manifest_sha256':digest(env/'manifest.json')}]}))
        mdl=runtime/'OmniPBR.mdl'; mdl.write_text('runtime shader')
        return project,runtime,env,audit,shared,mdl

    def test_closure_binds_baseline_package_and_runtime_without_duplicate_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root,runtime,env,audit,shared,mdl=self.fixture(temp)
            report=inventory(root,runtime,audit,lambda scene:([scene],[shared,shared,mdl],[]))
            self.assertTrue(report['passed']); self.assertEqual(report['preserved_versions'],1)
            self.assertEqual(len(report['environments'][0]['usd_assets']),2)
            self.assertEqual(report['files']['project:texture.png']['roles'],['baseline_shared_dependency','usd_asset'])
            self.assertIn('isaac_runtime:OmniPBR.mdl',report['files'])

    def test_changed_declared_package_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root,runtime,env,audit,shared,mdl=self.fixture(temp)
            (env/'scene.usda').write_text('changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                inventory(root,runtime,audit,lambda scene:([scene],[shared,mdl],[]))

    def test_unresolved_or_omitted_scene_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root,runtime,env,audit,shared,mdl=self.fixture(temp)
            for closure in (([env/'scene.usda'],[],['missing.png']),([],[],[])):
                with self.assertRaises(ValueError): inventory(root,runtime,audit,lambda scene:closure)

    def test_unknown_external_dependency_and_symlink_escape_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root,runtime,env,audit,shared,mdl=self.fixture(temp)
            external=Path(temp)/'outside'; external.write_bytes(b'outside')
            (root/'link').symlink_to(external)
            for path in (external,root/'link'):
                with self.assertRaises(ValueError): Files(root,runtime).add(path,'asset')

    def test_audit_must_cover_all_saved_versions(self):
        with tempfile.TemporaryDirectory() as temp:
            root,runtime,env,audit,shared,mdl=self.fixture(temp)
            extra=env.parent/'v002'; extra.mkdir(); (extra/'manifest.json').write_text('{}')
            with self.assertRaisesRegex(ValueError,'every saved version'):
                inventory(root,runtime,audit,lambda scene:([scene],[shared,mdl],[]))


if __name__=='__main__': unittest.main()
