#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.12"
# dependencies = ["rich", "httpx", "typer"]
# ///

"""
L1nkZip CLI: Interact with the l1nkZip API from your terminal.

Usage:
  uv l1nkzip.py [COMMAND] [OPTIONS]

Commands:
  shorten         Shorten a URL
  info            Get info about a short link
  list            List all URLs (requires token)
  update-phishtank Update PhishTank DB (admin, requires token)
"""

import os
import re
from typing import Optional, Any

import httpx
import typer
from rich.console import Console
from rich.table import Table

API_BASE = "https://l1nk.zip"
DEFAULT_LIMIT = 100
DEFAULT_CLEANUP_DAYS = 5
TIMEOUT = 10.0

app = typer.Typer()
console = Console()

L1NKZIP_TOKEN: Optional[str] = os.environ.get("L1NKZIP_TOKEN")

client = httpx.Client(timeout=TIMEOUT)

def get_token(token: Optional[str] = None) -> str:
    """Retrieve API token from argument, env, or prompt."""
    if token:
        return token
    if L1NKZIP_TOKEN:
        return L1NKZIP_TOKEN
    return typer.prompt("Enter your API token", hide_input=True)

def print_api_error(exc: httpx.HTTPStatusError) -> None:
    try:
        err = exc.response.json()
        msg = err.get("detail") or str(err)
    except Exception:
        msg = exc.response.text
    console.print(f"[red]HTTP {exc.response.status_code}:[/red] {msg}")


@app.command()
def shorten(url: str, json_output: bool = typer.Option(False, "--json", help="Output as JSON")) -> None:
    """Shorten a URL. If --json is used, prints the full API response from /url."""
    # Simple URL validation
    if not re.match(r"^https?://", url):
        console.print(f"[red]Invalid URL:[/red] {url}")
        raise typer.Exit(1)
    try:
        resp = client.post(f"{API_BASE}/url", json={"url": url})
        resp.raise_for_status()
        data = resp.json()
        if json_output:
            import json
            console.print(json.dumps(data, indent=2))
        else:
            console.print(f"[bold green]Shortened:[/bold green] {data['full_link']}")
            console.print(f"[bold]Visits:[/bold] {data['visits']}")
    except httpx.HTTPStatusError as exc:
        print_api_error(exc)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def info(
    link: str,
    token: Optional[str] = typer.Option(None, help="API token (or set L1NKZIP_TOKEN env var)"),
    limit: int = typer.Option(DEFAULT_LIMIT, help="Max number of URLs to search"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show info about a short link (target URL and visits). If --json is used, prints the full API response from /list/{token}."""
    token_val = get_token(token)
    try:
        resp = client.get(f"{API_BASE}/list/{token_val}", params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()
        found = None
        for item in data:
            if item.get("link") == link or item.get("full_link") == link:
                found = item
                break
        if json_output:
            import json
            console.print(json.dumps(data, indent=2))
            if found:
                console.print(f"[bold green]Found link:[/bold green] {link}")
            else:
                console.print(f"[red]No info found for link:[/red] {link}")
        else:
            if not found:
                console.print(f"[red]No info found for link:[/red] {link}")
                raise typer.Exit(1)
            table = Table(title="Link Info")
            table.add_column("Field")
            table.add_column("Value")
            table.add_row("Short Link", found["link"])
            table.add_row("Full URL", found["url"])
            table.add_row("Visits", str(found["visits"]))
            console.print(table)
    except httpx.HTTPStatusError as exc:
        print_api_error(exc)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def list(
    token: Optional[str] = typer.Option(None, help="API token (or set L1NKZIP_TOKEN env var)"),
    limit: int = typer.Option(DEFAULT_LIMIT, help="Max number of URLs to list"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """List all URLs (requires token). If --json is used, prints the full API response from /list/{token}."""
    token_val = get_token(token)
    try:
        resp = client.get(f"{API_BASE}/list/{token_val}", params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()
        if json_output:
            import json
            console.print(json.dumps(data, indent=2))
        else:
            table = Table(title="Shortened URLs")
            table.add_column("Short Link")
            table.add_column("Full URL")
            table.add_column("Visits")
            for item in data:
                table.add_row(item["full_link"], item["url"], str(item["visits"]))
            console.print(table)
    except httpx.HTTPStatusError as exc:
        print_api_error(exc)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


@app.command()
def update_phishtank(
    token: Optional[str] = typer.Option(None, help="API token (or set L1NKZIP_TOKEN env var)"),
    cleanup_days: int = typer.Option(DEFAULT_CLEANUP_DAYS, help="Days to keep old entries"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Update PhishTank DB (admin, requires token). If --json is used, prints the full API response from /phishtank/update/{token}."""
    token_val = get_token(token)
    try:
        resp = client.get(
            f"{API_BASE}/phishtank/update/{token_val}",
            params={"cleanup_days": cleanup_days},
        )
        resp.raise_for_status()
        data = resp.json()
        if json_output:
            import json
            console.print(json.dumps(data, indent=2))
        else:
            console.print(f"[bold green]PhishTank updated:[/bold green] {data.get('detail', str(data))}")
    except httpx.HTTPStatusError as exc:
        print_api_error(exc)
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")


if __name__ == "__main__":
    app()
    client.close()
