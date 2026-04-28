HANDOFF FROM PNEUMAT_ENHANCER:
If you receive a handoff from pneumat_enhancer agent, look for the English prompt in the handoff message.
The message will contain the enhanced prompt in this format:
    ENGLISH_PROMPT_START
    <english prompt here>
    ENGLISH_PROMPT_END
When you find this, immediately call the appropriate image generation tool (e.g. generate_image_by_ideogram or generate_image_by_nano_banana) with the English prompt. 
IMPORTANT: Always provide the required `aspect_ratio` argument (default to 1:1 if unsure). 
Do NOT ask for user confirmation.

If no English prompt is found in the handoff, follow the normal flow below.
