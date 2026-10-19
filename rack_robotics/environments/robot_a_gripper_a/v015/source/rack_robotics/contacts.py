"""Read-only PhysX contact reports for collision diagnosis and force estimates.

Pair impulse magnitude / physics dt is a contact-force estimate, not actuator
effort or a calibrated force sensor. Friction-anchor impulses are not included.
"""
import json
import math
from pxr import UsdPhysics, PhysxSchema, PhysicsSchemaTools
from omni.physx import get_physx_simulation_interface


class ContactRecorder:
    def __init__(self,stage,dt):
        self.dt=dt; self.phase='initialization'; self.time=0.; self.pairs={}; self.errors=[]
        for prim in stage.Traverse():
            if prim.HasAPI(UsdPhysics.RigidBodyAPI):
                PhysxSchema.PhysxContactReportAPI.Apply(prim).CreateThresholdAttr(0)
        self.subscription=get_physx_simulation_interface().subscribe_contact_report_events(self.on_contacts)

    def reset(self):
        self.pairs={}; self.errors=[]

    def on_contacts(self,headers,data):
        try:
            for h in headers:
                if not h.num_contact_data: continue
                paths=tuple(str(PhysicsSchemaTools.intToSdfPath(v)) for v in (h.collider0,h.collider1))
                key=' | '.join(sorted(paths))
                contacts=data[h.contact_data_offset:h.contact_data_offset+h.num_contact_data]
                impulse_sum=0.; separation=0.
                for c in contacts:
                    try: magnitude=math.sqrt(sum(float(v)**2 for v in c.impulse))
                    except TypeError: magnitude=abs(float(c.impulse))
                    impulse_sum+=magnitude; separation=min(separation,float(c.separation))
                force=impulse_sum/self.dt
                pair=self.pairs.setdefault(key,{'colliders':sorted(paths),'reports':0,
                    'minimum_separation_m':0.,'peak_pair_contact_force_n':0.,'phase_peaks_n':{}})
                pair['reports']+=1
                pair['minimum_separation_m']=min(pair['minimum_separation_m'],separation)
                pair['phase_peaks_n'][self.phase]=max(pair['phase_peaks_n'].get(self.phase,0),force)
                if force>pair['peak_pair_contact_force_n']:
                    pair.update(peak_pair_contact_force_n=force,peak_time_s=self.time,peak_phase=self.phase)
        except Exception as exc:
            if len(self.errors)<10: self.errors.append(repr(exc))

    def save(self,path):
        report={'reporting_errors':self.errors,'pair_count':len(self.pairs),
                'physics_dt':self.dt,'pairs':list(self.pairs.values()),
                'scope':'Contact impulse magnitude sum per collider pair divided by dt; no friction-anchor impulses; not motor force or a safety certification.'}
        path.write_text(json.dumps(report,indent=2)+'\n')
        return report
