"""Human decision records for the evidence-first PSPS preparation workflow."""


ALLOWED_DECISION_ACTIONS = (
    "Request missing information",
    "Review escalation brief",
    "Approve proposed next step",
    "Revise assessment",
    "Reject proposed next step",
)


def append_decision(log: list[dict], *, action: str, case_id: str, assessment_version: int,
                    evidence_ids: list[str], rationale: str, timestamp: str,
                    actor: str = "Demo operator") -> list[dict]:
    """Append one review decision, ignoring an identical repeat click."""
    if action not in ALLOWED_DECISION_ACTIONS:
        raise ValueError(f"Unsupported decision action: {action}")
    clean_rationale = rationale.strip() or "Operator decision recorded from reviewed evidence."
    decision_key = f"{case_id}:{assessment_version}:{action}:{clean_rationale}"
    if any(item.get("decision_key") == decision_key for item in log):
        return log
    log.append({
        "decision_key": decision_key,
        "timestamp": timestamp,
        "actor": actor,
        "case_id": case_id,
        "action": action,
        "assessment_version": assessment_version,
        "evidence_ids": list(dict.fromkeys(evidence_ids)),
        "rationale": clean_rationale,
        "status": "recorded",
        "operational_effect": "None; preparation/review workflow only",
    })
    return log
