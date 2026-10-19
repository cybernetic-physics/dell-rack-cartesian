"""Fresh-session execution of this saved assembly; requires --output NEW_DIR."""
import json
from pathlib import Path
import runpy
import sys
here=Path(__file__).resolve().parent
config=json.loads((here/'config.json').read_text())
runner=here/'source/rack_robotics/scripts/run_reference.py'
sys.argv=[str(runner),'--scene',str(here/config['scene']),
          '--baseline',str((here/config['baseline']).resolve()),*sys.argv[1:]]
runpy.run_path(str(runner),run_name='__main__')
