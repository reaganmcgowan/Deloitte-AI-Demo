# Phase 7 Command Center

Run from the project root:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Open the local URL Streamlit prints. Installation needs network access; the
Command Center itself uses local fixtures, a bundled Plotly schematic without
external map tiles, and deterministic template explanations. No API key is needed.

## Walkthrough

1. At 1:00 PM, review the investigation queue: three cases are visible with a
   priority, reason, and investigation status. Open Circuit 184 to inspect the
   assessment, evidence, unknowns, and response options.
2. Drag the **Time of day** slider to inspect gradual changes, or click **Start day**
   and let playback reach its first automatic pause. At 2:00 PM, Circuit 184's
   evidence shows rising load and a hospital relationship without a confirmed anomaly.
3. Click **Continue** to reach 3:00 PM: grid strain becomes High. Continue to 3:30 PM: environmental
   exposure rises while the combined indicator remains zero without an anomaly.
4. Continue to 4:00 PM: the banner highlights C-184's Critical combined incident.
   The queue has three distinct category findings, but KPI totals remain
   **8,420 customers and one hospital**, with zero customers interrupted.
5. Open Circuit 184 at 4:00 PM. The assessment names T-882, 46 mph wind, 11%
   humidity, the hospital, and eligible crew CR-01. Review the source-labeled
   evidence and unresolved hospital backup question, then compare response options.
   Expand the agent graph and investigation trail to inspect how the conclusion was formed.
6. Ordinary widget reruns preserve the stage and selected incident. A previous
   selection persists when advancing; the separate highest-priority banner still
   highlights a newly critical incident. Playback ends at the final stage.
7. Click **Reset scenario** to start a new session run at baseline. Replay as needed.

## Investigation-first workflow

The opening screen is an investigation queue. Its headline metrics count open cases,
cases awaiting review, and unresolved information requests. Select **Circuit 184** to
open the centerpiece workspace:

- **Current assessment** explains why the case needs attention and shows the assessment version.
- **Evidence** separates recorded facts from deterministic interpretations and includes a source and timestamp.
- **Missing or conflicting information** names each unknown, why it matters, and its verification owner.
- **Response options** show evidence, tradeoffs, prerequisites, and operator actions. Requests, escalation review, approval, and assessment revision are recorded against the current version; no action executes automatically.

Use **Introduce new field report** to add synthetic report FR-001. The assessment
version increments, the investigation trail records the update, and the escalation
brief reflects confirmed equipment damage while hospital backup readiness remains
unresolved. This is a scripted prototype update, clearly labeled as such.

## Presentation semantics

- Grid health means highest **active incident severity**, not a validated health
  percentage. The KPI tooltips explain this and the account-count approximation.
- KPI customer/facility values use the domain's union of impact, never sums of queue
  rows. Available crews is a global availability count, not the eligible count for
  one incident. Eligibility is shown beside the recommendation.
- The queue preserves domain priority ordering. The selector uses stable incident
  IDs and descriptive labels. **View highest priority** explicitly changes selection.
- The schematic shows all six circuits and eighteen assets. Squares are circuits,
  circles are assets; edges show membership, not electrical routing. Hover for
  loads and temperatures. Severity uses text in the queue as well as chart colors.
  Weather exposure is separate, so a shared weather zone alone cannot turn a
  circuit Critical. The selected circuit has a larger marker.
- Agent status means evaluation completed for the current stage. No fabricated
  live work, timers, or autonomous background activity is shown.
- The evidence preview is read-only. Approval/rejection/modification, simulated
  actions, a full investigation workflow, assets view, and decision log are deferred
  to Phases 8–9. No crew is reserved and no electricity state changes.
- One `Scenario` lives in Streamlit session state. Rendering evaluates it without
  advancing. Only running playback at a checkpoint, or an explicit Reset, changes scenario stage/run.
  New browser sessions start independently at baseline; state is not durable.
- Data-quality errors stop rendering instead of displaying reassuring zero metrics.

## Verification

`python -m unittest discover -s tests -v` runs 78 tests: all existing domain
checks plus Command Center/map/activity/playback/continuous-time tests. The new tests exercise actual Streamlit
widgets through `AppTest`, covering two complete advance/reset runs, empty state,
KPI totals, priority order, stable selection, selection-dependent evidence,
repeated reruns, final-stage disabling, missing data, and schematic content.

Native Chrome inspection verifies the rendered browser layout and interactions
in addition to AppTest. This is a Phase 7 check, not the full four-view, approval,
and outage walkthrough reserved for later phases.


## Compact overview, maps, and activity trail

Use **Risk layer** to compare grid strain, equipment, environmental exposure,
and combined electrical/wildfire indicators. The Overview keeps current status,
geographic risk, grid strain, and the recommended next step together. Six capacity
bars remain visible for side-by-side comparison, with each circuit's expandable
details directly beneath its own chart. Expand a circuit to inspect its current load,
capacity, utilization, demand drivers, weather, linked customers/facilities, anomaly,
and recommendation.
The Geographic
risk map groups the three co-located assets per circuit at their fixture coordinates
and adds lightning-bolt circuit icons plus hospital, fire-station, and water-facility
icons. Translucent shaded polygons show each circuit's approximate synthetic service
area, with the same qualitative risk color as its marker. These are display regions,
not surveyed utility boundaries or interpolated risk over land.
Circuit IDs are feeder/service-area identifiers: C-184 is the Santa Clarita Foothills
area, with a substation, transformer, and distribution line beneath it. Other areas
follow different synthetic load and equipment trajectories, so the map and heat map
show distributed movement even though the designed critical incident remains on C-184.
The default view needs no street tiles; enable **Show street basemap** for optional
OpenStreetMap context (internet required). All coordinates are synthetic and centered
around Santa Clarita; they do not identify real utility infrastructure.

**Circuit × time** uses the same fixed 0–100 scale and only colors stages already
evaluated in this dashboard session. Future/unrecorded cells are blank, not zero.
Reset clears history. Ordinary reruns replace existing stage evidence, so activity
records and heat map columns do not duplicate. If an existing browser session was
opened before this feature, Reset once to record a complete new progression.

**Grid strain** decomposes demand into baseline load, incremental energy demand, and
the synthetic afternoon event. These labels are scenario assumptions, not measured
end-use causes. Environmental operating conditions show wind, humidity, and ambient
temperature because they increase the consequence of an energized equipment fault;
weather alone cannot create an electrical anomaly. The T-882 fault is shown as a
discrete event at 4:00 PM.

**Agent activity** begins with an agent orchestration graph. Source nodes show the
structured information pulled from telemetry, circuit topology, weather, impact
relationships, and crews. Agent nodes show the four deterministic responsibilities;
output nodes show scores, environmental gates, deduplicated impact, and the reviewable
recommendation. Hover text explains each node and edge. A reasoning table beneath the
graph makes the input → reasoning → output contract inspectable. The existing activity
trail then lists completed analysis steps per evaluated stage for
the selected circuit, including actual anomaly results, environmental scores,
deduplicated impact and proposed response. A status indicator is shown while
current evaluation runs. No artificial delays or fabricated dispatch activity
are used. This is session-local evaluation history, not a durable audit log.

All 78 tests pass, including map coordinates/scores, blank future stages, continuous
interpolation, activity history persistence/deduplication/reset, evidence inspection,
and human-review workflow controls.

## Continuous playback and key moments

Click **Start day** to run the clock from 1:00 PM. Use the speed slider to choose
1, 3, 6, or 12 simulated minutes per real second. Measurements and risk values move
gradually between labeled checkpoints; at 2:00, 3:00, 3:30, and 4:00 PM playback
stops exactly, updates the agents/maps, and explains the key finding. The T-882 fault
is intentionally an immediate final-stage change. Click **Continue** to resume;
**Pause** lets you stop between checkpoints. Reset returns the clock, incidents, maps,
and activity history to baseline.

The visible clock moves continuously and interpolates synthetic inputs between
checkpoints. Delayed browser refreshes cannot skip checkpoints: elapsed time is
clamped to the next key moment, and unused elapsed time is discarded on pause.
Pauses do not accumulate elapsed time. Session state owns the clock, and a
Streamlit timer fragment updates it without rebuilding charts every second.

Verification now includes 78 tests: clock arithmetic, checkpoint clamping,
idempotent ticks, manual pause/resume, and the existing two full UI replays driven
by playback with injected time rather than waiting in real time.
