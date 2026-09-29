# CODEX BUILD BRIEF --- GridGuard

## Your role

Act as a senior full-stack / applied-AI engineer helping me build an
interview-ready prototype in VS Code.

I am building this project in approximately **2 days**, so
prioritize: 1. a working demo, 2. clear architecture, 3. explainable
logic, 4. a polished but simple UI, 5. code I can understand and explain
in an interview.

Do not over-engineer.

------------------------------------------------------------------------

# Original interview assignment

I was asked to:

> Demonstrate an AI-forward builder mindset through a prepared "show,
> not tell" demo/story/case study/video that brings AI-native thinking
> and skills to life.

One allowed approach is:

> Build a working prototype that demonstrates an AI-native approach to a
> problem in a target sector. Target sectors include financial services,
> healthcare, life sciences, energy, technology, media, telecom, and
> government. A repo, deployed app, or demo recording may be submitted.
> Rough is acceptable; the evaluation emphasizes thinking and ambition
> rather than polish.

I selected the **energy sector**.

------------------------------------------------------------------------

# Project

## GridGuard

### AI Grid Risk & Resilience Command Center

GridGuard is a prototype decision-support application for a **fictional
California investor-owned electric utility ("California Electric")**.

The problem:

Utilities must balance two competing responsibilities:

1.  keep electricity reliable, and
2.  prevent electrical infrastructure from creating unacceptable
    safety/wildfire risk.

GridGuard combines simulated: - grid data, - asset data, -
weather/environmental data, - customer impact data, - critical
infrastructure, - crew availability

and uses specialized AI-style agents to:

**Monitor → Detect → Investigate → Assess Impact → Recommend → Human
Decision → Simulated Action → Learn**

This is a **human-in-the-loop** system.

It must NEVER be presented as autonomously controlling real electrical
infrastructure.

------------------------------------------------------------------------

# Critical design principle

This should NOT feel like:

> "a dashboard with a chatbot."

It should feel like an operational AI application.

The user should visibly see the system: 1. detect an incident, 2.
investigate it, 3. combine information from multiple domains, 4. explain
why it matters, 5. recommend an action, 6. show tradeoffs, 7. request
human approval, 8. update the simulated state after the decision.

------------------------------------------------------------------------

# Technical constraints

Build locally in VS Code.

Preferred stack:

-   Python 3
-   Streamlit
-   pandas
-   numpy
-   Plotly
-   scikit-learn only if useful
-   optional OpenAI API integration for natural-language synthesis

The application MUST work without an OpenAI API key.

If no API key is available, use deterministic templates for agent
explanations.

Keep dependencies minimal.

------------------------------------------------------------------------

# Repository structure

Create something approximately like:

``` text
gridguard/
│
├── app.py
├── README.md
├── requirements.txt
├── .gitignore
│
├── data/
│   ├── assets.csv
│   ├── circuits.csv
│   ├── weather.csv
│   ├── customer_areas.csv
│   ├── critical_facilities.csv
│   └── crews.csv
│
├── src/
│   ├── __init__.py
│   ├── data_generator.py
│   ├── ontology.py
│   ├── risk_engine.py
│   ├── agents.py
│   ├── recommendations.py
│   └── scenario.py
│
└── docs/
    └── GRIDGUARD_DECOMPOSITION.md
```

Feel free to simplify if necessary.

------------------------------------------------------------------------

# Synthetic operational ontology

Represent these core objects.

## Asset

Fields: - asset_id - asset_name - asset_type - circuit_id - capacity -
current_load - temperature - age_years - condition_score - latitude -
longitude - status

## Circuit

Fields: - circuit_id - circuit_name - capacity - current_load -
fire_risk_zone - customers_served - energized

## WeatherObservation

Fields: - timestamp - zone - temperature - wind_speed - humidity

## CustomerArea

Fields: - area_id - circuit_id - customer_count - vulnerability_score

## CriticalFacility

Fields: - facility_id - name - facility_type - circuit_id -
backup_power - latitude - longitude

## Crew

Fields: - crew_id - available - location - skill_type

## Incident

Fields: - incident_id - timestamp - incident_type - affected_asset -
circuit_id - severity - risk_score - customers_at_risk -
critical_facilities_at_risk - status

## Recommendation

Fields: - recommendation_id - incident_id - recommended_action -
rationale - alternative_action - expected_benefit - tradeoff -
approval_status

------------------------------------------------------------------------

# Agents

Implement four understandable agents/classes/functions.

## 1. Grid Reliability Agent

Purpose: Detect grid strain and equipment anomalies.

Look at: - current_load / capacity, - asset temperature, - condition
score, - demand trend/scenario state.

Return: - risk score, - detected issues, - explanation.

Do not create a fake "AI" black box if simple logic is more appropriate.

------------------------------------------------------------------------

## 2. Wildfire Risk Agent

Purpose: Evaluate where electrical anomalies overlap dangerous
environmental conditions.

Look at: - wind speed, - humidity, - temperature, - fire-risk zone, -
asset anomaly.

Return: - simulated risk score, - contributing factors, - explanation.

Clearly label this as a prototype risk indicator---not a real wildfire
prediction model.

------------------------------------------------------------------------

## 3. Impact Agent

Purpose: Determine consequences.

Traverse relationships:

Asset → Circuit → Customer Areas → Critical Facilities

Return: - customers potentially affected, - critical facilities, -
vulnerability context.

------------------------------------------------------------------------

## 4. Response Agent

Purpose: Synthesize the previous agent outputs.

Return: - recommended next action, - alternatives, - explanation, -
benefits, - tradeoffs.

Example actions: - Continue monitoring - Dispatch inspection crew -
Escalate to emergency operations - Prepare load redistribution - Prepare
targeted de-energization review - Prioritize restoration

Do not simulate actual real-world electrical controls.

------------------------------------------------------------------------

# Risk logic

Create transparent, explainable risk scores.

Avoid pretending the numbers are scientifically validated.

For example, normalize factors to 0--1 and combine them using clearly
documented prototype weights.

Potential Grid Risk factors: - utilization - temperature anomaly -
condition score - demand trend

Potential Wildfire Risk factors: - wind - low humidity - temperature -
fire-risk-zone severity - electrical anomaly

Create a final priority score using: - safety risk, - reliability
risk, - customers affected, - critical facilities, - urgency.

Show the user WHY a score is high.

------------------------------------------------------------------------

# Primary demo scenario

Build a scenario controller that progresses through a simulated
California heat/fire-weather day.

Use buttons or a time slider.

## Stage 1 --- 1:00 PM

Normal conditions.

## Stage 2 --- 2:00 PM

Temperature and demand rise.

## Stage 3 --- 3:00 PM

One substation/circuit reaches elevated utilization.

## Stage 4 --- 3:30 PM

Wind rises and humidity falls in one high-fire-risk zone.

## Stage 5 --- 4:00 PM

An asset on Circuit 184 develops an abnormal temperature/load pattern.

This should create the hero incident.

Example synthetic values:

Circuit: C-184 Customers potentially affected: 8,420 Critical facility:
one hospital Wind: 46 mph Humidity: 11% Electrical anomaly: yes

These are synthetic scenario values.

The agents should now produce a CRITICAL incident.

Suggested recommendation:

> Dispatch/prepare an inspection response immediately and escalate the
> circuit for targeted de-energization review if electrical/fire-risk
> indicators worsen.

Show two sides of the decision:

### Keep energized

Benefit: - customers retain power.

Risk: - current electrical/fire exposure remains.

### Prepare targeted de-energization

Benefit: - reduces electrical ignition exposure.

Tradeoff: - customers and critical facilities may lose grid electricity.

Require human decision.

------------------------------------------------------------------------

# Streamlit UI

Build four views/tabs.

## 1. Command Center

Top KPI cards: - Grid Health - Active Incidents - Customers at Risk -
Critical Facilities at Risk - Available Crews

Then: - map or network visualization, - AI Priority Queue, - agent
activity/status.

The highest-risk incident should be visually obvious.

------------------------------------------------------------------------

## 2. Incident Investigation

When user selects an incident, show:

### Incident summary

### Why this was flagged

GRID - utilization - asset anomaly - temperature

ENVIRONMENT - wind - humidity - fire-risk zone

IMPACT - customers - critical facilities

### Agent analysis

Show each agent's output separately.

Then show:

### Recommended action

-   primary recommendation,
-   rationale,
-   alternative,
-   expected benefit,
-   tradeoff.

Buttons:

**Approve Simulation** **Modify** **Reject**

Store decision in Streamlit session state.

------------------------------------------------------------------------

## 3. Grid / Assets

Allow user to inspect: - circuits, - transformers, - substations.

Show: - utilization, - temperature, - condition, - risk, - linked
customers/facilities.

Include a chart of simulated load over time.

------------------------------------------------------------------------

## 4. Decision Log

Show a table of: - timestamp, - incident, - AI recommendation, - human
decision, - simulated outcome.

This is important because the product should demonstrate
governance/auditability.

------------------------------------------------------------------------

# AI experience

If an OpenAI API key is present:

Use the LLM only to turn structured agent findings into concise
operator-facing explanations.

Do NOT ask the LLM to calculate: - customer counts, - utilization, -
risk score arithmetic, - critical facilities, - numerical impact.

Those must come from deterministic code.

Provide the model structured JSON and ask it to summarize the evidence.

If no API key exists:

Use deterministic explanation templates.

The demo must remain fully functional.

------------------------------------------------------------------------

# UI philosophy

Professional utility operations center.

Do not make it flashy or gimmicky.

Prioritize: - clarity, - hierarchy, - explainability, - operational
context.

Use: - cards, - charts, - tables, - status indicators, - maps if easy.

Avoid spending excessive time on custom CSS.

------------------------------------------------------------------------

# Safety / credibility

Throughout README and UI:

Clearly state:

> GridGuard is a conceptual prototype using synthetic data. It is not a
> real grid-control, wildfire-prediction, or emergency-response system.

Never imply: - validated wildfire prediction, - real utility data, -
real power-flow modeling, - autonomous PSPS execution, - autonomous grid
control.

------------------------------------------------------------------------

# README

Create an interview-quality README containing:

1.  GridGuard title
2.  One-sentence thesis
3.  Problem
4.  Why it matters
5.  Product solution
6.  Architecture diagram
7.  Agent descriptions
8.  Screenshots placeholder
9.  Demo workflow
10. Tech stack
11. How to run
12. Project limitations
13. Future roadmap
14. Research / sources

Use the accompanying `GRIDGUARD_DECOMPOSITION.md` as the source of truth
for product context.

------------------------------------------------------------------------

# Development workflow

Do NOT try to build everything at once.

Work in this order:

## Phase 1

Set up repo and environment.

## Phase 2

Generate synthetic datasets.

Show me samples and explain them.

## Phase 3

Implement ontology/relationship helpers.

Test: Asset → Circuit → Customers → Critical Facilities.

## Phase 4

Implement transparent risk engine.

Test it independently.

## Phase 5

Implement agents.

Test each independently.

## Phase 6

Implement scenario progression.

Verify that the hero incident emerges at the correct stage.

## Phase 7

Build Streamlit Command Center.

## Phase 8

Build incident investigation + HITL controls.

## Phase 9

Add assets and decision-log views.

## Phase 10

Polish README and UI.

After each major phase: - run the code, - fix errors, - briefly tell me
what was created, - tell me how I can verify it.

------------------------------------------------------------------------

# Important instruction for working with me

I need to understand the project well enough to explain it in an
interview.

Therefore:

-   write readable code,
-   use descriptive variable/function names,
-   comment non-obvious logic,
-   avoid unnecessary abstractions,
-   explain important architecture choices,
-   flag anything I should understand before presenting it,
-   do not hide complexity behind generated code I cannot reasonably
    explain.

If you have to choose between: **technically sophisticated** and **easy
to demonstrate/explain**, choose the latter unless sophistication
materially improves the interview demo.

------------------------------------------------------------------------

# First task

Before writing the entire application:

1.  inspect the current repository,
2.  propose the final file structure,
3.  identify the minimum dependencies,
4.  give me a short implementation plan,
5.  then begin Phase 1.

Do not ask broad product questions unless something genuinely blocks
implementation. The product requirements above should be treated as the
source of truth.
