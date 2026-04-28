# Jaaz 后端优化与重构建议

**日期**: 2026-04-28

---

## 一、架构优化

### 1. Service 层职责膨胀 ✅ (已完成)

**问题**: `tool_service.py`、`chat_service.py` 等文件过大，职责不单一。

```
当前 (重构前): tool_service.py (工具注册 + 工具执行 + 动态加载) - 329行
现在 (重构后):
├── tool_service.py      # Facade 门面 - 44行
├── tool_registry.py    # 工具注册表 (内存存储) - 新增
├── tool_loader.py      # 工具加载器 - 新增
└── providers.py        # TOOL_MAPPING 常量 - 新增
```

**已完成**:
- ✅ `tool_service.py` → Facade 模式 (329行 → 44行)
- ✅ `tool_registry.py` → 内存注册表
- ✅ `tool_loader.py` → 加载逻辑
- ✅ `providers.py` → TOOL_MAPPING

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/tool_service.py`
- `/Users/cyberway/ocworkspace/jaaz/server/agents/tool_registry.py` (新增)
- `/Users/cyberway/ocworkspace/jaaz/server/agents/tool_loader.py` (新增)
- `/Users/cyberway/ocworkspace/jaaz/server/agents/providers.py` (新增)

**工作量**: 已完成核心重构

---

### 2. Agent 配置硬编码

**问题**: Agent 类型和 handoff 关系在 `agent_manager.py` 中硬编码。

```python
# 当前: 硬编码
if enable_pneumat_enhancer:
    agents.append(PneumatEnhancerAgent)
```

**建议**: 改为配置文件驱动

```python
# 建议: config/agents.yaml
agents:
  - name: planner
    class: PlannerAgent
    handoffs: [image_video_creator, pneumat_enhancer]
  - name: pneumat_enhancer
    class: PneumatEnhancerAgent
    handoffs: [image_video_creator]
```

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/agents/langgraph_service/agent_manager.py`
- `/Users/cyberway/ocworkspace/jaaz/server/agents/langgraph_service/configs/*.py`

**工作量**: 中等，需要新增配置文件和工厂类

---

### 3. 数据库事务处理 ✅ (已完成)

**问题**: CRUD 操作未使用事务，跨表操作可能不一致。

**实现方案**:

```python
# 1. ConnectionPool 添加事务方法
async def begin_transaction(self) -> aiosqlite.Connection:
    conn = await self.acquire()
    await conn.execute("BEGIN")
    return conn

# 2. 事务辅助类
class TransactionHelper:
    async def __aenter__(self) -> aiosqlite.Connection:
        self.conn = await self.pool.begin_transaction()
        return self.conn
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.conn.rollback()
        else:
            await self.conn.commit()
        await self.pool.release(self.conn)

# 3. 原子操作方法
async def create_chat_session_and_message(self, session_id, model, provider, canvas_id, role, message, title=None):
    pool = await get_db_pool()
    async with TransactionHelper(pool) as conn:
        await conn.execute("INSERT INTO chat_sessions...", ...)
        await conn.execute("INSERT INTO chat_messages...", ...)
```

**已修改**:
- `ConnectionPool.begin_transaction()` - 开启事务
- `TransactionHelper` - 上下文管理器，自动 commit/rollback
- `DatabaseService.create_chat_session_and_message()` - chat_session 和 message 原子操作
- `chat_service.py` - 使用原子操作替代分离的两次调用

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/database/db_service.py`
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/chat_service.py`

---

## 二、性能优化

### 4. 同步文件 I/O ✅ (部分完成)

**问题**: `config_service.py` 和 `settings_service.py` 使用同步 `open()` 而非异步。

**已完成修改**:

```python
# config_service.py - 写操作已改为 async
async with aiofiles.open(self.config_file, "w") as f:
    await f.write(toml.dumps(self.app_config))

# settings_service.py - update_settings() 已改为 async
async with aiofiles.open(self.settings_file, 'r', encoding='utf-8') as f:
    content = await f.read()
    existing_settings = json.loads(content)

async with aiofiles.open(self.settings_file, 'w', encoding='utf-8') as f:
    await f.write(json.dumps(existing_settings, indent=2))
```

**未完成**: `get_settings()` 和 `get_raw_settings()` 仍是同步方法，需要更大范围重构

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/config_service.py`
- `/Users/cyberway/ocworkspace/jaaz/server/database/settings_service.py`

**工作量**: 低，已完成核心写操作改造

---

### 5. 数据库连接池过小

**问题**: `get_db_pool` 硬编码 `max_connections=5`

```python
# 当前
max_connections=5  # 对于高并发可能不足
```

**建议**: 改为可配置

```python
max_connections = int(os.getenv("DB_POOL_SIZE", "10"))
```

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/database/db_service.py`

**工作量**: 低，仅 1 处修改

---

### 6. Token 验证每次查库

**问题**: 每次 Socket.IO 连接都查询数据库验证 Token。

```python
# 当前: 每次连接都查询
def validate_local_token(token):
    return db.query("SELECT * FROM auth_tokens WHERE token = ?", token)
```

**建议**: 引入缓存 (Redis/Memcached) 或 LRU 缓存

```python
# 建议: LRU 缓存
from functools import lru_cache

@lru_cache(maxsize=1000)
def validate_local_token_cached(token):
    return db.query(token)  # 缓存 5 分钟
```

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/auth_service.py`
- `/Users/cyberway/ocworkspace/jaaz/server/web/websocket/handlers.py`

**工作量**: 中等，需要引入缓存层

---

## 三、安全优化

### 7. CORS 过于宽松

**问题**: `cors_allowed_origins='*'` 生产环境不安全。

```python
# 当前: main.py
sio = socketio.AsyncServer(cors_allowed_origins='*', ...)
```

**建议**: 配置化

```python
# 建议
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5174").split(",")
sio = socketio.AsyncServer(cors_allowed_origins=ALLOWED_ORIGINS)
```

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/main.py`
- `/Users/cyberway/ocworkspace/jaaz/server/web/websocket/manager.py`

**工作量**: 低，但影响范围广

---

### 8. 密码哈希强度

**问题**: bcrypt rounds 可能过低。

```python
# 当前: 默认 rounds
bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

**建议**: 增加 rounds 到 12

```python
bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/auth_service.py`

**工作量**: 低，仅 1 处修改

---

### 9. 敏感信息日志

**问题**: API Key 可能被打印到日志。

```python
# 当前: 可能泄露
logger.info(f"Using API key: {api_key}")
```

**建议**: 脱敏日志

```python
logger.info(f"API key prefix: {api_key[:4]}***")
```

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/tool_service.py`
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/config_service.py`
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/jaaz_service.py`

**工作量**: 低，需要审计所有日志语句

---

## 四、可维护性优化

### 10. 类型提示不完整

**问题**: 部分函数缺少类型提示。

```python
# 当前
def get_config():
    pass
```

**建议**: 完善类型提示

```python
def get_config() -> dict[str, ProviderConfig]:
    pass
```

**涉及文件**: 全部 Python 文件

**工作量**: 中等，建议使用 mypy 扫描

---

### 11. 魔法数字/字符串 ✅ (部分完成)

**问题**: 硬编码的值散布在代码中。

**已创建**:
- `/Users/cyberway/ocworkspace/jaaz/server/core/constants.py`

**已提取常量**:
```python
# core/constants.py
TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days
DEFAULT_TIMEOUT_SECONDS = 30
COMFYUI_TIMEOUT_SECONDS = 300
DEFAULT_PORT = 57988
DB_TIMEOUT_SECONDS = 10
DEFAULT_MAX_TOKENS = 8192
PIXEL_COUNT = 1024 ** 2  # 1M pixels
```

**已应用**:
- `auth_service.py`: `TOKEN_EXPIRY_SECONDS`, `DEFAULT_TIMEOUT_SECONDS`

**工作量**: 低，已完成核心常量提取

---

### 12. 异常处理不一致

**问题**: 部分地方捕获所有异常，部分有特定处理。

```python
# 当前
try:
    do_something()
except:  # 太宽泛
    pass
```

**建议**: 细化异常处理

```python
try:
    do_something()
except FileNotFoundError:
    handle_missing_file()
except PermissionError:
    handle_permission_error()
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

**涉及文件**: 全部 Python 文件

**工作量**: 中等，需要全面审查

---

## 五、扩展性优化

### 13. Provider 硬编码

**问题**: 新增 Provider 需要修改多处代码。

```python
# 当前: provider 判断散布
if provider == "openai":
    return OpenAIProvider()
elif provider == "anthropic":
    return AnthropicProvider()
```

**建议**: 插件化注册

```python
# providers/__init__.py
PROVIDER_REGISTRY = {
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
}

def get_provider(name: str) -> BaseProvider:
    return PROVIDER_REGISTRY[name]()
```

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/agents/tools/utils/image_generation_core.py`
- `/Users/cyberway/ocworkspace/jaaz/server/agents/tools/utils/video_generation_core.py`

**工作量**: 中等，需要重构 Provider 加载逻辑

---

### 14. Tool 动态加载耦合

**问题**: `TOOL_MAPPING` 和 `ToolService` 紧耦合。

**建议**: 使用插件模式

```python
# tools/plugins/目录下放各 Provider 工具
# 自动发现和注册
for plugin in Path("tools/plugins").glob("*_plugin.py"):
    load_plugin(plugin)
```

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/web/services/tool_service.py`
- `/Users/cyberway/ocworkspace/jaaz/server/agents/tools/`

**工作量**: 中等

---

### 15. Agent 类型扩展复杂

**问题**: 新增 Agent 需要修改 `agent_manager.py`

**状态**: ⏳ 保持现状

**说明**: 当前每个 Agent Config 初始化参数不同（如 `PlannerAgentConfig()` 无参数，`ImageVideoCreatorAgentConfig(tool_list)` 需要 tool_list），工厂模式需要更复杂的注册机制。评估后认为当前架构已足够清晰，暂不重构。

**涉及文件**:
- `/Users/cyberway/ocworkspace/jaaz/server/agents/langgraph_service/agent_manager.py`

**工作量**: 中等（暂不实施）

---

## 六、测试覆盖

### 16. 单元测试 ✅ (已具备)

**现状**: 项目已配置 pytest，现有 40 个测试文件，350 个测试用例：

```
tests/
├── test_agent_manager.py
├── test_auth_service.py (隐式通过)
├── test_tool_service.py ✅
├── test_db_service.py
├── test_chat_service.py
├── test_config_service.py
├── test_settings_service.py
├── test_canvas_router.py
├── test_chat_router.py
├── ... (共 40 个测试文件)
└── conftest.py
```

**运行测试**: `pytest tests/`

**注意**: 部分测试因缺少 `langchain_google_genai` 等依赖而失败，需要补充依赖

---

## 七、优化优先级矩阵

| 优先级 | 问题 | 影响 | 工作量 | 状态 |
|--------|------|------|--------|------|
| 🔴 高 | CORS 过于宽松 | 安全风险 | 低 | ⏳ |
| 🔴 高 | 数据库无事务 | 数据一致性 | 中等 | ✅ |
| 🔴 高 | Token 验证无缓存 | 性能 | 中等 | ⏳ |
| 🟡 中 | Service 层膨胀 | 可维护性 | 中等 | ✅ |
| 🟡 中 | Provider 硬编码 | 扩展性 | 中等 | ⏳ |
| 🟡 中 | 类型提示不完整 | 开发体验 | 中等 | ⏳ |
| 🟡 中 | 缺少单元测试 | 质量保证 | 高 | ✅ |
| 🟢 低 | 密码哈希强度 | 安全风险 | 低 | ⏳ |
| 🟢 低 | 同步文件 I/O | 性能 | 低 | ✅ |
| 🟢 低 | 数据库连接池 | 性能 | 低 | ⏳ |
| 🟢 低 | 魔法数字 | 可维护性 | 低 | ✅ |
| 🟢 低 | 敏感信息日志 | 安全风险 | 低 | ⏳ |

✅ = 已完成 ⏳ = 待处理

---

## 八、推荐实施顺序

### Phase 1: 安全修复 (1-2 周)
1. 🔴 CORS 配置化
2. ✅ ~~数据库事务处理~~ (已完成)
3. 🟢 密码哈希强度

### Phase 2: 性能优化 (1 周)
4. 🟢 Token 验证缓存
5. ✅ ~~同步文件 I/O → 异步~~ (已完成核心写操作)
6. 🟢 数据库连接池可配置

### Phase 3: 可维护性 (2-3 周)
7. ✅ ~~抽取 constants.py~~ (已创建 core/constants.py)
8. 🟡 完善类型提示
9. 🟡 统一异常处理
10. ✅ ~~Service 层拆分~~ (已完成 tool_service.py 重构)

### Phase 4: 扩展性 (2 周)
11. 🟡 Provider 插件化
12. 🟡 Agent 工厂模式
13. 🟡 Tool 动态加载

### Phase 5: 测试 (持续)
14. ✅ ~~添加单元测试~~ (已有 40 个测试文件，350 个测试用例)

---

*文档生成时间: 2026-04-28*
