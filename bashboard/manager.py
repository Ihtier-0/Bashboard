import json
from pathlib import Path
from typing import Optional

from .script import Script

DEFAULT_CONFIG_FILE = Path.home() / ".config" / "bashboard" / "scripts.json"


class Manager:
    def __init__(self, config_path: Optional[Path] = None):
        path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        # Resolve so script paths and copied commands stay valid regardless
        # of the cwd Bashboard was launched from.
        self.config_path: Path = path.expanduser().absolute()
        self.scripts: list[Script] = []

    def _attach(self, script: Script) -> None:
        script.base_dir = str(self.config_path.parent)

    def load(self) -> None:
        if not self.config_path.exists():
            return
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            self.scripts = [Script.from_dict(d) for d in data]
        except (OSError, ValueError, KeyError):
            self.scripts = []
        for s in self.scripts:
            self._attach(s)

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = [s.to_dict() for s in self.scripts]
        self.config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, script: Script) -> None:
        self._attach(script)
        self.scripts.append(script)
        self.save()

    def remove(self, script: Script) -> None:
        if script.is_running:
            script.stop()
        self.scripts.remove(script)
        self.save()
