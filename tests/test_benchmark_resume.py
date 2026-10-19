import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from rack_robotics.scripts.evaluate_all import adopt_persisted_result,checked_result


class BenchmarkResumeTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.output=Path(self.temp.name); self.directory=self.output/'trial-attempt001'
        self.directory.mkdir()
        self.record={'attempt':1,'directory':self.directory.name,'status':'running','pid':999999}
        self.condition={'role':'randomized','port':4}
        source=self.directory/'source.py'; source.write_text('# frozen source\n')
        (self.directory/'source_manifest.json').write_text(json.dumps({'source.py':hashlib.sha256(source.read_bytes()).hexdigest()}))

    def result(self,passed=True):
        value={'passed':passed,'condition':self.condition,'environment_manifest_sha256':'environment-digest'}
        (self.directory/'results.json').write_text(json.dumps(value))
        return value

    def test_adopts_pass_and_failure_without_new_attempt_or_invented_exit_code(self):
        for passed in (True,False):
            value=self.result(passed)
            self.assertEqual(adopt_persisted_result(self.record,self.output,self.condition,'environment-digest'),value)
            self.assertEqual(self.record['status'],'finished')
            self.assertEqual(self.record['attempt'],1)
            self.assertNotIn('exit_code',self.record)

    def test_missing_result_leaves_attempt_unchanged(self):
        before=dict(self.record)
        self.assertIsNone(adopt_persisted_result(self.record,self.output,self.condition,'environment-digest'))
        self.assertEqual(self.record,before)

    def test_wrong_conditions_are_not_adopted(self):
        self.result()
        with self.assertRaises(ValueError):
            adopt_persisted_result(self.record,self.output,{'port':16},'environment-digest')
        self.assertEqual(self.record['status'],'running')

    def test_changed_source_is_not_adopted(self):
        self.result(); (self.directory/'source.py').write_text('# changed\n')
        with self.assertRaises(ValueError):
            adopt_persisted_result(self.record,self.output,self.condition,'environment-digest')

    def test_changed_completed_result_is_rejected(self):
        self.result()
        with self.assertRaises(ValueError):
            checked_result(self.directory,self.condition,'environment-digest','wrong-hash')
