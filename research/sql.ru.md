# SQL Perfect World 1.7.6 Build 4311

У Linear, Talolan и RuTracker совпадают определения всех 39 таблиц и 20 процедур `pw176`, а также обеих таблиц `licenseservice`. В комплекте с китайскими заданиями совпадают бинарники `gauthd` и `licenseservice`. Его SQL-схему по содержимому раздачи установить пока нельзя.

Из 20 процедур **18 входят в интерфейс старого Java `authd`**, две оставшиеся управляют правами GM. Все 20 определений Build 4311 уже встречались в SQL установщика, показанного на вьетнамской 1.7.3. Для чистой установки 4311 проверен запуск без строк в `pw176` при наличии штатных процедур и действующей записи в `licenseservice.users`.

## Сравнение сборок 1.7.6

Опорные файлы — `root/sql/pw176.sql` и `root/sql/licenseservice.sql` из `Linear/PWServer176.7z`. В таблицах сравнивались порядок и определения столбцов, ключи, ограничения, движок, кодировка и сопоставление. Учтены изменения из `ALTER TABLE`. Из сравнения исключены текущие счётчики `AUTO_INCREMENT`. Для процедур сравнивались сигнатуры и тела с нормализацией оформления, без учётки `DEFINER`. Для трёх комплектов 1.7.6 также сверены характеристики процедур. [Контрольные суммы и пообъектное сравнение](evidence/sql-schema-comparison.json)

| Комплект | Выбранные игровые данные | `pw176` относительно Linear | `licenseservice` относительно Linear |
| --- | --- | --- | --- |
| Linear, Build 4311 | Русские задания | Эталон, 39 таблиц и 20 процедур | Эталон, 2 таблицы |
| Talolan, VM 05/2025 | Русские задания | 39/39 таблиц и 20/20 процедур совпали | 2/2 таблиц совпали |
| RuTracker, VM 01/2026 | Русские задания | 39/39 таблиц и 20/20 процедур совпали | 2/2 таблиц совпали |
| Sranus 2025, TAR | Китайские задания и ИИ | Дампа и каталога MariaDB в архиве нет | Дампа и каталога MariaDB в архиве нет |

Дампы обеих VM прочитаны напрямую из Ext-разделов. У них побайтно совпадают `/root/sql/pw176.sql` и все 39 файлов определений `.frm` в `/var/lib/mysql/pw176`. Это два экземпляра одной SQL-схемы. В `licenseservice` табличный DDL совпадает, а настройки по умолчанию на уровне базы различаются. У Talolan задано `utf8mb4_general_ci`, у RuTracker — `utf8mb4_uca1400_ai_ci`. Обе таблицы в дампах явно используют `utf8mb3_general_ci`. [Инвентарь Talolan](evidence/distributions/talolan-052025-vm-filesystem.csv) · [Инвентарь RuTracker](evidence/distributions/rutracker-012026-vm-filesystem.csv)

В Sranus проверены весь TAR и вложенный `npcgen.rar`. `gauthd` и `licenseservice` побайтно совпали с Linear, поэтому известные SQL-вызовы этих ELF совпадают и для CN-комплекта. До получения его SQL или каталога MariaDB для пары RU/CN подтверждён только общий интерфейс этих служб. [Выбранные данные и архивы](server-distribution-comparison.ru.md#выбранные-данные-и-язык-содержимого) · [SHA-256 бинарников](evidence/distributions/selected-files.csv)

В китайской публикации от 11 марта 2026 года описана другая VM с MySQL. В открытой части указана версия 176 без номера сборки, а доступ к серверному архиву требует ответа на форуме. SQL из этой публикации пока не получен. [Тема раздачи](https://www.suvvv.com/forum.php?mod=viewthread&tid=1918)

## Сравнение с более ранними выпусками

Числа в таблице показывают, сколько определений из указанного SQL совпало с `pw176` Build 4311. При сравнении учтены эквивалентные написания типов, ширина отображения целых, историческое имя кодировки `utf8` и её сопоставление по умолчанию.

| Источник | Таблицы | Процедуры | Отличия |
| --- | ---: | ---: | --- |
| 1.4.6 v70 | 7/7 | 16/19 | Базовые таблицы совпадают. [Дамп v70](https://forum.ragezone.com/threads/perfect-world-1-4-6-register-problem.942614/post-7678418) |
| 1.4.6 v63 | 7/8 | 15/19 | `roles.role_name` и `roles.faction_name` имеют ширину `VARCHAR(32)` вместо `VARCHAR(64)`. [Дамп v63](https://forum.ragezone.com/threads/perfect-world-1-4-6-register-problem.942614/post-7678418) |
| 1.5.5, Linear | 7/7 | 16/19 | Семь базовых таблиц. `Linear/PWServer155.7z!/home/sql/pw.sql`. |
| 1.5.5 Build 2567, Docker-сборка сообщества | 8/8 | 16/19 | К семи таблицам добавлена `roles` с тем же определением, что у 4311. [SQL сборки](https://github.com/oss-perfectworld/perfectworld/blob/0c1439c8155108d4d368bcaeefc47de0134317ea/sql/db.sql) · [Публикация автора](https://forum.ragezone.com/threads/perfect-world-server-1-5-5-in-docker-compose.1203681/) |
| PWTools, установщик вьетнамской 1.7.3 | 13/13 | 20/20 | Совпали все определения предоставленного `pwa.sql`. [Дамп](https://github.com/hoangnguyent/pwtools/blob/8dd9ba34e02d07ea6d6c814a4ffd1b6a2a570024/pwa.sql) · [Импорт в установщике](https://github.com/hoangnguyent/pwtools/blob/340deee5d831e81b815db5ed71259ea8aacb5270/setup_inside_ubuntu_jammy.sh#L262-L282) · [Публикация автора](https://forum.ragezone.com/threads/share-script-to-install-game-server-automatically.1237305/) |

Семь общих таблиц — `auth`, `forbid`, `iplimit`, `point`, `usecashlog`, `usecashnow`, `users`. В PWTools к ним добавлены `files`, `online`, `roles`, `uwebplayers`, `webshop` и `wshoplog`. Автор PWTools демонстрировал установщик на вьетнамской 1.7.3. Дамп опубликован в 2024 году и содержит внутреннюю дату экспорта 30 апреля 2021 года. Исходная версия сервера, с которого экспортирован этот SQL, неизвестна.

В 4311 есть ещё 26 таблиц сверх набора PWTools, в том числе `arena_players` и `arena_teams`. Запросы к обеим есть в исходниках `gauthd` и ELF 4311. Сценарии арены предстоит проверить отдельно. [Запросы gauthd](https://github.com/huzeming/176source/blob/c0992a29/cnet/gauthd/gmysqlclient.cpp#L1011-L1243)

В архивах 1.7.4 v352 и Playerbots полного SQL учёток нет. Их `pw_arena.sql` побайтно совпал с одноимённым файлом в доступных исходниках 1.7.6. Определение `arena_players` совпадает с Linear, а у `arena_teams` 25 столбцов вместо 13. В 4311 отдельные поля участников, наград и команд заменены текстовыми `members` и `teams`. Имена этих полей есть в запросе `INSERT` нативного `gauthd`. Для пополнения схемы из старых исходников этот файл не подходит. [DDL из исходников](https://github.com/huzeming/176source/blob/c0992a29/cnet/gauthd/pw_arena.sql) · [Запись состава команды](https://github.com/huzeming/176source/blob/c0992a29/cnet/gauthd/gmysqlclient.cpp#L1189-L1243)

В SQL из репозитория `PW172v11x64` совпали 6 из 7 таблиц. Отличие в `users.passwd`, для которого добавлен `DEFAULT ''`. README того же коммита описывает 1.6.2, поэтому точная версия этого SQL неизвестна. [Дамп PW172](https://github.com/hrace009/PW172v11x64/blob/fdb6773b31c5e4b9ccd24d9ff5723433be8281a4/sql/pw.sql) · [README к нему](https://github.com/hrace009/PW172v11x64/blob/fdb6773b31c5e4b9ccd24d9ff5723433be8281a4/README.MD#L1)

В демо-дампе панели Web Platform 2015 совпали 2 из 12 таблиц. В нём `users` имеет 37 столбцов вместо 19, а `groups`, `migrations`, `throttle` и `users_groups` присутствуют только в демо. [SQL Web Platform](https://github.com/magenik/perfect-world-webplatform/blob/87537b98931aea29468df1b8d34b2ee29fac1caa/.setup/demo.sql)

В самих VM также поставляются старые дампы. У `/root/sql/old/wm.sql` 11 таблиц и 19 процедур. Все имена его таблиц встречаются в текущей `pw176`. У `/root/iweb/old/wm.sql` 30 таблиц, 27 процедур и одна функция. Среди названий таблиц 23 общие с `pw176`, а семь присутствуют только в этом старом дампе. Проверенные текущие определения взяты из файлов непосредственно в `/root/sql`. [Названия и отпечатки архивных дампов](evidence/sql-schema-comparison.json)

## Происхождение процедур

В `Linear/PWServer155.7z` сценарий `/home/auth/build/authd.sh` запускает Java-приложение с `/etc/table.xml`. В XML объявлены 18 из 20 процедур 4311. В `application.jar` класс `com.goldhuman.account.storage` передаёт их JDBC через `prepareCall`. В старых журналах 2009–2011 годов уже видны четыре вызова, которые сохранились в нативном `gauthd`. Авторство самого раннего SQL остаётся неизвестным. [Запуск 1.3.6 в 2009 году](https://forum.ragezone.com/threads/pw-136-server-files-for-use-with-mysql.556520/post-5001031) · [Четыре вызова в журнале 2011 года](https://forum.ragezone.com/threads/authd-offline.791876/post-6630511)

| Группа | Процедуры Build 4311 | Что подтверждено |
| --- | --- | --- |
| Поиск учётки и учёт сессий | `acquireuserpasswd`, `clearonlinerecords`, `recordonline`, `recordoffline` | Старый Java-контракт и явные SQL-вызовы в нативном `gauthd`. В 4311 успешный `clearonlinerecords` зафиксирован в живом запуске. [Код вызовов](https://github.com/huzeming/176source/blob/c0992a29/cnet/gauthd/gmysqlclient.cpp#L358-L465) |
| Учётки и ограничения | `adduser`, `updateUserInfo`, `changePasswd`, `changePasswd2`, `setiplimit`, `enableiplimit`, `lockuser` | Есть в интерфейсе JDBC старого Java `authd`. IWEB 1.7.6 также вызывает `adduser` и `changePasswd`. |
| Права, санкции и баланс | `addUserPriv`, `delUserPriv`, `addForbid`, `deleteTimeoutForbid`, `remaintime`, `adduserpoint`, `usecash` | Есть в интерфейсе JDBC старого Java `authd`. В нативном 4311 права и пополнения также обслуживаются прямыми запросами к таблицам. |
| Добавление GM | `addGM` | Административная процедура поверх интерфейса Java `authd`. Есть уже в дампах 2013 года. IWEB из Linear 1.5.5 вызывает её в `/usr/local/jakarta/webapps/iweb/index.jsp`. В IWEB 1.7.6 её вызывает `iweb176.jar!/BOOT-INF/classes/mybatis/mapper/UserMapper.xml`. [Дампы 2013 года](https://forum.ragezone.com/threads/perfect-world-1-4-6-register-problem.942614/post-7678418) |
| Удаление GM | `delGM` | Вошла в более поздние дампы. Тело 4311 уже есть в PWAdmin в 2023 году и в PWTools в 2024 году. Одноимённый метод IWEB 1.7.6 выполняет прямой `DELETE FROM auth`. Прямой вызов SQL-процедуры из нативного 4311 не найден. [PWAdmin](https://github.com/shadowvzs/pwAdmin/blob/0f3645119971f9584258fbf33c3973517114fed8/SQL/PW.sql) · [PWTools](https://github.com/hoangnguyent/pwtools/blob/8dd9ba34e02d07ea6d6c814a4ffd1b6a2a570024/pwa.sql) |

По сравнению с 1.4.6 v70 и Linear 1.5.5 у 4311 совпали определения **16 из 19 общих процедур**.

- `recordonline` вставляет запись в `online` до обращения к `FOUND_ROWS()`. `recordoffline` удаляет её до обращения к `ROW_COUNT()`. В обоих случаях осталась работа с `point`. Это изменения тел с прежними сигнатурами.
- `updateUserInfo` получила 13 параметров вместо 15. Из сигнатуры исчезли `email1` и `mobilenumber1`, а `gender1` переименован в `gender`. Тело по-прежнему ссылается на старые имена. Вызов этого варианта не проверялся.

У `acquireuserpasswd` тоже существовали разные тела. В v63 и PWAdmin 2023 результат проходит через `fn_varbintohexsubstring`, а в v70, Linear 1.5.5 и Build 4311 используется прямое чтение. `clearonlinerecords` в 4311 обновляет `point`. В PWAdmin 2023 эта процедура дополнительно очищает `online`. При замене SQL нужно сверять имена, сигнатуры и тела процедур. [Изменения по процедурам](evidence/sql-schema-comparison.json)

## Проверка запуска и вывод для пакета

На изолированной MariaDB 11.8.6 без панели сервер поднял девять служб и карты `gs01` и `is61`. Все 39 таблиц `pw176` были пусты, 20 штатных процедур присутствовали. Фактический `CALL clearonlinerecords` завершился с кодом 0. После удаления процедур только на стенде процессы открыли слушатели, но тот же вызов получил код 1305. При опустошении `licenseservice.users` `gauthd` завершился по `SIGUSR1`. [Протокол и измерения](../experiments/package-layout/clean-start-experiment.ru.md#пустые-таблицы-и-процедуры-сервера)

Для первой версии DEB с бинарниками берём оба штатных дампа Linear целиком. Полный импорт в пустые схемы воспроизводит таблицы, процедуры и начальные строки раздачи. В текущих дампах пользовательских SQL-функций, триггеров и событий нет. Минимум для входа с ролью, пополнений и арены ещё требует проверки игровыми сценариями. [Инициализация MariaDB при первом запуске](package-architecture-proposal.ru.md#инициализация-mariadb)

Схему SQL для 4311 можно использовать как общую основу серверного пакета. Переводы и выбор игровых ресурсов описываются отдельно. Для подключения к существующей базе следует учитывать её версию таблиц и процедур, поскольку ранние выпуски и сторонние панели имеют отличия. [Состав архивных строк и варианты импорта](../experiments/package-layout/clean-start-experiment.ru.md#содержимое-дампов) · [Хранилища и восстановление](storage-and-recovery.ru.md)
