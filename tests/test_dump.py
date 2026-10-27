from collections.abc import Callable
from pathlib import Path

import pytest
from lxml import etree

from onec.metadata import Catalog, Configuration
from onec.xml.builders import build_catalog
from onec.xml.dump import dump
from onec.xml.writer import write_xml

EMPTY_CONFIGURATION_FILES = ["Configuration.xml", "ConfigDumpInfo.xml", "Languages/Русский.xml"]


def dumped_files(out_dir: Path) -> dict[Path, bytes]:
    """Возвращает содержимое всех файлов выгрузки по относительным путям."""
    return {path.relative_to(out_dir): path.read_bytes() for path in out_dir.rglob("*.xml")}


@pytest.mark.parametrize("case", ["empty", "empty2"])
@pytest.mark.parametrize("rel_path", EMPTY_CONFIGURATION_FILES)
def test_empty_configuration_matches_golden(
    tmp_path: Path,
    golden: Path,
    normalize: Callable[[str], str],
    read_xml: Callable[[Path], str],
    rel_path: str,
    case: str,
) -> None:
    dump(Configuration(name="Конфигурация"), tmp_path)
    actual = read_xml(tmp_path / rel_path)
    expected = read_xml(golden / case / rel_path)
    assert normalize(actual) == normalize(expected)


@pytest.mark.parametrize("rel_path", EMPTY_CONFIGURATION_FILES)
def test_writer_roundtrip_is_byte_exact(tmp_path: Path, golden: Path, rel_path: str) -> None:
    source = golden / "empty" / rel_path
    out = tmp_path / "out.xml"
    write_xml(etree.fromstring(source.read_bytes()), out)
    assert out.read_bytes() == source.read_bytes()


def test_dump_writes_catalog_files(cfg: Configuration, tmp_path: Path) -> None:
    dump(cfg, tmp_path)
    files = sorted(path.name for path in (tmp_path / Catalog.FOLDER).iterdir())
    assert files == ["Склады.xml", "Товары.xml"]


def test_dump_without_catalogs_has_no_catalogs_dir(tmp_path: Path) -> None:
    dump(Configuration(name="Склад"), tmp_path)
    assert not (tmp_path / Catalog.FOLDER).exists()


def test_dumped_catalog_matches_builder(cfg: Configuration, tmp_path: Path) -> None:
    dump(cfg, tmp_path / "dump")
    for catalog in cfg.catalogs:
        expected = tmp_path / f"{catalog.name}.xml"
        write_xml(build_catalog(cfg, catalog), expected)
        actual = tmp_path / "dump" / Catalog.FOLDER / f"{catalog.name}.xml"
        assert actual.read_bytes() == expected.read_bytes()


def test_dump_is_stable(cfg: Configuration, tmp_path: Path) -> None:
    dump(cfg, tmp_path / "a")
    dump(cfg, tmp_path / "b")
    first = dumped_files(tmp_path / "a")
    # Configuration.xml, ConfigDumpInfo.xml, один язык и два справочника
    assert len(first) == 5
    assert first == dumped_files(tmp_path / "b")
