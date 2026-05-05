import os
import platform
import shlex
from datetime import datetime
from typing import Optional

from PySide6.QtCore import QObject, QProcess, QTimer, Signal

LOG_LIMIT = 5000

CLEAR_TOKEN = "\x00CLEAR\x00"


def format_duration(seconds: float) -> str:
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    if s < 3600:
        return f"{s // 60}m{s % 60:02d}s"
    return f"{s // 3600}h{(s % 3600) // 60:02d}m"


def format_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    if n < 1024 * 1024 * 1024:
        return f"{n / (1024 * 1024):.1f} MB"
    return f"{n / (1024 * 1024 * 1024):.1f} GB"


# /proc/<pid>/syscall reports the syscall number as decimal (kernel format
# "%ld 0x%lx ..."). The read() syscall number is arch-specific.
_READ_SYSCALL_NR = {
    "x86_64": "0",
    "i686": "3",
    "i386": "3",
    "aarch64": "63",
    "armv7l": "3",
    "armv6l": "3",
    "riscv64": "63",
}.get(platform.machine(), "0")


class Script(QObject):
    log_appended = Signal(str)
    state_changed = Signal()

    def __init__(self, name: str, path: str, args: str = "", cwd: str = ""):
        super().__init__()
        self.name = name
        self.path = path
        self.args = args
        self.cwd = cwd
        self.base_dir: Optional[str] = None
        self.process: Optional[QProcess] = None
        self.log_lines: list[str] = []
        self.waiting_input: bool = False
        # Session-only stats (not persisted to scripts.json).
        self.run_count: int = 0
        self.last_started_at: Optional[datetime] = None
        self.last_finished_at: Optional[datetime] = None
        self.last_exit_code: Optional[int] = None
        self.bytes_received: int = 0

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

    @property
    def resolved_cwd(self) -> str:
        """Working directory for the QProcess. Explicit cwd wins; empty falls
        back to the script file's directory."""
        if self.cwd:
            if os.path.isabs(self.cwd) or not self.base_dir:
                return self.cwd
            return os.path.join(self.base_dir, self.cwd)
        return os.path.dirname(self.resolved_path)

    def start(self) -> None:
        if self.is_running:
            return

        self.run_count += 1
        self.last_started_at = datetime.now()
        self.last_finished_at = None
        self.last_exit_code = None
        self.bytes_received = 0
        ts = self.last_started_at.strftime("%Y-%m-%d %H:%M:%S")
        prefix = "\n" if self.log_lines else ""
        self._append(f"{prefix}--- Run {self.run_count} · {ts} ---\n")

        proc = QProcess(self)
        proc.setProgram("/bin/bash")
        proc.setArguments([self.resolved_path, *shlex.split(self.args)])
        cwd = self.resolved_cwd
        if cwd:
            proc.setWorkingDirectory(cwd)
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
        QTimer.singleShot(3000, self._kill_if_running)

    def _kill_if_running(self) -> None:
        if self.is_running:
            self.process.kill()

    def clear_log(self) -> None:
        self.log_lines.clear()
        self.log_appended.emit(CLEAR_TOKEN)

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
        raw = bytes(self.process.readAllStandardOutput())
        self.bytes_received += len(raw)
        self._append(raw.decode("utf-8", errors="replace"))

    def _append(self, data: str) -> None:
        for line in data.splitlines(keepends=True):
            self.log_lines.append(line)
        if len(self.log_lines) > LOG_LIMIT:
            del self.log_lines[: len(self.log_lines) - LOG_LIMIT]
        self.log_appended.emit(data)

    def _on_finished(self, code: int, _status) -> None:
        self._wait_timer.stop()
        self.waiting_input = False
        self.last_finished_at = datetime.now()
        self.last_exit_code = code
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
        d = {"name": self.name, "path": self.path, "args": self.args}
        if self.cwd:
            d["cwd"] = self.cwd
        return d

    @classmethod
    def from_dict(cls, data: dict) -> "Script":
        return cls(
            data["name"],
            data["path"],
            data.get("args", ""),
            data.get("cwd", ""),
        )


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
            if len(parts) >= 2 and parts[0] == _READ_SYSCALL_NR and parts[1] == "0x0":
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
