"""Deterministic investigation workspace data for the Command Center prototype."""

from src.risk_engine import SEVERITY_ORDER
from src.evidence import sources_for_circuit
from src.retrieval import retrieve_passages
from src.evidence_quality import check_evidence_quality


def assessment_revision(field_report: bool, version: int, timestamp: str) -> dict:
    """Describe the evidence delta that produced the current assessment version."""
    if field_report:
        return {
            "version": version,
            "trigger": "FR-001 · synthetic field inspection report",
            "what_changed": "Field inspection reports visible equipment damage at T-882.",
            "assessment_change": "Escalation brief updated to treat the equipment anomaly as field-confirmed.",
            "still_unresolved": "Hospital backup-power readiness remains unverified.",
            "timestamp": timestamp,
        }
    return {
        "version": version,
        "trigger": "Initial synthetic case assembly",
        "what_changed": "Structured telemetry, relationship, procedure, and readiness records assembled.",
        "assessment_change": "C-184 is open for evidence review; no operational action is proposed automatically.",
        "still_unresolved": "Hospital backup-power readiness and T-882 inspection follow-up require verification.",
        "timestamp": timestamp,
    }


def investigation_queue(report: dict, tables: dict, field_report: bool = False) -> list[dict]:
    """Return prioritized cases with a visible reason and investigation status."""
    findings = report["findings"]
    hero = findings["C-184"]
    hero_score = max(hero["grid"]["grid_strain"]["score"], hero["wildfire"]["combined"]["score"])
    hero_status = "Awaiting review" if report["stage"] >= 5 else "Evidence gathering"
    hero_reason = "Electrical anomaly; hospital on circuit"
    if field_report:
        hero_reason = "Field report confirms equipment damage; hospital backup readiness remains unknown"
    cases = [
        dict(case_id="C-184", title="Circuit 184: equipment anomaly + fire weather",
             priority=1, score=hero_score, reason=hero_reason, status=hero_status,
             circuit_id="C-184", type="critical"),
        dict(case_id="T-884", title="Transformer T-884: abnormal temperature",
             priority=2, score=findings["C-186"]["grid"]["equipment_anomaly"]["score"],
             reason="Repeated temperature deviation", status="Field inspection pending",
             circuit_id="C-186", type="equipment"),
        dict(case_id="C-186", title="Circuit 186: rising load",
             priority=3, score=findings["C-186"]["grid"]["grid_strain"]["score"],
             reason="Capacity pressure", status="Monitoring; no additional evidence requested",
             circuit_id="C-186", type="load"),
    ]
    return sorted(cases, key=lambda case: (case["priority"], -case["score"]))


def assessment_workspace(report: dict, tables: dict, circuit_id: str,
                         field_report: bool = False, version: int = 1,
                         revision_history: list[dict] | None = None) -> dict:
    """Build the reviewable contract rendered by the investigation workspace.

    This keeps queue selection, evidence, unknowns, and response options tied to one
    assessment version.  It is intentionally descriptive: creating this object never
    changes grid state or approves an operational action.
    """
    case = next(item for item in investigation_queue(report, tables, field_report)
                if item["circuit_id"] == circuit_id)
    finding = report["findings"][circuit_id]
    impact = finding["impact"]["impact"]
    circuit = tables["circuits"].set_index("circuit_id").loc[circuit_id]
    evidence = evidence_records(report, tables, circuit_id, field_report)
    unknowns = investigation_unknowns(circuit_id, field_report)
    if finding["grid"]["anomaly_asset_ids"]:
        assessment = "Equipment anomaly detected during severe environmental conditions."
    else:
        assessment = "Electrical and environmental signals are being monitored; no equipment anomaly is confirmed."
    assessment += (f" {int(circuit.customers_served):,} accounts and "
                   f"{len(impact['critical_facilities'])} critical facilities are linked to this circuit.")
    if field_report and circuit_id == "C-184":
        assessment += " Field inspection evidence now confirms visible equipment damage; escalation brief updated."
    return {
        "case": case,
        "assessment": assessment,
        "assessment_version": version,
        "as_of": report["timestamp"],
        "evidence": evidence,
        "unknowns": unknowns,
        "options": response_options(circuit_id, report),
        "impact": {
            "customers": int(impact["customers_at_risk"]),
            "critical_facilities": [facility["facility_id"] for facility in impact["critical_facilities"]],
        },
        "decision_gate": "Preparation and review only; no PSPS authorization or grid action.",
        "revision": assessment_revision(field_report, version, report["timestamp"]),
        "revision_history": list(revision_history or [assessment_revision(False, 1, report["timestamp"])]),
        "retrieved_passages": retrieve_passages(
            "critical facility backup readiness abnormal equipment field confirmation",
            circuit_id, report["timestamp"], field_report),
        "evidence_quality": check_evidence_quality(circuit_id, report["timestamp"], field_report),
    }


def evidence_records(report: dict, tables: dict, circuit_id: str, field_report: bool = False) -> list[dict]:
    """Evidence is deliberately separated from interpretation and unknowns."""
    finding = report["findings"][circuit_id]
    grid, wildfire, impact = finding["grid"], finding["wildfire"], finding["impact"]
    telemetry = tables["circuits"].set_index("circuit_id").loc[circuit_id]
    records = [
        dict(kind="Recorded fact", source_id=f"TEL-{circuit_id}-CIRCUIT", source="Synthetic circuit telemetry",
             owner="Grid operations", timestamp=report["timestamp"], freshness_status="live",
             freshness_window="live snapshot", text=f"{circuit_id} load {telemetry.current_load_mw:.2f} MW; capacity {telemetry.capacity_mw:.2f} MW."),
        dict(kind="Recorded fact", source_id=f"TEL-{circuit_id}-ASSETS", source="Synthetic asset telemetry",
             owner="Grid operations", timestamp=report["timestamp"], freshness_status="live",
             freshness_window="live snapshot", text=f"Assets checked: {', '.join(grid['asset_ids'])}; anomalies: {', '.join(grid['anomaly_asset_ids']) or 'none detected'}."),
        dict(kind="Recorded fact", source_id=f"TEL-{circuit_id}-WEATHER", source="Synthetic weather observation",
             owner="Weather service", timestamp=wildfire["evidence"]["timestamp"], freshness_status="live",
             freshness_window="stage observation", text=f"{wildfire['evidence']['wind_speed_mph']:.0f} mph wind · {wildfire['evidence']['humidity_pct']:.0f}% humidity · {wildfire['evidence']['ambient_temperature_f']:.0f}°F."),
        dict(kind="Recorded fact", source_id=f"MODEL-{circuit_id}-IMPACT", source="Relationship model",
             owner="GridGuard model", timestamp=report["timestamp"], freshness_status="derived",
             freshness_window="recomputed each stage", text=f"Circuit exposure: {impact['impact']['customers_at_risk']:,} accounts and {len(impact['impact']['critical_facilities'])} critical facilities."),
        dict(kind="AI interpretation", source_id=f"MODEL-{circuit_id}-WILDFIRE", source="Deterministic risk engine",
             owner="GridGuard model", timestamp=report["timestamp"], freshness_status="derived",
             freshness_window="recomputed each stage", text=f"Environmental conditions increase consequence if an energized anomaly exists; combined indicator is {wildfire['combined']['score']:.1f}/100."),
    ]
    for source in sources_for_circuit(circuit_id, report["timestamp"], field_report):
        kind = "Synthetic field report" if source["source_type"] == "field_inspection_report" else "Recorded fact"
        records.append(dict(kind=kind, source_id=source["source_id"], source=source["source_type"],
                            owner=source["owner"], timestamp=source["timestamp"],
                            freshness_status=source["freshness_status"], freshness_window=source["freshness_window"],
                            text=source["text"] + (" Report is scripted prototype evidence." if source["source_id"] == "FR-001" else "")))
    if field_report and circuit_id == "C-184":
        records.append(dict(kind="AI interpretation", source="Investigation synthesis",
                            source_id="SYNTHESIS-C184-V2", owner="GridGuard model", freshness_status="derived",
                            freshness_window="assessment version", timestamp=report["timestamp"], text="Escalation brief updated because field evidence confirms the anomaly; facility backup readiness is still unresolved."))
    return records


def investigation_unknowns(circuit_id: str, field_report: bool = False) -> list[dict]:
    if circuit_id == "C-184":
        return [
            dict(question="Hospital backup-power readiness", why="Determines whether the critical facility has resilience if service is interrupted.", owner="Facility liaison", status="Unverified"),
            dict(question="T-882 maintenance history and inspection note", why="Confirms whether the temperature deviation is recurring or newly emergent.", owner="Asset maintenance", status="Verified by field report" if field_report else "Pending record review"),
        ]
    return [dict(question="Most recent field inspection", why="Confirms whether the temperature deviation requires physical intervention.", owner="Field operations", status="Pending")]


def response_options(circuit_id: str, report: dict) -> list[dict]:
    finding = report["findings"][circuit_id]
    crews = finding["response"]["recommendation"]["primary"].get("candidate_crew_ids", [])
    options = [
        dict(action="Request missing information", evidence="Open unknowns and facility/maintenance ownership", tradeoff="Delays escalation until verification returns", prerequisites="Assign owner and set response deadline"),
        dict(action="Review escalation brief", evidence=finding["response"]["recommendation"]["rationale"], tradeoff="Escalates attention without changing grid state", prerequisites="Operator confirms evidence version and audience"),
        dict(action="Approve proposed next step", evidence=finding["response"]["recommendation"]["primary"]["title"], tradeoff=finding["response"]["recommendation"]["primary"]["tradeoff"], prerequisites="Human approval; recheck crew availability" + (f" ({', '.join(crews)})" if crews else "")),
        dict(action="Reject proposed next step", evidence="Current assessment and unresolved information", tradeoff="Leaves the case open without advancing the proposed preparation step", prerequisites="Operator rationale and follow-up owner"),
    ]
    options.insert(3, dict(action="Revise assessment", evidence="Recorded facts, interpretations, and unresolved questions", tradeoff="Keeps the case open while changing its framing or priority", prerequisites="Operator rationale and a new assessment version"))
    return options
