"""Preserve a reference attempt as a composed, independently runnable environment.

Run with the project Python (usd-core) or Isaac Python. Existing outputs are never
overwritten. Packaging is not a reload test; run the generated demo separately.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil

parser=argparse.ArgumentParser()
parser.add_argument('--attempt',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args,_=parser.parse_known_args()
try:
    from pxr import Gf, Sdf, Usd, UsdGeom
except ModuleNotFoundError:
    # Isaac's bundled USD is exposed by Kit startup; usd-core environments do
    # not need this fallback. No simulation is run during packaging.
    from isaacsim import SimulationApp
    import atexit
    app=SimulationApp({'headless':True,'multi_gpu':False,'width':640,'height':480})
    atexit.register(app.close)
    from pxr import Gf, Sdf, Usd, UsdGeom
attempt=args.attempt.resolve(); output=args.output.resolve()
root=Path(__file__).resolve().parents[2]
baseline=root/'rack_robotics/assets/shared_rack/baseline-001'
result=json.loads((attempt/'results.json').read_text())
if result['scope']!='full_rack': raise ValueError('Only full-rack attempts can be packaged as rack environments')
output.mkdir(parents=True,exist_ok=False)
original=Sdf.Layer.FindOrOpen(str(attempt/'scene.usda'))
layer=Sdf.Layer.CreateNew(str(output/'scene.usda')); layer.TransferContent(original)
layer.subLayerPaths=[os.path.relpath((attempt/p).resolve(),output) for p in original.subLayerPaths]
layer.subLayerPaths.append('cameras.usda'); layer.Save()
views={'wide':((1.2,3.4,2.1),(0,.3,1.25)),
       'rear':((.50,1.25,1.98),(0,.55,1.68)),
       'macro':((.2325,.589,1.72),(.1875,.429,1.66)),
       'side':((.9,1.15,1.95),(0,.65,1.55))}
cameras=Usd.Stage.CreateNew(str(output/'cameras.usda'))
UsdGeom.SetStageUpAxis(cameras,'Z'); UsdGeom.SetStageMetersPerUnit(cameras,1)
for name,(eye,target) in views.items():
    camera=UsdGeom.Camera.Define(cameras,'/World/Cameras/'+name)
    camera.CreateClippingRangeAttr(Gf.Vec2f(.001,1000))
    camera.AddTransformOp().Set(Gf.Matrix4d().SetLookAt(Gf.Vec3d(*eye),Gf.Vec3d(*target),Gf.Vec3d(0,0,1)).GetInverse())
cameras.GetRootLayer().Save()
for name in ('results.json','trajectory.jsonl','diagnostic.png','physics_integrity.json'):
    if (attempt/name).exists(): shutil.copy2(attempt/name,output/name)
for source in (root/'rack_robotics').rglob('*.py'):
    relative=source.relative_to(root)
    if any(p in relative.parts for p in ('assets','research','experiments','environments','__pycache__')): continue
    target=output/'source'/relative; target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
config={'robot':'A_dual_supported_screw','gripper':'A_precision_parallel',
        'baseline':os.path.relpath(baseline,output),'scene':'scene.usda',
        'physics_dt':1/240,'recording_fps':30,'target_port':1,
        'initialization':'Physical pre-seat using baseline hand drive; remove it before robot trial',
        'camera_paths':{name:'/World/Cameras/'+name for name in views},
        'status':'single_feasibility_pass' if result['passed'] else 'failed_feasibility',
        'reload_verified':False,'randomized_trials':0,
        'limitations':result['limitations']}
(output/'config.json').write_text(json.dumps(config,indent=2)+'\n')
launcher='''"""Fresh-session execution of this saved assembly; requires --output NEW_DIR."""
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
'''
(output/'demo.py').write_text(launcher)
hashes={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest()
        for p in output.rglob('*') if p.is_file()}
(output/'manifest.json').write_text(json.dumps({'source_attempt':str(attempt),
    'tested_source':json.loads((attempt/'source_manifest.json').read_text()),
    'packaged_file_sha256':hashes,'baseline_manifest':str(baseline/'manifest.json'),
    'baseline_manifest_sha256':hashlib.sha256((baseline/'manifest.json').read_bytes()).hexdigest(),
    'reload_status':'Not yet tested; packaging alone is not a verification',
    'simulation':'Isaac Sim 6.0.1-rc.7 / PhysX contact-driven latch',
    'hardware_references':['https://schunk.com/us/en/gripping-systems/parallel-gripper/egp/c/PGR_1593',
                           'https://www.hiwin.us/wp-content/uploads/linear_guideways.pdf']},indent=2)+'\n')
print(output)
