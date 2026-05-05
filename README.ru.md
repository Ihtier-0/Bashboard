# Bashboard

Десктопное GUI-приложение для запуска bash-скриптов на Linux (протестировано только на Ubuntu). Сделано на PySide6.

[English version](README.md)

## Возможности

- Список скриптов со статусным кружком — серый (не запущен), зелёный (выполняется), оранжевый (ожидает ввод в stdin)
- Кнопки в каждой строке: Run, Stop, Copy, Edit, Delete
- Живой вывод stdout / stderr в правой панели с рендерингом ANSI-цветов
- Лог сохраняется между перезапусками; кнопка Clear для очистки
- Статистика по каждому запуску: время старта, длительность, объём вывода, код выхода
- Поиск в логе (Ctrl+F, Enter / Shift+Enter для навигации, Esc — закрыть)
- Отправка строк в stdin запущенному скрипту (например, ввести `yes` или вставить токен)
- Определение «ждёт ввод» через обход `/proc` и сверку inode fd 0
- Категории скриптов — перетащите один скрипт на другой для группировки; двойной клик — переименование
- Встроенный редактор скрипта с подсветкой синтаксиса Bash; открытие во внешнем редакторе через `$VISUAL`/`$EDITOR`
- Опциональные аргументы CLI и рабочая папка для каждого скрипта (аргументы парсятся через `shlex`)
- Параллельные запуски одного скрипта запрещены; редактирование заблокировано во время выполнения
- Темы оформления: Light / Dark / System (Settings → Theme)
- Интерфейс на английском / русском, по умолчанию английский (Settings → Language)
- Флаг `--config PATH` для указания пути к кастомному `scripts.json`

## Требования

- Linux, протестировано только на Ubuntu (используются `/proc` и `/bin/bash`)
- Python 3.10+
- PySide6, pygments (см. `requirements.txt`)

## Установка

```bash
git clone git@github.com:Ihtier-0/Bashboard.git
cd Bashboard
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
bash install.sh          # регистрирует .desktop-запись и иконку
```

Для удаления desktop-записи:

```bash
bash uninstall.sh
```

## Запуск

```bash
python main.py
# или после install.sh — запустите «Bashboard» из меню приложений
```

## Конфигурация

- Список скриптов: `~/.config/bashboard/scripts.json`
- Настройки интерфейса (язык, тема): `~/.config/bashboard/settings.json`

## Стек

- [PySide6](https://wiki.qt.io/Qt_for_Python) (LGPL)
- [pygments](https://pygments.org/) — подсветка синтаксиса Bash в редакторе
- Код отформатирован через [black](https://github.com/psf/black)
