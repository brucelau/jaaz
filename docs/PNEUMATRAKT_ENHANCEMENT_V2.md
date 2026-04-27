# PneumatCraft 增强流程优化方案

## 背景

当前流程存在以下问题：
1. `enhance_inflatable_prompt` 只返回 1 个候选 prompt
2. `score_inflatable_prompt` 是可选调用，未集成到主流程
3. 评分机制形同虚设，无法有效筛选优质 prompt

## 新流程

```
用户输入
    │
    ▼
┌─────────────────────────────────────┐
│ enhance_inflatable_prompt              │
│ 生成 3 个候选中文 prompt              │
│ (LLM 生成，温度 0.8-0.9)           │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│ 批量评分                            │
│ 对 3 个候选并行评分                  │
│ - material_accuracy (材质准确性)    │
│ - structural_soundness (结构合理性) │
│ - visual_quality (视觉质量)          │
│ - color_accuracy (颜色准确性)        │
│ Pass 标准: overall >= 3.5           │
└─────────────────────────────────────┘
    │
    │ 全部不通过
    │ (最多重试 3 次)
    ▼
┌─────────────────────────────────────┐
│ 重新生成 3 个候选                    │
└─────────────────────────────────────┘
    │
    ▼ (重试 3 次后)
┌─────────────────────────────────────┐
│ 选择最优 (overall 最高)             │
│ 不管是否达标                        │
└─────────────────────────────────────┘
    │
    ▼
Agent 生成【中文】Design Strategy Doc
    │  ← 详细设计规划
    │  - 分辨率
    │  - 风格与氛围
    │  - 关键视觉元素
    │  - 构图与布局
    │  - 色彩方案
    │  - 材质说明
    ▼
Agent 根据 Design Strategy Doc 生成英文 prompt
    │
    ▼
generate_image(英文 prompt)
    │
    ▼
check_inflatable_image → VQA 检查
    │
    ▼ (如有错误)
refine_inflatable_prompt → 修正
```

## 返回格式

### enhance_inflatable_prompt 返回

```json
{
  "candidates": [
    {
      "prompt": "设计一款圣诞节充气装饰...",
      "reason": "色彩鲜艳突出节日气氛"
    },
    {
      "prompt": "圣诞节主题大气模设计...",
      "reason": "结构清晰适合气模制作"
    },
    {
      "prompt": "节日充气装饰产品...",
      "reason": "构图专业视觉冲击力强"
    }
  ]
}
```

### 批量评分逻辑

```python
def batch_score(candidates: List[str]) -> List[ScoringResult]:
    # 并行对 3 个候选评分
    results = []
    for candidate in candidates:
        score = scorer.evaluate(candidate)
        results.append(score)
    return results

def select_best(results: List[ScoringResult]) -> str:
    # 直接返回评分最高的
    return max(results, key=lambda r: r.overall)
```

## 实现要点

### 1. enhance_inflatable_prompt 改造

- `_enhance_with_llm()` 返回 JSON 数组格式
- temperature 调高到 0.8-0.9（更有创意）
- 明确要求生成 3 个不同角度的候选

### 2. 新增批量评分逻辑

- 位置：在 `enhance_inflatable_prompt` 调用后
- 方式：并行评分
- 返回：最优候选

### 3. 流程控制

- Agent 调用 `enhance_inflatable_prompt` 后自动进行评分
- 若评分不通过，**enhancer 重新生成 3 个候选**（最多重试 3 次）
- 重试 3 次后，**直接选最优**（不管是否达标）

## 文件改动

| 文件 | 改动 |
|------|------|
| `enhancer.py` | `_enhance_with_llm()` 返回 3 个候选 |
| `scorer.py` | 可能需要适配批量评分 |
| `enhance_inflatable_prompt.py` | 新增批量评分+选择逻辑 |
| `image_vide_creator_config.py` | 更新 system prompt |

## 待定问题

1. 3 个候选如何保证多样性？（让 LLM 生成不同侧重点）
2. 若全部评分不通过，用户体验如何处理？
3. 英文 Design Strategy Doc 是否还由 Agent 生成？