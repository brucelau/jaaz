# 03 - API 路由

## 概述

后端共有 **11 个路由模块**，统一挂载在 `/api` 前缀下。

## 路由注册中心

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/core/routers.py`

```python
def register_routers(app):
    app.include_router(root_router, prefix="/api", tags=["root"])
    app.include_router(config_router, prefix="/api/config", tags=["config"])
    app.include_router(image_router, prefix="/api", tags=["image"])
    app.include_router(workspace_router, prefix="/api", tags=["workspace"])
    app.include_router(canvas_router, prefix="/api/canvas", tags=["canvas"])
    app.include_router(chat_router, prefix="/api", tags=["chat"])
    app.include_router(settings_router, prefix="/api/settings", tags=["settings"])
    app.include_router(tool_confirmation_router, prefix="/api", tags=["tool"])
    app.include_router(ssl_test_router, prefix="/api", tags=["ssl"])
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
```

---

## 1. 认证路由 (auth_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/auth_router.py`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/auth/register` | 用户注册 | 否 |
| POST | `/api/auth/login` | 用户登录 | 否 |
| GET | `/api/auth/refresh-token` | 刷新 Token | 可选 |

### POST /api/auth/register

**请求体**:
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**响应**:
```json
{
  "token": "local_xxx",
  "user_info": {
    "id": "xxx",
    "username": "xxx",
    "email": "xxx"
  }
}
```

### POST /api/auth/login

**请求体**:
```json
{
  "username": "string",
  "password": "string"
}
```

**响应**: 同注册

### GET /api/auth/refresh-token

**请求头**: `Authorization: Bearer <token>`

**响应**:
```json
{ "valid": true }
```
或
```json
{ "valid": true, "new_token": "local_xxx" }
```

---

## 2. 根路由 (root_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/root_router.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/list_models` | 获取可用模型列表 |
| GET | `/api/list_tools` | 获取可用工具列表 |
| GET | `/api/list_chat_sessions` | 获取聊天会话列表 |
| GET | `/api/chat_session/{session_id}` | 获取会话消息历史 |
| GET | `/api/billing/getBalance` | 获取余额 (Mock) |

### GET /api/list_models

**响应**:
```json
[
  {
    "provider": "openai",
    "model": "gpt-4o",
    "type": "text",
    "url": "https://api.openai.com/v1"
  }
]
```

### GET /api/list_tools

**响应**:
```json
[
  {
    "provider": "jaaz",
    "id": "generate_image",
    "display_name": "Generate Image",
    "type": "image"
  }
]
```

---

## 3. Canvas 路由 (canvas_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/canvas_router.py`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/canvas/list` | 列出所有 Canvas | 否 |
| POST | `/api/canvas/create` | 创建 Canvas | **是** |
| GET | `/api/canvas/{id}` | 获取 Canvas | 否 |
| POST | `/api/canvas/{id}/save` | 保存 Canvas | 否 |
| POST | `/api/canvas/{id}/rename` | 重命名 | 否 |
| DELETE | `/api/canvas/{id}/delete` | 删除 | 否 |

### POST /api/canvas/create

**请求体**:
```json
{
  "canvas_id": "string",
  "name": "string"
}
```

**响应**:
```json
{ "id": "canvas_xxx" }
```

### POST /api/canvas/{id}/save

**请求体**:
```json
{
  "data": { ... },
  "thumbnail": "base64_string"
}
```

---

## 4. 聊天路由 (chat_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/chat_router.py`

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/chat` | 发送消息 | **是** |
| POST | `/api/cancel/{session_id}` | 取消聊天 | 否 |
| POST | `/api/magic` | 魔法生成 | **是** |
| POST | `/api/magic/cancel/{session_id}` | 取消魔法 | 否 |

### POST /api/chat

**请求体**:
```json
{
  "messages": [...],
  "canvas_id": "string",
  "session_id": "string",
  "text_model": { "provider": "openai", "model": "gpt-4o" },
  "tool_list": [...],
  "system_prompt": "string"
}
```

**响应**:
```json
{ "status": "done" }
```

*注: 实际响应通过 WebSocket 推送*

### POST /api/magic

类似 `/api/chat`，触发特殊魔法生成流程。

---

## 5. 图片路由 (image_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/image_router.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/upload_image` | 上传图片 (支持压缩) |
| GET | `/api/file/{file_id}` | 获取图片文件 |
| POST | `/api/comfyui/object_info` | 获取 ComfyUI 模型信息 |

### POST /api/upload_image

**表单数据**:
- `file`: 文件
- `max_size_mb`: 最大尺寸 (可选)

**响应**:
```json
{
  "file_id": "xxx.jpg",
  "url": "http://localhost:57988/api/file/xxx.jpg",
  "width": 1024,
  "height": 768
}
```

---

## 6. 工作区路由 (workspace_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/workspace_router.py`

文件系统操作相关接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/update_file` | 更新文件 |
| POST | `/api/create_file` | 创建文件 |
| POST | `/api/delete_file` | 删除文件 |
| POST | `/api/rename_file` | 重命名文件 |
| POST | `/api/read_file` | 读取文件 |
| GET | `/api/list_files_in_dir` | 列出目录文件 |
| POST | `/api/open_folder_in_explorer` | 打开文件夹 |
| GET | `/api/browse_filesystem` | 浏览文件系统 |
| GET | `/api/get_media_files` | 获取媒体文件 |
| GET | `/api/get_file_thumbnail` | 获取缩略图 |
| GET | `/api/get_file_info` | 获取文件信息 |
| GET | `/api/serve_file` | 服务文件 |

---

## 7. 设置路由 (settings_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/settings_router.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/settings/exists` | 检查设置文件是否存在 |
| GET | `/api/settings` | 获取设置 |
| POST | `/api/settings` | 更新设置 |
| GET | `/api/settings/proxy/status` | 代理状态 |
| GET | `/api/settings/proxy` | 获取代理配置 |
| POST | `/api/settings/proxy` | 更新代理配置 |
| POST | `/api/settings/comfyui/create_workflow` | 创建 ComfyUI 工作流 |
| GET | `/api/settings/comfyui/list_workflows` | 列出工作流 |
| DELETE | `/api/settings/comfyui/delete_workflow/{id}` | 删除工作流 |
| POST | `/api/settings/comfyui/proxy` | ComfyUI 代理 |
| GET | `/api/settings/knowledge/enabled` | 获取启用的知识库 |
| GET | `/api/settings/my_assets_dir_path` | 获取资源目录路径 |

---

## 8. 配置路由 (config_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/config_router.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config/exists` | 检查配置是否存在 |
| GET | `/api/config` | 获取配置 |
| POST | `/api/config` | 更新配置 |

### POST /api/config

**请求体**:
```json
{
  "openai": {
    "api_key": "sk-xxx",
    "model": "gpt-4o"
  }
}
```

*注: 更新后会重新初始化工具*

---

## 9. 工具确认路由 (tool_confirmation_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/tool_confirmation_router.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/tool_confirmation` | 确认/取消工具调用 |

### POST /api/tool_confirmation

**请求体**:
```json
{
  "session_id": "string",
  "tool_call_id": "string",
  "confirmed": true
}
```

---

## 10. SSL 测试路由 (ssl_test_router.py)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/routers/ssl_test_router.py`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/test_ssl` | 快速 SSL 测试 |
| GET | `/api/test_ssl_full` | 完整 SSL 测试套件 |
| GET | `/api/ssl_status` | SSL 环境状态 |

---

## API 路径速查表

| 路径 | 方法 | 文件 |
|------|------|------|
| `/api/auth/register` | POST | auth_router.py |
| `/api/auth/login` | POST | auth_router.py |
| `/api/auth/refresh-token` | GET | auth_router.py |
| `/api/list_models` | GET | root_router.py |
| `/api/list_tools` | GET | root_router.py |
| `/api/canvas/list` | GET | canvas_router.py |
| `/api/canvas/create` | POST | canvas_router.py |
| `/api/canvas/{id}` | GET | canvas_router.py |
| `/api/canvas/{id}/save` | POST | canvas_router.py |
| `/api/chat` | POST | chat_router.py |
| `/api/magic` | POST | chat_router.py |
| `/api/upload_image` | POST | image_router.py |
| `/api/file/{file_id}` | GET | image_router.py |
| `/api/config` | GET/POST | config_router.py |
| `/api/settings` | GET/POST | settings_router.py |
| `/api/tool_confirmation` | POST | tool_confirmation_router.py |
