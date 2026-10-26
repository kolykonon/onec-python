"""Модель метаданных конфигурации 1С.

Dataclass'ы, описывающие объекты метаданных: конфигурацию, языки, справочники
и многоязычные строки. Модель не знает о формате XML: превращением её в файлы
выгрузки занимаются сборщики из ``onec.xml.builders``.
"""

import enum
import re
import uuid
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Self, SupportsIndex, overload

_NAME_RE = re.compile(r"^[^\W\d]\w*$")


def _validate_name(name: str) -> None:
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
        items: Словарь локализаций. Ключом является код языка, значением - текст.

    Example:
        >>> lstring = LocalString.ru("Строка на русском")
        >>> lstring.get("ru")
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


@dataclass
class Language:
    """Язык конфигурации 1С:Предприятие.

    При выгрузке конфигурации находится в папке Languages. Используется для формирования [Язык].xml

    Attributes:
        name: Имя языка
        synonym: Представление языка для пользователя
        code: Код языка, например ``"ru"``
        comment: Комментарий, виден только в конфигураторе

    Example:
        >>> lng = Language()
        >>> lng.name
        'Русский'

    """

    name: str = "Русский"
    synonym: LocalString = field(default_factory=lambda: LocalString.ru("Русский"))
    code: str = "ru"
    comment: str = ""

    def __post_init__(self) -> None:
        """Проверяет корректность имени языка."""
        _validate_name(self.name)


@dataclass
class Configuration:
    """Конфигурация 1С:Предприятие.

    Корневой объект метаданных. Из неё генерируется файл
    ``Configuration.xml`` и все подчинённые объекты выгрузки.

    Attributes:
        name: Имя конфигурации. Должно быть допустимым идентификатором 1С.
        catalogs: Список справочников конфигурации
        uuid: Идентификатор конфигурации. Из него детерминированно выводятся
            идентификаторы всех внутренних объектов, поэтому для повторных
            сборок его нужно зафиксировать.
        synonym: Представление конфигурации для пользователя.
        comment: Комментарий, виден только в Конфигураторе.
        compatibility_mode: Режим совместимости, например ``"Version8_3_27"``.
        languages: Языки конфигурации. Первый язык считается основным.

    Example:
        >>> cfg = Configuration(name="Склад", synonym=LocalString.ru("Склад"))
        >>> cfg.languages[0].name
        'Русский'

    """

    name: str
    catalogs: list["Catalog"] = field(default_factory=list)
    uuid: "uuid.UUID" = field(default_factory=uuid.uuid4)
    synonym: LocalString = field(default_factory=LocalString)
    comment: str = ""
    compatibility_mode: str = "Version8_3_27"
    languages: list[Language] = field(default_factory=lambda: [Language()])

    def __post_init__(self) -> None:
        """Проверяет имя,наличие хотя бы одного языка и дубликаты справочников."""
        _validate_name(self.name)
        if not self.languages:
            raise ValueError("В конфигурации должен быть хотя бы один язык")
        self.catalogs = CatalogList(self.catalogs)

    @property
    def main_language(self) -> Language:
        """Основной язык конфигурации."""
        return self.languages[0]


class CodeType(enum.StrEnum):
    """Тип кода для справочника.

    Представляет типы, которые можно использовать в коде справочника 1С.
    """

    STRING = "String"
    NUMBER = "Number"


@dataclass
class Catalog:
    """Сущность справочника в конфигурации.

    Объект метаданных 1С, представляющий некоторую сущность.

    Attributes:
        name: Имя справочника
        description_length: Длина наименования справочника
        code_length: Длина кода справочника
        synonym: Отображаемое имя справочника
        comment: Комментарий, виден только в конфигураторе
        code_type: Тип кода 1С (Строка, Число ...)

    Example:
        >>> cat = Catalog("Товары")
        >>> cat.code_type.value
        'String'

    """

    name: str
    description_length: int = 25
    code_length: int = 9
    synonym: LocalString = field(default_factory=LocalString)
    comment: str = ""
    code_type: CodeType = CodeType.STRING

    @property
    def full_name(self) -> str:
        """Возвращает полное имя справочника в XML."""
        return f"Catalog.{self.name}"

    def __post_init__(self) -> None:
        """Валидация полей справочника.

        Raises:
            ValueError: если длина кода < 1 или длина наименования < 1

        """
        _validate_name(self.name)
        if self.code_length < 1:
            raise ValueError("Длина кода не может быть меньше 1")
        if self.description_length < 1:
            raise ValueError("Длина наименования не может быть меньше 1")


def _check_unique_catalogs(catalogs: Iterable[Catalog]) -> None:
    """Проверяет, что имена справочников не повторяются.

    Args:
        catalogs: Проверяемые справочники.

    Raises:
        ValueError: Если два справочника имеют одинаковое имя.

    """
    cnt = Counter(catalog.name for catalog in catalogs)
    for key, val in cnt.items():
        if val > 1:
            raise ValueError(f"Найден справочник с повторяющимся именем: {key}")


class CatalogList(list[Catalog]):
    """Список справочников, не допускающий повторяющихся имён.

    Проверка выполняется при создании списка и при каждом изменении:
    ``append``, ``insert``, ``extend``, ``+=`` и присваивании по индексу.
    При ошибке список не изменяется.

    Example:
        >>> catalogs = CatalogList([Catalog("Товары")])
        >>> catalogs.append(Catalog("Товары"))
        Traceback (most recent call last):
        ...
        ValueError: Найден справочник с повторяющимся именем: Товары

    """

    def __init__(self, catalogs: Iterable[Catalog] = ()) -> None:
        """Создаёт список и проверяет уникальность имён."""
        items = list(catalogs)
        _check_unique_catalogs(items)
        super().__init__(items)

    def append(self, catalog: Catalog) -> None:
        """Добавляет справочник в конец списка."""
        _check_unique_catalogs([*self, catalog])
        super().append(catalog)

    def insert(self, index: SupportsIndex, catalog: Catalog) -> None:
        """Вставляет справочник перед позицией ``index``."""
        _check_unique_catalogs([*self, catalog])
        super().insert(index, catalog)

    def extend(self, catalogs: Iterable[Catalog]) -> None:
        """Добавляет несколько справочников в конец списка."""
        items = list(catalogs)
        _check_unique_catalogs([*self, *items])
        super().extend(items)

    def __iadd__(self, catalogs: Iterable[Catalog]) -> Self:  # type: ignore[override, misc]
        """Добавляет справочники оператором ``+=``."""
        self.extend(catalogs)
        return self

    @overload
    def __setitem__(self, index: SupportsIndex, value: Catalog) -> None: ...

    @overload
    def __setitem__(self, index: slice, value: Iterable[Catalog]) -> None: ...

    def __setitem__(self, index: SupportsIndex | slice, value: Catalog | Iterable[Catalog]) -> None:
        """Заменяет справочник или срез справочников."""
        candidate = list(self)
        if isinstance(index, slice):
            assert not isinstance(value, Catalog)
            value = list(value)
            candidate[index] = value
            _check_unique_catalogs(candidate)
            super().__setitem__(index, value)
        else:
            assert isinstance(value, Catalog)
            candidate[index] = value
            _check_unique_catalogs(candidate)
            super().__setitem__(index, value)
