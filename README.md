# frap-llm-helper

РЁР°Р±Р»РѕРЅ Python-СЃРµСЂРІРёСЃР° 



## РљРѕРЅС„РёРіСѓСЂР°С†РёСЏ

### Р‘Р°Р·РѕРІС‹Рµ РїРµСЂРµРјРµРЅРЅС‹Рµ (РѕР±С‰РёРµ РґР»СЏ РІСЃРµС… РєРѕРЅС‚СѓСЂРѕРІ)

[`settings/application.yaml`](settings/application.yaml) вЂ” РґРµС„РѕР»С‚С‹, РєРѕС‚РѕСЂС‹Рµ РґРѕРїРѕР»РЅСЏСЋС‚СЃСЏ РїСЂРѕС„РёР»РµРј.



### РџРµСЃРѕРє Рё РґСЂСѓРіРёРµ РєРѕРЅС‚СѓСЂС‹

[`settings/application-sandbox.yaml`](settings/application-sandbox.yaml) вЂ” РїРѕР»РЅС‹Р№ РєРѕРЅС„РёРі РїРµСЃРєР° (Р‘Р”, logging).

Р”СЂСѓРіРёРµ РїСЂРѕС„РёР»Рё вЂ” [`settings/application-{profile}.yaml`](settings/) (`application-test.yaml`, `application-prod.yaml` Рё С‚.Рґ.).
РЎРїСЂР°РІРѕС‡РЅРёРє РІСЃРµС… РїРѕР»РµР№: [`settings/config.reference.yaml`](settings/config.reference.yaml).



### Override С‡РµСЂРµР· environment (С‚РµСЃС‚РёСЂРѕРІС‰РёРєРё / СЃС‚РµРЅРґ)





## РџСЂРѕС„РёР»СЊ РїСЂРё Р·Р°РїСѓСЃРєРµ

РџСЂРѕС„РёР»СЊ Р·Р°РґР°С‘С‚СЃСЏ **РїСЂРё Р·Р°РїСѓСЃРєРµ РєРѕРЅС‚РµР№РЅРµСЂР°**

```bash
-e PYTHON_PROFILES_ACTIVE=sandbox
```

CI С‚РѕР»СЊРєРѕ СЃРѕР±РёСЂР°РµС‚ РѕР±СЂР°Р· Рё С‚СЂРёРіРіРµСЂРёС‚ РґРµРїР»РѕР№ Center-Inform (`DEPLOY_IMAGE_TAG`, `SERVICE_NAME`).
РќР° СЃС‚РµРЅРґРµ РїСЂРѕС„РёР»СЊ Рё override Р·Р°РґР°С‘С‚ СЌРєСЃРїР»СѓР°С‚Р°С†РёСЏ / С‚РµСЃС‚РёСЂРѕРІС‰РёРєРё С‡РµСЂРµР· **environment** РІ РјР°РЅРёС„РµСЃС‚Рµ РґРµРїР»РѕСЏ РёР»Рё `docker run`.


## РўРµСЃС‚РѕРІРѕРµ РїСЂРёР»РѕР¶РµРЅРёРµ (РІС‹РІРѕРґ РІ РєРѕРЅСЃРѕР»СЊ)

РџСЂРё СЃС‚Р°СЂС‚Рµ РІ Р»РѕРі РїРёС€РµС‚СЃСЏ Р°РєС‚РёРІРЅС‹Р№ РєРѕРЅС„РёРі:

- [`app/main.py`](app/main.py) вЂ” С‚РѕС‡РєР° РІС…РѕРґР°, `lifespan` РІС‹Р·С‹РІР°РµС‚ `log_app_config()`
- [`app/config/app_config.py`](app/config/app_config.py) вЂ” Р·Р°РіСЂСѓР·РєР° yaml, merge environment, РІС‹РІРѕРґ РІ stdout


РџСЂРѕРІРµСЂРєР° С‡РµСЂРµР· API:
- [`app/routers/hello_router.py`](app/routers/hello_router.py) вЂ” `GET /hello`


## РЎР±РѕСЂРєР° Рё Р»РѕРєР°Р»СЊРЅС‹Р№ Р·Р°РїСѓСЃРє РІ Docker

[`local-deploy.sh`](local-deploy.sh):


Р›РѕРіРё:

```bash
docker logs -f frap-llm-helper
```

## Kafka

**Р§С‚РµРЅРёРµ**
```bash
/opt/kafka/kafka/bin/kafka-console-consumer.sh --bootstrap-server gitlab-ci.ru:9092 --topic frap-llm-helper-in --from-beginning
```

```bash
/opt/kafka/kafka/bin/kafka-console-consumer.sh --bootstrap-server gitlab-ci.ru:9092 --topic frap-llm-helper-out --from-beginning
```

**Р—Р°РїРёСЃСЊ**
```bash
/opt/kafka/kafka/bin/kafka-console-producer.sh --broker-list gitlab-ci.ru:9092 --topic frap-llm-helper-in
```

```bash
/opt/kafka/kafka/bin/kafka-console-producer.sh --broker-list gitlab-ci.ru:9092 --topic frap-llm-helper-out
```
## Schema

frap-llm/
+-- app/
¦   +-- main.py                   # Модифицирован (добавлен lifespan, запуск Consumer)
¦   +-- config/
¦   ¦   +-- app_config.py         # Модифицирован (добавлена загрузка моделей)
¦   ¦   L-- __init__.py
¦   +-- models/
¦   ¦   +-- config_models.py      # НОВЫЙ: Pydantic-модели для конфигурации
¦   ¦   L-- __init__.py
¦   +-- services/
¦   ¦   +-- processor.py          # НОВЫЙ: Основная логика обработки
¦   ¦   +-- kafka_client.py       # НОВЫЙ: Обертка для работы с Kafka
¦   ¦   +-- db_client.py          # НОВЫЙ: Обертка для работы с PostgreSQL
¦   ¦   L-- __init__.py
¦   +-- routers/
¦   ¦   +-- hello_router.py       # Существующий (без изменений)
¦   ¦   L-- __init__.py
¦   L-- utils/
¦       +-- logging_config.py     # НОВЫЙ: Настройка логирования
¦       L-- __init__.py
+-- settings/
¦   +-- application.yaml
¦   +-- application-sandbox.yaml  # Модифицирован (добавлена секция file_storage)
¦   L-- config.reference.yaml
L-- requirements.txt              # Добавить: aiokafka, asyncpg, pydantic, PyYAML