# 01 - 项目概述与技术栈

## 一、项目概述

Jaaz 后端是一个基于 **Python FastAPI** 构建的 AI 设计 Agent 服务端，提供：
- RESTful API 接口
- Socket.IO 实时通信
- LangGraph 多 Agent 编排
- 多 Provider 图片/视频生成
- 本地 SQLite 数据库

**项目路径**: `/Users/cyberway/ocworkspace/jaaz/server`

### 核心功能
- 🎨 **图片生成** - Flux, Ideogram, Midjourney, DALL-E 等
- 🎬 **视频生成** - Kling, Veo3, Seedance, Hailuo 等
- 🤖 **AI Agent** - 基于 LangGraph 的多 Agent 编排
- 💬 **聊天系统** - 实时流式输出 + 工具调用
- 📁 **Canvas** - 设计画布数据管理
- 📚 **知识库** - 知识管理增强 AI 回答

## 二、技术栈

### Web 框架与服务器
| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| ASGI 服务器 | Uvicorn |
| 实时通信 | Socket.IO (AsyncServer) |
| CORS | FastAPI CORS Middleware |

### 数据层
| 类别 | 技术 |
|------|------|
| 数据库 | SQLite |
| 异步 DB | aiosqlite |
| 数据库连接池 | 自定义 ConnectionPool |

### AI / Agent
| 类别 | 技术 |
|------|------|
| Agent 框架 | LangGraph |
| LLM 集成 | OpenAI, Gemini, Ollama, Claude (MCP) |
| 图片生成 | 多 Provider 框架 |
| 视频生成 | 多 Provider 框架 |

### 认证与安全
| 类别 | 技术 |
|------|------|
| 密码哈希 | bcrypt |
| Token 管理 | SQLite 存储 + 7天过期 |

### 配置与日志
| 类别 | 技术 |
|------|------|
| 配置格式 | TOML + JSON |
| 日志 | 结构化日志 (JSON/Console) |

## 三、架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     Electron 主进程                          │
│              (启动 Python FastAPI 后端)                       │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
        HTTP/REST                      WebSocket (Socket.IO)
              │                               │
              ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI 应用                              │
├─────────────────────────────────────────────────────────────┤
│  CORS Middleware                                           │
├─────────────────────────────────────────────────────────────┤
│  Routers (11 个路由模块)                                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │ auth    │ │ root    │ │ canvas  │ │ chat    │ ...     │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
├─────────────────────────────────────────────────────────────┤
│  Services (服务层)                                          │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐        │
│  │auth     │ │config   │ │tool     │ │chat     │ ...     │
│  └─────────┘ └─────────┘ └─────────┘ └─────────┘        │
├─────────────────────────────────────────────────────────────┤
│  LangGraph Agent System                                    │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐                      │
│  │Planner  │ │Image    │ │Pneumat  │                      │
│  │Agent    │ │Creator  │ │Enhancer │                      │
│  └─────────┘ └─────────┘ └─────────┘                      │
├─────────────────────────────────────────────────────────────┤
│  Tools (图片/视频生成工具)                                    │
├─────────────────────────────────────────────────────────────┤
│  Database (SQLite) + Settings (JSON)                        │
└─────────────────────────────────────────────────────────────┘
```

## 四、启动入口

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/main.py`

```python
# 启动命令
python main.py --port 57988

# 关键流程
1. 创建 FastAPI app (lifespan=lifespan)
2. 添加 CORS 中间件
3. register_routers(app) - 注册所有路由
4. setup_static_files(app) - 提供前端静态文件
5. Socket.IO 挂载到 /socket.io
6. uvicorn.run(app, port=PORT)
```

## 五、端口配置

| 服务 | 端口 |
|------|------|
| FastAPI 后端 | 57988 (默认) |
| Socket.IO | 57988 (与 HTTP 共用) |
| 前端静态文件 | /static 或 / |

## 六、关键文件速查

| 功能 | 文件路径 |
|------|---------|
| 入口 | `main.py` |
| 路由注册 | `core/routers.py` |
| 生命周期 | `core/lifespan.py` |
| 认证服务 | `web/services/auth_service.py` |
| 配置服务 | `web/services/config_service.py` |
| 工具服务 | `web/services/tool_service.py` |
| 数据库 | `database/db_service.py` |
| Agent 管理 | `agents/langgraph_service/agent_manager.py` |
| WebSocket | `web/websocket/manager.py` |
