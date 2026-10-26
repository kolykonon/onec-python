# Changelog

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии следуют [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Добавлено

- Каркас проекта: пакет `onec`, команда `onec version`.
- Модель конфигурации: `Configuration`, `Language`, `LocalString`.
- Генерация выгрузки пустой конфигурации в формате Конфигуратора
  (формат 2.20, платформа 8.3.27) функцией `dump()`.
- Детерминированные UUID: UUID внутренних объектов вычисляются из
  `Configuration.uuid`, поэтому при фиксированном `uuid` повторная сборка
  даёт идентичные файлы.
- Справочники: класс `Catalog` и список `Configuration.catalogs`. Справочники
  выгружаются в `Catalogs/<Имя>.xml` и перечисляются в `ChildObjects`
  файла `Configuration.xml`.
- Проверка уникальности имён справочников: `Configuration.catalogs` не
  допускает дублей ни при создании конфигурации, ни при последующем
  `append`/`insert`/`extend`/`+=`/присваивании по индексу.
