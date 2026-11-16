# gs — Мир и серверы экземпляров карт

Build 4311. Снимок работающей VM от 2026-11-16.

Два процесса одного бинарника обслуживают `gs01` и `is61`. Они поддерживают собственные TCP-слушатели и установленные UNIX-соединения через `/tmp/gssock_world1` и `/tmp/gssock_is61`. Каждый соединён с `gdeliveryd`, шлюзом, гильдиями и базой персонажей.

## Запуск и ABI

- Бинарник `/root/pwserver/gamed/gs`.
- Рабочий каталог `/root/pwserver/gamed`.
- Обозначение сборки ELF `d4b1e56a7170f23509bfbbfb83cd09d403078d65`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libpcre.so.3`, `libcrypto.so.3`, `libstdc++.so.6`, `libmariadb.so.3`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`, `OPENSSL_3.0.0`.
- SHA-256 бинарника VM `6a1886831f16c3f1f9a4ea3bff3b9bd422bf3938306f1946894776050d019b60`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 3190 | `./gs gs01 gs.conf gmserver.conf gsalias.conf` | 2060 |
| 3193 | `./gs is61 gs.conf gmserver.conf gsalias.conf` | 1215 |

## Конфигурация и данные

Командные входы — идентификатор карты, `gs.conf`, `gmserver.conf` и `gsalias.conf`. В `gamed/config` лежат данные карты, NPC, целей, заданий, коллизий и другие ресурсы. Все пути перечислены построчно в инвентаре. В снимке процессов рядом поставляемые `libskill.so` и `libtask.so` не видны как загруженные динамические библиотеки.

В `huzeming-176source/cgame/gs/start.cpp` и `worldmanager.cpp` обнаружены объявление маршрута, разбор алиасов и выход на другую карту. Динамические копии внутри процесса следует отличать от запуска отдельного `gs`. Подробная проверка в [исследовании карт](../maps.ru.md).

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 10 127.0.0.1:10901 0.0.0.0:* users:(("gs",pid=3190,fd=7))
LISTEN 0 10 0.0.0.0:11971 0.0.0.0:* users:(("gs",pid=3193,fd=8))
ESTAB 0 0 127.0.0.1:45222 127.0.0.1:29600 users:(("gs",pid=3193,fd=14))
ESTAB 0 0 127.0.0.1:37882 127.0.0.1:29600 users:(("gs",pid=3190,fd=13))
ESTAB 0 0 127.0.0.1:60546 127.0.0.1:29300 users:(("gs",pid=3190,fd=14))
ESTAB 0 0 127.0.0.1:49096 127.0.0.1:11101 users:(("gs",pid=3193,fd=18))
ESTAB 0 0 127.0.0.1:58414 127.0.0.1:29300 users:(("gs",pid=3193,fd=15))
ESTAB 0 0 127.0.0.1:58432 127.0.0.1:11101 users:(("gs",pid=3190,fd=17))
ESTAB 0 0 127.0.0.1:60780 127.0.0.1:29301 users:(("gs",pid=3193,fd=13))
ESTAB 0 0 127.0.0.1:42814 127.0.0.1:29400 users:(("gs",pid=3193,fd=16))
ESTAB 0 0 127.0.0.1:42278 127.0.0.1:29301 users:(("gs",pid=3190,fd=12))
ESTAB 0 0 127.0.0.1:36342 127.0.0.1:29400 users:(("gs",pid=3190,fd=15))
```

### UDP

```text
ESTAB 0 0 127.0.0.1:38240 127.0.0.1:11100 users:(("gs",pid=3193,fd=17))
ESTAB 0 0 127.0.0.1:47630 127.0.0.1:11100 users:(("gs",pid=3190,fd=16))
```

### UNIX

```text
u_str ESTAB 0 0 /tmp/gssock_world1 19423 * 20360 users:(("gs",pid=3190,fd=18))
u_str ESTAB 0 0 * 20360 * 19423 users:(("gs",pid=3193,fd=20))
u_str LISTEN 0 10 /tmp/gssock_is61 20143 * 0 users:(("gs",pid=3193,fd=9))
u_str LISTEN 0 10 /tmp/gssock_world1 19167 * 0 users:(("gs",pid=3190,fd=8))
u_str ESTAB 0 0 * 19252 * 20306 users:(("gs",pid=3190,fd=79))
u_str ESTAB 0 0 /tmp/gssock_is61 20306 * 19252 users:(("gs",pid=3193,fd=19))
u_dgr ESTAB 0 0 * 19080 * 3301 users:(("gs",pid=3193,fd=4),("gs",pid=3190,fd=4))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 3190 · gs01

- `/root/pwserver/logs/gs01-16-11-26-03-00.log`

### PID 3193 · is61

- `/root/pwserver/logs/gs01-16-11-26-03-00.log`

## Фактически загруженные библиотеки

### PID 3190 · gs01

- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libcrypto.so.3`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libmariadb.so.3`
- `/usr/lib/x86_64-linux-gnu/libpcre.so.3.13.3`
- `/usr/lib/x86_64-linux-gnu/libssl.so.3`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`
- `/usr/lib/x86_64-linux-gnu/libz.so.1.3.1`
- `/usr/lib/x86_64-linux-gnu/libzstd.so.1.5.7`

### PID 3193 · is61

- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libcrypto.so.3`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libmariadb.so.3`
- `/usr/lib/x86_64-linux-gnu/libpcre.so.3.13.3`
- `/usr/lib/x86_64-linux-gnu/libssl.so.3`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`
- `/usr/lib/x86_64-linux-gnu/libz.so.1.3.1`
- `/usr/lib/x86_64-linux-gnu/libzstd.so.1.5.7`

- [Исходные наблюдения](../evidence/runtime.json)
- [Контрольные суммы](../evidence/fingerprints.tsv)
- [Сетевые зависимости](../runtime-contracts.ru.md)
