# app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.config.app_config import get_config, log_app_config
from app.services.kafka_client import KafkaConsumer
from app.services.processor import MessageProcessor
from app.routers import hello_router

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Управление жизненным циклом приложения"""
    # Запуск
    config = get_config()
    log_app_config(config)
    
    # Инициализируем Kafka Consumer и Processor
    processor = MessageProcessor(config)
    consumer = KafkaConsumer(
        bootstrap_servers=config.kafka.bootstrap_servers,
        group_id=config.kafka.consumer_group,
        topic=config.kafka.topic_in,
        processor=processor
    )
    
    # Запускаем потребление в фоновой задаче
    consumer_task = asyncio.create_task(consumer.start_consuming())
    
    app.state.consumer_task = consumer_task
    
    yield
    
    # Остановка
    consumer_task.cancel()
    await consumer_task

app = FastAPI(lifespan=lifespan)

# Подключаем роутеры
app.include_router(hello_router.router)

@app.get("/")
async def root():
    return {"message": "frap-llm-helper service is running"}
