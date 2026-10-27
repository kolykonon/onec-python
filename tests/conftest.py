import re
import uuid
from collections.abc import Callable
from pathlib import Path

import pytest

from onec.metadata import Catalog, Configuration, LocalString
from onec.platform.version import PLATFORM_VERSION
from onec.xml.constants import CONFIGURATION_CLASS_IDS

GOLDEN_DIR = Path(__file__).parent / "golden" / PLATFORM_VERSION
FIXED_UUID = uuid.UUID("12345678-1234-5678-1234-567812345678")

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_CONSTANT_IDS = frozenset(CONFIGURATION_CLASS_IDS)


def _normalize_uuids(text: str) -> str:
    """Заменяет UUID на метки ``UUID-1``, ``UUID-2``… по порядку появления.

    Одинаковые UUID получают одинаковую метку, поэтому структура ссылок
    сохраняется. Константные ClassId не заменяются и сравниваются буквально.

    Args:
        text: Содержимое XML-файла.

    Returns:
        Текст с нормализованными UUID.

    """
    mapping: dict[str, str] = {}

    def repl(match: re.Match[str]) -> str:
        value = match.group(0)
        if value in _CONSTANT_IDS:
            return value
        return mapping.setdefault(value, f"UUID-{len(mapping) + 1}")

    return _UUID_RE.sub(repl, text)


def _read_xml(path: Path) -> str:
    """Читает файл выгрузки как текст, сохраняя BOM и переводы строк CRLF."""
    return path.read_bytes().decode("utf-8")


@pytest.fixture
def golden() -> Path:
    """Папка с эталонными выгрузками текущей версии платформы."""
    return GOLDEN_DIR


@pytest.fixture
def cfg() -> Configuration:
    """Конфигурация с фиксированным UUID и двумя справочниками.

    UUID зафиксирован, чтобы результаты сборки были воспроизводимы.
    """
    return Configuration(
        name="Склад",
        uuid=FIXED_UUID,
        catalogs=[
            Catalog("Товары", synonym=LocalString.ru("Товары")),
            Catalog("Склады", synonym=LocalString.ru("Склады")),
        ],
    )


@pytest.fixture
def read_xml() -> Callable[[Path], str]:
    """Функция чтения файла выгрузки как текста."""
    return _read_xml


@pytest.fixture
def normalize() -> Callable[[str], str]:
    """Функция нормализации UUID для сравнения с эталонами."""
    return _normalize_uuids
