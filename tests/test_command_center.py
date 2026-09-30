"""Streamlit interaction tests exercise session behavior and rendered domain evidence."""
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.command_center import (activity_frame, agent_graph_figure, agent_reasoning_frame,
                                geographic_figure, heatmap_figure, network_figure)
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
            self.assertTrue(any("FR-001" in item.value for item in app.success))
            app.button(key="decision_C-184_0").click().run()
            self.assertEqual(app.session_state["decision_log"][0]["action"], "Request missing information")
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
