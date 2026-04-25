# Bashboard

Десктопное GUI-приложение для запуска bash-скриптов на Linux (протестировано только на Ubuntu). Сделано на PySide6.

[English version](README.md)

## Возможности

- Список скриптов со статусным кружком — серый (не запущен), зелёный (выполняется), оранжевый (ожидает ввод в stdin)
- Кнопки в каждой строке: Run, Stop, Copy, Edit, Delete
- Живой вывод stdout / stderr в правой панели, сохраняется при переключении между скриптами
- Отправка строк в stdin запущенному скрипту (например, ввести `yes` или вставить токен)
- Опциональные аргументы CLI для каждого скрипта (парсятся через `shlex`)
- Параллельные запуски одного скрипта запрещены; редактирование заблокировано во время выполнения
- Определение «ждёт ввод» через обход `/proc` и сверку inode fd 0
- Интерфейс на английском / русском, по умолчанию английский (Settings → Language)

## Требования

- Linux, протестировано только на Ubuntu (используются `/proc` и `/bin/bash`)
- Python 3.10+

## Установка

```bash
git clone git@github.com:Ihtier-0/Bashboard.git
cd Bashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
python main.py
```

## Конфигурация

- Список скриптов: `~/.config/bashboard/scripts.json`
- Язык интерфейса: `~/.config/bashboard/settings.json`

## Стек

- [PySide6](https://wiki.qt.io/Qt_for_Python) (LGPL)
- Код отформатирован через [black](https://github.com/psf/black)
