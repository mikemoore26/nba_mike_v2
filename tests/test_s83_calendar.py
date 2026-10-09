import csv
import importlib.util
import tempfile
import unittest
from datetime import date
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'research/p0_s8/s8_3/run_s8_3.py'
spec = importlib.util.spec_from_file_location('s83', SOURCE)
s83 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s83)


class CalendarTests(unittest.TestCase):
    def test_bubble_start(self):
        self.assertEqual(s83.classify('2019-20', date(2020, 7, 30)), 'BUBBLE_RESTART_CANDIDATE_UNVERIFIED')

    def test_bubble_end(self):
        self.assertEqual(s83.classify('2019-20', date(2020, 8, 14)), 'BUBBLE_RESTART_CANDIDATE_UNVERIFIED')

    def test_july_early_unverified(self):
        self.assertEqual(s83.classify('2019-20', date(2020, 7, 20)), 'JULY_PRE_RESTART_REQUIRES_REVIEW')

    def test_post_restart(self):
        self.assertEqual(s83.classify('2019-20', date(2020, 8, 15)), 'OUTSIDE_RESEARCH_WINDOW_REQUIRES_REVIEW')

    def test_regular_season(self):
        self.assertEqual(s83.classify('2019-20', date(2020, 1, 1)), 'IN_RESEARCH_WINDOW_NOT_SCHEDULE_VERIFIED')

    def test_invalid_date(self):
        self.assertEqual(s83.classify('2019-20', None), 'INVALID_DATE')

    def test_2023_date(self):
        self.assertEqual(s83.classify('2023-24', date(2024, 4, 14)), 'IN_RESEARCH_WINDOW_NOT_SCHEDULE_VERIFIED')

    def test_2025_date(self):
        self.assertEqual(s83.classify('2025-26', date(2026, 4, 12)), 'IN_RESEARCH_WINDOW_NOT_SCHEDULE_VERIFIED')

    def test_outside_2023(self):
        self.assertEqual(s83.classify('2023-24', date(2024, 4, 15)), 'OUTSIDE_RESEARCH_WINDOW_REQUIRES_REVIEW')

    def test_date_parser(self):
        self.assertEqual(s83.parse_iso_date('2020-08-01'), date(2020, 8, 1))

    def test_bad_date(self):
        self.assertIsNone(s83.parse_iso_date('nonsense'))

    def test_synthetic_end_to_end(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base = root / 'research/p0_s4/s5_1/snapshots'
            base.mkdir(parents=True)
            for season in s83.SEASONS:
                with (base / f'player_gamelogs_{season}.csv').open('w', newline='') as fh:
                    w = csv.DictWriter(fh, fieldnames=['game_id', 'event_date', 'player_id'])
                    w.writeheader()
                    dt = '2020-08-01' if season == '2019-20' else '2024-01-01' if season == '2023-24' else '2026-01-01'
                    w.writerow({'game_id': '1', 'event_date': dt, 'player_id': '42'})
                    w.writerow({'game_id': '1', 'event_date': dt, 'player_id': '43'})
            out = root / 'results'
            r = s83.run(root, out)
            self.assertEqual(r['s8_2_flagged_rows_observed'], 2)
            self.assertFalse(r['s8_2_flag_count_matches'])
            self.assertEqual(r['datasets'][0]['unique_games'], 1)
            self.assertEqual(r['2019_20_unresolved_calendar_rows'], 0)
            self.assertFalse(r['training_eligible'])
            self.assertTrue((out / 's8_3_game_calendar_review.csv').exists())

    def test_conflicting_dates_and_duplicate(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'a.csv'
            with path.open('w', newline='') as fh:
                w = csv.DictWriter(fh, fieldnames=['game_id', 'event_date', 'player_id'])
                w.writeheader()
                for d in ['2020-08-01', '2020-08-02']:
                    w.writerow({'game_id': '1', 'event_date': d, 'player_id': '42'})
            rows = []
            result = s83.inspect(path, '2019-20', rows)
            self.assertEqual(result['date_game_conflicts'], 1)
            self.assertEqual(result['duplicate_player_game'], 1)

    def test_missing_file(self):
        result = s83.inspect(Path('/does/not/exist.csv'), '2019-20', [])
        self.assertEqual(result['read_error'], 'MISSING_FILE')

    def test_no_training_promotion(self):
        self.assertIn('UNVERIFIED', s83.classify('2019-20', date(2020, 8, 1)))


if __name__ == '__main__':
    unittest.main()
