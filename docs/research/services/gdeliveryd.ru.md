# gdeliveryd — Координация шлюза, авторизации и карт

Build 4311. Снимок работающей VM от 2026-11-16.

Слушает TCP 29100 для игрового шлюза и 29300 для карт. Установлены прямые соединения к авторизации, базе персонажей, реестру имён, гильдиям и античиту. Это подтверждённый набор текущих связей, обязательность каждой требует отдельного опыта отключения.

## Запуск и ABI

- Бинарник `/root/pwserver/gdeliveryd/gdeliveryd`.
- Рабочий каталог `/root/pwserver/gdeliveryd`.
- Обозначение сборки ELF `80f724a52d7571801e05fcbf4c33b29337a48615`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libpcre.so.3`, `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`.
- SHA-256 бинарника VM `a3ce70f5ca56753063807ed9ff95bd75edeb5216cd71c194c152c96d8d23ab5c`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 2765 | `./gdeliveryd gamesys.conf` | 35 |

## Конфигурация и данные

В `gamesys.conf` перечислены клиентские секции этих служб. Каталог содержит `domain*.data`, `domain*.sev`, `auctionid.txt`, `sysauctionlist.txt`, `webtradeid.txt`, `filters` и `script.lua`. Точные имена входных файлов представлены в пофайловом инвентаре.

Точный исходный модуль `cnet/gdeliveryd` отсутствует в проверенных копиях 1.7.6. Соседние ветки позволяют проследить гипотезы регистрации маршрутов, подробности приведены в исследовании карт.

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 4096 0.0.0.0:29300 0.0.0.0:* users:(("gdeliveryd",pid=2765,fd=10))
LISTEN 0 10 0.0.0.0:29100 0.0.0.0:* users:(("gdeliveryd",pid=2765,fd=8))
CLOSE-WAIT 1 0 127.0.0.1:42546 127.0.0.1:33000 users:(("gdeliveryd",pid=2765,fd=4))
ESTAB 0 0 127.0.0.1:39488 127.0.0.1:29401 users:(("gdeliveryd",pid=2765,fd=7))
ESTAB 0 0 127.0.0.1:37020 127.0.0.1:29400 users:(("gdeliveryd",pid=2765,fd=11))
ESTAB 0 0 127.0.0.1:49830 127.0.0.1:29200 users:(("gdeliveryd",pid=2765,fd=14))
ESTAB 0 0 127.0.0.1:35100 127.0.0.1:29702 users:(("gdeliveryd",pid=2765,fd=9))
ESTAB 0 0 127.0.0.1:29300 127.0.0.1:58414 users:(("gdeliveryd",pid=2765,fd=17))
ESTAB 0 0 127.0.0.1:29300 127.0.0.1:60546 users:(("gdeliveryd",pid=2765,fd=18))
ESTAB 0 0 127.0.0.1:29100 127.0.0.1:45056 users:(("gdeliveryd",pid=2765,fd=13))
ESTAB 0 0 127.0.0.1:48318 127.0.0.1:29500 users:(("gdeliveryd",pid=2765,fd=12))
ESTAB 0 0 127.0.0.1:47912 127.0.0.1:11101 users:(("gdeliveryd",pid=2765,fd=6))
```

### UDP

```text
ESTAB 0 0 127.0.0.1:48593 127.0.0.1:11100 users:(("gdeliveryd",pid=2765,fd=16))
```

### UNIX

```text
u_dgr ESTAB 0 0 * 18166 * 3301 users:(("gdeliveryd",pid=2765,fd=5))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 2765

- `/root/pwserver/logs/gdeliveryd.log`

## Фактически загруженные библиотеки

### PID 2765

- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libpcre.so.3.13.3`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`

- [Исходные наблюдения](../evidence/runtime.json)
- [Контрольные суммы](../evidence/fingerprints.tsv)
- [Сетевые зависимости](../runtime-contracts.ru.md)
