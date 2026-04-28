# 05 - 实时通信系统

## 概述

实时通信基于 **Socket.IO** 实现，用于 AI 聊天时的实时消息推送。

## 核心文件

| 文件 | 职责 |
|------|------|
| `lib/socket.ts` | Socket.IO 管理器类 |
| `contexts/socket.tsx` | Socket React Context |
| `lib/event.ts` | 事件总线 (mitt) |
| `types/socket.ts` | Socket 事件类型定义 |

## 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    后端 Server                               │
│              (Socket.IO mounted at /socket.io)                │
└─────────────────────────────────────────────────────────────┘
                              │
                    WebSocket / Polling
                              │
┌─────────────────────────────────────────────────────────────┐
│              SocketIOManager (lib/socket.ts)                 │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ • 连接管理 (重连、自动重连)                             │    │
│  │ • 事件处理 (session_update 分发到 EventBus)            │    │
│  │ • Token 认证                                         │    │
│  │ • 重连策略 (最多5次，1s 间隔)                          │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼ EventBus (mitt)
┌─────────────────────────────────────────────────────────────┐
│                    eventBus (lib/event.ts)                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 全局事件总线                                          │    │
│  │ 组件通过 on/off 订阅                                  │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  SocketContext (contexts/socket.tsx)          │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ React Context 封装                                   │    │
│  │ • 连接状态 (connected, connecting, error)            │    │
│  │ • socketManager 实例                                │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## SocketIOManager (lib/socket.ts)

### 类结构

```typescript
export class SocketIOManager {
  private socket: Socket | null = null
  private connected = false
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectDelay = 1000

  constructor(config: SocketConfig = {}) {
    if (config.autoConnect !== false) {
      this.connect()
    }
  }

  connect(serverUrl?: string): Promise<boolean>
  disconnect(): void
  joinSession(sessionId: string): void
  ping(data: unknown): void
  isConnected(): boolean
  getSocketId(): string | undefined
  getSocket(): Socket | null
}
```

### 连接配置

```typescript
interface SocketConfig {
  serverUrl?: string
  autoConnect?: boolean
}

// 连接选项
{
  path: '/socket.io',
  transports: ['websocket', 'polling'],  // 优先 websocket，降级 polling
  upgrade: true,
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  auth: { token }  // Token 认证
}
```

### 连接 URL

```typescript
// 开发环境
const serverUrl = 'http://localhost:57988'

// 生产环境
const serverUrl = window.location.origin
```

## SocketContext (contexts/socket.tsx)

### Context 类型

```typescript
interface SocketContextType {
  connected: boolean       // 连接状态
  socketId?: string       // Socket ID
  connecting: boolean     // 是否正在连接
  error?: string          // 错误信息
  socketManager: SocketIOManager | null
}
```

### Provider 实现

```typescript
export const SocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [connected, setConnected] = useState(false)
  const [socketId, setSocketId] = useState<string>()
  const [connecting, setConnecting] = useState(true)
  const [error, setError] = useState<string>()

  const socketManagerRef = useRef<SocketIOManager | null>(null)

  useEffect(() => {
    const initializeSocket = async () => {
      socketManagerRef.current = new SocketIOManager({
        serverUrl: process.env.NODE_ENV === 'development'
          ? 'http://localhost:57988'
          : window.location.origin,
        autoConnect: false
      })
      await socketManagerRef.current.connect()
      // 更新连接状态...
    }
    initializeSocket()
  }, [])

  return (
    <SocketContext.Provider value={{ connected, socketId, connecting, error, socketManager }}>
      {children}
    </SocketContext.Provider>
  )
}
```

## EventBus (lib/event.ts)

### 事件类型

```typescript
export type TEvents = {
  // ========== Socket 事件 - Start ==========
  'Socket::Session::Error': ISocket.SessionErrorEvent
  'Socket::Session::Done': ISocket.SessionDoneEvent
  'Socket::Session::Info': ISocket.SessionInfoEvent
  'Socket::Session::ImageGenerated': ISocket.SessionImageGeneratedEvent
  'Socket::Session::VideoGenerated': ISocket.SessionVideoGeneratedEvent
  'Socket::Session::Delta': ISocket.SessionDeltaEvent
  'Socket::Session::ToolCall': ISocket.SessionToolCallEvent
  'Socket::Session::ToolCallArguments': ISocket.SessionToolCallArgumentsEvent
  'Socket::Session::ToolCallResult': ISocket.SessionToolCallResultEvent
  'Socket::Session::AllMessages': ISocket.SessionAllMessagesEvent
  'Socket::Session::ToolCallProgress': ISocket.SessionToolCallProgressEvent
  'Socket::Session::ToolCallPendingConfirmation': ISocket.SessionToolCallPendingConfirmationEvent
  'Socket::Session::ToolCallConfirmed': ISocket.SessionToolCallConfirmedEvent
  'Socket::Session::ToolCallCancelled': ISocket.SessionToolCallCancelledEvent

  // ========== Canvas 事件 - Start ==========
  'Canvas::AddImagesToChat': TCanvasAddImagesToChatEvent
  'Canvas::MagicGenerate': TCanvasMagicGenerateEvent

  // ========== Material 事件 - Start ==========
  'Material::AddImagesToChat': TMaterialAddImagesToChatEvent
}

export const eventBus = mitt<TEvents>()
```

### 使用方式

```typescript
import { eventBus } from '@/lib/event'

// 监听
eventBus.on('Socket::Session::Delta', (data) => {
  console.log('Delta:', data.text)
})

// 触发
eventBus.emit('Canvas::AddImagesToChat', { fileId: 'xxx', ... })

// 取消监听
eventBus.off('Socket::Session::Delta', handler)
```

## Socket 事件流

### 1. 连接建立

```
后端 'connect' 事件
        │
        ▼
SocketIOManager.connect() Promise resolves
        │
        ▼
SocketContext 更新 connected = true
        │
        ▼
组件可使用 socketManager
```

### 2. 加入会话

```typescript
// 组件中
socketManager?.joinSession(sessionId)

// 发送
socket.emit('join_session', { session_id: sessionId })
```

### 3. 接收 AI 响应

```
后端推送 session_update 事件
        │
        ▼
SocketIOManager.handleSessionUpdate()
        │
        ▼
根据 type 分发到对应 EventBus 事件
        │
        ▼
组件监听并更新 UI
```

## Socket 事件类型详解

### session_update 子类型

| 类型 | EventBus Key | 说明 |
|------|-------------|------|
| `Delta` | `Socket::Session::Delta` | 文本增量 (AI 正在输入) |
| `ToolCall` | `Socket::Session::ToolCall` | 工具调用开始 |
| `ToolCallPendingConfirmation` | `Socket::Session::ToolCallPendingConfirmation` | 工具调用待确认 |
| `ToolCallConfirmed` | `Socket::Session::ToolCallConfirmed` | 工具调用已确认 |
| `ToolCallCancelled` | `Socket::Session::ToolCallCancelled` | 工具调用已取消 |
| `ToolCallArguments` | `Socket::Session::ToolCallArguments` | 工具调用参数 |
| `ToolCallProgress` | `Socket::Session::ToolCallProgress` | 工具调用进度 |
| `ToolCallResult` | `Socket::Session::ToolCallResult` | 工具调用结果 |
| `ImageGenerated` | `Socket::Session::ImageGenerated` | 图片生成完成 |
| `VideoGenerated` | `Socket::Session::VideoGenerated` | 视频生成完成 |
| `AllMessages` | `Socket::Session::AllMessages` | 全量消息同步 |
| `Done` | `Socket::Session::Done` | 会话完成 |
| `Error` | `Socket::Session::Error` | 错误 |
| `Info` | `Socket::Session::Info` | 信息通知 |

### Delta 事件 (AI 打字效果)

```typescript
// 后端推送
{ session_id: 'xxx', type: 'Delta', text: '你好' }

// EventBus
eventBus.emit('Socket::Session::Delta', { session_id: 'xxx', text: '你好' })

// 组件处理 - 追加到消息
setMessages(produce((prev) => {
  const last = prev.at(-1)
  if (last?.role === 'assistant' && !last.tool_calls) {
    last.content += '你好'  // 追加文本
  } else {
    prev.push({ role: 'assistant', content: '你好' })
  }
}))
```

### ToolCall 事件

```typescript
// 后端推送
{
  session_id: 'xxx',
  type: 'ToolCall',
  id: 'call_abc',
  name: 'generate_image'
}

// EventBus
eventBus.emit('Socket::Session::ToolCall', { session_id: 'xxx', id: 'call_abc', name: 'generate_image' })

// 组件处理 - 添加 tool_calls
setMessages(produce((prev) => {
  prev.push({
    role: 'assistant',
    content: '',
    tool_calls: [{
      type: 'function',
      function: { name: 'generate_image', arguments: '' },
      id: 'call_abc'
    }]
  })
}))
```

## 错误处理

### 连接错误

```typescript
// SocketContext
const handleConnectError = (error: Error) => {
  setError(error.message)
  setConnected(false)
}

// 显示重连提示
{socketManagerRef.current?.isMaxReconnectAttemptsReached()
  ? '最大重连次数已到达'
  : `连接错误，第 ${attempts}/5 次重试`}
```

### API 错误 (401)

```typescript
// getAuthStatus 中的处理
if (error.message === 'TOKEN_EXPIRED') {
  localStorage.removeItem('jaaz_access_token')
  localStorage.removeItem('jaaz_user_info')
  await clearJaazApiKey()
  return { status: 'logged_out', is_logged_in: false, tokenExpired: true }
}
```

## 重连机制

```typescript
// SocketIOManager
private maxReconnectAttempts = 5
private reconnectDelay = 1000

// socket.io 客户端自动重连
{
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000
}

// 最大重连次数检查
isMaxReconnectAttemptsReached(): boolean {
  return this.reconnectAttempts >= this.maxReconnectAttempts
}
```
