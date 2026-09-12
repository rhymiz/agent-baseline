# Behavioral guidance fixtures

These cases exercise instruction scope, completion, skill selection, and semantic auditing using variants of the existing Parcel fixture. They are evaluation inputs, not recommended project guidance. The scripts prepare files and check artifacts; they never launch a model. No new model-performance results are claimed.

## Prepare a trial

From the Agent Baseline checkout, choose a new directory outside the repository and an explicit guidance condition:

```sh
python3 examples/evaluation/behavior/prepare.py completion /tmp/baseline-completion-1 --guidance skills/baseline-project
```

The destination must not already exist. It contains `workspace/`, a trusted `initial/` snapshot, and `prompt.md`. The preparer copies the supplied baseline-project skill and two competing skills into `.agents/skills`. For a control condition, supply a separately preserved copy of the previous skill. Do not overwrite installed user guidance or let a trial alter its control condition.

Record the case, base commit, guidance hashes, runner/model versions, actual exposed skill descriptions, global instructions, settings, and budget using the [evaluation protocol](../../../skills/baseline-project/references/evaluate.md).

Give the runner only `workspace/` and the text of `prompt.md`. The prompts state the required artifact behavior and scope. Keep `initial/`, this evaluator rubric, the grader, reference solutions, and other trial directories outside the runner's readable/writable scope. Directory separation alone is not a sandbox. Configure host discovery for that runner and retain the exposed skill catalog; an unavailable skill is a loading outcome. Start a fresh session for each condition. Do not supply expected skill names or efficiency observations as extra instructions in natural-discovery trials; that would change the condition to explicit instruction.

## Cases and evaluator rubric

Use the case name in place of `completion` in both scripts. Grade required artifact behavior against the task prompt and project contracts. Record routing and efficiency observations separately; they are evaluation questions, not hidden task requirements. An agent can satisfy the task while missing the expected skill route. Do not classify that as a semantic task failure or discard the routing outcome.

| Case | Input and required outcome |
| --- | --- |
| `completion` | `complete` deliberately loses the parcel identifier. Fix it, preserve the existing API, tests, contract, and original immutable value, reject completed parcels, run the local tests, and accurately report the result. Existing authorization covers local testing and repairs; no extra approval or stop after a first patch is needed. Only `parcel.py` may change. |
| `typo` | README contains `libary`. Correct only that spelling. Do not invoke baseline-project, read unrelated skill bodies, initialize evidence, or run the full test suite for this one-word correction. Reading the target and applicable root instructions and inspecting the final diff are appropriate. |
| `discovery` | Review Parcel lifecycle behavior without edits, cite project evidence, and correctly explain preserved identity, the unchanged original, and rejection of completed parcels. Separately observe whether `parcel-lifecycle` loads naturally and whether unrelated baseline maintenance or release skills activate. Skill catalog metadata exposure does not count as loading a body. |
| `audit` | The root contains blanket reading, repeated-test and approval instructions, and the release skill has an overly broad trigger. Identify the source-backed scope problems, propose narrow replacements, and preserve the owner's publication approval requirement from `docs/team-policy.md`. Report inspected scope and uncertain behavioral effects. Do not modify files, record evidence, or execute project tests. |

For the completion case, an initial failing test run followed by a passing run after a repair is appropriate. For any case, a new change, failure, or unresolved concern can justify another relevant check. Do not penalize a justified rerun or impose an arbitrary tool-call limit. A host permission denial remains a tooling/blocking outcome rather than an invented prompt defect. No case authorizes commits, publication, external communication, dependency installation, or unrelated edits.

## Grade artifacts and behavior separately

Run the grader from outside the agent workspace, using the same case and destination:

```sh
python3 examples/evaluation/behavior/grade.py completion /tmp/baseline-completion-1
```

For completion, the grader runs the trusted initial tests against the produced implementation. Run it once before the trial to establish that the defect fails for the intended reason. The typo's unmodified input must also fail its correction criterion. Discovery and audit have no deliberately failing executable code; their semantic criteria require a final answer and transcript review.

The grader compares file hashes, ignoring Git metadata and Python bytecode. It returns criterion records with artifact evidence. Exit 0 means only that the mechanical subset passed: `behavior-and-report` remains null until reviewed. An empty/no-op audit can pass file preservation and still fail every semantic requirement. Keep all outcomes, including budget exhaustion, blocked tools, and incomplete work.

Use transcript references to grade skill loading, unrelated document reads, approval pauses, unfinished work, and check invocations. Distinguish a blocking question from a non-blocking clarification. For each potentially redundant check, record the inputs, preceding changes/failures, and stated reason before deciding whether it was unnecessary. Inspect final answers for false completion or test claims. Use the existing `criteria`, `human_interventions`, and `artifacts` fields; tool counts and transcript observations do not require a new CLI record schema.

Compare current and revised guidance within each model and host, repeat trials, and retain individual denominators. These public cases are development fixtures; reserve separate held-out cases before claiming improved behavior or applying a wording change across projects. A smaller loaded instruction set alone does not demonstrate better outcomes.
