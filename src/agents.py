"""Four bounded deterministic agents. Templates explain evidence; they do not act."""

from src.data_generator import STAGE_TIMESTAMPS
from src.ontology import DataQualityError, GridModel
from src.recommendations import propose_response
from src.risk_engine import LABEL, electrical_risks, wildfire_risks


def finding(agent: str, model: GridModel, circuit_id: str, stage: int) -> dict:
    if type(stage) is not int or stage not in STAGE_TIMESTAMPS:
        raise DataQualityError(f"Unknown scenario stage {stage!r}")
    return dict(agent=agent, stage=stage, timestamp=STAGE_TIMESTAMPS[stage], circuit_id=circuit_id,
                asset_ids=sorted(model.assets_for_circuit(circuit_id).asset_id.tolist()),
                explanation_mode="deterministic_template", limitations=LABEL,
                data_quality="valid")


def maximum_result(per_asset: list[dict], category: str) -> dict:
    # Circuit findings use the strongest asset signal, never an average that dilutes it.
    winner = sorted(per_asset, key=lambda row: (-row[category]["score"], row["asset_id"]))[0]
    return dict(winner[category], source_asset_id=winner["asset_id"])


def grid_reliability_agent(model: GridModel, circuit_id: str, stage: int) -> dict:
    result = finding("Grid Reliability", model, circuit_id, stage)
    circuit = model.circuit(circuit_id)
    per_asset = []
    for asset_id in result["asset_ids"]:
        asset = model.asset(asset_id)
        per_asset.append(dict(asset_id=asset_id, **electrical_risks(asset, circuit), evidence={
            "current_load_mw": asset["current_load_mw"], "capacity_mw": asset["capacity_mw"],
            "temperature_f": asset["temperature_f"], "baseline_temperature_f": asset["baseline_temperature_f"],
            "condition_score": asset["condition_score"], "demand_trend_pct": circuit["demand_trend_pct"],
        }))
    result.update(per_asset=per_asset, grid_strain=maximum_result(per_asset, "grid_strain"),
                  equipment_anomaly=maximum_result(per_asset, "equipment_anomaly"),
                  anomaly_asset_ids=[row["asset_id"] for row in per_asset if row["electrical_anomaly"]])
    result["explanation"] = (f"{circuit_id}: grid strain {result['grid_strain']['score']:.1f}/100; "
                             f"equipment indicator {result['equipment_anomaly']['score']:.1f}/100. "
                             f"Electrical anomaly assets: {', '.join(result['anomaly_asset_ids']) or 'none'}. "
                             "Scores retain per-asset factors with units and weighted contributions.")
    return result


def wildfire_risk_agent(model: GridModel, circuit_id: str, stage: int) -> dict:
    result = finding("Wildfire Risk", model, circuit_id, stage)
    circuit = model.circuit(circuit_id)
    weather = model.weather_for_circuit(circuit_id, stage)
    per_asset = [dict(asset_id=asset_id, **wildfire_risks(model.asset(asset_id), circuit, weather))
                 for asset_id in result["asset_ids"]]
    result.update(per_asset=per_asset, environment=maximum_result(per_asset, "environment"),
                  combined=maximum_result(per_asset, "combined"), evidence=weather,
                  electrical_anomaly=any(row["electrical_anomaly"] for row in per_asset),
                  dangerous_weather=any(row["dangerous_weather"] for row in per_asset))
    result["explanation"] = (f"{weather['wind_speed_mph']:g} mph wind, {weather['humidity_pct']:g}% humidity, "
                             f"{weather['ambient_temperature_f']:g}°F ambient. "
                             f"Environmental exposure {result['environment']['score']:.1f}/100; "
                             f"combined electrical/wildfire {result['combined']['score']:.1f}/100. "
                             f"{result['combined']['rule']}.")
    return result


def impact_agent(model: GridModel, asset_ids: list[str], stage: int) -> dict:
    if type(stage) is not int or stage not in STAGE_TIMESTAMPS:
        raise DataQualityError(f"Unknown scenario stage {stage!r}")
    impact = model.impact_for_assets(asset_ids)
    return dict(agent="Impact", stage=stage, timestamp=STAGE_TIMESTAMPS[stage],
                asset_ids=sorted(set(asset_ids)), circuit_ids=impact["circuit_ids"], impact=impact,
                explanation_mode="deterministic_template", data_quality="valid",
                limitations="Circuit-wide potential exposure, not feeder tracing or predicted outages",
                explanation=f"{impact['customers_at_risk']:,} unique customer accounts; "
                            f"{len(impact['critical_facilities'])} unique critical facilities; "
                            f"{impact['customers_interrupted']:,} currently interrupted. "
                            "Facility accounts are already included in customer totals.")


def response_agent(model: GridModel, circuit_id: str, stage: int, incident_id: str | None,
                   grid: dict, wildfire: dict, impact: dict) -> dict:
    result = finding("Response", model, circuit_id, stage)
    # Reject accidentally mixed evidence (e.g. stale findings from a previous stage).
    if any(item["stage"] != stage for item in (grid, wildfire, impact)):
        raise DataQualityError("Response findings must have the same stage")
    if grid["circuit_id"] != circuit_id or wildfire["circuit_id"] != circuit_id or impact["circuit_ids"] != [circuit_id]:
        raise DataQualityError("Response findings must refer to the same circuit")
    crew_ids = model.crews_for_circuit(circuit_id).crew_id.tolist()
    recommendation = propose_response(incident_id, stage, grid, wildfire, impact["impact"], crew_ids)
    result.update(recommendation=recommendation, explanation=recommendation["rationale"],
                  limitations=f"{LABEL}; recommendations require human review and execute nothing")
    return result
