"""Run one preserved reference feasibility experiment in a fresh Isaac session.

--minimal omits the surrounding rack for isolated contact debugging and MUST NOT
be counted as a rack-integration pass. Default loads the immutable full rack.
"""
import argparse
import json
import os
import hashlib
import shutil
import traceback
from pathlib import Path
import sys
import time

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--minimal',action='store_true')
parser.add_argument('--scene',type=Path,help='Reuse a saved robot/rack assembly instead of rebuilding it')
parser.add_argument('--baseline',type=Path,help='Explicit immutable rack code/dependency baseline')
parser.add_argument('--fault',choices=['none','grasp_once','latch_once'],default='none')
parser.add_argument('--robot',choices=['A','B','C'],default='A')
parser.add_argument('--gripper',choices=['A','B','C'],default='A')
parser.add_argument('--physics-hz',type=int,choices=[240,480],default=240)
parser.add_argument('--hardware-detail',action='store_true',help='New drive-connections revision, with collision geometry and additive hardware mass')
parser.add_argument('--service-carriers',action='store_true',help='Add passive, attached dynamic service carriers to a drive-connected assembly before physics')
parser.add_argument('--motor-brakes',action='store_true',help='Add dimensioned motor brakes before physics; released during powered manipulation')
args,_=parser.parse_known_args()
robot_names={'A':'A_dual_supported_screw','B':'B_side_telescoping','C':'C_corexz_belt'}
gripper_names={'A':'A_precision_parallel','B':'B_rg2_linkage','C':'C_rj45_specific'}
root=Path(__file__).resolve().parents[2]
baseline=(args.baseline or root/'rack_robotics/assets/shared_rack/baseline-001').resolve()
if args.scene and args.minimal: parser.error('--scene and --minimal are mutually exclusive')
args.output=args.output.resolve(); args.output.mkdir(parents=True,exist_ok=False)
# Import the preserved source, not a working copy that may change during a run.
snapshot=args.output/'source'
hashes={}
for source in (root/'rack_robotics').rglob('*.py'):
    relative=source.relative_to(root)
    if any(p in relative.parts for p in ('assets','research','experiments','environments','__pycache__')):
        continue
    target=snapshot/relative; target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    hashes[str(relative)]=hashlib.sha256(target.read_bytes()).hexdigest()
(args.output/'source_manifest.json').write_text(json.dumps(hashes,indent=2)+'\n')
sys.path.insert(0,str(snapshot)); sys.path.insert(0,str(baseline))

from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':1280,'height':800})
recorder=None
startup_recorder=None
contacts=None
try:
    import omni.usd
    from pxr import Usd, UsdGeom, UsdPhysics, PhysxSchema, Gf
    from isaacsim.core.api import World
    from rack_sim.config import CFG, ROW_PORTS
    from rack_sim.connector import Interaction, create_plug, create_socket
    from rack_sim.cable import Cable, create_cable
    from rack_sim.geometry import xform, material
    from rack_sim.scene import camera
    from rack_robotics.mechanics import build_reference_robot, reference_drives
    from rack_robotics.architectures import build_telescoping_robot
    from rack_robotics.belt_gantry import build_belt_robot, CoreXZTransmission
    from rack_robotics.controllers.cartesian_interface import CartesianRobot
    from rack_robotics.controllers.gripper_interface import ParallelGripper, RackJawGripper, RG2Gripper
    from rack_robotics.controllers.connector_observer import ConnectorObserver
    from rack_robotics.controllers.rj45_task import RJ45Task
    from rack_robotics.recording import TrajectoryRecorder
    from rack_robotics.integrity import audit_trial
    from rack_robotics.experiment_timing import ExperimentTiming
    timing=ExperimentTiming(args.physics_hz)
    from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport

    scene_file=args.output/'scene.usda'
    new=Usd.Stage.CreateNew(str(scene_file))
    if args.scene:
        new.GetRootLayer().subLayerPaths=[os.path.relpath(args.scene.resolve(),args.output)]
    elif not args.minimal:
        new.GetRootLayer().subLayerPaths=[os.path.relpath(baseline/'assets/latch-row/dell_rack.usda',args.output)]
    new.GetRootLayer().Save()
    del new
    assert omni.usd.get_context().open_stage(str(scene_file))
    # Finish Kit's stage-open hooks before authoring physics. They can otherwise
    # mutate the same layer concurrently with this standalone script.
    for _ in range(30): app.update()
    while omni.usd.get_context().get_stage_loading_status()[2]>0: app.update()
    stage=omni.usd.get_context().get_stage()
    ports=[(f'/World/PortRow/Port{i+1:02d}',p) for i,p in enumerate(ROW_PORTS)]
    if args.minimal:
        UsdGeom.SetStageUpAxis(stage,'Z'); UsdGeom.SetStageMetersPerUnit(stage,1)
        xform(stage,'/World'); stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
        specs={'steel':(.5,.5,.5),'dark':(.08,.08,.08),'gold':(.8,.5,.1),
               'green':(0,1,0),'plug':(.5,.6,.7),'blue':(0,.1,.6),'orange':(1,.3,0)}
        mats={name:material(stage,name,color) for name,color in specs.items()}
        physics=UsdPhysics.Scene.Define(stage,'/World/Physics')
        physics.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1)); physics.CreateGravityMagnitudeAttr(9.81)
        px=PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim())
        px.CreateSolverTypeAttr('TGS'); px.CreateEnableCCDAttr(True); px.CreateEnableGPUDynamicsAttr(False)
        ports=ports[:1]
        create_socket(stage,ROW_PORTS[0],mats,ports[0][0])
        pos=(ROW_PORTS[0][0],ROW_PORTS[0][1]+.05,ROW_PORTS[0][2])
        create_plug(stage,pos,mats)
        cable=create_cable(stage,pos,mats['blue'])
        from pxr import UsdLux
        UsdLux.DomeLight.Define(stage,'/World/Light').CreateIntensityAttr(1500)
    else:
        cable=Cable(stage,[f'/World/Cable/Link{i:02d}' for i in range(CFG.cable_segments)],
                    UsdGeom.BasisCurves(stage.GetPrimAtPath('/World/Cable/Jacket')))
    initialization=Interaction(stage,ROW_PORTS[0],ports)
    gripper_asset=None
    if args.gripper=='B' and not args.scene:
        vendor=root/'rack_robotics/research/sources/onrobot-isaacsim'
        shutil.copytree(vendor/'assets/rg2',args.output/'assets/rg2')
        shutil.copy2(vendor/'LICENSE',args.output/'assets/LICENSE-OnRobot')
        gripper_asset=args.output/'assets/rg2/onrobot_rg2.usda'
    if args.gripper=='B':
        PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath('/World/Physics')).CreateEnableExternalForcesEveryIterationAttr().Set(True)
    drives=(reference_drives(stage,args.robot,args.gripper) if args.scene else
            build_belt_robot(stage,args.gripper,gripper_asset) if args.robot=='C' else
            build_telescoping_robot(stage,args.gripper,gripper_asset) if args.robot=='B' else build_reference_robot(stage,args.gripper,gripper_asset))
    if args.hardware_detail:
        from rack_robotics.hardware_detail import complete_drive_connections
        hardware=complete_drive_connections(stage,args.robot)
        (args.output/'hardware_detail.json').write_text(json.dumps(hardware,indent=2)+'\n')
    from rack_robotics.service_carriers import complete_service_carriers, carrier_metrics, initialize_cartesian_states
    if args.service_carriers:
        initial_states=initialize_cartesian_states(stage,args.robot)
        carriers=complete_service_carriers(stage,args.robot)
        carriers['startup_cartesian_states']=initial_states
        carriers['authored_metrics']=carrier_metrics(stage)
        (args.output/'service_carriers.json').write_text(json.dumps(carriers,indent=2)+'\n')
    if args.motor_brakes:
        from rack_robotics.brake_hardware import add_brake_hardware
        brake_hardware=add_brake_hardware(stage,args.robot)
        (args.output/'brake_hardware.json').write_text(json.dumps(brake_hardware,indent=2)+'\n')
    if stage.GetPrimAtPath('/World/Robot').GetCustomDataByKey('brake_revision') and args.gripper=='A':
        from rack_robotics.service_carriers import initialize_prismatic_states
        initial=initialize_prismatic_states(stage,['LeftJaw','RightJaw','LatchPress'])
        (args.output/'tool_startup_states.json').write_text(json.dumps(initial,indent=2)+'\n')
    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath('/World/Physics')).CreateTimeStepsPerSecondAttr(args.physics_hz)
    stage.GetRootLayer().Save()
    robot=CartesianRobot(stage,drives,args.robot,args.gripper,control_dt=timing.dt)
    gripper={'A':ParallelGripper,'B':RG2Gripper,'C':RackJawGripper}[args.gripper](stage,drives)
    if args.fault!='none':
        from rack_robotics.faults import SingleActuatorFault
        gripper=SingleActuatorFault(gripper,args.fault)
    from rack_robotics.contacts import ContactRecorder
    contacts=ContactRecorder(stage,timing.dt)
    world=World(physics_dt=timing.dt,rendering_dt=1/60,
                stage_units_in_meters=1,physics_prim_path='/World/Physics')
    world.reset()
    transmission=CoreXZTransmission(stage,drives) if args.robot=='C' else None
    brakes=None
    if stage.GetPrimAtPath('/World/Robot').GetCustomDataByKey('brake_revision'):
        from rack_robotics.brake_runtime import BrakeRuntime
        brakes=BrakeRuntime(stage,drives,args.robot,transmission)
    camera(stage,'handoff',focus=ROW_PORTS[0])
    frame=0; trace=[]; observer=initialization; carrier_samples=[]
    if args.gripper=='B' or stage.GetPrimAtPath('/World/Robot/ServiceCarriers'):
        startup_recorder=TrajectoryRecorder(stage,args.output/'initialization_trajectory.jsonl')
        startup_recorder.sample(0,'physical_preseat_and_tool_settle')

    def step():
        global frame
        if startup_recorder is not None: contacts.time=frame*timing.dt
        if brakes: brakes.step(timing.dt,release=True,x_force_limit_n=robot.transverse_force_limit)
        elif transmission: transmission.step(x_force_limit_n=robot.transverse_force_limit)
        world.step(render=False)
        if frame%timing.recording_stride==0:
            world.render()
            metrics=carrier_metrics(stage)
            if metrics is not None: carrier_samples.append({'time_s':frame*timing.dt,'phase':contacts.phase,**metrics})
        observer.update(timing.dt)
        if frame%timing.visual_stride==0:
            cable.update()
            if transmission: transmission.update_visuals()
        if startup_recorder is not None and frame%timing.recording_stride==0:
            startup_recorder.sample((frame+1)*timing.dt,'physical_preseat_and_tool_settle')
        frame+=1

    if args.gripper=='B':
        from rack_robotics.rg2_tool import prepare_rg2_park
        prepare_rg2_park(stage,drives,args.robot,robot.park,step,timing.dt)
    # Physical pre-seating outside the timed robotic trial; no pose assignment.
    for k in range(timing.steps(3.)):
        u=min(1.,k/timing.steps(2.)); u=u*u*(3-2*u)
        initialization.set_target((0,.05+(.0002-.05)*u,0))
        step()
    if initialization.connected_port!=0:
        raise RuntimeError('Initialization could not physically seat the connector')
    # Author inactive opinions over baseline's demo actuators; no connector,
    # cable, latch or socket collision prim is disabled or removed.
    for path in ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress'):
        stage.GetPrimAtPath(path).SetActive(False)
    observer=ConnectorObserver(stage,ports,previous=initialization)
    for _ in range(timing.steps(1.)): step()
    integrity=audit_trial(stage,ports,CFG.cable_segments)
    (args.output/'physics_integrity.json').write_text(json.dumps(integrity,indent=2)+'\n')
    if not integrity['passed']: raise RuntimeError(f'Physics integrity failed: {integrity["errors"]}')
    task=RJ45Task(robot,gripper,observer)
    if startup_recorder is not None:
        startup_recorder.close(); startup_recorder=None
    contacts.save(args.output/'initialization_contacts.json')
    contacts.reset()
    if carrier_samples:
        (args.output/'initialization_carriers.json').write_text(json.dumps(carrier_samples,indent=2)+'\n')
        carrier_samples=[]
    recorder=TrajectoryRecorder(stage,args.output/'trajectory.jsonl')
    recorder.sample(0,task.phase)
    initial_retained=observer.connected_port==0
    started=time.monotonic()
    while not task.done and task.time<60:
        if args.fault!='none': gripper.time=task.time
        task.tick(timing.dt)
        contacts.phase=task.phase; contacts.time=task.time
        step()
        if frame%timing.recording_stride==0:
            recorder.sample(task.time,task.phase)
            p,q=observer.pose()
            trace.append({'time':task.time,'phase':task.phase,'tcp':robot.tcp(),
                          'target':robot.target,'aperture_m':gripper.aperture(),
                          'compliance_offset_m':robot.deflection_filter.offset,
                          'drive_targets':{n:d.GetTargetPositionAttr().Get() for n,d in drives.items()},
                          'drive_force_limits':{n:d.GetMaxForceAttr().Get() for n,d in drives.items()},
                          'transmission':transmission.latest if transmission else None,
                          'brakes':brakes.latest if brakes else None,
                          'plug_position':list(p),'plug_orientation':[q.GetReal(),*q.GetImaginary()],
                          'connector_state':observer.state,**observer.metrics})
    if not task.done: task.fail('Overall timeout')
    recorder.close()
    contacts.save(args.output/'contacts.json')
    capture=capture_viewport_to_file(get_active_viewport(),str(args.output/'diagnostic.png'))
    for _ in range(timing.steps(32/240)): step()
    has_carriers=bool(stage.GetPrimAtPath('/World/Robot/ServiceCarriers'))
    carrier_checks=({'samples_present':bool(carrier_samples),
        'finite_state':all(not s['errors'] for s in carrier_samples),
        'sampled_anchor_gap_below_1p5mm':all(s['maximum_anchor_gap_m']<.0015 for s in carrier_samples),
        'sampled_hinge_limits_within_one_degree':all(-1<s['minimum_hinge_deg'] and s['maximum_hinge_deg']<31 for s in carrier_samples)} if has_carriers else {})
    if has_carriers:
        (args.output/'carrier_metrics.json').write_text(json.dumps({'sample_hz':30,'checks':carrier_checks,'samples':carrier_samples},indent=2)+'\n')
    report={'passed':bool(task.done and not task.error and all(carrier_checks.values())),
            'manipulation_passed':bool(task.done and not task.error),
            'service_carrier_checks':carrier_checks,
            'service_carrier_revision':stage.GetPrimAtPath('/World/Robot').GetCustomDataByKey('service_carrier_revision'),
            'scope':'isolated_contacts' if args.minimal else 'full_rack',
            'robot':robot_names[args.robot],
            'gripper':gripper_names[args.gripper],
            'error':task.error or ('Service carrier integrity gate failed: '+', '.join(k for k,v in carrier_checks.items() if not v) if not all(carrier_checks.values()) else None),
            'hardware_revision':stage.GetPrimAtPath('/World/Robot').GetCustomDataByKey('hardware_revision'),
            'brake_revision':stage.GetPrimAtPath('/World/Robot').GetCustomDataByKey('brake_revision'),
            'brake_mode':'released_while_motors_powered' if brakes else None,
            'loaded_scene':str(args.scene.resolve()) if args.scene else None,
            'physics_dt':timing.dt,'physics_hz':timing.physics_hz,'recording_fps':30,
            'lift_gravity_bias_m':robot.lift_gravity_bias,
            'initial_retained_without_hand':initial_retained,'unplug_success':task.unplugged,
            'replug_success':task.replugged,'cycle_time_s':task.time,'wall_time_s':time.monotonic()-started,
            'events':task.events,'trace':trace,'cable_max_gap_m':cable.max_gap,
            'recoveries':task.recoveries,
            'seating_nudges':task.seating_nudges,
            'fault_injection':{'mode':args.fault,'events':getattr(gripper,'events',[])},
            'topology_audit':integrity,
            'physics_integrity':{p:not stage.GetPrimAtPath(p).IsActive() for p in
                                 ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress')},
            'limitations':['Development prototype, not a calibrated commercial digital twin.',
                            'Controller uses simulator pose feedback, not modeled perception.',
                            'No randomized reliability or complete rack collision audit yet.',
                            'Bounded recovery implemented; randomized physical fault-injection validation pending.']}
    if args.gripper=='B':
        from rack_robotics.rg2_parameters import COMMAND_RATE_DEG_S, MOTOR_TORQUE_CAP_NM
        report['gripper_control']={'command_rate_deg_s':COMMAND_RATE_DEG_S,
            'motor_torque_cap_nm':MOTOR_TORQUE_CAP_NM,'grasp_duration_s':gripper.grasp_duration,
            'release_duration_s':gripper.release_duration}
        report['limitations'] += [
            'Full-size vendor RG2 with numerical mimic/drive assumptions, not calibrated motor or pad-force behavior.',
            'Vendor internal-link filtered pairs preserved; custom shoes remain collision-enabled.',
            'Rigid custom offset shoes; attachment stiffness, fasteners and strength remain unvalidated.',
            'Solver-rate sensitivity is a separate paired comparison; this trial alone does not establish convergence.']
    (args.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    stage.GetRootLayer().Export(str(args.output/'final_state.usda'))
    print('REFERENCE_RESULT',report['passed'],report['error'],flush=True)
except Exception:
    error=traceback.format_exc()
    if startup_recorder is not None: startup_recorder.close()
    if recorder is not None: recorder.close()
    if contacts is not None: contacts.save(args.output/'contacts.json')
    if 'trace' in globals():
        (args.output/'partial_trace.json').write_text(json.dumps(trace,indent=2)+'\n')
    (args.output/'exception.txt').write_text(error)
    (args.output/'results.json').write_text(json.dumps({
        'passed':False,'scope':'isolated_contacts' if args.minimal else 'full_rack',
        'robot':robot_names[args.robot],
        'gripper':gripper_names[args.gripper],
        'loaded_scene':str(args.scene.resolve()) if args.scene else None,
        'physics_dt':1/args.physics_hz,'physics_hz':args.physics_hz,
        'error':error,'failure_stage':'runner_exception',
        'limitations':['Runner exception; no successful task outcome is claimed.']},indent=2)+'\n')
    try:
        capture=capture_viewport_to_file(get_active_viewport(),str(args.output/'diagnostic.png'))
        for _ in range(32): app.update()
    except Exception:
        (args.output/'diagnostic_exception.txt').write_text(traceback.format_exc())
    raise
finally:
    app.close()
