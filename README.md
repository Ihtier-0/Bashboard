# Bashboard

Desktop GUI for running bash scripts on Linux (tested only on Ubuntu). Built with PySide6.

[Русская версия](README.ru.md)

## Features

- Script list with status dot — gray (idle), green (running), orange (waiting for stdin input)
- Per-row controls: Run, Stop, Copy command, Edit, Delete
- Live stdout / stderr in the right pane, preserved between selections
- Send input to a running script's stdin (e.g. typing `yes`, pasting a token)
- Optional CLI arguments per script (parsed via `shlex`)
- Parallel runs of the same script are disabled; editing is locked while running
- "Waiting for input" detection by walking `/proc` and matching the fd 0 inode
- English / Russian UI, default English (Settings → Language)

## Requirements

- Linux, tested only on Ubuntu (relies on `/proc` and `/bin/bash`)
- Python 3.10+

## Install

```bash
git clone git@github.com:Ihtier-0/Bashboard.git
cd Bashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Configuration

- Scripts list: `~/.config/bashboard/scripts.json`
- UI language: `~/.config/bashboard/settings.json`

## Stack

- [PySide6](https://wiki.qt.io/Qt_for_Python) (LGPL)
- Code formatted with [black](https://github.com/psf/black)
