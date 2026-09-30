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
| 1. Source-backed synthetic case | Add maintenance notes, field report FR-001, hospital readiness record, and procedure excerpt with source IDs, timestamps, owners, and freshness. | Phase 0 | Small | Open C-184 and trace every displayed fact to a source row/document. **Complete** |
| 2. Assessment queue/workspace | Replace generic health prominence with queue, case overview, evidence panel, readiness gaps, options, and assessment version. | Phases 0–1 | Medium | Complete the initial C-184 review without opening the old broad dashboard. **Complete** |
| 3. Evidence update and revision | Add field-report control, source diff, changed interpretation, preserved unknowns, and revision history. | Phase 2 | Medium | FR-001 changes the brief while hospital backup remains unresolved. **Complete** |
| 4. Retrieval and citation adapter | Implement a local source registry and deterministic passage retrieval; define an optional model adapter with offline fallback. | Phase 1; test fixtures | Medium | Retrieve a procedure passage and show source, timestamp, and quoted span. **Complete** |
| 5. Contradiction and freshness checks | Compare readiness records, maintenance notes, and field reports; flag stale, conflicting, or missing values without resolving them silently. | Phase 4 | Medium | Create a known contradiction and show its owner and effect on decision readiness. **Complete** |
| 6. Human decision workflow | Request information, review brief, revise assessment, approve preparation step, reject; record evidence version, rationale, actor placeholder, and timestamp. | Phases 2–3 | Medium | Make two different decisions against two assessment versions; replay safely. **Complete** |
| 7. Evaluation harness | Add known-answer cases for citations, unsupported claims, missed issues, contradictions, revision quality, and effort. | Phases 4–6 | Medium | Run an offline scorecard and show failures rather than hiding them. **Complete** |
| 8. Interview polish | Tighten copy, source links, limitations, screenshots, demo script, and clean-environment run. | Phase 7 | Small | Deliver a 3–5 minute evidence-first walkthrough twice from Reset. **Complete** |

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

## Phase 1 implementation record

Phase 1 is complete in the offline prototype. `src/evidence.py` provides a local source
registry for the C-184 maintenance note, hospital readiness record, procedure excerpt,
and opt-in synthetic field report `FR-001`. Each source has a stable ID, type, owner,
timestamp, circuit scope, and synthetic label. The investigation workspace now exposes
those IDs and freshness status alongside every evidence row. The fixed demo windows are
30 days for maintenance, 24 hours for backup readiness, and 7 days for field reports.

The hospital record is intentionally marked stale at the scenario start, so the
workspace shows an information gap instead of inferring readiness. `FR-001` appears only
after the demo control introduces it. This remains a local registry, not production
retrieval or verified utility documentation.

## Phase 2 implementation record

Phase 2 is complete. `assessment_workspace()` now produces one versioned contract for the
selected case: current assessment, evidence rows, impact totals, unresolved questions,
response options, timestamp, and the explicit preparation-only decision gate. The
Streamlit workspace renders that contract after queue selection, so the C-184 review is
the primary flow while map, playback, and technical views remain supporting context.

## Phase 3 implementation record

Phase 3 is complete. The **Introduce new field report** control is idempotent and creates
assessment version 2 exactly once. The workspace shows the FR-001 source delta, the
revised interpretation, the timestamp, and a revision-history table. The hospital
backup-readiness gap remains unresolved after the update, and no grid or operational
state changes as a result of introducing evidence.

## Phase 4 implementation record

Phase 4 is complete for the offline prototype. `src/retrieval.py` provides deterministic
lexical passage retrieval over the local source registry, returning matched terms,
stable source IDs, excerpts, timestamps, owners, and freshness status. The workspace
shows those retrieved passages and citations for the selected case. An
`OfflineExplanationAdapter` defines the provider-neutral explanation seam; it cites only
retrieved sources and explicitly reports when no source supports an answer. No external
model dependency or API key is required.

## Phase 5 implementation record

Phase 5 is complete. `check_evidence_quality()` reports stale sources using the fixed
demo windows and detects conflicting critical-facility readiness statements when they
are present. Each contradiction includes source IDs, an owner, and a verification
message. The default C-184 case remains explicitly not ready for decision because the
hospital readiness record is stale; the system does not infer readiness or clear that
gap when FR-001 arrives.

## Phase 8 implementation record

Phase 8 is complete. The [interview demo script](PSPS_DEMO_SCRIPT.md) gives a repeatable
offline walkthrough covering the queue, C-184 evidence, retrieval citations, stale
readiness, FR-001 revision, human decision logging, evaluation, and reset. It also states
the prototype limits clearly: synthetic records, deterministic calculations, demo
freshness settings, and no operational controls. The repository remains runnable with
the documented local commands and without an API key.

## Phase 7 implementation record

Phase 7 is complete. `src/evaluation.py` runs reproducible known-answer checks for
source coverage, unsupported claims, unresolved gaps, freshness, baseline safety,
weather-only behavior, deduplicated impact, and evidence revision quality. Run
`python -m src.evaluation` to print the scorecard. The harness is intentionally small
and offline; it reports what was checked rather than claiming production model quality
or measured analyst time savings.

## Phase 6 implementation record

Phase 6 is complete. `append_decision()` records named review actions with the case ID,
assessment version, cited evidence IDs, operator rationale, actor placeholder,
timestamp, status, and explicit zero operational effect. The workflow supports requesting
information, reviewing the brief, approving a preparation step, revising the assessment,
and rejecting a proposed next step. Identical repeat clicks are ignored, and unsupported
actions such as de-energizing a circuit are rejected.
