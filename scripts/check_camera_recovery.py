"""Actual noVNC regression: side views automatically return to perspective."""
import io,json,time,urllib.request
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

out=Path('artifacts/latch-row'); out.mkdir(parents=True,exist_ok=True)
def state():
    with urllib.request.urlopen('http://127.0.0.1:18080/live-state.json?t='+str(time.time()),timeout=5) as r:
        return json.load(r)
def wait_for(predicate):
    end=time.monotonic()+20
    while time.monotonic()<end:
        value=state()
        if predicate(value): return value
        time.sleep(.3)
    raise AssertionError(state())

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1600,'height':1050})
    page.goto('http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale')
    page.wait_for_function("document.querySelector('#noVNC_container canvas')?.width===1600")
    page.wait_for_timeout(3500)
    box=page.locator('#noVNC_container canvas').bounding_box()
    def click(x,y):
        page.mouse.click(box['x']+x*box['width']/1600,box['y']+y*box['height']/1000,delay=150)
        page.wait_for_timeout(600)
    page.keyboard.press('Escape')
    click(500,220)  # Focus the native application after connecting noVNC
    initial=state(); assert initial['perspective_lock']
    recoveries=[]
    for name,y in [('Right',216),('Top',165),('Front',190)]:
        count=state()['camera_recoveries']
        page.keyboard.press('Escape')
        click(500,220)
        # Native toolbar focus sometimes consumes the first click. Verify that
        # the menu is actually open before selecting a coordinate inside it.
        for attempt in range(3):
            click(350,70)
            page.wait_for_timeout(900)
            pixels=Image.open(io.BytesIO(page.screenshot())).convert('RGB')
            samples=[pixels.getpixel((round(box['x']+505*box['width']/1600),
                      round(box['y']+y0*box['height']/1000))) for y0 in (135,160,185,210)]
            if all(max(abs(a-b) for a,b in zip(sample,(37,40,42)))<8 for sample in samples):
                break
        else:
            raise AssertionError('Native camera menu did not open')
        page.screenshot(path=str(out/f'camera-menu-{name.lower()}.png'))
        click(337,y)
        restored=wait_for(lambda s:s['camera_recoveries']>count and s['active_camera']=='/OmniverseKit_Persp')
        assert restored['last_rejected_camera']=='/OmniverseKit_'+name,restored
        recoveries.append(restored)
        print('Automatically recovered from',name,flush=True)
    click(1173,176)
    before=state()['camera_transform']
    page.mouse.move(box['x']+500,box['y']+220)
    page.mouse.wheel(0,-300)
    navigated=wait_for(lambda s:s['camera_transform']!=before)
    assert navigated['active_camera']=='/OmniverseKit_Persp'
    click(1173,176)  # Restore full row framing after testing free navigation
    restored=state()
    moving=wait_for(lambda s:s['cycles']>restored['cycles'])
    assert moving['playing'] and moving['auto'] and moving['transfer']['error'] is None
    assert moving['active_camera']=='/OmniverseKit_Persp'
    page.screenshot(path=str(out/'camera-guard.png'))
    report={'passed':True,'initial':initial,'automatic_recoveries':recoveries,'navigation':navigated,'continued_transfer':moving}
    (out/'camera-guard.json').write_text(json.dumps(report,indent=2))
    print('PASS: Right/Top/Front automatically restored; zoom and transfer still work.')
    browser.close()
