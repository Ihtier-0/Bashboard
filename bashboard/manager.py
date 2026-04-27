import json
from pathlib import Path
from typing import Optional, Union

from .script import Script

DEFAULT_CONFIG_FILE = Path.home() / ".config" / "bashboard" / "scripts.json"


class Category:
    def __init__(self, name: str, scripts: Optional[list[Script]] = None):
        self.name = name
        self.scripts: list[Script] = scripts or []

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "scripts": [s.to_dict() for s in self.scripts],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Category":
        return cls(
            data["name"],
            [Script.from_dict(d) for d in data.get("scripts", [])],
        )


Item = Union[Script, Category]


class Manager:
    def __init__(self, config_path: Optional[Path] = None):
        path = Path(config_path) if config_path else DEFAULT_CONFIG_FILE
        # Resolve so script paths and copied commands stay valid regardless
        # of the cwd Bashboard was launched from.
        self.config_path: Path = path.expanduser().absolute()
        self.items: list[Item] = []

    def _attach(self, script: Script) -> None:
        script.base_dir = str(self.config_path.parent)

    @property
    def scripts(self) -> list[Script]:
        """Flat list of all scripts across categories — used by callers that
        only care about scripts (e.g. running-on-close check)."""
        result: list[Script] = []
        for item in self.items:
            if isinstance(item, Script):
                result.append(item)
            else:
                result.extend(item.scripts)
        return result

    def load(self) -> None:
        if not self.config_path.exists():
            return
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            self.items = []
            return

        items: list[Item] = []
        for raw in data:
            try:
                if "scripts" in raw:
                    cat = Category.from_dict(raw)
                    for s in cat.scripts:
                        self._attach(s)
                    items.append(cat)
                else:
                    s = Script.from_dict(raw)
                    self._attach(s)
                    items.append(s)
            except (KeyError, TypeError):
                continue
        self.items = items
        self._auto_flatten()

    def save(self) -> None:
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = [item.to_dict() for item in self.items]
        self.config_path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def add(self, script: Script) -> None:
        """Append a new script at top level."""
        self._attach(script)
        self.items.append(script)
        self.save()

    def remove(self, script: Script) -> None:
        if script.is_running:
            script.stop()
        for i, item in enumerate(self.items):
            if item is script:
                self.items.pop(i)
                self.save()
                return
            if isinstance(item, Category) and script in item.scripts:
                item.scripts.remove(script)
                self._auto_flatten()
                self.save()
                return

    def find_category(self, script: Script) -> Optional[Category]:
        for item in self.items:
            if isinstance(item, Category) and script in item.scripts:
                return item
        return None

    def _auto_flatten(self) -> None:
        """Promote single-script categories into top-level scripts."""
        new_items: list[Item] = []
        for item in self.items:
            if isinstance(item, Category) and len(item.scripts) <= 1:
                new_items.extend(item.scripts)
            else:
                new_items.append(item)
        self.items = new_items

    def set_items(self, items: list[Item]) -> None:
        """Replace the full item list (used after drag-drop reorders) and
        run the >1 invariant. Caller is responsible for calling save()."""
        for item in items:
            if isinstance(item, Script):
                self._attach(item)
            else:
                for s in item.scripts:
                    self._attach(s)
        self.items = items
        self._auto_flatten()
