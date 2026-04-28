# 01 - 项目概述与技术栈

## 一、项目概述

James 是一个**桌面 AI 设计 Agent 应用**，前端基于 React + TypeScript + Vite 构建，使用 TanStack Router 进行路由管理，Socket.IO 进行实时通信。

**项目路径**: `/Users/cyberway/ocworkspace/James/react`

### 核心功能
- 🎨 **Canvas 画布** - 基于 Excalidraw 的可视化设计画布
- 💬 **AI 聊天** - 与 AI Agent 对话，支持工具调用
- 🖼️ **图片生成** - 集成多种 AI 图片生成模型
- 🎬 **视频生成** - AI 视频生成能力
- 📚 **知识库** - 用户知识管理
- 🤖 **Agent 配置** - 自定义 AI Agent 行为

## 二、技术栈

### 核心框架
| 类别 | 技术 | 版本/说明 |
|------|------|----------|
| 框架 | React | 18.x |
| 语言 | TypeScript | 强类型 |
| 构建工具 | Vite | 快速开发 |
| 路由 | TanStack Router | 文件路由模式 |

### 状态管理与网络
| 类别 | 技术 |
|------|------|
| 状态管理 | React Query + Context |
| 实时通信 | Socket.IO Client |
| 事件总线 | Mitt |
| HTTP 客户端 | Fetch API |

### UI 与样式
| 类别 | 技术 |
|------|------|
| UI 框架 | Tailwind CSS |
| UI 组件库 | Radix UI |
| 图标 | Lucide React |
| 动画 | Framer Motion |
| Toast | Sonner |
| 图片预览 | react-photo-view |

### 可视化
| 类别 | 技术 |
|------|------|
| 画布 | Excalidraw |
| 国际化 | i18next |

### 数据持久化
| 类别 | 技术 |
|------|------|
| React Query 缓存 | IndexedDB (idb) |
| 本地存储 | localStorage |

### Electron 集成
| 类别 | 技术 |
|------|------|
| 桌面框架 | Electron |
| 主进程通信 | window.electronAPI |

## 三、架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                     Electron 主进程                          │
│              (Python FastAPI 后端 + Electron)                 │
└─────────────────────────────────────────────────────────────┘
                              │
                    HTTP / WebSocket
                              │
┌─────────────────────────────────────────────────────────────┐
│                     React 前端                               │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │ TanStack    │  │ React Query │  │   Socket     │       │
│  │   Router    │  │  + Context  │  │   Context    │       │
│  └─────────────┘  └─────────────┘  └─────────────┘       │
├─────────────────────────────────────────────────────────────┤
│                     UI Components                            │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐     │
│  │ Chat  │ │Canvas │ │Knowledge│ │Assets │ │ Agent │     │
│  └───────┘ └───────┘ └───────┘ └───────┘ └───────┘     │
└─────────────────────────────────────────────────────────────┘
```

## 四、环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `VITE_JAAZ_BASE_API_URL` | 后端 API 地址 | `http://127.0.0.1:57988` |
| `VITE_PUBLIC_POSTHOG_KEY` | PostHog Analytics Key | - |
| `VITE_PUBLIC_POSTHOG_HOST` | PostHog Host | - |

## 五、快速开始

```bash
# 安装依赖
cd James/react
npm install

# 开发模式
npm run dev

# 构建生产版本
npm run build
```

## 六、端口配置

| 服务 | 端口 |
|------|------|
| 前端开发服务器 | 5174 |
| 后端 API | 57988 |
| Socket.IO | 57988 (与后端共用) |
