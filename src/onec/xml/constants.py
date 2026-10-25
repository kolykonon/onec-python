from typing import Final

# Версия формата выгрузки 1С
FORMAT_VERSION: Final = "2.20"

# Пространства имен из выгрузок 1С в виде констант для удобства
MD: Final = "http://v8.1c.ru/8.3/MDClasses"
V8: Final = "http://v8.1c.ru/8.1/data/core"
XR: Final = "http://v8.1c.ru/8.3/xcf/readable"
DUMPINFO: Final = "http://v8.1c.ru/8.3/xcf/dumpinfo"

_XEN: Final = "http://v8.1c.ru/8.3/xcf/enums"
_XS: Final = "http://www.w3.org/2001/XMLSchema"
_XSI: Final = "http://www.w3.org/2001/XMLSchema-instance"


# Словарь пространств имен Configuration.xml
MD_NSMAP: Final[dict[str | None, str]] = {
    None: MD,
    "app": "http://v8.1c.ru/8.2/managed-application/core",
    "cfg": "http://v8.1c.ru/8.1/data/enterprise/current-config",
    "cmi": "http://v8.1c.ru/8.2/managed-application/cmi",
    "ent": "http://v8.1c.ru/8.1/data/enterprise",
    "lf": "http://v8.1c.ru/8.2/managed-application/logform",
    "style": "http://v8.1c.ru/8.1/data/ui/style",
    "sys": "http://v8.1c.ru/8.1/data/ui/fonts/system",
    "v8": V8,
    "v8ui": "http://v8.1c.ru/8.1/data/ui",
    "web": "http://v8.1c.ru/8.1/data/ui/colors/web",
    "win": "http://v8.1c.ru/8.1/data/ui/colors/windows",
    "xen": "http://v8.1c.ru/8.3/xcf/enums",
    "xpr": "http://v8.1c.ru/8.3/xcf/predef",
    "xr": XR,
    "xs": "http://www.w3.org/2001/XMLSchema",
    "xsi": "http://www.w3.org/2001/XMLSchema-instance",
}

# Словарь пространств имен ConfigurationDump.xml
DUMPINFO_NSMAP: Final[dict[str | None, str]] = {
    None: DUMPINFO,
    "xen": _XEN,
    "xs": _XS,
    "xsi": _XSI,
}


# UUID классов из выгрузок 1С, в отличие от ObjectID, они фиксированные
CONFIGURATION_CLASS_IDS: Final = (
    "9cd510cd-abfc-11d4-9434-004095e12fc7",
    "9fcd25a0-4822-11d4-9414-008048da11f9",
    "e3687481-0a87-462c-a166-9f34594f9bba",
    "9de14907-ec23-4a07-96f0-85521cb6b53b",
    "51f2d5d8-ea4d-4064-8892-82951750031e",
    "e68182ea-4237-4383-967f-90c1e3370bc7",
    "fb282519-d103-4dd3-bc12-cb271d631dfc",
)
