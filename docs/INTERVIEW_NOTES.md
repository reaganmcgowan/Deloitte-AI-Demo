# GridGuard interview notes

Use these notes for the short presentation after the three-minute video. The goal is to
show product judgment: how the problem was discovered, why this use case was prioritized,
what was built, how it was validated, and how it could become a real capability.

## One-minute positioning

**Target user:** a utility operations or resilience analyst who must assemble an incident
picture quickly and prepare an escalation or field-review brief for an authorized operator.

**Customer pain:** relevant facts are distributed across operational, weather, asset,
facility, maintenance, and field systems. The analyst must reconcile changing evidence,
identify missing information, estimate consequence, and explain the recommendation under
time pressure.

**Value proposition:** GridGuard turns fragmented, changing evidence into a shared,
circuit-level investigation package with traceable sources, visible uncertainty, deduplicated
impact, and reviewable response options.

**Differentiators:**

1. It is an investigation workflow, not a dashboard that only displays a risk score.
2. It joins electrical conditions, environmental context, and consequence relationships
   around one circuit.
3. It separates recorded facts, deterministic interpretations, and unknowns.
4. Its four agents have inspectable inputs and outputs.
5. Its human-in-the-loop controls record the evidence version and rationale without
   executing an operational action.

## How the prototype reflects the role

### Sector and market discovery

The About page frames the utility context: wildfire exposure, heat-driven demand,
equipment anomalies, critical facilities, and the need for a common operating picture.
The Related reading links ground that framing in DOE and GAO resilience material.

In the interview, say that the next discovery step would be interviews with:

- Distribution operations and control-room analysts
- Wildfire/resilience planning teams
- Field maintenance and inspection coordinators
- Critical-facility or emergency-management liaisons
- IT/data owners for telemetry, GIS, outage, weather, and maintenance systems

Ask each persona what triggers a review, what evidence they trust, where handoffs fail, and
what action they are authorized to recommend.

### Problem statement, personas, and prioritized use case

The primary persona is the operations/resilience analyst preparing a defensible review.
Secondary personas are the field coordinator, facility liaison, and approving operator.

The prioritized use case is deliberately narrow: **investigate one circuit when an equipment
signal and dangerous environmental conditions converge**. It was prioritized because it has:

- High consequence: customers and a hospital may be affected
- Multiple evidence sources and handoffs
- A clear human decision point
- A demonstrable need for provenance and freshness
- A safe prototype boundary: prepare and review, never control the grid

### Hands-on AI-native prototyping

The prototype demonstrates an agentic contract without pretending that an LLM is required
for deterministic calculations:

- Grid Agent evaluates load, capacity, demand trend, temperature, and condition.
- Wildfire Agent joins weather and fire-risk context and applies the anomaly gate.
- Impact Agent traverses relationships and deduplicates customers and facilities.
- Response Agent prepares options with evidence, alternatives, tradeoffs, and prerequisites.

Template explanations work offline. A future LLM seam could summarize new reports, classify
unstructured maintenance notes, or draft an escalation brief, while deterministic gates and
source citations remain authoritative.

### Rapid iteration and usability

The visible iterations are the shift from broad grid-health metrics to an investigation
queue, map, evidence files, agent pipeline, and human-review card. The scenario also changed
from a single dramatic score to staged evidence so the operator can see what changes and why.

Call out the interaction decisions:

- Dashboard opens directly for operational context; About provides presentation framing.
- Detail is collapsed until needed.
- Utilization bars update selected-circuit details on click.
- Evidence files use readable labels while retaining canonical IDs.
- Continue advances one checkpoint and pauses at key moments.
- Reset makes the demo reproducible.

### Validation activities

Validation already demonstrated in the prototype:

- Baseline produces no critical incident.
- Weather alone does not create an electrical anomaly.
- Customer and facility totals are deduplicated.
- Repeated evaluation does not duplicate incidents.
- Reset supports a second complete run.
- Browser progression was tested through 2:00 PM, 3:00 PM, 3:30 PM, and 4:00 PM.
- Regression coverage includes the former 2:00 PM transition failure.
- The full automated suite passes.

Next validation activities:

- Five-minute usability test with an operations persona: find the highest-priority case,
  explain why it matters, and identify the missing information.
- Compare time-to-brief and evidence completeness with the current manual workflow.
- Test whether users distinguish environmental exposure from gated combined exposure.
- Test whether operators trust the recommendation more when source freshness and unknowns
  are visible.
- Use findings to revise labels, hierarchy, and workflow before integrating live systems.

### Product positioning and GTM narrative

Position GridGuard as an **evidence-to-decision layer for utility resilience operations**,
not as an autonomous grid controller or a replacement for SCADA/OMS.

Initial buyer and champion hypotheses:

- Champion: resilience or operations transformation lead
- Daily user: operations/resilience analyst
- Stakeholders: field operations, emergency management, IT/data governance, and critical
  infrastructure coordination
- Executive value: faster triage, fewer duplicated reviews, better critical-facility
  visibility, and more defensible decisions

A credible adoption path is to start with one approved workflow and read-only integrations,
prove evidence assembly and review speed, then expand to additional hazards and circuits.

### Demo artifacts and next steps

Artifacts to mention:

- Three-minute prototype walkthrough
- About-page problem and solution framing
- Command Center with map, queue, utilization, evidence, agents, and HITL controls
- Synthetic scenario and source registry
- Deterministic tests and evaluation harness
- This demo script and interview notes

Recommended next steps:

1. Conduct discovery interviews and map the current incident-review process.
2. Validate the C-184 workflow with representative users and real redacted records.
3. Define data contracts, access controls, retention, and provenance requirements.
4. Replace synthetic rules with validated models and approved operating procedures.
5. Pilot read-only evidence assembly before considering any operational integration.

## Three phrases to remember

- “The product is an evidence-to-decision layer, not an autonomous controller.”
- “The differentiated output is a defensible investigation package, not just a score.”
- “Every recommendation shows what is known, what is missing, and what a human must decide.”
