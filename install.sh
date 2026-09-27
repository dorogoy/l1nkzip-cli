#!/bin/sh
# Install l1nkzip with uv. Safe to re-run. No sudo.
set -eu

REPO_URL="git+https://github.com/dorogoy/l1nkzip-cli"
# PATH changes made so this script can find uv must not hide a missing
# entry in the caller's shell.
orig_path=$PATH

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Trying the official installer..."
  if ! command -v curl >/dev/null 2>&1; then
    echo "curl is required to install uv." >&2
    echo "Install uv, then re-run this script:" >&2
    echo "  https://docs.astral.sh/uv/getting-started/installation/" >&2
    exit 1
  fi
  curl -LsSf https://astral.sh/uv/install.sh | sh || true
  if [ -f "$HOME/.local/bin/env" ]; then
    # shellcheck disable=SC1091
    . "$HOME/.local/bin/env"
  elif [ -x "$HOME/.local/bin/uv" ]; then
    PATH="$HOME/.local/bin:$PATH"
    export PATH
  fi
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv is still not available." >&2
    echo "Install it from https://docs.astral.sh/uv/getting-started/installation/" >&2
    echo "Then add it to your shell rc, for example:" >&2
    echo '  export PATH="$HOME/.local/bin:$PATH"' >&2
    exit 1
  fi
fi

if [ -n "${INSTALL_DIR:-}" ]; then
  # A trailing slash would miss the PATH-component check below.
  bin_dir=${INSTALL_DIR%/}
  uv tool install --force --bin-dir "$bin_dir" "$REPO_URL"
else
  uv tool install --force "$REPO_URL"
  bin_dir=$(uv tool dir --bin)
fi

case ":$orig_path:" in
  *":$bin_dir:"*) ;;
  *)
    echo "l1nkzip is installed in $bin_dir, which is not on PATH."
    echo "Add this line to your shell rc:"
    echo "export PATH=\"$bin_dir:\$PATH\""
    ;;
esac
