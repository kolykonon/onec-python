"""Модуль с реализацией объекта метаданных Справочник."""

import enum
from dataclasses import dataclass, field
from typing import Final

from onec.metadata.models.base import (
    ChildObject,
    LocalString,
    UniqueNameList,
    validate_name,
)

DEFAULT_CATALOG_CODE_LENGTH: Final = 9
DEFAULT_CATALOG_DESCRIPTION_LENGTH: Final = 25
DEFAULT_NUMBER_DIGITS: Final = 10


class CodeType(enum.StrEnum):
    """Тип кода справочника: строка или число."""

    STRING = "String"
    NUMBER = "Number"


class AttributeType(enum.StrEnum):
    """Тип атрибута справочника: (Строка, Число, Булево и т.д)."""

    STRING = "string"
    BOOL = "bool"
    DECIMAL = "decimal"
    INT = "integer"


@dataclass
class NumberQualifiers:
    """."""

    digits: int = DEFAULT_NUMBER_DIGITS


@dataclass(kw_only=True)
class Attribute(ChildObject):
    """Аттрибут объекта метаданных конфигурации 1С:Предприятие.

    Является ChildObject объекта метаданных, например справочника.

    Attributes:
        name: Имя атрибута
        type: Тип атрибута (Строка, число)
        synonym: Синоним атрибута

    Example:
        >>> catalog = Catalog("Пользователи")
        >>> attribute = Attribute(name="Почта', type=AttributeType.STRING)
        >>> catalog.attributes.append(attribute)
        >>> catalog.attributes[0].name
        'Почта'

    """

    name: str
    type: AttributeType
    synonym: LocalString = field(default_factory=LocalString)

    def __post_init__(self) -> None:
        """Валидирует правильность имени атрибута.

        Raises:
            ValueError: Если имя атрибута недопустимо.

        """
        validate_name(self.name)


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
    attributes: list[Attribute] = field(default_factory=list)

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
        self.attributes = UniqueNameList(self.attributes)
