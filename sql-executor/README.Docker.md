# Docker Setup для database API

## Быстрый старт

### Локально

```bash
# .env.local в корне проекта:
# DB_CONFIG_PG_DASHBOARD=postgresql://user:pass@host.docker.internal:5432/analytics_ai

docker compose -f docker-compose.local.yml up --build
```

API: http://localhost:9010/docs

### Только образ (нужен DSN PostgreSQL)

Без `DB_CONFIG_PG_DASHBOARD` контейнер не запустится.

```bash
docker build -t database .

docker run --rm -p 9010:9010 \
  -e DB_CONFIG_PG_DASHBOARD="postgresql://user:pass@host.docker.internal:5432/analytics_ai" \
  database
```

### Прод: docker-compose.yml

```bash
# GitLab CI/CD Variables → .env на сервере при deploy:
# DB_CONFIG_PG_DASHBOARD , SYSTEM_APPS_TOKEN 
docker compose up -d
docker compose logs -f
```

## Структура файлов

- `Dockerfile` — образ приложения
- `docker-compose.yml` — прод
- `docker-compose.local.yml` — локальный запуск
- `app/config/paths.py` — `.env.local`
- `app/config/db_config.py` — `DB_CONFIG_PG_DASHBOARD`, `postgres_pool`
- `app/config/system_apps_config.py` — `SYSTEM_APPS_TOKEN`, `system_apps_tokens`
- `app/config/logging_config.py` — единый формат логов
- `requirements.txt` — зависимости

## Переменные окружения

```env
DB_CONFIG_PG_DASHBOARD=postgresql://login:password@address:port/analytics_ai
API_ROOT_PATH=/gateway/api/database
# Опционально — GitLab CI/CD Variable SYSTEM_APPS_TOKEN (многострочный, пишется в .env при deploy):
# ===Dashboard===
# eyJhbG...
# ===SQL Agent===
# eyJhbG...
```

### Тестовый JWT (стенд, всегда включён)

1. `GET .../system/bearer-token` — в ответе `system_apps_tokens`: `[{app, token}, ...]` (из env + запасной)
2. В `/docs` на `POST /query/execute` → **Authorize** → вставить любой токен из списка
3. Через gateway: `/gateway/api/database/dev/bearer-token`

Org id в токене: `test-org` (`app/config/dev_auth.py`).

Локально DSN читается из `.env.local` (`paths.py`). В Docker и CI — из environment.

## API

- http://localhost:9010/docs
- POST http://localhost:9010/query/execute

Прод через gateway: `/gateway/api/database/query/execute`

## Troubleshooting

```bash
docker logs database-app
docker compose -f docker-compose.local.yml logs -f
docker exec -it database-app /bin/bash
```
