# Diary Agent CLI

CLI-first, local-first diary agent centered around **long-lived life topics** and a lightweight daily interview flow.

The product is designed to feel like a structured nightly check-in (not a freeform chatbot):
- select relevant topics for today,
- ask short natural questions,
- turn replies into durable memory,
- synthesize a daily diary entry.

---

## Current MVP status

This repository is currently at an **MVP core / early alpha** stage.

Implemented today:
- SQLAlchemy-backed local data model (topics, session queue, turns, history, diary entry)
- Explicit service pipeline:
  - session planner
  - question composer
  - signal extractor
  - memory writer
  - diary synthesizer
  - conversation orchestrator
- CLI commands for setup, topic management, session execution, and inspection
- Deterministic mode by default
- Optional Gemini-powered generation/extraction with safe deterministic fallback

Not implemented yet:
- Full Anthropic provider (placeholder only)
- Advanced error recovery / production hardening
- Web UI (intentionally out of scope)

---

## High-level architecture (current)

Runtime flow is explicit and inspectable:

1. `SessionPlanner` selects topics for the day.
2. `QuestionComposer` produces opening/topic/follow-up/free-share/closing prompts.
3. `ConversationOrchestrator` runs the turn loop.
4. `SignalExtractor` converts replies into structured memory signals.
5. `MemoryWriter` persists history and updates topic state/metadata.
6. `DiarySynthesizer` generates the final markdown diary entry.

LLM boundary (`src/diary_agent/llm/`):
- provider abstraction + request type
- deterministic provider (`stub`)
- Gemini provider
- Anthropic placeholder
- provider factory with automatic fallback

All state is persisted locally in SQLite (`DailySession`, `SessionTurn`, `SessionTopicQueue`, `TopicHistoryItem`, `DiaryEntry`).

---

## Requirements

- Python **3.11+**
- macOS / Linux / Windows
- Internet access for first-time dependency installation (`pip install`)

---

## Quickstart (first local run)

### 1) Clone

```bash
git clone <YOUR_REPO_URL>
cd Diary-Agent-CLI
```

### 2) Create and activate a virtual environment

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows (PowerShell)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -e .
```

Optional (dev/test tools):

```bash
python -m pip install -e ".[dev]"
```

### 4) (Recommended) pin database path for this repo

By default, the app uses a relative DB path (`data/diary_agent.db`) from your current working directory.

To avoid accidentally creating multiple DB files from different directories, set `DIARY_AGENT_DB_PATH` explicitly:

#### macOS / Linux

```bash
export DIARY_AGENT_DB_PATH="$PWD/data/diary_agent.db"
```

#### Windows (PowerShell)

```powershell
$env:DIARY_AGENT_DB_PATH = "$PWD/data/diary_agent.db"
```

### 5) Initialize database

```bash
diary-agent init-db
```

If `diary-agent` script is not found in your shell, use:

```bash
PYTHONPATH=src python -m diary_agent.cli init-db
```

### 6) Add starter topics

```bash
diary-agent topics add "Health" --description "Sleep, exercise, energy" --pinned
diary-agent topics add "Career" --description "Projects and focus"
diary-agent topics add "Relationships" --description "Family and friends"
```

### 7) Run today’s session

```bash
diary-agent run
```

You can also run for a specific date:

```bash
diary-agent run --session-date 2026-03-30
```

### 8) Inspect outputs

```bash
diary-agent topics list
diary-agent topics show health
diary-agent session show
diary-agent diary today
```

---

## LLM mode configuration

### Environment variables

The app reads these variables at runtime:

- `DIARY_AGENT_LLM_PROVIDER` (`stub`, `gemini`, `anthropic`)
- `DIARY_AGENT_LLM_MODEL` (provider model id)
- `GEMINI_API_KEY`
- `ANTHROPIC_API_KEY`

### Deterministic mode (default)

No API keys required:

```bash
export DIARY_AGENT_LLM_PROVIDER=stub
```

### Gemini-enabled mode

```bash
export DIARY_AGENT_LLM_PROVIDER=gemini
export DIARY_AGENT_LLM_MODEL=gemini-1.5-flash
export GEMINI_API_KEY="<your_key_here>"
```

Then run normally:

```bash
diary-agent run
```

### Fallback behavior

If Gemini is selected but `GEMINI_API_KEY` is missing/invalid or request fails, the app **falls back automatically** to deterministic behavior.

Anthropic is currently a placeholder provider and also falls back to deterministic mode.

---

## CLI command overview

Top-level:

```bash
diary-agent --help
```

Main commands:
- `init-db`
- `run [--session-date YYYY-MM-DD]`
- `topics list`
- `topics add <title> [--description ...] [--category ...] [--pinned]`
- `topics show <id-or-slug>`
- `session show [id-or-date]`
- `diary today`

---

## Caveats for first-time users

1. **DB path behavior:** default DB path is relative; set `DIARY_AGENT_DB_PATH` for consistency across shells/working directories.
2. **`--session-date` must be valid ISO format (`YYYY-MM-DD`)**; invalid values currently raise an error rather than a friendly message.
3. **Gemini usage is best-effort:** API/network failures degrade to deterministic mode.
4. **Anthropic provider is not implemented yet** (placeholder + fallback).

---

## Running tests

```bash
pytest -q
```

Current tests cover:
- session planning behavior
- memory writing behavior
- end-to-end orchestration flow
- resumable session behavior

---

## Project layout (key paths)

- `src/diary_agent/cli.py` — Typer CLI entry and wiring
- `src/diary_agent/services/` — orchestration and core behavior
- `src/diary_agent/llm/` — provider abstraction and concrete providers
- `src/diary_agent/db/models.py` — SQLAlchemy models
- `src/diary_agent/db/repositories/` — thin data access repositories
- `tests/` — MVP behavior tests

---

## Roadmap (near-term)

- Implement Anthropic provider fully
- Improve runtime checkpointing / interruption recovery
- Expand CLI UX guardrails and error messages
- Continue memory quality and diary quality tuning
