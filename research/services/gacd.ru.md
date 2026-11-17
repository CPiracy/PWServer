# gacd — Серверная служба античита

Build 4311. Снимок работающей VM от 2026-11-16.

Работают два TCP-слушателя. На 29702 видно живое соединение от `gdeliveryd`. На 29712 подтверждён слушатель, игровая нагрузка на этот порт без клиента не проверялась.

## Запуск и ABI

- Бинарник `/root/pwserver/gacd/gacd`.
- Рабочий каталог `/root/pwserver/gacd`.
- Обозначение сборки ELF `d7d95a41a9418fc0265be6713833f97c270acc2e`.
- ELF64 с загрузчиком `/lib64/ld-linux-x86-64.so.2` и прямыми импортами `libxml2.so.2`, `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.1`, `libc.so.6`.
- Максимальные версии символов в ELF `GLIBC_2.34`, `GLIBCXX_3.4.29`.
- SHA-256 бинарника VM `40f8d38e6b658117e5ee02e9272b83c15af0c360345783acab7fb11b585a06e5`.

| PID | Аргументы | RSS, МиБ |
|---:|---|---:|
| 2752 | `./gacd gamesys.conf` | 16 |

## Конфигурация и данные

В каталоге есть `gamesys.conf`, `gacd.xml` и файлы `charfont.dat`, `charlib.dat`, `hzfont.dat`. Конфиг XML и ресурсы входят в комплект, снимок открытых файлов сделан после загрузки и не показывает все чтения при старте.

Код службы есть в `huzeming-176source/cnet/gacd`. Роль соединения и имена параметров проверяются штатной конфигурацией. Настройки античита в стенде сохранены в поставляемом режиме.

[Пофайловый инвентарь](../evidence/inventory.tsv) · [Поля загруженных конфигов](../evidence/config-keys.tsv)

## Сокеты в момент проверки

Состояние и направления проверялись через `ss`. Эфемерные порты и PID относятся к этому снимку.

### TCP

```text
LISTEN 0 10 0.0.0.0:29712 0.0.0.0:* users:(("gacd",pid=2752,fd=5))
LISTEN 0 10 0.0.0.0:29702 0.0.0.0:* users:(("gacd",pid=2752,fd=4))
ESTAB 0 0 127.0.0.1:29702 127.0.0.1:35100 users:(("gacd",pid=2752,fd=7))
```

### UNIX

```text
u_dgr ESTAB 0 0 * 26077 * 3301 users:(("gacd",pid=2752,fd=8))
```

## Открытые пути

Список путей в игровом дереве, `/tmp` и `/run` снят с файловых дескрипторов. Он показывает состояние после загрузки.

### PID 2752

- `/root/pwserver/logs/gacd.log`

## Фактически загруженные библиотеки

### PID 2752

- `/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2`
- `/usr/lib/x86_64-linux-gnu/libc.so.6`
- `/usr/lib/x86_64-linux-gnu/libgcc_s.so.1`
- `/usr/lib/x86_64-linux-gnu/liblzma.so.5.8.1`
- `/usr/lib/x86_64-linux-gnu/libm.so.6`
- `/usr/lib/x86_64-linux-gnu/libstdc++.so.6.0.33`
- `/usr/lib/x86_64-linux-gnu/libxml2.so.2.9.14`
- `/usr/lib/x86_64-linux-gnu/libz.so.1.3.1`

- [Исходные наблюдения](../evidence/runtime.json)
- [Контрольные суммы](../evidence/fingerprints.tsv)
- [Сетевые зависимости](../runtime-contracts.ru.md)
