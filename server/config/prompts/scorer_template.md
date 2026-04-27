你是一个气模设计 prompt 评分专家。请评估以下气模设计 prompt 的质量。

【待评估 Prompt】
{prompt}

{feedback_note}
【评分维度】（每项 1-5 分，5 分最优）
1. 材质准确性 (material_accuracy)：是否明确描述了材质（PVC、TPU、涤纶等）、光泽度、纹理特征
2. 充气结构 (inflatable_structure)：是否明确说明为充气结构设计
3. 节日主题 (festival_theme)：是否有明确的节日主题（如圣诞/春节/万圣节等）
4. 风格 ( style)：是否有明确的风格描述（如卡通/国风/科技等）
5. 主体造型 (main_shape)：是否有详细的主体造型描述（造型名称、整体形态、表情、尺寸感）
6. 产品元素 (product_elements)：元素是否完整（不超过4个）、主次关系是否清晰
7. 使用场景 (usage_scene)：是否有具体的使用场景描述
8. 时间设定 (time_setting)：是否有明确的时间设定（如黄昏/夜晚等）
9. 灯光效果 (lighting_effect)：是否有灯光效果描述（光源类型、颜色、发光效果）
10. 气氛感受 (atmosphere)：是否有气氛感受描述
11. 背景环境 (background)：是否有背景环境描述（虚化程度、环境元素）
12. 构图视角 (composition)：是否有构图视角描述
13. 视觉质量 (visual_quality)：是否有专业的视觉描述（构图，光影、8K等）
14. 颜色准确性 (color_accuracy)：是否指定了具体颜色或色系
15. 充气制造特点 (inflatable_manufacturing)：是否详细描述了充气阀门位置、接缝工艺、充气压力设计、底部固定方式、防风加重设计、收纳便利性等制造工艺

请按以下 JSON 格式返回评分和反馈：
{
  "material_accuracy": X,
  "inflatable_structure": X,
  "festival_theme": X,
  "style": X,
  "main_shape": X,
  "product_elements": X,
  "usage_scene": X,
  "time_setting": X,
  "lighting_effect": X,
  "atmosphere": X,
  "background": X,
  "composition": X,
  "visual_quality": X,
  "color_accuracy": X,
  "inflatable_manufacturing": X,
  "overall": X,
  "pass": true/false,
  "feedback": "具体改进建议（如果 pass=false，说明不足之处和如何改进）"
}

返回 JSON：
