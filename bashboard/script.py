import os
import shlex
from typing import Optional

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

LOG_LIMIT = 5000

CLEAR_TOKEN = "\x00CLEAR\x00"


class Script(QObject):
    log_appended = Signal(str)
    state_changed = Signal()

    def __init__(self, name: str, path: str, args: str = ""):
        super().__init__()
        self.name = name
        self.path = path
        self.args = args
        self.base_dir: Optional[str] = None
        self.process: Optional[QProcess] = None
        self.log_lines: list[str] = []
        self.waiting_input: bool = False

        self._wait_timer = QTimer(self)
        self._wait_timer.setInterval(500)
        self._wait_timer.timeout.connect(self._poll_waiting)

    @property
    def is_running(self) -> bool:
        return self.process is not None and self.process.state() != QProcess.NotRunning

    @property
    def resolved_path(self) -> str:
        if os.path.isabs(self.path) or not self.base_dir:
            return self.path
        return os.path.join(self.base_dir, self.path)

    def start(self) -> None:
        if self.is_running:
            return
        self.log_lines.clear()
        self.log_appended.emit(CLEAR_TOKEN)

        proc = QProcess(self)
        proc.setProgram("/bin/bash")
        proc.setArguments([self.resolved_path, *shlex.split(self.args)])
        proc.setProcessChannelMode(QProcess.MergedChannels)
        proc.readyReadStandardOutput.connect(self._on_output)
        proc.finished.connect(self._on_finished)
        proc.errorOccurred.connect(self._on_error)

        self.process = proc
        proc.start()
        self.waiting_input = False
        self._wait_timer.start()
        self.state_changed.emit()

    def stop(self) -> None:
        if not self.is_running:
            return
        self.process.terminate()
        if not self.process.waitForFinished(3000):
            self.process.kill()
            self.process.waitForFinished(1000)

    def command(self) -> str:
        parts = ["bash", shlex.quote(self.resolved_path)]
        if self.args:
            parts.append(self.args)
        return " ".join(parts)

    def send_input(self, text: str) -> None:
        if not self.is_running:
            return
        if not text.endswith("\n"):
            text += "\n"
        self.process.write(text.encode("utf-8"))

    def _on_output(self) -> None:
        data = bytes(self.process.readAllStandardOutput()).decode(
            "utf-8", errors="replace"
        )
        self._append(data)

    def _append(self, data: str) -> None:
        for line in data.splitlines(keepends=True):
            self.log_lines.append(line)
        if len(self.log_lines) > LOG_LIMIT:
            del self.log_lines[: len(self.log_lines) - LOG_LIMIT]
        self.log_appended.emit(data)

    def _on_finished(self, code: int, _status) -> None:
        self._wait_timer.stop()
        self.waiting_input = False
        self._append(f"\n[exit code: {code}]\n")
        self.state_changed.emit()

    def _on_error(self, _error) -> None:
        self._wait_timer.stop()
        self.waiting_input = False
        if self.process is not None:
            self._append(f"\n[error: {self.process.errorString()}]\n")
        self.state_changed.emit()

    def _poll_waiting(self) -> None:
        if not self.is_running:
            return
        pid = self.process.processId()
        if pid <= 0:
            return
        new_state = _is_waiting_for_stdin(pid)
        if new_state != self.waiting_input:
            self.waiting_input = new_state
            self.state_changed.emit()

    def to_dict(self) -> dict:
        return {"name": self.name, "path": self.path, "args": self.args}

    @classmethod
    def from_dict(cls, data: dict) -> "Script":
        return cls(data["name"], data["path"], data.get("args", ""))


def _readlink(path: str) -> Optional[str]:
    try:
        return os.readlink(path)
    except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
        return None


def _is_waiting_for_stdin(root_pid: int) -> bool:
    """True if root_pid (or any descendant) is blocked on read() of fd 0,
    where that fd 0 is the same pipe inherited from root_pid (i.e. our QProcess
    stdin pipe). Avoids false positives for internal pipelines like `cat | grep`.

    Linux-only (reads /proc). On other systems silently returns False.
    """
    root_stdin = _readlink(f"/proc/{root_pid}/fd/0")
    if root_stdin is None:
        return False

    visited: set[int] = set()
    stack = [root_pid]
    while stack:
        pid = stack.pop()
        if pid in visited:
            continue
        visited.add(pid)
        try:
            with open(f"/proc/{pid}/syscall", "r") as fp:
                line = fp.read().strip()
        except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
            continue

        if line and not line.startswith("running"):
            parts = line.split()
            if len(parts) >= 2 and parts[1] == "0x0":
                proc_stdin = _readlink(f"/proc/{pid}/fd/0")
                if proc_stdin is not None and proc_stdin == root_stdin:
                    return True

        try:
            with open(f"/proc/{pid}/task/{pid}/children", "r") as fp:
                children = fp.read().split()
            stack.extend(int(c) for c in children if c.isdigit())
        except (FileNotFoundError, ProcessLookupError, PermissionError, OSError):
            continue

    return False
