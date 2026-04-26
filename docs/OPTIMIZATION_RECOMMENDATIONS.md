# Jaaz 优化建议报告

> 生成日期：2026-04-26
> 分析范围：架构、安全、性能、代码质量、流程

---

## 优先级速查

| 优先级 | 类别 | 数量 |
|--------|------|------|
| P0 立即修复 | 安全 + 可靠性 | 5 |
| P1 本周修复 | 性能 + 配置 + 架构 | 6 |
| P2 计划修复 | 质量 + 流程 | 5 |
| P3 可选优化 | 低优先级 | 4 |

---

## 🔴 P0 — 严重问题（必须修复）

### 1. 安全：无 API 鉴权

**严重性**：严重

所有 API 端点完全开放，无任何认证机制：

| 文件 | 端点 | 风险 |
|------|------|------|
| `routers/chat_router.py` | `/api/chat` | 任何人可发起聊天请求，耗尽 Gemini/Selene quota |
| `routers/config_router.py` | `/api/config/*` | 可读取/修改所有 provider API keys |
| `routers/workspace.py` | `update_file`, `delete_file`, `read_file` 等 | 可读写服务器任意文件 |
| `websocket_router.py` | Socket.IO connect | `auth` 参数被接收但未验证 |

**修复建议**：

```python
# main.py — 添加简单 API Key 中间件
from fastapi import Request, HTTPException

API_KEY = os.getenv("JAAZ_API_KEY", "")

@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        key = request.headers.get("X-API-Key")
        if key != API_KEY:
            raise HTTPException(status_code=401, detail="Unauthorized")
    return await call_next(request)
```

---

### 2. 安全：Workspace 路径遍历漏洞

**严重性**：严重

`routers/workspace.py` 所有文件操作端点未校验路径是否在 `WORKSPACE_ROOT` 内：

```python
# update_file (lines 16-25) — 直接拼接路径
full_path = os.path.join(WORKSPACE_ROOT, path)  # 无校验
# 攻击者可构造 "../../etc/passwd" 遍历服务器任意文件

# browse_filesystem — 默认回退到 home 目录
if not path:
    path = os.path.expanduser("~")  # 暴露整个 home 目录
```

**受影响端点**：`update_file`, `delete_file`, `read_file`, `rename_file`, `list_files_in_dir`, `browse_filesystem`, `serve_file`, `get_file_info`

**修复建议**：

```python
def validate_workspace_path(path: str) -> str:
    """确保路径在 WORKSPACE_ROOT 内，返回 realpath 或抛异常"""
    full = os.path.join(WORKSPACE_ROOT, path)
    real = os.path.realpath(full)
    if not real.startswith(os.path.realpath(WORKSPACE_ROOT)):
        raise ValueError("Path traversal attempt detected")
    return real
```

---

### 3. 安全：无 CORS 配置

**严重性**：严重

`main.py` 未配置 CORS 中间件，FastAPI 默认允许任意跨域请求。

**修复建议**：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://jaaz.app", "http://localhost:3000"],  # 限制来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

### 4. 可靠性：静默异常吞掉所有错误

**严重性**：严重

**`scorer.py` 第 155-156 行**：

```python
try:
    resp = requests.post(self.SELENE_URL, json={...})
except Exception:
    pass  # ← 静默吞掉所有异常
return self.evaluate_and_suggest(prompt)  # 静默降级到 keyword scoring
```

**`enhancer.py` 第 235 行**：

```python
except Exception:
    pass  # ← 吞异常
return self._enhance_with_templates(...)
```

Selene 挂了用户完全不知道，默默降级到 keyword scoring，评分质量大幅下降但不通知。

**修复建议**：异常至少打印 traceback，并返回明确错误状态：

```python
except Exception as e:
    print(f"[Selene] Scoring failed: {e}")
    traceback.print_exc()
    return {"error": "Selene unavailable", "score": None, "pass": False}
```

---

### 5. 性能：async 函数中同步阻塞

**严重性**：严重

**`enhancer.py` 第 229 行**：

```python
async def _enhance_with_llm(...):
    response = requests.post(url, json=payload, timeout=30)  # 同步阻塞！
```

**`scorer.py` 第 142 行**：

```python
eval_result = scorer.evaluate_with_feedback(...)  # 同步 requests.post
```

这会阻塞整个 FastAPI 事件循环。一个请求在等 Selene 响应时，所有其他请求都无法处理。

**修复建议**：用 `httpx.AsyncClient` 替代 `requests`：

```python
import httpx

async def _call_gemini_async(prompt: str):
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, timeout=30.0)
        return resp.json()
```

---


### 9. WebSocket Session 隔离缺失

**`websocket_service.py` 第 25-26 行**：

```python
async def send_to_websocket(session_id: str, event: Dict):
    await broadcast_session_update(session_id, None, event)
```

`broadcast_session_update` 会发送给**所有** socket 连接，而不是仅发给该 session 的连接。用户 A 的消息可能被用户 B 收到。

---

### 10. 启动竞态风险

**`main.py` 第 39 行注释明确警告**：

```python
# TODO: Check if there will be racing conditions when user send chat
# request but tools and models are not initialized yet.
```

lifespan 中初始化顺序：
1. `config_service.initialize()`
2. `broadcast_init_done()` → 通知前端"已就绪"
3. `tool_service.initialize()`

第 2 步时前端已收到 init_done，但 tool_service 尚未完成初始化。如果此时用户发送请求会失败。

---

### 11. 内存泄漏 / 效率问题

**`agent_manager.py` 第 93-97 行**：

```python
for tool_id, tool_info in tool_service.get_all_tools().items():
    if tool_info.get('provider') == 'system':
        tool = tool_service.get_tool(tool_id)
```

`get_all_tools()` 返回 `self.tools.copy()`，每次调用都复制整个字典。agent 创建时反复调用造成不必要开销。

---

### 12. 死代码

| 文件 | 内容 |
|------|------|
| `agent_manager.py` lines 44-54 | 注释掉的 `image_designer_config` 和 `video_designer_config` |
| `tool_service.py` lines 63-128 | 大量注释掉的 jaaz tools 配置（约 60+ 行） |

---



### 14. Python 类型提示不足

- `chat_service.py` 几乎无类型
- `tool_service.py` 部分方法无返回类型
- `enhance_airmold_prompt.py` 的 tool function 参数无 schema 验证（虽然用了 Pydantic）

---



### 16. 多语言硬编码

所有 UI 文案和错误消息中英混合写死在代码里：

```python
# scorer.py
suggestions.append("材质不够明确，缺少 PVC/TPU/防水面料 等专业材质描述")

# enhance_airmold_prompt.py
return "图像检查通过：未发现明显错误。"
```

建议 i18n 化，使用 `gettext` 或前端 i18n 框架（已有 `react/src/i18n/`）。

---



### 19. `TOOL_MAPPING` 重复注册警告

`tool_service.py` 中 `register_tool` 被重调用时会打印 `🔄 TOOL ALREADY REGISTERED`，应静默覆盖或去重。

---

### 20. `StreamProcessor.py` 未审查

架构文档中提到但未深入审查，需单独分析流式处理逻辑。

---

### 21. ComfyUI Workflow Type 硬编码

`tool_service.py` 第 320 行：

```python
"type": "image",  # TODO: Add comfyui workflow type! Not hardcoded!
```

ComfyUI workflow 的 type 应从 workflow 定义中读取，而非硬编码。

---

## 优先级总结

```
P0 (立即修复):
  [安全] API 无鉴权 — 所有 /api/* 端点开放
  [安全] Workspace 路径遍历 — 可读写服务器任意文件
  [安全] 无 CORS 配置
  [可靠] 静默异常吞掉 — Selene 挂了不通知
  [性能] async 中同步 requests — 阻塞事件循环

P1 (本周修复):
  [配置] 硬编码值 — SELENE_URL, PASS_THRESHOLD, 模型名
  [性能] Selene server 无并发限制/队列/优雅关闭
  [性能] 数据库无索引
  [安全] WebSocket session 隔离缺失 — 消息发给错误用户
  [架构] 启动竞态 — init_done 在 tools 就绪前发送
  [效率] get_all_tools() 每次复制整个字典

P2 (计划修复):
  [质量] 测试覆盖为零
  [质量] Python 类型提示不足
  [质量] 日志不规范 — print vs traceback 混用
  [安全] Prompt injection 风险
  [流程] 多语言硬编码无 i18n

P3 (可选):
  [性能] aiosqlite 无连接池
  [质量] 重复注册工具警告
  [质量] ComfyUI workflow type 硬编码
  [待审] StreamProcessor.py 未深入审查
```

---

## 建议行动计划

**第一周**：
1. 修复 API 鉴权（加 X-API-Key 中间件）
2. 修复 Workspace 路径遍历（加 realpath 校验）
3. 配置 CORS
4. 修复静默异常（加 traceback + 明确错误返回）
5. 将同步 `requests` 改为 `httpx.AsyncClient`

**第二周**：
6. 配置硬编码值改为环境变量
7. Selene server 加 semaphore + 健康检查
8. 加数据库索引
9. 修复 WebSocket session 隔离
10. 修复启动竞态

**持续迭代**：
- 补充测试
- 结构化日志
- 类型提示补全
- i18n 化

---

## 🟣 附加建议：后端代码组织与架构重构方案

目前的后端（FastAPI + Python）结构存在职责混淆、命名冗长、结构扁平化的问题。建议按照功能模块进行重构。

### 1. 目录结构重构 (Directory Restructuring)

#### 1.1 整理泛滥的 `tools/` 目录
当前 `tools` 目录下有 30 多个类似 `generate_image_by_xxx_jaaz.py` 的文件，非常臃肿。
**建议**：按生成媒介分类，并简化文件名。
```text
server/tools/
├── image/
│   ├── comfyui.py        # 替代原 generate_image_by_comfyui...
│   ├── midjourney.py     # 替代原 generate_image_by_midjourney...
│   ├── ideogram.py
│   └── flux.py           # 内部通过 class/method 区分具体模型
├── video/
│   ├── kling.py          # 替代原 generate_video_by_kling...
│   └── hailuo.py
└── core/                 # 放置基础工具类
```

#### 1.2 净化 `routers/` (路由层)
`routers` 应该**只包含 API 接口定义**。
- 将 `comfyui_execution.py` 移动到 `services/` 或 `tasks/`。
- 统一文件命名规范：全部使用 `*_router.py` 后缀（如 `settings.py` -> `settings_router.py`）。
- 将测试路由如 `ssl_test.py` 移入 `tests/` 或专用开发路由。

#### 1.3 抽离 WebSocket 模块
**建议**：为长连接新建独立目录 `server/websockets/`。
```text
server/websockets/
├── __init__.py
├── manager.py     # 替代 websocket_state.py，管理连接池和 sio 实例
├── handlers.py    # 替代 websocket_router.py，处理 connect/disconnect 事件
└── emitter.py     # 替代 websocket_service.py，处理主动推送逻辑
```

### 2. 核心文件优化 (`main.py` 瘦身)

当前的 `main.py` 混合了配置加载、静态代理、WebSocket 挂载和环境变量逻辑。
**建议**：将 `main.py` 作为纯粹的入口文件。
1. **抽离 Lifespan**：新建 `server/core/lifespan.py` 处理应用启动/关闭逻辑。
2. **抽离静态文件**：新建 `server/core/static.py` 处理 React 产物加载。
3. **批量注册**：封装 `register_routers(app)`，避免在 main 中写长串的 include_router。

### 3. 架构设计升级 (Architecture Best Practices)

#### 3.1 废弃全局 Singleton，改用 Dependency Injection
当前大量使用全局实例（如 `from services.db_service import db_service`），不利于单元测试和解耦。
**建议**：使用 FastAPI 的 `Depends()` 依赖注入系统：
```python
@router.get("/list")
async def list_canvases(db: DatabaseService = Depends(get_db)):
    return await db.list_canvases()
```

#### 3.2 命名规范统一
- **目录命名**：修改 `OpenAIAgents_service` 为纯 `snake_case`（如 `openai_agents`）。
- **文件命名**：将 `StreamProcessor.py` 改为小写 `stream_processor.py`，保持全项目统一。

#### 3.3 Pydantic 模型标准化
确保 `models/` 目录下的数据结构全部使用 Pydantic v2 `BaseModel`，以获得严格校验和完善的 OpenAPI Swagger 文档，弃用松散的 TypedDict 或手写类。
