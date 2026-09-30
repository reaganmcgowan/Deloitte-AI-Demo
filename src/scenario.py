"""Five deterministic snapshots and an idempotent incident registry; no actions.

Run python -m src.scenario for a readable walkthrough or add --json for evidence.
"""

import argparse
from copy import deepcopy
import json

from src.agents import grid_reliability_agent, wildfire_risk_agent, impact_agent, response_agent
from src.data_generator import STAGE_TIMESTAMPS
from src.ontology import DataQualityError, GridModel, load_data, validate_data
from src.risk_engine import LABEL, SEVERITY_THRESHOLDS, incident_priority

STAGE_LABELS = {1: "1:00 PM — baseline", 2: "2:00 PM — rising heat and demand",
                3: "3:00 PM — elevated grid utilization", 4: "3:30 PM — dangerous fire weather",
                5: "4:00 PM — T-882 electrical anomaly"}
# Each feeder has a different customer mix and load shape. Values are multipliers
# over that circuit's baseline load, not power-flow calculations.
OTHER_LOAD_MULTIPLIERS = {
    "C-185": {2: 1.08, 3: 1.17, 4: 1.12, 5: 1.08},
    "C-186": {2: 1.03, 3: 1.06, 4: 1.11, 5: 1.16},
    "C-187": {2: 1.10, 3: 1.18, 4: 1.26, 5: 1.31},
    "C-188": {2: 1.04, 3: 1.09, 4: 1.15, 5: 1.21},
    "C-189": {2: 1.06, 3: 1.13, 4: 1.08, 5: 1.04},
}
HERO_UTILIZATION = {2: 0.80, 3: 0.96, 4: 0.98, 5: 1.05}
TEMPERATURE_RISE_F = {
    "C-185": {2: 4, 3: 9, 4: 13, 5: 11},
    "C-186": {2: 3, 3: 7, 4: 12, 5: 16},
    "C-187": {2: 6, 3: 14, 4: 22, 5: 27},
    "C-188": {2: 5, 3: 10, 4: 16, 5: 21},
    "C-189": {2: 2, 3: 5, 4: 8, 5: 7},
}
CONDITION_DEGRADATION = {
    "C-185": {2: 1, 3: 2, 4: 3, 5: 3},
    "C-186": {2: 0, 3: 1, 4: 2, 5: 3},
    "C-187": {2: 2, 3: 4, 4: 7, 5: 9},
    "C-188": {2: 1, 3: 3, 4: 5, 5: 6},
    "C-189": {2: 0, 3: 1, 4: 1, 5: 2},
}
# Short-lived, circuit-specific equipment events make the synthetic day feel
# operationally distributed. They are deliberately resolved before 4:00 PM so
# C-184 remains the final critical exposure in this interview prototype.
ANOMALY_PROFILES = {
    "C-186": {3: {"load_multiplier": 1.50, "temperature_rise": 35}},
    "C-188": {4: {"load_multiplier": 1.75, "temperature_rise": 32}},
}
HERO_FINAL_TEMPERATURE_RISE_F = 65


def stage_tables(baseline: dict, stage: int) -> dict:
    """Derive each snapshot from baseline, never from the previous stage."""
    if type(stage) is not int or stage not in STAGE_TIMESTAMPS:
        raise DataQualityError(f"Unknown scenario stage {stage!r}")
    validate_data(baseline)
    tables = {name: frame.copy(deep=True) for name, frame in baseline.items()}
    if stage == 1:
        return tables
    circuits, assets = tables["circuits"], tables["assets"]
    for index, circuit in circuits.iterrows():
        baseline_load = float(circuit.current_load_mw)
        if baseline_load <= 0:
            raise DataQualityError("Scenario demand trend requires positive baseline circuit load")
        profile = ANOMALY_PROFILES.get(circuit.circuit_id, {}).get(stage, {})
        load = (float(circuit.capacity_mw) * HERO_UTILIZATION[stage] if circuit.circuit_id == "C-184"
                else baseline_load * profile.get("load_multiplier", OTHER_LOAD_MULTIPLIERS[circuit.circuit_id][stage]))
        load = round(load, 2)
        circuits.loc[index, "current_load_mw"] = load
        circuits.loc[index, "demand_trend_pct"] = (load / baseline_load - 1) * 100
        assets.loc[assets.circuit_id == circuit.circuit_id, "current_load_mw"] = load
    assets["temperature_f"] = assets.baseline_temperature_f + {1: 0, 2: 6, 3: 12, 4: 18, 5: 20}[stage]
    for circuit_id, rise_by_stage in TEMPERATURE_RISE_F.items():
        mask = assets.circuit_id == circuit_id
        rise = ANOMALY_PROFILES.get(circuit_id, {}).get(stage, {}).get("temperature_rise", rise_by_stage[stage])
        assets.loc[mask, "temperature_f"] = assets.loc[mask, "baseline_temperature_f"] + rise
        assets.loc[mask, "condition_score"] = (assets.loc[mask, "condition_score"] - CONDITION_DEGRADATION[circuit_id][stage]).clip(lower=0)
    if stage == 5:
        hero = assets.asset_id == "T-882"
        assets.loc[hero, "temperature_f"] = assets.loc[hero, "baseline_temperature_f"] + HERO_FINAL_TEMPERATURE_RISE_F
    validate_data(tables)
    return tables


class Scenario:
    """Forward-only in-memory scenario. Reset starts a new run at baseline.

    Run IDs are local counters, not persistent global identifiers. Evaluation only
    updates the evidence/incident registry; it cannot change operational state.
    """

    def __init__(self, baseline: dict | None = None):
        source = load_data() if baseline is None else baseline
        validate_data(source)
        self._baseline = {name: frame.copy(deep=True) for name, frame in source.items()}
        self._run_number = 0
        self.reset()

    @property
    def stage(self) -> int:
        return self._stage

    @property
    def run_id(self) -> str:
        return f"run-{self._run_number:03d}"

    @property
    def timestamp(self) -> str:
        return STAGE_TIMESTAMPS[self.stage]

    def reset(self) -> None:
        self._run_number += 1
        self._stage = 1
        self._incidents = {}

    def advance(self) -> dict:
        if self.stage == 5:
            raise DataQualityError("Already at final stage; use reset to replay")
        # Evaluate before advancing so first-detection metadata does not depend
        # on whether a caller separately rendered/evaluated the preceding stage.
        self.evaluate()
        self._stage += 1
        return self.evaluate()

    def baseline_tables(self) -> dict:
        return {name: frame.copy(deep=True) for name, frame in self._baseline.items()}

    def snapshot(self) -> dict:
        return stage_tables(self._baseline, self.stage)

    def evaluate(self) -> dict:
        tables = self.snapshot()
        model = GridModel(tables)
        findings, active_ids = {}, set()
        registry = deepcopy(self._incidents)
        for circuit_id in sorted(tables["circuits"].circuit_id):
            grid = grid_reliability_agent(model, circuit_id, self.stage)
            wildfire = wildfire_risk_agent(model, circuit_id, self.stage)
            impact = impact_agent(model, grid["asset_ids"], self.stage)
            response = response_agent(model, circuit_id, self.stage, None, grid, wildfire, impact)
            findings[circuit_id] = dict(grid=grid, wildfire=wildfire, impact=impact, response=response)
            categories = {"grid_strain": grid["grid_strain"],
                          "equipment_anomaly": grid["equipment_anomaly"],
                          "combined_wildfire": wildfire["combined"]}
            for category, risk in categories.items():
                if risk["score"] < SEVERITY_THRESHOLDS["ELEVATED"] or (category == "equipment_anomaly" and not grid["anomaly_asset_ids"]):
                    continue
                incident_id = f"{self.run_id}:{circuit_id}:{category}"
                active_ids.add(incident_id)
                previous = registry.get(incident_id)
                if category == "equipment_anomaly":
                    affected = grid["anomaly_asset_ids"]
                elif category == "combined_wildfire":
                    affected = [row["asset_id"] for row in wildfire["per_asset"]
                                if row["combined"]["score"] >= SEVERITY_THRESHOLDS["ELEVATED"]]
                else:
                    affected = grid["asset_ids"]
                incident_response = response_agent(model, circuit_id, self.stage, incident_id, grid, wildfire, impact)
                registry[incident_id] = dict(
                    incident_id=incident_id, run_id=self.run_id, category=category, circuit_id=circuit_id,
                    affected_asset_ids=affected, first_detected_stage=previous["first_detected_stage"] if previous else self.stage,
                    first_detected_timestamp=previous["first_detected_timestamp"] if previous else self.timestamp,
                    stage=self.stage, timestamp=self.timestamp, status="open",
                    score=risk["score"], severity=risk["severity"], risk=risk, impact=impact["impact"],
                    findings=dict(grid=grid, wildfire=wildfire, impact=impact, response=incident_response),
                    recommendation=incident_response["recommendation"],
                )
        for incident_id, incident in registry.items():
            if incident_id not in active_ids and incident["status"] == "open":
                incident.update(status="resolved", resolved_stage=self.stage)
        self._incidents = registry
        active = sorted((registry[key] for key in active_ids), key=incident_priority)
        impacted_assets = [asset for incident in active for asset in incident["affected_asset_ids"]]
        report = dict(run_id=self.run_id, stage=self.stage, timestamp=self.timestamp,
                      label=LABEL, findings=findings, incidents=active,
                      incident_history=sorted(registry.values(), key=lambda row: row["incident_id"]),
                      total_impact=model.impact_for_assets(impacted_assets))
        return deepcopy(report)  # Caller edits cannot corrupt future evaluations.


def format_stage(report: dict) -> str:
    hero = report["findings"]["C-184"]
    grid, wildfire = hero["grid"], hero["wildfire"]
    recommendation = hero["response"]["recommendation"]
    impact = report["total_impact"]
    lines = [STAGE_LABELS[report["stage"]],
             f"  C-184 indicators: grid {grid['grid_strain']['score']:.1f}, equipment {grid['equipment_anomaly']['score']:.1f}, "
             f"environment {wildfire['environment']['score']:.1f}, combined {wildfire['combined']['score']:.1f} / 100",
             f"  {grid['explanation']}", f"  {wildfire['explanation']}",
             f"  Open incidents: {len(report['incidents'])}; unique exposure: {impact['customers_at_risk']:,} accounts, "
             f"{len(impact['critical_facilities'])} facilities; interrupted: {impact['customers_interrupted']:,}",
             f"  Recommendation: {recommendation['primary']['title']}",
             f"  Benefit: {recommendation['primary']['expected_benefit']}",
             f"  Tradeoff: {recommendation['primary']['tradeoff']}",
             "  Alternatives: " + "; ".join(option["title"] for option in recommendation["alternatives"])]
    if recommendation["follow_up_review"]:
        lines.append("  Follow-up review: " + "; ".join(option["title"] for option in recommendation["follow_up_review"]))
    if report["incidents"]:
        lines.append("  Incident findings: " + "; ".join(
            f"{incident['circuit_id']} {incident['category']} {incident['severity']}"
            for incident in report["incidents"]))
        lines.append("  Exposed critical facilities: " + "; ".join(
            f"{facility['name']} ({facility['facility_type']})"
            for facility in impact["critical_facilities"]))
    lines.append("  Human review required. No action executed.")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline synthetic GridGuard Phases 4–6 demonstration")
    parser.add_argument("--json", action="store_true", help="Print full structured evidence for all five stages")
    args = parser.parse_args()
    scenario = Scenario()
    reports = [scenario.evaluate()]
    for _ in range(4):
        reports.append(scenario.advance())
    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        print(LABEL + ". Deterministic template mode.\n")
        print("\n\n".join(format_stage(report) for report in reports))


if __name__ == "__main__":
    main()
