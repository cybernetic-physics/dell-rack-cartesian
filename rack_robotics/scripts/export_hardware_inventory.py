"""Export a hash-bound saved-model component inventory, without simulation."""
import argparse
import csv
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from rack_robotics.hardware_inventory import inventory
from rack_robotics.mechanical_evidence import sha, verify_identity


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--properties',type=Path,required=True)
    parser.add_argument('--environment',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    env=args.environment.resolve(); properties=args.properties.resolve()
    props=json.loads(properties.read_text())
    verify_identity(props,env,env)
    if sha(properties.parent/'extract_source.py')!=props['source_sha256']:
        raise ValueError('Changed property extractor source')
    report=inventory(props)
    root=Path(__file__).resolve().parents[2]
    report.update(environment=str(env.relative_to(root)),
        environment_manifest_sha256=sha(env/'manifest.json'),
        properties_sha256=sha(properties),properties=str(properties.relative_to(root)),
        analysis_sha256=sha(root/'rack_robotics/hardware_inventory.py'))
    args.output.mkdir(parents=True,exist_ok=False)
    (args.output/'inventory.json').write_text(json.dumps(report,indent=2)+'\n')
    with (args.output/'components.csv').open('x',newline='') as stream:
        writer=csv.writer(stream)
        writer.writerow(['category','component_path','rigid_owner','body_x_mm','body_y_mm','body_z_mm','model_solids','unit_price_usd'])
        for row in report['components']:
            writer.writerow([row['category'],row['component_path'],row['rigid_owner'],
                *[round(v,6) for v in row['body_aligned_size_mm']],len(row['geometry_paths']),''])
    print(json.dumps({'environment':report['environment'],'counts':report['component_counts'],
        'rail_length_m':report['total_modeled_rail_length_m'],'complete_purchase_cost_usd':None}))


if __name__=='__main__': main()
