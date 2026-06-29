# app/services/processor.py
import json
import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from uuid import uuid4
import time
import socket

from app.services.db_client import DatabaseClient
from app.services.kafka_client import KafkaClient
from app.services.logging_service import log_service
from app.models.config_models import Config, IncomingMessage

logger = logging.getLogger(__name__)

async def process_message(
    message: Dict[str, Any],
    db_client: DatabaseClient,
    kafka_client: KafkaClient,
    config: Config
) -> None:
    """
    Основной обработчик сообщений из Kafka с расширенным логированием
    """
    correlation_id = str(uuid4())
    processing_start = time.time()
    start_time = datetime.utcnow()
    
    # Базовые параметры для логирования
    log_context = {
        'correlation_id': correlation_id,
        'service_name': 'frap-llm-helper',
        'active_profile': os.getenv('PYTHON_PROFILES_ACTIVE', 'sandbox'),
        'hostname': socket.gethostname(),
        'pid': os.getpid()
    }
    
    try:
        # Шаг 1: Валидация входящего сообщения
        logger.info("Получено новое сообщение", extra={'extra_fields': log_context})
        
        try:
            incoming = IncomingMessage(**message)
            log_context.update({
                'record_id': incoming.id,
                'request_type': incoming.type,
                'request_date': incoming.date,
                'uri': incoming.uri
            })
        except Exception as e:
            error_msg = f"Ошибка валидации сообщения: {e}"
            logger.error(error_msg, extra={'extra_fields': {
                **log_context,
                'error_type': 'ValidationError',
                'error_message': str(e)
            }})
            await log_error(log_context, error_msg, 'ValidationError')
            return
        
        logger.info(
            f"Обработка запроса: id={incoming.id}, type={incoming.type}, uri={incoming.uri}",
            extra={'extra_fields': log_context}
        )
        
        # Шаг 2: Поиск в PostgreSQL
        db_query_start = time.time()
        
        db_record = await db_client.fetch_one(
            f"SELECT * FROM {config.postgres.table_name} WHERE uri = $1",
            incoming.uri
        )
        
        db_query_time = int((time.time() - db_query_start) * 1000)
        log_context['db_query_time_ms'] = db_query_time
        
        if not db_record:
            # Пробуем поиск по id
            db_record = await db_client.fetch_one(
                f"SELECT * FROM {config.postgres.table_name} WHERE id = $1",
                incoming.id
            )
            
            if not db_record:
                error_msg = f"Запись не найдена: uri={incoming.uri}, id={incoming.id}"
                logger.error(error_msg, extra={'extra_fields': log_context})
                await log_error(log_context, error_msg, 'RECORD_NOT_FOUND')
                
                await send_error_response(
                    kafka_client, config, incoming, correlation_id, error_msg
                )
                return
        
        logger.info(
            f"Запись найдена в БД: id={db_record.get('id')}",
            extra={'extra_fields': log_context}
        )
        
        # Шаг 3: Обработка LLM
        llm_start = time.time()
        processing_result = await process_with_llm(db_record, incoming, config)
        llm_time = int((time.time() - llm_start) * 1000)
        log_context['llm_processing_time_ms'] = llm_time
        
        # Шаг 4: Формирование выходных данных
        output_data = {
            "request": {
                "id": incoming.id,
                "type": incoming.type,
                "date": incoming.date,
                "uri": incoming.uri
            },
            "record_id": incoming.id,
            "correlation_id": correlation_id,
            "processed_at": datetime.utcnow().isoformat() + "Z",
            "data": processing_result,
            "metadata": {
                "source_table": config.postgres.table_name,
                "service": "frap-llm-helper",
                "search_by": "uri",
                "search_value": incoming.uri,
                "db_record_found": True
            },
            "status": "success"
        }
        
        # Шаг 5: Сохранение JSON-файла
        file_start = time.time()
        output_folder = config.file_storage.output_folder
        Path(output_folder).mkdir(parents=True, exist_ok=True)
        
        file_prefix = getattr(config.file_storage, 'file_prefix', 'result_')
        filename = f"{file_prefix}{correlation_id}.json"
        file_path = os.path.join(output_folder, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        file_time = int((time.time() - file_start) * 1000)
        file_size = os.path.getsize(file_path)
        
        log_context.update({
            'file_path': file_path,
            'file_size_bytes': file_size,
            'file_operation': 'write'
        })
        
        logger.info(
            f"JSON файл сохранен: {file_path}",
            extra={'extra_fields': log_context}
        )
        
        # Шаг 6: Отправка результата в Kafka
        kafka_start = time.time()
        
        await kafka_client.send(
            topic=config.kafka.output_topic,
            value=json.dumps(output_data)
        )
        
        kafka_time = int((time.time() - kafka_start) * 1000)
        log_context['message_size_bytes'] = len(json.dumps(output_data))
        
        logger.info(
            f"Результат отправлен в Kafka: correlation_id={correlation_id}",
            extra={'extra_fields': log_context}
        )
        
        # Вычисление общего времени
        total_time = int((time.time() - processing_start) * 1000)
        log_context['total_processing_time_ms'] = total_time
        
        # Сохраняем успешный лог в БД
        await log_service.log(
            level="INFO",
            logger="app.services.processor",
            module="processor",
            function="process_message",
            message=f"Запрос обработан успешно: record_id={incoming.id}",
            **log_context
        )
        
        # Опционально: удаление файла после отправки
        if getattr(config.file_storage, 'cleanup_after_send', False):
            os.remove(file_path)
            logger.info(f"Файл {file_path} удален")
            
    except Exception as e:
        total_time = int((time.time() - processing_start) * 1000)
        log_context['total_processing_time_ms'] = total_time
        
        logger.error(
            f"Критическая ошибка при обработке: {e}",
            extra={'extra_fields': {
                **log_context,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'stack_trace': str(e.__traceback__)
            }},
            exc_info=True
        )
        
        await log_error(log_context, str(e), type(e).__name__)
        
        if 'incoming' in locals():
            await send_error_response(
                kafka_client, config, incoming, correlation_id, str(e)
            )
        raise

async def log_error(log_context: Dict[str, Any], error_message: str, error_code: str):
    """Сохранение ошибки в БД"""
    await log_service.log(
        level="ERROR",
        logger="app.services.processor",
        module="processor",
        function="process_message",
        message=error_message,
        error_code=error_code,
        error_type="ProcessingError",
        stack_trace=error_message,
        **log_context
    )
