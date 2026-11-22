# Файлы игрового образа PW 1.7.6 Build 4311

Источник для первого образа — `Linear/PWServer176.7z`, дерево `root/pwserver/`. У всех десяти штатных ELF совпал SHA-256 со снимком работающей VM. В VM также подтвердилось совпадение `gs.conf`, `gmserver.conf`, `gsalias.conf`, `maps` и `elements.data`. Цели двух символических ссылок совпали по SHA-256 с обычными файлами под соответствующими штатными именами в архиве. Происхождение комплекта как официальной поставки остаётся открытым. [Отпечатки VM](evidence/fingerprints.tsv) · [Происхождение сборок](distribution-provenance.ru.md)

| Ссылка в `gamed/config/` VM | Цель | SHA-256 содержимого |
|---|---|---|
| `tasks.data` | `tasks-176-(21606)-v191-ru.data` | `4fc9e68410cc305029f0cbc6e1df06da2b660522317b855461b38cf1a2a45c5b` |
| `aipolicy.data` | `aipolicy-176-(5124)-ru-pure.data` | `8730e59e01a66fb4a466f3138d19526dbef3b01f6ab645e8b9748dbf829af8c2` |

## Программы и их рабочие каталоги

Пути в таблице относительны к корню игрового дерева. `cwd` каждой службы — каталог её ELF. Путь основного конфига задаётся аргументом запуска. Относительные файлы по умолчанию продолжают читаться из `cwd`.

| ELF | Аргументы | Что положить рядом |
|---|---|---|
| `gamed/gs` | `<алиас> gs.conf gmserver.conf gsalias.conf` | Три конфига, `ptemplate.conf`, `settings.conf`, `ranking.conf`, `script.lua` и ресурсы ниже. |
| `licenseservice/licenseservice` | `gamesys.conf` | `gamesys.conf` с `[GLicenseServer]` и `[GMysqlClient]`. |
| `logservice/logservice` | `logservice.conf` | `logservice.conf`. Выходы `fd_*` в `[logservice]` направлены в `../logs/`. |
| `uniquenamed/uniquenamed` | `gamesys.conf` | `gamesys.conf` и том `dbhome`. |
| `gauthd/gauthd` | `gamesys.conf` | `gamesys.conf`, `script.lua`. |
| `gamedbd/gamedbd` | `gamesys.conf` | `gamesys.conf`, `script.lua`, `serverlist.sev`, `clsconfig` и том `dbhome`. |
| `gacd/gacd` | `gamesys.conf` | `gamesys.conf`, `gacd.xml`. Имя XML задано в `main`. |
| `gfactiond/gfactiond` | `gamesys.conf` | `gamesys.conf`, `script.lua`, `filters`. Имя фильтра задаёт `[GFactionServer] table_name`. |
| `gdeliveryd/gdeliveryd` | `gamesys.conf` | `gamesys.conf`, `script.lua`, `filters`, `domain.sev`, `auctionid.txt`, `sysauctionlist.txt`. Имя фильтра задаёт `[GDeliveryServer] table_name`. `domain2.sev` и `domain2_cross.sev` сохраняем для режимов с объявлением группы зон, `webtradeid.txt` — для веб-торгов. |
| `glinkd/glinkd` | `gamesys.conf 1` | `gamesys.conf`. `1` — номер шлюза в наблюдавшемся запуске. |

`script.lua` в таблице — входы игрового Lua, их сохраняем. У `gauthd`, `gamedbd`, `gfactiond`, `gdeliveryd` и `glinkd` в ELF подтверждён абсолютный путь `/home/license.conf`. Файл подаётся по этому пути при развёртывании. Реквизиты MariaDB в конфигурациях `gauthd` и `licenseservice` задаются в `[GMysqlClient]`. [Аргументы и рабочие каталоги VM](evidence/runtime.json) · [Описание служб](README.ru.md#отчёты-по-службам)

У `gs` относительное имя `ptemplate.conf` читают менеджеры мира и инстансов. `EmulateSettings::Init` и `InstanceSettings::Init` используют `settings.conf`, `RankingManager::Init` — `ranking.conf`, `LuaBase::Init` — `script.lua`. Ссылки проверены в ELF 4311.

У `glinkd/glinkd` два канала, клиентский TCP `29000` и внутренний TCP `29301` для карт. В комплект входит этот бинарник. Вариант `glinkd/glinkd!!!` относится к запасным файлам раздачи. [Шлюз](services/glinkd.ru.md)

Восемь служб с `gamesys.conf` принимают путь к своему конфигу в командной строке. Прямой абсолютный путь сохраняет рабочий каталог службы и позволяет хранить конфиги в одном каталоге, по одному файлу на процесс. Секции `[GMysqlClient]`, `[GProviderServer]`, `[storagewdb]`, `[ThreadPool]` у разных служб содержат разные настройки. Общие значения удобнее подставлять при формировании отдельных конфигов. [Справочник по конфигурации](server-configuration.ru.md#совместное-использование-gamesysconf)

## Общие ресурсы и карты `gs`

- В `gamed/config/` взять `elements.data`, `tasks.data`, `dyn_tasks.data`, `world_targets.sev`, `aipolicy.data`, `extra_drops.sev`, `rare_item.conf`, `global_api.lua`, `wmgj.nmd`, `globalcontroller.conf`, `filters` и три `gshop{,1,2}.data`. `world_manager::FirstStepInit` в ELF обращается к `[Template] Root` и соответствующим ключам, включая `MallData`, `Mall2Data`, `Mall3Data`. `globalcontroller.conf` читает `world_manager::InitBase`. В Linear `tasks.data` и `aipolicy.data` уже содержат выбранные RU-данные под ожидаемыми именами.
- Скопировать рекурсивно файлы по шаблону `^gamed/config/(?:world|[abm][0-9]{2,3}|random[0-9]{2})/`. Он покрывает **113 каталогов Linear**. В них входят все **101** различных `base_path` для 108 алиасов и ещё 12 архивных наборов. Убрать управляющие файлы с именами `restart2` и `restart_zhang` внутри этих каталогов. Вне шаблона остался `gamed/config/мусор/`. Найденный только в VM `gamed/config/mtv/` состоит из пустых каталогов.
- Карта выбирает папку через `gs.conf` → `[Template] Root` + `base_path` в её секции `[World_…]` или `[Instance_…]`. Имена NPC, регионов, маршрутов, коллизий и описаний карт идут из `NPCGenFile`, `RegionFile`, `RegionFile2`, `PathFile`, `CollisionFile` и `MapDespFile`. В наборах есть файлы без расширения, поэтому выбор делается по каталогу. Если используем ветку перезапуска карты, штатный параметр `[Template] RestartShell` задаёт имя сценария относительно папки карты. За жизненный цикл в нашем развёртывании отвечает своя обвязка.

[Конфиг VM](evidence/config-keys.tsv) · [Как выбираются карты](maps.ru.md) · [Языковые варианты данных](server-locales.ru.md)

### Водные карты `gs01`

В `Linear/PWServer176.7z` проверены 4 276 записей файлов и ссылок под `root/pwserver/`. Иероглифы есть в двух путях. Это `都城实验.wmap` и `露录鲁脟脢碌脩茅.wmap` в `gamed/config/world/watermap/`. Они входят в группу из восьми `.wmap` с нечисловыми именами. У всех восьми размер 116 байт и SHA-256 `4e6444e28ff65016cdac2fc70387e9055ef50639a1d5e9dd9a00b12eadcbc7c0`. [Имена из оглавления Linear](evidence/distributions/path-encoding/linear-path-corrections.csv)

Для `gs01` параметры `[Template] Root = ./config/` и `[World_gs01] base_path = world/` задают каталог `gamed/config/world/`. В `watermap/watermap.conf` указаны `Map Width = 8` и `Map Length = 11`. Статическая проверка оригинального `gamed/gs` Build 4311 подтвердила, что `CGlobalWaterAreaMap::Load(char const*)` (`0x1593382`) читает размеры, вычисляет номера клеток, формирует имена по шаблону `%d.wmap` и открывает каждый такой путь через `fopen`. [Отпечаток ELF](evidence/fingerprints.tsv) · [Соответствующий загрузчик в H176](https://github.com/huzeming/176source/blob/c0992a29c0848de4de139a8958ceb11edcf2d38b/cgame/gs/pathfinding/GlobalWaterAreaMap.cpp#L73-L132)

Для штатного `gs01` в этой поставке сохраняем `watermap.conf` и `1.wmap`–`88.wmap`. Все 88 файлов есть в архиве. Восемь дополнительных `.wmap`, включая два с иероглифами, можно исключить при подготовке пакета Linear.

## Данные вне образа и системные входы

- Смонтировать `gamedbd/dbhome` и `uniquenamed/dbhome` отдельными томами целиком. `[storagewdb]` задаёт `homedir`, пути к `dbdata` и `dblogs` внутри него и `backupdir`. При штатном `[gamedbd] noimportclsconfig=0` `gamedbd` импортирует `./clsconfig` в WDB через `system()` и `/bin/cp`. В системном слое нужны `/bin/sh` и `/bin/cp` даже при своей обвязке.
- `root/sql/{pw176,licenseservice}.sql` — входы инициализации отдельной MariaDB. Оставить доступные для записи `logs/` и `/tmp`. Пути UNIX-сокетов карт задают `listen_addr` и `address` в секциях `[MsgReceiverUNIX_<алиас>]` файла `gs.conf`. Обычные журналы и диагностические файлы создаются при работе.
- Системный слой — amd64 с glibc, загрузчиком `/lib64/ld-linux-x86-64.so.2` и библиотеками `libstdc++.so.6`, `libgcc_s.so.1`, `libpcre.so.3`, `libmariadb.so.3`, `libcrypto.so.3`. [ABI `gs`](services/gs.ru.md) · [WDB и MariaDB](storage-and-recovery.ru.md)

## Как классифицировать файлы вне базового набора

| Группа | Примеры и решение |
|---|---|
| Артефакты упаковки | Запасные `gs_v*`, `*d1`, `glinkd!!!`, локальные журналы, выгрузки и варианты `clsconfig*`, `elements*`, `tasks-176-*`, `aipolicy-176-*`. В образе оставляем выбранные версии под штатными именами. |
| Обвязка раздачи и обслуживание | `start`, `stop`, `server`, `maps`, `dc`, `dr`, сценарии обслуживания и панели. В раздаче `maps` читает `/root/server`, а при прямом запуске алиас передаётся как аргумент `gs`. `dbtool`, `dbanlz`, `base_util` принадлежат комплекту обслуживания WDB. `exportrole` и `importrole` встроены в `gamedbd`. |
| Условные ресурсы с известным потребителем | `domain2.sev`, `domain2_cross.sev`, `webtradeid.txt`, наборы карт за пределами стартовых алиасов. Сохраняем их для соответствующих режимов. `restart2` и `restart_zhang` связаны с крюком перезапуска карты, который при прямом управлении жизненным циклом заменяет обвязка. |
| Ресурсы других версий и клиента | `gamed/libtask.so` и `gamed/libskill.so` нужны некоторым другим ELF, код 4311 содержит задачи и навыки в `gs`. `skill.lua` загружался в S172. `gshop3.data` нужен для воспроизведения клиентского патча, в `gs` 4311 найден потребитель только для `MallData`–`Mall3Data`. |
| Потребитель пока не установлен | `gamedbd/gamedata`, `gdeliveryd/domain{,2}.data`, `gacd/{charfont,charlib,hzfont}.dat` и `gamed/config/{domain*,DynamicObjects.data,task_npc.data,serverlist.sev,world_targets.txt,rare_item2.conf,special_item.conf,sysauctionlist.txt,webtradeid.txt}`. Решение об их исключении относится к проверенному профилю запуска. |

У `gamedbd` есть ветка чтения `forbidpolicy.conf`. В архиве Linear этот файл отсутствует, инициализация переносит такое отсутствие. Расширение файла само по себе ничего не говорит о потребителе. Например, `domain.sev` читает `gdeliveryd` при старте территориальной подсистемы, а вложенный `domain.data` имеет неизвестное назначение для 4311. [Подтверждённые загрузчики и условия](dynamic-resources.ru.md)

На VM с этим сокращённым деревом запустились все девять демонов и по отдельности зарегистрировались карты `gs01`, `is61`, `is02`. Потребность в ресурсах условных режимов оценивается по их загрузчикам и профилям. [Протокол проверки исключений](../experiments/image-file-validation/image-file-validation.ru.md)
