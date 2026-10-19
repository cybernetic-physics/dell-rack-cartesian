import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH=Path(__file__).resolve().parents[1]/'rack_robotics/scripts/build_gallery.py'
SPEC=importlib.util.spec_from_file_location('build_gallery',PATH)
gallery=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(gallery)


class GalleryTest(unittest.TestCase):
    def test_physical_campaign_retains_failed_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);campaign=root/'physical';campaign.mkdir()
            (campaign/'manifest.json').write_text(json.dumps({'environments':{'AA':{'manifest_sha256':'exact'}}}))
            report={'passed':False,'cases':{'AA/open_transport':{'diagnostic_passed':False,'task_passed':False}}}
            with patch('rack_robotics.scripts.screen_physical_controls.verify_campaign',return_value=report):
                actual=gallery.verified_physical_campaign(root,campaign,{'AA':'exact'})
                self.assertIs(actual,report);self.assertFalse(actual['passed'])
                with self.assertRaises(ValueError):gallery.verified_physical_campaign(root,campaign,{'AA':'different'})
                with self.assertRaises(ValueError):gallery.verified_physical_campaign(root,campaign,{'BA':'exact'})

    def test_physical_campaign_does_not_hide_failed_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);campaign=root/'physical';campaign.mkdir()
            with patch('rack_robotics.scripts.screen_physical_controls.verify_campaign',side_effect=ValueError('changed trace')):
                with self.assertRaisesRegex(ValueError,'changed trace'):
                    gallery.verified_physical_campaign(root,campaign,{'AA':'exact'})

    def presentation_fixture(self, root, diagnostic=False):
        def save(path, value):
            file=root/path; file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text(json.dumps(value)); return gallery.sha(file)
        source={'passed':not diagnostic,'error':'pickup failed' if diagnostic else None}
        source_sha=save('attempt/results.json',source)
        trajectory_sha=save('attempt/trajectory.jsonl',{'measured':'fixture'})
        manifest_sha=save('rack_robotics/experiments/media/manifest.json',{})
        sheet_sha=save('temporal/00-AA/sheet.png',{'image':'fixture'})
        sheets=[{'file':'sheet.png','sha256':sheet_sha,'frames':[0]}]
        provenance={'video_sha256':'video-digest','source_attempt':'attempt','source_task_passed':not diagnostic,
                    'source_hashes_verified':True,'full_trajectory':True}
        temporal={'selection':{'directory':'media','design':'AA'},'provenance':provenance,
                  'technical_decode_passed':True,'decoded_frames':1,'review_flags':[],
                  'manifest_sha256':manifest_sha,'trajectory_sha256':trajectory_sha,
                  'codec':{'codec_name':'h264','width':1920,'height':1080,'r_frame_rate':'30/1','nb_frames':'1'},
                  'inspection_sheets':sheets}
        temporal_sha=save('temporal/00-AA/report.json',temporal)
        review_product={'directory':'media','video_sha256':'video-digest','temporal_report':'temporal/00-AA/report.json',
                        'temporal_report_sha256':temporal_sha,'decoded_frames':1,'review_flags':[],
                        'visually_inspected_sheets':sheets,'systematic_sample_review_passed':True}
        review_sha=save('review.json',{'products':[review_product]})
        playback_sha=save('playback.json',{'passed':True,'sha256':'video-digest','playback':{'error':None},
                         'natural_full_playback':{'ended':True,'error':None,'dropped_video_frames':0}})
        playback={'path':'playback.json','sha256':playback_sha,'dropped_video_frames':0}
        temporal_manifest_sha=save('temporal/manifest.json',{})
        verification_product={'directory':'00-AA','design':'AA','video_sha256':'video-digest','frames':1,
                              'flags':[],'sheets':1,'inspection_sample_count':1}
        refs=[]
        for host in ('vm','mac'):
            row=dict(verification_product)
            if host=='vm':row['timestamps']={'frames':1,'fps':30}
            digest=save(host+'.json',{'passed':True,'review_manifest_sha256':temporal_manifest_sha,'products':[row]})
            refs.append({'path':host+'.json','sha256':digest})
        product={**review_product,'design':'AA','frames':1,'native_resolution':[1920,1080],
                 'visual_review':'review.json','visual_review_sha256':review_sha,
                 'inspected_sheets':1,'visually_inspected_sample_frames':1,
                 'natural_mac_playback':[playback],'presentation_accepted':True}
        if diagnostic:
            product.update(source_results='attempt/results.json',source_results_sha256=source_sha,
                           source_task_passed=False,source_error='pickup failed',
                           accepted_as_failure_diagnostic=True,accepted_as_working_cycle=False,
                           natural_mac_playback=playback)
        record={'schema':'failure_diagnostic_review_v1' if diagnostic else 'presentation_acceptance_v1',
                'scope':'fixture only','products':[product],'verification_reports':refs}
        record_sha=save('acceptance.json',record)
        selected={'design':'AA','directory':'media','presentation_record':'acceptance.json',
                  'presentation_record_sha256':record_sha}
        return selected,provenance,record

    def test_presentation_acceptance_and_failure_diagnostic_remain_distinct(self):
        for diagnostic,status in [(False,'accepted_working_presentation'),(True,'reviewed_failure_diagnostic')]:
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp); selected,provenance,_=self.presentation_fixture(root,diagnostic)
                result=gallery.verify_presentation(root,selected,provenance)
                self.assertEqual(result['status'],status)
                self.assertIn('temporal/00-AA/sheet.png',result['files'])
                self.assertEqual(result['sampled_frames'],1)
        self.assertEqual(gallery.verify_presentation(Path('.'),{}, {})['status'],'candidate')

    def test_presentation_rejects_changed_decision_sheet_and_playback(self):
        for file in ('acceptance.json','temporal/00-AA/sheet.png','playback.json'):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp); selected,provenance,_=self.presentation_fixture(root)
                (root/file).write_text('changed')
                with self.assertRaisesRegex(ValueError,'Changed presentation evidence'):
                    gallery.verify_presentation(root,selected,provenance)

    def test_presentation_rejects_wrong_video_and_source_outcome(self):
        for change in ({'video_sha256':'other'}, {'source_task_passed':False}, {'full_trajectory':False}):
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp); selected,provenance,_=self.presentation_fixture(root)
                with self.assertRaises(ValueError):gallery.verify_presentation(root,selected,{**provenance,**change})

    def test_presentation_rejects_false_acceptance_coverage_and_failure_promotion(self):
        for diagnostic,change in [(False,{'presentation_accepted':False}),
                                  (False,{'inspected_sheets':2}),
                                  (False,{'natural_mac_playback':[]}),
                                  (True,{'accepted_as_working_cycle':True})]:
            with tempfile.TemporaryDirectory() as temp:
                root=Path(temp); selected,provenance,record=self.presentation_fixture(root,diagnostic)
                record['products'][0].update(change)
                (root/'acceptance.json').write_text(json.dumps(record))
                selected['presentation_record_sha256']=gallery.sha(root/'acceptance.json')
                with self.assertRaises(ValueError):gallery.verify_presentation(root,selected,provenance)

    def test_presentation_requires_bound_timestamp_verification(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); selected,provenance,record=self.presentation_fixture(root)
            vm=json.loads((root/'vm.json').read_text());vm['products'][0].pop('timestamps')
            (root/'vm.json').write_text(json.dumps(vm))
            record['verification_reports'][0]['sha256']=gallery.sha(root/'vm.json')
            (root/'acceptance.json').write_text(json.dumps(record))
            selected['presentation_record_sha256']=gallery.sha(root/'acceptance.json')
            with self.assertRaisesRegex(ValueError,'timestamp verification'):
                gallery.verify_presentation(root,selected,provenance)

    def test_snapshot_equivalence_only_allows_finite_float_roundoff(self):
        original={'count':22,'passed':True,'sha':'unchanged','values':[26.839583333340432,.0857219772283161]}
        rounded=json.loads(json.dumps(original))
        rounded['values']=[math.nextafter(v,math.inf) for v in rounded['values']]
        self.assertTrue(gallery.equivalent_snapshot(original,rounded))
        for key,value in [('count',23),('count',22.),('passed',1),('sha','changed'),('values',[26.839584,.0857219772283161]),('values',[float('nan'),.0857219772283161])]:
            altered=dict(original);altered[key]=value
            self.assertFalse(gallery.equivalent_snapshot(original,altered))
        self.assertFalse(gallery.equivalent_snapshot(float('nan'),float('nan')))

    def test_comparison_recomputed_and_changed_input_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); directory=root/'comparison';directory.mkdir()
            (root/'input.json').write_text('original')
            for name, data in [('observations.json',[]),('plan.json',{}),('evidence.json',
                    {'input':{'namespace':'project','relative_path':'input.json','sha256':gallery.sha(root/'input.json')}})]:
                (directory/name).write_text(json.dumps(data))
            fresh={'schema':'test','designs':[]}
            report={**fresh,'analysis_source_sha256':{}}
            for name,key in [('observations.json','observations_sha256'),('plan.json','plan_sha256'),('evidence.json','evidence_sha256')]:
                report[key]=gallery.sha(directory/name)
            path=directory/'comparison.json';path.write_text(json.dumps(report))
            with patch('rack_robotics.comparison.compare',return_value=fresh):
                self.assertEqual(gallery.verified_assessments(root,path)[0],report)
                report['designs']=['changed'];path.write_text(json.dumps(report))
                with self.assertRaisesRegex(ValueError,'scores no longer reproduce'):gallery.verified_assessments(root,path)
                report['designs']=[];path.write_text(json.dumps(report));(root/'input.json').write_text('changed')
                with self.assertRaisesRegex(ValueError,'Changed comparison input'):gallery.verified_assessments(root,path)

    def test_force_summary_allows_only_bounded_platform_roundoff(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);path=root/'force.json'
            fresh={'designs':{'AA':{'peak':8.75,'verification':{'maximum_recomputation_error_n':1e-16}}}}
            stored=json.loads(json.dumps(fresh));stored['designs']['AA']['verification']['maximum_recomputation_error_n']=2e-16
            path.write_text(json.dumps(stored))
            def recompute(_):return json.loads(json.dumps(fresh))
            with patch('rack_robotics.scripts.summarize_cable_force.summarize',side_effect=recompute):
                self.assertEqual(gallery.verified_assessments(root,force_path=path)[1],stored)
                stored['designs']['AA']['peak']=9.;path.write_text(json.dumps(stored))
                with self.assertRaisesRegex(ValueError,'Changed nominal force'):gallery.verified_assessments(root,force_path=path)
                stored['designs']['AA']['verification']['maximum_recomputation_error_n']=float('nan')
                path.write_text(json.dumps(stored))
                with self.assertRaisesRegex(ValueError,'Unacceptable force'):gallery.verified_assessments(root,force_path=path)

    def test_tooling_failure_notes_preserved_but_never_verify_playback(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); media=root/'attempt/media'; media.mkdir(parents=True)
            (media.parent/'results.json').write_text(json.dumps({'passed':True}))
            (media/'demo.mp4').write_bytes(b'video')
            (media/'manifest.json').write_text('{}')
            failure=media/'mac_playback001_failure.json'
            failure.write_text(json.dumps({'passed':False,'stage':'browser.close'}))
            result=gallery.verify_media(media,root)
            self.assertFalse(result['mac_playback_verified'])
            self.assertEqual(result['preserved_playback_tooling_failures'],[failure.name])
            (media/'mac_playback002.json').write_text(json.dumps(
                {'passed':True,'sha256':gallery.sha(media/'demo.mp4')}))
            self.assertTrue(gallery.verify_media(media,root)['mac_playback_verified'])
            failure.write_text(json.dumps({'passed':False,'sha256':'wrong'}))
            with self.assertRaisesRegex(ValueError,'wrong video hash'):gallery.verify_media(media,root)
            failure.write_text(json.dumps({'passed':True}))
            with self.assertRaisesRegex(ValueError,'cannot claim'):gallery.verify_media(media,root)

    def test_synchronized_edit_requires_frozen_editor_and_four_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);media=root/'attempt/media';media.mkdir(parents=True)
            (media.parent/'results.json').write_text(json.dumps({'passed':True}))
            (media/'demo.mp4').write_bytes(b'test fixture')
            (media/'edit_source.py').write_text('frozen editor fixture')
            report={'schema':'synchronized_physics_edit_v1','temporal_validation_passed':True,
                    'edit_source_sha256':gallery.sha(media/'edit_source.py'),'inputs':{}}
            (media/'manifest.json').write_text(json.dumps(report))
            with self.assertRaisesRegex(ValueError,'four verified inputs'):gallery.verify_media(media,root)
            (media/'edit_source.py').write_text('changed editor')
            with self.assertRaisesRegex(ValueError,'changed synchronized editor'):gallery.verify_media(media,root)

    def test_confines_resolved_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)/'root'; root.mkdir()
            (root/'outside').symlink_to(Path(temp),target_is_directory=True)
            for value in ('../secret', '/etc/passwd', 'outside/secret'):
                with self.assertRaises(ValueError): gallery.confined(root,value)
            self.assertEqual(gallery.confined(root,'data.json'),(root/'data.json').resolve())

    def test_version_mismatch_rejected(self):
        gallery.require_identity('original','original','AA')
        with self.assertRaises(ValueError): gallery.require_identity('new-version','original','AA')

    def test_replay_hashes_and_playback_are_bound_to_actual_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); attempt=root/'attempt'; media=attempt/'media'; media.mkdir(parents=True)
            (attempt/'results.json').write_text(json.dumps({'passed':False}))
            (attempt/'trajectory.jsonl').write_text('recorded poses')
            (media/'demo.mp4').write_bytes(b'video')
            report={'video_sha256':gallery.sha(media/'demo.mp4'),
                    'source_sha256':{'trajectory.jsonl':gallery.sha(attempt/'trajectory.jsonl')}}
            (media/'manifest.json').write_text(json.dumps(report))
            valid=gallery.verify_media(media,root)
            self.assertFalse(valid['source_task_passed'])
            self.assertFalse(valid['mac_playback_verified'])
            self.assertTrue(valid['source_hashes_verified'])
            (media/'mac_playback.json').write_text(json.dumps({'passed':True,'sha256':'wrong'}))
            with self.assertRaises(ValueError): gallery.verify_media(media,root)
            (media/'mac_playback.json').unlink()
            (attempt/'trajectory.jsonl').write_text('changed poses')
            with self.assertRaises(ValueError): gallery.verify_media(media,root)

    def test_legacy_media_is_not_promoted_to_verified_provenance(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); media=root/'attempt/media'; media.mkdir(parents=True)
            (media.parent/'results.json').write_text(json.dumps({'passed':True}))
            (media/'manifest.json').write_text('{}'); (media/'demo.mp4').write_bytes(b'legacy')
            result=gallery.verify_media(media,root)
            self.assertFalse(result['source_hashes_verified'])
            self.assertFalse(result['full_trajectory'])

    def test_batch_media_resolves_remote_attempt_and_numbered_playback(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); attempt=root/'attempt'; attempt.mkdir()
            media=root/'batch/CA/side'; media.mkdir(parents=True)
            (attempt/'results.json').write_text(json.dumps({'passed':True}))
            (attempt/'trajectory.jsonl').write_text('measured motion')
            (media/'demo.mp4').write_bytes(b'video')
            (media/'render_source.py').write_text('render code')
            report={'source_attempt':'/workspace/attempt','full_trajectory':True,
                    'video_sha256':gallery.sha(media/'demo.mp4'),
                    'source_sha256':{'trajectory.jsonl':gallery.sha(attempt/'trajectory.jsonl')},
                    'render_sources_sha256':{'render_source.py':gallery.sha(media/'render_source.py')}}
            (media/'manifest.json').write_text(json.dumps(report))
            (media/'mac_playback001.json').write_text(json.dumps({'passed':True,'sha256':report['video_sha256']}))
            checked=gallery.verify_media(media,root)
            self.assertEqual(checked['source_attempt'],'attempt')
            self.assertTrue(checked['mac_playback_verified'])
            with self.assertRaises(ValueError): gallery.verify_media(media,root,root/'wrong-attempt')
            (media/'render_source.py').write_text('changed render')
            with self.assertRaises(ValueError): gallery.verify_media(media,root)

    def test_latest_feasibility_uses_numeric_version_not_old_benchmark(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'v010').mkdir()
            (root/'v010/results.json').write_text(json.dumps({'passed':False,'error':'pickup failed'}))
            versions=[{'version':v,'path':v,'manifest_sha256':'hash','scene_load_verified':True,
                       'declared_outcome_verified':True,'links':{'results':'evidence/'+v+'.json'}}
                      for v in ('v010','v002')]
            result=gallery.latest_feasibility(root,versions)
            self.assertFalse(result['passed'])
            self.assertEqual(result['version'],'v010')
            self.assertEqual(result['error'],'pickup failed')

    def test_explicit_representative_frame_rejects_missing_and_invalid(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); (root/'frames').mkdir()
            (root/'frames/00003.png').write_bytes(b'image')
            self.assertEqual(gallery.select_representative(root,{'representative_frame':3}),(root/'frames/00003.png').resolve())
            for value in (-1,True,'../secret',4):
                with self.assertRaises(ValueError): gallery.select_representative(root,{'representative_frame':value})

    def current_fixture(self, root):
        campaign=root/'campaign'; (campaign/'plan').mkdir(parents=True)
        (campaign/'plan/plan.json').write_text(json.dumps({'environments':{'AA':{'manifest_sha256':'exact-version'}}}))
        report={'campaign_directory':'/workspace/campaign','evidence_hashes_valid':True,
                'designs':{'AA':{'complete':True,'complete_cycles':22},'BA':{'complete':False}},
                'controls':{'AA':{'directory':'/workspace/campaign/AA/control','complete_cycle':True}}}
        path=root/'summary.json'; path.write_text(json.dumps(report))
        return path,report

    def test_current_cohort_recomputed_and_partial_design_omitted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); path,report=self.current_fixture(root)
            with patch.object(gallery,'summarize',return_value=report):
                result=gallery.verified_current_cohorts(root,[path])
            self.assertEqual(set(result),{'AA'})
            self.assertEqual(result['AA']['environment_manifest_sha256'],'exact-version')

    def test_current_cohort_tampered_control_and_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); path,report=self.current_fixture(root)
            with patch.object(gallery,'summarize',return_value=report):
                with self.assertRaises(ValueError): gallery.verified_current_cohorts(root,[path,path])
                changed=json.loads(path.read_text()); changed['controls']['AA']['complete_cycle']=False
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError): gallery.verified_current_cohorts(root,[path])


if __name__=='__main__': unittest.main()
