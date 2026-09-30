"""Continuous synthetic measurements between the original five checkpoints.

The extra demand attribution is a declared scenario assumption, not inferred cause.
"""
from datetime import datetime, timedelta

from src.scenario import Scenario, stage_tables
from src.playback import CHECKPOINT_MINUTES
from src.ontology import DataQualityError, validate_data


def continuous_tables(baseline: dict, minute: float) -> dict:
    if not 0 <= minute <= 180:
        raise DataQualityError("Scenario time must be between 0 and 180 minutes")
    lower = max(i for i, value in enumerate(CHECKPOINT_MINUTES) if value <= minute)
    if minute == CHECKPOINT_MINUTES[lower]:
        return stage_tables(baseline, lower + 1)
    fraction = (minute - CHECKPOINT_MINUTES[lower]) / (CHECKPOINT_MINUTES[lower + 1] - CHECKPOINT_MINUTES[lower])
    before, after = stage_tables(baseline, lower + 1), stage_tables(baseline, lower + 2)
    tables = {name: frame.copy(deep=True) for name, frame in before.items()}
    for name, columns in {"assets": ["current_load_mw", "temperature_f"],
                          "circuits": ["current_load_mw", "demand_trend_pct"]}.items():
        for column in columns:
            target = after[name][column].copy()
            if name == "assets" and column == "temperature_f" and lower == 3:
                # The normal equipment rise approaches +20°F. The fault's additional
                # +45°F arrives at exactly 4 PM, never leaks into preceding minutes.
                hero = after[name].asset_id == "T-882"
                target.loc[hero] = baseline[name].loc[hero, "baseline_temperature_f"] + 20
            tables[name][column] = before[name][column] + fraction * (target - before[name][column])
    weather = tables["weather"]
    for zone in weather.zone_id.unique():
        current = (weather.zone_id == zone) & (weather.stage == lower + 1)
        following = (weather.zone_id == zone) & (weather.stage == lower + 2)
        for column in ("ambient_temperature_f", "wind_speed_mph", "humidity_pct"):
            start = float(weather.loc[current, column].iloc[0])
            end = float(weather.loc[following, column].iloc[0])
            weather[column] = weather[column].astype(float)
            weather.loc[current, column] = start + fraction * (end - start)
    validate_data(tables)
    return tables


class LiveScenario(Scenario):
    """Adds smooth measurements to Scenario without changing the checkpoint CLI."""
    def reset(self) -> None:
        super().reset()
        self.minute = 0.0

    @property
    def timestamp(self) -> str:
        return (datetime.fromisoformat("2026-08-15T13:00:00-07:00") + timedelta(minutes=self.minute)).isoformat()

    def snapshot(self) -> dict:
        return continuous_tables(self._baseline, self.minute)

    def seek(self, minute: float) -> dict:
        if not 0 <= minute <= 180:
            raise DataQualityError("Scenario time must be between 0 and 180 minutes")
        if minute < self.minute:
            self.reset()  # Earlier time is a new run, never future incident history.
        self.minute = float(minute)
        self._stage = max(i + 1 for i, value in enumerate(CHECKPOINT_MINUTES) if value <= minute)
        return self.evaluate()

    def advance(self) -> dict:
        if self.stage == 5:
            raise DataQualityError("Already at final stage; use reset to replay")
        return self.seek(CHECKPOINT_MINUTES[self.stage])

    def evaluate(self) -> dict:
        report = super().evaluate()
        report["minute"] = self.minute
        # Agent calculations use the validated fixture slot; observation time is
        # the interpolated sample's time, not the slot's original timestamp.
        groups = list(report["findings"].values())
        groups.extend(incident["findings"] for incident in report["incidents"])
        for finding in groups:
            for agent in finding.values():
                agent["timestamp"] = self.timestamp
            finding["wildfire"]["evidence"]["timestamp"] = self.timestamp
        return report


def demand_drivers(baseline: dict, tables: dict, circuit_id: str) -> dict:
    """Attribute the existing load increase; contributions sum exactly to load.

    C-184: event ramp is capped at 3 MW, with the remaining increase assigned
    to incremental energy demand. Other circuits use the same neutral demand bucket.
    """
    base = float(baseline["circuits"].set_index("circuit_id").loc[circuit_id, "current_load_mw"])
    current = float(tables["circuits"].set_index("circuit_id").loc[circuit_id, "current_load_mw"])
    extra = max(0.0, current - base)
    event = min(3.0, extra * .25) if circuit_id == "C-184" else 0.0
    return {"Baseline demand": base, "Incremental energy demand": extra - event, "Afternoon event": event}
