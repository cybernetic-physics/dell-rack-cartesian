import json
from pathlib import Path
import tempfile
import unittest
from rack_robotics.scripts.evaluate_all import copy_frozen_harness, sha


class BenchmarkExtensionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.campaign = Path(self.temp.name)/'original'; (self.campaign/'harness').mkdir(parents=True)
        self.source = self.campaign/'harness/runner.py'; self.source.write_text('# frozen\n')
        self.manifest = self.campaign/'campaign_manifest.json'
        self.manifest.write_text(json.dumps({'harness_sha256': {'harness/runner.py': sha(self.source)}}))
        self.output = Path(self.temp.name)/'new'; self.output.mkdir()

    def test_extension_copies_exact_sources_and_records_identity(self):
        provenance = copy_frozen_harness(self.campaign, self.output)
        self.assertEqual(sha(self.source), sha(self.output/'harness/runner.py'))
        self.assertEqual(provenance['campaign_manifest_sha256'], sha(self.manifest))

    def test_changed_source_cannot_enter_extension(self):
        self.source.write_text('# modified\n')
        with self.assertRaises(ValueError): copy_frozen_harness(self.campaign, self.output)

    def test_unrecorded_extra_source_is_rejected(self):
        (self.campaign/'harness/extra.py').write_text('# unrecorded\n')
        with self.assertRaises(ValueError): copy_frozen_harness(self.campaign, self.output)
