"""Focused operational overview with continuous synthetic-day playback."""
import functools
import logging
import time

import streamlit as st

from src.command_center import (CATEGORY_LABELS, RISK_LAYERS, activity_frame, geographic_figure,
                                agent_graph_figure, agent_reasoning_frame, heatmap_figure,
                                network_figure, queue_frame, strain_figure,
                                utilization_rank_figure)
from src.live_scenario import LiveScenario, demand_drivers
from src.investigation import assessment_workspace, investigation_queue, investigation_unknowns
from src.decision_workflow import append_decision
from src.ontology import DataQualityError
from src.playback import Playback, PAUSE_REASONS, CHECKPOINT_MINUTES
from src.risk_engine import SEVERITY_ORDER

st.set_page_config(page_title="GridGuard | Command Center", page_icon="⚡", layout="wide")
LOGGER = logging.getLogger("gridguard.dashboard")
st.markdown("""<style>
[data-testid="stMainBlockContainer"] {padding-top:1rem; max-width:1180px;}
[data-testid="stMetricLabel"] p {white-space:normal;}
[data-testid="stMetricValue"] {font-size:1.65rem;}
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {flex-wrap:wrap;}
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {min-width:130px;flex:1 1 130px;}
h1 {color:#18394a;} h3 {color:#294963;}
[data-testid="stMetric"] {background:#f0f5f7;border-radius:10px;padding:12px;}
</style>""", unsafe_allow_html=True)
st.title("⚡ GridGuard")
st.caption("AI-powered grid risk & resilience command center")
st.markdown("<span style='display:inline-block;background:#e7eef1;color:#294963;border-radius:999px;padding:3px 10px;font-size:.72rem;font-weight:700;letter-spacing:.04em'>DEMO · SYNTHETIC DATA</span>", unsafe_allow_html=True)


def evidence_display_name(record: dict) -> str:
    """Use short, operator-friendly names while retaining canonical source IDs."""
    source_id = record.get("source_id", "")
    if source_id.startswith("TEL-") and source_id.endswith("-CIRCUIT"):
        return "Circuit telemetry"
    if source_id.startswith("TEL-") and source_id.endswith("-ASSETS"):
        return "Asset telemetry"
    if source_id.startswith("TEL-") and source_id.endswith("-WEATHER"):
        return "Weather observation"
    if source_id.startswith("MODEL-") and source_id.endswith("-IMPACT"):
        return "Customer & facility impact model"
    if source_id.startswith("MODEL-") and source_id.endswith("-WILDFIRE"):
        return "Environmental risk model"
    labels = {
        "MAINT-T882-20260814-01": "T-882 maintenance note",
        "FAC-F001-READINESS-20260814-01": "Hospital readiness record",
        "PROC-7.2-20260815-01": "Escalation procedure excerpt",
        "FR-001": "Field inspection report",
        "SYNTHESIS-C184-V2": "Assessment revision",
    }
    return labels.get(source_id, record.get("source", source_id).replace("_", " ").title())


def _dashboard_error_boundary(function):
    """Keep a transition/rendering exception visible instead of yielding a blank app."""
    @functools.wraps(function)
    def guarded():
        try:
            return function()
        except DataQualityError as error:
            LOGGER.exception("GridGuard data-quality failure during dashboard render")
            st.error(f"GridGuard could not render this scenario state: {error}")
        except Exception as error:  # pragma: no cover - exercised by Streamlit runtime
            LOGGER.exception("GridGuard unexpected dashboard failure")
            st.error(f"GridGuard could not render this transition: {type(error).__name__}: {error}")
            st.caption("Use Reset to return to the initial checkpoint, then try Continue again.")
    return guarded


def reset_scenario():
    st.session_state.scenario.reset()
    st.session_state.playback = Playback(minutes_per_second=st.session_state.get("speed", 6))
    for key in ("report", "tables", "selected_incident", "investigation_case", "stage_reports", "sample_minute", "data_error", "field_report", "decision_log", "assessment_version", "assessment_history"):
        st.session_state.pop(key, None)


def introduce_field_report():
    if st.session_state.get("field_report", False):
        return
    st.session_state.field_report = True
    st.session_state.assessment_version = st.session_state.get("assessment_version", 1) + 1
    timestamp = st.session_state.get("report", {}).get("timestamp", "synthetic scenario time")
    st.session_state.setdefault("assessment_history", []).append({
        "version": st.session_state.assessment_version,
        "trigger": "FR-001 · synthetic field inspection report",
        "what_changed": "Field inspection reports visible equipment damage at T-882.",
        "assessment_change": "Escalation brief updated to treat the equipment anomaly as field-confirmed.",
        "still_unresolved": "Hospital backup-power readiness remains unverified.",
        "timestamp": timestamp,
    })


def record_decision(action: str, case_id: str, timestamp: str):
    workspace = assessment_workspace(st.session_state.report, st.session_state.tables, case_id,
                                     st.session_state.get("field_report", False),
                                     st.session_state.get("assessment_version", 1),
                                     st.session_state.get("assessment_history", []))
    append_decision(st.session_state.setdefault("decision_log", []), action=action,
                    case_id=case_id, assessment_version=workspace["assessment_version"],
                    evidence_ids=[row["source_id"] for row in workspace["evidence"]],
                    rationale=st.session_state.get("decision_rationale", ""), timestamp=timestamp)


def seek_time():
    minute = st.session_state.time_slider
    if minute < st.session_state.playback.minutes:
        reset_scenario()
    st.session_state.playback.seek(minute)


def change_speed():
    # Anchor a new rate at the moment of choice, not at an old tick.
    st.session_state.playback.minutes_per_second = st.session_state.speed
    if st.session_state.playback.running:
        st.session_state.playback.last_tick = time.monotonic()


def resume_playback():
    st.session_state.playback.resume(time.monotonic())


def pause_playback():
    st.session_state.playback.pause()


def focus_highest_priority():
    incidents = st.session_state.report["incidents"]
    if incidents:
        st.session_state.selected_incident = incidents[0]["incident_id"]


def about_page():
    """Interview-ready orientation page; the dashboard remains the default tab."""
    st.header("About GridGuard")
    st.subheader("The problem")
    st.write(
        "During a fast-moving heat and wildfire-weather event, a utility operator may need "
        "to decide whether an abnormal transformer reading is an isolated equipment issue, "
        "a reliability concern, or part of a larger ignition and customer-impact risk. The "
        "facts needed for that decision are split across systems: circuit load and capacity, "
        "asset telemetry and maintenance history, weather and fire-risk zones, customer and "
        "critical-facility relationships, crew availability, procedures, and field reports."
    )
    st.write(
        "The hard part is not producing another score. It is assembling a current, circuit-level "
        "picture quickly enough to answer four operational questions: What changed? Who could be "
        "affected? Which evidence is recorded, stale, or missing? What reviewable next step should "
        "an authorized operator consider? Without that shared picture, teams can duplicate analysis, "
        "miss a critical facility, overreact to weather alone, or make a recommendation that cannot "
        "be traced back to its sources."
    )
    st.subheader("What this prototype demonstrates")
    st.write(
        "GridGuard is an evidence-first command center for investigating grid and "
        "wildfire exposure. It joins those records into a traceable assessment, shows "
        "how bounded agents reason over the evidence, and keeps the final decision with "
        "a human operator."
    )
    st.caption("DEMO · SYNTHETIC DATA · deterministic prototype indicators, not validated probabilities")

    st.subheader("Related reading")
    st.caption("These public references describe the operating context this prototype is designed to make easier to investigate.")
    reading = st.columns(3)
    with reading[0]:
        st.markdown("**[DOE · Current Practices in Distribution Utility Resilience Planning for Wildfires](https://www.energy.gov/sites/default/files/2024-10/UtilityResiliencePlanningPracticesforHazards-Wildfire.pdf)**")
        st.caption("A utility-focused case-study report on anticipating, absorbing, and recovering from wildfire hazards. It relates to GridGuard’s circuit context, environmental evidence, and preparation-for-review workflow.")
    with reading[1]:
        st.markdown("**[DOE · Power System Impacts from Wildfires](https://www.energy.gov/oe/articles/us-department-energy-has-critical-role-power-system-impacts-wildfires)**")
        st.caption("Describes the need for higher-cadence wildfire data, shared access protocols, and common operating pictures. That is the coordination gap GridGuard’s evidence trail is meant to demonstrate.")
    with reading[2]:
        st.markdown("**[GAO · Electricity Grid Resilience and Climate Change](https://www.gao.gov/products/gao-21-423t)**")
        st.caption("Explains how wildfire and extreme weather can affect transmission, distribution, demand, outages, and infrastructure costs. It provides the broader resilience context for the demo scenario.")

    st.subheader("Why this can be a solution")
    st.write(
        "GridGuard is designed as an evidence-to-decision layer for the moment between "
        "detection and operator action. It does not replace a utility’s control systems or "
        "claim to predict a wildfire. It reduces the work required to assemble a defensible "
        "case and makes the remaining uncertainty explicit."
    )
    solution_points = st.columns(2)
    with solution_points[0]:
        st.markdown("**What is differentiated**")
        st.markdown(
            "- **Cross-system investigation:** joins electrical, environmental, relationship, and operational evidence around one circuit and incident.\n"
            "- **Evidence before explanation:** every interpretation has a source, timestamp, freshness status, or visible unknown.\n"
            "- **Consequence-aware reasoning:** connects an equipment signal to unique customers and critical facilities instead of showing an isolated risk score.\n"
            "- **Inspectable agent workflow:** each bounded agent shows what it pulled, what it calculated, and what it passed downstream."
        )
    with solution_points[1]:
        st.markdown("**How it could become a production capability**")
        st.markdown(
            "- Connect the same contracts to approved telemetry, weather, maintenance, GIS, outage, and facility systems.\n"
            "- Replace synthetic rules with validated utility models, thresholds, and governance-approved procedures.\n"
            "- Keep the evidence lineage, uncertainty checks, assessment versions, and operator approvals as the control boundary.\n"
            "- Measure value through faster triage, fewer duplicated reviews, better critical-facility visibility, and more defensible decisions."
        )
    st.info("The prototype’s core proposition: turn fragmented, changing evidence into a shared and reviewable investigation package—without allowing an agent to operate the grid.")

    st.subheader("How the workflow works")
    flow = st.columns([1.1, .18, 1.1, .18, 1.1, .18, 1.1, .18, 1.25])
    flow_items = [
        ("1", "Evidence", "Telemetry, weather, assets, customers, facilities, maintenance, procedures, and crews", "#2f6680"),
        ("→", "", "", "#9aaab4"),
        ("2", "Four agents", "Grid · Wildfire · Impact · Response", "#b9822b"),
        ("→", "", "", "#9aaab4"),
        ("3", "Investigation", "Detect → Context → Impact → Decide", "#6675a8"),
        ("→", "", "", "#9aaab4"),
        ("4", "Evidence trail", "Sources, freshness, calculations, unknowns, revisions", "#6b5b95"),
        ("→", "", "", "#9aaab4"),
        ("5", "Human review", "Approve, modify, reject, or request information", "#15803d"),
    ]
    for column, (number, title, detail_text, color) in zip(flow, flow_items):
        with column:
            if title:
                st.markdown(
                    f"<div style='border-top:4px solid {color};background:#f0f5f7;border-radius:0 0 9px 9px;"
                    f"padding:10px 9px;min-height:108px'><div style='font-size:1.25rem;font-weight:700;color:{color}'>{number}</div>"
                    f"<div style='font-weight:700'>{title}</div><div style='font-size:.78rem;color:#52636d'>{detail_text}</div></div>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(f"<div style='text-align:center;padding-top:42px;font-size:1.5rem;color:{color}'>{number}</div>", unsafe_allow_html=True)

    with st.expander("What information is included", expanded=False):
        st.markdown(
            "- **Grid and asset telemetry:** load, capacity, utilization, temperature, condition, and anomaly gates.\n"
            "- **Environmental context:** wind, humidity, ambient heat, and fire-risk zone.\n"
            "- **Impact relationships:** unique customer accounts and critical facilities linked to each circuit.\n"
            "- **Operational context:** maintenance notes, procedure excerpts, facility readiness, and eligible crews.\n"
            "- **Review record:** source IDs, timestamps, freshness, calculations, unresolved questions, assessment versions, and decision rationale."
        )
    with st.expander("Agent responsibilities", expanded=False):
        st.markdown(
            "- **Grid Agent:** evaluates utilization, demand trend, equipment condition, and electrical anomalies.\n"
            "- **Wildfire Agent:** evaluates environmental exposure and applies the electrical-anomaly gate.\n"
            "- **Impact Agent:** traverses relationships and deduplicates customers and facilities.\n"
            "- **Response Agent:** prepares evidence-backed options, alternatives, tradeoffs, and prerequisites."
        )
    st.info("The Command Center tab opens by default. Use this About tab to frame the problem, then switch to the dashboard to run the investigation.")


# The dashboard contains several large Plotly figures and an optional street-map
# tile layer. Repainting the entire fragment every second eventually overwhelms
# the browser after Reset/Continue cycles. Two seconds keeps playback responsive
# while bounding frontend render pressure; manual controls still rerun immediately.
@st.fragment(run_every="2s")
@_dashboard_error_boundary
def dashboard():
    try:
        # Upgrade a running older UI session without mixing old/new playback models.
        if not isinstance(st.session_state.get("scenario"), LiveScenario):
            st.session_state.scenario = LiveScenario()
            st.session_state.playback = Playback(minutes_per_second=st.session_state.get("speed", 6))
            st.session_state.stage_reports = {}
            st.session_state.pop("report", None)
        st.session_state.setdefault("field_report", False)
        st.session_state.setdefault("decision_log", [])
        st.session_state.setdefault("assessment_version", 1)
        st.session_state.setdefault("assessment_history", [])
        scenario = st.session_state.scenario
        playback = st.session_state.playback
        playback.tick(time.monotonic())
        minute = min(180, int(playback.minutes))
        if "report" not in st.session_state or st.session_state.get("sample_minute") != minute:
            # Preserve reached checkpoints for the heat map even when the slider jumps.
            history = st.session_state.setdefault("stage_reports", {})
            for stage, at in enumerate(CHECKPOINT_MINUTES, 1):
                if at <= minute and stage not in history:
                    history[stage] = scenario.seek(at)
            st.session_state.report = scenario.seek(minute)
            st.session_state.tables = scenario.snapshot()
            st.session_state.sample_minute = minute
        report, tables = st.session_state.report, st.session_state.tables
    except DataQualityError as error:
        st.error(f"Data quality issue: {error}")
        return

    controls = st.columns([1, 1, 1, 2])
    controls[0].subheader(playback.time_label)
    with controls[1]:
        if playback.running:
            st.button("Pause", key="pause_playback", on_click=pause_playback, width="stretch")
        elif not playback.finished:
            st.button("Start day" if minute == 0 else "Continue", key="resume_playback", on_click=resume_playback,
                      type="primary", width="stretch")
        else:
            st.caption("Day complete")
    controls[2].button("Reset", key="reset_scenario", on_click=reset_scenario, width="stretch")
    with controls[3]:
        st.select_slider("Playback speed · simulated min/sec", options=[1,3,6,12], value=6, key="speed", on_change=change_speed)
    st.session_state.time_slider = minute
    st.slider("Time of day · minutes after 1 PM", 0, 180, key="time_slider", on_change=seek_time,
              help="Drag to explore. Moving backward starts a new run and clears future history.")
    if not playback.running and minute in CHECKPOINT_MINUTES:
        st.info(PAUSE_REASONS[playback.checkpoint])
    st.caption("Smooth synthetic measurements · automatic pauses at key moments · drag backward to replay")

    cases = investigation_queue(report, tables, st.session_state.field_report)
    unknown_count = len(investigation_unknowns("C-184", st.session_state.field_report))
    awaiting = sum(case["status"] in {"Awaiting review", "Field inspection pending"} for case in cases)
    total_impact = report["total_impact"]
    hero_finding = report["findings"]["C-184"]
    hero_score = max(hero_finding["grid"]["grid_strain"]["score"],
                     hero_finding["grid"]["equipment_anomaly"]["score"],
                     hero_finding["wildfire"]["combined"]["score"])
    if hero_score >= 75:
        hero_color, hero_label = "#b42318", "CRITICAL"
    elif hero_score >= 55:
        hero_color, hero_label = "#d97706", "ELEVATED"
    elif hero_score >= 30:
        hero_color, hero_label = "#ca8a04", "WATCH"
    else:
        hero_color, hero_label = "#15803d", "STABLE"

    st.header("Command Center")
    kpis = st.columns(4)
    kpis[0].metric("Grid Health", f"{max(0, 100 - hero_score):.0f}/100", "Synthetic indicator")
    kpis[1].metric("Active Risks", len(report["incidents"]))
    kpis[2].metric("Customers at Risk", f"{int(total_impact['customers_at_risk']):,}")
    kpis[3].metric("Critical Facilities at Risk", len(total_impact["critical_facilities"]))

    map_column, queue_column = st.columns([2.2, 1], gap="large")
    with map_column:
        st.subheader("Grid risk map")
        layer = st.selectbox("Map layer", list(RISK_LAYERS), index=1, key="risk_layer")
        show_basemap = st.checkbox("Street map background · internet required", value=True, key="show_basemap")
        st.plotly_chart(geographic_figure(report, tables, layer, show_basemap), key="command_center_map", width="stretch")
        st.caption("Synthetic service areas around Santa Clarita. Select a case to inspect its evidence.")
    with queue_column:
        st.subheader("AI priority queue")
        st.caption("Why attention is needed, in plain language")
        queue_rows = [{"Priority": case["priority"], "Incident": case["title"], "Reason": case["reason"], "Status": case["status"]} for case in cases]
        for case in cases:
            color = {1: "#c43d4c", 2: "#d97706", 3: "#b9822b"}.get(case["priority"], "#2f6680")
            st.markdown(f"<div style='border-left:5px solid {color};background:#f5f7f8;border-radius:7px;padding:7px 10px;margin-bottom:6px'>"
                        f"<b>{case['title']}</b><br><span style='font-size:.82rem'>{case['reason']}</span><br>"
                        f"<span style='font-size:.76rem;color:#52636d'>{case['status']}</span></div>", unsafe_allow_html=True)
        with st.expander("Queue details", expanded=False):
            st.dataframe(queue_rows, hide_index=True, width="stretch")
        with st.container(border=True):
            st.markdown(f"<div style='border-left:8px solid {hero_color};padding:8px 12px;'>"
                        f"<div style='color:{hero_color};font-weight:700;font-size:1.05rem'>{hero_label} — Circuit 184</div>"
                        "<div style='font-weight:600'>Electrical anomaly + severe fire-weather conditions</div>"
                        f"<div><b>8,420 customers at risk · 1 hospital</b></div></div>", unsafe_allow_html=True)
            if hero_finding["grid"]["anomaly_asset_ids"]:
                st.caption("An equipment anomaly is confirmed while environmental conditions increase consequence.")
            elif hero_finding["wildfire"]["environment"]["score"] >= 50:
                st.caption("Environmental risk is elevated, but no electrical anomaly has been detected. Continue monitoring.")
            else:
                st.caption("Circuit 184 is currently stable. Continue monitoring.")
        st.caption(f"Risk state changes through the day: green → yellow → orange → red · {report['timestamp']}")

    with st.expander("Investigation workflow metrics", expanded=False):
        workflow_metrics = st.columns(3)
        workflow_metrics[0].metric("Open investigations", len(cases))
        workflow_metrics[1].metric("Cases awaiting review", awaiting)
        workflow_metrics[2].metric("Unresolved information requests", unknown_count)

    case_ids = [case["case_id"] for case in cases]
    current_case = st.session_state.get("investigation_case", case_ids[0])
    if current_case not in case_ids:
        current_case = case_ids[0]
    selected_case_id = st.selectbox("Open investigation", case_ids, index=case_ids.index(current_case), key="investigation_case",
                                   format_func=lambda case_id: next(case["title"] for case in cases if case["case_id"] == case_id))
    selected_case = next(case for case in cases if case["case_id"] == selected_case_id)
    if selected_case_id == "C-184":
        st.button("Introduce new field report", key="introduce_field_report", on_click=introduce_field_report)
        if st.session_state.field_report:
            st.success("Synthetic field report FR-001 is available. Assessment version updated; hospital backup readiness remains unresolved.")
    selected = next((incident for incident in report["incidents"] if incident["circuit_id"] == selected_case["circuit_id"]), None)
    circuit_id = selected_case["circuit_id"]

    st.caption("A circuit (for example, C-184) is a feeder serving a defined geographic service area. Its substation, transformer, and distribution line are linked assets; this prototype models circuit-wide exposure rather than detailed power-flow paths.")

    if not st.session_state.assessment_history:
        st.session_state.assessment_history = [workspace_initial := {
            "version": 1,
            "trigger": "Initial synthetic case assembly",
            "what_changed": "Structured telemetry, relationship, procedure, and readiness records assembled.",
            "assessment_change": "C-184 is open for evidence review; no operational action is proposed automatically.",
            "still_unresolved": "Hospital backup-power readiness and T-882 inspection follow-up require verification.",
            "timestamp": report["timestamp"],
        }]
    workspace = assessment_workspace(report, tables, circuit_id, st.session_state.field_report,
                                     st.session_state.assessment_version,
                                     st.session_state.assessment_history)
    findings = report["findings"][circuit_id]
    grid, wildfire = findings["grid"], findings["wildfire"]
    circuit = tables["circuits"].set_index("circuit_id").loc[circuit_id]
    overview, agents, detail, source_files = st.tabs(["Overview", "Agent activity", "Technical evidence", "Evidence files"])
    st.header(f"Investigation workspace · {selected_case['title']}")
    stage_columns = st.columns(4)
    investigation_stages = [
        ("1", "Detect", "Signal identified", "#2f6680"),
        ("2", "Context", "Weather + asset evidence", "#b9822b"),
        ("3", "Impact", f"{int(findings['impact']['impact']['customers_at_risk']):,} accounts · {len(findings['impact']['impact']['critical_facilities'])} facility", "#6675a8"),
        ("4", "Decide", "Human review required", "#6b5b95"),
    ]
    for column, (number, label, detail_text, color) in zip(stage_columns, investigation_stages):
        with column:
            st.markdown(f"<div style='border-top:4px solid {color};padding:6px 8px;background:#f5f7f8;border-radius:0 0 7px 7px'>"
                        f"<b>{number} · {label}</b><br><span style='font-size:.78rem'>{detail_text}</span></div>", unsafe_allow_html=True)
    with st.container(border=True):
        st.subheader("Current assessment")
        st.write(workspace["assessment"])
        st.caption(f"Assessment version {workspace['assessment_version']} · synthetic prototype evidence · {workspace['as_of']}")
        st.caption(workspace["decision_gate"])
        with st.expander("▸ View evidence & audit trail", expanded=False):
            revision = workspace["revision"]
            st.markdown(f"**Assessment change:** {revision['assessment_change']}")
            st.caption(f"Trigger: {revision['trigger']} · Still unresolved: {revision['still_unresolved']}")
            retrieved = [{"Source ID": row["source_id"], "Match": row["matched_terms"],
                          "Freshness": row["citation"].freshness_status, "Excerpt": row["excerpt"]}
                         for row in workspace["retrieved_passages"]]
            st.dataframe(retrieved, hide_index=True, width="stretch")
            quality = workspace["evidence_quality"]
            if quality["stale_sources"]:
                st.warning("Stale evidence requires verification: " + ", ".join(item["source_id"] for item in quality["stale_sources"]))
            if quality["contradictions"]:
                for conflict in quality["contradictions"]:
                    st.error(f"{conflict['topic']}: {conflict['message']} ({', '.join(conflict['source_ids'])})")
            st.caption("Source-labeled evidence")
            st.dataframe(workspace["evidence"], hide_index=True, width="stretch")
            st.caption("Assessment revision history")
            st.dataframe(workspace["revision_history"], hide_index=True, width="stretch")
    with st.expander("Missing or conflicting information", expanded=True):
        for unknown in workspace["unknowns"]:
            st.markdown(f"**{unknown['question']}** · {unknown['status']}")
            st.caption(f"Why it matters: {unknown['why']} · Owner: {unknown['owner']}")
    with st.container(border=True):
        st.subheader("Human review decision")
        st.caption("The primary recommendation is a preparation step for operator review. No operational action executes automatically.")
        primary = next(option for option in workspace["options"] if option["action"] == "Approve proposed next step")
        st.markdown(f"### {primary['evidence']}")
        st.write(f"**Why:** {findings['response']['recommendation']['rationale']}")
        st.caption(f"Tradeoff: {primary['tradeoff']} · Prerequisite: {primary['prerequisites']}")
        st.text_area("Operator rationale", key="decision_rationale", placeholder="Why is this option appropriate given the evidence?")
        approve, modify, reject = st.columns(3)
        with approve:
            st.button("Approve", key=f"hitl_approve_{circuit_id}", type="primary",
                      on_click=record_decision, args=("Approve proposed next step", circuit_id, report["timestamp"]), width="stretch")
        with modify:
            st.button("Modify", key=f"hitl_modify_{circuit_id}",
                      on_click=record_decision, args=("Revise assessment", circuit_id, report["timestamp"]), width="stretch")
        with reject:
            st.button("Reject", key=f"hitl_reject_{circuit_id}",
                      on_click=record_decision, args=("Reject proposed next step", circuit_id, report["timestamp"]), width="stretch")
        request_option = next(option for option in workspace["options"] if option["action"] == "Request missing information")
        st.button("Request missing information", key=f"decision_{circuit_id}_0",
                  on_click=record_decision, args=(request_option["action"], circuit_id, report["timestamp"]))
    if st.session_state.decision_log:
        with st.expander("Decision log", expanded=False):
            st.dataframe(st.session_state.decision_log, hide_index=True, width="stretch")
    with overview:
        st.subheader("Circuit utilization")
        utilization_state = st.plotly_chart(
            utilization_rank_figure(tables), key="utilization_rank", width="stretch",
            on_select="rerun", selection_mode="points",
        )
        # Plotly returns the clicked bar's y value. Persist it so the detail
        # boxes stay focused after the rerun triggered by the selection event.
        selected_points = getattr(getattr(utilization_state, "selection", None), "points", []) or []
        if selected_points:
            clicked_circuit = selected_points[0].get("y")
            if clicked_circuit in set(tables["circuits"]["circuit_id"]):
                st.session_state.utilization_selected_circuit = clicked_circuit
        display_circuit_id = st.session_state.get("utilization_selected_circuit") or circuit_id
        if display_circuit_id not in set(tables["circuits"]["circuit_id"]):
            display_circuit_id = circuit_id
        st.caption("Click a bar to change the circuit details below. Hover for load, maximum capacity, and remaining headroom.")
        selected_capacity_row = tables["circuits"].set_index("circuit_id").loc[display_circuit_id]
        selected_summary = st.columns(3)
        selected_summary[0].metric("Demand", f"{float(selected_capacity_row.current_load_mw):.2f} MW")
        selected_summary[1].metric("Capacity", f"{float(selected_capacity_row.capacity_mw):.2f} MW")
        selected_summary[2].metric("Capacity in use", f"{100 * float(selected_capacity_row.current_load_mw) / float(selected_capacity_row.capacity_mw):.1f}%")
        st.caption(f"Selected circuit: {display_circuit_id}. Detailed evidence and drivers are available in the investigation workspace above.")
        with st.expander("Detailed circuit × time heat map", expanded=False):
            st.plotly_chart(heatmap_figure(list(st.session_state.stage_reports.values()), layer), key="circuit_time", width="stretch")
    with agents:
        st.subheader(f"Agent activity · {circuit_id}")
        st.caption("Each agent follows a bounded evidence step. Expand a card to inspect what it pulled and produced.")
        agent_cards = (("grid", "⚡", "Grid Agent", "Grid strain + equipment indicator"),
                       ("wildfire", "🔥", "Wildfire Agent", "Environmental + combined exposure"),
                       ("impact", "🏥", "Impact Agent", "Unique customers + facilities"),
                       ("response", "✦", "Response Agent", "Review recommendation"))
        card_columns = st.columns(4)
        for column, (key, icon, title, task) in zip(card_columns, agent_cards):
            agent = findings[key]
            if key == "grid":
                output = f"{agent['grid_strain']['score']:.1f}/100 strain"
            elif key == "wildfire":
                output = f"{agent['combined']['score']:.1f}/100 combined"
            elif key == "impact":
                output = f"{agent['impact']['customers_at_risk']:,} accounts"
            else:
                output = agent["recommendation"]["primary"]["title"]
            complete = "Complete" if agent else "Analyzing"
            with column:
                arrow = " →" if key != "response" else ""
                st.markdown(f"<div style='background:#f0f5f7;border-radius:10px;padding:12px;min-height:105px'>"
                            f"<div style='font-size:1.05rem;font-weight:700'>{icon} {title}{arrow}</div>"
                            f"<div style='color:#15803d;font-weight:600'>{complete}</div>"
                            f"<div style='font-size:.78rem'>{task}</div>"
                            f"<div style='font-size:.82rem;font-weight:600;margin-top:5px'>{output}</div></div>", unsafe_allow_html=True)
                with st.expander("Evidence", expanded=False):
                    st.write(agent["explanation"])
                    st.caption(f"Stage {report['stage']} · deterministic template mode")
        with st.expander("Detailed reasoning flow", expanded=False):
            st.plotly_chart(agent_graph_figure(findings, circuit_id), key="agent_graph", width="stretch")
        st.subheader("Investigation trail")
        trail = [
            {"Step": "Reviewed telemetry", "Source": "Asset and circuit records", "Interpretation": "Compared load, capacity, temperature, condition, and anomaly gates", "Type": "Recorded facts → deterministic calculation"},
            {"Step": "Joined operating context", "Source": "Weather and fire-risk zone", "Interpretation": "Checked whether environmental conditions increase consequence", "Type": "Recorded facts → deterministic gate"},
            {"Step": "Resolved relationships", "Source": "Circuit → customer/facility model", "Interpretation": "Calculated unique exposure without double-counting", "Type": "Structured relationship traversal"},
            {"Step": "Prepared decision options", "Source": "Risk, impact, and crew findings", "Interpretation": "Presented evidence, alternatives, tradeoffs, and prerequisites", "Type": "AI-style synthesis; no execution"},
        ]
        if st.session_state.field_report and circuit_id == "C-184":
            trail.append({"Step": "Retrieved field report", "Source": "FR-001 · synthetic field inspection", "Interpretation": "Updated escalation brief; backup readiness remains unknown", "Type": "New evidence → assessment revision"})
        st.dataframe(trail, hide_index=True, width="stretch")
        st.caption("This graph makes the AI-native contract explicit: agents pull structured evidence, apply deterministic reasoning, and pass reviewable outputs downstream. No agent executes an operational action.")
        st.dataframe(agent_reasoning_frame(findings), hide_index=True, width="stretch")
        for key, icon in (("grid","⚡"),("wildfire","☀"),("impact","⌂"),("response","✓")):
            with st.container(border=True):
                agent = findings[key]
                st.markdown(f"**{icon} {agent['agent']} · analysis complete**")
                st.write(agent["explanation"])
        with st.expander("Checkpoint activity history"):
            st.dataframe(activity_frame(list(st.session_state.stage_reports.values()), circuit_id), hide_index=True, width="stretch")
    with detail:
        st.subheader(f"Evidence · {circuit_id}" + (f" · {CATEGORY_LABELS[selected['category']]}" if selected else " · baseline assessment"))
        if selected:
            st.write("Affected assets: " + ", ".join(selected["affected_asset_ids"]))
        st.caption(f"Sample time: {report['timestamp']} · {scenario.run_id}")
        st.plotly_chart(network_figure(report, tables, circuit_id), key="grid_network", width="stretch")
        st.json({"grid":grid, "wildfire":wildfire, "impact":findings["impact"]}, expanded=False)
    with source_files:
        st.subheader(f"Evidence files · {circuit_id}")
        st.caption("Synthetic source records used in this assessment. Select a record to open its contents, provenance, and freshness metadata.")
        source_rows = workspace["evidence"]
        source_ids = [row["source_id"] for row in source_rows]
        selected_source_id = st.selectbox("Select evidence to inspect", source_ids,
                                          format_func=lambda source_id: evidence_display_name(
                                              next(row for row in source_rows if row["source_id"] == source_id)),
                                          key=f"evidence_source_{circuit_id}")
        selected_source = next(row for row in source_rows if row["source_id"] == selected_source_id)
        with st.container(border=True):
            st.markdown(f"### {evidence_display_name(selected_source)}")
            st.caption(f"Canonical source ID: `{selected_source['source_id']}`")
            metadata = st.columns(3)
            metadata[0].caption(f"Type\n\n**{selected_source['kind']}**")
            metadata[1].caption(f"Owner\n\n**{selected_source['owner']}**")
            metadata[2].caption(f"Freshness\n\n**{selected_source['freshness_status']}** · {selected_source['freshness_window']}")
            st.caption(f"Recorded at {selected_source['timestamp']}")
            st.markdown("**Source content**")
            st.info(selected_source["text"])
            st.caption("Synthetic prototype record · displayed for traceability and demo review")
        st.dataframe([{
            "Source": evidence_display_name(row), "Type": row["kind"], "Owner": row["owner"],
            "Timestamp": row["timestamp"], "Freshness": row["freshness_status"],
        } for row in source_rows], hide_index=True, width="stretch")
    st.caption("Prototype indicators · deterministic analysis · review only")

command_center_tab, about_tab = st.tabs(["Command Center", "About"])
with command_center_tab:
    dashboard()
with about_tab:
    about_page()
