"""Модель метаданных конфигурации 1С.

Dataclass'ы, описывающие объекты метаданных: конфигурацию, языки, справочники
и многоязычные строки. Модель не знает о формате XML: превращением её в файлы
выгрузки занимаются сборщики из ``onec.xml.builders``. От формата выгрузки
в модели только вид объекта (``KIND``) и папка его файлов (``FOLDER``).
"""

import enum
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from typing import ClassVar, Final, Self, SupportsIndex, TypeVar, cast, overload
from uuid import UUID, uuid4

from onec.platform.version import DEFAULT_COMPATIBILITY_MODE

# Значения по умолчанию для нового справочника в Конфигураторе
DEFAULT_CATALOG_CODE_LENGTH: Final = 9
DEFAULT_CATALOG_DESCRIPTION_LENGTH: Final = 25

_NAME_RE: Final = re.compile(r"^[^\W\d]\w*$")


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
        _validate_name(self.name)


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


@dataclass
class Language(ChildObject):
    """Язык конфигурации 1С:Предприятие.

    При выгрузке конфигурации записывается в файл ``Languages/<Имя>.xml``.

    Attributes:
        name: Имя языка.
        synonym: Представление языка для пользователя.
        code: Код языка, например ``"ru"``.
        comment: Комментарий, виден только в Конфигураторе.

    Example:
        >>> language = Language()
        >>> language.name
        'Русский'

    """

    KIND = "Language"
    FOLDER = "Languages"

    name: str = "Русский"
    synonym: LocalString = field(default_factory=lambda: LocalString.ru("Русский"))
    code: str = "ru"
    comment: str = ""


class CodeType(enum.StrEnum):
    """Тип кода справочника: строка или число."""

    STRING = "String"
    NUMBER = "Number"


@dataclass
class Catalog(ChildObject):
    """Справочник конфигурации 1С:Предприятие.

    При выгрузке конфигурации записывается в файл ``Catalogs/<Имя>.xml``.

    Attributes:
        name: Имя справочника.
        description_length: Длина наименования.
        code_length: Длина кода.
        synonym: Представление справочника для пользователя.
        comment: Комментарий, виден только в Конфигураторе.
        code_type: Тип кода.

    Example:
        >>> catalog = Catalog("Товары")
        >>> catalog.code_type.value
        'String'

    """

    KIND = "Catalog"
    FOLDER = "Catalogs"

    name: str
    description_length: int = DEFAULT_CATALOG_DESCRIPTION_LENGTH
    code_length: int = DEFAULT_CATALOG_CODE_LENGTH
    synonym: LocalString = field(default_factory=LocalString)
    comment: str = ""
    code_type: CodeType = CodeType.STRING

    def __post_init__(self) -> None:
        """Проверяет имя и длины кода и наименования.

        Raises:
            ValueError: Если имя недопустимо или длина кода или наименования меньше 1.

        """
        super().__post_init__()
        if self.code_length < 1:
            raise ValueError("Длина кода не может быть меньше 1")
        if self.description_length < 1:
            raise ValueError("Длина наименования не может быть меньше 1")


@dataclass
class Configuration(MetadataObject):
    """Конфигурация 1С:Предприятие.

    Корневой объект метаданных. Из неё генерируется файл
    ``Configuration.xml`` и все подчинённые объекты выгрузки.

    Attributes:
        name: Имя конфигурации. Должно быть допустимым идентификатором 1С.
        uuid: Идентификатор конфигурации. Из него детерминированно выводятся
            идентификаторы всех внутренних объектов, поэтому для повторных
            сборок его нужно зафиксировать.
        synonym: Представление конфигурации для пользователя.
        comment: Комментарий, виден только в Конфигураторе.
        compatibility_mode: Режим совместимости, например ``"Version8_3_27"``.
        languages: Языки конфигурации. Первый язык считается основным.
            Имена языков должны быть уникальны.
        catalogs: Справочники конфигурации. Имена справочников должны быть
            уникальны.

    Example:
        >>> cfg = Configuration(name="Склад", synonym=LocalString.ru("Склад"))
        >>> cfg.languages[0].name
        'Русский'

    """

    KIND = "Configuration"

    name: str
    uuid: UUID = field(default_factory=uuid4)
    synonym: LocalString = field(default_factory=LocalString)
    comment: str = ""
    compatibility_mode: str = DEFAULT_COMPATIBILITY_MODE
    languages: list[Language] = field(default_factory=lambda: [Language()])
    catalogs: list[Catalog] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Проверяет имя, наличие хотя бы одного языка и уникальность имён объектов.

        Raises:
            ValueError: Если имя недопустимо, языков нет или имена объектов
                одного вида повторяются.

        """
        super().__post_init__()
        if not self.languages:
            raise ValueError("В конфигурации должен быть хотя бы один язык")
        self.languages = UniqueNameList(self.languages)
        self.catalogs = UniqueNameList(self.catalogs)

    @property
    def main_language(self) -> Language:
        """Основной язык конфигурации."""
        return self.languages[0]

    def child_objects(self) -> Iterator[ChildObject]:
        """Возвращает подчинённые объекты в порядке ``ChildObjects`` выгрузки."""
        yield from self.languages
        yield from self.catalogs
