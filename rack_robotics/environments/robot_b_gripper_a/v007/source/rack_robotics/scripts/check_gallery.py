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
        assert page.locator('.version').count()==data['preserved_versions']
        page.locator('#robot-filter').select_option('B'); assert page.locator('.card').count()==3
        page.locator('#tool-filter').select_option('B'); assert page.locator('.card').count()==1
        page.locator('#outcome-filter').select_option('tested'); assert page.locator('.card').count()==0
        assert page.locator('#empty').is_visible()
        page.locator('#reset-filters').click(); assert page.locator('.card').count()==9
        page.locator('#outcome-filter').select_option('failed'); assert page.locator('.card').count()==1
        assert page.locator('.card').get_attribute('id')=='design-BB'
        page.locator('#reset-filters').click()
        for img in page.locator('.card img').all():
            img.scroll_into_view_if_needed()
            page.wait_for_function('(img)=>img.complete && img.naturalWidth>0',arg=img.element_handle())
        # Lazy videos are started by actual UI interaction, never autoplay.
        for design in data['designs']:
            if not design['media']: continue
            block=page.locator('#design-'+design['id'])
            block.locator('summary').first.click()
            for index, video in enumerate(block.locator('video').all()):
                block.locator('.load-clip').nth(index).click()
                page.wait_for_function('(v)=>v.dataset.loaded==="true"',arg=video.element_handle())
                video.evaluate('(v)=>{v.muted=true}')
                page.wait_for_function('(v)=>v.readyState>=2',arg=video.element_handle())
                video.evaluate('(v)=>v.play()'); page.wait_for_timeout(350)
                details=video.evaluate('(v)=>({time:v.currentTime,width:v.videoWidth,height:v.videoHeight,duration:v.duration,error:v.error?.message||null})')
                assert details['time']>0 and details['width']>=1920 and details['height']>=1080 and not details['error']
                video.evaluate('(v)=>{v.pause();v.currentTime=Math.max(0,v.duration-.5)}')
                page.wait_for_function('(v)=>!v.seeking && v.currentTime>=v.duration-.6',arg=video.element_handle())
                playback.append({'design':design['id'],'clip':index,**details})
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
