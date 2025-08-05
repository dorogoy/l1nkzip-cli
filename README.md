# L1nkZip CLI

A simple, modern Python CLI to interact with the [L1nkZip](https://l1nk.zip) URL shortener API, with beautiful output using [rich](https://github.com/Textualize/rich).

## Features

- Shorten URLs from the command line
- Get info about a short link
- List all your shortened URLs (requires API token)
- Update the PhishTank database (admin, requires API token)
- Uses the [rich](https://github.com/Textualize/rich) library for pretty output
- Self-contained, runs with [uv](https://github.com/astral-sh/uv) (no manual pip install needed)

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (for running the script and managing dependencies)
- [ruff](https://github.com/astral-sh/ruff) (for linting, formatting, and import sorting)

## Installation

You can download the latest version with:

```sh
curl -O https://raw.githubusercontent.com/dorogoy/l1nkzip-cli/master/main.py
chmod +x main.py
chmod +x l1nkzip
```

## Usage

```sh
./main.py --help
```

### Commands

- `shorten <url>`: Shorten a URL
- `info <link>`: Get info about a short link
- `list [--token <token>] [--limit <n>]`: List all URLs (requires token)
- `update-phishtank [--token <token>] [--cleanup-days <n>]`: Update PhishTank DB (admin, requires token)

### Token

For commands that require a token, you can either:

- Pass it as a command-line option (`--token <token>`)
- Set the `L1NKZIP_TOKEN` environment variable
- The CLI will prompt you if the token is not provided

## Example

```sh
./main.py shorten https://www.google.com
```

## License

MIT
