# 06 - 聊天系统

## 概述

聊天系统是 Jaaz 的核心功能，通过 Socket.IO 与后端 AI Agent 通信，支持实时消息流式输出和工具调用。

## 核心文件

| 文件 | 行数 | 职责 |
|------|------|------|
| `components/chat/Chat.tsx` | 777 | 核心聊天组件 |
| `api/chat.ts` | 45 | 聊天 API |
| `components/chat/ChatTextarea.tsx` | - | 消息输入框 |
| `components/chat/SessionSelector.tsx` | - | 会话选择器 |

## ChatInterface 组件

### Props

```typescript
interface ChatInterfaceProps {
  canvasId: string           // Canvas ID
  sessionList: Session[]     // 会话列表
  setSessionList: Dispatch   // 更新会话列表
  sessionId: string          // 当前会话 ID
}
```

### 内部状态

```typescript
interface ChatState {
  session: Session | null                    // 当前会话
  messages: Message[]                       // 消息列表
  pending: PendingType | false             // pending 状态 ('text' | 'tool' | 'image' | false)
  expandingToolCalls: string[]              // 展开的工具调用 ID 列表
  pendingToolConfirmations: string[]         // 待确认的工具调用 ID 列表
}
```

## 消息渲染流程

```
用户输入 → ChatTextarea.onSendMessages
                          │
                          ▼
                  sendMessages API
                          │
                          ▼
                  Socket 连接后推送
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
        session_update           session_update
        (type: Delta)            (type: Done)
              │                       │
              ▼                       ▼
        追加文本到              pending = false
        messages               渲染完成
              │
              ▼
        渲染消息列表
```

## Socket 事件处理

### 事件订阅 (useEffect)

```typescript
useEffect(() => {
  // 各种事件监听
  eventBus.on('Socket::Session::Delta', handleDelta)
  eventBus.on('Socket::Session::ToolCall', handleToolCall)
  eventBus.on('Socket::Session::ToolCallPendingConfirmation', handleToolCallPendingConfirmation)
  eventBus.on('Socket::Session::ToolCallConfirmed', handleToolCallConfirmed)
  eventBus.on('Socket::Session::ToolCallCancelled', handleToolCallCancelled)
  eventBus.on('Socket::Session::ToolCallArguments', handleToolCallArguments)
  eventBus.on('Socket::Session::ToolCallResult', handleToolCallResult)
  eventBus.on('Socket::Session::ImageGenerated', handleImageGenerated)
  eventBus.on('Socket::Session::AllMessages', handleAllMessages)
  eventBus.on('Socket::Session::Done', handleDone)
  eventBus.on('Socket::Session::Error', handleError)
  eventBus.on('Socket::Session::Info', handleInfo)

  return () => {
    // 取消所有监听
    eventBus.off('Socket::Session::Delta', handleDelta)
    // ...
  }
})
```

### Delta 处理 (AI 打字效果)

```typescript
const handleDelta = useCallback((data: TEvents['Socket::Session::Delta']) => {
  if (data.session_id && data.session_id !== sessionId) return

  setPending('text')
  setMessages(produce((prev) => {
    const last = prev.at(-1)
    if (last?.role === 'assistant' && !last.tool_calls) {
      // 追加到上一条消息
      if (typeof last.content === 'string') {
        last.content += data.text
      }
    } else {
      // 创建新消息
      prev.push({ role: 'assistant', content: data.text })
    }
  }))
  scrollToBottom()
}, [sessionId, scrollToBottom])
```

### ToolCall 处理

```typescript
const handleToolCall = useCallback((data: TEvents['Socket::Session::ToolCall']) => {
  if (data.session_id && data.session_id !== sessionId) return

  // 检查是否已存在
  const existToolCall = messages.find(m =>
    m.role === 'assistant' && m.tool_calls?.find(t => t.id == data.id)
  )
  if (existToolCall) return

  setMessages(produce((prev) => {
    prev.push({
      role: 'assistant',
      content: '',
      tool_calls: [{
        type: 'function',
        function: { name: data.name, arguments: '' },
        id: data.id
      }]
    })
  }))

  // 添加到展开列表
  setExpandingToolCalls(prev => [...prev, data.id])
}, [sessionId, messages])
```

### ToolCallArguments 处理 (参数追加)

```typescript
const handleToolCallArguments = useCallback((data: TEvents['Socket::Session::ToolCallArguments']) => {
  if (data.session_id && data.session_id !== sessionId) return

  setMessages(produce((prev) => {
    // 找到对应的 tool_call
    const lastMessage = prev.find(m =>
      m.role === 'assistant' && m.tool_calls?.find(t => t.id == data.id)
    )
    if (lastMessage) {
      const toolCall = lastMessage.tool_calls?.find(t => t.id == data.id)
      if (toolCall && !pendingToolConfirmations.includes(data.id)) {
        toolCall.function.arguments += data.text
      }
    }
  }))
}, [sessionId, pendingToolConfirmations])
```

### ToolCallResult 处理

```typescript
const handleToolCallResult = useCallback((data: TEvents['Socket::Session::ToolCallResult']) => {
  if (data.session_id && data.session_id !== sessionId) return

  // 更新对应 tool_call 的 result
  setMessages(produce((prev) => {
    prev.forEach(m => {
      if (m.role === 'assistant' && m.tool_calls) {
        m.tool_calls.forEach(t => {
          if (t.id === data.id) {
            t.result = data.message.content
          }
        })
      }
    })
  }))
}, [sessionId])
```

## 发送消息流程

```typescript
const onSendMessages = useCallback((data: Message[], configs: { textModel: Model; toolList: ToolInfo[] }) => {
  setPending('text')
  setMessages(data)

  sendMessages({
    sessionId: sessionId!,
    canvasId: canvasId,
    newMessages: data,
    textModel: configs.textModel,
    toolList: configs.toolList,
    systemPrompt: localStorage.getItem('system_prompt') || DEFAULT_SYSTEM_PROMPT,
  })

  // 更新 URL
  window.history.pushState({}, '', `/canvas/${canvasId}?sessionId=${sessionId}`)
}, [canvasId, sessionId])
```

## 会话管理

### 初始化会话

```typescript
const initChat = useCallback(async () => {
  if (!sessionId) return

  // 加入 Socket 会话
  socketManager?.joinSession(sessionId)

  // 获取历史消息
  const resp = await fetch('/api/chat_session/' + sessionId)
  const data = await resp.json()
  setMessages(data?.length ? data : [])

  if (data?.length > 0) {
    setInitCanvas(false)
  }
}, [sessionId, socketManager, setInitCanvas])
```

### 新建会话

```typescript
const onClickNewChat = () => {
  const newSession: Session = {
    id: nanoid(),
    title: t('chat:newChat'),
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    model: session?.model || 'gpt-4o',
    provider: session?.provider || 'openai',
  }
  setSessionList(prev => [...prev, newSession])
  onSelectSession(newSession.id)
}
```

### 切换会话

```typescript
const onSelectSession = (sessionId: string) => {
  setSession(sessionList.find(s => s.id === sessionId) || null)
  window.history.pushState({}, '', `/canvas/${canvasId}?sessionId=${sessionId}`)
}
```

## 工具调用确认

### 确认弹窗

用户点击确认或取消时：

```typescript
// 确认
fetch('/api/tool_confirmation', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    session_id: sessionId,
    tool_call_id: toolCall.id,
    confirmed: true
  })
})

// 取消
fetch('/api/tool_confirmation', {
  method: 'POST',
  body: JSON.stringify({
    session_id: sessionId,
    tool_call_id: toolCall.id,
    confirmed: false
  })
})
```

### 取消状态显示

```typescript
setMessages(produce((prev) => {
  prev.forEach(msg => {
    if (msg.role === 'assistant' && msg.tool_calls) {
      msg.tool_calls.forEach(tc => {
        if (tc.id === data.id) {
          tc.result = '工具调用已取消'  // 标记取消
        }
      })
    }
  })
}))
```

## 消息类型

### Message 接口

```typescript
interface Message {
  id?: string
  role: 'user' | 'assistant' | 'system' | 'tool'
  content: string | ContentBlock[]
  tool_calls?: ToolCall[]
  tool_call_id?: string
  name?: string
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

### 消息渲染

```typescript
{messages.map((message, idx) => (
  <div key={idx}>
    {/* 普通文本消息 */}
    {typeof message.content === 'string' && message.role !== 'tool' && (
      <MessageRegular message={message} content={message.content} />
    )}

    {/* 工具结果 (合并后隐藏) */}
    {message.role === 'tool' && mergedToolCallIds.current.includes(message.tool_call_id) && (
      <></>
    )}

    {/* 混合内容 (图片+文本) */}
    {Array.isArray(message.content) && (
      <>
        <MixedContentImages contents={message.content} />
        <MixedContentText message={message} contents={message.content} />
      </>
    )}

    {/* 工具调用标签 */}
    {message.role === 'assistant' && message.tool_calls?.map(toolCall => (
      <ToolCallTag key={toolCall.id} toolCall={toolCall} ... />
    ))}
  </div>
))}
```

## 子组件

| 组件 | 职责 |
|------|------|
| `ChatTextarea` | 消息输入框，支持发送和取消 |
| `ChatMagicGenerator` | 魔法生成功能 (图生图等) |
| `SessionSelector` | 会话选择下拉框 |
| `MessageRegular` | 普通文本消息渲染 |
| `ToolCallTag` | 工具调用标签 (可展开/确认) |
| `ToolCallContent` | 工具调用内容详情 |
| `ToolcallProgressUpdate` | 工具调用进度显示 |
| `ChatSpinner` | 加载动画 |
| `MixedContent` | 混合内容 (图片+文本) |
| `ShareTemplateDialog` | 分享模板弹窗 |

## 滚动行为

```typescript
const scrollRef = useRef<HTMLDivElement>(null)
const isAtBottomRef = useRef(false)

const handleScroll = () => {
  if (scrollRef.current) {
    isAtBottomRef.current =
      scrollRef.current.scrollHeight - scrollRef.current.scrollTop <=
      scrollRef.current.clientHeight + 1
  }
}

const scrollToBottom = useCallback(() => {
  if (!isAtBottomRef.current) return
  setTimeout(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current!.scrollHeight,
      behavior: 'smooth',
    })
  }, 200)
}, [])
```
