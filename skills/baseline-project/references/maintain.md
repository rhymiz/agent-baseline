# Set up or refresh guidance

The result is reviewed project guidance with supporting evidence and accurately reported verification. Keep effort proportional to the requested scope.

## Establish relevant evidence

For first-time setup, run `init <project>` and add `--agent codex` and/or `--agent claude` for the hosts requested. Initialization creates an unreviewed draft. For other hosts, supply the skill explicitly through `skill show` or direct file reading; do not guess host configuration. Link existing skills with `skill link <canonical-folder> --project <project> --agent <host>` to preserve one canonical copy.

Use `inspect <project>` to locate candidate evidence. For setup, establish the relevant runtime versions, declared commands, CI entrypoints, test prerequisites, agent configuration, and domain ownership. For refresh, inspect the differences in changed monitored sources and trace them to affected guidance. Broaden reading when those changes cross another contract or ownership boundary.

Resolve material contradictions before writing dependent rules. Do not invent commands, source paths, invariants, or measured improvements. Prefer stable contracts, schemas, command manifests, and representative tests to monitoring an entire source tree.

## Author and prune

Keep the root short: essential rules and routing with task-specific detail in references. For ambiguous rules, state the triggering task, the decision, and evidence of compliance. Link to a maintained example instead of copying a code tour. Apply the [audit criteria](audit.md) to existing and proposed instructions within scope; use supported findings to keep, narrow, move, or remove rules. A setup or refresh request authorizes these relevant edits without a separate audit report unless one was requested.

For domain workflows, establish identity, lifecycle, ownership, valid states, boundary validation, failure semantics, and observable examples. Reuse concepts only when their invariants match. Keep internal types precise, imports at module scope, and test-only branches out of production. Do not use casts or unexplained nullable state to hide contract errors.

Prefer repository-owned executable checks for mechanically decidable rules, and state their coverage limits. Architectural quality still needs a concrete rubric or owner review. Add a skill only for a recurring procedure needing more than a short routing rule. Make its description brief and distinguish applicable requests from nearby requests that should not trigger it. Keep discovery and execution evaluation separate; explicitly supply mandatory procedures at their task entrypoints.

## Review, record, and verify

Read [project-record.md](project-record.md) before authoring `.agent-baseline.json`. Each artifact needs real supporting sources distinct from itself. Declare exact check arguments and working directories. Prefer named Markdown sections or JSON pointers when they capture the supporting contract without excluding contradictory evidence.

Use `doctor` for links and metadata, adding host flags for requested native routes. Resolve findings against the actual linked source; preserve meaning when fixing structural errors. Keep host adapters minimal and check loading behavior in supported installed versions; standard skill content is portable but host invocation and plugin formats differ.

Inspect check behavior and prerequisites. Setup or refresh authorizes the relevant non-destructive development checks; retain any explicit execution limits from the user or environment. Exclude deployment, production mutation, publishing, and credential-bearing commands from the check list.

After semantic review, run `record`, then `check`, then `verify`. This ordering preserves the reviewed snapshot and rejects drift before commands run. `verify` executes every declared check; use its results instead of redundantly rerunning the same suite without a reason. Recording does not certify correctness or successful verification. Never automatically re-record to silence drift. For refresh, update or affirm affected guidance with a concrete reason before recording.

Report files changed, source-backed decisions, actual verification results, and limitations. Report an empty project-check list as guidance-only verification. Retain blocked, failed, and timed-out results, complete independent work, and never substitute a passing no-op. Distinguish mechanical validation, semantic review, and measured model performance.
