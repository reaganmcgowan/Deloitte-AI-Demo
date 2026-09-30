import unittest

from src.decision_workflow import ALLOWED_DECISION_ACTIONS, append_decision


class DecisionWorkflowTests(unittest.TestCase):
    def test_decision_records_evidence_version_rationale_and_no_effect(self):
        log = []
        append_decision(log, action="Approve proposed next step", case_id="C-184",
                        assessment_version=2, evidence_ids=["FR-001", "FR-001", "PROC-7.2-20260815-01"],
                        rationale="Prepare the review brief for the authorized operator.",
                        timestamp="2026-08-15T16:00:00-07:00")
        self.assertEqual(len(log), 1)
        self.assertEqual(log[0]["evidence_ids"], ["FR-001", "PROC-7.2-20260815-01"])
        self.assertEqual(log[0]["assessment_version"], 2)
        self.assertEqual(log[0]["operational_effect"], "None; preparation/review workflow only")

    def test_duplicate_click_is_idempotent(self):
        log = []
        kwargs = dict(action="Request missing information", case_id="C-184", assessment_version=1,
                      evidence_ids=["FAC-F001-READINESS-20260814-01"], rationale="Verify backup readiness.",
                      timestamp="2026-08-15T13:00:00-07:00")
        append_decision(log, **kwargs)
        append_decision(log, **kwargs)
        self.assertEqual(len(log), 1)

    def test_only_named_review_actions_are_allowed(self):
        self.assertIn("Reject proposed next step", ALLOWED_DECISION_ACTIONS)
        with self.assertRaises(ValueError):
            append_decision([], action="De-energize circuit", case_id="C-184", assessment_version=1,
                            evidence_ids=[], rationale="", timestamp="now")
