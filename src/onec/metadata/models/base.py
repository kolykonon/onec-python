"""Базовые типы конфигурации 1С."""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import ClassVar, Final, Self, SupportsIndex, TypeVar, cast, overload

_NAME_RE: Final = re.compile(r"^[^\W\d]\w*$")


def validate_name(name: str) -> None:
    """Проверяет, что строка является допустимым именем объекта 1С.

    Имя должно начинаться с буквы или подчёркивания и состоять
    только из букв, цифр и подчёркиваний.

    Args:
        name: Проверяемое имя.

    Raises:
        ValueError: Если имя недопустимо.

    """
    if not _NAME_RE.match(name):
        raise ValueError(f"Недопустимое имя объекта 1С: {name!r}")


@dataclass(frozen=True)
class LocalString:
    """Многоязычная строка 1С.

    Attributes:
        items: Пары «код языка, текст» в порядке добавления.

    Example:
        >>> synonym = LocalString.ru("Строка на русском")
        >>> synonym.get("ru")
        'Строка на русском'

    """

    items: tuple[tuple[str, str], ...] = ()

    @classmethod
    def ru(cls, text: str) -> Self:
        """Создаёт строку только на русском языке.

        Args:
            text: Текст на русском языке.

        Returns:
            Многоязычная строка с одним языком ``ru``.

        """
        return cls((("ru", text),))

    @classmethod
    def from_dict(cls, values: dict[str, str]) -> Self:
        """Создаёт строку из словаря «код:текст».

        Args:
            values: Тексты по кодам языков.

        Returns:
            Многоязычная строка с языками в порядке словаря.

        """
        return cls(tuple(values.items()))

    def get(self, lang: str) -> str | None:
        """Возвращает текст на указанном языке.

        Args:
            lang: Код языка, например ``"ru"``.

        Returns:
            Текст или ``None``, если для языка текста нет.

        """
        return dict(self.items).get(lang)

    def __bool__(self) -> bool:
        """Пустая строка считается ложной."""
        return bool(self.items)


class MetadataObject:
    """Базовый класс объектов метаданных 1С.

    Задаёт общие для всех объектов свойства и проверку имени. Поля объявляются
    в dataclass'ах наследников.

    Attributes:
        KIND: Вид объекта в выгрузке, например ``"Catalog"``. Используется
            как имя тега, префикс полного имени и имя файла шаблона.

    """

    KIND: ClassVar[str]

    name: str
    synonym: LocalString
    comment: str

    @property
    def full_name(self) -> str:
        """Полное имя объекта метаданных, например ``"Catalog.Товары"``."""
        return f"{self.KIND}.{self.name}"

    def __post_init__(self) -> None:
        """Проверяет корректность имени объекта.

        Raises:
            ValueError: Если имя недопустимо.

        """
        validate_name(self.name)


class ChildObject(MetadataObject):
    """Объект, подчинённый конфигурации и выгружаемый в отдельный файл.

    Attributes:
        FOLDER: Папка выгрузки, в которой лежит файл ``<Имя>.xml`` объекта.

    """

    FOLDER: ClassVar[str]


_T = TypeVar("_T", bound=MetadataObject)


def _check_unique_names(items: Iterable[MetadataObject]) -> None:
    """Проверяет, что имена объектов не повторяются.

    Args:
        items: Проверяемые объекты.

    Raises:
        ValueError: Если два объекта имеют одинаковое имя.

    """
    seen: set[str] = set()
    for item in items:
        if item.name in seen:
            raise ValueError(f"Найден объект с повторяющимся именем: {item.name!r}")
        seen.add(item.name)


class UniqueNameList(list[_T]):
    """Список объектов метаданных, не допускающий повторяющихся имён.

    Проверка выполняется при создании списка и при каждом изменении:
    ``append``, ``insert``, ``extend``, ``+=`` и присваивании по индексу.
    При ошибке список не изменяется.

    Example:
        >>> catalogs = UniqueNameList([Catalog("Товары")])
        >>> catalogs.append(Catalog("Товары"))
        Traceback (most recent call last):
        ...
        ValueError: Найден объект с повторяющимся именем: 'Товары'

    """

    def __init__(self, items: Iterable[_T] = ()) -> None:
        """Создаёт список и проверяет уникальность имён."""
        items = list(items)
        _check_unique_names(items)
        super().__init__(items)

    def append(self, item: _T) -> None:
        """Добавляет объект в конец списка."""
        _check_unique_names([*self, item])
        super().append(item)

    def insert(self, index: SupportsIndex, item: _T) -> None:
        """Вставляет объект перед позицией ``index``."""
        _check_unique_names([*self, item])
        super().insert(index, item)

    def extend(self, items: Iterable[_T]) -> None:
        """Добавляет несколько объектов в конец списка."""
        items = list(items)
        _check_unique_names([*self, *items])
        super().extend(items)

    # В typeshed list.__iadd__ согласован с перегрузками list.__add__, которые
    # принимают списки других типов. Здесь допускаются только объекты типа _T
    def __iadd__(self, items: Iterable[_T]) -> Self:  # type: ignore[override, misc]
        """Добавляет объекты оператором ``+=``."""
        self.extend(items)
        return self

    @overload
    def __setitem__(self, index: SupportsIndex, value: _T) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[_T]) -> None: ...

    def __setitem__(self, index: SupportsIndex | slice, value: _T | Iterable[_T]) -> None:
        """Заменяет объект или срез объектов."""
        candidate = list(self)
        if isinstance(index, slice):
            items = list(cast("Iterable[_T]", value))
            candidate[index] = items
            _check_unique_names(candidate)
            super().__setitem__(index, items)
        else:
            item = cast("_T", value)
            candidate[index] = item
            _check_unique_names(candidate)
            super().__setitem__(index, item)
