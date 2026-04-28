# 08 - 知识库系统

## 概述

知识库系统允许用户创建、管理和使用个人知识库，用于增强 AI 的回答质量。

## 核心文件

| 文件 | 职责 |
|------|------|
| `components/knowledge/Knowledge.tsx` | 知识库主组件 |
| `components/knowledge/Editor.tsx` | 知识编辑器 |
| `api/knowledge.ts` | 知识库 API |

## 知识库 API (api/knowledge.ts)

### 类型定义

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
  content?: string  // 可选，详情才返回
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

### API 函数

| 函数 | 说明 | 端点 |
|------|------|------|
| `getKnowledgeList(params?)` | 获取知识库列表 | GET `/api/knowledge/list` |
| `getKnowledgeById(id)` | 获取知识库详情 | GET `/api/knowledge/:id` |
| `createKnowledge(data)` | 创建知识库 | POST `/api/knowledge/create` |
| `updateKnowledge(id, data)` | 更新知识库 | PUT `/api/knowledge/:id` |
| `deleteKnowledge(id)` | 删除知识库 | DELETE `/api/knowledge/:id` |
| `saveEnabledKnowledgeDataToSettings(data)` | 保存启用状态 | POST `/api/settings` |

### 获取知识库列表

```typescript
interface KnowledgeListParams {
  pageSize?: number    // 默认 10
  pageNumber?: number  // 默认 1
  search?: string      // 搜索关键词
}

export async function getKnowledgeList(
  params: KnowledgeListParams = {}
): Promise<KnowledgeListResponse> {
  const { pageSize = 10, pageNumber = 1, search } = params

  const queryParams = new URLSearchParams({
    pageSize: pageSize.toString(),
    pageNumber: pageNumber.toString(),
  })

  if (search?.trim()) {
    queryParams.append('search', search.trim())
  }

  const response = await authenticatedFetch(
    `${BASE_API_URL}/api/knowledge/list?${queryParams.toString()}`
  )

  return await response.json()
}
```

### 创建知识库

```typescript
interface CreateKnowledgeData {
  name: string
  description?: string
  cover?: string
  is_public?: boolean
  content?: string
}

export async function createKnowledge(
  knowledgeData: CreateKnowledgeData
): Promise<ApiResponse> {
  const response = await authenticatedFetch(
    `${BASE_API_URL}/api/knowledge/create`,
    {
      method: 'POST',
      body: JSON.stringify(knowledgeData),
    }
  )
  return await response.json()
}
```

### 更新知识库

```typescript
export async function updateKnowledge(
  id: string,
  knowledgeData: Partial<CreateKnowledgeData>
): Promise<ApiResponse> {
  const response = await authenticatedFetch(
    `${BASE_API_URL}/api/knowledge/${id}`,
    {
      method: 'PUT',
      body: JSON.stringify(knowledgeData),
    }
  )
  return await response.json()
}
```

### 删除知识库

```typescript
export async function deleteKnowledge(id: string): Promise<ApiResponse> {
  const response = await authenticatedFetch(
    `${BASE_API_URL}/api/knowledge/${id}`,
    { method: 'DELETE' }
  )
  return await response.json()
}
```

### 保存启用状态

```typescript
// 注意：这个接口不需要认证
export async function saveEnabledKnowledgeDataToSettings(
  knowledgeData: KnowledgeBase[]
): Promise<ApiResponse> {
  const response = await fetch('/api/settings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      enabled_knowledge_data: knowledgeData,
    }),
  })
  return await response.json()
}
```

## Knowledge 组件

### 功能

- 知识库列表展示 (分页)
- 搜索功能
- 启用/禁用切换
- 创建、编辑、删除知识库
- 知识详情查看

### 状态

```typescript
interface KnowledgeState {
  knowledgeList: KnowledgeBase[]
  pagination: Pagination
  isLoading: boolean
  search: string
  page: number
  selectedKnowledge: KnowledgeBase | null  // 详情面板
}
```

### 主要操作

```typescript
// 加载列表
const loadKnowledgeList = async () => {
  const result = await getKnowledgeList({ pageNumber: page, search })
  setKnowledgeList(result.data.list)
  setPagination(result.data.pagination)
}

// 切换启用状态
const toggleEnabled = async (knowledge: KnowledgeBase) => {
  // 更新启用状态
  const updated = { ...knowledge, enabled: !knowledge.enabled }
  await updateKnowledge(knowledge.id, updated)

  // 保存到 settings
  const enabledList = knowledgeList.filter(k => k.enabled)
  await saveEnabledKnowledgeDataToSettings(enabledList)
}

// 删除
const handleDelete = async (id: string) => {
  await deleteKnowledge(id)
  await loadKnowledgeList()
}
```

## Knowledge 编辑器

```typescript
interface EditorProps {
  knowledge?: KnowledgeBase  // 传入则是编辑，不传则是创建
  onSave: (data: CreateKnowledgeData) => Promise<void>
  onCancel: () => void
}

const Editor: React.FC<EditorProps> = ({ knowledge, onSave, onCancel }) => {
  const [name, setName] = useState(knowledge?.name || '')
  const [description, setDescription] = useState(knowledge?.description || '')
  const [content, setContent] = useState(knowledge?.content || '')

  const handleSubmit = async () => {
    await onSave({ name, description, content })
  }

  return (
    <div>
      <input value={name} onChange={e => setName(e.target.value)} />
      <textarea value={description} onChange={e => setDescription(e.target.value)} />
      <textarea value={content} onChange={e => setContent(e.target.value)} />
      <button onClick={handleSubmit}>保存</button>
      <button onClick={onCancel}>取消</button>
    </div>
  )
}
```

## 知识库启用流程

```
1. 用户在知识库页面启用某个知识库
2. 前端调用 updateKnowledge 更新 is_public 或 enabled 状态
3. 前端调用 saveEnabledKnowledgeDataToSettings 保存完整数据到 /api/settings
4. 后端将启用状态存储到 settings.json
5. AI Agent 处理请求时，后端读取 settings 中的 enabled_knowledge_data
6. 将知识库内容注入到 system prompt 或作为 context
```

## 分页处理

```typescript
const handlePageChange = (newPage: number) => {
  setPage(newPage)
  loadKnowledgeList()
}

const renderPagination = () => {
  const { current_page, total_pages, has_next, has_prev } = pagination

  return (
    <div className="flex items-center gap-2">
      <button
        disabled={!has_prev}
        onClick={() => handlePageChange(current_page - 1)}
      >
        上一页
      </button>

      <span>{current_page} / {total_pages}</span>

      <button
        disabled={!has_next}
        onClick={() => handlePageChange(current_page + 1)}
      >
        下一页
      </button>
    </div>
  )
}
```

## 搜索功能

```typescript
const [searchInput, setSearchInput] = useState('')

const handleSearch = () => {
  setPage(1)  // 搜索重置页码
  loadKnowledgeList()
}

// 防抖搜索
const debouncedSearch = useDebouncedCallback(() => {
  handleSearch()
}, 300)
```

## 相关配置

知识库数据最终存储在后端的 `config/settings.json` 中：

```json
{
  "enabled_knowledge_data": [
    {
      "id": "xxx",
      "name": "知识库名称",
      "content": "知识库内容...",
      ...
    }
  ]
}
```
