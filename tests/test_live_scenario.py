import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from src.data_generator import generate_data
from src.live_scenario import LiveScenario, continuous_tables, demand_drivers
from src.playback import CHECKPOINT_MINUTES, Playback
from src.scenario import stage_tables
from src.ontology import DataQualityError


class ContinuousTests(unittest.TestCase):
    def test_checkpoints_preserve_original_fixture_values(self):
        baseline = generate_data()
        for stage, minute in enumerate(CHECKPOINT_MINUTES, 1):
            actual = continuous_tables(baseline, minute)
            expected = stage_tables(baseline, stage)
            for name in actual:
                pd.testing.assert_frame_equal(actual[name], expected[name])

    def test_midpoint_changes_load_and_weather_gradually(self):
        baseline = generate_data()
        middle = continuous_tables(baseline, 30)
        self.assertAlmostEqual(middle['circuits'].iloc[0].current_load_mw, 20.94)
        self.assertAlmostEqual(middle['weather'].iloc[0].ambient_temperature_f, 91)
        self.assertAlmostEqual(middle['assets'].iloc[0].temperature_f, 101.3)
        next_minute = continuous_tables(baseline, 31)
        self.assertLess(next_minute['circuits'].iloc[0].current_load_mw - middle['circuits'].iloc[0].current_load_mw, .2)

    def test_fault_is_sudden_and_does_not_leak_into_earlier_time(self):
        scenario = LiveScenario()
        before = scenario.seek(179)
        self.assertEqual(before['findings']['C-184']['grid']['anomaly_asset_ids'], [])
        self.assertEqual(before['findings']['C-184']['wildfire']['combined']['score'], 0)
        temperature = scenario.snapshot()['assets'].iloc[0].temperature_f
        final = scenario.seek(180)
        self.assertEqual(final['findings']['C-184']['grid']['anomaly_asset_ids'], ['T-882'])
        self.assertGreater(scenario.snapshot()['assets'].iloc[0].temperature_f-temperature, 45)
        self.assertAlmostEqual(final['findings']['C-184']['wildfire']['combined']['score'], 88.44)
        self.assertEqual(final['total_impact']['customers_at_risk'], 8420)
        self.assertEqual(len(final['total_impact']['critical_facilities']), 1)

    def test_demand_explanation_reconciles_to_load(self):
        baseline = generate_data()
        for minute in (0,30,90,165,180):
            tables = continuous_tables(baseline, minute)
            for circuit in tables['circuits'].itertuples():
                drivers = demand_drivers(baseline, tables, circuit.circuit_id)
                self.assertAlmostEqual(sum(drivers.values()), circuit.current_load_mw)
                self.assertTrue(all(value >= 0 for value in drivers.values()))
                if circuit.circuit_id != 'C-184':
                    self.assertEqual(drivers['Afternoon event'], 0)

    def test_seek_backward_clears_future_incidents_and_updates_timestamp(self):
        scenario = LiveScenario()
        scenario.seek(180)
        run = scenario.run_id
        report = scenario.seek(30)
        self.assertNotEqual(run, scenario.run_id)
        self.assertEqual(report['timestamp'], '2026-08-15T13:30:00-07:00')
        self.assertEqual(report['incidents'], [])
        self.assertEqual(report['findings']['C-184']['wildfire']['evidence']['timestamp'], report['timestamp'])
        for bad in (-1,181,float('nan')):
            with self.assertRaises(DataQualityError):
                scenario.seek(bad)

    def test_slider_and_speed_update_ui_without_future_history(self):
        app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
        self.assertEqual(Playback().minutes_per_second, 6)
        app.slider(key='time_slider').set_value(90).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['scenario'].minute, 90)
        metrics = {m.label:m.value for m in app.metric}
        self.assertEqual(metrics['Demand'], '26.40 MW')
        app.select_slider(key='speed').set_value(12).run()
        self.assertEqual(app.session_state['playback'].minutes_per_second, 12)
        app.slider(key='time_slider').set_value(180).run()
        self.assertEqual(app.session_state['report']['total_impact']['customers_at_risk'], 8420)
        app.slider(key='time_slider').set_value(30).run()
        self.assertEqual(len(app.session_state['stage_reports']), 1)
        self.assertEqual(app.session_state['report']['incidents'], [])
        self.assertFalse(app.exception)
