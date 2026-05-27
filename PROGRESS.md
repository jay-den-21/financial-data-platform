# Progress

This file tracks implementation progress. `PROJECT.md` remains the project specification.

## Current Status

The project has a runnable, testable, and committable Python + Poetry scaffold.

Completed:

- Python package scaffold under `src/fdp`
- Poetry project metadata and dependency definitions
- CLI entrypoint through `poetry run fdp --help`
- Configuration templates through `.env.example` and `config/default.yaml`
- Alembic scaffold with an empty `versions/` directory
- Smoke test scaffold under `tests/`
- README quickstart for setup, build, test, CLI, and configuration
- Initial SQLAlchemy table definitions for `us_share` and `system`
- Initial Alembic migration for platform schemas and core tables
- First EODHD instrument parser slice for active stock/ETF rows
- MySQL upsert statement builders for `instrument` and `daily_price`
- Unit tests for metadata, EODHD symbol parsing, and upsert SQL generation
- EODHD Exchange Symbols client with API call summary fields
- `fdp ingest instruments --market US --source eodhd` command path
- Instrument ingestion service that parses, rejects unsupported/malformed rows, upserts valid rows, and records task/API summaries
- Unit tests for EODHD client URL construction, instrument row rejection, ingestion task logging, and CLI command registration

Not started:

- EODHD historical daily price ingestion
- Data quality checks
- Repair plan workflow
- Database-backed access functions
- Real `fdp ingest history`, `fdp ingest daily`, `fdp validate`, and `fdp repair` subcommands

## Next Step

Start EODHD historical daily price ingestion with a small symbol-limited path:

- add an EODHD client method for historical EOD prices
- parse and validate `date/open/high/low/close/adjusted_close/volume`
- reject invalid OHLCV rows before database write
- upsert valid rows into `us_share.daily_price`
- record task and API call summaries in `system`
