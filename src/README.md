# Application logic

- `data_generator.py`: stable synthetic topology, seeded measurements, deterministic
  CSV export. Run `python -m src.data_generator` from the project root.
- `ontology.py`: CSV loading, data validation, and `GridModel` lookup helpers.
  Run `python -m src.ontology` for the T-882 trace; `--asset T-883` selects another asset.

`GridModel` validates its input and stores a copy. Lookups return copied records.
Use `circuit_for_asset`, `assets_for_circuit`, `customer_areas_for_circuit`,
`facilities_for_circuit`, `weather_for_circuit`, `crews_for_circuit`, and
`impact_for_assets`. Unknown IDs and missing data raise `DataQualityError`.
Valid circuits with no facilities or eligible crews return empty tables.

Customer areas are the source of truth. Impact joins start with unique circuits,
so multiple assets on the same circuit cannot multiply customer or facility counts.
Domain code is independent of Streamlit.

Phases 4–6 add `risk_engine.py` (factors, gates, priorities), `agents.py` (four
bounded deterministic functions), `recommendations.py` (proposals without action
execution), and `scenario.py` (baseline-derived stages and stable incidents).
Run `python -m src.scenario` or `python -m src.scenario --json`.
See [the contract](../docs/SCORING.md) for formulas and API semantics.

`Scenario.evaluate()` returns copied findings without advancing time;
`advance()` moves forward one stage; `reset()` clears incidents and returns to
baseline with a new local run ID. The Phase 7 Command Center uses `command_center.py` for queue formatting and the
offline Plotly schematic; `app.py` owns widgets and session state. Approval
handling, simulated actions, assets and log views remain future work (Phases 8–9).
