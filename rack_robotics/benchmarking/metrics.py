"""Read-only outcome metrics; force estimates and missing evidence stay explicit."""
import math


def wilson(successes,total,z=1.959963984540054):
    if type(total) is not int or type(successes) is not int or not 0<=successes<=total:
        raise ValueError('Invalid binomial counts')
    if total==0: return None
    p=successes/total; denominator=1+z*z/total
    centre=(p+z*z/(2*total))/denominator
    radius=z*math.sqrt(p*(1-p)/total+z*z/(4*total*total))/denominator
    return [max(0.,centre-radius),min(1.,centre+radius)]


def trial_metrics(result,contacts=None):
    trace=result.get('trace') or []
    final=trace[-1] if trace else {}
    phases={}; robot_rack=[]; robot_self=[]
    for pair in contacts.get('pairs',[]) if contacts else []:
        paths=pair['colliders']
        for phase,force in pair.get('phase_peaks_n',{}).items():
            phases[phase]=max(phases.get(phase,0.),force)
        robot=[path.startswith('/World/Robot/') for path in paths]
        if all(robot): robot_self.append(pair['peak_pair_contact_force_n'])
        elif any(robot):
            other=paths[0] if not robot[0] else paths[1]
            if not other.startswith(('/World/Plug/','/World/Latch/','/World/Cable/')):
                robot_rack.append(pair['peak_pair_contact_force_n'])
    initial=result.get('measured_initial_pose',{}).get('metrics',{})
    admissible=(bool(result.get('initial_retained_without_hand')) and initial.get('hook_behind_lip') is True
                and initial.get('depth_m',0)>=.0105 and result.get('timed_trial_started',bool(trace)))
    verified=all((result.get('passed'),admissible,result.get('unplug_success'),
                  result.get('replug_success'),result.get('topology_audit',{}).get('passed')))
    return {'reported_pass':bool(result.get('passed')),'complete_cycle':verified,
        'admissible_initial_state':admissible,
        'fixture_failure':(result.get('failure_stage')=='initialization_exception'
                           or ('measured_initial_pose' in result and not admissible)),
        'initial_retained':bool(result.get('initial_retained_without_hand')),
        'unplug_success':bool(result.get('unplug_success')),'replug_success':bool(result.get('replug_success')),
        'cycle_time_s':result.get('cycle_time_s'),
        'latch_clear_observed':any(row.get('hook_clear') and row.get('phase') in ('release_latch','withdraw') for row in trace),
        'final_angle_deg':final.get('angle_deg'),'final_lateral_m':final.get('lateral_m'),
        'final_depth_m':final.get('depth_m'),'final_hook_behind_lip':final.get('hook_behind_lip'),
        'cable_max_gap_m':result.get('cable_max_gap_m'),
        'contact_reporting_errors':contacts.get('reporting_errors') if contacts else None,
        'phase_peak_pair_contact_estimate_n':phases if contacts else None,
        'robot_rack_contact_pair_count':len(robot_rack) if contacts else None,
        'robot_self_contact_pair_count':len(robot_self) if contacts else None,
        'robot_rack_peak_pair_estimate_n':max(robot_rack,default=0.) if contacts else None,
        'error':result.get('error'),'failure_stage':result.get('failure_stage'),
        'recoveries':len(result.get('recoveries',[]))}


def cable_displacement(header,samples):
    indices=[i for i,p in enumerate(header['body_paths']) if p.startswith('/World/Cable/Link')]
    if not indices or not samples: return None
    initial=samples[0]['poses']
    maximum=max(math.dist(row['poses'][i][:3],initial[i][:3]) for row in samples for i in indices)
    return {'max_segment_centre_displacement_m':maximum,
            'scope':'30 Hz measured segment-centre displacement from trial start, not tensile force or continuous-time maximum'}
