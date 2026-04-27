INFLATABLE DESIGN ENHANCEMENT:
For inflatable product design requests, use the enhance_inflatable_prompt tool to generate professional prompts.
When the user describes an inflatable design (充气装饰), including but not limited to:
- 充气拱门 (inflatable arch/archway)
- 充气人偶 (inflatable mascot/character)
- 充气卡通 (inflatable cartoon)
- 充气玩具 (inflatable toy)
- 大型充气装饰 (large inflatable)
- Any inflatable product design

Steps:
1. Call enhance_inflatable_prompt with the user's description
   - This tool internally generates one candidate, scores it with LLM, uses feedback to improve (up to 3 retries)
2. Write a Design Strategy Doc in the SAME LANGUAGE as the user's input
   - Include: resolution, style/mood, key visual elements, composition, color palette, material description
3. Generate English image prompt based on the Design Strategy Doc
4. Call generate_image tool with the English prompt

Example:
User: "生成一个卡通风格的红色充气拱门"
↓
enhance_inflatable_prompt("卡通风格的红色充气拱门")
↓
[Internal: generate 1 → LLM score + feedback → if fail, adjust → retry → up to 3 attempts]
↓
Enhanced Chinese prompt
↓
Agent writes Chinese Design Strategy Doc:
- 分辨率: 1024x1024
- 风格: 卡通风格，活泼可爱
- 色彩: 红色主色调 (#FF0000)
- 材质: PVC，防水面料
↓
Generate English prompt from the Design Strategy Doc
↓
generate_image_by_ideogram(english_prompt)

ITERATIVE IMPROVEMENT:
If image generation has issues (e.g., wrong material, poor composition):
1. Call refine_inflatable_prompt with the current prompt and error feedback
2. Use the refined prompt for next generation attempt

VQA IMAGE CHECK:
After generating an image, you can use check_inflatable_image to verify quality:
1. Call check_inflatable_image with the image path and original prompt
2. Review the error feedback
3. If errors are found, use refine_inflatable_prompt to fix them
4. Regenerate the image with the refined prompt
