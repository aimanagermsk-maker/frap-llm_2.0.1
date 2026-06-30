python
from typing import List, Optional
from pydantic import BaseModel

class XmlTagInfo(BaseModel):
    """Информация о теге из XML"""
    tag_name: str
    attributes: dict
    text_content: Optional[str] = None
    children_count: int = 0

class XmlStructure(BaseModel):
    """Структура XML файла"""
    root_tag: str
    all_tags: List[str] = []  # Список всех уникальных тегов
    tags_hierarchy: dict  # Иерархия тегов
    total_tags: int = 0
