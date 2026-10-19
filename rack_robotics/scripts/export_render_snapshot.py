"""Export completed render products only; original full frame sets stay on the VM.

Stream a tar.gz containing verified videos/manifests/render source, selected
original PNGs, and the exact batch-state snapshot used to select products.
Never include a still-rendering directory or infer that the batch is complete.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import sys
import tarfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frame_indices(frames,count):
    if type(frames) is not int or frames<1 or type(count) is not int or count<2:
        raise ValueError('Positive frame count and at least two samples required')
    return sorted({round(i*(frames-1)/(count-1)) for i in range(count)})


def select_files(batch,state,count=9):
    manifest=json.loads((batch/'manifest.json').read_text())
    files={batch/'manifest.json'}
    mapping_digest=manifest.get('phase_cameras_input_sha256')
    if mapping_digest is not None:
        mapping=(batch/'phase_cameras_input.json').resolve()
        if not mapping.is_relative_to(batch.resolve()) or not mapping.is_file() or sha(mapping)!=mapping_digest:
            raise ValueError('Missing, changed or external phase-camera input')
        files.add(mapping)
    for name,digest in manifest['source_sha256'].items():
        path=(batch/name).resolve()
        if not path.is_relative_to(batch.resolve()) or sha(path)!=digest:
            raise ValueError('Changed or external batch source: '+name)
        files.add(path)
    selected={}
    products=[]
    for key,record in state['cases'].items():
        if record.get('status')!='captured':continue
        if not re.fullmatch('[ABC]{2}/(wide|rear|macro|side)',key):raise ValueError('Invalid case key')
        products.append((key,record.get('manifest_sha256'),True))
    for label,record in state.get('edits',{}).items():
        if record.get('status')!='edited':continue
        if not re.fullmatch('[ABC]{2}',label):raise ValueError('Invalid edit label')
        products.append((label+'/multi_angle',None,False))
    for key,expected,is_render in products:
        directory=batch/key
        report_path=directory/'manifest.json'
        if is_render and (not expected or sha(report_path)!=expected):
            raise ValueError('Changed capture manifest: '+key)
        report=json.loads(report_path.read_text())
        if sha(directory/'demo.mp4')!=report['video_sha256']:
            raise ValueError('Changed completed video: '+key)
        for name,digest in report.get('render_sources_sha256',{}).items():
            path=(directory/name).resolve()
            if not path.is_relative_to(directory.resolve()) or sha(path)!=digest:
                raise ValueError('Changed render source: '+key+'/'+name)
        files.update(p for p in directory.iterdir() if p.is_file() and p.suffix in ('.json','.py','.mp4'))
        indices=frame_indices(report['frames'],count) if is_render else []
        for index in indices:
            path=directory/'frames'/f'{index:05d}.png'
            if not path.is_file():raise ValueError('Missing original render frame: '+str(path))
            files.add(path)
        selected[key]={'manifest_sha256':sha(report_path),'video_sha256':report['video_sha256'],
                       'original_png_frame_indices':indices}
    if not selected:raise ValueError('No completed products to export')
    return sorted(files),selected


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--batch',type=Path,required=True)
    parser.add_argument('--sample-frames',type=int,default=9)
    args=parser.parse_args()
    batch=args.batch.resolve()
    state_bytes=(batch/'state.json').read_bytes()
    state=json.loads(state_bytes)
    files,selected=select_files(batch,state,args.sample_frames)
    collection={'batch_complete_at_snapshot':state.get('complete'),
                'state_sha256':hashlib.sha256(state_bytes).hexdigest(),'products':selected,
                'scope':'Completed media and selected original frames only; all original frames remain at source'}
    with tarfile.open(fileobj=sys.stdout.buffer,mode='w|gz') as archive:
        for path in files:archive.add(path,arcname=str(path.relative_to(batch.parent)),recursive=False)
        for name,data in [('state.json',state_bytes),('collection.json',(json.dumps(collection,indent=2)+'\n').encode())]:
            info=tarfile.TarInfo(batch.name+'/'+name);info.size=len(data)
            archive.addfile(info,io.BytesIO(data))


if __name__=='__main__':main()
