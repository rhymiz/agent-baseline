# Agent Baseline development

The CLI implementation is in `src/agent_baseline`: records owns typed evidence, execution owns processes, skills owns installation, and doctor owns structural guidance checks. The skill in `skills/baseline-project` owns the semantic authoring workflow; the CLI owns inventory, evidence hashes, input validation, and declared command execution. Keep the CLI independent of model APIs.

Version 1 and 2 project records are defined in `skills/baseline-project/references/project-record.md`. Parse unknown JSON into the immutable `Source`, `Artifact`, `Check`, and `Baseline` types before domain operations. Update that reference and integration tests when the record contract changes.

`check` never executes project commands. `record` never certifies correctness. `verify` must reject stale evidence before running commands and cannot report success when monitored inputs change during execution. Preserve distinct failed, timed-out, and blocked command results. Arguments are passed directly to subprocesses; never reinterpret them through a shell.

Install the working package with `python3 -m pip install -e .` first. Run `python3 -m unittest discover -s tests -v` from the package root. Fixtures use temporary directories and real subprocesses. Python 3.11+ is required; Git is optional for inventory. Process-group verification is supported on macOS/Linux.

CI in `.github/workflows/check.yml` installs the CLI and runs `agent-baseline verify .` on Python 3.11 and 3.14, on Linux and macOS. It validates the recorded evidence without automatically recording a new baseline.

The PyPI package and executable are both named `agent-baseline`. `.github/workflows/publish.yml` publishes only on GitHub releases whose tag matches the package version. Keep builds and verification in the unprivileged build job; the separate `pypi` environment job alone receives OIDC publishing permission.

Do not equate hash freshness with semantic correctness or test success with model parity. Skill discovery and model performance require separate behavioral evaluation.

The wheel bundles the canonical skill folder as the `agent_baseline_guidance` resource package. `skill show` supplies all references explicitly; `skill install` copies persistent guidance only into an explicit host/scope. Managed upgrades require unchanged previous fingerprints; preserve local conflicts and restore the previous directory when replacement fails. `init` creates an unreviewed draft that cannot pass as configured evidence. Test the built distribution outside the checkout. Updating the CLI does not update installed skill copies. Keep the skill command pin aligned with the package version.

Use `uv run --no-project --with-editable . python -m unittest discover -s tests -v` when developing through uv, so subprocess tests load current source. Test built wheels separately with fresh environments; cached local non-editable installs may otherwise hide source changes.
