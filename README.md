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
