"""Isolated physical coupling/negative-control test, NOT an RJ45 trial."""
import argparse,json,shutil,sys,traceback
from pathlib import Path

parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,required=True)
args,_=parser.parse_known_args()
root=Path(__file__).resolve().parents[2]
args.output=args.output.resolve(); args.output.mkdir(parents=True,exist_ok=False)
snapshot=args.output/'source'
for source in (root/'rack_robotics').rglob('*.py'):
    relative=source.relative_to(root)
    if any(p in relative.parts for p in ('assets','research','experiments','environments','__pycache__')): continue
    target=snapshot/relative; target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
sys.path.insert(0,str(snapshot))
sys.path.insert(0,str(root/'rack_robotics/assets/shared_rack/baseline-001'))
from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':640,'height':480})
samples=[]
try:
    import omni.usd
    from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf
    from isaacsim.core.api import World
    from rack_robotics.belt_gantry import build_belt_robot,CoreXZTransmission
    stage=omni.usd.get_context().get_stage()
    UsdGeom.SetStageUpAxis(stage,'Z'); UsdGeom.SetStageMetersPerUnit(stage,1)
    physics=UsdPhysics.Scene.Define(stage,'/World/Physics')
    physics.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1)); physics.CreateGravityMagnitudeAttr(9.81)
    PhysxSchema.PhysxSceneAPI.Apply(physics.GetPrim()).CreateSolverTypeAttr('TGS')
    drives=build_belt_robot(stage,'A')
    stage.GetRootLayer().Export(str(args.output/'scene.usda'))
    world=World(physics_dt=1/240,rendering_dt=1/60,stage_units_in_meters=1,physics_prim_path='/World/Physics')
    world.reset()
    motor=CoreXZTransmission(stage,drives)
    def run(seconds,phase):
        for k in range(round(seconds*240)):
            motor.step(); world.step(render=False)
            if k%8==0:
                q=motor.articulation.get_joint_positions(joint_indices=motor.indices)
                samples.append({'phase':phase,'position':q.tolist(),**motor.latest})
        return motor.articulation.get_joint_positions(joint_indices=motor.indices).tolist()
    initial=run(.5,'hold')
    drives['x'].GetTargetPositionAttr().Set(.10)
    drives['z'].GetTargetPositionAttr().Set(-.05)
    moved=run(2,'diagonal')
    motor.enabled=(False,True)
    failed=run(.15,'motor_a_disabled')
    motor.enabled=(True,True)
    restored=run(2,'restored')
    checks={'independent_axis_gains_zero':all(d.GetStiffnessAttr().Get()==0 and d.GetDampingAttr().Get()==0 for n,d in drives.items() if n in ('x','z')),
            'initial_gravity_hold':max(abs(a-b) for a,b in zip(initial,(.15,0)))<.0005,
            'coupled_motion_tracks':max(abs(a-b) for a,b in zip(moved,(.10,-.05)))<.0005,
            'lost_motor_moves_both_axes':all(abs(a-b)>.0005 for a,b in zip(failed,moved)),
            'restored_motor_recovers':max(abs(a-b) for a,b in zip(restored,(.10,-.05)))<.0005,
            'motor_force_caps':all(abs(f)<=25.000001 for s in samples for f in s['motor_force_n'])}
    report={'passed':all(checks.values()),'scope':'isolated transmission, not rack or connector feasibility',
            'checks':checks,'lift_mass_kg':motor.lift_mass,'initial':initial,'moved':moved,'motor_disabled':failed,'restored':restored,
            'samples':samples,'limitations':['Lumped elastic belt; no tooth/slack/rotor/brake dynamics; uncalibrated motor limits.']}
    (args.output/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    print('COREXZ_PROBE',checks,flush=True)
except Exception:
    error=traceback.format_exc()
    print(error,flush=True)
    # A serialization failure must not also prevent the exception report.
    (args.output/'results.json').write_text(json.dumps({'passed':False,'error':error},indent=2)+'\n')
    raise
finally:
    app.close()
