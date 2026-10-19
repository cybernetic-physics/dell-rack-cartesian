import copy
import unittest
from rack_robotics.comparison import score, compare, DESIGNS, BUILD_ITEMS, PHYSICS_ITEMS


def observation(design='AA'):
    def judgment(value): return {'score':value,'rationale':'Explicit modeled limitation','evidence':['report.json']}
    return {'design':design,'environment':'saved/'+design,'environment_manifest_sha256':'a'*64,
        'nominal_passed':True,'leading_candidate':True,
        'benchmark':{'complete':True,'control_passed':True,'planned':24,'finished':24,
                     'admissible':22,'complete_cycles':22,'fixture_failures':2},
        'occupied':{'starts':5,'clearance_passes':4},'workspace_passed':True,'supported_box_passed':True,
        'overhang_m':{'left_m':.054,'right_m':.0542,'rear_m':.3452},
        'buildability':{n:judgment(2.5) for n in BUILD_ITEMS},
        'physics':{n:judgment(1) for n in PHYSICS_ITEMS},'visual':judgment(1)}


class ComparisonTest(unittest.TestCase):
    def test_formula_and_fixture_denominator(self):
        r=score(observation()); self.assertEqual(r['status'],'scored')
        self.assertEqual(r['components']['rack_compatibility'],18)
        self.assertAlmostEqual(r['components']['compactness'],10/(1+.4534/.6))
        self.assertEqual(r['reliability']['conditional_rate'],1)
        self.assertAlmostEqual(r['reliability']['protocol_rate'],22/24)
        self.assertLess(r['components']['reliability'],45)

    def test_incomplete_or_failed_control_cannot_score(self):
        for key in ('complete','control_passed'):
            r=observation();r['benchmark'][key]=False
            self.assertEqual(score(r)['status'],'pending')

    def test_valid_trial_minimum_not_declared_starts(self):
        r=observation();r['benchmark'].update(admissible=19,complete_cycles=19,fixture_failures=5)
        self.assertEqual(score(r)['status'],'pending')
        r['leading_candidate']=False
        self.assertEqual(score(r)['status'],'scored')

    def test_missing_evidence_never_becomes_a_pass(self):
        r=observation();r['pending']=['No workspace report']
        self.assertEqual(score(r)['status'],'pending')
        r=observation();r['workspace_passed']=None
        with self.assertRaises(ValueError):score(r)
        r=observation();r['visual']['evidence']=[]
        with self.assertRaises(ValueError):score(r)

    def test_bad_counts_or_nonfinite_dimensions_rejected(self):
        for update in ({'admissible':25},{'finished':23},{'complete_cycles':23},{'fixture_failures':0}):
            r=observation();r['benchmark'].update(update)
            with self.assertRaises(ValueError):score(r)
        for v in (float('nan'),float('inf'),-.1):
            r=observation();r['overhang_m']['rear_m']=v
            with self.assertRaises(ValueError):score(r)

    def test_failed_design_preserved_but_not_ranked(self):
        rows=[observation(d) for d in DESIGNS];rows[-1]['nominal_passed']=False
        r=compare(rows)
        self.assertEqual(r['designs'][-1]['status'],'failed_nominal')
        self.assertNotIn('CC',[v['design'] for v in r['rankings_by_reliability_weight']['45']])

    def test_no_partial_ranking_and_no_omitted_designs(self):
        rows=[observation(d) for d in DESIGNS];rows[4]['pending']=['Cohort running']
        r=compare(rows);self.assertFalse(r['complete_evidence']);self.assertIsNone(r['rankings_by_reliability_weight'])
        with self.assertRaises(ValueError):compare(rows[:-1])
        with self.assertRaises(ValueError):compare(rows[:-1]+[copy.deepcopy(rows[0])])

    def test_sensitivity_preserves_declared_total_at45(self):
        rows=[observation(d) for d in DESIGNS];r=compare(rows)
        self.assertEqual(set(r['rankings_by_reliability_weight']),{'35','45','55'})
        self.assertAlmostEqual(r['rankings_by_reliability_weight']['45'][0]['total'],r['designs'][0]['total'])
        self.assertFalse(r['recommendation_preference_sensitive'])


if __name__=='__main__':unittest.main()
