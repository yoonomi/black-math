import re
import time
from typing import Any, Dict

from graphrag.graph import TinyGraph
from graphrag.llm.base import BaseLLM
from graphrag.prompt import LOCAL_QUERY

from .evidence import Evidence
from .planner import plan, seed_subquestions
from .retrieval import retrieve
from .verifier import verify


SYNTH_PROMPT = """你是《黑神话：悟空》影神图解说。只根据下面的设定回答用户的问题。

写作要求：
1. 只用完整通顺的中文，一两句说完，像人口述，不要病句、不要分号堆砌。
2. 问什么答什么。例如问「分别管哪座山」，只说黑风山土地管黑风山、黄风岭土地管黄风岭，不要夹带灵吉菩萨等无关人物。
3. 禁止出现这些字样：证据提到、根据三元组、原文显示、子问题、hop、fact、compare、FOLLOWUP。
4. 不要复述检索过程，不要列举没用上的关系。
5. 优先游戏影神图设定，不要改写成《西游记》课文。
6. 称呼用原文：土地公、黑熊精、狼妖、杨戬等。

问题: {query}

可用设定:
{evidence}
"""


def clean_answer(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"^(hop|fact|compare|answer|followup)[:：\s]+", "", t, flags=re.I)
    for sep in ("证据提到", "证据：", "证据:", "根据三元组", "原文显示", "子问题:"):
        if sep in t:
            t = t.split(sep, 1)[0]
    t = t.strip("；;，, \n")
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def ask(query: str, graph: TinyGraph, llm: BaseLLM, max_rounds: int = 4) -> Dict[str, Any]:
    started = time.perf_counter()
    evidence = Evidence()
    queue = seed_subquestions(query)
    rounds = 0
    draft = ""
    mark = "NEED"

    while rounds < max_rounds:
        rounds += 1
        sub = queue.pop(0) if queue else query
        retrieve(sub, graph, evidence)
        draft = clean_answer(
            llm.predict(SYNTH_PROMPT.format(query=query, evidence=evidence.as_prompt()))
        )
        mark = verify(query, draft, evidence, llm)
        if mark == "OK":
            break
        if mark == "UNKNOWN":
            draft = "小神查过影神图，现有条目未记载此事。"
            break
        nxt = plan(query, evidence, llm, rounds, max_rounds)
        if nxt == "ANSWER":
            break
        if nxt.startswith("FOLLOWUP:"):
            queue.append(nxt.split(":", 1)[1].strip())

    draft = clean_answer(draft)
    if not draft:
        try:
            draft = clean_answer(graph.local_query(query))
        except Exception:
            draft = clean_answer(
                llm.predict(LOCAL_QUERY.format(query=query, context=evidence.as_prompt()))
            )

    return {
        "answer": draft,
        "path": evidence.subquestions,
        "cites": [e.get("name") for e in evidence.entities if e.get("name")],
        "triples": evidence.triples[:20],
        "rounds": rounds,
        "mark": mark,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "context": evidence.as_prompt(),
    }
