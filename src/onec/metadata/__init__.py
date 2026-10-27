"""Классы объектов метаданных конфигурации 1С."""

from onec.metadata.models.base import (
    ChildObject,
    LocalString,
    MetadataObject,
    UniqueNameList,
)
from onec.metadata.models.catalog import Catalog, CodeType
from onec.metadata.models.configuration import Configuration, Language

__all__ = [
    "Catalog",
    "ChildObject",
    "CodeType",
    "Configuration",
    "Language",
    "LocalString",
    "MetadataObject",
    "UniqueNameList",
]
