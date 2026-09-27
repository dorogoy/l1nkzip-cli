import json
import os
import shutil
import subprocess
import sys
import urllib.error
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

import main
from main import api_request, app, is_valid_url

runner = CliRunner()


class TestURLValidation:
    """Test URL validation function."""

    def test_valid_urls(self):
        """Test that valid URLs are accepted."""
        valid_urls = [
            "https://example.com",
            "http://example.com",
            "https://example.com/path",
            "https://example.com/path?query=value",
            "https://example.com:8080",
            "https://subdomain.example.com",
        ]

        for url in valid_urls:
            assert is_valid_url(url), f"URL should be valid: {url}"

    def test_invalid_urls(self):
        """Test that invalid URLs are rejected."""
        invalid_urls = [
            "not-a-url",
            "just some text",
            "ftp://example.com",
            "example.com",
            "://example.com",
            "",
        ]

        for url in invalid_urls:
            assert not is_valid_url(url), f"URL should be invalid: {url}"


class TestGetToken:
    """Test token retrieval function."""

    @patch("main.api_request")
    def test_token_from_argument(self, mock_api_request):
        """Test that token is taken from argument when provided."""
        mock_api_request.return_value = []  # Simulate API call
        with patch("main.typer.prompt") as mock_prompt:
            runner.invoke(app, ["info", "test-link", "--token", "test-token"])
            # The token should be used without prompting
            mock_prompt.assert_not_called()

    @patch("main.api_request")
    def test_token_from_env(self, mock_api_request):
        """Test that token is taken from environment variable when not provided as argument."""
        mock_api_request.return_value = []  # Simulate API call
        with (
            patch.dict(os.environ, {"L1NKZIP_TOKEN": "env-token"}),
            patch("main.typer.prompt") as mock_prompt,
        ):
            runner.invoke(app, ["info", "test-link"])
            # The token should be used without prompting
            mock_prompt.assert_not_called()

    @patch("main.api_request")
    def test_token_from_prompt(self, mock_api_request):
        """Test that token is prompted when not provided as argument or env var."""
        mock_api_request.return_value = []  # Simulate API call
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("main.typer.prompt", return_value="prompted-token") as mock_prompt,
        ):
            runner.invoke(app, ["info", "test-link"])
            # Should prompt for token
            mock_prompt.assert_called_once()


class TestShortenCommand:
    """Test the shorten command."""

    @patch("main.api_request")
    def test_shorten_valid_url(self, mock_api_request):
        """Test shortening a valid URL."""
        mock_api_request.return_value = {
            "link": "abc123",
            "full_link": "https://l1nk.zip/abc123",
            "url": "https://example.com",
            "visits": 0,
        }

        result = runner.invoke(app, ["shorten", "https://example.com"])

        assert result.exit_code == 0
        assert "Shortened: https://l1nk.zip/abc123" in result.stdout
        assert "Visits: 0" in result.stdout
        mock_api_request.assert_called_once_with(
            "POST", "/url", json={"url": "https://example.com"}
        )

    @patch("main.api_request")
    def test_shorten_json_output(self, mock_api_request):
        """Test shortening a URL with JSON output."""
        mock_api_request.return_value = {
            "link": "abc123",
            "full_link": "https://l1nk.zip/abc123",
            "url": "https://example.com",
            "visits": 0,
        }

        result = runner.invoke(app, ["shorten", "https://example.com", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["link"] == "abc123"
        assert data["full_link"] == "https://l1nk.zip/abc123"
        mock_api_request.assert_called_once_with(
            "POST", "/url", json={"url": "https://example.com"}
        )

    def test_shorten_invalid_url(self):
        """Test shortening an invalid URL."""
        result = runner.invoke(app, ["shorten", "not-a-url"])

        assert result.exit_code == 1
        assert "Invalid URL:" in result.stdout

    @patch("main.api_request")
    def test_shorten_api_error(self, mock_api_request):
        """Test handling API errors during URL shortening."""
        mock_api_request.side_effect = SystemExit(1)

        with patch("main.console.print"):
            result = runner.invoke(app, ["shorten", "https://example.com"])
            # Should handle the error gracefully
            assert result.exit_code == 1


class TestInfoCommand:
    """Test the info command."""

    @patch("main.api_request")
    def test_info_found_link(self, mock_api_request):
        """Test getting info for a found link."""
        mock_api_request.return_value = [
            {
                "link": "abc123",
                "full_link": "https://l1nk.zip/abc123",
                "url": "https://example.com",
                "visits": 5,
            },
            {
                "link": "def456",
                "full_link": "https://l1nk.zip/def456",
                "url": "https://google.com",
                "visits": 10,
            },
        ]

        result = runner.invoke(app, ["info", "abc123", "--token", "test-token"])

        assert result.exit_code == 0
        assert "Link Info" in result.stdout
        assert "Short Link" in result.stdout
        assert "Full URL" in result.stdout
        assert "Visits" in result.stdout
        mock_api_request.assert_called_once_with(
            "GET", "/list/test-token", params={"limit": 100}
        )

    @patch("main.api_request")
    def test_info_json_output(self, mock_api_request):
        """Test getting info with JSON output."""
        mock_api_request.return_value = [
            {
                "link": "abc123",
                "full_link": "https://l1nk.zip/abc123",
                "url": "https://example.com",
                "visits": 5,
            }
        ]

        result = runner.invoke(
            app, ["info", "abc123", "--token", "test-token", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["link"] == "abc123"

    @patch("main.api_request")
    def test_info_not_found(self, mock_api_request):
        """Test getting info for a non-existent link."""
        mock_api_request.return_value = [
            {
                "link": "def456",
                "full_link": "https://l1nk.zip/def456",
                "url": "https://google.com",
                "visits": 10,
            }
        ]

        result = runner.invoke(app, ["info", "abc123", "--token", "test-token"])

        assert result.exit_code == 1
        assert "No info found for link:" in result.stdout

    @patch("main.api_request")
    def test_info_with_limit(self, mock_api_request):
        """Test getting info with custom limit."""
        mock_api_request.return_value = []

        result = runner.invoke(
            app, ["info", "abc123", "--token", "test-token", "--limit", "50"]
        )

        assert result.exit_code == 1  # Link not found
        mock_api_request.assert_called_once_with(
            "GET", "/list/test-token", params={"limit": 50}
        )


class TestListCommand:
    """Test the list command."""

    @patch("main.api_request")
    def test_list_urls(self, mock_api_request):
        """Test listing URLs."""
        mock_api_request.return_value = [
            {
                "link": "abc123",
                "full_link": "https://l1nk.zip/abc123",
                "url": "https://example.com",
                "visits": 5,
            },
            {
                "link": "def456",
                "full_link": "https://l1nk.zip/def456",
                "url": "https://google.com",
                "visits": 10,
            },
        ]

        result = runner.invoke(app, ["list", "--token", "test-token"])

        assert result.exit_code == 0
        assert "Shortened URLs" in result.stdout
        assert "https://l1nk.zip/abc123" in result.stdout
        assert "https://l1nk.zip/def456" in result.stdout
        mock_api_request.assert_called_once_with(
            "GET", "/list/test-token", params={"limit": 100}
        )

    @patch("main.api_request")
    def test_list_json_output(self, mock_api_request):
        """Test listing URLs with JSON output."""
        mock_api_request.return_value = [
            {
                "link": "abc123",
                "full_link": "https://l1nk.zip/abc123",
                "url": "https://example.com",
                "visits": 5,
            }
        ]

        result = runner.invoke(app, ["list", "--token", "test-token", "--json"])

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert len(data) == 1
        assert data[0]["link"] == "abc123"

    @patch("main.api_request")
    def test_list_with_limit(self, mock_api_request):
        """Test listing URLs with custom limit."""
        mock_api_request.return_value = []

        result = runner.invoke(app, ["list", "--token", "test-token", "--limit", "50"])

        assert result.exit_code == 0
        mock_api_request.assert_called_once_with(
            "GET", "/list/test-token", params={"limit": 50}
        )


class TestUpdatePhishtankCommand:
    """Test the update-phishtank command."""

    @patch("main.api_request")
    def test_update_phishtank(self, mock_api_request):
        """Test updating PhishTank database."""
        mock_api_request.return_value = {"detail": "PhishTank updated successfully"}

        result = runner.invoke(app, ["update-phishtank", "--token", "test-token"])

        assert result.exit_code == 0
        assert "PhishTank updated:" in result.stdout
        mock_api_request.assert_called_once_with(
            "GET", "/phishtank/update/test-token", params={"cleanup_days": 5}
        )

    @patch("main.api_request")
    def test_update_phishtank_json_output(self, mock_api_request):
        """Test updating PhishTank with JSON output."""
        mock_api_request.return_value = {"detail": "PhishTank updated successfully"}

        result = runner.invoke(
            app, ["update-phishtank", "--token", "test-token", "--json"]
        )

        assert result.exit_code == 0
        data = json.loads(result.stdout)
        assert data["detail"] == "PhishTank updated successfully"

    @patch("main.api_request")
    def test_update_phishtank_with_cleanup_days(self, mock_api_request):
        """Test updating PhishTank with custom cleanup days."""
        mock_api_request.return_value = {"detail": "PhishTank updated successfully"}

        result = runner.invoke(
            app, ["update-phishtank", "--token", "test-token", "--cleanup-days", "10"]
        )

        assert result.exit_code == 0
        mock_api_request.assert_called_once_with(
            "GET", "/phishtank/update/test-token", params={"cleanup_days": 10}
        )


class TestAPIRequest:
    """Test the api_request helper function."""

    @patch("main.client")
    def test_successful_request(self, mock_client):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_client.request.return_value = mock_response

        result = api_request("GET", "/test", token="test-token")

        assert result == {"success": True}
        mock_client.request.assert_called_once_with(
            "GET", "/test", headers={"Authorization": "Bearer test-token"}
        )

    @patch("main.client")
    def test_request_without_token(self, mock_client):
        """Test API request without token."""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True}
        mock_client.request.return_value = mock_response

        result = api_request("GET", "/test")

        assert result == {"success": True}
        mock_client.request.assert_called_once_with("GET", "/test", headers={})

    @patch("main.client")
    @patch("main.console.print")
    def test_http_status_error(self, mock_print, mock_client):
        """Test handling HTTP status errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.json.return_value = {"detail": "Not found"}
        mock_response.text = "Not found"
        mock_response.raise_for_status.side_effect = Mock()

        # Create a proper HTTPStatusError
        from httpx import HTTPStatusError

        error = HTTPStatusError("Not found", request=Mock(), response=mock_response)
        mock_client.request.side_effect = error

        with pytest.raises(typer.Exit):
            api_request("GET", "/test", token="test-token")

        mock_print.assert_called_once()
        assert "HTTP 404:" in mock_print.call_args[0][0]

    @patch("main.client")
    @patch("main.console.print")
    def test_request_error(self, mock_print, mock_client):
        """Test handling request errors."""
        from httpx import RequestError

        error = RequestError("Network error", request=Mock())
        mock_client.request.side_effect = error

        with pytest.raises(typer.Exit):
            api_request("GET", "/test", token="test-token")

        mock_print.assert_called_once()
        assert "Network error:" in mock_print.call_args[0][0]


class TestAPIEndpointConfiguration:
    """Test API endpoint configuration."""

    def test_api_base_default(self):
        """Test API_BASE uses default when no env var is set."""
        with patch.dict(os.environ, {}, clear=True):
            # Need to reload the module to pick up env changes
            import importlib

            import main

            importlib.reload(main)
            assert main.API_BASE == "https://l1nk.zip"

    def test_api_base_from_env(self):
        """Test API_BASE uses environment variable when set."""
        test_url = "http://custom-api.example.com"
        with patch.dict(os.environ, {"L1NKZIP_API_URL": test_url}):
            # Need to reload the module to pick up env changes
            import importlib

            import main

            importlib.reload(main)
            assert main.API_BASE == test_url

    def test_client_uses_configured_base_url(self):
        """Test that HTTP client uses the configured base URL."""
        test_url = "http://custom-api.example.com"
        with patch.dict(os.environ, {"L1NKZIP_API_URL": test_url}):
            # Need to reload the module to pick up env changes
            import importlib

            import main

            importlib.reload(main)

            # Verify the API_BASE was set correctly
            assert main.API_BASE == test_url

            # The client should have been created with the correct base URL
            assert main.client.base_url == test_url


class TestCLIIntegration:
    """Test CLI integration."""

    def test_help_command(self):
        """Test help command."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "shorten" in result.stdout
        assert "info" in result.stdout
        assert "list" in result.stdout
        assert "update-phishtank" in result.stdout
        assert "Update l1nkzip" in result.stdout
        assert "Print the current version" in result.stdout

    def test_no_command_shows_help(self):
        """Test that running without command shows help."""
        result = runner.invoke(app, [])

        assert result.exit_code == 2
        assert "Usage:" in result.stderr


class TestVersionAndUpdate:
    """Version reporting, the update notice, and self-update."""

    def test_version_files_match(self):
        root = Path(__file__).resolve().parents[1]
        version_line = (root / "VERSION").read_text(encoding="utf-8").strip()
        assert version_line.split()[0] == main.VERSION
        project = (root / "pyproject.toml").read_text(encoding="utf-8")
        assert f'version = "{main.VERSION}"' in project

    def test_version_command(self):
        result = runner.invoke(app, ["version"])
        assert result.exit_code == 0
        assert result.stdout.strip() == main.VERSION

    def test_version_flag(self):
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert result.stdout.strip() == main.VERSION

    def test_is_newer(self):
        assert main._is_newer("0.2.0", "0.1.0")
        assert main._is_newer("0.1.1", "0.1")
        assert not main._is_newer("0.1.0", "0.1.0")
        assert not main._is_newer("0.1.0", "0.2.0")
        assert not main._is_newer("0.1", "0.1.0")

    @patch("main.api_request")
    def test_notice_leaves_json_stdout_intact(
        self, mock_api_request, monkeypatch, tmp_path: Path
    ):
        monkeypatch.delenv("L1NKZIP_NO_UPDATE_CHECK", raising=False)
        cache = tmp_path / "update-check.json"
        cache.write_text(
            json.dumps({"checked": 10**10, "remote": "9.9.9"}),
            encoding="utf-8",
        )
        monkeypatch.setattr(main, "_cache_file", lambda: cache)
        mock_api_request.return_value = {
            "link": "abc123",
            "full_link": "https://l1nk.zip/abc123",
            "url": "https://example.com",
            "visits": 0,
        }
        result = runner.invoke(app, ["shorten", "https://example.com", "--json"])
        assert result.exit_code == 0
        assert json.loads(result.stdout)["link"] == "abc123"
        assert "Update available: 0.1.0 -> 9.9.9" in result.stderr

    def test_notice_from_cache(self, monkeypatch, tmp_path: Path):
        monkeypatch.delenv("L1NKZIP_NO_UPDATE_CHECK", raising=False)
        cache = tmp_path / "update-check.json"
        cache.write_text(
            json.dumps({"checked": 10**10, "remote": "9.9.9"}),
            encoding="utf-8",
        )
        monkeypatch.setattr(main, "_cache_file", lambda: cache)
        printed: list[str] = []
        monkeypatch.setattr(main.notice, "print", lambda msg: printed.append(msg))
        main.maybe_check_update()
        assert printed
        assert "0.1.0 -> 9.9.9" in printed[0]
        assert "l1nkzip update" in printed[0]

    def test_corrupt_cache_is_replaced(self, monkeypatch, tmp_path: Path):
        monkeypatch.delenv("L1NKZIP_NO_UPDATE_CHECK", raising=False)
        cache = tmp_path / "update-check.json"
        cache.write_text("[1, 2]", encoding="utf-8")
        monkeypatch.setattr(main, "_cache_file", lambda: cache)
        calls = {"n": 0}

        class _Body:
            def read(self, _n: int = -1) -> bytes:
                return b"9.9.9\n"

        @contextmanager
        def _open(*_args: object, **_kwargs: object):
            calls["n"] += 1
            yield _Body()

        monkeypatch.setattr(main.urllib.request, "urlopen", _open)
        main.maybe_check_update()
        assert calls["n"] == 1
        assert json.loads(cache.read_text(encoding="utf-8"))["remote"] == "9.9.9"

    def test_offline_check_is_cached(self, monkeypatch, tmp_path: Path):
        monkeypatch.delenv("L1NKZIP_NO_UPDATE_CHECK", raising=False)
        cache = tmp_path / "update-check.json"
        monkeypatch.setattr(main, "_cache_file", lambda: cache)
        calls = {"n": 0}

        def boom(*_args, **_kwargs):
            calls["n"] += 1
            raise urllib.error.URLError("offline")

        monkeypatch.setattr(main.urllib.request, "urlopen", boom)
        main.maybe_check_update()
        main.maybe_check_update()
        assert calls["n"] == 1
        saved = json.loads(cache.read_text(encoding="utf-8"))
        assert saved["remote"] is None

    def test_env_disables_check(self, monkeypatch, tmp_path: Path):
        monkeypatch.setenv("L1NKZIP_NO_UPDATE_CHECK", "1")
        cache = tmp_path / "missing.json"
        monkeypatch.setattr(main, "_cache_file", lambda: cache)

        def boom(*_args, **_kwargs):
            raise AssertionError("network")

        monkeypatch.setattr(main.urllib.request, "urlopen", boom)
        main.maybe_check_update()
        assert not cache.exists()

    def test_download_replace(self, monkeypatch, tmp_path: Path):
        target = tmp_path / "l1nkzip"
        target.write_text("old\n", encoding="utf-8")
        payload = b'VERSION = "1.2.3"\nprint("hi")\n'

        class _Body:
            def read(self) -> bytes:
                return payload

        @contextmanager
        def _open(*_args: object, **_kwargs: object):
            yield _Body()

        monkeypatch.setattr(main.urllib.request, "urlopen", _open)
        assert main._download_replace(target) == "1.2.3"
        assert 'VERSION = "1.2.3"' in target.read_text(encoding="utf-8")
        assert os.access(target, os.X_OK)

    def test_download_replace_rejects_missing_version(
        self, monkeypatch, tmp_path: Path
    ):
        target = tmp_path / "l1nkzip"
        target.write_text("old\n", encoding="utf-8")

        class _Body:
            def read(self, _n: int = -1) -> bytes:
                return b"<html>nope</html>\n"

        @contextmanager
        def _open(*_args: object, **_kwargs: object):
            yield _Body()

        monkeypatch.setattr(main.urllib.request, "urlopen", _open)
        with pytest.raises(ValueError, match="VERSION"):
            main._download_replace(target)
        assert target.read_text(encoding="utf-8") == "old\n"

    def test_update_command_rewrites_file(self, monkeypatch):
        monkeypatch.setattr(main, "_is_uv_tool_install", lambda: False)
        monkeypatch.setattr(main, "_download_replace", lambda _target: "0.2.0")
        result = runner.invoke(app, ["update"])
        assert result.exit_code == 0
        assert f"{main.VERSION} -> 0.2.0" in result.stdout

    def test_update_command_uses_uv(self, monkeypatch):
        calls: list[str] = []
        monkeypatch.setattr(main, "_is_uv_tool_install", lambda: True)
        monkeypatch.setattr(main, "_uv_reinstall", lambda: calls.append("uv"))
        monkeypatch.setattr(main, "_installed_version", lambda: "0.9.0")
        result = runner.invoke(app, ["update"])
        assert result.exit_code == 0
        assert calls == ["uv"]
        assert f"{main.VERSION} -> 0.9.0" in result.stdout

    def test_uv_reinstall_forces_git_install(self, monkeypatch):
        seen: dict[str, list[str]] = {}

        def fake_run(cmd, **_kwargs):
            seen["cmd"] = cmd

            class _Proc:
                returncode = 0

            return _Proc()

        monkeypatch.setattr(main.subprocess, "run", fake_run)
        main._uv_reinstall()
        assert seen["cmd"] == [
            "uv",
            "tool",
            "install",
            "--force",
            main._GIT_TOOL,
        ]

    def test_uv_tool_detects_shim(self, monkeypatch, tmp_path: Path):
        shim = tmp_path / "l1nkzip"
        shim.write_text("#!/bin/sh\n", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", [str(shim)])

        def which(name: str) -> str | None:
            if name in {"uv", "l1nkzip"}:
                return str(shim)
            return None

        monkeypatch.setattr(shutil, "which", which)

        def fake_run(_cmd, **_kwargs):
            class _Proc:
                returncode = 0
                stdout = "l1nkzip v0.1.0\n- l1nkzip\n"

            return _Proc()

        monkeypatch.setattr(subprocess, "run", fake_run)
        assert main._is_uv_tool_install()

    def test_plain_file_is_not_a_uv_tool(self, monkeypatch, tmp_path: Path):
        shim = tmp_path / "l1nkzip"
        shim.write_text("#!/bin/sh\n", encoding="utf-8")
        monkeypatch.setattr(sys, "argv", ["main.py"])
        monkeypatch.setattr(
            shutil,
            "which",
            lambda name: str(shim) if name in {"uv", "l1nkzip"} else None,
        )
        assert not main._is_uv_tool_install()
