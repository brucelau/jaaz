# PneumatCraft Enhancement - TODO

## 概述
基于 GenPilot + PneumatCraft 的 patterns 机制，为 jaaz 添加气模设计 prompt 增强功能。

## 已完成

### Phase 1: Pattern 匹配 + 增强 ✅
- [x] `server/tools/patterns/database.py` - PatternDatabase 数据结构
- [x] `server/tools/patterns/matcher.py` - PatternMatcher 关键词匹配
- [x] `server/tools/patterns/enhancer.py` - PromptEnhancer 增强生成
- [x] `server/tools/patterns/design_patterns.json` - 气模设计规范知识库
- [x] `server/tools/enhance_inflatable_prompt.py` - LangGraph 工具
- [x] `server/services/tool_service.py` - 工具注册
- [x] `server/services/langgraph_service/configs/image_vide_creator_config.py` - System prompt 更新

### Phase 2: Refinement + Scoring ✅
- [x] `server/tools/patterns/error_patterns.json` - 20种错误类型及修正策略
- [x] `server/tools/patterns/refinement.py` - RefinementEngine 错误修正引擎
- [x] `server/tools/patterns/scorer.py` - AirMoldScorer 评分引擎
- [x] `refine_inflatable_prompt` 工具 - 基于错误反馈修正 prompt
- [x] `score_inflatable_prompt` 工具 - 四维度评分

### Phase 3: VQA 错误检查集成 ✅
- [x] `server/tools/patterns/vqa_checker.py` - VQA 图像检查器
- [x] `check_inflatable_image` 工具 - VQA 图像质量检查
- [x] 集成 VQA 到工具流程
- [x] 更新 ImageVideoCreator prompt 添加 VQA 检查指引

### Phase 4: 端到端测试 ✅
- [x] 测试 enhance_inflatable_prompt 工具链
- [x] 测试 refine_inflatable_prompt 迭代修正
- [x] 测试 score_inflatable_prompt 评分
- [x] 测试 check_inflatable_image VQA 流程
- [x] 修复 refinement.py 规则修正 bug

## 暂不实现（可选）

### Phase 5: 高级功能（可选，暂不实现）
- [ ] 聚类选择机制（GenPilot 的 K-Means 聚类）
  - 参考: GenPilot/utils_all/cluster.py
  - 用途: 多候选 prompts 的聚类选择
- [ ] 多候选生成 + 贝叶斯更新
  - 参考: GenPilot/utils_all/refiner.py, scorer.py
  - 用途: 迭代优化最优 prompt
- [ ] 历史记忆系统
  - 参考: GenericAgent/memory/
  - 用途: 累积成功的设计经验
- [ ] 用户反馈学习
  - 用途: 根据用户选择学习偏好

## 错误类型定义

参考 `server/tools/patterns/error_patterns.json`:

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

## 设计规范分类

参考 `server/tools/patterns/design_patterns.json`:

### Styles (风格)
- 卡通、简约、写实、梦幻、科技

### Products (产品)
- 气模拱门、气模人偶、气模卡通、气模玩具、大气模
- 气模滑梯、气模水池、气模蹦床、气模广告、节日气模

### Colors (颜色)
- 蓝色系、黄色系、红粉色系、绿青色系、紫灰色系、橙粉色系、白黑色系

### Materials (材质)
- PVC、TPU、Dacron、尼龙、网布

## 评分维度

| 维度 | 描述 | 权重 |
|------|------|------|
| material_accuracy | 材质准确性 | 1.0 |
| structural_soundness | 结构合理性 | 1.0 |
| visual_quality | 视觉质量 | 1.0 |
| color_accuracy | 颜色准确性 | 1.0 |

Pass 标准: overall >= 3.5

## 技术债务

- [ ] scorer.py 的 rule-based 评分过于简单，需要更复杂的权重计算
- [x] refinement.py 的规则修正已实现（Phase 4 修复）
- [ ] 没有错误边界处理
- [ ] 没有超时处理

## 工具清单

| 工具 | 描述 |
|------|------|
| `enhance_inflatable_prompt` | 增强气模设计 prompt |
| `refine_inflatable_prompt` | 基于错误反馈修正 prompt |
| `score_inflatable_prompt` | 评估 prompt 质量 |
| `check_inflatable_image` | VQA 图像质量检查 |

## 工作流

```
用户输入 -> PatternMatcher.match() -> 匹配设计规范
    -> PromptEnhancer.enhance() -> 增强 prompt
    -> score_inflatable_prompt() -> 评分检查
    -> generate_image() -> 生成图像
    -> check_inflatable_image() -> VQA 检查
    -> refine_inflatable_prompt() -> 错误修正（如有）
    -> 重新生成（如需要）
```

## 参考资料

- GenPilot: `/Users/cyberway/ocworkspace/GenPilot/`
- PneumatCraft: `/Users/cyberway/ocworkspace/pneumatcraft/`
- jaaz main: `/Users/cyberway/ocworkspace/jaaz/`