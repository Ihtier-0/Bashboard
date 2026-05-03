#!/usr/bin/env bash
# Register Bashboard with the desktop environment for the current user.
# Idempotent: safe to re-run after a `git pull` or moving the repo.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"

if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
    echo "error: $ROOT/.venv/bin/python not found." >&2
    echo "Create the venv first (see README): python3 -m venv .venv && \\" >&2
    echo "    .venv/bin/pip install -r requirements.txt" >&2
    exit 1
fi

mkdir -p "$DESKTOP_DIR" "$ICON_DIR"

cp "$ROOT/icons/bashboard.svg" "$ICON_DIR/bashboard.svg"

sed -e "s|@PYTHON@|$ROOT/.venv/bin/python|g" \
    -e "s|@MAIN@|$ROOT/main.py|g" \
    "$ROOT/bashboard.desktop.in" > "$DESKTOP_DIR/bashboard.desktop"
chmod 644 "$DESKTOP_DIR/bashboard.desktop"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "Installed for $USER:"
echo "  $DESKTOP_DIR/bashboard.desktop"
echo "  $ICON_DIR/bashboard.svg"
echo
echo "Bashboard should now appear in your application menu."
