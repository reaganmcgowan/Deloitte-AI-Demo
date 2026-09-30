# GridGuard PSPS assessment pivot brief

**Purpose:** Define the next product direction before further implementation. This brief
does not replace the working prototype or the preserved source documents.

## Product decision

GridGuard should become an interview prototype for an operations analyst preparing a
Public Safety Power Shutoff (PSPS) assessment for an authorized decision-maker. The
product assembles evidence, exposes uncertainty, prepares options, and records review.
It does not decide whether to shut off power, authorize a PSPS, dispatch crews, notify
customers, or control infrastructure.

The central question is:

> What needs attention, what do we know, what is still unknown, and what must happen
> before an authorized person can make a defensible decision?

## Documented problem and evidence

The [CPUC PSPS overview](https://www.cpuc.ca.gov/PSPS) describes PSPS as a temporary
power shutoff for specific areas to reduce wildfire risk from electric infrastructure.
It also describes the tradeoff: de-energization can leave communities and essential
facilities without power. This supports the operational problem and the need to examine
both hazard exposure and consequences; it does not provide a universal operational
threshold for this prototype.

The [CPUC 2021 findings on 2019 events](https://www.cpuc.ca.gov/news-and-updates/all-news/cpuc-addresses-utility-failures-to-protect-public-safety-during-2019-psps-events)
documented failures and corrective actions involving communications, medical-needs
customers, backup-power coordination, critical-facility identification, public-safety
coordination, and GIS information. That supports treating information completeness and
coordination as first-class product concerns. It does not establish that every utility
today has the same deficiencies.

The [SCE outage-types explanation](https://www.sce.com/outages-safety/outage-preparedness/outage-types)
distinguishes repair, maintenance, rotating, and PSPS outages and states that PSPS is
used during dangerous fire-weather conditions. It supports separating preventive
de-energization from ordinary outage response and from repair/restoration workflows.

The [DOE account of FireMap and Firescape](https://www.energy.gov/technologycommercialization/articles/firemap-helps-utilities-spot-wildfire-risks-and-boost-grid)
describes existing decision-support that combines satellite, weather, infrastructure,
and machine learning information and produces mitigation guidance. This is evidence
that GridGuard is entering an existing decision-support landscape; AI-assisted
assembly is not unique. GridGuard's differentiator should be inspectable source
provenance, explicit unknowns, revision history, and human decision preparation.

## Target user and decision

- **Primary user:** utility operations analyst preparing a PSPS assessment.
- **Decision-maker:** an authorized utility or emergency-management reviewer.
- **Decision:** whether the evidence is complete enough to prepare, revise, escalate,
  defer, or reject a proposed preventive-shutoff review.
- **Out of scope:** GridGuard does not authorize or execute a shutoff.

An electrical anomaly is not required to consider a preventive shutoff. Dangerous
environmental conditions can justify assessment before equipment fails. The prototype
must not invent ignition probabilities, avoided-harm estimates, or operational PSPS
thresholds.

## Proposed value and hypotheses

**Proposed value:** reduce the analyst's work assembling a defensible case by linking
structured records and documents, showing freshness and provenance, preserving unknowns,
and making revisions auditable.

**Hypotheses to test:**

1. Source-backed evidence and explicit readiness gaps help an analyst prepare a case
   faster or with fewer omissions.
2. Separating facts, interpretations, and unknowns improves reviewer trust and reduces
   unsupported conclusions.
3. Evidence updates and versioned assessment history make handoff to an authorized
   decision-maker clearer.
4. The workflow adds value beyond existing utility decision-support tools.

These are research hypotheses, not established benefits.

## MVP scope

### Include

- One excellent synthetic case: C-184 serving 8,420 accounts and one hospital.
- Assessment queue with transparent priority reasons and review status.
- Case workspace with current assessment, evidence, freshness, citations, unknowns,
  contradictions, options, prerequisites, and consequences.
- Synthetic maintenance note, field report, hospital-readiness record, and procedure
  excerpt with stable source IDs and timestamps.
- One meaningful evidence update that revises the assessment and explains what changed.
- Human actions: request information, review brief, revise assessment, and approve a
  proposed preparation step. Every action records evidence version, rationale, and time.
- Existing map, circuit relationships, scenario controls, impact joins, and decision log
  as supporting context.
- Offline rules-based fallback with explicit labeling.

### Explicitly exclude

- Automatic PSPS authorization, de-energization, dispatch, notifications, or controls.
- Operational shutoff thresholds or scientific ignition probabilities.
- Claims that all utilities reactively operate or lack existing systems.
- Production retrieval, authentication, durable audit storage, or real integrations.
- A single score that mechanically balances wildfire exposure against customer harm.
- Calling deterministic functions or templates autonomous AI agents.
- Filling missing facts with estimates or invented engineering feasibility.

## End-to-end demonstration

1. Open the queue and select C-184 because dangerous fire weather and a critical
   facility make the case important; the hospital's backup readiness is unverified.
2. Review source-labeled circuit, asset, weather, customer, facility, maintenance, and
   procedure evidence. The assessment distinguishes recorded facts from interpretations.
3. Request facility-status verification and review a preparation brief. The interface
   shows prerequisites and tradeoffs without recommending an automatic shutoff.
4. Introduce synthetic field report `FR-001`: visible T-882 damage is reported.
5. The assessment version increments, cites FR-001, changes the interpretation, and
   retains the unresolved hospital backup question.
6. Record an operator rationale and decision against the exact evidence version.

## Success measures and acceptance criteria

The prototype should measure:

- **Citation accuracy:** cited source supports the displayed claim.
- **Unsupported-claim rate:** claims without a source or explicit synthetic label.
- **Issue recall:** known missing or conflicting facts identified.
- **Revision appropriateness:** assessment changes when the field report changes and
  leaves unrelated unknowns unresolved.
- **Decision traceability:** every decision identifies evidence version, rationale, and
  timestamp.
- **Human effort:** analyst time or clicks to assemble a review packet, measured in a
  small usability exercise rather than claimed in advance.

The MVP passes when the C-184 walkthrough can be completed twice offline; all known
missing facts remain unknown; every factual statement has a source or synthetic label;
FR-001 changes the assessment; no action changes grid state; and the decision log is
reproducible after reset.

## Current implementation assessment

**Works today:** seeded six-CSV synthetic data, validated relationships, circuit-wide
impact joins, deterministic risk calculations, staged scenario, geographic map and
heatmap, investigation queue, Circuit 184 workspace, source-like evidence records,
unknowns, response options, synthetic field-report update, agent flow graph, session
decision log, and 58 automated tests.

**Not implemented:** real AI, document retrieval, embeddings, citations verified against
documents, contradiction detection across documents, durable audit storage, real
procedures, real PSPS rules, human authentication, and production controls.

The current four “agents” are deterministic Python functions with template text. They
are useful orchestration boundaries for the prototype, but should be described as
rules-based analysis modules until a real model and retrieval evaluation exist.

## Accepted demo decisions

- The first operator action is approval to prepare a PSPS review brief; simulated
  de-energization is outside the first decision flow.
- The first build stays rules-based and offline. A provider-neutral model adapter is a
  later seam, added only after retrieval and citation evaluation passes.
- Fixed synthetic freshness windows are 30 days for maintenance history, 24 hours for
  critical-facility backup readiness, and 7 days for field inspection reports. These
  values are demo settings, not utility policy.
