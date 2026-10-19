"""Pool disjoint randomized campaigns only under identical frozen protocols."""
from .metrics import wilson


def pool_campaigns(bundles):
    if not bundles:
        raise ValueError('At least one campaign is required')
    harness = bundles[0]['manifest']['harness_sha256']
    if not harness:
        raise ValueError('Missing frozen harness identity')
    identities, cases, rows, controls, campaigns = {}, {}, {}, {}, []
    for bundle in bundles:
        summary, manifest, plan = (bundle[k] for k in ('summary', 'manifest', 'plan'))
        name = summary['campaign_directory']
        if name in campaigns:
            raise ValueError(f'Duplicate campaign: {name}')
        campaigns.append(name)
        if not summary['evidence_hashes_valid'] or summary['errors']:
            raise ValueError(f'Invalid campaign evidence: {name}')
        if manifest['harness_sha256'] != harness:
            raise ValueError(f'Different frozen protocol: {name}')
        for design in manifest['designs']:
            identity = plan['environments'][design]
            if design in identities and identities[design] != identity:
                raise ValueError(f'Different environment for {design}')
            identities[design] = identity
            cases.setdefault(design, {})
            rows.setdefault(design, [])
            controls.setdefault(design, []).append({
                'campaign': name, 'passed': bool(summary['controls'].get(design, {}).get('complete_cycle'))})
            by_name = {}
            for condition_name, condition in bundle['conditions'].items():
                if condition.get('role') != 'randomized':
                    raise ValueError('Controls must not enter randomized conditions')
                key = (condition['seed'], condition['index'])
                if key in cases[design]:
                    raise ValueError(f'Duplicate randomized condition for {design}: {key}')
                cases[design][key] = {'campaign': name, 'condition': condition_name}
                by_name[condition_name] = key
            if len(by_name) != plan['count_per_environment']:
                raise ValueError(f'Missing predeclared conditions: {name}')
            seen = set()
            for observation in summary['trials']:
                if observation['design'] != design:
                    continue
                condition_name = observation['condition']
                if condition_name not in by_name or condition_name in seen:
                    raise ValueError(f'Unexpected/duplicate trial observation: {design}/{condition_name}')
                seen.add(condition_name)
                seed, index = by_name[condition_name]
                if observation['complete_cycle'] and not observation['admissible_initial_state']:
                    raise ValueError('An inadmissible start cannot count as a complete cycle')
                rows[design].append(dict(observation, campaign=name, seed=seed, index=index))

    designs = {}
    for design, observations in rows.items():
        valid = [r for r in observations if r['admissible_initial_state']]
        successes = sum(r['complete_cycle'] for r in valid)
        finished = len(observations) == len(cases[design]) and all(c['passed'] for c in controls[design])
        ready = finished and len(valid) >= 10
        times = [r['cycle_time_s'] for r in valid if r['complete_cycle'] and r['cycle_time_s'] is not None]
        seen = {(r['seed'], r['index']) for r in observations}
        designs[design] = {
            'environment': identities[design], 'planned': len(cases[design]),
            'finished': len(observations), 'admissible_manipulation_trials': len(valid),
            'fixture_failures': sum(r['fixture_failure'] for r in observations),
            'complete_cycles': successes, 'complete': finished,
            'unplug_successes': sum(r['unplug_success'] for r in valid),
            'replug_successes': sum(r['replug_success'] for r in valid),
            'minimum_ten_valid_trials_met': finished and len(valid) >= 10,
            'minimum_twenty_valid_trials_met': finished and len(valid) >= 20,
            'complete_cycle_rate': successes / len(valid) if ready else None,
            'wilson_95_interval': wilson(successes, len(valid)) if ready else None,
            'protocol_success_rate_including_fixture': successes / len(observations) if finished and observations else None,
            'mean_successful_cycle_s': sum(times) / len(times) if times else None,
            'missing': [dict(value, seed=key[0], index=key[1])
                        for key, value in cases[design].items() if key not in seen],
            'controls': controls[design],
            'port_counts': {str(port): {
                'trials': sum(r['port'] == port for r in observations),
                'admissible': sum(r['port'] == port for r in valid),
                'complete_cycles': sum(r['port'] == port and r['complete_cycle'] for r in valid)}
                for port in sorted({r['port'] for r in observations})}}
    return {'schema': 'rack_benchmark_pool_v1', 'campaigns': campaigns,
            'harness_sha256': harness, 'designs': designs,
            'trials': [r for design_rows in rows.values() for r in design_rows],
            'ranking': None,
            'limitations': [
                'Controls are excluded; failed starts are retained but do not satisfy valid-trial minimums.',
                'Rates are withheld until all declared conditions finish and at least ten starts are admissible.',
                'Identical frozen simulator protocols do not establish hardware reliability or calibration.',
                'Final ranking also requires rack compatibility, loads, buildability and visual evidence.']}
