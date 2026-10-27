"""Запись конфигурации в папку в формате выгрузки Конфигуратора.

Раскладывает файлы так же, как команда «Выгрузить конфигурацию в файлы»
в иерархическом формате: ``Configuration.xml`` в корне, объекты по папкам
своих видов (``Languages/``, ``Catalogs/``).
"""

from pathlib import Path

from onec.metadata import Configuration
from onec.xml.builders import build_child_object, build_configuration, build_dump_info
from onec.xml.constants import CONFIGURATION_FILE, DUMP_INFO_FILE
from onec.xml.writer import write_xml


def dump(cfg: Configuration, out_dir: Path) -> None:
    """Записывает конфигурацию в формате выгрузки Конфигуратора.

    Результат можно загрузить в информационную базу командой
    «Загрузить конфигурацию из файлов» или в пакетном режиме
    через ``/LoadConfigFromFiles``.

    Args:
        cfg: Описание конфигурации.
        out_dir: Папка для выгрузки. Будет создана, если её нет.
            Существующие файлы с теми же именами перезаписываются.

    Example:
        >>> from pathlib import Path
        >>> dump(Configuration(name="Склад"), Path("./out"))  # doctest: +SKIP

    """
    write_xml(build_configuration(cfg), out_dir / CONFIGURATION_FILE)
    write_xml(build_dump_info(), out_dir / DUMP_INFO_FILE)
    for obj in cfg.child_objects():
        write_xml(build_child_object(cfg, obj), out_dir / obj.FOLDER / f"{obj.name}.xml")
