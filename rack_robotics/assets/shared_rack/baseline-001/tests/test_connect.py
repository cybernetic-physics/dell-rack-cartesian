"""Connection script regression tests using isolated fake network commands."""
import os,subprocess,tempfile,unittest
from pathlib import Path

SCRIPT=Path(__file__).resolve().parents[1]/'scripts/connect.sh'

class ConnectTests(unittest.TestCase):
    def run_script(self,occupied,healthy):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            commands={
                'lsof':'#!/bin/bash\n'+('echo "ssh 123 user LISTEN"\n' if occupied else 'exit 1\n'),
                'curl':'#!/bin/bash\n'+('case "$*" in *vnc.html*) echo noVNC;; *) echo "Dell rack";; esac\n' if healthy else 'exit 7\n'),
                'gcloud':'#!/bin/bash\necho STARTED_GCLOUD\n',
            }
            for name,contents in commands.items():
                path=root/name; path.write_text(contents); path.chmod(0o755)
            return subprocess.run(['/bin/bash',str(SCRIPT)],env={**os.environ,'PATH':tmp+os.pathsep+os.environ['PATH']},capture_output=True,text=True)

    def test_healthy_existing_connection_is_success(self):
        result=self.run_script(True,True)
        self.assertEqual(result.returncode,0)
        self.assertIn('Already connected',result.stdout)
        self.assertNotIn('STARTED_GCLOUD',result.stdout)

    def test_unhealthy_occupied_ports_do_not_start_or_kill(self):
        result=self.run_script(True,False)
        self.assertEqual(result.returncode,1)
        self.assertIn('No processes were stopped',result.stderr)
        self.assertNotIn('STARTED_GCLOUD',result.stdout)

    def test_free_ports_start_tunnel(self):
        result=self.run_script(False,False)
        self.assertEqual(result.returncode,0)
        self.assertIn('STARTED_GCLOUD',result.stdout)

if __name__=='__main__': unittest.main()
