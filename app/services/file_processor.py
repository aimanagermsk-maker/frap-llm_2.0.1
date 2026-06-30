import os
import xml.etree.ElementTree as ET
import aiofiles
from pathlib import Path
from typing import List, Set
import logging
from app.models.xml_models import XmlStructure

logger = logging.getLogger(__name__)

class FileProcessor:
    def __init__(self, base_path: str, output_dir: str):
        self.base_path = base_path
        self.output_dir = output_dir
        # Создаем output директорию, если её нет
        Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    async def process_xml_file(self, file_path: str, request_id: str) -> XmlStructure:
        """
        Читает XML файл, извлекает все теги и сохраняет список в текстовый файл
        """
        try:
            # 1. Читаем XML файл
            xml_content = await self._read_file(file_path)
            
            # 2. Парсим XML
            root = ET.fromstring(xml_content)
            
            # 3. Извлекаем все теги
            tags_info = self._extract_tags(root)
            
            # 4. Формируем результат
            xml_structure = XmlStructure(
                root_tag=root.tag,
                all_tags=tags_info['all_tags'],
                tags_hierarchy=tags_info['hierarchy'],
                total_tags=tags_info['total_tags']
            )
            
            # 5. Сохраняем список тегов в текстовый файл
            tags_file_path = await self._save_tags_to_file(
                xml_structure.all_tags, 
                request_id
            )
            
            logger.info(f"XML processed successfully. Tags: {len(xml_structure.all_tags)}")
            logger.info(f"Tags saved to: {tags_file_path}")
            
            return xml_structure
            
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise
        except ET.ParseError as e:
            logger.error(f"XML parsing error in {file_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            raise
    
    async def _read_file(self, file_path: str) -> str:
        """Асинхронно читает файл"""
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            return await f.read()
    
    def _extract_tags(self, element: ET.Element) -> dict:
        """Рекурсивно извлекает все теги из XML"""
        all_tags = set()
        hierarchy = {}
        total_tags = 0
        
        def traverse(el: ET.Element, path: str = ""):
            nonlocal total_tags
            tag_name = el.tag
            full_path = f"{path}/{tag_name}" if path else tag_name
            
            all_tags.add(tag_name)
            total_tags += 1
            
            # Сохраняем иерархию
            if full_path not in hierarchy:
                hierarchy[full_path] = {
                    'tag': tag_name,
                    'attributes': list(el.attrib.keys()),
                    'has_text': bool(el.text and el.text.strip()),
                    'children': [child.tag for child in el]
                }
            
            # Рекурсивно обходим детей
            for child in el:
                traverse(child, full_path)
        
        traverse(element)
        
        return {
            'all_tags': sorted(list(all_tags)),
            'hierarchy': hierarchy,
            'total_tags': total_tags
        }
    
    async def _save_tags_to_file(self, tags: List[str], request_id: str) -> str:
        """Сохраняет список тегов в текстовый файл"""
        output_file = os.path.join(self.output_dir, f"tags_{request_id}.txt")
        
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            # Записываем заголовок
            await f.write(f"Tags extracted for request: {request_id}\n")
            await f.write(f"Total tags: {len(tags)}\n")
            await f.write("-" * 50 + "\n")
            
            # Записываем каждый тег с номером
            for idx, tag in enumerate(tags, 1):
                await f.write(f"{idx:4d}. {tag}\n")
        
        return output_file
    
    async def save_processing_result(self, request_id: str, result: dict) -> str:
        """Сохраняет результат обработки"""
        output_file = os.path.join(self.output_dir, f"result_{request_id}.json")
        
        import json
        async with aiofiles.open(output_file, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(result, indent=2, default=str))
        
        return output_file
