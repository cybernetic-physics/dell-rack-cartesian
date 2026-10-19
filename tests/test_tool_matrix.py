import json
from pathlib import Path
import tempfile
import unittest
from rack_robotics.scripts.run_tool_matrix import select_designs,build_arguments,result_summary,DEFAULT_DESIGNS


class ToolMatrixTest(unittest.TestCase):
    def test_labels_and_default_coverage(self):
        self.assertEqual(set(select_designs(DEFAULT_DESIGNS)),{'AC','BC','CC','AB','BB','CB'})
        for text in ('','AA,AA','../AA','AD','AA,','A','AAA'):
            with self.assertRaises(ValueError):select_designs(text)

    def test_frame_and_tool_specific_flags(self):
        for robot,flag in [('A','--open-screw-frame'),('B','--open-telescoping-frame'),('C','--open-gantry-frame')]:
            for tool in 'ABC':
                args=build_arguments(robot+tool,480)
                self.assertIn(flag,args)
                self.assertEqual('--forward-latch-neck' in args,tool=='A')
                self.assertIn('--cable-clearance-front-support',args)
                self.assertNotIn('--minimal',args)
        with self.assertRaises(ValueError):build_arguments('AA',123)
        with self.assertRaises(ValueError):build_arguments('AA,BA',480)

    def test_outcomes_do_not_promote_missing_or_partial_results(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'results.json'
            self.assertEqual(result_summary(path)['outcome'],'runtime_error')
            path.write_text(json.dumps({'passed':True}))
            self.assertEqual(result_summary(path)['outcome'],'failed')
            result={'passed':True,'initial_retained_without_hand':True,'unplug_success':True,
                    'replug_success':True,'scope':'full_rack','topology_audit':{'passed':True}}
            path.write_text(json.dumps(result));self.assertEqual(result_summary(path)['outcome'],'passed')
            result['passed']=False;path.write_text(json.dumps(result))
            self.assertEqual(result_summary(path)['outcome'],'failed')
