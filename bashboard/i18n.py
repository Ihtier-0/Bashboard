from PySide6.QtCore import QObject, Signal

SUPPORTED_LANGUAGES = ["en", "ru"]
DEFAULT_LANGUAGE = "en"


_TRANSLATIONS = {
    "ru": {
        # Main window
        "Scripts": "Скрипты",
        "+ Add": "+ Добавить",
        "File": "Файл",
        "Settings": "Настройки",
        "Language": "Язык",
        "Theme": "Тема",
        "New category": "Новая категория",
        "Category name:": "Название категории:",
        "Rename category": "Переименовать категорию",
        "System": "Системная",
        "Light": "Светлая",
        "Dark": "Тёмная",
        "Add script…": "Добавить скрипт…",
        "Quit": "Выход",
        "Error": "Ошибка",
        "Specify name and path.": "Укажите название и путь к скрипту.",
        "Specify a name.": "Укажите название.",
        "Specify a file path or type the script content.": (
            "Укажите путь к файлу или напечатайте содержимое скрипта."
        ),
        "Script is running": "Скрипт запущен",
        "Stop the script before editing.": "Остановите скрипт перед редактированием.",
        "Delete": "Удалить",
        "Delete '{name}' from the list?\n(The script file on disk will remain.)": (
            "Удалить «{name}» из списка?\n(Файл скрипта на диске останется.)"
        ),
        "Close Bashboard": "Закрыть Bashboard",
        "{count} script(s) running. Stop them and exit?": (
            "Запущено скриптов: {count}. Остановить и выйти?"
        ),
        "Copied: {cmd}": "Скопировано: {cmd}",
        # Log panel
        "Logs": "Логи",
        "Logs — {name}": "Логи — {name}",
        "Send to stdin of the running script (Enter to send)": (
            "Ввод в stdin запущенного скрипта (Enter — отправить)"
        ),
        "Send": "Отправить",
        "Clear": "Очистить",
        # Script item
        "Run": "Запустить",
        "Stop": "Остановить",
        "Copy command to clipboard": "Копировать команду в буфер",
        "Edit": "Редактировать",
        "Not running": "Не запущен",
        "Running": "Выполняется",
        "Waiting for input on stdin": "Ожидает ввод в stdin",
        # Edit dialog
        "Script": "Скрипт",
        "Name:": "Название:",
        "File:": "Файл:",
        "Arguments:": "Аргументы:",
        "Browse…": "Обзор…",
        "e.g. Backup DB": "Например: Backup DB",
        "Select bash script": "Выберите bash-скрипт",
        "Working dir:": "Рабочая папка:",
        "(default: directory of the script)": "(по умолчанию: папка скрипта)",
        "Select working directory": "Выберите рабочую папку",
        "Content:": "Содержимое:",
        "Open in external editor": "Открыть во внешнем редакторе",
        "Unsaved changes": "Несохранённые изменения",
        "Discard inline changes and open in external editor?": (
            "Отбросить правки в окне и открыть во внешнем редакторе?"
        ),
        "Discard typed content and load the picked file?": (
            "Отбросить набранное и загрузить выбранный файл?"
        ),
    }
}


class _Translator(QObject):
    language_changed = Signal()

    def __init__(self):
        super().__init__()
        self._current = DEFAULT_LANGUAGE

    @property
    def current(self) -> str:
        return self._current

    def set_language(self, lang: str) -> None:
        if lang not in SUPPORTED_LANGUAGES:
            lang = DEFAULT_LANGUAGE
        if lang != self._current:
            self._current = lang
            self.language_changed.emit()


translator = _Translator()


def tr(s: str) -> str:
    if translator.current == "en":
        return s
    return _TRANSLATIONS.get(translator.current, {}).get(s, s)
