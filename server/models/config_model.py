from pydantic import BaseModel
from typing import Literal

class LLMConfig(BaseModel):
    model: str
    base_url: str
    api_key: str
    max_tokens: int
    temperature: float

class ConfigUpdate(BaseModel):
    llm: LLMConfig

class ModelInfo(BaseModel):
    provider: str
    model: str
    url: str
    type: Literal['text', 'image', 'tool', 'video']
