"""Focused operational overview with continuous synthetic-day playback."""
import time

import streamlit as st

from src.command_center import (CATEGORY_LABELS, RISK_LAYERS, activity_frame, geographic_figure,
                                agent_graph_figure, agent_reasoning_frame, heatmap_figure,
                                network_figure, queue_frame, strain_figure)
from src.live_scenario import LiveScenario, demand_drivers
from src.investigation import (evidence_records, investigation_queue, investigation_unknowns,
                               response_options)
from src.ontology import DataQualityError
from src.playback import Playback, PAUSE_REASONS, CHECKPOINT_MINUTES
from src.risk_engine import SEVERITY_ORDER

st.set_page_config(page_title="GridGuard | Command Center", page_icon="⚡", layout="wide")
st.markdown("""<style>
[data-testid="stMainBlockContainer"] {padding-top:1.4rem; max-width:1400px;}
[data-testid="stMetricLabel"] p {white-space:normal;}
[data-testid="stMetricValue"] {font-size:1.65rem;}
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) {flex-wrap:wrap;}
[data-testid="stHorizontalBlock"]:has([data-testid="stMetric"]) > [data-testid="stColumn"] {min-width:130px;flex:1 1 130px;}
h1 {color:#18394a;} h3 {color:#294963;}
[data-testid="stMetric"] {background:#f0f5f7;border-radius:10px;padding:12px;}
</style>""", unsafe_allow_html=True)
st.title("⚡ GridGuard")
st.caption("CALIFORNIA ELECTRIC · SYNTHETIC OPERATIONS DEMO · AUG 15, 2026 / PDT")


def reset_scenario():
    st.session_state.scenario.reset()
    st.session_state.playback = Playback(minutes_per_second=st.session_state.get("speed", 6))
    for key in ("report", "tables", "selected_incident", "investigation_case", "stage_reports", "sample_minute", "data_error", "field_report", "decision_log", "assessment_version"):
        st.session_state.pop(key, None)


def introduce_field_report():
    st.session_state.field_report = True
    st.session_state.assessment_version = st.session_state.get("assessment_version", 1) + 1


def record_decision(action: str, case_id: str, timestamp: str):
    st.session_state.setdefault("decision_log", []).append({
        "timestamp": timestamp, "case_id": case_id, "action": action,
        "assessment_version": st.session_state.get("assessment_version", 1),
        "rationale": st.session_state.get("decision_rationale", "Operator decision recorded from reviewed evidence."),
    })


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


@st.fragment(run_every="1s")
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
    st.header("Investigation queue")
    st.caption("Prioritized cases show why attention is needed, what has been reviewed, and what remains before an operator can decide.")
    metrics = st.columns(3)
    metrics[0].metric("Open investigations", len(cases))
    metrics[1].metric("Cases awaiting review", awaiting)
    metrics[2].metric("Unresolved information requests", unknown_count)
    queue_rows = [{"Priority": case["priority"], "Incident": case["title"], "Why it needs attention": case["reason"], "Investigation status": case["status"]} for case in cases]
    st.dataframe(queue_rows, hide_index=True, width="stretch")

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

    findings = report["findings"][circuit_id]
    grid, wildfire = findings["grid"], findings["wildfire"]
    circuit = tables["circuits"].set_index("circuit_id").loc[circuit_id]
    overview, agents, detail = st.tabs(["Overview", "Agent activity", "Technical evidence"])
    st.header(f"Investigation workspace · {selected_case['title']}")
    if grid["anomaly_asset_ids"]:
        assessment_text = "Equipment anomaly detected during severe environmental conditions. "
    else:
        assessment_text = "Electrical and environmental signals are being monitored; no equipment anomaly is confirmed at this time. "
    assessment_text += (f"{int(circuit.customers_served):,} accounts and "
                        f"{len(findings['impact']['impact']['critical_facilities'])} critical facilities are linked to this circuit.")
    if st.session_state.field_report and circuit_id == "C-184":
        assessment_text += " Field inspection evidence now confirms visible equipment damage; escalation brief updated."
    with st.container(border=True):
        st.subheader("Current assessment")
        st.write(assessment_text)
        st.caption(f"Assessment version {st.session_state.assessment_version} · synthetic prototype evidence · {report['timestamp']}")
    evidence, unknowns = st.columns([1.35, 1])
    with evidence:
        with st.expander("Evidence · recorded facts and interpretations", expanded=True):
            st.dataframe(evidence_records(report, tables, circuit_id, st.session_state.field_report), hide_index=True, width="stretch")
    with unknowns:
        with st.expander("Missing or conflicting information", expanded=True):
            for unknown in investigation_unknowns(circuit_id, st.session_state.field_report):
                st.markdown(f"**{unknown['question']}** · {unknown['status']}")
                st.caption(f"Why it matters: {unknown['why']} · Owner: {unknown['owner']}")
    with st.expander("Response options", expanded=True):
        st.caption("Options refer to this assessment version and require operator review. No action executes automatically.")
        st.text_area("Operator rationale", key="decision_rationale", placeholder="Why is this option appropriate given the evidence?")
        option_columns = st.columns(4)
        for index, option in enumerate(response_options(circuit_id, report)):
            with option_columns[index]:
                st.markdown(f"**{option['action']}**")
                st.caption(f"Evidence: {option['evidence']}")
                st.caption(f"Tradeoff: {option['tradeoff']}")
                st.caption(f"Prerequisite: {option['prerequisites']}")
                st.button(option["action"], key=f"decision_{circuit_id}_{index}",
                           on_click=record_decision, args=(option["action"], circuit_id, report["timestamp"]))
    if st.session_state.decision_log:
        with st.expander("Decision log", expanded=False):
            st.dataframe(st.session_state.decision_log, hide_index=True, width="stretch")
    with overview:
        st.subheader("Where is the pressure?")
        layer = st.selectbox("Risk layer", list(RISK_LAYERS), index=1, key="risk_layer")
        basemap = st.checkbox("Street map · internet required", value=False, key="show_basemap")
        st.plotly_chart(geographic_figure(report, tables, layer, basemap), key="geographic_risk", width="stretch")
        st.caption("⚡ Grid assets · shaded circuit service areas · + Hospital · ◇ Fire station · droplet: water facility. Boundaries are approximate synthetic display regions around Santa Clarita.")

        st.subheader("Capacity by circuit")
        st.caption("All six circuit bars stay visible. Expand the matching circuit below for the detailed explanation.")
        capacity_columns = st.columns(2)
        for index, row in enumerate(tables["circuits"].sort_values("circuit_id").itertuples()):
            with capacity_columns[index % 2]:
                cid = row.circuit_id
                item = report["findings"][cid]
                circuit_drivers = demand_drivers(scenario.baseline_tables(), tables, cid)
                circuit_weather = item["wildfire"]["evidence"]
                circuit_impact = item["impact"]["impact"]
                st.markdown(f"**{cid} · {row.circuit_name}**")
                st.plotly_chart(strain_figure(circuit_drivers, float(row.capacity_mw)),
                                key=f"capacity_summary_{row.circuit_id}", width="stretch")
                with st.expander(f"Details · {cid} · {float(row.current_load_mw):.2f} / {float(row.capacity_mw):.2f} MW", expanded=(cid == circuit_id)):
                    a, b, c = st.columns(3)
                    a.metric("Demand" if cid == circuit_id else "Load", f"{float(row.current_load_mw):.2f} MW")
                    b.metric("Capacity", f"{float(row.capacity_mw):.2f} MW")
                    c.metric("Capacity in use", f"{100 * float(row.current_load_mw) / float(row.capacity_mw):.1f}%")
                    st.write(f"**Energy demand change:** the scenario adds **{circuit_drivers['Incremental energy demand']:.2f} MW** above baseline as temperature and time-of-day conditions change; this is a synthetic demand assumption, not a measured end-use breakdown.")
                    if circuit_drivers["Afternoon event"]:
                        st.write(f"**Afternoon event:** the scenario assigns **{circuit_drivers['Afternoon event']:.2f} MW** to the event load.")
                    st.write(f"**Environmental operating context:** {circuit_weather['wind_speed_mph']:.1f} mph wind · {circuit_weather['humidity_pct']:.1f}% humidity · {circuit_weather['ambient_temperature_f']:.1f}°F. These conditions increase the consequence of an energized equipment fault; they do not create an electrical anomaly by themselves.")
                    if item["grid"]["anomaly_asset_ids"]:
                        st.error("Sudden equipment fault · " + ", ".join(item["grid"]["anomaly_asset_ids"]))
                    facility_names = ", ".join(f["name"] for f in circuit_impact["critical_facilities"]) or "No critical facilities"
                    st.write(f"**Circuit context:** {int(row.customers_served):,} accounts · {facility_names}")
                    st.caption("Illustrative demand attribution; recommendations are proposals and no operational action executes.")
        with st.expander("How risk changes through the day", expanded=False):
            st.plotly_chart(heatmap_figure(list(st.session_state.stage_reports.values()), layer), key="circuit_time", width="stretch")
            st.caption("Reached checkpoints only. Blank cells are future times, not zero risk.")
    with agents:
        st.subheader(f"Agent activity · {circuit_id}")
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
        st.plotly_chart(agent_graph_figure(findings, circuit_id), key="agent_graph", width="stretch")
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
    st.caption("Synthetic prototype indicators, not validated probabilities. No real grid controls. "
               "Energy-demand and event contributions are scenario assumptions; agents use deterministic templates.")


dashboard()
