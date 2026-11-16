# gfactiond — Гильдии и связи со смежными службами

Build 4311. Снимок работающей VM от 2026-11-16.

Контур гильдий слушает TCP 29500 и 29600. В нём видны соединения с `glinkd`, `gdeliveryd` и картами. Исходящие соединения идут к `gamedbd` на 29400 и к `uniquenamed` на 29401.

## Запуск и ABI

- Бинарник `/root/pwserver/gfactiond/gfactiond`.
- Рабочий каталог `/root/pwserver/gfactiond`.
- Обозначение сборки ELF `b1aa44f66e6e93ee80078db12a8f4f6b2103833c`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libpcre.so.3`, `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`.
- SHA-256 бинарника VM `11a6f78e2b66717437ea202b1434750c6d8eeb580eff8cddf48a677d1a6daa3e`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 2758 | `./gfactiond gamesys.conf` | 21 |

## Конфигурация и данные

Исполняемый файл использует `gamesys.conf`. Дополнительные файлы каталога включают `filters` и `script.lua`. Состояние гильдий встречается в именах таблиц файлового хранилища `gamedbd`.

В двух деревьях 1.7.6 исходники гильдий лежат в `cnet/gfaction`, а установленный процесс называется `gfactiond`. Исходники содержат чтение `/home/license.conf`. Изменения гильдий не выполнялись.

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 10 0.0.0.0:29500 0.0.0.0:* users:(("gfactiond",pid=2758,fd=7))
LISTEN 0 4096 0.0.0.0:29600 0.0.0.0:* users:(("gfactiond",pid=2758,fd=8))
ESTAB 0 0 127.0.0.1:29500 127.0.0.1:48322 users:(("gfactiond",pid=2758,fd=13))
CLOSE-WAIT 1 0 127.0.0.1:57444 127.0.0.1:33000 users:(("gfactiond",pid=2758,fd=4))
ESTAB 0 0 127.0.0.1:54714 127.0.0.1:29401 users:(("gfactiond",pid=2758,fd=5))
ESTAB 0 0 127.0.0.1:51102 127.0.0.1:29400 users:(("gfactiond",pid=2758,fd=12))
ESTAB 0 0 127.0.0.1:29600 127.0.0.1:45222 users:(("gfactiond",pid=2758,fd=14))
ESTAB 0 0 127.0.0.1:29600 127.0.0.1:37882 users:(("gfactiond",pid=2758,fd=15))
ESTAB 0 0 127.0.0.1:44752 127.0.0.1:11101 users:(("gfactiond",pid=2758,fd=9))
ESTAB 0 0 127.0.0.1:29500 127.0.0.1:48318 users:(("gfactiond",pid=2758,fd=10))
```

### UDP

```text
ESTAB 0 0 127.0.0.1:52171 127.0.0.1:11100 users:(("gfactiond",pid=2758,fd=6))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 2758

- `/root/pwserver/logs/gfactiond.log`

## Фактически загруженные библиотеки

### PID 2758

- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libpcre.so.3.13.3`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`

- [Исходные наблюдения](../evidence/runtime.json)
- [Контрольные суммы](../evidence/fingerprints.tsv)
- [Сетевые зависимости](../runtime-contracts.ru.md)
