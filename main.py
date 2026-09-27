#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich", "httpx", "typer"]
# ///

"""
L1nkZip CLI: Interact with the l1nkZip API from your terminal.

Usage:
  l1nkzip [COMMAND] [OPTIONS]

Commands:
  shorten          Shorten a URL
  info             Get info about a short link
  list             List all URLs (requires token)
  update-phishtank Update PhishTank DB (admin, requires token)
  update           Update this CLI
  version          Print the version
"""

import atexit
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from typing import Any

import httpx
import typer
from rich.console import Console
from rich.table import Table

VERSION = "0.3.0"  # x-release-please-version
_GIT_TOOL = "git+https://github.com/dorogoy/l1nkzip-cli"
_RAW_MAIN = "https://raw.githubusercontent.com/dorogoy/l1nkzip-cli/master/main.py"
_RAW_VERSION = "https://raw.githubusercontent.com/dorogoy/l1nkzip-cli/master/VERSION"
_UPDATE_INTERVAL = 24 * 60 * 60
_UPDATE_TIMEOUT = 2.5

API_BASE = os.environ.get("L1NKZIP_API_URL", "https://l1nk.zip")
DEFAULT_LIMIT = 100
DEFAULT_CLEANUP_DAYS = 5
TIMEOUT = 10.0

app = typer.Typer()
console = Console()
notice = Console(stderr=True)

# Configure HTTP client with base URL and timeout
client = httpx.Client(base_url=API_BASE, timeout=TIMEOUT)
atexit.register(lambda: client.close())


def get_token(token: str | None = None) -> str:
    """Retrieve API token from argument, env, or prompt."""
    if token:
        return token
    env_token = os.environ.get("L1NKZIP_TOKEN")
    if env_token:
        return env_token
    return typer.prompt("Enter your API token", hide_input=True)


def api_request(method: str, path: str, token: str | None = None, **kwargs) -> Any:
    """Make request to API, return parsed JSON or raise typer.Exit on error."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        resp = client.request(method, path, headers=headers, **kwargs)
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        try:
            err = exc.response.json()
            msg = err.get("detail") or str(err)
        except Exception:  # noqa: BLE001 — any JSON/text decode failure falls back to raw text
            msg = exc.response.text
        console.print(f"[red]HTTP {exc.response.status_code}:[/red] {msg}")
        raise typer.Exit(1)
    except httpx.RequestError as exc:
        console.print(f"[red]Network error:[/red] {exc}")
        raise typer.Exit(1)


def is_valid_url(url: str) -> bool:
    """Check if URL is valid."""
    # Simple regex validation for http/https URLs
    return re.match(r"^https?://", url) is not None


def _version_key(value: str) -> tuple[int, ...]:
    parts = []
    for piece in value.strip().split("."):
        digits = ""
        for char in piece:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def _is_newer(remote: str, local: str) -> bool:
    """Return True when `remote` is a newer dotted version than `local`."""
    left = _version_key(remote)
    right = _version_key(local)
    width = max(len(left), len(right))
    left = left + (0,) * (width - len(left))
    right = right + (0,) * (width - len(right))
    return left > right


def _cache_file() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        root = Path(base) if base else Path.home() / "AppData" / "Local"
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Caches"
    else:
        env = os.environ.get("XDG_CACHE_HOME")
        root = Path(env) if env else Path.home() / ".cache"
    return root / "l1nkzip" / "update-check.json"


def _announce(remote: object) -> None:
    if isinstance(remote, str) and _is_newer(remote, VERSION):
        notice.print(
            "[yellow]Update available:[/yellow] "
            f"{VERSION} -> {remote}. Run 'l1nkzip update'."
        )


def _fetch_remote_version() -> str:
    req = urllib.request.Request(
        _RAW_VERSION,
        headers={"User-Agent": f"l1nkzip/{VERSION}"},
    )
    with urllib.request.urlopen(req, timeout=_UPDATE_TIMEOUT) as resp:
        text = resp.read(64).decode("utf-8", errors="replace")
    line = text.strip().splitlines()[0].strip()
    token = line.split()[0]
    if not re.fullmatch(r"\d+(?:\.\d+)*", token):
        raise ValueError(line)
    return token


def maybe_check_update() -> None:
    """Best-effort update notice. Never raises; skips the network for 24h."""
    try:
        if os.environ.get("L1NKZIP_NO_UPDATE_CHECK") == "1":
            return
        path = _cache_file()
        now = time.time()
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if not isinstance(data, dict):
                    raise TypeError("cache root must be an object")
                checked = float(data.get("checked", 0))
                if now - checked < _UPDATE_INTERVAL:
                    _announce(data.get("remote"))
                    return
            except (OSError, json.JSONDecodeError, TypeError, ValueError):
                pass
        remote: str | None = None
        try:
            remote = _fetch_remote_version()
        except Exception:  # noqa: BLE001 — offline or a bad payload stays quiet
            remote = None
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"checked": now, "remote": remote}),
                encoding="utf-8",
            )
        except OSError:
            pass
        _announce(remote)
    except Exception:  # noqa: BLE001 — the notice must never break a command
        return


def _version_flag(value: bool) -> None:
    if value:
        console.print(VERSION)
        raise typer.Exit()


@app.callback()
def _root(
    ctx: typer.Context,
    no_update_check: bool = typer.Option(
        False,
        "--no-update-check",
        help="Skip the update check for this run.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_flag,
        is_eager=True,
        help="Show the version and exit.",
    ),
) -> None:
    """Interact with the l1nkZip API from your terminal."""
    if version or no_update_check:
        return
    if ctx.invoked_subcommand in {None, "update", "version"}:
        return
    if "--help" in sys.argv:
        return
    maybe_check_update()


def _is_uv_tool_install() -> bool:
    """True when this process is the uv-installed l1nkzip executable."""
    if shutil.which("uv") is None:
        return False
    found = shutil.which("l1nkzip")
    if found is None:
        return False
    try:
        if Path(sys.argv[0]).resolve() != Path(found).resolve():
            return False
        proc = subprocess.run(
            ["uv", "tool", "list"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if proc.returncode != 0:
        return False
    for line in proc.stdout.splitlines():
        parts = line.split()
        if parts and parts[0] == "l1nkzip":
            return True
    return False


def _uv_reinstall() -> None:
    # `uv tool upgrade` fetches the git repo but can keep serving old bytecode.
    proc = subprocess.run(
        ["uv", "tool", "install", "--force", _GIT_TOOL],
        check=False,
    )
    if proc.returncode != 0:
        console.print("[red]uv tool install failed.[/red]")
        raise typer.Exit(proc.returncode or 1)


def _installed_version() -> str:
    exe = shutil.which("l1nkzip")
    if not exe:
        return VERSION
    try:
        proc = subprocess.run(
            [exe, "--no-update-check", "version"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return VERSION
    if proc.returncode != 0:
        return VERSION
    lines = [line.strip() for line in proc.stdout.splitlines() if line.strip()]
    return lines[-1] if lines else VERSION


def _download_replace(target: Path) -> str:
    """Download main.py and atomically replace `target`. Return its version."""
    req = urllib.request.Request(
        _RAW_MAIN,
        headers={"User-Agent": f"l1nkzip/{VERSION}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = resp.read()
    match = re.search(rb'(?m)^VERSION\s*=\s*"([^"]+)"', data)
    if match is None:
        raise ValueError("downloaded main.py is missing VERSION")
    new_version = match.group(1).decode("utf-8")
    fd, name = tempfile.mkstemp(prefix=".l1nkzip-", suffix=".tmp", dir=target.parent)
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
        os.chmod(tmp, 0o755)
        os.replace(tmp, target)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise
    return new_version


@app.command()
def shorten(
    url: str,
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Shorten a URL. If --json is used, prints the full API response from /url."""
    if not is_valid_url(url):
        console.print(f"[red]Invalid URL:[/red] {url}")
        raise typer.Exit(1)

    try:
        data = api_request("POST", "/url", json={"url": url})
        if json_output:
            console.print_json(data=data)
        else:
            console.print(f"[bold green]Shortened:[/bold green] {data['full_link']}")
            console.print(f"[bold]Visits:[/bold] {data['visits']}")
    except typer.Exit:
        # Error already printed by api_request
        pass
    except Exception as e:  # noqa: BLE001 — CLI boundary: report any error via rich and exit cleanly
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    link: str,
    token: str | None = typer.Option(
        None, help="API token (or set L1NKZIP_TOKEN env var)"
    ),
    limit: int = typer.Option(DEFAULT_LIMIT, help="Max number of URLs to search"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Show info about a short link (target URL and visits). If --json is used, prints the full API response from /list/{token}."""
    token_val = get_token(token)

    try:
        data = api_request("GET", f"/list/{token_val}", params={"limit": limit})
    except typer.Exit:
        # Error already printed by api_request
        return
    except Exception as e:  # noqa: BLE001 — CLI boundary: report any error via rich and exit cleanly
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)

    found = None
    for item in data:
        if item.get("link") == link or item.get("full_link") == link:
            found = item
            break

    if not found:
        console.print(f"[red]No info found for link:[/red] {link}")
        raise typer.Exit(1)

    if json_output:
        console.print_json(data=data)
    else:
        table = Table(title="Link Info")
        table.add_column("Field")
        table.add_column("Value")
        table.add_row("Short Link", found["link"])
        table.add_row("Full URL", found["url"])
        table.add_row("Visits", str(found["visits"]))
        console.print(table)


@app.command()
def list(
    token: str | None = typer.Option(
        None, help="API token (or set L1NKZIP_TOKEN env var)"
    ),
    limit: int = typer.Option(DEFAULT_LIMIT, help="Max number of URLs to list"),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """List all URLs (requires token). If --json is used, prints the full API response from /list/{token}."""
    token_val = get_token(token)

    try:
        data = api_request("GET", f"/list/{token_val}", params={"limit": limit})
        if json_output:
            console.print_json(data=data)
        else:
            table = Table(title="Shortened URLs")
            table.add_column("Short Link")
            table.add_column("Full URL")
            table.add_column("Visits")
            for item in data:
                table.add_row(item["full_link"], item["url"], str(item["visits"]))
            console.print(table)
    except typer.Exit:
        # Error already printed by api_request
        pass
    except Exception as e:  # noqa: BLE001 — CLI boundary: report any error via rich and exit cleanly
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def update_phishtank(
    token: str | None = typer.Option(
        None, help="API token (or set L1NKZIP_TOKEN env var)"
    ),
    cleanup_days: int = typer.Option(
        DEFAULT_CLEANUP_DAYS, help="Days to keep old entries"
    ),
    json_output: bool = typer.Option(False, "--json", "-j", help="Output as JSON"),
) -> None:
    """Update PhishTank DB (admin, requires token). If --json is used, prints the full API response from /phishtank/update/{token}."""
    token_val = get_token(token)

    try:
        data = api_request(
            "GET",
            f"/phishtank/update/{token_val}",
            params={"cleanup_days": cleanup_days},
        )
        if json_output:
            console.print_json(data=data)
        else:
            console.print(
                f"[bold green]PhishTank updated:[/bold green] {data.get('detail', str(data))}"
            )
    except typer.Exit:
        # Error already printed by api_request
        pass
    except Exception as e:  # noqa: BLE001 — CLI boundary: report any error via rich and exit cleanly
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def version() -> None:
    """Print the current version."""
    console.print(VERSION)


@app.command()
def update() -> None:
    """Update l1nkzip to the latest version."""
    old = VERSION
    try:
        if _is_uv_tool_install():
            _uv_reinstall()
            new = _installed_version()
        else:
            new = _download_replace(Path(os.path.realpath(__file__)))
    except typer.Exit:
        raise
    except Exception as exc:
        console.print(f"[red]Update failed:[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(f"[bold green]Updated:[/bold green] {old} -> {new}")


def main() -> None:
    """CLI entry point for the console script and `python main.py`."""
    if len(sys.argv) == 1:
        app(["--help"])
    else:
        app()


if __name__ == "__main__":
    main()
