import unittest

from src.evaluation import evaluation_summary, run_evaluation


class EvaluationTests(unittest.TestCase):
    def test_known_answer_scorecard_passes(self):
        summary = evaluation_summary()
        self.assertTrue(summary["all_passed"], summary)
        self.assertEqual(summary["passed"], summary["total"])

    def test_scorecard_is_reproducible_and_names_checks(self):
        first = run_evaluation()
        second = run_evaluation()
        self.assertEqual(first, second)
        names = {item["check"] for item in first}
        self.assertTrue({"Citation coverage", "Weather-only behavior", "Revision quality"}.issubset(names))
