# Agent Baseline

A local tool for maintaining evidence-backed project instructions. Version 0.1.1 combines a reusable authoring skill, a standard-library Python CLI, and a Codex plugin manifest. It needs no model API key or service. The skill runs inside the coding agent you already use.

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

Pin a version for reproducible automation, for example `uvx agent-baseline@0.1.1 check .`. These commands operate on the current project; `check` and `verify` require its configured baseline. Verification runs in the caller's environment, so declared commands must select the project's runtime explicitly where needed (for example, `uv run pytest`).

## Make the guidance available to your agent

`uvx` runs the executable in an isolated environment. It does not register skills with your agent. The PyPI package includes the complete guidance; choose one of these entrypoints.

**Install once for all your local projects:**

```sh
uvx agent-baseline@0.1.1 skill install --agent codex --scope user
# Or for Claude Code:
uvx agent-baseline@0.1.1 skill install --agent claude --scope user
```

**Share it with a project team:** run from the project root and commit the resulting skill directory.

```sh
uvx agent-baseline@0.1.1 skill install --agent codex --scope project
# Use --agent claude for Claude Code, or --project /absolute/path for another project.
```

| Host | User directory | Project directory |
| --- | --- | --- |
| Codex | `~/.agents/skills/baseline-project/` | `.agents/skills/baseline-project/` |
| Claude Code | `~/.claude/skills/baseline-project/` | `.claude/skills/baseline-project/` |

The installer copies `SKILL.md` and all references into persistent files, independent of uv's cache. Repeating the same installation is harmless. If any existing file differs, it refuses to overwrite the directory: review it and move it aside before installing an update. Updating the CLI alone does not update installed skill copies. The skill pins its CLI version to keep their contracts aligned.

Start a new agent session and explicitly invoke `$baseline-project` in Codex or `/baseline-project` in Claude Code (or select it in the host's skill picker). Confirm it appears in that host before relying on discovery. Installation makes the skill available; it does not guarantee automatic selection or compliance. User-scoped files are local to that machine; remote sessions need the committed project skill or their own installation.

**Without native skill support or persistent installation:** tell the agent:

> Run `uvx agent-baseline@0.1.1 skill show`, read the complete output including its references, and use that guidance to set up this project's agent baseline.

`skill show` prints all guidance as Markdown with file headings. It does not modify files. This is also an explicit bootstrap for agents that can run commands but cannot discover installed skills.

This package is also a configured example project: from its root, run `agent-baseline check .` and `agent-baseline verify .`. Its declared check executes the integration suite against the tool itself. Inspect its `AGENTS.md` and `.agent-baseline.json` to see a populated record.

## Set up a project with an agent

After installing the skill or supplying `skill show` output, ask:

> Use baseline-project to set up an agent baseline for the current project. Ground every rule in inspected code, contracts, or commands. Preserve existing instructions and unrelated edits. Create the project evidence record, run the relevant development checks, and report anything unverified.

The skill writes or improves a small root instruction file, relevant task routing and domain guidance, and `.agent-baseline.json`. It records the reviewed hashes in `.agent-baseline.lock.json`. These project files belong in version control. The helper does not generate guidance from filenames; the agent inspects the actual evidence first.

The GitHub repository also includes a Codex plugin manifest for hosts using a configured plugin marketplace. CLI installation does not register that plugin.

Codex skill authoring/discovery: [official docs](https://learn.chatgpt.com/docs/build-skills). Claude Code skill loading: [official docs](https://code.claude.com/docs/en/skills). Codex local plugin packaging: [official docs](https://developers.openai.com/plugins/build/plugins).

## Ongoing use

Ask the agent to audit guidance for a read-only report, or refresh guidance after the tool reports drift. Examples:

> Use baseline-project to audit this project's agent guidance. Report concrete contradictions, weak triggers, stale references, and verification gaps.

> Use baseline-project to review the changed evidence, update only affected guidance, and verify the refreshed baseline.

The skill offers a model-evaluation protocol when requested. Automated model trials, aggregate scoring, and model-specific routing are not implemented in this release.

## CLI behavior

| Command | Behavior |
| --- | --- |
| `skill show` | Prints the bundled skill and references as Markdown. |
| `skill install --agent codex\|claude --scope user\|project [--project PATH]` | Copies complete guidance for native discovery, preserving differing existing skills. |
| `inspect [project]` | Finds candidate instructions, manifests, CI files, and contracts. Reads filenames; does not execute project commands. |
| `record [project]` | Snapshots the config, guidance, and supporting files after review. Does not certify quality. |
| `check [project]` | Detects drift in the monitored files. No project commands execute. |
| `verify [project]` | Runs every explicitly declared project check and reports pass/failure/timeout/blocked status. |

Project commands and `skill install` emit JSON; successful `skill show` emits Markdown. Exit codes are 0 for operation success, 1 for drift or failed verification, and 2 for invalid input/configuration or prerequisite errors. Run `--help` for invocation syntax. See [the record specification](https://github.com/rhymiz/agent-baseline/blob/main/skills/baseline-project/references/project-record.md) for configuration and limitations.

Use `record` only after semantic review. Never run it automatically in a CI validation job before `check`. A hash change means guidance needs review, not necessarily rewriting. A matching hash means files are unchanged, not that their claims are correct.

In CI, use a pinned copy/version of the CLI, run `check`, then the project's required verification. Independently review changes to verification policy. The tool tracks selected evidence files, not the full patch, and does not establish architecture quality or model parity.

## Development verification

```sh
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

Tests use temporary project fixtures and real child commands. They cover evidence drift, missing and malformed inputs, path escape rejection, command failures/timeouts, working directories, and mutation during verification.

## Publishing

Publishing a GitHub release with a tag matching `v<project.version>` triggers `.github/workflows/publish.yml`. The workflow verifies the evidence and tests, builds and checks distributions, tests the wheel outside the checkout, and publishes through the `pypi` environment using PyPI Trusted Publishing. No PyPI API token is stored in the repository.

The PyPI publisher is scoped to project `agent-baseline`, GitHub owner `rhymiz`, repository `agent-baseline`, workflow `publish.yml`, and environment `pypi`. Both the wheel and source distribution contain the CLI, skill, and references. Release smoke tests read and install the guidance from the built wheel outside the checkout.
