# Phases 4–6: saved synthetic walkthrough

Generated from the same report formatter as `python -m src.scenario` using baseline CSVs.
All measurements and scores are synthetic, not validated probabilities.
No recommendations execute actions. Full factors and alternatives are available
with `python -m src.scenario --json`. See [SCORING.md](SCORING.md) for the contract.

```text
Synthetic prototype indicator; not a validated probability. Deterministic template mode.

1:00 PM — baseline
  C-184 indicators: grid 3.8, equipment 3.8, environment 12.4, combined 0.0 / 100
  C-184: grid strain 3.8/100; equipment indicator 3.8/100. Electrical anomaly assets: none. Scores retain per-asset factors with units and weighted contributions.
  8 mph wind, 40% humidity, 88°F ambient. Environmental exposure 12.4/100; combined electrical/wildfire 0.0/100. No energized operational asset with an electrical anomaly.
  Open incidents: 0; unique exposure: 0 accounts, 0 facilities; interrupted: 0
  Recommendation: Continue monitoring
  Benefit: Preserves electricity and crew availability
  Tradeoff: Current exposure remains; monitoring does not repair equipment
  Alternatives: Escalate for operator review
  Human review required. No action executed.

2:00 PM — rising heat and demand
  C-184 indicators: grid 31.4, equipment 8.3, environment 27.2, combined 0.0 / 100
  C-184: grid strain 31.4/100; equipment indicator 8.3/100. Electrical anomaly assets: none. Scores retain per-asset factors with units and weighted contributions.
  12 mph wind, 32% humidity, 94°F ambient. Environmental exposure 27.2/100; combined electrical/wildfire 0.0/100. No energized operational asset with an electrical anomaly.
  Open incidents: 1; unique exposure: 8,420 accounts, 1 facilities; interrupted: 0
  Recommendation: Prepare load redistribution study
  Benefit: Allows review of potential capacity relief
  Tradeoff: No relief is achieved yet; feasibility requires engineering review
  Alternatives: Continue monitoring; Escalate for operator review
  Incident findings: C-184 grid_strain ELEVATED
  Exposed critical facilities: Synthetic Foothill Hospital (hospital)
  Human review required. No action executed.

3:00 PM — elevated grid utilization
  C-184 indicators: grid 66.0, equipment 18.9, environment 46.0, combined 0.0 / 100
  C-184: grid strain 66.0/100; equipment indicator 18.9/100. Electrical anomaly assets: none. Scores retain per-asset factors with units and weighted contributions.
  18 mph wind, 24% humidity, 100°F ambient. Environmental exposure 46.0/100; combined electrical/wildfire 0.0/100. No energized operational asset with an electrical anomaly.
  Open incidents: 1; unique exposure: 8,420 accounts, 1 facilities; interrupted: 0
  Recommendation: Propose inspection response
  Benefit: Could obtain field evidence after human approval
  Tradeoff: Uses crew capacity; inspection alone does not repair equipment or eliminate exposure
  Alternatives: Continue monitoring; Escalate for operator review
  Incident findings: C-184 grid_strain HIGH
  Exposed critical facilities: Synthetic Foothill Hospital (hospital)
  Human review required. No action executed.

3:30 PM — dangerous fire weather
  C-184 indicators: grid 69.2, equipment 27.7, environment 76.6, combined 0.0 / 100
  C-184: grid strain 69.2/100; equipment indicator 27.7/100. Electrical anomaly assets: none. Scores retain per-asset factors with units and weighted contributions.
  38 mph wind, 15% humidity, 102°F ambient. Environmental exposure 76.6/100; combined electrical/wildfire 0.0/100. No energized operational asset with an electrical anomaly.
  Open incidents: 1; unique exposure: 8,420 accounts, 1 facilities; interrupted: 0
  Recommendation: Propose inspection response
  Benefit: Could obtain field evidence after human approval
  Tradeoff: Uses crew capacity; inspection alone does not repair equipment or eliminate exposure
  Alternatives: Continue monitoring; Escalate for operator review
  Incident findings: C-184 grid_strain HIGH
  Exposed critical facilities: Synthetic Foothill Hospital (hospital)
  Human review required. No action executed.

4:00 PM — T-882 electrical anomaly
  C-184 indicators: grid 80.6, equipment 85.8, environment 90.2, combined 88.4 / 100
  C-184: grid strain 80.6/100; equipment indicator 85.8/100. Electrical anomaly assets: T-882. Scores retain per-asset factors with units and weighted contributions.
  46 mph wind, 11% humidity, 104°F ambient. Environmental exposure 90.2/100; combined electrical/wildfire 88.4/100. Electrical anomaly AND dangerous weather: critical floor 85.
  Open incidents: 3; unique exposure: 8,420 accounts, 1 facilities; interrupted: 0
  Recommendation: Propose inspection response
  Benefit: Could obtain field evidence after human approval
  Tradeoff: Uses crew capacity; inspection alone does not repair equipment or eliminate exposure
  Alternatives: Continue monitoring; Escalate for operator review; Prepare targeted de-energization review
  Follow-up review: Escalate for operator review; Prepare targeted de-energization review
  Incident findings: C-184 combined_wildfire CRITICAL; C-184 equipment_anomaly CRITICAL; C-184 grid_strain HIGH
  Exposed critical facilities: Synthetic Foothill Hospital (hospital)
  Human review required. No action executed.
```
