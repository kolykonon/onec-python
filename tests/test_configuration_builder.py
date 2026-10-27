from lxml import etree

from onec.metadata import Catalog, Configuration, Language
from onec.xml.builders import build_configuration
from onec.xml.ns import md


def child_objects(root: etree._Element) -> list[tuple[str, str | None]]:
    """Возвращает пары «вид, имя» из ``ChildObjects`` конфигурации."""
    node = root.find(f"{md('Configuration')}/{md('ChildObjects')}")
    assert node is not None
    return [(etree.QName(child).localname, child.text) for child in node]


def test_child_objects_list_catalogs_after_languages(cfg: Configuration) -> None:
    assert child_objects(build_configuration(cfg)) == [
        ("Language", "Русский"),
        ("Catalog", "Товары"),
        ("Catalog", "Склады"),
    ]


def test_child_objects_with_several_languages(cfg: Configuration) -> None:
    cfg.languages.append(Language("Английский", code="en"))
    assert child_objects(build_configuration(cfg)) == [
        ("Language", "Русский"),
        ("Language", "Английский"),
        ("Catalog", "Товары"),
        ("Catalog", "Склады"),
    ]


def test_child_objects_without_catalogs() -> None:
    cfg = Configuration(name="Склад")
    assert child_objects(build_configuration(cfg)) == [("Language", "Русский")]


def test_catalog_appended_after_creation_is_in_child_objects(cfg: Configuration) -> None:
    cfg.catalogs.append(Catalog("Контрагенты"))
    assert child_objects(build_configuration(cfg))[-1] == ("Catalog", "Контрагенты")
