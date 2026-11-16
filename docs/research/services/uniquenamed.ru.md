# uniquenamed — Уникальные имена и идентификаторы

Build 4311. Снимок работающей VM от 2026-11-16.

На TCP 29401 принимаются соединения от `gfactiond` и `gdeliveryd`. Это самостоятельная файловая служба с собственным журналом.

## Запуск и ABI

- Бинарник `/root/pwserver/uniquenamed/uniquenamed`.
- Рабочий каталог `/root/pwserver/uniquenamed`.
- Обозначение сборки ELF `241d16577174fa08302c6eca7f9efe56510d1fb3`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`.
- SHA-256 бинарника VM `895e77176d7dbe003323822dfc797c4c056068ba4753ae815924870e3a1f9320`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 2698 | `./uniquenamed gamesys.conf` | 17 |

## Конфигурация и данные

`gamesys.conf` имеет секции `[storagewdb]` и `[storage]`. Процесс открыл файлы из `dbhome/dbdata` и `dbhome/dblogs`, что соответствует `[storagewdb]`. Контрольный том должен сохранить состояние отдельно от обычных логов.

Сверены `huzeming-176source/cnet/uniquenamed/accessdb.cpp` и `share/storage/storage.h`. Переключение WDB/BDB связано со сборкой. Состояние имён нельзя автоматически считать частью SQL-схемы или базы персонажей.

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 10 0.0.0.0:29401 0.0.0.0:* users:(("uniquenamed",pid=2698,fd=13))
ESTAB 0 0 127.0.0.1:29401 127.0.0.1:39488 users:(("uniquenamed",pid=2698,fd=19))
ESTAB 0 0 127.0.0.1:29401 127.0.0.1:54714 users:(("uniquenamed",pid=2698,fd=5))
ESTAB 0 0 127.0.0.1:32890 127.0.0.1:11101 users:(("uniquenamed",pid=2698,fd=4))
```

### UDP

```text
ESTAB 0 0 127.0.0.1:37364 127.0.0.1:11100 users:(("uniquenamed",pid=2698,fd=17))
```

### UNIX

```text
u_dgr ESTAB 0 0 * 18040 * 3301 users:(("uniquenamed",pid=2698,fd=18))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 2698

- `/root/pwserver/logs/uniquename.log`
- `/root/pwserver/uniquenamed/dbhome/dbdata/config`
- `/root/pwserver/uniquenamed/dbhome/dbdata/logicuid`
- `/root/pwserver/uniquenamed/dbhome/dbdata/uidrole`
- `/root/pwserver/uniquenamed/dbhome/dbdata/unamearenateam`
- `/root/pwserver/uniquenamed/dbhome/dbdata/unamefaction`
- `/root/pwserver/uniquenamed/dbhome/dbdata/unamerole`
- `/root/pwserver/uniquenamed/dbhome/dblogs/log.6afa582e`

## Фактически загруженные библиотеки

### PID 2698

- `/usr/lib/x86_64-linux-gnu/gconv/GBK.so`
- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`

- [Исходные наблюдения](../evidence/runtime.json)
- [Контрольные суммы](../evidence/fingerprints.tsv)
- [Сетевые зависимости](../runtime-contracts.ru.md)
