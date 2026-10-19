import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'rack_robotics/scripts'))
SPEC=importlib.util.spec_from_file_location('occupied_harness',ROOT/'rack_robotics/scripts/screen_occupied_ports.py')
module=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)


class OccupiedHarnessTest(unittest.TestCase):
    def test_freezes_current_runner_dependencies(self):
        with tempfile.TemporaryDirectory() as temporary:
            frozen=Path(temporary)/'harness'
            module.freeze_harness(ROOT,frozen)
            for source,target in module.COMMON_HARNESS_FILES:
                self.assertEqual((ROOT/'rack_robotics'/source).read_bytes(),
                                 (frozen/'benchmarking'/target).read_bytes())
            result=subprocess.run([sys.executable,'-c',
                'from benchmarking.timing import ExperimentTiming; '
                'from benchmarking.carrier_validation import carrier_integrity_checks; '
                'assert ExperimentTiming(480).physics_hz == 480; '
                'assert not all(carrier_integrity_checks([], []).values())'],
                cwd=frozen,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)


if __name__=='__main__':unittest.main()
