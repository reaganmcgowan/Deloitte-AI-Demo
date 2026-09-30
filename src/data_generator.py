"""Generate reviewable synthetic fixtures; run with python -m src.data_generator."""

import argparse
from pathlib import Path
import random

import pandas as pd

DEFAULT_SEED = 42
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SERVICE_AREAS = {
    "C-184": "Santa Clarita Foothills",
    "C-185": "Newhall",
    "C-186": "Valencia",
    "C-187": "Saugus",
    "C-188": "Canyon Country",
    "C-189": "Agua Dulce",
}
STAGE_TIMESTAMPS = {
    stage: f"2026-08-15T{time}:00-07:00"
    for stage, time in enumerate(("13:00", "14:00", "15:00", "15:30", "16:00"), 1)
}


def generate_data(seed: int = DEFAULT_SEED) -> dict[str, pd.DataFrame]:
    """Stable topology and hero counts; seed varies ordinary synthetic measurements."""
    rng = random.Random(seed)  # Local RNG: no dependence on global random state.
    circuits, assets, areas = [], [], []
    totals = [8420, 6200, 4800, 7100, 3900, 5600]
    zones = ["Z-01", "Z-02", "Z-03"]
    for index, total in enumerate(totals):
        circuit_id = f"C-{184 + index}"
        zone = zones[index % 3]
        capacity = float(30 + index * 4)
        load = round(capacity * rng.uniform(0.50, 0.65), 2)
        # Synthetic service area centered around Santa Clarita, California.
        # Coordinates are approximate and do not represent real utility assets.
        latitude, longitude = 34.39 + index * 0.025, -118.54 + index * 0.025
        circuits.append(dict(
            circuit_id=circuit_id, circuit_name=f"{SERVICE_AREAS[circuit_id]} service area",
            zone_id=zone, capacity_mw=capacity, current_load_mw=load,
            demand_trend_pct=0.0, fire_risk_zone=("high", "moderate", "low")[index % 3],
            customers_served=total, energized=True,
        ))
        # Two mutually exclusive service areas per circuit; counts include facilities.
        first_count = 4200 if index == 0 else total // 2
        for part, count in enumerate((first_count, total - first_count), 1):
            areas.append(dict(
                area_id=f"CA-{index * 2 + part:03d}", circuit_id=circuit_id,
                customer_count=count, vulnerability_score=round(rng.uniform(0.2, 0.8), 2),
            ))
        # Series equipment represents the same circuit load; do not sum asset loads.
        for kind, prefix, multiplier in (("transformer", "T", 1.0),
                                          ("substation", "S", 1.2),
                                          ("distribution_line", "L", 1.1)):
            temperature = round(rng.uniform(95, 110), 1)
            assets.append(dict(
                asset_id=f"{prefix}-{882 + index}",
                asset_name=f"Synthetic {kind.replace('_', ' ').title()} {882 + index}",
                asset_type=kind, circuit_id=circuit_id,
                capacity_mw=round(capacity * multiplier, 2), current_load_mw=load,
                temperature_f=temperature, baseline_temperature_f=temperature,
                age_years=rng.randint(5, 30), condition_score=rng.randint(75, 95),
                latitude=round(latitude, 4), longitude=round(longitude, 4), status="operational",
            ))
    weather = []
    for stage, timestamp in STAGE_TIMESTAMPS.items():
        for index, zone in enumerate(zones):
            hero_zone = zone == "Z-01"
            weather.append(dict(
                stage=stage, timestamp=timestamp, zone_id=zone,
                ambient_temperature_f=([88, 94, 100, 102, 104][stage - 1]
                                       if hero_zone else 84 + stage * 2 + index),
                wind_speed_mph=([8, 12, 18, 38, 46][stage - 1] if hero_zone else 6 + stage),
                humidity_pct=([40, 32, 24, 15, 11][stage - 1] if hero_zone else 48 - stage * 3),
            ))
    facilities = [
        dict(facility_id="F-001", name="Synthetic Foothill Hospital", facility_type="hospital",
             circuit_id="C-184", backup_power=True, latitude=34.395, longitude=-118.535),
        dict(facility_id="F-002", name="Synthetic Valley Fire Station", facility_type="fire_station",
             circuit_id="C-185", backup_power=True, latitude=34.42, longitude=-118.51),
        dict(facility_id="F-003", name="Synthetic Ridge Water Facility", facility_type="water_facility",
             circuit_id="C-187", backup_power=False, latitude=34.44, longitude=-118.49),
    ]
    crews = [
        dict(crew_id="CR-01", available=True, location="Synthetic Foothill Depot",
             zone_id="Z-01", skill_type="electrical_inspection"),
        dict(crew_id="CR-02", available=False, location="Synthetic Foothill Depot",
             zone_id="Z-01", skill_type="electrical_inspection"),
        dict(crew_id="CR-03", available=True, location="Synthetic Valley Depot",
             zone_id="Z-02", skill_type="electrical_inspection"),
        dict(crew_id="CR-04", available=True, location="Synthetic Ridge Depot",
             zone_id="Z-03", skill_type="line_repair"),
    ]
    return {name: pd.DataFrame(rows) for name, rows in dict(
        assets=assets, circuits=circuits, weather=weather, customer_areas=areas,
        critical_facilities=facilities, crews=crews,
    ).items()}


def write_data(output_dir: Path = DATA_DIR, seed: int = DEFAULT_SEED) -> dict[str, pd.DataFrame]:
    from src.ontology import validate_data

    tables = generate_data(seed)
    validate_data(tables)  # Validate everything before writing any fixture.
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(output_dir / f"{name}.csv", index=False, lineterminator="\n")
    return tables


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate six synthetic GridGuard CSVs.")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output-dir", type=Path, default=DATA_DIR)
    args = parser.parse_args()
    for name, table in write_data(args.output_dir, args.seed).items():
        print(f"{name}.csv: {len(table)} rows")


if __name__ == "__main__":
    main()
