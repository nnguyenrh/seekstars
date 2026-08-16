# SeekStars (StarSeek)

A self-hosted Python app for generating astrological birth charts using the Swiss Ephemeris engine.

## Quick Start

```bash
./setup.sh          # First-time setup (interactive)
source .venv/bin/activate
make run             # Start the API server
make test            # Run tests
make help            # See all available commands
```

## What This Does

- Computes natal birth charts (planetary positions, house cusps, aspects, dignities)
- Exposes results via CLI, REST API (FastAPI), and Python library
- Stores charts in SQLite with geocoding cache
- Outputs LLM-friendly JSON and human-readable Markdown
- Designed for integration with local LLMs (DeepSeek-R1 via Ollama/LibreChat)

## Tech Stack

- Python 3.11, pyswisseph (Swiss Ephemeris), FastAPI, Pydantic v2, SQLite
- GeoNames for geocoding (free account required)

## Documentation

Full project planning docs are in:
`/home/nnguyen/repos/obsidian/work-learning/Personal Notes/starseek-project/planning/`

Start with `CRUSH_INSTRUCTIONS.md` in that folder.
