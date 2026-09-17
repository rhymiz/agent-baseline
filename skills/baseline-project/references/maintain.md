# Set up or refresh guidance

The result is reviewed project guidance with supporting evidence and accurately reported verification. Keep effort proportional to the requested scope.

## Establish relevant evidence

For first-time setup, run `init <project>` and add `--agent codex` and/or `--agent claude` for the hosts requested. Initialization creates an unreviewed draft. For other hosts, supply the skill explicitly through `skill show` or direct file reading; do not guess host configuration. Link existing skills with `skill link <canonical-folder> --project <project> --agent <host>` to preserve one canonical copy.

Use `inspect <project>` to locate candidate evidence. For setup, establish the relevant runtime versions, declared commands, CI entrypoints, test prerequisites, agent configuration, and domain ownership. For refresh, inspect the differences in changed monitored sources and trace them to affected guidance. Broaden reading when those changes cross another contract or ownership boundary.

Resolve material contradictions before writing dependent rules. Do not invent commands, source paths, invariants, or measured improvements. Prefer stable contracts, schemas, command manifests, and representative tests to monitoring an entire source tree.

## Author and prune

Keep the root short: essential rules and routing with task-specific detail in references. Link to maintained examples instead of copying a code tour. Apply the [audit criteria](audit.md) to existing and proposed instructions within scope; use supported findings to keep, narrow, move, or remove rules. A setup or refresh request authorizes these relevant edits without a separate audit report unless one was requested.

Before adding an instruction, identify the decision it changes: a project-specific requirement, non-obvious constraint, or observed recurring failure. Preserve explicit owner policy. Prefer a canonical reference when maintained documentation already supplies the needed detail. An expected performance benefit is a hypothesis until evaluated; neither accuracy nor brevity alone establishes usefulness. This criterion needs no additional form or experiment for routine corrections.

For domain workflows, establish identity, lifecycle, ownership, valid states, boundary validation, failure semantics, and observable examples. Reuse concepts only when their invariants match. Keep internal types precise without widening; preserve validated domain information across boundaries. Do not hide contract errors with casts or unexplained nullable state. Keep test-only branches out of production. Apply the owner's explicit type, import, and public API policies within their stated scope, including module-scope imports or a ban on re-exports when required. Do not export this package's conventions as universal consumer requirements or weaken an explicit owner rule because another project differs.

Prefer repository-owned executable checks for mechanically decidable rules, and state their coverage limits. Architectural quality still needs a concrete rubric or owner review. Add a skill only for a recurring procedure needing more than a short routing rule. Make its description brief and distinguish applicable requests from nearby requests that should not trigger it. Keep discovery and execution evaluation separate; explicitly supply mandatory procedures at their task entrypoints.

## Output contract

For each important engineering rule introduced or reviewed in the requested scope, the maintained guidance must make these relationships clear:

- **Application and decision:** when the rule applies and the observable invariant or behavior to preserve.
- **Authority and example:** the inspected contract, source section, or explicit owner policy supporting the decision, with a maintained example when it clarifies application. Distinguish intended behavior from current implementation.
- **Compliance and gaps:** the relevant executable check and what its assertions establish, or a concrete review criterion naming the behavior or artifact to inspect. State missing coverage and unresolved evidence explicitly. A proposed check is not existing verification.

Use concise prose or links to canonical guidance; no fixed table, new skill, or separate report file is required. A source list and a passing suite alone do not establish these relationships. Inspect the relevant assertions before claiming coverage; an owner review requirement still needs an observable criterion. Keep temporary check results in the completion report rather than permanent rules.

For refresh, update or affirm the affected relationships and their supporting evidence. Preserve valid mappings elsewhere without duplicating them or expanding the review to unrelated rules. An unresolved relationship must be reported as a gap, not described as an established contract.

## Set up the learning workflow

During setup, use [outcomes.md](outcomes.md) to choose the project's evidence location, write its conditional routing instruction, and configure how an agent retrieves and updates a follow-up. Do this work for the consumer using inspected project conventions; do not leave templates for the user to fill in or ask them to design a process. The reference supplies defaults for projects without shared memory or tracking tools.

For a substantive guidance change intended to improve agent work, link the observed finding, changed guidance and revision, expected improvement, and next comparable-task criterion in that location. Create an initial pending case only when the inspected work supplies a real finding; otherwise leave the workflow ready without inventing an incident. On refresh, reuse the established location and update the affected case. Routine corrections do not need new cases.

Keep the workflow and case format separate from its changing observations. Include maintained routing and workflow guidance in the evidence record with their real supporting contracts. Keep transient case results out of normative instructions and out of monitored evidence unless they actually support an in-scope rule. A subsequent outcome assessment should not force unrelated guidance re-recording.

## Review, record, and verify

Read [project-record.md](project-record.md) before authoring `.agent-baseline.json`. Each artifact needs real supporting sources distinct from itself. Declare exact check arguments and working directories. Prefer named Markdown sections or JSON pointers when they capture the supporting contract without excluding contradictory evidence.

Use `doctor` for links and metadata, adding host flags for requested native routes. Resolve findings against the actual linked source; preserve meaning when fixing structural errors. Keep host adapters minimal; standard skill content is portable but host invocation and plugin formats differ. Distinguish files installed, metadata exposed, instruction bodies loaded, and behavior observed. For a requested loading check, inspect the effective context or trace in a fresh supported host session; report unavailable evidence instead of inferring loading from valid files. Maintenance alone does not require a new model trial.

Inspect check behavior and prerequisites. Setup or refresh authorizes the relevant non-destructive development checks; retain any explicit execution limits from the user or environment. Exclude deployment, production mutation, publishing, and credential-bearing commands from the check list.

Review the resulting guidance against the output contract before recording. Trace the in-scope decisions to their authority and compliance criteria; resolve unsupported claims or disclose the remaining gaps. Then run `record`, `check`, and `verify`. This ordering preserves the reviewed snapshot and rejects drift before commands run. `verify` executes every declared check; use its results instead of redundantly rerunning the same suite without a reason. Recording does not certify correctness or successful verification. Never automatically re-record to silence drift.

Report files changed, point to the maintained decisions and their compliance criteria, and state actual verification results and remaining gaps. For setup, name the configured evidence location, retrieval/update route, and any pending case with its next trigger. State which sources and assertions were inspected and which remain unavailable or out of scope. Distinguish executed checks from review judgments, proposed checks, and outcomes that still await comparable work. Report an empty project-check list as guidance-only verification. Retain blocked, failed, and timed-out results, complete independent work, and never substitute a passing no-op. Distinguish mechanical validation, semantic review, and measured model performance.
