# 04 - 认证系统

## 概述

认证系统基于 **SQLite + bcrypt** 实现本地用户注册/登录，Token 存储在数据库中。

## 核心文件

| 文件 | 职责 |
|------|------|
| `web/services/auth_service.py` | 认证逻辑 (注册/登录/Token) |
| `web/routers/auth_router.py` | 认证 API 路由 |
| `web/websocket/handlers.py` | Socket.IO Token 验证 |
| `database/db_service.py` | 数据库操作 |

## 数据库表

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

## 认证流程

```
┌─────────────────────────────────────────────────────────┐
│                    用户注册 /api/auth/register             │
└─────────────────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────┐
│                auth_service.register()                     │
│  1. 检查 username/email 唯一性                            │
│  2. bcrypt.hashpw(password) 生成密码哈希                   │
│  3. 生成 user_id (uuid)                                  │
│  4. 生成 token = f"local_{uuid}"                        │
│  5. Token 7 天过期                                       │
│  6. 写入 auth_users + auth_tokens                        │
│  7. 返回 { token, user_info }                           │
└─────────────────────────────────────────────────────────┘
```

## Token 类型

| 前缀 | 类型 | 说明 |
|------|------|------|
| `local_` | 本地 Token | SQLite 存储，7天过期 |

## API 函数 (auth_service.py)

### register(username, email, password)

```python
def register(username: str, email: str, password: str):
    # 1. 检查唯一性
    # 2. bcrypt 哈希密码
    # 3. 生成 token
    # 4. 写入数据库
    return { "token": "local_xxx", "user_info": {...} }
```

### login(username, password)

```python
def login(username: str, password: str):
    # 1. 查询用户
    # 2. bcrypt.checkpw(password, hash)
    # 3. 生成新 token
    # 4. 返回 token + user_info
```

### refresh_token(token)

```python
def refresh_token(token: str):
    # 1. 查询 token
    # 2. 检查过期
    # 3. 删除旧 token
    # 4. 生成新 token
    # 5. 返回新 token + user_info
```

## Token 验证 (WebSocket)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/websocket/handlers.py`

```python
async def connect(sid, environ, auth):
    token = auth.get('token')

    if token and token.startswith('local_'):
        # 验证本地 token
        valid, user_info = validate_local_token(token)
        if valid:
            add_connection(sid, user_info, authenticated=True)
            await sio.emit('connected', {...})
            return

    # 未认证
    add_connection(sid, None, authenticated=False)
```

### validate_local_token(token)

```python
def validate_local_token(token: str):
    # 1. 查询 auth_tokens 表
    # 2. 检查 expires_at > now()
    # 3. 返回 (valid, user_info)
```

## Socket.IO 认证流程

```
客户端连接 Socket.IO
        │
        ▼
emit('connect', { auth: { token: 'local_xxx' } })
        │
        ▼
handlers.connect() 验证 token
        │
        ├── Token 有效 → authenticated = True
        │
        └── Token 无效/过期 → authenticated = False
        │
        ▼
emit('connected', { authenticated, user_info })
```

## join_session 权限检查

```python
async def join_session(sid, data):
    conn_info = active_connections.get(sid)

    # 必须已认证
    if not conn_info.get('authenticated'):
        await sio.emit('error', { message: 'Unauthorized' })
        return

    # 检查 session 是否存在
    session_id = data.get('session_id')
    if not session_exists(session_id):
        await sio.emit('error', { message: 'Session not found' })
        return

    # 进入 room
    sio.enter_room(sid, session_id)
```

## 密码安全

- 使用 **bcrypt** 哈希密码
- 永不存储明文密码
- Token 使用随机 UUID

## 相关配置

| 配置 | 路径 | 说明 |
|------|------|------|
| 数据库 | `DB_DIR/localmanus.db` | SQLite 数据库 |
| Token TTL | 7 天 | 固定 |
| 密码哈希 | bcrypt | 同步哈希 |
