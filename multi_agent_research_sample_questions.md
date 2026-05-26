# CCAF Sample Questions: Multi-Agent Research System

Twenty practice questions in the format of the *Claude Certified Architect – Foundations* exam guide, all set within the **Multi-Agent Research System** scenario.

**Scenario recap:** A coordinator agent built on the Claude Agent SDK delegates work to specialized subagents — web search, document analysis, synthesis, and report generation — to produce cited, multi-source research reports. Subagents have role-scoped tools (`web_search`, `fetch_url`, `extract_content`, `plan_research`, report-generation tools) and the system must hit a target of correctly-cited reports without drift on long, complex queries.

**Primary domains:** Agentic Architecture & Orchestration, Tool Design & MCP Integration, Context Management & Reliability.

---

## Question 1

A single Claude agent currently handles each research query end-to-end: web search, document parsing, synthesis, and report drafting all in one context. On complex multi-source queries (e.g., "compare regulatory frameworks for digital assets across six jurisdictions") the agent loses focus mid-task, mixes citations between jurisdictions, and produces inconsistent reports. The team is deciding whether to refactor into a coordinator with specialized subagents. What is the primary architectural benefit?

A) Each specialized subagent runs in its own context window with role-specific instructions, preventing cross-task confusion and letting the coordinator orchestrate independent work in parallel.
B) Subagents are cheaper because each one can use a smaller model.
C) Subagents share a single context window so the coordinator sees every tool call in real time.
D) Splitting work across subagents always lowers latency on every query, regardless of structure.

**Correct Answer: A**

The defining property of the coordinator/subagent pattern is *context isolation with role specialization*: each subagent reasons within a clean, focused context bounded by its job, and the coordinator composes their outputs. B may be true situationally but is not the *primary* benefit, and is over-stated as a rule. C describes the opposite of what subagents provide — they specifically avoid sharing full conversation context. D is too strong: parallelism only helps when subtasks are independent; serial chains may not benefit at all.

---

## Question 2

For a query like "compile a market overview of three competing payment platforms," the coordinator currently dispatches one research subagent at a time and takes ~90 seconds per platform serially. The three platforms are independent of one another. What is the right architectural change?

A) Increase `max_tokens` on each subagent so they finish faster.
B) Dispatch three research subagents in parallel — one per platform — then have the coordinator synthesize their outputs once all return.
C) Combine all three platforms into a single subagent call so it can compare them as it researches.
D) Switch to a faster model and keep the calls serial.

**Correct Answer: B**

Parallel dispatch is the canonical pattern when subtasks are independent — total wall-clock time approaches the slowest single subagent rather than the sum of all three. A confuses `max_tokens` (an output-length cap) with throughput; it doesn't make work finish sooner. C collapses the specialization the architecture was designed around and overloads a single context with three platforms of source material. D addresses a symptom (raw model speed) rather than the structural inefficiency of serial scheduling.

---

## Question 3

The synthesis subagent has access to `web_search`, `fetch_url`, `extract_content`, `parse_pdf`, plus the report-generation tools. Logs show it frequently re-runs `web_search` at synthesis time instead of working from the structured findings the research subagent already gathered. What is the most effective fix?

A) Add a system-prompt instruction telling the synthesis subagent to "rely on the research output and not call search tools."
B) Add a `PreToolUse` hook that throws an error whenever the synthesis subagent attempts `web_search` or `fetch_url`.
C) Scope the synthesis subagent to only the tools it actually needs (report-generation tools), removing the search/fetch tools from its tool list entirely.
D) Add few-shot examples in the prompt showing the synthesis subagent ignoring search tools.

**Correct Answer: C**

The architectural fix is to scope each subagent's tool list to its role — the synthesis subagent doesn't need search tools at all, so they shouldn't be in its toolset. Tool availability is the strongest signal for tool selection; removing irrelevant tools eliminates the bad choice deterministically and at configuration time. A and D are probabilistic prompt-based mitigations that the model can ignore. B works but adds runtime complexity to enforce something that can be eliminated up front by not exposing the tool in the first place.

---

## Question 4

The report-generation subagent occasionally drops citation tags when stitching together long reports, leading downstream auditors to flag uncited claims. Strengthening the system prompt to "always cite every claim" has reduced but not eliminated the problem. What is the most reliable fix?

A) Add a few-shot example demonstrating correct citation format.
B) Lower the model temperature so the format is followed more deterministically.
C) Have the coordinator agent review every paragraph and add missing citations.
D) Add a post-processing hook that scans the report for uncited claims and either re-prompts the subagent on the offending paragraphs or fails the run.

**Correct Answer: D**

Citation completeness is a hard contract — it requires programmatic enforcement, not probabilistic instruction-following. A post-processing hook deterministically verifies the contract and can either trigger targeted re-generation or fail loudly. A and B are probabilistic mitigations of the same class the team has already found insufficient. C is appealing but the coordinator is also an LLM and has the same probabilistic failure mode the original prompt does; it does not provide a guarantee.

---

## Question 5

A multi-hour research run for a 50-page report accumulates 200K+ tokens of tool results, search snippets, and intermediate subagent outputs in the coordinator's conversation history. The coordinator starts losing track of which sources have already been gathered and dispatches duplicate research subagents on topics it already covered. What is the cleanest fix?

A) Persist gathered findings (sources, key facts, citations) to an external structured store and have the coordinator read from that store rather than relying on conversation history.
B) Have the coordinator summarize the full context every 10 turns to compress history.
C) Move to a model with a 1M-token context window and keep all outputs verbatim in the prompt.
D) Cap each research run at 100K tokens and abort if it exceeds the cap.

**Correct Answer: A**

Progress tracking on a long-running workflow should be externalized to a structured store of record, not encoded implicitly in a growing conversation history. Once findings are persisted, the coordinator queries the store deterministically to see what is already done. B trades one problem (size) for another: progressive summarization reliably loses precise source-level detail, which is exactly what's needed to deduplicate. C delays the problem rather than solving it; lost-in-the-middle attention degradation still applies at any context size. D imposes an arbitrary ceiling that truncates legitimate work without addressing the underlying coupling.

---

## Question 6

The web-search subagent currently returns the full HTML of every page it fetches (~30KB each). After about a dozen pages, the coordinator's context window is nearly full and the subagent's downstream reasoning degrades. What is the best tool-design change?

A) Switch to a model with a larger context window so more pages fit.
B) Have the research subagent return only structured extracts (URL, title, relevant passages, publication date) and persist the full content to a referenced store that downstream subagents can fetch on demand.
C) Limit `web_search` to one result per query.
D) Compress the HTML with gzip before adding it to context.

**Correct Answer: B**

Tool outputs should be trimmed to the *relevant* fields before entering context; full source material can be persisted to a content store and fetched on demand by ID. A delays the problem and dilutes attention with irrelevant fields. C artificially restricts research breadth, harming output quality. D doesn't help: the model still consumes the decompressed tokens — compression saves transport bytes, not context tokens.

---

## Question 7

The final report must include citations in the form `[1]`, `[2]`, … keyed to a references list at the end. The team is deciding between two output formats: (i) freeform markdown that downstream code parses for citations, or (ii) structured JSON with separate `claims` and `references` arrays validated against a JSON Schema. Which is more reliable for a production research system?

A) Freeform markdown, because Claude is more fluent in prose than in structured output.
B) JSON with no schema definition, letting the model decide structure per report.
C) Structured JSON with an explicit schema (`claims: [{text, refs}]`, `references: [{id, title, url}]`) validated against a JSON Schema, then rendered to markdown by deterministic code.
D) A custom DSL the team invents specifically for citations.

**Correct Answer: C**

An explicit schema plus validation gives a deterministic structural contract: malformed outputs are caught at parse time, and rendering is a non-LLM problem owned by deterministic code. A makes citations an exercise in regex-parsing prose, which is fragile and silently fails. B (schema-less JSON) still varies between runs — the model may emit different key names, nest things differently, or drop the references array. D reinvents what JSON Schema already provides, with no ecosystem tooling.

---

## Question 8

For a query like "find recent academic papers on diffusion models AND summarize the top 5 most-cited," the coordinator currently writes one large prompt to a single research subagent. The subagent partially completes both subtasks but inconsistently — sometimes returning a list of papers with no summaries, sometimes summaries of papers it never explicitly listed. What is the right delegation pattern?

A) Repeat the same prompt to the same subagent until both subtasks complete.
B) Add more emphatic instructions to the subagent prompt ("you MUST do BOTH parts").
C) Move both subtasks into the coordinator itself and skip the subagent.
D) Decompose into two clearly-bounded subagent calls — a search subagent that returns the candidate paper list, then a summarization subagent given the top 5 — and have the coordinator chain them.

**Correct Answer: D**

Each subagent should have one clearly-bounded responsibility; the coordinator chains them in the order their dependencies require. Single-responsibility subagents have higher reliability and easier-to-debug outputs. A retries the structurally flawed prompt and produces the same inconsistency. B is probabilistic — the team has already seen prompt strengthening fail. C collapses specialization back into a single overloaded context, which is exactly what the architecture exists to avoid.

---

## Question 9

A research subagent's loop sometimes terminates prematurely. On inspection, the loop ends whenever the assistant message contains "I have completed my research." Occasionally it ends while the subagent still intends to call `fetch_url`. How should the loop's termination be controlled?

A) Drive termination off the API's `stop_reason` — continue the loop while it is `"tool_use"` and end when it is `"end_turn"`.
B) Tighten the regex on completion phrases to catch more variations.
C) Cap the loop at 8 iterations regardless of state so it always terminates predictably.
D) Have the subagent emit a structured `<DONE>` block in its message and parse for it.

**Correct Answer: A**

The agentic loop's stop signal is `stop_reason`: `"tool_use"` means the model wants to execute a tool and the loop must continue; `"end_turn"` means it has finished. B is the same anti-pattern with a fancier regex — assistant text is not a reliable completion signal. C is a safety backstop, not a primary termination mechanism, and will mask bugs by silently truncating valid work. D still relies on parsing assistant text and shares A's failure mode without the API-supported reliability.

---

## Question 10

The team wants to keep each subagent's context "clean" so that a long, messy web-search session in the research subagent does not pollute the synthesis subagent's reasoning. How does the Claude Agent SDK's subagent model achieve this?

A) Subagents share their full conversation history with the coordinator after every step.
B) Each subagent runs in its own isolated context window, and only the subagent's *final output* is returned to the coordinator — not the intermediate tool calls or message history.
C) Subagents stream their full conversation to the coordinator in real time so the coordinator can intervene mid-task.
D) Subagents and the coordinator always operate over a single shared global context.

**Correct Answer: B**

Subagent isolation means each subagent has its own context window; the coordinator sees only the final, summarized output the subagent returns, not every intermediate search result or scratchpad message. This is the property that lets a noisy research session feed a clean synthesis session. A, C, and D all describe shared-context models, which are precisely what the subagent pattern is designed to avoid.

---

## Question 11

Dispatching six research subagents in parallel completes a complex query in ~25 seconds but costs roughly 6× a serial single-agent run. The product team wants to keep parallelism only where it actually matters. What is the right architectural choice?

A) Always run subagents in parallel and accept the cost.
B) Always run subagents serially and accept the latency.
C) Have the coordinator decide per-query: parallelize when subtasks are independent and latency-sensitive; serialize when they are dependent or cost-sensitive.
D) Use a fixed parallelism factor of 3 across all queries regardless of subtask structure.

**Correct Answer: C**

Concurrency should be a per-query decision driven by subtask dependency structure and the query's latency/cost profile. The coordinator already has the planning context to make that call. A and B are extremes that pick one axis at the expense of the other. D is a fixed compromise that ignores actual subtask structure — independent 8-way work gets under-parallelized while sequential chains get pointlessly parallelized.

---

## Question 12

The `fetch_url` tool currently returns the string `"Operation failed"` when a target site times out, blocks crawlers, or returns 404. The research subagent retries every failure identically and frequently loops on permanent failures. How should the tool's error response be structured?

A) Return an empty document so the subagent moves on.
B) Crash the subagent process so the failure is loudly surfaced.
C) Return a generic `"failed — please try again"` string to encourage retries.
D) Return a structured error with `errorCategory` (timeout / blocked / not_found / parse_error), an `isRetryable` boolean, and a human-readable description so the subagent can decide whether to retry, try a different source, or skip.

**Correct Answer: D**

Structured, categorized errors let the agent make recovery decisions appropriate to the failure mode — retry transient errors, abandon permanent ones, and skip cleanly without polluting the report. A silently turns a failure into a misleading empty result. B removes any chance of graceful recovery and aborts upstream work. C is the current behavior with friendlier wording; it causes exactly the wasted-retry loop described.

---

## Question 13

The synthesis subagent receives one large prompt containing 40+ source snippets in chronological retrieval order. The final report consistently over-weights the first 5 and last 5 sources and effectively ignores the middle 30. What is the best mitigation?

A) Restructure the input so each source has a stable ID, and instruct the model to produce a coverage matrix (claim → source IDs) — turning "use all middle sources" into an explicit, structured task.
B) Sort all sources alphabetically before feeding them in.
C) Place the most important sources at the beginning and end of the prompt, deprioritizing the middle entirely.
D) Repeat the middle sources twice in the prompt.

**Correct Answer: A**

Lost-in-the-middle is an attention phenomenon: middle content gets less weight in long prompts. The structural mitigation is to make coverage an explicit *task* — a coverage matrix forces the model to address every source ID, turning recall into a checked output. B reorders without addressing attention. C accepts the bias rather than mitigating it and discards content the report needs. D adds noise (duplicate tokens) without changing the fundamental attention distribution and bloats the context.

---

## Question 14

A new `research_topic` tool currently bundles web search, URL fetching, content extraction, and summarization into one tool call. Logs show the subagent often can't tell *why* the tool failed (was it search? fetch? extraction?), so it either retries blindly or gives up. What is the right tool decomposition?

A) Bundle even more steps into `research_topic` so the agent treats it as a black box.
B) Split into atomic tools (`web_search`, `fetch_url`, `extract_content`) so failures are localized and the agent can retry or substitute steps individually.
C) Keep the bundled tool and append a "what went wrong" string to its error response.
D) Always have the coordinator call `research_topic` exactly once per query.

**Correct Answer: B**

Tools should follow single-responsibility design: each does one thing, fails for one reason, and can be retried or substituted independently. The agent gains the ability to retry just the failed step or swap sources. A makes the opacity worse. C improves the error message but the agent still cannot act on substep granularity — it cannot retry just the extraction step if only that failed. D is unrelated to the failure-localization problem.

---

## Question 15

A 25-minute research workflow occasionally crashes near the end — e.g., a synthesis subagent times out — discarding all upstream work. What is the right design?

A) Add a try/except around the entire workflow and retry from the beginning on any failure.
B) Increase the subagent timeout so synthesis never times out.
C) Persist subagent outputs (findings, citations, partial drafts) to durable storage after each successful step so the workflow can resume from the last checkpoint.
D) Run the workflow on a more powerful machine so it is less likely to be interrupted.

**Correct Answer: C**

Long-running workflows need durable checkpointing — each completed step writes its output, and the workflow resumes from the last good checkpoint on failure. This makes 25 minutes of upstream work recoverable. A throws away successful work and retries from zero, wasting time and money. B addresses one specific failure mode (timeouts) while leaving every other crash class destructive. D treats reliability as a hardware problem rather than a state-management one and provides no recovery when a failure does happen.

---

## Question 16

A user asks the system to "research X and email a summary to the team." The coordinator has research tools but no email tool. Which is the right behavior?

A) Have the coordinator simulate sending an email by writing one to its scratchpad and claim success.
B) Have the coordinator return a fabricated confirmation that the email was sent.
C) Refuse to engage with the request because part of it cannot be fulfilled.
D) Complete the research portion, return the summary, and explicitly tell the user that emailing is outside the agent's current capabilities.

**Correct Answer: D**

The agent should complete what it can, return concrete value, and clearly state the gap — partial honest fulfillment is better than full failure or fabricated success. A and B both hallucinate capabilities the agent does not have; B is the worst outcome because the user believes work was done that wasn't. C abandons the resolvable portion (the research) over a missing capability that the user can be told about and addressed separately.

---

## Question 17

You need a hard guarantee that every claim in the final report traces to a URL that `fetch_url` actually retrieved successfully during the run — no hallucinated sources. What is the most reliable enforcement?

A) Validate at report-generation time that every cited URL in the final report appears in a deterministic registry of URLs `fetch_url` actually returned successfully during the run; reject the report if any citation is unverifiable.
B) Add a system-prompt rule: "Only cite URLs you have fetched."
C) Have a second Claude call review the report and remove any uncited or hallucinated URLs.
D) Use a larger model so it hallucinates fewer URLs.

**Correct Answer: A**

A guarantee requires deterministic validation against an authoritative source of truth — here, the registry of URLs that `fetch_url` returned during the run. Any cited URL not in the registry is rejected, no probabilistic step required. B is a prompt rule the model can violate. C is a probabilistic LLM judge that has the same hallucination failure mode as the generator and offers no guarantee. D reduces the rate of hallucination but does not eliminate it, so it does not meet the "hard guarantee" requirement.

---

## Question 18

A user asks the system "what is the capital of France?" The coordinator currently dispatches a full research subagent (web search + fetch + summarize), taking ~12 seconds and 4 tool calls. What is the right design?

A) Always dispatch research subagents for every query for behavioral consistency.
B) Let the coordinator answer simple factual queries directly from its own knowledge and reserve subagent dispatch for queries that genuinely require external sources or specialized work.
C) Dispatch *more* subagents in parallel for trivial queries as a stress test of the system.
D) Always require web search regardless of query type, to avoid relying on potentially-outdated model knowledge.

**Correct Answer: B**

Delegation overhead should match query complexity: simple, stable facts are best answered directly; multi-source, time-sensitive, or specialized queries justify subagent dispatch. A and C apply expensive machinery to trivial work for no benefit. D is the closest competing answer — fresh-fact concerns are real — but blanket-required web search ignores that stable facts ("capital of France") do not change between training cutoffs, and the principle is to route by *volatility and complexity*, not to apply a single rule to every query.

---

## Question 19

The research subagent's system prompt currently reads, in full: "You are a helpful assistant." Logs show it often drifts off task — sometimes drafting partial prose instead of returning structured findings. What is the most effective change?

A) Replace "helpful assistant" with "expert researcher with 20 years of experience in academic search."
B) Remove the system prompt entirely.
C) Replace it with a role-specific prompt that defines the subagent's job (gather and return structured findings, not draft prose), the expected output schema, what it should *not* do (no narrative writing), and how it indicates "no further sources needed."
D) Move all instructions into the user message instead.

**Correct Answer: C**

Subagent prompts should be role-specialized: explicit job description, output contract, out-of-scope guidance, and a defined "I'm done" signal. This directly addresses the observed drift. A swaps one generic persona for another and does not constrain output shape. B removes the only guidance the subagent has. D changes the *location* of instructions, not their *content* — the problem is what the instructions say, not which message role carries them.

---

## Question 20

At the start of every research run, the coordinator should always call the `plan_research` tool first to produce a structured research plan before dispatching any subagents. In practice it sometimes skips this and dispatches subagents immediately. What is the most reliable way to enforce this on the first turn?

A) Add an emphatic instruction in the system prompt: "ALWAYS call `plan_research` first."
B) Set `tool_choice: "auto"` and rely on the model to choose correctly.
C) Set `tool_choice: "any"` to force *some* tool call on the first turn.
D) Set `tool_choice: {"type": "tool", "name": "plan_research"}` for the first turn, then switch to `"auto"` after the plan exists.

**Correct Answer: D**

Forced-tool selection pins the model to a specific tool deterministically — exactly what's needed when one specific call must happen first. A is probabilistic and the team has already seen the prompt instruction fail. B is the current behavior that produced the bug. C is the closest competing answer because it forces a tool call, but it lets the model pick *which* tool — the coordinator could still skip `plan_research` and call something else first.

---

## Answer Key

| # | Answer | # | Answer | # | Answer | # | Answer |
|---|--------|---|--------|---|--------|---|--------|
| 1 | A | 6 | B | 11 | C | 16 | D |
| 2 | B | 7 | C | 12 | D | 17 | A |
| 3 | C | 8 | D | 13 | A | 18 | B |
| 4 | D | 9 | A | 14 | B | 19 | C |
| 5 | A | 10 | B | 15 | C | 20 | D |

Distribution: A × 5, B × 5, C × 5, D × 5.
