"""Verify temporal-review files; optionally inspect every encoded presentation time.

Metric recomputation here covers flags derived from saved per-frame metrics,
not a second RGB decode. Visual acceptance remains a separate recorded review.
"""
import argparse
import gzip
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from rack_robotics.scripts.screen_video_temporal import sha
from rack_robotics.scripts.build_gallery import verify_media
from rack_robotics.temporal_quality import screen_flags, inspection_indices, phase_spans, validate_timestamps


def same_render_identity(current, recorded):
    """Later playback checks may be added without changing immutable media.

    verify_media still verifies every present playback report against the MP4.
    Its mutable QA annotations are not part of the recorded render identity.
    """
    fields = ('video_sha256', 'source_task_passed', 'source_attempt',
              'full_trajectory', 'source_hashes_verified')
    return all(key in current and key in recorded and current[key] == recorded[key]
               for key in fields)


def verify(output, timestamps=False):
    summary = json.loads((output/'summary.json').read_text())
    manifest = json.loads((output/'manifest.json').read_text())
    if summary['complete'] is not True or summary['manifest_sha256'] != sha(output/'manifest.json'):
        raise ValueError('Incomplete or changed temporal review')
    for name, digest in manifest['source_sha256'].items():
        if sha(output/name) != digest: raise ValueError('Changed analysis source')
    if sha(output/'selection.json') != manifest['selection_sha256']:
        raise ValueError('Changed media selection')
    if [p['selection'] for p in summary['products']] != manifest['products']:
        raise ValueError('Review omitted or reordered selected products')
    products = []
    for product in summary['products']:
        folder = output/product['directory']
        if sha(folder/'report.json') != product['report_sha256']:
            raise ValueError('Changed product report')
        report = json.loads((folder/'report.json').read_text())
        selected = product['selection']
        directory = ROOT/'rack_robotics/experiments'/selected['directory']
        attempt = ROOT/'rack_robotics/experiments'/selected['attempt'] if selected.get('attempt') else None
        provenance = verify_media(directory, ROOT, attempt)
        source = json.loads((directory/'manifest.json').read_text())
        if (not same_render_identity(provenance, report['provenance'])
                or sha(directory/'manifest.json') != report['manifest_sha256']):
            raise ValueError('Changed video/provenance')
        trajectory = ROOT/provenance['source_attempt']/source.get('trajectory_file', 'trajectory.jsonl')
        if sha(trajectory) != report['trajectory_sha256']:
            raise ValueError('Changed measured trajectory')
        with trajectory.open() as stream:
            next(stream); samples = [json.loads(line) for line in stream]
        if sha(folder/'frame_metrics.jsonl.gz') != report['frame_metrics_sha256']:
            raise ValueError('Changed frame metrics')
        with gzip.open(folder/'frame_metrics.jsonl.gz', 'rt') as stream:
            rows = [json.loads(line) for line in stream]
        if (len(rows) != len(samples) or len(rows) != report['decoded_frames']
                or [r['frame'] for r in rows] != list(range(len(rows)))
                or [r['phase'] for r in rows] != [s['phase'] for s in samples]
                or phase_spans(samples) != report['phase_spans']):
            raise ValueError('Temporal coverage mismatch')
        cuts = [s['start_frame'] for i, s in enumerate(source.get('shots', []))
                if i and s['view'] != source['shots'][i-1]['view']]
        if cuts != report['declared_camera_cuts'] or screen_flags(rows, cuts) != report['review_flags']:
            raise ValueError('Temporal flags or declared cuts differ')
        indices = inspection_indices(samples, detail=source.get('view') == 'macro')
        if indices != [index for sheet in report['inspection_sheets'] for index in sheet['frames']]:
            raise ValueError('Missing phase-sampled review frames')
        for sheet in report['inspection_sheets']:
            if sha(folder/sheet['file']) != sheet['sha256']:
                raise ValueError('Changed review sheet')
        result = {'directory': product['directory'], 'design': selected['design'],
                  'video_sha256': provenance['video_sha256'], 'frames': len(rows),
                  'flags': report['review_flags'], 'sheets': len(report['inspection_sheets']),
                  'inspection_sample_count': len(indices)}
        if timestamps:
            probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
                '-show_frames', '-show_entries', 'frame=best_effort_timestamp_time', '-of', 'json', str(directory/'demo.mp4')]))
            result['timestamps'] = validate_timestamps([float(r['best_effort_timestamp_time']) for r in probe['frames']], len(rows))
        products.append(result)
    return {'schema': 'temporal_review_verification_v1', 'passed': True,
            'visual_acceptance': False, 'review_manifest_sha256': sha(output/'manifest.json'),
            'verifier_source_sha256': sha(Path(__file__)), 'products': products,
            'scope': __doc__}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timestamps', action='store_true')
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    report = verify(args.input, args.timestamps)
    with args.output.open('x') as target: json.dump(report, target, indent=2)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
