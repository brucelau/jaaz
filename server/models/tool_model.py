from typing import Optional, Any
from pydantic import BaseModel


class ToolInfo(BaseModel):
    tool_function: Any
    provider: str
    display_name: Optional[str] = None
    type: Optional[str] = None


class ToolInfoJson(BaseModel):
    provider: str
    id: str
    display_name: Optional[str] = None
    type: Optional[str] = None
