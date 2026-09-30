"""Offline evaluation harness for the evidence-first PSPS prototype."""

from src.investigation import assessment_workspace
from src.scenario import Scenario


EXPECTED_CITATIONS = {"MAINT-T882-20260814-01", "FAC-F001-READINESS-20260814-01", "PROC-7.2-20260815-01"}


def _check(name: str, passed: bool, detail: str) -> dict:
    return {"check": name, "passed": bool(passed), "detail": detail}


def run_evaluation() -> list[dict]:
    """Run deterministic known-answer checks and return a readable scorecard."""
    scenario = Scenario()
    baseline = scenario.evaluate()
    workspace = assessment_workspace(baseline, scenario.baseline_tables(), "C-184")
    evidence_ids = {row["source_id"] for row in workspace["evidence"]}
    checks = [
        _check("Citation coverage", EXPECTED_CITATIONS.issubset(evidence_ids),
               f"expected {sorted(EXPECTED_CITATIONS)}; found {len(evidence_ids)} source IDs"),
        _check("Unsupported claims", all(row.get("source_id") for row in workspace["evidence"]),
               "every displayed evidence row has a source ID"),
        _check("Known gap recall", any(item["question"] == "Hospital backup-power readiness" for item in workspace["unknowns"]),
               "hospital backup readiness remains an explicit unknown"),
        _check("Freshness behavior", not workspace["evidence_quality"]["ready_for_decision"],
               "stale readiness evidence blocks decision readiness"),
        _check("Baseline safety gate", not any(item["severity"] == "CRITICAL" for item in baseline["incidents"]),
               "baseline has no critical incident"),
    ]
    for _ in range(3):
        scenario.advance()
    stage4 = scenario.evaluate()
    c184_stage4 = stage4["findings"]["C-184"]
    checks.append(_check("Weather-only behavior", not c184_stage4["grid"]["anomaly_asset_ids"],
                         "C-184 has no electrical anomaly before the final stage"))
    final = scenario.advance()
    impact = final["findings"]["C-184"]["impact"]["impact"]
    checks.append(_check("Impact join", impact["customers_at_risk"] == 8420 and len(impact["critical_facilities"]) == 1,
                         "C-184 impact is 8,420 accounts and one facility"))
    revised = assessment_workspace(final, scenario.snapshot(), "C-184", field_report=True, version=2)
    checks.append(_check("Revision quality", "visible equipment damage" in revised["revision"]["what_changed"].lower()
                         and any(item["question"] == "Hospital backup-power readiness" for item in revised["unknowns"]),
                         "FR-001 changes the assessment while preserving the hospital gap"))
    return checks


def evaluation_summary() -> dict:
    checks = run_evaluation()
    return {"checks": checks, "passed": sum(item["passed"] for item in checks),
            "total": len(checks), "all_passed": all(item["passed"] for item in checks)}


def main() -> None:
    summary = evaluation_summary()
    print(f"GridGuard offline evaluation: {summary['passed']}/{summary['total']} checks passed")
    for item in summary["checks"]:
        marker = "PASS" if item["passed"] else "FAIL"
        print(f"[{marker}] {item['check']}: {item['detail']}")


if __name__ == "__main__":
    main()
