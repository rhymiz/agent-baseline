# Research behind instruction maintenance

Reviewed 2026-09-17. Consult this reference when revising the authoring or
evaluation method. Ordinary setup and engineering tasks do not need to load this
literature. These sources inform design choices; none evaluates Agent Baseline
0.4.3 or overrides explicit owner policy.

## What belongs in instructions

[OpenAI's September 2026 skills and prompts guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
recommends precise descriptions, progressive disclosure, minimal routers, and
reconsidering elaborate procedures as models change. It also cautions that shared
skills serve different models. This supports conditional references and testing
within each model/host, not removing required constraints based on model branding.
This is vendor engineering guidance, not a controlled benchmark.

[Anthropic's context engineering article](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
describes a finite attention budget, focused instructions, and retrieving relevant
context when needed. Its [Claude Code best practices](https://code.claude.com/docs/en/best-practices)
recommend broadly applicable root instructions and on-demand skills for specialized
work. Retain non-obvious decisions and canonical pointers; do not optimize a word
count or duplicate an easily discovered code tour.

[Gloaguen et al., Evaluating AGENTS.md, version 2](https://arxiv.org/html/2602.11988v2)
(revised June 23, 2026) compares absent, generated, and developer-provided context
across four model/agent pairings, SWE-bench Lite, and 138 CTXbench tasks from 12
repositories. Task-success differences versus absent context were not statistically
significant; generated context increased average inference cost by 20% and 23% on
the two benchmarks. Agents generally followed instructions, but overviews did not
meaningfully improve navigation. The study is Python-focused, uses one completion
per agent-instance-condition, and grades task resolution through tests. It does
not establish that instructions generally harm success, that shorter always wins,
or that owner policy lacks value. Use a minimal control to test added guidance.

[Vercel's Next.js evaluation](https://vercel.com/blog/agents-md-outperforms-skills-in-our-agent-evals)
(January 2026) reports 53% for no documentation, 53% for default skill discovery,
79% with explicit skill instructions, and 100% with an embedded documentation index.
This is a company experiment on framework-specific tasks, not a universal ranking
of instruction formats. Its useful implication is to distinguish relevant knowledge
from reliable delivery of that knowledge. An optional skill is not a guarantee that
a mandatory procedure reaches the agent.

Taken together, these sources support testing what an instruction adds and how it
is delivered. They do not justify automatically generating longer guidance or
discarding detailed domain knowledge. This synthesis is a design inference.

## Loading and evaluation

[OpenAI's AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md)
describes discovery, precedence, and size limits. Its [skill documentation](https://learn.chatgpt.com/docs/build-skills)
distinguishes metadata exposure from body loading and documents catalog shortening.
[Google's Gemini CLI context guide](https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/tutorials/memory-management.md)
describes hierarchical instructions and active-context inspection. These are
host-specific, changing contracts. Check the supported installed version before
using a context-inspection command; a local alias alone proves no loading behavior.

[Anthropic's agent evaluation guidance](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents)
(January 2026) distinguishes tasks, repeated trials, transcripts, outcomes, and
graders. It recommends combining suitable deterministic, model, and human grading,
with calibration and separate capability and regression evaluation. Agent Baseline
uses independent artifact checks and preserves failed or blocked trials. A generated
baseline also needs a fresh consumer task before claiming downstream benefit.

[Google's agent evaluation documentation](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/evaluation-agents)
separates final-response evaluation from trajectory evaluation, including several
tool-sequence metrics. This supports separate outcome and routing evidence. Exact
sequence matching is suitable only when order is part of the task contract; a valid
alternative implementation should not fail merely for taking a different route.

## Learning and engineering effort

[Zhang et al., Agentic Context Engineering, version 1](https://arxiv.org/html/2510.04618v1)
(October 2025; Stanford, SambaNova, and UC Berkeley authors) studies incremental
curation of context in agent and domain-specific benchmarks. It identifies loss of
useful detail during repeated rewriting and acknowledges that poor reflection can
create harmful context. Its results do not establish gains for repository-baseline
authoring. Preserve linked evidence and contrary outcomes; do not promote every
incident into policy or introduce automatic self-modifying instructions.

[METR's July 2025 randomized study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/)
involved 16 experienced developers and 246 real tasks. Early-2025 AI access increased
completion time by 19% despite perceived speedups. This is a specific historical
setting, not a current productivity estimate. The [February 2026 update](https://metr.org/blog/2026-02-24-uplift-update/)
reports selection and time-measurement problems that limit interpretation of newer
results. Record human review, repair, and maintenance effort alongside model cost
and latency; neither perceived helpfulness nor benchmark success is productivity.

## Applying this evidence

The maintenance method preserves owner policy, asks what decision each added rule
changes, and separates structural checks, semantic review, loading, and outcomes.
Controlled evaluation compares fixed conditions and includes downstream use of
generated guidance. These are research-informed requirements, not measured gains.
Routine fixes need no benchmark. Broader effectiveness claims require representative
held-out tasks, repeated trials, independent grading, and stated uncertainty.

When refreshing this reference, retain exact paper versions, distinguish empirical
results from vendor recommendations and local inferences, and check newer revisions
before repeating quantitative claims. Evidence hashes cover this local record;
they do not monitor remote publications or certify the research conclusions.
