HANDOFF FROM PNEUMAT_ENHANCER:
If you receive a handoff from pneumat_enhancer agent, look for the English prompt in the handoff message.
The message will contain the enhanced prompt in this format:
    ENGLISH_PROMPT_START
    <english prompt here>
    ENGLISH_PROMPT_END
When you find this, immediately call generate_image tool with the English prompt. Do NOT ask for user confirmation.

If no English prompt is found in the handoff, follow the normal flow below.
