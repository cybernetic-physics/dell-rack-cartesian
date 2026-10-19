"""Read-only, physics-step cable reaction estimate from validated momentum balance."""
import gzip
import json
import math

from .cable_balance import FullContactImpulses, residual_forces, distal_reactions, axial_component


def validate_calibration(calibration,balance_hash,dt):
    required={'free_fall_residual_below_1mn','held_weight_within_1mn',
              'resting_contact_residual_below_10mn','sliding_contact_residual_below_10mn',
              'friction_anchors_present','chain_root_weight_within_2mn',
              'chain_distal_weight_within_1mn','all_finite','reporting_errors_absent'}
    checks=calibration.get('checks',{})
    if (calibration.get('passed') is not True or not required<=set(checks)
            or not all(value is True for value in checks.values())
            or calibration.get('source_sha256',{}).get('balance_source.py')!=balance_hash
            or calibration.get('physics_dt_s')!=dt):
        raise ValueError('Missing, failed, timestep-mismatched or source-mismatched cable momentum calibration')


def negative_y_axis(quaternion_xyzw):
    x,y,z,w=map(float,quaternion_xyzw)
    length=math.sqrt(x*x+y*y+z*z+w*w)
    if not math.isfinite(length) or length<1e-12:
        raise ValueError('Invalid measured cable orientation')
    x,y,z,w=[v/length for v in (x,y,z,w)]
    return [-2*(x*y-z*w),-(1-2*(x*x+z*z)),-2*(y*z+x*w)]


class CableForceTrace:
    def __init__(self,stage,dt,count,output):
        import omni.usd
        import omni.physics.tensors as tensors
        from pxr import UsdPhysics,PhysxSchema
        self.dt=dt;self.paths=[f'/World/Cable/Link{i:02d}' for i in range(count)]
        expected={f'/World/Cable/Joint{i:02d}' for i in range(count)}
        attached=set()
        for prim in stage.Traverse():
            if not prim.IsA(UsdPhysics.Joint):continue
            joint=UsdPhysics.Joint(prim)
            targets=[str(p) for rel in (joint.GetBody0Rel(),joint.GetBody1Rel()) for p in rel.GetTargets()]
            if any(p in self.paths for p in targets):attached.add(str(prim.GetPath()))
        if attached!=expected:raise ValueError('Momentum estimator requires the original unbranched free-ended cable')
        for i,path in enumerate(self.paths):
            joint=UsdPhysics.Joint(stage.GetPrimAtPath(f'/World/Cable/Joint{i:02d}'))
            if ([str(p) for p in joint.GetBody0Rel().GetTargets()]!=[self.paths[i-1] if i else '/World/Plug']
                    or [str(p) for p in joint.GetBody1Rel().GetTargets()]!=[path]):
                raise ValueError('Unexpected cable connectivity')
            local=joint.GetLocalPos1Attr().Get()
            if abs(local[0])+abs(local[2])>1e-9 or local[1]>=0:
                raise ValueError('Cable joint axis is not the expected local negative Y')
        self.sim_view=tensors.create_simulation_view('numpy',stage_id=omni.usd.get_context().get_stage_id())
        self.sim_view.set_subspace_roots('/')
        self.view=self.sim_view.create_rigid_body_view('/World/Cable/Link*')
        if set(self.view.prim_paths)!=set(self.paths):raise ValueError('Cable tensor view contains missing or extra bodies')
        self.order=[list(self.view.prim_paths).index(p) for p in self.paths]
        self.masses=self.view.get_masses().reshape(-1)[self.order].astype(float).tolist()
        self.damping=[float(PhysxSchema.PhysxRigidBodyAPI(stage.GetPrimAtPath(p)).GetLinearDampingAttr().Get()) for p in self.paths]
        physics=UsdPhysics.Scene(stage.GetPrimAtPath('/World/Physics'))
        direction=physics.GetGravityDirectionAttr().Get();magnitude=float(physics.GetGravityMagnitudeAttr().Get())
        norm=math.sqrt(sum(float(x)**2 for x in direction))
        self.gravity=[float(x)*magnitude/norm for x in direction]
        self.contacts=FullContactImpulses(self.paths)
        self.count=0;self.phase_peaks={};self.peak_axial=None;self.peak_resultant=None
        self.joint_axial_peaks=[0.]*count;self.minimum_axial=0.;self.before_velocity=None
        self.stream=gzip.open(output,'xt',encoding='utf-8')
        self.stream.write(json.dumps({'schema':'cable_momentum_trace_v1','body_paths':self.paths,
            'masses_kg':self.masses,'linear_damping':self.damping,'gravity_m_s2':self.gravity,
            'physics_dt_s':dt,'scope':'Per-step momentum balance; axial projection on post-step child negative-Y axis; no body actuation'})+'\n')

    def before(self):
        self.before_velocity=self.view.get_velocities()[self.order,:3].astype(float).copy()
        self.contacts.begin()

    def after(self,time_s,phase):
        if self.before_velocity is None:raise RuntimeError('Missing pre-step velocity sample')
        after=self.view.get_velocities()[self.order,:3].astype(float).copy()
        transforms=self.view.get_transforms()[self.order].astype(float).copy()
        impulses=self.contacts.totals()
        residuals=residual_forces(self.masses,self.before_velocity,after,impulses,self.dt,self.gravity,self.damping)
        forces=distal_reactions(residuals)
        axes=[negative_y_axis(t[3:7]) for t in transforms]
        axial=[axial_component(f,a) for f,a in zip(forces,axes)]
        resultant=[math.sqrt(sum(x*x for x in f)) for f in forces]
        peak=self.phase_peaks.setdefault(phase,{'maximum_tension_n':0.,'maximum_resultant_n':0.,'samples':0})
        peak['samples']+=1;peak['maximum_tension_n']=max(peak['maximum_tension_n'],max(axial))
        peak['maximum_resultant_n']=max(peak['maximum_resultant_n'],max(resultant))
        for i,(a,r) in enumerate(zip(axial,resultant)):
            self.joint_axial_peaks[i]=max(self.joint_axial_peaks[i],a)
            self.minimum_axial=min(self.minimum_axial,a)
            if self.peak_axial is None or a>self.peak_axial['force_n']:
                self.peak_axial={'joint_index':i,'force_n':max(0.,a),'time_s':time_s,'phase':phase}
            if self.peak_resultant is None or r>self.peak_resultant['force_n']:
                self.peak_resultant={'joint_index':i,'force_n':r,'time_s':time_s,'phase':phase}
        self.stream.write(json.dumps({'time_s':time_s,'phase':phase,
            'before_m_s':self.before_velocity.tolist(),'after_m_s':after.tolist(),
            'contact_impulse_ns':impulses,'toward_parent_axes':axes,
            'axial_force_n':axial,'resultant_force_n':resultant,
            'friction_anchor_count':self.contacts.anchors},separators=(',',':'))+'\n')
        self.count+=1;self.before_velocity=None

    def close(self,task_complete):
        self.stream.close()
        return {'schema':'cable_momentum_summary_v1','sample_count':self.count,'physics_dt_s':self.dt,
            'task_complete':bool(task_complete),'reporting_errors':self.contacts.errors,
            'peak_tension':self.peak_axial,'peak_resultant':self.peak_resultant,
            'maximum_compression_n':-self.minimum_axial,'per_joint_peak_tension_n':self.joint_axial_peaks,
            'phase_peaks':self.phase_peaks,
            'scope':'Timed-task free-ended cable reaction estimate, including normal and friction contact impulses; not a calibrated material stress or hardware safe-load limit',
            'limitations':['Requires unbranched cable and no unrecorded external linear forces.',
                           'Angular drive torques have no net linear impulse; torque/stress is not estimated.',
                           'Finite-step reaction projected onto post-step child axis; not instantaneous continuum tension.',
                           'Solver stabilization/projection and unreported impulses can bias dynamic estimates; validate against independent controls.']}
