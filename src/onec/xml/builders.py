import uuid
from importlib.resources import files

from lxml import etree

from onec.xml.constants import (
    CONFIGURATION_CLASS_IDS,
    DUMPINFO_NSMAP,
    FORMAT_VERSION,
    MD_NSMAP,
)
from onec.xml.model import Configuration, Language, LocalString
from onec.xml.ns import dumpinfo, md, v8, xr


def append_local_string(element: etree._Element, value: LocalString) -> None:
    """
    Добавляет в элемент многоязычную строку.

    Для каждого языка создается блок ``v8:item`` с ``v8:lang`` и ``v8:content``.

    Args:
        element: Элемент, например ``<Synonym/>``.
        value: Многоязычная строка
    """

    for lang, text in value.items:
        item = etree.SubElement(element, v8("item"))
        etree.SubElement(item, v8("lang")).text = lang
        etree.SubElement(item, v8("content")).text = text


def _find(parent: etree._Element, path: str) -> etree._Element:
    """
    Находит обязательный дочерний элемент.

    Args:
        parent: Элемент, в котором выполняется поиск.
        path: Путь в синтаксисе ElementPath.

    Returns:
        Найденный элемент.

    Raises:
        ValueError: Если элемент не найден, то есть шаблон не соответствует ожиданиям.
    """

    el = parent.find(path)
    if el is None:
        raise ValueError(f"В шаблоне не найден элемент {path}")
    return el


def _set_property(props: etree._Element, name: str, value: str) -> None:
    """
    Устанавливает значение свойства в блоке ``Properties``.

    Пустая строка записывается как пустой тег ``<Name/>``, как в выгрузке 1С.

    Args:
        props: Элемент ``Properties``.
        name: Имя свойства (тега), например ``"Comment"``.
        value: Значение свойства.
    """

    _find(props, md(name)).text = value or None


def _load_template(name: str) -> etree._Element:
    """
    Загружает XML-шаблон из пакета ``onec.xml.templates``.

    Пробельные символы между тегами удаляются, чтобы при записи отступы
    расставлялись заново и не смешивались со старыми.

    Args:
        name: Имя файла шаблона.

    Returns:
        Корневой элемент шаблона.
    """

    data = files("onec.xml.templates").joinpath(name).read_bytes()
    return etree.fromstring(data, etree.XMLParser(remove_blank_text=True))


def object_uuid(cfg: Configuration, key: str) -> uuid.UUID:
    """
    Вычисляет UUID объекта внутри конфигурации.

    Один и тот же ключ в одной и той же конфигурации всегда даёт один и тот же
    UUID.

    Args:
        cfg: Конфигурация, UUID которой используется как пространство имён.
        key: Уникальный ключ объекта, например ``"Language.Русский"``.

    Returns:
        UUID объекта.
    """

    return uuid.uuid5(cfg.uuid, key)


def build_configuration(cfg: Configuration) -> etree._Element:
    """
    Строит дерево файла ``Configuration.xml``.

    Используется шаблон из выгрузки пустой конфигурации, в котором
    переопределяются идентификаторы, имя, синоним и другие свойства из модели,
    а также список подчинённых объектов.

    Args:
        cfg: Описание конфигурации.

    Returns:
        Корневой элемент ``MetaDataObject``.
    """

    root = _load_template("Configuration.xml")
    node = _find(root, md("Configuration"))
    node.set("uuid", str(cfg.uuid))

    object_ids = node.findall(f"{md('InternalInfo')}/{xr('ContainedObject')}/{xr('ObjectId')}")
    for el, class_id in zip(object_ids, CONFIGURATION_CLASS_IDS, strict=True):
        el.text = str(object_uuid(cfg, class_id))

    props = _find(node, md("Properties"))
    _set_property(props, "Name", cfg.name)
    _set_property(props, "Comment", cfg.comment)
    _set_property(props, "CompatibilityMode", cfg.compatibility_mode)
    _set_property(props, "ConfigurationExtensionCompatibilityMode", cfg.compatibility_mode)
    _set_property(props, "DefaultLanguage", f"Language.{cfg.main_language.name}")
    append_local_string(_find(props, md("Synonym")), cfg.synonym)

    children = _find(node, md("ChildObjects"))
    children.clear()
    for lang in cfg.languages:
        etree.SubElement(children, md("Language")).text = lang.name
    return root


def build_language(cfg: Configuration, lang: Language) -> etree._Element:
    """
    Строит дерево файла ``Languages/<Имя>.xml``.

    Args:
        cfg: Конфигурация, которой принадлежит язык (нужна для вычисления UUID).
        lang: Описание языка.

    Returns:
        Корневой элемент ``MetaDataObject``.
    """

    root = etree.Element(
        md("MetaDataObject"),
        nsmap=MD_NSMAP,
        version=FORMAT_VERSION,
    )
    node = etree.SubElement(
        root, md("Language"), uuid=str(object_uuid(cfg, f"Language.{lang.name}"))
    )
    props = etree.SubElement(node, md("Properties"))
    etree.SubElement(props, md("Name")).text = lang.name
    append_local_string(etree.SubElement(props, md("Synonym")), lang.synonym)
    etree.SubElement(props, md("Comment")).text = lang.comment or None
    etree.SubElement(props, md("LanguageCode")).text = lang.code
    return root


def build_dump_info() -> etree._Element:
    """
    Строит дерево служебного файла ``ConfigDumpInfo.xml``.

    Пока список версий объектов всегда пустой: он используется Конфигуратором
    для частичной выгрузки и при генерации не заполняется.

    Returns:
        Корневой элемент ``ConfigDumpInfo``.
    """

    root = etree.Element(
        dumpinfo("ConfigDumpInfo"),
        nsmap=DUMPINFO_NSMAP,
        format="Hierarchical",
        version=FORMAT_VERSION,
    )
    etree.SubElement(root, dumpinfo("ConfigVersions"))
    return root
