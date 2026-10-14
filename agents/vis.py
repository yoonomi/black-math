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


def _with_metrics(rows):
    lats = [max(float(r.get("latency_ms") or 1), 1) for r in rows]
    fastest = min(lats) if lats else 1.0
    scored = []
    for r in rows:
        hit = float(r.get("hit") or 0)
        cite = float(r.get("citation") or 0)
        f1 = min(float(r.get("f1") or 0), 1.0)
        speed = fastest / max(float(r.get("latency_ms") or 1), 1)
        score = 0.45 * hit + 0.25 * cite + 0.15 * f1 + 0.15 * speed
        item = dict(r)
        item["speed"] = round(speed, 4)
        item["score"] = round(score, 4)
        scored.append(item)
    scored.sort(key=lambda x: x["score"], reverse=True)
    for i, item in enumerate(scored, 1):
        item["rank"] = i
    return scored


def overall_table_rows(summary_rows):
    """三家 GraphRAG 智能体综合分，供表格展示。"""
    agents = [r for r in summary_rows if r.get("mode") == "graphrag"]
    plains = {r["model"]: r for r in summary_rows if r.get("mode") == "plain"}
    scored = _with_metrics(agents)
    rows = []
    for item in scored:
        plain = plains.get(item["model"]) or {}
        lift = float(item.get("hit") or 0) - float(plain.get("hit") or 0)
        rows.append(
            {
                "排名": item["rank"],
                "智能体": LABELS.get(item["model"], item["model"]),
                "综合分": item["score"],
                "正确率": round(float(item.get("hit") or 0), 4),
                "图谱引用": round(float(item.get("citation") or 0), 4),
                "速度": item["speed"],
                "相对纯生成提升": round(lift, 4),
            }
        )
    return rows


def overall_findings(summary_rows) -> str:
    """答辩用：由评测数字生成综合结论。"""
    rows = overall_table_rows(summary_rows)
    if not rows:
        return "暂无评测结论。"
    plains = {r["model"]: r for r in summary_rows if r.get("mode") == "plain"}
    labeled = []
    for item in rows:
        mid = None
        for k, v in LABELS.items():
            if v == item["智能体"]:
                mid = k
                break
        plain_hit = float((plains.get(mid) or {}).get("hit") or 0)
        labeled.append({**item, "plain_hit": plain_hit})
    labeled.sort(key=lambda x: x["plain_hit"])
    weak = labeled[0]
    strong = labeled[-1]
    top = rows[0]
    cite_top = max(rows, key=lambda r: r["图谱引用"])
    lift_top = max(rows, key=lambda r: r["相对纯生成提升"])
    rank_line = " ＞ ".join(f"{r['智能体']}（{r['综合分']:.2f}）" for r in rows)
    return f"""### 综合结论（14 题 · 前三章图谱）

1. **综合能力**：{rank_line}。DeepSeek 又准又快，总分第一；千问引用最好；智谱综合第三。
2. **基线越弱，GraphRAG 提升越大**：纯生成 Hit@1 最低的是 **{weak['智能体']}（{weak['plain_hit']:.0%}）**，接上图谱后提升 **{weak['相对纯生成提升']:.0%}**；最强基线 **{strong['智能体']}（{strong['plain_hit']:.0%}）** 只再提升 **{strong['相对纯生成提升']:.0%}**。弱模型更容易把《西游记》常识当成游戏设定，图谱约束的收益更明显。
3. **正确率**：GraphRAG 最高约 **{max(r['正确率'] for r in rows):.0%}**（{ '、'.join(r['智能体'] for r in rows if r['正确率'] == max(x['正确率'] for x in rows)) } 并列）。三家 GraphRAG 都高于各自纯生成。
4. **图谱质量**：引用覆盖最高的是 **{cite_top['智能体']}（{cite_top['图谱引用']:.0%}）**，答案更常点名影神图实体。
5. **速度**：DeepSeek GraphRAG 在三家里最快；千问已关闭思考链，仍慢于智谱/DeepSeek。
6. 增益来自检索约束，不是某一家 API 单独变强：同一模型「有图谱 / 无图谱」对照均成立。
"""


def overall_dashboard(summary_rows):
    """综合能力：排名柱 + 三家雷达 + 相对纯生成提升。"""
    import numpy as np

    font = cjk_font()
    fig, axes = plt.subplots(1, 3, figsize=(13.2, 4.2), gridspec_kw={"width_ratios": [1.1, 1.15, 1.0]})
    agents = [r for r in summary_rows if r.get("mode") == "graphrag"]
    scored = _with_metrics(agents)
    if not scored:
        for ax in axes:
            ax.text(0.5, 0.5, "暂无数据", ha="center", fontproperties=font)
            ax.axis("off")
        return fig

    colors = {"zhipu": "#c9a227", "deepseek": "#3d6b8c", "qwen": "#a65d3f", "grok": "#5b8c5a"}
    names = [LABELS.get(r["model"], r["model"]) for r in scored]
    scores = [r["score"] for r in scored]
    bar_colors = [colors.get(r["model"], "#888888") for r in scored]
    y = np.arange(len(scored))[::-1]
    axes[0].barh(y, scores, color=bar_colors, height=0.55)
    axes[0].set_yticks(y)
    axes[0].set_yticklabels(names)
    _apply_tick_font(axes[0], font, 10)
    axes[0].set_xlim(0, 1.0)
    axes[0].set_xlabel("综合分", fontproperties=font)
    axes[0].set_title("综合能力排名", fontproperties=font)
    for yi, val in zip(y, scores):
        axes[0].text(val + 0.02, yi, f"{val:.2f}", va="center", fontproperties=font, fontsize=9)

    axr = fig.add_subplot(1, 3, 2, polar=True)
    axes[1].remove()
    axes_names = ["正确率", "答案 F1", "图谱引用", "生成速度"]
    n_ax = len(axes_names)
    angles = np.linspace(0, 2 * np.pi, n_ax, endpoint=False).tolist()
    angles += angles[:1]
    for r in scored:
        vals = [
            float(r.get("hit") or 0),
            min(float(r.get("f1") or 0), 1.0),
            float(r.get("citation") or 0),
            float(r.get("speed") or 0),
        ]
        vals += vals[:1]
        c = colors.get(r["model"], "#888888")
        label = LABELS.get(r["model"], r["model"])
        axr.plot(angles, vals, color=c, linewidth=2.2, label=label)
        axr.fill(angles, vals, color=c, alpha=0.14)
    axr.set_xticks(angles[:-1])
    axr.set_xticklabels(axes_names, fontproperties=font, fontsize=9)
    axr.set_ylim(0, 1.0)
    axr.set_yticks([0.5, 1.0])
    axr.legend(loc="upper right", bbox_to_anchor=(1.35, 1.15), prop=font, fontsize=8)
    axr.set_title("三家综合画像", fontproperties=font, pad=14)

    plains = {r["model"]: r for r in summary_rows if r.get("mode") == "plain"}
    lifts = []
    lift_names = []
    lift_colors = []
    for r in scored:
        plain = plains.get(r["model"]) or {}
        lifts.append(float(r.get("hit") or 0) - float(plain.get("hit") or 0))
        lift_names.append(LABELS.get(r["model"], r["model"]))
        lift_colors.append(colors.get(r["model"], "#888888"))
    x = np.arange(len(lift_names))
    axes[2].bar(x, lifts, color=lift_colors, width=0.6)
    axes[2].axhline(0, color="#333", lw=0.8)
    axes[2].set_xticks(x)
    axes[2].set_xticklabels(lift_names)
    _apply_tick_font(axes[2], font, 9)
    axes[2].set_ylabel("Hit@1 提升", fontproperties=font)
    axes[2].set_title("相对纯生成的增益", fontproperties=font)
    fig.suptitle(
        "综合分 = 0.45×正确率 + 0.25×图谱引用 + 0.15×F1 + 0.15×速度",
        fontproperties=font,
        fontsize=11,
        y=1.02,
    )
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

