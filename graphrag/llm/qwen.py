from typing import Any, Dict, Optional

from openai import OpenAI

from .base import BaseLLM


class QwenLLM(BaseLLM):
    def __init__(
        self,
        model_name: str,
        api_key: str,
        model_params: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(model_name, model_params, **kwargs)
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )

    def predict(self, input: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": input}],
        )
        return response.choices[0].message.content or ""
