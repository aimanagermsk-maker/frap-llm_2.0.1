# app/main.py
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config.app_config import log_app_config
from app.services.kafka_client import KafkaConsumerService
from app.services.processor import MessageProcessor
from app.services.db_client import DatabaseClient
from app.routers import hello_router
import logging

logger = logging.getLogger(__name__)

# Глобальные переменные для сервисов, чтобы можно было управлять ими извне
consumer_service = None
db_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Действия при СТАРТЕ ---
    global consumer_service, db_client
    logger.info("Starting up frap-llm-helper service...")

    # 1. Выводим активный конфиг для проверки
    await log_app_config()

    # 2. Инициализируем клиент БД
    db_client = DatabaseClient()
    await db_client.connect()

    # 3. Инициализируем обработчик сообщений (передаем клиент БД)
    processor = MessageProcessor(db_client)

    # 4. Создаем и запускаем Kafka Consumer как фоновую задачу
    consumer_service = KafkaConsumerService(processor)
    consumer_task = asyncio.create_task(consumer_service.start())

    # Отдаем управление FastAPI
    yield

    # --- Действия при ОСТАНОВКЕ ---
    logger.info("Shutting down frap-llm-helper service...")
    if consumer_service:
        await consumer_service.stop()
    if db_client:
        await db_client.disconnect()
    # Отменяем фоновую задачу, если она еще существует
    if consumer_task and not consumer_task.done():
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            logger.info("Consumer task cancelled successfully.")

app = FastAPI(
    title="FRAP LLM Helper",
    version="2.0.1",
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(hello_router.router)

@app.get("/")
async def root():
    return {"message": "FRAP LLM Helper is running"}
