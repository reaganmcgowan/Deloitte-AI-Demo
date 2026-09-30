import unittest

from src.investigation import assessment_workspace
from src.retrieval import OfflineExplanationAdapter, explain_with_offline_fallback, retrieve_passages
from src.scenario import Scenario


class RetrievalTests(unittest.TestCase):
    def test_local_retrieval_returns_cited_backup_readiness_source(self):
        rows = retrieve_passages("hospital backup readiness", "C-184", "2026-08-15T13:00:00-07:00")
        self.assertTrue(rows)
        self.assertEqual(rows[0]["source_id"], "FAC-F001-READINESS-20260814-01")
        self.assertEqual(rows[0]["citation"].freshness_status, "stale")
        self.assertIn("backup", rows[0]["matched_terms"])

    def test_retrieval_is_scoped_and_deterministic(self):
        query = "abnormal equipment field confirmation"
        first = retrieve_passages(query, "C-184", "2026-08-15T16:00:00-07:00", True)
        second = retrieve_passages(query, "C-184", "2026-08-15T16:00:00-07:00", True)
        self.assertEqual(first, second)
        self.assertIn("FR-001", [row["source_id"] for row in first])
        self.assertNotIn("F-001", [row["source_id"] for row in first])

    def test_offline_adapter_cites_only_retrieved_sources(self):
        passages = retrieve_passages("procedure backup readiness", "C-184", "2026-08-15T13:00:00-07:00")
        result = explain_with_offline_fallback("Can readiness be verified?", passages)
        self.assertEqual(result["mode"], "offline-template")
        self.assertEqual(result["citations"], [row["source_id"] for row in passages])
        self.assertIsInstance(OfflineExplanationAdapter().explain("x", []), dict)

    def test_workspace_exposes_retrieval_results(self):
        scenario = Scenario()
        workspace = assessment_workspace(scenario.evaluate(), scenario.baseline_tables(), "C-184")
        self.assertTrue(workspace["retrieved_passages"])
        self.assertTrue(all(row["citation"].source_id == row["source_id"] for row in workspace["retrieved_passages"]))
