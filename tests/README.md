# Verification

No application tests exist yet. Add focused standard-library `unittest` tests as the corresponding domain behavior is implemented.

Prioritize relationship correctness, risk boundaries, main-incident timing, and human-decision state transitions. See [the verification plan](../docs/IMPLEMENTATION_PLAN.md#7-verification-plan).

Once test files exist, run `python -m unittest discover -s tests -v` from the project root. Verify the Streamlit walkthrough separately.
