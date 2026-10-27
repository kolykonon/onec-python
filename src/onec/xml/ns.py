"""Функции для построения имён тегов с пространством имён.

lxml хранит имя тега вместе с URI пространства имён в нотации Кларка:
``{uri}tag``. Функции модуля строят такие имена, чтобы код сборщиков читался
так же, как XML: ``v8("lang")`` соответствует ``<v8:lang>``.

Example:
    >>> md("Properties")
    '{http://v8.1c.ru/8.3/MDClasses}Properties'

"""

import re
from collections.abc import Callable
from typing import Final

from onec.xml.constants import DUMP_INFO, MD, V8, XR


def _make_ns(namespace: str) -> Callable[[str], str]:
    """Создаёт функцию, строящую имена тегов в заданном пространстве имён.

    Args:
        namespace: URI пространства имён.

    Returns:
        Функция, принимающая локальное имя тега и возвращающая ``{uri}tag``.

    """

    def tag(name: str) -> str:
        return f"{{{namespace}}}{name}"

    return tag


md = _make_ns(MD)

v8 = _make_ns(V8)

xr = _make_ns(XR)

dump_info = _make_ns(DUMP_INFO)

_PREFIXES: Final = {MD: "md", V8: "v8", XR: "xr", DUMP_INFO: "dumpinfo"}
_CLARK_RE: Final = re.compile(r"\{([^}]*)\}")


def prefixed(path: str) -> str:
    """Переводит имена из нотации Кларка в запись с префиксами для сообщений.

    Args:
        path: Имя тега или путь ElementPath, например ``"{uri}Properties"``.

    Returns:
        Тот же путь с префиксами вместо URI, например ``"md:Properties"``.

    Example:
        >>> prefixed(md("Properties"))
        'md:Properties'

    """
    return _CLARK_RE.sub(lambda match: f"{_PREFIXES.get(match.group(1), match.group(1))}:", path)
