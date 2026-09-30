import unittest

from src.evidence import sources_for_circuit
from src.evidence_quality import check_evidence_quality


class EvidenceQualityTests(unittest.TestCase):
    def test_baseline_flags_stale_backup_readiness_without_inventing_contradiction(self):
        quality = check_evidence_quality("C-184", "2026-08-15T13:00:00-07:00")
        self.assertFalse(quality["ready_for_decision"])
        self.assertEqual(quality["contradictions"], [])
        self.assertIn("FAC-F001-READINESS-20260814-01", [row["source_id"] for row in quality["stale_sources"]])

    def test_conflicting_readiness_records_are_flagged_with_owner_and_sources(self):
        conflicting = {
            "source_id": "FAC-F001-READINESS-20260815-02",
            "source_type": "facility_readiness_record",
            "owner": "Facility liaison",
            "timestamp": "2026-08-15T12:30:00-07:00",
            "freshness_status": "current",
            "freshness_window": "1 day",
            "text": "Generator tested successfully; readiness verified.",
        }
        quality = check_evidence_quality("C-184", "2026-08-15T13:00:00-07:00", additional_sources=[conflicting])
        self.assertEqual(len(quality["contradictions"]), 1)
        conflict = quality["contradictions"][0]
        self.assertEqual(conflict["owner"], "Facility liaison")
        self.assertIn("FAC-F001-READINESS-20260815-02", conflict["source_ids"])

    def test_field_report_does_not_clear_unrelated_stale_readiness(self):
        quality = check_evidence_quality("C-184", "2026-08-15T16:00:00-07:00", field_report=True)
        self.assertIn("FAC-F001-READINESS-20260814-01", [row["source_id"] for row in quality["stale_sources"]])
        self.assertEqual(len(sources_for_circuit("C-184", "2026-08-15T16:00:00-07:00", True)), 4)
