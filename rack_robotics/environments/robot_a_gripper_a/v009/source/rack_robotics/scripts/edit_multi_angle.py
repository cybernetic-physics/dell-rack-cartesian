"""Frame-exact camera cuts from verified, synchronized physics replays.

No interpolation, retiming, synthesized motion, or mixing of different trials.
Source renders retain their own quality reviews; this script verifies temporal
and provenance consistency, not artistic or hardware quality.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess


VIEWS = ('wide','rear','macro','side')
PHASE_VIEW = {'initialize':'wide', 'approach':'rear', 'align':'rear', 'align_datum':'rear',
              'grasp':'macro', 'release_latch':'macro', 'withdraw':'side', 'separate':'side',
              'realign':'rear', 'insert':'macro', 'seat_and_latch':'macro', 'seat_nudge':'macro',
              'release_gripper':'macro', 'retract':'side', 'park':'wide'}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs(paths):
    manifests = {}
    for view in VIEWS:
        path = paths[view]; manifest = json.loads((path/'manifest.json').read_text())
        if (manifest.get('view') != view or manifest.get('full_trajectory') is not True
                or manifest.get('source_passed') is not True or manifest.get('fps') != 30
                or manifest.get('start_frame') != 0 or manifest.get('initialization_only')
                or manifest.get('physics_running') is not False
                or manifest.get('replay_only') is not True
                or manifest.get('frames') != manifest.get('recording_validation',{}).get('samples')
                or manifest.get('resolution') != [1920,1080]
                or sha(path/'demo.mp4') != manifest.get('video_sha256')):
            raise ValueError('Incomplete, changed, or incompatible replay: '+view)
        manifests[view] = manifest
    reference = manifests['wide']
    for view, manifest in manifests.items():
        for name in ('source_sha256','frames','trajectory_file'):
            if manifest[name] != reference[name]: raise ValueError('Mixed source/timing: '+view+'/'+name)
    return manifests


def shot_list(samples):
    shots = []
    for frame, sample in enumerate(samples):
        phase = sample['phase']
        if phase not in PHASE_VIEW or not re.fullmatch('[a-z_]+',phase):
            raise ValueError('Unmapped phase: '+phase)
        view = PHASE_VIEW[phase]
        if shots and shots[-1]['phase'] == phase:
            shots[-1]['end_frame_exclusive'] = frame+1
        else:
            shots.append({'view':view,'phase':phase,'start_frame':frame,'end_frame_exclusive':frame+1})
    if not shots: raise ValueError('Empty trajectory')
    return shots


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for view in VIEWS: parser.add_argument('--'+view,type=Path,required=True)
    parser.add_argument('--attempt',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    paths={view:getattr(args,view).resolve() for view in VIEWS}
    manifests=verify_inputs(paths); reference=manifests['wide']
    for name,digest in reference['source_sha256'].items():
        if sha(args.attempt/name)!=digest: raise ValueError('Changed physical source: '+name)
    with (args.attempt/reference['trajectory_file']).open() as source:
        header=json.loads(next(source)); samples=[json.loads(line) for line in source]
    if len(samples)!=reference['frames'] or header['fps']!=30: raise ValueError('Frame count mismatch')
    shots=shot_list(samples)
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=False)
    shutil.copy2(__file__,output/'edit_source.py')
    (output/'shots.json').write_text(json.dumps(shots,indent=2)+'\n')
    command=['ffmpeg','-nostdin','-v','warning']
    for view in VIEWS: command+=['-i',str(paths[view]/'demo.mp4')]
    filters=[]
    for index,shot in enumerate(shots):
        filters.append(f"[{VIEWS.index(shot['view'])}:v]trim=start_frame={shot['start_frame']}:end_frame={shot['end_frame_exclusive']},"
                       f"setpts=PTS-STARTPTS,drawtext=text='{shot['view'].upper()} - {shot['phase'].replace('_',' ')}':"
                       f"fontcolor=white:fontsize=26:x=20:y=h-55:box=1:boxcolor=black@0.6[s{index}]")
    filters.append(''.join(f'[s{i}]' for i in range(len(shots)))+f'concat=n={len(shots)}:v=1:a=0[out]')
    command+=['-filter_complex',';'.join(filters),'-map','[out]','-an','-c:v','libx264','-crf','18',
              '-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(output/'demo.mp4')]
    subprocess.run(command,check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
        '-show_entries','stream=width,height,r_frame_rate,nb_read_frames,duration','-of','json',str(output/'demo.mp4')]))
    stream=probe['streams'][0]
    if (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_read_frames'])) != (1920,1080,'30/1',len(samples)):
        raise ValueError('Edited video lost frames or changed dimensions/cadence')
    if abs(float(stream['duration'])-len(samples)/30)>1e-5: raise ValueError('Edited duration mismatch')
    verify_inputs(paths)
    report={'schema':'synchronized_physics_edit_v1','source_sha256':reference['source_sha256'],
        'inputs':{view:{'directory':str(paths[view]),'manifest_sha256':sha(paths[view]/'manifest.json'),
                        'video_sha256':manifests[view]['video_sha256']} for view in VIEWS},
        'shots':shots,'frames':len(samples),'fps':30,'resolution':[1920,1080],
        'video_sha256':sha(output/'demo.mp4'),'edit_source_sha256':sha(output/'edit_source.py'),
        'ffprobe':probe,'temporal_validation_passed':True,
        'scope':'Exact frame cuts across the same measured successful trial; visual acceptance is separate'}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'frames':len(samples),'shots':len(shots),'video':str(output/'demo.mp4')}))


if __name__=='__main__': main()
