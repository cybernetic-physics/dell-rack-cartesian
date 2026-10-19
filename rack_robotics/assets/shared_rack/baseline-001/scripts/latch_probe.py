"""Small Isaac scene for mechanical latch regressions, without rack asset loading."""
import argparse,json,sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
parser=argparse.ArgumentParser()
parser.add_argument('--output',default='/workspace/artifacts/latch-probe.json')
args,_=parser.parse_known_args()
from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':640,'height':480})
import omni.usd
from isaacsim.core.api import World
from pxr import UsdGeom,UsdPhysics,PhysxSchema,Gf
from rack_sim.geometry import xform,material
from rack_sim.connector import create_socket,create_plug,Interaction
from rack_sim.config import CFG
from rack_sim.latch import REST_DEG

stage=omni.usd.get_context().get_stage()
UsdGeom.SetStageUpAxis(stage,'Z'); UsdGeom.SetStageMetersPerUnit(stage,1)
xform(stage,'/World'); stage.SetDefaultPrim(stage.GetPrimAtPath('/World'))
mats={name:material(stage,name,color) for name,color in {
    'steel':(.5,.5,.5),'dark':(.1,.1,.1),'gold':(.8,.5,.1),'green':(0,1,0),
    'plug':(.6,.7,.8),'blue':(0,.1,.8),'orange':(1,.3,0)}.items()}
scene=UsdPhysics.Scene.Define(stage,'/World/Physics')
scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1)); scene.CreateGravityMagnitudeAttr(9.81)
px=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim())
px.CreateSolverTypeAttr('TGS'); px.CreateEnableCCDAttr(True); px.CreateEnableGPUDynamicsAttr(False)
mouth=(0,0,1)
create_socket(stage,mouth,mats); create_plug(stage,(0,.05,1),mats)
interaction=Interaction(stage,mouth)
world=World(physics_dt=CFG.physics_dt,rendering_dt=1/60,stage_units_in_meters=1,physics_prim_path='/World/Physics')
world.reset()
trace=[]; checks=[]; phase='settle'; ticks=0
def check(name,ok,**data):
    checks.append({'name':name,'passed':bool(ok),**data})
    print('CHECK',checks[-1],flush=True)
def step(n):
    global ticks
    for _ in range(n):
        world.step(render=False)
        if ticks%4==0: world.render()
        interaction.update(CFG.physics_dt)
        if ticks%4==0: trace.append({'phase':phase,'time':interaction.time,'state':interaction.state,**interaction.metrics})
        ticks+=1
def move(target,seconds=1):
    start=list(interaction.target); count=int(seconds/CFG.physics_dt)
    for i in range(count):
        a=(i+1)/count; a=a*a*(3-2*a)
        interaction.set_target([s+(t-s)*a for s,t in zip(start,target)]); step(1)
def snapshot(label):
    print('POSE',label,interaction.state,interaction.metrics,flush=True)
try:
    step(240)
    check('no_socket_retention_joint',not stage.GetPrimAtPath('/World/Retention'))
    rest=interaction.metrics['latch_angle_deg']; snapshot('free')
    phase='free_press'; interaction.release(True)
    step(240); depressed=interaction.metrics['latch_angle_deg']; snapshot('depressed')
    check('physical_pad_deflects_latch',depressed<rest-4,rest_deg=rest,pressed_deg=depressed)
    phase='spring_return'; interaction.release(False); step(240)
    check('spring_returns_latch',abs(interaction.metrics['latch_angle_deg']-REST_DEG)<1,**interaction.metrics)
    phase='insert'; move((0,.0002,0),2); step(240); snapshot('seated')
    angles=[p['latch_angle_deg'] for p in trace if p['phase']=='insert']
    check('ramp_deflects_latch_on_entry',min(angles)<rest-3,min_deg=min(angles),rest_deg=rest)
    check('hook_springs_behind_lip',interaction.state=='retained' and interaction.metrics['hook_behind_lip'],**interaction.metrics)
    phase='pull'; before,_=interaction.pose(); move((0,.035,0)); step(240); after,_=interaction.pose(); snapshot('pull')
    check('contact_retains_under_5N',(after-before).GetLength()<.0005 and interaction.state=='retained',drift_m=(after-before).GetLength(),**interaction.metrics)
    # Negative control: keep pressing command but remove the pad's ability to push.
    phase='blocked_press'; move((0,.0002,0),.5)
    interaction.press_drive.GetMaxForceAttr().Set(0); interaction.release(True); step(120)
    check('release_command_alone_does_not_unlock',interaction.state=='retained',**interaction.metrics)
    interaction.press_drive.GetMaxForceAttr().Set(4)
    phase='press'; step(240); snapshot('release')
    check('measured_depression_releases',interaction.state=='released' and interaction.metrics['hook_clear'],**interaction.metrics)
    phase='reengage_without_removal'; interaction.release(False); step(240)
    check('letting_go_of_pad_relatches',interaction.state=='retained' and interaction.metrics['hook_behind_lip'],**interaction.metrics)
    phase='second_press'; interaction.release(True); step(240)
    check('second_press_physically_releases',interaction.state=='released' and interaction.metrics['hook_clear'],**interaction.metrics)
    phase='extract'; move((0,.05,0),2); step(120)
    check('pressed_latch_allows_extraction',interaction.metrics['depth_m']<-.02,**interaction.metrics)
    # Reinsert, then remove only the socket lip's collision as a causal control.
    phase='reinsert'; interaction.release(False); step(120); move((0,.0002,0),2); step(240)
    check('repeated_contact_engagement',interaction.state=='retained',**interaction.metrics)
    UsdPhysics.CollisionAPI(stage.GetPrimAtPath('/World/Socket/LatchLip')).GetCollisionEnabledAttr().Set(False)
    phase='lip_disabled'; move((0,.05,0),2); step(120)
    check('without_lip_unpressed_plug_extracts',interaction.metrics['depth_m']<-.02,**interaction.metrics)
    report={'passed':all(c['passed'] for c in checks),'checks':checks,'trace':trace,'run_source':str(Path(__file__).parent.parent)}
    Path(args.output).write_text(json.dumps(report,indent=2)); print('PROBE_RESULT',report['passed'],flush=True)
    stage.GetRootLayer().Export(str(Path(args.output).with_suffix('.usda')))
    if not report['passed']: raise RuntimeError('Mechanical latch probe failed')
finally:
    app.close()
