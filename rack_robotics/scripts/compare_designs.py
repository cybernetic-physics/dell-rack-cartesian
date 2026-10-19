"""Read-only exact-version comparison. Pending evidence withholds final ranking."""
import argparse
import json
import math
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rack_robotics.comparison import compare, BUILD_ITEMS, PHYSICS_ITEMS
from rack_robotics.dependency_inventory import Files, confined, digest
from rack_robotics.mechanical_evidence import verify_identity
from rack_robotics.mechanical_screen import screen as mechanical_screen
from summarize_benchmark import summarize as benchmark_summary
from summarize_occupied_screen import summarize as occupied_summary


def identity(report, expected):
    if report.get('environment_manifest_sha256') != expected:
        raise ValueError('Report belongs to a different saved environment')


def workspace_verdict(result):
    required={'samples_present','finite_state','sampled_anchor_gap_below_1p5mm',
        'sampled_hinge_limits_within_one_degree','startup_samples_present','startup_finite_state',
        'startup_sampled_anchor_gap_below_1p5mm','startup_sampled_hinge_limits_within_one_degree',
        'all_waypoints_reached','no_runtime_error','no_robot_contact_violations'}
    checks=result['checks']
    if not required <= checks.keys() or any(type(v) is not bool for v in checks.values()):
        raise ValueError('Incomplete workspace gates')
    verdict=all(checks.values())
    if result['passed'] != verdict: raise ValueError('Workspace verdict disagrees with checks')
    if verdict and (result['error'] or result['contact_violations'] or
                    len(result['waypoints_reached']) != result['planned_waypoint_count']):
        raise ValueError('Workspace lacks complete declared path')
    return verdict


def replay_verdict(manifest):
    if (manifest.get('source_passed') is not True or manifest.get('full_trajectory') is not True
            or manifest.get('physics_running') is not False):
        raise ValueError('Visual evidence is not a complete successful measured replay')
    frames=manifest['frames'];recording=manifest['recording_validation']
    poses=manifest['pose_replay_validation'];camera=manifest['capture_camera_validation']
    if (type(frames) is not int or frames<2 or recording['samples']!=frames or
            poses['body_sample_checks']!=frames*recording['body_count'] or camera['checked']!=frames):
        raise ValueError('Incomplete replay pose/camera checks')
    for value,limit in ((poses['maximum_translation_error_m'],1e-6),
                        (poses['maximum_rotation_error_rad'],1e-5),
                        (camera['maximum_view_matrix_element_error'],1e-6)):
        if not math.isfinite(value) or not 0<=value<=limit:raise ValueError('Replay error exceeds declared tolerance')


class Evidence:
    def __init__(self, root):
        self.root=root.resolve(); self.files=Files(self.root,Path('/isaac-sim'))
    def path(self, value): return confined(self.root,value)
    def add(self, value, expected=None):
        return self.files.add(self.path(value),'comparison_input',expected)
    def read(self, value, expected=None):
        self.add(value,expected);return json.loads(self.path(value).read_text())
    def sources(self, directory):
        directory=self.path(directory)
        for name,h in self.read(directory/'source_manifest.json').items():
            self.add(confined(directory/'source',name),h)


def prepare(root, plan, evidence, cache):
    rows=[]; occupied_cache={}; benchmarks={}
    for design,entry in plan['designs'].items():
        env=evidence.path(entry['environment']);manifest=evidence.read(env/'manifest.json')
        env_hash=digest(env/'manifest.json')
        for name,h in manifest['packaged_file_sha256'].items():evidence.add(confined(env,name),h)
        result=evidence.read(env/'results.json'); config=evidence.read(env/'config.json')
        row={'design':design,'environment':entry['environment'],'environment_manifest_sha256':env_hash,
             'nominal_passed':result['passed'],'failure_reason':result.get('error'),
             'leading_candidate':entry.get('leading_candidate',False),'pending':[]}
        rows.append(row)
        if not result['passed']:continue
        if not evidence.read(env/'physics_integrity.json').get('passed'):
            raise ValueError('Functional design lacks physical-integrity pass')
        campaign=entry['campaign'];directory=evidence.path(campaign)
        if campaign not in benchmarks:
            summary=benchmark_summary(directory)
            if not summary['evidence_hashes_valid']:raise ValueError(summary['errors'])
            benchmarks[campaign]=summary
            # Keep the complete regenerated summary, not just selected rates.
            target=cache/(directory.name+'.json');target.write_text(json.dumps(summary,indent=2)+'\n')
            m=evidence.read(directory/'campaign_manifest.json');evidence.read(directory/'campaign_state.json')
            p=evidence.read(directory/'plan/plan.json',m['plan_sha256'])
            for name,h in m['harness_sha256'].items():evidence.add(confined(directory,name),h)
            for name,h in p['condition_sha256'].items():evidence.add(confined(directory/'plan',name),h)
            for trial in [*summary['trials'],*summary['controls'].values()]:
                if not trial.get('directory'):continue
                trial_dir=evidence.path(trial['directory'])
                evidence.add(trial_dir/'results.json',trial['results_sha256'])
                # These hashes bind additional metrics that are not package files.
                for name in ('contacts.json','trajectory.jsonl','source_manifest.json'):
                    if (trial_dir/name).exists():evidence.add(trial_dir/name)
        summary=benchmarks[campaign];b=summary['designs'][design]
        p=evidence.read(directory/'plan/plan.json')
        declared=p['environments'][design]
        if declared['manifest_sha256']!=env_hash or evidence.path(declared['environment_relative_to_project'])!=env:
            raise ValueError('Benchmark cohort does not match exact selected version')
        row['benchmark']={'complete':b['complete'],'control_passed':summary['controls'][design].get('complete_cycle',False),
            'planned':b['planned'],'finished':b['finished'],'admissible':b['admissible_manipulation_trials'],
            'complete_cycles':b['complete_cycles'],'fixture_failures':b['fixture_failures']}
        row['protocol']={'campaign':campaign,'harness_sha256':evidence.read(directory/'campaign_manifest.json')['harness_sha256']}
        row['context_metrics']=b
        row['trial_metrics']=[t for t in summary['trials'] if t['design']==design]
        if not b['complete']:row['pending'].append('Randomized cohort incomplete')
        # Recompute the occupied screen with its original frozen source/conditions/results.
        occupied=entry['occupied_screen'];occ_dir=evidence.path(occupied)
        if occupied not in occupied_cache:
            occupied_cache[occupied]=occupied_summary(occ_dir)
            (cache/(occ_dir.name+'.json')).write_text(json.dumps(occupied_cache[occupied],indent=2)+'\n')
            for name in ('manifest.json','state.json','plan/plan.json'):evidence.add(occ_dir/name)
            for case in occupied_cache[occupied]['cases']:
                evidence.add(occ_dir/case['result_relative_to_screen'],case['results_sha256'])
                if case.get('contacts_sha256'):evidence.add((occ_dir/case['result_relative_to_screen']).with_name('contacts.json'),case['contacts_sha256'])
        occ=occupied_cache[occupied]
        if occ['environment_manifest_sha256'][design]!=env_hash:raise ValueError('Wrong occupied version')
        row['occupied']={'starts':occ['designs'][design]['cases'],'clearance_passes':occ['designs'][design]['clearance_passes']}
        # Exact-package mechanical screen, recomputed from frozen trajectory/property data.
        props_path=evidence.path(entry['properties']);props=evidence.read(props_path)
        verify_identity(props,env,env);evidence.add(props_path.parent/'extract_source.py',props['source_sha256'])
        mechanics=evidence.read(entry['mechanical_screen']);identity(mechanics,env_hash)
        for key,path in [('properties',props_path),('trajectory',env/'trajectory.jsonl'),('results',env/'results.json')]:
            evidence.add(path,mechanics['evidence_sha256'][key])
        evidence.add(root/'rack_robotics/mechanical_screen.py',mechanics['analysis_sha256'])
        with (env/'trajectory.jsonl').open() as stream:
            header=json.loads(next(stream));samples=[json.loads(line) for line in stream]
        recomputed=mechanical_screen(props,header,samples)
        if any(mechanics[k]!=v for k,v in recomputed.items()):raise ValueError('Mechanical screen no longer reproduces')
        row['overhang_m']=mechanics['maximum_sampled_overhang']
        row['mechanical_context']={k:mechanics[k] for k in ('total_modeled_mass_kg','moving_mass_kg',
            'largest_sampled_gravity_mount_moment','telescoping_joint_gravity_loads','rigid_geometry_swept_bounds')}
        # Workspace gates are a finite unloaded raster, not all-pose clearance.
        work=evidence.path(entry['workspace']);identity(evidence.read(work/'manifest.json'),env_hash)
        evidence.sources(work);row['workspace_passed']=workspace_verdict(evidence.read(work/'results.json'))
        box=evidence.read(env/'robot_box_sweep001.json')
        if not box.get('all_robot_box_pairs') or box.get('errors'):raise ValueError('Unsupported/incomplete box audit')
        if box['passed'] != (not box['possible_overlaps']):raise ValueError('Box verdict mismatch')
        row['supported_box_passed']=box['passed']
        # Human judgments remain explicit, attributable, and separately inspectable.
        row['buildability']=json.loads(json.dumps(plan['buildability']))
        row['physics']=json.loads(json.dumps(plan['physics']))
        row['visual']=json.loads(json.dumps(plan['visual']))
        brake=evidence.path(entry['brake'])
        if not (brake/'results.json').exists():
            row['pending'].append('Exact-version power-loss probe pending')
        else:
            identity(evidence.read(brake/'manifest.json'),env_hash);evidence.sources(brake)
            r=evidence.read(brake/'results.json')
            if type(r['passed']) is not bool or r['passed'] != all(r['checks'].values()):
                raise ValueError('Brake verdict differs from declared checks')
            row['buildability']['power_loss_loads']={'score':2.5 if r['passed'] else 0,
                'rationale':'Exact-version model fault test '+('passes; hardware parameters remain uncalibrated' if r['passed'] else 'fails declared gates; nominal powered success does not qualify power loss'),
                'evidence':[str((brake/'results.json').relative_to(root)),str((brake/'manifest.json').relative_to(root))]}
        # At least one completed actual-trajectory clip supports the partial-media score.
        media=evidence.path(entry['media'])
        if not (media/'manifest.json').exists():row['pending'].append('Current recorded-motion clip pending')
        else:
            m=evidence.read(media/'manifest.json')
            replay_verdict(m)
            source=Path(m['source_attempt'])
            if source.is_absolute() and source.is_relative_to('/workspace'):
                source=root/source.relative_to('/workspace')
            source=evidence.path(source)
            for name,h in m['source_sha256'].items():
                evidence.add(confined(source,name),h)
                if name in ('trajectory.jsonl','results.json'):evidence.add(env/name,h)
            for name,h in m['render_sources_sha256'].items():evidence.add(confined(media,name),h)
            evidence.add(media/'demo.mp4',m['video_sha256'])
            row['visual']['evidence'].append(str((media/'manifest.json').relative_to(root)))
        for group in (row['buildability'],row['physics'],{'visual':row['visual']}):
            for judgment in group.values():
                for name in judgment['evidence']:evidence.add(name)
        print('COMPARISON_INPUT',design,'pending='+str(row['pending']),flush=True)
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();args.output.mkdir(parents=True,exist_ok=False)
    evidence=Evidence(ROOT);plan=evidence.read(args.plan)
    evidence.add(plan['method'])
    sources=(Path(__file__),ROOT/'rack_robotics/comparison.py',
        ROOT/'rack_robotics/dependency_inventory.py',ROOT/'rack_robotics/mechanical_evidence.py',
        ROOT/'rack_robotics/mechanical_screen.py',ROOT/'rack_robotics/benchmarking/metrics.py',
        *[Path(__file__).with_name(n) for n in ('summarize_benchmark.py','summarize_occupied_screen.py',
                                               'evaluate_all.py','screen_occupied_ports.py')])
    source_hashes={}
    for source in sources:
        shutil.copy2(source,args.output/source.name);evidence.add(source)
        source_hashes[source.name]=digest(args.output/source.name)
    shutil.copy2(args.plan,args.output/'plan.json')
    cache=args.output/'regenerated';cache.mkdir()
    try:
        rows=prepare(ROOT,plan,evidence,cache);report=compare(rows)
        report['analysis_source_sha256']=source_hashes
        report['method_sha256']=digest(evidence.path(plan['method']))
        report['plan_sha256']=digest(args.output/'plan.json')
        files=evidence.files.finish()
        (args.output/'observations.json').write_text(json.dumps(rows,indent=2)+'\n')
        (args.output/'evidence.json').write_text(json.dumps(files,indent=2)+'\n')
        report['observations_sha256']=digest(args.output/'observations.json')
        report['evidence_sha256']=digest(args.output/'evidence.json')
        (args.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'complete_evidence':report['complete_evidence'],'pending':report['pending_designs'],
                          'ranking':report['rankings_by_reliability_weight']},indent=2))
    except Exception as error:
        (args.output/'failure.json').write_text(json.dumps({'error':str(error)},indent=2)+'\n');raise


if __name__=='__main__':main()
