# 11 - TypeScript 类型定义

## 概述

本文档记录前端核心 TypeScript 类型定义。

## 核心类型文件

| 文件 | 职责 |
|------|------|
| `types/types.ts` | 全局类型定义 |
| `types/socket.ts` | Socket 事件类型 |
| `api/*.ts` | 各模块类型定义 |

---

## types/types.ts

### Message 消息

```typescript
interface Message {
  id?: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string | ContentBlock[]
  tool_calls?: ToolCall[]
  tool_call_id?: string
  name?: string
}

interface ContentBlock {
  type: 'text' | 'image_url'
  text?: string
  image_url?: {
    url: string
    detail?: 'low' | 'high' | 'auto'
  }
}

interface ToolCall {
  id: string
  type: 'function'
  function: {
    name: string
    arguments: string
  }
  result?: any  // 工具执行结果
}
```

### Session 会话

```typescript
interface Session {
  id: string
  title: string
  created_at: string
  updated_at: string
  model: string
  provider: string
}
```

### Model 模型

```typescript
interface Model {
  provider: string
  model: string
  url?: string
}
```

### CanvasData 画布数据

```typescript
interface CanvasData {
  elements: any[]   // Excalidraw elements
  appState: any     // Excalidraw app state
}
```

### LLMConfig

```typescript
interface LLMConfig {
  provider: string
  api_key?: string
  base_url?: string
  model?: string
  [key: string]: any
}
```

---

## types/socket.ts

### SessionUpdateEvent

```typescript
interface SessionUpdateEvent {
  session_id?: string
  type: SessionEventType
  [key: string]: any
}

enum SessionEventType {
  Delta = 'Delta',
  ToolCall = 'ToolCall',
  ToolCallPendingConfirmation = 'ToolCallPendingConfirmation',
  ToolCallConfirmed = 'ToolCallConfirmed',
  ToolCallCancelled = 'ToolCallCancelled',
  ToolCallArguments = 'ToolCallArguments',
  ToolCallProgress = 'ToolCallProgress',
  ToolCallResult = 'ToolCallResult',
  ImageGenerated = 'ImageGenerated',
  VideoGenerated = 'VideoGenerated',
  AllMessages = 'AllMessages',
  Done = 'Done',
  Error = 'Error',
  Info = 'Info',
}
```

### 具体事件类型

```typescript
interface SessionDeltaEvent {
  session_id: string
  type: 'Delta'
  text: string
}

interface SessionToolCallEvent {
  session_id: string
  type: 'ToolCall'
  id: string
  name: string
}

interface SessionToolCallPendingConfirmationEvent {
  session_id: string
  type: 'ToolCallPendingConfirmation'
  id: string
  name: string
  arguments: string
}

interface SessionToolCallConfirmedEvent {
  session_id: string
  type: 'ToolCallConfirmed'
  id: string
}

interface SessionToolCallCancelledEvent {
  session_id: string
  type: 'ToolCallCancelled'
  id: string
}

interface SessionToolCallArgumentsEvent {
  session_id: string
  type: 'ToolCallArguments'
  id: string
  text: string
}

interface SessionToolCallProgressEvent {
  session_id: string
  type: 'ToolCallProgress'
  id: string
  progress: number
  message?: string
}

interface SessionToolCallResultEvent {
  session_id: string
  type: 'ToolCallResult'
  id: string
  message: {
    role: 'tool'
    content: string
  }
}

interface SessionImageGeneratedEvent {
  session_id: string
  type: 'ImageGenerated'
  id: string
  image_url: string
  width?: number
  height?: number
  canvas_id?: string
}

interface SessionVideoGeneratedEvent {
  session_id: string
  type: 'VideoGenerated'
  id: string
  video_url: string
  duration?: number
  canvas_id?: string
}

interface SessionAllMessagesEvent {
  session_id: string
  type: 'AllMessages'
  messages: Message[]
}

interface SessionDoneEvent {
  session_id: string
  type: 'Done'
}

interface SessionErrorEvent {
  session_id: string
  type: 'Error'
  error: string
}

interface SessionInfoEvent {
  session_id: string
  type: 'Info'
  info: string
}
```

---

## api/auth.ts

### AuthStatus

```typescript
interface AuthStatus {
  status: 'logged_out' | 'pending' | 'logged_in'
  is_logged_in: boolean
  user_info?: UserInfo
  tokenExpired?: boolean
}

interface UserInfo {
  id: string
  username: string
  email: string
  image_url?: string
  provider?: string
  created_at?: string
  updated_at?: string
}

interface DeviceAuthResponse {
  status: string
  code: string
  expires_at: string
  message: string
}

interface DeviceAuthPollResponse {
  status: 'pending' | 'authorized' | 'expired' | 'error'
  message?: string
  token?: string
  user_info?: UserInfo
}
```

---

## api/model.ts

```typescript
interface ModelInfo {
  provider: string
  model: string
  type: 'text' | 'image' | 'tool' | 'video'
  url: string
}

interface ToolInfo {
  provider: string
  id: string
  display_name?: string | null
  type?: 'image' | 'tool' | 'video'
}
```

---

## api/knowledge.ts

```typescript
interface KnowledgeBase {
  id: string
  user_id: string
  name: string
  description: string | null
  cover: string | null
  is_public: boolean
  created_at: string
  updated_at: string
  content?: string
}

interface Pagination {
  current_page: number
  page_size: number
  total_count: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

interface KnowledgeListResponse {
  success: boolean
  data: {
    list: KnowledgeBase[]
    pagination: Pagination
    is_admin: boolean
  }
  message: string
}

interface ApiResponse {
  success: boolean
  message: string
  error?: string
  details?: string
}
```

---

## api/canvas.ts

```typescript
interface ListCanvasesResponse {
  id: string
  name: string
  description?: string
  thumbnail?: string
  created_at: string
}

interface CreateCanvasPayload {
  name: string
  canvas_id: string
  messages: Message[]
  session_id: string
  text_model: {
    provider: string
    model: string
    url: string
  }
  tool_list: ToolInfo[]
  system_prompt: string
}

interface GetCanvasResponse {
  data: CanvasData
  name: string
  sessions: Session[]
}

interface SaveCanvasPayload {
  data: CanvasData
  thumbnail: string
}
```

---

## lib/event.ts

### 事件总线事件类型

```typescript
type TCanvasAddImagesToChatEvent = {
  fileId: string
  base64?: string
  width: number
  height: number
}[]

type TCanvasMagicGenerateEvent = {
  fileId: string
  base64: string
  width: number
  height: number
  timestamp: string
}

type TMaterialAddImagesToChatEvent = {
  filePath: string
  fileName: string
  fileType: string
  width?: number
  height?: number
}[]

type TEvents = {
  // Socket 事件
  'Socket::Session::Error': SessionErrorEvent
  'Socket::Session::Done': SessionDoneEvent
  'Socket::Session::Info': SessionInfoEvent
  'Socket::Session::ImageGenerated': SessionImageGeneratedEvent
  'Socket::Session::VideoGenerated': SessionVideoGeneratedEvent
  'Socket::Session::Delta': SessionDeltaEvent
  'Socket::Session::ToolCall': SessionToolCallEvent
  'Socket::Session::ToolCallArguments': SessionToolCallArgumentsEvent
  'Socket::Session::ToolCallResult': SessionToolCallResultEvent
  'Socket::Session::AllMessages': SessionAllMessagesEvent
  'Socket::Session::ToolCallProgress': SessionToolCallProgressEvent
  'Socket::Session::ToolCallPendingConfirmation': SessionToolCallPendingConfirmationEvent
  'Socket::Session::ToolCallConfirmed': SessionToolCallConfirmedEvent
  'Socket::Session::ToolCallCancelled': SessionToolCallCancelledEvent

  // Canvas 事件
  'Canvas::AddImagesToChat': TCanvasAddImagesToChatEvent
  'Canvas::MagicGenerate': TCanvasMagicGenerateEvent

  // Material 事件
  'Material::AddImagesToChat': TMaterialAddImagesToChatEvent
}
```

---

## PendingType

```typescript
type PendingType = 'text' | 'tool' | 'image'

// ChatInterface 中的状态
const [pending, setPending] = useState<PendingType | false>(false)
```

---

## ToolCallFunctionName

```typescript
type ToolCallFunctionName =
  | 'generate_image'
  | 'prompt_user_multi_choice'
  | 'prompt_user_single_choice'
  | 'write_plan'
  | 'finish'
```
