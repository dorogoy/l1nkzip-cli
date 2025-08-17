# Technology Stack

## Core Technologies
- Python 3.12+
- Typer (CLI framework)
- Rich (terminal formatting)
- httpx (HTTP client)

## Development Environment
- **Package Manager**: uv
- **Linting/Formatting**: Ruff
- **Type Checking**: mypy
- **Testing**: pytest (to be implemented)

## Tool Usage Patterns
```mermaid
graph LR
    A[Development] --> B[make format]
    A --> C[make lint]
    A --> D[./main.py test]

    B -->|Auto-format| E[Code]
    C -->|Static analysis| E
    D -->|Verify functionality| E
```

## Dependencies
- See `pyproject.toml` for complete list
- Managed via uv lockfile

## Constraints
- Requires Python 3.12+
- Needs L1NKZIP_TOKEN for authenticated operations
