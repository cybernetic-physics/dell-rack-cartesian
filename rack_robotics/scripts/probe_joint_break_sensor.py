"""Calibrate ordinary D6 break-force events against known gravitational loads.

Isolated destructive sensor controls only: no rack, cable safety rating, or
RJ45 task-success claim. Existing scenes and benchmark evidence are untouched.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import traceback


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--gpu', type=int, default=0)
    parser.add_argument('--position-iterations', type=int, default=128)
    parser.add_argument('--velocity-iterations', type=int, default=8)
    args, _ = parser.parse_known_args()
    if not (1 <= args.position_iterations <= 255 and 0 <= args.velocity_iterations <= 255):
        parser.error('Solver iteration counts outside supported diagnostic range')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    source = output / 'probe_joint_break_sensor.py'
    shutil.copy2(__file__, source)
    provenance = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                  'scope': 'Isolated ordinary-D6 gravitational load controls, not a rack trial',
                  'gravity_m_s2': 9.81, 'physics_dt_s': 1 / 480,
                  'solver_position_iterations': args.position_iterations,
                  'solver_velocity_iterations': args.velocity_iterations,
                  'limitations': [
                      'Break-force events threshold resultant constraint force, not axial tension.',
                      'Joint drive forces are excluded by PhysX from break-force accounting.',
                      'No manufacturer cable or connector safe-load rating is asserted.',
                      'No absence-of-break claim is valid without the positive controls passing.']}
    (output / 'manifest.json').write_text(json.dumps(provenance, indent=2) + '\n')
    from isaacsim import SimulationApp
    app = SimulationApp({'headless': True, 'multi_gpu': False,
                         'active_gpu': args.gpu, 'physics_gpu': args.gpu,
                         'width': 320, 'height': 240})
    try:
        import omni.usd
        from omni.physx import get_physx_interface
        from omni.physx.bindings._physx import SimulationEvent
        from isaacsim.core.api import World
        from pxr import Gf, UsdGeom, UsdPhysics, PhysxSchema, PhysicsSchemaTools

        stage = omni.usd.get_context().get_stage()
        UsdGeom.SetStageUpAxis(stage, 'Z')
        UsdGeom.SetStageMetersPerUnit(stage, 1)
        UsdPhysics.SetStageKilogramsPerUnit(stage, 1)
        UsdGeom.Xform.Define(stage, '/World')
        scene = UsdPhysics.Scene.Define(stage, '/World/Physics')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
        scene.CreateGravityMagnitudeAttr(9.81)
        PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateSolverTypeAttr('TGS')
        fixtures, events, samples = [], [], []
        step_index = -1

        def on_event(event):
            if event.type == int(SimulationEvent.JOINT_BREAK):
                encoded = event.payload['jointPath']
                events.append({'joint': str(PhysicsSchemaTools.decodeSdfPath(*encoded)),
                               'observed_step': step_index})

        subscription = get_physx_interface().get_simulation_event_stream_v2().create_subscription_to_pop(on_event)
        for mass in (.0007, .0252, .1):
            for ratio in (.5, .9, 1.1, 2.):
                index = len(fixtures)
                base = '/World/Fixture%02d' % index
                UsdGeom.Xform.Define(stage, base)
                body = UsdGeom.Cube.Define(stage, base + '/Body')
                body.CreateSizeAttr(.01)
                position = Gf.Vec3d(index * .1, 0, 1)
                body.AddTranslateOp().Set(position)
                UsdPhysics.CollisionAPI.Apply(body.GetPrim())
                UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
                UsdPhysics.MassAPI.Apply(body.GetPrim()).CreateMassAttr(mass)
                rb = PhysxSchema.PhysxRigidBodyAPI.Apply(body.GetPrim())
                rb.CreateSolverPositionIterationCountAttr(args.position_iterations)
                rb.CreateSolverVelocityIterationCountAttr(args.velocity_iterations)
                rb.CreateSleepThresholdAttr(0)
                joint = UsdPhysics.Joint.Define(stage, base + '/D6')
                joint.CreateBody1Rel().SetTargets([body.GetPath()])
                joint.CreateLocalPos0Attr(Gf.Vec3f(*position))
                joint.CreateLocalPos1Attr(Gf.Vec3f(0))
                joint.CreateBreakForceAttr(mass * 9.81 * ratio)
                for axis in ('transX', 'transY', 'transZ'):
                    limit = UsdPhysics.LimitAPI.Apply(joint.GetPrim(), axis)
                    limit.CreateLowAttr(1)
                    limit.CreateHighAttr(-1)
                for axis in ('rotX', 'rotY', 'rotZ'):
                    limit = UsdPhysics.LimitAPI.Apply(joint.GetPrim(), axis)
                    limit.CreateLowAttr(-40)
                    limit.CreateHighAttr(40)
                    drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), axis)
                    drive.CreateTypeAttr('force')
                    drive.CreateStiffnessAttr(.0002)
                    drive.CreateDampingAttr(.00008)
                fixtures.append({'body': str(body.GetPath()), 'joint': str(joint.GetPath()),
                                 'mass_kg': mass, 'expected_load_n': mass * 9.81,
                                 'threshold_n': mass * 9.81 * ratio,
                                 'threshold_to_load_ratio': ratio, 'expected_break': ratio < 1})
        stage.GetRootLayer().Export(str(output / 'scene.usda'))
        world = World(physics_dt=1 / 480, rendering_dt=1 / 60,
                      stage_units_in_meters=1, physics_prim_path='/World/Physics')
        world.reset()
        for step_index in range(480):
            world.step(render=(step_index % 8 == 0))
            if step_index % 8 == 0 or step_index == 479:
                samples.append({'step': step_index, 'z_m': [float(
                    UsdGeom.Xformable(stage.GetPrimAtPath(f['body'])).ComputeLocalToWorldTransform(0).ExtractTranslation()[2])
                    for f in fixtures]})
        # Flush queued simulation events while keeping the subscription alive.
        world.pause()
        app.update()
        broken = {event['joint'] for event in events}
        for fixture, z in zip(fixtures, samples[-1]['z_m']):
            fixture['event_received'] = fixture['joint'] in broken
            fixture['final_z_m'] = z
            fixture['motion_agrees'] = (z < .9 if fixture['expected_break'] else abs(z - 1) < .001)
            fixture['passed'] = (fixture['event_received'] == fixture['expected_break']
                                 and fixture['motion_agrees'] and math.isfinite(z))
        checks = {'all_threshold_and_motion_controls': all(f['passed'] for f in fixtures),
                  'only_expected_joint_events': broken <= {f['joint'] for f in fixtures},
                  'all_samples_finite': all(math.isfinite(z) for s in samples for z in s['z_m'])}
        report = {**provenance, 'passed': all(checks.values()), 'checks': checks,
                  'fixtures': fixtures, 'events': events, 'samples': samples,
                  'scene_sha256': hashlib.sha256((output / 'scene.usda').read_bytes()).hexdigest()}
        (output / 'results.json').write_text(json.dumps(report, indent=2) + '\n')
        print('JOINT_BREAK_SENSOR', json.dumps({'passed': report['passed'], 'checks': checks}), flush=True)
        if not report['passed']:
            raise RuntimeError('D6 break-force calibration controls failed; see results.json')
    except Exception:
        error = traceback.format_exc()
        (output / 'failure.json').write_text(json.dumps({'passed': False, 'error': error}, indent=2) + '\n')
        print(error, flush=True)
        raise
    finally:
        app.close()


if __name__ == '__main__':
    main()
