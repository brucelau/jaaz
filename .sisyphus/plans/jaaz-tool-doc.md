# Plan: 为 Jaaz 项目编写 Tool 架构文档

## TL;DR
将 Tool 注册、加载、调用流程写成详细文档，保存到 `jaaz/docs/TOOL_ARCHITECTURE.md`

## Context
用户需要一份关于 Jaaz 项目中 Tool 注册、加载、调用机制的详细文档，便于理解整个架构。

## Work Objectives

### Concrete Deliverables
- 创建文档: `jaaz/docs/TOOL_ARCHITECTURE.md`
- 内容涵盖:
  1. 工具定义 (TOOL_MAPPING)
  2. Provider 分类
  3. ToolService 注册流程
  4. Agent 获取工具流程
  5. 工具调用链路 (ReAct Loop)
  6. Provider 路由机制
  7. 完整调用链路图
  8. Tool 函数定义规范

### Definition of Done
- [ ] 文档创建在正确位置
- [ ] 包含所有核心组件说明
- [ ] 包含完整架构图/流程图
- [ ] 包含代码示例

## Guardrails
- 只写 markdown 文档，不修改任何代码
- 文档路径: `/Users/cyberway/ocworkspace/jaaz/docs/TOOL_ARCHITECTURE.md`

## Execution Strategy

### Wave 1 (创建文档)
- [ ] 1. 创建 `jaaz/docs/TOOL_ARCHITECTURE.md`
- [ ] 2. 写入文档内容（见下方详细内容）

### 详细内容

文档应包含以下章节：

1. **概述** - 简述 Tool 在 Jaaz 中的角色

2. **目录结构** - 展示 tools 相关文件的目录布局

3. **工具定义** - `TOOL_MAPPING` 字典的结构和示例

4. **Provider 分类** - 各 provider 的说明和 API Key 来源

5. **系统内置工具** - write_plan, enhance_inflatable_prompt 等

6. **工具注册流程** - ToolService.initialize() 的详细流程

7. **ComfyUI 动态工具注册** - 如何从数据库读取工作流动态构建工具

8. **Agent 获取工具** - AgentManager.create_agents() 如何筛选和分配工具

9. **各 Agent 的工具配置** - Planner / ImageVideoCreator / PneumatEnhancer

10. **工具绑定到 Agent** - _create_langgraph_agent() 实现细节

11. **工具调用流程** - LangGraph ReAct Loop 完整流程

12. **Provider 路由** - generate_image_with_provider() 机制

13. **Provider 实现示例** - IdeogramProvider 完整代码

14. **完整调用链路图** - ASCII 流程图

15. **Tool 函数定义规范** - @tool 装饰器使用规范

16. **特殊工具说明** - enhance_inflatable_prompt, write_plan 等

17. **配置说明** - config.toml 和环境变量的使用

18. **总结表格** - 各阶段负责组件

## Verification Strategy
- [ ] 文档已创建
- [ ] 路径正确: `jaaz/docs/TOOL_ARCHITECTURE.md`
- [ ] 文件非空

## Success Criteria
文档创建成功，内容完整，可读性强。
