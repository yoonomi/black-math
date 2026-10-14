from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Evidence:
    entities: List[Dict[str, Any]] = field(default_factory=list)
    triples: List[Dict[str, Any]] = field(default_factory=list)
    chunks: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    subquestions: List[str] = field(default_factory=list)

    def as_prompt(self) -> str:
        lines = []
        names = []
        for e in self.entities:
            n = (e.get("name") or "").strip()
            if n and n not in names:
                names.append(n)
        if names:
            lines.append("相关人物: " + "、".join(names[:12]))
        seen = []
        for t in self.triples:
            rel = (t.get("rel") or "").strip()
            if rel in {"", "是", "为"}:
                continue
            key = f"{t.get('src')}-{rel}-{t.get('dst')}"
            if key not in seen:
                seen.append(key)
            if len(seen) >= 10:
                break
        if seen:
            lines.append("关系: " + "；".join(seen))
        texts = []
        for chunk in self.chunks[:2]:
            piece = (chunk or "").strip()
            if len(piece) > 700:
                piece = piece[:700] + "…"
            if piece:
                texts.append(piece)
        if texts:
            lines.append("设定摘录:\n" + "\n".join(texts))
        return "\n".join(lines) if lines else "暂无证据"
