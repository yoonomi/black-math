import os
from typing import Optional, Tuple

from dotenv import load_dotenv

from graphrag.embedding.zhipu import zhipuEmb
from graphrag.llm.base import BaseLLM
from graphrag.llm.factory import get_llm


def load_env() -> None:
    load_dotenv()


def zhipu_key() -> str:
    return os.getenv("ZHIPU_API_KEY") or os.getenv("ZHIPUAI_API_KEY") or ""


def neo4j_conf() -> Tuple[str, str, str]:
    return (
        os.getenv("NEO4J_URL", "bolt://localhost:7687"),
        os.getenv("NEO4J_USER", "neo4j"),
        os.getenv("NEO4J_PASS") or "",
    )


def get_embedding():
    key = zhipu_key()
    if not key:
        raise ValueError("缺少 ZHIPU_API_KEY，无法使用 embedding-3")
    return zhipuEmb("embedding-3", key)


def get_chat_llm(name: Optional[str] = None) -> BaseLLM:
    return get_llm(name or "zhipu")
