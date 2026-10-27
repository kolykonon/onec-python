"""Построение XML-деревьев файлов выгрузки из модели.

Для каждого вида объектов метаданных есть свой сборщик (``build_configuration``,
``build_language``, ``build_catalog``), возвращающий корневой элемент файла.
``build_child_object`` выбирает сборщик по виду подчинённого объекта,
``build_dump_info`` строит служебный файл ``ConfigDumpInfo.xml``.
Сложные файлы строятся по шаблонам из реальной выгрузки, в которых
переопределяются значения из модели.

Все UUID вычисляются детерминированно из UUID конфигурации, поэтому повторная
сборка одной и той же конфигурации даёт идентичные файлы.
"""

import uuid
from importlib.resources import files
from typing import Final

from lxml import etree

from onec.metadata import (
    Catalog,
    ChildObject,
    Configuration,
    Language,
    LocalString,
    MetadataObject,
)
from onec.xml.constants import (
    CONFIGURATION_CLASS_IDS,
    DUMP_FORMAT,
    DUMP_INFO_NSMAP,
    FORMAT_VERSION,
    MD_NSMAP,
)
from onec.xml.ns import dump_info, md, prefixed, v8, xr

# Категории порождаемых типов справочника в порядке из выгрузки 1С
_CATALOG_GENERATED_CATEGORIES: Final = ("Object", "Ref", "Selection", "List", "Manager")

# Идентификаторы, которые 1С выдаёт каждому порождаемому типу
_GENERATED_TYPE_IDS: Final = ("TypeId", "ValueId")

_INPUT_BY_STRING_FIELDS: Final = ("Description", "Code")


def _set_local_string(element: etree._Element, value: LocalString) -> None:
    """Заменяет в элементе многоязычную строку.

    Для каждого языка меняется блок ``v8:item`` с ``v8:lang`` и ``v8:content``.

    Args:
        element: Элемент, например ``<Synonym/>``.
        value: Многоязычная строка.

    """
    element.clear()
    for code, text in value.items:
        item = etree.SubElement(element, v8("item"))
        etree.SubElement(item, v8("lang")).text = code
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
    element = parent.find(path)
    if element is None:
        raise ValueError(f"В шаблоне не найден элемент {prefixed(path)!r}")
    return element


def _set_property(props: etree._Element, name: str, value: str) -> None:
    """Устанавливает значение свойства в блоке ``Properties``.

    Пустая строка записывается как пустой тег ``<Name/>``, как в выгрузке 1С.

    Args:
        props: Элемент ``Properties``.
        name: Имя свойства (тега), например ``"Comment"``.
        value: Значение свойства.

    """
    _find(props, md(name)).text = value or None


def _set_common_properties(props: etree._Element, obj: MetadataObject) -> None:
    """Устанавливает свойства, общие для всех объектов: имя, синоним и комментарий.

    Args:
        props: Элемент ``Properties`` с тегами ``Name``, ``Synonym`` и ``Comment``.
        obj: Объект метаданных.

    """
    _set_property(props, "Name", obj.name)
    _set_property(props, "Comment", obj.comment)
    _set_local_string(_find(props, md("Synonym")), obj.synonym)


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


def _load_object_template(
    obj: MetadataObject, object_id: uuid.UUID
) -> tuple[etree._Element, etree._Element]:
    """Загружает шаблон ``<Вид>.xml`` объекта и задаёт UUID его узла.

    Args:
        obj: Объект метаданных, вид которого определяет шаблон.
        object_id: UUID объекта.

    Returns:
        Корневой элемент ``MetaDataObject`` и узел объекта, например ``Catalog``.

    """
    root = _load_template(f"{obj.KIND}.xml")
    node = _find(root, md(obj.KIND))
    node.set("uuid", str(object_id))
    return root, node


def _object_uuid(cfg: Configuration, key: str) -> uuid.UUID:
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
        field_element = etree.SubElement(input_by_string, xr("Field"))
        field_element.text = f"{catalog.full_name}.StandardAttribute.{attribute}"


def build_configuration(cfg: Configuration) -> etree._Element:
    """Строит дерево файла ``Configuration.xml``.

    Используется шаблон из выгрузки пустой конфигурации, в котором
    переопределяются идентификаторы, имя, синоним и другие свойства из модели,
    а также список подчинённых объектов.

    Args:
        cfg: Описание конфигурации.

    Returns:
        Корневой элемент ``MetaDataObject``.

    Raises:
        ValueError: Если ClassId в шаблоне не совпадают с ожидаемыми.

    """
    root, node = _load_object_template(cfg, cfg.uuid)

    contained_objects = node.findall(f"{md('InternalInfo')}/{xr('ContainedObject')}")
    class_ids = tuple(_find(contained, xr("ClassId")).text for contained in contained_objects)
    if class_ids != CONFIGURATION_CLASS_IDS:
        raise ValueError(f"Неожиданные ClassId в шаблоне конфигурации: {class_ids}")
    for contained, class_id in zip(contained_objects, CONFIGURATION_CLASS_IDS, strict=True):
        _find(contained, xr("ObjectId")).text = str(_object_uuid(cfg, class_id))

    props = _find(node, md("Properties"))
    _set_common_properties(props, cfg)
    _set_property(props, "CompatibilityMode", cfg.compatibility_mode)
    # Отдельного режима для расширений в модели нет: 1С по умолчанию
    # выставляет его равным режиму совместимости конфигурации
    _set_property(props, "ConfigurationExtensionCompatibilityMode", cfg.compatibility_mode)
    _set_property(props, "DefaultLanguage", cfg.main_language.full_name)

    children = _find(node, md("ChildObjects"))
    children.clear()
    for child in cfg.child_objects():
        etree.SubElement(children, md(child.KIND)).text = child.name
    return root


def build_language(cfg: Configuration, language: Language) -> etree._Element:
    """Строит дерево файла ``Languages/<Имя>.xml``.

    Args:
        cfg: Конфигурация, которой принадлежит язык (нужна для вычисления UUID).
        language: Описание языка.

    Returns:
        Корневой элемент ``MetaDataObject``.

    """
    root = etree.Element(md("MetaDataObject"), nsmap=MD_NSMAP, version=FORMAT_VERSION)
    language_id = _object_uuid(cfg, language.full_name)
    node = etree.SubElement(root, md(language.KIND), uuid=str(language_id))
    props = etree.SubElement(node, md("Properties"))
    for name in ("Name", "Synonym", "Comment", "LanguageCode"):
        etree.SubElement(props, md(name))
    _set_common_properties(props, language)
    _set_property(props, "LanguageCode", language.code)
    return root


def build_dump_info() -> etree._Element:
    """Строит дерево служебного файла ``ConfigDumpInfo.xml``.

    Пока список версий объектов всегда пустой: он используется Конфигуратором
    для частичной выгрузки и при генерации не заполняется.

    Returns:
        Корневой элемент ``ConfigDumpInfo``.

    """
    root = etree.Element(
        dump_info("ConfigDumpInfo"),
        nsmap=DUMP_INFO_NSMAP,
        format=DUMP_FORMAT,
        version=FORMAT_VERSION,
    )
    etree.SubElement(root, dump_info("ConfigVersions"))
    return root


def build_catalog(cfg: Configuration, catalog: Catalog) -> etree._Element:
    """Строит дерево файла ``Catalogs/<Имя>.xml``.

    Используется шаблон из выгрузки пустого справочника, в котором
    переопределяются свойства из модели.

    Args:
        cfg: Конфигурация, которой принадлежит справочник (нужна для вычисления UUID).
        catalog: Описание справочника.

    Returns:
        Корневой элемент ``MetaDataObject``.

    Raises:
        ValueError: Если порождаемые типы в шаблоне не совпадают с ожидаемыми.

    """
    root, node = _load_object_template(catalog, _object_uuid(cfg, catalog.full_name))

    generated_types = node.findall(f"{md('InternalInfo')}/{xr('GeneratedType')}")
    categories = tuple(generated.get("category") for generated in generated_types)
    if categories != _CATALOG_GENERATED_CATEGORIES:
        raise ValueError(
            f"Ожидались категории порождаемых типов {_CATALOG_GENERATED_CATEGORIES}, "
            f"в шаблоне: {categories}"
        )

    for generated, category in zip(generated_types, _CATALOG_GENERATED_CATEGORIES, strict=True):
        generated.set("name", f"{catalog.KIND}{category}.{catalog.name}")
        for id_tag in _GENERATED_TYPE_IDS:
            key = f"{catalog.full_name}.{category}.{id_tag}"
            _find(generated, xr(id_tag)).text = str(_object_uuid(cfg, key))

    props = _find(node, md("Properties"))
    _set_common_properties(props, catalog)
    _set_property(props, "CodeType", catalog.code_type.value)
    _set_property(props, "CodeLength", str(catalog.code_length))
    _set_property(props, "DescriptionLength", str(catalog.description_length))
    _set_input_by_string(props, catalog)

    _find(node, md("ChildObjects")).clear()
    return root


def build_child_object(cfg: Configuration, obj: ChildObject) -> etree._Element:
    """Строит дерево файла подчинённого объекта ``<Папка>/<Имя>.xml``.

    Args:
        cfg: Конфигурация, которой принадлежит объект.
        obj: Подчинённый объект конфигурации.

    Returns:
        Корневой элемент ``MetaDataObject``.

    Raises:
        TypeError: Если для вида объекта нет сборщика.

    """
    match obj:
        case Language():
            return build_language(cfg, obj)
        case Catalog():
            return build_catalog(cfg, obj)
    raise TypeError(f"Нет сборщика для объекта вида {obj.KIND!r}")
