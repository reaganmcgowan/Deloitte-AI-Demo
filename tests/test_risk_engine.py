import math
import unittest

from src.ontology import DataQualityError, GridModel
from src.risk_engine import electrical_risks, wildfire_risks, normalize, severity, incident_priority


class RiskTests(unittest.TestCase):
    def setUp(self):
        model = GridModel.from_csv()
        self.asset = model.asset("T-882")
        self.circuit = model.circuit("C-184")
        self.weather = model.weather_for_circuit("C-184", 5)

    def test_normalization_and_severity_boundaries(self):
        self.assertEqual([normalize(v, 10, 20) for v in (0, 10, 15, 20, 30)], [0, 0, .5, 1, 1])
        self.assertEqual([severity(v) for v in (0, 29.99, 30, 59.99, 60, 84.99, 85, 100)],
                         ["NORMAL", "NORMAL", "ELEVATED", "ELEVATED", "HIGH", "HIGH", "CRITICAL", "CRITICAL"])
        for value in (math.nan, math.inf):
            with self.assertRaises(DataQualityError):
                normalize(value, 0, 1)

    def test_hand_calculated_contributions(self):
        self.asset.update(current_load_mw=27, temperature_f=133.3, condition_score=80)
        self.circuit.update(current_load_mw=27, demand_trend_pct=30)
        result = electrical_risks(self.asset, self.circuit)
        # Utilization .9 maps to .5; rise 35 maps to .5; poor condition .2.
        self.assertAlmostEqual(result["grid_strain"]["score"], 32.5 + 10 + 3)
        self.assertAlmostEqual(result["equipment_anomaly"]["score"], 32.5 + 10 + 3)
        for category in ("grid_strain", "equipment_anomaly"):
            self.assertAlmostEqual(result[category]["score"], sum(f["contribution"] for f in result[category]["factors"]))

    def test_factors_move_in_expected_direction(self):
        baseline = electrical_risks(self.asset, self.circuit)
        for field, value, category in (("current_load_mw", 30, "grid_strain"),
                                        ("temperature_f", 150, "equipment_anomaly"),
                                        ("condition_score", 20, "equipment_anomaly")):
            changed = dict(self.asset, **{field: value})
            self.assertGreater(electrical_risks(changed, self.circuit)[category]["score"], baseline[category]["score"])
        self.assertGreater(electrical_risks(self.asset, dict(self.circuit, demand_trend_pct=50))["grid_strain"]["score"], baseline["grid_strain"]["score"])
        environment = wildfire_risks(self.asset, self.circuit, dict(self.weather, wind_speed_mph=10, humidity_pct=40, ambient_temperature_f=85))["environment"]["score"]
        for field, value in (("wind_speed_mph", 40), ("humidity_pct", 10), ("ambient_temperature_f", 110)):
            changed = dict(self.weather, wind_speed_mph=10, humidity_pct=40, ambient_temperature_f=85)
            changed[field] = value
            self.assertGreater(wildfire_risks(self.asset, self.circuit, changed)["environment"]["score"], environment)

    def test_weather_alone_never_invents_anomaly(self):
        result = wildfire_risks(self.asset, self.circuit, self.weather)
        self.assertTrue(result["dangerous_weather"])
        self.assertGreater(result["environment"]["score"], 85)
        self.assertFalse(result["electrical_anomaly"])
        self.assertEqual(result["combined"]["score"], 0)

    def test_anomaly_boundaries_and_critical_conjunction(self):
        asset = dict(self.asset, current_load_mw=27, temperature_f=128.3)
        self.assertTrue(electrical_risks(asset, self.circuit)["electrical_anomaly"])
        self.assertFalse(electrical_risks(dict(asset, temperature_f=128.29), self.circuit)["electrical_anomaly"])
        self.assertFalse(electrical_risks(dict(asset, current_load_mw=26.99), self.circuit)["electrical_anomaly"])
        self.assertTrue(electrical_risks(dict(self.asset, current_load_mw=33), self.circuit)["electrical_anomaly"])
        boundary_weather = dict(self.weather, wind_speed_mph=35, humidity_pct=20, ambient_temperature_f=95)
        result = wildfire_risks(asset, self.circuit, boundary_weather)
        self.assertEqual(result["combined"]["score"], 85)
        self.assertGreater(result["combined"]["rule_adjustment"], 0)
        for field, value in (("wind_speed_mph", 34.99), ("humidity_pct", 20.01), ("ambient_temperature_f", 94.99)):
            self.assertNotEqual(wildfire_risks(asset, self.circuit, dict(boundary_weather, **{field: value}))["combined"]["severity"], "CRITICAL")
        for circuit, changed_asset in ((dict(self.circuit, energized=False), asset),
                                        (self.circuit, dict(asset, status="out_of_service"))):
            self.assertEqual(wildfire_risks(changed_asset, circuit, self.weather)["combined"]["score"], 0)

    def test_extreme_valid_measurements_are_bounded(self):
        asset = dict(self.asset, current_load_mw=3000, temperature_f=1000, condition_score=0)
        results = electrical_risks(asset, self.circuit)
        for category in ("grid_strain", "equipment_anomaly"):
            self.assertTrue(0 <= results[category]["score"] <= 100)
        combined = wildfire_risks(asset, self.circuit, self.weather)["combined"]
        self.assertTrue(0 <= combined["score"] <= 100)
        self.assertAlmostEqual(combined["score"], sum(f["contribution"] for f in combined["factors"]) + combined["rule_adjustment"])

    def test_invalid_or_missing_inputs_fail_explicitly(self):
        for record_name, key, value in (("asset", "capacity_mw", 0), ("circuit", "capacity_mw", 0),
                                         ("asset", "temperature_f", math.nan), ("weather", "humidity_pct", None),
                                         ("weather", "wind_speed_mph", math.inf), ("weather", "zone_id", "Z-99")):
            records = {"asset": dict(self.asset), "circuit": dict(self.circuit), "weather": dict(self.weather)}
            records[record_name][key] = value
            with self.subTest(key=key), self.assertRaises(DataQualityError):
                wildfire_risks(**records)

    def test_priority_never_dilutes_critical_severity(self):
        critical = dict(severity="CRITICAL", score=85, incident_id="a",
                        impact=dict(customers_at_risk=1, critical_facilities=[]))
        high = dict(severity="HIGH", score=84, incident_id="b",
                    impact=dict(customers_at_risk=100000, critical_facilities=[{}, {}]))
        self.assertEqual(sorted([high, critical], key=incident_priority)[0], critical)
        self.assertLess(incident_priority(critical), incident_priority(dict(critical, incident_id="z")))
