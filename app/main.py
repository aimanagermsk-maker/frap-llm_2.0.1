# app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.config.app_config import get_config
from app.routers import hello_router
from app.services.kafka_client import KafkaClient
from app.services.db_client import DatabaseClient
from app.services.processor import process_message
from app.utils.logging_config import log_app_config

logger = logging.getLogger(__name__)

# Глобальные переменные для клиентов
kafka_client = None
db_client = None
config = get_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения: инициализация и очистка ресурсов"""
    global kafka_client, db_client
    
    # Логируем активную конфигурацию при старте
    log_app_config(config)
    
    # 1. Инициализация клиента Kafka
    kafka_client = KafkaClient(
        bootstrap_servers=config.kafka.bootstrap_servers,
        consumer_group_id=config.kafka.consumer_group_id,
        input_topic=config.kafka.input_topic,
        output_topic=config.kafka.output_topic
    )
    await kafka_client.start()
    logger.info("Kafka клиент инициализирован")
    
    # 2. Инициализация клиента PostgreSQL
    db_client = DatabaseClient(
        host=config.postgres.host,
        port=config.postgres.port,
        database=config.postgres.database,
        user=config.postgres.user,
        password=config.postgres.password
    )
    await db_client.connect()
    logger.info("PostgreSQL клиент инициализирован")
    
    # 3. Запуск фоновой задачи для чтения Kafka
    consumer_task = asyncio.create_task(
        consume_kafka_messages(kafka_client, db_client, config)
    )
    logger.info("Фоновый Consumer Kafka запущен")
    
    # Передаем управление приложению
    yield
    
    # 4. Очистка ресурсов при завершении
    consumer_task.cancel()
    await kafka_client.stop()
    await db_client.disconnect()
    logger.info("Ресурсы освобождены")

app = FastAPI(
    title="FRAP LLM Helper",
    description="Сервис для обработки данных через LLM",
    version="1.0.0",
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(hello_router.router)

async def consume_kafka_messages(kafka_client: KafkaClient, db_client: DatabaseClient, config):
    """Фоновая задача для чтения сообщений из Kafka"""
    async for message in kafka_client.consume():
        try:
            # Вызываем основной обработчик из модуля processor
            await process_message(message, db_client, kafka_client, config)
        except Exception as e:
            logger.error(f"Ошибка при обработке сообщения: {e}")
            # Здесь можно реализовать логику отправки в DLQ