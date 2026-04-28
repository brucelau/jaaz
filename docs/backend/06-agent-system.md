# 06 - Agent 系统

## 概述

Agent 系统基于 **LangGraph** 实现多 Agent 编排，支持 Agent 间 handoff。

## 核心文件

| 文件 | 职责 |
|------|------|
| `agents/langgraph_service/agent_manager.py` | Agent 创建和编排 |
| `agents/langgraph_service/stream_processor.py` | 流式输出处理 |
| `agents/langgraph_service/configs/base_config.py` | 基础配置 + handoff 工具 |
| `agents/langgraph_service/configs/*.py` | 各 Agent 配置 |

## Agent 类型

| Agent | 配置文件 | 职责 |
|-------|---------|------|
| **PlannerAgent** | `planner_config.py` | 任务规划，决定下一步 |
| **ImageVideoCreatorAgent** | `image_vide_creator_config.py` | 图片/视频生成编排 |
| **PneumatEnhancerAgent** | `pneumat_enhancer_config.py` | 充气设计增强 |

## Agent 架构

```
┌─────────────────────────────────────────────────────────────┐
│                     LangGraph Agent                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐                                           │
│  │   Planner   │ ◄────────────────────┐                   │
│  │   Agent     │                      │                    │
│  └──────┬──────┘                      │                    │
│         │                                │                    │
│         │ handoff                       │ handoff            │
│         ▼                                ▼                    │
│  ┌─────────────┐              ┌─────────────────┐          │
│  │   Pneumat   │              │  ImageVideo     │          │
│  │  Enhancer   │──────────────│    Creator      │          │
│  └─────────────┘   handoff    └─────────────────┘          │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                    Tools                              │  │
│  │  write_plan, enhance_prompt, generate_image, etc.   │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Agent 创建流程

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/langgraph_service/agent_manager.py`

```python
class AgentManager:
    def create_agents(self, model, tool_list, system_prompt=""):
        # 1. 分离 image_tools 和 video_tools
        # 2. 创建 PlannerAgent
        planner = _create_langgraph_agent(
            PlannerAgentConfig(),
            model,
            tools,
            system_prompt
        )

        # 3. 创建 ImageVideoCreatorAgent
        image_video_creator = _create_langgraph_agent(
            ImageVideoCreatorAgentConfig(),
            model,
            tools,
            system_prompt
        )

        # 4. 创建 PneumatEnhancerAgent
        pneumat_enhancer = _create_langgraph_agent(
            PneumatEnhancerAgentConfig(),
            model,
            tools,
            system_prompt
        )

        return [planner, image_video_creator, pneumat_enhancer]
```

## Handoff 机制

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/langgraph_service/configs/base_config.py`

```python
def create_handoff_tool(agent_name: str, name=None, description=None):
    """
    创建一个 LangGraph Tool，用于 Agent 间转移控制权
    """
    # 工具名: transfer_to_<agent_name>
    # 调用后，下一个 Agent 接管对话
```

### Planner 的 Handoffs

```python
# planner_config.py
PlannerAgentConfig:
    handoffs = [
        HandoffConfig(
            name="image_video_creator",
            description="转移到图片/视频创建"
        ),
        HandoffConfig(
            name="pneumat_enhancer",
            description="转移到充气设计增强"
        )
    ]
```

## 工具注册到 Agent

```python
# AgentManager.create_agents()
tools = []
for tool_json in tool_list:
    tool = tool_service.get_tool(tool_json['id'])
    if tool:
        tools.append(tool)

# 添加系统工具
tools.extend(tool_service.get_system_tools())

# 创建 Agent 时传入
_create_langgraph_agent(config, model, tools, system_prompt)
```

## 流式处理

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/langgraph_service/stream_processor.py`

```python
class StreamProcessor:
    def process_stream(self, event):
        # 处理 LangGraph 的流式事件
        # 提取 tool_call, delta 等
        # 发送到 WebSocket
```

## Chat Service 调用 Agent

```python
# web/services/chat_service.py

async def handle_chat(request):
    # 1. 获取 Agent
    agents = agent_manager.create_agents(
        model=request.text_model,
        tool_list=request.tool_list,
        system_prompt=request.system_prompt
    )

    # 2. 启动 Agent
    async for event in agents[0].stream(messages):
        # 3. 流式处理
        stream_processor.process(event)
```

---

## 配置文件详解

### base_config.py

```python
class BaseAgentConfig:
    name: str                           # Agent 名称
    tools: list                         # 工具列表
    system_prompt: str                  # 系统提示词
    handoffs: list[HandoffConfig]      # Handoff 配置

class HandoffConfig:
    name: str                           # 目标 Agent 名称
    description: str                    # 描述
```

### planner_config.py

```python
PlannerAgentConfig(BaseAgentConfig):
    name = "planner"
    # 工具: write_plan
    # Handoffs: image_video_creator, pneumat_enhancer
```

### image_vide_creator_config.py

```python
ImageVideoCreatorAgentConfig(BaseAgentConfig):
    name = "image_video_creator"
    # 工具: 图片/视频生成工具
    # Handoffs: 无
```

### pneumat_enhancer_config.py

```python
PneumatEnhancerAgentConfig(BaseAgentConfig):
    name = "pneumat_enhancer"
    # 工具: 充气设计增强工具
    # Handoffs: image_video_creator
```

---

## 系统提示词

Agent 的系统提示词从以下位置加载：
- `agents/langgraph_service/configs/prompts/` (推测)

提示词组成：
1. 基础系统提示词
2. 额外的 prompt 文件
3. 工具描述
