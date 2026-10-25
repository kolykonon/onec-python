# onec-py

Python-библиотека для описания конфигураций 1С:Предприятие кодом.
Генерирует XML-выгрузку конфигурации и загружает её в информационную базу
через пакетный режим Конфигуратора.

> Проект на ранней стадии разработки, API может меняться.

## Установка

```bash
pip install onec-py
```

## Использование

```python
import uuid
from pathlib import Path

from onec import Configuration, LocalString, dump

cfg = Configuration(
    name="Склад",
    uuid=uuid.UUID("0b6b1c1e-6f43-4c49-9a0e-6f1d8a3c2e51"),
    synonym=LocalString.ru("Складской учёт"),
)
dump(cfg, Path("./out"))
```

В папке `out` появится выгрузка конфигурации в формате Конфигуратора
(`Configuration.xml`, `ConfigDumpInfo.xml`, `Languages/Русский.xml`).
Её можно загрузить в информационную базу командой «Загрузить конфигурацию
из файлов» или в пакетном режиме через `/LoadConfigFromFiles`.

UUID всех внутренних объектов вычисляются из `uuid` конфигурации. Если его
не указать, при каждом запуске будет сгенерирован новый и UUID в выгрузке
изменятся, поэтому для повторяемых сборок задавайте `uuid` явно.

Версия библиотеки:

```bash
onec version
```

## Разработка

```bash
uv sync
uv run pytest -m "not platform"
uv run ruff check . && uv run ruff format .
uv run mypy
```
