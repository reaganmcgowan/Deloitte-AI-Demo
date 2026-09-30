"""Proposal construction only. No execution, dispatch, or state mutation exists here."""

from src.risk_engine import SEVERITY_ORDER

ACTION_DETAILS = {
    "monitor": ("Continue monitoring", "Preserves electricity and crew availability", "Current exposure remains; monitoring does not repair equipment"),
    "prepare_load_redistribution": ("Prepare load redistribution study", "Allows review of potential capacity relief", "No relief is achieved yet; feasibility requires engineering review"),
    "dispatch_inspection": ("Propose inspection response", "Could obtain field evidence after human approval", "Uses crew capacity; inspection alone does not repair equipment or eliminate exposure"),
    "escalate": ("Escalate for operator review", "Brings the evidence to an operator for coordination", "Escalation itself does not reduce electrical or environmental exposure"),
    "prepare_deenergization_review": ("Prepare targeted de-energization review", "Allows an operator to compare potential exposure reduction against outage consequences", "Preparation changes no power state; a separate future shutoff decision could interrupt customers and critical facilities"),
}


def propose_response(incident_id: str | None, stage: int, grid: dict, wildfire: dict,
                     impact: dict, eligible_crew_ids: list[str]) -> dict:
    """Return evidence-linked options; a candidate crew is never assigned/reserved."""
    crew_ids = sorted(eligible_crew_ids)
    critical = wildfire["combined"]["severity"] == "CRITICAL"
    electrical_severity = max((grid["grid_strain"]["severity"], grid["equipment_anomaly"]["severity"]),
                              key=SEVERITY_ORDER.get)
    if critical or SEVERITY_ORDER[electrical_severity] >= SEVERITY_ORDER["HIGH"]:
        primary = "dispatch_inspection" if crew_ids else "escalate"
    elif electrical_severity == "ELEVATED":
        primary = "prepare_load_redistribution"
    else:
        primary = "monitor"

    def option(action: str) -> dict:
        title, benefit, tradeoff = ACTION_DETAILS[action]
        prerequisites = ["Explicit human review and approval before any future simulated action"]
        if action == "dispatch_inspection":
            prerequisites.append("Recheck crew availability, same-zone coverage, and electrical_inspection skill at approval time")
        if action == "prepare_load_redistribution":
            prerequisites.append("Engineering feasibility review; no power-flow model is provided")
        return dict(action_type=action, title=title, prerequisites=prerequisites,
                    expected_benefit=benefit, tradeoff=tradeoff,
                    candidate_crew_ids=crew_ids if action == "dispatch_inspection" else [],
                    requires_human_approval=True)

    alternatives = ["monitor", "escalate"] if primary != "monitor" else ["escalate"]
    if critical:
        alternatives.append("prepare_deenergization_review")
    alternatives = [option(action) for action in alternatives if action != primary]
    evidence = dict(grid_score=grid["grid_strain"]["score"],
                    equipment_score=grid["equipment_anomaly"]["score"],
                    environmental_score=wildfire["environment"]["score"],
                    combined_score=wildfire["combined"]["score"],
                    electrical_anomaly=wildfire["electrical_anomaly"],
                    dangerous_weather=wildfire["dangerous_weather"],
                    customers_at_risk=impact["customers_at_risk"],
                    facility_ids=[facility["facility_id"] for facility in impact["critical_facilities"]],
                    eligible_crew_ids=crew_ids)
    rationale = (f"Grid strain {evidence['grid_score']:.1f}/100, equipment {evidence['equipment_score']:.1f}/100, "
                 f"environment {evidence['environmental_score']:.1f}/100, combined {evidence['combined_score']:.1f}/100. "
                 f"Electrical anomaly: {evidence['electrical_anomaly']}; dangerous weather: {evidence['dangerous_weather']}. "
                 f"Circuit-wide exposure: {impact['customers_at_risk']:,} customer accounts and "
                 f"{len(evidence['facility_ids'])} critical facilities. "
                 + ("No eligible inspection crew is available. " if not crew_ids else "")
                 + "Template explanation; no action has executed.")
    return dict(recommendation_id=f"{incident_id or grid['circuit_id'] + ':assessment'}:response", revision=stage, incident_id=incident_id,
                approval_status="awaiting_human_review", explanation_mode="deterministic_template",
                primary=option(primary), alternatives=alternatives,
                follow_up_review=[option("escalate"), option("prepare_deenergization_review")] if critical else [],
                evidence=evidence, rationale=rationale, executed=False)
