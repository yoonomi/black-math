import json
import os
from pathlib import Path

import gradio as gr
import pandas as pd

from agents.loop import ask
from graphrag.config import get_chat_llm, get_embedding, load_env, neo4j_conf
from graphrag.graph import TinyGraph
from graphrag.llm.factory import available_llms, provider_status

load_env()

ROOT = Path(__file__).resolve().parent
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


def init_graph(data_path):
    global graph
    path = (data_path or "").strip() or SAMPLE
    if not os.path.exists(path):
        return f"找不到文件: {path}"
    try:
        url, user, password = neo4j_conf()
        graph = TinyGraph(url, user, password, get_chat_llm("zhipu"), get_embedding())
        graph.add_document(path)
        return f"已加载 {path}，可用模型: {', '.join(available_llms())}"
    except Exception as e:
        return f"初始化失败: {e}"


def combined_response(history1, history2, user_input, model_label):
    history1 = history1 or []
    history2 = history2 or []
    if not user_input:
        return history1, history2, "", "请输入问题"
    if graph is None:
        return history1, history2, "", "请先初始化 GraphRAG"
    llm = _llm(model_label)
    graph.llm = llm
    try:
        packed = ask(user_input, graph, llm)
        left = packed["answer"]
        path = " → ".join(packed.get("path") or [])
        cites = ", ".join(packed.get("cites") or [])
        extra = f"\n\n路径: {path}\n实体: {cites}\n时延: {packed.get('latency_ms')} ms"
        left = left + extra
    except Exception as e:
        left = f"GraphRAG 失败: {e}"
        extra = str(e)
    try:
        right = llm.predict(user_input)
    except Exception as e:
        right = f"纯生成失败: {e}"
        extra = str(e)
    history1 = history1 + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": left},
    ]
    history2 = history2 + [
        {"role": "user", "content": user_input},
        {"role": "assistant", "content": right},
    ]
    return history1, history2, "", extra


def load_results():
    if not RESULTS.exists():
        empty = pd.DataFrame()
        return empty, None, empty, "还没有 eval/results.json，请先运行 python eval/run_eval.py"
    data = json.loads(RESULTS.read_text(encoding="utf-8"))
    summary_rows = []
    for key, val in data.get("summary", {}).items():
        model, mode = key.split("/", 1)
        summary_rows.append({"model": model, "mode": mode, **val})
    summary_df = pd.DataFrame(summary_rows)
    rows_df = pd.DataFrame(data.get("rows", []))
    chart = None
    if not summary_df.empty:
        import matplotlib.pyplot as plt

        fig, axes = plt.subplots(1, 2, figsize=(8, 3.2))
        pivot_hit = summary_df.pivot(index="model", columns="mode", values="hit")
        pivot_hit.plot(kind="bar", ax=axes[0], rot=0)
        axes[0].set_title("Hit@1")
        axes[0].set_ylim(0, 1)
        pivot_lat = summary_df.pivot(index="model", columns="mode", values="latency_ms")
        pivot_lat.plot(kind="bar", ax=axes[1], rot=0)
        axes[1].set_title("平均时延 ms")
        fig.tight_layout()
        chart = fig
    return summary_df, chart, rows_df, "已加载评测结果"


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
同一套图谱上切换智谱 / DeepSeek / Grok，对照 GraphRAG 与纯生成。
"""

with gr.Blocks() as demo:
    gr.Markdown(TITLE)
    with gr.Tabs():
        with gr.Tab("问答"):
            model_dd = gr.Radio(CHOICES, value=CHOICES[0], label="问答模型")
            with gr.Row():
                data_path = gr.Textbox(label="数据路径", value=SAMPLE)
                update_button = gr.Button("初始化 GraphRAG")
                init_message = gr.Textbox(label="初始化提示", interactive=False)
            with gr.Row():
                chatbot1 = gr.Chatbot(label="GraphRAG 多智能体", height=420)
                chatbot2 = gr.Chatbot(label="同模型纯生成", height=420)
            user_input = gr.Textbox(placeholder="例如：黑风山土地是谁？", lines=1, label="问题")
            send_button = gr.Button("发送")
            path_box = gr.Textbox(label="推理路径 / 引用", interactive=False, lines=4)
            update_button.click(init_graph, inputs=[data_path], outputs=[init_message])
            send_button.click(
                combined_response,
                inputs=[chatbot1, chatbot2, user_input, model_dd],
                outputs=[chatbot1, chatbot2, user_input, path_box],
            )

        with gr.Tab("性能"):
            refresh = gr.Button("加载 results.json")
            summary_table = gr.Dataframe(label="模型 × 模式 汇总")
            hit_plot = gr.Plot(label="Hit@1 与时延")
            rows_table = gr.Dataframe(label="逐题明细")
            status = gr.Textbox(label="状态", interactive=False)
            qid = gr.Textbox(label="题目 id，如 q1", placeholder="q1")
            compare_table = gr.Dataframe(label="该题三模型对照")
            refresh.click(
                load_results,
                outputs=[summary_table, hit_plot, rows_table, status],
            )
            qid.change(question_compare, inputs=[qid, rows_table], outputs=[compare_table])

if __name__ == "__main__":
    demo.launch()
