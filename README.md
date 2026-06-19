# frap-llm-helper

Шаблон Python-сервиса 



## Конфигурация

### Базовые переменные (общие для всех контуров)

[`settings/application.yaml`](settings/application.yaml) — дефолты, которые дополняются профилем.



### Песок и другие контуры

[`settings/contours/sandbox.yaml`](settings/contours/sandbox.yaml) — полный конфиг песка (БД, logging).

Другие профили — файлы в [`settings/contours/`](settings/contours/) (`test.yaml`, `prod.yaml` и т.д.).
Справочник всех полей: [`settings/config.reference.yaml`](settings/config.reference.yaml).



### Override на сервере

Папка [`settings/server/`](settings/server/) на сервере монтируется в образ`/app/settings/server`. Файл `{profile}.yaml` (profile берется из переменной задаваемой при запуске контейнера : `APP_PROFILE`) — yaml со свойствами на сервере: перезаписывает и дополняет конфиг профиля из образа без пересборки. Пример: `settings/server/sandbox.yaml`.






## Профиль при запуске

Профиль задаётся **при запуске контейнера**

```bash
-e APP_PROFILE=sandbox
```

CI только собирает образ и триггерит деплой Center-Inform (`DEPLOY_IMAGE_TAG`, `SERVICE_NAME`).
На стенде профиль и override задаёт команда эксплуатации / тестировщики при `docker run` или в манифесте деплоя.


## Тестовое приложение (вывод в консоль)

При старте в лог пишется активный конфиг:

- [`app/main.py`](app/main.py) — точка входа, `lifespan` вызывает `log_app_config()`
- [`app/config/app_config.py`](app/config/app_config.py) — загрузка yaml и вывод в stdout


Проверка через API:
- [`app/routers/hello_router.py`](app/routers/hello_router.py) — `GET /hello`


## Сборка и локальный запуск в Docker

Два скрипта с одинаковой логикой — выбирай под свою ОС:

| ОС | Скрипт |
|----|--------|
| Windows | [`local-deploy.ps1`](local-deploy.ps1) |
| Linux / macOS / Git Bash | [`local-deploy.sh`](local-deploy.sh) |

**Windows (PowerShell):**

```powershell
.\local-deploy.ps1
```

```powershell
$env:APP_PROFILE = "test"
.\local-deploy.ps1
```

**Linux / macOS / Git Bash:**

```bash
chmod +x local-deploy.sh   # один раз
./local-deploy.sh
```

```bash
APP_PROFILE=test ./local-deploy.sh
```

Оба скрипта:
- собирают образ `frap-llm-helper-img`
- запускают контейнер `frap-llm-helper-app` на порту `8000`
- передают `-e APP_PROFILE=...` (по умолчанию `sandbox`)
- монтируют `settings/server` — yaml с сервера перезаписывает и дополняет конфиг профиля из образа (см. выше)

Или вручную:

```bash
docker build -t frap-llm-helper-img .

docker run -d -p 8000:8000 --name frap-llm-helper-app \
  -e APP_PROFILE=sandbox \
  -v ./settings/server:/app/settings/server:ro \
  frap-llm-helper-img
```


Логи:

```bash
docker logs -f frap-llm-helper-app
```

## CI/CD

[`.gitlab-ci.yml`](.gitlab-ci.yml):

1. `image_build` — kaniko, push в GitLab Registry
2. `retag_image` — копия в dockerhub.local
3. `deploy:trigger` — триггер pipeline деплоя Center-Inform

Переменные GitLab CI/CD (Settings → CI/CD → Variables):

| Variable | Назначение |
|----------|------------|
| `DEPLOY_TOKEN` | токен trigger pipeline деплоя |
| `DEPLOY_PROJECT_ID` | id проекта деплоя в GitLab |
| `CI_TEST_PASSWORD` | для dockerhub.local (retag) |

Профиль (`APP_PROFILE`) в CI **не задаётся**.
