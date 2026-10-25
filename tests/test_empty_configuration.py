from collections.abc import Callable
from pathlib import Path

import pytest
from lxml import etree

from onec.xml.dump import dump
from onec.xml.model import Configuration
from onec.xml.writer import write_1c_to_xml

FILES = ["Configuration.xml", "ConfigDumpInfo.xml", "Languages/Русский.xml"]


@pytest.mark.parametrize("case", ["empty", "empty2"])
@pytest.mark.parametrize("rel_path", FILES)
def test_matches_golden(
    tmp_path: Path, golden: Path, normalize: Callable[[str], str], rel_path: str, case: str
) -> None:
    dump(Configuration(name="Конфигурация"), tmp_path)
    actual = (tmp_path / rel_path).read_bytes().decode("utf-8")
    expected = (golden / "8.3.27" / case / rel_path).read_bytes().decode("utf-8")
    assert normalize(actual) == normalize(expected)


@pytest.mark.parametrize("rel_path", FILES)
def test_writer_roundtrip_is_byte_exact(tmp_path: Path, golden: Path, rel_path: str) -> None:
    source = golden / "8.3.27" / "empty" / rel_path
    out = tmp_path / "out.xml"
    write_1c_to_xml(etree.fromstring(source.read_bytes()), out)
    assert out.read_bytes() == source.read_bytes()


def test_uuids_are_stable(tmp_path: Path) -> None:
    cfg = Configuration(name="Склад")
    dump(cfg, tmp_path / "a")
    dump(cfg, tmp_path / "b")
    for rel_path in FILES:
        assert (tmp_path / "a" / rel_path).read_bytes() == (tmp_path / "b" / rel_path).read_bytes()


def test_invalid_name_rejected() -> None:
    with pytest.raises(ValueError, match="Недопустимое имя"):
        Configuration(name="1Склад")
