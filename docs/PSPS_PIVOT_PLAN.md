# PSPS pivot development plan

This plan follows the pivot brief and precedes major implementation changes. Existing
working functionality remains the fallback at every phase.

## Architecture direction

Keep the current deterministic domain layer: `data_generator.py`, `ontology.py`,
`scenario.py`, `risk_engine.py`, and relationship helpers. Add a document/evidence
layer beside it rather than making the risk engine an AI system.

```text
synthetic records + synthetic documents
                 ↓
source registry / retrieval adapter
                 ↓
fact extraction + contradiction / freshness checks
                 ↓
versioned PSPS assessment
                 ↓
options and prerequisites → human decision log
```

Deterministic code owns IDs, joins, required fields, timestamps, arithmetic, workflow
constraints, and action idempotency. An optional model may summarize retrieved passages
but cannot invent values, thresholds, feasibility, or actions. The offline fallback is
rules-based and visibly labeled.

## Phased backlog

| Phase | Deliverable | Dependency | Relative effort | Demonstration milestone |
| --- | --- | --- | --- | --- |
| 0. Product contract | Adopt this brief; rename PSPS preparation language; freeze exclusions and source labels. | None | Small | Explain the target user, decision, and non-goals in 60 seconds. |
| 1. Source-backed synthetic case | Add maintenance notes, field report FR-001, hospital readiness record, and procedure excerpt with source IDs, timestamps, owners, and freshness. | Phase 0 | Small | Open C-184 and trace every displayed fact to a source row/document. |
| 2. Assessment queue/workspace | Replace generic health prominence with queue, case overview, evidence panel, readiness gaps, options, and assessment version. | Phases 0–1 | Medium | Complete the initial C-184 review without opening the old broad dashboard. |
| 3. Evidence update and revision | Add field-report control, source diff, changed interpretation, preserved unknowns, and revision history. | Phase 2 | Medium | FR-001 changes the brief while hospital backup remains unresolved. |
| 4. Retrieval and citation adapter | Implement a local source registry and deterministic passage retrieval; define an optional model adapter with offline fallback. | Phase 1; test fixtures | Medium | Retrieve a procedure passage and show source, timestamp, and quoted span. |
| 5. Contradiction and freshness checks | Compare readiness records, maintenance notes, and field reports; flag stale, conflicting, or missing values without resolving them silently. | Phase 4 | Medium | Create a known contradiction and show its owner and effect on decision readiness. |
| 6. Human decision workflow | Request information, review brief, revise assessment, approve preparation step, reject; record evidence version, rationale, actor placeholder, and timestamp. | Phases 2–3 | Medium | Make two different decisions against two assessment versions; replay safely. |
| 7. Evaluation harness | Add known-answer cases for citations, unsupported claims, missed issues, contradictions, revision quality, and effort. | Phases 4–6 | Medium | Run an offline scorecard and show failures rather than hiding them. |
| 8. Interview polish | Tighten copy, source links, limitations, screenshots, demo script, and clean-environment run. | Phase 7 | Small | Deliver a 3–5 minute evidence-first walkthrough twice from Reset. |

## Synthetic validation set

Use small cases with known answers:

1. **Complete C-184 case:** weather, asset, impact, procedure, and hospital readiness
   are internally consistent; expected result is a complete citation set and no false gap.
2. **Missing readiness:** remove the hospital backup record; expected result is an
   unresolved information request, not an inferred readiness status.
3. **Contradictory readiness:** facility record says generator tested; field report says
   test date is unknown; expected result is a contradiction assigned to the facility owner.
4. **Stale maintenance:** maintenance note is older than the configured freshness
   window; expected result is stale evidence, not a current condition claim.
5. **New damage report:** add FR-001 confirming T-882 damage; expected result is a
   versioned assessment revision with the new source cited and hospital gap retained.
6. **Weather without equipment issue:** dangerous weather but no electrical fault;
   expected result is PSPS assessment consideration, not an invented anomaly or automatic
   shutoff recommendation.

## Evaluation measures

For each case, record:

- citation precision and recall against the known source spans;
- unsupported factual claims per assessment;
- missed known gaps and contradictions;
- whether the revision changes only what new evidence supports;
- whether a reviewer can identify evidence freshness and limitations;
- time and clicks for an analyst to prepare a review packet.

Use a small human review rubric with two reviewers and preserve disagreements. Do not
report time savings until measured. A model response that sounds plausible but lacks a
source is a failure, even when its conclusion happens to be correct.

## Accepted scope decisions

1. The first human decision is **approve preparation of a PSPS review brief**, not
   approval of a simulated de-energization. This keeps the prototype focused on
   assembling and reviewing evidence.
2. Phase 1 remains rules-based and offline. Add a provider-neutral model adapter only
   after the retrieval evaluation passes. This gives the demo a reliable fallback,
   avoids a new API dependency, and makes any future AI contribution measurable.
3. Use fixed freshness windows for the synthetic case:
   - maintenance history: **30 days**;
   - critical-facility backup-readiness verification: **24 hours**;
   - field inspection reports: **7 days**.

These are demo configuration choices, not utility policy or operational standards. The
interface should show the window and source timestamp whenever it marks evidence stale.
Until Phase 4's retrieval evaluation is complete, do not add real model dependencies,
operational shutoff logic, or claims that the workflow improves utility practice.
