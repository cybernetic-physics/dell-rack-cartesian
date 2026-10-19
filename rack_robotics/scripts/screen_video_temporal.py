"""Decode every selected MP4 frame and produce auditable temporal review sheets.

All metric frames are480x270 with the bottom caption band excluded. This is a
coarse temporal screen, not proof of local detail, physical correctness or
photorealism. Source files are verified and never edited. Original-resolution
renders remain the authority for fine-detail review.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from PIL import Image, ImageDraw
from rack_robotics.temporal_quality import frame_metrics, screen_flags, phase_spans, inspection_indices
from rack_robotics.scripts.build_gallery import verify_media


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_frame(stream, length):
    parts = []; size = 0
    while size < length:
        chunk = stream.read(length-size)
        if not chunk:
            if size:
                raise ValueError('Truncated decoded RGB frame')
            return None
        parts.append(chunk); size += len(chunk)
    return b''.join(parts)


def make_sheet(destination, indices, frames, samples, label):
    columns = 3; tile_width = 480; tile_height = 300
    sheet = Image.new('RGB', (columns*tile_width, ((len(indices)+columns-1)//columns)*tile_height), '#121820')
    draw = ImageDraw.Draw(sheet)
    for tile, index in enumerate(indices):
        x = tile % columns * tile_width; y = tile // columns * tile_height
        sheet.paste(frames[index], (x, y))
        draw.text((x+5, y+274), f'{label} f{index:04d} {index/30:.2f}s {samples[index]["phase"]}', fill='white')
    sheet.save(destination)


def analyze(selected, output):
    directory = ROOT/'rack_robotics/experiments'/selected['directory']
    attempt = ROOT/'rack_robotics/experiments'/selected['attempt'] if selected.get('attempt') else None
    provenance = verify_media(directory, ROOT, attempt)
    manifest = json.loads((directory/'manifest.json').read_text())
    attempt = ROOT/provenance['source_attempt']
    trajectory = attempt/manifest.get('trajectory_file', 'trajectory.jsonl')
    with trajectory.open() as stream:
        header = json.loads(next(stream)); samples = [json.loads(line) for line in stream]
    if header['fps'] != 30 or len(samples) != manifest['frames']:
        raise ValueError('Source trajectory timing mismatch')
    video = directory/'demo.mp4'
    probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-show_entries', 'stream=codec_name,width,height,r_frame_rate,nb_frames', '-of', 'json', str(video)]))
    info = probe['streams'][0]
    if (info['codec_name'] != 'h264' or info['r_frame_rate'] != '30/1'
            or [info['width'], info['height']] != manifest['resolution']
            or int(info['nb_frames']) != len(samples)):
        raise ValueError('Native encoded timing/format differs from manifest')
    output.mkdir(parents=True, exist_ok=False)
    cuts = [s['start_frame'] for i, s in enumerate(manifest.get('shots', []))
            if i and s['view'] != manifest['shots'][i-1]['view']]
    indices = inspection_indices(samples, detail=manifest.get('view') == 'macro')
    selected_frames = {}; rows = []; previous = None
    command = ['ffmpeg', '-nostdin', '-v', 'error', '-xerror', '-threads', '2', '-filter_threads', '2', '-i', str(video),
               '-an', '-vf', 'scale=480:270', '-vsync', '0', '-pix_fmt', 'rgb24', '-f', 'rawvideo', '-']
    with (output/'decode.log').open('xb') as errors:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=errors)
        try:
            while True:
                data = read_frame(process.stdout, 480*270*3)
                if data is None:
                    break
                index = len(rows)
                if index >= len(samples):
                    raise ValueError('Decoded more frames than the physical trajectory')
                frame = Image.frombytes('RGB', (480, 270), data)
                # Exclude the editor's bottom caption band from differences.
                metric_frame = frame.crop((0, 0, 480, 248))
                rows.append({'frame': index, 'phase': samples[index]['phase'],
                             **frame_metrics(metric_frame, previous)})
                previous = metric_frame
                if index in indices:
                    selected_frames[index] = frame.copy()
            code = process.wait()
        except BaseException:
            process.terminate(); process.wait()
            raise
    if code != 0 or len(rows) != len(samples):
        raise ValueError('Full decode failed or omitted frames')
    flags = screen_flags(rows, cuts)
    with gzip.open(output/'frame_metrics.jsonl.gz', 'xt') as target:
        for row in rows: target.write(json.dumps(row)+'\n')
    sheets = []
    for start in range(0, len(indices), 12):
        path = output/f'sheet-{start//12:03d}.png'
        group = indices[start:start+12]
        make_sheet(path, group, selected_frames, samples, selected['design']+'/'+manifest.get('view', 'edit'))
        sheets.append({'file': path.name, 'sha256': sha(path), 'frames': group})
    report = {'schema': 'full_video_temporal_screen_v1', 'technical_decode_passed': True,
        'visual_acceptance': False, 'selection': selected, 'provenance': provenance,
        'manifest_sha256': sha(directory/'manifest.json'), 'trajectory_sha256': sha(trajectory),
        'codec': info, 'decoded_frames': len(rows), 'metric_resolution': [480, 248],
        'declared_camera_cuts': cuts, 'phase_spans': phase_spans(samples), 'review_flags': flags,
        'maximum_mean_absolute_change_excluding_cuts': max(r['mean_absolute_change'] for r in rows if r['frame'] not in cuts),
        'minimum_visible_fraction_above_15': min(r['visible_fraction_above_15'] for r in rows),
        'inspection_sheets': sheets, 'frame_metrics_sha256': sha(output/'frame_metrics.jsonl.gz'),
        'scope': __doc__}
    (output/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--designs', help='Optional comma-separated subset')
    args = parser.parse_args()
    selected = json.loads(args.selection.read_text())
    if args.designs:
        requested = set(args.designs.split(','))
        if not requested <= {s['design'] for s in selected}:
            raise ValueError('Unknown design in selection')
        selected = [s for s in selected if s['design'] in requested]
    output = args.output.resolve(); output.mkdir(parents=True, exist_ok=False)
    shutil.copy2(args.selection, output/'selection.json')
    sources = [Path(__file__), ROOT/'rack_robotics/temporal_quality.py', ROOT/'rack_robotics/scripts/build_gallery.py']
    for path in sources: shutil.copy2(path, output/path.name)
    manifest = {'schema': 'temporal_review_inputs_v1', 'selection_sha256': sha(args.selection),
                'source_sha256': {p.name: sha(p) for p in sources}, 'products': selected}
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    products = []
    for index, selection in enumerate(selected):
        name = f'{index:02d}-{selection["design"]}'
        report = analyze(selection, output/name)
        products.append({'directory': name, 'selection': selection,
                         'report_sha256': sha(output/name/'report.json'),
                         'frames': report['decoded_frames'], 'flag_count': len(report['review_flags'])})
        print('TEMPORAL_SCREEN', name, report['decoded_frames'], 'frames', len(report['review_flags']), 'flags', flush=True)
    (output/'summary.json').write_text(json.dumps({'complete': True, 'visual_acceptance': False,
        'manifest_sha256': sha(output/'manifest.json'), 'products': products}, indent=2)+'\n')


if __name__ == '__main__': main()
