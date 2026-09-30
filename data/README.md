# Synthetic fixtures and data contract

All records describe fictional California Electric. The synthetic service area is
centered around Santa Clarita, California for map context. No real customers, facilities,
crew positions, utility measurements, or weather observations are used.

Regenerate from the project root with `python -m src.data_generator`. The default
seed is 42; `--seed 100 --output-dir /tmp/gridguard-sample` creates a separate
variant. Topology, IDs, customer totals, facilities, crews, and stage weather are
fixed story fixtures. The seed varies ordinary baseline equipment measurements
and vulnerability values. No wall-clock time or global random state enters generation.
The same seed and tested environment produce byte-identical CSV files.

| File | Rows | Key | Relationships |
| --- | ---: | --- | --- |
| assets.csv | 18 | asset_id | circuit_id → circuits |
| circuits.csv | 6 | circuit_id | zone_id → weather and crew coverage |
| weather.csv | 15 | zone_id + stage | 3 zones × 5 stages |
| customer_areas.csv | 12 | area_id | circuit_id → circuits |
| critical_facilities.csv | 3 | facility_id | circuit_id → circuits |
| crews.csv | 4 | crew_id | zone_id → circuit zones |

## Units and meanings

- `capacity_mw`, `current_load_mw`: MW everywhere, for both circuits and assets.
  Positive capacity; nonnegative load. Over-capacity load is valid input for a
  future risk engine. Three series assets per circuit carry the same baseline
  load; adding those loads would double-count electrical demand. A circuit ID
  (`C-184`) represents a feeder/service area; its substation, transformer, and
  distribution line are linked assets beneath that area. This remains a simplified
  circuit association, not an electrical topology or power-flow model.
- `temperature_f` and `baseline_temperature_f`: equipment temperature in °F.
  `ambient_temperature_f`: outdoor weather temperature in °F, a separate quantity.
- `wind_speed_mph`: mph. `humidity_pct`: 0–100 percent.
- `condition_score`: 0–100; higher means healthier equipment.
- `vulnerability_score`: illustrative 0–1 index; higher means more vulnerable.
  It is randomly generated and is not a demographic inference.
- `demand_trend_pct`: percentage change relative to baseline load, initially 0.
  Scenario stages give each service area a distinct load shape; assets do not have
  time-series copies in the static CSV fixtures.
- `age_years`: whole years; `latitude` and `longitude`: decimal degrees.
- `customer_count`, `customers_served`: whole synthetic service accounts, not people.
  Areas do not overlap; facility accounts are already included in the totals and
  must not be added again. Area counts are authoritative; cached circuit totals
  must agree with their sum.
- `energized`, `available`, `backup_power`: CSV `True` / `False` booleans.
  Backup power records its presence only, not capacity, readiness, or runtime.
- `fire_risk_zone`: low, moderate, high; a synthetic category on each circuit.
  It is not a calculated risk score. `zone_id` provides the shared geographic key.
- `stage`: 1–5. `timestamp`: synthetic August 15, 2026, in California
  (`America/Los_Angeles`, PDT, explicit `-07:00` offset): 13:00, 14:00,
  15:00, 15:30, 16:00. Every zone must have exactly one record at every stage.

`validate_data` checks required unit-bearing columns, nonempty values, unique and
well-formed IDs, foreign keys, finite measurements, bounds, integer counts,
booleans, categories, complete stage weather, and customer-total agreement.
Bounds are prototype data sanity checks, not operational safety thresholds.
A mislabeled measurement cannot be detected from its value alone: producers must
honor the documented units; the validator never guesses or converts units.

## Sample relationship

`T-882 → C-184 → CA-001 (4,200) + CA-002 (4,220) = 8,420 accounts`.
C-184 powers F-001, Synthetic Foothill Hospital, the circuit's only critical
facility. It maps to Z-01 weather and available inspection crew CR-01. CR-02
is unavailable and is excluded. Crew eligibility requires same zone, availability,
and exact skill; there is no dispatch, routing, distance, or travel-time model.

Weather at stage 5 in Z-01 is 104°F ambient, 46 mph wind, and 11% humidity.
These future-stage inputs are stored now; the static electrical tables remain
at the 13:00 baseline. No risk classification or incident is generated yet.

Use `python -m src.ontology` to validate the CSVs and print the linked hero record.
`customers_at_risk` means circuit-wide potential exposure, not an outage forecast;
`customers_interrupted` counts only selected circuits whose `energized` flag is false.
Repeated assets on a circuit are deduplicated before joining customer areas and
facilities. The model reports customer-weighted vulnerability, or `None` for zero
customers. This intentionally coarse impact approximation is not feeder tracing.
