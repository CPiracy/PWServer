# Конфигурация Perfect World 1.7.6 Build 4311

Настройки ниже относятся к Linux-комплекту `Linear/PWServer176.7z`. Пути в примерах рассчитаны на `/root/pwserver`. [Состав комплекта](image-files.ru.md) · [Проверка на VM](../experiments/image-file-validation/image-file-validation.ru.md)

## Основы использования

### Службы и настройки

1. Импортируйте `root/sql/pw176.sql` и `root/sql/licenseservice.sql` в MariaDB. Настройте подключения в обоих `gamesys.conf` с секцией `[GMysqlClient]`.
2. Разместите штатный файл `/home/license.conf`. Его `[GLicenseClient]` указывает на `licenseservice`, в проверенной конфигурации на `127.0.0.1:33000`.
3. Подготовьте два отдельных каталога WDB и доступный для записи каталог `/root/pwserver/logs`. Запускайте службы в порядке таблицы, каждую из каталога её бинарника.

| Команда | Секция слушателя | Порт VM |
|---|---|---|
| `./licenseservice gamesys.conf` | `[GLicenseServer]` | TCP `33000` |
| `./logservice logservice.conf` | `[LogserviceServer]`, `[LogserviceTcpServer]` | UDP `11100`, TCP `11101` |
| `./uniquenamed gamesys.conf` | `[UniqueNameServer]` | TCP `29401` |
| `./gauthd gamesys.conf` | `[GAuthServer]` | TCP `29200` |
| `./gamedbd gamesys.conf` | `[GameDBServer]` | TCP `29400` |
| `./gacd gamesys.conf` | `[GAntiCheaterServer]`, `[GACControlServer]` | TCP `29702`, `29712` |
| `./gfactiond gamesys.conf` | `[GFactionServer]`, `[GProviderServer]` | TCP `29500`, `29600` |
| `./gdeliveryd gamesys.conf` | `[GDeliveryServer]`, `[GProviderServer]` | TCP `29100`, `29300` |
| `./glinkd gamesys.conf 1` | `[GLinkServer1]`, `[GProviderServer1]` | TCP `29000`, `29301` |

### Запуск мира

Запустите `gs` после шлюза. Для отдельного PID передавайте один алиас карты на команду.

```sh
cd /root/pwserver/gamed
./gs gs01 gs.conf gmserver.conf gsalias.conf
```

Для карты `is61` замените первый аргумент на `is61`. Проверьте `ss -ltnp` для порта `29000`. Готовая карта открывает свой UNIX-сокет, соединяется с `gdeliveryd` и `gamedbd` и появляется в журнале координатора с нужными `index` и `tag`. [Проверка запуска](../experiments/image-file-validation/image-file-validation.ru.md) · [Сетевые связи](runtime-contracts.ru.md)

## Файлы настроек

### Формат

- Пишите заголовки `[Section]` и отдельные комментарии `#` или `;` с первой колонки. Кавычки и `${VAR}` остаются частью значения.
- В парсерах H176 имена секций и ключей сравниваются без учёта регистра. Повторное непустое значение заменяет предыдущее, повтор секции заменяет весь блок. Используйте уникальные секции и ключи.
- Абсолютный путь к конфигу сохраняет рабочий каталог процесса. Относительные ресурсы, журналы и WDB по-прежнему используют `cwd` либо корень, заданный загрузчиком.

`H176 share/common/conf.h` · `H176 cgame/libcm/conf.cpp` · [Ключи VM](evidence/config-keys.tsv)

### Совместное использование `gamesys.conf`

Передавайте каждому из восьми демонов абсолютный путь к своему файлу, например `./glinkd /etc/pw/glinkd.conf 1`. Такой запуск проверен без симлинков. Общие значения можно подставлять из одного шаблона. `[GMysqlClient]`, `[GProviderServer]`, `[storagewdb]` и `[ThreadPool]` держите отдельными для каждой службы, поскольку их значения различаются. [Контрольный запуск](../experiments/image-file-validation/image-file-validation.ru.md)

### Настройки служб

| Файл | Основные параметры |
|---|---|
| `logservice/logservice.conf` | `[logservice] threshhold` задаёт уровень журнала. `fd_*` указывают на файлы, в комплекте под `../logs/`. |
| `gacd/gamesys.conf` | Сетевые параметры. Античит отдельно читает `gacd.xml` из рабочего каталога. |
| `gfactiond/gamesys.conf`, `gdeliveryd/gamesys.conf` | `table_name`, `name_charset` и `table_charset` в секции соответствующего сервера задают файл фильтра и кодировки. |
| `gdeliveryd/gamesys.conf` | В Linear `pvp=1`, `battlefield=1`, `is_central_ds=false` в `[GDeliveryServer]`, `is_countrybattle_open=1` в `[COUNTRYBATTLE]`. `domain.sev` загружается для территорий, `domain2*.sev` — при объявлении группы зон. |
| `glinkd/gamesys.conf` | Аргумент `1` выбирает суффикс секций шлюза. `max_users` и `halflogin_users` задают лимиты. Адрес шлюза должен совпадать с настройками клиента, а порт провайдера — с соответствующим `GProviderClientN` в GS. |

Для GNET согласуйте `type`, `address` и `port` на обеих сторонах. Для внутренних соединений используйте проверенные числовые IPv4. В H176 этот путь разбирает адрес через `inet_addr()`. [Карточки служб](README.ru.md#отчёты-по-службам) · [Условные ресурсы](dynamic-resources.ru.md#домены-wdb-и-античит)

## Примеры настроек

### Внешняя MariaDB

`gauthd/gamesys.conf`

```ini
[GMysqlClient]
address = 192.0.2.10
port = 3306
name = pw176
```

Подставьте адрес MariaDB и заполните `user` и `passwd` в этой же секции. В `licenseservice/gamesys.conf` укажите `name=licenseservice` и реквизиты этой схемы. Отдельная MariaDB проверена с числовым адресом. [SQL-контракты](storage-and-recovery.ru.md#контракты-mariadb)

### Постоянные каталоги WDB

`gamedbd/gamesys.conf` и `uniquenamed/gamesys.conf`

```ini
[storagewdb]
homedir = ./dbhome
datadir = ./dbdata
logdir = ./dblogs
backupdir = ./backup
```

Оставьте в своих файлах параметры `tables`, кэша и интервала checkpoint. `datadir` и `logdir` разрешаются внутри `homedir`, `backupdir` — от `cwd`. Для каждой службы храните весь `dbhome` в своём томе.

При `[gamedbd] noimportclsconfig=0` и `[GameDBServer] is_recall_server=false` `gamedbd` импортирует свой `./clsconfig` в `dbdata/clsconfig`. Служба также читает `serverlist.sev` из своего каталога. [Резервное копирование WDB](storage-and-recovery.ru.md#проверка-резервной-копии)

### Ресурсы карт

`gamed/gs.conf`

```ini
[Template]
Root = ./config/
ItemDataFile = elements.data
QuestPackage = tasks.data
QuestPackage2 = dyn_tasks.data
```

- `gsalias.conf` накладывается на `gs.conf` по ключам. Проверяйте итоговые `[General] world_servers` и `instance_servers` в обоих файлах.
- Алиас выбирает `[World_<alias>]` или `[Instance_<alias>]`. В этой секции `index` задаёт ID процесса для маршрутизации, `tag` — тег карты, `base_path` — каталог под `[Template] Root`. Сохраняйте конечный `/` в `Root`.
- Для `gs01` штатные значения `index=1`, `tag=1`, `base_path=world/`. Для `is61` — `index=101`, `tag=161`, `base_path=a61/`. `instance_capacity` и пороги пула задаются в секции инстанса.
- Сетевой конфиг `gmserver.conf` читается отдельно. `[ProviderServers] count` определяет число секций `GProviderClientN`, начиная с `0`. В Linear `count=6`. `[ThreadPool]` здесь относится к сети, а `[General] logic_threads` в `gs.conf` — к логике карты.

Пути прямой связи карт задают `[MsgReceiverTCP_<alias>]` и `[MsgReceiverUNIX_<alias>]` через `listen_addr`. Код H176 применяет `[AddrAlias]` к именам в TCP-адресах, выбирает UNIX для совпадающих IPv4 и TCP для разных. Для UNIX обоим процессам нужен доступ к пути сокета. [Загрузчики ресурсов](dynamic-resources.ru.md) · [Маршруты карт](maps.ru.md)

## Перечитывание и штатное завершение

- `logservice` по `SIGHUP` перечитывает порог и переоткрывает файлы. Для смены слушателей перезапустите службу.
- Готовые сетевые демоны завершаются по `SIGUSR1` на свой PID. У `gamedbd` и `uniquenamed` обработчик выполняет `checkpoint()` и `Close()`. Сначала остановите писателей WDB.
- `SIGTERM` проверен для пустой карты. Для сохранения ролей занятой карты нужен игровой сценарий завершения. Контрольный файл `quit_lockfile` у WDB вызывает `SIGKILL` для всей группы процессов.

`H176 share/common/thread.cpp:108` · `S172 share/storage/storagewdb.h:719` · [Остановка карты](maps.ru.md#что-считать-занятостью-и-как-завершать-работу)

## См. также

- [Происхождение и ревизии исходников](source-coverage.ru.md)
- [Аргументы, сокеты и открытые файлы VM](evidence/runtime.json)
