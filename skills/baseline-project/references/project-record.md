# Project evidence record

Create `.agent-baseline.json` in the selected project directory after inspecting it. Commit that record and `.agent-baseline.lock.json` with the guidance. Version 1 requires exactly the fields below and at least one artifact and check. It rejects missing files, outside-project paths, duplicate artifact paths/check names, and malformed values.

Illustrative example only: these paths and commands must be replaced with evidence from the actual repository.

```json
{
  "schema_version": 1,
  "artifacts": [
    {
      "path": "AGENTS.md",
      "sources": ["package.json", ".github/workflows/check.yml"]
    },
    {
      "path": "docs/contracts/editor.md",
      "sources": ["src/editor/state.ts", "tests/editor-persistence.test.ts"]
    }
  ],
  "checks": [
    {
      "name": "repository-checks",
      "argv": ["bun", "run", "check"],
      "cwd": ".",
      "timeout_seconds": 600
    }
  ]
}
```

`artifacts` are maintained instruction or contract files. `sources` are the inspected files supporting those artifacts. Multiple artifacts may share a source. All paths are relative to the selected project. In monorepos, checks can use a package working directory. In-project symlinks are resolved; links outside the selected project are rejected rather than silently tracked across ownership boundaries.

The check `argv` is an argument array, not a shell string. Environment setup belongs in the documented runtime or a maintained script. Commands inherit the caller's environment. The CLI invokes the executable directly, but declared commands can themselves execute arbitrary code. Use `verify` only in a trusted project, after inspecting the record. Do not put secrets in command arguments.

Commands, using `uvx agent-baseline@0.1.1` or the matching installed CLI:

- `inspect <project>`: inventory candidate paths; no project code runs.
- `record <project>`: validate the record and atomically store hashes of the config, artifacts, and sources. Run only after reviewing guidance. Does not execute checks.
- `check <project>`: validate and compare hashes. Missing config/lock/files is an error. Changed monitored files require review; changes may be harmless.
- `verify <project>`: require current evidence, run every declared command with its timeout, and check that monitored inputs did not change during execution. Reports each command separately. It does not repair failures.

Exit status: `0` means the requested operation succeeded, `1` means drift or verification did not pass, `2` means malformed/missing configuration or an execution prerequisite error. The JSON `status` distinguishes inventory, recorded, current, needs_review, passed, not_passed, and invalid. A command that cannot start is blocked; timeout and failure are distinct per-check statuses.

Outputs retain the final 8 KB of combined stdout/stderr for each check; full logs are not retained. Reports may contain project command output, so review before sharing. Verification timeouts terminate the command process group on macOS/Linux. Background services should be managed by the project's normal test harness, not detached from checks.

The evidence digest covers only monitored files. It does not attest the whole worktree, prove that a command tests the right properties, validate Markdown links, or establish semantic correctness. Keep acceptance policy in independently reviewed CI, and require review for changes to the record or checks. Never use a job that automatically runs `record` before `check` in CI: that would hide drift.
