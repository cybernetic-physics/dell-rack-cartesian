"""Preserve a static frame candidate and exact source; NOT a physical trial.

Only the saved root layer is copied, without external baseline sublayers.
Use run_reference.py to test and package an actual complete rack assembly.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
from pxr import Sdf, Usd, UsdGeom

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root))
from rack_robotics.carrier_mount_screen import screen_carrier_mount_sweep


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--environment',type=Path,required=True)
    parser.add_argument('--architecture',choices=('A','B','C'),required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--service-carriers',action='store_true')
    args=parser.parse_args()
    config=json.loads((args.environment/'config.json').read_text())
    if config['robot'][0]!=args.architecture:parser.error('Saved architecture mismatch')
    module_name,function_name={
        'A':('screw_frame','complete_screw_frame'),
        'B':('telescoping_frame','complete_telescoping_frame'),
        'C':('gantry_frame','complete_gantry_frame')}[args.architecture]
    import importlib
    transform=getattr(importlib.import_module('rack_robotics.'+module_name),function_name)
    output=args.output.resolve();output.mkdir(parents=True,exist_ok=False)
    source=args.environment.resolve()/'scene.usda'
    layer=Sdf.Layer.CreateNew(str(output/'scene.usda'))
    layer.TransferContent(Sdf.Layer.FindOrOpen(str(source)));layer.subLayerPaths=[]
    stage=Usd.Stage.Open(layer);UsdGeom.Xform.Define(stage,'/World')
    report=transform(stage,args.architecture)
    carrier_report=None
    if args.service_carriers:
        from rack_robotics.service_carriers import complete_service_carriers
        carrier_report=complete_service_carriers(stage,args.architecture,open_frame=True)
    audit=screen_carrier_mount_sweep(stage,True,True)
    layer.Save()
    def save(name,value):
        (output/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
    save('geometry_report.json',report);save('audit.json',audit)
    if carrier_report:save('service_carriers.json',carrier_report)
    paths=[root/'rack_robotics'/f'{name}.py' for name in
           {module_name,'gantry_frame','hardware_detail','carrier_mount_screen','service_carriers'}]+[Path(__file__).resolve()]
    hashes={}
    for path in paths:
        target=output/'source'/path.relative_to(root)
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target)
        hashes[str(path.relative_to(root))]=hashlib.sha256(target.read_bytes()).hexdigest()
    save('source_manifest.json',hashes)
    save('manifest.json',{'source_scene':str(source),'source_scene_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'scope':'Static copied root opinions WITHOUT rack baseline sublayers; no physical trial or full-rack clearance claim',
        'passed_box_screen':audit['passed']})
    print(json.dumps({'passed':audit['passed'],'pairs':audit['distinct_body_pairs_checked'],
                      'overlaps':len(audit['possible_overlaps']),'output':str(output)}))


if __name__=='__main__':main()
