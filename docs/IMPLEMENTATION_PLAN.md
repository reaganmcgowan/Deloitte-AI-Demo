# GridGuard implementation plan

**Status:** Planned; no application implementation completed.
**Target:** An understandable, interview-ready local demo in approximately two working days.

## 1. Outcome and scope

Build one complete operational story for fictional California Electric: emerging heat and fire-weather conditions combine with an electrical anomaly, the system explains the consequences, and an operator makes a recorded decision that changes simulated state.

Use the [decomposition](GRIDGUARD_DECOMPOSITION.md) for product context and the [original build brief](../CODEX_BUILD_PROMPT.md) for technical constraints. Preserve both source documents. This plan is the working checklist for implementation.

### Required MVP

- Four views: Command Center, Incident Investigation, Grid / Assets, and Decision Log.
- Four specialized agents with structured, inspectable outputs.
- Three risk categories: grid strain, equipment anomaly, and combined wildfire/electrical exposure.
- Five-stage scenario, with the main C-184 incident at 4:00 PM.
- Approve Simulation / Modify / Reject controls and observable simulated outcomes.
- A small active-outage/restoration branch to cover incident response.
- An entirely functional offline mode with deterministic explanations.
- Clear synthetic-data and prototype labels in the README and application.

### Deferred

Real utility or weather integrations, live controls, actual crew dispatch, authentication, production persistence, trained wildfire prediction, power-flow modeling, autonomous PSPS execution, elaborate CSS, and agent frameworks. Optional LLM synthesis is secondary to a working demo.

## 2. Decisions for the first build

| Topic | Decision and reason |
| --- | --- |
| Project root | Use the existing `Deloitte AI Demo` directory; avoid a redundant nested project. |
| Data size | Start with 18 assets, 6 circuits, 12 customer areas, 3 critical facilities, and 4 crews. This fits the supplied scope while keeping inspection manageable. |
| Main incident | Transformer T-882 on C-184; linked customer areas total 8,420; exactly one linked hospital. |
| Data generation | Fixed seed and stable IDs; generated baseline CSV fixtures can be committed for easy review. |
| Relationships | Explicit IDs and pandas joins; no graph database. |
| Weather mapping | Add `zone_id` to circuits and weather. Store fire-zone severity on circuits for the MVP; a separate FireRiskArea table is deferred. |
| Customer totals | Use `customer_areas.csv` as the source of truth; validate any circuit-level cached totals against it. |
| State | Streamlit session state owns scenario stage, incidents, recommendations, decisions, and simulation overlays. Pure domain functions do not import Streamlit. |
| Navigation | Advance stages forward. Replay earlier conditions through Reset, which starts a new simulation run. This avoids inconsistent history. |
| Visual | Use a Plotly schematic network or geographic scatter without external tiles, so the demo works offline. |
| AI mode | Clearly display template mode or optional LLM-assisted explanation mode. Deterministic modules perform all calculations. |
| Repository tooling | Add dependency pins only when installed and checked. Git initialization, commits, and remote publishing are separate from this organization task. |

## 3. Planned file structure and ownership

Files below are future implementation targets unless already present.

```text
app.py                         # Streamlit entry point and four views
requirements.txt               # Tested runtime dependency versions
README.md                      # Status, project story, verified setup, demo
CODEX_BUILD_PROMPT.md           # Original build brief, unchanged
.gitignore
data/
  README.md
  assets.csv
  circuits.csv
  weather.csv
  customer_areas.csv
  critical_facilities.csv
  crews.csv
src/
  __init__.py
  data_generator.py            # Seeded fixture generation and validation
  ontology.py                  # Load and traverse connected objects
  risk_engine.py               # Normalization, scores, severity, priority
  agents.py                    # Four bounded agents and structured findings
  recommendations.py          # Allowed actions, eligibility, alternatives
  scenario.py                 # Stage fixtures and repeatable progression
  simulation.py               # Human decisions, state transitions, log
tests/
  test_data_and_ontology.py
  test_risk_engine.py
  test_agents.py
  test_scenario.py
  test_simulation.py
docs/
  GRIDGUARD_DECOMPOSITION.md   # Original decomposition, unchanged
  IMPLEMENTATION_PLAN.md
  DEMO_SCRIPT.md              # Add during final rehearsal
  screenshots/                # Add verified screenshots during final polish
```

Start with readable functions and dictionaries or standard-library dataclasses. Introduce additional modules only when they simplify the code. `simulation.py` separates state changes from recommendation generation, making approval behavior testable without the UI.

## 4. Data and reasoning contracts

### Units and validation

Use MW consistently for capacity and load, °F for temperatures, mph for wind, and percentages from 0–100 for humidity and condition. Define higher condition scores as healthier equipment. Distinguish asset temperature from ambient weather temperature. All timestamps use a documented synthetic scenario date and local California time.

Require unique primary IDs, valid foreign keys, positive capacity, nonnegative customer counts, finite measurements, and humidity/condition within bounds. Missing weather or an invalid join must produce an explicit data-quality issue; never silently turn missing inputs into zero risk.

Add a baseline asset temperature and a demand-trend value to the fixture contract so anomaly and trend calculations have defined inputs. Store weather by stage and zone; avoid duplicating static assets for each timestamp.

### Structured outputs

| Output | Required information |
| --- | --- |
| Risk result | Category, score 0–100, severity, contributing factors, normalization bounds, weights, and data-quality status. |
| Agent finding | Agent name, stage, linked asset/circuit IDs, evidence with units, explanation, and limitations. |
| Impact result | Unique customer-area IDs and total customers; unique facility IDs; vulnerability context; at-risk versus currently interrupted counts. |
| Incident | Stable ID within a run, risk category, affected circuit/assets, stage first detected, current severity, lifecycle status, and linked findings. |
| Recommendation | Stable ID and revision, incident ID, action type, prerequisites, rationale, alternatives, expected qualitative benefit, tradeoff, and approval state. |
| Decision | Run ID, recommendation revision, decision type, selected action, rationale, scenario timestamp, recorded timestamp, and before/after simulation state. |

Circuit-wide impact is a deliberate MVP approximation: an affected asset exposes its circuit's customer areas. Do not describe this as feeder-level electrical topology analysis. When multiple incidents overlap a circuit, count each customer area and facility once in dashboard totals.

### Risk scoring design

Implement normalization and weights as named constants in `risk_engine.py`; document exact values when implementing Phase 4. Use a bounded weighted sum for reliability factors (utilization, temperature anomaly, poor condition, demand trend). Keep environmental exposure visible separately from combined wildfire/electrical risk; extreme weather alone must not fabricate an electrical anomaly.

Use a documented rule requiring dangerous environmental conditions plus an electrical anomaly for the main critical wildfire incident. Rank incidents by maximum safety/reliability severity first, followed by consequence and urgency, with stable ID tie-breaking. Customer counts must not dilute a critical safety signal. Severity cutoffs and weights are illustrative prototype choices, not operational standards or probabilities.

Freeze the scoring contract and scenario expectations together in Phase 4. Test factor contributions and boundary behavior; do not tune the app to claim a particular scientifically meaningful numerical score.

## 5. Build sequence and acceptance gates

Complete each phase, run its checks, fix failures, and provide a brief explanation of what changed and how to verify it. Do not build all modules in one pass.

| Phase | Deliverable | Acceptance gate |
| --- | --- | --- |
| 1. Environment | Local virtual environment, tested minimal dependencies, package setup, basic Streamlit launch. | Launch successfully from a fresh environment; README commands match actual setup. |
| 2. Synthetic data | Six baseline CSV datasets, generator, validation, and documented units. | Same seed reproduces the same data; IDs and links validate; show sample records and explain their role. |
| 3. Ontology | Asset/circuit/weather/customer/facility/crew lookup helpers. | T-882 → C-184 resolves to exactly 8,420 customers and one hospital; orphan links fail clearly; overlapping impact is deduplicated. |
| 4. Risk engine | Transparent normalized factors, weights, severity rules, and priority calculation. | Ordinary baseline produces no critical incident; intended rising factors increase relevant indicators; results remain finite and bounded; zero capacity and missing data are handled explicitly. |
| 5. Agents | Four agents, evidence records, action candidates, and deterministic explanations. | Numerical outputs match domain calculations; response references actual evidence and offers eligible alternatives; unavailable crews are not assigned. |
| 6. Scenario | Five repeatable stages and the main incident, with stable identities. | Main combined-risk incident becomes critical at stage 5, not baseline; stage 4 shows weather exposure; re-evaluation does not duplicate incidents. |
| 7. Command Center | KPIs, sorted queue, schematic, agent progress, and stage controls. | Highest-severity incident is obvious; selection opens corresponding evidence; repeated Streamlit reruns do not reset or advance the simulation. |
| 8. Investigation and HITL | Evidence breakdown, options, modification, approval/rejection, and simulated state updates. | No action executes before approval; rejection changes no operational state; modified options require explicit submission; stale approvals and duplicate clicks cannot repeat an action. |
| 9. Assets and log | Linked asset view, load chart, decision log, and outage/restoration branch. | State, crew availability, affected customers, and log agree; repair/restoration closes the outage without claiming fire weather disappeared. |
| 10. Interview readiness | Final README, verified screenshots, demo script, and honest mode labels. | Complete a 3–5 minute offline walkthrough twice from Reset; run focused tests and clean-environment launch; distinguish implemented features from roadmap. |

### Suggested time allocation

**Day 1 (~8 hours):** environment 0.5h; datasets and relationships 2h; risk logic 1.5h; agents 1.5h; scenario and integrated checks 2.5h.

**Day 2 (~8 hours):** command center 2h; investigation and decisions 2h; assets/log/outage branch 1.5h; tests, README, screenshots, and rehearsal 2.5h.

If time gets tight, cut optional LLM support and visual polish first. Preserve the end-to-end story, correct impact calculations, approval behavior, and repeatability.

## 6. Scenario and decision semantics

| Stage | Expected behavior |
| --- | --- |
| 1 — 1:00 PM | Normal baseline; no critical incident. |
| 2 — 2:00 PM | Higher demand and ambient temperature; show evolving load. |
| 3 — 3:00 PM | Elevated utilization creates a grid-strain finding and preventive recommendation. |
| 4 — 3:30 PM | Wind rises and humidity falls around C-184; environmental exposure increases visibly. |
| 5 — 4:00 PM | T-882 anomaly combines with synthetic 46 mph wind and 11% humidity; C-184 becomes critical with 8,420 customers and one hospital at risk. |

Do not conflate preparing a de-energization review with actually de-energizing a simulated circuit. Every option has a distinct action type and explicit effect:

| Operator-approved option | Simulated effect |
| --- | --- |
| Monitor / escalate / prepare review | Record monitoring or review status; leave electricity state unchanged. |
| Dispatch inspection | Reserve an eligible available crew and mark inspection assigned. This alone does not repair equipment or remove risk. |
| Simulate de-energization | Explicit separate option showing interruption impact before approval; set `energized=False` and track interrupted customers/facilities. Environmental exposure remains visible. |
| Reject | Record rejection and rationale; retain the existing circuit and crew state. |
| Modify | Select an allowed alternative and rationale, then approve that specific revision. Editing alone does not execute it. |

For incident response, offer a small, explicitly labeled simulated equipment-outage event after the main scenario. This is distinct from a preventive shutoff. It creates an outage incident, supports approved crew assignment, and allows a separate explicit simulated repair-completion event. Restoration requires the repair-complete state and a fresh human decision; do not automatically re-energize a circuit merely because a crew was assigned. Track the outage reason so restoration cannot accidentally clear a preventive shutoff.

Apply decisions against the current run, stage, and recommendation revision. Invalidate stale recommendations when conditions change. Use an action identifier to make approval idempotent across Streamlit reruns.

Reset creates a new run with baseline conditions, no current incidents or decisions, and all baseline crew states. Clearly state that the session-local log is a demo history, not a durable or tamper-proof audit system. Optional CSV export can be added only after the required flow works.

## 7. Verification plan

Use standard-library `unittest` for deterministic domain tests; avoid introducing an extra test dependency initially.

- Data and ontology: fixed-seed reproduction, invalid references, customer totals, hospital link, and overlapping incidents.
- Risk: normalization bounds, thresholds, expected factor direction, missing inputs, and electrical/environmental conjunction.
- Agents: evidence fidelity, eligible actions, unavailable crews, and correct deterministic fallback.
- Scenario: expected main-incident timing, stable incident IDs, forward progression, and reset behavior.
- Simulation: no action without approval, rejection, modified action, stale decision rejection, idempotent approval, crew reservation, repair prerequisites, and restoration accounting.
- Manual UI: all four views, empty/no-incident state, stage progression, selected-incident persistence, consistent KPIs, and two full replay runs without a key or network.

The planned test command after test files exist is `python -m unittest discover -s tests -v`. Use UI checks for the actual interaction flow; passing unit tests alone does not verify Streamlit behavior.

## 8. Optional LLM explanation pass

Only after Phase 10 is functional, consider adding an optional provider SDK and adapter. Consult current official SDK documentation then, select and document a supported model, and keep credentials outside version control.

Send structured findings for wording assistance only. Preserve deterministic numbers and action choices in the UI regardless of generated text. On missing credentials, timeout, malformed response, or provider error, fall back to templates without losing the scenario or decision state. Show which explanation mode was used. Do not describe template-based agent functions as autonomous AI.

## 9. Interview story and definition of done

Explain the tradeoff, advance the scenario, open C-184, trace the customer/hospital relationships, show the evidence from each agent, and compare response options. Make one human decision and show its effect in the log. Briefly demonstrate the separate outage/restoration branch if time permits.

Be ready to explain why an ontology adds context, which calculations are deterministic, what generative AI contributes if enabled, why approval is separate from recommendation, and why a prototype indicator is not a wildfire probability.

- [ ] App launches using the documented setup in a clean environment.
- [ ] Complete offline demo works without secrets or external services.
- [ ] Main scenario and outage branch meet their acceptance gates.
- [ ] Impact calculations are traceable and do not double-count.
- [ ] Decisions are explicit, recorded, and safe against duplicate reruns.
- [ ] Tests pass; UI walkthrough is verified twice from Reset.
- [ ] README, screenshots, and demo script reflect actual behavior.
- [ ] Original documents remain unchanged.
- [ ] Public research claims are checked against their cited sources before interview submission; synthetic operational values are labeled throughout.

**Next implementation task:** Phase 1 environment setup, followed by Phase 2 synthetic data generation and a reviewable sample. This organization task stops before building the application.
