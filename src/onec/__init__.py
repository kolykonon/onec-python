"""Описание конфигураций 1С:Предприятие на Python.

Библиотека генерирует выгрузку конфигурации в формате Конфигуратора
(«Выгрузить конфигурацию в файлы»), которую можно загрузить
в информационную базу.

Example:
    >>> from pathlib import Path
    >>> from onec import Catalog, Configuration, dump
    >>> cfg = Configuration(name="Склад", catalogs=[Catalog("Товары")])
    >>> dump(cfg, Path("out"))  # doctest: +SKIP

"""

from importlib.metadata import version

from onec.xml.dump import dump
from onec.xml.model import Catalog, Configuration, Language, LocalString

__version__ = version("onec-py")

__all__ = [
    "Catalog",
    "Configuration",
    "Language",
    "LocalString",
    "__version__",
    "dump",
]
