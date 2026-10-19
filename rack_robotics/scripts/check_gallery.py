"""Read-only Mac browser QA of the gallery through its actual SSH tunnel."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.parse
import urllib.request
from playwright.sync_api import sync_playwright


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(); args.output.mkdir(parents=True,exist_ok=False)
    base=args.url.rstrip('/')+'/'
    def get(name):
        url=urllib.parse.urljoin(base,name)
        if not url.startswith(base): raise ValueError('Artifact escapes gallery URL')
        with urllib.request.urlopen(url,timeout=30) as response: return response.read()
    manifest=json.loads(get('manifest.json')); data=json.loads(get('data.json'))
    # Exercise every published file URL, including downloads, and verify bytes.
    checked=[]
    for name,digest in manifest['files'].items():
        if hashlib.sha256(get(name)).hexdigest()!=digest: raise ValueError('Wrong served artifact: '+name)
        checked.append(name)
    errors=[]; playback=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1100})
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(base); page.wait_for_selector('.card')
        assert page.locator('.card').count()==9
        assert page.locator('#comparison tr').count()==9
        if data.get('physical_challenges'):
            section=page.locator('#physical-challenges')
            assert section.is_visible()
            text=section.inner_text()
            assert 'none of these cases adds to randomized reliability' in text
            for name,report in data['physical_challenges'].items():
                passed=sum(c['diagnostic_passed'] for c in report['cases'].values())
                verdict='PASS' if report['passed'] else 'FAIL — counterevidence preserved'
                assert f'{name}: {passed}/{len(report["cases"])} diagnostic cases passed. Overall diagnostic {verdict}.' in text
                target=data['sources'][name+'-verification']
                assert section.locator('a[href="'+urllib.parse.urljoin(base,target)+'"]').count()==1
        if data.get('comparison') and data.get('nominal_cable_forces'):
            assert page.locator('#recommendation').is_visible()
            ranks=data['comparison']['rankings_by_reliability_weight']['45']
            assert page.locator('#recommendation-comparison tr').count()==len(ranks)
            for rank in ranks:
                force=data['nominal_cable_forces']['designs'][rank['design']]
                cells=page.locator('#recommendation-comparison tr[data-design="'+rank['design']+'"] td').all_text_contents()
                assert cells==[rank['design'],f"{rank['total']:.2f}",f"{force['peak_tension']['force_n']:.2f} N",
                               f"{force['plug_joint_peak_tension_n']:.2f} N",
                               f"{1000*force['exposure_above_n']['5.0']['total_duration_s']:.2f} ms"]
        if page.locator('#current-comparison').count():
            assert page.locator('#current-comparison tr').count()==9
            for design in data['designs']:
                cells=page.locator('#current-comparison tr[data-design="'+design['id']+'"] td').all_text_contents()
                benchmark=design.get('current_benchmark')
                assert cells[1].startswith(design['current']['version'])
                if benchmark:
                    assert cells[2]==f"{benchmark['complete_cycles']} / {benchmark['admissible_manipulation_trials']}"
                    assert cells[3]==f"{benchmark['complete_cycles']} / {benchmark['planned']}"
                else:
                    assert cells[2]==('Pending cohort' if design['current']['passed'] else 'Not eligible')
        assert page.locator('.version').count()==data['preserved_versions']
        page.locator('#robot-filter').select_option('B'); assert page.locator('.card').count()==3
        page.locator('#tool-filter').select_option('B'); assert page.locator('.card').count()==1
        page.locator('#outcome-filter').select_option('tested'); assert page.locator('.card').count()==0
        assert page.locator('#empty').is_visible()
        page.locator('#reset-filters').click(); assert page.locator('.card').count()==9
        page.locator('#outcome-filter').select_option('failed')
        expected_failed={c['id'] for c in data['designs'] if (c['current']['passed'] is False if c.get('current') else not c['benchmark'])}
        assert {c.get_attribute('id').removeprefix('design-') for c in page.locator('.card').all()}==expected_failed
        page.locator('#reset-filters').click()
        if data['schema']=='rack_gallery_snapshot_v2':
            page.locator('#outcome-filter').select_option('passed')
            assert page.locator('.card').count()==sum(c['current']['passed'] is True for c in data['designs'])
            page.locator('#reset-filters').click()
        for img in page.locator('.card img').all():
            img.scroll_into_view_if_needed()
            page.wait_for_function('(img)=>img.complete && img.naturalWidth>0',arg=img.element_handle())
        assert page.locator('.current-cohort').count()==sum(bool(c.get('current_benchmark')) for c in data['designs'])
        for design in data['designs']:
            if design.get('current_benchmark'):
                b=design['current_benchmark']
                text=page.locator('#design-'+design['id']+' .current-cohort').inner_text()
                assert f"{b['complete_cycles']} / {b['planned']} planned starts" in text
                assert design['current']['version'] in text
        # Lazy videos are started by actual UI interaction, never autoplay.
        for design in data['designs']:
            if not design['media']: continue
            block=page.locator('#design-'+design['id'])
            block.locator('summary').first.click()
            for index, video in enumerate(block.locator('video').all()):
                selected = design['media'][index]
                presentation = selected.get('presentation')
                if presentation:
                    status = block.locator('.presentation-status').nth(index)
                    assert status.get_attribute('data-status') == presentation['status']
                    if presentation['status'] != 'candidate':
                        assert (presentation['status'] == 'accepted_working_presentation') == selected['source_task_passed']
                        clip = block.locator('.clip').nth(index)
                        for label, key in [('Acceptance record','record'),('Visual observations','visual_review'),('Temporal report','temporal_report')]:
                            target = presentation['links'][presentation[key]]
                            assert target in manifest['files']
                            assert clip.get_by_role('link',name=label,exact=True).get_attribute('href') == urllib.parse.urljoin(base,target)
                block.locator('.load-clip').nth(index).click()
                page.wait_for_function('(v)=>v.dataset.loaded==="true"',arg=video.element_handle())
                video.evaluate('(v)=>{v.muted=true}')
                page.wait_for_function('(v)=>v.readyState>=2',arg=video.element_handle())
                video.evaluate('(v)=>v.play()'); page.wait_for_timeout(350)
                details=video.evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,height:v.videoHeight,duration:v.duration,error:v.error?.message||null})')
                assert details['time']>0 and details['width']>=1920 and details['height']>=1080 and not details['error']
                video.evaluate('(v)=>{v.pause();v.currentTime=Math.max(0,v.duration-.5)}')
                page.wait_for_function('(v)=>!v.seeking && v.currentTime>=v.duration-.6',arg=video.element_handle())
                playback.append({'design':design['id'],'clip':index,
                                 'presentation_status':presentation['status'] if presentation else 'legacy',**details})
            block.locator('summary').first.click()
        page.evaluate('window.scrollTo(0,0)'); page.screenshot(path=str(args.output/'desktop.png'),full_page=True)
        page.set_viewport_size({'width':390,'height':844})
        # Let Chromium repaint after resizing; immediate captures can contain
        # stale desktop-compositor tiles despite the correct responsive DOM.
        page.wait_for_timeout(300)
        assert page.evaluate('document.documentElement.scrollWidth<=window.innerWidth')
        page.screenshot(path=str(args.output/'mobile.png'),full_page=True)
        assert not page.locator('#error').is_visible()
        browser.close()
    report={'passed':not errors,'url':base,'checked_files':checked,'playback':playback,'browser_errors':errors,
            'gallery_manifest_sha256':hashlib.sha256(get('manifest.json')).hexdigest(),
            'scope':'All allowlisted file hashes, browser filters, images, desktop/mobile layout and Mac video play/seek; not physics or visual-quality certification'}
    (args.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'passed':report['passed'],'files':len(checked),'videos':len(playback),'errors':errors}))
    if errors: raise SystemExit(1)


if __name__=='__main__': main()
