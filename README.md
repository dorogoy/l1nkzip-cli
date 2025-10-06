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

### Quick Install (Recommended)

You can download and install the `l1nkzip` executable with a single command:

```sh
curl -sSL https://raw.githubusercontent.com/dorogoy/l1nkzip-cli/master/main.py -o l1nkzip && chmod +x l1nkzip
```

This will download the script and make it executable in your current directory.

#### System-Wide Access

To make `l1nkzip` available from anywhere, move it to a directory in your system's `PATH`:

```sh
sudo mv l1nkzip /usr/local/bin/
```

### Manual Installation

Alternatively, you can clone the repository and run the script directly:

```sh
git clone https://github.com/dorogoy/l1nkzip-cli.git
cd l1nkzip-cli
./main.py --help
```

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
