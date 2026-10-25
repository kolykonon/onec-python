"""Запись конфигурации в папку в формате выгрузки Конфигуратора.

Раскладывает файлы так же, как команда «Выгрузить конфигурацию в файлы»
в иерархическом формате: ``Configuration.xml`` в корне, объекты по папкам
своих типов (``Languages/``, ``Catalogs/``).
"""

from pathlib import Path

from onec.xml.builders import build_configuration, build_dump_info, build_language
from onec.xml.model import Configuration
from onec.xml.writer import write_1c_to_xml


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
    write_1c_to_xml(build_configuration(cfg), out_dir / "Configuration.xml")
    write_1c_to_xml(build_dump_info(), out_dir / "ConfigDumpInfo.xml")
    for lang in cfg.languages:
        write_1c_to_xml(build_language(cfg, lang), out_dir / "Languages" / f"{lang.name}.xml")
