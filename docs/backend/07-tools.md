# 07 - 工具详解

## 概述

工具系统包含两大类：
1. **系统工具** - 内置于 Agent 系统
2. **Provider 工具** - 外部 Provider 的图片/视频生成

## 核心文件

| 文件 | 职责 |
|------|------|
| `web/services/tool_service.py` | Facade 门面 (委托给其他模块) |
| `agents/tool_registry.py` | 工具注册表 (内存存储) |
| `agents/tool_loader.py` | 工具加载器 (配置/DB加载) |
| `agents/providers.py` | Provider 工具映射 |
| `agents/tools/write_plan.py` | 写计划工具 |
| `agents/tools/generate_image_by_*.py` | 图片生成工具 |
| `agents/tools/generate_video_by_*.py` | 视频生成工具 |

## 架构 (重构后)

```
web/services/tool_service.py (Facade)
└── agents/
    ├── tool_registry.py (内存存储)
    │   └── tools: Dict[str, ToolInfo]
    ├── tool_loader.py (加载逻辑)
    │   ├── load_required_system_tools()
    │   ├── load_provider_tools()
    │   └── load_comfyui_tools()
    └── providers.py (常量映射)
        └── PROVIDER_TOOLS
```

## tool_registry.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/tool_registry.py`

内存工具注册表：

```python
class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}

    def register(self, tool_id: str, tool_info: ToolInfo)
    def unregister(self, tool_id: str)
    def get(self, tool_id: str) -> ToolInfo | None
    def get_tool_function(self, tool_id: str) -> BaseTool | None
    def get_all(self) -> Dict[str, ToolInfo]
    def get_by_provider(self, provider: str) -> Dict[str, ToolInfo]
    def get_system_tools(self) -> List[Any]
    def clear(self)
```

## tool_loader.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/tool_loader.py`

工具加载器：

```python
class ToolLoader:
    @staticmethod
    def load_required_system_tools() -> Dict[str, ToolInfo]
        # 加载内置系统工具

    @staticmethod
    def load_provider_tools(tool_mapping) -> Dict[str, ToolInfo]
        # 根据配置加载 Provider 工具

    @staticmethod
    async def load_comfyui_tools() -> Dict[str, ToolInfo]
        # 从数据库加载 ComfyUI 工作流

    @staticmethod
    async def initialize(tool_mapping, registry)
        # 初始化注册表
```

## providers.py

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/providers.py`

Provider 工具映射常量：

```python
PROVIDER_TOOLS = {
    "generate_image_by_ideogram": {
        "display_name": "Ideogram",
        "type": "image",
        "provider": "ideogram",
    },
    "generate_image_by_doubao_seedream_3_volces": {
        "display_name": "Doubao Seedream 3 by volces",
        "type": "image",
        "provider": "volces",
    },
    # ...
}
```

---

## 系统工具

### write_plan

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/tools/write_plan.py`

生成任务执行计划：

```python
@tool("write_plan", description="Write a plan for the user task")
def write_plan(task: str) -> str:
    """
    生成结构化执行计划
    """
    # 分析任务
    # 生成步骤
    return plan_document
```

---

## 图片生成工具

### 工具列表

| 工具名 | Provider | 文件 |
|--------|----------|------|
| `generate_image_by_ideogram` | Ideogram | `generate_image_by_ideogram3_bal_jaaz.py` |
| `generate_image_by_flux_1_1_pro` | Flux | `generate_image_by_flux_1_1_pro_jaaz.py` |
| `generate_image_by_flux_kontext` | Flux | `generate_image_by_flux_kontext_jaaz.py` |
| `generate_image_by_recraft` | Recraft | `generate_image_by_recraft_v3_jaaz.py` |
| `generate_image_by_imagen` | Imagen | `generate_image_by_imagen_4_jaaz.py` |
| `generate_image_by_doubao` | Doubao | `generate_image_by_doubao_seedream_3_jaaz.py` |
| `generate_image_by_gpt_image` | GPT Image | `generate_image_by_gpt_image_1_jaaz.py` |
| `generate_image_by_midjourney` | Midjourney | `generate_image_by_midjourney_jaaz.py` |

### 图片生成核心

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/tools/utils/image_generation_core.py`

```python
IMAGE_PROVIDERS = {
    "openai": OpenAIProvider,
    "replicate": ReplicateProvider,
    "volces": VolcesProvider,
    "wavespeed": WavespeedProvider,
    "ideogram": IdeogramProvider,
    "nano_banana": NanoBananaProvider,
    # ...
}

def generate_image(model_info: dict, prompt: str, **kwargs):
    provider_class = IMAGE_PROVIDERS.get(model_info["provider"])
    provider = provider_class(model_info)
    return provider.generate(prompt, **kwargs)
```

### 图片 Provider

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/tools/image_providers/`

| Provider | 文件 | 说明 |
|----------|------|------|
| Jaaz | `jaaz_provider.py` | Jaaz 云服务 |
| OpenAI | `openai_provider.py` | DALL-E |
| NanoBanana | `nano_banana_provider.py` | 其他源 |

---

## 视频生成工具

### 工具列表

| 工具名 | Provider | 文件 |
|--------|----------|------|
| `generate_video_by_kling_v2` | Kling | `generate_video_by_kling_v2_jaaz.py` |
| `generate_video_by_veo3_fast` | Veo3 | `generate_video_by_veo3_fast_jaaz.py` |
| `generate_video_by_seedance` | Seedance | `generate_video_by_seedance_v1_jaaz.py` |
| `generate_video_by_hailuo_02` | Hailuo | `generate_video_by_hailuo_02_jaaz.py` |

### 视频生成核心

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/agents/tools/video_generation/video_generation_core.py`

```python
VIDEO_PROVIDERS = {
    "kling": KlingProvider,
    "veo3": Veo3Provider,
    "seedance": SeedanceProvider,
    "hailuo": HailuoProvider,
}

def generate_video(model_info: dict, prompt: str, **kwargs):
    provider_class = VIDEO_PROVIDERS.get(model_info["provider"])
    provider = provider_class(model_info)
    return provider.generate(prompt, **kwargs)
```

---

## 工具调用流程

```
Agent 决定调用工具
        │
        ▼
tool_service.get_tool(tool_name)
        │
        ▼
调用 tool_function(prompt, **kwargs)
        │
        ▼
Provider 生成图片/视频
        │
        ▼
返回结果给 Agent
        │
        ▼
Agent 继续执行或返回用户
```

---

## 工具装饰器

```python
from langchain_core.tools import tool

@tool("generate_image", description="Generate an image")
def generate_image(prompt: str, **kwargs) -> str:
    """图片生成"""
    # 实现
    return image_url
```

---

## ComfyUI 工作流工具

工作流存储在数据库，可动态注册为工具：

```python
# settings_router.py
POST /api/settings/comfyui/create_workflow

# tool_service.py
def register_comfy_tools():
    workflows = db.list_comfy_workflows()
    for wf in workflows:
        tool = build_tool_from_workflow(wf)
        register_tool(f"comfyui_{wf.id}", tool)
```
