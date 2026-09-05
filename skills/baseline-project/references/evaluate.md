# Evaluate guidance across models

This procedure needs an agent runner and a declared execution budget. The included CLI does not launch models or synthesize benchmark scores.

Choose historical tasks with observable acceptance criteria: an invented nullable state, unsafe boundary parsing, stale async responses, wrong test setup, or premature completion. Include nearby tasks that should not activate a specialized skill. Keep some cases held out.

For each case, record its base commit, task prompt, fixtures, setup, acceptance criteria, independent grader, and runtime prerequisites. Write requirements visible to the implementing agent; do not hide new requirements in the grader. Keep solution patches and holdout grading implementation outside the implementing agent's accessible workspace.

Compare the current configuration with proposed guidance using the same model/host versions, tools, environment, budget, and initial state. Repeat in fresh workspaces and conversations. Record reasoning settings and global instructions rather than assuming equally named settings behave identically.

Measure two skill conditions separately:

1. Natural request: did the right skill load, and did unrelated requests avoid it?
2. Explicitly supplied skill: did the workflow produce acceptable changes?

Track first-attempt success, success within a declared repair budget, consistency across trials, invariant violations, false completion claims, cost, time, and human intervention. Evaluate the actual artifacts with independent tests and a calibrated architecture rubric. An agent's self-assessment is not a score.

Classify failures as loading, missing knowledge, judgment, tooling, verification, or stopping. Fix the responsible layer. Do not keep adding universal instructions for unrelated incidents. Report per-model and per-task-family outcomes with uncertainty; a few successful trials do not prove equivalence.
