# SeekStars (StarSeek) - Crush Context

> Read this file first. It tells you where everything is and how to work on this project.

## Before You Do Anything

1. The **task-manager skill** (`.crush/skills/task-manager/SKILL.md`) governs all work tracking. Read it.
2. Check `tasks/` for any open tasks (see paths below). Resume if something is in-progress.
3. If no open tasks, check `ROADMAP.md` for the next unchecked step.
4. Create a task file BEFORE writing code. Update it as you go. Close it when done.

## Key Paths

| What | Where |
|------|-------|
| **Planning docs** (13 files) | `/home/nnguyen/repos/obsidian/work-learning/Personal Notes/starseek-project/planning/` |
| **Active tasks** | `/home/nnguyen/repos/obsidian/work-learning/Personal Notes/starseek-project/tasks/` |
| **Closed tasks** | `/home/nnguyen/repos/obsidian/work-learning/Personal Notes/starseek-project/tasks/closed/` |
| **Source code** | This repo (`/home/nnguyen/repos/github/nnguyen/seekstars/`) |

Planning docs reading order: `CRUSH_INSTRUCTIONS.md` first (it lists the order for all 13 files).

## Git Workflow

- **`main`** branch: stable, releasable. Merge only (no direct commits).
- **`dev`** branch: active development. Day-to-day work happens here.
- **Feature branches**: optional, for larger changes. Branch from `dev`, merge back to `dev`.
- **Releases**: merge `dev` to `main`, tag with semver (e.g., `v0.1.0`).
- **Git credentials**: GitHub token is in `~/.bashrc_aliases`.

Create the `dev` branch on first session if it doesn't exist:
```bash
git checkout -b dev
```

## Python Version

Use **Python 3.11** specifically. pyswisseph only has prebuilt wheels for 3.6-3.11.
The system has Python 3.14; use pyenv or a direct `python3.11` binary.

## Key Commands

```bash
./setup.sh              # First-time setup (creates venv, installs deps, inits DB)
source .venv/bin/activate
make run                 # Start FastAPI server (dev mode with reload)
make test                # Run all tests
make test-unit           # Unit tests only (fast)
make test-integration    # Integration tests only
make check               # Lint + tests (quality gate before merging)
make help                # Show all Makefile targets
```

## Architecture Summary

```
seekstars/
├── starseek/              # Python package
│   ├── core/              # Ephemeris wrapper, chart builder, aspects, dignities, houses
│   ├── models/            # Pydantic models (enums, input, output, user)
│   ├── services/          # Geocoding (GeoNames), storage (SQLite), auth (future)
│   ├── formatters/        # JSON and Markdown output formatters
│   ├── api/               # FastAPI app, routes, dependencies
│   └── cli/               # Click CLI entry point
├── tests/                 # pytest test suite
├── Makefile               # Dev/ops task runner
├── setup.sh               # First-time interactive setup
└── requirements.txt       # Dependencies
```

All logic lives in `starseek.core`. CLI and API are thin wrappers.

## Task Workflow (Summary)

Full details in `.crush/skills/task-manager/SKILL.md`. The short version:

1. **Start session**: read open tasks in `tasks/`, resume or create new
2. **Create task**: `YYYY-MM-DD-description.md` with front matter (`status`, `phase`, `roadmap_steps`)
3. **During work**: update checklist and progress notes in the task file
4. **Finish task**: set `status: closed`, write summary, move to `tasks/closed/`
5. **End session**: if unfinished, leave clear notes on where you stopped

## Current Status

Check `ROADMAP.md` in the planning folder for checkboxes showing what's done.
Check `tasks/` for the latest active work.
