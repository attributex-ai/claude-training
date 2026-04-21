---
name: claude-api-lecture-notebook
description: Generate a live-lecture Jupyter notebook for a Claude API / Anthropic SDK course from user-supplied notes. Produces a walkthrough-ready .ipynb that pairs concept markdown, a demo description, executable demo code, and an instructor "🏫 During class" callout for every topic. Use this skill whenever the user pastes lecture notes (often as `<note title="...">...</note>` blocks or a topic list) and asks for a Jupyter notebook, teaching notebook, lecture notebook, walkthrough notebook, or "notebook based on these notes" — even if they don't explicitly name the skill. Also use it when the user asks to extend, rebuild, or style-match an existing notebook in this project.
---

# Claude API Lecture Notebook

This skill builds live-lecture Jupyter notebooks for teaching the Anthropic Python SDK. The user supplies lecture notes (usually as `<note title="Topic">...</note>` blocks, sometimes as a plain topic list). Output is a single `.ipynb` file at the project root, ready to walk through on a live call.

The canonical example already lives in this project at `Intro_to_Claude_API.ipynb` — match that file's structure, tone, and rhythm. Everything below describes how to reproduce it for new material.

## What the output looks like

A successful notebook follows this exact shape, top to bottom:

1. **Title + agenda** — one markdown cell with the notebook title, a short "instructor walkthrough notebook" framing sentence, and a numbered agenda listing every topic in order.
2. **Setup section** — one markdown cell with `.env` + install instructions, one `%pip install` code cell (commented out so it's opt-in), one markdown description of the client-init cell, one code cell that loads the key and creates the client. The client-init cell must end with three `print()` lines acting as a sanity check: SDK version, model name, and `Key loaded: True/False`.
3. **One section per input note**, in the same order the user provided them. Each section is four cells:
   1. **Concept markdown** — the lecture notes, converted into clean lesson prose (tables/diagrams welcome).
   2. **Demo description markdown** — one short paragraph explaining what *this* specific code cell will show, what to watch for, and what to tweak.
   3. **Demo code cell** — small, runnable, and visibly demonstrates the concept.
   4. **`🏫 During class` callout markdown** — instructor steps (run order, talking points, a question or variation).
4. **Recap + exercises** — one markdown cell with a bulleted recap and 3–5 progressively harder exercises.
5. **Exercise scaffold** — one code cell (usually commented out) that starts the first exercise for the live build.

## Non-negotiable rules

### 1. Every code cell has a markdown cell directly above it describing that code
This is the single most important rule. Not a section header — a specific paragraph about what *this* code cell demonstrates, what to watch for when it runs, and what to swap to explore further. A student glancing at the notebook without running it should know what each cell is for.

When the concept markdown already describes the demo closely (e.g., *"Two quick examples follow"*), that counts — but if the concept markdown is abstract and the code is concrete, add a dedicated description cell.

### 2. Use current model names
- Default workhorse: `claude-sonnet-4-6`
- Fastest: `claude-haiku-4-5`
- Most capable: `claude-opus-4-7`

Never emit `claude-3-*` — those families are deprecated. If the user's notes reference `claude-3-sonnet` or similar, silently update to the current equivalent and mention the substitution in your end-of-turn summary.

### 3. One shared `chat()` helper, defined once
After the multi-turn section introduces helpers, every later demo reuses the same function. This keeps cells short and makes it obvious to students that *"we're only varying one argument"*. Do not redefine `chat()` per section.

Canonical helpers to emit verbatim:

```python
def add_user_message(messages, text):
    messages.append({"role": "user", "content": text})
    return messages

def add_assistant_message(messages, text):
    messages.append({"role": "assistant", "content": text})
    return messages

def chat(messages, system=None, temperature=1.0, stop_sequences=None):
    """Send messages to Claude and return the assistant text."""
    params = {
        "model": model,
        "max_tokens": 1000,
        "messages": messages,
        "temperature": temperature,
    }
    if system is not None:
        params["system"] = system
    if stop_sequences is not None:
        params["stop_sequences"] = stop_sequences
    response = client.messages.create(**params)
    return response.content[0].text
```

### 4. Secret hygiene
API key loads from `.env` via `python-dotenv`. Never hard-code it into a notebook cell. Setup instructions must tell the user to add `.env` to `.gitignore`. The setup sanity check must print `Key loaded: True/False` so a missing `.env` is caught before any API call.

### 5. Demos must be observably different
A teaching demo fails when the output looks the same across runs or variants. Design each demo so the contrast is visible at a glance. Proven patterns:

- **Side-by-side contrast:** with/without history, with/without system prompt, before/after pre-fill.
- **Loop over a parameter:** multiple temperatures, multiple models, multiple stop sequences.
- **Same prompt, three models:** run Haiku → Sonnet → Opus with timing; latency + tone differences land together.

### 6. "🏫 During class" callouts are concrete
Each callout must contain, in order:
1. A **specific action** — *"Run cell A first"*, not *"discuss with the class"*.
2. A **specific talking point** — the sentence the instructor says out loud, often the one-line takeaway.
3. A **question for the room or a variation to try live** — gives students something to do and exposes common misconceptions.

Generic callouts ("discuss streaming") produce dead lecture time. Specific ones drive the live feel.

### 7. Tone
- Use tables where a comparison is natural (model families, temperature use cases, event types).
- Use fenced code snippets in markdown for inline examples, not just in code cells.
- Explain **why**, not just **what**. `temperature=1.0 → creative output` is weaker than *"higher temperature flattens the probability distribution, so low-ranked tokens sometimes win"*.
- No emoji anywhere in the notebook **except** the 🏫 marker on "During class" callouts. That's a deliberate visual anchor for the instructor.

## Building the notebook

### Input handling
The user will typically provide notes in one of these shapes:

```
<note title="Topic Name">
Body text about the topic — bullets, definitions, examples.
</note>
```

or occasionally just a numbered topic list. Preserve the order. Do not reorder or collapse topics without asking.

If a note references deprecated APIs (old model names, removed SDK methods), silently modernize and flag it in your summary.

### Output location
Write to `<project-root>/<DescriptiveName>.ipynb` — one file. The name should match the subject (e.g., `Intro_to_Claude_API.ipynb`, `Tool_Use_Deep_Dive.ipynb`). Use the **Write tool** to emit the raw notebook JSON. Do **not** try to use the generic `Edit` tool on a `.ipynb` — it will reject the operation. For edits to an existing notebook, use `NotebookEdit`.

### Notebook JSON skeleton
```json
{
 "cells": [ ... ],
 "metadata": {
  "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
  "language_info": {"name": "python", "version": "3.11"}
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
```

Markdown cell shape:
```json
{"cell_type": "markdown", "metadata": {}, "source": ["line1\n", "line2"]}
```

Code cell shape:
```json
{"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["..."]}
```

### Validate after writing
Always confirm the JSON loads before declaring done:

```bash
python3 -c "import json; nb=json.load(open('PATH')); print('cells:', len(nb['cells']), 'types:', [c['cell_type'] for c in nb['cells']])"
```

If validation fails, the most common cause is an unescaped quote or a trailing comma inside a cell's `source` array.

## A complete section template

Copy this exact shape for every input note:

**Cell 1 — concept markdown**
```
---
# N. Topic Name

One-sentence definition that names the concept and its purpose.

### Key subheadings
Bullet list, table, or diagram — whichever teaches fastest.

### When/why it matters
Short prose explaining why a student should care. Tie to something they'll
recognize (a real app, a real failure mode, a recognizable UX feel).
```

**Cell 2 — demo description markdown**
```
### Demo: <what the code shows>

One paragraph: what this code does, the observation to point out when it
runs, and what the instructor can swap live to explore further.
```

**Cell 3 — demo code**
Small, uses the shared `chat()` helper, produces visibly different output across runs or variants.

**Cell 4 — during-class markdown**
```
> **🏫 During class:**
> 1. <specific action — which cell to run, in what order>
> 2. <specific talking point — the sentence the instructor says out loud>
> 3. <question for the room OR variation to try live>
```

## Interaction checklist

**Before writing the notebook**
- Confirm the output filename if the topic is ambiguous.
- Scan the notes for deprecated references and plan substitutions.
- If the notes imply a topic that isn't there yet (e.g., notes mention "tool use" but there's no tool-use note), ask the user whether to add it.

**After writing the notebook**
- Run the JSON validation command.
- Report back: file path, cell count (markdown vs code), which notes became which sections, any substitutions made (e.g., model names), and any heads-up the user should know before class.
- If any demo depends on state from a prior cell (e.g., the helpers defined in §4), call that out so the instructor doesn't try to run a later cell in isolation.

## Editing an existing notebook
When the user asks to extend or tweak an existing notebook rather than generate a new one:

- Use `NotebookEdit` (not `Edit` or `Write`) — the generic editors reject `.ipynb`.
- For inserts, `edit_mode=insert` with a `cell_id` inserts the new cell **after** the referenced cell. Inserting from the end backwards avoids index-shift surprises when doing multiple inserts.
- After any structural change, re-run the JSON validator and print the updated cell order so the user can see the new layout without opening the file.
