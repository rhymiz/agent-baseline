# Agent Baseline

A local tool for maintaining evidence-backed project instructions. Version 0.1.0 combines a reusable authoring skill, a standard-library Python CLI, and a Codex plugin manifest. It needs no model API key or service. The skill runs inside the coding agent you already use.

## Run with uvx or install once

Requires Python 3.11+; Git for inventory; macOS or Linux for running checks. Run the CLI from PyPI without a permanent installation:

```sh
uvx agent-baseline --help
uvx agent-baseline inspect .
uvx agent-baseline check .
uvx agent-baseline verify .
```

For a persistent installation:

```sh
uv tool install agent-baseline
```

Pin a version for reproducible automation, for example `uvx agent-baseline@0.1.0 check .`. These commands operate on the current project; `check` and `verify` require its configured baseline. Verification runs in the caller's environment, so declared commands must select the project's runtime explicitly where needed (for example, `uv run pytest`).

To develop the tool or obtain the agent skill, clone the public repository:

```sh
gh repo clone rhymiz/agent-baseline
cd agent-baseline
uv tool install .
```

If you already have a checkout, run `uv tool install .` from its root. The GitHub repository is the maintained source; project-specific guidance and baseline records belong in each project repository.

Or run directly without installation:

```sh
python3 skills/baseline-project/scripts/baseline.py inspect /absolute/project/path
```

The installed command works from any project:

```sh
agent-baseline inspect .
agent-baseline check .
agent-baseline verify .
```

The CLI installation does not register a skill or plugin with an agent.

This package is also a configured example project: from its root, run `agent-baseline check .` and `agent-baseline verify .`. Its declared check executes the integration suite against the tool itself. Inspect its `AGENTS.md` and `.agent-baseline.json` to see a populated record.

## Set up a project with an agent

Give your agent the absolute path to `skills/baseline-project/SKILL.md` and this request:

> Use this skill to set up an agent baseline for the current project. Ground every rule in inspected code, contracts, or commands. Preserve existing instructions and unrelated edits. Create the project evidence record, run the relevant development checks, and report anything unverified.

The skill writes or improves a small root instruction file, relevant task routing and domain guidance, and `.agent-baseline.json`. It records the reviewed hashes in `.agent-baseline.lock.json`. These project files belong in version control. The helper does not generate guidance from filenames; the agent inspects the actual evidence first.

For global discovery, copy the entire `skills/baseline-project` folder into a user skill directory supported by your host, preserving scripts and references. Codex and Claude Code also support linked skill folders. Alternatively, install the supplied Codex plugin through a configured local marketplace. The plugin is packaged here but is not registered or installed globally.

| Host | User skill destination |
| --- | --- |
| Codex | `~/.agents/skills/baseline-project/` |
| Claude Code | `~/.claude/skills/baseline-project/` |

Preserve an existing destination if one is already present; review and update it rather than overwriting blindly. After the host discovers the skill, invoke it by name: `$baseline-project` in Codex CLI/IDE or `/baseline-project` in Claude Code. In other surfaces, select it through the skill picker. Other agents can read the same `SKILL.md` by absolute path and use the CLI without the Codex manifest.

Codex skill authoring/discovery: [official docs](https://learn.chatgpt.com/docs/build-skills). Claude Code skill loading: [official docs](https://code.claude.com/docs/en/skills). Codex local plugin packaging: [official docs](https://developers.openai.com/plugins/build/plugins).

## Ongoing use

Ask the agent to audit guidance for a read-only report, or refresh guidance after the tool reports drift. Examples:

> Use baseline-project to audit this project's agent guidance. Report concrete contradictions, weak triggers, stale references, and verification gaps.

> Use baseline-project to review the changed evidence, update only affected guidance, and verify the refreshed baseline.

The skill offers a model-evaluation protocol when requested. Automated model trials, aggregate scoring, and model-specific routing are not implemented in this release.

## CLI behavior

| Command | Behavior |
| --- | --- |
| `inspect [project]` | Finds candidate instructions, manifests, CI files, and contracts. Reads filenames; does not execute project commands. |
| `record [project]` | Snapshots the config, guidance, and supporting files after review. Does not certify quality. |
| `check [project]` | Detects drift in the monitored files. No project commands execute. |
| `verify [project]` | Runs every explicitly declared project check and reports pass/failure/timeout/blocked status. |

All commands emit JSON. Exit codes are 0 for operation success, 1 for drift or failed verification, and 2 for invalid input/configuration or prerequisite errors. Run `--help` for invocation syntax. See [the record specification](https://github.com/rhymiz/agent-baseline/blob/main/skills/baseline-project/references/project-record.md) for configuration and limitations.

Use `record` only after semantic review. Never run it automatically in a CI validation job before `check`. A hash change means guidance needs review, not necessarily rewriting. A matching hash means files are unchanged, not that their claims are correct.

In CI, use a pinned copy/version of the CLI, run `check`, then the project's required verification. Independently review changes to verification policy. The tool tracks selected evidence files, not the full patch, and does not establish architecture quality or model parity.

## Development verification

```sh
python3 -m unittest discover -s tests -v
```

Tests use temporary project fixtures and real child commands. They cover evidence drift, missing and malformed inputs, path escape rejection, command failures/timeouts, working directories, and mutation during verification.

## Publishing

Publishing a GitHub release with a tag matching `v<project.version>` triggers `.github/workflows/publish.yml`. The workflow verifies the evidence and tests, builds and checks distributions, tests the wheel outside the checkout, and publishes through the `pypi` environment using PyPI Trusted Publishing. No PyPI API token is stored in the repository.

The PyPI publisher is scoped to project `agent-baseline`, GitHub owner `rhymiz`, repository `agent-baseline`, workflow `publish.yml`, and environment `pypi`. PyPI distributions contain the CLI; the authoring skill remains available in the GitHub repository and Codex plugin.
