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
        if self.subquestions:
            lines.append("子问题: " + " | ".join(self.subquestions))
        if self.entities:
            lines.append("实体: " + ", ".join(e.get("name", "") for e in self.entities))
        if self.triples:
            lines.append(
                "三元组: "
                + "; ".join(f"{t.get('src')}-{t.get('rel')}-{t.get('dst')}" for t in self.triples)
            )
        if self.chunks:
            lines.append("原文: " + "\n".join(self.chunks[:6]))
        if self.notes:
            lines.append("备注: " + " ".join(self.notes))
        return "\n".join(lines) if lines else "暂无证据"
