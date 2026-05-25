# CCAF Sample Questions: Structured Data Extraction

Twenty practice questions in the format of the *Claude Certified Architect – Foundations* exam guide, all set within the **Structured Data Extraction** scenario.

**Scenario recap:** An extraction pipeline uses Claude to pull structured information from unstructured source documents (invoices, contracts, receipts, scanned PDFs). Each extraction is validated against a JSON schema before being passed to a downstream consumer (auto-payment, analytics, audit). The target is high precision on every field, with deterministic schema compliance and explicit handling of edge cases such as missing values, ambiguous mentions, format variants, and long documents.

**Primary domains:** Prompt Engineering & Structured Output, Context Management & Reliability.

---

## Question 1

Even with the schema in the system prompt and `temperature=0`, roughly 6% of extractions still return responses that begin with conversational preamble like "Here is the JSON: ..." and break the downstream JSON parser. The team cannot migrate to forced tool calls in this release because the downstream consumer expects raw JSON in the response text. Which technique most reliably suppresses the preamble?

A) Prefill the assistant turn with `{` so Claude continues the response from the opening brace; the consumer concatenates the prefill with the response and parses normally.
B) Increase `max_tokens` so the model has room to write a clean response.
C) Strengthen the system prompt with "RESPOND ONLY IN JSON. NO PREAMBLE." in capitals.
D) Lower the temperature further (e.g., set `top_k` and `top_p` to very restrictive values).

**Correct Answer: A**

Assistant-turn prefilling forces the response to *start* from the prefilled tokens, which deterministically removes the surface where preamble could appear. C and D are probabilistic — the team is already running at `temperature=0` and still seeing 6% leakage, so prompt wording and sampling parameters are not the load-bearing fix. B affects truncation, not preamble: it solves a different failure mode entirely.

---

## Question 2

Invoices without a purchase-order number are coming back with fabricated values like `"PO-00000"` or `"N/A-001"` in the `po_number` field. The schema requires `po_number` as a non-null string, and the prompt instructs Claude to "extract the purchase order number."

A) Add the sentence "do not invent purchase order numbers" to the system prompt.
B) Change the schema to `"po_number": {"type": ["string", "null"]}`, mark the field optional, and update its description to "Purchase order number printed on the invoice, or null if the document does not contain one."
C) Lower the temperature so the model stops hallucinating.
D) Default the field to an empty string in the schema when no value is found.

**Correct Answer: B**

The current schema and prompt jointly create structural pressure: a required, non-null string must always be produced even when no value exists, so the model fabricates one. Making the field nullable and explicitly documenting `null` as the correct response for absence removes that pressure. A and C are probabilistic instructions that don't change what the schema requires of the model. D produces a sentinel value (`""`) that still misrepresents absence and propagates a bad shape downstream.

---

## Question 3

An audit of the extraction pipeline finds that ~3% of `total_amount` values do not appear anywhere in the underlying invoice — Claude confidently extracts amounts like `$847.50` that aren't in the source. Downstream auto-payment relies on these values. What is the most reliable mitigation?

A) Lower the temperature to 0 on every extraction.
B) Add the instruction "do not invent amounts not found in the document" to the system prompt.
C) Add a `source_quote` field to the schema that requires Claude to return the exact substring from the document that justifies each extracted value; downstream validates that the quote appears in the source and rejects any field whose quote cannot be found.
D) Run a second Claude call as a judge to flag suspicious values for human review.

**Correct Answer: C**

A grounding constraint that requires Claude to cite a verbatim source quote — and downstream verification that the quote is actually present in the document — is a deterministic check that catches fabrication. A and B are probabilistic and do not prevent confident fabrication. D is a probabilistic judge: sophisticated but it can miss the same hallucinations the extractor did, and it does not give a hard verifiable signal.

---

## Question 4

Eighty-page commercial contracts are processed in a single extraction call. Claude reliably extracts the effective date (page 1) and the signature block (last page), but indemnification clauses and warranty terms — typically on pages 30–60 — are missed on about one quarter of contracts. Which change most directly addresses the failure?

A) Switch to a model with a longer context window.
B) Place the schema and instructions at both the beginning *and* the end of the prompt to bracket the document.
C) Add few-shot examples of indemnification clauses to the system prompt.
D) Chunk the contract into focused sections aligned to clause types, run a targeted extraction per chunk against a partial schema, then merge the results.

**Correct Answer: D**

The failure pattern — strong recall at the edges of a long document, weak recall in the middle — is the canonical attention-on-long-context problem. Splitting the document into focused chunks gives each clause type its own narrow context, which is the targeted fix. A doesn't change attention distribution within a long input. B helps attention *to instructions*, not attention to middle-document content. C teaches the model what indemnification clauses look like but doesn't change which pages it reads carefully.

---

## Question 5

The team needs to re-extract 50,000 historical purchase orders under a new schema for analytics. There is no real-time requirement — results can land within a day. Current per-document cost on the standard /messages API is too high to be acceptable for a one-time backfill of this size.

A) Submit the workload via the Message Batches API to receive the ~50% per-token discount; the 24-hour completion window matches the offline nature of the backfill.
B) Stream every call so progress is visible.
C) Run all 50,000 in parallel against /messages with a very high concurrency cap.
D) Move the extraction to a self-hosted open-source model.

**Correct Answer: A**

The workload — large, offline, latency-insensitive — is exactly what the Message Batches API is designed for, and the ~50% discount is a first-class cost lever Anthropic ships for this case. B doesn't change cost at all; streaming is a UX feature. C maximizes throughput but pays full price per token. D abandons the platform when a built-in cost lever solves the problem.

---

## Question 6

Each extraction call sends a 4,200-token system message containing the schema, formatting rules, and six few-shot examples, followed by a 1,500-token document. The same system content is sent on every call. Daily volume is 12,000 calls. Latency is acceptable, but input token costs dominate the bill.

A) Reduce the few-shot examples to one to shrink the system prompt.
B) Move the schema, formatting rules, and few-shot examples into a system prompt with a `cache_control` breakpoint; subsequent calls read the cached prefix at roughly 10% of the input token cost.
C) Send the schema as a tool `input_schema` instead of in the system prompt.
D) Switch to a smaller model.

**Correct Answer: B**

The 4,200 static tokens repeated across 12,000 calls per day is the textbook prompt-caching case: cache the static prefix once, pay ~10% of the input cost on subsequent reads. A reduces tokens by trading quality, and gives up most of the savings that caching would provide for free. C is a valid structural choice but doesn't change the economics of repeatedly transmitting the same content. D affects per-token price but doesn't address the repeated transmission of identical content.

---

## Question 7

About 5% of extractions fail downstream JSON-schema validation — most commonly because a required nested object is missing or a date string is in the wrong format. The current pipeline drops these requests and reports an error.

A) Strip the invalid fields from the response and pass the remainder downstream.
B) Lower the temperature on the failing requests and silently retry once.
C) Catch the validation failure, send Claude back its previous response together with the specific validation error message, and ask it to produce a corrected output that satisfies the schema.
D) Mark these cases for manual extraction.

**Correct Answer: C**

Feeding the validation error back into the conversation gives Claude a concrete signal about *what* failed — a targeted correction loop that resolves the failure on the next turn for most of the 5%. A produces partial outputs that misrepresent the extraction. B is a generic retry with no information about what was wrong; the model has no reason to produce a different result. D abandons automation for a class of failure that is recoverable.

---

## Question 8

Across vendors, the invoice number is labeled as "Invoice #", "Inv No.", "Invoice Number:", or "INV-". Dates appear in both US (`MM/DD/YYYY`) and EU (`DD/MM/YYYY`) formats. Extraction quality is ~95% on the dominant US "Invoice #" variant and drops to ~70% on the others.

A) Add 4–6 few-shot examples in the prompt that cover the format variants — each showing a different label or date format and the same canonical extracted output.
B) Add a regex-based pre-processor that rewrites every variant to "Invoice #" and US dates before sending to Claude.
C) Add the instruction "be flexible about formats" to the system prompt.
D) Fine-tune a custom model on examples of each vendor's invoices.

**Correct Answer: A**

A handful of well-chosen few-shot examples teach the model the mapping from the long-tail variants to the canonical output — directly addressing the variants where quality is weakest. B is brittle (variants are by definition the long tail; new labels will appear and silently break the regex). C is vague prompting with no specific behavioral target. D is disproportionate to the problem when a small set of examples solves it.

---

## Question 9

Vendor invoices arrive as scanned multi-page PDFs with column tables, stamps, and occasionally rotated text. The current pipeline runs the PDFs through a third-party OCR tool, concatenates the text, and sends it to Claude. Total amounts are routinely associated with the wrong row of a line-item table.

A) Add a regex-based table parser between OCR and Claude that re-aligns columns based on whitespace.
B) Tell Claude in the prompt that "tables may be misaligned and you should re-align them."
C) Have humans pre-process every table-heavy invoice.
D) Pass the PDF directly to Claude as a document content block — Claude reads the PDF natively and preserves the column-row structure that the OCR-to-text conversion was destroying.

**Correct Answer: D**

The misalignment is happening *before* Claude ever sees the document, in the OCR-to-text step that flattens column structure. Sending the PDF directly preserves the layout natively. A re-implements the structure that the API would otherwise preserve, and is brittle on stamps and rotated text. B asks the model to recover information that was already discarded upstream. C abandons the automation for a problem the platform handles natively.

---

## Question 10

Contracts begin "This Agreement is entered into between Acme Corp. ('the Buyer') and Beta Inc. ('the Seller')" and then refer to the parties throughout as "the Buyer" / "the Seller". On ~8% of contracts — those where the proper name appears only in the opening paragraph — Claude returns `"buyer_name": "the Buyer"` literally rather than `"Acme Corp."`.

A) Add the instruction "resolve all references" to the system prompt.
B) Update the `buyer_name` field description in the schema to: "Full legal name of the buying party. Resolve role labels such as 'the Buyer' or 'the Customer' to the proper party name defined in the document. Return null if no proper name is defined."
C) Pre-process the document by replacing every occurrence of "the Buyer" with the proper name found in the first paragraph.
D) Lower the temperature so the model is more decisive.

**Correct Answer: B**

A precise field description is the model's strongest selection signal — telling Claude exactly what "buyer_name" means and how to resolve role references is the targeted fix and works inside the schema itself. A is vague prompting with no behavioral target. C is brittle string substitution that fails when the proper name isn't in the first paragraph or appears with stylistic variation. D doesn't address what the model should *do* about role references.

---

## Question 11

For larger invoices with 30+ line items, extraction sometimes returns truncated JSON. The pipeline logs show `stop_reason: "max_tokens"` and the response ends mid-object. `max_tokens` is currently set to 1024. Which response is correct?

A) Lower the temperature so the model produces more concise outputs.
B) Catch the truncated response, parse whatever is structurally complete, and discard the malformed tail.
C) Measure the output-token length on the 95th-percentile invoice, set `max_tokens` to comfortably exceed it, and treat `stop_reason: "max_tokens"` as a hard error so silent truncation cannot reach downstream.
D) Switch to a smaller, faster model so each line item is encoded in fewer tokens.

**Correct Answer: C**

The `stop_reason: "max_tokens"` signal is the API telling you the output was cut off; the only correct response is to size `max_tokens` to the workload and to treat any further occurrence as an explicit failure rather than a silent partial. A doesn't meaningfully shrink JSON keyspace. B is a silent-truncation workaround that lets partial extractions reach downstream as if they were complete. D changes which model writes the output but does not change the configured ceiling.

---

## Question 12

For each 100-page contract, three separate extractions are run in sequence: parties, key dates, and clause types. Each call currently re-sends the full document. Per-call latency is ~12 s and per-call input cost is dominated by the document.

A) Place the document at the beginning of each call with a `cache_control` breakpoint; the second and third calls read the cached document at ~10% of input cost and reduced latency.
B) Combine all three extractions into a single prompt that requests every field at once.
C) Pre-summarize the document and run the three extractions against the summary.
D) Run the three extractions in parallel.

**Correct Answer: A**

The same document is being sent three times to the same model — exactly the case where a `cache_control` breakpoint on the document content unlocks ~10× cheaper subsequent reads and lower latency. B looks reasonable but couples three independent extractions into one large response and dilutes per-extraction prompting. C discards detail the extractions need. D doesn't reduce per-call input cost or the total tokens transmitted; it just spreads the same cost over wall-clock time.

---

## Question 13

The downstream pipeline crashes on roughly 12% of receipts. The crash trace points to the `address` field: most receipts return it as a nested object (`{street, city, postal}`), but on the failing 12% Claude returns it as a flat string (`"123 Main St, Springfield, 02101"`). The current schema defines `address` as `anyOf: [{type: "string"}, {type: "object", properties: {...}}]`. Four engineers each propose a different root cause:

A) Output is nondeterministic — lower the temperature to suppress the alternate shape.
B) The system prompt is not emphatic enough about always returning a nested object — strengthen the wording.
C) There are not enough few-shot examples of the nested form — add more examples.
D) The schema explicitly permits two shapes via `anyOf`; tightening it to a single nested object (and updating the field description to instruct that single-line source addresses still be returned as the nested object, with `null` sub-fields where the source does not contain them) eliminates the variance at its source.

**Correct Answer: D**

A, B, and C all blame the *model* for behavior the *schema* is sanctioning. The schema permits the flat string, so the model is correct to emit it — no amount of prompt strengthening, temperature lowering, or few-shot pressure will reliably override an explicit `anyOf` permitting both shapes. Schema variance is fixed in the schema; everything else is a workaround.

---

## Question 14

On receipts where the customer paid a flat fee with no itemized lines, Claude omits the `line_items` field entirely from the response. Downstream expects `line_items` to be present as an array — even an empty one — and crashes when the key is absent.

A) Update every downstream consumer to treat a missing `line_items` field as equivalent to `[]`.
B) Mark `line_items` as a required field in the schema with type `array`, and update its description to read "All line items on the receipt. Return `[]` if the receipt has no itemized line items."
C) Default the missing field to `null` in a post-processing step before passing to downstream.
D) Lower the temperature on these requests.

**Correct Answer: B**

Making the field required-and-array, and explicitly documenting `[]` as the correct response for the empty case, fixes the contract at its source. A pushes the contract problem onto every current and future downstream consumer. C produces a different shape (`null`) than what downstream expects (`[]`) and merely substitutes one crash for another. D is unrelated — the omission is a schema-shape behavior, not a sampling issue.

---

## Question 15

Across 50,000 daily extractions, roughly 30% of responses come back with conversational text wrapping the JSON ("Here is the extracted data: ```json {...}```") and another 4% return prose like "The invoice does not contain a clear total — please review manually." Engineers debate the root cause:

A) The temperature is too high — lower it.
B) The system prompt is not strict enough about JSON-only output — strengthen the wording.
C) The architecture asks Claude to *generate text that happens to be JSON*, which leaves room for preamble and free-form refusals. Switching to a forced tool call (`tool_choice: {"type": "tool", "name": "extract_invoice"}`) with the schema as the tool's `input_schema` removes the free-text surface entirely — the model fills tool inputs, not a text response.
D) The model size is too small — switch to a larger model.

**Correct Answer: C**

A, B, and D all treat the symptom on a free-text generation surface; each can reduce — but not eliminate — preamble and free-form refusals because they leave the underlying surface in place. The structural fix is to change the *type* of output the model produces: a forced tool call constrains the response to a structured object that conforms to the tool's input schema, so there is no surface where preamble or refusal prose can appear.

---

## Question 16

Compliance has asked that every extracted value be linked to the page number of the source PDF for audit, starting in two weeks. Today the pipeline returns only field values. What is the most effective *first step*?

A) Add a `source_page` integer field beside each extracted value in the schema, instruct Claude to populate it from the document, and add a downstream validation that the page number falls within the document's page count.
B) Build a separate OCR + page-fingerprint pipeline that links each extracted value to its source page after extraction.
C) Convert the pipeline to a manual-review workflow where humans note the page for each field.
D) Switch to a model that emits document bounding boxes natively.

**Correct Answer: A**

A schema change — one new field with a range validation — is the smallest change that meets the compliance ask, and it can be in production within the two-week window. B and D are *valid* heavier architectures but disproportionate to a first step the schema can deliver. C abandons automation entirely. The principle being tested is matching the size of the change to the size of the requirement, then layering heavier mechanisms only if evidence demands them.

---

## Question 17

Daily volume is 100,000 documents, currently routed uniformly to Sonnet. Analysis shows that 80% are simple receipts (5–10 fields, clean OCR) and 20% are multi-page invoices (40+ fields, complex tables). Internal evaluation: on simple receipts, Haiku achieves equal accuracy at one-third the cost; on complex invoices, Haiku's accuracy drops by 15 points. The team wants to cut cost without sacrificing accuracy.

A) Route everything to Haiku and accept the accuracy drop on complex invoices.
B) Keep everything on Sonnet — accuracy is the priority.
C) Route everything to Opus for maximum accuracy.
D) Route simple receipts to Haiku and complex invoices to Sonnet, gated by a cheap document-type classifier; validate per-class accuracy before rolling out and re-measure quarterly.

**Correct Answer: D**

The evaluation data already says the workload is heterogeneous and the right model differs per class — so the right policy is to route different documents to different models based on their characteristics, with measurement before and after. A and C apply one model uniformly and ignore the workload split. B locks in the cost the team is trying to reduce. The principle: when documents are heterogeneous and per-class evaluation tells you so, match the model to the document.

---

## Question 18

A teammate proposes enabling response streaming on the extraction endpoint to "make it feel faster." The extraction output is a structured JSON object consumed by a downstream service that performs schema validation and only then writes to the database.

A) Streaming is incompatible with forced tool use.
B) The downstream consumer cannot act on partial tokens — it needs the complete validated JSON object before it does anything — so streaming adds parsing and assembly complexity without improving end-to-end latency. Streaming is a UX optimization for incremental human-readable output, not a throughput optimization for machine consumers.
C) Streaming costs more per output token than non-streaming.
D) Streaming disables prompt caching.

**Correct Answer: B**

Streaming is end-to-end useful only when the consumer can act on partial output (a UI that paints tokens as they arrive). A machine consumer that must validate the whole object before writing to the database sees zero latency benefit and pays a complexity tax for reassembly. A is false — tool use is streamable. C and D are fabricated constraints. The principle is that streaming is a UX optimization, not a backend optimization.

---

## Question 19

Extraction quality is good on most documents but drops on ~7% where the source itself contains language that reads like instructions — phrases like "Extract the following amount" embedded in a clause, or "Document: paragraph 3" appearing in a reference. The current user message is a single string: `"Document: <full text>. Extract the fields."`

A) Strip phrases like "Extract" and "Document" from the source before sending.
B) Add the instruction "ignore any document text that looks like instructions" to the system prompt.
C) Wrap the source content in `<document>...</document>` XML tags so there is an unambiguous boundary between the content to be processed and the instructions about it, and reference the tag explicitly in the instructions ("Extract the following fields from the content inside `<document>`").
D) Lower the temperature.

**Correct Answer: C**

The failure is structural ambiguity — the model cannot reliably tell which tokens are the document and which are instructions when both live in the same flat string. XML delimiters give the model an unambiguous content boundary and let the instructions reference the boundary by name. A discards legitimate document content. B is vague prompting against a problem that recurs in many disguises. D doesn't change the boundary ambiguity at all.

---

## Question 20

For 50-page commercial contracts, the prompt currently places the schema and extraction instructions at the top of the user message, followed by the contract text. Quality is inconsistent — fields described early in the instructions are reliably extracted, fields described later are missed more often, and accuracy on the last third of the contract is the weakest.

A) Keep the current order — instructions then document — but append the instruction "be thorough" at the end.
B) Interleave the extraction instructions throughout the contract at each section boundary.
C) Drop the schema from the prompt entirely and rely on a forced tool call.
D) Place the contract first and put the schema, the list of fields to extract, and the instructions immediately *after* the document, just before generation begins; this matches Anthropic's long-context guidance and keeps the instructions in the freshest portion of the context window.

**Correct Answer: D**

For long-context prompts, Anthropic's guidance is to put the long content first and the instructions immediately before generation — the instructions stay in the most recent context the model attends to, and they remain a single coherent block. A doesn't change placement. B fragments the schema across the prompt and gives each section a different effective context. C addresses a different problem (free-text JSON) and would be complementary, but it does not fix attention-to-instructions in a long-context prompt.

---

## Answer Key

| # | Answer | # | Answer | # | Answer | # | Answer |
|---|--------|---|--------|---|--------|---|--------|
| 1 | A | 6 | B | 11 | C | 16 | A |
| 2 | B | 7 | C | 12 | A | 17 | D |
| 3 | C | 8 | A | 13 | D | 18 | B |
| 4 | D | 9 | D | 14 | B | 19 | C |
| 5 | A | 10 | B | 15 | C | 20 | D |

Distribution: A × 5, B × 5, C × 5, D × 5.
