# PneumatCraft 气模设计增强功能 - 技术文档

## 概述

基于 GenPilot + PneumatCraft 的 patterns 机制，为 jaaz 添加气模设计 prompt 增强功能。

## 新增工具

| 工具 | 描述 |
|------|------|
| `enhance_inflatable_prompt` | 增强气模设计 prompt |
| `refine_inflatable_prompt` | 基于错误反馈修正 prompt |
| `score_inflatable_prompt` | 评估 prompt 质量 |
| `check_inflatable_image` | VQA 图像质量检查 |

## 工作流程

```
用户输入
    │
    ▼
┌─────────────────────────┐
│  PatternMatcher.match() │  关键词匹配设计规范
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  PromptEnhancer.enhance()│  增强 prompt
│  - 添加结构特点           │
│  - 添加材质描写           │
│  - 添加节日元素           │
│  - 添加氛围感觉           │
│  - 添加构图方式           │
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  score_inflatable_prompt() │  四维度评分
│  - material_accuracy     │  材质准确性
│  - structural_soundness  │  结构合理性
│  - visual_quality        │  视觉质量
│  - color_accuracy        │  颜色准确性
│  Pass 标准: overall >= 3.5
└─────────────────────────┘
    │
    ▼ (评分通过)
┌─────────────────────────┐
│  generate_image()       │  生成图像
└─────────────────────────┘
    │
    ▼
┌─────────────────────────┐
│  check_inflatable_image()  │  VQA 图像检查
│  - 材质问题              │
│  - 结构问题              │
│  - 颜色问题              │
│  - 视觉问题              │
└─────────────────────────┘
    │
    ▼ (如有错误)
┌─────────────────────────┐
│  refine_inflatable_prompt()│  错误修正
└─────────────────────────┘
    │
    ▼
  重新生成
```

## 文件结构

```
server/tools/
├── patterns/
│   ├── __init__.py
│   ├── database.py          # PatternDatabase 数据结构
│   ├── matcher.py           # PatternMatcher 关键词匹配
│   ├── enhancer.py          # PromptEnhancer 增强生成
│   ├── scorer.py            # AirMoldScorer 评分引擎
│   ├── refinement.py        # RefinementEngine 错误修正引擎
│   ├── vqa_checker.py      # VQAChecker 图像检查器
│   ├── prompts/
│   │   └── enhancer_template.md  # 增强模板
│   ├── design_patterns.json     # 气模设计规范知识库
│   └── error_patterns.json       # 20种错误类型及修正策略
└── enhance_inflatable_prompt.py   # LangGraph 工具入口
```

## 设计规范分类

### Styles (风格)
- 卡通、简约、写实、梦幻、科技

### Products (产品)
- 气模拱门、气模人偶、气模卡通、气模玩具、大气模
- 气模滑梯、气模水池、气模蹦床、气模广告、节日气模

### Colors (颜色)
- 蓝色系、黄色系、红粉色系、绿青色系、紫灰色系、橙粉色系、白黑色系

### Materials (材质)
- PVC、TPU、Dacron、尼龙、网布

### Festivals (节日)
- 万圣节、圣诞节、春节

## 错误类型定义

| ID | 错误类型 | 描述 |
|----|----------|------|
| 1 | Quantity Errors | 数量描述错误 |
| 2 | Spatial Positioning Errors | 空间位置错误 |
| 3 | Material Errors | 材质选择错误 |
| 4 | Color Errors | 颜色偏差 |
| 5 | Texture Errors | 表面纹理不对 |
| 6 | Shape Errors | 形状失真 |
| 7 | Proportion Errors | 比例失调 |
| 8 | Structure Errors | 结构不合理 |
| 9 | Lighting Errors | 光影错误 |
| 10 | Shadow Errors | 阴影错误 |
| 11 | Style Errors | 风格不一致 |
| 12 | Composition Errors | 构图问题 |
| 13 | Detail Errors | 细节缺失 |
| 14 | Background Errors | 背景问题 |
| 15 | Weather Resistance Errors | 耐候性错误 |
| 16 | Safety Errors | 安全问题 |
| 17 | Durability Errors | 耐用性问题 |
| 18 | Installation Errors | 安装问题 |
| 19 | Visibility Errors | 可视性问题 |
| 20 | Brand Errors | 品牌标识错误 |

## 评分维度

| 维度 | 描述 | 权重 |
|------|------|------|
| material_accuracy | 材质准确性 | 1.0 |
| structural_soundness | 结构合理性 | 1.0 |
| visual_quality | 视觉质量 | 1.0 |
| color_accuracy | 颜色准确性 | 1.0 |

Pass 标准: overall >= 3.5

## 增强模板变量

| 变量 | 描述 |
|------|------|
| `{material}` | 材质描写 |
| `{structure}` | 结构特点 |
| `{style}` | 风格描述 |
| `{scene}` | 场景描写 |
| `{mood}` | 氛围感觉 |
| `{elements}` | 节日元素 |
| `{festival_dynamic}` | 动态节日元素（待实现） |

## VQA 检查分类

| 分类 | 问题数 | 检查内容 |
|------|--------|----------|
| material | 3 | PVC材质、光泽度、质感 |
| structure | 3 | 充气结构、接缝、比例 |
| color | 3 | 主色调、鲜艳度、色差 |
| visual | 3 | 构图、光影、背景 |

## 待实现功能

- [ ] `{festival_dynamic}` 动态节日元素生成（需要 LLM 调用）
- [ ] 聚类选择机制（GenPilot K-Means）
- [ ] 多候选生成 + 贝叶斯更新
- [ ] 历史记忆系统
- [ ] 用户反馈学习

## 技术债务

- [ ] scorer.py 的 rule-based 评分过于简单
- [ ] 没有错误边界处理
- [ ] 没有超时处理

## 参考资料

- GenPilot: `/Users/cyberway/ocworkspace/GenPilot/`
- PneumatCraft: `/Users/cyberway/ocworkspace/pneumatcraft/`
- jaaz main: `/Users/cyberway/ocworkspace/jaaz/`