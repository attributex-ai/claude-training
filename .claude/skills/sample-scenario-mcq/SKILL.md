---
name: sample-scenario-mcq
description: Generate CCAF-style multiple-choice practice questions for one of the six Claude Certified Architect – Foundations exam scenarios, matching the official exam guide's stem / four-option / answer / explanation format. Use this skill whenever the user asks for "sample MCQs", "practice questions", "exam-style questions", "CCAF questions", a "practice quiz", or wants to generate quiz material for a specific CCAF scenario (Customer Support Resolution Agent, Code Generation with Claude Code, Multi-Agent Research System, Developer Productivity, CI/CD, Structured Data Extraction) — even if they don't explicitly name this skill. Also trigger when extending or regenerating an existing `*_sample_questions.md` file in this repo.
---

# Sample Scenario MCQ Generator

Generates practice MCQs for one of the six CCAF exam scenarios. Output is a single well-formatted markdown file that matches the rhythm and rigor of the sample questions in `ccaf-exam-guide.pdf`.

The canonical reference output already exists in this project at `customer_support_sample_questions.md` — match that file's structure and tone. The exam guide's "Sample Questions" section (pp. 25–33 of `ccaf-exam-guide.pdf`) is the gold standard for question style.

## Workflow

1. **Ask the user for inputs** using `AskUserQuestion` — two questions in one message:
   - *Which scenario?* — single-select among the six scenarios listed below.
   - *How many questions?* — single-select with options "10", "15", "20", "25" (or let the user type a custom number via "Other").
2. **Generate** the requested number of MCQs against that scenario, applying the format and quality rules below.
3. **Save** to a markdown file at the repo root named `<scenario_slug>_sample_questions.md` (e.g., `multi_agent_research_sample_questions.md`). If a file with that name already exists, ask the user whether to overwrite, append a numeric suffix, or extend the existing file.
4. **Report** the file path and the answer-letter distribution in the end-of-turn summary.

## The six exam scenarios

When asking the user to pick, present these with their primary domains. The scenario text below is the *only* context the generated questions should live in — keep tools, metrics, and terminology consistent with the scenario.

1. **Customer Support Resolution Agent** — Claude Agent SDK agent handling returns, billing disputes, account issues. MCP tools: `get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`. Target: 80%+ first-contact resolution. *Primary domains:* Agentic Architecture & Orchestration, Tool Design & MCP Integration, Context Management & Reliability.
2. **Code Generation with Claude Code** — Team uses Claude Code for code generation, refactoring, debugging, docs. Needs custom slash commands, CLAUDE.md configs, plan mode vs direct execution. *Primary domains:* Claude Code Configuration & Workflows, Context Management & Reliability.
3. **Multi-Agent Research System** — Coordinator delegates to specialized subagents (web search, document analysis, synthesis, report generation) using the Claude Agent SDK; produces cited reports. *Primary domains:* Agentic Architecture & Orchestration, Tool Design & MCP Integration, Context Management & Reliability.
4. **Developer Productivity with Claude** — Agent helps engineers explore unfamiliar codebases, understand legacy systems, generate boilerplate, automate repetitive tasks. Uses built-in tools (Read, Write, Bash, Grep, Glob) plus MCP servers. *Primary domains:* Tool Design & MCP Integration, Claude Code Configuration & Workflows, Agentic Architecture & Orchestration.
5. **Claude Code for Continuous Integration** — Claude Code in CI/CD pipelines for automated code reviews, test generation, PR feedback. Needs actionable prompts that minimize false positives. *Primary domains:* Claude Code Configuration & Workflows, Prompt Engineering & Structured Output.
6. **Structured Data Extraction** — Extract info from unstructured docs, validate with JSON schemas, handle edge cases, integrate downstream. *Primary domains:* Prompt Engineering & Structured Output, Context Management & Reliability.

## Anatomy of one question

Every question follows this exact shape:

```markdown
## Question N

<Stem: 2–4 sentences. Opens with a concrete production signal — a metric, log
excerpt, observed behavior, or specific failure. Ends with a focused question.>

A) <Option text>
B) <Option text>
C) <Option text>
D) <Option text>

**Correct Answer: X**

<Explanation: 3–5 sentences. State the principle that makes X correct, then
name each distractor by letter and identify the *category* of mistake it
represents (e.g., "relies on probabilistic LLM compliance", "addresses tool
availability rather than tool ordering", "over-engineered for a first step").>
```

End the file with an answer-key table and a one-line distribution summary, mirroring `customer_support_sample_questions.md`.

## Quality rubric — apply to every question before moving on

These rules exist because earlier generations of this set were graded against the exam guide's official samples and the gaps below were the recurring deductions. Each rule has a *why*; use the why to judge edge cases.

### 1. Distractors must be plausible — never strawmen

A good distractor is something a candidate with **incomplete** knowledge would actually pick. The exam guide's distractors include things like "implement a routing classifier" or "deploy a separate ML model" — wrong, but the kind of wrong that comes from over-engineering, not from absurdity. Reject distractors that are obviously wrong on first read.

**Avoid:** "Crash the agent session so the failure is visible", "Lower the model temperature so it follows the prompt", "Remove `process_refund` and have a human do all refunds".

**Prefer:** "Retry internally with exponential backoff and return only the final outcome", "Add 5–8 few-shot examples showing correct ordering", "Consolidate both tools into one that dispatches internally".

### 2. Pair the correct answer against the *next-best* alternative, not a weak one

The exam-guide samples are hard because the wrong options are *also tempting*. The correct answer should beat the strongest distractor on a specific principle, and the explanation should name that principle. If three of your four options are obviously bad, the question is testing recognition, not judgment.

### 3. Avoid rhetorical strawmen in the stem

Framings like "A new engineer proposes…" or "Your intern suggests…" cue the reader that the proposal is wrong. Instead, present the alternative as something the team is genuinely considering: "You're considering replacing full tool results with one-line summaries to save tokens. Why is this risky?" The candidate must judge the idea on its merits.

### 4. Wrap pure-recall questions in a scenario

If a question is testing API trivia (e.g., what `tool_choice: "any"` does), embed it in a production symptom: "Your agent occasionally returns a chatty acknowledgment instead of calling a tool when a customer asks for order status. You want to guarantee a tool call but let the model choose which. Which `tool_choice` value?" The candidate then has to recognize the symptom *and* know the mechanic.

### 5. End explanations crisply — no caveats or "Note:" tails

Official exam-guide explanations end after rebutting the distractors. They don't tack on "Note: of course, X is also reasonable in some cases…" — that kind of hedge undermines the answer. If a caveat is genuinely needed (e.g., "compiling a handoff summary is still appropriate"), fold it into the main explanation, don't append it.

### 6. Distribute correct answers evenly across A / B / C / D

Candidates pattern-match on positional bias. For N questions, the correct letter must be uniformly distributed:

- 20 questions → 5 each of A, B, C, D
- 16 questions → 4 each
- 12 questions → 3 each
- Any N → either ⌊N/4⌋ or ⌈N/4⌉ of each letter; no letter may dominate

Plan the assignment **before** drafting the questions (you can write the question content first, then permute the option order to land on the assigned letter). Include the distribution as the last line of the markdown file.

### 7. Stem realism — anchor every stem in concrete numbers or signals

Every stem should contain at least one of: a percentage ("12% of cases"), a count ("40+ fields per response"), a dollar amount ("refunds above $500"), a file path, a tool name, a log excerpt, or a specific failure mode. Vague stems ("sometimes the agent misbehaves") produce vague distractors.

## Domain coverage

Spread the questions across the scenario's primary domains rather than clustering on one. For a 20-question Customer Support set, a healthy split is roughly:

- Agentic loop + multi-step workflow (Task 1.1, 1.4): 4–5 questions
- Hooks / programmatic enforcement (Task 1.5): 2–3 questions
- Tool design + MCP (Domain 2): 3–4 questions
- Escalation + ambiguity (Task 5.2): 4–5 questions
- Context management (Task 5.1, 5.3): 3–4 questions

Adapt the split to the scenario's primary domains listed above.

## File output format

Header (always identical structure — vary only the scenario name and recap):

```markdown
# CCAF Sample Questions: <Scenario Name>

<N> practice questions in the format of the *Claude Certified Architect – Foundations* exam guide, all set within the **<Scenario Name>** scenario.

**Scenario recap:** <one-paragraph recap from the scenario list above, with tools and target metrics.>

**Primary domains:** <comma-separated primary domains from the scenario list.>

---

## Question 1
…
```

Footer (always):

```markdown
## Answer Key

| # | Answer | # | Answer | # | Answer | # | Answer |
|---|--------|---|--------|---|--------|---|--------|
| 1 | <X> | … | … | … | … | … | … |

Distribution: A × <n>, B × <n>, C × <n>, D × <n>.
```

For sets where N doesn't divide evenly into 4 columns, use as many columns as fit (e.g., a 10-question set may use a 2-column table).

## End-of-turn summary

Two short lines:
1. The file path that was written.
2. The answer distribution and which scenario was used.

Example: "Wrote `multi_agent_research_sample_questions.md` — 20 questions for the Multi-Agent Research System scenario, A×5 / B×5 / C×5 / D×5."

## Anti-patterns to avoid

- Generating fewer or more questions than the user requested.
- Letting the correct letter cluster (e.g., 8 of 20 on "A").
- Using the same distractor template across multiple questions ("Lower the model temperature" appearing as a distractor more than once is a smell).
- Drifting outside the chosen scenario's tools or terminology (e.g., referencing `lookup_order` in the Multi-Agent Research scenario).
- Restating the question's premise in the explanation instead of explaining the underlying principle.
- Skipping the `AskUserQuestion` step and assuming defaults — the choice of scenario and count must be the user's.
