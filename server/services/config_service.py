import copy
import os
import traceback
import aiofiles
import toml
from typing import Dict, TypedDict, Literal, Optional
from services.log_service import app_logger as logger

# 定义配置文件的类型结构


class ModelConfig(TypedDict, total=False):
    type: Literal["text", "image", "video"]
    is_custom: Optional[bool]
    is_disabled: Optional[bool]


class ProviderConfig(TypedDict, total=False):
    url: str
    api_key: str
    max_tokens: int
    models: Dict[str, ModelConfig]
    is_custom: Optional[bool]


AppConfig = Dict[str, ProviderConfig]


def _env_models(key: str, default: str) -> Dict[str, ModelConfig]:
    val = os.getenv(key, default)
    if not val:
        return {}
    return {m.strip(): {"type": "text"} for m in val.split(",") if m.strip()}


DEFAULT_PROVIDERS_CONFIG: AppConfig = {
    'comfyui': {
        'models': {},
        'url': 'http://127.0.0.1:8188',
        'api_key': '',
    },
    'minimax': {
        'models': _env_models("MINIMAX_MODELS", "MiniMax-M2.5-highspeed,MiniMax-M2.7-highspeed"),
        'url': os.getenv("MINIMAX_URL", 'https://api.minimax.io/v1/'),
        'api_key': '',
        'max_tokens': 8192,
    },
    'openai': {
        'models': _env_models("OPENAI_MODELS", "gpt-4o,gpt-4o-mini"),
        'url': os.getenv("OPENAI_URL", 'https://api.openai.com/v1/'),
        'api_key': '',
        'max_tokens': 8192,
    },
    'gemini': {
        'models': _env_models("GEMINI_MODELS", "gemini-2.5-pro,gemini-2.5-flash,gemini-2.0-flash"),
        'url': os.getenv("GEMINI_URL", 'https://generativelanguage.googleapis.com/'),
        'api_key': '',
        'max_tokens': 8192,
    },

}

SERVER_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_DIR = os.getenv("CONFIG_DIR", os.path.join(SERVER_DIR, "config"))
USER_DATA_DIR = os.getenv(
    "USER_DATA_DIR",
    os.path.join(SERVER_DIR, "user_data"),
)
FILES_DIR = os.getenv("FILES_DIR", os.path.join(USER_DATA_DIR))


IMAGE_FORMATS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",  # 基础格式
    ".bmp",
    ".tiff",
    ".tif",  # 其他常见格式
    ".webp",
)
VIDEO_FORMATS = (
    ".mp4",
    ".avi",
    ".mkv",
    ".mov",
    ".wmv",
    ".flv",
)


class ConfigService:
    def __init__(self):
        self.app_config: AppConfig = copy.deepcopy(DEFAULT_PROVIDERS_CONFIG)
        self.config_file = os.getenv(
            "CONFIG_PATH", os.path.join(CONFIG_DIR, "config.toml")
        )
        self.initialized = False

    def _get_jaaz_url(self) -> str:
        """Get the correct jaaz URL"""
        return os.getenv('BASE_API_URL', 'https://jaaz.app').rstrip('/') + '/api/v1/'

    async def initialize(self) -> None:
        try:
            # Ensure the user_data directory exists
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            # Check if config file exists
            if not self.exists_config():
                logger.info("config_not_found", path=self.config_file, msg="creating_default")
                with open(self.config_file, "w") as f:
                    toml.dump(self.app_config, f)
                logger.info("config_created", path=self.config_file)
                self.initialized = True
                return

            async with aiofiles.open(self.config_file, "r") as f:
                content = await f.read()
                config: AppConfig = toml.loads(content)
            for provider, provider_config in config.items():
                if provider not in DEFAULT_PROVIDERS_CONFIG:
                    provider_config['is_custom'] = True
                self.app_config[provider] = provider_config
                # image/video models are hardcoded in the default provider config
                provider_models = DEFAULT_PROVIDERS_CONFIG.get(
                    provider, {}).get('models', {})
                for model_name, model_config in provider_config.get('models', {}).items():
                    # Only text model can be self added
                    if model_config.get('type') == 'text' and model_name not in provider_models:
                        provider_models[model_name] = model_config
                        provider_models[model_name]['is_custom'] = True
                self.app_config[provider]['models'] = provider_models

            # 确保 jaaz URL 始终正确
            if 'jaaz' in self.app_config:
                self.app_config['jaaz']['url'] = self._get_jaaz_url()
        except Exception as e:
            logger.error("config_load_error", error=str(e))
            traceback.print_exc()
        finally:
            self.initialized = True

    def get_config(self) -> AppConfig:
        if 'jaaz' in self.app_config:
            self.app_config['jaaz']['url'] = self._get_jaaz_url()
        return self.app_config

    async def update_config(self, data: AppConfig) -> Dict[str, str]:
        try:
            if 'jaaz' in data:
                data['jaaz']['url'] = self._get_jaaz_url()

            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, "w") as f:
                toml.dump(data, f)
            self.app_config = data

            return {
                "status": "success",
                "message": "Configuration updated successfully",
            }
        except Exception as e:
            traceback.print_exc()
            return {"status": "error", "message": str(e)}

    def exists_config(self) -> bool:
        return os.path.exists(self.config_file)


config_service = ConfigService()
