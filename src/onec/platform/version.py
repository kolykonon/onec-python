"""Версия платформы, под которую генерируется выгрузка.

Шаблоны в ``onec.xml.templates``, версия формата выгрузки и эталоны
в ``tests/golden/<версия>`` получены из этой версии платформы. При переходе
на другую платформу их нужно обновлять вместе.
"""

from typing import Final

PLATFORM_VERSION: Final = "8.3.27"

# Режим совместимости новой конфигурации, например "Version8_3_27"
DEFAULT_COMPATIBILITY_MODE: Final = "Version" + PLATFORM_VERSION.replace(".", "_")
