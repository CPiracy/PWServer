# gauthd — Авторизация и игровые права

Build 4311. Снимок работающей VM от 2026-11-16.

TCP 29200 обслуживает `gdeliveryd`. В рабочей VM также установлено SQL-соединение с MariaDB на 3306. Адрес GameDB из конфигурации фиксируется отдельно от живых соединений.

## Запуск и ABI

- Бинарник `/root/pwserver/gauthd/gauthd`.
- Рабочий каталог `/root/pwserver/gauthd`.
- Обозначение сборки ELF `397cec51958e9ef56f57458ef3b38c58b8633f5d`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libmariadb.so.3`, `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`.
- SHA-256 бинарника VM `573c0198dee480b892413df0a9c9fa9b5c57900f59b0f0e4da89a18668e015bd`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 2710 | `./gauthd gamesys.conf` | 10 |

## Конфигурация и данные

`gamesys.conf` содержит `[GMysqlClient]` со схемой `pw176`. Рядом лежит `script.lua`. При старте исходники читают `/home/license.conf`, поэтому проверка нового процесса требует действующей штатной службы лицензирования.

В `huzeming-176source/cnet/gauthd/gmysqlclient.cpp` задокументированы `acquireuserpasswd`, `users` и `auth` с ключом пользователя и зоны. Вход игрока и применение прав не испытывались при текущем ограничении на клиент.

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 10 127.0.0.1:29200 0.0.0.0:* users:(("gauthd",pid=2710,fd=5))
ESTAB 0 0 127.0.0.1:49600 127.0.0.1:3306 users:(("gauthd",pid=2710,fd=6))
CLOSE-WAIT 1 0 127.0.0.1:51584 127.0.0.1:33000 users:(("gauthd",pid=2710,fd=4))
ESTAB 0 0 127.0.0.1:29200 127.0.0.1:49830 users:(("gauthd",pid=2710,fd=10))
```

### UNIX

```text
u_dgr ESTAB 0 0 * 26072 * 3301 users:(("gauthd",pid=2710,fd=11))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 2710

- `/root/pwserver/logs/gauthd.log`

## Фактически загруженные библиотеки

### PID 2710

- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libcrypto.so.3`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libmariadb.so.3`
- `/usr/lib/x86_64-linux-gnu/libssl.so.3`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`
- `/usr/lib/x86_64-linux-gnu/libz.so.1.3.1`
- `/usr/lib/x86_64-linux-gnu/libzstd.so.1.5.7`

- [Исходные наблюдения](../evidence/runtime.json)
- [Контрольные суммы](../evidence/fingerprints.tsv)
- [Сетевые зависимости](../runtime-contracts.ru.md)
