# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository purpose

This is a **live-lecture course repo** for teaching the Claude / Anthropic API. The deliverables are Jupyter notebooks designed to be walked through in front of students, plus two small Python sub-projects used as hands-on exercises. There is no application to deploy and no production code — when editing, optimize for instructor readability and stepwise, demonstrable cells.

## Notebook conventions

Each top-level folder corresponds to one course module. Inside each module:

- `<Module_Title>.ipynb` — the **main lecture notebook**. Mixes lecture markdown, demo descriptions, executable cells, and `🏫 During class` instructor callouts. This is the canonical artifact for that module.
- `001_*.ipynb`, `002_*.ipynb`, … — numbered **exercise / demo notebooks**, started in class.
- `*_complete.ipynb` / `*_completed.ipynb` — the **finished version** of the matching exercise. When asked to "fix" or "extend" an exercise, check the completed sibling first — the answer is often there.

Modules: `prompt_engineering_techniques/`, `prompt_evaluation/`, `features_of_claude/`, `tool_use_with_claude/`, `rag_and_agentic_search/`, `mcp/`, `anthropic_apps/`. The standalone `Intro_to_Claude_API.ipynb` is the course-opening notebook.

When generating or extending lecture notebooks, use the `claude-api-lecture-notebook` skill (defined in `.claude/skills/`) — it encodes the cell pattern (concept markdown → demo description → executable demo → instructor callout) that the existing notebooks follow.

## Sub-projects

Two folders contain real Python packages rather than notebooks. Both use **uv** and define an `app` package via `pyproject.toml`:

- **`anthropic_apps/app_starter/`** — MCP server starter using `FastMCP`. `main.py` registers tools (`tools/*.py`) onto the server. Tests live in `tests/` and run with pytest.
- **`mcp/cli_project/`** and **`mcp/cli_project_COMPLETE/`** — MCP-aware CLI chat client. `main.py` wires together `core/claude.py` (Anthropic SDK wrapper), `mcp_client.py` (MCP client), and `core/cli_chat.py` (prompt-toolkit REPL). The `_COMPLETE` variant is the finished reference; `cli_project/` is the student starter with TODOs.

Standard workflow inside either sub-project:

```bash
cd <subproject>
uv venv && source .venv/bin/activate
uv pip install -e .
uv run main.py            # run server / CLI
uv run pytest             # only app_starter has tests
```

The CLI project requires `ANTHROPIC_API_KEY` and `CLAUDE_MODEL` in its own `.env`; passing extra MCP server scripts as CLI args attaches them as additional clients (see `main.py`).

## Environment

- Python **3.10+** for sub-projects; the root notebooks target Python 3.11 / 3.13 (`pyrightconfig.json`).
- Secrets live in `/.env` at the repo root (`ANTHROPIC_API_KEY`, `VOYAGE_API_KEY`). Notebooks load it via `python-dotenv`. `.env` is gitignored — never commit it, and never paste the key into a notebook cell.
- `voyageai` is used for embeddings in `rag_and_agentic_search/`; `anthropic` SDK + `mcp[cli]` is used everywhere else.

## Editing notebooks

- Notebooks are the primary artifact; edit them in place rather than extracting code to `.py` files unless the user asks.
- Keep `execution_count` and cell `outputs` consistent with the rest of the notebook — recent commits explicitly normalize these (see `git log`).
- `*_complete*` notebooks are reference solutions; do not "improve" them speculatively — they are paired with the matching starter and changes there break the pedagogical contrast.

## GitHub account

This repo lives under the `attributex-ai` GitHub org. Always use the `attributex-ai` gh account for any git/gh operations here — **never** the `xhonorated` account, which lacks push access and will fail with 403. If `gh auth status` shows `xhonorated` as active, switch with `gh auth switch --user attributex-ai` before pushing or running `gh` commands.

## Document format conversion

When the user asks to convert a document from one format to another (PDF → Markdown, DOCX → HTML, etc.):

1. First, look for an available MCP server that can perform the conversion.
2. If no suitable MCP server is available, **ask** the user whether they want a utility / program written for the job.
3. Do not write any conversion code until the user explicitly confirms.
