# gamedbd — Персонажи и другое файловое состояние игры

Build 4311. Снимок работающей VM от 2026-11-16.

TCP 29400 принимает соединения от `gdeliveryd`, `gfactiond` и обоих `gs`. Снимок показывает прямое открытие файлов и журнала WDB из каталога этой службы.

## Запуск и ABI

- Бинарник `/root/pwserver/gamedbd/gamedbd`.
- Рабочий каталог `/root/pwserver/gamedbd`.
- Обозначение сборки ELF `3fc8a6328344ff77d6c2cf25d9a72f0741975e22`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`.
- SHA-256 бинарника VM `46e091b1c817132f3a99b1b55c7dcd1dd4ad1bb0102de0b77b25654f32040661`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 2724 | `./gamedbd gamesys.conf` | 34 |

## Конфигурация и данные

В `gamesys.conf` присутствуют две конфигурации хранилища. Открытые пути соответствуют `[storagewdb]`. `base_util`, `dbtool` и `dbanlz` лежат рядом как отдельные утилиты. Команды анализа и ремонта следует проверять на копии базы, поскольку часть из них выполняет recovery или перезапись.

Исходный каталог `cnet/gamedbd` отсутствует в двух скачанных деревьях 1.7.6. Доступное дерево 1.7.2 полезно для понимания интерфейса, при этом итоговые выводы о Build 4311 привязаны к порту, конфигу и открытым файлам VM.

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 10 0.0.0.0:29400 0.0.0.0:* users:(("gamedbd",pid=2724,fd=67))
ESTAB 0 0 127.0.0.1:29400 127.0.0.1:51102 users:(("gamedbd",pid=2724,fd=6))
ESTAB 0 0 127.0.0.1:29400 127.0.0.1:42814 users:(("gamedbd",pid=2724,fd=73))
ESTAB 0 0 127.0.0.1:29400 127.0.0.1:36342 users:(("gamedbd",pid=2724,fd=74))
ESTAB 0 0 127.0.0.1:29400 127.0.0.1:37020 users:(("gamedbd",pid=2724,fd=72))
CLOSE-WAIT 1 0 127.0.0.1:51596 127.0.0.1:33000 users:(("gamedbd",pid=2724,fd=4))
ESTAB 0 0 127.0.0.1:54312 127.0.0.1:11101 users:(("gamedbd",pid=2724,fd=5))
```

### UDP

```text
ESTAB 0 0 127.0.0.1:46879 127.0.0.1:11100 users:(("gamedbd",pid=2724,fd=71))
```

### UNIX

```text
u_dgr ESTAB 0 0 * 18577 * 3301 users:(("gamedbd",pid=2724,fd=66))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 2724

- `/root/pwserver/gamedbd/dbhome/dbdata/arenaplayer`
- `/root/pwserver/gamedbd/dbhome/dbdata/arenateam`
- `/root/pwserver/gamedbd/dbhome/dbdata/auction`
- `/root/pwserver/gamedbd/dbhome/dbdata/base`
- `/root/pwserver/gamedbd/dbhome/dbdata/city`
- `/root/pwserver/gamedbd/dbhome/dbdata/clsconfig`
- `/root/pwserver/gamedbd/dbhome/dbdata/config`
- `/root/pwserver/gamedbd/dbhome/dbdata/crslogicuid`
- `/root/pwserver/gamedbd/dbhome/dbdata/equipment`
- `/root/pwserver/gamedbd/dbhome/dbdata/factionfortress`
- `/root/pwserver/gamedbd/dbhome/dbdata/factioninfo`
- `/root/pwserver/gamedbd/dbhome/dbdata/factionname`
- `/root/pwserver/gamedbd/dbhome/dbdata/factionrelation`
- `/root/pwserver/gamedbd/dbhome/dbdata/force`
- `/root/pwserver/gamedbd/dbhome/dbdata/foundryformulas`
- `/root/pwserver/gamedbd/dbhome/dbdata/friendext`
- `/root/pwserver/gamedbd/dbhome/dbdata/friends`
- `/root/pwserver/gamedbd/dbhome/dbdata/globalcontrol`
- `/root/pwserver/gamedbd/dbhome/dbdata/gtask`
- `/root/pwserver/gamedbd/dbhome/dbdata/home`
- `/root/pwserver/gamedbd/dbhome/dbdata/inventory`
- `/root/pwserver/gamedbd/dbhome/dbdata/kingelection`
- `/root/pwserver/gamedbd/dbhome/dbdata/luaother`
- `/root/pwserver/gamedbd/dbhome/dbdata/luarole`
- `/root/pwserver/gamedbd/dbhome/dbdata/luatag`
- `/root/pwserver/gamedbd/dbhome/dbdata/luauser`
- `/root/pwserver/gamedbd/dbhome/dbdata/mailbox`
- `/root/pwserver/gamedbd/dbhome/dbdata/mappassword`
- `/root/pwserver/gamedbd/dbhome/dbdata/messages`
- `/root/pwserver/gamedbd/dbhome/dbdata/mndomainbonus`
- `/root/pwserver/gamedbd/dbhome/dbdata/mndomaininfo`
- `/root/pwserver/gamedbd/dbhome/dbdata/mnfactionapplyinfo`
- `/root/pwserver/gamedbd/dbhome/dbdata/mnfactioninfo`
- `/root/pwserver/gamedbd/dbhome/dbdata/newroleinfo`
- `/root/pwserver/gamedbd/dbhome/dbdata/newtrashbox`
- `/root/pwserver/gamedbd/dbhome/dbdata/order`
- `/root/pwserver/gamedbd/dbhome/dbdata/playerprofile`
- `/root/pwserver/gamedbd/dbhome/dbdata/playershop`
- `/root/pwserver/gamedbd/dbhome/dbdata/recalluser`
- `/root/pwserver/gamedbd/dbhome/dbdata/rolename`
- `/root/pwserver/gamedbd/dbhome/dbdata/rolenamehis`
- `/root/pwserver/gamedbd/dbhome/dbdata/sellpoint`
- `/root/pwserver/gamedbd/dbhome/dbdata/serverdata`
- `/root/pwserver/gamedbd/dbhome/dbdata/shoplog`
- `/root/pwserver/gamedbd/dbhome/dbdata/solochallengerank`
- `/root/pwserver/gamedbd/dbhome/dbdata/status`
- `/root/pwserver/gamedbd/dbhome/dbdata/storehouse`
- `/root/pwserver/gamedbd/dbhome/dbdata/syslog`
- `/root/pwserver/gamedbd/dbhome/dbdata/task`
- `/root/pwserver/gamedbd/dbhome/dbdata/translog`
- `/root/pwserver/gamedbd/dbhome/dbdata/uniquedata`
- `/root/pwserver/gamedbd/dbhome/dbdata/user`
- `/root/pwserver/gamedbd/dbhome/dbdata/userfaction`
- `/root/pwserver/gamedbd/dbhome/dbdata/userstore`
- `/root/pwserver/gamedbd/dbhome/dbdata/waitdel`
- `/root/pwserver/gamedbd/dbhome/dbdata/weborderitem`
- `/root/pwserver/gamedbd/dbhome/dbdata/webtrade`
- `/root/pwserver/gamedbd/dbhome/dbdata/webtradesold`
- `/root/pwserver/gamedbd/dbhome/dblogs/log.6afa7b05`
- `/root/pwserver/logs/gamedbd.log`

## Фактически загруженные библиотеки

### PID 2724

- `/usr/lib/x86_64-linux-gnu/gconv/GBK.so`
- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`

- [Исходные наблюдения](../evidence/runtime.json)
- [Контрольные суммы](../evidence/fingerprints.tsv)
- [Сетевые зависимости](../runtime-contracts.ru.md)
