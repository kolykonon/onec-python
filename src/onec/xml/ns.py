from collections.abc import Callable

from onec.xml.constants import DUMPINFO, MD, V8, XR


def _make_ns(namespace: str) -> Callable[[str], str]:
    """
    Создаёт функцию, строящую имена тегов в заданном пространстве имён.

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
