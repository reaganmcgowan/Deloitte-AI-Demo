"""Validated ID relationships, with circuit-wide impact as an explicit approximation."""

import argparse
import json
import math
from pathlib import Path

import pandas as pd

from src.data_generator import DATA_DIR, STAGE_TIMESTAMPS


class DataQualityError(ValueError):
    """Missing, ambiguous, or invalid operational data; never substitute zero risk."""


# Explicit suffixes encode the unit contract. Bounds are data sanity checks,
# not operating limits or risk thresholds. Loads may exceed capacity.
NUMERIC_BOUNDS = {
    "capacity_mw": (0, None), "current_load_mw": (0, None),
    "temperature_f": (-100, 1000), "baseline_temperature_f": (-100, 1000),
    "ambient_temperature_f": (-100, 160), "wind_speed_mph": (0, 300),
    "humidity_pct": (0, 100), "condition_score": (0, 100),
    "vulnerability_score": (0, 1), "age_years": (0, 150),
    "customer_count": (0, None), "customers_served": (0, None),
    "latitude": (-90, 90), "longitude": (-180, 180),
    "demand_trend_pct": (-100, None), "stage": (1, 5),
}
SCHEMAS = {
    "assets": "asset_id asset_name asset_type circuit_id capacity_mw current_load_mw temperature_f baseline_temperature_f age_years condition_score latitude longitude status",
    "circuits": "circuit_id circuit_name zone_id capacity_mw current_load_mw demand_trend_pct fire_risk_zone customers_served energized",
    "weather": "stage timestamp zone_id ambient_temperature_f wind_speed_mph humidity_pct",
    "customer_areas": "area_id circuit_id customer_count vulnerability_score",
    "critical_facilities": "facility_id name facility_type circuit_id backup_power latitude longitude",
    "crews": "crew_id available location zone_id skill_type",
}
PRIMARY_KEYS = {
    "assets": "asset_id", "circuits": "circuit_id", "customer_areas": "area_id",
    "critical_facilities": "facility_id", "crews": "crew_id",
}
ID_PATTERNS = {
    "asset_id": r"[TSL]-\d{3}", "circuit_id": r"C-\d{3}", "area_id": r"CA-\d{3}",
    "facility_id": r"F-\d{3}", "crew_id": r"CR-\d{2}", "zone_id": r"Z-\d{2}",
}
ENUMS = {
    "asset_type": {"transformer", "substation", "distribution_line"},
    "status": {"operational", "out_of_service"},
    "fire_risk_zone": {"low", "moderate", "high"},
    "facility_type": {"hospital", "fire_station", "water_facility", "emergency_shelter"},
    "skill_type": {"electrical_inspection", "line_repair"},
}


def validate_data(tables: dict[str, pd.DataFrame]) -> None:
    """Validate schemas, scalar values, keys, weather coverage, and cached totals."""
    for name, columns in SCHEMAS.items():
        if name not in tables:
            raise DataQualityError(f"Missing table: {name}")
        table = tables[name]
        missing = set(columns.split()) - set(table.columns)
        if missing:
            raise DataQualityError(f"{name}: missing columns {sorted(missing)} (check units)")
        if table.empty:
            raise DataQualityError(f"{name}: empty dataset")
        for column in columns.split():
            values = table[column]
            if values.isna().any() or values.astype(str).str.strip().eq("").any():
                raise DataQualityError(f"{name}.{column}: missing values")
            if column in ID_PATTERNS and not values.astype(str).str.fullmatch(ID_PATTERNS[column]).all():
                raise DataQualityError(f"{name}.{column}: malformed IDs")
            if column in ENUMS and not values.isin(ENUMS[column]).all():
                raise DataQualityError(f"{name}.{column}: unsupported category")
            if column in {"energized", "available", "backup_power"}:
                if not pd.api.types.is_bool_dtype(values):
                    raise DataQualityError(f"{name}.{column}: must contain booleans")
            if column in NUMERIC_BOUNDS:
                if not pd.api.types.is_numeric_dtype(values) or pd.api.types.is_bool_dtype(values):
                    raise DataQualityError(f"{name}.{column}: must be numeric")
                low, high = NUMERIC_BOUNDS[column]
                if not values.map(math.isfinite).all() or (values < low).any() or (high is not None and (values > high).any()):
                    raise DataQualityError(f"{name}.{column}: nonfinite or out-of-range values")
                if column == "capacity_mw" and (values <= 0).any():
                    raise DataQualityError(f"{name}.{column}: capacity must be positive")
                if column in {"customer_count", "customers_served", "age_years", "stage"} and (values % 1 != 0).any():
                    raise DataQualityError(f"{name}.{column}: must be whole numbers")
        key = [PRIMARY_KEYS[name]] if name in PRIMARY_KEYS else ["zone_id", "stage"]
        if table.duplicated(key).any():
            raise DataQualityError(f"{name}: duplicate key {key}")

    circuits = tables["circuits"]
    circuit_ids = set(circuits.circuit_id)
    zones = set(circuits.zone_id)
    for name in ("assets", "customer_areas", "critical_facilities"):
        orphan_ids = set(tables[name].circuit_id) - circuit_ids
        if orphan_ids:
            raise DataQualityError(f"{name}: unknown circuit_id {sorted(orphan_ids)}")
    for name in ("weather", "crews"):
        orphan_zones = set(tables[name].zone_id) - zones
        if orphan_zones:
            raise DataQualityError(f"{name}: unknown zone_id {sorted(orphan_zones)}")
    for name in ("assets", "customer_areas"):
        if circuit_ids - set(tables[name].circuit_id):
            raise DataQualityError(f"{name}: every circuit needs linked records")
    weather = tables["weather"]
    expected = {(zone, stage) for zone in zones for stage in STAGE_TIMESTAMPS}
    if set(zip(weather.zone_id, weather.stage)) != expected:
        raise DataQualityError("weather: missing zone/stage coverage")
    for row in weather.itertuples():
        if row.timestamp != STAGE_TIMESTAMPS[row.stage]:
            raise DataQualityError("weather.timestamp: expected synthetic California date/time and -07:00 offset")
    totals = tables["customer_areas"].groupby("circuit_id").customer_count.sum()
    cached = circuits.set_index("circuit_id").customers_served
    if not cached.sort_index().eq(totals.sort_index()).all():
        raise DataQualityError("circuits.customers_served: does not match customer_areas totals")


def load_data(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    tables = {}
    for name in SCHEMAS:
        try:
            tables[name] = pd.read_csv(Path(data_dir) / f"{name}.csv")
        except (OSError, pd.errors.ParserError, pd.errors.EmptyDataError) as error:
            raise DataQualityError(f"Unable to load {name}.csv: {error}") from error
    validate_data(tables)
    return tables


class GridModel:
    """A validated snapshot; returned records are copies, not editable model state."""

    def __init__(self, tables: dict[str, pd.DataFrame]):
        validate_data(tables)
        self._tables = {name: table.copy(deep=True) for name, table in tables.items()}

    @classmethod
    def from_csv(cls, data_dir: Path = DATA_DIR) -> "GridModel":
        return cls(load_data(data_dir))

    def _one(self, table: str, key: str, value: str) -> dict:
        rows = self._tables[table]
        selected = rows.loc[rows[key] == value]
        if len(selected) != 1:
            raise DataQualityError(f"{table}: unknown or ambiguous {key} {value!r}")
        return selected.iloc[0].to_dict()

    def asset(self, asset_id: str) -> dict:
        return self._one("assets", "asset_id", asset_id)

    def circuit(self, circuit_id: str) -> dict:
        return self._one("circuits", "circuit_id", circuit_id)

    def circuit_for_asset(self, asset_id: str) -> dict:
        return self.circuit(self.asset(asset_id)["circuit_id"])

    def _circuit_rows(self, table: str, circuit_id: str) -> pd.DataFrame:
        self.circuit(circuit_id)  # Unknown IDs must not resemble an empty valid result.
        rows = self._tables[table]
        return rows.loc[rows.circuit_id == circuit_id].copy()

    def assets_for_circuit(self, circuit_id: str) -> pd.DataFrame:
        return self._circuit_rows("assets", circuit_id)

    def customer_areas_for_circuit(self, circuit_id: str) -> pd.DataFrame:
        return self._circuit_rows("customer_areas", circuit_id)

    def facilities_for_circuit(self, circuit_id: str) -> pd.DataFrame:
        return self._circuit_rows("critical_facilities", circuit_id)

    def weather_for_circuit(self, circuit_id: str, stage: int = 1) -> dict:
        zone_id = self.circuit(circuit_id)["zone_id"]
        rows = self._tables["weather"]
        selected = rows.loc[(rows.zone_id == zone_id) & (rows.stage == stage)]
        if len(selected) != 1:
            raise DataQualityError(f"weather: missing zone {zone_id}, stage {stage}")
        return selected.iloc[0].to_dict()

    def crews_for_circuit(self, circuit_id: str, skill_type: str = "electrical_inspection") -> pd.DataFrame:
        """Eligible = available, same zone, exact skill. No dispatch or travel estimate."""
        zone_id = self.circuit(circuit_id)["zone_id"]
        if skill_type not in ENUMS["skill_type"]:
            raise DataQualityError(f"Unknown crew skill_type {skill_type!r}")
        crews = self._tables["crews"]
        return crews.loc[crews.available & (crews.zone_id == zone_id) & (crews.skill_type == skill_type)].copy()

    def impact_for_assets(self, asset_ids: list[str]) -> dict:
        """Union circuit-wide exposure; repeated assets/circuits never multiply counts."""
        circuit_ids = sorted({self.circuit_for_asset(asset_id)["circuit_id"] for asset_id in asset_ids})
        # Join from unique circuits, never directly from many assets to many areas.
        circuits = self._tables["circuits"]
        selected = circuits.loc[circuits.circuit_id.isin(circuit_ids)]
        areas = selected[["circuit_id", "energized"]].merge(
            self._tables["customer_areas"], on="circuit_id", validate="one_to_many")
        facilities = selected[["circuit_id", "energized"]].merge(
            self._tables["critical_facilities"], on="circuit_id", validate="one_to_many")
        customer_count = int(areas.customer_count.sum())
        return {
            "circuit_ids": circuit_ids,
            "customer_area_ids": sorted(areas.area_id.tolist()),
            "customers_at_risk": customer_count,
            "customers_interrupted": int(areas.loc[~areas.energized, "customer_count"].sum()),
            "critical_facilities": facilities.drop(columns="energized").to_dict("records"),
            "interrupted_facility_ids": sorted(facilities.loc[~facilities.energized, "facility_id"].tolist()),
            "customer_weighted_vulnerability": (
                float((areas.customer_count * areas.vulnerability_score).sum() / customer_count)
                if customer_count else None),
        }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate CSVs and trace a synthetic asset.")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--asset", default="T-882")
    args = parser.parse_args()
    model = GridModel.from_csv(args.data_dir)
    circuit = model.circuit_for_asset(args.asset)
    print(json.dumps(dict(asset_id=args.asset, impact=model.impact_for_assets([args.asset]),
                         baseline_weather=model.weather_for_circuit(circuit["circuit_id"]),
                         eligible_crews=model.crews_for_circuit(circuit["circuit_id"]).crew_id.tolist()), indent=2))


if __name__ == "__main__":
    main()
