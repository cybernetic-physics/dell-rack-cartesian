"""Drive a saved precision/specialized-tool assembly through a retracted rack raster.

This is an unloaded travel/clearance probe, not an RJ45 success trial. No body
poses/velocities are written after reset. Stop on the first measured collision,
carrier violation, nonfinite state, or tracking failure; preserve partial motion.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import traceback


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--environment', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args, _ = parser.parse_known_args()
root = Path(__file__).resolve().parents[2]
environment = args.environment.resolve()
output = args.output.resolve()
config = json.loads((environment/'config.json').read_text())
manifest = json.loads((environment/'manifest.json').read_text())
for name, digest in manifest['packaged_file_sha256'].items():
    if sha(environment/name) != digest:
        raise ValueError('Changed packaged input: '+name)
output.mkdir(parents=True, exist_ok=False)
snapshot = output/'source'
hashes = {}
for source in (root/'rack_robotics').rglob('*.py'):
    relative = source.relative_to(root)
    if any(p in relative.parts for p in ('assets','research','experiments','environments','__pycache__')):
        continue
    target = snapshot/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    hashes[str(relative)] = sha(target)
save(output/'source_manifest.json', hashes)
baseline = root/'rack_robotics/assets/shared_rack/baseline-001'
sys.path.insert(0,str(snapshot))
sys.path.insert(0,str(baseline))
from rack_robotics.workspace_probe import REVISION, TELESCOPING_REVISION, fixture_architecture, retracted_raster, telescoping_retracted_raster, move_duration, interpolate, robot_contact_violations
architecture = fixture_architecture(config)
gripper = config['gripper'].split('_')[0]
revision = TELESCOPING_REVISION if architecture == 'B' else REVISION
hz = round(1/config['physics_dt'])
if hz not in (240,480,960):
    raise ValueError('Unsupported source timestep')
dt = 1/hz
gates = {'contact_force_n':.1, 'moving_tracking_error_m':.010,
         'settled_tracking_error_m':.002, 'joint_limit_error_m':.001,
         'maximum_joint_speed_m_s':.06, 'endpoint_hold_s':.75}
scope = 'Unloaded retracted finite-raster travel through the unchanged full rack; NOT connector manipulation or continuous-volume clearance'
save(output/'manifest.json', {'environment':str(environment),
    'environment_manifest_sha256':sha(environment/'manifest.json'),
    'revision':revision, 'architecture':architecture, 'gripper':gripper,
    'physics_hz':hz, 'gates':gates, 'scope':scope})

from isaacsim import SimulationApp
app = SimulationApp({'headless':True,'multi_gpu':False,'width':1280,'height':800})
recorder = stream = contacts = None
frame = 0
startup_samples = []
travel_samples = []
reached = []
plan = []
violations = []
error = None
try:
    import numpy as np
    import omni.usd
    from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema
    from isaacsim.core.api import World
    from rack_sim.config import CFG, ROW_PORTS
    from rack_sim.connector import Interaction
    from rack_sim.cable import Cable
    from rack_sim.scene import camera
    from rack_robotics.mechanics import reference_drives
    from rack_robotics.belt_gantry import CoreXZTransmission
    from rack_robotics.brake_runtime import BrakeRuntime
    from rack_robotics.service_carriers import carrier_metrics, initialize_cartesian_states, initialize_prismatic_states
    from rack_robotics.carrier_validation import carrier_integrity_checks
    from rack_robotics.controllers.connector_observer import ConnectorObserver
    from rack_robotics.recording import TrajectoryRecorder
    from rack_robotics.contacts import ContactRecorder
    from rack_robotics.integrity import audit_trial
    from omni.kit.viewport.utility import capture_viewport_to_file, get_active_viewport

    scene = output/'scene.usda'
    layer = Usd.Stage.CreateNew(str(scene))
    layer.GetRootLayer().subLayerPaths = [os.path.relpath(environment/'scene.usda',output)]
    layer.GetRootLayer().Save()
    del layer
    assert omni.usd.get_context().open_stage(str(scene))
    for _ in range(30): app.update()
    while omni.usd.get_context().get_stage_loading_status()[2] > 0: app.update()
    stage = omni.usd.get_context().get_stage()
    if not stage.GetPrimAtPath('/World/Robot/ServiceCarriers'):
        raise ValueError('Carrier-equipped scene is required for this probe')
    drives = reference_drives(stage,architecture,gripper)
    initial = initialize_cartesian_states(stage,architecture)
    if gripper == 'A':
        initial.extend(initialize_prismatic_states(stage,['LeftJaw','RightJaw','LatchPress']))
    save(output/'startup_states.json', initial)
    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath('/World/Physics')).CreateTimeStepsPerSecondAttr(hz)
    ports = [(f'/World/PortRow/Port{i+1:02d}',p) for i,p in enumerate(ROW_PORTS)]
    observer = initialization = Interaction(stage,ROW_PORTS[0],ports)
    cable = Cable(stage,[f'/World/Cable/Link{i:02d}' for i in range(CFG.cable_segments)],
                  UsdGeom.BasisCurves(stage.GetPrimAtPath('/World/Cable/Jacket')))
    keys = ('x_outer','x_inner','y','z') if architecture == 'B' else ('x','y','z')
    limits = {key:(UsdPhysics.PrismaticJoint(drives[key].GetPrim()).GetLowerLimitAttr().Get(),
                   UsdPhysics.PrismaticJoint(drives[key].GetPrim()).GetUpperLimitAttr().Get())
              for key in keys}
    start = {key:drives[key].GetTargetPositionAttr().Get() for key in limits}
    raster = telescoping_retracted_raster if architecture == 'B' else retracted_raster
    plan = raster(limits) + [{'name':'return_authored_park','target':start}]
    save(output/'plan.json', {'limits':limits,'start':start,'waypoints':plan,'scope':scope})
    stage.GetRootLayer().Save()  # Save only initial opinions, not the live state.
    contacts = ContactRecorder(stage,dt)
    world = World(physics_dt=dt,rendering_dt=1/60,stage_units_in_meters=1,
                  physics_prim_path='/World/Physics')
    world.reset()
    transmission = CoreXZTransmission(stage,drives) if architecture == 'C' else None
    brake = BrakeRuntime(stage,drives,architecture,transmission)
    articulation = brake.articulation
    indices = np.array([articulation.get_dof_index(drives[k].GetPrim().GetName())
                        for k in limits])
    camera(stage,'rear')
    recorder = TrajectoryRecorder(stage,output/'trajectory.jsonl')
    stream = (output/'trace.jsonl').open('x')

    def step(phase, startup=False):
        global frame, violations
        contacts.phase = phase
        contacts.time = frame*dt
        applied = brake.step(dt,release=True)
        world.step(render=False)
        observer.update(dt)
        frame += 1
        # Contact reports are gathered every physics tick, including startup.
        violations = robot_contact_violations(contacts.pairs.values(),gates['contact_force_n'])
        if contacts.errors or violations:
            raise RuntimeError('Robot contact threshold or contact reporting failure: '+
                               str([p['colliders'] for p in violations[:3]] or contacts.errors))
        q = articulation.get_joint_positions(joint_indices=indices).tolist()
        v = articulation.get_joint_velocities(joint_indices=indices).tolist()
        if not all(math.isfinite(value) for value in q+v):
            raise RuntimeError('Nonfinite joint state')
        measured = dict(zip(limits,q))
        if any(not lo-.001 <= measured[k] <= hi+.001 for k,(lo,hi) in limits.items()):
            raise RuntimeError('Measured joint limit exceeded: '+str(measured))
        tracking = max(abs(measured[k]-drives[k].GetTargetPositionAttr().Get()) for k in limits)
        if not startup and tracking > gates['moving_tracking_error_m']:
            raise RuntimeError('Moving tracking error exceeded 10 mm: '+str(tracking))
        if frame % (hz//30) == 0:
            world.render()
            cable.update()
            if transmission: transmission.update_visuals()
            metric = carrier_metrics(stage)
            sample = {'time_s':frame*dt,'phase':phase,**metric}
            (startup_samples if startup else travel_samples).append(sample)
            recorder.sample(frame*dt,phase)
            stream.write(json.dumps({'time_s':frame*dt,'phase':phase,'position_m':measured,
                'velocity_m_s':dict(zip(limits,v)), 'tracking_error_m':tracking,
                'target_m':{k:drives[k].GetTargetPositionAttr().Get() for k in limits},
                'motor_and_brake':applied})+'\n')
            stream.flush()
            if not all(carrier_integrity_checks([sample],[sample]).values()):
                raise RuntimeError('Carrier integrity failure: '+str(sample))
        return measured, tracking

    for k in range(round(3*hz)):
        u = min(1.,k/(2*hz))
        u = u*u*(3-2*u)
        initialization.set_target((0,.05+(.0002-.05)*u,0))
        step('physical_preseat',startup=True)
    if initialization.connected_port != 0:
        raise RuntimeError('Initialization could not physically seat connector')
    for path in ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress'):
        stage.GetPrimAtPath(path).SetActive(False)
    observer = ConnectorObserver(stage,ports,previous=initialization)
    for _ in range(hz): step('fixture_removed_settle',startup=True)
    integrity = audit_trial(stage,ports,CFG.cable_segments)
    save(output/'physics_integrity.json', integrity)
    if not integrity['passed']: raise RuntimeError('Physics integrity failed')
    contacts.save(output/'initialization_contacts.json')
    # Do not clear contacts: a startup collision cannot disappear from acceptance.
    current = start
    for waypoint in plan:
        phase = waypoint['name']
        target = waypoint['target']
        steps = math.ceil(move_duration(current,target,gates['maximum_joint_speed_m_s'])*hz)
        print('WORKSPACE_BEGIN',phase,target,flush=True)
        for k in range(steps):
            for name,value in interpolate(current,target,(k+1)/steps).items():
                drives[name].GetTargetPositionAttr().Set(value)
            step(phase)
        for _ in range(round(gates['endpoint_hold_s']*hz)):
            measured,tracking = step(phase+'_hold')
        if tracking > gates['settled_tracking_error_m']:
            raise RuntimeError('Endpoint tracking error exceeded 2 mm: '+str(tracking))
        reached.append({'name':phase,'target':target,'measured':measured,'error_m':tracking})
        save(output/'reached.json',reached)
        print('WORKSPACE_REACHED',phase,measured,flush=True)
        current = target
except Exception:
    error = traceback.format_exc()
    print(error,flush=True)
finally:
    if recorder: recorder.close()
    if stream: stream.close()
    if contacts: contacts.save(output/'contacts.json')
    if 'world' in globals() and recorder:
        # Render/read the final physical state without advancing physics.
        try:
            import omni.timeline
            omni.timeline.get_timeline_interface().pause()
            world.render()
            final_snapshot = TrajectoryRecorder(stage,output/'final_snapshot.jsonl')
            final_snapshot.sample(frame*dt,'failure' if error else 'completed')
            final_snapshot.close()
            capture_viewport_to_file(get_active_viewport(),str(output/'diagnostic.png'))
            for _ in range(20): app.update()
        except Exception as capture_error:
            save(output/'diagnostic_error.json',{'error':repr(capture_error)})
    save(output/'carrier_metrics.json',{'startup':startup_samples,'travel':travel_samples})
    from rack_robotics.carrier_validation import carrier_integrity_checks
    checks = carrier_integrity_checks(travel_samples,startup_samples)
    checks.update(all_waypoints_reached=bool(plan) and len(reached)==len(plan),
                  no_runtime_error=error is None, no_robot_contact_violations=not violations)
    report = {'passed':all(checks.values()),'checks':checks,'error':error,'scope':scope,
              'physics_hz':hz,'simulated_time_s':frame*dt,'waypoints_reached':reached,
              'planned_waypoint_count':len(plan),'contact_violations':violations,
              'limitations':['Finite raster at retracted insertion axis, not continuous volume coverage.',
                 'Unloaded tool; no grasp, occupied-row approach or insertion qualification.',
                 'Physics collision filters are unchanged; separate unfiltered geometry audit is required.',
                 'Carrier poses sampled at 30 Hz; contact reports collected every physics step.']}
    save(output/'results.json',report)
    print('WORKSPACE_RESULT',json.dumps({'passed':report['passed'],'reached':len(reached),
          'planned':len(plan),'error':error}),flush=True)
    app.close()
if not report['passed']: raise SystemExit(1)
