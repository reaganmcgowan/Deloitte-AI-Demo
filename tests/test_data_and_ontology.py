"""Focused data-contract and relationship tests; no network or API keys."""

from pathlib import Path
import tempfile
import unittest

import pandas as pd

from src.data_generator import DATA_DIR, generate_data, write_data
from src.ontology import DataQualityError, GridModel, load_data, validate_data


class DataTests(unittest.TestCase):
    def setUp(self):
        self.tables = generate_data()

    def test_fixture_sizes_and_validity(self):
        validate_data(self.tables)
        self.assertEqual({name: len(table) for name, table in self.tables.items()}, {
            "assets": 18, "circuits": 6, "weather": 15, "customer_areas": 12,
            "critical_facilities": 3, "crews": 4,
        })

    def test_csv_reproducibility_and_committed_fixtures(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            write_data(Path(first))
            write_data(Path(second))
            for name in self.tables:
                filename = f"{name}.csv"
                self.assertEqual((Path(first) / filename).read_bytes(), (Path(second) / filename).read_bytes())
                self.assertEqual((Path(first) / filename).read_bytes(), (DATA_DIR / filename).read_bytes())
                pd.testing.assert_frame_equal(load_data(Path(first))[name], load_data()[name])

    def test_other_seed_changes_measurements_preserves_hero(self):
        other = generate_data(100)
        self.assertFalse(other["assets"].equals(self.tables["assets"]))
        self.assertEqual(GridModel(other).impact_for_assets(["T-882"])["customers_at_risk"], 8420)

    def test_bad_scalar_values_fail(self):
        cases = [
            ("assets", "capacity_mw", 0), ("assets", "current_load_mw", -1),
            ("assets", "temperature_f", float("inf")), ("assets", "condition_score", 101),
            ("assets", "baseline_temperature_f", float("nan")),
            ("assets", "latitude", 91), ("assets", "age_years", -1),
            ("weather", "humidity_pct", -1), ("weather", "wind_speed_mph", -1),
            ("customer_areas", "customer_count", -1),
            ("customer_areas", "customer_count", 2.5),
            ("customer_areas", "vulnerability_score", 1.1),
            ("assets", "asset_id", "bad-id"), ("assets", "asset_name", " "),
            ("crews", "available", "False"), ("assets", "asset_type", "unknown"),
            ("weather", "timestamp", "2026-08-15T13:00:00"),
        ]
        for table, column, value in cases:
            with self.subTest(table=table, column=column, value=value):
                broken = generate_data()
                # Preserve numeric dtype so bounds/integer validation is exercised.
                dtype = float if isinstance(value, (int, float)) else object
                broken[table][column] = broken[table][column].astype(dtype)
                broken[table].loc[0, column] = value
                with self.assertRaises(DataQualityError):
                    validate_data(broken)

    def test_numeric_bounds_on_numeric_columns(self):
        for column, value in (("capacity_mw", 0), ("condition_score", 101),
                              ("current_load_mw", -1), ("temperature_f", float("inf"))):
            with self.subTest(column=column):
                broken = generate_data()
                broken["assets"][column] = broken["assets"][column].astype(float)
                broken["assets"].loc[0, column] = value
                with self.assertRaisesRegex(DataQualityError, column):
                    validate_data(broken)

    def test_duplicate_primary_and_weather_keys(self):
        for name in self.tables:
            with self.subTest(table=name):
                broken = generate_data()
                broken[name] = pd.concat([broken[name], broken[name].iloc[[0]]], ignore_index=True)
                with self.assertRaisesRegex(DataQualityError, "duplicate"):
                    validate_data(broken)

    def test_orphan_relationships(self):
        for name, column, value in (("assets", "circuit_id", "C-999"),
                                    ("customer_areas", "circuit_id", "C-999"),
                                    ("critical_facilities", "circuit_id", "C-999"),
                                    ("crews", "zone_id", "Z-99"),
                                    ("weather", "zone_id", "Z-99")):
            with self.subTest(table=name):
                broken = generate_data()
                broken[name].loc[0, column] = value
                with self.assertRaisesRegex(DataQualityError, "unknown"):
                    validate_data(broken)

    def test_missing_weather_and_unit_column(self):
        self.tables["weather"] = self.tables["weather"].iloc[1:]
        with self.assertRaisesRegex(DataQualityError, "coverage"):
            validate_data(self.tables)
        self.tables = generate_data()
        self.tables["assets"] = self.tables["assets"].rename(columns={"capacity_mw": "capacity_kw"})
        with self.assertRaisesRegex(DataQualityError, "units"):
            validate_data(self.tables)

    def test_cached_customer_total_must_match(self):
        self.tables["circuits"].loc[0, "customers_served"] += 1
        with self.assertRaisesRegex(DataQualityError, "totals"):
            validate_data(self.tables)

    def test_missing_csv_is_explicit(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(DataQualityError, "assets.csv"):
                load_data(Path(directory))


class RelationshipTests(unittest.TestCase):
    def setUp(self):
        self.model = GridModel(generate_data())

    def test_hero_chain(self):
        self.assertEqual(self.model.circuit_for_asset("T-882")["circuit_id"], "C-184")
        impact = self.model.impact_for_assets(["T-882"])
        self.assertEqual(impact["customer_area_ids"], ["CA-001", "CA-002"])
        self.assertEqual(impact["customers_at_risk"], 8420)
        self.assertEqual(impact["customers_interrupted"], 0)
        self.assertEqual(len(impact["critical_facilities"]), 1)
        self.assertEqual(impact["critical_facilities"][0]["facility_type"], "hospital")
        self.assertEqual(impact["critical_facilities"][0]["facility_id"], "F-001")

    def test_overlapping_assets_deduplicate_customers_and_facilities(self):
        self.assertEqual(self.model.impact_for_assets(["T-882", "S-882", "T-882"]),
                         self.model.impact_for_assets(["T-882"]))
        impact = self.model.impact_for_assets(["T-882", "L-882", "T-883"])
        self.assertEqual(impact["customers_at_risk"], 14620)
        self.assertEqual(len(impact["critical_facilities"]), 2)
        self.assertEqual(len(impact["customer_area_ids"]), 4)

    def test_weather_by_zone_and_stage(self):
        baseline = self.model.weather_for_circuit("C-184")
        final = self.model.weather_for_circuit("C-184", 5)
        self.assertEqual(baseline["wind_speed_mph"], 8)
        self.assertEqual(final["wind_speed_mph"], 46)
        self.assertEqual(final["humidity_pct"], 11)
        self.assertEqual(final["zone_id"], "Z-01")
        self.assertNotEqual(self.model.weather_for_circuit("C-185", 5)["wind_speed_mph"], 46)

    def test_crew_eligibility(self):
        self.assertEqual(self.model.crews_for_circuit("C-184").crew_id.tolist(), ["CR-01"])
        self.assertTrue(self.model.crews_for_circuit("C-184", "line_repair").empty)
        self.assertEqual(self.model.crews_for_circuit("C-186", "line_repair").crew_id.tolist(), ["CR-04"])

    def test_unknown_ids_and_stage_raise(self):
        for lookup in (lambda: self.model.asset("T-999"),
                       lambda: self.model.customer_areas_for_circuit("C-999"),
                       lambda: self.model.facilities_for_circuit("C-999"),
                       lambda: self.model.crews_for_circuit("C-999"),
                       lambda: self.model.weather_for_circuit("C-184", 6),
                       lambda: self.model.impact_for_assets(["T-999"])):
            with self.assertRaises(DataQualityError):
                lookup()

    def test_valid_empty_results(self):
        self.assertTrue(self.model.facilities_for_circuit("C-186").empty)
        impact = self.model.impact_for_assets([])
        self.assertEqual(impact["customers_at_risk"], 0)
        self.assertEqual(impact["critical_facilities"], [])
        self.assertIsNone(impact["customer_weighted_vulnerability"])

    def test_interrupted_and_exposed_are_distinct(self):
        tables = generate_data()
        tables["circuits"].loc[0, "energized"] = False
        impact = GridModel(tables).impact_for_assets(["T-882", "T-883"])
        self.assertEqual(impact["customers_at_risk"], 14620)
        self.assertEqual(impact["customers_interrupted"], 8420)
        self.assertEqual(impact["interrupted_facility_ids"], ["F-001"])

    def test_returned_records_do_not_mutate_snapshot(self):
        areas = self.model.customer_areas_for_circuit("C-184")
        areas.loc[:, "customer_count"] = 0
        self.assertEqual(self.model.impact_for_assets(["T-882"])["customers_at_risk"], 8420)
        self.assertEqual(len(self.model.assets_for_circuit("C-184")), 3)


if __name__ == "__main__":
    unittest.main()
