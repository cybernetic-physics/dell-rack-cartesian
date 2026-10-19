"""Build a self-contained, immutable, SSH-only comparison gallery snapshot.

Copies only explicitly selected artifacts, never exposes the project root or
follows external paths. Missing media stays visibly pending. No new server,
cloud resource, or public service is provisioned by this script.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from rack_robotics.scripts.summarize_benchmark import summarize
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


def equivalent_snapshot(left, right):
    """Exact structure/counts/hashes; at most eight finite-float ULPs.

    Python/CPU implementations can differ in final arithmetic bits when
    recomputing a Mac snapshot on the VM. This never relaxes source hashes,
    booleans, integer counts, field presence or meaningful numeric changes.
    """
    if type(left) is not type(right): return False
    if isinstance(left,dict):
        return left.keys()==right.keys() and all(equivalent_snapshot(left[k],right[k]) for k in left)
    if isinstance(left,list):
        return len(left)==len(right) and all(equivalent_snapshot(a,b) for a,b in zip(left,right))
    if isinstance(left,float):
        return (math.isfinite(left) and math.isfinite(right)
                and abs(left-right)<=8*max(math.ulp(left),math.ulp(right)))
    return left==right


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


def project_path(project, value):
    path = Path(value)
    if path.is_relative_to('/workspace'):
        path = project/path.relative_to('/workspace')
    return confined(project, path)


def latest_feasibility(project, versions):
    latest = max(versions, key=lambda row: int(row['version'][1:]))
    result = json.loads((confined(project, latest['path'])/'results.json').read_text())
    if type(result.get('passed')) is not bool:
        raise ValueError('Missing literal saved feasibility outcome')
    return {'version': latest['version'], 'environment': latest['path'],
            'manifest_sha256': latest['manifest_sha256'], 'passed': result['passed'],
            'cycle_time_s': result.get('cycle_time_s'), 'error': result.get('error'),
            'scene_load_verified': latest['scene_load_verified'],
            'declared_outcome_verified': latest['declared_outcome_verified'],
            'result_link': latest['links']['results'],
            'scope': 'Latest saved nominal feasibility only; historical reliability is not transferred'}


def verify_media(directory, project, attempt=None):
    project = project.resolve()
    report = json.loads((directory/'manifest.json').read_text())
    attempt = project_path(project, attempt or report.get('source_attempt', directory.parent))
    if report.get('source_attempt') and project_path(project, report['source_attempt']) != attempt:
        raise ValueError('Selected media attempt differs from recorded provenance')
    video = directory/'demo.mp4'
    digest = sha(video)
    if report.get('video_sha256') and report['video_sha256'] != digest:
        raise ValueError('Changed video: '+str(directory))
    for name, expected in report.get('source_sha256', {}).items():
        if sha(confined(attempt, name)) != expected:
            raise ValueError('Changed replay input: '+name)
    for name, expected in report.get('render_sources_sha256', {}).items():
        if sha(confined(directory, name)) != expected: raise ValueError('Changed renderer source: '+name)
    if report.get('schema') == 'synchronized_physics_edit_v1':
        if (report.get('temporal_validation_passed') is not True
                or sha(directory/'edit_source.py') != report.get('edit_source_sha256')):
            raise ValueError('Unverified or changed synchronized editor')
        if set(report.get('inputs',{})) != {'wide','rear','macro','side'}:
            raise ValueError('Synchronized edit lacks four verified inputs')
        if report.get('phase_cameras_input_sha256') is not None:
            if sha(directory/'phase_cameras_input.json') != report['phase_cameras_input_sha256']:
                raise ValueError('Changed phase-camera choices')
    for row in report.get('inputs', {}).values():
        source_dir = project_path(project, row['directory'])
        if sha(source_dir/'manifest.json') != row['manifest_sha256'] or sha(source_dir/'demo.mp4') != row['video_sha256']:
            raise ValueError('Changed multi-angle input')
        source_report=json.loads((source_dir/'manifest.json').read_text())
        if source_report['source_sha256'] != report['source_sha256']:
            raise ValueError('Multi-angle input belongs to a different trajectory')
        if any(source_report.get(k)!=report.get(k) for k in ('frames','fps','resolution')):
            raise ValueError('Multi-angle input has different timing or native dimensions')
    source = json.loads((attempt/'results.json').read_text())
    playback = sorted(directory.glob('mac_playback*.json'))
    mac_reports = []
    tooling_failures = []
    for path in playback:
        mac = json.loads(path.read_text())
        # Preserve failed checker attempts, but never use unbound tooling
        # notes as playback evidence. Any supplied hash must still match.
        if path.name.endswith('_failure.json'):
            if mac.get('passed') is not False:
                raise ValueError('Tooling failure note cannot claim playback success')
            if mac.get('sha256') is not None and mac['sha256'] != digest:
                raise ValueError('Playback report has wrong video hash')
            tooling_failures.append(path.name)
            continue
        if mac.get('sha256') != digest:
            raise ValueError('Playback report has wrong video hash')
        mac_reports.append(mac)
    return {'video_sha256': digest, 'source_task_passed': source['passed'],
            'source_attempt': str(attempt.relative_to(project)),
            'full_trajectory': report.get('full_trajectory', report.get('schema') == 'synchronized_physics_edit_v1'),
            'source_hashes_verified': bool(report.get('source_sha256')),
            'mac_playback_verified': any(mac.get('passed') is True for mac in mac_reports),
            'preserved_playback_tooling_failures': tooling_failures}


def verified_current_cohorts(project, paths):
    """Recompute selected snapshots; never promote a partial or old cohort."""
    project = project.resolve()
    completed = {}
    for path in paths:
        report = json.loads(path.read_text())
        campaign = project_path(project, report['campaign_directory'])
        fresh = summarize(campaign)
        def normalized(value):
            if isinstance(value, list): return [normalized(v) for v in value]
            if not isinstance(value, dict): return value
            return {k:str(project_path(project,v).relative_to(project))
                    if k in ('directory','campaign_directory') else normalized(v)
                    for k,v in value.items()}
        if not equivalent_snapshot(normalized(fresh),normalized(report)):
            raise ValueError('Changed current benchmark snapshot')
        if not fresh['evidence_hashes_valid']: raise ValueError('Invalid current benchmark hashes')
        plan = json.loads((campaign/'plan/plan.json').read_text())
        for design, row in fresh['designs'].items():
            if not row['complete']: continue
            if design in completed: raise ValueError('Ambiguous current cohort: '+design)
            completed[design] = {**row, 'environment_manifest_sha256':plan['environments'][design]['manifest_sha256'],
                                 'summary_source':path, 'campaign':str(campaign.relative_to(project))}
    return completed


def verify_presentation(project, selected, provenance):
    """Verify recorded human decisions; never infer visual quality from a hash.

    Old selections without a decision remain candidates. Accepted selections
    must bind the exact decision, source, sheets, technical checks and natural
    playback. This checks evidence integrity, not a new visual inspection.
    """
    if not selected.get('presentation_record'):
        return {'status': 'candidate', 'files': []}
    project = project.resolve()
    files = set()

    def checked(value, digest=None):
        path = confined(project, value)
        if digest is not None and sha(path) != digest:
            raise ValueError('Changed presentation evidence: '+str(value))
        files.add(str(path.relative_to(project)))
        return path

    def read(value, digest=None):
        return json.loads(checked(value, digest).read_text())

    digest = selected.get('presentation_record_sha256')
    if not digest: raise ValueError('Presentation decision must be hash-bound')
    record = read(selected['presentation_record'], digest)
    diagnostic = record['schema'] == 'failure_diagnostic_review_v1'
    if record['schema'] not in ('presentation_acceptance_v1', 'failure_diagnostic_review_v1'):
        raise ValueError('Unsupported presentation decision')
    matches = [p for p in record['products'] if p['directory'] == selected['directory']]
    if len(matches) != 1: raise ValueError('Missing or ambiguous presentation product')
    product = matches[0]
    if (product['design'] != selected['design'] or product['video_sha256'] != provenance['video_sha256']
            or provenance['source_hashes_verified'] is not True or provenance['full_trajectory'] is not True):
        raise ValueError('Presentation video/source identity mismatch')
    if diagnostic:
        if (product['accepted_as_failure_diagnostic'] is not True
                or product['accepted_as_working_cycle'] is not False
                or product['source_task_passed'] is not False or provenance['source_task_passed'] is not False):
            raise ValueError('Failure diagnostic cannot claim a working cycle')
        result = read(product['source_results'], product['source_results_sha256'])
        if (product['source_results'] != provenance['source_attempt']+'/results.json'
                or result['passed'] is not False or result.get('error') != product['source_error']):
            raise ValueError('Failure diagnostic source differs')
        reviewed = product
        frames = product['decoded_frames']
        playback_refs = [product['natural_mac_playback']]
    else:
        if product['presentation_accepted'] is not True or provenance['source_task_passed'] is not True:
            raise ValueError('Working presentation lacks accepted successful source')
        review = read(product['visual_review'], product['visual_review_sha256'])
        matches = [r for r in review['products'] if r['directory'] == selected['directory']]
        if len(matches) != 1: raise ValueError('Missing or ambiguous visual review')
        reviewed = matches[0]
        if reviewed['systematic_sample_review_passed'] is not True:
            raise ValueError('Visual review did not pass')
        frames = product['frames']
        playback_refs = product['natural_mac_playback']
    report_path = checked(product['temporal_report'], product['temporal_report_sha256'])
    report = json.loads(report_path.read_text())
    for field in ('temporal_report', 'temporal_report_sha256', 'video_sha256'):
        if reviewed[field] != product[field]: raise ValueError('Visual review identity differs')
    if (report['selection']['directory'] != selected['directory']
            or report['selection']['design'] != selected['design']
            or report['technical_decode_passed'] is not True
            or report['decoded_frames'] != frames or reviewed['decoded_frames'] != frames
            or report['review_flags'] != [] or reviewed['review_flags'] != []):
        raise ValueError('Presentation temporal coverage or unresolved flags')
    for field in ('video_sha256', 'source_attempt', 'source_task_passed', 'source_hashes_verified', 'full_trajectory'):
        if report['provenance'][field] != provenance[field]: raise ValueError('Temporal source differs')
    directory = confined(project/'rack_robotics/experiments', selected['directory'])
    manifest = read(directory/'manifest.json', report['manifest_sha256'])
    checked(confined(project, provenance['source_attempt'])/manifest.get('trajectory_file', 'trajectory.jsonl'),
            report['trajectory_sha256'])
    codec = report['codec']
    if (codec['codec_name'] != 'h264' or codec['r_frame_rate'] != '30/1'
            or int(codec['nb_frames']) != frames or codec['width'] < 1920 or codec['height'] < 1080):
        raise ValueError('Presentation format below required native delivery')
    sheets = report['inspection_sheets']
    count = sum(len(s['frames']) for s in sheets)
    if not sheets or reviewed['visually_inspected_sheets'] != sheets:
        raise ValueError('Incomplete visual sheet coverage')
    if not diagnostic and (product['native_resolution'] != [codec['width'], codec['height']]
            or product['inspected_sheets'] != len(sheets) or product['visually_inspected_sample_frames'] != count):
        raise ValueError('Accepted coverage differs from temporal report')
    for sheet in sheets: checked(report_path.parent/sheet['file'], sheet['sha256'])
    for frame in reviewed.get('original_frames_inspected', []):
        if isinstance(frame, dict): checked(frame['file'], frame['sha256'])
        else:
            # Earlier reviews record frame indices, not original PNG hashes.
            # Check availability, but do not retrospectively claim a hash bind.
            if not checked(directory/'frames'/f'{frame:05d}.png').is_file():
                raise ValueError('Missing indexed native inspection frame')
    if not playback_refs: raise ValueError('Missing natural Mac playback')
    for ref in playback_refs:
        playback = read(ref['path'], ref['sha256'])
        full = playback.get('natural_full_playback', {})
        if (playback['passed'] is not True or playback['sha256'] != product['video_sha256']
                or full.get('ended') is not True or full.get('error') is not None
                or playback.get('browser_errors') or playback['playback'].get('error') is not None):
            raise ValueError('Natural Mac playback not verified')
        if 'dropped_video_frames' in ref and ref['dropped_video_frames'] != full['dropped_video_frames']:
            raise ValueError('Playback drop count differs')
    refs = record.get('verification_reports')
    if refs is None:
        refs = [{'path':'artifacts/temporal-review001/verification_'+host+'001.json',
                 'sha256':record[host+'_verification_sha256']} for host in ('vm', 'mac')]
    bound = []
    for ref in refs:
        verification = read(ref['path'], ref['sha256'])
        if verification['passed'] is not True: raise ValueError('Failed temporal verification')
        matches = [p for p in verification['products'] if p['video_sha256'] == product['video_sha256']]
        if not matches: continue  # Acceptance002 spans two temporal campaigns.
        checked(report_path.parent.parent/'manifest.json', verification['review_manifest_sha256'])
        if len(matches) != 1: raise ValueError('Ambiguous temporal verification')
        row = matches[0]
        if (row['design'] != selected['design'] or row['directory'] != report_path.parent.name
                or row['frames'] != frames or row['flags'] != [] or row['sheets'] != len(sheets)
                or row['inspection_sample_count'] != count):
            raise ValueError('Temporal verification coverage differs')
        bound.append(row)
    if len(bound) < 2 or not any(r.get('timestamps', {}).get('frames') == frames
                               and r['timestamps'].get('fps') == 30 for r in bound):
        raise ValueError('Missing bound temporal/timestamp verification')
    return {'status': 'reviewed_failure_diagnostic' if diagnostic else 'accepted_working_presentation',
            'record': selected['presentation_record'], 'record_sha256': digest,
            'visual_review': product.get('visual_review', selected['presentation_record']),
            'temporal_report': product['temporal_report'], 'frames': frames,
            'inspected_sheets': len(sheets), 'sampled_frames': count,
            'scope': record['scope'], 'files': sorted(files)}


def select_representative(directory, selected):
    directory = directory.resolve()
    frames = sorted((directory/'frames').glob('*.png'))
    if selected.get('representative_frame') is None: return frames[0] if frames else None
    index = selected['representative_frame']
    if type(index) is not int or index < 0: raise ValueError('Invalid representative frame')
    path = confined(directory, 'frames/'+f'{index:05d}.png')
    if not path.is_file(): raise ValueError('Missing selected representative frame')
    return path


def verified_assessments(project, comparison_path=None, force_path=None):
    """Bind optional current recommendations to recomputed, exact-version data."""
    comparison = None
    forces = None
    if comparison_path:
        from rack_robotics.comparison import compare
        directory = comparison_path.parent
        comparison = json.loads(comparison_path.read_text())
        for name, key in [('observations.json', 'observations_sha256'), ('evidence.json', 'evidence_sha256'),
                          ('plan.json', 'plan_sha256')]:
            if sha(directory/name) != comparison[key]: raise ValueError('Changed comparison '+name)
        for name, digest in comparison['analysis_source_sha256'].items():
            if sha(confined(directory, name)) != digest: raise ValueError('Changed comparison analysis source')
        evidence = json.loads((directory/'evidence.json').read_text())
        for row in evidence.values():
            if row['namespace'] != 'project' or sha(confined(project,row['relative_path'])) != row['sha256']:
                raise ValueError('Changed comparison input')
        fresh = compare(json.loads((directory/'observations.json').read_text()))
        if any(not equivalent_snapshot(comparison.get(k),v) for k,v in fresh.items()):
            raise ValueError('Comparison scores no longer reproduce')
    if force_path:
        from rack_robotics.scripts.summarize_cable_force import summarize as force_summary
        forces = json.loads(force_path.read_text())
        fresh = force_summary(project/'rack_robotics/experiments')
        # Different CPU arithmetic may change the verifier's tiny roundoff only.
        # All force values, durations, trajectories and input hashes must match.
        clean = json.loads(json.dumps(forces))
        for report in (clean, fresh):
            for row in report['designs'].values():
                error = row['verification'].pop('maximum_recomputation_error_n')
                if not 0 <= error <= 1e-9: raise ValueError('Unacceptable force recomputation error')
        if clean != fresh: raise ValueError('Changed nominal force summary')
    return comparison, forces


def verified_physical_campaign(project, directory, current_digests):
    """A verified failed diagnostic remains failed; completion is not success."""
    from rack_robotics.scripts.screen_physical_controls import verify_campaign
    directory = confined(project, directory)
    report = verify_campaign(directory, project/'rack_robotics/experiments')
    manifest = json.loads((directory/'manifest.json').read_text())
    for design, row in manifest['environments'].items():
        if design not in current_digests:
            raise ValueError('Physical campaign contains unknown current design')
        require_identity(row['manifest_sha256'], current_digests[design], 'physical '+design)
    return report


def build(project, output, pool_path, crowded_path, audit_path, media_path, current_paths=(),
          comparison_path=None, force_path=None, physical_paths=()):
    pool = json.loads(pool_path.read_text()); crowded = json.loads(crowded_path.read_text())
    audit = json.loads(audit_path.read_text()); selected_media = json.loads(media_path.read_text())
    if not crowded['complete']: raise ValueError('Crowded screen incomplete')
    if not all(r['complete'] for r in pool['designs'].values()): raise ValueError('Benchmark incomplete')
    verify_reports(project,pool,crowded)
    current_cohorts = verified_current_cohorts(project, current_paths)
    comparison, forces = verified_assessments(project, comparison_path, force_path)
    if any(s.get('presentation_record') for s in selected_media):
        if not (project/'rack_robotics/research/sources_and_licenses.md').is_file():
            raise ValueError('Accepted-media gallery requires sources and licenses')
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
    sources['gallery-builder']=copy(Path(__file__),'build_source.py')
    sources['media-selection']=copy(media_path,'media_selection.json')
    for index, path in enumerate(current_paths):
        sources['current-benchmark-'+str(index)] = copy(path, 'evidence/current-benchmark-'+str(index)+'.json')
    for name in ('buildability_and_bom.md', 'scoring_method.md', 'supplier_costs001.json',
                 'cable_motion_and_loads.md', 'continuous_cycles.md', 'current_design_comparison.md',
                 'current_candidate_matrix001.csv', 'cartesian_robots.md', 'grippers.md',
                 'rj45_mechanisms.md', 'sources_and_licenses.md', 'cable_momentum_measurement.md',
                 'cable_constraint_load.md', 'cable_load_screen001.csv', 'cable_force_comparison001.json',
                 'actuator_interlocks.md', 'source_review001.md',
                 'physical_challenge_results001.md', 'physical_challenge_protocol001.md',
                 'matched_release_results001.md', 'matched_release_protocol001.md',
                 'presentation/inspection_review001.json', 'presentation/inspection_review002.json',
                 'presentation/inspection_review003.json'):
        path = project/'rack_robotics/research'/name
        if path.exists(): sources[name] = copy(path, 'research/'+name)
    sources['reproduction-guide']=copy(project/'rack_robotics/REPRODUCE.md','REPRODUCE.md')
    sources['delivery-audit']=copy(project/'rack_robotics/DELIVERY_AUDIT.md','DELIVERY_AUDIT.md')
    if comparison_path: sources['current-comparison']=copy(comparison_path,'evidence/current-comparison.json')
    if force_path: sources['nominal-cable-forces']=copy(force_path,'evidence/nominal-cable-forces.json')
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
        current = latest_feasibility(project, versions[key])
        current_benchmark = current_cohorts.get(key)
        if current_benchmark:
            require_identity(current_benchmark['environment_manifest_sha256'], current['manifest_sha256'], key+' current cohort')
            current_benchmark = {**current_benchmark, 'summary_source':copy(current_benchmark['summary_source'], 'evidence/current-'+key+'.json')}
        cards.append({'id':key, 'architecture':mechanism[0], 'architecture_description':mechanism[1],
            'architecture_reference':mechanism[2], 'tool':tool[0], 'tool_description':tool[1], 'tool_reference':tool[2],
            'versions':versions[key], 'current':current, 'current_benchmark':current_benchmark,
            'benchmark':benchmark, 'neighbors':neighbors,
            'mechanical':mechanical, 'mechanical_version':mechanical_version,
            'mechanical_link':mechanical_link, 'media':[], 'image':None})
    lookup={c['id']:c for c in cards}
    physical = {}
    for path in physical_paths:
        if path.name in physical: raise ValueError('Duplicate physical campaign name')
        report = verified_physical_campaign(project,path,
            {key:row['current']['manifest_sha256'] for key,row in lookup.items() if row['current']})
        physical[path.name] = report
        relative = 'evidence/'+path.name+'-verification.json'
        (output/relative).write_text(json.dumps(report,indent=2)+'\n')
        copied[relative] = sha(output/relative)
        sources[path.name+'-verification'] = relative
        for name in ('manifest.json','protocol.md','state.json'):
            sources[path.name+'-'+name] = copy(path/name,'evidence/'+path.name+'/'+name)
    if physical:
        sources['physical-verifier-source'] = copy(project/'rack_robotics/scripts/screen_physical_controls.py','evidence/physical-verifier-source.py')
    if comparison:
        for row in comparison['designs']:
            current = lookup[row['design']]['current']
            require_identity(row['environment_manifest_sha256'],current['manifest_sha256'],'ranked '+row['design'])
            lookup[row['design']]['comparison'] = row
    if forces:
        for label,row in forces['designs'].items():
            result = json.loads((confined(project/'rack_robotics/experiments',row['directory'])/'results.json').read_text())
            require_identity(result['environment_manifest_sha256'],lookup[label]['current']['manifest_sha256'],'force '+label)
            lookup[label]['nominal_cable_force'] = row
    for number, selected in enumerate(selected_media):
        directory=confined(project/'rack_robotics/experiments', selected['directory'])
        attempt=project/'rack_robotics/experiments'/selected['attempt'] if selected.get('attempt') else None
        evidence=verify_media(directory,project,attempt)
        result=json.loads((project/evidence['source_attempt']/'results.json').read_text())
        if result['robot'][0]+result['gripper'][0]!=selected['design']: raise ValueError('Wrong media design')
        prefix='media/'+selected['design']+'/'+str(number)
        row={**selected,**evidence,
             'manifest':copy(directory/'manifest.json',prefix+'/manifest.json')}
        presentation = verify_presentation(project, selected, evidence)
        # Keep original evidence bytes and their project-relative hierarchy.
        # The link map makes root-relative paths in the records resolvable.
        presentation['links'] = {path:copy(project/path, 'presentation/'+path)
                                 for path in presentation.pop('files')}
        row['presentation'] = presentation
        if not selected.get('image_only'):
            row['url']=copy(directory/'demo.mp4',prefix+'/demo.mp4')
        for report in sorted({*directory.glob('mac_playback*.json'), *directory.glob('visual_review*.json')}):
            row[report.name]=copy(report,prefix+'/'+report.name)
        if not selected.get('image_only'): lookup[selected['design']]['media'].append(row)
        frame=select_representative(directory,selected)
        if frame and lookup[selected['design']]['image'] is None:
            lookup[selected['design']]['image']=copy(frame,prefix+'/representative.png')
            lookup[selected['design']]['image_caption']=selected['label']+' · recorded render'
            lookup[selected['design']]['image_evidence']=row
        if selected.get('image_only') and frame is None: raise ValueError('Image-only entry has no frame')
    for name in ('index.html','gallery.css','gallery.js'):
        copy(project/'rack_robotics/gallery'/name,name)
    data={'schema':'rack_gallery_snapshot_v2','generated_utc':datetime.now(timezone.utc).isoformat(),
          'designs':cards,'sources':sources,'preserved_versions':audit['versions'],
          'loaded_versions':audit['independent_scene_loads_verified'],
          'reproduced_outcomes':audit['declared_outcomes_verified'],
          'randomized_trials':sum(r['admissible_manipulation_trials'] for r in pool['designs'].values()),
          'comparison':comparison, 'nominal_cable_forces':forces, 'physical_challenges':physical,
          'scope':'Version-specific simulation comparison; scores and accepted media do not certify hardware safety'}
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
    parser.add_argument('--current-benchmark',type=Path,action='append',default=[])
    parser.add_argument('--comparison',type=Path)
    parser.add_argument('--cable-forces',type=Path)
    parser.add_argument('--physical-campaign',type=Path,action='append',default=[])
    args=parser.parse_args()
    data=build(ROOT,args.output.resolve(),args.pool.resolve(),args.neighbors.resolve(),args.audit.resolve(),args.media.resolve(),
               [path.resolve() for path in args.current_benchmark],
               args.comparison.resolve() if args.comparison else None,
               args.cable_forces.resolve() if args.cable_forces else None,
               [path.resolve() for path in args.physical_campaign])
    print(json.dumps({'designs':len(data['designs']),'versions':data['preserved_versions'],'output':str(args.output)}))
