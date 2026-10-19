"""Isolated momentum/contact accounting controls, not a rack tension result."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import traceback


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args,_=parser.parse_known_args()
    root=Path(__file__).resolve().parents[2]
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
    shutil.copy2(__file__,out/'probe_source.py')
    shutil.copy2(root/'rack_robotics/benchmarking/cable_balance.py',out/'balance_source.py')
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.py')}
    (out/'source_manifest.json').write_text(json.dumps(hashes,indent=2)+'\n')
    sys.path.insert(0,str(out))
    from balance_source import residual_forces,distal_reactions,FullContactImpulses
    from isaacsim import SimulationApp
    app=SimulationApp({'headless':True,'multi_gpu':False,'width':320,'height':240})
    try:
        import numpy as np
        import omni.usd
        import omni.physics.tensors as tensors
        from pxr import Gf,UsdGeom,UsdPhysics,PhysxSchema,UsdShade
        from isaacsim.core.api import World
        stage=omni.usd.get_context().get_stage()
        UsdGeom.SetStageMetersPerUnit(stage,1);UsdGeom.SetStageUpAxis(stage,'Z')
        UsdPhysics.SetStageKilogramsPerUnit(stage,1)
        UsdGeom.Xform.Define(stage,'/World')
        scene=UsdPhysics.Scene.Define(stage,'/World/Physics')
        scene.CreateGravityDirectionAttr(Gf.Vec3f(0,0,-1));scene.CreateGravityMagnitudeAttr(9.81)
        px=PhysxSchema.PhysxSceneAPI.Apply(scene.GetPrim());px.CreateSolverTypeAttr('TGS')
        px.CreateEnableGPUDynamicsAttr(False)
        material=UsdShade.Material.Define(stage,'/World/Material')
        mat=UsdPhysics.MaterialAPI.Apply(material.GetPrim())
        mat.CreateStaticFrictionAttr(.5);mat.CreateDynamicFrictionAttr(.5);mat.CreateRestitutionAttr(0)
        paths=[]

        def cube(name,position,size,mass=None,velocity=None):
            body=UsdGeom.Cube.Define(stage,'/World/'+name);body.CreateSizeAttr(1.)
            body.AddTranslateOp().Set(Gf.Vec3d(*position));body.AddScaleOp().Set(Gf.Vec3f(*size))
            UsdPhysics.CollisionAPI.Apply(body.GetPrim())
            UsdShade.MaterialBindingAPI.Apply(body.GetPrim()).Bind(material,materialPurpose='physics')
            col=PhysxSchema.PhysxCollisionAPI.Apply(body.GetPrim());col.CreateContactOffsetAttr(.001);col.CreateRestOffsetAttr(0)
            if mass is not None:
                rb=UsdPhysics.RigidBodyAPI.Apply(body.GetPrim())
                if velocity is not None:rb.CreateVelocityAttr(Gf.Vec3f(*velocity))
                UsdPhysics.MassAPI.Apply(body.GetPrim()).CreateMassAttr(mass)
                api=PhysxSchema.PhysxRigidBodyAPI.Apply(body.GetPrim())
                api.CreateSolverPositionIterationCountAttr(128);api.CreateSolverVelocityIterationCountAttr(8)
                api.CreateLinearDampingAttr(.15);api.CreateAngularDampingAttr(.15);api.CreateSleepThresholdAttr(0.)
                PhysxSchema.PhysxContactReportAPI.Apply(body.GetPrim()).CreateThresholdAttr(0)
                paths.append(str(body.GetPath()))
            return body

        cube('BodyFree',(0,0,3),(.1,.1,.1),.0252)
        cube('BodyHeld',(1,0,2),(.1,.1,.1),.0252)
        cube('BodyRest',(2,0,.101),(.2,.2,.2),.1)
        cube('BodySlide',(4,0,.101),(.2,.2,.2),.1,(1,0,0))
        cube('FloorRest',(2,0,-.1),(1,1,.2))
        cube('FloorSlide',(4,0,-.1),(2,1,.2))
        cube('BodyChain0',(6,0,2),(.1,.1,.1),.0252)
        cube('BodyChain1',(6,0,1.8),(.1,.1,.1),.0252)

        def joint(name,body0,body1,pos0,pos1):
            j=UsdPhysics.Joint.Define(stage,'/World/'+name)
            if body0:j.CreateBody0Rel().SetTargets([body0])
            j.CreateBody1Rel().SetTargets([body1])
            j.CreateLocalPos0Attr(Gf.Vec3f(*pos0));j.CreateLocalPos1Attr(Gf.Vec3f(*pos1))
            j.CreateCollisionEnabledAttr(False)
            for axis in ('transX','transY','transZ'):
                lim=UsdPhysics.LimitAPI.Apply(j.GetPrim(),axis);lim.CreateLowAttr(1);lim.CreateHighAttr(-1)
            for axis in ('rotX','rotY','rotZ'):
                lim=UsdPhysics.LimitAPI.Apply(j.GetPrim(),axis);lim.CreateLowAttr(-40);lim.CreateHighAttr(40)
                d=UsdPhysics.DriveAPI.Apply(j.GetPrim(),axis);d.CreateTypeAttr('force');d.CreateStiffnessAttr(.0002);d.CreateDampingAttr(.00008)
        joint('HeldJoint',None,'/World/BodyHeld',(1,0,2),(0,0,0))
        joint('ChainRoot',None,'/World/BodyChain0',(6,0,2),(0,0,0))
        joint('ChainDistal','/World/BodyChain0','/World/BodyChain1',(0,0,-.1),(0,0,.1))
        stage.GetRootLayer().Export(str(out/'scene.usda'))
        dt=1/480
        world=World(physics_dt=dt,rendering_dt=1/60,stage_units_in_meters=1,physics_prim_path='/World/Physics')
        contacts=FullContactImpulses(paths)
        world.reset()
        # Kit attaches this fresh stage lazily on the first update. Read-only
        # tensor views require that attachment; calibration begins afterward.
        world.step(render=True)
        # The installed SimulationManager also passes an explicit stage ID;
        # the legacy implicit attached-stage lookup is unavailable here.
        view=tensors.create_simulation_view('numpy',stage_id=omni.usd.get_context().get_stage_id())
        view.set_subspace_roots('/')
        bodies=view.create_rigid_body_view('/World/Body*')
        order=[list(bodies.prim_paths).index(p) for p in paths]
        masses=bodies.get_masses().reshape(-1)[order].astype(float).tolist()
        samples=[]
        for index in range(480):
            before=bodies.get_velocities()[order,:3].astype(float).copy()
            contacts.begin();world.step(render=False)
            after=bodies.get_velocities()[order,:3].astype(float).copy()
            impulses=contacts.totals()
            residuals=residual_forces(masses,before,after,impulses,dt,[0,0,-9.81],[.15]*len(paths))
            samples.append({'step':index,'before_m_s':before.tolist(),'after_m_s':after.tolist(),
                'normal_impulse_ns':[contacts.normal[p] for p in paths],
                'friction_impulse_ns':[contacts.friction[p] for p in paths],
                'residual_force_n':residuals,'friction_anchor_count':contacts.anchors})
            if index%8==0:world.render()
        world.pause();app.update()
        peaks={p:max(float(np.linalg.norm(s['residual_force_n'][i])) for s in samples)
               for i,p in enumerate(paths)}
        mean=np.mean([s['residual_force_n'] for s in samples[100:]],axis=0)
        expected=.0252*9.81*(1-.15*dt)
        held=paths.index('/World/BodyHeld');chain0=paths.index('/World/BodyChain0');chain1=paths.index('/World/BodyChain1')
        chain=distal_reactions([mean[chain0].tolist(),mean[chain1].tolist()])
        checks={'free_fall_residual_below_1mn':peaks['/World/BodyFree']<.001,
                'held_weight_within_1mn':abs(float(mean[held,2])-expected)<.001,
                'resting_contact_residual_below_10mn':peaks['/World/BodyRest']<.01,
                'sliding_contact_residual_below_10mn':peaks['/World/BodySlide']<.01,
                'friction_anchors_present':sum(s['friction_anchor_count'] for s in samples)>0,
                'chain_root_weight_within_2mn':abs(chain[0][2]-2*expected)<.002,
                'chain_distal_weight_within_1mn':abs(chain[1][2]-expected)<.001,
                'all_finite':all(np.isfinite(s['residual_force_n']).all() for s in samples),
                'reporting_errors_absent':not contacts.errors}
        report={'passed':all(checks.values()),'checks':checks,'body_paths':paths,'masses_kg':masses,
                'physics_dt_s':dt,'linear_damping':.15,'source_sha256':hashes,
                'scene_sha256':hashlib.sha256((out/'scene.usda').read_bytes()).hexdigest(),
                'peak_residual_n':peaks,'mean_residual_n':mean.tolist(),'chain_reaction_n':chain,
                'expected_single_weight_n':expected,'samples':samples,
                'scope':'Isolated momentum, gravity/damping, normal/friction contact and distal-sum controls; not cable-load safety'}
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
        print('CABLE_BALANCE_PROBE',json.dumps({'passed':report['passed'],'checks':checks,'peaks':peaks}),flush=True)
        if not report['passed']:raise RuntimeError('Momentum estimator calibration failed; no rack force claim allowed')
    except Exception:
        error=traceback.format_exc();print(error,flush=True)
        (out/'failure.json').write_text(json.dumps({'passed':False,'error':error},indent=2)+'\n')
        raise
    finally:app.close()


if __name__=='__main__':main()
