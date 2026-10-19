"""Recompute every saved cable-force sample from velocities and full impulses.

This verifies trace arithmetic, completeness and provenance, not manufacturer
safe loads or an independent physical force sensor.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(directory):
    directory=directory.resolve()
    sources=json.loads((directory/'source_manifest.json').read_text())
    if not sources:raise ValueError('Missing source manifest')
    for name,digest in sources.items():
        path=(directory/name).resolve()
        if not path.is_relative_to(directory) or sha(path)!=digest:
            raise ValueError('Changed or external frozen source: '+name)
    result=json.loads((directory/'results.json').read_text())
    summary=json.loads((directory/'cable_force_summary.json').read_text())
    if result.get('cable_momentum')!=summary:raise ValueError('Force summary differs from trial result')
    if result.get('runner')!='cable_momentum_diagnostic_v1' or result.get('randomized_reliability_sample') is not False:
        raise ValueError('Not a separately labeled momentum diagnostic')
    calibration_path=directory/'cable_force_calibration.json'
    if sha(calibration_path)!=result['cable_force_calibration_sha256']:
        raise ValueError('Changed calibration input')
    calibration=json.loads(calibration_path.read_text())
    source=directory/'harness/benchmarking/cable_balance.py'
    if calibration.get('passed') is not True or calibration['source_sha256']['balance_source.py']!=sha(source):
        raise ValueError('Failed or source-mismatched calibration')
    spec=importlib.util.spec_from_file_location('frozen_cable_balance',source)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    maximum_error=0.;count=0;last_time=0.;peak_axial=0.;peak_resultant=0.;minimum=0.
    phases={};joint_peaks=None
    trace=directory/'cable_force_trace.jsonl.gz'
    with gzip.open(trace,'rt') as stream:
        header=json.loads(next(stream));dt=header['physics_dt_s'];n=len(header['body_paths'])
        if n!=36 or header['body_paths']!=[f'/World/Cable/Link{i:02d}' for i in range(36)]:
            raise ValueError('Unexpected cable body list')
        if dt!=result['physics_dt'] or dt!=calibration['physics_dt_s']:
            raise ValueError('Timestep disagreement')
        joint_peaks=[0.]*n
        for line in stream:
            row=json.loads(line);now=row['time_s']
            if not math.isfinite(now) or abs(now-last_time-dt)>1e-9:
                raise ValueError('Missing or out-of-order physics-step sample')
            axes=row['toward_parent_axes']
            if len(axes)!=n or any(abs(sum(v*v for v in axis)-1)>1e-8 for axis in axes):
                raise ValueError('Invalid axial directions')
            residual=module.residual_forces(header['masses_kg'],row['before_m_s'],row['after_m_s'],
                row['contact_impulse_ns'],dt,header['gravity_m_s2'],header['linear_damping'])
            reactions=module.distal_reactions(residual)
            axial=[module.axial_component(f,a) for f,a in zip(reactions,axes)]
            resultant=[math.sqrt(sum(v*v for v in f)) for f in reactions]
            for actual,stored in [(axial,row['axial_force_n']),(resultant,row['resultant_force_n'])]:
                if len(stored)!=n or not all(math.isfinite(v) for v in stored):raise ValueError('Invalid saved force')
                maximum_error=max(maximum_error,max(abs(a-b) for a,b in zip(actual,stored)))
            peak_axial=max(peak_axial,max(axial));peak_resultant=max(peak_resultant,max(resultant));minimum=min(minimum,min(axial))
            joint_peaks=[max(a,b) for a,b in zip(joint_peaks,axial)]
            phase=phases.setdefault(row['phase'],{'maximum_tension_n':0.,'maximum_resultant_n':0.,'samples':0})
            phase['samples']+=1;phase['maximum_tension_n']=max(phase['maximum_tension_n'],max(axial))
            phase['maximum_resultant_n']=max(phase['maximum_resultant_n'],max(resultant))
            count+=1;last_time=now
    if not count or count!=summary['sample_count'] or summary['reporting_errors']:
        raise ValueError('Missing samples or reporting errors')
    if maximum_error>1e-9:raise ValueError('Stored forces differ from recomputed momentum balance')
    if result['passed'] and (not summary['task_complete'] or abs(last_time-result['cycle_time_s'])>1e-9):
        raise ValueError('Successful task lacks complete force-trace coverage')
    comparisons=[(peak_axial,summary['peak_tension']['force_n']),
                 (peak_resultant,summary['peak_resultant']['force_n']),(-minimum,summary['maximum_compression_n'])]
    if len(summary['per_joint_peak_tension_n'])!=n:raise ValueError('Missing per-joint summary')
    comparisons+=list(zip(joint_peaks,summary['per_joint_peak_tension_n']))
    if set(phases)!=set(summary['phase_peaks']):raise ValueError('Phase coverage disagreement')
    for name,p in phases.items():
        if p['samples']!=summary['phase_peaks'][name]['samples']:raise ValueError('Phase sample-count disagreement')
        comparisons.extend((p[key],summary['phase_peaks'][name][key]) for key in ('maximum_tension_n','maximum_resultant_n'))
    if any(abs(a-b)>1e-9 for a,b in comparisons):raise ValueError('Recomputed summary disagrees')
    return {'passed':True,'scope':__doc__,'samples_verified':count,'maximum_recomputation_error_n':maximum_error,
            'peak_tension_n':peak_axial,'peak_resultant_n':peak_resultant,'maximum_compression_n':-minimum,
            'task_completed':result['passed'],'trace_sha256':sha(trace),'results_sha256':sha(directory/'results.json'),
            'summary_sha256':sha(directory/'cable_force_summary.json'),'source_manifest_sha256':sha(directory/'source_manifest.json'),
            'calibration_sha256':sha(calibration_path),'verifier_sha256':sha(Path(__file__))}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():raise FileExistsError(args.output)
    report=verify(args.directory)
    with args.output.open('x') as target:target.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
