# Product acceptance: portable Agent Baseline

The objective is a project-agnostic tool that makes evidence-backed agent guidance practical to install, maintain, and evaluate. New Faces is a real integration fixture, not an architectural dependency. Identical capability across all models cannot be guaranteed by documentation; measurable baseline behavior and honest verification are required.

The user's clarified acceptance boundary is best-effort host discovery and good engineering decisions when the guidance is actually read. The package does not control agent harnesses. Judge explicit-invocation outcomes separately from natural selection, and do not expand the product into a harness controller to compensate for a host skipping a skill.

## Required outcomes

- [x] A documented bootstrap works in an existing repository and a new project without inventing domain rules, runnable checks, or reviewed evidence. Existing instructions and unrelated edits survive.
- [x] Generic guidance validation lives in the package. It understands Markdown links and code examples, skill YAML, host imports, and canonical aliases without project-specific names or a Node dependency.
- [x] Drift reports identify affected guidance and the supporting changes. Selective evidence can reduce irrelevant drift without hiding missing or ambiguous evidence.
- [x] Skill installation supports persistent discovery, existing canonical skills, safe updates, and local-edit conflict detection. It never relies on a temporary uv environment.
- [x] Project guidance remains canonical across host adapters. An explicit CLI reading path works for hosts without native discovery.
- [x] Verification distinguishes mechanical guidance checks, project checks, host discovery, and actual model behavior. No hash snapshot certifies correctness.
- [x] Portable fixtures cover multiple codebase shapes, missing Git, monorepos, paths with spaces, malformed metadata, links/aliases, and failure handling. Release distributions are tested outside the source checkout.
- [x] New Faces uses the published generic implementation; remove the bespoke checker once its responsibilities are covered. Preserve the existing application verification policy.
- [x] Fresh installed agent sessions demonstrate discovery and explicit invocation. Test representative New Faces engineering decisions with observable criteria and record limitations.
- [x] A reusable evaluation protocol or executable interface supports user-selected runners and recorded artifacts without coupling the package to one model API. Report actual outcomes rather than inferred quality scores.
- [x] Documentation, package metadata, CI, GitHub release, and PyPI commands agree with the final behavior. Verify the release from a fresh uv cache.

- [x] Run the same explicit-guidance evaluation against the installed Grok CLI, grade actual artifacts, and retain runner limitations or failures in the report.

## Evidence ledger

Initial state: v0.1.1 supplies a CLI and bundled skill, but installation lacks update support; verification requires bespoke project guidance checks; drift reports contain paths without impact routing. New Faces has local uncommitted setup work from this task that must be preserved or deliberately replaced. Its existing engineering guidance is authoritative context, not a reusable package template.

This checklist stays open until each outcome has current evidence. Passing unit tests alone does not close integration or behavioral outcomes.

## Current evidence

The 49-test suite passes against the built wheel outside the source checkout, and strict typing, lint, and skill/plugin structural checks pass. The suite exercises the portable project shapes and failure boundaries above. Native development trials and their limitations are recorded in [evaluation-0.2.0.md](evaluation-0.2.0.md); the public authoring fixture makes the semantic rubric reproducible. New Faces now has schema 2 evidence, persistent managed guidance, canonical aliases, and generic checker commands; its local doctor and nine database-guard tests pass. The [four-platform CI run](https://github.com/rhymiz/agent-baseline/actions/runs/34003687617) and [Trusted Publishing run](https://github.com/rhymiz/agent-baseline/actions/runs/34003786301) passed for release commit `28086f473781f8f945ec56a6c3855149d88e6563`. Fresh-cache `uvx agent-baseline@0.2.0` initialization and doctor checks passed; the published package verified New Faces with 17 artifacts, two declared checks, nine guard tests, and unchanged monitored inputs. The installed managed skill matched the published package. The subsequent Grok Build 1.0.13 evaluation completed all three task families with independent artifact checks; its bounded README coverage and three runner-cancelled authoring attempts are retained in the evaluation report. Native discovery is best effort, not a controlled harness guarantee.
