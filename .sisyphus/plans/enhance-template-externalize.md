# 计划：增强模板外部化

## 目标
将 `enhancer.py` 中的 `DEFAULT_TEMPLATE` 移至外部 `.md` 文件，便于维护和修改。

## 步骤

### 1. 创建模板文件
创建 `server/tools/patterns/prompts/enhancer_template.md`，内容：
```
你是一个气模设计专家。根据用户需求和专业设计规范，生成专业、详细、高质量的气模设计提示词。

用户需求：{user_input}

匹配到的设计规范：
{pattern_context}{style_note}

{festival_dynamic}

要求：
1. 确保提示词专业、详细，符合气模设计行业水准
2. 强制包含颜色、构图、材质，光影等关键要素
3. 直接输出提示词，不包含任何解释或额外文字

输出：
```

### 2. 修改 enhancer.py
1. 移除 `DEFAULT_TEMPLATE` 类变量（第 24-36 行）
2. 添加类变量 `DEFAULT_TEMPLATE_PATH` = `Path(__file__).parent / "prompts" / "enhancer_template.md"`
3. 在 `__init__` 中读取文件内容，若读取失败则使用内置默认模板

### 3. 验证
- 启动 jaaz
- 测试万圣节增强，确认模板文件被正确加载

## 预期输出
增强后的提示词包含万圣节元素（南瓜灯、蝙蝠、糖果等）而非通用话术