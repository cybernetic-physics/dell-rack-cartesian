"""Mac browser acceptance: actual noVNC input, verified against live PhysX state.

Requires the default 1600x1000 desktop/control-window layout and completed validation.
Runs a manual cycle and leaves the automatic demo playing. Do not use during validation.
"""
import io,json,time,urllib.request
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
from playwright.sync_api import sync_playwright

out=Path('artifacts'); out.mkdir(exist_ok=True)
base='http://127.0.0.1:18080/'
def read(name):
    return urllib.request.urlopen(base+name+'?t='+str(time.time()),timeout=5).read()
def state(): return json.loads(read('live-state.json'))
def wait_for(test,timeout=15):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        value=state()
        if test(value): return value
        time.sleep(.3)
    raise AssertionError(('Timed out waiting for GUI effect',state()))
def frame(): return Image.open(io.BytesIO(read('live.png'))).convert('RGB')
def difference(a,b):
    return sum(ImageStat.Stat(ImageChops.difference(a.resize((320,200)),b.resize((320,200)))).mean)/3

checks={}
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1600,'height':1050})
    errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale')
    canvas=page.locator('#noVNC_container canvas')
    page.wait_for_function("document.querySelector('#noVNC_container canvas')?.width===1600")
    page.wait_for_timeout(3000)
    bounds=canvas.bounding_box()
    def point(x,y): return bounds['x']+x*bounds['width']/1600,bounds['y']+y*bounds['height']/1000
    def click(x,y):
        page.mouse.click(*point(x,y),delay=100); page.wait_for_timeout(300)
    def field(y,value):
        page.mouse.dblclick(*point(1435,y),delay=100); page.keyboard.press('Control+A')
        page.keyboard.type(str(value)); page.keyboard.press('Enter')
    click(1460,209)  # Manual control
    wait_for(lambda s:not s['auto'])
    click(1190,242)  # Pause
    paused=wait_for(lambda s:not s['playing'])
    time.sleep(1.5)
    assert abs(state()['time']-paused['time'])<.01
    checks['pause_freezes_physics']=True
    before=frame()
    initial_camera=state()['camera_transform']
    click(1173,176)  # Front camera
    time.sleep(3)
    after=frame(); delta=difference(before,after)
    assert delta>5, delta
    checks['camera_preset_pixel_difference']=delta
    assert state()['camera_transform']!=initial_camera
    page.screenshot(path=str(out/'remote-front.png'))
    front_camera=state()['camera_transform']
    page.mouse.move(*point(450,220)); page.mouse.down(button='right')
    page.wait_for_timeout(200)
    page.mouse.move(*point(540,250),steps=15)
    page.mouse.up(button='right')
    time.sleep(2)
    assert state()['camera_transform']!=front_camera
    checks['viewport_navigation_changes_camera']=True
    click(1517,176)  # Connector camera
    click(1500,242)  # Stop/reset
    wait_for(lambda s:s['stopped'])
    time.sleep(1.5)
    click(1345,242)  # Resume; resets software and physics state
    reset=wait_for(lambda s:s['playing'] and s['cycles']==0 and s['state']=='unplugged')
    assert reset['time']<5,reset
    checks['stop_resume_resets']=True
    click(1460,275)  # Release clip button
    field(364,.2)  # Manual Y target in mm
    seated=wait_for(lambda s:s['state']=='retained')
    checks['manual_insert']=seated
    field(364,50)
    time.sleep(2)
    assert state()['state']=='retained'
    checks['manual_pull_retained']=True
    field(364,.2)
    time.sleep(.6)
    click(1230,275)  # Press clip
    wait_for(lambda s:s['state']=='released')
    field(364,50)
    removed=wait_for(lambda s:s['state']=='unplugged' and s['cycles']==1)
    checks['manual_clip_release_and_removal']=removed
    click(1230,209)  # Run repeated cycle
    repeated=wait_for(lambda s:s['cycles']>=2,timeout=30)
    checks['automatic_repeat']=repeated
    page.screenshot(path=str(out/'remote-viewer.png'))
    checks['javascript_errors']=errors
    assert not errors
    checks['passed']=True
    (out/'remote-interaction.json').write_text(json.dumps(checks,indent=2))
    print(json.dumps(checks,indent=2),flush=True)
    browser.close()
