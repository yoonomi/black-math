"""用新的关键词规则重打已有 results.json，不重新调用模型。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from eval.run_eval import hit_at_1  # noqa: E402

QUESTIONS = ROOT / "eval" / "questions.json"
RESULTS = ROOT / "eval" / "results.json"


def main():
    qs = {q["id"]: q for q in json.loads(QUESTIONS.read_text(encoding="utf-8"))["questions"]}
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    rows = data["rows"]
    for row in rows:
        q = qs[row["id"]]
        row["hit"] = hit_at_1(row.get("pred") or "", q["answer"], q.get("aliases"))
    summary = {}
    by_type = {}
    for row in rows:
        key = f"{row['model']}/{row['mode']}"
        bucket = summary.setdefault(
            key, {"n": 0, "hit": 0, "f1": 0.0, "citation": 0.0, "latency_ms": 0}
        )
        bucket["n"] += 1
        bucket["hit"] += row["hit"]
        bucket["f1"] += row.get("f1") or 0
        bucket["citation"] += row.get("citation") or 0
        bucket["latency_ms"] += row.get("latency_ms") or 0
        tkey = f"{key}/{row['type']}"
        tb = by_type.setdefault(tkey, {"n": 0, "hit": 0})
        tb["n"] += 1
        tb["hit"] += row["hit"]
    for bucket in summary.values():
        n = max(bucket["n"], 1)
        bucket["hit"] = round(bucket["hit"] / n, 4)
        bucket["f1"] = round(bucket["f1"] / n, 4)
        bucket["citation"] = round(bucket["citation"] / n, 4)
        bucket["latency_ms"] = int(bucket["latency_ms"] / n)
    for tb in by_type.values():
        tb["hit"] = round(tb["hit"] / max(tb["n"], 1), 4)
    data["summary"] = summary
    data["by_type"] = by_type
    RESULTS.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
