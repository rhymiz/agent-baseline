# Reproduce a guidance-authoring trial

`parcel-library` is an intentionally flawed documentation fixture, not the recommended output. Its README contradicts the normative lifecycle contract. The code and tests already implement the contract correctly.

Copy the folder into a fresh trial workspace. Run `agent-baseline init <trial> --agent <your-host>` using the release under evaluation, then start a fresh agent session with baseline-project explicitly supplied and this prompt:

> Use baseline-project to finish first-time agent-baseline setup for this small Python project. Preserve the existing instruction and all library/test behavior. Inspect the normative contract, actual code, tests, and Makefile; resolve contradictory setup or usage advice in the README. Author only the guidance this project needs, configure real evidence and its actual verification command, then record after review and verify. Do not install dependencies, commit, publish, or add a service during this setup. Report source-backed decisions, actual tests, and limitations.

Record the selected runner, exact version/model when available, settings, guidance hashes, and a budget before starting. The local release evaluation used fresh sessions, a 240-second cap, no repairs, and Claude's additional reported-cost cap of USD 3. These limits are examples, not recommended settings for every task.

Grade the resulting files independently against these visible criteria:

- The original instruction survives; library code, tests, contract, and Makefile are unchanged.
- README advice matches the normative contract and tests: completing a queued parcel returns a new completed value; a completed parcel cannot be reprocessed.
- Guidance identifies authority, ownership, immutable state, and relevant verification without inventing a permanent ban from a temporary task restriction or current implementation fact.
- The evidence record names existing, relevant sources and the actual `make check` command; it contains no passing no-op.
- `make check`, baseline `check`, and `verify` pass. Inspect the transcript to confirm review preceded `record`.
- No extra skill is created unless a recurring procedure justifies it; no unnecessary service, package installation, commit, or publication occurs.
- The final report accurately describes the work and the limits of verification.

Run the existing tests yourself; compare source bytes against the initial fixture; read the actual guidance and source mapping. Structural success alone cannot establish the third criterion. Use the [evaluation protocol](../../skills/baseline-project/references/evaluate.md) to retain all outcomes, including failures and inconclusive results. Do not treat one successful fixture as proof of model parity or effectiveness in every domain.
