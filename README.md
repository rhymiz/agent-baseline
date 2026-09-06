# Agent Baseline

Portable tooling for evidence-backed coding-agent guidance. It helps an agent set up project instructions, detect stale supporting evidence, validate guidance structure, and run declared checks. It works with your existing coding agent and has no model API or service dependency.

Guidance improves the agent's working environment. Host discovery is best effort; the target is better decisions when the agent reads the guidance. The tool does not control agent harnesses, make models equally capable, or prove architecture quality through file hashes.

## Start in any project

Requires uv and Python 3.11+. Project commands run on macOS/Linux; Git is optional for inventory. The package supplies its own Markdown and YAML parsers, so setup does not require Node, Bun, or another project's runtime.

```sh
uvx agent-baseline@0.2.0 init . --agent codex --agent claude
```

Choose the hosts you use; omit both flags for the explicit CLI workflow. Initialization installs the skill and creates an empty evidence-record draft. It preserves existing project instructions and does not invent domain rules, sources, or test commands.

Then start a new agent session and ask:

> Use baseline-project to set up this project's agent baseline. Preserve existing guidance, ground instructions in inspected contracts and code, configure the evidence record, and run the relevant verification.

Invoke `$baseline-project` in Codex or `/baseline-project` in Claude Code, or select it in the host's skill picker. If the host does not discover local skills, ask it to run and follow:

```sh
uvx agent-baseline@0.2.0 skill show
```

That command prints the complete skill and references. Running `uvx` alone does not load instructions into the agent.

## Daily use

```sh
uvx agent-baseline@0.2.0 doctor .
uvx agent-baseline@0.2.0 check .
uvx agent-baseline@0.2.0 verify .
```

`doctor` checks local Markdown links, referenced guidance, skill YAML, and selected host routes. Add `--agent codex --agent claude` for native project discovery requirements. It understands Markdown references and code examples instead of searching prose with a link regex.

`check` detects changed evidence and names the guidance that depends on it. `verify` requires current evidence, runs built-in guidance validation and declared project commands, and checks that monitored inputs stayed unchanged. These commands do not replace task-specific engineering review, UI checks, or required application CI.

On drift, ask the agent to inspect the changed evidence and update or affirm the affected guidance. After that review:

```sh
uvx agent-baseline@0.2.0 record .
uvx agent-baseline@0.2.0 verify .
```

Never automatically re-record to clear a failure. An empty draft cannot pass as a reviewed baseline. If there are no project checks, version 2 records allow an empty check list and verification reports that limitation explicitly.

## Track the relevant evidence

The same configuration works across languages and repository layouts:

```json
{
  "schema_version": 2,
  "artifacts": [
    {
      "path": "AGENTS.md",
      "sources": [
        {"path": "package.json", "json_pointer": "/scripts"},
        {"path": "docs/architecture.md", "heading": "Ownership"},
        "tests/domain.test.ts"
      ]
    }
  ],
  "checks": [
    {"name": "tests", "argv": ["npm", "test"], "cwd": ".", "timeout_seconds": 600}
  ]
}
```

Replace these illustrative sources and commands with inspected project evidence. Track a whole file, one JSON value, or one named Markdown section. Selectors reduce irrelevant drift; missing or ambiguous selections fail. Version 1 records remain readable.

The [record specification](skills/baseline-project/references/project-record.md) describes validation, exit codes, compatibility, execution boundaries, and verification limits. `--help` and `--version` describe the installed CLI.

## Keep guidance canonical

Initialization installs the baseline skill in `.agents/skills` and creates aliases for the selected hosts. Link an existing project skill without copying it:

```sh
uvx agent-baseline@0.2.0 skill link tooling/skills/team-engineering --agent codex --agent claude
```

The linker validates the resulting relative links and preserves existing destinations. A skill whose references depend on its original nesting may need its links corrected before it can be shared at another location.

For a user-level installation across your local projects:

```sh
uvx agent-baseline@0.2.0 skill install --agent codex --scope user
```

Use `--agent claude` for Claude Code. Project discovery uses `.agents/skills` for Codex and `.claude/skills` for Claude Code. User discovery uses those directories under the user's home. The repository also includes a Codex plugin manifest; CLI installation does not register that plugin with a marketplace.

Installed files are persistent copies outside uv's cache. To upgrade a managed installation:

```sh
uvx agent-baseline@0.2.0 skill install --agent codex --scope user --upgrade
```

Installation receipts identify the previous managed files. Upgrades preserve local edits and extra files by refusing conflicting replacements. They roll back a failed directory replacement. Older installations without receipts require a one-time comparison and manual move-aside before replacement; the tool does not assume those files are unmodified. Update the canonical directory when other hosts use aliases.

Host routing is based on [Codex's local skills documentation](https://learn.chatgpt.com/docs/build-skills), [Claude Code's skills documentation](https://code.claude.com/docs/en/skills), and the [Agent Skills specification](https://agentskills.io/specification). File placement and host loading are separate checks; native policies can disable discovery.

## Evaluate actual agent results

Use the [evaluation protocol](skills/baseline-project/references/evaluate.md) to compare natural discovery and explicit skill invocation against observable acceptance criteria. Keep model/host versions, environment, inputs, and budgets recorded. Judge output artifacts independently; neither the agent's self-assessment nor a green structural check measures model parity.

The [reproducible authoring exercise](examples/evaluation/README.md) includes a small Python project, an intentional documentation contradiction, a task prompt, and artifact-level grading criteria. Copy it into an isolated workspace to try your own agent.

The [0.2.0 evaluation report](docs/evaluation-0.2.0.md) records actual New Faces and authoring trials, including failed policy-authoring criteria and successful repeats. It is development evidence, not a model-parity benchmark.

The package does not launch model APIs or claim performance scores. Evaluation runners are selected by the user. The New Faces integration is a testing ground; no New Faces paths, domain rules, or language commands belong in the package implementation.

## Develop and publish

```sh
python3 -m pip install -e .
python3 -m unittest discover -s tests -v
```

The implementation is in `src/agent_baseline`; canonical skill content is in `skills/baseline-project`. Runtime dependencies are `markdown-it-py` and `PyYAML` for their supported syntax and safe parsers. `uv tool install agent-baseline` is available for a persistent CLI installation.

GitHub releases matching `v<project.version>` trigger the build and isolated PyPI Trusted Publishing workflow. Tests, distribution metadata, wheel execution outside the checkout, and bundled guidance are checked before publication. No PyPI API token is stored in the repository.
