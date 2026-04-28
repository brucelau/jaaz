# 02 - 目录结构

## 完整目录结构

```
react/src/
├── main.tsx                    # ✅ 应用入口
├── App.tsx                     # ✅ 根组件
├── index.ts                    # ✅ 组件统一导出
├── route-tree.gen.ts           # TanStack Router 生成路由树
├── constants.ts                # ✅ 全局常量 (API地址、模型映射、系统提示词)
│
├── routes/                     # ✅ 路由页面
│   ├── __root.tsx             # 根路由布局 (Outlet + DevTools)
│   ├── index.tsx              # 首页 / (Canvas 创建入口)
│   ├── canvas.$id.tsx         # Canvas 编辑器 /canvas/:id
│   ├── knowledge.tsx           # 知识库 /knowledge
│   ├── agent_studio.tsx        # Agent 配置 /agent_studio
│   └── assets.tsx              # 资源管理 /assets
│
├── components/                  # ✅ UI 组件
│   ├── auth/                   # 认证相关
│   │   ├── LoginDialog.tsx     # 登录对话框 (登录/注册/设备码)
│   │   ├── UserMenu.tsx        # 用户菜单
│   │   └── PointsDisplay.tsx   # 积分显示
│   │
│   ├── canvas/                 # Canvas 画布模块
│   │   ├── CanvasExcali.tsx    # Excalidraw 画布核心
│   │   ├── CanvasHeader.tsx    # Canvas 顶部栏 (名称编辑)
│   │   ├── CanvasExport.tsx    # 导出功能
│   │   ├── VideoElement.tsx    # 视频元素
│   │   ├── menu/               # 工具菜单
│   │   │   ├── CanvasMenuIcon.tsx
│   │   │   ├── CanvasToolMenu.tsx
│   │   │   ├── CanvasViewMenu.tsx
│   │   │   └── CanvasMenuButton.tsx
│   │   └── pop-bar/            # 弹出工具栏
│   │       ├── CanvasPopbar.tsx
│   │       ├── CanvasMagicGenerator.tsx
│   │       └── CanvasPopbarContainer.tsx
│   │
│   ├── chat/                   # 聊天模块
│   │   ├── Chat.tsx            # ✅ 核心聊天组件 (777行)
│   │   ├── ChatTextarea.tsx    # 聊天输入框
│   │   ├── ChatHistory.tsx     # 聊天历史
│   │   ├── ChatMagicGenerator.tsx  # 魔法生成
│   │   ├── ModelSelectorV2.tsx # 模型选择器 V2
│   │   ├── ModelSelectorV3.tsx # 模型选择器 V3
│   │   ├── SessionSelector.tsx  # 会话选择器
│   │   ├── Spinner.tsx         # 加载动画
│   │   ├── IconCarousel.tsx    # 图标轮播
│   │   ├── MultiChoicePrompt.tsx # 多选提示
│   │   ├── ShareTemplateDialog.tsx # 分享模板
│   │   ├── ToolcallProgressUpdate.tsx # 工具调用进度
│   │   └── Message/             # 消息展示组件
│   │       ├── Regular.tsx      # 普通文本消息
│   │       ├── Image.tsx        # 图片消息
│   │       ├── TextFoldTag.tsx  # 折叠文本
│   │       ├── ToolCallTag.tsx  # 工具调用标签
│   │       ├── ToolCallContent.tsx # 工具调用内容
│   │       ├── WritePlanToolcall.tsx # 写计划工具
│   │       └── MixedContent.tsx # 混合内容 (文本+图片)
│   │
│   ├── knowledge/              # 知识库模块
│   │   ├── Knowledge.tsx       # 知识库主组件
│   │   └── Editor.tsx          # 知识编辑器
│   │
│   ├── material/               # 素材管理
│   │   ├── MaterialManager.tsx  # 素材管理器
│   │   └── FilePreviewModal.tsx # 文件预览弹窗
│   │
│   ├── agent_studio/           # Agent 配置
│   │   ├── AgentStudio.tsx     # Agent 工作台
│   │   ├── AgentNode.tsx       # Agent 节点
│   │   └── AgentSettings.tsx   # Agent 设置
│   │
│   ├── comfyui/                # ComfyUI 相关
│   │   ├── InstallComfyUIDialog.tsx
│   │   ├── InstallProgressDialog.tsx
│   │   └── UninstallProgressDialog.tsx
│   │
│   ├── theme/                  # 主题系统
│   │   ├── ThemeProvider.tsx   # 主题 Provider
│   │   └── ThemeButton.tsx     # 主题切换按钮
│   │
│   ├── common/                 # 通用组件
│   │   ├── DialogContent.tsx   # 对话框内容
│   │   ├── ErrorBoundary.tsx   # 错误边界
│   │   ├── LanguageSwitcher.tsx # 语言切换
│   │   ├── UpdateNotificationDialog.tsx # 更新通知
│   │   ├── Blur.tsx           # 模糊背景
│   │   └── NotificationPanel.tsx # 通知面板
│   │
│   ├── settings/               # 设置相关
│   │   └── dialog.tsx          # 设置对话框
│   │
│   └── ui/                     # ✅ UI 原语组件 (Radix UI)
│       ├── button.tsx
│       ├── input.tsx
│       ├── dialog.tsx
│       ├── card.tsx
│       ├── resizable.tsx       # 可调整大小面板
│       ├── scroll-area.tsx     # 滚动区域
│       ├── shiny-text.tsx      # 闪光文字
│       ├── select.tsx
│       ├── tabs.tsx
│       ├── dropdown-menu.tsx
│       ├── separator.tsx
│       ├── tooltip.tsx
│       ├── sonner.tsx          # Toast 通知
│       └── ...                  # 其他组件
│
├── contexts/                    # ✅ React Context
│   ├── AuthContext.tsx         # 认证状态管理
│   ├── socket.tsx              # Socket.IO 上下文
│   ├── canvas.tsx              # Canvas 上下文
│   └── configs.tsx              # 配置上下文
│
├── hooks/                      # 自定义 Hooks
│   ├── use-theme.ts           # 主题管理
│   ├── use-balance.ts         # 余额查询
│   ├── use-mobile.ts          # 移动端检测
│   ├── use-language.ts         # 语言管理
│   ├── use-debounce.ts        # 防抖
│   └── use-notifications.ts   # 通知管理
│
├── api/                        # ✅ API 客户端
│   ├── auth.ts                # 认证 API (286行)
│   ├── chat.ts                # 聊天 API
│   ├── canvas.ts              # Canvas API
│   ├── model.ts               # 模型 API
│   ├── settings.ts            # 设置 API
│   ├── upload.ts              # 上传 API
│   ├── knowledge.ts           # 知识库 API (247行)
│   ├── magic.ts               # 魔法功能 API
│   ├── billing.ts             # 计费 API
│   └── config.ts              # 配置 API
│
├── lib/                        # ✅ 工具库
│   ├── socket.ts              # Socket.IO 管理器 (189行)
│   ├── event.ts               # 事件总线 (mitt)
│   ├── utils.ts               # 通用工具函数
│   └── notifications.ts       # 通知工具
│
├── types/                      # TypeScript 类型
│   ├── types.ts               # 全局类型定义
│   └── socket.ts              # Socket 事件类型
│
├── i18n/                       # 国际化
│   ├── index.ts               # i18n 配置
│   ├── README.md
│   └── locales/
│       ├── en/                 # 英文翻译
│       │   ├── common.json
│       │   ├── canvas.json
│       │   ├── chat.json
│       │   ├── home.json
│       │   └── settings.json
│       └── zh-CN/              # 中文翻译
│           ├── common.json
│           ├── canvas.json
│           ├── chat.json
│           ├── home.json
│           └── settings.json
│
├── assets/                     # 静态资源
│   ├── style/                 # 全局样式
│   │   ├── index.css          # 主样式
│   │   ├── App.css            # App 样式
│   │   ├── canvas.css         # Canvas 样式
│   │   ├── animations.css     # 动画
│   │   └── shiny-text.css     # 闪光文字样式
│   └── jaaz.png               # Logo
│
└── index.d.ts                 # 全局类型声明 (Electron API)
```

## 目录分类说明

### 入口文件
| 文件 | 职责 |
|------|------|
| `main.tsx` | React 应用入口，包裹 SocketProvider + PostHogProvider |
| `App.tsx` | 根组件，初始化所有 Provider 和路由 |
| `index.ts` | 统一导出所有 UI 组件 |
| `constants.ts` | 全局常量 (API URL、模型映射、系统提示词) |

### 路由文件 (routes/)
| 文件 | 路由 | 页面 |
|------|------|------|
| `__root.tsx` | / | 根布局 |
| `index.tsx` | / | 首页 |
| `canvas.$id.tsx` | /canvas/:id | Canvas 编辑器 |
| `knowledge.tsx` | /knowledge | 知识库 |
| `agent_studio.tsx` | /agent_studio | Agent 配置 |
| `assets.tsx` | /assets | 资源管理 |

### 核心 Context
| Context | 职责 |
|---------|------|
| `AuthContext` | 用户认证状态 |
| `SocketContext` | Socket.IO 连接状态 |
| `CanvasContext` | Canvas 画布状态 |
| `ConfigsContext` | 应用配置 (initCanvas 等) |

### 核心 API (api/)
| API | 职责 |
|-----|------|
| `auth.ts` | 登录/注册/Token 管理 |
| `chat.ts` | 消息发送/接收 |
| `canvas.ts` | Canvas CRUD |
| `model.ts` | 模型列表 |
| `knowledge.ts` | 知识库 CRUD |
| `config.ts` | Provider 配置 |
