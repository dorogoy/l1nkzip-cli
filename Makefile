lint:
	uv run ruff check .
	uv run ruff check --select I .
	uv run mypy --ignore-missing-imports .

format:
	uv run ruff format .
	uv run ruff check --select I --fix .

test:
	uv run pytest tests/ -v
