# Evaluation of the 0.2.0 candidate

The target is sound, source-backed work when an agent reads the guidance. Host discovery is best effort. This evaluation found real defects and informed two changes: explicit host inspection now includes installed skills outside the configured artifact list, and the authoring guidance distinguishes permanent policy from current facts and temporary task limits.

## Conditions

Trials ran on macOS in fresh, isolated filesystem snapshots using Codex CLI 0.153.4 and Claude Code 2.1.236. No model override was supplied. Claude's event stream reported `claude-opus-5`; the retained Codex CLI stream did not expose a model identifier, so its exact model is unavailable. Codex used ephemeral workspace-write sessions with user configuration omitted; Claude used project settings, no persistent session or external MCP configuration, and tools limited to the exercise. Global/default host context is a remaining confound.

Each trial had a 240-second cap and zero implementing-agent repair rounds. Claude also had a USD 3 reported-cost cap. No trial below exhausted either limit. These are runner-reported usage estimates, not billing statements. The user owns the runner and budget; Agent Baseline does not launch or control models.

The New Faces fixtures contain private project source and remain local. They copied tracked working files and current guidance, excluded environment-value files and dependencies, and used stubbed database commands. The live application was not modified by trial agents. The independent regression grader rejected the deliberately defective input before grading model output.

## Observed outcomes

| Exercise | Codex | Claude |
| --- | --- | --- |
| New Faces database-name guard regression, natural engineering request | Correct fix and focused tests; independent grader passed; read engineering skill and references | Correct fix and focused tests; independent grader passed; engineering skill was not loaded |
| New Faces renamed-evidence refresh, explicit baseline-project | Correct source updates, reviewed before recording, checks passed, renamed test content preserved | Same artifact outcome; narrative had minor test-count and staging inaccuracies |
| Python authoring fixture, initial skill | Correct README correction, evidence, checks, and policy scope | Mechanical checks passed, but authored an unsupported permanent dependency prohibition |
| Same authoring fixture, first policy clarification | Policy criterion passed | Still introduced an unsupported requirement to raise future dependency changes first |
| Same authoring fixture, final policy clarification | All listed artifact criteria passed | All listed artifact criteria passed; current dependencies described without an invented ban or approval boundary |

Both engineering trials changed only the resolver and its test file. Neither invoked baseline-project for ordinary implementation. Both refresh trials kept the renamed test byte-for-byte intact and passed all nine existing guard tests when independently re-run. Both final authoring trials preserved the library, tests, normative contract, Makefile, and existing instruction; corrected the README contradiction; configured the actual `make check`; and passed both existing tests plus baseline verification. Transcript review established that both read the supplied skill and reviewed evidence before recording.

The authoring output varied in length and wording. It did not need to be identical to satisfy the same contract. The final clarification says that only durable preferences or explicit normative decisions establish prohibitions or approval requirements, and that “not needed” does not mean “forbidden.” The final output in both hosts satisfied that distinction in this exercise.

## Reproduce and interpret

The [public authoring fixture](../examples/evaluation/README.md) includes the prompt, input project, and visible artifact rubric. The [evaluation protocol](../skills/baseline-project/references/evaluate.md) supplies a result-record shape and guidance for user-selected runners. Compare outputs against sources and test behavior, not an agent's self-score.

These are development trials, not a held-out benchmark or a statistically powered comparison. There was one trial per host per condition; wording changes were informed by the same fixture. The deterministic doctor also changed between authoring iterations. The observed final success does not isolate a causal improvement, establish consistency under repetition, prove equal model capability, or validate unrelated codebases. The reporting inaccuracies and failed policy criteria remain part of the evidence, rather than being discarded because later trials passed.

The separate deterministic suite covers 49 integration tests: versioned records, source selectors, real subprocess success/failure/timeouts, mutation during verification, safe installs/upgrades, canonical aliases, Markdown/YAML validation, and Python/Rust/Java/monorepo/documentation project shapes including paths with spaces. Language-shape fixtures test guidance tooling without requiring each language's compiler; they do not claim to validate those projects' application code. The built wheel passed the suite outside the source checkout.

## Grok CLI follow-up

At the user's request, the same exercises were also run with the installed official Grok Build CLI 1.0.13 (`5e9a58528b76`, stable), authenticated through its device flow. The native stream reported `grok-4.6` (usage key `grok-4.6-build`); no model override was supplied. `grok inspect --json` discovered baseline-project in the shared `.agents/skills` directory. The explicit tasks asked Grok to read that file, so no Grok-specific Agent Baseline adapter was necessary. Headless flags and filesystem boundaries were checked against the installed help and the official [CLI reference](https://docs.x.ai/build/cli/reference) and [sandbox documentation](https://docs.x.ai/build/features/sandbox).

| Completed exercise | Observed result | Elapsed seconds |
| --- | --- | ---: |
| New Faces guard regression | Read the engineering skill through the existing canonical alias; changed only resolver and test; independent guard grader passed and all 10 resulting script tests passed | 53.1 |
| New Faces evidence refresh | Read baseline-project; reviewed before recording; updated the two affected guides and source paths; preserved the renamed test byte-for-byte; independent verification and all nine guard tests passed | 124.1 |
| Python authoring fixture with final guidance | Corrected the contradiction, preserved code/tests/contract/Makefile and the existing instruction, declared real `make check`, recorded after review, and passed independent verification; no unsupported dependency prohibition or approval requirement | 186.2 |

Grok's authoring record monitors `AGENTS.md` with the contract, implementation, tests, and Makefile as evidence. It corrected but did not monitor README, and explicitly reported that bounded coverage. This differs from the two-artifact choice made by Codex and Claude; the one-artifact result meets the published fixture rubric but does not protect README from later unreviewed edits.

Three earlier authoring attempts were blocked by the evaluation harness's narrow command allowlist: harmless compound commands and ordinary `git -C` / `make -C` variants caused headless cancellation. They returned process exit code 0 while the structured result reported `error_during_execution`, `is_error: true`, and `cancelled`. They are retained as blocked runner attempts, not successful authoring trials or evidence of poor semantic guidance. The completed setup and regression trials used automatic tool approval with Grok's workspace sandbox, bounded tool set, no subagents, and web tools disabled; refresh completed under the narrower allowlist. Global plugin/MCP configuration produced startup warnings, so the host environment was not fully isolated. No MCP tools were invoked in the completed exercises.

All completed Grok trials stayed within the same 240-second cap with zero repair rounds. Different permission configurations and unmeasured global context preclude direct timing or cost rankings across hosts. These remain single development exercises, not proof of reliable model parity. Check the terminal structured status as well as process exit code when adapting the evaluation protocol to this CLI.
