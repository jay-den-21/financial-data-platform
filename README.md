# financial-data-platform

Traceable and verifiable financial data platform.

`PROJECT.md` is the project specification. This README is the quickstart for local development.

## Development Setup

Install Poetry if it is not already available:

```bash
brew install pipx
pipx ensurepath
pipx install poetry
```

After installing Poetry, reopen the terminal or reload your shell, then verify:

```bash
poetry --version
```

Install project dependencies from this directory:

```bash
poetry install
```

## Build And Test

Run the test suite:

```bash
poetry run pytest
```

Run the CLI entrypoint:

```bash
poetry run fdp --help
```

## Configuration

Copy the environment template before adding local secrets:

```bash
cp .env.example .env
```

Do not commit `.env`, API keys, database passwords, tokens, or private keys.

