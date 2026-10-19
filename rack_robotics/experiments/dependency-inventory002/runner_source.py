"""Index all preserved dependency files without starting Isaac or changing USD."""
import argparse
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from rack_robotics.dependency_inventory import inventory, digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',type=Path,default=ROOT)
    parser.add_argument('--runtime',type=Path,default=Path('/isaac-sim'))
    parser.add_argument('--audit',type=Path,required=True)
    parser.add_argument('--asset-search-path',type=Path,action='append',default=[])
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    from pxr import Ar, Usd, UsdUtils
    for path in args.asset_search_path:
        if not path.is_dir(): raise ValueError('Missing installed asset library: '+str(path))
    Ar.DefaultResolver.SetDefaultSearchPath([str(p.resolve()) for p in args.asset_search_path])
    args.output.mkdir(parents=True,exist_ok=False)
    source_hashes = {}
    for source,name in ((Path(__file__),'runner_source.py'),(ROOT/'rack_robotics/dependency_inventory.py','inventory_source.py')):
        shutil.copy2(source,args.output/name); source_hashes[name] = digest(args.output/name)
    def dependencies(scene):
        layers,assets,unresolved = UsdUtils.ComputeAllDependencies(str(scene))
        return [layer.realPath for layer in layers],list(assets),list(unresolved)
    def progress(name,layers,assets): print('DEPENDENCY_CLOSURE',name,layers,assets,flush=True)
    try:
        report = inventory(args.project,args.runtime,args.audit,dependencies,progress)
        report.update(usd_version=list(Usd.GetVersion()),asset_search_paths=[str(p.resolve()) for p in args.asset_search_path],
                      source_sha256=source_hashes)
        report['runtime_definition'] = {'path':'infra/Dockerfile','sha256':digest(args.project/'infra/Dockerfile'),
            'base_image_line':next(line for line in (args.project/'infra/Dockerfile').read_text().splitlines() if line.startswith('FROM ')),
            'scope':'Declared pinned runtime prerequisite, not a new runtime installation test'}
        (args.output/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('passed','preserved_versions','unique_files','unique_file_bytes')}),flush=True)
    except Exception as error:
        (args.output/'failure.json').write_text(json.dumps({'passed':False,'error':str(error),'source_sha256':source_hashes},indent=2)+'\n')
        raise


if __name__=='__main__': main()
