"""Read cooked PhysX mass/COM/inertia and geometry from a saved environment.

This isolated property query is not a manipulation test or a load certification.
It never saves changes to the source environment or drives connector motion.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import traceback


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--environment',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
args,_=p.parse_known_args()
env=args.environment.resolve(); out=args.output.resolve()
manifest=json.loads((env/'manifest.json').read_text())
config=json.loads((env/'config.json').read_text())
for name,digest in manifest['packaged_file_sha256'].items():
    if sha(env/name)!=digest: raise ValueError(f'Changed saved environment: {name}')
out.mkdir(parents=True,exist_ok=False)
shutil.copy2(__file__,out/'extract_source.py')
report={'schema':'rack_mechanical_properties_v1','environment':str(env),
        'environment_manifest_sha256':sha(env/'manifest.json'),
        'source_sha256':sha(Path(__file__)),'robot':config['robot'],'gripper':config['gripper'],
        'passed':False,'scope':'Cooked simulation properties, not measured hardware properties'}

from isaacsim import SimulationApp
app=SimulationApp({'headless':True,'multi_gpu':False,'width':1280,'height':800})
try:
    import omni.usd
    from pxr import Usd,UsdGeom,UsdPhysics,Gf
    from isaacsim.core.api import World
    from isaacsim.core.simulation_manager import SimulationManager
    layer=Usd.Stage.CreateNew(str(out/'query_scene.usda'))
    layer.GetRootLayer().subLayerPaths=[os.path.relpath(env/config['scene'],out)]
    layer.GetRootLayer().Save(); del layer
    assert omni.usd.get_context().open_stage(str(out/'query_scene.usda'))
    for _ in range(30): app.update()
    while omni.usd.get_context().get_stage_loading_status()[2]>0: app.update()
    stage=omni.usd.get_context().get_stage()
    if stage.GetCompositionErrors(): raise ValueError(str(stage.GetCompositionErrors()))
    root=stage.GetPrimAtPath('/World/Robot')
    bodies={str(prim.GetPath()):prim for prim in Usd.PrimRange(root)
            if prim.HasAPI(UsdPhysics.RigidBodyAPI)}
    if not bodies: raise ValueError('Missing robot bodies')
    xforms=UsdGeom.XformCache()
    # Recorded poses contain rotation/translation, not scale or shear. Reject
    # bodies for which those seven numbers cannot reproduce the body frame.
    for path,prim in bodies.items():
        matrix=xforms.GetLocalToWorldTransform(prim)
        axes=[matrix.TransformDir(Gf.Vec3d(*(1. if i==j else 0. for i in range(3)))) for j in range(3)]
        if (any(abs(axis.GetLength()-1)>1e-6 for axis in axes)
                or any(abs(Gf.Dot(axes[i],axes[j]))>1e-6 for i in range(3) for j in range(i))
                or matrix.GetDeterminant()<0):
            raise ValueError(f'Scale/shear/reflection is not represented by recorded rigid poses: {path}')
    # Extract geometry in body frames before reset. No pose assumptions enter
    # the later trajectory calculation; it uses recorded world body poses.
    bbox=UsdGeom.BBoxCache(Usd.TimeCode.Default(),['default','render','proxy'],False,True)
    geometry={path:[] for path in bodies}
    unowned=[]
    for prim in Usd.PrimRange(root):
        if not prim.IsA(UsdGeom.Boundable): continue
        owner=prim
        while owner and str(owner.GetPath()) not in bodies: owner=owner.GetParent()
        if not owner:
            unowned.append(str(prim.GetPath())); continue
        bounds=bbox.ComputeRelativeBound(prim,owner).ComputeAlignedRange()
        if bounds.IsEmpty(): raise ValueError(f'Empty geometry bound: {prim.GetPath()}')
        geometry[str(owner.GetPath())].append({'path':str(prim.GetPath()),
            'lower_m':list(bounds.GetMin()),'upper_m':list(bounds.GetMax()),
            'collision':prim.HasAPI(UsdPhysics.CollisionAPI),
            'visible':UsdGeom.Imageable(prim).ComputeVisibility()!=UsdGeom.Tokens.invisible})
    joints=[]
    for prim in Usd.PrimRange(root):
        if not prim.IsA(UsdPhysics.Joint): continue
        joint=UsdPhysics.Joint(prim)
        row={'path':str(prim.GetPath()),'type':prim.GetTypeName(),
             'body0':[str(v) for v in joint.GetBody0Rel().GetTargets()],
             'body1':[str(v) for v in joint.GetBody1Rel().GetTargets()],
             'anchor_in_body0_m':list(joint.GetLocalPos0Attr().Get())}
        if prim.IsA(UsdPhysics.PrismaticJoint):
            j=UsdPhysics.PrismaticJoint(prim)
            row.update(axis=j.GetAxisAttr().Get(),limits_m=[j.GetLowerLimitAttr().Get(),j.GetUpperLimitAttr().Get()])
        joints.append(row)
    mounts=[str(prim.GetPath()) for prim in Usd.PrimRange(root) if prim.GetName().startswith('PostClamp')]
    mount_centres=[list(xforms.GetLocalToWorldTransform(stage.GetPrimAtPath(path)).ExtractTranslation()) for path in mounts]
    world=World(physics_dt=1/240,rendering_dt=1/60,stage_units_in_meters=1,physics_prim_path='/World/Physics')
    world.reset()
    # Use the manager's stage-attached view. The installed multi-stage backend
    # does not infer the correct stage from legacy create_simulation_view(-1).
    sim=SimulationManager.get_physics_sim_view()
    if sim is None: raise RuntimeError('Physics manager has no initialized simulation view')
    def flat(value):
        if hasattr(value,'detach'): value=value.detach().cpu()
        if hasattr(value,'numpy'): value=value.numpy()
        return value.reshape(-1).tolist()
    rows={}
    for path,prim in bodies.items():
        view=sim.create_rigid_body_view(path)
        if view.count!=1: raise ValueError(f'Expected one cooked body: {path}, got {view.count}')
        mass=float(flat(view.get_masses())[0])
        com=flat(view.get_coms())
        inertia=flat(view.get_inertias())
        if len(com)!=7 or len(inertia)!=9 or mass<=0 or not all(math.isfinite(v) for v in [mass,*com,*inertia]):
            raise ValueError(f'Invalid cooked properties: {path}')
        authored=UsdPhysics.MassAPI(prim).GetMassAttr().Get()
        if authored is not None and abs(mass-authored)>1e-5:
            raise ValueError(f'Cooked mass differs from saved mass: {path}')
        rows[path]={'mass_kg':mass,'com_local_xyz_xyzw':com,
                    'inertia_at_com_expressed_body_frame_column_major_kg_m2':inertia,
                    'geometry':geometry[path]}
    report.update(passed=True,bodies=rows,joints=joints,mount_centres_m=mount_centres,
        mount_paths=mounts,unowned_geometry=unowned,total_mass_kg=sum(row['mass_kg'] for row in rows.values()),
        limitations=['Masses are design/asset estimates; inertia and COM are cooked from simulation geometry.',
                     'Bounds include visual and collision shapes; transformed boxes are conservative, not exact contact clearances.',
                     'Non-rigid decorative belt curves are listed separately; cables/carriers not modeled are not included.',
                     'No bracket, fastener, rack, belt, brake or motor safety rating is established.'])
except Exception:
    report.update(error=traceback.format_exc())
finally:
    (out/'properties.json').write_text(json.dumps(report,indent=2)+'\n')
    print('MECHANICAL_PROPERTIES',report['passed'],report.get('error'),flush=True)
    app.close()
if not report['passed']: raise SystemExit(1)
