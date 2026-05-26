---
name: quiz-from-mcq-markdown
description: Convert a pre-generated markdown MCQ file (one of the `*_sample_questions.md` files in this repo, or any similarly-formatted file) into a self-contained interactive HTML quiz that runs in any browser with no external dependencies. Use this skill whenever the user asks to "turn the questions into a quiz", "make an interactive quiz", "build an HTML quiz", "generate a practice quiz page", "convert the MCQs to a webpage", "build a quiz from a markdown file", or wants a clickable practice tool from any of the `*_sample_questions.md` files — even if they don't explicitly say "HTML" or "interactive". Also trigger when the user references a specific MCQ markdown file and wants to study from it interactively.
---

# Quiz from MCQ Markdown

Turn a CCAF-style MCQ markdown file (the kind produced by the `sample-scenario-mcq` skill) into a single self-contained `.html` file. The output displays every question with clickable A/B/C/D options, then on click marks the selection green/red, reveals the correct answer if wrong, shows the explanation, and tracks score across the quiz.

The conversion is deterministic — markdown structure in, fixed HTML template out — so this skill delegates the work to a Python script (`scripts/build_quiz.py`) rather than asking the model to hand-write HTML each time. That keeps output consistent across runs and saves tokens.

## Workflow

1. **Pick the input file.** Find candidate `*_sample_questions.md` files at the repo root with `ls *_sample_questions.md` (run from the repo root). Use `AskUserQuestion` to let the user choose:
   - One option per discovered file (label = filename, description = first non-heading line of the file if cheap to read, otherwise just the filename)
   - Always include an "Other" path so they can supply a different markdown file

   If exactly one candidate file exists *and* the user's message already names it or clearly refers to it, you can skip the question and proceed.

2. **Decide the output path.** Default is `<input_basename>.html` in the same directory as the input. If a file with that name already exists, ask via `AskUserQuestion` whether to overwrite, write to `<input_basename>_quiz.html`, or pick a custom path.

3. **Run the script** from the repo root:

   ```bash
   python3 .claude/skills/quiz-from-mcq-markdown/scripts/build_quiz.py <input.md> <output.html>
   ```

   On systems where `python` is Python 3, `python` works too. The script is dependency-free (standard library only) and targets Python 3.9+.

   The script prints the output path and the parsed question count on success, or a clear error if parsing fails.

4. **Report** the absolute output path in the end-of-turn summary so the user can `open` it. One sentence is enough.

## Expected input format

The script assumes the standard format used in this repo's `*_sample_questions.md` files:

- A top-level `# Title` heading
- Optional intro paragraphs and a `**Scenario recap:**` paragraph used for the quiz header
- Repeated blocks of:
  - `## Question N` heading
  - Question prose (may include inline `` `code` ``, `**bold**`, `*italic*`)
  - Four lettered choices: `A) …`, `B) …`, `C) …`, `D) …` (one per line, may wrap)
  - A `**Correct Answer: X**` line where X is A/B/C/D
  - Explanation paragraph(s) following the answer line
- An optional `## Answer Key` section at the end (ignored by the script — the per-question answer lines are the source of truth)

If the input deviates substantially from this layout, the script raises a `ParseError` with a line number. When that happens, surface the error to the user verbatim — don't try to silently fix the source file unless they ask.

## What the generated HTML does

This is what the script emits, so you don't need to re-derive it:

- **Header card** with the title and scenario recap pulled from the markdown
- **Progress bar** updating as each question is answered (X of N · Correct: Y)
- **One card per question** with A/B/C/D as clickable list items
- **On click:** the chosen choice turns green (correct) or red (incorrect). If incorrect, the correct choice is also highlighted green. The explanation appears below. Further clicks on that question are ignored.
- **Summary card** at the end with final score, a short message keyed to the percentage, and a "Try again" button that resets all questions without reloading

## Implementation notes that matter

- **No `innerHTML` at runtime.** Every question card is pre-rendered as static HTML in the body; the JavaScript only toggles CSS classes on click. This is deliberate — it sidesteps the project's XSS security hook (`security_reminder_hook.py`), which blocks Write calls that set `innerHTML` from a string. If you ever change the script to construct DOM at runtime, build elements with `document.createElement` and `textContent`, not innerHTML.
- **Self-contained file.** All CSS and JS are inlined. No CDNs, no external fonts beyond system stacks. The user should be able to email the `.html` file and have it work.
- **Inline-code preservation.** Backticked spans in the source become `<code>` tags in the output with monospace styling, because the questions frequently reference paths like `~/.claude/CLAUDE.md` and the formatting carries meaning.

## When *not* to use this skill

- The user wants a Jupyter notebook quiz (different format, different skill).
- The user wants to *generate new MCQ content* — that's the `sample-scenario-mcq` skill. Suggest running that first to produce the markdown, then this skill to render it.
- The input isn't an MCQ file (e.g., free-response questions, flashcards). The script will fail; don't try to coerce it.
