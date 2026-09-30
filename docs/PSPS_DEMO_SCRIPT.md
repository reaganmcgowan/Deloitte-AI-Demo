# GridGuard three-minute demo script

This script is designed for a maximum three-minute recording. The scenario, records, and
indicators are synthetic and deterministic. GridGuard prepares a reviewable decision; it
does not authorize or execute a PSPS, dispatch, notification, or grid-control action.

## Before recording

Run:

```sh
streamlit run app.py
```

Start at **1:00 PM** with **C-184** selected in **Open investigation**. If needed, click
**Reset**. Keep the browser zoom and window fixed so the Command Center fits on screen.

## 0:00–0:25 — Frame the problem in About

Click **About** and say:

> “Utility operators have to assemble a time-sensitive incident picture from separate
> electrical, weather, asset, customer, facility, maintenance, and field systems. The
> challenge is not another risk score—it is knowing what changed, who could be affected,
> what evidence is stale or missing, and what reviewable next step an authorized operator
> can defend.”

Point briefly to the flow:

**Evidence → Four agents → Investigation → Evidence trail → Human review**

Then say:

> “GridGuard is an evidence-to-decision layer. It joins the records around one circuit,
> shows the reasoning and uncertainty, and keeps the final decision with a human.”

Click **Command Center**.

## 0:25–0:55 — Show the command center

Point to the four KPIs, then the **map + AI priority queue**:

> “The map answers where the assets are. The queue answers why attention is needed.”

Click one **Circuit utilization** bar. Point out that the detail boxes change to the selected
circuit’s demand, capacity, and percent in use. Do not open technical evidence yet.

## 0:55–1:20 — Establish the baseline investigation

With C-184 selected, point to **Detect → Context → Impact → Decide** and the assessment:

> “At 1:00 PM, C-184 is stable. The system is monitoring demand and environmental context;
> it has not invented an equipment anomaly.”

Open **Evidence files**, select **Hospital readiness record**, and show its content and
freshness. Say:

> “This is the difference between a claim and a traceable record: the hospital backup
> readiness gap is visible, owned, timestamped, and still unresolved.”

Close the tab or return to the workspace.

## 1:20–2:05 — Progress the scenario

Click **Start day** once and wait for the pause at **2:00 PM**. Say:

> “Demand rises, but weather alone does not create an electrical fault.”

Click **Continue** once to reach **3:00 PM**. Open **Agent activity** and point across:

**Grid Agent → Wildfire Agent → Impact Agent → Response Agent**

Say:

> “Each agent has a bounded responsibility: electrical conditions, environmental context,
> deduplicated impact, and review options. The cards show what the system pulled and
> produced; no agent operates the grid.”

Click **Continue** once to reach **3:30 PM**. Point to the environmental context and say:

> “Environmental exposure is now high, but combined exposure remains gated until an
> energized equipment anomaly is also present.”

Click **Continue** once to reach **4:00 PM**.

## 2:05–2:35 — Show the differentiated outcome

Point to the hero incident:

> **CRITICAL — Circuit 184**
> Electrical anomaly + severe fire-weather conditions
> **8,420 customers at risk · 1 hospital**

Say:

> “At the final checkpoint, T-882 supplies the electrical anomaly and the dangerous
> weather gate is satisfied. The impact model deduplicates the circuit relationships, so
> this is 8,420 accounts and one hospital—not repeated totals for each signal.”

Click **Introduce new field report** and show:

> “What changed: visible equipment damage is now field-confirmed. What remains unresolved:
> hospital backup readiness.”

## 2:35–3:00 — Human decision and close

In **Human review decision**, enter:

> “Request facility backup verification and field follow-up before escalation review.”

Click **Request missing information** (or **Approve** if demonstrating the proposed preparation
step). Open **Decision log** and point to the assessment version, evidence IDs, rationale,
timestamp, and zero operational effect.

Close with:

> “The differentiated value is not autonomous control. It is faster, consequence-aware
> investigation with evidence lineage, visible uncertainty, inspectable agent reasoning,
> and a human approval boundary. In production, the same contracts could connect to approved
> utility systems and validated models.”

## If the interviewer asks for more

Use the **About** tab’s Related reading section and the full Evidence/Audit trail only after
the three-minute walkthrough. Mention that all prototype scores are synthetic indicators,
not validated probabilities, and that the scenario is designed for workflow validation.
