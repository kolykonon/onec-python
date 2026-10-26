import pytest

from onec.xml.model import Catalog, CatalogList, Configuration

DUPLICATE = "Найден справочник с повторяющимся именем"


def names(catalogs: list[Catalog]) -> list[str]:
    return [catalog.name for catalog in catalogs]


@pytest.fixture
def cfg() -> Configuration:
    return Configuration(name="Склад", catalogs=[Catalog("Товары"), Catalog("Склады")])


def test_invalid_name_rejected() -> None:
    with pytest.raises(ValueError, match="Недопустимое имя"):
        Catalog("1Товары")


def test_code_length_must_be_positive() -> None:
    with pytest.raises(ValueError, match="Длина кода"):
        Catalog("Товары", code_length=0)


def test_description_length_must_be_positive() -> None:
    with pytest.raises(ValueError, match="Длина наименования"):
        Catalog("Товары", description_length=0)


def test_full_name() -> None:
    assert Catalog("Товары").full_name == "Catalog.Товары"


def test_catalogs_are_empty_by_default() -> None:
    assert Configuration(name="Склад").catalogs == []


def test_catalogs_converted_to_catalog_list(cfg: Configuration) -> None:
    assert isinstance(cfg.catalogs, CatalogList)
    assert names(cfg.catalogs) == ["Товары", "Склады"]


def test_duplicates_rejected_in_constructor() -> None:
    with pytest.raises(ValueError, match=f"{DUPLICATE}: Товары"):
        Configuration(name="Склад", catalogs=[Catalog("Товары"), Catalog("Товары")])


def test_append(cfg: Configuration) -> None:
    cfg.catalogs.append(Catalog("Контрагенты"))
    assert names(cfg.catalogs) == ["Товары", "Склады", "Контрагенты"]


def test_append_duplicate_rejected(cfg: Configuration) -> None:
    with pytest.raises(ValueError, match=f"{DUPLICATE}: Товары"):
        cfg.catalogs.append(Catalog("Товары", code_length=5))
    assert names(cfg.catalogs) == ["Товары", "Склады"]


def test_append_same_object_twice_rejected() -> None:
    cfg = Configuration(name="Склад")
    catalog = Catalog("Товары")
    cfg.catalogs.append(catalog)
    with pytest.raises(ValueError, match=DUPLICATE):
        cfg.catalogs.append(catalog)
    assert cfg.catalogs == [catalog]


def test_insert_duplicate_rejected(cfg: Configuration) -> None:
    with pytest.raises(ValueError, match=DUPLICATE):
        cfg.catalogs.insert(0, Catalog("Склады"))
    assert names(cfg.catalogs) == ["Товары", "Склады"]


def test_extend_duplicate_rejected(cfg: Configuration) -> None:
    with pytest.raises(ValueError, match=DUPLICATE):
        cfg.catalogs.extend([Catalog("Контрагенты"), Catalog("Товары")])
    assert names(cfg.catalogs) == ["Товары", "Склады"]


def test_extend_with_duplicates_inside_rejected(cfg: Configuration) -> None:
    with pytest.raises(ValueError, match=f"{DUPLICATE}: Контрагенты"):
        cfg.catalogs.extend(Catalog("Контрагенты") for _ in range(2))
    assert names(cfg.catalogs) == ["Товары", "Склады"]


def test_extend_accepts_generator(cfg: Configuration) -> None:
    cfg.catalogs.extend(Catalog(name) for name in ("Контрагенты", "Валюты"))
    assert names(cfg.catalogs) == ["Товары", "Склады", "Контрагенты", "Валюты"]


def test_iadd_duplicate_rejected(cfg: Configuration) -> None:
    catalogs = cfg.catalogs
    with pytest.raises(ValueError, match=DUPLICATE):
        catalogs += [Catalog("Склады")]
    assert names(cfg.catalogs) == ["Товары", "Склады"]


def test_iadd_keeps_catalog_list(cfg: Configuration) -> None:
    cfg.catalogs += [Catalog("Контрагенты")]
    assert isinstance(cfg.catalogs, CatalogList)
    assert names(cfg.catalogs) == ["Товары", "Склады", "Контрагенты"]


def test_setitem_duplicate_rejected(cfg: Configuration) -> None:
    with pytest.raises(ValueError, match=DUPLICATE):
        cfg.catalogs[1] = Catalog("Товары")
    assert names(cfg.catalogs) == ["Товары", "Склады"]


def test_setitem_replaces_catalog_with_same_name(cfg: Configuration) -> None:
    cfg.catalogs[0] = Catalog("Товары", code_length=20)
    assert cfg.catalogs[0].code_length == 20


def test_slice_assignment_duplicate_rejected(cfg: Configuration) -> None:
    with pytest.raises(ValueError, match=DUPLICATE):
        cfg.catalogs[1:] = [Catalog("Контрагенты"), Catalog("Товары")]
    assert names(cfg.catalogs) == ["Товары", "Склады"]


def test_slice_assignment(cfg: Configuration) -> None:
    cfg.catalogs[:1] = (Catalog(name) for name in ("Контрагенты", "Валюты"))
    assert names(cfg.catalogs) == ["Контрагенты", "Валюты", "Склады"]


def test_name_freed_after_remove(cfg: Configuration) -> None:
    del cfg.catalogs[0]
    cfg.catalogs.append(Catalog("Товары"))
    assert names(cfg.catalogs) == ["Склады", "Товары"]
