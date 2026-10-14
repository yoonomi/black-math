import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import gradio as gr
import pandas as pd

from agents.loop import ask
from agents.vis import compare_bars, compare_radar, triples_figure, type_bars
from graphrag.config import get_chat_llm, get_embedding, load_env, neo4j_conf
from graphrag.graph import TinyGraph
from graphrag.llm.factory import available_llms, provider_status

load_env()

ROOT = Path(__file__).resolve().parent
SAMPLE = str(ROOT / "data" / "samples" / "portraits_ch1_3.md")
if not Path(SAMPLE).exists():
    SAMPLE = str(ROOT / "data" / "samples" / "portraits_sample.md")
RESULTS = ROOT / "eval" / "results.json"

graph = None
chat_llms = {}


def _label_map():
    status = provider_status()
    labels = []
    mapping = {"智谱": "zhipu", "DeepSeek": "deepseek", "Grok": "grok"}
    for zh, key in mapping.items():
        if status.get(key):
            labels.append(zh)
    return labels or ["智谱"], mapping


CHOICES, LABEL_TO_KEY = _label_map()


def _llm(label: str):
    key = LABEL_TO_KEY.get(label, "zhipu")
    if key not in chat_llms:
        chat_llms[key] = get_chat_llm(key)
    return chat_llms[key]


def _graph_stats():
    if graph is None:
        return "未连接"
    with graph.driver.session() as s:
        n = s.run("MATCH (e:Entity) RETURN count(e) AS c").single()["c"]
        r = s.run("MATCH ()-[rel]->() RETURN count(rel) AS c").single()["c"]
    return f"实体 {n}，关系 {r}"


def init_graph(data_path, rebuild):
    global graph
    path = (data_path or "").strip() or SAMPLE
    try:
        url, user, password = neo4j_conf()
        graph = TinyGraph(url, user, password, get_chat_llm("zhipu"), get_embedding())
        if rebuild:
            if not os.path.exists(path):
                return f"找不到文件: {path}"
            graph.add_document(path)
            return f"已建图 {path}。{_graph_stats()}。模型: {', '.join(available_llms())}"
        return f"已连接 Neo4j。{_graph_stats()}。模型: {', '.join(available_llms())}。默认语料 {path}"
    except Exception as e:
        return f"初始化失败: {e}"


def combined_response(history1, history2, user_input, model_label):
    history1 = history1 or []
    history2 = history2 or []
    empty_df = pd.DataFrame()
    empty_fig = triples_figure([])
    if not user_input:
        return history1, history2, "", "请输入问题", empty_df, empty_df, empty_fig
    if graph is None:
        return history1, history2, "", "请先点「连接图谱」", empty_df, empty_df, empty_fig
    llm = _llm(model_label)
    graph.llm = llm
    extra = ""
    ent_df = empty_df
    tri_df = empty_df
    fig = empty_fig
    packed = None
    left = ""
    right = ""

    def _run_graph():
        return ask(user_input, graph, llm)

    def _run_plain():
        return llm.predict(user_input)

    with ThreadPoolExecutor(max_workers=2) as pool:
        fut_graph = pool.submit(_run_graph)
        fut_plain = pool.submit(_run_plain)
        try:
            packed = fut_graph.result()
        except Exception as e:
            left = f"GraphRAG 失败: {e}"
            extra = str(e)
        try:
            right = fut_plain.result()
        except Exception as e:
            right = f"纯生成失败: {e}"

    if packed is not None:
        left = packed["answer"]
        path = " → ".join(packed.get("path") or [])
        cites = list(dict.fromkeys(packed.get("cites") or []))
        triples = packed.get("triples") or []
        extra = (
            f"校验: {packed.get('mark')}  |  轮次: {packed.get('rounds')}  |  "
            f"时延: {packed.get('latency_ms')} ms\n"
            f"子问题: {path or '（无）'}\n"
            f"引用实体: {', '.join(cites) or '（无）'}"
        )
        ent_df = pd.DataFrame({"实体": cites})
        if triples:
            tri_df = pd.DataFrame(triples)
        fig = triples_figure(triples, title=f"检索子图 · {model_label}")
    history1 = history1 + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": left},
    ]
    history2 = history2 + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": right},
    ]
    return history1, history2, "", extra, ent_df, tri_df, fig


def load_results():
    empty = pd.DataFrame()
    if not RESULTS.exists():
        return (
            empty,
            None,
            None,
            None,
            empty,
            empty,
            "还没有 eval/results.json，请先运行 python eval/run_eval.py",
        )
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    summary_rows = []
    for key, val in data.get("summary", {}).items():
        model, mode = key.split("/", 1)
        summary_rows.append({"model": model, "mode": mode, **val})
    summary_df = pd.DataFrame(summary_rows)
    type_rows = []
    for key, val in data.get("by_type", {}).items():
        parts = key.split("/")
        if len(parts) == 3:
            type_rows.append(
                {"model": parts[0], "mode": parts[1], "type": parts[2], **val}
            )
    type_df = pd.DataFrame(type_rows)
    rows_df = pd.DataFrame(data.get("rows", []))
    bars = compare_bars(summary_rows)
    radar = compare_radar(summary_rows)
    types = type_bars(type_rows)
    return summary_df, bars, radar, types, type_df, rows_df, "已加载评测：正确率 / 图谱引用 / 速度"


def question_compare(qid, rows_df):
    if rows_df is None or getattr(rows_df, "empty", True):
        return pd.DataFrame()
    if "id" not in rows_df.columns:
        return pd.DataFrame()
    if not qid:
        return rows_df
    return rows_df[rows_df["id"] == qid]


TITLE = """
# 影神图多智能体问答评测台
前三章图谱（黑风山 / 黄风岭 / 小西天）。先点「连接图谱」，再提问。
左栏 GraphRAG，右栏同模型纯生成；下方展示检索子图、实体和三元组。
"""

EXAMPLES = [
    "黑风山土地是谁？",
    "黑风大王和白衣秀士是什么关系？",
    "哪些妖怪曾与孙悟空交过手？",
    "黄眉是谁？",
    "广智和广谋是什么来历？",
]

with gr.Blocks() as demo:
    gr.Markdown(TITLE)
    with gr.Tabs():
        with gr.Tab("问答"):
            model_dd = gr.Radio(CHOICES, value=CHOICES[0], label="问答模型")
            with gr.Row():
                data_path = gr.Textbox(label="语料路径（仅勾选重建时使用）", value=SAMPLE)
                rebuild = gr.Checkbox(label="重建图谱（耗时长）", value=False)
                update_button = gr.Button("连接图谱", variant="primary")
            init_message = gr.Textbox(label="图谱状态", interactive=False)
            with gr.Row():
                chatbot1 = gr.Chatbot(label="GraphRAG 多智能体", height=380)
                chatbot2 = gr.Chatbot(label="同模型纯生成", height=380)
            user_input = gr.Textbox(placeholder="例如：黄眉是谁？", lines=1, label="问题")
            send_button = gr.Button("发送", variant="primary")
            gr.Examples(examples=EXAMPLES, inputs=user_input)
            path_box = gr.Textbox(label="推理过程", interactive=False, lines=4)
            graph_plot = gr.Plot(label="本轮检索子图")
            with gr.Row():
                ent_table = gr.Dataframe(label="命中实体")
                tri_table = gr.Dataframe(label="命中三元组")
            update_button.click(
                init_graph, inputs=[data_path, rebuild], outputs=[init_message]
            )
            send_button.click(
                combined_response,
                inputs=[chatbot1, chatbot2, user_input, model_dd],
                outputs=[
                    chatbot1,
                    chatbot2,
                    user_input,
                    path_box,
                    ent_table,
                    tri_table,
                    graph_plot,
                ],
            )

        with gr.Tab("性能对照"):
            gr.Markdown(
                "对比 **GraphRAG 智能体** 与 **纯生成** 在智谱 / DeepSeek 上的正确率、图谱引用质量和生成速度。"
                "点「加载评测结果」。速度以最快一路为 1，越高越快。"
            )
            refresh = gr.Button("加载评测结果", variant="primary")
            status = gr.Textbox(label="状态", interactive=False)
            summary_table = gr.Dataframe(label="汇总：Hit@1 / F1 / 引用覆盖 / 时延")
            bars_plot = gr.Plot(label="正确率 · 图谱质量 · 速度")
            with gr.Row():
                radar_plot = gr.Plot(label="综合雷达图")
                type_plot = gr.Plot(label="题型正确率")
            type_table = gr.Dataframe(label="题型明细")
            rows_table = gr.Dataframe(label="逐题明细")
            qid = gr.Textbox(label="题目 id，如 q1", placeholder="q1")
            compare_table = gr.Dataframe(label="该题各智能体对照")
            refresh.click(
                load_results,
                outputs=[
                    summary_table,
                    bars_plot,
                    radar_plot,
                    type_plot,
                    type_table,
                    rows_table,
                    status,
                ],
            )
            qid.change(question_compare, inputs=[qid, rows_table], outputs=[compare_table])

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
