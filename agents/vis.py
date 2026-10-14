from pathlib import Path
from typing import Any, Dict, List, Optional

import matplotlib
import matplotlib.pyplot as plt
from matplotlib import font_manager

matplotlib.use("Agg")

_FONT: Optional[font_manager.FontProperties] = None


def cjk_font() -> font_manager.FontProperties:
    global _FONT
    if _FONT is not None:
        return _FONT
    candidates = [
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyhbd.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
        Path(r"C:\Windows\Fonts\simsun.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttf"),
    ]
    for path in candidates:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            _FONT = font_manager.FontProperties(fname=str(path))
            name = _FONT.get_name()
            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["font.sans-serif"] = [name, "Microsoft YaHei", "SimHei", "SimSun"]
            plt.rcParams["axes.unicode_minus"] = False
            return _FONT
    _FONT = font_manager.FontProperties()
    plt.rcParams["axes.unicode_minus"] = False
    return _FONT


def triples_figure(triples: List[Dict[str, Any]], title: str = "检索子图"):
    font = cjk_font()
    fig, ax = plt.subplots(figsize=(8.2, 5.2))
    ax.set_title(title, fontproperties=font)
    if not triples:
        ax.text(0.5, 0.5, "暂无图谱命中", ha="center", va="center", fontproperties=font)
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
        ax.text(
            mx,
            my,
            t.get("rel") or "",
            fontsize=8,
            color="#4a3728",
            ha="center",
            fontproperties=font,
        )

    for name, (x, y) in pos.items():
        ax.scatter([x], [y], s=420, c="#c9a227", zorder=3)
        ax.text(x, y, name, fontsize=8, ha="center", va="center", zorder=4, fontproperties=font)

    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.axis("off")
    fig.tight_layout()
    return fig


LABELS = {
    "zhipu": "智谱",
    "deepseek": "DeepSeek",
    "qwen": "千问",
    "grok": "Grok",
    "graphrag": "GraphRAG",
    "plain": "纯生成",
}


def _series_name(model: str, mode: str) -> str:
    return f"{LABELS.get(model, model)}·{LABELS.get(mode, mode)}"


def _apply_tick_font(ax, font, size=9):
    for lab in ax.get_xticklabels() + ax.get_yticklabels():
        lab.set_fontproperties(font)
        lab.set_fontsize(size)


def compare_bars(summary_rows):
    """正确率、图谱引用、生成速度 三组柱状对照。"""
    import numpy as np

    font = cjk_font()
    if not summary_rows:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "暂无评测数据", ha="center", fontproperties=font)
        ax.axis("off")
        return fig

    names = [_series_name(r["model"], r["mode"]) for r in summary_rows]
    hits = [float(r.get("hit") or 0) for r in summary_rows]
    cites = [float(r.get("citation") or 0) for r in summary_rows]
    lats = [max(float(r.get("latency_ms") or 1), 1) for r in summary_rows]
    fastest = min(lats)
    speeds = [fastest / x for x in lats]

    fig, axes = plt.subplots(1, 3, figsize=(11.5, 3.6))
    x = np.arange(len(names))
    colors = ["#c9a227", "#8a7a5a", "#3d6b8c", "#5b8c5a", "#a65d3f", "#6b5b95"][: len(names)]

    specs = [
        (hits, "正确率 Hit@1", 1.05),
        (cites, "图谱引用覆盖", 1.05),
        (speeds, "生成速度（相对最快=1）", 1.05),
    ]
    for ax, (vals, title, ymax) in zip(axes, specs):
        ax.bar(x, vals, color=colors, width=0.68)
        ax.set_title(title, fontproperties=font, fontsize=11)
        ax.set_xticks(x)
        ax.set_xticklabels(names, rotation=20, ha="right")
        _apply_tick_font(ax, font, 8)
        ax.set_ylim(0, ymax)
        ax.set_ylabel("")
    fig.suptitle("智能体对照：正确率 · 图谱质量 · 速度", fontproperties=font, fontsize=13)
    fig.tight_layout()
    return fig


def compare_radar(summary_rows):
    """雷达图：正确率、F1、引用、速度。"""
    import numpy as np

    font = cjk_font()
    fig = plt.figure(figsize=(6.4, 5.2))
    ax = fig.add_subplot(111, polar=True)
    if not summary_rows:
        ax.text(0, 0, "暂无数据", fontproperties=font)
        return fig

    axes_names = ["正确率", "答案 F1", "图谱引用", "生成速度"]
    n_ax = len(axes_names)
    angles = np.linspace(0, 2 * np.pi, n_ax, endpoint=False).tolist()
    angles += angles[:1]

    lats = [max(float(r.get("latency_ms") or 1), 1) for r in summary_rows]
    fastest = min(lats)
    colors = ["#c9a227", "#8a7a5a", "#3d6b8c", "#5b8c5a", "#a65d3f", "#6b5b95"]

    for i, row in enumerate(summary_rows):
        speed = fastest / max(float(row.get("latency_ms") or 1), 1)
        vals = [
            float(row.get("hit") or 0),
            min(float(row.get("f1") or 0), 1.0),
            float(row.get("citation") or 0),
            speed,
        ]
        vals += vals[:1]
        name = _series_name(row["model"], row["mode"])
        ax.plot(angles, vals, color=colors[i % len(colors)], linewidth=2, label=name)
        ax.fill(angles, vals, color=colors[i % len(colors)], alpha=0.12)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(axes_names, fontproperties=font, fontsize=10)
    ax.set_ylim(0, 1.0)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    legend = ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), prop=font, fontsize=8)
    ax.set_title("综合画像（越靠外越好）", fontproperties=font, pad=16)
    fig.tight_layout()
    return fig


def type_bars(type_rows):
    """各题型 Hit@1。"""
    import numpy as np

    font = cjk_font()
    fig, ax = plt.subplots(figsize=(10.5, 3.8))
    if not type_rows:
        ax.text(0.5, 0.5, "暂无题型数据", ha="center", fontproperties=font)
        ax.axis("off")
        return fig

    type_map = {"fact": "事实", "hop": "多跳关系", "compare": "对比"}
    series = {}
    types = []
    for r in type_rows:
        name = _series_name(r["model"], r["mode"])
        t = type_map.get(r.get("type"), r.get("type") or "")
        series.setdefault(name, {})[t] = float(r.get("hit") or 0)
        if t not in types:
            types.append(t)

    names = list(series.keys())
    x = np.arange(len(types))
    width = 0.8 / max(len(names), 1)
    colors = ["#c9a227", "#8a7a5a", "#3d6b8c", "#5b8c5a", "#a65d3f", "#6b5b95"]
    for i, name in enumerate(names):
        vals = [series[name].get(t, 0) for t in types]
        ax.bar(x + i * width, vals, width=width, label=name, color=colors[i % len(colors)])
    ax.set_xticks(x + width * (len(names) - 1) / 2)
    ax.set_xticklabels(types)
    _apply_tick_font(ax, font, 10)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Hit@1", fontproperties=font)
    ax.set_title("题型正确率对照", fontproperties=font)
    ax.legend(prop=font, fontsize=8)
    fig.tight_layout()
    return fig

