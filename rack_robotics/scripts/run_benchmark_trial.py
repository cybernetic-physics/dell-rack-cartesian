"""Fresh-session full-rack trial of a frozen environment under explicit conditions.

The orchestration/shared task is frozen separately from the saved design's
low-level controllers. This is not claimed to be its original reload test.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--environment',type=Path,required=True)
parser.add_argument('--condition',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--occupied-neighbors',action='store_true',help='Separate crowded-port diagnostic, excluded from randomized reliability')
parser.add_argument('--cycles',type=int,default=1,
                    help='Consecutive nominal cycles in one live scene; >1 is a separate diagnostic, never pooled with randomized trials')
parser.add_argument('--cable-load-threshold-n',type=float,
                    help='Separate destructive constraint-load threshold screen; never pooled with randomized reliability')
parser.add_argument('--cable-force-trace',action='store_true',help='Read-only per-step cable momentum diagnostic; separate nominal control')
parser.add_argument('--cable-force-calibration',type=Path,help='Required passed isolated momentum calibration result for --cable-force-trace')
parser.add_argument('--actuator-control',choices=('nominal','latch_disabled','grasp_open'),
                    help='Separate normal-controller interlock diagnostic; permanent command fault, no observer override')
parser.add_argument('--physical-control',choices=('nominal','unpressed_pull','open_transport','released_hold','released_transport'),
                    help='Separate bounded physical challenge after normal grasp/extraction; never a reliability sample')
args,_=parser.parse_known_args()
root=Path(__file__).resolve().parents[2]
env=args.environment.resolve(); out=args.output.resolve()
config=json.loads((env/'config.json').read_text())
manifest=json.loads((env/'manifest.json').read_text())
for name,digest in manifest['packaged_file_sha256'].items():
    if hashlib.sha256((env/name).read_bytes()).hexdigest()!=digest:
        raise ValueError(f'Saved environment changed: {name}')
baseline=(env/config['baseline']).resolve()
if hashlib.sha256((baseline/'manifest.json').read_bytes()).hexdigest()!=manifest['baseline_manifest_sha256']:
    raise ValueError('Immutable baseline manifest changed')
baseline_manifest=json.loads((baseline/'manifest.json').read_text())
for name,digest in baseline_manifest['files'].items():
    if hashlib.sha256((baseline/name).read_bytes()).hexdigest()!=digest:
        raise ValueError(f'Immutable baseline file changed: {name}')
out.mkdir(parents=True,exist_ok=False)
shutil.copytree(env/'source/rack_robotics',out/'source/rack_robotics',ignore=shutil.ignore_patterns('__pycache__'))
frozen_harness=Path(__file__).resolve().parent/'benchmarking'
shutil.copytree(frozen_harness if frozen_harness.is_dir() else root/'rack_robotics/benchmarking',
                out/'harness/benchmarking',ignore=shutil.ignore_patterns('__pycache__'))
if not frozen_harness.is_dir():
    for source,target in [('controllers/rj45_task.py','task.py'),('controllers/connector_observer.py','observer.py'),
                          ('contacts.py','contacts.py'),('recording.py','recording.py'),('integrity.py','integrity.py'),
                          ('experiment_timing.py','timing.py'),('carrier_validation.py','carrier_validation.py')]:
        shutil.copy2(root/'rack_robotics'/source,out/'harness/benchmarking'/target)
shutil.copy2(__file__,out/'harness/run_benchmark_trial.py')
sys.path.insert(0,str(out/'source')); sys.path.insert(0,str(out/'harness')); sys.path.insert(0,str(baseline))
from benchmarking.spec import validate
from benchmarking.repetition import CycleLedger,validate_request
from benchmarking.cable_load import validate_request as validate_load_request
from benchmarking.timing import ExperimentTiming
from benchmarking.carrier_validation import carrier_integrity_checks,REVISION as CARRIER_GATE_REVISION
timing=ExperimentTiming(round(1/config.get('physics_dt',1/240)))
condition=validate(json.loads(args.condition.read_text()))
validate_request(args.cycles,condition['role'],args.occupied_neighbors)
validate_load_request(args.cable_load_threshold_n,condition['role'],args.cycles,args.occupied_neighbors)
from benchmarking.actuator_controls import validate_request as validate_actuator_request
validate_actuator_request(args.actuator_control,condition['role'],args.cycles,args.occupied_neighbors,
                          args.cable_load_threshold_n,args.cable_force_trace)
from benchmarking.physical_controls import validate_request as validate_physical_request
if args.physical_control in ('released_hold','released_transport'):
    from benchmarking.release_controls import validate_request as validate_physical_request
validate_physical_request(args.physical_control,condition['role'],args.cycles,args.occupied_neighbors,
                          args.cable_load_threshold_n,args.cable_force_trace,args.actuator_control)
if args.physical_control and timing.physics_hz!=480:
    raise ValueError('Physical challenge protocol requires the calibrated480 Hz timestep')
if args.cable_force_trace:
    validate_load_request(1.,condition['role'],args.cycles,args.occupied_neighbors)
    if args.cable_load_threshold_n is not None or not args.cable_force_calibration:
        raise ValueError('Force trace needs its calibration and cannot be combined with destructive break thresholds')
    calibration_bytes=args.cable_force_calibration.read_bytes()
    calibration=json.loads(calibration_bytes)
    balance_hash=hashlib.sha256((out/'harness/benchmarking/cable_balance.py').read_bytes()).hexdigest()
    from benchmarking.cable_force_trace import CableForceTrace,validate_calibration
    validate_calibration(calibration,balance_hash,timing.dt)
    (out/'cable_force_calibration.json').write_bytes(calibration_bytes)
elif args.cable_force_calibration:
    raise ValueError('--cable-force-calibration requires --cable-force-trace')
(out/'condition.json').write_text(json.dumps(condition,indent=2)+'\n')
provenance={str(p.relative_to(out)):hashlib.sha256(p.read_bytes()).hexdigest()
            for folder in ('source','harness') for p in (out/folder).rglob('*.py')}
(out/'source_manifest.json').write_text(json.dumps(provenance,indent=2)+'\n')
metadata={'runner':'benchmark_harness_v3','scope':'full_rack','robot':config['robot'],'gripper':config['gripper'],
    'environment':str(env),'environment_manifest_sha256':hashlib.sha256((env/'manifest.json').read_bytes()).hexdigest(),
    'physics_hz':timing.physics_hz,'physics_dt':timing.dt,'condition':condition,
    'baseline_manifest_sha256':manifest['baseline_manifest_sha256'],
    'controller_scope':'Frozen design low-level controller with separately frozen common task/harness',
    'randomized_reliability_sample':condition['role']=='randomized' and not args.occupied_neighbors,
    'requested_cycles':args.cycles}
if args.cycles>1:
    metadata.update(runner='continuous_cycles_diagnostic_v1',
        comparison_scope='Consecutive nominal cycles without physics reset or fixture re-seating; not independent randomized trials')
if args.occupied_neighbors:
    metadata.update(runner='occupied_neighbors_diagnostic_v1',fixture='occupied_neighbors_v1',
                    comparison_scope='Separate contact-clearance diagnostic; never pooled with sparse-row randomized trials')
if args.cable_load_threshold_n is not None:
    metadata.update(runner='cable_constraint_load_diagnostic_v1',randomized_reliability_sample=False,
                    cable_load_threshold_n=args.cable_load_threshold_n,
                    comparison_scope='Separate resultant constraint-load threshold screen; not axial cable tension or randomized reliability')
if args.cable_force_trace:
    metadata.update(runner='cable_momentum_diagnostic_v1',randomized_reliability_sample=False,
                    cable_force_calibration_sha256=hashlib.sha256(calibration_bytes).hexdigest(),
                    comparison_scope='Separate read-only cable momentum/axial-reaction estimate; not randomized reliability or hardware safety')
if args.actuator_control:
    metadata.update(runner='actuator_interlock_diagnostic_v1',randomized_reliability_sample=False,
                    actuator_control=args.actuator_control,
                    comparison_scope='Separate actuator-disabled interlock diagnostic, not forced withdrawal or randomized reliability')
if args.physical_control:
    from benchmarking.physical_controls import PROTOCOL,PhysicalTrace,task_class as physical_task_class
    if args.physical_control in ('released_hold','released_transport'):
        from benchmarking.release_controls import PROTOCOL,PhysicalTrace,task_class as physical_task_class
    metadata.update(runner='physical_challenge_diagnostic_v1',randomized_reliability_sample=False,
                    physical_control=args.physical_control,physical_protocol=PROTOCOL,
                    comparison_scope='Separate bounded physical challenge; contact impulse/dt is not motor torque or a hardware rating')
(out/'trial_manifest.json').write_text(json.dumps(metadata,indent=2)+'\n')

from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':1280,'height':800})
recorders=[]; contacts=None; trial_started=False; trace=[]; task=None; neighbors=None
cable_load=None
cable_force=None
actuator_trace=None
physical_trace=None
carrier_samples=[]; startup_carrier_samples=[]; has_carriers=False; brakes=None
cycle_ledger=CycleLedger(args.cycles)
report=dict(metadata,passed=False)
try:
    import omni.usd
    from pxr import Usd,UsdGeom,UsdPhysics,PhysxSchema
    from isaacsim.core.api import World
    from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport
    from rack_sim.config import CFG,ROW_PORTS
    from rack_sim.connector import Interaction
    from rack_sim.cable import Cable
    from rack_sim.scene import camera
    from rack_robotics.controllers.cartesian_interface import CartesianRobot
    import rack_robotics.controllers.gripper_interface as tools_module
    from benchmarking.task import RJ45Task
    from benchmarking.observer import ConnectorObserver
    from benchmarking.contacts import ContactRecorder
    from benchmarking.recording import TrajectoryRecorder
    from benchmarking.integrity import audit_trial
    from benchmarking.initialization import apply_conditions
    from benchmarking.adapters import construct,PerturbedRobot,varied_task_class,bind_transmission_step

    architecture=config['robot'][0]; gripper_id=config['gripper'][0]
    stage_file=out/'scene.usda'
    layer=Usd.Stage.CreateNew(str(stage_file))
    layer.GetRootLayer().subLayerPaths=[os.path.relpath(env/config['scene'],out)]
    layer.GetRootLayer().Save(); del layer
    assert omni.usd.get_context().open_stage(str(stage_file))
    for _ in range(30): app.update()
    while omni.usd.get_context().get_stage_loading_status()[2]>0: app.update()
    stage=omni.usd.get_context().get_stage()
    ports=[(f'/World/PortRow/Port{i+1:02d}',p) for i,p in enumerate(ROW_PORTS)]
    port=condition['port']-1; mouth=ROW_PORTS[port]
    # The saved reference scene contains pre-seat actors. They are allowed
    # only during initialization and are all disabled before the timed task.
    for path in ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress'):
        if not stage.GetPrimAtPath(path): raise ValueError(f'Missing pre-seat actor {path}')
        stage.GetPrimAtPath(path).SetActive(True)
    authored=apply_conditions(stage,condition,ports)
    if args.occupied_neighbors:
        from benchmarking.neighbors import OccupiedNeighbors
        neighbors=OccupiedNeighbors(stage,condition['port'],ports,CFG.cable_segments,CFG.cable_segment_length)
        (out/'neighbor_fixture.json').write_text(json.dumps(neighbors.report(),indent=2)+'\n')
    (out/'authored_conditions.json').write_text(json.dumps(authored,indent=2)+'\n')
    initialization=Interaction(stage,mouth,ports)
    names={'z':'Lift','y':'Insertion','latch':'LatchPress'}
    names.update({'x_outer':'OuterExtension','x_inner':'InnerExtension'} if architecture=='B' else {'x':'Traverse'})
    names.update({'left':'LeftJaw','right':'RightJaw'} if gripper_id=='A' else {'servo':'JawServo'})
    drives={}
    for name,joint_name in names.items():
        path='/World/Robot/RG2/Physics/finger_joint' if gripper_id=='B' and name=='servo' else '/World/Robot/Joints/'+joint_name
        prim=stage.GetPrimAtPath(path)
        if not prim or not prim.IsA(UsdPhysics.Joint): raise ValueError(f'Missing saved joint {path}')
        drives[name]=UsdPhysics.DriveAPI(prim,'angular' if name=='servo' else 'linear')
    robot_prim=stage.GetPrimAtPath('/World/Robot')
    has_carriers=bool(stage.GetPrimAtPath('/World/Robot/ServiceCarriers'))
    if has_carriers or robot_prim.GetCustomDataByKey('insertion_revision'):
        from rack_robotics.service_carriers import initialize_cartesian_states
        initial=initialize_cartesian_states(stage,architecture)
        (out/'cartesian_startup_states.json').write_text(json.dumps(initial,indent=2)+'\n')
    if robot_prim.GetCustomDataByKey('brake_revision') and gripper_id=='A':
        from rack_robotics.service_carriers import initialize_prismatic_states
        initial=initialize_prismatic_states(stage,['LeftJaw','RightJaw','LatchPress'])
        (out/'tool_startup_states.json').write_text(json.dumps(initial,indent=2)+'\n')
    if has_carriers:
        from rack_robotics.service_carriers import carrier_metrics
    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath('/World/Physics')).CreateTimeStepsPerSecondAttr(timing.physics_hz)
    contacts=ContactRecorder(stage,timing.dt)
    if args.cable_load_threshold_n is not None:
        from benchmarking.cable_load import CableLoadMonitor
        cable_load=CableLoadMonitor(stage,args.cable_load_threshold_n,CFG.cable_segments)
    stage.GetRootLayer().Save()
    base=construct(CartesianRobot,stage,drives,architecture,gripper_id,control_dt=timing.dt)
    robot=PerturbedRobot(base,condition,architecture)
    gripper=getattr(tools_module,{'A':'ParallelGripper','B':'RG2Gripper','C':'RackJawGripper'}[gripper_id])(stage,drives)
    if args.actuator_control:
        from benchmarking.actuator_controls import ActuatorControl,ActuatorTrace
        gripper=ActuatorControl(gripper,args.actuator_control)
    cable=Cable(stage,[f'/World/Cable/Link{i:02d}' for i in range(CFG.cable_segments)],
                UsdGeom.BasisCurves(stage.GetPrimAtPath('/World/Cable/Jacket')))
    world=World(physics_dt=timing.dt,rendering_dt=1/60,stage_units_in_meters=1,physics_prim_path='/World/Physics')
    world.reset()
    transmission=None
    if architecture=='C':
        from rack_robotics.belt_gantry import CoreXZTransmission
        transmission=CoreXZTransmission(stage,drives)
        step_transmission=bind_transmission_step(transmission,robot)
    if robot_prim.GetCustomDataByKey('brake_revision'):
        from rack_robotics.brake_runtime import BrakeRuntime
        brakes=BrakeRuntime(stage,drives,architecture,transmission)
    report.update(service_carrier_revision=robot_prim.GetCustomDataByKey('service_carrier_revision'),
                  carrier_gate_revision=CARRIER_GATE_REVISION if has_carriers else None,
                  brake_revision=robot_prim.GetCustomDataByKey('brake_revision'),
                  brake_mode='released_while_motors_powered' if brakes else None)
    camera(stage,'handoff',focus=mouth)
    frame=0; observer=initialization
    startup=TrajectoryRecorder(stage,out/'initialization_trajectory.jsonl'); recorders.append(startup)
    startup.sample(0,'physical_initialization')

    def step():
        global frame
        if not trial_started: contacts.time=frame*timing.dt
        if cable_load:
            cable_load.context={'interval':'task' if trial_started else 'initialization',
                                'time_s':contacts.time,'phase':contacts.phase}
        if brakes: brakes.step(timing.dt,release=True,x_force_limit_n=getattr(robot,'transverse_force_limit',None))
        elif transmission: step_transmission()
        if cable_force: cable_force.before()
        if physical_trace: physical_trace.before()
        world.step(render=False)
        if cable_force: cable_force.after(contacts.time,contacts.phase)
        if frame%timing.recording_stride==0:
            world.render()
            if cable_load: cable_load.assert_intact()
            if has_carriers:
                sample=carrier_metrics(stage)
                carrier_samples.append({'time_s':frame*timing.dt,'phase':contacts.phase,**sample})
        observer.update(timing.dt)
        if frame%timing.visual_stride==0:
            cable.update()
            if neighbors: neighbors.refresh_visuals()
            if transmission: transmission.update_visuals()
        if not trial_started and frame%timing.recording_stride==0: startup.sample((frame+1)*timing.dt,'physical_initialization')
        frame+=1

    if gripper_id=='B':
        from rack_robotics.rg2_tool import prepare_rg2_park
        prepare_rg2_park(stage,drives,architecture,robot.park,step,timing.dt)
    # Smooth physical pre-seat with sampled offset and angular target. These
    # temporary drives are never active during robotic manipulation.
    dx,dy,dz=condition['connector_offset_m']
    for k in range(timing.steps(3.)):
        u=min(1.,k/timing.steps(2.)); u=u*u*(3-2*u)
        initialization.set_target((dx*u,.05+(.0002+dy-.05)*u,dz*u),
                                  [a*u for a in condition['connector_angles_deg']])
        step()
    from benchmarking.spec import can_nudge_preseat
    report['physical_initialization_adjustments']=[]
    for attempt in range(2):
        if initialization.connected_port==port: break
        position,_=initialization.pose()
        if not can_nudge_preseat(initialization.metrics,position,mouth): break
        before=dict(initialization.metrics)
        start_y=.0002+dy-attempt*.00015
        target_y=start_y-.00015
        for k in range(timing.steps(1.)):
            u=min(1.,(k+1)/timing.steps(.6)); u=u*u*(3-2*u)
            initialization.set_target((dx,start_y+(target_y-start_y)*u,dz),condition['connector_angles_deg'])
            step()
        report['physical_initialization_adjustments'].append({'kind':'force_limited_preseat_nudge',
            'advance_m':.00015,'target_y_offset_m':target_y,'before':before,'after':dict(initialization.metrics)})
    if initialization.connected_port!=port: raise RuntimeError('Physical pre-seat did not retain the intended port')
    for path in ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress'): stage.GetPrimAtPath(path).SetActive(False)
    observer=ConnectorObserver(stage,ports,previous=initialization)
    # Vary actual starting robot position through its existing joint drives.
    start=tuple(robot.tcp()); destination=tuple(a+b for a,b in zip(robot.park,condition['initial_robot_offset_m']))
    for k in range(timing.steps(1.)):
        if condition['role']!='control':
            u=min(1.,(k+1)/timing.steps(.5)); u=u*u*(3-2*u)
            base.command([a+(b-a)*u for a,b in zip(start,destination)])
        step()
    robot.target=tuple(base.target)
    integrity=audit_trial(stage,ports,CFG.cable_segments)
    (out/'physics_integrity.json').write_text(json.dumps(integrity,indent=2)+'\n')
    if not integrity['passed']: raise RuntimeError(str(integrity['errors']))
    runtime_modules={}
    for name,module in tuple(sys.modules.items()):
        if not name.startswith(('rack_robotics','benchmarking','rack_sim')) or not getattr(module,'__file__',None): continue
        file=Path(module.__file__).resolve()
        expected=out/'source' if name.startswith('rack_robotics') else out/'harness' if name.startswith('benchmarking') else baseline
        if not file.is_relative_to(expected): raise RuntimeError(f'Unexpected live-source import: {name}: {file}')
        runtime_modules[name]={'file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
    report['runtime_modules']=runtime_modules
    report.update(initial_retained_without_hand=observer.connected_port==port,
                  measured_initial_pose={'position':list(observer.pose()[0]),'metrics':dict(observer.metrics)})
    def new_task():
        task_type=physical_task_class(RJ45Task,args.physical_control,drives) if args.physical_control else RJ45Task
        return varied_task_class(task_type)(robot,gripper,observer,port=port,condition=condition)

    def measured_boundary():
        position,orientation=observer.pose()
        return {'plug_position_m':list(position),
                'plug_orientation_wxyz':[orientation.GetReal(),*orientation.GetImaginary()],
                'tcp_m':list(robot.tcp()),'metrics':dict(observer.metrics),
                'retained':bool(observer.connected_port==port and observer.metrics.get('hook_behind_lip')
                                and observer.metrics.get('depth_m',0)>=.0105),
                'initialization_helpers_disabled':all(not stage.GetPrimAtPath(p).IsActive() for p in
                    ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress'))}

    task=new_task()
    startup.close(); recorders.remove(startup)
    startup_carrier_samples=list(carrier_samples); carrier_samples.clear()
    initialization_contacts=contacts.save(out/'initialization_contacts.json')
    if initialization_contacts['reporting_errors']:
        raise RuntimeError('Initialization contact reporting failed')
    contacts.reset()
    cable.max_gap=0.; cable.worst={}
    if neighbors: neighbors.reset_metrics()
    recorder=TrajectoryRecorder(stage,out/'trajectory.jsonl'); recorders.append(recorder)
    if args.cable_force_trace:
        cable_force=CableForceTrace(stage,timing.dt,CFG.cable_segments,out/'cable_force_trace.jsonl.gz')
    if args.actuator_control:
        actuator_trace=ActuatorTrace(out/'actuator_trace.jsonl.gz')
    if args.physical_control:
        physical_trace=PhysicalTrace(out/'physical_trace.jsonl.gz')
    recorder.sample(0,task.phase); trial_started=True
    all_events=[];all_recoveries=[];all_nudges=0
    for cycle_index in range(args.cycles):
        if cycle_index: task=new_task()
        cycle_start=cycle_ledger.elapsed
        if not cycle_ledger.begin(measured_boundary()) and args.cycles>1:
            task.fail('Continuous cycle boundary is not physically latched with initialization helpers disabled')
        while not task.done and task.time<60:
            if args.actuator_control:
                gripper.time=cycle_start+task.time+timing.dt; gripper.phase=task.phase
            task.tick(timing.dt); contacts.phase=task.phase; contacts.time=cycle_start+task.time; step()
            if actuator_trace:
                actuator_trace.sample(contacts.time,task.phase,gripper,observer,robot,stage,drives)
            if physical_trace:
                physical_trace.sample(contacts.time,task,gripper,observer,robot,stage,drives)
            if frame%timing.recording_stride==0:
                recorder.sample(cycle_start+task.time,task.phase)
                p,q=observer.pose()
                trace.append({'time':cycle_start+task.time,'cycle':cycle_index+1,
                    'phase':task.phase,'tcp':robot.tcp(),'target':robot.target,
                    'aperture_m':gripper.aperture(),'plug_position':list(p),
                    'plug_orientation':[q.GetReal(),*q.GetImaginary()],
                    'connector_state':observer.state,'brakes':brakes.latest if brakes else None,**observer.metrics})
        if not task.done: task.fail('Overall per-cycle timeout')
        record=cycle_ledger.finish({'done':task.done,'error':task.error,'duration_s':task.time,
            'unplug_success':task.unplugged,'replug_success':task.replugged,
            'recoveries':task.recoveries,'seating_nudges':task.seating_nudges},measured_boundary())
        for events,target in ((task.events,all_events),(task.recoveries,all_recoveries)):
            target.extend(dict(event,time=cycle_start+event['time'],cycle=cycle_index+1) for event in events)
        all_nudges+=task.seating_nudges
        (out/'cycle_boundaries.json').write_text(json.dumps(cycle_ledger.records,indent=2)+'\n')
        print('CONTINUOUS_CYCLE_RESULT',cycle_index+1,record['passed'],flush=True)
        if not record['passed']: break
    final_integrity=audit_trial(stage,ports,CFG.cable_segments)
    report.update(passed=cycle_ledger.passed and final_integrity['passed'],
        error=task.error or (None if cycle_ledger.passed else 'Continuous cycle boundary gate failed'),
        unplug_success=all(c['unplug_success'] for c in cycle_ledger.records),
        replug_success=all(c['replug_success'] for c in cycle_ledger.records),cycle_time_s=cycle_ledger.elapsed,
        events=task.events if args.cycles==1 else all_events,
        recoveries=task.recoveries if args.cycles==1 else all_recoveries,seating_nudges=all_nudges,
        continuous_cycles=cycle_ledger.records,
        trace=trace,topology_audit=final_integrity,cable_max_gap_m=cable.max_gap,
        cable_gap_scope='Timed robotic trial only; initialization excluded',
        limitations=['Ground-truth pose feedback; no modeled perception.',
                     'Impulse/dt contact estimates are uncalibrated; no cable tensile-force sensor.',
                     'An individual randomized trial is not a reliability estimate.'])
    if args.physical_control and args.physical_control!='nominal':
        report.update(passed=False,full_cycle_attempted=False,
                      error=task.error or 'Diagnostic challenge only; no full replug cycle attempted')
except Exception:
    report.update(passed=False,error=traceback.format_exc(),trace=trace,
                  failure_stage='task_exception' if trial_started else 'initialization_exception')
finally:
    report['timed_trial_started']=trial_started
    if cable_load:
        # Flush pending break events before deciding whether the diagnostic passed.
        try:
            world.pause(); app.update()
            cable_load.assert_intact()
        except Exception:
            report.update(passed=False,error=report.get('error') or traceback.format_exc())
    if args.cycles>1:
        report['continuous_cycles']=cycle_ledger.records
        report['continuous_cycle_scope']='Only task-controller state is renewed; same live world, robot, observer, cable and connector; no between-cycle fixture initialization.'
    if has_carriers:
        if not trial_started:
            startup_carrier_samples=list(carrier_samples); carrier_samples=[]
        carrier_checks=carrier_integrity_checks(carrier_samples,startup_carrier_samples)
        report.update(service_carrier_checks=carrier_checks,carrier_gate_revision=CARRIER_GATE_REVISION,
                      passed=bool(report['passed'] and all(carrier_checks.values())))
        if not all(carrier_checks.values()) and not report.get('error'):
            report['error']='Startup or timed service-carrier integrity gate failed'
        (out/'carrier_metrics.json').write_text(json.dumps({'sample_hz':30,'checks':carrier_checks,
            'startup':startup_carrier_samples,'task':carrier_samples},indent=2)+'\n')
    if 'observer' in globals() and not trial_started:
        # A threshold event may abort the very first physics step, before the
        # initialization observer has ever produced its metrics dictionary.
        report['initialization_final_metrics']=dict(getattr(observer,'metrics',{}))
    for recorder in recorders: recorder.close()
    if contacts:
        contact_report=contacts.save(out/('contacts.json' if trial_started else 'initialization_contacts.json'))
        if args.actuator_control:
            report['actuator_contact_reporting_errors']=contact_report['reporting_errors']
        if contact_report['reporting_errors']:
            report.update(passed=False,error=report.get('error') or 'Contact reporting failed')
        if neighbors:
            report['occupied_neighbors']=neighbors.report(contact_report if trial_started else None,
                metric_interval='timed_robotic_trial' if trial_started else 'initialization_only')
            report['crowded_port_clearance_passed']=bool(report.get('passed') and trial_started
                and report['occupied_neighbors']['fixture_stable']
                and report['occupied_neighbors']['no_reported_robot_neighbor_contact']
                and not contact_report['reporting_errors'])
    if cable_load:
        report['cable_constraint_load']=cable_load.report(report['passed'],timing.recording_stride*timing.dt)
    if cable_force:
        force_report=cable_force.close(report['passed'])
        if force_report['reporting_errors'] or not force_report['sample_count']:
            report.update(passed=False,error=report.get('error') or 'Cable force trace lacks valid samples')
        report['cable_momentum']=force_report
        (out/'cable_force_summary.json').write_text(json.dumps(force_report,indent=2)+'\n')
    if actuator_trace:
        report['actuator_final_phase']=task.phase if task else None
        report['actuator_interlock']=actuator_trace.close(args.actuator_control,gripper.events,report)
    if physical_trace:
        if args.physical_control in ('released_hold','released_transport'):
            report['release_open_targets']=getattr(task,'release_open_targets',None)
        report.update(physical_challenge_reference=getattr(task,'challenge_reference',None),
                      physical_transport_reference=getattr(task,'transport_reference',None),
                      physical_challenge_completed=getattr(task,'challenge_completed',False),
                      physical_contact_reporting_errors=physical_trace.contacts.errors+contact_report['reporting_errors'])
        report['physical_challenge']=physical_trace.close(args.physical_control,report)
    (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    try:
        from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport
        capture=capture_viewport_to_file(get_active_viewport(),str(out/'diagnostic.png'))
        for _ in range(32): app.update()
    except Exception:
        (out/'diagnostic_exception.txt').write_text(traceback.format_exc())
    print('BENCHMARK_RESULT',report['passed'],report.get('error'),flush=True)
    verdict = (report.get('physical_challenge',{}).get('passed',False) if args.physical_control else
               report.get('actuator_interlock',{}).get('passed',False) if args.actuator_control else report['passed'])
    # Kit fast shutdown may terminate inside close(); code after it is not a
    # reliable place to set a failed trial's process status. Supported by the
    # pinned installed SimulationApp; preserve frozen historical runners.
    app.close(exit_code=0 if verdict else 1)
if not verdict:
    raise SystemExit(1)
