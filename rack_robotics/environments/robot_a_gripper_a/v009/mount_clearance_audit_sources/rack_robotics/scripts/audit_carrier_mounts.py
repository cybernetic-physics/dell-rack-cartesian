"""Read a preserved USD; emit a new static carrier bracket audit without editing it."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
import sys
from pxr import Usd

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from rack_robotics.carrier_mount_screen import screen_carrier_mounts

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scene',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    source_dir=args.output.parent/(args.output.stem+'_sources')
    source_dir.mkdir(exist_ok=False)
    sources=(Path(__file__).resolve(),root/'rack_robotics/carrier_mount_screen.py')
    for path in sources:
        target=source_dir/path.relative_to(root); target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(path,target)
    report=screen_carrier_mounts(Usd.Stage.Open(str(args.scene.resolve())))
    report.update(scene=str(args.scene.resolve()),scene_sha256=hashlib.sha256(args.scene.read_bytes()).hexdigest(),
                  source_sha256={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in sources},source_directory=source_dir.name)
    with args.output.open('x') as target: target.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    sys.exit(0 if report['passed'] else 1)
