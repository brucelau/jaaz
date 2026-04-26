# Jaaz API Reference

本文档详细记录了 Jaaz 应用中前端 (React) 与后端 (FastAPI) 之间交互的所有 RESTful API 接口。

## 1. 启动与基础配置类 (Config & Setup)

前端应用在启动时会并行调用这些接口以初始化应用状态。

| 接口端点 (Endpoint) | 方法 (Method) | 作用描述 | 前端调用位置 |
|--------------------|--------------|----------|-------------|
| `/api/list_models` | GET | 获取所有支持的文本/视觉大语言模型 (LLM) 列表。返回数据会合并所有配置的 provider (如 openai, gemini, minimax 等)。 | `src/api/model.ts` -> `listModels()` |
| `/api/list_tools` | GET | 获取系统中已注册并启用的所有 AI 工具 (Tools/Functions) 列表。 | `src/api/model.ts` -> `listModels()` |
| `/api/settings` | GET | 获取应用全局配置 (例如全局代理、启用的默认知识库等)。自动屏蔽 API Key 等敏感信息。 | `src/api/settings.ts` -> `getSettings()` |
| `/api/settings/update` | POST | 提交更新全局配置信息，后端会深度合并更新。 | `src/api/settings.ts` -> `updateSettings()` |

---

## 2. 画布管理 (Canvas Management)

画布 (Canvas) 是本系统的核心实体，关联了可视化的界面与背后的 AI 对话会话。

| 接口端点 (Endpoint) | 方法 (Method) | 作用描述 | 前端调用位置 |
|--------------------|--------------|----------|-------------|
| `/api/canvas/list` | GET | 获取所有画布的列表，主要用于渲染首页瀑布流或项目列表，包含画布基础信息与缩略图路径。 | `src/api/canvas.ts` -> `listCanvases()` |
| `/api/canvas/create` | POST | 创建一个全新的画布。前端会提交画布初始名、关联的 Session ID 和选择的文本模型。后端会同步创建关联的会话与历史记录。 | `src/api/canvas.ts` -> `createCanvas()` |
| `/api/canvas/{id}` | GET | 进入特定画布时调用，获取该画布的 JSON 节点数据、名称以及该画布下所有历史的对话 Sessions。 | `src/api/canvas.ts` -> `getCanvas()` |
| `/api/canvas/{id}/save` | POST | 手动/自动保存当前画布的状态，接收 `data` (节点 JSON) 和 `thumbnail` (封面缩略图 Base64 或 URL)。 | `src/api/canvas.ts` -> `saveCanvas()` |
| `/api/canvas/{id}/rename`| POST | 画布重命名接口。 | `src/api/canvas.ts` -> `renameCanvas()` |
| `/api/canvas/{id}/delete`| DELETE| 删除指定的画布及关联数据。 | `src/api/canvas.ts` -> `deleteCanvas()` |

---

## 3. 会话与对话流 (Chat & Sessions)

**注意**: Jaaz 核心的对话回复是通过 WebSocket (`/socket.io`) 进行双向通信与流式推送的。以下的 HTTP API 主要用于初始触发与历史查询。

| 接口端点 (Endpoint) | 方法 (Method) | 作用描述 | 前端调用位置 |
|--------------------|--------------|----------|-------------|
| `/api/chat` | POST | 发送一条新的聊天消息，触发后端 LangGraph/Agent 运行。后续的回答文本、工具调用等状态会通过 WebSocket 推送给前端。 | `src/api/chat.ts` -> `sendMessages()` |
| `/api/chat_session/{id}` | GET | 获取特定对话 Session 下的所有历史消息数组，用于恢复聊天界面的上下文。 | `src/components/chat/Chat.tsx` |
| `/api/tool_confirmation` | POST | **人机交互接口**。当后端 Agent 计划调用高风险工具（如生成视频等耗时操作）被拦截时，等待前端用户点击“确认”后，通过此接口提交继续执行的指令。 | `src/components/chat/Chat.tsx` |

---

## 4. 静态资源与文件管理 (Assets & Files)

管理应用内生成的素材、上传的文档以及画布截图。

| 接口端点 (Endpoint) | 方法 (Method) | 作用描述 | 前端调用位置 |
|--------------------|--------------|----------|-------------|
| `/api/file/{filename}.extension`| GET | 文件读取接口。前端通过这个接口拉取后端 `user_data` 目录下的各种资源，例如生成的图片、视频和上传的附件。 | 各类 `<img>`, `<video>` 标签的 `src` 属性 |
| `/api/upload` | POST | 用户上传图片、文档或知识库素材的入口，上传成功后后端返回文件的存储 ID/路径。 | `src/api/upload.ts` -> `uploadImage()` |

---

## 5. 第三方服务集成 (ComfyUI & Others)

针对集成的高级工作流组件 API。

| 接口端点 (Endpoint) | 方法 (Method) | 作用描述 | 前端调用位置 |
|--------------------|--------------|----------|-------------|
| `/api/settings/comfyui/list_workflows` | GET | 获取保存在本地 SQLite 数据库中的常用 ComfyUI 工作流列表。 | `src/components/settings/ComfyuiWorkflowSetting.tsx` |
| `/api/settings/comfyui/delete_workflow/{id}` | DELETE| 删除已保存的特定 ComfyUI 工作流。 | 同上 |
| `/api/settings/comfyui/proxy` | GET | ComfyUI 本地跨域代理接口。主要用于前端去请求 ComfyUI 的 `/object_info` 接口，以探测 ComfyUI 中安装了哪些模型和节点。 | `src/components/settings/ComfyuiSetting.tsx` |

---

## 6. 系统与账单类 (System)

| 接口端点 (Endpoint) | 方法 (Method) | 作用描述 | 前端调用位置 |
|--------------------|--------------|----------|-------------|
| `/api/billing/getBalance` | GET | 私有化部署中使用的虚拟账单余额接口 (目前写死返回 999999.99 供前端模拟计费显示)。 | 账单相关 UI 组件 |
