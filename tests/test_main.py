import json
import os
from unittest.mock import Mock, patch

import pytest
import typer
from typer.testing import CliRunner

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

    def test_token_from_argument(self):
        """Test that token is taken from argument when provided."""
        with patch("main.typer.prompt") as mock_prompt:
            app(["info", "test-link", "--token", "test-token"], standalone_mode=False)
            # The token should be used without prompting
            mock_prompt.assert_not_called()

    def test_token_from_env(self):
        """Test that token is taken from environment variable when not provided as argument."""
        with patch.dict(os.environ, {"L1NKZIP_TOKEN": "env-token"}):
            with patch("main.typer.prompt") as mock_prompt:
                app(["info", "test-link"], standalone_mode=False)
                # The token should be used without prompting
                mock_prompt.assert_not_called()

    def test_token_from_prompt(self):
        """Test that token is prompted when not provided as argument or env var."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("main.L1NKZIP_TOKEN", None):
                with patch(
                    "main.typer.prompt", return_value="prompted-token"
                ) as mock_prompt:
                    app(["info", "test-link"], standalone_mode=False)
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

    def test_no_command_shows_help(self):
        """Test that running without command shows help."""
        result = runner.invoke(app, [])

        assert result.exit_code == 2
        assert "Usage:" in result.stderr
