"""Функции для построения имён тегов с пространством имён.

lxml хранит имя тега вместе с URI пространства имён в нотации Кларка:
``{uri}tag``. Функции модуля строят такие имена, чтобы код сборщиков читался
так же, как XML: ``v8("lang")`` соответствует ``<v8:lang>``.

Example:
    >>> md("Properties")
    '{http://v8.1c.ru/8.3/MDClasses}Properties'

"""

from collections.abc import Callable

from onec.xml.constants import DUMPINFO, MD, V8, XR


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

dumpinfo = _make_ns(DUMPINFO)
