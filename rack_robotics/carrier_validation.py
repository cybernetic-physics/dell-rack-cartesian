"""Sampled carrier integrity gates: startup is part of acceptance, not discarded."""
import math

REVISION = 'startup_and_task_sampled_carriers_v1'


def carrier_integrity_checks(task_samples, startup_samples):
    checks = {}
    for prefix, samples in (('',task_samples),('startup_',startup_samples)):
        finite = all(not s.get('errors') and all(math.isfinite(s.get(k,float('nan')))
                     for k in ('maximum_anchor_gap_m','minimum_hinge_deg','maximum_hinge_deg'))
                     for s in samples)
        checks[prefix+'samples_present'] = bool(samples)
        checks[prefix+'finite_state'] = bool(samples) and finite
        checks[prefix+'sampled_anchor_gap_below_1p5mm'] = bool(samples) and finite and all(
            0 <= s['maximum_anchor_gap_m'] < .0015 for s in samples)
        checks[prefix+'sampled_hinge_limits_within_one_degree'] = bool(samples) and finite and all(
            -1 < s['minimum_hinge_deg'] <= s['maximum_hinge_deg'] < 31 for s in samples)
    return checks


def brake_carrier_checks(samples):
    """Apply the same gates to the brake probe, including its initial settle."""
    return carrier_integrity_checks(
        [s for s in samples if s.get('phase') != 'initial_settle'],
        [s for s in samples if s.get('phase') == 'initial_settle'])
