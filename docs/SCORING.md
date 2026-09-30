# Phases 4–6: scoring, agents, and scenario contract

Every score is a **synthetic prototype indicator, not a validated probability**.
Weights, normalization bounds, anomaly rules, and severity thresholds below are
illustrative design choices for this fictional demo, not utility operating limits
or scientific wildfire thresholds. No model training or LLM is involved.

## Scoring arithmetic

Normalize each factor with `clip((value - lower) / (upper - lower), 0, 1)`.
Multiply by its weight and 100, then sum. Each result includes its category,
score, severity, data-quality status, raw factors, units, normalization bounds,
normalized values, weights, and individual point contributions. Calculations
retain full precision; the walkthrough rounds displayed scores to one decimal.

| Indicator | Factor | Raw input and normalization bounds | Weight |
| --- | --- | --- | ---: |
| Grid strain | Utilization | Maximum of asset load/capacity and circuit load/capacity; 0.70–1.10 | 65% |
| Grid strain | Demand trend | Percent increase from baseline circuit load; 0–60% | 20% |
| Grid strain | Poor condition | 100 minus condition score; 0–100 points | 15% |
| Equipment anomaly | Temperature rise | Asset temperature minus baseline equipment temperature; 10–60°F | 65% |
| Equipment anomaly | Utilization | Asset load/capacity; 0.70–1.10 | 20% |
| Equipment anomaly | Poor condition | 100 minus condition score; 0–100 points | 15% |
| Environmental exposure | Wind | 10–50 mph | 40% |
| Environmental exposure | Dryness | 40 minus humidity percentage; 0–30 percentage points | 30% |
| Environmental exposure | Ambient heat | 85–110°F | 20% |
| Environmental exposure | Zone | Low=0, moderate=0.5, high=1; 0–1 | 10% |
| Combined electrical/wildfire | Environmental indicator | 0–100 points | 60% |
| Combined electrical/wildfire | Equipment indicator | 0–100 points | 40% |

Severity is NORMAL below 30, ELEVATED from 30 to below 60, HIGH from 60 to
below 85, and CRITICAL at 85 or higher. Customer counts do not enter these risk
scores: a smaller circuit cannot dilute an otherwise critical safety signal.

Grid strain and equipment indicators are computed per asset. The circuit finding
uses the maximum per-asset score and records its source asset ID. Grid strain
includes circuit utilization because equipment belongs to the same circuit.
Series equipment loads are never summed. Scores can differ slightly among assets
due to their capacities and condition scores.

## Electrical anomaly and combined-risk gates

An electrical anomaly is detected from **electrical inputs alone** when either:

- Equipment temperature is at least 30°F above baseline **and** asset utilization
  is at least 90%; or
- Asset utilization reaches at least 110%.

Dangerous environmental conditions require **all** of: high fire-risk zone,
wind at least 35 mph, humidity at most 20%, and ambient temperature at least 95°F.
These values are illustrative prototype rules, not operational instructions.

The combined result applies these explicit rules after its weighted sum:

1. Without an electrical anomaly on an energized circuit and an operational asset,
   the combined score is zero. Environmental exposure remains independently visible.
2. With eligible electrical anomaly **and** dangerous environmental conditions,
   the combined score has a CRITICAL floor of 85.
3. With an eligible anomaly but without the full environmental conjunction,
   the combined score is capped at 84, below CRITICAL.

Each combined result retains `weighted_score`, `rule`, and `rule_adjustment`.
The final score equals the sum of weighted contributions plus the rule adjustment.
The critical floor is a visible policy rule, not a hidden change to the arithmetic.
A zero combined score means this particular prototype conjunction is absent; it
does not establish that real-world conditions are safe.

The risk functions reject zero capacity, nonfinite measurements, missing inputs,
and incompatible asset/circuit/weather links with `DataQualityError`. Scenario
snapshots also pass the full Phase 3 schema validation. Invalid data never becomes
a synthetic zero-risk result.

## Four agents and recommendation behavior

| Agent | Bounded responsibility |
| --- | --- |
| Grid Reliability | Read electrical measurements, calculate grid/equipment indicators, identify anomalous assets, and explain the contributing factors. |
| Wildfire Risk | Read stage-specific zone weather, show environmental exposure separately, and calculate the gated combined indicator for each asset. |
| Impact | Traverse validated relationships and union customer areas and facilities. Report exposed and interrupted accounts separately, plus vulnerability context. |
| Response | Combine those findings into a proposal with evidence, prerequisites, alternatives, benefits, and tradeoffs. Filter eligible inspection crews by availability, zone, and skill. |

All explanations are labeled `deterministic_template`. No API key, network call,
or generative model is needed. These are bounded functions, not autonomous agents
that operate infrastructure. Findings carry stage, timestamp, asset/circuit IDs,
evidence, and limitations. Response rejects mismatched stages/circuits.

Response policy:

- Normal electrical conditions: continue monitoring; escalation is an alternative.
- Elevated electrical indicator: prepare a load-redistribution study; this proposes
  engineering review and makes no claim that redistribution is feasible.
- High/critical electrical indicator or critical combined exposure: propose
  inspection if an eligible crew exists, otherwise escalate without assigning one.
- Critical combined exposure: also recommend escalation and preparation of a
  targeted de-energization review. The alternatives retain monitoring with current
  exposure, and planning a review with the possible consequences of a future outage.

Each proposal includes a stable recommendation ID, incident ID (or `None` for a
circuit assessment without an incident), revision equal to the evaluated stage,
`awaiting_human_review` status, and `executed=False`. Re-evaluating a stage produces
the same revision. Crew IDs are candidates only; no reservation occurs. Preparing
review does not shut off electricity. The human-review workflow records approval,
modification, rejection, or information requests with an assessment version and
evidence IDs; no action execution function exists.

## Scenario and incident semantics

Synthetic date: August 15, 2026, California PDT (`-07:00`). Every stage is derived
from a copied baseline rather than incrementally multiplying the previous state.
CSV fixtures remain unchanged. Existing five-stage weather fixtures are reused.

| Stage | Time | C-184 load/capacity | Ordinary asset rise above baseline | T-882 rise |
| --- | --- | ---: | ---: | ---: |
| 1 | 1:00 PM | Baseline: 17.88/30 MW, 59.6% | 0°F | 0°F |
| 2 | 2:00 PM | 24/30 MW, 80% | 6°F | 6°F |
| 3 | 3:00 PM | 28.8/30 MW, 96% | 12°F | 12°F |
| 4 | 3:30 PM | 29.4/30 MW, 98% | 18°F | 18°F |
| 5 | 4:00 PM | 31.5/30 MW, 105% | 20°F | 65°F |

Other circuits use baseline load multipliers 1, 1.05, 1.10, 1.12, 1.15.
Demand trend is `(stage load / baseline load - 1) × 100`. The scenario requires
positive baseline circuit loads to define that percentage. All three series
assets inherit their circuit's load while retaining individual capacities.
At 3:00 PM, S-882 carries 28.8/36 MW (80% utilization); C-184 reaches 96%.
At 4:00 PM, T-882 reaches 163.3°F against its 98.3°F equipment baseline.
The deterministic anomaly is thus independently supported by temperature and load.

Incident creation is keyed by `(run_id, circuit_id, category)`:

- Grid strain: score at least ELEVATED.
- Equipment anomaly: score at least ELEVATED **and** a detected electrical anomaly.
- Combined exposure: gated score at least ELEVATED.
- Environmental exposure alone is shown as evidence, not a fabricated electrical incident.

An incident retains its first-detected stage/timestamp and ID as its evidence and
recommendation update. Repeated evaluation replaces the same registry entries;
it does not append copies. Inactive entries are marked resolved and retained in
history. Reports are deep copies. Active incidents sort by severity first,
then number of critical facilities, customer count, indicator score as an urgency
proxy, and stable ID. The ordering is a prototype prioritization rule.

At stage 5 there are three distinct C-184 category incidents, not three copies of
one event. The combined incident ranks first. Aggregate impact unions their assets
through unique circuits: **8,420 accounts and one hospital**, never 25,260 accounts
or three hospitals. Accounts remain energized, so interrupted customers stay zero.

`Scenario.advance()` moves forward one stage. `evaluate()` cannot advance time.
After stage 5, advancing raises an explicit error. `reset()` restores stage 1 and
clears the incident registry under a new local run ID. Measurements, findings,
and recommendations replay identically apart from run-scoped IDs. Run counters
are in-memory identifiers, not persistent globally unique audit records.

## Worked final-stage arithmetic

For T-882, the equipment contributions are 65 points for the 65°F temperature
rise (clipped to 1), 17.5 for utilization (105%), and 3.3 for condition (78):
**85.8**. Z-01 environmental contributions are 36 wind + 29 dryness + 15.2 ambient
heat + 10 zone = **90.2**. Combined is `0.6 × 90.2 + 0.4 × 85.8 = 88.44`, displayed
as **88.4 CRITICAL**. The critical floor does not alter this particular result.

## Local verification

```sh
source .venv/bin/activate
python -m unittest discover -s tests -v
python -m src.scenario
python -m src.scenario --json > /tmp/gridguard-stages.json
```

The 38 tests include the original 18, eight risk tests, four agent tests, and eight
scenario tests. They cover formula arithmetic and boundaries, invalid inputs,
weather without anomalies, unavailable crews, no action mutation, exact final
impact, deduplication, stable incident/recommendation identities, forward-only
stages, and reset replay. A saved readable run is in `PHASE_4_6_DEMO.md`.
