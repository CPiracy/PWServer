# logservice — Агрегация игровых журналов

Build 4311. Снимок работающей VM от 2026-11-16.

Служба получает TCP и UDP на разных портах. Связь с `gs`, `glinkd`, `uniquenamed` и другими клиентами видна в снимке сокетов. UDP-состояние ESTAB у подключённого датаграммного сокета фиксирует адрес назначения, оно не подтверждает передачу конкретной записи.

## Запуск и ABI

- Бинарник `/root/pwserver/logservice/logservice`.
- Рабочий каталог `/root/pwserver/logservice`.
- Обозначение сборки ELF `d74872dc13413c8d4f6875267f8bd85acd83fd7f`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`.
- SHA-256 бинарника VM `01cb71943424ab392fec1839d6923a88dbfcef11a0c63695a509f3108e2ff002`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 2687 | `./logservice logservice.conf` | 28 |

## Конфигурация и данные

Основной вход — `logservice.conf`. Наблюдаемые выходы приведены по открытым файлам. К ним относятся раздельные серии `world2.*` и статистические файлы под `/root/pwserver/logs`.

Содержательная реализация имеется в `huzeming-176source/cnet/logservice`. Требование запуска этой службы до каждой игровой функции проверкой пока не доказано. Скрипт раздачи запускает её заранее.

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 10 0.0.0.0:11101 0.0.0.0:* users:(("logservice",pid=2687,fd=14))
ESTAB 0 0 127.0.0.1:11101 127.0.0.1:58432 users:(("logservice",pid=2687,fd=26))
ESTAB 0 0 127.0.0.1:11101 127.0.0.1:47922 users:(("logservice",pid=2687,fd=24))
ESTAB 0 0 127.0.0.1:11101 127.0.0.1:32890 users:(("logservice",pid=2687,fd=18))
ESTAB 0 0 127.0.0.1:11101 127.0.0.1:47912 users:(("logservice",pid=2687,fd=23))
ESTAB 0 0 127.0.0.1:11101 127.0.0.1:54312 users:(("logservice",pid=2687,fd=20))
ESTAB 0 0 127.0.0.1:11101 127.0.0.1:44752 users:(("logservice",pid=2687,fd=21))
ESTAB 0 0 127.0.0.1:11101 127.0.0.1:49096 users:(("logservice",pid=2687,fd=25))
```

### UDP

```text
UNCONN 0 0 0.0.0.0:11100 0.0.0.0:* users:(("logservice",pid=2687,fd=22),("logservice",pid=2687,fd=13))
```

### UNIX

```text
u_dgr ESTAB 0 0 * 18542 * 3301 users:(("logservice",pid=2687,fd=19))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 2687

- `/root/pwserver/logs/logservice.log`
- `/root/pwserver/logs/statinfod`
- `/root/pwserver/logs/statinfoh`
- `/root/pwserver/logs/statinfom`
- `/root/pwserver/logs/world2.cash`
- `/root/pwserver/logs/world2.chat`
- `/root/pwserver/logs/world2.err`
- `/root/pwserver/logs/world2.formatlog`
- `/root/pwserver/logs/world2.log`
- `/root/pwserver/logs/world2.trace`

## Фактически загруженные библиотеки

### PID 2687

- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`

- [Исходные наблюдения](../evidence/runtime.json)
- [Контрольные суммы](../evidence/fingerprints.tsv)
- [Сетевые зависимости](../runtime-contracts.ru.md)
