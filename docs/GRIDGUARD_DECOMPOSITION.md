# GridGuard: AI Grid Risk & Resilience Command Center

## Problem Decomposition, Product Thesis, and Prototype Reference

**Project type:** Interview prototype / case study\
**Target sector:** Energy / electric utilities\
**Client:** Fictional California investor-owned utility ("California
Electric")\
**Primary users:** Grid operators, wildfire-risk teams, emergency
operations leaders, and field operations\
**Operating principle:** Human-in-the-loop (HITL). GridGuard recommends
and prioritizes; authorized humans approve consequential actions.

------------------------------------------------------------------------

## 1. Executive Thesis

California electric utilities face a difficult operating problem: they
must keep power reliable while also managing conditions in which
electrical infrastructure can contribute to catastrophic wildfire risk.
The safest action is not always "keep the power on," and the safest
action is not always "turn the power off."

GridGuard is an AI-enabled operational decision-support system designed
to help a utility answer:

> **Where is risk emerging across the grid, why is it happening, who
> could be affected, and what should we do next?**

Rather than creating another monitoring dashboard, GridGuard combines
grid, asset, environmental, customer-impact, and operational data into a
shared operational model. Specialized AI agents detect emerging risks,
investigate their causes, assess consequences, and recommend response
options. High-consequence actions remain subject to human approval.

The product is designed around three major risk classes:

1.  **Grid strain and reliability risk** --- demand, capacity, or
    failures threaten outages.
2.  **Wildfire ignition risk** --- electrical conditions interact with
    severe environmental conditions.
3.  **Asset failure risk** --- equipment degradation or abnormal
    behavior threatens reliability or safety.

The north-star workflow is:

**Monitor → Detect → Investigate → Assess Impact → Recommend → Human
Decision → Act → Learn**

------------------------------------------------------------------------

# 2. Why This Problem Matters

## 2.1 Wildfire risk

California Public Utilities Commission (CPUC) states that utility
infrastructure has historically been responsible for **less than 10% of
reported California wildfires**, but fires attributed to power lines
comprise **roughly half of the most destructive fires in California
history**.

This creates an asymmetric-risk problem: a relatively small number of
electrical ignitions can have extraordinarily high consequences.

**Source:** California Public Utilities Commission, "Wildfire and
Wildfire Safety"\
https://www.cpuc.ca.gov/industries-and-topics/wildfires

## 2.2 Preventive shutoffs create a second risk

California utilities may use a **Public Safety Power Shutoff (PSPS)** as
a last-resort wildfire-prevention measure when electrical infrastructure
faces imminent and significant wildfire risk. CPUC also emphasizes that
PSPS events create their own risks because communities and essential
facilities can lose electricity.

The tradeoff is therefore not:

> wildfire vs. nothing

It is:

> **wildfire/ignition risk vs. outage/public-safety risk**

A better decision system should help operators understand both sides of
that tradeoff.

**Source:** California Public Utilities Commission, "Public Safety Power
Shutoffs"\
https://www.cpuc.ca.gov/PSPS

## 2.3 The consequences can be large

During the October 26 and 29, 2019 PSPS events, transmission and
distribution de-energizations in California's North Coast affected
approximately **245,000 customers**, according to CPUC.

This illustrates why de-energization decisions require careful impact
assessment rather than a simple risk threshold.

**Source:** CPUC, "North Coast Resiliency Initiative"\
https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/infrastructure/resiliency-and-microgrids/north-coast-resiliency-initiative

## 2.4 Reliability risk exists even when system-wide capacity looks healthy

CAISO's 2026 Summer Loads and Resources Assessment reports a **2,547 MW
surplus** above the capacity needed to meet its planning reliability
standard under modeled conditions. Yet CAISO still identifies extreme
region-wide heat and wildfires as threats that can create emergency
conditions, particularly when disruptive events coincide.

This matters for the GridGuard thesis: risk is not simply "California
does not have enough electricity." Operational risk emerges from
combinations of load, resource availability, local equipment conditions,
wildfire, weather, and other disruptions.

**Source:** California ISO, "2026 Summer Loads and Resources
Assessment"\
https://www.caiso.com/generation-transmission/resource-adequacy/2026-summer-loads-and-resources-assessment

------------------------------------------------------------------------

# 3. Client

## California Electric (fictional)

For the prototype, California Electric is a fictional investor-owned
electric utility serving a mix of urban, suburban, and high-fire-risk
territory.

The fictional client allows the prototype to use realistic California
operating conditions without claiming access to any real utility's
internal data, thresholds, procedures, or systems.

### Client mission

Deliver electricity:

-   safely,
-   reliably,
-   affordably,
-   while reducing wildfire risk,
-   and maintaining regulatory accountability.

### Executive problem

California Electric has large quantities of operational information, but
the relevant signals are fragmented across systems and teams.

The challenge is not merely collecting more data.

The challenge is converting fragmented signals into a **shared
operational picture and prioritized decisions fast enough to matter.**

------------------------------------------------------------------------

# 4. Parties in the System

## Utility parties

### Grid Control / Distribution Operations

**Goal:** Maintain reliable electricity service.

Needs to know: - Where is the grid stressed? - Which assets are
approaching limits? - Where is an outage likely? - Can load be
shifted? - What action is operationally feasible?

### Wildfire / Meteorology / Risk Team

**Goal:** Reduce the probability of utility-involved ignition.

Needs to know: - Which circuits overlap dangerous fire-weather
conditions? - Where are wind, humidity, vegetation, and equipment risk
compounding? - Which circuits require inspection, protective settings,
or possible de-energization?

### Asset Management

**Goal:** Maintain equipment and prioritize limited maintenance
resources.

Needs to know: - Which transformers, lines, substations, or other assets
are degrading? - Which maintenance action has the highest risk-reduction
value?

### Emergency Operations Center

**Goal:** Coordinate response during high-impact events.

Needs to know: - What incidents are active? - Which communities and
facilities are affected? - What resources are available? - What is the
highest-priority response?

### Field Crews

**Goal:** Safely inspect, repair, and restore infrastructure.

Needs: - Clear task - Location - Asset context - Suspected cause -
Priority - Safety conditions

### Customer / Community Operations

**Goal:** Reduce harm from outages and communicate effectively.

Needs to know: - How many customers could lose power? - Which vulnerable
communities or critical facilities may be affected? - What is the
expected duration? - Who needs notification?

### Utility Executives

**Goal:** Balance safety, reliability, cost, and regulatory performance.

Needs: - System-level risk - Major incidents - reliability impacts -
wildfire exposure - operational response performance

## External parties

### CAISO

Operates the bulk electric grid across much of California and
coordinates system reliability.

### CPUC

Regulates California investor-owned electric utilities and oversees
areas including safety, reliability, rates, and PSPS requirements.

### California Office of Energy Infrastructure Safety

Focused on reducing utility-involved wildfire risk.

### CAL FIRE / emergency agencies

Provide wildfire and emergency context and coordinate response.

### Hospitals, fire stations, water systems, communications facilities

Critical infrastructure whose loss of electricity can amplify the
consequences of a shutoff or outage.

### Customers and communities

Ultimately experience both sides of the decision: the consequences of
wildfire and the consequences of electricity loss.

------------------------------------------------------------------------

# 5. The Core Decision Problem

The utility is continuously solving a constrained optimization problem:

> **Minimize expected harm while maintaining safe and reliable
> electricity service.**

Potential harm includes:

-   wildfire ignition,
-   uncontrolled equipment failure,
-   customer outages,
-   disruption to critical facilities,
-   worker/public safety,
-   restoration time,
-   economic loss,
-   regulatory consequences.

This creates competing objectives.

### Objective A --- Reliability

Keep electricity flowing.

### Objective B --- Safety

Prevent infrastructure from creating unacceptable hazards.

### Objective C --- Resilience

When disruption occurs, minimize its impact and recover quickly.

GridGuard should make these tradeoffs visible rather than hide them
behind a single opaque AI score.

------------------------------------------------------------------------

# 6. Problem Decomposition

## Problem 1 --- Fragmented operational picture

Relevant information may exist across different systems:

-   grid telemetry,
-   outage management,
-   GIS,
-   weather,
-   asset management,
-   vegetation/fire-risk information,
-   customer data,
-   critical-facility records,
-   crew availability.

### Consequence

No single operator or team necessarily sees the entire context of an
emerging event.

### GridGuard response

Create a common operational model connecting the real-world entities and
relationships required for decisions.

------------------------------------------------------------------------

## Problem 2 --- Signal overload

Thousands of measurements can change continuously.

### Consequence

Operators should not have to manually inspect every signal to discover
the handful of situations requiring attention.

### GridGuard response

Detection logic continuously screens for:

-   abnormal equipment behavior,
-   capacity pressure,
-   unusual temperature/load patterns,
-   dangerous combinations of environmental and electrical risk,
-   new outages,
-   rapidly increasing risk.

The objective is:

> **Many signals → few actionable incidents**

------------------------------------------------------------------------

## Problem 3 --- Risk signals lack context

An overloaded transformer alone may not be the highest-priority event.

The same transformer could become much more important if it:

-   serves a hospital,
-   sits in extreme fire weather,
-   has abnormal temperature,
-   is difficult to access,
-   has no easy load-transfer alternative.

### GridGuard response

Agents investigate incidents using linked operational context rather
than evaluating isolated alerts.

------------------------------------------------------------------------

## Problem 4 --- Prioritization under constraints

A utility may have:

-   20 incidents,
-   6 available crews,
-   multiple critical facilities,
-   several high-fire-risk circuits.

### Consequence

Everything cannot be handled simultaneously.

### GridGuard response

Rank incidents based on transparent dimensions such as:

-   safety risk,
-   wildfire risk,
-   probability/severity of failure,
-   customers affected,
-   critical infrastructure affected,
-   grid consequences,
-   available mitigation,
-   response feasibility.

------------------------------------------------------------------------

## Problem 5 --- Decision tradeoffs are difficult

Example:

**Circuit 184 has high wildfire risk.**

Option A: Keep energized\
Benefit: 8,420 customers retain electricity.\
Risk: possible ignition.

Option B: De-energize\
Benefit: electrical ignition risk decreases.\
Cost: 8,420 customers lose electricity and a critical facility may be
affected.

### GridGuard response

Present alternative actions and consequences rather than issuing an
unexplained command.

------------------------------------------------------------------------

## Problem 6 --- Response is often reactive

Traditional outage workflows begin after something has failed.

### GridGuard response

Support both:

**Preventive operations** - detect emerging risk, - inspect, -
redistribute load, - prepare crews, - prepare customers, - evaluate
de-energization.

**Incident operations** - localize failure, - determine impact, -
prioritize response, - dispatch crews, - track restoration.

------------------------------------------------------------------------

# 7. Palantir-Style Operational Ontology

This prototype does **not** implement Palantir Foundry. It borrows the
conceptual idea of representing operational reality as connected
objects, relationships, logic, and actions.

Palantir describes its Ontology as a representation of real-world
organizational objects, links, properties, actions, and logic. Palantir
also publishes a utility example in which electrical-grid and GIS data
were unified into a network model supporting outage localization,
root-cause analysis, asset reporting, and other workflows.

**Sources:** - Palantir, Ontology architecture:
https://www.palantir.com/docs/foundry/object-backend/overview - Palantir
utility network modeling example:
https://www.palantir.com/docs/foundry/use-case-examples/improving-decision-making-through-holistic-power-grid-network-modelling

## Core objects

### Asset

Examples: - Transformer - Substation - Distribution line - Circuit

Properties: - asset_id - type - capacity - current_load - temperature -
age - condition - latitude - longitude - operational_status

### Circuit

Properties: - circuit_id - energized - current_load - capacity -
wildfire_risk_zone - customers_served

### WeatherObservation

Properties: - location - timestamp - temperature - wind_speed - humidity

### FireRiskArea

Properties: - area_id - risk_level - vegetation/dryness proxy - weather
severity

### CustomerArea

Properties: - area_id - customer_count - vulnerability indicator

### CriticalFacility

Examples: - hospital - fire station - water facility - emergency shelter

Properties: - facility_type - location - backup_power - circuit_id

### Crew

Properties: - crew_id - location - availability - skills -
current_assignment

### Incident

Properties: - incident_id - risk_type - severity - status - confidence -
affected_asset - estimated_customers_affected -
critical_facilities_affected

### Recommendation

Properties: - recommendation_id - incident_id - proposed_action -
rationale - expected_benefit - expected_cost/risk - confidence -
approval_status

## Key relationships

-   Asset **BELONGS_TO** Circuit
-   Circuit **SERVES** CustomerArea
-   Circuit **POWERS** CriticalFacility
-   Asset **LOCATED_IN** FireRiskArea
-   WeatherObservation **AFFECTS** FireRiskArea
-   Incident **INVOLVES** Asset
-   Incident **IMPACTS** CustomerArea
-   Incident **THREATENS** CriticalFacility
-   Recommendation **RESPONDS_TO** Incident
-   Crew **CAN_RESPOND_TO** Incident

The ontology creates a connected operational graph.

Instead of:

> "Transformer T-882 is hot."

GridGuard can reason:

> "Transformer T-882 is hot, is operating near capacity, belongs to
> Circuit 184, Circuit 184 crosses a high-fire-risk area, serves 8,420
> customers, and powers a hospital."

That context changes the decision.

------------------------------------------------------------------------

# 8. Agent Architecture

## Agent 1 --- Grid Reliability Agent

### Question

**Where is the electrical system under abnormal strain?**

Inputs: - asset load, - capacity, - voltage/current proxies, - equipment
temperature, - demand forecast, - asset condition.

Outputs: - abnormal assets, - overload risk, - estimated reliability
risk, - contributing signals.

------------------------------------------------------------------------

## Agent 2 --- Wildfire Risk Agent

### Question

**Where could electrical conditions interact with dangerous fire
conditions?**

Inputs: - wind, - humidity, - temperature, - fire-risk zone, - asset
anomalies, - circuit location.

Outputs: - wildfire-related risk level, - environmental drivers, -
circuits requiring closer attention.

Important: the prototype must not claim to predict actual wildfire
ignition probability. It produces a simulated decision-support risk
score.

------------------------------------------------------------------------

## Agent 3 --- Impact Agent

### Question

**If this event worsens or we intervene, who and what are affected?**

Inputs: - grid topology, - customer counts, - critical facilities, -
incident location.

Outputs: - customers affected, - critical facilities affected, -
relative consequence.

------------------------------------------------------------------------

## Agent 4 --- Response Agent

### Question

**What should the operator consider doing next?**

Possible prototype recommendations: - monitor, - dispatch inspection
crew, - prepare backup resources, - redistribute load (simulated), -
escalate to emergency operations, - prepare targeted de-energization
review, - restore/repair after an outage.

Outputs: - recommended action, - alternatives, - rationale, - expected
impact.

------------------------------------------------------------------------

# 9. Human-in-the-Loop Control

GridGuard does **not** autonomously:

-   de-energize circuits,
-   control substations,
-   dispatch real crews,
-   change protective equipment,
-   reroute real electricity.

The prototype proposes actions.

Example:

**Recommended action:** Escalate Circuit 184 for targeted
de-energization review.

**Why** - high environmental fire risk, - abnormal asset signal, -
elevated wind, - 8,420 customers exposed.

**Tradeoff** - de-energization reduces electrical ignition exposure, -
but interrupts electricity to 8,420 customers and one critical facility.

Buttons:

**APPROVE SIMULATION**\
**MODIFY**\
**REJECT**

The operator's decision is recorded.

This makes the system an example of **human + AI operational
collaboration**, not autonomous critical-infrastructure control.

------------------------------------------------------------------------

# 10. Primary Use Cases

## Use Case 1 --- Emerging wildfire/electrical risk

**Trigger:** High wind + low humidity + electrical anomaly on a circuit
in a high-risk zone.

GridGuard: 1. detects abnormal conditions, 2. links circuit to
environmental conditions, 3. identifies customers/critical facilities,
4. raises incident priority, 5. recommends inspection/escalation, 6.
presents de-energization as an option if warranted, 7. requires human
approval.

------------------------------------------------------------------------

## Use Case 2 --- Heat-driven grid strain

**Trigger:** Forecast load approaches/exceeds a simulated local asset
threshold during extreme heat.

GridGuard: 1. detects forecast capacity pressure, 2. identifies affected
assets, 3. calculates downstream customers, 4. identifies alternatives,
5. recommends preventive actions, 6. monitors whether risk decreases.

------------------------------------------------------------------------

## Use Case 3 --- Equipment degradation

**Trigger:** Transformer shows unusual temperature/load behavior.

GridGuard: 1. detects anomaly, 2. reviews asset context, 3. assesses
downstream impact, 4. prioritizes inspection, 5. assigns/suggests a crew
in the simulation.

------------------------------------------------------------------------

## Use Case 4 --- Active blackout

**Trigger:** Asset/circuit becomes unavailable.

GridGuard: 1. creates incident, 2. localizes likely affected grid
segment, 3. identifies affected customers/facilities, 4. prioritizes
incident, 5. recommends crew response, 6. tracks simulated restoration.

------------------------------------------------------------------------

# 11. Prototype Scenario

## Scenario: California Heat + Fire-Weather Day

The interview demo should tell one coherent story.

### 1:00 PM

Grid operating normally.

### 2:00 PM

Temperature rises and electricity demand increases.

GridGuard identifies several assets moving toward elevated utilization.

### 3:00 PM

One substation enters a high-load state.

**Grid Reliability Agent:** elevated strain.

### 3:30 PM

Wind rises and humidity falls in a high-fire-risk territory.

**Wildfire Risk Agent:** Circuit 184 risk rises.

### 4:00 PM

An asset on Circuit 184 develops an abnormal temperature/load pattern.

Agents combine context.

**Incident: CIRCUIT 184**

Risk: CRITICAL\
Customers potentially affected: 8,420\
Critical facilities: 1 hospital\
Wind: 46 mph *(synthetic scenario value)*\
Humidity: 11% *(synthetic scenario value)*\
Electrical anomaly: detected

### AI recommendation

**Immediate:** Dispatch/prepare inspection response and escalate
incident.

**Contingency:** Evaluate targeted de-energization if
electrical/fire-risk indicators worsen.

### Human decision

Operator reviews:

**Keep energized** - preserves electricity, - retains current wildfire
exposure.

**Prepare/de-energize** - lowers electrical ignition exposure, - creates
outage consequences.

The human chooses.

The dashboard records the decision and updates the simulated operational
state.

------------------------------------------------------------------------

# 12. Dashboard

## Screen 1 --- Command Center

Top KPIs:

-   Grid Health
-   Active Incidents
-   Customers at Risk
-   Critical Facilities at Risk
-   Available Crews

Main components:

### Map / network visualization

Assets/circuits colored by risk.

### AI Priority Queue

Ranked incidents.

### Agent Activity

Shows: - detected, - investigating, - recommendation ready, - awaiting
human approval.

------------------------------------------------------------------------

## Screen 2 --- Incident Investigation

Example:

### Circuit 184 --- Critical

**WHY THIS WAS FLAGGED**

Grid: - asset anomaly, - high utilization.

Environment: - high wind, - low humidity, - high-risk territory.

Impact: - 8,420 customers, - hospital on circuit.

### Recommendation

Primary action\
Alternatives\
Expected benefits\
Tradeoffs\
Confidence/limitations

### Human decision controls

Approve simulation / Modify / Reject

------------------------------------------------------------------------

## Screen 3 --- Asset / Grid View

Select an asset and see:

-   historical load,
-   current load,
-   capacity,
-   temperature,
-   condition,
-   linked circuit,
-   downstream customers,
-   incidents.

------------------------------------------------------------------------

## Screen 4 --- Decision Log

Every AI recommendation and human decision is logged.

Columns: - time, - incident, - AI recommendation, - operator decision, -
rationale, - simulated outcome.

This demonstrates governance and auditability.

------------------------------------------------------------------------

# 13. What Is Actually AI in the Prototype?

Avoid using an LLM for everything.

## Deterministic logic

Use code for: - capacity calculations, - customers affected, - critical
facilities, - threshold logic, - scenario state, - numerical impact.

## Anomaly/risk model

Use a transparent synthetic risk model or simple anomaly detection
for: - unusual asset behavior, - load/capacity risk, - combined
environmental/electrical risk.

## Generative AI / agent layer

Use an LLM if available to: - synthesize findings, - explain why an
incident matters, - generate concise operator-facing recommendations, -
compare response options.

The app should include a deterministic fallback so the demo works
without an API key.

------------------------------------------------------------------------

# 14. Prototype Architecture

``` text
SYNTHETIC DATA
    |
    +-- assets.csv
    +-- circuits.csv
    +-- weather.csv
    +-- customers.csv
    +-- critical_facilities.csv
    +-- crews.csv
           |
           v
    OPERATIONAL MODEL
           |
    +------+-------+
    |              |
    v              v
RISK LOGIC      RELATIONSHIPS
    |              |
    +------+-------+
           |
           v
       AI AGENTS
    /      |       \
 Grid   Wildfire   Impact
    \      |       /
           v
     Response Agent
           |
           v
   RECOMMENDATION
           |
           v
     HUMAN APPROVAL
           |
           v
   SIMULATED ACTION
           |
           v
      DECISION LOG
```

------------------------------------------------------------------------

# 15. MVP Build Boundary

## Build in the 2-day prototype

-   Streamlit app
-   synthetic utility data
-   fictional California utility
-   10--30 assets
-   4--8 circuits
-   several customer zones
-   2--4 critical facilities
-   3--5 crews
-   simulated weather
-   3 risk categories
-   risk calculations
-   priority queue
-   incident drill-down
-   AI/agent explanation layer
-   HITL buttons
-   decision log
-   scenario progression

## Do NOT build

-   real grid controls,
-   real utility integrations,
-   real PSPS prediction,
-   real wildfire ignition prediction,
-   actual dispatch,
-   authentication,
-   production database,
-   complex power-flow simulation,
-   real-time SCADA,
-   autonomous infrastructure actions.

The prototype should demonstrate the **decision architecture**, not
recreate a utility control room.

------------------------------------------------------------------------

# 16. Success Metrics

If deployed for real, candidate metrics would include:

### Safety

-   high-risk conditions identified before incident,
-   time from risk emergence to operator awareness,
-   wildfire-risk events escalated appropriately.

### Reliability

-   customer interruption minutes,
-   outage duration,
-   customers affected,
-   restoration time.

### Operations

-   alert-to-incident compression,
-   time to root-cause hypothesis,
-   time to recommended action,
-   crew utilization.

### AI/HITL

-   recommendation acceptance rate,
-   operator overrides,
-   false-positive rate,
-   explanation usefulness,
-   time saved per incident.

The prototype should not claim measured real-world improvements.

------------------------------------------------------------------------

# 17. Palantir-Style Decomposition in One View

``` text
MISSION
Safe + Reliable Electricity
        |
        v
OPERATIONAL TENSIONS
Reliability <-----> Wildfire/Public Safety
        |
        v
DECISIONS
Where is risk?
Why?
Who is affected?
What action is available?
What are the tradeoffs?
        |
        v
OBJECTS
Assets -- Circuits -- Weather -- Fire Risk
   |          |          |          |
Customers -- Critical Facilities -- Crews
        |
        v
LOGIC
Anomaly Detection
Risk Scoring
Impact Analysis
Prioritization
        |
        v
AGENTS
Grid Agent
Wildfire Agent
Impact Agent
Response Agent
        |
        v
WORKFLOW
Detect
Investigate
Recommend
        |
        v
HUMAN DECISION
Approve / Modify / Reject
        |
        v
SIMULATED ACTION
Inspect / Escalate / Prepare / Restore
        |
        v
FEEDBACK
Outcome + Decision Log
```

------------------------------------------------------------------------

# 18. How to Explain the Project in the Interview

## 30-second version

> California utilities face a difficult tradeoff: they need to keep
> electricity reliable, but under certain conditions electrical
> infrastructure can also create wildfire risk. I built GridGuard as an
> AI-enabled grid risk and resilience command center. It brings together
> simulated grid, asset, weather, customer, and critical-infrastructure
> data. AI agents detect emerging risks, investigate why they matter,
> assess who could be affected, and recommend actions to an operator.
> Because these are high-consequence infrastructure decisions, the
> system is intentionally human-in-the-loop---the AI supports the
> decision rather than autonomously controlling the grid.

## The key insight

> The problem isn't a lack of dashboards. Utilities already generate
> enormous amounts of data. The problem I wanted to explore is how AI
> can turn fragmented signals into an operational decision.

## Why agents?

> Each agent has a bounded job. One evaluates grid conditions, one
> evaluates wildfire conditions, one assesses downstream impact, and a
> response agent synthesizes those findings into an actionable
> recommendation. That makes the reasoning easier to inspect than asking
> one general-purpose model to make an infrastructure decision.

## Why an ontology?

> A temperature reading isn't useful in isolation. It becomes
> operationally meaningful when I know which transformer it belongs to,
> which circuit that transformer is on, which customers that circuit
> serves, whether a hospital depends on it, and what environmental
> conditions surround it. The connected object model provides that
> context.

## Why HITL?

> In this domain, the cost of an incorrect action can be enormous. I
> designed AI to accelerate investigation and surface tradeoffs, while
> leaving consequential decisions---especially de-energization---with an
> authorized human operator.

------------------------------------------------------------------------

# 19. What This Prototype Is Not

GridGuard is a **conceptual prototype using synthetic data**.

It does not: - represent a real utility's internal operating
procedures, - predict actual wildfire ignition, - calculate real power
flows, - issue operational grid commands, - replace trained utility
operators.

Its purpose is to demonstrate how an AI-native decision architecture
could connect data, reasoning, recommendations, and human action in a
high-stakes operational environment.

------------------------------------------------------------------------

# 20. Research References

1.  California Public Utilities Commission. **Wildfire and Wildfire
    Safety.**\
    https://www.cpuc.ca.gov/industries-and-topics/wildfires

2.  California Public Utilities Commission. **Public Safety Power
    Shutoffs.**\
    https://www.cpuc.ca.gov/PSPS

3.  California Public Utilities Commission. **North Coast Resiliency
    Initiative.**\
    https://www.cpuc.ca.gov/industries-and-topics/electrical-energy/infrastructure/resiliency-and-microgrids/north-coast-resiliency-initiative

4.  California Independent System Operator. **2026 Summer Loads and
    Resources Assessment.**\
    https://www.caiso.com/generation-transmission/resource-adequacy/2026-summer-loads-and-resources-assessment

5.  Palantir. **Improving decision-making through holistic power grid
    network modeling.**\
    https://www.palantir.com/docs/foundry/use-case-examples/improving-decision-making-through-holistic-power-grid-network-modelling

6.  Palantir. **Ontology Architecture / Overview.**\
    https://www.palantir.com/docs/foundry/object-backend/overview

7.  Palantir. **The Ontology System.**\
    https://www.palantir.com/docs/foundry/architecture-center/ontology-system

------------------------------------------------------------------------

## Research integrity note

All client-specific operating data in the prototype---including customer
counts, asset measurements, wind values, humidity values, risk scores,
crews, recommendations, and incident scenarios---should be labeled
**synthetic** unless directly cited to a public source. Public
statistics above are included only where supported by the listed
sources.
