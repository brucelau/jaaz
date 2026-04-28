# 09 - 配置系统

## 概述

配置系统管理 Provider 配置和全局设置，支持 TOML 文件和环境变量覆盖。

## 核心文件

| 文件 | 职责 |
|------|------|
| `web/services/config_service.py` | config.toml 加载/保存 |
| `database/settings_service.py` | settings.json 管理 |
| `core/lifespan.py` | 启动时初始化 |

## 配置目录

```python
SERVER_DIR = <jaaz>/server
CONFIG_DIR = <SERVER_DIR>/config
CONFIG_FILE = <CONFIG_DIR>/config.toml
DB_DIR = <SERVER_DIR>/database
USER_DATA_DIR = <CONFIG_DIR>/user_data
FILES_DIR = <CONFIG_DIR>/files
```

## config.toml (Provider 配置)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/services/config_service.py`

### 默认 Provider 配置

```python
DEFAULT_PROVIDERS_CONFIG = {
    "comfyui": {
        "name": "ComfyUI",
        "type": "image",
        "api_key": "",
        "base_url": "http://127.0.0.1:8188"
    },
    "minimax": {
        "name": "MiniMax",
        "type": "video",
        "api_key": "",
        "base_url": ""
    },
    "openai": {
        "name": "OpenAI",
        "type": "text",
        "api_key": "",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini"]
    },
    "gemini": {
        "name": "Google Gemini",
        "type": "text",
        "api_key": "",
        "base_url": "https://generativelanguage.googleapis.com",
        "models": ["gemini-1.5-flash", "gemini-1.5-pro"]
    }
}
```

### config.toml 格式

```toml
[jaaz]
api_key = "xxx"
base_url = "https://api.jaaz.app"

[openai]
api_key = "sk-xxx"
base_url = "https://api.openai.com/v1"
models = ["gpt-4o", "gpt-4o-mini"]

[comfyui]
base_url = "http://127.0.0.1:8188"
```

## ConfigService

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/web/services/config_service.py`

```python
class ConfigService:
    def __init__(self):
        self.app_config = DEFAULT_PROVIDERS_CONFIG.copy()
        self.config_file = CONFIG_FILE

    async def initialize(self):
        """初始化配置"""
        if not os.path.exists(self.config_file):
            # 写入默认配置
            await self._write_config(self.app_config)
        else:
            # 加载并合并
            loaded = await self._load_config()
            self.app_config = self._merge_config(loaded)

    def get_config(self) -> dict:
        return self.app_config

    def update_config(self, data: dict):
        """更新配置并保存"""
        self._merge_config(data)
        self._write_config(self.app_config)
```

### 配置更新流程

```
POST /api/config
        │
        ▼
config_service.update_config(data)
        │
        ├── 深合并到 app_config
        │
        ├── 写入 config.toml
        │
        └── 触发 tool_service.initialize()
                │
                └── 重新加载 Provider 工具
```

## 环境变量覆盖

```python
# 优先使用环境变量
MINIMAX_URL = os.getenv("MINIMAX_URL")
OPENAI_URL = os.getenv("OPENAI_URL")
GEMINI_URL = os.getenv("GEMINI_URL")
BASE_API_URL = os.getenv("BASE_API_URL", "http://127.0.0.1:57988")
```

## 设置 (settings.json)

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/database/settings_service.py`

### 存储位置

```python
SETTINGS_FILE = <CONFIG_DIR>/settings.json
```

### 默认设置

```json
{
  "proxy": "system",
  "enabled_knowledge": [],
  "enabled_knowledge_data": []
}
```

### SettingsService

```python
class SettingsService:
    def get_settings(self) -> dict:
        """获取设置 (合并默认值)"""
        raw = self._load()
        return deep_merge(DEFAULT_SETTINGS, raw)

    def update_settings(self, data: dict):
        """更新设置 (深合并)"""
        current = self._load()
        updated = deep_merge(current, data)
        self._save(updated)

    def get_proxy_config(self) -> str:
        return self.get_settings().get("proxy", "system")

    def get_enabled_knowledge_data(self) -> list:
        return self.get_settings().get("enabled_knowledge_data", [])
```

## 生命周期初始化

**文件**: `/Users/cyberway/ocworkspace/jaaz/server/core/lifespan.py`

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    await config_service.initialize()
    await tool_service.initialize()

    # 广播初始化完成
    await broadcast_init_done()

    yield

    # 关闭时
    # 清理资源
```

## 配置获取流程

```
应用启动
    │
    ▼
lifespan.initialize()
    │
    ├── config_service.initialize()
    │       │
    │       ├── 加载 config.toml
    │       │
    │       └── 合并到 DEFAULT_PROVIDERS_CONFIG
    │
    ├── tool_service.initialize()
    │       │
    │       ├── 读取 app_config
    │       │
    │       └── 根据 api_key 加载 Provider 工具
    │
    └── broadcast_init_done()
            │
            └── Socket.IO 推送 init_done
```

## 敏感信息

- API Keys 存储在 config.toml
- 密码哈希存储在 SQLite
- Token 存储在 SQLite

## 相关 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/config/exists` | 检查配置是否存在 |
| GET | `/api/config` | 获取配置 |
| POST | `/api/config` | 更新配置 |
| GET | `/api/settings` | 获取设置 |
| POST | `/api/settings` | 更新设置 |
