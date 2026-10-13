import re
from typing import List

from graphrag.graph import TinyGraph

from .evidence import Evidence

REL_WORDS = ("部下", "从属", "交手", "同属", "位于", "交好", "相关", "占据")


def _names_from(text: str) -> List[str]:
    known = [
        "孙悟空",
        "二郎神",
        "二郎显圣真君",
        "黑风大王",
        "黑风山土地",
        "白衣秀士",
        "灵吉菩萨",
        "黄风大王",
        "黄风岭土地",
        "黑风山",
        "黄风岭",
    ]
    return [n for n in known if n in text]


def retrieve(subquestion: str, graph: TinyGraph, evidence: Evidence) -> None:
    evidence.subquestions.append(subquestion)
    names = _names_from(subquestion)
    if not names:
        names = re.findall(r"[\u4e00-\u9fff]{2,6}", subquestion)[:3]

    use_graph = any(w in subquestion for w in REL_WORDS) or "既" in subquestion
    for name in names:
        found = graph.search_entities(name)
        evidence.entities.extend(found)
        hops = graph.graph_query(name, hops=2)
        evidence.triples.extend(hops)

    if (not use_graph) or not evidence.triples:
        try:
            ctx = graph.build_local_query_context(subquestion)
            evidence.chunks.append(ctx)
        except Exception as e:
            evidence.notes.append(f"local 检索失败: {e}")
