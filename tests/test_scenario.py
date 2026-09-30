import json
import unittest

import pandas as pd

from src.data_generator import generate_data
from src.ontology import DataQualityError, GridModel
from src.scenario import Scenario, stage_tables


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        self.baseline = generate_data()
        self.scenario = Scenario(self.baseline)

    def reports(self):
        return [self.scenario.evaluate()] + [self.scenario.advance() for _ in range(4)]

    def test_baseline_and_exact_main_incident_timing(self):
        reports = self.reports()
        self.assertEqual(reports[0]["incidents"], [])
        for report in reports[:4]:
            self.assertFalse(any(incident["severity"] == "CRITICAL" for incident in report["incidents"]))
            self.assertEqual(report["findings"]["C-184"]["grid"]["anomaly_asset_ids"], [])
        final = reports[-1]
        main = next(incident for incident in final["incidents"] if incident["category"] == "combined_wildfire")
        self.assertEqual(main["severity"], "CRITICAL")
        self.assertEqual(main["circuit_id"], "C-184")
        self.assertEqual(main["affected_asset_ids"], ["T-882"])
        self.assertEqual(main["first_detected_stage"], 5)
        self.assertEqual(main["impact"]["customers_at_risk"], 8420)
        self.assertEqual([facility["facility_type"] for facility in main["impact"]["critical_facilities"]], ["hospital"])
        self.assertEqual(final["incidents"][0]["incident_id"], main["incident_id"])

    def test_stage_four_weather_is_separate_and_other_zone_assets_stay_normal(self):
        reports = self.reports()
        hero = reports[3]["findings"]["C-184"]["wildfire"]
        self.assertTrue(hero["dangerous_weather"])
        self.assertGreater(hero["environment"]["score"], 60)
        self.assertFalse(hero["electrical_anomaly"])
        self.assertEqual(hero["combined"]["score"], 0)
        # C-187 shares Z-01, including the final extreme weather, but no anomaly.
        peer = reports[4]["findings"]["C-187"]["wildfire"]
        self.assertTrue(peer["dangerous_weather"])
        self.assertEqual(peer["combined"]["score"], 0)

    def test_service_areas_have_distinct_load_trajectories(self):
        reports = self.reports()
        trajectories = {
            circuit_id: tuple(round(report["findings"][circuit_id]["grid"]["per_asset"][0]["circuit_utilization"], 3)
                              for report in reports)
            for circuit_id in reports[0]["findings"]
        }
        self.assertGreater(len(set(trajectories.values())), 4)
        self.assertGreater(trajectories["C-187"][-1], trajectories["C-187"][0])
        self.assertNotEqual(trajectories["C-185"], trajectories["C-189"])

    def test_secondary_anomalies_are_circuit_specific_and_time_bounded(self):
        reports = self.reports()
        self.assertTrue(reports[2]["findings"]["C-186"]["grid"]["anomaly_asset_ids"])
        self.assertTrue(reports[3]["findings"]["C-188"]["grid"]["anomaly_asset_ids"])
        self.assertFalse(reports[4]["findings"]["C-186"]["grid"]["anomaly_asset_ids"])
        self.assertFalse(reports[4]["findings"]["C-188"]["grid"]["anomaly_asset_ids"])

    def test_multiple_categories_do_not_multiply_impact(self):
        final = self.reports()[-1]
        self.assertEqual({incident["category"] for incident in final["incidents"]},
                         {"grid_strain", "equipment_anomaly", "combined_wildfire"})
        self.assertEqual(final["total_impact"]["customers_at_risk"], 8420)
        self.assertEqual(final["total_impact"]["customer_area_ids"], ["CA-001", "CA-002"])
        self.assertEqual(len(final["total_impact"]["critical_facilities"]), 1)
        self.assertEqual(final["total_impact"]["customers_interrupted"], 0)

    def test_repeated_evaluation_and_stable_identity(self):
        reports = self.reports()
        final = reports[-1]
        for _ in range(3):
            self.assertEqual(self.scenario.evaluate(), final)
        grid_incidents = [next(incident for incident in report["incidents"] if incident["category"] == "grid_strain")
                          for report in reports[1:]]
        self.assertEqual(len({incident["incident_id"] for incident in grid_incidents}), 1)
        self.assertEqual({incident["first_detected_stage"] for incident in grid_incidents}, {2})
        self.assertEqual([incident["recommendation"]["revision"] for incident in grid_incidents], [2, 3, 4, 5])
        # Mutating the returned report cannot corrupt the registry.
        final["incidents"][0]["status"] = "corrupted"
        self.assertEqual(self.scenario.evaluate()["incidents"][0]["status"], "open")

    def test_reset_reproduces_every_stage_with_new_run_identity(self):
        first = self.reports()
        first_run = self.scenario.run_id
        self.scenario.reset()
        self.assertNotEqual(first_run, self.scenario.run_id)
        self.assertEqual(self.scenario.stage, 1)
        self.assertEqual(self.scenario.evaluate()["incident_history"], [])
        second = self.reports()
        self.assertEqual(json.dumps(first, sort_keys=True).replace(first_run, "RUN"),
                         json.dumps(second, sort_keys=True).replace(self.scenario.run_id, "RUN"))

    def test_forward_only_and_stage_snapshots_do_not_compound(self):
        for bad_stage in (0, 6, True, 2.5):
            with self.assertRaises(DataQualityError):
                stage_tables(self.baseline, bad_stage)
        for _ in range(4):
            self.scenario.advance()
        with self.assertRaises(DataQualityError):
            self.scenario.advance()
        self.assertEqual(self.scenario.stage, 5)
        direct = stage_tables(self.baseline, 5)
        for name in direct:
            pd.testing.assert_frame_equal(direct[name], self.scenario.snapshot()[name])
        model = GridModel(direct)
        self.assertAlmostEqual(model.asset("T-882")["current_load_mw"], 31.5)
        self.assertAlmostEqual(model.asset("T-882")["temperature_f"], 163.3)

    def test_no_recommendation_changes_power_crews_or_source_tables(self):
        for report in self.reports():
            for item in report["findings"].values():
                recommendation = item["response"]["recommendation"]
                self.assertFalse(recommendation["executed"])
                self.assertTrue(recommendation["primary"]["requires_human_approval"])
            self.assertEqual(report["total_impact"]["customers_interrupted"], 0)
        snapshot = self.scenario.snapshot()
        pd.testing.assert_frame_equal(snapshot["crews"], self.baseline["crews"])
        pd.testing.assert_series_equal(snapshot["circuits"].energized, self.baseline["circuits"].energized)
        for name, expected in generate_data().items():
            pd.testing.assert_frame_equal(self.baseline[name], expected)
        self.scenario.reset()
        for name in self.baseline:
            pd.testing.assert_frame_equal(self.scenario.snapshot()[name], self.baseline[name])

    def test_input_snapshot_is_isolated_and_bad_data_fails(self):
        self.baseline["assets"].loc[0, "capacity_mw"] = 0
        self.assertEqual(self.scenario.snapshot()["assets"].loc[0, "capacity_mw"], 30)
        with self.assertRaises(DataQualityError):
            Scenario(self.baseline)
