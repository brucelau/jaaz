# 08 - WebSocket (Socket.IO)

## 概述

使用 **Socket.IO AsyncServer** 实现实时双向通信，用于聊天流式输出和工具调用状态推送。

## 核心文件

| 文件 | 职责 |
|------|------|
| `web/websocket/manager.py` | Socket.IO AsyncServer 单例 |
| `web/websocket/handlers.py` | 事件处理器 |
| `web/websocket/emitter.py` | 广播辅助 |
| `main.py` | Socket.IO 挂载 |

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI 应用                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│         app.mount("/socket.io", socketio.ASGIApp(sio))       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Socket.IO AsyncServer                      │
│  - async_mode='asgi'                                      │
│  - cors_allowed_origins='*'                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Event Handlers                           │
│  - connect                                                 │
│  - join_session                                            │
│  - disconnect                                               │
│  - ping                                                    │
└─────────────────────────────────────────────────────────────┘
```

## Socket.IO 挂载

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/main.py`

```python
import socketio
from web.websocket.manager import sio

# 创建 ASGI App
sio_app = socketio.ASGIApp(sio)

# 挂载到 /socket.io
app.mount("/socket.io", sio_app)
```

## Server 配置

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/websocket/manager.py`

```python
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',      # 允许所有来源
    allow_upgrades=True,             # 允许 WebSocket 升级
    always_reject=False
)
```

## 事件处理器

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/websocket/handlers.py`

### connect

```python
async def connect(sid, environ, auth):
    token = auth.get('token')

    # 验证 local_ token
    if token and token.startswith('local_'):
        valid, user_info = validate_local_token(token)
        if valid:
            add_connection(sid, user_info, authenticated=True)
            await sio.emit('connected', {
                'sid': sid,
                'authenticated': True,
                'user': user_info
            })
            return

    # 未认证连接
    add_connection(sid, None, authenticated=False)
    await sio.emit('connected', {
        'sid': sid,
        'authenticated': False
    })
```

### join_session

```python
async def join_session(sid, data):
    conn_info = active_connections.get(sid)

    # 检查认证
    if not conn_info.get('authenticated'):
        await sio.emit('error', {'message': 'Unauthorized'})
        return

    session_id = data.get('session_id')

    # 检查 session 存在
    if not session_exists(session_id):
        await sio.emit('error', {'message': 'Session not found'})
        return

    # 进入 room
    sio.enter_room(sid, session_id)
    await sio.emit('session_joined', {'session_id': session_id})
```

### disconnect

```python
async def disconnect(sid):
    remove_connection(sid)
```

### ping

```python
async def ping(sid, data):
    await sio.emit('pong', data)
```

## 广播辅助

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/websocket/emitter.py`

### 广播 session_update

```python
async def broadcast_session_update(session_id: str, event_type: str, data: dict):
    """向特定 session room 广播"""
    await sio.emit('session_update', {
        'session_id': session_id,
        'type': event_type,
        **data
    }, room=session_id)
```

### 发送 WebSocket 消息

```python
async def send_to_websocket(sid: str, event: str, data: dict):
    """向特定连接发送"""
    await sio.emit(event, data, room=sid)
```

### 广播 init_done

```python
async def broadcast_init_done():
    """向所有连接广播初始化完成"""
    await sio.emit('init_done', {'status': 'ready'})
```

## Session Update 类型

后端主动推送到前端的事件类型：

| 类型 | 说明 | 触发时机 |
|------|------|----------|
| `Delta` | 文本增量 | AI 输出文本时 |
| `ToolCall` | 工具调用开始 | Agent 调用工具 |
| `ToolCallPendingConfirmation` | 工具待确认 | 需要用户确认 |
| `ToolCallConfirmed` | 工具已确认 | 用户确认后 |
| `ToolCallCancelled` | 工具已取消 | 用户取消后 |
| `ToolCallArguments` | 工具参数 | 工具执行中 |
| `ToolCallProgress` | 工具进度 | 长时间操作 |
| `ToolCallResult` | 工具结果 | 工具执行完成 |
| `ImageGenerated` | 图片生成完成 | 图片生成成功 |
| `VideoGenerated` | 视频生成完成 | 视频生成成功 |
| `AllMessages` | 全量消息 | 同步历史 |
| `Done` | 会话完成 | Agent 完成 |
| `Error` | 错误 | 发生错误 |
| `Info` | 信息 | 通知信息 |

## Room 管理

```
客户端                          服务端
  │                               │
  │──── join_session(id) ────────►│
  │                               │
  │                               │ sio.enter_room(sid, session_id)
  │                               │
  │◄─── session_joined ───────────│
  │                               │
  │                    ┌──────────┴──────────┐
  │                    │ 其他客户端加入       │
  │                    │ sio.enter_room      │
  │                    └──────────┬──────────┘
  │                               │
  │◄══ session_update (broadcast) ══│ (所有 room 成员收到)
  │                               │
```

## 主动推送示例

```python
# chat_service.py

async def handle_chat(request):
    # AI 流式输出
    async for event in agent.stream(messages):
        if event.type == 'chunk':
            # 推送文本增量
            await broadcast_session_update(
                session_id=request.session_id,
                event_type='Delta',
                data={'text': event.text}
            )
        elif event.type == 'tool_call':
            # 推送工具调用
            await broadcast_session_update(
                session_id=request.session_id,
                event_type='ToolCall',
                data={'id': event.tool_call_id, 'name': event.tool_name}
            )
```

## 客户端连接

```javascript
// 前端 socket.ts
const socket = io('http://localhost:57988', {
  path: '/socket.io',
  transports: ['websocket', 'polling'],
  auth: { token: getAccessToken() }
})

socket.on('connect', () => {
  // 加入 session
  socket.emit('join_session', { session_id })
})

socket.on('session_update', (data) => {
  // 处理不同类型
  switch(data.type) {
    case 'Delta': handleDelta(data) }
    case 'ToolCall': handleToolCall(data) }
    // ...
  }
})
```
