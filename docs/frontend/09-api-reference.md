# 09 - API 参考手册

## 概述

本手册详细说明前端所有 API 调用的接口定义、请求参数和响应格式。

**基础配置**:
```typescript
const BASE_API_URL = 'http://127.0.0.1:57988'
```

---

## 认证 API (api/auth.ts)

### auth_register

用户注册。

```typescript
auth_register(
  username: string,
  email: string,
  password: string
): Promise<{ token: string, user_info: UserInfo }>
```

| 参数 | 类型 | 说明 |
|------|------|------|
| username | string | 用户名 |
| email | string | 邮箱 |
| password | string | 密码 |

**请求**: `POST /api/auth/register`
```json
{ "username": "xxx", "email": "xxx", "password": "xxx" }
```

**响应**:
```json
{ "token": "local_xxx", "user_info": { "id": "xxx", "username": "xxx", ... } }
```

---

### auth_login

用户名密码登录。

```typescript
auth_login(
  username: string,
  password: string
): Promise<{ token: string, user_info: UserInfo }>
```

**请求**: `POST /api/auth/login`
```json
{ "username": "xxx", "password": "xxx" }
```

---

### startDeviceAuth

启动设备码登录。

```typescript
startDeviceAuth(): Promise<DeviceAuthResponse>

interface DeviceAuthResponse {
  status: string
  code: string
  expires_at: string
  message: string
}
```

**请求**: `POST /api/device/auth`

**响应**:
```json
{ "status": "pending", "code": "ABC123", "expires_at": "2024-01-01T00:05:00Z", "message": "..." }
```

---

### pollDeviceAuth

轮询设备码授权状态。

```typescript
pollDeviceAuth(deviceCode: string): Promise<DeviceAuthPollResponse>

interface DeviceAuthPollResponse {
  status: 'pending' | 'authorized' | 'expired' | 'error'
  message?: string
  token?: string
  user_info?: UserInfo
}
```

**请求**: `GET /api/device/poll?code=ABC123`

**响应** (authorized):
```json
{ "status": "authorized", "token": "xxx", "user_info": {...} }
```

---

### getAuthStatus

获取认证状态 (含自动 Token 刷新)。

```typescript
getAuthStatus(): Promise<AuthStatus>

interface AuthStatus {
  status: 'logged_out' | 'pending' | 'logged_in'
  is_logged_in: boolean
  user_info?: UserInfo
  tokenExpired?: boolean
}
```

---

### getAccessToken

获取存储的 Token。

```typescript
getAccessToken(): string | null
```

---

### authenticatedFetch

带 Token 的 fetch 封装。

```typescript
authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response>
```

---

### refreshToken

刷新 Token。

```typescript
refreshToken(currentToken: string): Promise<string>  // 返回新 token
```

---

### logout

登出。

```typescript
logout(): Promise<{ status: string; message: string }>
```

---

## 聊天 API (api/chat.ts)

### getChatSession

获取会话消息历史。

```typescript
getChatSession(sessionId: string): Promise<Message[]>
```

**请求**: `GET /api/chat_session/:sessionId`

---

### sendMessages

发送消息。

```typescript
sendMessages(payload: {
  sessionId: string
  canvasId: string
  newMessages: Message[]
  textModel: Model
  toolList: ToolInfo[]
  systemPrompt: string | null
}): Promise<Message[]>
```

**请求**: `POST /api/chat`
```json
{
  "session_id": "xxx",
  "canvas_id": "xxx",
  "messages": [...],
  "text_model": { "provider": "openai", "model": "gpt-4o" },
  "tool_list": [...],
  "system_prompt": "..."
}
```

---

### cancelChat

取消正在进行的聊天。

```typescript
cancelChat(sessionId: string): Promise<any>
```

**请求**: `POST /api/cancel/:sessionId`

---

## Canvas API (api/canvas.ts)

### listCanvases

列出所有 Canvas。

```typescript
listCanvases(): Promise<ListCanvasesResponse[]>

interface ListCanvasesResponse {
  id: string
  name: string
  description?: string
  thumbnail?: string
  created_at: string
}
```

**请求**: `GET /api/canvas/list`

---

### createCanvas

创建新 Canvas。

```typescript
createCanvas(data: {
  name: string
  canvas_id: string
  messages: Message[]
  session_id: string
  text_model: { provider: string; model: string; url: string }
  tool_list: ToolInfo[]
  system_prompt: string
}): Promise<{ id: string }>
```

**请求**: `POST /api/canvas/create`

---

### getCanvas

获取 Canvas 详情。

```typescript
getCanvas(id: string): Promise<{
  data: CanvasData
  name: string
  sessions: Session[]
}>
```

**请求**: `GET /api/canvas/:id`

---

### saveCanvas

保存 Canvas。

```typescript
saveCanvas(
  id: string,
  payload: { data: CanvasData; thumbnail: string }
): Promise<void>
```

**请求**: `POST /api/canvas/:id/save`

---

### renameCanvas

重命名 Canvas。

```typescript
renameCanvas(id: string, name: string): Promise<void>
```

**请求**: `POST /api/canvas/:id/rename`
```json
{ "name": "新名称" }
```

---

### deleteCanvas

删除 Canvas。

```typescript
deleteCanvas(id: string): Promise<void>
```

**请求**: `DELETE /api/canvas/:id/delete`

---

## 模型 API (api/model.ts)

### listModels

获取模型和工具列表。

```typescript
listModels(): Promise<{
  llm: ModelInfo[]
  tools: ToolInfo[]
}>

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

**请求**:
- `GET /api/list_models`
- `GET /api/list_tools`

---

## 知识库 API (api/knowledge.ts)

### getKnowledgeList

获取知识库列表 (分页)。

```typescript
getKnowledgeList(params?: {
  pageSize?: number
  pageNumber?: number
  search?: string
}): Promise<KnowledgeListResponse>
```

**请求**: `GET /api/knowledge/list?pageSize=10&pageNumber=1&search=xxx`

---

### getKnowledgeById

获取知识库详情。

```typescript
getKnowledgeById(id: string): Promise<KnowledgeBase>
```

**请求**: `GET /api/knowledge/:id`

---

### createKnowledge

创建知识库。

```typescript
createKnowledge(data: {
  name: string
  description?: string
  cover?: string
  is_public?: boolean
  content?: string
}): Promise<ApiResponse>
```

**请求**: `POST /api/knowledge/create`

---

### updateKnowledge

更新知识库。

```typescript
updateKnowledge(
  id: string,
  data: Partial<{
    name: string
    description: string
    cover: string
    is_public: boolean
    content: string
  }>
): Promise<ApiResponse>
```

**请求**: `PUT /api/knowledge/:id`

---

### deleteKnowledge

删除知识库。

```typescript
deleteKnowledge(id: string): Promise<ApiResponse>
```

**请求**: `DELETE /api/knowledge/:id`

---

### saveEnabledKnowledgeDataToSettings

保存启用的知识库数据到设置。

```typescript
saveEnabledKnowledgeDataToSettings(knowledgeData: KnowledgeBase[]): Promise<ApiResponse>
```

**请求**: `POST /api/settings`
```json
{ "enabled_knowledge_data": [...] }
```

---

## 配置 API (api/config.ts)

### getConfigExists

检查配置是否存在。

```typescript
getConfigExists(): Promise<{ exists: boolean }>
```

**请求**: `GET /api/config/exists`

---

### getConfig

获取配置。

```typescript
getConfig(): Promise<{ [key: string]: LLMConfig }>
```

**请求**: `GET /api/config`

---

### updateConfig

更新配置。

```typescript
updateConfig(config: { [key: string]: LLMConfig }): Promise<{ status: string; message: string }>
```

**请求**: `POST /api/config`

---

### updateJaazApiKey

登录后更新 jaaz provider 的 api_key。

```typescript
updateJaazApiKey(token: string): Promise<void>
```

---

### clearJaazApiKey

登出后清除 jaaz provider 的 api_key。

```typescript
clearJaazApiKey(): Promise<void>
```

---

## 设置 API (api/settings.ts)

### getSettings

获取设置。

### updateSettings

更新设置。

---

## 上传 API (api/upload.ts)

### uploadFile

上传文件。

```typescript
uploadFile(file: File, onProgress?: (progress: number) => void): Promise<UploadResponse>
```

---

## 魔法 API (api/magic.ts)

### generateMagic

触发魔法生成功能。

---

## 计费 API (api/billing.ts)

### getBalance

获取用户余额。

```typescript
getBalance(): Promise<{ balance: number }>
```

---

## 前端 → 后端 API 路径映射

| 前端调用路径 | 后端路由 | 说明 |
|-------------|---------|------|
| `/api/canvas/list` | `/api/canvas/list` | Canvas 列表 |
| `/api/canvas/create` | `/api/canvas/create` | 创建 Canvas |
| `/api/canvas/:id` | `/api/canvas/:id` | 获取 Canvas |
| `/api/canvas/:id/save` | `/api/canvas/:id/save` | 保存 Canvas |
| `/api/canvas/:id/rename` | `/api/canvas/:id/rename` | 重命名 |
| `/api/canvas/:id/delete` | `/api/canvas/:id/delete` | 删除 |
| `/api/chat_session/:id` | `/api/chat_session/:session_id` | 会话消息 |
| `/api/chat` | `/api/chat` | 发送消息 |
| `/api/cancel/:id` | `/api/cancel/:session_id` | 取消聊天 |
| `/api/list_models` | `/api/list_models` | 模型列表 |
| `/api/list_tools` | `/api/list_tools` | 工具列表 |
| `/api/knowledge/list` | `/api/knowledge/list` | 知识库列表 |
| `/api/knowledge/:id` | `/api/knowledge/:id` | 知识库详情 |
| `/api/knowledge/create` | `/api/knowledge/create` | 创建知识库 |
| `/api/settings` | `/api/settings` | 设置 (本地) |
| `/api/config` | `/api/config` | Provider 配置 |
| `/api/config/exists` | `/api/config/exists` | 配置是否存在 |
| `/api/auth/register` | `/api/auth/register` | 注册 |
| `/api/auth/login` | `/api/auth/login` | 登录 |
| `/api/auth/refresh-token` | `/api/auth/refresh-token` | 刷新 Token |
| `/api/device/auth` | `/api/device/auth` | 设备码认证 |
| `/api/device/poll` | `/api/device/poll` | 轮询设备码 |
| `/api/device/refresh-token` | `/api/device/refresh-token` | 设备 Token 刷新 |
| `/api/tool_confirmation` | `/api/tool_confirmation` | 工具调用确认 |
