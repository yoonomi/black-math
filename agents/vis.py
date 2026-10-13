from typing import Any, Dict, List

import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")


def triples_figure(triples: List[Dict[str, Any]], title: str = "检索子图"):
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    ax.set_title(title)
    if not triples:
        ax.text(0.5, 0.5, "暂无图谱命中", ha="center", va="center")
        ax.axis("off")
        fig.tight_layout()
        return fig

    nodes = []
    for t in triples[:24]:
        for k in ("src", "dst"):
            name = t.get(k)
            if name and name not in nodes:
                nodes.append(name)
    n = max(len(nodes), 1)
    import math

    pos = {}
    for i, name in enumerate(nodes):
        ang = 2 * math.pi * i / n
        pos[name] = (math.cos(ang), math.sin(ang))

    for t in triples[:24]:
        src, dst = t.get("src"), t.get("dst")
        if src not in pos or dst not in pos:
            continue
        x1, y1 = pos[src]
        x2, y2 = pos[dst]
        ax.annotate(
            "",
            xy=(x2, y2),
            xytext=(x1, y1),
            arrowprops=dict(arrowstyle="->", color="#8B4513", lw=1.2),
        )
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        ax.text(mx, my, t.get("rel") or "", fontsize=8, color="#4a3728", ha="center")

    for name, (x, y) in pos.items():
        ax.scatter([x], [y], s=420, c="#c9a227", zorder=3)
        ax.text(x, y, name, fontsize=8, ha="center", va="center", zorder=4)

    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.axis("off")
    fig.tight_layout()
    return fig
