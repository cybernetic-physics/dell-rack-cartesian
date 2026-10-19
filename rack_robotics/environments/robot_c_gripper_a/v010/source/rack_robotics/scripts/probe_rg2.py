"""Measure the unscaled vendor RG2 linkage before designing RJ45 fingertips.

Isolated empty-jaw test, not a rack-feasibility or gripping-force certification.
Only finger_joint is commanded. All link poses are read from physics. Outputs
include the referenced asset, license, source, initial scene and measured trace.
Run separately at 240 and 480 Hz to expose timestep sensitivity.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import traceback

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--hz', type=int, choices=(240, 480), default=240)
parser.add_argument('--targets', type=float, nargs='+', default=(0, 10, 20, 30, 40, 50, 60, 70, 60, 40, 20, 0))
parser.add_argument('--torque-cap', type=float, help='Optional angular drive cap, Nm; not a contact-force setting')
args, _ = parser.parse_known_args()
if any(not math.isfinite(q) or not 0 <= q <= 70.06 for q in args.targets):
    parser.error('Every target must lie within 0..70.06 degrees')
if len(args.targets) < 2 or args.targets[-1] != args.targets[0]:
    parser.error('Sweep must include at least two entries and return to its first angle')
if args.torque_cap is not None and (not math.isfinite(args.torque_cap) or args.torque_cap <= 0):
    parser.error('Torque cap must be finite and positive')
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
vendor = root / 'rack_robotics/research/sources/onrobot-isaacsim'
shutil.copytree(vendor / 'assets/rg2', out / 'assets/rg2')
shutil.copy2(vendor / 'LICENSE', out / 'assets/LICENSE-OnRobot')
shutil.copy2(vendor / 'README.md', out / 'assets/README-OnRobot.md')
shutil.copy2(__file__, out / 'probe_rg2.py')
manifest = {str(p.relative_to(out)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in out.rglob('*') if p.is_file()}
(out / 'source_manifest.json').write_text(json.dumps(manifest, indent=2))

from isaacsim import SimulationApp
app = SimulationApp({'headless': True, 'multi_gpu': False,
                     'width': 640, 'height': 480})
samples = []
try:
    import omni.usd
    from pxr import Gf, Usd, UsdGeom, UsdPhysics, PhysxSchema
    from isaacsim.core.api import World
    from isaacsim.core.prims import SingleArticulation

    stage = omni.usd.get_context().get_stage()
    UsdGeom.SetStageUpAxis(stage, 'Z')
    UsdGeom.SetStageMetersPerUnit(stage, 1)
    prim = stage.DefinePrim('/World/RG2', 'Xform')
    prim.GetReferences().AddReference(str(out / 'assets/rg2/onrobot_rg2.usda'))
    prim.GetVariantSets().GetVariantSet('Physics').SetVariantSelection('physx_parallel_grip')
    # Original +Z extension becomes rack insertion -Y. This is authored ONCE,
    # before physics; the fixed joint, not the parent transform, holds the tool.
    transform = UsdGeom.Xformable(prim)
    transform.AddTranslateOp().Set(Gf.Vec3d(0, 0, .4))
    transform.AddRotateXOp().Set(90)
    mount = UsdPhysics.FixedJoint.Get(stage, '/World/RG2/Physics/root_joint')
    mount.GetBody0Rel().SetTargets([])
    mount.CreateLocalPos0Attr().Set(Gf.Vec3f(0, 0, .4))
    rotation = Gf.Rotation(Gf.Vec3d(1, 0, 0), 90).GetQuat()
    mount.CreateLocalRot0Attr().Set(Gf.Quatf(rotation))
    scene = UsdPhysics.Scene.Define(stage, '/World/Physics')
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0, 0, -1))
    scene.CreateGravityMagnitudeAttr(9.81)
    scene_api = PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
    scene_api.CreateSolverTypeAttr().Set('TGS')
    scene_api.CreateTimeStepsPerSecondAttr().Set(args.hz)
    scene_api.CreateEnableExternalForcesEveryIterationAttr().Set(True)
    drive = UsdPhysics.DriveAPI.Get(stage.GetPrimAtPath('/World/RG2/Physics/finger_joint'), 'angular')
    drive.GetTargetPositionAttr().Set(args.targets[0])
    if args.torque_cap is not None:
        drive.GetMaxForceAttr().Set(args.torque_cap)

    bodies = [p for p in stage.Traverse() if p.HasAPI(UsdPhysics.RigidBodyAPI)]
    colliders = [str(p.GetPath()) for p in stage.Traverse() if p.HasAPI(UsdPhysics.CollisionAPI)]
    filters = {str(p.GetPath()): [str(t) for t in p.GetRelationship('physics:filteredPairs').GetTargets()]
               for p in bodies if p.HasAPI(UsdPhysics.FilteredPairsAPI)}
    audit = {'mass_kg': sum(UsdPhysics.MassAPI(p).GetMassAttr().Get() or 0 for p in bodies),
             'body_count': len(bodies), 'colliders': colliders, 'filtered_pairs': filters,
             'self_collisions': prim.GetAttribute('physxArticulation:enabledSelfCollisions').Get(),
             'variant': 'physx_parallel_grip', 'hz': args.hz,
             'target_angles_deg': args.targets, 'angular_drive_cap_nm': drive.GetMaxForceAttr().Get(),
             'limitations': ['Vendor internal pair filtering retained for isolated linkage characterization.',
                             'Vendor drive inertia and mimic tuning are numerical assumptions, not calibrated hardware.',
                             'Tip-origin separation is not the contact-surface aperture. No payload or connector in this test.']}
    (out / 'asset_audit.json').write_text(json.dumps(audit, indent=2))
    stage.GetRootLayer().Export(str(out / 'scene.usda'))
    world = World(physics_dt=1/args.hz, rendering_dt=1/60,
                  stage_units_in_meters=1, physics_prim_path='/World/Physics')
    world.reset()
    articulation = SingleArticulation(prim_path='/World/RG2')
    articulation.initialize()
    index = articulation.get_dof_index('finger_joint')

    def measure(label, target):
        cache = UsdGeom.XformCache()
        base = cache.GetLocalToWorldTransform(stage.GetPrimAtPath('/World/RG2/Geometry/base_link'))
        tips = {}
        for side in ('left', 'right'):
            p = stage.GetPrimAtPath(f'/World/RG2/Geometry/{side}_finger_tip_link')
            relative = cache.GetLocalToWorldTransform(p) * base.GetInverse()
            tips[side] = {'origin_m': list(relative.ExtractTranslation()),
                          'matrix': [float(v) for row in relative for v in row]}
        q = articulation.get_joint_positions()
        return {'phase': label, 'target_deg': target,
                'joint_deg': math.degrees(float(q[index])),
                'all_joint_positions_rad': [float(v) for v in q],
                'tips': tips,
                'tip_origin_separation_m': tips['right']['origin_m'][0] - tips['left']['origin_m'][0],
                'tip_extension_m': (tips['right']['origin_m'][2] + tips['left']['origin_m'][2]) / 2,
                'base_world_position_m': list(base.ExtractTranslation())}

    endpoints = []
    for number, target in enumerate(args.targets):
        drive.GetTargetPositionAttr().Set(target)
        label = f'{number:02d}_target_{target}'
        for k in range(round(2.5 * args.hz)):
            world.step(render=False)
            if k % (args.hz // 30) == 0:
                world.render()
                samples.append(measure(label, target))
        world.render()
        endpoints.append(measure(label, target))
        print('RG2_SWEEP', target, endpoints[-1]['joint_deg'],
              endpoints[-1]['tip_origin_separation_m'], endpoints[-1]['tip_extension_m'], flush=True)
    finite = all(math.isfinite(v) for s in samples for v in s['all_joint_positions_rad'])
    checks = {
        'finite_joint_states': finite,
        'single_drive_tracks': max(abs(s['joint_deg'] - s['target_deg']) for s in endpoints) < .25,
        'fixed_mount_holds': max(math.dist(s['base_world_position_m'], (0, 0, .4)) for s in samples) < .0001,
        'both_fingers_move': all(max(s['tips'][side]['origin_m'][0] for s in endpoints) - min(s['tips'][side]['origin_m'][0] for s in endpoints) > .001 for side in ('left', 'right')),
        'reopens_repeatably': abs(endpoints[-1]['tip_origin_separation_m'] - endpoints[0]['tip_origin_separation_m']) < .0001,
    }
    report = {'passed': all(checks.values()), 'scope': 'isolated unloaded RG2 linkage sweep; not RJ45 feasibility',
              'hz': args.hz, 'checks': checks, 'dof_names': articulation.dof_names,
              'endpoints': endpoints, 'samples': samples}
    (out / 'results.json').write_text(json.dumps(report, indent=2))
    print('RG2_PROBE', checks, flush=True)
except Exception:
    error = traceback.format_exc()
    (out / 'exception.txt').write_text(error)
    (out / 'results.json').write_text(json.dumps({'passed': False, 'error': error, 'samples': samples}, indent=2))
    raise
finally:
    app.close()
