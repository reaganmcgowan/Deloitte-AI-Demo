"""Streamlit interaction tests exercise session behavior and rendered domain evidence."""
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.command_center import (activity_frame, agent_graph_figure, agent_reasoning_frame,
                                geographic_figure, heatmap_figure, network_figure)
from src.investigation import assessment_revision, assessment_workspace
from src.ontology import DataQualityError
from src.scenario import Scenario

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def reach_next_checkpoint(app):
    """Drive the real UI callbacks with injected elapsed time; no test sleeps."""
    app.button(key="resume_playback").click().run()
    app.session_state["playback"].last_tick -= 100
    app.run()
    return app


class CommandCenterTests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(APP, default_timeout=20).run()

    def metrics(self, app):
        return {metric.label: metric.value for metric in app.metric}

    def test_baseline_empty_queue_and_rerun_do_not_advance(self):
        app = self.app()
        self.assertFalse(app.exception)
        self.assertEqual(self.metrics(app)["Open investigations"], "3")
        self.assertEqual(self.metrics(app)["Cases awaiting review"], "1")
        self.assertEqual(self.metrics(app)["Unresolved information requests"], "2")
        run = app.session_state["scenario"].run_id
        app.selectbox(key="investigation_case").select("C-186").run()
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state["scenario"].stage, 1)
        self.assertEqual(app.session_state["scenario"].run_id, run)
        self.assertTrue(any("Evidence · C-186" in item.value for item in app.subheader))

    def test_continue_from_two_pm_checkpoint_renders_without_exception(self):
        app = self.app()
        # Put the real session at the first automatic pause, then click the same
        # Continue control used in the browser. This targets the reported failure.
        app.session_state["scenario"].seek(60)
        app.session_state["playback"].seek(60)
        app.session_state["stage_reports"] = {1: app.session_state["scenario"].seek(0),
                                                2: app.session_state["scenario"].seek(60)}
        app.session_state["report"] = app.session_state["stage_reports"][2]
        app.session_state["tables"] = app.session_state["scenario"].snapshot()
        app.session_state["sample_minute"] = 60
        app.run()
        self.assertEqual(app.session_state["scenario"].stage, 2)
        app.button(key="resume_playback").click().run()
        self.assertFalse(app.exception)
        self.assertIn(app.session_state["scenario"].stage, (2, 3))

    def test_agent_graph_exposes_inputs_reasoning_and_outputs(self):
        report = Scenario().evaluate()
        findings = report["findings"]["C-184"]
        figure = agent_graph_figure(findings, "C-184")
        labels = list(figure.data[0].node.label)
        self.assertIn("Grid Reliability", labels)
        self.assertIn("Wildfire Risk", labels)
        self.assertIn("Recommendation", labels)
        frame = agent_reasoning_frame(findings)
        self.assertEqual(frame["Agent"].tolist(), ["Grid Reliability", "Wildfire Risk", "Impact", "Response"])
        self.assertIn("energized anomaly", frame.iloc[1]["Reasoning"])
        self.assertEqual(list(figure.data[0].node.x), [0.02] * 5 + [0.34] * 4 + [0.72] * 4)
        self.assertEqual(figure.layout.height, 620)

    def test_assessment_workspace_binds_evidence_unknowns_and_options_to_version(self):
        scenario = Scenario()
        report = scenario.evaluate()
        workspace = assessment_workspace(report, scenario.baseline_tables(), "C-184", version=3)
        self.assertEqual(workspace["assessment_version"], 3)
        self.assertEqual(workspace["impact"]["customers"], 8420)
        self.assertEqual(workspace["impact"]["critical_facilities"], ["F-001"])
        self.assertEqual(len(workspace["unknowns"]), 2)
        self.assertEqual(len(workspace["options"]), 5)
        self.assertIn("no PSPS authorization", workspace["decision_gate"])
        self.assertTrue(any(row["source_id"] == "FAC-F001-READINESS-20260814-01" for row in workspace["evidence"]))
        self.assertFalse(workspace["evidence_quality"]["ready_for_decision"])

    def test_evidence_files_tab_inspects_selected_source_record(self):
        app = self.app()
        source_picker = app.selectbox(key="evidence_source_C-184")
        self.assertIn("Hospital readiness record", source_picker.options)
        source_picker.select("Hospital readiness record").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("No current hospital backup-power readiness verification" in item.value
                            for item in app.info))

    def test_field_report_revision_changes_assessment_and_preserves_unknown(self):
        revision = assessment_revision(True, 2, "2026-08-15T16:00:00-07:00")
        self.assertEqual(revision["version"], 2)
        self.assertIn("visible equipment damage", revision["what_changed"])
        self.assertIn("backup-power readiness", revision["still_unresolved"])
        initial = assessment_revision(False, 1, "2026-08-15T13:00:00-07:00")
        self.assertNotEqual(initial["assessment_change"], revision["assessment_change"])

    def test_final_kpis_queue_selection_and_reset_twice(self):
        app = self.app()
        for replay in range(2):
            original_run = app.session_state["scenario"].run_id
            reach_next_checkpoint(app)
            original_selection = app.selectbox(key="investigation_case").value
            for _ in range(3):
                reach_next_checkpoint(app)
            self.assertFalse(app.exception)
            self.assertEqual(app.selectbox(key="investigation_case").value, original_selection)
            self.assertEqual(self.metrics(app)["Open investigations"], "3")
            self.assertEqual(self.metrics(app)["Cases awaiting review"], "2")
            self.assertEqual(self.metrics(app)["Unresolved information requests"], "2")
            self.assertTrue(app.session_state["playback"].finished)
            self.assertNotIn("resume_playback", [button.key for button in app.button])
            self.assertEqual(app.dataframe[0].value.iloc[0]["Incident"], "Circuit 184: equipment anomaly + fire weather")
            app.button(key="introduce_field_report").click().run()
            self.assertTrue(app.session_state["field_report"])
            self.assertEqual(app.session_state["assessment_version"], 2)
            app.button(key="introduce_field_report").click().run()
            self.assertEqual(app.session_state["assessment_version"], 2)
            self.assertEqual(len(app.session_state["assessment_history"]), 2)
            self.assertTrue(any("FR-001" in item.value for item in app.success))
            app.button(key="decision_C-184_0").click().run()
            self.assertEqual(app.session_state["decision_log"][0]["action"], "Request missing information")
            self.assertEqual(app.session_state["decision_log"][0]["operational_effect"], "None; preparation/review workflow only")
            self.assertTrue(app.session_state["decision_log"][0]["evidence_ids"])
            self.assertEqual(app.session_state["scenario"].stage, 5)
            app.button(key="reset_scenario").click().run()
            self.assertEqual(app.session_state["scenario"].stage, 1)
            self.assertNotEqual(app.session_state["scenario"].run_id, original_run)
            self.assertEqual(self.metrics(app)["Open investigations"], "3")
            self.assertEqual(app.button(key="resume_playback").label, "Start day")

    def test_missing_data_shows_error_instead_of_reassuring_metrics(self):
        with patch("src.scenario.load_data", side_effect=DataQualityError("Missing assets.csv")):
            app = self.app()
        self.assertFalse(app.exception)
        self.assertIn("Missing assets.csv", app.error[0].value)
        self.assertEqual(len(app.metric), 0)

    def test_network_contains_all_assets_and_critical_hero(self):
        scenario = Scenario()
        for _ in range(4):
            scenario.advance()
        figure = network_figure(scenario.evaluate(), scenario.snapshot(), "C-184")
        node_traces = [trace for trace in figure.data if trace.mode == "markers+text"]
        labels = [label for trace in node_traces for label in trace.text]
        self.assertEqual(len(labels), 24)
        self.assertEqual(len(set(labels)), 24)
        critical = next(trace for trace in node_traces if trace.name == "Critical")
        self.assertIn("C-184", critical.text)
        self.assertIn("T-882", critical.text)
        self.assertNotIn("C-187", critical.text)  # Shared weather alone does not turn the circuit red.


class MapAndActivityTests(unittest.TestCase):
    def test_future_stages_blank_and_final_scores_match(self):
        scenario = Scenario()
        reports = [scenario.evaluate()]
        figure = heatmap_figure(reports, "Combined electrical / wildfire")
        self.assertEqual(list(figure.data[0].z[0]), [0, None, None, None, None])
        reports.extend(scenario.advance() for _ in range(4))
        figure = heatmap_figure(reports, "Combined electrical / wildfire")
        self.assertAlmostEqual(figure.data[0].z[0][-1], 88.44)
        self.assertEqual(figure.data[0].z[3][-1], 0)  # Shared weather, no anomaly.

    def test_geography_uses_fixture_coordinates_and_selected_risk(self):
        scenario = Scenario()
        for _ in range(4):
            scenario.advance()
        figure = geographic_figure(scenario.evaluate(), scenario.snapshot(), "Environmental exposure")
        self.assertEqual(figure.layout.map.style, "white-bg")
        self.assertEqual(len(figure.data[0].lat), 6)
        self.assertAlmostEqual(figure.data[0].lat[0], 34.39)
        self.assertAlmostEqual(figure.data[0].lon[0], -118.54)
        self.assertAlmostEqual(figure.data[0].marker.color[0], 90.2)
        self.assertEqual(len(figure.data[1].lat), 3)

    def test_ui_history_deduplicates_and_reset_clears(self):
        app = AppTest.from_file(APP, default_timeout=20).run()
        reach_next_checkpoint(app)
        app.selectbox(key="risk_layer").select("Environmental exposure").run()
        app.run()
        history = list(app.session_state["stage_reports"].values())
        self.assertEqual(len(history), 2)
        self.assertEqual(len(activity_frame(history, "C-184")), 8)
        self.assertIn("proposed only", activity_frame(history, "C-184").iloc[3]["Result"])
        self.assertEqual(app.session_state["scenario"].stage, 2)
        app.button(key="reset_scenario").click().run()
        self.assertEqual(len(app.session_state["stage_reports"]), 1)
        self.assertFalse(app.exception)
