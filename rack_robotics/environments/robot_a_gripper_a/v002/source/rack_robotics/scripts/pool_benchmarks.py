"""Verify campaign snapshots and pool only disjoint, same-protocol trials."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from rack_robotics.benchmarking.pooling import pool_campaigns
from rack_robotics.scripts.summarize_benchmark import summarize


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    bundles = []
    for campaign in args.campaign:
        manifest = json.loads((campaign/'campaign_manifest.json').read_text())
        plan = json.loads((campaign/'plan/plan.json').read_text())
        summary = summarize(campaign)
        conditions = {f'trial-{i:03d}': json.loads((campaign/'plan'/f'trial-{i:03d}.json').read_text())
                      for i in range(plan['count_per_environment'])}
        bundles.append(dict(manifest=manifest, plan=plan, summary=summary, conditions=conditions))
    report = pool_campaigns(bundles)
    report['source_snapshots'] = [{key: b['summary'][key] for key in (
        'campaign_directory', 'campaign_manifest_sha256', 'campaign_state_snapshot_sha256')}
        for b in bundles]
    report['analysis_sha256'] = {
        str(path.relative_to(Path(__file__).resolve().parents[2])): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in (Path(__file__).resolve(), Path(__file__).with_name('summarize_benchmark.py'),
                     Path(__file__).parents[1]/'benchmarking/pooling.py',
                     Path(__file__).parents[1]/'benchmarking/metrics.py')}
    with args.output.open('x') as target:
        target.write(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report['designs'], indent=2))


if __name__ == '__main__':
    main()
