"""Source-backed synthetic evidence for the PSPS assessment demo.

These records are deliberately small and local.  They provide stable identifiers,
ownership, timestamps, and demo freshness rules so every claim in the investigation
workspace can be traced without an external document system.
"""

from copy import deepcopy
from datetime import timedelta

import pandas as pd


DEMO_FRESHNESS_WINDOWS = {
    "maintenance": timedelta(days=30),
    "critical_facility_backup": timedelta(hours=24),
    "field_inspection": timedelta(days=7),
    "procedure": None,
    "telemetry": None,
}


_SOURCES = [
    {
        "source_id": "MAINT-T882-20260814-01",
        "source_type": "maintenance_note",
        "owner": "Asset maintenance",
        "timestamp": "2026-08-14T09:00:00-07:00",
        "freshness_class": "maintenance",
        "circuit_id": "C-184",
        "text": "T-882 temperature deviation noted; follow-up inspection remains unresolved.",
        "synthetic": True,
    },
    {
        "source_id": "FAC-F001-READINESS-20260814-01",
        "source_type": "facility_readiness_record",
        "owner": "Facility liaison",
        "timestamp": "2026-08-14T08:00:00-07:00",
        "freshness_class": "critical_facility_backup",
        "circuit_id": "C-184",
        "text": "No current hospital backup-power readiness verification is available.",
        "synthetic": True,
    },
    {
        "source_id": "PROC-7.2-20260815-01",
        "source_type": "procedure_excerpt",
        "owner": "Operations procedures",
        "timestamp": "2026-08-15T12:00:00-07:00",
        "freshness_class": "procedure",
        "circuit_id": None,
        "text": "Before approving escalation, verify critical-facility backup readiness and obtain field confirmation for abnormal equipment.",
        "synthetic": True,
    },
    {
        "source_id": "FR-001",
        "source_type": "field_inspection_report",
        "owner": "Field operations",
        "timestamp": "2026-08-15T15:30:00-07:00",
        "freshness_class": "field_inspection",
        "circuit_id": "C-184",
        "text": "Visible equipment damage reported at T-882; scripted synthetic field evidence.",
        "synthetic": True,
    },
]


def source_registry(field_report: bool = False) -> list[dict]:
    """Return the available synthetic documents for the current assessment."""
    records = [source for source in _SOURCES if source["source_id"] != "FR-001" or field_report]
    return deepcopy(records)


def freshness(source: dict, as_of: str) -> dict:
    """Annotate one source with a deterministic demo freshness status."""
    window = DEMO_FRESHNESS_WINDOWS[source["freshness_class"]]
    observed = pd.Timestamp(source["timestamp"])
    reference = pd.Timestamp(as_of)
    age = reference - observed
    if window is None:
        status = "reference"
        window_label = "not time-limited"
    elif age <= window:
        status = "current"
        window_label = str(window)
    else:
        status = "stale"
        window_label = str(window)
    annotated = deepcopy(source)
    annotated.update(age_hours=round(age.total_seconds() / 3600, 1), freshness_status=status,
                     freshness_window=window_label)
    return annotated


def sources_for_circuit(circuit_id: str, as_of: str, field_report: bool = False) -> list[dict]:
    """Return source records relevant to a selected circuit with freshness labels."""
    records = [source for source in source_registry(field_report)
               if source["circuit_id"] in (None, circuit_id)]
    return [freshness(source, as_of) for source in records]
