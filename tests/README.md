# Verification

Run from the project root after activating `.venv`:

```sh
python -m unittest discover -s tests -v
python -m src.ontology
python -m pip check
```

The original 18 focused data/relationship tests cover reproducible CSV bytes (including committed fixtures),
seed variation, schema and unit contracts, finite/bounded measurements, IDs,
foreign keys, stage weather coverage, cached totals, the exact hero chain,
overlapping impacts, available/skilled crews, interrupted versus exposed
customers, empty results, and snapshot isolation.

The default fixture comparison intentionally fails if committed CSVs drift from
seed 42. Generate other seeds in a separate directory. Tests require no network,
API key, or test framework beyond standard-library `unittest`.

The Phase 7 Command Center is tested with Streamlit AppTest and native Chrome.
The full approval/action workflow remains future work.


Phases 4–6 add 20 tests in `test_risk_engine.py`, `test_agents.py`, and
`test_scenario.py`: formula contributions and boundaries, missing/invalid data,
weather-only exposure, recommendation evidence and crew eligibility, no automatic
execution, stage timing, unique impact totals, repeated evaluation, and reset.
All **38 tests** pass. Run `python -m src.scenario` for the readable CLI demo.

Phase 7 adds four tests in `test_command_center.py`, bringing the total to **42**.
They cover baseline and error states, two full advance/reset cycles, stable selection
and reruns, exact KPIs and queue ordering, selected evidence, and schematic nodes.
See [the UI walkthrough](../docs/COMMAND_CENTER.md).

Map/activity refinement adds three tests (45 total): fixture geography and risk
layer correctness, blank future heat-map stages, and UI history deduplication/reset.

Timed playback adds four clock tests (49 total); UI tests now drive Start/Continue
and checkpoint timing, preserving the prior KPI, selection, and reset checks.

Continuous-time playback adds six tests (55 total): interpolated measurements,
discrete final-stage fault timing, slider and speed controls, backward seeking,
and exact final impact totals.

Service-area variability and secondary anomaly coverage add two scenario tests (57
total), ensuring circuits have distinct load trajectories while the designed C-184
incident remains deterministic and earlier C-186/C-188 advisories are retained as
resolved history.

The agent orchestration graph adds one presentation-contract test (58 total),
covering source nodes, agent responsibilities, reasoning text, and outputs.
