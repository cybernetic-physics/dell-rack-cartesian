"""Stream a consistent read-only snapshot of finished trials as tar.gz on stdout.

Running trial directories and derived render subdirectories are omitted. The state file embedded in the archive
is the exact one used to choose completed directories, even if the campaign
advances while its completed files are being read.
"""
import argparse
import io
import json
from pathlib import Path
import sys
import tarfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--campaign',type=Path,required=True)
args=p.parse_args(); campaign=args.campaign.resolve()
state_bytes=(campaign/'campaign_state.json').read_bytes()
state=json.loads(state_bytes)
roots=[campaign/'harness',campaign/'plan']
files=[campaign/'campaign_manifest.json']
for task in state['tasks'].values():
    if task.get('status')!='finished': continue
    directory=campaign/task['directory']
    # A finished physics trial may later contain an actively rendering replay.
    # Export its original evidence only, not arbitrary derived subdirectories.
    files.extend(p for p in directory.iterdir() if p.is_file())
    roots.extend(directory/name for name in ('source','harness') if (directory/name).is_dir())
for directory in roots:
    files.extend(p for p in directory.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as archive:
    for path in sorted(set(files)):
        archive.add(path,arcname=str(path.relative_to(campaign.parent)),recursive=False)
    info=tarfile.TarInfo(campaign.name+'/campaign_state.json'); info.size=len(state_bytes)
    archive.addfile(info,io.BytesIO(state_bytes))
