import unittest

import pandas as pd

from src.agents import grid_reliability_agent, wildfire_risk_agent, impact_agent, response_agent
from src.data_generator import generate_data
from src.ontology import DataQualityError, GridModel
from src.risk_engine import electrical_risks


class AgentTests(unittest.TestCase):
    def evaluate(self, tables, stage=5):
        model = GridModel(tables)
        grid = grid_reliability_agent(model, "C-184", stage)
        wildfire = wildfire_risk_agent(model, "C-184", stage)
        impact = impact_agent(model, ["T-882", "S-882", "T-882"], stage)
        response = response_agent(model, "C-184", stage, "test:C-184", grid, wildfire, impact)
        return grid, wildfire, impact, response

    def test_evidence_matches_calculations_and_counts(self):
        tables = generate_data()
        grid, wildfire, impact, response = self.evaluate(tables)
        hero = next(row for row in grid["per_asset"] if row["asset_id"] == "T-882")
        model = GridModel(tables)
        self.assertEqual(hero["grid_strain"], electrical_risks(model.asset("T-882"), model.circuit("C-184"))["grid_strain"])
        self.assertEqual(impact["impact"]["customers_at_risk"], 8420)
        self.assertEqual(len(impact["impact"]["critical_facilities"]), 1)
        self.assertEqual(wildfire["combined"]["score"], 0)
        for agent in (grid, wildfire, impact, response):
            self.assertEqual(agent["explanation_mode"], "deterministic_template")
            self.assertTrue(agent["explanation"])

    def test_critical_recommendation_has_evidence_alternatives_and_no_actions(self):
        tables = generate_data()
        tables["assets"].loc[0, "temperature_f"] += 65
        tables["assets"].loc[0, "current_load_mw"] = 31.5
        before = {name: frame.copy(deep=True) for name, frame in tables.items()}
        recommendation = self.evaluate(tables)[3]["recommendation"]
        self.assertEqual(recommendation["primary"]["action_type"], "dispatch_inspection")
        self.assertEqual(recommendation["primary"]["candidate_crew_ids"], ["CR-01"])
        self.assertEqual(recommendation["evidence"]["customers_at_risk"], 8420)
        self.assertEqual(recommendation["evidence"]["facility_ids"], ["F-001"])
        self.assertIn("prepare_deenergization_review", [option["action_type"] for option in recommendation["alternatives"]])
        for option in [recommendation["primary"], *recommendation["alternatives"]]:
            self.assertTrue(option["prerequisites"] and option["tradeoff"] and option["expected_benefit"])
            self.assertTrue(option["requires_human_approval"])
        self.assertFalse(recommendation["executed"])
        self.assertEqual(recommendation["approval_status"], "awaiting_human_review")
        for name in tables:
            pd.testing.assert_frame_equal(tables[name], before[name])

    def test_no_available_crew_escalates_without_assignment(self):
        tables = generate_data()
        tables["assets"].loc[0, "temperature_f"] += 65
        tables["assets"].loc[0, "current_load_mw"] = 31.5
        tables["crews"]["available"] = False
        recommendation = self.evaluate(tables)[3]["recommendation"]
        self.assertEqual(recommendation["primary"]["action_type"], "escalate")
        self.assertEqual(recommendation["primary"]["candidate_crew_ids"], [])

    def test_stale_findings_are_rejected(self):
        tables = generate_data()
        grid, wildfire, impact, _ = self.evaluate(tables)
        with self.assertRaises(DataQualityError):
            response_agent(GridModel(tables), "C-184", 4, "test", grid, wildfire, impact)
