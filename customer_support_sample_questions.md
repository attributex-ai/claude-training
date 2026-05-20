# CCAF Sample Questions: Customer Support Resolution Agent

Twenty practice questions in the format of the *Claude Certified Architect – Foundations* exam guide, all set within the **Customer Support Resolution Agent** scenario.

**Scenario recap:** An agent built on the Claude Agent SDK handles high-ambiguity requests like returns, billing disputes, and account issues. It has access to backend systems through custom MCP tools (`get_customer`, `lookup_order`, `process_refund`, `escalate_to_human`). The target is 80%+ first-contact resolution while knowing when to escalate.

**Primary domains:** Agentic Architecture & Orchestration, Tool Design & MCP Integration, Context Management & Reliability.

---

## Question 1

Your agentic loop currently terminates when Claude's response contains phrases like "I've resolved this" or "Is there anything else?" Occasionally the loop ends while Claude still intends to call `process_refund`, leaving refunds unprocessed. What is the correct way to control loop termination?

A) Add a regular expression that matches a wider set of completion phrases in the assistant's text.
B) Continue the loop while `stop_reason` is `"tool_use"` and terminate when `stop_reason` is `"end_turn"`.
C) Set a maximum iteration cap of 10 turns so the loop always terminates predictably.
D) Ask Claude to emit a special `[DONE]` token and terminate when that token appears.

**Correct Answer: B**

The agentic loop should be driven by the API's `stop_reason` field: `"tool_use"` means Claude wants to execute a tool and the loop must continue, while `"end_turn"` means Claude has finished. Parsing natural-language signals (A, D) is an anti-pattern — assistant text is not a reliable completion indicator, which is exactly the bug described. An iteration cap (C) is a safety backstop, not a primary stopping mechanism, and would either truncate valid work or mask the real problem.

---

## Question 2

Production data shows the agent sometimes calls `process_refund` before `get_customer` has run, processing refunds against unverified accounts. The team has already tried strengthening the system prompt. What is the most reliable fix?

A) Lower the model temperature so the agent follows the prompt more deterministically.
B) Add more emphatic language to the system prompt ("You MUST ALWAYS verify identity FIRST").
C) Add a few-shot example showing the correct ordering once at the top of the prompt.
D) Implement a tool-call interception hook that blocks `process_refund` until `get_customer` has returned a verified customer ID.

**Correct Answer: D**

Identity verification before a financial operation is a business rule requiring deterministic compliance. Programmatic enforcement via a hook guarantees the prerequisite, whereas prompt-based approaches (B, C) have a non-zero failure rate — and the team already found prompting insufficient. Temperature (A) does not guarantee ordering and is not a compliance mechanism.

---

## Question 3

`get_customer` and `process_refund` both have one-line descriptions. The agent occasionally calls `process_refund` when a customer merely *asks about* refund eligibility. What is the most effective first step?

A) Expand each tool's description to specify its purpose, expected inputs, side effects, and when to use it versus alternatives.
B) Remove `process_refund` from the agent and have a human run all refunds.
C) Add a confirmation step where the agent asks the user "Should I proceed?" before every tool call.
D) Rename `process_refund` to `refund` so it is shorter and easier to select.

**Correct Answer: A**

Tool descriptions are the primary mechanism the model uses for tool selection; minimal descriptions leave the model unable to distinguish a read-only inquiry from a state-changing action. Expanding the description — especially noting that `process_refund` *executes* a refund — directly addresses the root cause. Removing the tool (B) defeats the automation goal. A blanket confirmation step (C) is heavy-handed and doesn't fix selection. Renaming for brevity (D) does nothing to clarify behavior.

---

## Question 4

When `lookup_order` cannot reach the order database, it currently returns the string `"Operation failed"`. The agent then either retries forever or gives up entirely. How should the tool's failure response be designed?

A) Return an empty order list so the agent treats it as "no orders found."
B) Raise an exception that crashes the agent session so the failure is visible.
C) Return a structured error with `errorCategory` (transient/validation/permission), an `isRetryable` boolean, and a human-readable description.
D) Return `"Operation failed — please try again"` so the agent always retries.

**Correct Answer: C**

Structured error metadata lets the agent make appropriate recovery decisions: retry transient errors, stop retrying non-retryable ones, and explain the situation to the customer. Returning empty results (A) silently misrepresents a failure as a valid empty result. Crashing the session (B) prevents any recovery. A generic "try again" string (D) causes wasted retries on permanent failures.

---

## Question 5

The agent achieves 58% first-contact resolution. Logs show it escalates routine cases (standard returns with photo evidence) while autonomously attempting cases requiring policy exceptions. What is the most effective way to improve escalation calibration?

A) Have the agent output a 1–10 confidence score and escalate everything below 7.
B) Add explicit escalation criteria to the system prompt with few-shot examples showing when to escalate versus resolve.
C) Escalate every case to a human and have the agent only draft suggested replies.
D) Run sentiment analysis and escalate whenever customer frustration is detected.

**Correct Answer: B**

The root cause is unclear decision boundaries; explicit criteria plus few-shot examples directly address it and is the proportionate first step. Self-reported confidence (A) is poorly calibrated — the agent is already wrongly confident on hard cases. Escalating everything (C) abandons the resolution target. Sentiment (D) is an unreliable proxy: frustration does not correlate with case complexity.

---

## Question 6

A customer's first message is "I want to speak to a human right now." The agent responds by calling `get_customer` and `lookup_order` to investigate before escalating. What should the agent do instead?

A) Honor the explicit request and call `escalate_to_human` immediately, without first investigating.
B) Investigate fully so the human agent has complete context before handoff.
C) Attempt to resolve the issue itself and escalate only if it cannot.
D) Ask the customer three qualifying questions to decide whether escalation is warranted.

**Correct Answer: A**

An explicit customer request for a human is a primary escalation trigger and should be honored immediately. Investigating first (B) ignores the stated preference and adds friction. Attempting resolution anyway (C) overrides the customer's explicit choice. Interrogating the customer (D) does the same while adding more friction. Note: compiling a structured handoff summary is still appropriate — but escalation should not be *delayed* by investigation the customer didn't ask for.

---

## Question 7

In long billing-dispute conversations, the agent's progressive summarization condenses "$47.50 charged twice on March 3" into "customer had a billing concern," and the agent later quotes the wrong refund amount. What is the best fix?

A) Disable summarization entirely and always send the full raw transcript.
B) Instruct the model to "never forget important numbers" in the system prompt.
C) Summarize more aggressively so less context competes for the model's attention.
D) Extract transactional facts (amounts, dates, order numbers, statuses) into a persistent "case facts" block included in every prompt, outside the summarized history.

**Correct Answer: D**

Progressive summarization reliably loses precise numerical and transactional detail. Pinning those facts in a persistent structured block, separate from summarized prose, preserves them regardless of how history is compressed. Sending the full transcript (A) does not scale and reintroduces lost-in-the-middle risk. A prompt instruction (B) cannot reliably counteract summarization that happens outside the model's control. Aggressive summarization (C) worsens the problem.

---

## Question 8

Each `lookup_order` call returns 40+ fields (warehouse codes, carrier metadata, internal flags), but only ~5 are relevant to a return. Over a long session these outputs accumulate and crowd the context window. What should you do?

A) Increase `max_tokens` so there is room for the full outputs.
B) Summarize the entire conversation more often to reclaim space.
C) Trim the tool output to only the return-relevant fields before it enters conversation context.
D) Switch to a model with a larger context window and keep the full outputs.

**Correct Answer: C**

Tool results accumulate and consume tokens disproportionately to their relevance; trimming verbose outputs to the relevant fields before they enter context is the targeted fix. `max_tokens` (A) limits *output* length, not context accumulation. Frequent summarization (B) risks losing transactional detail. A larger window (D) delays the problem without addressing the waste, and dilutes attention with irrelevant fields.

---

## Question 9

A customer writes: "My order #5567 arrived damaged, AND I was double-charged on my last invoice, AND I want to update my shipping address." How should the agent handle this?

A) Address only the first issue and ask the customer to open separate tickets for the rest.
B) Decompose the message into three distinct items, investigate each (in parallel where possible) using shared customer context, then synthesize a single unified resolution.
C) Escalate immediately because multi-issue messages exceed the agent's scope.
D) Handle whichever issue it happens to address first and end the turn.

**Correct Answer: B**

Multi-concern requests should be decomposed into distinct items, each investigated against shared context, then resolved in one coherent response — this is core to hitting the first-contact resolution target. Handling only one issue (A, D) leaves the contact unresolved. Escalating (C) is unwarranted: multiple issues are not inherently complex or beyond scope.

---

## Question 10

The agent cannot resolve a dispute and must hand off to a human who has no access to the conversation transcript. What should the handoff include?

A) A structured summary: customer ID, root-cause analysis, relevant amounts/order IDs, and a recommended action.
B) The instruction "see chat history" — the human can scroll back if needed.
C) Only the customer's most recent message, to keep the handoff short.
D) The full raw transcript with no summary, so nothing is lost.

**Correct Answer: A**

A human who lacks the transcript needs a structured handoff summary containing the key facts and a recommended action so they can act without re-investigating. "See chat history" (B) fails because the human cannot access it. The last message alone (C) omits essential context. A raw dump (D) forces the human to reconstruct everything, defeating the purpose of the handoff.

---

## Question 11

Company policy caps autonomous refunds at $500; anything higher needs manager approval. Prompt instructions alone occasionally let larger refunds through. What is the most reliable way to enforce this?

A) A system prompt line stating "Never refund more than $500."
B) A few-shot example showing the agent declining a $600 refund.
C) Lowering the model temperature to make the agent more rule-abiding.
D) A hook that intercepts `process_refund` calls, blocks any amount over $500, and redirects to the escalation workflow.

**Correct Answer: D**

A monetary policy ceiling is a hard business rule requiring deterministic enforcement. A tool-call interception hook guarantees compliance and routes over-limit cases to escalation. Prompt instructions (A) and few-shot examples (B) are probabilistic and the team has already seen them fail. Temperature (C) does not enforce rules.

---

## Question 12

`get_customer` returns account-creation dates as Unix timestamps, while `lookup_order` returns order dates as ISO 8601 strings. The agent miscompares them and gives customers wrong timelines. What is the cleanest fix?

A) Tell the model in the system prompt to convert Unix timestamps itself.
B) Ask the customer to confirm all dates verbally.
C) Add a `PostToolUse` hook that normalizes all date fields to a single format before the model sees the results.
D) Remove dates from both tool outputs since they cause confusion.

**Correct Answer: C**

A `PostToolUse` hook intercepts tool results and can normalize heterogeneous formats (Unix vs ISO 8601) deterministically before the model reasons over them. Asking the model to convert (A) reintroduces probabilistic arithmetic errors. Confirming with the customer (B) is unreliable and high-friction. Removing dates (D) discards information the agent legitimately needs.

---

## Question 13

A customer says "It's me, John Smith — process my refund." `get_customer` returns three different accounts named John Smith. What should the agent do?

A) Pick the most recently active account, since it is the most likely match.
B) Ask the customer for an additional identifier (order number, email, or account ID) to disambiguate before proceeding.
C) Process refunds on all three accounts to be safe.
D) Escalate to a human because the lookup returned multiple matches.

**Correct Answer: B**

Multiple matches require clarification — the agent should request another identifier rather than guessing. Heuristic selection (A) risks acting on the wrong account, exactly the misidentification failure the scenario warns about. Refunding all three (C) is reckless and causes financial harm. Escalating (D) is premature: asking one clarifying question is a normal, resolvable step that supports first-contact resolution.

---

## Question 14

After a `lookup_order` tool call, your loop appends the tool result to the conversation and sends it back to Claude. A new engineer proposes instead summarizing each tool result into a one-line note and discarding the structured result. Why is the original approach better for an agentic loop?

A) The model needs the actual tool results in conversation history to reason about the next action; discarding them removes the information the next iteration depends on.
B) Summaries are slower to generate than passing the raw result.
C) Tool results must be kept verbatim for legal compliance reasons.
D) The API rejects requests where tool results have been modified.

**Correct Answer: A**

In an agentic loop, tool results are appended to conversation history precisely so the model can incorporate the new information into its reasoning for the next step. Aggressively discarding the structured result starves subsequent iterations of needed data. (Trimming *irrelevant* fields is fine — but that is different from discarding the result entirely.) B is a minor concern, not the core reason. C and D are fabricated constraints.

---

## Question 15

You want to guarantee that, on a given turn, the agent calls a tool rather than replying with conversational text — but it may choose which tool. Which `tool_choice` setting achieves this?

A) `tool_choice: "auto"`
B) `tool_choice: {"type": "tool", "name": "get_customer"}`
C) `tool_choice: "none"`
D) `tool_choice: "any"`

**Correct Answer: D**

`"any"` forces the model to call *some* tool while leaving the choice of which tool to the model. `"auto"` (A) lets the model decide whether to call a tool at all, so it may return text. Forced selection (B) pins a *specific* tool, which is more restrictive than "may choose which." `"none"` (C) forbids tool use entirely.

---

## Question 16

`process_refund` can fail two ways: a transient gateway timeout, or a business-rule rejection ("item outside the 30-day return window"). The agent currently retries both identically. What should the tool's error responses enable?

A) A single generic "refund failed" response, with the agent retrying a fixed three times.
B) Always escalate to a human on any `process_refund` failure.
C) Distinct structured errors — the transient timeout marked retryable, the business rejection marked non-retryable with a customer-friendly explanation — so the agent retries one and explains the other.
D) Retry both error types indefinitely until one succeeds.

**Correct Answer: C**

Transient and business errors call for different agent behavior: retry the timeout, but do not retry a policy rejection — instead explain it to the customer. Structured, categorized errors with `isRetryable` flags enable that distinction. A generic response (A) and indefinite retries (D) waste attempts on permanent failures. Escalating every failure (B) undermines first-contact resolution for cases the agent could handle (e.g., simply explaining the return-window policy).

---

## Question 17

A customer asks the agent to price-match a competitor's lower price. Company policy documents only address price adjustments for items discounted on the company's *own* site and are silent on competitor matching. What should the agent do?

A) Escalate to a human, because the policy is silent on this specific request.
B) Deny the request, since competitor matching is not in the policy.
C) Approve the match, since the policy does not explicitly forbid it.
D) Apply the own-site adjustment policy to the competitor's price as the closest rule.

**Correct Answer: A**

A policy gap — where policy is ambiguous or silent on the customer's specific request — is a legitimate escalation trigger. The agent should not invent a ruling. Denying (B) or approving (C) both fabricate a policy decision the agent has no authority to make. Stretching an unrelated rule (D) misapplies policy and risks an incorrect, inconsistent outcome.

---

## Question 18

A teammate proposes routing cases to humans whenever the agent self-reports a confidence score below 8/10 before each response. Why is this an unreliable escalation mechanism?

A) Confidence scores add too much latency to every response.
B) LLM self-reported confidence is poorly calibrated — the agent is often confidently wrong on exactly the hard cases that need escalation.
C) The API does not allow a model to output numeric scores.
D) Customers find confidence scores confusing if they appear in the reply.

**Correct Answer: B**

Self-reported confidence is a poor proxy for actual case complexity; a model can be highly confident on cases it gets wrong, so a low-confidence threshold will miss the very cases that most need a human. Escalation should be driven by explicit criteria (customer request, policy gap, lack of progress). A, C, and D are not the substantive reason — the calibration problem is.

---

## Question 19

To "future-proof" the agent, an engineer wants to give it access to all 19 internal MCP tools, even though resolving returns, billing disputes, and account issues needs only `get_customer`, `lookup_order`, `process_refund`, and `escalate_to_human`. What is the main risk?

A) Each additional tool measurably increases the model's per-token price.
B) The API enforces a hard limit of 5 tools per request.
C) A large, mostly irrelevant tool set increases decision complexity and degrades tool-selection reliability.
D) Unused tools cause the agent to terminate the loop early.

**Correct Answer: C**

Giving an agent far more tools than its role requires increases decision complexity and degrades selection reliability — the agent should be scoped to the tools its role actually needs. A is false (tools add some token overhead but not a separate per-tool price). B is a fabricated limit. D misdescribes loop termination, which is governed by `stop_reason`.

---

## Question 20

A customer is clearly frustrated ("This is the third time I've contacted you!") but the underlying issue — a standard damaged-item replacement with photo evidence — is squarely within the agent's capability. What is the best response?

A) Escalate immediately, since the customer is upset.
B) Process the replacement silently without acknowledging the customer's frustration.
C) Ask the customer to rate their frustration on a 1–10 scale to decide whether to escalate.
D) Acknowledge the frustration and offer to resolve the issue directly, escalating only if the customer reiterates that they want a human.

**Correct Answer: D**

When the issue is within the agent's capability, the agent should acknowledge the customer's frustration *and* offer resolution, escalating only if the customer reiterates a preference for a human. Escalating purely on sentiment (A) is unreliable and abandons a resolvable case, hurting first-contact resolution. Ignoring the frustration (B) damages the customer experience. A frustration-rating scale (C) is awkward and still relies on sentiment, which does not correlate with whether escalation is actually needed.

---

## Answer Key

| # | Answer | # | Answer | # | Answer | # | Answer |
|---|--------|---|--------|---|--------|---|--------|
| 1 | B | 6 | A | 11 | D | 16 | C |
| 2 | D | 7 | D | 12 | C | 17 | A |
| 3 | A | 8 | C | 13 | B | 18 | B |
| 4 | C | 9 | B | 14 | A | 19 | C |
| 5 | B | 10 | A | 15 | D | 20 | D |

Distribution: A × 5, B × 5, C × 5, D × 5.
