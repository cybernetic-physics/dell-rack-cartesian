"""Fresh-session load of the frozen full rack plus all-port mechanical regression.

This is deliberately a BASELINE test of the old hand-driven demo, not a robot
benchmark. It writes only into a new run directory and leaves the GUI untouched.
"""
import argparse
import json
from pathlib import Path
import sys
import time

parser = argparse.ArgumentParser()
parser.add_argument('--baseline', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args, _ = parser.parse_known_args()
args.output.mkdir(parents=True, exist_ok=False)
sys.path.insert(0, str(args.baseline.resolve()))

from isaacsim import SimulationApp
app = SimulationApp({'headless': True, 'multi_gpu': False, 'width': 640, 'height': 480})
try:
    import omni.usd
    from isaacsim.core.api import World
    from pxr import UsdGeom
    from rack_sim.config import CFG, ROW_PORTS
    from rack_sim.connector import Interaction
    from rack_sim.cable import Cable
    from rack_sim.row_demo import validate_row

    scene_file = args.baseline.resolve() / 'assets/latch-row/dell_rack.usda'
    assert omni.usd.get_context().open_stage(str(scene_file)), scene_file
    stage = omni.usd.get_context().get_stage()
    print('BASELINE_STAGE_LOADED', scene_file, flush=True)
    ports = [(f'/World/PortRow/Port{i+1:02d}', p) for i, p in enumerate(ROW_PORTS)]
    interaction = Interaction(stage, ROW_PORTS[0], ports)
    cable = Cable(stage, [f'/World/Cable/Link{i:02d}' for i in range(CFG.cable_segments)],
                  UsdGeom.BasisCurves(stage.GetPrimAtPath('/World/Cable/Jacket')))
    world = World(physics_dt=CFG.physics_dt, rendering_dt=1/60,
                  stage_units_in_meters=1, physics_prim_path='/World/Physics')
    world.reset()
    ticks = 0

    def step(count=1):
        global ticks
        for _ in range(count):
            world.step(render=False)
            if ticks % 8 == 0:
                world.render()
            interaction.update(CFG.physics_dt)
            if ticks % 4 == 0:
                cable.update()
            ticks += 1

    def move(target, seconds=1):
        start = list(interaction.target)
        count = int(seconds / CFG.physics_dt)
        for i in range(count):
            a = (i+1)/count
            a = a*a*(3-2*a)
            interaction.set_target([s+(t-s)*a for s,t in zip(start,target)])
            step()

    step(240)
    started = time.monotonic()
    report = validate_row(interaction, cable, move, step, lambda _: None, lambda _: None)
    report.update(scene_file=str(scene_file), source=str(args.baseline.resolve()),
                  scope='Existing hand-driven baseline; NOT a robotic manipulation test',
                  wall_seconds=time.monotonic()-started)
    (args.output / 'results.json').write_text(json.dumps(report, indent=2)+'\n')
    print('BASELINE_RESULT', report['passed'], len(report['checks']), flush=True)
    if not report['passed']:
        raise RuntimeError('Baseline regression failed')
finally:
    app.close()
