"""Freshness and contradiction checks for the evidence-first workflow."""

from src.evidence import sources_for_circuit


def check_evidence_quality(circuit_id: str, as_of: str, field_report: bool = False,
                           additional_sources: list[dict] | None = None) -> dict:
    """Return explicit evidence gaps without resolving them automatically."""
    sources = sources_for_circuit(circuit_id, as_of, field_report)
    sources.extend(additional_sources or [])
    stale = [source for source in sources if source.get("freshness_status") == "stale"]
    readiness = [source for source in sources if source.get("source_type") == "facility_readiness_record"]
    verified = [source for source in readiness if "verified" in source.get("text", "").lower()
                or "tested" in source.get("text", "").lower()]
    unresolved = [source for source in readiness if "no current" in source.get("text", "").lower()
                  or "unknown" in source.get("text", "").lower()
                  or "unverified" in source.get("text", "").lower()]
    contradictions = []
    if verified and unresolved:
        contradictions.append({
            "topic": "Critical-facility backup readiness",
            "source_ids": [source["source_id"] for source in verified + unresolved],
            "owner": "Facility liaison",
            "message": "Readiness records conflict; verify the test date and current backup status.",
        })
    return {
        "stale_sources": [{"source_id": source["source_id"], "owner": source["owner"],
                           "window": source["freshness_window"], "timestamp": source["timestamp"]}
                          for source in stale],
        "contradictions": contradictions,
        "ready_for_decision": not stale and not contradictions,
    }
