# 07 - Canvas 系统

## 概述

Canvas 系统是基于 Excalidraw 的可视化设计画布，与 Chat 系统结合，实现边画边聊的 AI 设计体验。

## 核心文件

| 文件 | 职责 |
|------|------|
| `routes/canvas.$id.tsx` | Canvas 页面路由 |
| `components/canvas/CanvasExcali.tsx` | Excalidraw 画布核心 |
| `components/canvas/CanvasHeader.tsx` | 顶部标题栏 |
| `components/canvas/menu/` | 工具菜单组件 |
| `components/canvas/pop-bar/` | 弹出工具栏 |
| `api/canvas.ts` | Canvas API |
| `contexts/canvas.tsx` | Canvas Context |

## Canvas 页面布局

```
┌──────────────────────────────────────────────────────────┐
│                    CanvasHeader                          │
│               (Canvas 名称，可重命名)                      │
├────────────────────────────┬─────────────────────────────┤
│                            │                             │
│                            │       ChatInterface         │
│                            │       (聊天面板)             │
│      CanvasExcali          │                             │
│      (Excalidraw 画布)      │   - SessionSelector        │
│                            │   - Messages                │
│                            │   - ChatTextarea            │
│                            │                             │
│                            │                             │
├────────────────────────────┴─────────────────────────────┤
│              CanvasMenu (左下角工具栏)                      │
│              CanvasPopbar (右侧弹出工具栏)                  │
└──────────────────────────────────────────────────────────┘
         ▲ 可拖动分割线调整比例
```

## 页面路由 (routes/canvas.$id.tsx)

**URL**: `/canvas/:id?sessionId=xxx`

```typescript
export const Route = createFileRoute('/canvas/$id')({
  component: Canvas,
})

function Canvas() {
  const { id } = useParams({ from: '/canvas/$id' })
  const search = useSearch({ from: '/canvas/$id' }) as { sessionId: string }

  const [canvas, setCanvas] = useState(null)
  const [canvasName, setCanvasName] = useState('')
  const [sessionList, setSessionList] = useState<Session[]>([])

  // 获取 Canvas 数据
  useEffect(() => {
    const fetchCanvas = async () => {
      const data = await getCanvas(id)
      setCanvas(data)
      setCanvasName(data.name)
      setSessionList(data.sessions)
    }
    fetchCanvas()
  }, [id])

  return (
    <CanvasProvider>
      <div className='flex flex-col w-screen h-screen'>
        <CanvasHeader
          canvasName={canvasName}
          canvasId={id}
          onNameChange={setCanvasName}
          onNameSave={handleNameSave}
        />
        <ResizablePanelGroup direction='horizontal'>
          <ResizablePanel defaultSize={75}>
            <CanvasExcali canvasId={id} initialData={canvas?.data} />
            <CanvasMenu />
            <CanvasPopbarWrapper />
          </ResizablePanel>
          <ResizableHandle />
          <ResizablePanel defaultSize={25}>
            <ChatInterface
              canvasId={id}
              sessionList={sessionList}
              setSessionList={setSessionList}
              sessionId={search.sessionId}
            />
          </ResizablePanel>
        </ResizablePanelGroup>
      </div>
    </CanvasProvider>
  )
}
```

## Canvas API (api/canvas.ts)

| 函数 | 说明 | 请求/响应 |
|------|------|----------|
| `listCanvases()` | 列出所有 Canvas | GET `/api/canvas/list` → `ListCanvasesResponse[]` |
| `createCanvas(data)` | 创建新 Canvas | POST `/api/canvas/create` → `{ id }` |
| `getCanvas(id)` | 获取 Canvas | GET `/api/canvas/:id` → `{ data, name, sessions }` |
| `saveCanvas(id, payload)` | 保存 Canvas | POST `/api/canvas/:id/save` |
| `renameCanvas(id, name)` | 重命名 | POST `/api/canvas/:id/rename` |
| `deleteCanvas(id)` | 删除 | DELETE `/api/canvas/:id/delete` |

### 创建 Canvas

```typescript
interface CreateCanvasPayload {
  name: string
  canvas_id: string
  messages: Message[]
  session_id: string
  text_model: { provider: string; model: string; url: string }
  tool_list: ToolInfo[]
  system_prompt: string
}

export async function createCanvas(data: CreateCanvasPayload): Promise<{ id: string }> {
  const response = await fetch('/api/canvas/create', {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return await response.json()
}
```

### 获取 Canvas

```typescript
export async function getCanvas(id: string): Promise<{
  data: CanvasData      // Excalidraw 数据
  name: string         // Canvas 名称
  sessions: Session[]  // 会话列表
}> {
  const response = await fetch(`/api/canvas/${id}`)
  return await response.json()
}
```

### 保存 Canvas

```typescript
export async function saveCanvas(
  id: string,
  payload: {
    data: CanvasData   // Excalidraw JSON 数据
    thumbnail: string // 缩略图 base64
  }
): Promise<void> {
  await fetch(`/api/canvas/${id}/save`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
```

## CanvasExcali 组件

基于 Excalidraw 实现画布功能：

```typescript
import { Excalidraw } from '@excalidraw/excalidraw'

const CanvasExcali: React.FC<{
  canvasId: string
  initialData?: CanvasData
}> = ({ canvasId, initialData }) => {
  return (
    <div className="w-full h-full">
      <Excalidraw
        initialData={initialData}
        onChange={(elements, appState) => {
          // 实时保存或自动保存
        }}
      />
    </div>
  )
}
```

## CanvasHeader 组件

顶部栏，显示 Canvas 名称并支持重命名：

```typescript
interface CanvasHeaderProps {
  canvasName: string
  canvasId: string
  onNameChange: (name: string) => void
  onNameSave: () => void
}

const CanvasHeader: React.FC<CanvasHeaderProps> = ({
  canvasName,
  canvasId,
  onNameChange,
  onNameSave,
}) => {
  return (
    <div className="flex items-center px-4 py-2 border-b">
      <input
        value={canvasName}
        onChange={(e) => onNameChange(e.target.value)}
        onBlur={onNameSave}
        className="text-lg font-medium"
      />
    </div>
  )
}
```

## CanvasMenu 组件

左下角工具菜单：

```typescript
// components/canvas/menu/
CanvasMenuIcon.tsx    // 菜单图标
CanvasToolMenu.tsx    // 工具子菜单
CanvasViewMenu.tsx    // 视图子菜单 (缩放、网格等)
CanvasMenuButton.tsx  // 菜单按钮
```

## CanvasPopbar 组件

右侧弹出工具栏：

```typescript
// components/canvas/pop-bar/
CanvasPopbar.tsx              // 主组件
CanvasMagicGenerator.tsx      // 魔法生成工具
CanvasPopbarContainer.tsx     // 容器
```

### 魔法生成

```typescript
// CanvasMagicGenerator.tsx
const handleMagicGenerate = async (imageData: string) => {
  // 调用 magic API 生成图片
  // 将生成的图片添加到 Canvas
  // 同时发送到 Chat
}
```

## 可调整面板 (Resizable)

使用 `react-resizable-panels` 实现面板大小调整：

```typescript
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from '@/components/ui/resizable'

<ResizablePanelGroup direction="horizontal" autoSaveId="jaaz-chat-panel">
  <ResizablePanel defaultSize={75}>
    <CanvasExcali />
  </ResizablePanel>

  <ResizableHandle />

  <ResizablePanel defaultSize={25}>
    <ChatInterface />
  </ResizablePanel>
</ResizablePanelGroup>
```

- `autoSaveId`: 自动保存面板大小到 localStorage
- `defaultSize`: 默认大小百分比
- `direction="horizontal"`: 水平分割

## 数据流

### 创建新 Canvas

```
1. 首页 ChatTextarea 输入描述
2. 点击创建 → createCanvas API
3. 后端返回 { id: 'xxx' }
4. 路由跳转到 /canvas/xxx?sessionId=yyy
5. Canvas 页面加载 getCanvas(xxx)
6. 渲染 CanvasExcali + ChatInterface
```

### 画布操作

```
用户操作 Excalidraw
        │
        ▼
onChange 回调
        │
        ▼
自动保存 (debounce) → saveCanvas API
        │
        ▼
更新本地状态
```

### 添加图片到聊天

```
Canvas 中选择图片
        │
        ▼
eventBus.emit('Canvas::AddImagesToChat', { fileId, ... })
        │
        ▼
Chat 组件监听
        │
        ▼
添加到 messages
```

## Canvas Context

```typescript
// contexts/canvas.tsx
interface CanvasContextType {
  canvasData: any
  setCanvasData: (data: any) => void
  // ...
}
```

## 相关类型

```typescript
interface CanvasData {
  elements: any[]      // Excalidraw 元素
  appState: any        // Excalidraw 应用状态
}

interface ListCanvasesResponse {
  id: string
  name: string
  description?: string
  thumbnail?: string
  created_at: string
}
```
