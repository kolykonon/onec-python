import uuid
from collections.abc import Callable
from pathlib import Path

import pytest
from lxml import etree

from onec.xml.builders import build_catalog, build_configuration
from onec.xml.dump import dump
from onec.xml.model import Catalog, Configuration, Language, LocalString
from onec.xml.ns import md
from onec.xml.writer import write_1c_to_xml

GOLDEN = Path(__file__).parent / "golden" / "8.3.27" / "catalog_empty"


@pytest.fixture
def cfg() -> Configuration:
    return Configuration(
        name="Склад",
        uuid=uuid.UUID("12345678-1234-5678-1234-567812345678"),
        catalogs=[
            Catalog("Товары", synonym=LocalString.ru("Товары")),
            Catalog("Склады", synonym=LocalString.ru("Склады")),
        ],
    )


def child_objects(root: etree._Element) -> list[tuple[str, str | None]]:
    """Возвращает пары «тип, имя» из ``ChildObjects`` конфигурации."""
    node = root.find(f"{md('Configuration')}/{md('ChildObjects')}")
    assert node is not None
    return [(etree.QName(el).localname, el.text) for el in node]


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


def test_dump_writes_catalog_files(cfg: Configuration, tmp_path: Path) -> None:
    dump(cfg, tmp_path)
    files = sorted(p.name for p in (tmp_path / "Catalogs").iterdir())
    assert files == ["Склады.xml", "Товары.xml"]


def test_dump_without_catalogs_has_no_catalogs_dir(tmp_path: Path) -> None:
    dump(Configuration(name="Склад"), tmp_path)
    assert not (tmp_path / "Catalogs").exists()


def test_dumped_catalog_matches_builder(cfg: Configuration, tmp_path: Path) -> None:
    dump(cfg, tmp_path / "dump")
    for catalog in cfg.catalogs:
        expected = tmp_path / f"{catalog.name}.xml"
        write_1c_to_xml(build_catalog(cfg, catalog), expected)
        actual = tmp_path / "dump" / "Catalogs" / f"{catalog.name}.xml"
        assert actual.read_bytes() == expected.read_bytes()


def test_dumped_catalog_matches_golden(tmp_path: Path, normalize: Callable[[str], str]) -> None:
    name = "ПустойСправочник"
    cfg = Configuration(
        name="Конфигурация",
        catalogs=[Catalog(name, synonym=LocalString.ru("Пустой справочник"))],
    )
    dump(cfg, tmp_path)
    actual = (tmp_path / "Catalogs" / f"{name}.xml").read_bytes().decode("utf-8")
    expected = (GOLDEN / "Catalogs" / f"{name}.xml").read_bytes().decode("utf-8")
    assert normalize(actual) == normalize(expected)


def test_dump_is_stable(cfg: Configuration, tmp_path: Path) -> None:
    dump(cfg, tmp_path / "a")
    dump(cfg, tmp_path / "b")
    for rel_path in ["Configuration.xml", "Catalogs/Товары.xml", "Catalogs/Склады.xml"]:
        assert (tmp_path / "a" / rel_path).read_bytes() == (tmp_path / "b" / rel_path).read_bytes()
