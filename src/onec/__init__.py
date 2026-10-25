from importlib.metadata import version

from onec.xml.dump import dump
from onec.xml.model import Configuration, Language, LocalString

__version__ = version("onec-py")

__all__ = [
    "Configuration",
    "Language",
    "LocalString",
    "__version__",
    "dump",
]
