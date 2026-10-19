"""Mac/noVNC test of destination buttons and a real port-1 -> port-2 handoff.
Run after row validation, with the default 1600x1000 desktop layout.
"""
import json,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

out=Path('artifacts/latch-row'); out.mkdir(parents=True,exist_ok=True)
def state():
    with urllib.request.urlopen('http://127.0.0.1:18080/live-state.json?t='+str(time.time()),timeout=5) as r:
        return json.load(r)
history=[]
def wait_for(predicate,timeout=65):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        s=state(); history.append(s)
        assert s['transfer']['error'] is None,s
        if predicate(s): return s
        time.sleep(.3)
    raise AssertionError(('Timed out',state()))

with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1600,'height':1050})
    errors=[]; page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto('http://127.0.0.1:16080/vnc.html?autoconnect=1&resize=scale')
    page.wait_for_function("document.querySelector('#noVNC_container canvas')?.width===1600")
    page.wait_for_timeout(3000)
    box=page.locator('#noVNC_container canvas').bounding_box()
    def click(x,y):
        page.mouse.click(box['x']+x*box['width']/1600,box['y']+y*box['height']/1000,delay=100)
        page.wait_for_timeout(300)
    assert state()['port_count']==16
    click(1460,209)  # Manual controller mode
    click(1146,336)  # Port 01
    print('Requested port 01 through noVNC',flush=True)
    first=wait_for(lambda s:s['connected_port']==1 and not s['transfer']['running'])
    click(1517,176)  # Latch close camera
    page.wait_for_timeout(1000)
    page.screenshot(path=str(out/'latch-unpressed.png'))
    click(1230,275)  # Physical pressing pad, not scripted release
    pressed=wait_for(lambda s:s['state']=='released' and s['metrics']['hook_clear'])
    assert pressed['metrics']['latch_angle_deg']<first['metrics']['latch_angle_deg']-4
    page.screenshot(path=str(out/'latch-pressed.png'))
    click(1460,275)  # Pad retracts; passive spring should reengage the same port
    reengaged=wait_for(lambda s:s['connected_port']==1 and s['metrics']['hook_behind_lip'])
    start=len(history)
    click(1203,336)  # Port 02
    print('Requested transfer 01 -> 02 through noVNC',flush=True)
    second=wait_for(lambda s:s['connected_port']==2 and not s['transfer']['running'])
    assert any(s['connected_port'] is None for s in history[start:]),'No extraction observed'
    assert second['cycles']>first['cycles'],'No completed unplug event'
    click(1173,176)  # Row camera
    page.wait_for_timeout(1200)
    page.screenshot(path=str(out/'remote-row.png'))
    click(1230,209)  # Repeated sweep
    third=wait_for(lambda s:s['connected_port']==3 and s['auto'])
    report={'passed':not errors,'port_count':16,'source_port':first,'destination_port':second,
            'physical_press':pressed,'spring_reengagement':reengaged,
            'automatic_next_port':third,'observed_phases':sorted({s['transfer']['phase'] for s in history}),
            'javascript_errors':errors,'history':history}
    (out/'remote-transfer.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k not in ('history','source_port','destination_port','automatic_next_port')}),flush=True)
    assert not errors
    browser.close()
