#!/usr/bin/env bash
# Undo install.sh — removes the .desktop entry and icon for the current user.
set -euo pipefail

DESKTOP="$HOME/.local/share/applications/bashboard.desktop"
ICON="$HOME/.local/share/icons/hicolor/scalable/apps/bashboard.svg"

rm -f "$DESKTOP" "$ICON"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

echo "Removed Bashboard desktop entry and icon."
