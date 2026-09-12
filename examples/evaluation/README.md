# Reproduce a guidance-authoring trial

`parcel-library` is an intentionally flawed documentation fixture, not the recommended output. Its README contradicts the normative lifecycle contract. The code and tests already implement the contract correctly.

Copy the folder into a fresh trial workspace. Run `agent-baseline init <trial> --agent <your-host>` using the release under evaluation, then start a fresh agent session with baseline-project explicitly supplied and this prompt:

> Use baseline-project to finish first-time agent-baseline setup for this small Python project. Preserve the existing instruction and all library/test behavior. Inspect the normative contract, actual code, tests, and Makefile; resolve contradictory setup or usage advice in the README. Author only the guidance this project needs. Make important engineering rules traceable to when they apply, the behavior to preserve, supporting authority, and a relevant check or concrete review criterion. Identify missing coverage without modifying tests. Configure real evidence and the actual verification command, then record after review and verify. Do not install dependencies, commit, publish, or add a service during this setup. Report source-backed decisions, actual tests, and limitations.

Record the selected runner, exact version/model when available, settings, guidance hashes, and a budget before starting. The local release evaluation used fresh sessions, a 240-second cap, no repairs, and Claude's additional reported-cost cap of USD 3. These limits are examples, not recommended settings for every task.

Grade the resulting files independently against these visible criteria:

- The original instruction survives; library code, tests, contract, and Makefile are unchanged.
- README advice matches the normative contract and tests: completing a queued parcel returns a new completed value; a completed parcel cannot be reprocessed.
- Guidance identifies authority, ownership, immutable state, and relevant verification without inventing a permanent ban from a temporary task restriction or current implementation fact.
- Important rules connect their application and invariant to supporting authority and inspected test assertions or concrete review criteria. Uncovered behavior is disclosed; a proposed check is not reported as executed verification.
- The evidence record names existing, relevant sources and the actual `make check` command; it contains no passing no-op.
- `make check`, baseline `check`, and `verify` pass. Inspect the transcript to confirm review preceded `record`.
- No extra skill is created unless a recurring procedure justifies it; no unnecessary service, package installation, commit, or publication occurs.
- The final report accurately describes the work and the limits of verification.

Run the existing tests yourself; compare source bytes against the initial fixture; read the actual guidance and source mapping. Structural success alone cannot establish the semantic criteria. Use the [evaluation protocol](../../skills/baseline-project/references/evaluate.md) to retain all outcomes, including failures and inconclusive results. Do not treat one successful fixture as proof of model parity or effectiveness in every domain.

## Calibrate semantic grading

Keep this evaluator reference outside the implementing agent's workspace; provide the task prompt above and raw fixture files. Grade the meaning and evidence, not a required phrase or layout. The fixture already supports these checks without changing its code or tests:

| Decision | Supporting evidence and sufficient output |
| --- | --- |
| Completing a queued parcel preserves its identifier and the original state | Guidance connects changes to `complete` with the Completion and Ownership sections of [the contract](parcel-library/docs/contract.md) and `test_completion_preserves_identity_and_original` in [the tests](parcel-library/tests/test_parcel.py). The assertions establish the returned identifier/state and unchanged original state for the tested input. |
| A completed parcel cannot be reprocessed | Guidance connects that transition to the Completion contract and `test_completed_parcel_is_rejected`, which requires `ValueError`. |
| The caller's entire original value remains unchanged | The Ownership contract requires an immutable original value. The test asserts the original state, but never checks its identifier after completion. Guidance identifies that coverage limit and a concrete review criterion: inspect `complete` in [parcel.py](parcel-library/parcel.py) for construction of a new Parcel without mutating any input field, including through immutability bypasses. A proposed assertion comparing the original value after completion remains a proposal under the task's no-test-edit scope. |
| Lifecycle ownership stays in `parcel.py` | The Ownership contract establishes responsibility. Existing behavior tests do not enforce module ownership. A concrete review criterion checks whether lifecycle decisions remain in `parcel.py` and callers delegate to it; a passing suite alone does not establish this. |

"Preserve immutability; follow the contract; run make check" fails traceability even when the suite passes. Claiming that those tests establish module ownership or verify that every original field is unchanged fails coverage accuracy. An output that maps the first two rules to their assertions and supplies the last two review criteria with their testing limits meets these criteria. Reporting a limitation does not make an unperformed review or missing assertion pass. Grade each decision and the final claims separately, citing the generated guidance, source assertions, and transcript where applicable.

The [behavioral fixtures](behavior/README.md) add reproducible local-fix, typo, competing-skill, and read-only audit cases. Their preparer accepts an explicit guidance condition; artifact checks and transcript grading remain separate.
