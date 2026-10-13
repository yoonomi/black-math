import time
from typing import Any, Dict

from graphrag.graph import TinyGraph
from graphrag.llm.base import BaseLLM
from graphrag.prompt import LOCAL_QUERY

from .evidence import Evidence
from .planner import plan, seed_subquestions
from .retrieval import retrieve
from .verifier import verify


SYNTH_PROMPT = """你是《黑神话：悟空》影神图助手，自称小神。只根据证据回答。
若证据不足，明确说「影神图未记载」。
回答中点名用到的实体。

问题: {query}
证据:
{evidence}
"""


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
        draft = llm.predict(SYNTH_PROMPT.format(query=query, evidence=evidence.as_prompt()))
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

    if not draft:
        try:
            draft = graph.local_query(query)
        except Exception:
            draft = llm.predict(LOCAL_QUERY.format(query=query, context=evidence.as_prompt()))

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
