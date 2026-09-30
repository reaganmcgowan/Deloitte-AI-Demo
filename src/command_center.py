"""Presentation helpers; domain calculations remain in the tested agents/scenario."""

import pandas as pd
import plotly.graph_objects as go

from src.risk_engine import SEVERITY_ORDER

CATEGORY_LABELS = {
    "grid_strain": "Grid strain", "equipment_anomaly": "Equipment anomaly",
    "combined_wildfire": "Electrical / wildfire exposure",
}
COLORS = {"NORMAL": "#277c70", "ELEVATED": "#b38212", "HIGH": "#dc6b22", "CRITICAL": "#c43d4c"}


def circuit_severity(report: dict, circuit_id: str) -> str:
    return max((row["severity"] for row in report["incidents"] if row["circuit_id"] == circuit_id),
               key=SEVERITY_ORDER.get, default="NORMAL")


def queue_frame(report: dict) -> pd.DataFrame:
    """Keep the domain's severity-first ordering; never sum row impact totals."""
    return pd.DataFrame([{
        "Priority": index, "Severity": row["severity"], "Circuit": row["circuit_id"],
        "Finding": CATEGORY_LABELS[row["category"]], "Indicator / 100": round(row["score"], 1),
        "Customers exposed": row["impact"]["customers_at_risk"],
        "Critical facilities": len(row["impact"]["critical_facilities"]),
    } for index, row in enumerate(report["incidents"], 1)])


def network_figure(report: dict, tables: dict, selected_circuit: str | None = None) -> go.Figure:
    """Offline relationship schematic. Lines are associations, not electrical routes."""
    figure = go.Figure()
    circuits = sorted(tables["circuits"].circuit_id)
    nodes = []
    edge_x, edge_y = [], []
    for index, circuit_id in enumerate(circuits):
        y = (len(circuits) - index - 1) * 2
        level = circuit_severity(report, circuit_id)
        circuit = tables["circuits"].set_index("circuit_id").loc[circuit_id]
        nodes.append(dict(x=0, y=y, label=circuit_id, severity=level, symbol="square",
                          detail=f"{circuit_id} · {level}<br>{circuit.current_load_mw:g} / {circuit.capacity_mw:g} MW"
                                 f"<br>{int(circuit.customers_served):,} accounts",
                          selected=circuit_id == selected_circuit))
        assets = tables["assets"].loc[tables["assets"].circuit_id == circuit_id].sort_values("asset_id")
        grid = report["findings"][circuit_id]["grid"]
        wildfire = report["findings"][circuit_id]["wildfire"]
        for offset, asset in enumerate(assets.itertuples()):
            asset_y = y + (offset - 1) * .48
            electrical = next(row for row in grid["per_asset"] if row["asset_id"] == asset.asset_id)
            fire = next(row for row in wildfire["per_asset"] if row["asset_id"] == asset.asset_id)
            levels = [electrical["grid_strain"]["severity"], fire["combined"]["severity"]]
            if electrical["electrical_anomaly"]:
                levels.append(electrical["equipment_anomaly"]["severity"])
            nodes.append(dict(x=1, y=asset_y, label=asset.asset_id,
                              severity=max(levels, key=SEVERITY_ORDER.get), symbol="circle",
                              detail=f"{asset.asset_id} · {asset.asset_type}<br>{asset.current_load_mw:g} / {asset.capacity_mw:g} MW"
                                     f"<br>{asset.temperature_f:g}°F equipment", selected=False))
            edge_x.extend([0, 1, None])
            edge_y.extend([y, asset_y, None])
    figure.add_trace(go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color="#ccd4dc", width=1),
                               hoverinfo="skip", showlegend=False))
    for level, color in COLORS.items():
        matching = [node for node in nodes if node["severity"] == level]
        if not matching:
            continue
        figure.add_trace(go.Scatter(
            x=[node["x"] for node in matching], y=[node["y"] for node in matching],
            text=[node["label"] for node in matching], mode="markers+text", textposition="middle right",
            customdata=[node["detail"] for node in matching], hovertemplate="%{customdata}<extra></extra>",
            name=level.title(), marker=dict(color=color, size=[20 if node["selected"] else 12 for node in matching],
                                          symbol=[node["symbol"] for node in matching]),
        ))
    figure.update_layout(height=440, margin=dict(l=12, r=70, t=12, b=10),
                         xaxis=dict(visible=False, range=[-.15, 1.4]),
                         yaxis=dict(visible=False, range=[-1, 11]),
                         legend=dict(orientation="h", y=1.08), paper_bgcolor="rgba(0,0,0,0)",
                         plot_bgcolor="rgba(0,0,0,0)", font=dict(size=12))
    return figure


RISK_LAYERS = {
    "Combined electrical / wildfire": ("wildfire", "combined"),
    "Grid strain": ("grid", "grid_strain"),
    "Equipment indicator": ("grid", "equipment_anomaly"),
    "Environmental exposure": ("wildfire", "environment"),
}
RISK_COLORS = [[0, "#277c70"], [.3, "#dfbe58"], [.6, "#e78d42"], [.85, "#c43d4c"], [1, "#791e3b"]]
STAGE_TIMES = ["1:00 PM", "2:00 PM", "3:00 PM", "3:30 PM", "4:00 PM"]


def boundary_color(score: float) -> str:
    """Use the same qualitative colors as markers for synthetic area shading."""
    if score >= 85:
        return "#c43d4c"
    if score >= 60:
        return "#e78d42"
    if score >= 30:
        return "#dfbe58"
    return "#277c70"


def layer_score(report: dict, circuit_id: str, layer: str) -> float:
    agent, category = RISK_LAYERS[layer]
    return report["findings"][circuit_id][agent][category]["score"]


def geographic_figure(report: dict, tables: dict, layer: str, basemap: bool = False) -> go.Figure:
    """One marker per co-located asset group; no inferred risk between locations."""
    locations = tables["assets"].groupby("circuit_id", sort=True).agg(
        latitude=("latitude", "mean"), longitude=("longitude", "mean"),
        asset_ids=("asset_id", lambda values: ", ".join(sorted(values))),
    ).reset_index()
    scores = [layer_score(report, circuit, layer) for circuit in locations.circuit_id]
    details = [[row.circuit_id, row.asset_ids, layer_score(report, row.circuit_id, layer)]
               for row in locations.itertuples()]
    figure = go.Figure(go.Scattermap(
        lat=locations.latitude.tolist(), lon=locations.longitude.tolist(),
        mode="markers+text", text=locations.circuit_id.tolist(), textposition="top right",
        customdata=details, marker=dict(size=26, color=scores, cmin=0, cmax=100,
                                      colorscale=RISK_COLORS, colorbar=dict(title="Indicator", thickness=12)),
        hovertemplate="%{customdata[0]}<br>%{customdata[1]}<br>Indicator: %{customdata[2]:.1f}/100"
                      "<br>Latitude %{lat:.3f} · Longitude %{lon:.3f}<extra></extra>", name="Synthetic asset groups"))
    facilities = tables["critical_facilities"]
    figure.add_trace(go.Scattermap(lat=facilities.latitude.tolist(), lon=facilities.longitude.tolist(),
                                   mode="markers", marker=dict(size=9, color="#23445c"),
                                   text=(facilities["name"] + " · " + facilities.circuit_id).tolist(),
                                   hovertemplate="%{text}<extra>Critical facility</extra>", name="Critical facilities"))
    # Approximate service-area polygons make the feeder's geographic responsibility
    # visible. They are synthetic display boundaries, not surveyed utility right-of-way.
    for index, (row, score) in enumerate(zip(locations.itertuples(), scores)):
        half_lat, half_lon = .014, .019
        polygon = [(-half_lon, -.004), (-.012, -half_lat), (.004, -half_lat),
                   (half_lon, -.006), (.014, .010), (.002, half_lat),
                   (-.014, .011), (-half_lon, -.004)]
        color = boundary_color(score)
        figure.add_trace(go.Scattermap(
            lon=[row.longitude + x for x, y in polygon], lat=[row.latitude + y for x, y in polygon],
            mode="lines", fill="toself", fillcolor=color, opacity=.08,
            line=dict(color=color, width=1.5), text=[f"{row.circuit_id} synthetic service area"] * len(polygon),
            hovertemplate="%{text}<br>Indicator: " + f"{score:.1f}/100<extra></extra>",
            name="Synthetic service areas" if index == 0 else None,
            showlegend=index == 0))
    # Vector icons need no external sprite/font service, so they also work offline.
    # A lightning bolt identifies grid assets; facility-specific shapes identify services.
    for row in locations.itertuples():
        dx, dy = .005, .007
        shape = [(0.2, 1), (-.6, -.05), (0, -.05), (-.2, -1), (.6, .1), (0, .1), (.2, 1)]
        figure.add_trace(go.Scattermap(
            lon=[row.longitude + x*dx for x,y in shape], lat=[row.latitude + y*dy for x,y in shape],
            mode="lines", fill="toself", fillcolor="white", line=dict(color="#173449", width=1),
            hoverinfo="skip", showlegend=False))
    for facility in facilities.itertuples():
        if facility.facility_type == "hospital":
            shape = [(-.25,1),(.25,1),(.25,.25),(1,.25),(1,-.25),(.25,-.25),(.25,-1),(-.25,-1),(-.25,-.25),(-1,-.25),(-1,.25),(-.25,.25),(-.25,1)]
        elif facility.facility_type == "fire_station":
            shape = [(0,1),(-.8,-.6),(0,-1),(.8,-.6),(0,1)]
        else:
            shape = [(0,1),(-.7,-.3),(-.5,-.9),(.5,-.9),(.7,-.3),(0,1)]
        figure.add_trace(go.Scattermap(
            lon=[facility.longitude+x*.004 for x,y in shape], lat=[facility.latitude+y*.005 for x,y in shape],
            mode="lines", fill="toself", fillcolor="#d9e8f0", line=dict(color="#173449", width=2),
            text=[facility.name]*len(shape), hovertemplate="%{text}<extra></extra>", showlegend=False))
    figure.update_layout(map=dict(style="open-street-map" if basemap else "white-bg",
                                  center=dict(lat=float(locations.latitude.mean()), lon=float(locations.longitude.mean())), zoom=8),
                         height=480, margin=dict(l=0,r=0,t=10,b=0),
                         legend=dict(orientation="h", y=-.04), uirevision="geographic")
    return figure


def heatmap_figure(reports: list[dict], layer: str) -> go.Figure:
    """Only evaluated stages are colored. Future/unrecorded stages remain blank."""
    by_stage = {report["stage"]: report for report in reports}
    circuits = sorted(reports[-1]["findings"])
    values = [[layer_score(by_stage[stage], circuit, layer) if stage in by_stage else None
               for stage in range(1, 6)] for circuit in circuits]
    labels = [[f"{score:.1f}" if score is not None else "—" for score in row] for row in values]
    figure = go.Figure(go.Heatmap(x=STAGE_TIMES, y=circuits, z=values, zmin=0, zmax=100,
                                 colorscale=RISK_COLORS, text=labels, texttemplate="%{text}",
                                 xgap=4, ygap=4, hoverongaps=False,
                                 hovertemplate="%{y} · %{x}<br>Indicator: %{z:.1f}/100<extra></extra>",
                                 colorbar=dict(title="Indicator", thickness=12)))
    figure.update_layout(height=350, margin=dict(l=5,r=5,t=15,b=5),
                         yaxis=dict(autorange="reversed"), xaxis=dict(side="top"),
                         plot_bgcolor="#eef1f4")
    return figure


def activity_frame(reports: list[dict], circuit_id: str) -> pd.DataFrame:
    """Evidence of completed evaluations, not invented live actions or dispatches."""
    events = []
    for report in sorted(reports, key=lambda item: item["stage"], reverse=True):
        findings = report["findings"][circuit_id]
        grid, fire = findings["grid"], findings["wildfire"]
        impact = findings["impact"]["impact"]
        recommendation = findings["response"]["recommendation"]
        steps = [
            ("Grid Reliability", "Checked load, capacity, temperature and condition",
             f"{len(grid['asset_ids'])} assets checked; anomalies: {', '.join(grid['anomaly_asset_ids']) or 'none'}"),
            ("Wildfire Risk", "Joined zone weather and applied electrical anomaly gate",
             f"Environment {fire['environment']['score']:.1f}; combined {fire['combined']['score']:.1f}/100"),
            ("Impact", "Traversed circuit links and deduplicated customers / facilities",
             f"{impact['customers_at_risk']:,} accounts; {len(impact['critical_facilities'])} facilities"),
            ("Response", "Checked eligible crews and prepared recommendation",
             recommendation["primary"]["title"] + " — proposed only"),
        ]
        for agent, action, outcome in steps:
            events.append({"Scenario time": STAGE_TIMES[report["stage"]-1], "Agent": agent,
                           "Analysis step": action, "Result": outcome, "Status": "Completed"})
    return pd.DataFrame(events)


def agent_graph_figure(findings: dict, circuit_id: str) -> go.Figure:
    """Show the deterministic data-to-agent-to-decision flow for one circuit."""
    labels = [
        "Asset telemetry", "Circuit load / capacity", "Weather + fire zone",
        "Customers + facilities", "Crew availability", "Grid Reliability",
        "Wildfire Risk", "Impact", "Response", "Risk indicators",
        "Environmental gate", "Deduplicated impact", "Recommendation",
    ]
    descriptions = [
        "temperature, condition, utilization", "MW load, capacity, demand trend",
        "wind, humidity, ambient temperature, zone", "circuit-linked accounts and facilities",
        "available crews and skills", "compares utilization, demand trend, condition, and temperature",
        "scores environmental exposure and applies the electrical-anomaly gate",
        "traverses circuit links and deduplicates customers and facilities",
        "checks evidence, crew eligibility, alternatives, and tradeoffs",
        "grid strain and equipment anomaly scores", "weather severity plus anomaly conjunction",
        "unique customers, facilities, and interruption state", "human-review proposal; no action executes",
    ]
    links = [
        (0, 5, "asset readings"), (1, 5, "load and capacity"),
        (5, 6, "electrical anomaly result"), (2, 6, "weather observation"),
        (0, 7, "affected asset IDs"), (3, 7, "relationship joins"),
        (4, 8, "eligible crews"), (5, 8, "grid evidence"),
        (6, 8, "environment evidence"), (7, 8, "impact evidence"),
        (5, 9, "weighted scores"), (6, 10, "weather gate"),
        (7, 11, "deduplicated totals"), (8, 12, "reviewable recommendation"),
    ]
    node_colors = (["#d7e8ef"] * 5 + ["#2f6680", "#b9822b", "#6675a8", "#6b5b95"]
                   + ["#d9edf0", "#f4e5bd", "#e5e1f0", "#e6d8ee"])
    figure = go.Figure(go.Sankey(
        arrangement="fixed",
        node=dict(label=labels, color=node_colors, pad=22, thickness=22,
                  customdata=descriptions, hovertemplate="%{label}<br>%{customdata}<extra></extra>"),
        link=dict(source=[source for source, _, _ in links], target=[target for _, target, _ in links],
                  value=[1] * len(links), label=[label for _, _, label in links],
                  hovertemplate="%{label}<extra></extra>"),
    ))
    figure.update_layout(title=f"Agent reasoning flow · {circuit_id}", height=430,
                         margin=dict(l=8, r=8, t=45, b=8), paper_bgcolor="rgba(0,0,0,0)",
                         font=dict(size=11), uirevision="agent-flow")
    return figure


def agent_reasoning_frame(findings: dict) -> pd.DataFrame:
    """Tabular contract for the graph: inputs, reasoning, and produced evidence."""
    grid, wildfire, impact, response = (findings[key] for key in ("grid", "wildfire", "impact", "response"))
    return pd.DataFrame([
        {"Agent": "Grid Reliability", "Pulls": "Asset telemetry; circuit load/capacity",
         "Reasoning": "Normalize utilization, demand trend, condition, and temperature; gate electrical anomaly",
         "Produces": f"Grid {grid['grid_strain']['score']:.1f}; equipment {grid['equipment_anomaly']['score']:.1f}; anomalies {', '.join(grid['anomaly_asset_ids']) or 'none'}"},
        {"Agent": "Wildfire Risk", "Pulls": "Weather; fire-risk zone; electrical result",
         "Reasoning": "Score environment, then require an energized anomaly before combined exposure can activate",
         "Produces": f"Environment {wildfire['environment']['score']:.1f}; combined {wildfire['combined']['score']:.1f}"},
        {"Agent": "Impact", "Pulls": "Asset → circuit → customer/facility relationships",
         "Reasoning": "Join circuit links and deduplicate overlapping exposure",
         "Produces": f"{impact['impact']['customers_at_risk']:,} customers; {len(impact['impact']['critical_facilities'])} facilities"},
        {"Agent": "Response", "Pulls": "All findings; crew availability and skills",
         "Reasoning": "Choose a review proposal with evidence, alternatives, and tradeoffs",
         "Produces": response["recommendation"]["primary"]["title"]},
    ])


def strain_figure(drivers: dict, capacity: float) -> go.Figure:
    """A physical MW comparison, separate from a synthetic 0–100 risk score."""
    figure = go.Figure()
    for (name, value), color in zip(drivers.items(), ("#294963", "#e5a43c", "#9674bf")):
        figure.add_trace(go.Bar(x=[value], y=["Demand"], name=name, orientation="h",
                               marker_color=color, hovertemplate=f"{name}: %{{x:.2f}} MW<extra></extra>"))
    figure.add_vline(x=capacity, line_dash="dash", line_color="#c43d4c",
                    annotation_text=f"Capacity · {capacity:g} MW", annotation_position="top left")
    figure.update_layout(barmode="stack", height=210, margin=dict(l=0,r=5,t=30,b=0),
                         xaxis=dict(title="Megawatts", range=[0, max(capacity * 1.2, sum(drivers.values()) * 1.1)]),
                         yaxis=dict(visible=False), legend=dict(orientation="h", y=-.5),
                         paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                         uirevision="capacity")
    return figure
