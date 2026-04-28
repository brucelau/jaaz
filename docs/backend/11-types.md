# 11 - 类型定义

## 概述

后端使用 Pydantic 定义请求/响应模型。

## 核心文件

| 文件 | 职责 |
|------|------|
| `web/models/tool_model.py` | 工具类型 |
| `web/models/config_model.py` | 配置类型 |
| `web/routers/*` | 各路由的 Request/Response 模型 |

---

## tool_model.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/models/tool_model.py`

### ToolInfo

```python
from pydantic import BaseModel
from typing import Callable, Optional

class ToolInfo(BaseModel):
    tool_function: Callable = None  # 实际工具函数
    provider: str                  # Provider 名称
    display_name: Optional[str] = None
    type: str = "tool"  # "image" | "video" | "tool"
```

### ToolInfoJson

```python
class ToolInfoJson(BaseModel):
    """API 返回给前端的工具信息"""
    provider: str
    id: str
    display_name: Optional[str] = None
    type: str = "tool"
```

---

## config_model.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/models/config_model.py`

### LLMConfig

```python
class LLMConfig(BaseModel):
    provider: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: Optional[str] = None
    models: Optional[List[str]] = None  # 支持多模型
    name: Optional[str] = None
    type: Optional[str] = None  # "text" | "image" | "video"
    is_custom: bool = False  # 是否用户自定义
```

### ModelInfo

```python
class ModelInfo(BaseModel):
    provider: str
    model: str
    type: str  # "text" | "image" | "tool" | "video"
    url: str
```

### ConfigUpdate

```python
class ConfigUpdate(BaseModel):
    """配置更新请求"""
    # 动态 key，如 { "openai": { "api_key": "xxx" } }
```

---

## auth_router.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/auth_router.py`

### RegisterRequest

```python
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
```

### LoginRequest

```python
class LoginRequest(BaseModel):
    username: str
    password: str
```

### TokenResponse

```python
class TokenResponse(BaseModel):
    token: str
    user_info: UserInfo

class UserInfo(BaseModel):
    id: str
    username: str
    email: str
    image_url: Optional[str] = None
    provider: Optional[str] = None
    created_at: Optional[str] = None
```

---

## chat_router.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/chat_router.py`

### ChatRequest

```python
class ChatRequest(BaseModel):
    messages: List[Message]
    canvas_id: str
    session_id: str
    text_model: Model  # { provider, model, url? }
    tool_list: List[ToolInfoJson]
    system_prompt: Optional[str] = None
```

### Message (前端定义，后端透传)

```python
class Message(BaseModel):
    role: str  # "user" | "assistant" | "system" | "tool"
    content: Union[str, List[ContentBlock]]
    tool_calls: Optional[List[ToolCall]] = None
    tool_call_id: Optional[str] = None

class ContentBlock(BaseModel):
    type: str  # "text" | "image_url"
    text: Optional[str] = None
    image_url: Optional[dict] = None

class ToolCall(BaseModel):
    id: str
    type: str = "function"
    function: Function
    result: Optional[Any] = None

class Function(BaseModel):
    name: str
    arguments: str
```

### MagicRequest

```python
class MagicRequest(BaseModel):
    # 类似 ChatRequest
    messages: List[Message]
    canvas_id: str
    session_id: str
    text_model: Model
    tool_list: List[ToolInfoJson]
    system_prompt: Optional[str] = None
```

---

## canvas_router.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/canvas_router.py`

### CreateCanvasRequest

```python
class CreateCanvasRequest(BaseModel):
    canvas_id: str
    name: str
```

### SaveCanvasRequest

```python
class SaveCanvasRequest(BaseModel):
    data: dict  # Excalidraw JSON
    thumbnail: str  # Base64
```

### RenameCanvasRequest

```python
class RenameCanvasRequest(BaseModel):
    name: str
```

### CanvasResponse

```python
class CanvasResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    created_at: str
```

---

## image_router.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/image_router.py`

### UploadImageResponse

```python
class UploadImageResponse(BaseModel):
    file_id: str
    url: str
    width: int
    height: int
```

---

## tool_confirmation_router.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/tool_confirmation_router.py`

### ToolConfirmationRequest

```python
class ToolConfirmationRequest(BaseModel):
    session_id: str
    tool_call_id: str
    confirmed: bool
```

---

## settings_router.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/settings_router.py`

### ProxyConfig

```python
class ProxyConfig(BaseModel):
    proxy: str  # "system" | "no_proxy" | "http://..." | "socks5://..."
```

### CreateWorkflowRequest

```python
class CreateWorkflowRequest(BaseModel):
    name: str
    api_json: dict
    description: str = ""
    inputs: List[str] = []
    outputs: Optional[str] = None
```

---

## database/db_service.py

### 数据库模型 (非 Pydantic，直接 SQL)

```python
# Canvas
{
    "id": str,
    "name": str,
    "data": str,  # JSON
    "description": str,
    "thumbnail": str,  # Base64
    "created_at": str,
    "updated_at": str
}

# ChatSession
{
    "id": str,
    "canvas_id": str,
    "title": str,
    "model": str,
    "provider": str,
    "created_at": str,
    "updated_at": str
}

# ChatMessage
{
    "id": int,
    "session_id": str,
    "role": str,
    "message": str,  # JSON
    "created_at": str,
    "updated_at": str
}

# ComfyWorkflow
{
    "id": int,
    "name": str,
    "api_json": str,  # JSON
    "description": str,
    "inputs": str,  # JSON
    "outputs": str,
    "created_at": str,
    "updated_at": str
}
```

---

## WebSocket 事件类型

### SessionUpdateEvent

```python
class SessionUpdateEvent(BaseModel):
    session_id: str
    type: str  # EventType 枚举
```

### EventType 枚举

```python
class SessionEventType(str, Enum):
    Delta = "Delta"
    ToolCall = "ToolCall"
    ToolCallPendingConfirmation = "ToolCallPendingConfirmation"
    ToolCallConfirmed = "ToolCallConfirmed"
    ToolCallCancelled = "ToolCallCancelled"
    ToolCallArguments = "ToolCallArguments"
    ToolCallProgress = "ToolCallProgress"
    ToolCallResult = "ToolCallResult"
    ImageGenerated = "ImageGenerated"
    VideoGenerated = "VideoGenerated"
    AllMessages = "AllMessages"
    Done = "Done"
    Error = "Error"
    Info = "Info"
```
