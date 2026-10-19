"""Declared comparison rubric; callers must separately verify source evidence.

No missing value becomes a pass or zero-cost advantage. Incomplete cohorts
cannot receive reliability scores, and no overall ranking is issued while a
nominally functional design has pending evidence.
"""
import math
from .benchmarking.metrics import wilson


DESIGNS = tuple(a+b for a in 'ABC' for b in 'ABC')
BUILD_ITEMS = ('parts_interfaces', 'assembly_service', 'power_loss_loads')
PHYSICS_ITEMS = ('manipulation_causality', 'transmission', 'cable_contact', 'initial_state_observation')


def integer(value, name, minimum=0):
    if type(value) is not int or value < minimum:
        raise ValueError('Invalid count: '+name)
    return value


def boolean(value, name):
    if type(value) is not bool: raise ValueError('Missing/invalid boolean: '+name)
    return value


def assessment(items, names, allowed):
    if set(items) != set(names): raise ValueError('Missing/extra judgment subitems')
    total = 0
    for name in names:
        row = items[name]
        if type(row['score']) not in (int,float) or row['score'] not in allowed:
            raise ValueError('Invalid judgment score: '+name)
        if not isinstance(row.get('rationale'),str) or not row['rationale'].strip() or not row.get('evidence'):
            raise ValueError('Unjustified judgment: '+name)
        total += row['score']
    return total


def score(row):
    """Score normalized verified observations, retaining explicit pending status."""
    if row['design'] not in DESIGNS: raise ValueError('Unknown design')
    if not isinstance(row.get('environment_manifest_sha256'),str) or len(row['environment_manifest_sha256']) != 64:
        raise ValueError('Missing exact environment identity')
    base = {'design':row['design'],'environment':row['environment'],
            'environment_manifest_sha256':row['environment_manifest_sha256'],
            'total':None,'components':None}
    if not boolean(row['nominal_passed'],'nominal_passed'):
        return dict(base,status='failed_nominal',reason=row.get('failure_reason','Saved nominal task failed'))
    if row.get('pending'):
        return dict(base,status='pending',reason=list(row['pending']))
    b = row['benchmark']
    if not boolean(b['complete'],'benchmark complete') or not boolean(b['control_passed'],'control'):
        return dict(base,status='pending',reason=['Complete declared cohort and passing control required'])
    planned = integer(b['planned'],'planned',1)
    finished = integer(b['finished'],'finished')
    admissible = integer(b['admissible'],'admissible')
    success = integer(b['complete_cycles'],'complete_cycles')
    fixtures = integer(b['fixture_failures'],'fixture_failures')
    if finished != planned or not 0 <= success <= admissible <= planned or fixtures+admissible != planned:
        raise ValueError('Inconsistent terminal cohort counts')
    minimum = 20 if boolean(row['leading_candidate'],'leading_candidate') else 10
    if admissible < minimum:
        return dict(base,status='pending',reason=[f'Needs {minimum} admissible trials; has {admissible}'])
    conditional = wilson(success,admissible); protocol = wilson(success,planned)
    reliability = 45*(.7*conditional[0]+.3*protocol[0])
    occupied = row['occupied']; starts = integer(occupied['starts'],'occupied starts',1)
    clear = integer(occupied['clearance_passes'],'occupied clearance passes')
    if clear > starts: raise ValueError('Impossible occupied-port counts')
    rack = 10*clear/starts+5*boolean(row['workspace_passed'],'workspace')+5*boolean(row['supported_box_passed'],'supported box')
    overhang = row['overhang_m']
    if set(overhang) != {'left_m','right_m','rear_m'}: raise ValueError('Missing overhang axes')
    if any(type(v) not in (int,float) or not math.isfinite(v) or v<0 for v in overhang.values()):
        raise ValueError('Invalid overhang')
    compactness = 10/(1+sum(overhang.values())/.6)
    buildability = assessment(row['buildability'],BUILD_ITEMS,(0,2.5,5))
    physics = assessment(row['physics'],PHYSICS_ITEMS,(0,1,2))
    visual = assessment({'visual':row['visual']},('visual',),(0,1,2))
    components = {'reliability':reliability,'rack_compatibility':rack,'compactness':compactness,
                  'buildability':buildability,'physical_realism':physics,'visual_quality':visual}
    return dict(base,status='scored',total=sum(components.values()),components=components,
                reliability={'complete_cycles':success,'admissible':admissible,'planned':planned,
                    'fixture_failures':fixtures,'conditional_rate':success/admissible,'protocol_rate':success/planned,
                    'conditional_wilson95':conditional,'protocol_wilson95':protocol},
                scope='Declared simulation design rubric, not statistical significance or hardware safety certification')


def compare(rows):
    if len(rows)!=9 or {r['design'] for r in rows}!=set(DESIGNS):
        raise ValueError('Comparison must retain all nine distinct combinations')
    scored = [score(row) for row in rows]
    pending = [row['design'] for row in scored if row['status']=='pending']
    ranks = None
    if not pending:
        eligible = [row for row in scored if row['status']=='scored']
        ranks = {}
        for weight in (35,45,55):
            values = [{'design':row['design'],
                       'total':row['components']['reliability']*weight/45+
                               (row['total']-row['components']['reliability'])*(100-weight)/55}
                      for row in eligible]
            ranks[str(weight)] = sorted(values,key=lambda r:(-r['total'],r['design']))
    winners = {values[0]['design'] for values in ranks.values() if values} if ranks else set()
    return {'schema':'rack_design_comparison_v1','complete_evidence':not pending,'pending_designs':pending,
            'designs':scored,'rankings_by_reliability_weight':ranks,
            'recommendation_preference_sensitive':len(winners)>1 if ranks else None,
            'limits':['Caller must bind and verify exact source observations; scalar scoring does not validate them.',
                      'A final score does not imply all PLAN_p2 deliverables or fabrication readiness.',
                      'Different controller protocols remain distinct; scores do not isolate hardware causality.',
                      'Unknown complete costs or calibrated tension receive no invented numerical values.']}
