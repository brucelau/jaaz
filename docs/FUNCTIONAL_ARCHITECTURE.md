# Jaaz 功能流程架构文档

## 目标

将 Selene LLM 模型迁移到远程 Mac Studio 服务器（100.75.202.111），作为服务运行并暴露 REST API 接口，集成到 jaaz 工作流中进行 prompt 评分/评估。

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         React Frontend                          │
│                    (Socket.IO 实时通信)                          │
└────────────────────────────┬────────────────────────────────────┘
                              │ HTTP/WebSocket
┌────────────────────────────▼────────────────────────────────────┐
│                      FastAPI Backend                            │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  Chat Service │  │ Agent Service │  │   Tool Service        │  │
│  │  (编排协调)   │  │  (LangGraph)  │  │   (工具注册)          │  │
│  └──────────────┘  └──────────────┘  └────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              Pattern Enhancement System                  │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │   │
│  │  │ Enhancer.py │  │ Scorer.py   │  │ Inflatable      │  │   │
│  │  │ (Gemini 3.1)│→→│ (Selene)    │→→│ Prompt Enhancer │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐  │
│  │  DB Service  │  │ Config Svc   │  │  Auth Service        │  │
│  │  (SQLite)    │  │ (Provider)   │  │  (SQLite + bcrypt)   │  │
│  └──────────────┘  └──────────────┘  └────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
               ┌──────────────┴──────────────┐
               │                              │
      ┌────────▼────────┐         ┌──────────▼──────────┐
      │  Gemini (Google) │         │  Selene (远程 Mac)   │
      │  100.75.202.111  │         │  :8080              │
      │  提示生成模型    │         │  Llama-3.1-8B       │
      │  gemini-3.1-flash│        │  MPS Backend        │
      └──────────────────┘         └─────────────────────┘
```

## 数据流

### 1. 用户请求流程

1. 用户通过 React 前端发送 prompt 请求
2. FastAPI 接收请求 → Chat Service 编排
3. Agent Service 加载 LangGraph agent
4. Agent 调用工具生成内容（英文 prompt）
5. Stream Processor 实时流式输出到前端

### 2. Prompt 增强流程（Sequential）

```
用户输入 → Gemini 生成候选 → Selene 评分 → 通过?
                                         ├── Yes → 采用该候选
                                         └── No  → 收集反馈 → Gemini 改进 → 重试（最多3次）
```

**详细步骤：**

1. **用户输入** → `enhance_inflatable_prompt.py`
2. **Gemini 生成** → `enhancer.py` 调用 `gemini-3.1-flash` 生成 1 个候选
3. **Selene 评分** → `scorer.py` 调用 `http://100.75.202.111:8080/v1/chat/completions`
   - 评估 4 个维度：语法正确性、语义一致性、风格一致性、创意与原创性
   - 每维度 1-5 分，总分 ≥3.5 分则通过
4. **反馈重试** → 如果不通过，将 Selene 反馈注入 LLM prompt 重新生成
5. **最终输出** → 采用通过的候选或最佳尝试结果

### 3. LangGraph Agent 系统

```
Agent Manager
     │
     ├── image_designer (scaffolded, not wired)
     ├── video_designer (scaffolded, not wired)
     ├── prompt_enhancer ─────────────────┐
     │                                     │
     │                              LangGraph StateGraph
     │                                     │
     │                    ┌────────────────┼────────────────┐
     │                    ▼                ▼                ▼
     │              Supervisor        Researcher       Analyst
     │                                     │
     │                              ┌──────▼──────┐
     │                              │   Tools     │
     │                              │  - search   │
     │                              │  - memory   │
     │                              │  - scraper  │
     │                              │  - enhancer │
     │                              └─────────────┘
```

## 核心模块

### 后端服务

| 文件 | 职责 |
|------|------|
| `main.py` | FastAPI 启动入口，Socket.IO 配置 |
| `chat_service.py` | 聊天编排，协调各服务 |
| `agent_service.py` | LangGraph agent 入口 |
| `agent_manager.py` | Agent 创建与管理 |
| `tool_service.py` | 工具注册表 |
| `config_service.py` | Provider 配置（Gemini 等） |
| `db_service.py` | SQLite 持久化 |
| `StreamProcessor.py` | 实时流式输出处理 |
| `auth_service.py` | 本地用户注册/登录/Token 管理 |
| `routers/auth_router.py` | 认证 API 路由 |

### Pattern 增强系统

| 文件 | 职责 |
|------|------|
| `scorer.py` | Selene 评分，`evaluate_with_feedback()` 方法 |
| `enhancer.py` | Gemini LLM 提示增强，支持 feedback 参数 |
| `enhance_inflatable_prompt.py` | 重试循环，串联评分与增强 |
| `design_patterns.json` | 模式数据库 |

### Selene 服务（远程 Mac）

| 文件 | 位置 | 职责 |
|------|------|------|
| `selene_server.py` | 远程 Mac | FastAPI/uvicorn 服务，LlamaConfig 加载模型 |
| `selene_client.py` | 本地 | 测试客户端 |

## 端口映射

| 服务 | 地址 | 端口 |
|------|------|------|
| Jaaz API | localhost | 8000 |
| Selene (远程) | 100.75.202.111 | 8080 |
| Frontend | localhost | 3000 |

## 环境变量

| 变量 | 值 | 说明 |
|------|-----|------|
| `PYTHONUNBUFFERED` | `1` | 实时日志输出 |
| `SELENE_URL` | `http://100.75.202.111:8080/v1/chat/completions` | Selene 端点 |
| `PASS_THRESHOLD` | `3.5` | Selene 评分通过阈值 |
| `MAX_ENHANCE_ATTEMPTS` | `3` | 最大重试次数 |

## 日志增强点

- `enhance_inflatable_prompt.py` — 每次尝试的候选、评分、反馈、最终选择
- `scorer.py` — Selene 请求与响应
- `enhancer.py` — Gemini 输入/输出
- `StreamProcessor.py` — 英文 prompt 生成

## 模型信息

### Selene（远程 Mac）

- **模型**: AtlaAI/Selene-1-Mini-Llama-3.1-8B
- **格式**: safetensors，4 个 shard
- **大小**: ~15GB
- **路径**: `~/.cache/huggingface/hub/models--AtlaAI--Selene-1-Mini-Llama-3.1-8B/snapshots/427792f1c3e2073cb7da216924fd884b1ba496e0`
- **后端**: MPS (Apple Silicon)
- **加载方式**: `LlamaConfig.from_pretrained()` + `device_map="auto"`

### Gemini（本地/云）

- **提示生成**: `gemini-3.1-flash`
- **Agent**: `gemini-2.5-pro`

## 已完成

- [x] Selene 模型下载并 rsync 到远程 Mac
- [x] Selene server 部署到远程 Mac（端口 8080）
- [x] Sequential prompt 增强流程实现
- [x] Selene 评分集成（4 维度，总分阈值 3.5）
- [x] 反馈重试机制（最多 3 次）
- [x] 详细日志增强
- [x] Prompt 生成模型升级到 gemini-3.1-flash
- [x] 深度代码审查
- [x] 用户认证系统（本地 SQLite + bcrypt，Token 认证）

## 待办

- [ ] 端到端流程验证（Gemini + Selene 集成）
- [ ] 英文 prompt 日志捕获验证
- [ ] image_designer/video_designer 接入主流程

## 相关文件路径

```
/Users/cyberway/ocworkspace/jaaz/
├── server/
│   ├── main.py
│   ├── auth.db
│   ├── chat_service.py
│   ├── services/
│   │   ├── langgraph_service/
│   │   │   ├── agent_service.py
│   │   │   ├── agent_manager.py
│   │   │   ├── StreamProcessor.py
│   │   │   └── configs/image_vide_creator_config.py
│   │   ├── config_service.py
│   │   ├── db_service.py
│   │   ├── tool_service.py
│   │   └── auth_service.py
│   ├── routers/
│   │   └── auth_router.py
│   └── tools/
│       ├── patterns/
│       │   ├── scorer.py
│       │   ├── enhancer.py
│       │   └── design_patterns.json
│       └── enhance_inflatable_prompt.py
├── scripts/
│   ├── selene_server.py
│   └── selene_client.py
├── react/
│   └── (React 前端)
└── docs/
    └── FUNCTIONAL_ARCHITECTURE.md (本文档)
```
