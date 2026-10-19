"""Fresh full-rack powered-off holding probe; NOT an RJ45 success trial.

Predeclared gates are development thresholds, not safety certification.
No body positions/velocities are written after reset; robot joint targets
move the mechanism. Inputs, source and failure traces are preserved.
"""
import argparse,hashlib,json,math,os,shutil,sys,traceback
from pathlib import Path


parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--environment',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--physics-hz',type=int,choices=(240,480,960),help='Explicit solver-rate comparison; does not promote the source task configuration')
parser.add_argument('--lift-position',type=float,default=-.28,help='Midstroke test position in metres, with clearance for the unsupported control')
args,_=parser.parse_known_args()
if not -.55<=args.lift_position<=-.15:parser.error('Lift test position must be within [-.55,-.15] m')
root=Path(__file__).resolve().parents[2]
environment=args.environment.resolve(); output=args.output.resolve()
config=json.loads((environment/'config.json').read_text())
manifest=json.loads((environment/'manifest.json').read_text())
for name,digest in manifest['packaged_file_sha256'].items():
    if hashlib.sha256((environment/name).read_bytes()).hexdigest()!=digest:
        raise ValueError('Changed packaged input: '+name)
output.mkdir(parents=True,exist_ok=False)
snapshot=output/'source';hashes={}
for source in (root/'rack_robotics').rglob('*.py'):
    relative=source.relative_to(root)
    if any(p in relative.parts for p in ('assets','research','experiments','environments','__pycache__')):continue
    target=snapshot/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
    hashes[str(relative)]=hashlib.sha256(target.read_bytes()).hexdigest()
(output/'source_manifest.json').write_text(json.dumps(hashes,indent=2)+'\n')
# The baseline is immutable; the new adapter/geometry comes only from this snapshot.
baseline=root/'rack_robotics/assets/shared_rack/baseline-001'
sys.path.insert(0,str(snapshot));sys.path.insert(0,str(baseline))
architecture=config['robot'][0];gripper=config['gripper'][0]
source_hz=config.get('physics_hz',round(1/config.get('physics_dt',1/240)))
hz=args.physics_hz or source_hz
dt=1/hz
gates={'maximum_power_loss_drop_m':.010,'final_half_second_drift_m':.0005,
       'final_lift_speed_m_s':.002,'negative_control_drop_m':.020,
       'carrier_anchor_gap_m':.0015,'carrier_angle_margin_deg':1.}
(output/'manifest.json').write_text(json.dumps({'environment':str(environment),
    'environment_manifest_sha256':hashlib.sha256((environment/'manifest.json').read_bytes()).hexdigest(),
    'physics_hz':hz,'source_task_physics_hz':source_hz,'lift_test_position_m':args.lift_position,
    'architecture':architecture,'gripper':gripper,'gates':gates,
    'scope':'Full-rack robot-only power-loss and brake-release probe; no connector manipulation qualification'},indent=2)+'\n')
from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':1280,'height':800})
recorder=None;stream=None;contacts=None
try:
    import omni.usd
    from pxr import Usd,PhysxSchema
    from isaacsim.core.api import World
    from rack_robotics.mechanics import reference_drives
    from rack_robotics.belt_gantry import CoreXZTransmission
    from rack_robotics.brake_hardware import add_brake_hardware
    from rack_robotics.brake_runtime import BrakeRuntime
    from rack_robotics.service_carriers import carrier_metrics,initialize_prismatic_states
    from rack_robotics.recording import TrajectoryRecorder
    from rack_robotics.contacts import ContactRecorder
    from rack_robotics.carrier_validation import brake_carrier_checks,REVISION as CARRIER_GATE_REVISION
    from rack_sim.scene import camera
    from omni.kit.viewport.utility import capture_viewport_to_file,get_active_viewport
    scene=output/'scene.usda'; layer=Usd.Stage.CreateNew(str(scene))
    layer.GetRootLayer().subLayerPaths=[os.path.relpath(environment/'scene.usda',output)]
    layer.GetRootLayer().Save();del layer
    assert omni.usd.get_context().open_stage(str(scene))
    for _ in range(30):app.update()
    while omni.usd.get_context().get_stage_loading_status()[2]>0:app.update()
    stage=omni.usd.get_context().get_stage()
    existing_brakes=stage.GetPrimAtPath('/World/Robot').GetCustomDataByKey('brake_revision')
    hardware=({'loaded_revision':existing_brakes,'source_environment':str(environment),
               'scope':'Brake geometry/mass already present in the saved scene; no package added twice'}
              if existing_brakes else add_brake_hardware(stage,architecture))
    (output/'brake_hardware.json').write_text(json.dumps(hardware,indent=2)+'\n')
    drives=reference_drives(stage,architecture,gripper)
    if gripper=='A':
        initial=initialize_prismatic_states(stage,['LeftJaw','RightJaw','LatchPress'])
        (output/'tool_startup_states.json').write_text(json.dumps(initial,indent=2)+'\n')
    PhysxSchema.PhysxSceneAPI.Apply(stage.GetPrimAtPath('/World/Physics')).CreateTimeStepsPerSecondAttr(hz)
    stage.GetRootLayer().Save()
    contacts=ContactRecorder(stage,dt)
    world=World(physics_dt=dt,rendering_dt=1/60,stage_units_in_meters=1,physics_prim_path='/World/Physics')
    world.reset()
    transmission=CoreXZTransmission(stage,drives) if architecture=='C' else None
    brake=BrakeRuntime(stage,drives,architecture,transmission)
    camera(stage,'rear')
    recorder=TrajectoryRecorder(stage,output/'trajectory.jsonl')
    stream=(output/'step_trace.jsonl').open('x')
    samples=[];carrier_samples=[];frame=0

    def run(seconds,phase,release=True,move=None):
        global frame
        result=[];steps=round(seconds*hz)
        for k in range(steps):
            if move:move((k+1)/steps)
            contacts.phase=phase;contacts.time=frame*dt
            applied=brake.step(dt,release)
            world.step(render=False)
            q,v=brake.state()
            row={'time_s':(frame+1)*dt,'phase':phase,'phase_time_s':(k+1)*dt,
                 'position_after_m':q,'velocity_after_m_s':v,**applied}
            stream.write(json.dumps(row)+'\n');samples.append(row);result.append(row)
            if frame%(hz//30)==0:
                world.render()
                recorder.sample((frame+1)*dt,phase)
                metric=carrier_metrics(stage)
                if metric:carrier_samples.append({'time_s':(frame+1)*dt,'phase':phase,**metric})
                if transmission:transmission.update_visuals()
            frame+=1
        stream.flush()
        print('BRAKE_PHASE',phase,result[-1]['position_after_m'],flush=True)
        return result

    run(1.,'initial_settle')
    start={n:d.GetTargetPositionAttr().Get() for n,d in drives.items()}
    # Leave clearance below the housing for the deliberately unsupported
    # negative control. The first -.32 m fixture struck a server fan at -.367 m.
    target={'z':args.lift_position}
    if architecture=='B':target.update(x_outer=.15,x_inner=.15)
    else:target['x']=.10
    def move(u):
        u=u*u*(3-2*u)
        for name,value in target.items():drives[name].GetTargetPositionAttr().Set(start[name]+(value-start[name])*u)
    run(3.,'move_to_midstroke',move=move)
    settled=run(2.,'powered_hold')
    origin=settled[-1]['position_after_m']
    brake.power(False)
    held=run(2.,'motor_power_off_brakes_engage',release=False)
    off_end=held[-1]['position_after_m']
    released=run(.14,'negative_control_brakes_release',release=True)
    recovery_targets={n:d.GetTargetPositionAttr().Get() for n,d in drives.items()}
    recovery_start={}
    for name,drive in drives.items():
        index=brake.articulation.get_dof_index(drive.GetPrim().GetName())
        value=float(brake.articulation.get_joint_positions(joint_indices=brake.np.array([index]))[0])
        recovery_start[name]=value
        drive.GetTargetPositionAttr().Set(value)
    brake.power(True)
    run(.25,'recovery_velocity_arrest',release=True)
    def recover(u):
        u=u*u*(3-2*u)
        for name,value in recovery_targets.items():
            drives[name].GetTargetPositionAttr().Set(recovery_start[name]+(value-recovery_start[name])*u)
    run(2.,'powered_recovery_ramp',release=True,move=recover)
    recovered=run(1.,'powered_recovery_hold',release=True)
    recorder.close();recorder=None;stream.close();stream=None
    contacts_report=contacts.save(output/'contacts.json')
    (output/'carrier_metrics.json').write_text(json.dumps(carrier_samples,indent=2)+'\n')
    z=brake.bank.joints.index('Lift')
    drop=max(origin[z]-s['position_after_m'][z] for s in held)
    tail=[s['position_after_m'][z] for s in held[-round(hz*.5):]]
    free_drop=off_end[z]-released[-1]['position_after_m'][z]
    delayed=[s for s in held if s['phase_time_s']<.030-1e-12]
    fully_released=[s for s in released if s['phase_time_s']>=.050+dt]
    off=held+released
    checks={
        'powered_midstroke_reached':abs(origin[z]-target['z'])<.002,
        'all_robot_drive_gains_zero_when_off':all(all(k==0 and d==0 for k,d in s['drive_gains'].values()) for s in off),
        'external_motor_efforts_zero_when_off':all(all(f==0 for f in s['external_motor_effort_n']) for s in off),
        'engagement_delay_observed':bool(delayed) and all(not m['engaged'] for s in delayed for m in s['brakes']['motors']),
        'engaged_after_delay':all(m['engaged'] for m in held[-1]['brakes']['motors']),
        'motor_brake_torque_caps':all(abs(m['torque_nm'])<=.40000001 for s in samples for m in s['brakes']['motors']),
        'power_loss_drop_below_10mm':drop<gates['maximum_power_loss_drop_m'],
        'final_hold_drift_below_half_mm':max(tail)-min(tail)<gates['final_half_second_drift_m'],
        'final_lift_speed_below_2mm_s':abs(held[-1]['velocity_after_m_s'][z])<gates['final_lift_speed_m_s'],
        'released_brakes_apply_no_force':bool(fully_released) and all(m['torque_nm']==0 and not m['engaged'] for s in fully_released for m in s['brakes']['motors']),
        'negative_control_falls_over_20mm':free_drop>gates['negative_control_drop_m'],
        'powered_recovery':max(abs(a-b) for a,b in zip(recovered[-1]['position_after_m'],origin))<.003,
        'finite_joint_states':all(math.isfinite(v) for s in samples for v in s['position_after_m']+s['velocity_after_m_s']),
        'contact_reporting_ok':not contacts_report['reporting_errors'],
        'no_robot_collision_impulses_above_0p1N':not any(p['peak_pair_contact_force_n']>.1
            and any('/Robot/' in c for c in p['colliders']) for p in contacts_report['pairs'])}
    checks.update({'carrier_'+name:value for name,value in brake_carrier_checks(carrier_samples).items()})
    import omni.timeline
    omni.timeline.get_timeline_interface().pause()
    capture=capture_viewport_to_file(get_active_viewport(),str(output/'diagnostic.png'))
    for _ in range(30):app.update()
    report={'passed':all(checks.values()),'checks':checks,'maximum_drop_m':drop,
        'final_hold_drift_m':max(tail)-min(tail),'negative_control_drop_m':free_drop,
        'physics_hz':hz,'robot':architecture,'gripper':gripper,'scope':'powered_off_hold_probe_not_RJ45_trial',
        'carrier_gate_revision':CARRIER_GATE_REVISION,
        'limitations':['Static vendor torque used as dynamic friction cap; uncalibrated stiffness/damping and no stopping rating.',
            'No rotor inertia, thermal, wear, electrical fault circuit or manufacturing validation.',
            'Midstroke unloaded tool only; not all payloads, stroke locations or timestep convergence.',
            'Original baseline hand fixture may retain its plug; only ROBOT motor power is disabled.']}
    (output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('BRAKE_PROBE',json.dumps(report),flush=True)
except Exception:
    error=traceback.format_exc();print(error,flush=True)
    (output/'results.json').write_text(json.dumps({'passed':False,'error':error},indent=2)+'\n')
    raise
finally:
    if recorder:recorder.close()
    if stream:stream.close()
    if contacts and not (output/'contacts.json').exists():contacts.save(output/'contacts.json')
    app.close()
