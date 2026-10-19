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
              'release_gripper':'macro', 'release_datum':'macro', 'retract':'side', 'park':'wide',
              'recover_grasp_open':'macro', 'recover_grasp_clear_datum':'macro',
              'recover_grasp_retreat':'rear', 'recover_latch_reset':'macro',
              'recover_insert_release':'macro', 'recover_insert_retreat':'rear'}


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def native_resolution(value):
    if (not isinstance(value,list) or len(value)!=2
            or any(type(v) is not int or v%2 for v in value)
            or value[0]<1920 or value[1]<1080 or value[0]*9!=value[1]*16):
        raise ValueError('Expected even native16:9 dimensions at least1920x1080')
    return tuple(value)


def phase_cameras(overrides=None):
    mapping=dict(PHASE_VIEW)
    if overrides is not None:
        if not isinstance(overrides,dict) or any(k not in PHASE_VIEW or v not in VIEWS
                                               for k,v in overrides.items()):
            raise ValueError('Camera overrides must map known task phases to verified views')
        mapping.update(overrides)
    return mapping


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
                or sha(path/'demo.mp4') != manifest.get('video_sha256')):
            raise ValueError('Incomplete, changed, or incompatible replay: '+view)
        native_resolution(manifest.get('resolution'))
        manifests[view] = manifest
    reference = manifests['wide']
    for view, manifest in manifests.items():
        for name in ('source_sha256','frames','trajectory_file','resolution'):
            if manifest[name] != reference[name]: raise ValueError('Mixed source/timing: '+view+'/'+name)
    return manifests


def shot_list(samples,overrides=None):
    mapping=phase_cameras(overrides)
    shots = []
    for frame, sample in enumerate(samples):
        phase = sample['phase']
        if phase not in PHASE_VIEW or not re.fullmatch('[a-z_]+',phase):
            raise ValueError('Unmapped phase: '+phase)
        view = mapping[phase]
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
    parser.add_argument('--phase-cameras',type=Path,
                        help='Optional JSON phase:view overrides for reviewed camera choices; no frames omitted or retimed')
    args=parser.parse_args()
    paths={view:getattr(args,view).resolve() for view in VIEWS}
    manifests=verify_inputs(paths); reference=manifests['wide']
    width,height=native_resolution(reference['resolution'])
    mapping_bytes=args.phase_cameras.read_bytes() if args.phase_cameras else None
    overrides=json.loads(mapping_bytes) if mapping_bytes is not None else None
    mapping=phase_cameras(overrides)
    mapping_sha=hashlib.sha256(mapping_bytes).hexdigest() if mapping_bytes is not None else None
    for name,digest in reference['source_sha256'].items():
        if sha(args.attempt/name)!=digest: raise ValueError('Changed physical source: '+name)
    with (args.attempt/reference['trajectory_file']).open() as source:
        header=json.loads(next(source)); samples=[json.loads(line) for line in source]
    if len(samples)!=reference['frames'] or header['fps']!=30: raise ValueError('Frame count mismatch')
    shots=shot_list(samples,overrides)
    output=args.output.resolve(); output.mkdir(parents=True,exist_ok=False)
    shutil.copy2(__file__,output/'edit_source.py')
    if args.phase_cameras: (output/'phase_cameras_input.json').write_bytes(mapping_bytes)
    (output/'phase_cameras.json').write_text(json.dumps(mapping,indent=2)+'\n')
    (output/'shots.json').write_text(json.dumps(shots,indent=2)+'\n')
    command=['ffmpeg','-nostdin','-v','warning']
    for view in VIEWS: command+=['-i',str(paths[view]/'demo.mp4')]
    filters=[]
    for index,shot in enumerate(shots):
        filters.append(f"[{VIEWS.index(shot['view'])}:v]trim=start_frame={shot['start_frame']}:end_frame={shot['end_frame_exclusive']},"
                       f"setpts=PTS-STARTPTS,drawtext=text='{shot['view'].upper()} - {shot['phase'].replace('_',' ')}':"
                       f"fontcolor=white:fontsize={round(26*height/1080)}:x={round(20*width/1920)}:"
                       f"y=h-{round(55*height/1080)}:box=1:boxcolor=black@0.6[s{index}]")
    filters.append(''.join(f'[s{i}]' for i in range(len(shots)))+f'concat=n={len(shots)}:v=1:a=0[out]')
    command+=['-filter_complex',';'.join(filters),'-map','[out]','-an','-c:v','libx264','-crf','18',
              '-pix_fmt','yuv420p','-r','30','-movflags','+faststart',str(output/'demo.mp4')]
    subprocess.run(command,check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-select_streams','v:0',
        '-show_entries','stream=width,height,r_frame_rate,nb_read_frames,duration','-of','json',str(output/'demo.mp4')]))
    stream=probe['streams'][0]
    if (stream['width'],stream['height'],stream['r_frame_rate'],int(stream['nb_read_frames'])) != (width,height,'30/1',len(samples)):
        raise ValueError('Edited video lost frames or changed dimensions/cadence')
    if abs(float(stream['duration'])-len(samples)/30)>1e-5: raise ValueError('Edited duration mismatch')
    verify_inputs(paths)
    if args.phase_cameras and sha(args.phase_cameras)!=mapping_sha:
        raise ValueError('Camera choices changed during editing')
    report={'schema':'synchronized_physics_edit_v1','source_sha256':reference['source_sha256'],
        'inputs':{view:{'directory':str(paths[view]),'manifest_sha256':sha(paths[view]/'manifest.json'),
                        'video_sha256':manifests[view]['video_sha256']} for view in VIEWS},
        'shots':shots,'frames':len(samples),'fps':30,'resolution':[width,height],
        'phase_cameras':mapping,'phase_cameras_input_sha256':mapping_sha,
        'native_resolution_preserved':True,'upscaled_inputs':False,
        'video_sha256':sha(output/'demo.mp4'),'edit_source_sha256':sha(output/'edit_source.py'),
        'ffprobe':probe,'temporal_validation_passed':True,
        'scope':'Exact frame cuts across the same measured successful trial; visual acceptance is separate'}
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'frames':len(samples),'shots':len(shots),'video':str(output/'demo.mp4')}))


if __name__=='__main__': main()
