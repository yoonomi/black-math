from typing import List

from graphrag.llm.base import BaseLLM

from .evidence import Evidence

PLAN_PROMPT = """你是影神图问答规划器。根据用户问题和已有证据，判断下一步。
只输出一行，格式必须是以下之一：
ANSWER
FOLLOWUP:<下一个子问题>

规则：
- 单跳事实题（某某是谁、外貌、地点）若证据已够，输出 ANSWER
- 多跳（既...又...、部下、交手、同属）若证据缺口，输出 FOLLOWUP:具体子问题
- 已有足够实体和关系，输出 ANSWER
- 子问题要短，一次只问一个缺口

用户问题: {query}
已有证据:
{evidence}
"""


def plan(query: str, evidence: Evidence, llm: BaseLLM, round_idx: int, max_rounds: int = 4) -> str:
    if round_idx >= max_rounds:
        return "ANSWER"
    raw = llm.predict(PLAN_PROMPT.format(query=query, evidence=evidence.as_prompt()))
    text = (raw or "").strip().splitlines()[0].strip()
    if text.upper().startswith("FOLLOWUP"):
        _, _, rest = text.partition(":")
        sub = rest.strip() or query
        return f"FOLLOWUP:{sub}"
    return "ANSWER"


def seed_subquestions(query: str) -> List[str]:
    if "既" in query and "又" in query:
        return [query]
    return [query]
