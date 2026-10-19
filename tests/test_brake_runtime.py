import unittest
from types import SimpleNamespace
from rack_robotics.brakes import BrakeBank
from rack_robotics.brake_runtime import BrakeRuntime


class Attr:
    def __init__(self,value):self.value=value
    def Get(self):return self.value
    def Set(self,value):self.value=value


class Drive:
    def __init__(self,k,d):self.k=Attr(k);self.d=Attr(d)
    def GetStiffnessAttr(self):return self.k
    def GetDampingAttr(self):return self.d


class Articulation:
    def set_joint_efforts(self,values,joint_indices):self.effort=values


class Transmission:
    def __init__(self):self.enabled=(True,True)
    def step(self,x_force_limit_n=None):self.latest={'joint_force_n':[3.,7.] if all(self.enabled) else [0.,0.]}


class BrakeRuntimeTest(unittest.TestCase):
    def runtime(self,architecture):
        r=BrakeRuntime.__new__(BrakeRuntime)
        r.bank=BrakeBank(architecture);r.np=SimpleNamespace(array=list)
        r.drives={'z':Drive(0 if architecture=='C' else 100000,0 if architecture=='C' else 500),
                  'y':Drive(15000,35),'left':Drive(20000,8)}
        r.original_gains={n:(d.k.Get(),d.d.Get()) for n,d in r.drives.items()}
        r.transmission=Transmission() if architecture=='C' else None
        r.articulation=Articulation();r.indices=list(range(len(r.bank.joints)))
        r.powered=True;r.state=lambda:([0.]*len(r.indices),[0.]*len(r.indices))
        return r

    def test_power_off_all_drive_gains_and_restore(self):
        for architecture in 'ABC':
            r=self.runtime(architecture);r.power(False)
            s=r.step(.01)
            self.assertTrue(all(pair==[0.,0.] for pair in s['drive_gains'].values()))
            self.assertFalse(s['motor_power_enabled'])
            self.assertTrue(all(f==0 for f in s['external_motor_effort_n']))
            r.power(True)
            self.assertEqual({n:(d.k.Get(),d.d.Get()) for n,d in r.drives.items()},r.original_gains)

    def test_corexz_efforts_sum_without_overwriting_passive_brake(self):
        r=self.runtime('C');r.step(.03,False)
        r.state=lambda:([.01,-.01],[0.,0.])
        s=r.step(.001,False)
        self.assertEqual(r.articulation.effort,[a+b for a,b in zip(s['brakes']['joint_effort_n'],[3.,7.])])
        self.assertTrue(any(f!=0 for f in s['brakes']['joint_effort_n']))
        r.power(False);s=r.step(.001,False)
        self.assertEqual(r.articulation.effort,s['brakes']['joint_effort_n'])
