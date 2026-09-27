# L1nkZip CLI

A simple, modern Python CLI to interact with the [L1nkZip](https://l1nk.zip) URL shortener API, with beautiful output using [rich](https://github.com/Textualize/rich).

## Features

- Shorten URLs from the command line
- Get info about a short link
- List all your shortened URLs (requires API token)
- Update the PhishTank database (admin, requires API token)
- Uses the [rich](https://github.com/Textualize/rich) library for pretty output
- Installs with one command via [uv tool](https://docs.astral.sh/uv/concepts/tools/)
- Updates itself with `l1nkzip update`

## Requirements

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (for running the script and managing dependencies)
- [ruff](https://github.com/astral-sh/ruff) (for linting, formatting, and import sorting)

## Installation

```sh
curl -sSL https://raw.githubusercontent.com/dorogoy/l1nkzip-cli/master/install.sh | bash
```

`INSTALL_DIR` chooses the directory the `l1nkzip` executable is placed in. If that directory is not on `PATH`, the script prints the exact line to add to your shell rc.

If you already have [uv](https://docs.astral.sh/uv/):

```sh
uv tool install git+https://github.com/dorogoy/l1nkzip-cli
```

To run from a checkout instead: `uv run main.py --help`.

## Usage

Once installed, you can use the `l1nkzip` command:

```sh
l1nkzip --help
```

### Commands

- `shorten <url>`: Shorten a URL.
- `info <link>`: Get information about a shortened link.
- `list [--token <token>] [--limit <n>]`: List all your shortened URLs (requires an API token).
- `update-phishtank [--token <token>] [--cleanup-days <n>]`: Update the PhishTank database (admin-only, requires an API token).
- `version`: Print the version. `--version` does the same.
- `update`: Update to the latest version. A uv tool install reinstalls from git; a plain copy of `main.py` replaces itself from GitHub.

On other commands, l1nkzip checks GitHub at most once a day and prints a one-line notice when a newer version exists. Skip that check with `--no-update-check` or `L1NKZIP_NO_UPDATE_CHECK=1`. The check fails silently when you are offline.

### Configuration

#### API Token

For commands that require an API token, you can:

1.  Pass it with the `--token` option: `l1nkzip list --token YOUR_TOKEN`
2.  Set the `L1NKZIP_TOKEN` environment variable: `export L1NKZIP_TOKEN="YOUR_TOKEN"`

If a token is not provided, the CLI will prompt for it when required.

#### Custom API Endpoint

To use a self-hosted L1nkZip instance, set the `L1NKZIP_API_URL` environment variable:

```sh
export L1NKZIP_API_URL="https://your-custom-domain.com"
```

If this variable is not set, the CLI will default to the public API at `https://l1nk.zip`.

## Example

```sh
l1nkzip shorten https://www.google.com
```

## License

MIT
