#!/usr/bin/env python3
"""Convert a CCAF-style MCQ markdown file into a self-contained interactive HTML quiz.

Usage:
    python build_quiz.py <input.md> <output.html>

The expected input format (the format used by the `sample-scenario-mcq` skill):
    # Title
    ... optional intro paragraphs ...
    **Scenario recap:** Some scenario context.

    ## Question 1
    Question text, may include `code`, **bold**, *italic*.
    A) First choice
    B) Second choice
    C) Third choice
    D) Fourth choice

    **Correct Answer: C**

    Explanation paragraph(s).

    ---
    ## Question 2
    ...

A trailing `## Answer Key` section is allowed and ignored.
"""

from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path


class ParseError(Exception):
    """Raised when the markdown does not match the expected MCQ format."""


@dataclass
class Question:
    number: int
    text_html: str
    choices_html: list[str] = field(default_factory=list)  # 4 entries, A-D
    correct_index: int = -1  # 0-3
    explanation_html: str = ""


@dataclass
class Document:
    title: str
    intro_html: str
    scenario_html: str
    questions: list[Question]


# --------------------------------------------------------------------------- #
# Inline markdown -> HTML
# --------------------------------------------------------------------------- #

_CODE_SPAN_RE = re.compile(r"`([^`]+)`")
_BOLD_RE = re.compile(r"\*\*([^*]+)\*\*")
_ITALIC_RE = re.compile(r"(?<!\*)\*([^*]+)\*(?!\*)")


def inline_md_to_html(text: str) -> str:
    """Convert a small subset of inline markdown to HTML, with proper escaping.

    Handles `code`, **bold**, *italic*. Escapes everything else (so `<`, `>`, `&`
    in question text render literally). Code spans are extracted first so their
    contents are not interpreted as markdown.
    """
    placeholders: list[str] = []

    def stash_code(m: re.Match[str]) -> str:
        placeholders.append(m.group(1))
        return f"\x00CODE{len(placeholders) - 1}\x00"

    text = _CODE_SPAN_RE.sub(stash_code, text)
    text = html.escape(text, quote=False)
    text = _BOLD_RE.sub(r"<strong>\1</strong>", text)
    text = _ITALIC_RE.sub(r"<em>\1</em>", text)

    def restore_code(m: re.Match[str]) -> str:
        idx = int(m.group(1))
        return f"<code>{html.escape(placeholders[idx], quote=False)}</code>"

    return re.sub(r"\x00CODE(\d+)\x00", restore_code, text)


# --------------------------------------------------------------------------- #
# Markdown parser
# --------------------------------------------------------------------------- #

_TITLE_RE = re.compile(r"^#\s+(.+?)\s*$")
_QUESTION_HEADER_RE = re.compile(r"^##\s+Question\s+(\d+)\s*$")
_ANSWER_KEY_RE = re.compile(r"^##\s+Answer\s+Key\s*$", re.IGNORECASE)
_CHOICE_RE = re.compile(r"^([A-D])\)\s+(.*)$")
_CORRECT_RE = re.compile(r"^\*\*Correct Answer:\s*([A-D])\*\*\s*$")
_SCENARIO_RE = re.compile(r"^\*\*Scenario recap:\*\*\s*(.+)$", re.IGNORECASE)


def parse_markdown(md_text: str) -> Document:
    """Parse the MCQ markdown into a Document. Raise ParseError on bad input."""
    lines = md_text.splitlines()
    title = ""
    intro_lines: list[str] = []
    scenario_html = ""
    questions: list[Question] = []

    i = 0
    n = len(lines)

    # Header: title and intro until the first ## Question
    while i < n:
        line = lines[i]
        if _QUESTION_HEADER_RE.match(line) or _ANSWER_KEY_RE.match(line):
            break
        if not title:
            m = _TITLE_RE.match(line)
            if m:
                title = m.group(1).strip()
                i += 1
                continue
        scen = _SCENARIO_RE.match(line.strip())
        if scen:
            scenario_html = inline_md_to_html(scen.group(1).strip())
        elif line.strip() and not line.startswith("#"):
            intro_lines.append(line.rstrip())
        i += 1

    intro_text = " ".join(s.strip() for s in intro_lines if s.strip())
    intro_html = inline_md_to_html(intro_text) if intro_text else ""

    # Questions
    while i < n:
        line = lines[i]
        if _ANSWER_KEY_RE.match(line):
            break  # ignore the answer key table
        m = _QUESTION_HEADER_RE.match(line)
        if not m:
            i += 1
            continue
        q_num = int(m.group(1))
        i += 1
        q = Question(number=q_num, text_html="")
        q_text_lines: list[str] = []
        choices: list[str] = ["", "", "", ""]
        explanation_lines: list[str] = []
        saw_correct = False

        # Question body until next ## or end
        while i < n:
            ln = lines[i]
            if _QUESTION_HEADER_RE.match(ln) or _ANSWER_KEY_RE.match(ln):
                break

            cm = _CHOICE_RE.match(ln.strip())
            if cm:
                idx = "ABCD".index(cm.group(1))
                choices[idx] = inline_md_to_html(cm.group(2).strip())
                i += 1
                continue

            am = _CORRECT_RE.match(ln.strip())
            if am:
                q.correct_index = "ABCD".index(am.group(1))
                saw_correct = True
                i += 1
                continue

            if ln.strip() == "---":
                i += 1
                continue

            if saw_correct:
                if ln.strip():
                    explanation_lines.append(ln.rstrip())
                else:
                    if explanation_lines and explanation_lines[-1] != "":
                        explanation_lines.append("")
            else:
                if ln.strip():
                    q_text_lines.append(ln.rstrip())

            i += 1

        # Validate
        if not q_text_lines:
            raise ParseError(f"Question {q_num} has no question text")
        if any(not c for c in choices):
            missing = [letter for letter, c in zip("ABCD", choices) if not c]
            raise ParseError(
                f"Question {q_num} is missing choice(s) {', '.join(missing)}"
            )
        if q.correct_index < 0:
            raise ParseError(
                f"Question {q_num} has no '**Correct Answer: X**' line"
            )

        q.text_html = inline_md_to_html(" ".join(q_text_lines).strip())
        q.choices_html = choices
        # Join explanation paragraphs with double newline -> two <br> for spacing
        explanation = "\n".join(explanation_lines).strip()
        # Convert blank-line-separated paragraphs into separate <p> blocks
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", explanation) if p.strip()]
        if paragraphs:
            q.explanation_html = "".join(
                f"<p>{inline_md_to_html(' '.join(p.split()))}</p>" for p in paragraphs
            )

        questions.append(q)

    if not questions:
        raise ParseError("No questions found — expected '## Question 1' headers")

    if not title:
        title = "Practice Quiz"

    return Document(
        title=title,
        intro_html=intro_html,
        scenario_html=scenario_html,
        questions=questions,
    )


# --------------------------------------------------------------------------- #
# HTML emission
# --------------------------------------------------------------------------- #

_CSS = """
* { box-sizing: border-box; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  background: #f5f7fa;
  color: #1f2937;
  margin: 0;
  padding: 24px;
  line-height: 1.5;
}
.container { max-width: 880px; margin: 0 auto; }
header {
  background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
  color: #fff;
  padding: 32px;
  border-radius: 12px;
  margin-bottom: 24px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.07);
}
header h1 { margin: 0 0 8px 0; font-size: 1.75rem; }
header p { margin: 4px 0; opacity: 0.95; font-size: 0.95rem; }
.scenario {
  background: rgba(255,255,255,0.12);
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 16px;
  font-size: 0.9rem;
}
.progress-bar {
  background: #e5e7eb;
  border-radius: 8px;
  height: 8px;
  overflow: hidden;
  margin-bottom: 24px;
}
.progress-fill {
  background: linear-gradient(90deg, #10b981, #059669);
  height: 100%;
  width: 0%;
  transition: width 0.3s ease;
}
.progress-text {
  text-align: center;
  margin-bottom: 16px;
  font-weight: 600;
  color: #4b5563;
}
.question-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  border: 1px solid #e5e7eb;
}
.question-number {
  display: inline-block;
  background: #3b82f6;
  color: #fff;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  margin-bottom: 12px;
}
.question-text {
  font-size: 1.05rem;
  font-weight: 500;
  margin-bottom: 18px;
  color: #111827;
}
.question-text code, .choice-text code, .explanation code {
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
  font-family: "SF Mono", Monaco, Consolas, monospace;
  color: #be185d;
}
.choices { list-style: none; padding: 0; margin: 0; }
.choice {
  display: flex;
  align-items: flex-start;
  background: #f9fafb;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px 16px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.question-card.answered .choice { cursor: not-allowed; }
.question-card:not(.answered) .choice:hover {
  background: #eff6ff;
  border-color: #3b82f6;
  transform: translateX(2px);
}
.choice-label {
  background: #d1d5db;
  color: #1f2937;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  margin-right: 12px;
  flex-shrink: 0;
  font-size: 0.9rem;
}
.choice-text { flex: 1; font-size: 0.95rem; }
.choice.correct { background: #d1fae5; border-color: #10b981; }
.choice.correct .choice-label { background: #10b981; color: #fff; }
.choice.incorrect { background: #fee2e2; border-color: #ef4444; }
.choice.incorrect .choice-label { background: #ef4444; color: #fff; }
.choice.correct .choice-text::after {
  content: " \\2713";
  color: #047857;
  font-weight: 700;
}
.choice.incorrect .choice-text::after {
  content: " \\2717";
  color: #b91c1c;
  font-weight: 700;
}
.explanation {
  margin-top: 16px;
  padding: 16px;
  background: #fef3c7;
  border-left: 4px solid #f59e0b;
  border-radius: 6px;
  font-size: 0.95rem;
  color: #78350f;
  display: none;
}
.question-card.answered .explanation { display: block; }
.explanation p { margin: 0 0 8px 0; }
.explanation p:last-child { margin-bottom: 0; }
.explanation-title { font-weight: 700; margin-bottom: 6px; color: #92400e; }
.summary {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  margin-top: 24px;
  text-align: center;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  display: none;
}
.summary.show { display: block; }
.summary h2 { margin: 0 0 8px 0; color: #1f2937; }
.score { font-size: 2.5rem; font-weight: 800; color: #3b82f6; margin: 12px 0; }
.reset-btn {
  background: #3b82f6;
  color: #fff;
  border: none;
  padding: 10px 24px;
  border-radius: 8px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  margin-top: 8px;
  transition: background 0.15s;
}
.reset-btn:hover { background: #2563eb; }
""".strip()


_JS = """
(function () {
  const cards = document.querySelectorAll('.question-card');
  const total = cards.length;
  let answered = 0;
  let correct = 0;

  const progressFill = document.getElementById('progressFill');
  const progressText = document.getElementById('progressText');
  const summary = document.getElementById('summary');
  const finalScore = document.getElementById('finalScore');
  const scoreMessage = document.getElementById('scoreMessage');

  function updateProgress() {
    const pct = (answered / total) * 100;
    progressFill.style.width = pct + '%';
    progressText.textContent = 'Answered ' + answered + ' of ' + total + ' \\u00b7 Correct: ' + correct;
    if (answered === total) showSummary();
  }

  function showSummary() {
    summary.classList.add('show');
    const pct = Math.round((correct / total) * 100);
    finalScore.textContent = correct + ' / ' + total + ' (' + pct + '%)';
    let msg;
    if (pct === 100) msg = "Perfect score! You're ready for the exam.";
    else if (pct >= 85) msg = "Excellent \\u2014 strong grasp of the material.";
    else if (pct >= 70) msg = "Good work. Review the missed questions and try again.";
    else if (pct >= 50) msg = "Decent start \\u2014 revisit the explanations and retry.";
    else msg = "Worth another pass through the explanations before retrying.";
    scoreMessage.textContent = msg;
    summary.scrollIntoView({ behavior: 'smooth' });
  }

  function resetQuiz() {
    answered = 0;
    correct = 0;
    summary.classList.remove('show');
    cards.forEach(function (card) {
      card.classList.remove('answered');
      card.querySelectorAll('.choice').forEach(function (c) {
        c.classList.remove('correct', 'incorrect');
      });
    });
    updateProgress();
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  cards.forEach(function (card) {
    const correctIdx = parseInt(card.getAttribute('data-correct'), 10);
    const choices = card.querySelectorAll('.choice');
    choices.forEach(function (choice) {
      choice.addEventListener('click', function () {
        if (card.classList.contains('answered')) return;
        const idx = parseInt(choice.getAttribute('data-idx'), 10);
        card.classList.add('answered');
        if (idx === correctIdx) {
          choice.classList.add('correct');
          correct++;
        } else {
          choice.classList.add('incorrect');
          choices[correctIdx].classList.add('correct');
        }
        answered++;
        updateProgress();
      });
    });
  });

  document.getElementById('resetBtn').addEventListener('click', resetQuiz);
})();
""".strip()


def render_html(doc: Document) -> str:
    """Render the parsed document as a complete self-contained HTML file."""
    parts: list[str] = []
    title_escaped = html.escape(doc.title, quote=True)
    parts.append(
        '<!DOCTYPE html>\n'
        '<html lang="en">\n'
        '<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{title_escaped}</title>\n'
        '<style>\n'
        f'{_CSS}\n'
        '</style>\n'
        '</head>\n'
        '<body>\n'
        '<div class="container">\n'
        '  <header>\n'
        f'    <h1>{html.escape(doc.title)}</h1>\n'
    )
    if doc.intro_html:
        parts.append(f'    <p>{doc.intro_html}</p>\n')
    if doc.scenario_html:
        parts.append(
            f'    <div class="scenario"><strong>Scenario:</strong> {doc.scenario_html}</div>\n'
        )
    parts.append(
        '  </header>\n'
        f'  <div class="progress-text" id="progressText">Answered 0 of {len(doc.questions)} · Correct: 0</div>\n'
        '  <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>\n'
    )

    for q in doc.questions:
        parts.append(
            f'  <div class="question-card" data-correct="{q.correct_index}">\n'
            f'    <span class="question-number">Question {q.number}</span>\n'
            f'    <div class="question-text">{q.text_html}</div>\n'
            '    <ul class="choices">\n'
        )
        for idx, choice_html in enumerate(q.choices_html):
            letter = "ABCD"[idx]
            parts.append(
                f'      <li class="choice" data-idx="{idx}">'
                f'<span class="choice-label">{letter}</span>'
                f'<span class="choice-text">{choice_html}</span></li>\n'
            )
        parts.append('    </ul>\n')
        if q.explanation_html:
            parts.append(
                '    <div class="explanation">'
                '<div class="explanation-title">Explanation</div>'
                f'{q.explanation_html}</div>\n'
            )
        parts.append('  </div>\n')

    parts.append(
        '  <div class="summary" id="summary">\n'
        '    <h2>Quiz complete!</h2>\n'
        '    <div class="score" id="finalScore"></div>\n'
        '    <p id="scoreMessage"></p>\n'
        '    <button class="reset-btn" id="resetBtn" type="button">Try again</button>\n'
        '  </div>\n'
        '</div>\n'
        '<script>\n'
        f'{_JS}\n'
        '</script>\n'
        '</body>\n'
        '</html>\n'
    )
    return "".join(parts)


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("Usage: build_quiz.py <input.md> <output.html>", file=sys.stderr)
        return 2

    input_path = Path(argv[1]).expanduser().resolve()
    output_path = Path(argv[2]).expanduser().resolve()

    if not input_path.is_file():
        print(f"Input file not found: {input_path}", file=sys.stderr)
        return 1

    md_text = input_path.read_text(encoding="utf-8")
    try:
        doc = parse_markdown(md_text)
    except ParseError as exc:
        print(f"Parse error: {exc}", file=sys.stderr)
        return 1

    html_text = render_html(doc)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")

    print(f"Wrote {output_path}")
    print(f"Parsed {len(doc.questions)} questions from {input_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
