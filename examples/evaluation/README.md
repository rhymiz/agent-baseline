# Reproduce a guidance-authoring trial

`parcel-library` is an intentionally flawed documentation fixture, not the recommended output. Its README contradicts the normative lifecycle contract. The code and tests already implement the contract correctly.

Copy the folder into a fresh trial workspace. Run `agent-baseline init <trial> --agent <your-host>` using the release under evaluation, then start a fresh agent session with baseline-project explicitly supplied and this prompt:

> Use baseline-project to finish first-time agent-baseline setup for this small Python project. Preserve the existing instruction and all library/test behavior. Inspect the normative contract, actual code, tests, and Makefile; resolve contradictory setup or usage advice in the README. Author only the guidance this project needs. Make important engineering rules traceable to when they apply, the behavior to preserve, supporting authority, and a relevant check or concrete review criterion. Identify missing coverage without modifying tests. Configure real evidence and the actual verification command, then record after review and verify. Set up a usable outcome log and routing for later work, retaining a pending follow-up for an observed guidance problem without inventing improvement evidence. Do not install dependencies, commit, publish, or add a service during this setup. Report source-backed decisions, actual tests, and limitations.

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
- Setup supplies a working outcome procedure and conditional routing without asking the consumer to write it. This fixture has no external store, so a local Markdown log is sufficient. A pending case links the contradictory README advice to its correction and a concrete next-task criterion; source/tests remaining green is not graded as subsequent workflow improvement. Record only the sources and tasks actually inspected.

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

## Test authored guidance in a fresh consumer

This is a public development exercise for the two-stage protocol, not a held-out
performance benchmark. First complete and independently grade the authoring trial
above. Freeze its generated guidance, supporting references, installed skill copy,
and hashes outside the consumer's writable workspace. Keep its transcript private
to the evaluator. Record which authoring trial produced each consumer baseline.

Create a fresh copy of the authored project for each consumer condition. Preserve
the generated guidance rather than using the behavioral preparer, which replaces
AGENTS.md. In each copy, introduce the same controlled defect in `parcel.py`:
replace `return Parcel(parcel.identifier, State.COMPLETED)` with
`return Parcel("lost", State.COMPLETED)`. Require exactly one matching occurrence
before replacement; stop if the fixture has changed. Retain the original tests in
an evaluator-owned location outside the consumer's access. Run those tests against
the defective copy first to confirm the intended failure.

Give each fresh consumer session only its workspace and this task:

> Fix `complete` so a queued Parcel returns a new completed Parcel with the same
> identifier, leaving every field of the original unchanged. Completed Parcels
> must still raise ValueError. Preserve the public API, contract, tests, and all
> guidance; only `parcel.py` may change. Run the local tests and report their actual
> results. Do not install packages, commit, publish, or re-record baseline evidence.
> The fixture deliberately changed a monitored source after authoring; if baseline
> freshness is checked, report that drift rather than hiding it.

The evaluator checks that only `parcel.py` changed, runs the trusted original tests
against it, and separately runs this preservation probe with the consumer root on
the import path. Keep the probe outside the consumer's accessible workspace:

```python
from parcel import Parcel, State, complete

for identifier in ("sample", "", "parcel-2"):
    original = Parcel(identifier, State.QUEUED)
    before = (original.identifier, original.state)
    result = complete(original)
    assert result == Parcel(identifier, State.COMPLETED)
    assert result is not original
    assert (original.identifier, original.state) == before

try:
    complete(Parcel("done", State.COMPLETED))
except ValueError:
    pass
else:
    raise AssertionError("Completed parcel was accepted")
```

Calibrate the probe against the unchanged correct fixture and both a lost-identifier
defect and an implementation that mutates the original identifier through
`object.__setattr__`. The latter can pass the original tests; the probe must reject
it. This verifies the grader's specific assertions, not model performance or every
possible implementation defect. Review the final report independently for accurate
test claims and any unresolved drift.

For authoring-method comparisons, produce separate baselines from the same initial
fixture using current and proposed authoring guidance. For the minimal consumer
condition, retain the original owner instruction, explicit task requirements, and
essential test command; keep the raw contract and source accessible. Record exactly
which optional generated guidance was removed, including host imports or aliases
that would otherwise leak it. Match consumer code, prompt, environment, and budget
across conditions. Do not call a trial natural discovery if the task explicitly
names a skill. Retain both authoring and consumer results even when one fails.

Before broader claims, add independent repositories and held-out consumer tasks,
including a nearby documentation correction that should not invoke maintenance.
Repeat both stages, counterbalance conditions, and keep results from a shared
authored baseline grouped. A passing public example establishes bounded behavior,
not a causal improvement in the authoring method.

## Outcome follow-up variants

Use isolated copies and give the implementing agent each variant's visible task and raw evidence. These extend the setup exercise; they do not require a model runner for fixture preparation.

| Variant and visible task | Evidence and grading criterion |
| --- | --- |
| Complete baseline setup using the existing project log | Before the trial, add `docs/engineering-outcomes.md` with an unrelated historical entry and route to it from AGENTS.md. The agent preserves that entry and configures the existing location; it does not create a second log or require a service. |
| Assess the README correction after setup, with no subsequent engineering task | Supply only the setup artifact and its test result. The follow-up remains pending; the agent identifies the missing comparable-task evidence rather than claiming improvement from a passing suite. |
| Assess the correction against a later usage example | Supply a dated example that still calls `complete` twice on the returned completed Parcel. Read the Completion contract and execute the example independently if permitted. An assessment that the original misuse persists is supported; a claimed improvement is not. Preserve the case and contrary evidence. |
| Review outcome evidence from a bounded export | Supply one existing case plus an explicitly truncated search result with no later task. The report states the inspected subset and missing evidence. It cannot establish that all follow-ups are resolved or every source was checked. |

Grade the generated route by following its actual path to the procedure and store. Grade a case by tracing its finding, revision, criterion, and evidence. Preserve fixture source bytes and read the final claims; neither headings nor the presence of the word `pending` earns semantic credit on its own.
