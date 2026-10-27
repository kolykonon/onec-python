from collections.abc import Callable
from pathlib import Path

import pytest
from lxml import etree

from onec import Catalog, Configuration, LocalString
from onec.metadata.models.catalog import CodeType
from onec.xml.builders import build_catalog
from onec.xml.ns import md, v8, xr
from onec.xml.writer import write_xml

TEMPLATE_NAME = "ПустойСправочник"
TEMPLATE_SYNONYM = "Пустой справочник"
CATEGORIES = ("Object", "Ref", "Selection", "List", "Manager")


@pytest.fixture
def render(tmp_path: Path, read_xml: Callable[[Path], str]) -> Callable[[etree._Element], str]:
    """Функция, записывающая дерево в формате 1С и возвращающая текст файла."""

    def _render(root: etree._Element) -> str:
        path = tmp_path / "catalog.xml"
        write_xml(root, path)
        return read_xml(path)

    return _render


def catalog_node(root: etree._Element) -> etree._Element:
    """Возвращает элемент ``Catalog`` из корня ``MetaDataObject``."""
    node = root.find(md("Catalog"))
    assert node is not None
    return node


def prop(root: etree._Element, name: str) -> etree._Element:
    """Возвращает свойство из блока ``Properties`` справочника."""
    element = catalog_node(root).find(f"{md('Properties')}/{md(name)}")
    assert element is not None, name
    return element


def generated_types(root: etree._Element) -> list[etree._Element]:
    """Возвращает элементы ``xr:GeneratedType`` справочника."""
    return catalog_node(root).findall(f"{md('InternalInfo')}/{xr('GeneratedType')}")


def test_catalog_matches_golden(
    cfg: Configuration,
    golden: Path,
    render: Callable[[etree._Element], str],
    normalize: Callable[[str], str],
    read_xml: Callable[[Path], str],
) -> None:
    catalog = Catalog(TEMPLATE_NAME, synonym=LocalString.ru(TEMPLATE_SYNONYM))
    actual = render(build_catalog(cfg, catalog))
    expected = read_xml(golden / "catalog_empty" / "Catalogs" / f"{TEMPLATE_NAME}.xml")
    assert normalize(actual) == normalize(expected)


def test_no_template_leftovers(cfg: Configuration, render: Callable[[etree._Element], str]) -> None:
    catalog = Catalog("Товары", synonym=LocalString.ru("Товары на складе"))
    text = render(build_catalog(cfg, catalog))
    assert TEMPLATE_NAME not in text
    assert TEMPLATE_SYNONYM not in text


def test_generated_type_names(cfg: Configuration) -> None:
    root = build_catalog(cfg, Catalog("Товары"))
    names = [generated.get("name") for generated in generated_types(root)]
    assert names == [f"Catalog{category}.Товары" for category in CATEGORIES]


def test_all_uuids_are_unique(cfg: Configuration) -> None:
    root = build_catalog(cfg, Catalog("Товары"))
    ids = [catalog_node(root).get("uuid")]
    for generated in generated_types(root):
        ids.append(generated.findtext(xr("TypeId")))
        ids.append(generated.findtext(xr("ValueId")))
    # UUID справочника и пара TypeId/ValueId на каждый порождаемый тип
    assert len(ids) == 1 + 2 * len(CATEGORIES)
    assert len(set(ids)) == len(ids)


def test_uuids_are_stable(cfg: Configuration, render: Callable[[etree._Element], str]) -> None:
    first = render(build_catalog(cfg, Catalog("Товары")))
    second = render(build_catalog(cfg, Catalog("Товары")))
    assert first == second


def test_uuids_depend_on_configuration(cfg: Configuration) -> None:
    other = Configuration(name=cfg.name)
    first = catalog_node(build_catalog(cfg, Catalog("Товары"))).get("uuid")
    second = catalog_node(build_catalog(other, Catalog("Товары"))).get("uuid")
    assert first != second


def test_uuids_depend_on_catalog_name(cfg: Configuration) -> None:
    first = catalog_node(build_catalog(cfg, Catalog("Товары"))).get("uuid")
    second = catalog_node(build_catalog(cfg, Catalog("Склады"))).get("uuid")
    assert first != second


def test_properties_from_model(cfg: Configuration) -> None:
    catalog = Catalog(
        "Товары",
        code_length=11,
        description_length=150,
        code_type=CodeType.NUMBER,
        comment="Тестовый комментарий",
    )
    root = build_catalog(cfg, catalog)
    assert prop(root, "Name").text == "Товары"
    assert prop(root, "CodeLength").text == "11"
    assert prop(root, "DescriptionLength").text == "150"
    assert prop(root, "CodeType").text == "Number"
    assert prop(root, "Comment").text == "Тестовый комментарий"


def test_empty_comment_is_empty_tag(cfg: Configuration) -> None:
    root = build_catalog(cfg, Catalog("Товары"))
    assert prop(root, "Comment").text is None


def test_input_by_string_uses_catalog_name(cfg: Configuration) -> None:
    root = build_catalog(cfg, Catalog("Товары"))
    fields = [field.text for field in prop(root, "InputByString").findall(xr("Field"))]
    assert fields == [
        "Catalog.Товары.StandardAttribute.Description",
        "Catalog.Товары.StandardAttribute.Code",
    ]


def synonym_items(root: etree._Element) -> list[tuple[str | None, str | None]]:
    """Возвращает пары «язык, текст» из синонима справочника."""
    return [
        (item.findtext(v8("lang")), item.findtext(v8("content")))
        for item in prop(root, "Synonym").findall(v8("item"))
    ]


def test_synonym_replaces_template(cfg: Configuration) -> None:
    root = build_catalog(cfg, Catalog("Товары", synonym=LocalString.ru("Товары на складе")))
    assert synonym_items(root) == [("ru", "Товары на складе")]


def test_multilingual_synonym(cfg: Configuration) -> None:
    synonym = LocalString.from_dict({"ru": "Товары", "en": "Products"})
    root = build_catalog(cfg, Catalog("Товары", synonym=synonym))
    assert synonym_items(root) == [("ru", "Товары"), ("en", "Products")]


def test_empty_synonym_is_empty_tag(cfg: Configuration) -> None:
    root = build_catalog(cfg, Catalog("Товары"))
    synonym = prop(root, "Synonym")
    assert len(synonym) == 0
    assert synonym.text is None


def test_template_is_not_shared_between_calls(cfg: Configuration) -> None:
    build_catalog(cfg, Catalog("Товары", synonym=LocalString.ru("Первый")))
    root = build_catalog(cfg, Catalog("Склады"))
    assert synonym_items(root) == []
    assert prop(root, "Name").text == "Склады"
