# 03 - 路由系统

## 概述

Jaaz 前端使用 **TanStack Router** 进行路由管理，采用**文件路由模式**。

## 路由定义

### 路由列表

| 文件 | 路径 | 组件 | 说明 |
|------|------|------|------|
| `__root.tsx` | / | RootLayout | 根布局，包含 Outlet + DevTools |
| `index.tsx` | / | Home | 首页，Canvas 创建入口 |
| `canvas.$id.tsx` | /canvas/:id | Canvas | Canvas 编辑器页面 |
| `knowledge.tsx` | /knowledge | Knowledge | 知识库页面 |
| `agent_studio.tsx` | /agent_studio | AgentStudio | Agent 配置页面 |
| `assets.tsx` | /assets | MaterialManager | 资源管理页面 |

## 根路由 (__root.tsx)

```typescript
// routes/__root.tsx
import { createRootRoute, Outlet } from '@tanstack/react-router'
import { TanStackRouterDevtools } from '@tanstack/react-router-devtools'
import ErrorBoundary from '@/components/common/ErrorBoundary'

export const Route = createRootRoute({
  component: () => (
    <>
      <Outlet />
      <TanStackRouterDevtools />
    </>
  ),
  errorComponent: ErrorBoundary,
})
```

**关键点**:
- `<Outlet />` 渲染子路由
- `<TanStackRouterDevtools />` 提供路由调试工具
- `errorComponent` 捕获子路由错误

## 首页路由 (index.tsx)

**路径**: `/`

```typescript
export const Route = createFileRoute('/')({
  component: Home,
})
```

**功能**:
- 显示 TopMenu
- ChatTextarea 用于发起 Canvas 创建
- CanvasList 展示已有 Canvas
- 创建成功后导航到 `/canvas/:id?sessionId=xxx`

## Canvas 路由 (canvas.$id.tsx)

**路径**: `/canvas/:id`

```typescript
export const Route = createFileRoute('/canvas/$id')({
  component: Canvas,
})

function Canvas() {
  // 获取路由参数
  const { id } = useParams({ from: '/canvas/$id' })

  // 获取查询参数
  const search = useSearch({ from: '/canvas/$id' }) as {
    sessionId: string
  }
}
```

**URL 参数**:
| 参数 | 类型 | 说明 |
|------|------|------|
| `id` (路径参数) | string | Canvas ID |
| `sessionId` (查询参数) | string | 会话 ID |

## 路由组织

```
route-tree.gen.ts (自动生成)
└── RootRoute (/)
    ├── IndexRoute (/)
    ├── CanvasIdRoute (/canvas/:id)
    ├── KnowledgeRoute (/knowledge)
    ├── Agent_studioRoute (/agent_studio)
    └── AssetsRoute (/assets)
```

## 路由守卫

**当前实现**: 无显式路由守卫

认证检查通过以下方式实现：
1. API 请求返回 401 时触发登录弹窗
2. AuthContext 在应用启动时检查 Token 状态
3. `getAuthStatus()` 验证 Token 有效性

```typescript
// App.tsx 中的全局登录弹窗
<AuthProvider>
  <ConfigsProvider>
    <RouterProvider router={router} />
    <LoginDialog />  {/* 全局显示，根据 authStatus 决定是否可见 */}
  </ConfigsProvider>
</AuthProvider>
```

## 代码分割

TanStack Router 自动为每个路由文件创建代码分割点：

```typescript
// 实际构建时自动分割
// 每个路由组件会单独打包
import('./routes/canvas.$id.tsx')  // Canvas 页面独立 chunk
import('./routes/knowledge.tsx')    // 知识库独立 chunk
```

## 路由导航

### 导航到 Canvas
```typescript
// 创建 Canvas 后导航
const handleCreateCanvas = async () => {
  const result = await createCanvas(data)
  // 方式1: 使用 navigate
  navigate({ to: '/canvas/$id', params: { id: result.id } })

  // 方式2: 使用 window.location
  window.location.href = `/canvas/${result.id}?sessionId=${sessionId}`
}
```

### 切换会话
```typescript
// 在 Canvas 页面切换 session
const onSelectSession = (sessionId: string) => {
  window.history.pushState(
    {},
    '',
    `/canvas/${canvasId}?sessionId=${sessionId}`
  )
}
```

## TanStack Router 特点

1. **类型安全**: 自动生成路由类型
2. **文件路由**: 基于文件结构自动生成路由
3. **代码分割**: 自动按路由分割代码
4. **嵌套路由**: 支持布局嵌套
5. **搜索参数**: 支持类型安全的搜索参数

## 相关文件

| 文件 | 说明 |
|------|------|
| `route-tree.gen.ts` | 自动生成的路由树 |
| `App.tsx` | 创建 Router 实例 |
| `main.tsx` | 包裹 RouterProvider |
