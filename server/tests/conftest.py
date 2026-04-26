import pytest
import sys
from pathlib import Path

server_dir = Path(__file__).parent.parent
sys.path.insert(0, str(server_dir))


@pytest.fixture
def sample_prompt_basic():
    return "一个卡通风格的红色大气模"


@pytest.fixture
def sample_prompt_detailed():
    return "充气 PVC 材质黄色大象造型气模，立体结构，加固底座，专业摄影，8K分辨率"


@pytest.fixture
def sample_prompt_minimal():
    return ""


@pytest.fixture
def sample_prompt_chinese():
    return "一个蓝色的防水面料充气兔子，多点固定，专业光影，高质量"
