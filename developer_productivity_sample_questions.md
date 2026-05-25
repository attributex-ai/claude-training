# CCAF Sample Questions: Developer Productivity with Claude

20 practice questions in the format of the *Claude Certified Architect – Foundations* exam guide, all set within the **Developer Productivity with Claude** scenario.

**Scenario recap:** An engineering organization deploys Claude Code to help engineers explore unfamiliar codebases, understand legacy systems, generate boilerplate, and automate repetitive tasks. The agent uses the built-in tools (`Read`, `Write`, `Bash`, `Grep`, `Glob`) alongside MCP servers (issue trackers, observability, databases). The configuration surface includes project- and user-level `CLAUDE.md`, `.claude/settings.json`, custom slash commands in `.claude/commands/`, custom subagents in `.claude/agents/`, optional `.claude/rules/` files with glob-conditional conventions, hooks (`PreToolUse`, `PostToolUse`, …), the `Explore` subagent, and plan mode. Success criteria: shorter time-to-first-useful-edit on unfamiliar code, fewer wrong-tool selections, and high engineer trust in agent-initiated actions.

**Primary domains:** Tool Design & MCP Integration, Claude Code Configuration & Workflows, Agentic Architecture & Orchestration, Context Management & Reliability.

---

## Question 1

An engineer asks Claude Code to "find all callers of `calculate_tax` in this Python monorepo." Claude runs `Bash` with `grep -rn calculate_tax .` and receives 1,400 matches that include `.venv/`, `dist/`, and compiled migration artifacts. The session burns roughly 12% of its context budget filtering noise before producing a useful answer. Which Claude Code primitive should it have used?

A) The built-in `Grep` tool, which uses ripgrep semantics, honors ignored paths, and returns ranked file matches scoped to source files by default.
B) The built-in `Glob` tool to pattern-match file names containing `calculate_tax`.
C) The built-in `Read` tool with the repository root as `file_path`, letting Claude inspect the source itself.
D) The same `Bash` call with `--exclude-dir` flags for `.venv`, `dist`, and other noise sources.

**Correct Answer: A**

`Grep` is Claude Code's purpose-built source-search primitive: ripgrep semantics, ignored-path defaults, and structured ranked output that fits cleanly in context. Options B and C confuse the layer — `Glob` matches filenames rather than file contents, and `Read` operates on a single file with no across-tree search. Option D keeps the wrong tool and chases noise sources one at a time, where the right tool already excludes them as a class.

---

## Question 2

An engineer needs to rename a misspelled identifier `recieved_at → received_at` across 4 occurrences in 2 files. Claude Code is in plan mode by default. Should they stay in plan mode or switch?

A) Stay in plan mode — every multi-occurrence rename benefits from an upfront plan, even small ones.
B) Stay in plan mode and dispatch a subagent to enumerate the occurrences first.
C) Switch to direct execution — plan mode's confirmation overhead exceeds the value of a plan for a trivial, mechanical rename.
D) Stay in plan mode and run with `--dangerously-skip-permissions` so the planning turns are quick.

**Correct Answer: C**

Plan mode is calibrated to changes where getting the *plan* wrong carries real cost — multi-file edits, architectural decisions, refactors that interact with other systems. A 4-occurrence rename in 2 files has none of that surface; the plan and the change are the same length. Options A and B keep plan mode and pay the planning tax for no benefit, with B layering on a subagent dispatch that adds context cost without changing what gets edited. Option D toggles a different safety layer (permission prompts) without addressing the mismatch between plan mode and the size of the work.

---

## Question 3

A team wants a `PostToolUse` hook on `Edit` and `Write` that runs `pnpm test --related <file>` after every code modification. The hook must apply to every engineer who clones the repo, with no per-engineer setup. Where should it be configured?

A) Each engineer's `~/.claude/settings.json` so the hook applies across all their projects.
B) The project's `.claude/settings.json` committed to the repository so the hook ships with the codebase.
C) The project's `CLAUDE.md` under a "Hooks" heading.
D) A custom slash command that engineers invoke after edits.

**Correct Answer: B**

Hooks are defined in `settings.json`; the project-level `.claude/settings.json` is the correct scope when the rule must apply uniformly to everyone who clones the repo and be version-controlled. Option A drifts the rule into personal config — new engineers join without it, and the hook also fires on unrelated projects. Option C misplaces the configuration — `CLAUDE.md` carries instructions to the model, not harness-level hook definitions. Option D shifts responsibility back to the engineer to remember to invoke a command, which is exactly the failure mode a `PostToolUse` hook removes.

---

## Question 4

An engineer asks Claude to refactor `auth_module.py` to use the new `SessionService` interface. Claude dispatches a subagent for the refactor. The subagent's output renames methods consistently but introduces 14 calls to `SessionService.validate(token)` — a method that does not exist. The actual method is `SessionService.verify(token)`. The dispatch log shows the subagent was launched with a 60-word task description naming "the new SessionService" but no file path or interface excerpt. What is the most likely root cause?

A) The subagent's underlying model is hallucinating method names; switching to a stronger model will resolve it.
B) The subagent ran out of time before it could open the `SessionService` file.
C) The main thread should have used plan mode so the interface would have been read first.
D) The subagent's prompt did not include the `SessionService` interface or a file reference, and subagents only see what their dispatch prompt contains.

**Correct Answer: D**

Subagents start with a clean context — they only know what the dispatch prompt tells them. With a symbol name but no file path or interface excerpt, the subagent has nothing to read and fills the gap with a plausible-sounding guess. Options A and B blame the wrong layer: a stronger model and more wall-clock time both still need the file reference, because the subagent has no awareness the file exists. Option C miscasts plan mode, which gates execution in the main thread but cannot inject context into a subagent the dispatch prompt omits.

---

## Question 5

A team needs Claude to query their production Postgres analytics database during incident debugging. Queries are read-only `SELECT`s across 4–5 tables, run a few times per week. Which approach best balances safety and ergonomics?

A) Install the official `postgres-mcp` server scoped to a read-only DB role; Claude calls it with structured query arguments, and write paths are physically unavailable at the database.
B) Give Claude `Bash` plus `psql`; engineers already know the CLI, and prompts can request read-only behavior.
C) Wrap `psql` in a Python script and have Claude invoke it through `Bash`.
D) Build a `/query-pg` slash command that templates SQL into a `psql` invocation.

**Correct Answer: A**

A purpose-built MCP server provides two properties the alternatives cannot: a typed tool surface (structured arguments instead of shell strings) and a privilege boundary enforced at the database (a read-only role). Options B, C, and D all run `psql` through `Bash` under the hood — the underlying tool retains full database privileges and a shell-string surface, so the safety properties are unchanged; only the ergonomic wrappers differ.

---

## Question 6

A team wants to prevent Claude Code sessions from executing `rm -rf` and `git push --force` under any circumstance, including when the command is wrapped (`bash -c "rm -rf ..."`) or aliased. The block must be programmatic, not probabilistic. Which mechanism enforces this?

A) Document the rule in the project's `CLAUDE.md` so Claude learns to avoid those commands.
B) Add a `PreToolUse` hook on the `Bash` tool that inspects the resolved command string and refuses calls matching the dangerous patterns.
C) Revoke the `Bash` tool permission entirely for the project.
D) Set Claude Code's permission policy to prompt the engineer on every Bash invocation.

**Correct Answer: B**

A `PreToolUse` hook is Claude Code's programmatic safety primitive — it runs before every Bash invocation, sees the resolved command (including wrappers), and can deny outright. Options A and D both live in the probabilistic regime: a `CLAUDE.md` rule is followed by the model most of the time, and per-invocation prompts depend on the engineer catching the dangerous moment correctly. Option C eliminates the symptom and most of the value; the team needs Bash for legitimate work.

---

## Question 7

An engineer asks Claude to audit a Django codebase for three independent issues: (1) N+1 query patterns, (2) missing CSRF protection on POST endpoints, (3) unused migration files. Each audit takes ~4 minutes and reads a disjoint slice of the repo. What is the best approach?

A) Run all three audits in the main thread sequentially so the engineer can review each finding as it lands.
B) Dispatch three subagents sequentially — one per audit, waiting for each to finish before starting the next.
C) Run audit 1 in the main thread while dispatching audits 2 and 3 as subagents in parallel.
D) Dispatch three subagents in parallel by issuing all three `Agent` tool calls in a single message.

**Correct Answer: D**

Independent tasks with disjoint file sets and no sequential dependency are the trigger for parallel subagent dispatch — issuing the three `Agent` tool calls in a single message runs them concurrently and cuts wall-clock time roughly threefold. Options A and B serialize work that has no reason to serialize, multiplying time-to-result. Option C splits the main thread between coordination and execution, forfeiting the isolation that makes subagent dispatch worthwhile and crowding the main thread's context.

---

## Question 8

A team's `/scaffold-crud` slash command generates boilerplate Django models, serializers, and viewsets from a one-line description and runs ~1,500 times per week. Inspecting outputs shows 95% of runs produce near-template work with minor variation. A separate `/refactor-module` command, which restructures existing code, also runs on the same model and produces work the team strongly values. What is the best move?

A) Switch both commands to Haiku to maximize cost savings; the refactor quality drop is acceptable.
B) Keep both on Opus — model choice should be uniform across commands for predictability.
C) Route `/scaffold-crud` to Haiku for the template-shaped work and keep `/refactor-module` on Opus for the reasoning-heavy work.
D) Cache `/scaffold-crud` outputs by description string so 95% of runs are free.

**Correct Answer: C**

The right lever is proportionality: match the model's capability to each task's complexity. Boilerplate scaffolding is template-shaped work Haiku handles cheaply, while refactoring needs Opus-grade reasoning. Options A and B refuse to use the routing lever — A trades real refactor value for marginal scaffold savings, and B pays Opus prices uniformly for work that doesn't need Opus. Option D misreads the input distribution: boilerplate runs share *structure*, not exact description strings, so a description-keyed cache rarely hits and returns stale scaffolds when it does.

---

## Question 9

An engineer wants Claude to use the project's `User` factory at `app/factories/user_factory.py` whenever code that creates a `User` is generated — in tests, in seed scripts, in admin commands, anywhere in the codebase. Where should the rule live?

A) The project-level `CLAUDE.md` — persistent rules that must apply on every turn, regardless of which file is being edited, belong here.
B) A new `/scaffold-test` slash command whose prompt template embeds the factory rule.
C) Each engineer's user-level `~/.claude/CLAUDE.md` so it follows them across projects.
D) A `.claude/rules/factory.md` file with a glob pattern matching `tests/**/*.py`.

**Correct Answer: A**

Project-level `CLAUDE.md` loads on every turn in the repo and applies regardless of which file is being edited — the right home for a convention that spans tests, seed scripts, admin commands, and any other path that touches `User`. Option B narrows the rule to a single command and misses every freeform turn that creates a `User` elsewhere. Option C drifts the convention into personal config; new engineers join without it. Option D is the wrong scope — `.claude/rules/` with a glob is for path-conditional conventions, and the glob `tests/**/*.py` misses the seed scripts and admin commands the rule explicitly needs to cover.

---

## Question 10

An engineer asks Claude to summarize the changes in `CHANGELOG.md`. Claude's summary covers v1.x and v2.x but does not mention any v3.x release, even though v3.0 shipped months ago. Inspection: `CHANGELOG.md` is 4,200 lines, newest entries are at the bottom, and Claude's session log shows a single `Read` call — `Read(file_path="CHANGELOG.md")` with no `offset` or `limit`. What is the most likely root cause?

A) Claude's model cannot summarize documents of this size; chunk the file and summarize each chunk.
B) The `Read` tool returned only the first ~2,000 lines by default, so the v3.x entries at the bottom were never loaded into context.
C) Markdown parsing dropped the v3.x section because of a malformed heading.
D) The session needs plan mode so the file is fully read before summarization.

**Correct Answer: B**

`Read` has a default line cap (~2,000) and reads from the start of the file unless `offset` and `limit` are passed. With a 4,200-line CHANGELOG and newest entries at the bottom, everything past the cutoff — v3.x included — is simply absent from Claude's context. Options A and C misidentify the layer: the model never *saw* the v3.x lines, so summarization quality and markdown parsing are irrelevant. Option D conflates plan mode (an execution-gating feature) with tool parameters; plan mode does not change how `Read` defaults.

---

## Question 11

A team installed 12 MCP servers (Jira, Linear, Slack, GitHub, Sentry, Datadog, Stripe, Vercel, Postgres, S3, Figma, Notion). Engineers report: sessions feel slow at startup, Claude sometimes picks the wrong tool — calling `linear_create_issue` when an engineer said "log this in Jira" — and context budgets feel tighter than before. What is the best fix?

A) Switch the team to a model with a larger context window so the tool inventory fits comfortably.
B) Consolidate the 12 servers into one custom "super-MCP" that dispatches internally.
C) Add a routing classifier as a preprocessing step that picks the right MCP server before Claude runs.
D) Scope `.mcp.json` per project (or per task) so only the 3–4 servers actually needed are enabled.

**Correct Answer: D**

Every loaded MCP tool consumes context and enlarges the surface Claude must choose from; 12 servers across overlapping domains (Jira and Linear, Sentry and Datadog) makes wrong-tool selection the expected outcome. Scoping `.mcp.json` per project keeps only the relevant servers active and shrinks the decision space directly. Option A treats the context-pressure symptom but leaves the selection ambiguity untouched. Options B and C over-engineer ahead of the cheapest lever — a super-MCP still loads 12 tools' worth of context behind a wrapper, and a classifier adds a preprocessing layer to fix a problem selective enablement removes.

---

## Question 12

A team wants Claude to prompt the engineer before running `npm install` — they do not want to block it (engineers do legitimately add dependencies) but they want a beat of human review to catch accidental installs. What is the right mechanism?

A) Add `npm install` to the deny list in `~/.claude/settings.json`.
B) Add a `PreToolUse` hook that blocks `npm install` and emits a message asking the engineer to run it themselves.
C) Set the `Bash` permission policy for `npm install*` to **ask** in the project's `.claude/settings.json` so Claude prompts before each invocation.
D) Add a `CLAUDE.md` instruction telling Claude to confirm with the engineer before running `npm install`.

**Correct Answer: C**

Claude Code's permission system has three states — allow, ask, deny — and "ask" is the state designed for this case: the engineer is prompted to approve each invocation with the exact command visible. Options A and B both implement *deny* by different mechanisms, which the team explicitly does not want. Option D delegates to model behavior (probabilistic) instead of the harness's enforcement layer; the team needs a guarantee.

---

## Question 13

Engineers report that Claude "sometimes" forgets to run `pnpm test` after editing files. Logs across 200 sessions show Claude runs tests in roughly 70% of edit-flows; the remaining 30% commit untested changes. The engineering manager wants a guarantee, not best-effort. What is the most effective first step?

A) Strengthen the `CLAUDE.md` instruction from "remember to run tests" to "ALWAYS run tests after every `Edit` or `Write`, no exceptions."
B) Configure a `PostToolUse` hook on `Edit` and `Write` that runs `pnpm test --related <file>` automatically and surfaces failures.
C) Switch to a more capable model so instruction-following improves.
D) Build a `/check` slash command engineers must invoke after edits to run the test suite.

**Correct Answer: B**

A `PostToolUse` hook moves test execution from "model behavior" to "harness behavior" — once configured, it fires on every `Edit`/`Write` regardless of what the model decides on that turn, converting a 70% probabilistic compliance rate into a 100% deterministic one. Options A and C stay in the probabilistic regime; stronger prompts and stronger models improve compliance but never reach guarantee territory. Option D shifts responsibility back to the engineer to remember `/check`, which is the same failure mode one layer up.

---

## Question 14

An engineer is debugging an intermittent production crash. The session has read 32 source files, run 47 Bash commands, and built a working hypothesis. The transcript is approaching the context budget and the engineer expects another 1–2 hours of work. What is the right move?

A) Compact the session — distill the hypothesis, evidence gathered, and ruled-out branches into a structured summary, then continue with that summary plus only the files still actively under investigation.
B) Start a fresh session and have the engineer re-explain everything from scratch.
C) Keep going and hope the context budget holds; compaction risks losing key details.
D) Ask Claude to "forget" the early turns to free up budget, then continue.

**Correct Answer: A**

Compaction is designed for exactly this profile — a long investigative session where early raw data has already been distilled into a working hypothesis. A structured summary preserves the *conclusions* while shedding the transcript that produced them. Option B discards hours of investigative state. Option C ignores the imminent budget exhaustion; once the window fills, reasoning quality degrades and earlier turns fall out anyway. Option D misuses the model — asking Claude to "forget" does not free budget because the tokens are already in the transcript; the harness, not the model, manages the window.

---

## Question 15

An engineer asks Claude "where is rate limiting implemented in our API?" The codebase is a medium-sized Python service (~40k LOC). The engineer expects this is a 3–5 file question — likely a middleware file and one or two config locations. Should they dispatch the `Explore` subagent or let the main thread handle it?

A) Always dispatch `Explore` for any "where is X" question — that is what the subagent is for.
B) Dispatch `Explore` *and* search in the main thread in parallel to maximize coverage.
C) Let the main thread handle it — a direct `Grep` + `Read` sequence is the right tool for a 3–5 file lookup.
D) Build a custom `/find-impl` slash command that wraps the search pattern.

**Correct Answer: C**

`Explore` is built for broad investigations that would otherwise burn many tool calls and bloat the main session's context — typically 3+ queries across multiple naming conventions or directories. A focused "where is rate limiting" lookup is a direct `Grep` + `Read` sequence; doing it in the main thread costs little context and returns the answer faster than a subagent dispatch. Option A over-applies the subagent and pays dispatch overhead for work that does not need it. Option B duplicates the same search across two paths. Option D builds a slash command for what is already a one-liner with built-in tools.

---

## Question 16

An engineer ran `/init` early in the project to bootstrap a `CLAUDE.md`. A week later, in a fresh session, they asked: "Can you write me a project overview document covering the major modules?" Claude produced the document — but overwrote the existing `CLAUDE.md` instead of creating `PROJECT_OVERVIEW.md`. The `Write` tool call in the log targeted `CLAUDE.md`. What is the root cause?

A) The `Write` tool unconditionally overwrites whatever path it is given; the `Write` tool itself is at fault.
B) Claude Code lacks a read-only mode for `CLAUDE.md`; the file needs filesystem-level locking.
C) The engineer should have used plan mode so Claude would have surfaced the target path before writing.
D) The prompt did not specify a target filename, and Claude chose a plausible-but-wrong path (`CLAUDE.md`) — the request was ambiguous about *where* to write.

**Correct Answer: D**

`Write` overwrites when handed the same path because that is its contract — the model chooses the path and is responsible for resolving ambiguity in the user's request. The engineer asked for "a project overview document" without naming a target file, and Claude picked the most semantically adjacent existing path it knew about. Options A and B misplace the fault — `Write`'s overwrite semantics are deliberate and necessary, and filesystem locking would break legitimate edits to `CLAUDE.md`. Option C miscasts plan mode, which gates execution but does not change how Claude infers a target filename when none is specified.

---

## Question 17

A team agrees that read-only `gh` commands (`gh pr view`, `gh issue view`, `gh pr list`) should be auto-allowed in their Claude Code sessions. The allow-list should apply to everyone who clones the repo and survive engineer onboarding. Where should the permission live?

A) Each engineer's user-level `~/.claude/settings.json` so the rule applies across all their projects.
B) Each engineer's project-local `.claude/settings.local.json` so they can tune it independently.
C) The shell profile (`.zshrc`) so the commands are aliased and pre-approved.
D) The project's committed `.claude/settings.json` — the rule is shared, scoped to this repo, and tracked in version control.

**Correct Answer: D**

Committed `.claude/settings.json` is the right home for repo-shared permissions: it ships with the codebase, applies uniformly to everyone who clones the repo, and changes are visible in pull requests. Option A drifts the rule into personal config — new engineers join without it, and the permission leaks to unrelated projects. Option B duplicates configuration work across the team and invites drift. Option C operates at the wrong layer — shell aliases do not affect Claude Code's permission system, which evaluates the tool call before invoking the shell.

---

## Question 18

A repetitive task: an engineer runs the same review on every PR — `gh pr view <PR#>`, read the changed files, run `pnpm test --related <changed-files>`, and post a structured review comment. They want a one-keystroke workflow that takes a PR number as input. What is the right Claude Code primitive?

A) A custom slash command (`/review-pr <PR#>`) in `.claude/commands/` whose prompt template captures the workflow and takes the PR number as an argument.
B) A new MCP server that exposes a `review_pr` tool.
C) A `PostToolUse` hook on `Bash` that triggers the review whenever `gh pr view` is called.
D) A custom subagent dispatched via the `Agent` tool, with the PR number passed in the prompt.

**Correct Answer: A**

Slash commands are the right primitive for repeatable, parameterized prompt templates: they live in `.claude/commands/`, accept arguments, and capture a workflow as a reusable invocation. Option B builds infrastructure (a new MCP server) for what is a prompt-template problem, paying server-development cost for no functional gain. Option C misuses hooks, which fire on tool events rather than user invocation, and would trigger on every incidental `gh pr view`. Option D forces the engineer to assemble the dispatch prompt manually each time and forfeits the slash command's argument-passing.

---

## Question 19

A custom MCP tool `query_logs` returns application logs and is correctly wired into Claude Code, but Claude rarely calls it — even when an engineer pastes a stack trace and asks "what was happening in prod around 14:30?" The current tool description is: *"Fetches application logs."* What is the most effective fix?

A) Force the tool to be called by setting `tool_choice: "any"` for the session.
B) Rewrite the description with explicit triggers, arguments, and return shape — e.g., *"Use when investigating errors, crashes, 5xx responses, or unexpected production behavior. Arguments: `service` (string), `time_range` (ISO interval), `severity` (debug|info|warn|error). Returns timestamped log lines with severity and message."*
C) Rename the tool from `query_logs` to `logs_tool` so it surfaces alphabetically.
D) Increase the tool's priority in `.mcp.json` so Claude considers it first.

**Correct Answer: B**

Tool selection is driven primarily by the description: Claude reads it like any other prompt content and decides relevance from the language. *"Fetches application logs"* lacks triggers, argument hints, and return-shape signal, so it does not surface against a stack-trace-with-timestamp prompt. Option A forces *some* tool call rather than the right one, and would also force a tool call when none is appropriate. Options C and D over-credit positional and priority mechanics that do not meaningfully drive selection — the model picks tools by reading their descriptions, not by sort order or a non-existent priority field.

---

## Question 20

A junior engineer reports a frustrating pattern: Claude Code in plan mode spends 3–4 turns asking clarifying questions ("Should I rename the variable in tests too?", "Do you want a comment?") before doing any work — even for trivial fixes like a typo in a comment or a one-line variable rename. They want to keep plan mode for big changes. What is the right adjustment?

A) Add a `CLAUDE.md` instruction: "Do not ask questions for trivial edits — just make them."
B) Switch the junior engineer to Haiku so planning turns are faster.
C) Turn off plan mode for trivial edits — plan mode is calibrated to multi-step, architecturally meaningful changes; for one-line edits, direct execution is the right default.
D) Run with `--dangerously-skip-permissions` so Claude does not pause to confirm.

**Correct Answer: C**

Plan mode is a flow-control feature meant for changes where getting the *plan* wrong has real cost — multi-file edits, architectural decisions, refactors that interact with other systems. For a typo or single-line rename, the planning overhead exceeds the value of the plan; direct execution is the right default. Option A tries to fix the symptom inside the wrong mode — plan mode's contract is to produce and confirm a plan, so it will continue to surface clarifying questions. Option B mistakes latency for the problem; the goal is not faster planning, it is no planning for trivial work. Option D disables a different safety layer entirely (permission prompts), trading too much safety for ergonomics on the wrong axis.

---

## Answer Key

| #  | Answer | #  | Answer | #  | Answer | #  | Answer |
|----|--------|----|--------|----|--------|----|--------|
| 1  | A      | 6  | B      | 11 | D      | 16 | D      |
| 2  | C      | 7  | D      | 12 | C      | 17 | D      |
| 3  | B      | 8  | C      | 13 | B      | 18 | A      |
| 4  | D      | 9  | A      | 14 | A      | 19 | B      |
| 5  | A      | 10 | B      | 15 | C      | 20 | C      |

Distribution: A × 5, B × 5, C × 5, D × 5.
