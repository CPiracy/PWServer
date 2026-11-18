# Когда сервер 4311 читает игровые ресурсы

В комплекте 1.7.6 Build 4311 код задач и навыков присутствует внутри `gs`. Для `gamed/libtask.so`, `gamed/libskill.so`, `gamed/skill.lua` и `gamed/config/gshop3.data` штатный потребитель в проверенном `gs` не найден. `gdeliveryd/domain.sev` читается при инициализации территориальных сражений. Чтение `domain2.sev` или `domain2_cross.sev` привязано к объявлению группы зон. [Инвентарь запускаемых файлов](image-files.ru.md) · [Отпечатки ELF](evidence/fingerprints.tsv)

Здесь **4311** означает ELF из `Linear/PWServer176.7z!root/pwserver/`, сверенные со снимком работающей VM. **H176** и **S172** означают деревья `GitHub/huzeming-176source` и `GitHub/172source`. **A174** и **A178** означают деревья `RageZone/174.rar!SOURCE/SourceServer174/` и `RageZone/PW1.7.6Playerbots.rar!PW1.7.6Playerbots/PW_178_SRC/`. Пути к архивам и деревьям даны от корня коллекции Perfect World Server. Адреса вызовов относятся к ELF 4311 до загрузки. Исходники других веток помогают расшифровать вызовы и условия в 4311, но не подтверждают идентичность реализации. [Ревизии и сопоставление исходников](source-coverage.ru.md)

## Библиотеки задач, навыков и Lua

С 18 ноября все семь Lua-файлов четырёх комплектов [сопоставлены отдельно](server-lua.ru.md). Шесть путей побайтово одинаковы, у `gamed/script.lua` совпали значимые токены; принято относить игровую Lua-логику к серверному пакету.

В `DT_NEEDED` у `gamed/gs` перечислены `libpcre.so.3`, `libcrypto.so.3`, `libmariadb.so.3`, `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1` и `libc.so.6`. В самом ELF находятся определения `GNET::SkillWrapper::Initialize`, `ATaskTemplMan::LoadTasksFromPack` и `ATaskTemplMan::LoadDynTasksFromPack`. Из `LoadTasksFromPack` игровые загрузчики вызываются по адресам `0x1560231` и `0x156027f`. Имена `libtask.so`, `libskill.so` и `skill.lua` отсутствуют в проверенных секциях данных `gs`. Две `.so` отсутствуют и в сохранённых списках отображений процессов `gs01` и `is61`. Размеры и CRC вложенных библиотек совпадают с файлами `libtask.so__orig` и `libskill.so__orig` из раздачи talolan. [Карточка 4311 GS](services/gs.ru.md) · [Сверка вариантов talolan](distribution-provenance.ru.md)

У `gs` есть импорты `dlopen`, `dlsym` и `dlclose`. Найденные прямые вызовы первых двух идут из `lookforfunc` по адресам `0x2ddbf75` и `0x2ddbf24`. `dlclose` вызывается из `gctm` в `0x2ddc110`. Это функции встроенной Lua 5.4.4. Та же схема видна в `gdeliveryd`, `gamedbd` и `gacd`. `require` ищет Lua-файлы через `package.path` и C-модули через `package.cpath`, а `package.loadlib` использует переданный путь. В ELF 4311 есть шаблоны поиска `./?.lua`, `./?/init.lua`, `./?.so` и каталоги под `/usr/local/{share,lib}/lua/5.4/`. В H176 `share/lua/src/loadlib.c:291–305,390–415,545–606,744–745` инициализация путей учитывает `LUA_PATH_5_4`, `LUA_CPATH_5_4` и их варианты без номера версии. В архивных `script.lua` для GS, `gauthd`, `gfactiond`, `gamedbd`, `gdeliveryd`, а также в `skill.lua` и `global_api.lua` прямых обращений к `require`, `loadfile`, `dofile`, `package.loadlib` и двум игровым `.so` при поиске по тексту не обнаружено. [Ревизии исходников](source-coverage.ru.md)

| Файл | Когда и как читается |
| --- | --- |
| `gamed/script.lua` | 4311 `main` вызывает `LuaBase::Init()` в `0xf56df5`. Имя берётся внутри функции и разрешается от рабочего каталога `gamed/`. H176 `share/io/luabase.cpp:252–300` создаёт Lua state, читает и выполняет `script.lua`. Таймер проверяет `mtime` на каждом тридцатом тике. При изменении H176 закрывает старое состояние, создаёт новое и вызывает обновление скрипта. Функция `LuaBase::HeartBeat` в 4311 вызывает `Update` в `0x1686f97`. Ошибка исполнения в H176 не оставляет прежнее Lua state в качестве запасного. |
| `gamed/config/global_api.lua` | `[Template] LuaData = global_api.lua` под `Root = ./config/`. В 4311 `world_manager::FirstStepInit` вызывает `LoadLuaVersion` в `0x115676a`. H176 и A178 открывают файл и извлекают положительный номер из первой строки `--<номер>`. Это чтение версии при старте, с возвратом ошибки при открытии или неверной версии в H176. Загрузка Lua state относится к `script.lua`. |
| `gamed/skill.lua` | В S172 `cskill/skill/skillwrapper.cpp:66` подключает его через `LuaSkill::Init`. В H176 это строка-комментарий в `cgame/gs/skillwrapper.cpp:66` и `cskill/skill/skillwrapper.cpp:67`. То же видно в A174 `cskill/skill/skillwrapper.cpp:66` и A178 `cskill/skill/skillwrapper.cpp:69`. Для 4311 подтверждён код умений в ELF, использование отдельного скрипта не подтверждено. |
| `gauthd/script.lua`, `gfactiond/script.lua`, `gamedbd/script.lua`, `gdeliveryd/script.lua` | Вызов местного `LuaManager::Init` находится в `main` 4311 по адресам `0x9f7ca`, `0xbab43`, `0x25baf9` и `0x3f2399` соответственно. У всех четырёх виден вызов `Update` из `HeartBeat`. В H176 `cnet/gauthd/luaman.cpp:164–222` и S172 `cnet/gdeliveryd/luaman.cpp:202–248` обновление проверяет время изменения местного `script.lua`. Литерал `script.lua` в общем Lua-коде прочих демонов сам по себе не подтверждает его использование при старте. |

В A178 `cgame/gs/gs` уже имеет две прямые зависимости `DT_NEEDED` от `libtask.so` и `libskill.so` по абсолютным путям. Сборочный `gs.deploy` меняет эти пути на размещение в `/opt/gamed/`. Пара библиотек нужна этой сборке уже при запуске загрузчика ELF. Результат для 4311 относится к его конкретному бинарнику. [Отчёт об A178](source-178-export.ru.md#что-осталось-от-октябрьского-экспорта)

## Как GS выбирает данные и карту

Первый аргумент `gs` задаёт алиас карты, по умолчанию `gs01`. Следующие три аргумента заменяют `gs.conf`, `gmserver.conf` и `gsalias.conf`. Смена имени конфигурации сохраняет `cwd` процесса. Аргументы видны в H176 `cgame/gs/start.cpp:197–204`. `[Template] Root` из комплектного `gs.conf` равен `./config/`. H176 соединяет значение ключа с `Root` или с `Root + base_path` как строки, включая разделители из самих значений. Чтение общих ключей видно в H176 `cgame/gs/worldmanager.cpp:1165–1337` и `cgame/gs/template/globaldataman.cpp:228–255`. Значения ниже взяты из `Linear/PWServer176.7z!root/pwserver/gamed/gs.conf:62–87,105–109,3073–3076`. [Фактические ключи](evidence/config-keys.tsv) · [Покрытие исходниками](source-coverage.ru.md)

| Ключи в комплекте 4311 | Файлы и момент чтения |
| --- | --- |
| `[Template] itemDataFile`, `PolicyData`, `DropData`, `GlobalData` | `elements.data`, `aipolicy.data`, `extra_drops.sev`, `world_targets.sev` под `Root` при общей инициализации. Ошибка чтения в этих вызовах H176 прекращает запуск GS. |
| `[Template] QuestPackage`, `QuestPackage2` | `tasks.data` и `dyn_tasks.data` под `Root` при общей инициализации. H176 `cgame/gs/task/TaskServer.cpp:18–25` последовательно загружает базовый пакет и пакет динамических заданий. Слово «динамический» относится к типу заданий. Штатная автоматическая перечитка этих файлов GS не установлена. В VM `tasks.data` является ссылкой на выбранный RU-вариант. При переносе набора путь должен разрешаться в соответствующий файл. |
| `[Template] MallData`, `Mall2Data`, `Mall3Data` | `gshop.data`, `gshop1.data`, `gshop2.data` под `Root`. В 4311 `FirstStepInit` передаёт их вместе с `GlobalData` в `globaldata_loadserver` в `0x115618e`. H176 пропускает второй или третий магазин при пустом ключе, но непустой путь с ошибкой чтения прерывает инициализацию. В комплектном конфиге все три пути заданы. |
| `[Template] Mall4Data` | В конфиге 4311 задан `gshop3.data`. Ключ отсутствует в проверенных секциях ELF, загрузчик имеет аргументы только для трёх магазинов. Такое же ограничение видно в H176 и A178. `gshop3.data` совпадает по размеру и CRC с файлом клиентского RU-патча, поэтому это отдельный ресурс раздачи даже без подтверждённого чтения сервером. |
| `[World_…]` или `[Instance_…] base_path`, `[Terrain_…] mapres_type`, `[Template] NPCGenFile`, `RegionFile`, `RegionFile2`, `PathFile`, `CollisionFile`, `MapDespFile` | Выбранный процесс читает каталог карты. В 4311 `[World_gs01] base_path = world/`, а `[Instance_is61] base_path = a61/`. Ключи добавляют `npcgen.data`, `precinct.sev`, `region.sev`, `path.sev`, `map.bht` и `map_desp.sev`. Поднабор зависит от режима карты и наличия вызова в выбранном менеджере. H176 `mapresman.cpp:28–42` использует `origin`, если тип не равен `random`, `maze` или `solo_challenge`. `MapResManager::Init` загружает terrain, навигацию, коллизии и NPC при инициализации менеджера. |

H176 вызывает `FirstStepInit` до выбора менеджера конкретной карты и перед ответвлением процессов при запуске нескольких алиасов одним вызовом. Затем `global_world_manager::Init` или `instance_world_manager::Init` рассчитывает `base_path` и читает ресурсы своего шаблона. Создание очередной копии внутри уже работающего instance GS на показанном пути берёт объект из `_planes_pool`. Оно отличается от холодного запуска нового GS, для которого снова нужны общие и локальные входы. В ELF 4311 есть ссылки на `base_path` из обоих менеджеров и на `NPCGenFile`, `CollisionFile`, `MapDespFile` из `MapResManager::Init`. Готовность маршрута карты определяется отдельно от удачного открытия этих файлов. Точки H176 — `cgame/gs/start.cpp:241–304`, `cgame/gs/mapresman.cpp:28–42,63–112,130–232` и `cgame/gs/instance/instance_manager.cpp:778–815`. [Наблюдения по картам 4311](maps.ru.md) · [Ревизии исходников](source-coverage.ru.md)

### Выбор варианта одного ресурса

В архиве Linear есть несколько редакций для одного входного файла. Для каждого такого входа выбирается один файл, который будет доступен загрузчику по штатному ключу или пути.

| Штатный файл | Вход загрузчика | Варианты в архиве |
| --- | --- | --- |
| `aipolicy.data` | `PolicyData` | Шесть редакций RU, EN и CN с метками 5124 и 5385. Штатный файл совпадает с `5124-ru-pure`. |
| `tasks.data` | `QuestPackage` | Три редакции формата 191. RU и BR содержат по 21 606 корневых заданий, CN — 21 630. Штатный файл совпадает с RU 21 606. |
| `elements.data` | `itemDataFile` | `elements-orig.data` и `elements-bug list 302.data` имеют тот же номер формата, что штатный файл. Это кандидаты на выбор после проверки с соответствующим клиентом. |
| `rare_item.conf` | `RareItem` | `rare_item.conf` содержит 833 ID, `rare_item2.conf` — 17 ID и комментарий. Обе записи соответствуют формату списка, который читает `LoadRareItemList`. |
| `gamedbd/clsconfig` | Импорт из `./clsconfig` | `clsconfig-o` и `clsconfig_176_pure` — разные архивные кандидаты на вход импорта. Для них проверен состав архива, а чистый запуск выполнен со штатным `clsconfig`. |

Для заданий `QuestPackage2` отдельно подключает `dyn_tasks.data`. В одном запуске открываются выбранный основной пакет и пакет динамических заданий. `GlobalData` выбирает `world_targets.sev` в двоичном формате, а одноимённый `world_targets.txt` записан в UTF-16LE. [Загрузчик заданий](https://github.com/huzeming/176source/blob/c0992a29/cgame/gs/task/TaskServer.cpp#L18-L25) · [Сверка вариантов](server-locales.ru.md) · [Инвентарь Linear](evidence/distributions/linear-7z-archive.csv)

### Магазины и составные наборы

`gs` 4311 последовательно открывает три настроенных каталога магазина за один запуск. В ELF `globaldata_loadserver` вызывается по `0x115618e`, а три вызова `load_malldata` по `0x151df03`, `0x151df4d` и `0x151df97` заполняют разные коллекции. Во всех трёх холодных прогонах зарегистрированы открытия `gshop.data`, `gshop1.data` и `gshop2.data`. [Загрузчик H176](https://github.com/huzeming/176source/blob/c0992a29/cgame/gs/template/globaldataman.cpp#L228-L256) · [Контроль открытий](../experiments/image-file-validation/evidence/image-file-validation.json)

| Файл в `gamed/config` | Записей | Назначение |
| --- | ---: | --- |
| `gshop.data` | 1 470 | Основной магазин. В 4311 `PlayerDoShopping` вызывает `GetPlayerMall`. |
| `gshop1.data` | 190 | Магазин за дивиденды. `PlayerDoDividendShopping` вызывает `GetPlayerMall2` и `SpendDividend`. |
| `gshop2.data` | 5 | Магазин за баллы Cash VIP. `PlayerDoCashVipShopping` вызывает `GetPlayerMall3` и `SpendCashVipScore`. |
| `gshop3.data` | 18 | Клиентский каталог костюмов. В `elementclient_64.exe` функция `GlobalData_Load` передаёт все четыре пути одному загрузчику, обращение к `Data\gshop3.data` находится по RVA `0x29221f`. Штатный серверный профиль 4311 запущен без этого файла. |

Числа записей получены разбором файлов проверенного RU-клиента, которые совпадают с комплектом сервера по SHA-256. Сохраняем все четыре используемых каталога. `MallData`, `Mall2Data` и `Mall3Data` образуют комплект входов сервера. `gshop3.data` сохраняем в наборе клиента. `gshop*.data` из `gamed/config/мусор` находятся вне этих путей. [Хэши комплектов](server-patching.ru.md#что-меняется-в-build-4311) · [Клиентский набор](client-server-sync.ru.md)

Составные карты тоже используют несколько входов. Для карты `rand04` конфиг задаёт `base_path=random04/`, `mapres_type=maze` и `nPiece=64`. `MapResManager::Init` читает основной `npcgen.data`, затем загружает `npcgen/npcgen_1.data` … `npcgen/npcgen_64.data` в цикле. Основной вызов `CNPCGenMan::Load` в ELF 4311 находится по `0x11e88cf`, вызов для фрагментов по `0x11e89a2`. Состав из 65 файлов подтверждён архивом и кодом загрузчика для этой карты.

## Домены, WDB и античит

| Путь | Подтверждённый потребитель и условие |
| --- | --- |
| `gdeliveryd/domain.sev` | В 4311 `main` вызывает `BattleManager::Initialize` в `0x3f4c97`, оттуда вызов `domain_data_load` в `0x40db8b`. Файл открывается из `cwd` службы. В S172 `[GDeliveryServer] battlefield=0` или пустое значение отключает ветку. При включённой ветке сбой загрузки завершает сервер с ошибкой. Комплект 4311 задаёт `battlefield=1`. |
| `gdeliveryd/domain2.sev`, `gdeliveryd/domain2_cross.sev` | В 4311 `AnnounceZoneGroup::Process` вызывает `CountryBattleMan::OnInitialize` в `0x2b23e1`. Цепочка продолжается вызовами `Initialize` (`0x42ce9b`), `InitDomainInfo` (`0x4228a4`) и `domain2_data_load` (`0x422558`). S172 проверяет `[COUNTRYBATTLE] is_countrybattle_open`, в локальном режиме инициализирует одну группу и выбирает `domain2.sev`. При распределении по зонам выбирает `domain2_cross.sev`. В комплекте 4311 `is_countrybattle_open=1`, `[GDeliveryServer] is_central_ds=false`. Регистрация карты `CountryBattleServerRegister` заполняет сведения о серверах через отдельный обработчик и сама по себе чтение `.sev` не подтверждает. |
| `gdeliveryd/domain.data`, `gdeliveryd/domain2.data` | Лежат рядом с серверными `.sev`, имеют другие размеры. Для этих имён не найдено прямого чтения в ELF 4311 или в проверенных загрузчиках S172 и A178. Одинаковая основа имени не делает файлы взаимозаменяемыми. `gamed/config/domain*.data` и `gamed/config/domain2.sev` относятся к другому каталогу и не подхватываются этим относительным открытием в `gdeliveryd`. |
| `gamedbd/serverlist.sev`, `gamedbd/clsconfig` | `GameDBManager::LoadZoneNameConfig` открывает `./serverlist.sev`. В S172 и A178 сбой чтения завершает штатный запуск. Отдельный `gamed/config/serverlist.sev` имеет другой размер. Импорт `./clsconfig` определяется `[gamedbd] noimportclsconfig=0` и `[GameDBServer] is_recall_server=false` в комплекте. Файл поступает в `dbhome/dbdata/clsconfig`, а данные и журналы WDB берутся из `[storagewdb]`. |
| `gamedbd/gamedata` | В Linear это отдельный текстовый файл, 178 байт в форме Base64. Связь с `dbhome`, конфигом, штатным `script.lua` или ELF 4311 не найдена. Назначение файла остаётся неподтверждённым. |
| `gacd/gacd.xml`, `gacd/{charfont,charlib,hzfont}.dat` | В 4311 `main` передаёт `gacd.xml` в `ConfigManager::Init` в `0xeb2ad`. В коде также есть отдельный вызов `ConfigManager::Reload` с буфером XML в `0xad918`. В H176 `cnet/gacd/configmanager.cpp:15–54` старт читает файл, а обновление из буфера заново разбирает переданный XML. Три `.dat` не названы в активном XML, ELF или просмотренных исходниках загрузчиков. Назначение и использование этих файлов в проверенном режиме не подтверждены. |

Значения `battlefield`, `is_central_ds` и `is_countrybattle_open` выбирают режимы. Имена `.sev` фиксированы в S172 `cnet/gdeliveryd/domaindataman.cpp:15–62`. Чтение доменов связано с указанными инициализациями. Ветка объявления группы зон может вызвать инициализацию повторно по S172 `cnet/gdeliveryd/announcezonegroup.hpp:17–31` и `cnet/gdeliveryd/countrybattleman.cpp:2795–2805`. У `gacd` предусмотрено отдельное обновление XML из входного буфера. [Ревизии исходников](source-coverage.ru.md) · [Инвентарь и признаки импорта WDB](storage-and-recovery.ru.md)

### Территории в `gamed/config`

Домены здесь обозначают игровые территории. В записях есть ID, имена, центры областей, вершины и треугольники контуров, соседи и параметры боёв. Клиентский `GlobalData_Load` ссылается на `Data\domain.data`, `Data\domain2.data` и `Data\domain2_cross.data` по RVA `0x2918be`, `0x291ce1` и `0x291cff`. Все три архивных файла разобраны до конца по структурам из `GitHub/MyAceEditor/PerfectWorld/DomainFile.cs:39–78`.

| Путь в `gamed/config` | Содержимое |
| --- | --- |
| `domain.data` | 52 области карты территориальных войн. Есть награды, граф соседства и расписания. |
| `domain2.data` | 42 области Битвы династий, две нации и две столицы. |
| `domain2_cross.data` | 292 области межсерверной Битвы династий, четыре нации и четыре столицы. |

В проверенном RU-клиенте соответствующие файлы содержат 52, 132 и 292 области. В `domain.data` совпали геометрия и соседи, а имена и расписание расходятся. В `domain2_cross.data` обнаружены различия только в полях имён. При подготовке клиента используем данные из согласованного клиентского набора. [Сверка доменов клиента и сервера](client-server-sync.ru.md#одноимённые-файлы-вне-патча)

Три `gamed/config/domain*.data` сохраняем как варианты клиентских ресурсов территорий. Все три и отдельный `gamed/config/domain2.sev` отсутствовали на контрольном чистом серверном запуске с двумя зарегистрированными картами. В `gs` и его конфигах чтение этих путей не обнаружено. Для территориальных механик координатор открывает свои `gdeliveryd/domain.sev` и `gdeliveryd/domain2.sev`. `gdeliveryd/domain2_cross.sev` выбирается межсерверной веткой и сохраняется для поддержки этого профиля. [Чистый запуск](../experiments/package-layout/clean-start-experiment.ru.md#входные-файлы) · [Открытия файлов координатора](../experiments/image-file-validation/evidence/image-file-validation.json)

### Справочники зон `serverlist.sev`

Обе записи из Linear разобраны как последовательность пар `zoneid → имя зоны`. Формат записи состоит из 32-битного ID, 32-битной длины в кодовых единицах и имени UTF-16LE.

| Путь | Содержимое | Загрузка в 4311 |
| --- | --- | --- |
| `gamed/config/serverlist.sev` | ID 1 — `Servidor`, 24 байта, CRC32 `477B042E`. | Можно исключить из серверного профиля. Без файла прошли предыдущие холодные старты и чистый старт с WDB с нуля. |
| `gamedbd/serverlist.sev` | ID 1 — `天策`, 2 — `二区`, 3 — `跨服`, 36 байт, CRC32 `1D3DBAD6`. | Сохраняем в рабочем каталоге GameDB. `main` вызывает `LoadZoneNameConfig` по `0x25d7cb`. Контрольный запуск без этого файла завершился с кодом 1. |

В S172 `cnet/gamedbd/abstractplayers.cpp:10–37` функция `GenerateCDSRoleName` добавляет имя исходной зоны к имени персонажа при межсерверном переносе. В обычном локальном профиле сам справочник также загружается при старте `gamedbd`. Адрес и порт подключения игрового клиента задаются отдельно в `patcher/server/serverlist.txt`. [Исходники и ревизии](source-coverage.ru.md) · [Контроль запуска GameDB](../experiments/package-layout/clean-start-experiment.ru.md#входные-файлы) · [Настройка клиента](rutracker-1.7.6-4311-usage.ru.md)

## Как проверить исключения из серверного комплекта

В контрольном запуске 4311 зафиксировано открытие обоих файлов `gdeliveryd/domain.sev` и `gdeliveryd/domain2.sev`. Для сохранённых `domain2_cross.sev` и `webtradeid.txt` событий открытия в этом прогоне нет. Три карты зарегистрировались с сокращённым набором, при этом системные пути к `libtask.so` также были скрыты в окружении проверки. [Выполненный контроль](../experiments/image-file-validation/image-file-validation.ru.md)

`libtask.so` и `libskill.so` можно рассматривать как архивные файлы для выбранного 4311 после проверки холодного запуска и путей загрузки. `skill.lua` имеет потребителя в S172. `gshop3.data` входит в клиентскую поставку, а `domain2_cross.sev` нужен межсерверной ветке. Эти файлы имеют назначение вне текущего штатного пути. Для `gamedbd/gamedata`, `gdeliveryd/domain*.data` и трёх `.dat` `gacd` вывод ограничивается отсутствием найденного потребителя. Для исключения из рабочего образа важен результат в выбранных режимах. [Сравнение содержимого поставок](distribution-provenance.ru.md)

Наблюдение за чтениями начинается до холодного старта. `inotify` с `IN_OPEN` фиксирует успешные открытия известных файлов, но не сообщает PID открывшего процесса и не видит неудачные попытки. Трасса файловых системных вызовов с потомками показывает и открытия, и `stat`, а `/proc/<pid>/maps` сохраняет доказательство оставшихся отображений библиотек. Положительные контроли для `gs` — `config/elements.data`, `config/tasks.data`, `config/gshop{,1,2}.data`, `config/global_api.lua` и `script.lua`, а для новой карты — файлы её `base_path`. Для `gdeliveryd` это `domain.sev` при `battlefield=1`, для `gamedbd` — `serverlist.sev`, для `gacd` — `gacd.xml`. Отрицательные контроли — оба игровых `.so`, `skill.lua`, `gshop3.data`, доменные `.data`, `gamedata` и три `.dat` античита в том же прогоне. `domain2*.sev` проверяются в прогоне, где действительно получено объявление группы. Отсутствие события означает, что обращение не зарегистрировано данным методом в пределах прогона. Успешное открытие файла подтверждает доступ к пути. Корректный разбор ресурса и готовность службы подтверждаются её журналом или результатом операции. [Границы серверных проб](../experiments/server-validation/server-only-validation.ru.md)
