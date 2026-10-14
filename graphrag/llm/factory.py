import os
from typing import Dict, List, Optional

from .base import BaseLLM
from .zhipu import zhipuLLM


PROVIDERS = {
    "zhipu": {"env": "ZHIPU_API_KEY", "model_env": "ZHIPU_MODEL", "default_model": "glm-4-flash"},
    "deepseek": {"env": "DEEPSEEK_API_KEY", "model_env": "DEEPSEEK_MODEL", "default_model": "deepseek-chat"},
    "qwen": {"env": "DASHSCOPE_API_KEY", "model_env": "QWEN_MODEL", "default_model": "qwen3.5-flash"},
    "grok": {"env": "XAI_API_KEY", "model_env": "GROK_MODEL", "default_model": "grok-4"},
}


def available_llms() -> List[str]:
    names = []
    for name, spec in PROVIDERS.items():
        if os.getenv(spec["env"]):
            names.append(name)
    return names


def get_llm(name: str, model_name: Optional[str] = None) -> BaseLLM:
    key = (name or "zhipu").strip().lower()
    if key not in PROVIDERS:
        raise ValueError(f"未知模型: {name}，可选 {list(PROVIDERS)}")
    spec = PROVIDERS[key]
    api_key = os.getenv(spec["env"])
    if not api_key:
        raise ValueError(f"{name} 未配置 {spec['env']}")
    model = model_name or os.getenv(spec["model_env"]) or spec["default_model"]
    if key == "zhipu":
        return zhipuLLM(model, api_key)
    if key == "deepseek":
        from .deepseek import DeepSeekLLM

        return DeepSeekLLM(model, api_key)
    if key == "qwen":
        from .qwen import QwenLLM

        return QwenLLM(model, api_key)
    from .grok import GrokLLM

    return GrokLLM(model, api_key)


def provider_status() -> Dict[str, bool]:
    return {name: bool(os.getenv(spec["env"])) for name, spec in PROVIDERS.items()}
