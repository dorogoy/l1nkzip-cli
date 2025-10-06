#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich", "httpx", "typer"]
# ///

"""
L1nkZip CLI: Interact with the l1nkZip API from your terminal.

Usage:
  uv main.py [COMMAND] [OPTIONS]

Commands:
  shorten         Shorten a URL
  info            Get info about a short link
  list            List all URLs (requires token)
  update-phishtank Update PhishTank DB (admin, requires token)
"""

import atexit
import os
import re
from typing import Any, Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

API_BASE = os.environ.get("L1NKZIP_API_URL", "https://l1nk.zip")
DEFAULT_LIMIT = 100
DEFAULT_CLEANUP_DAYS = 5
TIMEOUT = 10.0

app = typer.Typer()
console = Console()

# Configure HTTP client with base URL and timeout
client = httpx.Client(base_url=API_BASE, timeout=TIMEOUT)
atexit.register(lambda: client.close())


def get_token(token: Optional[str] = None) -> str:
    """Retrieve API token from argument, env, or prompt."""
    if token:
        return token
    env_token = os.environ.get("L1NKZIP_TOKEN")
    if env_token:
        return env_token
    return typer.prompt("Enter your API token", hide_input=True)


def api_request(method: str, path: str, token: Optional[str] = None, **kwargs) -> Any:
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
        except Exception:
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
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def info(
    link: str,
    token: Optional[str] = typer.Option(
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
    except Exception as e:
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
    token: Optional[str] = typer.Option(
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
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


@app.command()
def update_phishtank(
    token: Optional[str] = typer.Option(
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
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    import sys

    if len(sys.argv) == 1:
        app(["--help"])
    else:
        app()
