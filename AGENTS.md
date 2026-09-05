# Agent Baseline development

The CLI implementation is `skills/baseline-project/scripts/baseline.py`. The skill in the same folder owns the semantic authoring workflow; the CLI owns inventory, evidence hashes, input validation, and declared command execution. Keep the CLI independent of model APIs.

Version 1 project records are defined in `skills/baseline-project/references/project-record.md`. Parse unknown JSON into the immutable `Artifact`, `Check`, and `Baseline` types before domain operations. Update that reference and integration tests when the record contract changes.

`check` never executes project commands. `record` never certifies correctness. `verify` must reject stale evidence before running commands and cannot report success when monitored inputs change during execution. Preserve distinct failed, timed-out, and blocked command results. Arguments are passed directly to subprocesses; never reinterpret them through a shell.

Run `python3 -m unittest discover -s tests -v` from the package root. Fixtures use temporary directories and real subprocesses. Python 3.11+ and Git are required; process-group verification is supported on macOS/Linux.

CI in `.github/workflows/check.yml` installs the CLI and runs `agent-baseline verify .` on Python 3.11 and 3.14. It validates the recorded evidence without automatically recording a new baseline.

The PyPI package and executable are both named `agent-baseline`. `.github/workflows/publish.yml` publishes only on GitHub releases whose tag matches the package version. Keep builds and verification in the unprivileged build job; the separate `pypi` environment job alone receives OIDC publishing permission.

Do not equate hash freshness with semantic correctness or test success with model parity. Skill discovery and model performance require separate behavioral evaluation.
