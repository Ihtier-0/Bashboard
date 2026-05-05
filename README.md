# Bashboard

Desktop GUI for running bash scripts on Linux (tested only on Ubuntu). Built with PySide6.

[Русская версия](README.ru.md)

## Features

- Script list with status dot — gray (idle), green (running), orange (waiting for stdin input)
- Per-row controls: Run, Stop, Copy command, Edit, Delete
- Live stdout / stderr in the right pane with ANSI color rendering
- Log persists across re-runs; Clear button to wipe it
- Per-script run stats: start time, elapsed, output size, exit code
- Search in the log (Ctrl+F, Enter / Shift+Enter to navigate, Esc to close)
- Send input to a running script's stdin (e.g. typing `yes`, pasting a token)
- "Waiting for input" detection by walking `/proc` and matching the fd 0 inode
- Script categories — drag one script onto another to group them; double-click to rename
- Inline script editor with Bash syntax highlighting; open in external editor via `$VISUAL`/`$EDITOR`
- Optional CLI arguments and working directory per script (arguments parsed via `shlex`)
- Parallel runs of the same script are disabled; editing is locked while running
- Light / Dark / System themes (Settings → Theme)
- English / Russian UI, default English (Settings → Language)
- `--config PATH` flag to point at a custom `scripts.json`

## Requirements

- Linux, tested only on Ubuntu (relies on `/proc` and `/bin/bash`)
- Python 3.10+
- PySide6, pygments (see `requirements.txt`)

## Install

```bash
git clone git@github.com:Ihtier-0/Bashboard.git
cd Bashboard
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
bash install.sh          # registers the .desktop entry and icon
```

To uninstall the desktop entry:

```bash
bash uninstall.sh
```

## Run

```bash
python main.py
# or, after install.sh:
# launch "Bashboard" from your application menu
```

## Configuration

- Scripts list: `~/.config/bashboard/scripts.json`
- UI settings (language, theme): `~/.config/bashboard/settings.json`

## Stack

- [PySide6](https://wiki.qt.io/Qt_for_Python) (LGPL)
- [pygments](https://pygments.org/) — Bash syntax highlighting in the editor
- Code formatted with [black](https://github.com/psf/black)
