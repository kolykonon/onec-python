from __future__ import annotations

import uuid
from collections.abc import Callable
from pathlib import Path

import pytest
from lxml import etree

from onec.xml.builders import build_catalog
from onec.xml.model import Catalog, CodeType, Configuration, LocalString
from onec.xml.ns import md, v8, xr
from onec.xml.writer import write_1c_to_xml

GOLDEN = Path(__file__).parent / "golden" / "8.3.27" / "catalog_empty"
TEMPLATE_NAME = "ПустойСправочник"
TEMPLATE_SYNONYM = "Пустой справочник"
CATEGORIES = ("Object", "Ref", "Selection", "List", "Manager")


@pytest.fixture
def cfg() -> Configuration:
    """Конфигурация с фиксированным UUID, чтобы результаты были воспроизводимы."""
    return Configuration(name="Склад", uuid=uuid.UUID("12345678-1234-5678-1234-567812345678"))


def render(root: etree._Element, tmp_path: Path) -> str:
    """Записывает дерево в формате 1С и возвращает текст файла."""
    path = tmp_path / "catalog.xml"
    write_1c_to_xml(root, path)
    return path.read_bytes().decode("utf-8")


def catalog_node(root: etree._Element) -> etree._Element:
    """Возвращает элемент ``Catalog`` из корня ``MetaDataObject``."""
    node = root.find(md("Catalog"))
    assert node is not None
    return node


def prop(root: etree._Element, name: str) -> etree._Element:
    """Возвращает свойство из блока ``Properties`` справочника."""
    el = catalog_node(root).find(f"{md('Properties')}/{md(name)}")
    assert el is not None, name
    return el


def generated_types(root: etree._Element) -> list[etree._Element]:
    """Возвращает элементы ``xr:GeneratedType`` справочника."""
    return catalog_node(root).findall(f"{md('InternalInfo')}/{xr('GeneratedType')}")


def test_matches_golden(
    cfg: Configuration, tmp_path: Path, normalize: Callable[[str], str]
) -> None:
    catalog = Catalog(TEMPLATE_NAME, synonym=LocalString.ru(TEMPLATE_SYNONYM))
    actual = render(build_catalog(cfg, catalog), tmp_path)
    expected = (GOLDEN / "Catalogs" / f"{TEMPLATE_NAME}.xml").read_bytes().decode("utf-8")
    assert normalize(actual) == normalize(expected)


def test_no_template_leftovers(cfg: Configuration, tmp_path: Path) -> None:
    catalog = Catalog("Товары", synonym=LocalString.ru("Товары на складе"))
    text = render(build_catalog(cfg, catalog), tmp_path)
    assert TEMPLATE_NAME not in text
    assert TEMPLATE_SYNONYM not in text


def test_generated_type_names(cfg: Configuration) -> None:
    root = build_catalog(cfg, Catalog("Товары"))
    names = [el.get("name") for el in generated_types(root)]
    assert names == [f"Catalog{category}.Товары" for category in CATEGORIES]


def test_all_uuids_are_unique(cfg: Configuration) -> None:
    root = build_catalog(cfg, Catalog("Товары"))
    ids = [catalog_node(root).get("uuid")]
    for el in generated_types(root):
        ids.append(el.findtext(xr("TypeId")))
        ids.append(el.findtext(xr("ValueId")))
    assert len(ids) == 11
    assert len(set(ids)) == 11


def test_uuids_are_stable(cfg: Configuration, tmp_path: Path) -> None:
    first = render(build_catalog(cfg, Catalog("Товары")), tmp_path)
    second = render(build_catalog(cfg, Catalog("Товары")), tmp_path)
    assert first == second


def test_uuids_depend_on_configuration(cfg: Configuration) -> None:
    other = Configuration(name="Склад", uuid=uuid.UUID("87654321-4321-8765-4321-876543218765"))
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
    fields = [el.text for el in prop(root, "InputByString").findall(xr("Field"))]
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
