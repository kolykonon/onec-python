import re
from collections.abc import Callable
from pathlib import Path

import pytest

from onec.xml.constants import CONFIGURATION_CLASS_IDS

GOLDEN_DIR = Path(__file__).parent / "golden"

_UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_CONSTANT_IDS = frozenset(CONFIGURATION_CLASS_IDS)


def normalize_uuids(text: str) -> str:
    """
    Заменяет UUID на метки ``UUID-1``, ``UUID-2``… по порядку появления.

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


@pytest.fixture
def golden() -> Path:
    """Папка с эталонными выгрузками."""
    return GOLDEN_DIR


@pytest.fixture
def normalize() -> Callable[[str], str]:
    """Функция нормализации UUID для сравнения с эталонами."""
    return normalize_uuids
