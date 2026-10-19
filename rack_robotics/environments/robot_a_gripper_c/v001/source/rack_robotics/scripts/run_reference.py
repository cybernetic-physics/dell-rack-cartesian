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
parser.add_argument('--robot',choices=['A','B'],default='A')
parser.add_argument('--gripper',choices=['A','C'],default='A')
args,_=parser.parse_known_args()
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
    from rack_robotics.controllers.cartesian_interface import CartesianRobot
    from rack_robotics.controllers.gripper_interface import ParallelGripper, RackJawGripper
    from rack_robotics.controllers.connector_observer import ConnectorObserver
    from rack_robotics.controllers.rj45_task import RJ45Task
    from rack_robotics.recording import TrajectoryRecorder
    from rack_robotics.integrity import audit_trial
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
    drives=(reference_drives(stage,args.robot,args.gripper) if args.scene else
            build_telescoping_robot(stage,args.gripper) if args.robot=='B' else build_reference_robot(stage,args.gripper))
    stage.GetRootLayer().Save()
    robot=CartesianRobot(stage,drives,args.robot,args.gripper)
    gripper=(RackJawGripper if args.gripper=='C' else ParallelGripper)(stage,drives)
    if args.fault!='none':
        from rack_robotics.faults import SingleActuatorFault
        gripper=SingleActuatorFault(gripper,args.fault)
    from rack_robotics.contacts import ContactRecorder
    contacts=ContactRecorder(stage,CFG.physics_dt)
    world=World(physics_dt=CFG.physics_dt,rendering_dt=1/60,
                stage_units_in_meters=1,physics_prim_path='/World/Physics')
    world.reset()
    camera(stage,'handoff',focus=ROW_PORTS[0])
    frame=0; trace=[]; observer=initialization

    def step():
        global frame
        world.step(render=False)
        if frame%8==0: world.render()
        observer.update(CFG.physics_dt)
        if frame%4==0: cable.update()
        frame+=1

    # Physical pre-seating outside the timed robotic trial; no pose assignment.
    for k in range(720):
        u=min(1.,k/480); u=u*u*(3-2*u)
        initialization.set_target((0,.05+(.0002-.05)*u,0))
        step()
    if initialization.connected_port!=0:
        raise RuntimeError('Initialization could not physically seat the connector')
    # Author inactive opinions over baseline's demo actuators; no connector,
    # cable, latch or socket collision prim is disabled or removed.
    for path in ('/World/HandDrive','/World/ClipPressSlide','/World/ClipPress'):
        stage.GetPrimAtPath(path).SetActive(False)
    observer=ConnectorObserver(stage,ports,previous=initialization)
    for _ in range(240): step()
    integrity=audit_trial(stage,ports,CFG.cable_segments)
    (args.output/'physics_integrity.json').write_text(json.dumps(integrity,indent=2)+'\n')
    if not integrity['passed']: raise RuntimeError(f'Physics integrity failed: {integrity["errors"]}')
    task=RJ45Task(robot,gripper,observer)
    contacts.reset()
    recorder=TrajectoryRecorder(stage,args.output/'trajectory.jsonl')
    recorder.sample(0,task.phase)
    initial_retained=observer.connected_port==0
    started=time.monotonic()
    while not task.done and task.time<60:
        if args.fault!='none': gripper.time=task.time
        task.tick(CFG.physics_dt)
        contacts.phase=task.phase; contacts.time=task.time
        step()
        if frame%8==0:
            recorder.sample(task.time,task.phase)
            p,q=observer.pose()
            trace.append({'time':task.time,'phase':task.phase,'tcp':robot.tcp(),
                          'target':robot.target,'aperture_m':gripper.aperture(),
                          'plug_position':list(p),'plug_orientation':[q.GetReal(),*q.GetImaginary()],
                          'connector_state':observer.state,**observer.metrics})
    if not task.done: task.fail('Overall timeout')
    recorder.close()
    contacts.save(args.output/'contacts.json')
    capture=capture_viewport_to_file(get_active_viewport(),str(args.output/'diagnostic.png'))
    for _ in range(32): step()
    report={'passed':task.done and not task.error,'scope':'isolated_contacts' if args.minimal else 'full_rack',
            'robot':'B_side_telescoping' if args.robot=='B' else 'A_dual_supported_screw',
            'gripper':'C_rj45_specific' if args.gripper=='C' else 'A_precision_parallel','error':task.error,
            'loaded_scene':str(args.scene.resolve()) if args.scene else None,
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
    (args.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    stage.GetRootLayer().Export(str(args.output/'final_state.usda'))
    print('REFERENCE_RESULT',report['passed'],report['error'],flush=True)
except Exception:
    error=traceback.format_exc()
    if recorder is not None: recorder.close()
    if contacts is not None: contacts.save(args.output/'contacts.json')
    (args.output/'exception.txt').write_text(error)
    (args.output/'results.json').write_text(json.dumps({
        'passed':False,'scope':'isolated_contacts' if args.minimal else 'full_rack',
        'robot':'B_side_telescoping' if args.robot=='B' else 'A_dual_supported_screw',
        'gripper':'C_rj45_specific' if args.gripper=='C' else 'A_precision_parallel',
        'loaded_scene':str(args.scene.resolve()) if args.scene else None,
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
