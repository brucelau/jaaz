# 02 - 目录结构

## 完整目录结构

```
server/
├── main.py                          # ✅ FastAPI 入口
├── core/
│   ├── routers.py                  # ✅ 路由注册中心
│   ├── lifespan.py                 # ✅ 生命周期管理
│   └── static.py                  # 静态文件服务
│
├── web/
│   ├── routers/                    # ✅ API 路由
│   │   ├── __init__.py
│   │   ├── auth_router.py         # 认证 (/api/auth/*)
│   │   ├── root_router.py         # 根路由 (/api/*)
│   │   ├── canvas_router.py       # Canvas (/api/canvas/*)
│   │   ├── chat_router.py         # 聊天 (/api/chat, /api/magic)
│   │   ├── image_router.py        # 图片 (/api/image, /api/file/*)
│   │   ├── workspace_router.py    # 工作区 (/api/workspace/*)
│   │   ├── settings_router.py     # 设置 (/api/settings/*)
│   │   ├── config_router.py       # 配置 (/api/config/*)
│   │   ├── tool_confirmation_router.py  # 工具确认
│   │   └── ssl_test_router.py     # SSL 测试
│   │
│   ├── services/                   # ✅ 服务层
│   │   ├── auth_service.py         # 认证 (注册/登录/Token)
│   │   ├── config_service.py       # 配置 (config.toml)
│   │   ├── tool_service.py        # 工具注册表
│   │   ├── chat_service.py        # 聊天处理
│   │   ├── magic_service.py       # 魔法生成
│   │   ├── knowledge_service.py   # 知识库
│   │   ├── log_service.py         # 日志
│   │   ├── jaaz_service.py        # Jaaz 云 API 客户端
│   │   ├── comfyui_execution_service.py  # ComfyUI 执行
│   │   └── stream_service.py      # 流式任务注册表
│   │
│   ├── websocket/                  # ✅ WebSocket
│   │   ├── __init__.py
│   │   ├── manager.py             # Socket.IO AsyncServer
│   │   ├── handlers.py            # 事件处理 (connect/join_session/disconnect/ping)
│   │   └── emitter.py             # 广播辅助
│   │
│   └── models/
│       ├── tool_model.py          # 工具 Pydantic 模型
│       └── config_model.py         # 配置 Pydantic 模型
│
├── database/                        # ✅ 数据库层
│   ├── db_service.py              # 数据库服务 (连接池 + CRUD)
│   ├── settings_service.py         # 设置服务 (JSON)
│   ├── localmanus.db             # SQLite 数据库文件
│   └── migrations/                # 数据库迁移
│       ├── __init__.py
│       ├── manager.py             # 迁移管理器
│       ├── v1_initial_schema.py   # 初始 schema
│       ├── v2_add_canvases.py    # 添加 canvases 表
│       ├── v3_add_comfy_workflow.py  # 添加 comfy_workflows 表
│       ├── v4_add_performance_indexes.py  # 性能索引
│       └── v5_add_auth.py        # 添加 auth 表
│
├── agents/                         # ✅ Agent 系统
│   ├── __init__.py
│   ├── mcp_client.py              # MCP 客户端 (Claude 工具链)
│   ├── tool_confirmation_manager.py  # 工具确认管理器
│   │
│   ├── langgraph_service/          # LangGraph Agent
│   │   ├── __init__.py
│   │   ├── agent_manager.py       # Agent 管理器 (创建/编排)
│   │   ├── stream_processor.py    # 流式处理器
│   │   └── configs/              # Agent 配置
│   │       ├── __init__.py
│   │       ├── base_config.py     # 基础配置 + handoff 工具
│   │       ├── planner_config.py  # Planner Agent
│   │       ├── image_designer_config.py  # ImageDesigner
│   │       ├── video_designer_config.py  # VideoDesigner
│   │       ├── image_vide_creator_config.py  # ImageVideoCreator
│   │       └── pneumat_enhancer_config.py  # PneumatEnhancer
│   │
│   ├── tools/                     # 工具实现
│   │   ├── write_plan.py         # 写计划工具
│   │   ├── generate_image_by_*.py  # 图片生成工具 (多种 Provider)
│   │   ├── generate_video_by_*.py  # 视频生成工具
│   │   ├── image_providers/       # 图片 Provider
│   │   │   ├── __init__.py
│   │   │   ├── jaaz_provider.py   # Jaaz Provider
│   │   │   ├── openai_provider.py  # OpenAI Provider
│   │   │   └── nano_banana_provider.py
│   │   ├── utils/
│   │   │   ├── image_generation_core.py  # 图片生成核心
│   │   │   ├── image_utils.py     # 图片工具
│   │   │   └── canvas.py         # Canvas 工具
│   │   └── video_generation/
│   │       ├── video_generation_core.py  # 视频生成核心
│   │       └── video_canvas_utils.py  # 视频 Canvas 工具
│   │
│   └── workflow/                  # 工作流 JSON
│       ├── default_comfy_t2i_workflow.json
│       └── flux_comfy_workflow.json
│
├── models/                         # (备用模型目录)
│
└── requirements.txt               # 依赖
```

## 目录分类说明

### 入口文件
| 文件 | 职责 |
|------|------|
| `main.py` | FastAPI 入口，路由注册，Socket.IO 挂载，启动 uvicorn |

### 核心 (core/)
| 文件 | 职责 |
|------|------|
| `routers.py` | 集中注册所有路由到 FastAPI app |
| `lifespan.py` | 生命周期管理，初始化配置和工具 |

### Web 路由 (web/routers/)
| 文件 | 前缀 | 职责 |
|------|------|------|
| `auth_router.py` | `/api/auth` | 注册/登录/Token 刷新 |
| `root_router.py` | `/api` | 列表模型/工具，会话，Billing |
| `canvas_router.py` | `/api/canvas` | Canvas CRUD |
| `chat_router.py` | `/api` | 聊天/取消/魔法 |
| `image_router.py` | `/api` | 图片上传/服务 |
| `workspace_router.py` | `/api` | 文件系统操作 |
| `settings_router.py` | `/api/settings` | 设置/代理/知识库 |
| `config_router.py` | `/api/config` | Provider 配置 |
| `tool_confirmation_router.py` | `/api` | 工具调用确认 |
| `ssl_test_router.py` | `/api` | SSL 测试 |

### Web 服务 (web/services/)
| 文件 | 职责 |
|------|------|
| `auth_service.py` | 用户认证，Token 管理 (bcrypt + SQLite) |
| `config_service.py` | config.toml 加载，Provider 配置 |
| `tool_service.py` | 工具注册表，动态工具加载 |
| `chat_service.py` | 聊天处理，LangGraph 编排 |
| `magic_service.py` | 魔法生成编排 |
| `knowledge_service.py` | 知识库数据访问 |
| `log_service.py` | 结构化日志 |
| `jaaz_service.py` | Jaaz 云 API 客户端 |
| `comfyui_execution_service.py` | ComfyUI 工作流执行 |
| `stream_service.py` | 流式任务注册表 (session_id → task) |

### WebSocket (web/websocket/)
| 文件 | 职责 |
|------|------|
| `manager.py` | Socket.IO AsyncServer 单例 |
| `handlers.py` | connect/join_session/disconnect/ping 处理器 |
| `emitter.py` | session_update 广播辅助 |

### 数据库 (database/)
| 文件 | 职责 |
|------|------|
| `db_service.py` | 连接池，CRUD，迁移执行 |
| `settings_service.py` | JSON 设置读写 |
| `migrations/` | 版本化数据库迁移 |

### Agent 系统 (agents/)
| 文件 | 职责 |
|------|------|
| `agent_manager.py` | LangGraph Agent 创建和编排 |
| `stream_processor.py` | Agent 流式输出处理 |
| `configs/*.py` | 各 Agent 类型的配置 |
| `tools/*.py` | 具体工具实现 |
| `image_providers/*.py` | 图片 Provider 实现 |
| `video_generation/*.py` | 视频生成实现 |
