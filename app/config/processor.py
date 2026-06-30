import logging
from typing import Dict, Any
from app.models.message_models import IncomingMessage
from app.services.file_processor import FileProcessor

logger = logging.getLogger(__name__)

class MessageProcessor:
    def __init__(self, config):
        self.config = config
        self.file_processor = FileProcessor(
            base_path=config.file_storage.base_path,
            output_dir=config.file_storage.output_dir
        )
    
    async def process_message(self, raw_message: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка входящего сообщения из Kafka
        
        Шаги:
        1. Валидация сообщения
        2. Построение пути к файлу
        3. Чтение и парсинг XML
        4. Извлечение тегов
        5. Передача списка тегов в LLM
        """
        try:
            # 1. Валидируем входящее сообщение
            message = IncomingMessage(**raw_message)
            logger.info(f"Processing message: {message.id} of type {message.type}")
            
            # 2. Формируем путь к файлу
            file_path = message.get_file_path(self.config.file_storage.base_path)
            logger.info(f"Looking for file: {file_path}")
            
            # 3. Обрабатываем XML файл
            xml_structure = await self.file_processor.process_xml_file(
                file_path, 
                message.id
            )
            
            # 4. Формируем результат для LLM
            # Вместо данных из БД, передаем список тегов
            llm_input = {
                "request_id": message.id,
                "file_info": {
                    "path": file_path,
                    "type": message.type,
                    "date": str(message.date)
                },
                "xml_structure": {
                    "root_tag": xml_structure.root_tag,
                    "tags": xml_structure.all_tags,
                    "total_tags": xml_structure.total_tags,
                    "tags_hierarchy": xml_structure.tags_hierarchy
                }
            }
            
            # 5. Вызываем LLM с новыми данными
            llm_result = await self._process_with_llm(llm_input)
            
            # 6. Сохраняем результат
            result_file = await self.file_processor.save_processing_result(
                message.id,
                llm_result
            )
            
            # 7. Формируем ответ
            result = {
                "request_id": message.id,
                "status": "success",
                "file_processed": file_path,
                "tags_found": len(xml_structure.all_tags),
                "tags_list": xml_structure.all_tags[:20],  # Только первые 20 для примера
                "result_file": result_file,
                "llm_response": llm_result.get("response", ""),
                "timestamp": str(message.date)
            }
            
            logger.info(f"Successfully processed request {message.id}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            raise
    
    async def _process_with_llm(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Асинхронный вызов LLM с данными из XML
        
        Вместо данных из БД, передаем:
        - Список всех тегов из XML
        - Структуру XML файла
        - Метаданные файла
        """
        # TODO: Здесь должен быть реальный вызов LLM
        # Пока возвращаем заглушку
        
        tags_summary = {
            "total_tags": data["xml_structure"]["total_tags"],
            "unique_tags": len(data["xml_structure"]["tags"]),
            "tags_sample": data["xml_structure"]["tags"][:10],
            "root_tag": data["xml_structure"]["root_tag"]
        }
        
        # Имитация обработки LLM
        logger.info(f"Calling LLM with {data['xml_structure']['total_tags']} tags")
        
        return {
            "response": f"Анализ XML завершен. Найдено {data['xml_structure']['total_tags']} тегов.",
            "tags_summary": tags_summary,
            "processing_time": 0.5
        }
