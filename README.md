# frap-llm-helper

Шаблон Python-сервиса 



## Конфигурация

### Базовые переменные (общие для всех контуров)

[`settings/application.yaml`](settings/application.yaml) — дефолты, которые дополняются профилем.



### Песок и другие контуры

[`settings/application-sandbox.yaml`](settings/application-sandbox.yaml) — полный конфиг песка (БД, logging).

Другие профили — [`settings/application-{profile}.yaml`](settings/) (`application-test.yaml`, `application-prod.yaml` и т.д.).
Справочник всех полей: [`settings/config.reference.yaml`](settings/config.reference.yaml).



### Override через environment (тестировщики / стенд)





## Профиль при запуске

Профиль задаётся **при запуске контейнера**

```bash
-e PYTHON_PROFILES_ACTIVE=sandbox
```

CI только собирает образ и триггерит деплой Center-Inform (`DEPLOY_IMAGE_TAG`, `SERVICE_NAME`).
На стенде профиль и override задаёт эксплуатация / тестировщики через **environment** в манифесте деплоя или `docker run`.


## Тестовое приложение (вывод в консоль)

При старте в лог пишется активный конфиг:

- [`app/main.py`](app/main.py) — точка входа, `lifespan` вызывает `log_app_config()`
- [`app/config/app_config.py`](app/config/app_config.py) — загрузка yaml, merge environment, вывод в stdout


Проверка через API:
- [`app/routers/hello_router.py`](app/routers/hello_router.py) — `GET /hello`


## Сборка и локальный запуск в Docker

[`local-deploy.sh`](local-deploy.sh):

```bash
chmod +x local-deploy.sh  
./local-deploy.sh
```

```bash
PYTHON_PROFILES_ACTIVE=test ./local-deploy.sh
```

```bash
docker build -t frap-llm-helper-img .

docker run -d -p 8000:8000 --name frap-llm-helper \
  -e PYTHON_PROFILES_ACTIVE=sandbox \
  frap-llm-helper-img
```


Логи:

```bash
docker logs -f frap-llm-helper
```

## CI/CD

[`.gitlab-ci.yml`](.gitlab-ci.yml):

1. `image_build` — kaniko, push в GitLab Registry
2. `retag_image` — копия в dockerhub.local
3. `deploy:trigger` — триггер pipeline деплоя Center-Inform

Переменные GitLab CI/CD (Settings → CI/CD → Variables):

Профиль (`PYTHON_PROFILES_ACTIVE`) в CI **не задаётся**.
