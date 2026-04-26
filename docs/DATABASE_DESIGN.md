# Jaaz 数据库设计文档

## 概览

- **数据库**: SQLite (`aiosqlite`)
- **数据库文件**: `user_data/localmanus.db`
- **连接池**: `ConnectionPool` — 复用连接，减少每次请求新建连接的开销
- **迁移系统**: 版本化管理，当前版本 v4

---

## 迁移历史

| 版本 | 名称 | 描述 |
|------|------|------|
| v1 | Initial schema | 创建 `chat_sessions`、`chat_messages` 表 |
| v2 | Add canvases | 创建 `canvases` 表，添加 `canvas_id` 外键 |
| v3 | Add comfy workflow | 创建 `comfy_workflows` 表 |
| v4 | Add performance indexes | 添加查询性能索引 |

---

## 表结构

### 1. `canvases` — 画布

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT | PRIMARY KEY | 唯一标识 |
| `name` | TEXT | NOT NULL | 画布名称 |
| `data` | TEXT | | 画布数据 (JSON) |
| `description` | TEXT | DEFAULT '' | 描述 |
| `thumbnail` | TEXT | DEFAULT '' | 缩略图路径 |
| `created_at` | TEXT | DEFAULT (STRFTIME) | 创建时间 ISO8601 |
| `updated_at` | TEXT | DEFAULT (STRFTIME) | 更新时间 ISO8601 |

**索引:**
- `idx_canvases_updated_at` ON `updated_at DESC, id DESC`
- `idx_canvases_updated` ON `updated_at DESC` (v4)

---

### 2. `chat_sessions` — 聊天会话

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | TEXT | PRIMARY KEY | 唯一标识 |
| `canvas_id` | TEXT | FOREIGN KEY → `canvases(id)` | 所属画布 |
| `title` | TEXT | | 会话标题 |
| `model` | TEXT | | 使用的模型 |
| `provider` | TEXT | | 模型提供商 |
| `created_at` | TEXT | DEFAULT (STRFTIME) | 创建时间 |
| `updated_at` | TEXT | DEFAULT (STRFTIME) | 更新时间 |

**索引:**
- `idx_chat_sessions_updated_at` ON `updated_at DESC, id DESC`
- `idx_chat_sessions_canvas` ON `canvas_id` (v4)

---

### 3. `chat_messages` — 聊天消息

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 消息 ID |
| `session_id` | TEXT | FOREIGN KEY → `chat_sessions(id)` | 所属会话 |
| `role` | TEXT | | 角色 (user/assistant/system) |
| `message` | TEXT | | 消息内容 (JSON) |
| `created_at` | TEXT | DEFAULT (STRFTIME) | 创建时间 |
| `updated_at` | TEXT | DEFAULT (STRFTIME) | 更新时间 |

**索引:**
- `idx_chat_messages_session_id_id` ON `session_id, id`
- `idx_chat_messages_session` ON `session_id` (v4)

---

### 4. `comfy_workflows` — ComfyUI 工作流

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 工作流 ID |
| `name` | TEXT | NOT NULL | 工作流名称 |
| `api_json` | TEXT | | API JSON 定义 |
| `description` | TEXT | DEFAULT '' | 描述 |
| `inputs` | TEXT | | 输入定义 |
| `outputs` | TEXT | | 输出定义 |
| `created_at` | TEXT | DEFAULT (STRFTIME) | 创建时间 |
| `updated_at` | TEXT | DEFAULT (STRFTIME) | 更新时间 |

**索引:**
- `idx_comfy_workflows_updated_at` ON `updated_at DESC, id DESC`

---

## 索引汇总

| 索引名 | 表 | 字段 | 用途 |
|--------|-----|------|------|
| `idx_canvases_updated_at` | canvases | `updated_at DESC, id DESC` | 按更新时间排序 |
| `idx_canvases_updated` | canvases | `updated_at DESC` | 画布列表排序 |
| `idx_chat_sessions_updated_at` | chat_sessions | `updated_at DESC, id DESC` | 按更新时间排序 |
| `idx_chat_sessions_canvas` | chat_sessions | `canvas_id` | 查某画布的所有会话 |
| `idx_chat_messages_session_id_id` | chat_messages | `session_id, id` | 查某会话的消息 |
| `idx_chat_messages_session` | chat_messages | `session_id` | 消息关联查询 |
| `idx_comfy_workflows_updated_at` | comfy_workflows | `updated_at DESC, id DESC` | 工作流列表排序 |

---

## 服务层

`DatabaseService` (单例 `db_service`) 提供所有数据库操作：

| 方法 | 说明 |
|------|------|
| `create_canvas(id, name)` | 创建画布 |
| `list_canvases()` | 列出所有画布 (按 updated_at DESC) |
| `save_canvas_data(id, data, thumbnail)` | 保存画布数据 |
| `get_canvas_data(id)` | 获取画布数据 + 会话列表 |
| `delete_canvas(id)` | 删除画布 |
| `rename_canvas(id, name)` | 重命名画布 |
| `create_chat_session(...)` | 创建会话 |
| `list_sessions(canvas_id)` | 列出某画布的所有会话 |
| `create_message(session_id, role, message)` | 保存消息 |
| `get_chat_history(session_id)` | 获取某会话的消息历史 |
| `create_comfy_workflow(...)` | 保存工作流 |
| `list_comfy_workflows()` | 列出所有工作流 |
| `get_comfy_workflow(id)` | 获取单个工作流 |
| `delete_comfy_workflow(id)` | 删除工作流 |

---

## 连接池

`ConnectionPool` 实现 (aiosqlite 无内置池):

```python
class ConnectionPool:
    def __init__(self, database: str, min_connections=1, max_connections=5)
    async def initialize()
    async def acquire() -> aiosqlite.Connection
    async def release(conn)
    async def close_all()
```

全局单例通过 `get_db_pool()` 获取，所有 `DatabaseService` 方法使用此池。

---

## 时间格式

所有时间字段使用 SQLite `STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')` 生成，格式为 ISO8601:
```
2026-04-26T14:30:00.123Z
```
