# 10 - 数据流与组件关系

## 核心数据流

### 1. 聊天消息发送流程

```
┌──────────────────────────────────────────────────────────────────┐
│                         用户操作                                  │
│  用户在 ChatTextarea 输入文字，点击发送                            │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ChatInterface.onSendMessages                   │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │ 1. setPending('text') - 显示发送状态                        │   │
│  │ 2. setMessages(data) - 更新消息列表                        │   │
│  │ 3. sendMessages({ sessionId, canvasId, messages, ... })    │   │
│  │ 4. scrollToBottom() - 滚动到底部                           │   │
│  └────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    sendMessages API (api/chat.ts)                  │
│  POST /api/chat                                                  │
│  Headers: { Authorization: 'Bearer <token>' }                   │
│  Body: { session_id, canvas_id, messages, text_model, ... }     │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                         后端处理                                  │
│  1. 验证 Token                                                  │
│  2. 调用 AI Agent (LangGraph)                                    │
│  3. AI 实时推送 session_update 事件                              │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Socket session_update
┌──────────────────────────────────────────────────────────────────┐
│              SocketIOManager.handleSessionUpdate                   │
│  根据 type 分发到不同 EventBus 事件                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼ EventBus.emit
┌──────────────────────────────────────────────────────────────────┐
│                    ChatInterface 事件监听                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ Delta       │ │ ToolCall    │ │ Done        │  ...           │
│  │ (文本增量)   │ │ (工具调用)   │ │ (完成)       │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    更新 UI (setMessages)                          │
│  1. Delta: 追加文本到最后一条消息                                 │
│  2. ToolCall: 添加 tool_calls 到消息                             │
│  3. Done: setPending(false)                                      │
└──────────────────────────────────────────────────────────────────┘
```

### 2. Canvas 创建流程

```
┌──────────────────────────────────────────────────────────────────┐
│                         首页操作                                  │
│  用户在首页 ChatTextarea 输入描述，点击创建 Canvas                  │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      createCanvas API                            │
│  POST /api/canvas/create                                         │
│  Body: { name, canvas_id, messages, session_id, ... }           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      后端响应                                     │
│  { id: 'canvas_xxx' }                                           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      路由导航                                     │
│  window.location.href = `/canvas/canvas_xxx?sessionId=yyy`        │
│  或 navigate({ to: '/canvas/$id', params: { id: 'canvas_xxx' } }) │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    Canvas 页面加载                                │
│  useEffect(() => { fetchCanvas(id) }, [id])                      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      getCanvas API                               │
│  GET /api/canvas/:id → { data, name, sessions }                 │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    渲染 Canvas 页面                              │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐          │
│  │ CanvasHeader  │ │ CanvasExcali  │ │ ChatInterface │          │
│  │ (名称显示)     │ │ (画布渲染)     │ │ (聊天面板)     │          │
│  └───────────────┘ └───────────────┘ └───────────────┘          │
└──────────────────────────────────────────────────────────────────┘
```

### 3. 工具调用流程

```
┌──────────────────────────────────────────────────────────────────┐
│                      AI 决定调用工具                               │
│  AI 返回 tool_call                                                │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Socket (ToolCall)
┌──────────────────────────────────────────────────────────────────┐
│              SocketIOManager → EventBus                          │
│  emit('Socket::Session::ToolCall', { id, name, ... })           │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    ChatInterface 处理                            │
│  1. 检查消息是否已存在                                            │
│  2. 添加 tool_calls 到 messages                                   │
│  3. 添加到 expandingToolCalls                                    │
│  4. 显示 ToolCallTag                                             │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      用户确认/取消                                │
│  点击确认 → POST /api/tool_confirmation { confirmed: true }      │
│  点击取消 → POST /api/tool_confirmation { confirmed: false }      │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Socket (ToolCallConfirmed/Cancelled)
┌──────────────────────────────────────────────────────────────────┐
│                    后端执行/取消工具                               │
│  执行工具 → 推送 ToolCallResult                                   │
└──────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│              ChatInterface 显示工具结果                           │
│  更新 tool_call.result                                            │
└──────────────────────────────────────────────────────────────────┘
```

---

## 组件调用关系

### App 组件树

```
App
├── ThemeProvider
│   └── PersistQueryClientProvider
│       └── QueryClient
├── AuthProvider
│   └── AuthContext
├── ConfigsProvider
│   └── ConfigsContext
├── RouterProvider
│   └── routeTree
│       └── RootRoute
│           ├── IndexRoute (/)
│           │   └── Home
│           │       ├── TopMenu
│           │       ├── ChatTextarea (首页简单聊天)
│           │       └── CanvasList
│           │
│           ├── CanvasIdRoute (/canvas/:id)
│           │   └── Canvas
│           │       ├── CanvasProvider
│           │       ├── CanvasHeader
│           │       ├── ResizablePanelGroup
│           │       │   ├── ResizablePanel (75%)
│           │       │   │   ├── CanvasExcali
│           │       │   │   ├── CanvasMenu
│           │       │   │   └── CanvasPopbar
│           │       │   │
│           │       │   ├── ResizableHandle
│           │       │   │
│           │       │   └── ResizablePanel (25%)
│           │       │       └── ChatInterface
│           │       │           ├── SessionSelector
│           │       │           ├── ScrollArea
│           │       │           │   └── Messages
│           │       │           │       ├── MessageRegular
│           │       │           │       ├── ToolCallTag
│           │       │           │       └── MixedContent
│           │       │           └── ChatTextarea
│           │       │
│           │       └── CanvasPopbar
│           │           └── CanvasMagicGenerator
│           │
│           ├── KnowledgeRoute (/knowledge)
│           │   └── Knowledge
│           │       ├── KnowledgeList
│           │       └── KnowledgeEditor
│           │
│           ├── Agent_studioRoute (/agent_studio)
│           │   └── AgentStudio
│           │       ├── AgentNode
│           │       └── AgentSettings
│           │
│           └── AssetsRoute (/assets)
│               └── MaterialManager
│                   └── FilePreviewModal
│
├── UpdateNotificationDialog
├── SettingsDialog
└── LoginDialog
```

### Context 依赖关系

```
AuthContext
    └── useAuth() → authStatus, refreshAuth
        └── used by: App, LoginDialog, ChatInterface, ...

SocketContext
    └── useSocket() → socketManager, connected, socketId
        └── used by: ChatInterface, App

ConfigsContext
    └── useConfigs() → initCanvas, setInitCanvas
        └── used by: ChatInterface, App

CanvasContext
    └── useCanvas() → canvasData, setCanvasData
        └── used by: CanvasExcali, Canvas 相关组件
```

### API 层依赖关系

```
api/auth.ts
    ├── getAccessToken()
    ├── authenticatedFetch()
    └── used by: 所有需要认证的 API

api/chat.ts
    └── authenticatedFetch
        └── used by: ChatInterface

api/canvas.ts
    └── authenticatedFetch
        └── used by: Canvas 页面, Home

api/model.ts
    └── used by: ModelSelector, ConfigsProvider

api/knowledge.ts
    └── authenticatedFetch
        └── used by: Knowledge 组件

api/config.ts
    ├── getConfig()
    ├── updateConfig()
    └── used by: AuthContext (登录/登出时更新 James api_key)
```

---

## 状态管理架构

### localStorage Keys

| Key | 类型 | 说明 |
|-----|------|------|
| `James_access_token` | string | 认证 Token |
| `James_user_info` | string (JSON) | 用户信息 |
| `system_prompt` | string | 自定义系统提示词 |

### IndexedDB (React Query 缓存)

```
Database: react-query-db
└── Store: cache
    └── Key: react-query-cache
        └── Value: Query 缓存数据
```

### Context 状态

```
AuthContext
├── authStatus: AuthStatus
│   ├── status: 'logged_out' | 'pending' | 'logged_in'
│   ├── is_logged_in: boolean
│   ├── user_info?: UserInfo
│   └── tokenExpired?: boolean
└── isLoading: boolean

SocketContext
├── connected: boolean
├── socketId?: string
├── connecting: boolean
├── error?: string
└── socketManager: SocketIOManager | null

ConfigsContext
├── initCanvas: boolean
├── textModel: Model
├── toolList: ToolInfo[]
└── systemPrompt: string

CanvasContext
├── canvasData: CanvasData
└── setCanvasData: ...
```

---

## 事件流汇总

### Socket → Component

```
Socket event
    │
    ▼
SocketIOManager.handleSessionUpdate()
    │
    ▼ EventBus.emit()
Socket::Session::* 事件
    │
    ▼ eventBus.on()
ChatInterface / 其他组件
    │
    ▼ setState()
UI 更新
```

### Component → Socket

```
用户操作 (点击确认)
    │
    ▼
API 调用 (tool_confirmation)
    │
    ▼
后端执行工具
    │
    ▼ Socket
session_update (ToolCallResult / Done)
    │
    ▼
UI 更新
```

### Canvas → Chat

```
用户操作 Canvas
    │
    ▼
eventBus.emit('Canvas::AddImagesToChat', data)
    │
    ▼ eventBus.on()
ChatInterface 监听
    │
    ▼
添加到 messages
```
