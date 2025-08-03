# AGENTS.md

## Build, Lint, and Test Commands

- **Run CLI:** `./main.py [COMMAND] [OPTIONS]`
- **Show help:** `./main.py --help`
- **Lint & type check:** `make lint`
- **Test:** No tests present; add tests in `tests/` and run with `pytest`.

## Code Style Guidelines

- Use modern Python 3.12+ features and type hints (`Optional`, etc.).
- Imports: Standard library first, then third-party, then local.
- Naming: Use `snake_case` for functions/variables, `UPPER_CASE` for constants.
- Formatting: Follow PEP8 (4 spaces, max 88 chars/line).
- Error handling: Use `try/except`, print errors with `rich` for clarity.
- Use Typer for CLI commands and Rich for output.
- Environment variables: Prefer `L1NKZIP_TOKEN` for API token.
- Functions should have docstrings and clear argument names.

## Agentic Coding Instructions

- For architectural reasoning, use iterative, stepwise approaches (see `.github/chatmodes/Architect.chatmode.md`).
- When planning, break down complex problems into manageable steps and revise as needed.
- Store architectural documents in `.github/prompts/` if required.
- Ask clarifying questions if requirements are unclear.
- Always run the linter and type checker before committing changes.

---
This file is the source of truth for agentic coding in this repository.
