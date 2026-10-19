import io
import json
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import unittest


class CampaignSnapshotTests(unittest.TestCase):
    def test_includes_finished_physics_not_running_trials_or_render_directories(self):
        with tempfile.TemporaryDirectory() as tmp:
            campaign=Path(tmp)/'campaign'
            for name in ('harness','plan','AA/done/source','AA/done/harness','AA/done/replay_wide001/frames','AA/running'):
                (campaign/name).mkdir(parents=True,exist_ok=True)
            state={'tasks':{'AA/control':{'status':'finished','directory':'AA/done'},
                            'AA/trial-000':{'status':'running','directory':'AA/running'}}}
            (campaign/'campaign_state.json').write_text(json.dumps(state))
            for name in ('campaign_manifest.json','plan/plan.json','harness/runner.py',
                         'AA/done/results.json','AA/done/source/controller.py','AA/done/harness/runner.py',
                         'AA/done/replay_wide001/frames/00001.png','AA/running/results.json'):
                (campaign/name).write_text('{}')
            script=Path(__file__).resolve().parents[1]/'rack_robotics/scripts/export_campaign_snapshot.py'
            data=subprocess.check_output([sys.executable,str(script),'--campaign',str(campaign)])
            with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
                names=archive.getnames()
                self.assertIn('campaign/AA/done/results.json',names)
                self.assertIn('campaign/AA/done/source/controller.py',names)
                self.assertFalse(any('/replay_' in name or '/running/' in name for name in names))
                self.assertEqual(json.load(archive.extractfile('campaign/campaign_state.json')),state)
