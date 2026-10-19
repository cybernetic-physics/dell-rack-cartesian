"""Physical empty-jaw transmission test, including disconnected negative control.

This tests the custom tool only, not connector manipulation or rack feasibility.
Every output is new and includes a frozen source copy and initial scene.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import traceback

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args,_=parser.parse_known_args()
root=Path(__file__).resolve().parents[2]
out=args.output.resolve(); out.mkdir(parents=True,exist_ok=False)
snapshot=out/'source'; hashes={}
for source in (root/'rack_robotics').rglob('*.py'):
    rel=source.relative_to(root)
    if any(p in rel.parts for p in ('assets','research','experiments','environments','__pycache__')): continue
    target=snapshot/rel; target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(source,target)
    hashes[str(rel)]=hashlib.sha256(target.read_bytes()).hexdigest()
(out/'source_manifest.json').write_text(json.dumps(hashes,indent=2))
sys.path.insert(0,str(snapshot)); sys.path.insert(0,str(root/'rack_robotics/assets/shared_rack/baseline-001'))
from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':640,'height':480})
try:
    import omni.usd
    from pxr import UsdGeom, UsdPhysics, PhysxSchema, Gf
    from isaacsim.core.api import World
    from rack_robotics.mechanics import ROOT, robot_materials, pose
    from rack_robotics.specialized_tool import build_specialized_tool
    from rack_robotics.controllers.gripper_interface import RackJawGripper
    from rack_robotics.tool_parameters import OPEN_JAW_X, CLOSED_JAW_X, PINION_RADIUS
    stage=omni.usd.get_context().get_stage()
    UsdGeom.SetStageUpAxis(stage,'Z'); UsdGeom.SetStageMetersPerUnit(stage,1)
    drives=build_specialized_tool(stage,{},robot_materials(stage),0)
    fixed=UsdPhysics.FixedJoint.Define(stage,ROOT+'/Joints/ProbeMount')
    fixed.CreateBody1Rel().SetTargets([ROOT+'/ToolMount'])
    fixed.CreateLocalPos0Attr(Gf.Vec3f(0,.68,1.8))
    UsdPhysics.ArticulationRootAPI.Apply(fixed.GetPrim())
    px=PhysxSchema.PhysxArticulationAPI.Apply(fixed.GetPrim())
    px.CreateSolverPositionIterationCountAttr(128); px.CreateSolverVelocityIterationCountAttr(8)
    px.CreateEnabledSelfCollisionsAttr(True)
    scene=UsdPhysics.Scene.Define(stage,'/World/Physics')
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1)); scene.CreateGravityMagnitudeAttr(9.81)
    PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim()).CreateSolverTypeAttr('TGS')
    stage.GetRootLayer().Export(str(out/'scene.usda'))
    world=World(physics_dt=1/240,rendering_dt=1/60,stage_units_in_meters=1,physics_prim_path='/World/Physics')
    world.reset(); tool=RackJawGripper(stage,drives); samples=[]

    def measure(label):
        f=UsdGeom.Xformable(stage.GetPrimAtPath(ROOT+'/ToolFrame')).ComputeLocalToWorldTransform(0)
        p=UsdGeom.Xformable(stage.GetPrimAtPath(ROOT+'/JawPinion')).ComputeLocalToWorldTransform(0)*f.GetInverse()
        axis=p.TransformDir(Gf.Vec3d(1,0,0))
        angle=math.degrees(math.atan2(axis[1],axis[0]))
        right=f.GetInverse().Transform(pose(stage,ROOT+'/RightJaw'))
        return {'phase':label,'angle_deg':angle,'jaw_x_m':right[0],'aperture_m':tool.aperture(),
                'constraint_residual_m':right[0]-OPEN_JAW_X+math.radians(angle)*PINION_RADIUS}

    def settle(label):
        for k in range(360):
            world.step(render=False)
            if k%8==0: world.render(); samples.append(measure(label))
        return measure(label)

    opened=settle('open')
    tool.grasp(True); closed=settle('close_coupled')
    tool.grasp(False); reopened=settle('reopen_coupled')
    UsdPhysics.Joint(stage.GetPrimAtPath(ROOT+'/Joints/JawTransmission')).GetJointEnabledAttr().Set(False)
    tool.grasp(True); disconnected=settle('close_disconnected')
    peak_speed=max(abs(b['angle_deg']-a['angle_deg'])/(8/240) for a,b in zip(samples,samples[1:]))
    speed_limit=PhysxSchema.PhysxJointAPI(drives['servo'].GetPrim()).GetMaxJointVelocityAttr().Get()
    checks={
        'open_position':abs(opened['jaw_x_m']-OPEN_JAW_X)<.0001,
        'coupled_jaw_closes':abs(closed['jaw_x_m']-CLOSED_JAW_X)<.00015,
        'coupled_jaw_reopens':abs(reopened['jaw_x_m']-OPEN_JAW_X)<.0001,
        'six_mm_pitch_radius':max(abs(s['constraint_residual_m']) for s in samples if s['phase']!='close_disconnected')<.0001,
        'disconnected_servo_turns':disconnected['angle_deg']>30,
        'disconnected_jaw_not_driven':abs(disconnected['jaw_x_m']-reopened['jaw_x_m'])<.0002,
        'no_linear_jaw_drive':not stage.GetPrimAtPath(ROOT+'/Joints/MovingJaw').HasAPI(UsdPhysics.DriveAPI,'linear'),
        'servo_speed_limit':peak_speed<speed_limit*1.03,
    }
    report={'passed':all(checks.values()),'scope':'isolated_empty_tool_transmission',
            'checks':checks,'open':opened,'closed':closed,'reopened':reopened,
            'disconnected':disconnected,'trace':samples}
    report['sampled_peak_servo_speed_deg_s']=peak_speed
    report['authored_servo_speed_limit_deg_s']=speed_limit
    (out/'results.json').write_text(json.dumps(report,indent=2))
    print('TOOL_PROBE',checks,flush=True)
except Exception:
    (out/'exception.txt').write_text(traceback.format_exc()); raise
finally:
    app.close()
