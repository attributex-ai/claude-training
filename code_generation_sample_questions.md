# CCAF Sample Questions: Code Generation with Claude Code

Twenty practice questions in the format of the *Claude Certified Architect – Foundations* exam guide, all set within the **Code Generation with Claude Code** scenario.

**Scenario recap:** Your team uses Claude Code to accelerate software development — code generation, refactoring, debugging, and documentation. You're integrating it into the development workflow with custom slash commands, CLAUDE.md configurations, path-specific rules, and a working understanding of when to use plan mode versus direct execution.

**Primary domains:** Claude Code Configuration & Workflows, Context Management & Reliability.

---

## Question 1

A senior engineer keeps reminding teammates about a particular linting convention every time they run Claude Code, even though she has added it to `~/.claude/CLAUDE.md` and pushed nothing else for two weeks. Teammates consistently don't see the convention applied. What's the root cause?

A) `~/.claude/CLAUDE.md` is user-scoped and applies only to that user's machine; project-shared instructions belong in `.claude/CLAUDE.md` or root `CLAUDE.md`, which is checked into the repo.
B) Claude Code only loads `CLAUDE.md` from the repository root — files inside `.claude/` aren't read at session start.
C) Teammates must run `/memory reload` after she pushes a new memory file before it takes effect for them.
D) The convention is being loaded but lower-priority project rules are overriding it; she needs to reorder the sections so the lint rule appears first.

**Correct Answer: A**

The CLAUDE.md hierarchy is user-level → project-level → directory-level, and the user-level file lives in the user's home directory — it isn't shared via version control. The fix is to move (or duplicate) the rule into the project's `.claude/CLAUDE.md`. B inverts the actual lookup order. C invents a reload command that doesn't exist. D imagines a precedence-conflict problem that the symptoms don't support.

---

## Question 2

A staff engineer is using Claude Code to add a single null-check to a 30-line helper function — clear stack trace, single file, no dependencies. They reach for plan mode out of habit. Why is this the wrong choice?

A) Plan mode requires team-lead approval — it's reserved for architectural decisions only.
B) Plan mode disables the Edit tool, forcing the engineer to use Read + Write workflows for every modification.
C) Plan mode operates on a snapshot of the codebase, so it can't see the engineer's local uncommitted changes.
D) Plan mode is designed for tasks with multiple valid approaches or architectural implications; using it on a single-file null-check adds an investigation phase that produces no design value and delays the fix.

**Correct Answer: D**

Plan mode's value is exploring tradeoffs and designing before committing to changes — for a well-scoped single-file fix with a clear stack trace, that phase is pure overhead. Direct execution is the right tool. A invents a governance gate that doesn't exist. B confuses plan mode (no writes during planning) with a permanent tool restriction. C invents a snapshot behavior; plan mode reads the live working tree.

---

## Question 3

A developer creates a `/test-coverage-gaps` slash command at `~/.claude/commands/test-coverage-gaps.md` and pushes a commit referencing the command in `CLAUDE.md`. Teammates report that running `/test-coverage-gaps` says "command not found." What's the fix?

A) Custom slash commands need a `.command` extension, not `.md` — rename the file.
B) Slash commands must be declared in a `.claude/config.json` `commands` array before they're discoverable.
C) The command file is in `~/.claude/commands/`, which is user-scoped and not shared via version control; move it to `.claude/commands/test-coverage-gaps.md` in the repo so teammates pick it up on pull.
D) The command file needs to be marked executable (`chmod +x`) before Claude Code will pick it up.

**Correct Answer: C**

Project-scoped slash commands live in `.claude/commands/` inside the repo; the developer put theirs in the user-scoped equivalent under their home directory, so only they see it. A invents an extension requirement; `.md` is correct. B describes a registration mechanism that doesn't exist — commands are auto-discovered from the directory. D imagines a Unix-permission step that doesn't apply.

---

## Question 4

The team has a `/codebase-summary` skill that explores 200+ files and emits a detailed report. Users complain that after invoking it, the rest of the Claude Code session feels sluggish and starts referencing random files brought up during the summary instead of the file they're now editing. What's the appropriate fix?

A) Lower the skill's `max_tokens` setting so it produces a shorter summary.
B) Set `context: fork` in the skill's `SKILL.md` frontmatter so the skill runs in an isolated sub-agent context and only its final summary returns to the main session.
C) Have users run `/compact` immediately after the skill finishes to reclaim context tokens.
D) Restrict the skill via `allowed-tools` so it can only call `Read`, preventing it from loading too many files at once.

**Correct Answer: B**

`context: fork` is built exactly for this — verbose discovery output stays in the sub-agent and the main session sees only the summary, so subsequent edits aren't distracted by 200 unrelated files. A shortens the output but the exploration still pollutes context as it runs. C is post-hoc and lossy — `/compact` discards detail you may have wanted. D limits what the skill can do but doesn't change where its output lands.

---

## Question 5

Test files in the codebase follow a strict convention (specific fixture helpers, naming pattern, must use the project's `assertEqualDeep` instead of plain `===`). Test files live alongside source files everywhere — e.g., `src/api/users.test.ts` next to `src/api/users.ts`. What's the cleanest way to ensure Claude Code applies the convention only when editing test files?

A) Create `.claude/rules/test-conventions.md` with YAML frontmatter `paths: ["**/*.test.ts", "**/*.test.tsx"]` so the rule loads only when a matching file is being edited.
B) Place a directory-level `CLAUDE.md` in `tests/` containing the convention.
C) Build a custom skill that wraps test-file edits and prepends the convention to every prompt the developer sends while in a test file.
D) Add a section titled "Test conventions" to the root `CLAUDE.md` with explicit file globs described in prose.

**Correct Answer: A**

Path-scoped rules in `.claude/rules/` with a `paths:` glob load only when matching files are being touched — exactly right for a convention that applies to files scattered across the codebase. B fails because tests aren't in a single `tests/` directory. C is heavy machinery for what should be a configuration file. D forces Claude to *infer* applicability from prose, which is unreliable compared to a glob-matched load.

---

## Question 6

You're asking Claude Code to refactor a custom date-format string parser. After three rounds of "no, more like this", outputs still drift on edge cases (locale separators, two-digit years, missing time components). Each round fixes one edge case while subtly breaking another. What's the most effective next step?

A) Rewrite the system prompt in more authoritative language ("You MUST handle all locale separators, you MUST preserve two-digit years…").
B) Provide 2–3 concrete input/output examples — including the edge cases that keep drifting — so Claude can pattern-match the transformation instead of inferring it from prose.
C) Switch to a higher-capability model so subtle locale handling is interpreted more reliably.
D) Break the parser into one function per format and have Claude refactor each separately to limit the surface area of each iteration.

**Correct Answer: B**

When prose descriptions are interpreted inconsistently, concrete input/output examples are the most effective way to communicate the expected transformation — the model can pattern-match, and edge cases stop ping-ponging. A is prompt-strengthening, which is probabilistic and didn't work the first three times. C throws compute at a communication problem. D is over-decomposition: the failure isn't scope, it's specification.

---

## Question 7

The project's root `CLAUDE.md` has grown to 800 lines covering style, testing, deployment, API conventions, and database conventions. Maintainers say it's unwieldy to edit, and Claude Code occasionally references rules from sections unrelated to what's being edited. How should you reorganize it?

A) Split it into one `CLAUDE.md` per top-level directory (e.g., `src/api/CLAUDE.md`, `src/db/CLAUDE.md`).
B) Move all the conventions into a single skill that loads on demand, so they're only in context when explicitly invoked.
C) Compress prose into terse bullet points to halve the line count while keeping the same coverage.
D) Split into topic-specific files in `.claude/rules/` with YAML `paths:` frontmatter so each rule loads only when its files are being edited.

**Correct Answer: D**

Path-scoped rule files give you modularity *and* conditional loading — exactly the two pain points described. A is brittle for conventions that span directories (e.g., testing standards apply to test files everywhere, not one directory). B forces opt-in invocation for what are baseline standards. C reduces volume but doesn't change *which* rules load — irrelevant sections still influence the model.

---

## Question 8

Your team is restructuring a 50-file Express monolith into per-domain microservices. There are multiple defensible service boundaries (per-feature, per-data-store, per-team) and the decision affects 6 downstream services. The engineer is reaching for direct execution. What should they do instead?

A) Direct execution with a TODO list — Claude can adapt as boundaries are discovered.
B) Open one Claude Code session per proposed boundary, run the migration in each, and pick the result that looks cleanest.
C) Use plan mode to explore the codebase, surface tradeoffs across the boundary options, and reach a design before any file is modified.
D) Spawn an Explore subagent to map dependencies, then immediately edit the 50 files in the main session.

**Correct Answer: C**

Plan mode is built for exactly this — large-scale changes with multiple valid approaches and architectural implications. Designing first avoids the costly rework that happens when dependencies are discovered mid-migration. A is what triggers the rework risk. B treats migration as a brute-force tournament and wastes effort on parallel attempts. D skips the design step — Explore maps the codebase but doesn't decide the boundary.

---

## Question 9

Your `/release-notes` skill in `.claude/skills/release-notes/SKILL.md` requires the developer to specify the previous release tag. Users frequently invoke it without an argument; Claude then has to ask "which tag?" mid-conversation, derailing their flow. What's the cleanest fix?

A) Add an `argument-hint` field to the skill's frontmatter so Claude Code prompts the developer for the required argument up front, before the skill runs.
B) Add a runtime guard in the skill body that exits early with an error message when no argument is detected.
C) Rename the skill to `/release-notes-from-tag` so the required argument is implied by the name.
D) Document the requirement in `CLAUDE.md` and rely on developers reading it before invocation.

**Correct Answer: A**

`argument-hint` in skill frontmatter is built to prompt for required parameters when the skill is invoked without them — the developer is asked once, up front, instead of being interrupted later. B works mechanically but has worse UX (after-the-fact error). C is a naming hack that doesn't actually enforce the argument. D shifts the burden to developers reading documentation they often won't.

---

## Question 10

A developer wants a `/code-review` variant with their personal style preferences (heavier emphasis on naming, looser on commenting). The team already has a project-shared `/code-review` skill in `.claude/skills/` and they don't want their preferences to affect teammates. What's the right approach?

A) Edit `.claude/skills/code-review/SKILL.md` and add a conditional that branches based on the developer's git user.email.
B) Create a personally-scoped variant in `~/.claude/skills/` with a different name (e.g., `code-review-personal`) — it's available only to that developer and doesn't affect the team.
C) Modify `.claude/skills/code-review/SKILL.md` locally and add the file to `.git/info/exclude` so the edits aren't committed.
D) Add the personal preferences to `~/.claude/CLAUDE.md` so they apply silently whenever `/code-review` runs.

**Correct Answer: B**

Personal customizations belong in user-scoped skills under `~/.claude/skills/`, with a distinct name so they don't shadow the shared skill — clean, isolated, no risk to teammates. A creates dual-mode shared config that's fragile and surprising. C creates a permanently-dirty working tree and risks accidentally committing the change. D leaks the preferences into every Claude Code session, not just code reviews — and doesn't actually customize the shared skill.

---

## Question 11

You're using Claude Code to review a 14-file PR in a single session. The output has detailed feedback for the first two files and the last file but superficial comments for the middle ones, with obvious bugs missed in the middle section. What's the underlying issue and the right fix?

A) The diff is too large for the model's context window — switch to a higher-context model and re-run.
B) Claude is being rate-limited mid-review; increase `max_tokens` so it has room to write longer feedback per file.
C) Auto-`/compact` is running partway through and dropping the middle context — disable auto-compact for review sessions.
D) Long inputs suffer attention dilution (the "lost in the middle" effect); split the review into per-file passes for local issues, plus a separate cross-file integration pass.

**Correct Answer: D**

Models reliably attend to the beginning and end of long inputs but can underweight the middle — this matches the observed symptom exactly. Per-file passes give each file uniform attention; an integration pass catches cross-file issues that single-file passes would miss. A misreads the symptom as a size problem rather than an attention problem. B confuses `max_tokens` (output length cap) with input attention. C invents an auto-compact behavior.

---

## Question 12

You're migrating a project from Jest to Vitest. About 45 files are affected. Most changes are mechanical (import paths, syntax tweaks), but a handful of test files use Jest-specific globals that have no direct Vitest equivalent and need case-by-case decisions. What's the most effective workflow?

A) Use plan mode to investigate the codebase, decide on a strategy for the Jest-specific globals, and design the migration approach — then switch to direct execution to apply the planned changes.
B) Direct execution end-to-end — open each file, decide on the spot how to handle it, and repeat 45 times.
C) Plan mode end-to-end — never leave plan mode so every file modification gets a documented design step.
D) Spawn 45 parallel Explore subagents, one per file, and synthesize their findings into a single batch edit.

**Correct Answer: A**

Combining plan mode for investigation with direct execution for implementation is the documented pattern: design the tricky parts (the Jest-specific globals strategy) before committing to changes, then apply the planned mechanical edits efficiently. B risks inconsistent treatment of the globals because there's no upfront strategy. C wastes time on routine, low-ambiguity mechanical edits. D over-uses Explore (which is for verbose discovery) and skips the human design step the globals require.

---

## Question 13

You're asking Claude Code to implement a CSV-to-Markdown converter. The first attempt handles simple inputs but fails on edge cases (empty cells, embedded commas inside quoted strings, multiline cells). You've described the failures in prose three times and Claude keeps "fixing" one edge case while reintroducing another. What's the most effective next step?

A) Write a single comprehensive prose description listing every edge case in priority order, then paste it as one message.
B) Run a tighter loop — paste each failing case individually as soon as you spot it, rather than batching them.
C) Write a test suite covering each edge case, share the failing test output with Claude, and iterate by sharing test failures until all pass.
D) Reset the conversation and start over with a clean context so previous wrong implementations don't bias the next attempt.

**Correct Answer: C**

Test-driven iteration is the most effective pattern for edge-case work: tests pin down the desired behavior precisely, and shared failure output gives Claude unambiguous signal about exactly what broke. A is more of the prose specification that's already failing. B is essentially what's already happening — and doesn't fix the regression problem where each fix breaks the previous one. D abandons useful context to dodge the underlying specification problem.

---

## Question 14

A developer is confused: a `CLAUDE.md` instruction ("use double quotes, never single") is being followed in some Claude Code sessions but not others, on the same project. They suspect the file isn't loading consistently. What's the most direct way to confirm?

A) Add a debug marker like `// CLAUDE_MD_LOADED` to the top of `CLAUDE.md` and ask each session whether it sees the marker.
B) Run the `/memory` command in each session to see exactly which memory files are loaded; compare across sessions to diagnose the inconsistency.
C) Check `~/.claude/logs/session-init.log` for a "loaded CLAUDE.md" entry in the sessions where the rule fires.
D) Reinstall Claude Code to reset any cached state that might be skipping the file on some sessions.

**Correct Answer: B**

`/memory` is the built-in introspection command for this — it lists the memory files currently in context, which is exactly the information needed to confirm whether `CLAUDE.md` was loaded. A is a hacky workaround that depends on Claude echoing the marker. C invents a log path that doesn't exist. D is a reach-for-the-nuke when a one-command diagnostic is available.

---

## Question 15

Two weeks ago you ran a named Claude Code session that mapped your authentication flow across 30 files. Since then half of those files have been refactored. You want to continue the original investigation. Should you `--resume` that session?

A) Yes — `--resume` reattaches you to the original context, which is the fastest way to pick back up.
B) Yes, but pass `--refresh` first so Claude re-reads each previously analyzed file from disk before continuing.
C) Yes, but immediately follow up with `/compact` to reduce the resumed context to a summary before adding any new questions.
D) No — the prior tool results referencing those 30 files are now stale; start a new session and inject a structured summary of the previous findings into the initial prompt.

**Correct Answer: D**

Resuming pulls in tool results that no longer match the current code; the agent will reason from outdated file contents and give incorrect answers. The documented pattern is to start fresh with a structured summary when prior tool results are stale. A treats `--resume` as universally safe. B invents a `--refresh` flag. C reduces context volume but does nothing about the staleness of what remains.

---

## Question 16

You're investigating "where is the rate-limiting logic implemented in this codebase?" and the main Claude Code session is producing 40+ Read calls' worth of file contents in the conversation. You're worried about context exhaustion before you can ask the actual question you're aiming at. What should you do?

A) Spawn an Explore subagent for the discovery phase — it isolates the verbose file-reading in its own sub-context and returns a summary to the main session, preserving main-session context.
B) Continue in the main session but run `/compact` every 10 file reads to keep the context bounded.
C) Lower `max_tokens` so each Read call returns less content, slowing the accumulation rate.
D) Switch to a 1M-token context window model so the verbose reads fit comfortably.

**Correct Answer: A**

Explore is built for exactly this — isolate verbose discovery in a sub-agent so the main session keeps its budget for the question you actually want to ask. B is a band-aid that loses detail you may need later. C confuses Read's behavior (Read returns the file's content; `max_tokens` doesn't truncate that). D defers the problem; the same exploration pattern will eventually crowd out a million-token window too.

---

## Question 17

You're asking Claude Code to implement a cache invalidation layer in a part of the codebase you're not deeply familiar with. The first implementation looks plausible, but you can't tell if Claude has thought through the failure modes (stale reads, write-through ordering, cache stampedes, eviction race conditions). What's the most effective next step?

A) Deploy the implementation behind a feature flag to a canary environment and observe production traffic to surface issues empirically.
B) Ask Claude to write extensive comments explaining every line, so you can audit the reasoning step by step.
C) Ask Claude to interview you with clarifying questions about your cache-invalidation strategy and the failure modes you care about, then refine the implementation based on your answers.
D) Generate three independent implementations and pick the one with the most defensive guards (retries, locks, fallbacks).

**Correct Answer: C**

The interview pattern — having Claude ask questions before implementing — surfaces design considerations you may not have anticipated and forces both sides to be explicit about constraints. A externalizes risk to production for a problem you can solve in the editor. B confuses comment volume with reasoning quality; you'd be auditing prose, not architecture. D treats "most guards" as a proxy for correctness, which it isn't.

---

## Question 18

Your codebase has Terraform files in `infra/aws/`, `infra/gcp/`, and `infra/legacy/`, and SQL migration files (`*.sql`) scattered across multiple service directories. You want one strict naming convention applied to every Terraform file regardless of cloud directory, and a separate convention for migration files regardless of where they live. What's the most maintainable approach?

A) A single `infra/CLAUDE.md` covering both Terraform and the cloud-specific quirks, with the migration convention duplicated into each service's CLAUDE.md.
B) `.claude/rules/terraform.md` with frontmatter `paths: ["**/*.tf", "**/*.tfvars"]` and `.claude/rules/migrations.md` with `paths: ["**/migrations/**/*.sql"]` — each rule loads only when its files are touched.
C) A combined `.claude/commands/check-conventions.md` slash command that developers run manually before each commit.
D) Three subdirectory `CLAUDE.md` files — one in each `infra/<cloud>/` — duplicating the shared Terraform convention.

**Correct Answer: B**

Path-scoped rules in `.claude/rules/` apply by glob, which cleanly handles both cases: Terraform rules trigger on `.tf` files anywhere; migration rules trigger on `.sql` files in any `migrations/` directory. A doesn't cover SQL files outside `infra/` and forces duplication. C makes enforcement opt-in via a manual command. D duplicates the Terraform rule across three locations and doesn't address SQL migrations at all.

---

## Question 19

You're three hours into a single Claude Code session exploring an unfamiliar Python data pipeline. Claude has started giving inconsistent answers about which class implements the deduplication logic — sometimes specifically naming `BatchDeduplicator`, sometimes referring vaguely to "the typical deduplication class for this pattern." What's happening, and what's the appropriate fix?

A) The session has hit "temperature drift" — restart Claude Code with `--temperature 0` to force consistent responses.
B) Follow-up questions have biased the context — start a fresh session and ask the deduplication question more precisely.
C) The session has silently downgraded to a smaller model after some threshold — explicitly select the larger model for the rest of the session.
D) Context has degraded over the long session, so the model now references "typical patterns" instead of the specifics it discovered earlier; have Claude maintain a scratchpad file recording key findings and reference that file for subsequent questions.

**Correct Answer: D**

Long sessions are prone to context degradation: specifics that were discovered earlier get diluted, and the model falls back on generic patterns. Scratchpad files persist those specifics across the context boundary and counteract the drift. A invents a "temperature drift" concept that doesn't exist. B blames your inputs rather than the underlying context capacity issue. C invents an auto-downgrade behavior.

---

## Question 20

You want every Claude Code session to apply your team's logging convention automatically: every log line must include a request ID and a structured `event` field. You're deciding where the convention should live: a slash command, a skill, or always-loaded memory. Which is the right home, and why?

A) Make it a slash command — developers explicitly opt in when they care about logging.
B) Make it a skill with `context: fork` — it runs in isolation when invoked and doesn't pollute the main context.
C) Put it in `CLAUDE.md` (or a path-scoped rule for files that emit logs) — it's an always-loaded universal standard, not an on-demand workflow.
D) Put it in `.claude/settings.json` under an `instructions` array so it's enforced at the tool layer rather than the model layer.

**Correct Answer: C**

Skills are on-demand workflows; CLAUDE.md (and `.claude/rules/`) hold always-loaded universal standards. A logging convention that must apply on *every* edit fits the second category. A makes opt-in something that should be default. B isolates the convention from the main session — the opposite of what you want. D invents a settings.json mechanism; instructions live in CLAUDE.md, not settings.

---

## Answer Key

| # | Answer | # | Answer | # | Answer | # | Answer |
|---|--------|---|--------|---|--------|---|--------|
| 1 | A | 6 | B | 11 | D | 16 | A |
| 2 | D | 7 | D | 12 | A | 17 | C |
| 3 | C | 8 | C | 13 | C | 18 | B |
| 4 | B | 9 | A | 14 | B | 19 | D |
| 5 | A | 10 | B | 15 | D | 20 | C |

Distribution: A × 5, B × 5, C × 5, D × 5.
