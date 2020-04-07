from unittest import TestCase

from alfalfa_worker.step_sim.step_sim_utils import valid_date
from datetime import datetime


class TestStepSimUtils(TestCase):
    def test_valid_dates(self):
        self.assertEqual(valid_date('2018-06-15 08:30:45'), datetime(2018, 6, 15, 8, 30, 45))

        date = "invalid-date"
        with self.assertRaises(Exception) as exc:
            valid_date(date)
        self.assertEqual(f"Not a valid date: '{date}'", str(exc.exception))

        date = "06-15-2018"
        with self.assertRaises(Exception) as exc:
            valid_date(date)
        self.assertEqual(f"Not a valid date: '{date}'", str(exc.exception))
