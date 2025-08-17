# System Architecture

## Component Structure
```
graph TD
    A[CLI Interface] --> B[Command Handlers]
    B --> C[API Client]
    C --> D[L1nkZip API]

    subgraph CLI Components
        A -->|Typer Framework| B
        B -->|Rich Library| E[Output Formatter]
    end
```

## Key Technical Decisions
1. **Typer Framework**: For intuitive CLI building
2. **Rich Library**: For beautiful terminal output
3. **httpx**: Modern HTTP client with async support
4. **Centralized Error Handling**: `print_api_error` function

## Critical Paths
1. URL shortening workflow:
   `shorten command → POST /url → format output`
2. Link lookup:
   `info command → GET /list → search → format output`

## File Structure
- `main.py`: Core application (500+ lines)
- `Makefile`: Build automation
- `pyproject.toml`: Dependency management
