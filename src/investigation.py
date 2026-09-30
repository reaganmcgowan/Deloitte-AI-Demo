"""Deterministic investigation workspace data for the Command Center prototype."""

from src.risk_engine import SEVERITY_ORDER


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


def evidence_records(report: dict, tables: dict, circuit_id: str, field_report: bool = False) -> list[dict]:
    """Evidence is deliberately separated from interpretation and unknowns."""
    finding = report["findings"][circuit_id]
    grid, wildfire, impact = finding["grid"], finding["wildfire"], finding["impact"]
    records = [
        dict(kind="Recorded fact", source="Synthetic circuit telemetry",
             timestamp=report["timestamp"], text=f"{circuit_id} load {tables['circuits'].set_index('circuit_id').loc[circuit_id, 'current_load_mw']:.2f} MW; capacity {tables['circuits'].set_index('circuit_id').loc[circuit_id, 'capacity_mw']:.2f} MW."),
        dict(kind="Recorded fact", source="Synthetic asset telemetry",
             timestamp=report["timestamp"], text=f"Assets checked: {', '.join(grid['asset_ids'])}; anomalies: {', '.join(grid['anomaly_asset_ids']) or 'none detected'}."),
        dict(kind="Recorded fact", source="Synthetic weather observation",
             timestamp=wildfire["evidence"]["timestamp"], text=f"{wildfire['evidence']['wind_speed_mph']:.0f} mph wind · {wildfire['evidence']['humidity_pct']:.0f}% humidity · {wildfire['evidence']['ambient_temperature_f']:.0f}°F."),
        dict(kind="Recorded fact", source="Relationship model",
             timestamp=report["timestamp"], text=f"Circuit exposure: {impact['impact']['customers_at_risk']:,} accounts and {len(impact['impact']['critical_facilities'])} critical facilities."),
        dict(kind="AI interpretation", source="Deterministic risk engine",
             timestamp=report["timestamp"], text=f"Environmental conditions increase consequence if an energized anomaly exists; combined indicator is {wildfire['combined']['score']:.1f}/100."),
        dict(kind="Procedure excerpt", source="Procedure 7.2 · synthetic operating procedure",
             timestamp="2026-08-15T12:00:00-07:00", text="Before approving escalation, verify critical-facility backup readiness and obtain field confirmation for abnormal equipment."),
    ]
    if field_report and circuit_id == "C-184":
        records.append(dict(kind="Synthetic field report", source="FR-001 · field inspection simulation",
                            timestamp=report["timestamp"], text="Visible equipment damage reported at T-882; report is scripted prototype evidence."))
        records.append(dict(kind="AI interpretation", source="Investigation synthesis",
                            timestamp=report["timestamp"], text="Escalation brief updated because field evidence confirms the anomaly; facility backup readiness is still unresolved."))
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
    ]
    options.append(dict(action="Revise assessment", evidence="Recorded facts, interpretations, and unresolved questions", tradeoff="Keeps the case open while changing its framing or priority", prerequisites="Operator rationale and a new assessment version"))
    return options
