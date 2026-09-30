"""Transparent synthetic prototype indicators, NOT validated probabilities.

See docs/SCORING.md. These functions have no side effects or external services.
Invalid inputs raise DataQualityError rather than returning a reassuring zero.
"""

import math
from numbers import Real

from src.ontology import DataQualityError, NUMERIC_BOUNDS

LABEL = "Synthetic prototype indicator; not a validated probability"
SEVERITY_THRESHOLDS = {"ELEVATED": 30, "HIGH": 60, "CRITICAL": 85}
SEVERITY_ORDER = {"NORMAL": 0, "ELEVATED": 1, "HIGH": 2, "CRITICAL": 3}
GRID_WEIGHTS = {"utilization": 0.65, "demand_trend": 0.20, "poor_condition": 0.15}
EQUIPMENT_WEIGHTS = {"temperature_rise": 0.65, "utilization": 0.20, "poor_condition": 0.15}
ENVIRONMENT_WEIGHTS = {"wind": 0.40, "dryness": 0.30, "ambient_heat": 0.20, "zone": 0.10}
COMBINED_WEIGHTS = {"environment": 0.60, "equipment": 0.40}
BOUNDS = {
    "utilization": (0.70, 1.10), "demand_trend": (0, 60),
    "poor_condition": (0, 100), "temperature_rise": (10, 60),
    "wind": (10, 50), "dryness": (0, 30), "ambient_heat": (85, 110),
    "zone": (0, 1), "environment": (0, 100), "equipment": (0, 100),
}
ZONE_VALUES = {"low": 0, "moderate": 0.5, "high": 1}
ANOMALY_TEMPERATURE_RISE_F = 30
ANOMALY_MIN_UTILIZATION = 0.90
ANOMALY_OVERLOAD = 1.10
DANGER_WIND_MPH = 35
DANGER_MAX_HUMIDITY_PCT = 20
DANGER_AMBIENT_F = 95


def number(record: dict, key: str) -> float:
    value = record.get(key)
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value):
        raise DataQualityError(f"{key}: missing or nonfinite numeric input")
    low, high = NUMERIC_BOUNDS[key]
    if value < low or (high is not None and value > high) or (key == "capacity_mw" and value <= 0):
        raise DataQualityError(f"{key}: out of range")
    return float(value)


def normalize(value: float, low: float, high: float) -> float:
    if not all(math.isfinite(v) for v in (value, low, high)) or high <= low:
        raise DataQualityError("Invalid normalization input or bounds")
    return min(1.0, max(0.0, (value - low) / (high - low)))


def severity(score: float) -> str:
    for label, cutoff in reversed(SEVERITY_THRESHOLDS.items()):
        if score >= cutoff:
            return label
    return "NORMAL"


def weighted_result(category: str, values: dict, weights: dict, units: dict) -> dict:
    factors = []
    for name, weight in weights.items():
        low, high = BOUNDS[name]
        normalized = normalize(values[name], low, high)
        factors.append(dict(name=name, value=values[name], unit=units[name],
                            bounds=[low, high], weight=weight, normalized=normalized,
                            contribution=100 * weight * normalized))
    score = sum(factor["contribution"] for factor in factors)
    return dict(category=category, score=score, severity=severity(score), factors=factors,
                data_quality="valid", label=LABEL)


def electrical_risks(asset: dict, circuit: dict) -> dict:
    if asset.get("circuit_id") != circuit.get("circuit_id"):
        raise DataQualityError("Asset/circuit relationship mismatch")
    asset_utilization = number(asset, "current_load_mw") / number(asset, "capacity_mw")
    circuit_utilization = number(circuit, "current_load_mw") / number(circuit, "capacity_mw")
    temperature_rise = number(asset, "temperature_f") - number(asset, "baseline_temperature_f")
    poor_condition = 100 - number(asset, "condition_score")
    grid = weighted_result("grid_strain", {
        "utilization": max(asset_utilization, circuit_utilization),
        "demand_trend": number(circuit, "demand_trend_pct"), "poor_condition": poor_condition,
    }, GRID_WEIGHTS, {"utilization": "ratio", "demand_trend": "%", "poor_condition": "points"})
    equipment = weighted_result("equipment_anomaly", {
        "temperature_rise": temperature_rise, "utilization": asset_utilization,
        "poor_condition": poor_condition,
    }, EQUIPMENT_WEIGHTS, {"temperature_rise": "°F above baseline", "utilization": "ratio", "poor_condition": "points"})
    # This gate uses electrical measurements only; weather cannot change it.
    anomaly = ((temperature_rise >= ANOMALY_TEMPERATURE_RISE_F
                and asset_utilization >= ANOMALY_MIN_UTILIZATION)
               or asset_utilization >= ANOMALY_OVERLOAD)
    return dict(grid_strain=grid, equipment_anomaly=equipment, electrical_anomaly=anomaly,
                asset_utilization=asset_utilization, circuit_utilization=circuit_utilization,
                temperature_rise_f=temperature_rise)


def wildfire_risks(asset: dict, circuit: dict, weather: dict) -> dict:
    electrical = electrical_risks(asset, circuit)
    if weather.get("zone_id") != circuit.get("zone_id"):
        raise DataQualityError("Weather/circuit zone mismatch")
    zone = circuit.get("fire_risk_zone")
    if zone not in ZONE_VALUES:
        raise DataQualityError("Unknown fire risk zone category")
    wind = number(weather, "wind_speed_mph")
    humidity = number(weather, "humidity_pct")
    ambient = number(weather, "ambient_temperature_f")
    environment = weighted_result("environmental_exposure", {
        "wind": wind, "dryness": 40 - humidity, "ambient_heat": ambient, "zone": ZONE_VALUES[zone],
    }, ENVIRONMENT_WEIGHTS, {"wind": "mph", "dryness": "percentage points below 40% humidity",
                             "ambient_heat": "°F", "zone": "category index"})
    if not isinstance(circuit.get("energized"), bool):
        raise DataQualityError("energized: missing boolean")
    if asset.get("status") not in {"operational", "out_of_service"}:
        raise DataQualityError("status: missing or invalid asset state")
    eligible = electrical["electrical_anomaly"] and circuit["energized"] and asset["status"] == "operational"
    dangerous_weather = (zone == "high" and wind >= DANGER_WIND_MPH
                         and humidity <= DANGER_MAX_HUMIDITY_PCT and ambient >= DANGER_AMBIENT_F)
    combined = weighted_result("combined_wildfire", {
        "environment": environment["score"], "equipment": electrical["equipment_anomaly"]["score"],
    }, COMBINED_WEIGHTS, {"environment": "indicator points", "equipment": "indicator points"})
    raw_score = combined["score"]
    # Explicit policy gate: neither weather alone nor a numerical average may
    # imply a critical combined incident. Retain the adjustment as evidence.
    if not eligible:
        score, rule = 0.0, "No energized operational asset with an electrical anomaly"
    elif dangerous_weather:
        score, rule = max(85.0, raw_score), "Electrical anomaly AND dangerous weather: critical floor 85"
    else:
        score, rule = min(84.0, raw_score), "Dangerous-weather conjunction absent: cap below critical"
    combined.update(score=score, severity=severity(score), weighted_score=raw_score,
                    rule=rule, rule_adjustment=score - raw_score)
    return dict(environment=environment, combined=combined,
                electrical_anomaly=electrical["electrical_anomaly"],
                dangerous_weather=dangerous_weather, combined_eligible=eligible)


def incident_priority(incident: dict) -> tuple:
    """Safety/reliability severity first, then consequence, urgency, stable ID."""
    impact = incident["impact"]
    return (-SEVERITY_ORDER[incident["severity"]], -len(impact["critical_facilities"]),
            -impact["customers_at_risk"], -incident["score"], incident["incident_id"])
