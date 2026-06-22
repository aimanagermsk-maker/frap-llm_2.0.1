# app/models/config_models.py
from pydantic import BaseModel
from typing import Optional

class PostgresConfig(BaseModel):
    host: str
    port: int
    database: str
    user: str
    password: str
    table_name: str

class KafkaConfig(BaseModel):
    bootstrap_servers: str
    consumer_group_id: str
    input_topic: str
    output_topic: str

class FileStorageConfig(BaseModel):
    output_folder: str
    file_prefix: Optional[str] = "result_"
    cleanup_after_send: Optional[bool] = False

class AppConfig(BaseModel):
    postgres: PostgresConfig
    kafka: KafkaConfig
    file_storage: FileStorageConfig