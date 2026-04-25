import json
from pathlib import Path

from .script import Script


CONFIG_DIR = Path.home() / ".config" / "bashboard"
CONFIG_FILE = CONFIG_DIR / "scripts.json"


class Manager:
    def __init__(self):
        self.scripts: list[Script] = []

    def load(self) -> None:
        if not CONFIG_FILE.exists():
            return
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            self.scripts = [Script.from_dict(d) for d in data]
        except (OSError, ValueError, KeyError):
            self.scripts = []

    def save(self) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        data = [s.to_dict() for s in self.scripts]
        CONFIG_FILE.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, script: Script) -> None:
        self.scripts.append(script)
        self.save()

    def remove(self, script: Script) -> None:
        if script.is_running:
            script.stop()
        self.scripts.remove(script)
        self.save()
