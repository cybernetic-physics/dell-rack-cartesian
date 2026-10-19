"""Build a self-contained, immutable, SSH-only comparison gallery snapshot.

Copies only explicitly selected artifacts, never exposes the project root or
follows external paths. Missing media stays visibly pending. No new server,
cloud resource, or public service is provisioned by this script.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil


ROOT = Path(__file__).resolve().parents[2]
ARCHITECTURES = {
    'A': ('Dual-supported screw gantry', 'Two rack-supported uprights, moving bridge and short insertion slide.',
          'https://github.com/matthew-yates/openbuildsParts'),
    'B': ('Side-mounted telescoping carriage', 'Vertical side rail with two nested horizontal stages; substantial left overhang.',
          'https://hiwin.com/products/linear-guideways/'),
    'C': ('Stationary-motor CoreXZ', 'Coupled elastic belt transmission with passive X/Z guide joints; not a commercial digital twin.',
          'https://corexy.com/theory.html'),
}
TOOLS = {
    'A': ('Precision parallel + latch tongue', 'EGP25-envelope custom fingertips; independent contact-driven latch press.',
          'https://schunk.com/de/en/gripping-systems/parallel-gripper/egp/egp-25-n-n-b/p/000000000000310900'),
    'B': ('Full-size RG2 linkage + latch tongue', 'Official articulated RG2 asset with custom terminal shoes; not scaled down.',
          'https://github.com/OnRobot/onrobot-isaacsim'),
    'C': ('Connector-specific compliant tool', 'Fixed datum jaw, rack-and-pinion closing jaw, passive wrist and separate tongue.',
          'https://doi.org/10.1007/s11633-021-1300-5'),
}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): digest.update(block)
    return digest.hexdigest()


def confined(root, value):
    path = (root/value).resolve()
    if not path.is_relative_to(root.resolve()): raise ValueError('Path escapes root: '+str(value))
    return path


def require_identity(row, digest, context):
    if row != digest: raise ValueError('Environment identity mismatch: '+context)


def verify_reports(project, pool, crowded):
    for snapshot in pool['source_snapshots']:
        campaign = confined(project, snapshot['campaign_directory'])
        for name, key in [('campaign_manifest.json','campaign_manifest_sha256'),
                          ('campaign_state.json','campaign_state_snapshot_sha256')]:
            if sha(campaign/name) != snapshot[key]: raise ValueError('Changed campaign evidence: '+name)
    for row in pool['trials']:
        if sha(confined(project,row['directory'])/'results.json') != row['results_sha256']:
            raise ValueError('Changed benchmark result')
    # Screen identity is resolved from its manifest digest, not from a guessed
    # newest directory. Refuse ambiguity rather than blending protocols.
    matches = [p.parent for p in (project/'rack_robotics/experiments').glob('occupied-screen*/manifest.json')
               if sha(p) == crowded['screen_manifest_sha256']]
    if len(matches) != 1: raise ValueError('Cannot identify unique occupied screen')
    screen = matches[0]
    if sha(screen/'state.json') != crowded['screen_state_sha256']: raise ValueError('Changed screen state')
    for row in crowded['cases']:
        if sha(confined(screen,row['result_relative_to_screen'])) != row['results_sha256']:
            raise ValueError('Changed neighbor result')


def verify_media(directory, project):
    report = json.loads((directory/'manifest.json').read_text())
    video = directory/'demo.mp4'
    digest = sha(video)
    if report.get('video_sha256') and report['video_sha256'] != digest:
        raise ValueError('Changed video: '+str(directory))
    for name, expected in report.get('source_sha256', {}).items():
        if sha(confined(directory.parent, name)) != expected:
            raise ValueError('Changed replay input: '+name)
    source = json.loads((directory.parent/'results.json').read_text())
    playback = directory/'mac_playback.json'
    mac = json.loads(playback.read_text()) if playback.exists() else {}
    if mac and mac.get('sha256') != digest: raise ValueError('Playback report has wrong video hash')
    return {'video_sha256': digest, 'source_task_passed': source['passed'],
            'source_attempt': str(directory.parent.relative_to(project)),
            'full_trajectory': report.get('full_trajectory', report.get('schema') == 'synchronized_physics_edit_v1'),
            'source_hashes_verified': bool(report.get('source_sha256')),
            'mac_playback_verified': mac.get('passed') is True}


def build(project, output, pool_path, crowded_path, audit_path, media_path):
    pool = json.loads(pool_path.read_text()); crowded = json.loads(crowded_path.read_text())
    audit = json.loads(audit_path.read_text()); selected_media = json.loads(media_path.read_text())
    if not crowded['complete']: raise ValueError('Crowded screen incomplete')
    if not all(r['complete'] for r in pool['designs'].values()): raise ValueError('Benchmark incomplete')
    verify_reports(project,pool,crowded)
    output.mkdir(parents=True, exist_ok=False)
    copied = {}

    def copy(source, destination):
        source = confined(project, source)
        target = confined(output, destination)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            if sha(target) != sha(source): raise ValueError('Destination collision')
        else: shutil.copy2(source, target)
        copied[str(target.relative_to(output))] = sha(target)
        return str(target.relative_to(output))

    sources = {name:copy(path, 'evidence/'+name+'.json') for name,path in
               [('benchmark',pool_path),('neighbors',crowded_path),('preservation',audit_path)]}
    versions = {key:[] for key in (a+b for a in 'ABC' for b in 'ABC')}
    for row in audit['environments']:
        environment = confined(project, row['environment'])
        require_identity(sha(environment/'manifest.json'), row['manifest_sha256'], row['environment'])
        manifest = json.loads((environment/'manifest.json').read_text())
        for name, digest in manifest['packaged_file_sha256'].items():
            if sha(confined(environment, name)) != digest: raise ValueError('Changed environment package')
        for evidence in row['evidence']:
            if sha(confined(project,evidence['report'])) != evidence['report_sha256']:
                raise ValueError('Changed reload report')
        config = json.loads((environment/'config.json').read_text())
        key = config['robot'][0]+config['gripper'][0]
        links = {n:copy(environment/(n+'.json'), 'environments/'+key+'/'+environment.name+'/'+n+'.json')
                 for n in ('manifest','config','results')}
        links['reload_reports'] = [copy(project/e['report'], 'evidence/reloads/'+str(i)+'-'+key+'-'+environment.name+'.json')
                                   for i,e in enumerate(row['evidence'])]
        versions[key].append({'version':environment.name,'path':row['environment'],
            'manifest_sha256':row['manifest_sha256'],'status':config['status'],
            'hardware_revision':config.get('hardware_revision'),
            'scene_load_verified':row['independent_scene_load_verified'],
            'declared_outcome_verified':row['declared_outcome_verified'], 'links':links,
            'run_command':'/isaac-sim/python.sh '+row['environment']+'/demo.py --output NEW_OUTPUT_DIRECTORY --allow-root'})
    cards=[]
    for key in sorted(versions):
        benchmark=pool['designs'].get(key); neighbors=crowded['designs'].get(key)
        if benchmark:
            path=benchmark['environment']['environment_relative_to_project']
            digest=benchmark['environment']['manifest_sha256']
            require_identity(sha(confined(project,path)/'manifest.json'),digest,key)
            require_identity(crowded['environment_manifest_sha256'][key],digest,key+' neighbors')
        mechanism=ARCHITECTURES[key[0]]; tool=TOOLS[key[1]]
        mechanical_path=project/'rack_robotics/experiments'/('mechanical-screen-'+key.lower()+'001.json')
        mechanical=json.loads(mechanical_path.read_text()) if mechanical_path.exists() else None
        if mechanical and benchmark:
            require_identity(mechanical['environment_manifest_sha256'],digest,key+' mechanical')
        mechanical_version = None
        if mechanical:
            matched = [v['version'] for v in versions[key] if v['manifest_sha256']==mechanical['environment_manifest_sha256']]
            if len(matched)!=1: raise ValueError('Mechanical screen lacks unique saved version')
            mechanical_version=matched[0]
        mechanical_link=copy(mechanical_path,'evidence/mechanical-'+key+'.json') if mechanical else None
        cards.append({'id':key, 'architecture':mechanism[0], 'architecture_description':mechanism[1],
            'architecture_reference':mechanism[2], 'tool':tool[0], 'tool_description':tool[1], 'tool_reference':tool[2],
            'versions':versions[key], 'benchmark':benchmark, 'neighbors':neighbors,
            'mechanical':mechanical, 'mechanical_version':mechanical_version,
            'mechanical_link':mechanical_link, 'media':[], 'image':None})
    lookup={c['id']:c for c in cards}
    for number, selected in enumerate(selected_media):
        directory=confined(project/'rack_robotics/experiments', selected['directory'])
        evidence=verify_media(directory,project)
        result=json.loads((directory.parent/'results.json').read_text())
        if result['robot'][0]+result['gripper'][0]!=selected['design']: raise ValueError('Wrong media design')
        prefix='media/'+selected['design']+'/'+str(number)
        row={**selected,**evidence,'url':copy(directory/'demo.mp4',prefix+'/demo.mp4'),
             'manifest':copy(directory/'manifest.json',prefix+'/manifest.json')}
        for name in ('mac_playback.json','visual_review.json'):
            if (directory/name).exists(): row[name]=copy(directory/name,prefix+'/'+name)
        lookup[selected['design']]['media'].append(row)
        frames=sorted((directory/'frames').glob('*.png'))
        if frames and lookup[selected['design']]['image'] is None:
            lookup[selected['design']]['image']=copy(frames[0],prefix+'/representative.png')
            lookup[selected['design']]['image_caption']=selected['label']+' · recorded render'
    for name in ('index.html','gallery.css','gallery.js'):
        copy(project/'rack_robotics/gallery'/name,name)
    data={'schema':'rack_gallery_snapshot_v1','generated_utc':datetime.now(timezone.utc).isoformat(),
          'designs':cards,'sources':sources,'preserved_versions':audit['versions'],
          'loaded_versions':audit['independent_scene_loads_verified'],
          'reproduced_outcomes':audit['declared_outcomes_verified'],
          'randomized_trials':sum(r['admissible_manipulation_trials'] for r in pool['designs'].values()),
          'scope':'Development comparison, not a final ranking or hardware safety certification'}
    (output/'data.json').write_text(json.dumps(data,indent=2)+'\n')
    copied['data.json']=sha(output/'data.json')
    manifest={'schema':'gallery_allowlisted_artifacts_v1','files':copied,'builder_sha256':sha(Path(__file__)),
              'input_media_sha256':sha(media_path),'scope':data['scope']}
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return data


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--pool',type=Path,default=ROOT/'rack_robotics/experiments/benchmark-pooled004.json')
    parser.add_argument('--neighbors',type=Path,default=ROOT/'rack_robotics/experiments/occupied-summary001.json')
    parser.add_argument('--audit',type=Path,default=ROOT/'rack_robotics/experiments/preservation-audit003.json')
    parser.add_argument('--media',type=Path,default=ROOT/'rack_robotics/gallery/media.json')
    args=parser.parse_args()
    data=build(ROOT,args.output.resolve(),args.pool.resolve(),args.neighbors.resolve(),args.audit.resolve(),args.media.resolve())
    print(json.dumps({'designs':len(data['designs']),'versions':data['preserved_versions'],'output':str(args.output)}))
