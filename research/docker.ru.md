# Docker для Perfect World

Исследовательская схема для обсуждения и проверки будущего образа. Игровой контейнер устанавливает те же DEB, что и сервер на хосте. Внутри systemd управляет игровыми службами и картами. MariaDB работает отдельным сервисом, панели размещаются отдельно от игрового контура. [Границы контейнеров](deployment-boundaries.ru.md) · [Состав пакетов](package-architecture-proposal.ru.md#слои-пакетов)

Игровые службы используют Unix-сокеты для проверенных внутренних соединений. Для записи состояния и пользовательских переопределений контейнер получает отдельные тома или bind mounts для `/opt/pwserver/database` и `/opt/pwserver/overlay`. В `database` сохраняются обе WDB вместе с их журналами. Этап инициализации MariaDB открыт. [Раскладка файлов](package-architecture-proposal.ru.md#размещение-файлов-пакетов) · [Хранилища](storage-and-recovery.ru.md)

## Запуск и остановка контейнера

Для загруженных карт выбрана политика `Restart=always`. Пока карта должна работать, systemd перезапускает её процесс и после аварии, и после самостоятельного завершения с кодом 0. Оператор, собственная панель и `lazy-maps` останавливают карту через операцию `stop` юнита. После неё карта ждёт нового запроса запуска. Решение о том, какие карты должны быть загружены, принимает управляющий слой. [Политика перезапуска systemd](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#Restart=)

В контейнерном профиле точка входа передаёт PID 1 systemd. Для Debian-образа с `/sbin/init`, указывающим на systemd, предлагается такой фрагмент Dockerfile.

```dockerfile
ENTRYPOINT ["/sbin/init"]
STOPSIGNAL SIGRTMIN+3
```

Если для подготовки окружения понадобится входной скрипт, он передаст PID 1 systemd через `exec /sbin/init`. При старте systemd поднимает игровой target, условно `pwserver.target`, включённый через `WantedBy=multi-user.target` в контейнерном профиле. Через `Wants=` target подтягивает базовые службы и стартовые карты. У игровых юнитов, включая карты по запросу и `lazy-maps` при его установке, `PartOf=pwserver.target` распространяет явную остановку target на эти юниты. Порядок запуска задаётся `After=`. При совместной остановке зависимые юниты завершаются в обратном порядке. [Управление зависимостями юнитов](https://man7.org/linux/man-pages/man5/systemd.unit.5.html)

При `docker stop` или `docker compose stop` Docker посылает `SIGRTMIN+3` процессу systemd. Systemd переходит в `halt.target`, завершает игровые юниты и выходит. `systemctl stop pwserver.target` внутри контейнера выполняет остановку только игрового набора и оставляет сам контейнер в работе. [Остановка systemd в контейнере](https://systemd.io/CONTAINER_INTERFACE/) · [Сигнал Docker](https://docs.docker.com/reference/cli/docker/container/stop/)

Для штатного выключения карты systemd должен использовать подтверждённую операцию игрового завершения и дождаться выхода процесса. Службы, нужные для сохранения персонажей, работают до завершения карт. `gamedbd` и `uniquenamed` закрывают WDB после сохранений. При совместной остановке Compose зависимость игрового контейнера от MariaDB удерживает БД до выхода игрового контейнера. [Завершение карт](maps.ru.md#что-считать-занятостью-и-как-завершать-работу) · [Закрытие WDB](server-configuration.ru.md#перечитывание-и-штатное-завершение) · [Порядок Docker Compose](https://docs.docker.com/compose/how-tos/startup-order/)

`TimeoutStopSec` задаёт бюджет юнита, а `stop_grace_period` — бюджет всей остановки контейнера. В доступных исходниках штатное завершение GS включает ожидание 15 секунд. Время остановки всего 4311, сохранение на занятой карте и работу systemd как PID 1 в итоговом образе ещё предстоит проверить. По этому прогону подбирается `stop_grace_period` с запасом на завершение карт и обеих WDB. После истечения этого времени Docker отправит `SIGKILL`. [Таймауты systemd](https://www.freedesktop.org/software/systemd/man/latest/systemd.service.html#TimeoutStopSec=) · [Таймаут Compose](https://docs.docker.com/reference/compose-file/services/#stop_grace_period)

### Готовность игрового сервера

В контейнерном профиле предусмотрен `healthcheck`. Он должен проверять готовность основных служб и регистрацию в `gdeliveryd` тех карт, которые сейчас должны быть загружены. Выгруженные по решению `lazy-maps` карты исключаются из проверки. Compose может дождаться результата `healthy` для зависимых контейнеров через `condition: service_healthy`. Перезапуском игровых юнитов управляет systemd. [Проверка Docker](https://docs.docker.com/reference/dockerfile/#healthcheck) · [Ожидание готовности в Compose](https://docs.docker.com/compose/how-tos/startup-order/)
