import re
import uuid
from dataclasses import dataclass, field

_NAME_RE = re.compile(r"^[^\W\d]\w*$")


def _validate_name(name: str) -> None:
    """
    Проверяет, что строка является допустимым именем объекта 1С.

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
    """
    Многоязычная строка 1С.

    Attributes:
        items: Словарь локализаций. Ключом является код языка, значением - текст.

    Example:
        >>> lstring = LocalString.ru("Строка на русском")
        >>> lstring.get("ru")
        'Строка на русском'
    """

    items: tuple[tuple[str, str], ...] = ()

    @classmethod
    def ru(cls, text: str) -> "LocalString":
        """
        Создаёт строку только на русском языке.

        Args:
            text: Текст на русском языке.

        Returns:
            Многоязычная строка с одним языком ``ru``.
        """
        return cls((("ru", text),))

    @classmethod
    def from_dict(cls, values: dict[str, str]) -> "LocalString":
        """
        Создаёт строку из словаря «код:текст».

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
    """
    Язык конфигурации 1С:Предприятие.

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
        """
        Проверяет корректность имени языка

        """
        _validate_name(self.name)


@dataclass
class Configuration:
    """
    Конфигурация 1С:Предприятие.

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

    Example:
        >>> cfg = Configuration(name="Склад", synonym=LocalString.ru("Склад"))
        >>> cfg.languages[0].name
        'Русский'
    """

    name: str
    uuid: "uuid.UUID" = field(default_factory=uuid.uuid4)
    synonym: LocalString = field(default_factory=LocalString)
    comment: str = ""
    compatibility_mode: str = "Version8_3_27"
    languages: list[Language] = field(default_factory=lambda: [Language()])

    def __post_init__(self) -> None:
        """
        Проверяет имя и наличие хотя бы одного языка.

        """
        _validate_name(self.name)
        if not self.languages:
            raise ValueError("В конфигурации должен быть хотя бы один язык")

    @property
    def main_language(self) -> Language:
        """
        Основной язык конфигурации.

        """
        return self.languages[0]
