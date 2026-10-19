import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from rack_robotics.scripts.reload_environments import verify_package


class ReloadPackageTests(unittest.TestCase):
    def test_rejects_changed_source_before_launch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root/'demo.py'; source.write_text('original')
            manifest = root/'manifest.json'
            manifest.write_text(json.dumps({'packaged_file_sha256': {
                'demo.py': hashlib.sha256(source.read_bytes()).hexdigest()}}))
            self.assertEqual(verify_package(root), hashlib.sha256(manifest.read_bytes()).hexdigest())
            source.write_text('changed')
            with self.assertRaises(ValueError): verify_package(root)

    def test_rejects_missing_packaged_dependency(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'manifest.json').write_text(json.dumps({'packaged_file_sha256': {'scene.usda': 'missing'}}))
            with self.assertRaises(FileNotFoundError): verify_package(root)
