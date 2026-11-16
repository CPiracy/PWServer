# licenseservice — Лицензирование игровых служб

Build 4311. Снимок работающей VM от 2026-11-16.

Главный скрипт запускает эту службу до авторизации. Служба принимает локальные подключения на TCP 33000. В снятом состоянии устойчивого TCP-сеанса лицензирования не было, поэтому проверка лицензии при запуске остаётся отдельным сценарием.

## Запуск и ABI

- Бинарник `/root/pwserver/licenseservice/licenseservice`.
- Рабочий каталог `/root/pwserver/licenseservice`.
- Обозначение сборки ELF `3b2ff60bce91577a02afe3ea120ceb49e9f52291`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libmariadb.so.3`, `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`.
- SHA-256 бинарника VM `d0bd766311b829a88cb045d9ce6edd89829d9e3d005975822bdaf08bb32c7dce`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 2675 | `./licenseservice gamesys.conf` | 10 |

## Конфигурация и данные

В `gamesys.conf` раздел `[GLicenseServer]` задаёт игровой слушатель. Раздел `[GMysqlClient]` обращается к схеме `licenseservice`. Общий файл клиентов лицензирования лежит по пути `/home/license.conf`.

Из VM видно установленное TCP-соединение с MariaDB. В поставленном бинарнике и SQL-шаблоне найдены обращения к `licenseservice.users` и `licenseservice.logs`. В опубликованных копиях `cnet/licenseservice` часть функций осталась в виде заготовок, поэтому поведение Build 4311 опирается на бинарник и наблюдение.

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 10 127.0.0.1:33000 0.0.0.0:* users:(("licenseservice",pid=2675,fd=4))
ESTAB 0 0 127.0.0.1:54028 127.0.0.1:3306 users:(("licenseservice",pid=2675,fd=5))
```

### UNIX

```text
u_dgr ESTAB 0 0 * 26070 * 3301 users:(("licenseservice",pid=2675,fd=9))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 2675

- `/root/pwserver/logs/licenseservice.log`

## Фактически загруженные библиотеки

### PID 2675

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
