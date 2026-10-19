"""Actually load, decode and seek a downloaded MP4 in Chrome on the Mac."""
import argparse
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

parser=argparse.ArgumentParser()
parser.add_argument('video',type=Path)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
video=args.video.resolve()
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1920,'height':1080})
    errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(video.as_uri())
    page.wait_for_function("document.querySelector('video')?.readyState>=2")
    page.evaluate("async()=>{const v=document.querySelector('video');v.muted=true;await v.play()}")
    page.wait_for_timeout(1500)
    playback=page.evaluate("()=>{const v=document.querySelector('video');return {width:v.videoWidth,height:v.videoHeight,duration:v.duration,time:v.currentTime,error:v.error?.message||null}}")
    assert playback['time']>0 and not playback['error']
    page.evaluate("()=>{const v=document.querySelector('video');v.pause();v.currentTime=Math.max(0,v.duration-.5)}")
    page.wait_for_function("(()=>{const v=document.querySelector('video');return !v.seeking && v.currentTime>=v.duration-.6})()")
    seek=page.evaluate("document.querySelector('video').currentTime")
    browser.close()
report={'passed':not errors,'video':str(video),'sha256':hashlib.sha256(video.read_bytes()).hexdigest(),
        'playback':playback,'seek_time_s':seek,'browser_errors':errors,
        'scope':'Mac Chrome decode/playback/seek only; NOT a physics or visual-fidelity verdict'}
with args.output.open('x') as target: target.write(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
