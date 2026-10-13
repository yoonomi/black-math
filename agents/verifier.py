from graphrag.llm.base import BaseLLM

from .evidence import Evidence

VERIFY_PROMPT = """你是影神图答案校验器。根据证据判断草稿是否成立。
只输出一行：
OK
NEED:<还缺什么>
UNKNOWN

用户问题: {query}
证据:
{evidence}
草稿答案:
{draft}
"""


def verify(query: str, draft: str, evidence: Evidence, llm: BaseLLM) -> str:
    if not evidence.entities and not evidence.triples and not evidence.chunks:
        return "UNKNOWN"
    raw = llm.predict(
        VERIFY_PROMPT.format(query=query, evidence=evidence.as_prompt(), draft=draft)
    )
    text = (raw or "").strip().splitlines()[0].strip().upper()
    if text.startswith("NEED"):
        return raw.strip().splitlines()[0].strip()
    if "UNKNOWN" in text:
        return "UNKNOWN"
    return "OK"
