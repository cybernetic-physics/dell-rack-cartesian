"""Run with system Python inside the container after physical validation."""
import argparse,hashlib,json,subprocess
from pathlib import Path
from PIL import Image,ImageStat

parser=argparse.ArgumentParser(); parser.add_argument('--port-row',action='store_true'); args=parser.parse_args()
root=Path('/workspace'); out=root/'artifacts'/('latch-row' if args.port_row else 'latch-single')
report=json.loads((out/'validation.json').read_text())
assert report['passed'], 'Physical validation did not pass'
assert len(report['checks'])>=16
checks={'physics':report['passed'],'source':report.get('run_source')}
probe=json.loads((root/'artifacts/latch-probe-2.json').read_text())
assert probe['passed'], 'Mechanical latch regression did not pass'
for relative in ('rack_sim/latch.py','rack_sim/connector.py','rack_sim/geometry.py','rack_sim/config.py'):
    assert (root/relative).read_bytes()==(Path(probe['run_source'])/relative).read_bytes(), f'Untested latch source: {relative}'
checks['mechanical_latch']={'passed':True,'checks':len(probe['checks']),'source':probe['run_source']}
if args.port_row: assert report['port_count']==16
for name in (('rear','row','handoff') if args.port_row else ('front','rear','rear_detail','connector')):
    im=Image.open(out/f'{name}.png').convert('RGB')
    spread=max(ImageStat.Stat(im).stddev)
    assert im.width>=1920 and im.height>=1200 and spread>10, (name,im.size,spread)
    checks[name]={'size':im.size,'pixel_stddev':spread}
video=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
    'format=duration:stream=codec_name,width,height,nb_frames','-of','json',str(out/'demo.mp4')]))
assert float(video['format']['duration'])>=(6 if args.port_row else 7)
assert video['streams'][0]['codec_name']=='h264'
checks['video']=video
for name in ('dell_rack','rack','servers','rj45_socket','rj45_plug','cable'):
    path=root/'assets'/('latch-row' if args.port_row else 'latch-single')/f'{name}.usda'
    assert path.stat().st_size>100
    if name=='rj45_plug':
        usd=path.read_text()
        assert 'def PhysicsRevoluteJoint "LatchHinge"' in usd
        assert 'def PhysicsPrismaticJoint "ClipPressSlide"' in usd
        assert 'def PhysicsFixedJoint "Retention"' not in usd
checks['source_sha256']={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [root/'demo.py',*sorted((root/'rack_sim').glob('*.py'))]}
for relative,digest in checks['source_sha256'].items():
    tested=Path(report['run_source'])/relative
    assert hashlib.sha256(tested.read_bytes()).hexdigest()==digest, f'Untested source change: {relative}'
checks['tested_source_matches_delivery']=True
checks['passed']=True
(out/'delivery-smoke.json').write_text(json.dumps(checks,indent=2))
print(json.dumps(checks,indent=2))
