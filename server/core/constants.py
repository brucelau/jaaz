"""
Constants - 集中管理魔法数字和字符串

This module contains hardcoded values that should be configured centrally
to improve maintainability and avoid magic numbers scattered across the codebase.
"""

from enum import Enum


# ============== 时间相关 ==============

TOKEN_EXPIRY_SECONDS = 7 * 24 * 3600  # 7 days
DEFAULT_TIMEOUT_SECONDS = 30
COMFYUI_TIMEOUT_SECONDS = 300


# ============== 端口和 URL ==============

DEFAULT_PORT = 57988
COMFYUI_DEFAULT_URL = "http://127.0.0.1:8188"
OLLAMA_DEFAULT_URL = "http://localhost:11434"


# ============== 数据库 ==============

DB_TIMEOUT_SECONDS = 10


# ============== Token 限制 ==============

DEFAULT_MAX_TOKENS = 8192
ENHANCER_MAX_TOKENS = 8192


# ============== 图片/视频 ==============

DEFAULT_IMAGE_SIZE = "1024x1024"
IMAGE_SIZE_MAP = {
    "1:1": "1024x1024",
    "16:9": "1792x1024",
    "9:16": "1024x1792",
    "4:3": "1024x768",
    "3:4": "768x1024",
}
PIXEL_COUNT = 1024 ** 2  # 1M pixels


# ============== 测试 ==============

E2E_TEST_PORT = 57999
E2E_TIMEOUT_SECONDS = 5
