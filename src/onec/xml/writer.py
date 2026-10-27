"""Запись XML-файлов в формате выгрузки Конфигуратора 1С."""

from pathlib import Path
from typing import Final

from lxml import etree

_DECLARATION: Final = '<?xml version="1.0" encoding="UTF-8"?>\n'
_BOM: Final = "\ufeff"


def write_xml(root: etree._Element, path: Path) -> None:
    """Записывает XML в формате выгрузки Конфигуратора 1С.

    Формат: UTF-8 с BOM, переводы строк CRLF, отступы табуляцией,
    объявление XML с двойными кавычками, без перевода строки в конце.

    Args:
        root: Корневой элемент файла.
        path: Путь к файлу. Недостающие папки будут созданы.

    """
    etree.indent(root, space="\t")
    body = etree.tostring(root, encoding="unicode")
    text = (_DECLARATION + body).replace("\r\n", "\n").replace("\n", "\r\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes((_BOM + text).encode("utf-8"))
