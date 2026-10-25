"""Построение XML-деревьев файлов выгрузки из модели.

Для каждого вида объектов метаданных есть свой сборщик (``build_configuration``,
``build_language``, ``build_catalog``), возвращающий корневой элемент файла.
Сложные файлы строятся по шаблонам из реальной выгрузки, в которых
переопределяются значения из модели.

Все UUID вычисляются детерминированно из UUID конфигурации, поэтому повторная
сборка одной и той же конфигурации даёт идентичные файлы.
"""

import uuid
from importlib.resources import files
from typing import Final

from lxml import etree

from onec.xml.constants import (
    CONFIGURATION_CLASS_IDS,
    DUMPINFO_NSMAP,
    FORMAT_VERSION,
    MD_NSMAP,
)
from onec.xml.model import Catalog, Configuration, Language, LocalString
from onec.xml.ns import dumpinfo, md, v8, xr

_CATALOG_CATEGORY_SET: Final = {"Object", "Ref", "Selection", "List", "Manager"}

_INPUT_BY_STRING_FIELDS: Final = ("Description", "Code")


def set_local_string(element: etree._Element, value: LocalString) -> None:
    """Заменяет в элементе многоязычную строку.

    Для каждого языка меняется блок ``v8:item`` с ``v8:lang`` и ``v8:content``.

    Args:
        element: Элемент, например ``<Synonym/>``.
        value: Многоязычная строка

    """
    element.clear()
    for lang, text in value.items:
        item = etree.SubElement(element, v8("item"))
        etree.SubElement(item, v8("lang")).text = lang
        etree.SubElement(item, v8("content")).text = text


def _find(parent: etree._Element, path: str) -> etree._Element:
    """Находит обязательный дочерний элемент.

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
    """Устанавливает значение свойства в блоке ``Properties``.

    Пустая строка записывается как пустой тег ``<Name/>``, как в выгрузке 1С.

    Args:
        props: Элемент ``Properties``.
        name: Имя свойства (тега), например ``"Comment"``.
        value: Значение свойства.

    """
    _find(props, md(name)).text = value or None


def _load_template(name: str) -> etree._Element:
    """Загружает XML-шаблон из пакета ``onec.xml.templates``.

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
    """Вычисляет UUID объекта внутри конфигурации.

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
    """Строит дерево файла ``Configuration.xml``.

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
    set_local_string(_find(props, md("Synonym")), cfg.synonym)

    children = _find(node, md("ChildObjects"))
    children.clear()
    for lang in cfg.languages:
        etree.SubElement(children, md("Language")).text = lang.name
    return root


def build_language(cfg: Configuration, lang: Language) -> etree._Element:
    """Строит дерево файла ``Languages/<Имя>.xml``.

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
    set_local_string(etree.SubElement(props, md("Synonym")), lang.synonym)
    etree.SubElement(props, md("Comment")).text = lang.comment or None
    etree.SubElement(props, md("LanguageCode")).text = lang.code
    return root


def build_dump_info() -> etree._Element:
    """Строит дерево служебного файла ``ConfigDumpInfo.xml``.

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


def _set_input_by_string(props: etree._Element, catalog: Catalog) -> None:
    """Заполняет поля ввода по строке справочника.

    Содержимое ``InputByString`` из шаблона полностью заменяется: поля строятся
    заново из полного имени справочника, поэтому имя справочника из шаблона
    не может остаться в результате.

    Args:
        props: Элемент ``Properties`` справочника.
        catalog: Справочник, для которого строятся поля.

    """
    input_by_string = _find(props, md("InputByString"))
    input_by_string.clear()
    for attribute in _INPUT_BY_STRING_FIELDS:
        etree.SubElement(
            input_by_string, xr("Field")
        ).text = f"{catalog.full_name}.StandardAttribute.{attribute}"


def build_catalog(cfg: Configuration, catalog: Catalog) -> etree._Element:
    """Строит дерево файла ``<Имя справочника>.xml``.

    Использует шаблон из выгрузки пустого справочника в котором переопределяются параметры из модели

    Args:
        cfg: Объект конфигурации, uuid используется как пространство имён
        catalog: Объект справочника, из которого берутся атрибуты

    Raises:
        ValueError: если найден неожиданный порождаемый тип или несоответствие ожидаемому количеству

    Returns:
        Корневой элемент ``MetaDataObject``

    """
    root = _load_template("Catalog.xml")
    node = _find(root, md("Catalog"))
    node.set("uuid", str(object_uuid(cfg, catalog.full_name)))

    objects = node.findall(f"{md('InternalInfo')}/{xr('GeneratedType')}")

    if len(objects) != len(_CATALOG_CATEGORY_SET):
        raise ValueError(
            f"Ожидалось {len(_CATALOG_CATEGORY_SET)} порождаемых типов, найдено: {len(objects)}"
        )

    for generated in objects:
        category = generated.get("category")
        if not category:
            raise ValueError("Категория не найдена")
        if category not in _CATALOG_CATEGORY_SET:
            raise ValueError(f"Неожиданная категория порождаемых типов {category}")
        generated.set("name", f"Catalog{category}.{catalog.name}")
        uuid_key = f"{catalog.full_name}.{category}"
        _find(generated, xr("TypeId")).text = str(object_uuid(cfg, f"{uuid_key}.TypeId"))
        _find(generated, xr("ValueId")).text = str(object_uuid(cfg, f"{uuid_key}.ValueId"))
    props = _find(node, md("Properties"))

    _set_property(props, "Name", catalog.name)
    _set_property(props, "Comment", catalog.comment)
    _set_property(props, "CodeType", catalog.code_type.value)
    _set_property(props, "CodeLength", str(catalog.code_length))
    _set_property(props, "DescriptionLength", str(catalog.description_length))

    set_local_string(_find(props, md("Synonym")), catalog.synonym)
    _set_input_by_string(props, catalog)
    children = _find(node, md("ChildObjects"))
    children.clear()
    return root
