from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class RenderGpuTest(unittest.TestCase):
    def test_negative_gpu_rejected_before_output_or_simulator_start(self):
        script=Path(__file__).resolve().parents[1]/'rack_robotics/scripts/render_replay.py'
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'must_not_exist'
            result=subprocess.run([sys.executable,str(script),'--attempt',directory,
                                   '--output',str(output),'--gpu','-1'],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn('GPU index must be nonnegative',result.stderr)
            self.assertFalse(output.exists())
