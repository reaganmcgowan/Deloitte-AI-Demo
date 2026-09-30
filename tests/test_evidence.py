import unittest

from src.evidence import DEMO_FRESHNESS_WINDOWS, freshness, source_registry, sources_for_circuit
from src.investigation import evidence_records
from src.scenario import Scenario


class EvidenceTests(unittest.TestCase):
    def test_registry_has_stable_owned_sources_and_fixed_windows(self):
        sources = source_registry()
        ids = [source["source_id"] for source in sources]
        self.assertEqual(ids, ["MAINT-T882-20260814-01", "FAC-F001-READINESS-20260814-01", "PROC-7.2-20260815-01"])
        self.assertTrue(all(source["owner"] for source in sources))
        self.assertEqual(DEMO_FRESHNESS_WINDOWS["maintenance"].days, 30)
        self.assertEqual(DEMO_FRESHNESS_WINDOWS["critical_facility_backup"].total_seconds(), 24 * 3600)

    def test_backup_readiness_is_explicitly_stale_and_field_report_is_opt_in(self):
        records = sources_for_circuit("C-184", "2026-08-15T16:00:00-07:00")
        readiness = next(record for record in records if record["source_id"].startswith("FAC-"))
        self.assertEqual(readiness["freshness_status"], "stale")
        self.assertNotIn("FR-001", [record["source_id"] for record in records])
        with_report = sources_for_circuit("C-184", "2026-08-15T16:00:00-07:00", True)
        self.assertIn("FR-001", [record["source_id"] for record in with_report])

    def test_workspace_rows_expose_provenance_and_freshness(self):
        report = Scenario().evaluate()
        rows = evidence_records(report, Scenario().baseline_tables(), "C-184")
        self.assertTrue(all(row.get("source_id") and row.get("owner") for row in rows))
        self.assertTrue(any(row["source_id"] == "MAINT-T882-20260814-01" for row in rows))
        self.assertTrue(any(row["freshness_status"] == "stale" for row in rows))

    def test_freshness_is_deterministic(self):
        source = source_registry()[0]
        first = freshness(source, "2026-08-15T16:00:00-07:00")
        second = freshness(source, "2026-08-15T16:00:00-07:00")
        self.assertEqual(first, second)
