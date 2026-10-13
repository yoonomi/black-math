import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graphrag.config import get_chat_llm, get_embedding, load_env, neo4j_conf
from graphrag.graph import TinyGraph
from graphrag.llm.factory import available_llms
from agents.loop import ask


QUESTIONS = ROOT / "eval" / "questions.json"
RESULTS = ROOT / "eval" / "results.json"
SAMPLE = ROOT / "data" / "samples" / "portraits_sample.md"


def hit_at_1(pred: str, gold: str) -> int:
    pred = pred or ""
    keys = [p.strip() for p in gold.replace("、", ",").split(",") if p.strip()]
    return int(any(k in pred for k in keys))


def f1_overlap(pred: str, gold: str) -> float:
    p = set(pred or "")
    g = set(gold or "")
    if not p or not g:
        return 0.0
    inter = len(p & g)
    prec = inter / max(len(p), 1)
    rec = inter / max(len(g), 1)
    if prec + rec == 0:
        return 0.0
    return 2 * prec * rec / (prec + rec)


def citation_cover(pred: str, entities) -> float:
    if not entities:
        return 0.0
    hit = sum(1 for e in entities if e in (pred or ""))
    return hit / len(entities)


def main():
    load_env()
    llms = available_llms()
    if not llms:
        raise SystemExit("没有可用的 API Key")
    url, user, password = neo4j_conf()
    graph = TinyGraph(url, user, password, get_chat_llm("zhipu"), get_embedding())
    if SAMPLE.exists():
        graph.add_document(str(SAMPLE))

    questions = json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]
    rows = []
    for model in llms:
        llm = get_chat_llm(model)
        graph.llm = llm
        for mode in ("graphrag", "plain"):
            for q in questions:
                t0 = time.perf_counter()
                cites = []
                try:
                    if mode == "graphrag":
                        out = ask(q["query"], graph, llm)
                        pred = out["answer"]
                        cites = out.get("cites") or []
                        latency = out.get("latency_ms", int((time.perf_counter() - t0) * 1000))
                    else:
                        pred = llm.predict(q["query"])
                        latency = int((time.perf_counter() - t0) * 1000)
                except Exception as e:
                    pred = f"ERROR: {e}"
                    latency = int((time.perf_counter() - t0) * 1000)
                rows.append(
                    {
                        "id": q["id"],
                        "type": q["type"],
                        "query": q["query"],
                        "gold": q["answer"],
                        "model": model,
                        "mode": mode,
                        "pred": pred,
                        "hit": hit_at_1(pred, q["answer"]),
                        "f1": round(f1_overlap(pred, q["answer"]), 4),
                        "citation": round(citation_cover(pred, q["entities"]), 4),
                        "latency_ms": latency,
                        "cites": cites,
                    }
                )
                print(q["id"], model, mode, rows[-1]["hit"], rows[-1]["latency_ms"])

    summary = {}
    for row in rows:
        key = f"{row['model']}/{row['mode']}"
        bucket = summary.setdefault(
            key, {"n": 0, "hit": 0, "f1": 0.0, "citation": 0.0, "latency_ms": 0}
        )
        bucket["n"] += 1
        bucket["hit"] += row["hit"]
        bucket["f1"] += row["f1"]
        bucket["citation"] += row["citation"]
        bucket["latency_ms"] += row["latency_ms"]
    for bucket in summary.values():
        n = max(bucket["n"], 1)
        bucket["hit"] = round(bucket["hit"] / n, 4)
        bucket["f1"] = round(bucket["f1"] / n, 4)
        bucket["citation"] = round(bucket["citation"] / n, 4)
        bucket["latency_ms"] = int(bucket["latency_ms"] / n)

    RESULTS.write_text(
        json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print("wrote", RESULTS)


if __name__ == "__main__":
    os.chdir(ROOT)
    main()
