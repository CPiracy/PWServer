# Классы и объекты сборщика DEB

Согласованная схема классов сборщика. Общий сценарий упаковки описан в [архитектуре билдера](package-builder-proposal.ru.md), правила отбора собраны в [оценке файлов сервера](pwserver-files-review.ru.md).

## Диаграмма классов

```mermaid
classDiagram
    direction TB

    class AbstractSource {
        <<abstract>>
        +Path path
        +list_files() list~SourceFile~
        +get_file(path) SourceFile
        +get_file_sha256(path) str
        +extract_file(file, path) None
    }

    class DirectorySource
    class SevenZipSource
    class ZipSource
    class TarSource
    class VmdkSource

    class SourceFile {
        +__init__(source, path, link) None
        +AbstractSource source
        +PurePath path
        +Optional~SourceFile~ link
        +str sha256
        +extract(path) None
    }


    class PackageFile {
        +SourceFile source_file
        +PurePosixPath destination
        +extract(path) None
    }

    class ConfigBuilder {
        +SourceFactory source_factory
        -tuple~Path~ source_paths
        -list~SourceFile~ excluded_files
        +__init__(source_paths, source_factory) None
        +build_config() Config
        +get_excluded_files() list~SourceFile~
        -select_files(files_by_source) tuple
    }

    class Config {
        +list~PackageFile~ files
        +save(path) None
        +load(path, source_factory) Config$
        +filter_config(package_filter) Config
    }

    class SourceFactory {
        +create(path) AbstractSource
    }

    AbstractSource <|-- DirectorySource
    AbstractSource <|-- SevenZipSource
    AbstractSource <|-- ZipSource
    AbstractSource <|-- TarSource
    AbstractSource <|-- VmdkSource
    SourceFile <|-- PackageFile
    AbstractSource ..> SourceFile : возвращает
    SourceFile --> AbstractSource : source
    PackageFile --> SourceFile : source_file
    Config o-- PackageFile : files
    ConfigBuilder o-- SourceFile : excluded_files
    ConfigBuilder ..> PackageFile : создаёт при отборе
    ConfigBuilder --> SourceFactory : source_factory
    ConfigBuilder ..> Config : создаёт
    Config ..> SourceFactory : load
    Config ..> AbstractSource : get_file
    SourceFactory ..> AbstractSource : создаёт
```

`SourceFile` — общий класс для всех форматов. Адрес записи и цель ссылки имеют тип `PurePath`. Для файлов каталога ридер передаёт `Path`, для записей архива — `PurePosixPath`. Конструктор вычисляет адрес цели выражением `path.parent / link`. Свойство `link` получает следующий файл через `AbstractSource.get_file()`. Этот метод интерпретирует путь, включая `..`, по правилам источника. Хеширование и извлечение рекурсивно переходят к конечному файлу.

`PackageFile` наследуется от `SourceFile` и хранит ссылку `source_file` на исходный экземпляр. Свойства и вызов `extract(path)` делегируются исходному файлу. `destination` хранит назначение внутри пакета. Подготовка пакета преобразует это назначение в рабочий путь.

`Config` хранит выбранные `PackageFile`. Метод `save` записывает в JSON строковые представления абсолютного пути источника, пути записи и назначения. Метод `load` получает `SourceFactory`, создаёт один ридер на источник и восстанавливает записи через `AbstractSource.get_file(path)`.

`SourceFactory` живёт в `libs.sources` рядом с ридерами. `create(path: Path) -> AbstractSource` выбирает реализацию для каталога, 7z, ZIP, TAR или VMDK. Та же фабрика используется при создании и при загрузке конфига.

## Отбор и фильтрация конфига

`ConfigBuilder(source_paths, source_factory)` принимает список путей к источникам и фиксирует их порядок на время жизни экземпляра. Другой набор путей получает свой экземпляр билдера.

`ConfigBuilder.build_config() -> Config` открывает источники из сохранённого списка и передаёт файлы внутреннему методу отбора. Отбор определяет назначения, выбирает варианты и создаёт `PackageFile` для общего конфига. Исключённые `SourceFile` сохраняются в этом же экземпляре после успешного построения.

`get_excluded_files() -> list[SourceFile]` возвращает копию списка исключённых последнего успешного построения. До первого построения список пуст. Следующее успешное построение заменяет список. CLI может использовать этот метод для вывода `--exclude`.

`Config.filter_config(package_filter) -> Config` применяет предикат `PackageFile -> bool` и возвращает новый конфиг. В нём остаются ссылки на выбранные `PackageFile` в прежнем порядке. Это позволяет получить серверный конфиг и конфиг данных из одного общего.

## Пример связанных объектов

```mermaid
classDiagram
    direction LR
    class Config["config : Config"]
    class Selected["selected : PackageFile"]
    class Entry["entry : SourceFile"]
    class Archive["archive : SevenZipSource"]

    Selected : destination = /opt/pwserver/binary/gamed/gs
    Entry : path = pwserver/gamed/gs
    Archive : path = /archives/server.7z

    Config --> Selected : files
    Selected --> Entry : source_file
    Entry --> Archive : source
```

## Выбор паттернов

- Адаптеры источника реализуют операции чтения для своих форматов. Общий `SourceFile` обращается к адаптеру по адресу записи.
- `PackageFile` использует декоратор для `SourceFile`. Он добавляет назначение пакета и делегирует операции исходному экземпляру.
- `SourceFactory` сосредоточивает выбор ридера в одном методе. Если понадобятся настройки чтения, например выбор раздела VMDK, их можно передать фабрике при создании.
- Интерактивный режим и пресеты используют общий отбор `ConfigBuilder`. Способ выбора варианта можно передать как метод объекта. В `build config` флаг `--batch` предназначен для выбора вариантов без запросов пользователю.
