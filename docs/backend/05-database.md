# 05 - 数据库层

## 概述

使用 **SQLite (aiosqlite)** 作为数据库，通过连接池管理连接，支持版本化迁移。

## 核心文件

| 文件 | 职责 |
|------|------|
| `database/db_service.py` | 连接池、CRUD、迁移 |
| `database/settings_service.py` | JSON 设置管理 |
| `database/migrations/*.py` | 版本化迁移脚本 |
| `database/localmanus.db` | SQLite 数据库文件 |

## 数据库路径

```python
# config_service.py
DB_DIR = <SERVER_DIR>/database
DB_PATH = <SERVER_DIR>/database/localmanus.db
```

## 连接池

**文件**: `/Users/cyberway/ocworkspace/James/server/database/db_service.py`

```python
class ConnectionPool:
    def __init__(self, database, min_connections=1, max_connections=10):
        self._pool = []  # 缓存连接
        self.database = database

    def initialize(self):
        # 创建 min_connections 个初始连接

    def acquire(self):
        # 获取连接

    def release(self, conn):
        # 放回连接池

    def close_all(self):
        # 关闭所有连接
```

## 数据库表

### v1: 初始 Schema

**表**: `chat_sessions`
```sql
CREATE TABLE chat_sessions (
  id TEXT PRIMARY KEY,
  canvas_id TEXT REFERENCES canvases(id),
  created_at TEXT DEFAULT STRFTIME(...),
  updated_at TEXT DEFAULT STRFTIME(...),
  title TEXT,
  model TEXT,
  provider TEXT
)
```

**表**: `chat_messages`
```sql
CREATE TABLE chat_messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT,
  role TEXT,
  message TEXT,
  created_at TEXT DEFAULT STRFTIME(...),
  updated_at TEXT DEFAULT STRFTIME(...),
  FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
)
```

### v2: 添加 Canvas

**表**: `canvases`
```sql
CREATE TABLE canvases (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  data TEXT,
  description TEXT DEFAULT '',
  thumbnail TEXT DEFAULT '',
  created_at TEXT DEFAULT STRFTIME(...),
  updated_at TEXT DEFAULT STRFTIME(...)
)
```

### v3: 添加 ComfyUI Workflow

**表**: `comfy_workflows`
```sql
CREATE TABLE comfy_workflows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  api_json TEXT,
  description TEXT DEFAULT '',
  inputs TEXT,
  outputs TEXT,
  created_at TEXT DEFAULT STRFTIME(...),
  updated_at TEXT DEFAULT STRFTIME(...)
)
```

### v4: 性能索引

```sql
-- chat_sessions 索引
CREATE INDEX idx_chat_sessions_canvas ON chat_sessions(canvas_id)
CREATE INDEX idx_chat_sessions_updated ON chat_sessions(updated_at DESC, id DESC)

-- chat_messages 索引
CREATE INDEX idx_chat_messages_session ON chat_messages(session_id)
CREATE INDEX idx_chat_messages_session_id ON chat_messages(session_id, id)

-- canvases 索引
CREATE INDEX idx_canvases_updated ON canvases(updated_at DESC)
```

### v5: 认证表

**表**: `auth_users`
```sql
CREATE TABLE auth_users (
  id TEXT PRIMARY KEY,
  username TEXT UNIQUE NOT NULL,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  created_at REAL NOT NULL
)
```

**表**: `auth_tokens`
```sql
CREATE TABLE auth_tokens (
  token TEXT PRIMARY KEY,
  user_id TEXT NOT NULL,
  created_at REAL NOT NULL,
  expires_at REAL NOT NULL,
  FOREIGN KEY (user_id) REFERENCES auth_users(id)
)
```

---

## 迁移系统

**文件**: `/Users/cyberway/ocworkspace/James/server/database/migrations/manager.py`

```python
CURRENT_VERSION = 5

class MigrationManager:
    def migrate(self, conn, from_version, to_version):
        # 逐步执行 up() 方法
        for version in range(from_version + 1, to_version + 1):
            migration = ALL_MIGRATIONS[version]
            migration().up(conn)
            # 更新 db_version
```

### 迁移列表

| 版本 | 文件 | 说明 |
|------|------|------|
| v1 | v1_initial_schema.py | chat_sessions, chat_messages |
| v2 | v2_add_canvases.py | canvases 表 |
| v3 | v3_add_comfy_workflow.py | comfy_workflows 表 |
| v4 | v4_add_performance_indexes.py | 性能索引 |
| v5 | v5_add_auth.py | auth_users, auth_tokens |

---

## CRUD 操作

### Canvas

```python
# 创建
create_canvas(id: str, name: str)

# 列表
list_canvases() -> [{ id, name, description, thumbnail, created_at }]

# 获取
get_canvas_data(id: str) -> { data, name, sessions }

# 保存
save_canvas_data(id: str, data, thumbnail=None)

# 重命名
rename_canvas(id: str, name: str)

# 删除
delete_canvas(id: str)
```

### Chat Sessions

```python
# 创建
create_chat_session(id: str, model: str, provider: str, canvas_id: str, title=None)

# 列表
list_sessions(canvas_id=None) -> [sessions]

# 检查存在
session_exists(session_id) -> bool
```

### Chat Messages

```python
# 创建
create_message(session_id: str, role: str, message: str)

# 获取历史
get_chat_history(session_id: str) -> [messages]
```

### Comfy Workflows

```python
# 创建
create_comfy_workflow(name, api_json, description, inputs, outputs)

# 列表
list_comfy_workflows() -> [workflows]

# 获取
get_comfy_workflow(id) -> workflow

# 删除
delete_comfy_workflow(id)
```

---

## 设置服务 (settings_service.py)

**文件**: `/Users/cyberway/ocworkspace/James/server/database/settings_service.py`

### 设置存储

```python
# 设置文件路径
CONFIG_DIR = <SERVER_DIR>/config
SETTINGS_FILE = <CONFIG_DIR>/settings.json
```

### 默认设置

```json
{
  "proxy": "system",
  "enabled_knowledge": [],
  "enabled_knowledge_data": []
}
```

### API

```python
class SettingsService:
    def exists_settings(self) -> bool
    def get_settings(self) -> dict  # 合并默认值
    def get_raw_settings(self) -> dict
    def update_settings(self, data: dict) -> dict  # 深合并
    def get_proxy_config(self) -> str
    def get_enabled_knowledge_ids(self) -> list
    def get_enabled_knowledge_data(self) -> list
    def update_enabled_knowledge_data(self, list)
```

---

## 版本跟踪

**表**: `db_version`
```sql
CREATE TABLE db_version (
  version INTEGER PRIMARY KEY
)
```

迁移时更新此表记录当前版本。
