# Файлы игрового образа PW 1.7.6 Build 4311

Источник для первого образа — `Linear/PWServer176.7z`, дерево `root/pwserver/`. У всех десяти штатных ELF совпал SHA-256 со снимком работающей VM. Текущая VM подтвердила совпадение `gs.conf`, `gmserver.conf`, `gsalias.conf`, `maps`, `elements.data` и выбранных RU-данных `tasks.data` и `aipolicy.data`. Деревья различаются, например в VM два последних файла представлены ссылками. Происхождение комплекта как официальной поставки остаётся открытым. [Отпечатки VM](evidence/fingerprints.tsv) · [Происхождение сборок](distribution-provenance.ru.md)

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
| `gdeliveryd/gdeliveryd` | `gamesys.conf` | `gamesys.conf`, `script.lua`, `filters`, `domain.sev`, `domain2.sev`, `auctionid.txt`, `sysauctionlist.txt`. Имя фильтра задаёт `[GDeliveryServer] table_name`. `domain2_cross.sev` нужен межсерверному режиму, `webtradeid.txt` — веб-торгам. |
| `glinkd/glinkd` | `gamesys.conf 1` | `gamesys.conf`. `1` — номер шлюза в наблюдавшемся запуске. |

`script.lua` в таблице — входы игрового Lua, их сохраняем. У `gauthd`, `gamedbd`, `gfactiond`, `gdeliveryd` и `glinkd` в ELF подтверждён абсолютный путь `/home/license.conf`. Файл подаётся по этому пути при развёртывании. Реквизиты MariaDB в конфигурациях `gauthd` и `licenseservice` задаются в `[GMysqlClient]`. [Аргументы и рабочие каталоги VM](evidence/runtime.json) · [Описание служб](README.ru.md#отчёты-по-службам)

У `gs` относительное имя `ptemplate.conf` читают менеджеры мира и инстансов. `EmulateSettings::Init` и `InstanceSettings::Init` используют `settings.conf`, `RankingManager::Init` — `ranking.conf`, `LuaBase::Init` — `script.lua`. Ссылки проверены в ELF 4311.

## Общие ресурсы и карты `gs`

- В `gamed/config/` взять `elements.data`, `tasks.data`, `dyn_tasks.data`, `world_targets.sev`, `aipolicy.data`, `extra_drops.sev`, `rare_item.conf`, `global_api.lua`, `wmgj.nmd`, `globalcontroller.conf`, `filters` и три `gshop{,1,2}.data`. `world_manager::FirstStepInit` в ELF обращается к `[Template] Root` и соответствующим ключам, включая `MallData`, `Mall2Data`, `Mall3Data`. `globalcontroller.conf` читает `world_manager::InitBase`. В Linear `tasks.data` и `aipolicy.data` уже содержат выбранные RU-данные под ожидаемыми именами.
- Скопировать рекурсивно файлы по шаблону `^gamed/config/(?:world|[abm][0-9]{2,3}|random[0-9]{2})/`. Он покрывает **113 каталогов Linear**. В них входят все **101** различных `base_path` для 108 алиасов и ещё 12 архивных наборов. Убрать управляющие файлы с именами `restart2` и `restart_zhang` внутри этих каталогов. Вне шаблона остался `gamed/config/мусор/`. Найденный только в VM `gamed/config/mtv/` состоит из пустых каталогов.
- Карта выбирает папку через `gs.conf` → `[Template] Root` + `base_path` в её секции `[World_…]` или `[Instance_…]`. Имена NPC, регионов, маршрутов, коллизий и описаний карт идут из `NPCGenFile`, `RegionFile`, `RegionFile2`, `PathFile`, `CollisionFile` и `MapDespFile`. В наборах есть файлы без расширения, поэтому выбор делается по каталогу. Если используем ветку перезапуска карты, штатный параметр `[Template] RestartShell` задаёт имя сценария относительно папки карты. За жизненный цикл в нашем развёртывании отвечает своя обвязка.

[Конфиг VM](evidence/config-keys.tsv) · [Как выбираются карты](maps.ru.md) · [Языковые варианты данных](server-locales.ru.md)

## Данные вне образа и системные входы

- Смонтировать `gamedbd/dbhome` и `uniquenamed/dbhome` отдельными томами целиком. `[storagewdb]` задаёт `homedir`, пути к `dbdata` и `dblogs` внутри него и `backupdir`. При штатном `[gamedbd] noimportclsconfig=0` `gamedbd` импортирует `./clsconfig` в WDB через `system()` и `/bin/cp`. В системном слое нужны `/bin/sh` и `/bin/cp` даже при своей обвязке.
- `root/sql/{pw176,licenseservice}.sql` — входы инициализации отдельной MariaDB. Оставить доступные для записи `logs/` и `/tmp`. Пути UNIX-сокетов карт задают `listen_addr` и `address` в секциях `[MsgReceiverUNIX_<алиас>]` файла `gs.conf`. Обычные журналы и диагностические файлы создаются при работе.
- Системный слой — amd64 с glibc, загрузчиком `/lib64/ld-linux-x86-64.so.2` и библиотеками `libstdc++.so.6`, `libgcc_s.so.1`, `libpcre.so.3`, `libmariadb.so.3`, `libcrypto.so.3`. [ABI `gs`](services/gs.ru.md) · [WDB и MariaDB](storage-and-recovery.ru.md)

## Что оставить за пределами стартового списка

- Панели, `iwebx32`, `start`, `stop`, `server`, `maps`, файлы обслуживания `dc`, `dr`, `*.sh`, запасные `gs_v*`, `*d1`, `glinkd!!!`, локальные журналы и выгрузки. В раздаче `maps` читает сценарий `/root/server`. Наш запуск будет передавать выбранные алиасы как аргументы `gs`.
- `dbtool`, `dbanlz`, `base_util` — инструменты обслуживания WDB. `exportrole` и `importrole` уже находятся внутри `gamedbd`. Запасные варианты `clsconfig*`, `elements*`, `tasks-176-*` и `aipolicy-176-*` держать рядом с исходным архивом, если в образ копируются текущие файлы под штатными именами.
- Кандидаты на исключение с проверкой чистого запуска — `gamed/{libtask.so,libskill.so,skill.lua}`, `gamed/config/gshop3.data`, `gamedbd/gamedata`, `gdeliveryd/domain{,2}.data` и `gacd/{charfont,charlib,hzfont}.dat`. У двух `*.so` нет записей `DT_NEEDED` и отображений в обоих работающих `gs`. В проверенном ELF отсутствуют строки `skill.lua` и `Mall4Data`. Для остальных файлов потребитель в проверенных путях не найден. Режимы, до которых запуск не дошёл, требуют отдельной проверки.
- В стартовый набор также не входят `gamed/config/{domain*,DynamicObjects.data,task_npc.data,serverlist.sev,world_targets.txt,rare_item2.conf,special_item.conf,sysauctionlist.txt,webtradeid.txt}`. Их чтение штатным `gs` пока не подтверждено. У `gamedbd` есть путь к `forbidpolicy.conf`, которого нет в Linear. Этот вызов не блокирует штатный старт при отсутствии файла.

Список составлен по оглавлению архива, чтению конфигов, срезу работающей VM и ссылкам из функций ELF. Холодный запуск с этим точным набором файлов остаётся следующей проверкой образа.
