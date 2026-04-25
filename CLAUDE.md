# Bashboard — project notes

## What this is

Desktop GUI to run, monitor, and interactively input data into bash scripts on Linux (tested only on Ubuntu). Single-user local app, not a server. Python + PySide6.

## Tech stack

- Python 3.10+
- PySide6 (Qt for Python, LGPL)
- Standard library only otherwise

## Code layout

- `main.py` — entry point. Creates `QApplication`, loads settings, sets language, opens `MainWindow`.
- `bashboard/main_window.py` — `QMainWindow`, menubar, list/log split, all dispatch to scripts.
- `bashboard/script.py` — `Script` class wraps a `QProcess`. Owns the log buffer and the waiting-for-stdin polling via `/proc`.
- `bashboard/manager.py` — JSON persistence of the script list at `~/.config/bashboard/scripts.json`.
- `bashboard/settings.py` — JSON persistence of UI settings at `~/.config/bashboard/settings.json`.
- `bashboard/script_item.py` — custom row widget: status dot + name + Run / Stop / Copy / Edit / Delete buttons.
- `bashboard/log_panel.py` — log view + stdin input field.
- `bashboard/edit_dialog.py` — modal for adding / editing a script.
- `bashboard/i18n.py` — gettext-style translator with English / Russian dictionaries.

## Conventions

- Format with `black` (default 4-space indent, line length 88). Run `python -m black main.py bashboard/` before committing.
- All code, commit messages, and `CLAUDE.md` are in English.
- `README.md` is mirrored in `README.ru.md` (same content, Russian).
- All user-facing strings are wrapped in `tr()` from `bashboard.i18n`. The English string is the key; Russian translation lives in `_TRANSLATIONS["ru"]`. Missing keys fall back to the English string.
- Widgets that show translatable text connect to `translator.language_changed` and re-apply `tr()` on retranslate.

## Architecture decisions

- "Waiting for input" detection: walks the `/proc` tree from the QProcess root PID, checks `/proc/<pid>/syscall` for any descendant blocked on a syscall with `arg0 == 0x0` (fd 0), and confirms the fd 0 inode matches the root's. The inode check avoids false positives from internal pipelines like `cat | grep` where the inner process's fd 0 is a different pipe.
- Stop sequence: `SIGTERM`, wait 3 seconds, then `SIGKILL`.
- Parallel runs of the same script are disabled. While running: Run is greyed, Stop is enabled, Edit is locked.
- Log buffer is in-memory only — capped at 5000 lines per script, view widget capped at 10000 blocks. No on-disk log persistence yet.
- On window close with running scripts: confirmation dialog, then graceful stop on Yes.

## Linux-only assumptions

- `/bin/bash` as interpreter (hardcoded in `Script.start`).
- `/proc/<pid>/syscall`, `/proc/<pid>/task/<pid>/children`, `/proc/<pid>/fd/0` for stdin-wait detection.
- On non-Linux the app launches but Run fails (no `/bin/bash`) and the waiting-for-input detection silently no-ops.

## Things to avoid

- Don't add backwards-compatibility shims, feature flags, or `Optional` parameters for situations that can't happen.
- Don't add comments that just restate the code.
- Don't introduce new dependencies without a clear reason — stdlib + PySide6 only.

## Future ideas (not in scope yet)

- Save logs to disk; browse history of past runs.
- Detach process from GUI lifetime (closing the window keeps scripts running, reattach on next launch).
- System tray icon.
- Application icon, `.desktop` file, deb / AppImage packaging.
- More UI languages.
