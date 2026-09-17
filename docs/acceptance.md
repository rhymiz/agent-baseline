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

## Instruction maintenance in 0.3.0

The accepted follow-up to the [OpenAI skills and prompts article](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) is a focused revision of guidance and evaluation, preserving the deterministic CLI and its execution boundaries:

- Audit existing and new instructions for trigger precision, source authority, conditional reading, necessary ordering, approval scope, completion, and conflicting guidance. Recommend keeping, narrowing, moving, or removing rules with concrete evidence. Preserve explicit owner policy and distinguish predicted effects from observed failures.
- Route the root skill to maintenance, audit, evaluation, and record references. Keep audit read-only unless fixes are also requested. Authorized maintenance should reach reviewed guidance, recorded evidence, required verification, and an accurate report without another routine approval stop.
- Preserve the complete `skill show` export and add an optional exact bundled-file selector. Reject unbundled paths without reading arbitrary local files. Keep installed guidance portable and test the distribution outside the checkout.
- Supply reproducible local-fix, typo, competing-skill, and audit fixtures. Separate artifact checks from transcript and semantic grading; retain failed, blocked, and incomplete outcomes. Compare guidance within each model and host before claiming a behavioral improvement.

These are acceptance requirements for the new work. The native trials below evaluate 0.2.0; they do not establish the revised guidance's performance.

## Engineering guidance output contract in 0.3.1

Setup and refresh must leave each important engineering rule in scope traceable from its application and observable invariant to supporting authority and a relevant executable check or concrete review criterion. Inspect actual assertions before claiming test coverage. Identify unresolved authority, missing coverage, and proposed checks explicitly; do not describe them as established or verified.

Keep these relationships in maintained guidance or its canonical references. No fixed layout, additional skill, or new evidence-record schema is required. Refresh reviews affected relationships without expanding to unrelated rules. Completion reports point to those decisions and distinguish executed verification, review judgments, proposals, and remaining gaps.

Audit and evaluation must assess the relationships themselves. A valid record, a list of sources, or a passing suite is insufficient evidence of semantic coverage. Include uncovered invariants and decisions that require review in authoring exercises; judge accurate gap reporting separately from engineering compliance. The CLI continues to validate structure, freshness, and declared command outcomes without claiming semantic certification.

## Consumer outcome workflow

Authorized setup must configure a usable learning workflow for the consumer, not merely recommend one. Reuse an established evidence location and available authorized operations; otherwise create a plain Markdown log using project conventions. Write conditional project routing with actual paths and update semantics, and seed an initial pending case only from an observed finding. No external memory service, tracker, model API, or hand-authored consumer template is required. Preserve existing stores and avoid duplicate histories; report unavailable preferred storage and any blocked fallback honestly.

The bundled outcome reference connects findings, changes, revisions, desired behavior, next comparable-task criteria, evidence coverage, and assessment history. Applying a change and passing checks are distinct from observed improvement. Pending, unchanged, regressed, and inconclusive results remain visible; contrary evidence can reopen a case. Root guidance and stable procedures can be baseline artifacts; routine case assessments do not become normative rules or force unrelated evidence refreshes.

Audit reports the requested versus inspected scope and unavailable or bounded evidence. Evaluation grades consumer usability and evidence relationships, including a project without integrations, preserved existing storage, and missing outcome evidence. Structural/export/install tests prove packaging and routing; behavioral fixtures require separately reported semantic or model evaluation. The CLI evidence schema and runtime remain unchanged.

## Research-informed maintenance in 0.4.2

The authorized research follow-up strengthens the authoring and evaluation method
without changing the CLI execution or record contracts:

- Retain an instruction for an identifiable project decision, non-obvious constraint,
  or recurring failure. Preserve owner policy and prefer canonical references to
  duplicated explanations; accuracy or shorter text alone does not establish value.
- Keep reusable domain and validation principles distinct from owner-specific import,
  type, and public API restrictions. This repository's explicit no-re-export policy
  remains in force; consumer guidance must honor the consumer's own authority.
- Distinguish installation, metadata exposure, body loading, and observed behavior.
  A requested native loading check needs effective-context or trace evidence, not
  only valid files. Ordinary maintenance does not require a model run.
- For controlled trials, compare minimal required guidance, current guidance, and
  proposed changes when measuring added value. Use instruction-removal comparisons
  where relevant without removing mandatory policy. Predeclare outcomes, budgets,
  stopping criteria, and regression limits; retain paired results and uncertainty.
- Evaluate baseline authoring and downstream consumer use separately. Freeze generated
  artifacts before fresh consumer tasks, preserve owner policy in every condition,
  and keep solutions and graders outside the agent's accessible workspace.
- Record model effort, human review and repair, and maintenance effort separately.
  Preserve unknown measurements and contrary outcomes in the existing workflow.
- Bundle optional research provenance with source versions and applicability limits.
  The local evidence record monitors this synthesis and its accepted scope; linked
  remote literature still requires source review and is not hash-verified by the CLI.

Review the maintained rules against the [research rationale](../skills/baseline-project/references/research.md)
and these criteria. The [consumer exercise](../examples/evaluation/README.md#test-authored-guidance-in-a-fresh-consumer)
provides a development task and independent preservation probe. Package tests check
export, installation, links, and existing execution behavior. These are release
acceptance checks, not a controlled model-performance study; no performance gain or
cross-model equivalence is claimed for 0.4.2.

## 0.2.0 release evidence

The 49-test suite passes against the built wheel outside the source checkout, and strict typing, lint, and skill/plugin structural checks pass. The suite exercises the portable project shapes and failure boundaries above. Native development trials and their limitations are recorded in [evaluation-0.2.0.md](evaluation-0.2.0.md); the public authoring fixture makes the semantic rubric reproducible. New Faces now has schema 2 evidence, persistent managed guidance, canonical aliases, and generic checker commands; its local doctor and nine database-guard tests pass. The [four-platform CI run](https://github.com/rhymiz/agent-baseline/actions/runs/34003687617) and [Trusted Publishing run](https://github.com/rhymiz/agent-baseline/actions/runs/34003786301) passed for release commit `28086f473781f8f945ec56a6c3855149d88e6563`. Fresh-cache `uvx agent-baseline@0.2.0` initialization and doctor checks passed; the published package verified New Faces with 17 artifacts, two declared checks, nine guard tests, and unchanged monitored inputs. The installed managed skill matched the published package. The subsequent Grok Build 1.0.13 evaluation completed all three task families with independent artifact checks; its bounded README coverage and three runner-cancelled authoring attempts are retained in the evaluation report. Native discovery is best effort, not a controlled harness guarantee.
