"""Модуль, где реализован класс языка конфигурации и корневой класс самой конфигурации 1С."""

from collections.abc import Iterator
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from onec.metadata.models.base import (
    ChildObject,
    LocalString,
    MetadataObject,
    UniqueNameList,
)
from onec.metadata.models.catalog import Catalog
from onec.platform.version import DEFAULT_COMPATIBILITY_MODE


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
