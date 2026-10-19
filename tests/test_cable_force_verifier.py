import gzip
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from rack_robotics.benchmarking.cable_balance import residual_forces,distal_reactions

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('force_verifier',ROOT/'rack_robotics/scripts/verify_cable_force.py')
module=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(module)


class CableForceVerifierTests(unittest.TestCase):
    def fixture(self,p):
        source=p/'harness/benchmarking/cable_balance.py';source.parent.mkdir(parents=True)
        shutil.copy2(ROOT/'rack_robotics/benchmarking/cable_balance.py',source)
        (p/'source_manifest.json').write_text(json.dumps({'harness/benchmarking/cable_balance.py':module.sha(source)}))
        cal={'passed':True,'source_sha256':{'balance_source.py':module.sha(source)},'physics_dt_s':.1}
        (p/'cable_force_calibration.json').write_text(json.dumps(cal))
        header={'physics_dt_s':.1,'body_paths':[f'/World/Cable/Link{i:02d}' for i in range(36)],
                'masses_kg':[.001]*36,'gravity_m_s2':[0.,0.,-10.],'linear_damping':[0.]*36}
        zeros=[[0.]*3 for _ in range(36)]
        reaction=distal_reactions(residual_forces(header['masses_kg'],zeros,zeros,zeros,.1,header['gravity_m_s2'],header['linear_damping']))
        values=[r[2] for r in reaction]
        row={'time_s':.1,'phase':'test','before_m_s':zeros,'after_m_s':zeros,'contact_impulse_ns':zeros,
             'toward_parent_axes':[[0.,0.,1.]]*36,'axial_force_n':values,'resultant_force_n':values}
        summary={'sample_count':1,'reporting_errors':[],'task_complete':True,
                 'peak_tension':{'force_n':values[0]},'peak_resultant':{'force_n':values[0]},
                 'maximum_compression_n':0.,'per_joint_peak_tension_n':values,
                 'phase_peaks':{'test':{'samples':1,'maximum_tension_n':values[0],'maximum_resultant_n':values[0]}}}
        (p/'cable_force_summary.json').write_text(json.dumps(summary))
        result={'runner':'cable_momentum_diagnostic_v1','randomized_reliability_sample':False,'passed':True,
                'physics_dt':.1,'cycle_time_s':.1,'cable_momentum':summary,
                'cable_force_calibration_sha256':module.sha(p/'cable_force_calibration.json')}
        (p/'results.json').write_text(json.dumps(result))
        self.trace(p,header,row)
        return header,row

    def trace(self,p,header,row):
        with gzip.open(p/'cable_force_trace.jsonl.gz','wt') as f:
            f.write(json.dumps(header)+'\n')
            if row is not None:f.write(json.dumps(row)+'\n')

    def test_recomputes_every_saved_joint(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);self.fixture(p);r=module.verify(p)
            self.assertTrue(r['passed']);self.assertEqual(r['samples_verified'],1)
            self.assertAlmostEqual(r['peak_tension_n'],.36)

    def test_changed_force_and_missing_step_rejected(self):
        for change in ('force','time','missing'):
            with tempfile.TemporaryDirectory() as folder:
                p=Path(folder);h,r=self.fixture(p)
                if change=='force':r['axial_force_n'][0]=1.
                if change=='time':r['time_s']=.2
                self.trace(p,h,None if change=='missing' else r)
                with self.assertRaises(ValueError):module.verify(p)

    def test_changed_frozen_source_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder);self.fixture(p)
            (p/'harness/benchmarking/cable_balance.py').write_text('changed')
            with self.assertRaises(ValueError):module.verify(p)
