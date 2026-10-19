import json
from pathlib import Path
import tempfile
import unittest

from rack_robotics.scripts.summarize_cable_force import compare_trajectory, exposure


class CableForceSummaryTests(unittest.TestCase):
    def test_duration_separates_nonconsecutive_transients(self):
        rows = [{'axial_force_n': [v, -.3]} for v in (0., 6., 6., 0., 6., 5.)]
        stats = exposure(rows, .002)
        self.assertEqual(stats['5.0']['steps'], 3)
        self.assertEqual(stats['5.0']['longest_consecutive_steps'], 2)
        self.assertEqual(stats['5.0']['total_duration_s'], .006)
        self.assertEqual(stats['10.0']['steps'], 0)

    def test_exact_first_cycle_and_reject_missing_or_changed_frame(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / 'a', Path(folder) / 'b'
            header = {'format': 'test', 'fps': 30, 'body_paths': ['body']}
            rows = [{'time': i, 'phase': 'test', 'poses': [i]} for i in range(4)]
            def write(path, records):
                path.write_text('\n'.join(json.dumps(r) for r in [header] + records) + '\n')
            write(a, rows[:3]); write(b, rows)
            self.assertEqual(compare_trajectory(a, b, 2)['equal_recorded_frames'], 3)
            write(a, rows[:2])
            with self.assertRaises(ValueError): compare_trajectory(a, b, 2)
            write(a, [rows[0], dict(rows[1], poses=[9]), rows[2]])
            with self.assertRaises(ValueError): compare_trajectory(a, b, 2)


if __name__ == '__main__':
    unittest.main()
