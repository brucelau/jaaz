# James 后端代码文档

## 文档索引

本文档分为以下模块：

| 文档 | 内容 |
|------|------|
| [01-overview.md](01-overview.md) | 项目概述、技术栈、架构概览 |
| [02-directory-structure.md](02-directory-structure.md) | 完整目录结构与文件说明 |
| [03-api-routes.md](03-api-routes.md) | API 路由详解 |
| [04-authentication.md](04-authentication.md) | 认证系统 |
| [05-database.md](05-database.md) | 数据库层 (SQLite + 迁移) |
| [06-agent-system.md](06-agent-system.md) | LangGraph Agent 系统 |
| [07-tools.md](07-tools.md) | 工具详解 (图片/视频生成) |
| [08-websocket.md](08-websocket.md) | Socket.IO 实时通信 |
| [09-config.md](09-config.md) | 配置系统 (config.toml) |
| [10-data-flow.md](10-data-flow.md) | 核心数据流 |
| [11-types.md](11-types.md) | Pydantic 类型定义 |

---

## 技术栈

| 类别 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| 异步服务器 | Uvicorn + Socket.IO |
| 数据库 | SQLite (aiosqlite) |
| Agent 框架 | LangGraph |
| AI 集成 | OpenAI, Gemini, Ollama 等 |
| 实时通信 | Socket.IO (AsyncServer) |
| 认证 | bcrypt + JWT-like Token |

## 启动方式

```bash
cd James/server
pip install -r requirements.txt
python main.py --port 57988
```

---

*生成时间: 2026-04-28*
