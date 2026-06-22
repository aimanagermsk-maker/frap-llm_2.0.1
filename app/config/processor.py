# app/services/processor.py
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from app.services.db_client import DatabaseClient
from app.services.kafka_client import KafkaClient
from app.models.config_models import Config

logger = logging.getLogger(__name__)

async def process_message(
    message: Dict[str, Any],
    db_client: DatabaseClient,
    kafka_client: KafkaClient,
    config: Config
) -> None:
    """
    Основной обработчик сообщений из Kafka.
    
    Шаги:
    1. Извлечение record_id из сообщения
    2. Получение данных из PostgreSQL
    3. Обработка данных (бизнес-логика)
    4. Сохранение результата в JSON-файл
    5. Чтение JSON-файла
    6. Отправка содержимого в Kafka
    """
    try:
        # Шаг 1: Извлечение данных из сообщения
        record_id = message.get('record_id')
        correlation_id = message.get('correlation_id')
        
        if not record_id:
            logger.error("Отсутствует record_id в сообщении")
            return
        
        logger.info(f"Обработка записи ID: {record_id}, Correlation ID: {correlation_id}")
        
        # Шаг 2: Получение данных из PostgreSQL
        db_record = await db_client.fetch_one(
            f"SELECT * FROM {config.postgres.table_name} WHERE id = $1",
            record_id
        )
        
        if not db_record:
            logger.error(f"Запись с ID {record_id} не найдена в таблице {config.postgres.table_name}")
            return
        
        # Шаг 3: Обработка данных (здесь будет ваша бизнес-логика, например, вызов LLM)
        processing_result = await process_with_llm(db_record, config)
        
        # Шаг 4: Формирование и сохранение JSON-файла
        output_data = {
            "record_id": record_id,
            "correlation_id": correlation_id,
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "data": processing_result,
            "metadata": {
                "source_table": config.postgres.table_name,
                "service": "frap-llm-helper"
            }
        }
        
        # Создаем папку для выходных файлов, если её нет
        output_folder = config.file_storage.output_folder
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        # Формируем имя файла
        file_prefix = getattr(config.file_storage, 'file_prefix', 'result_')
        filename = f"{file_prefix}{correlation_id or record_id}.json"
        file_path = os.path.join(output_folder, filename)
        
        # Сохраняем JSON в файл с форматированием для читаемости
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"JSON файл сохранен: {file_path}")
        
        # Шаг 5: Чтение JSON-файла
        with open(file_path, 'r', encoding='utf-8') as f:
            result_json = json.load(f)
        
        # Шаг 6: Отправка содержимого в Kafka
        await kafka_client.send(
            topic=config.kafka.output_topic,
            value=json.dumps(result_json)
        )
        logger.info(f"Результат отправлен в Kafka для record_id {record_id}")
        
        # Опционально: удаление файла после отправки
        if getattr(config.file_storage, 'cleanup_after_send', False):
            os.remove(file_path)
            logger.info(f"Файл {file_path} удален")
            
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения {message.get('correlation_id')}: {e}")
        # Здесь можно реализовать отправку в DLQ (Dead Letter Queue)
        # await kafka_client.send_dlq(message, str(e))
        raise

async def process_with_llm(db_record: Dict[str, Any], config: Config) -> Dict[str, Any]:
    """
    Пример бизнес-логики с LLM.
    В реальном проекте здесь будет вызов модели через API.
    """
    # Извлекаем текстовое поле для обработки (предположим, оно есть)
    original_text = db_record.get('text_content', 'Текст для обработки отсутствует')
    
    # Имитация работы LLM (замените на реальный вызов)
    logger.info(f"Обработка текста через LLM: {original_text[:50]}...")
    
    # Например, можно вызывать OpenAI или другую модель
    # result = await call_llm_api(original_text, config.llm_settings)
    
    # Заглушка
    result = {
        "original_text": original_text,
        "generated_text": f"Обработанный текст для записи {db_record.get('id')}",
        "tokens_used": 150,
        "model": "example-model-v1"
    }
    
    return result