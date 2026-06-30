# app/models/config_models.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class KafkaConfig(BaseModel):
    bootstrap_servers: str
    consumer_group_id: str
    input_topic: str
    output_topic: str

class FileStorageConfig(BaseModel):
    """Конфигурация файлового хранилища"""
    base_path: str = "/data"  # Базовый путь к файлам [Part1]
    output_dir: str = "/output"  # Папка для сохранения результатов

class LoggingConfig(BaseModel):
    """Конфигурация логирования в БД"""
    enabled: bool = True
    table_name: str = "service_logs"
    batch_size: int = 10
    flush_interval_seconds: int = 5
    async_mode: bool = True
    log_levels: list[str] = ["ERROR", "WARNING", "INFO", "DEBUG"]

class AppConfig(BaseModel):
    kafka: KafkaConfig
    file_storage: FileStorageConfig
    logging: Optional[Dict[str, Any]] = None
