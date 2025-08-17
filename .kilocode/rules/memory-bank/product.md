# L1nkZip CLI Product Documentation

## Why This Project Exists
To provide a command-line interface for the L1nkZip URL shortener service, enabling users to interact with the API directly from their terminal without needing a browser.

## Problems Solved
1. Terminal-based URL shortening and management
2. Quick access to link analytics
3. Administrative functions (PhishTank updates)
4. Automation-friendly API interactions

## How It Should Work
1. Users install the CLI via simple curl command
2. Execute commands for:
   - `shorten`: Create short URLs
   - `info`: Get link details
   - `list`: View all user's shortened URLs
   - `update-phishtank`: Refresh phishing database
3. Beautiful terminal output using Rich
4. Token-based authentication via env var or prompt

## User Experience Goals
- Intuitive command structure
- Instant feedback with formatted output
- JSON support for machine-readable output
- Secure token handling
