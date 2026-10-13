# 基于 GraphRAG 的《黑神话：悟空》影神图多智能体问答系统

浙江理工大学信息学院《创新实践》。学号 2023337621104，姓名金科丞。

同一套影神图知识图谱上，切换智谱 / DeepSeek / Grok，对照多智能体 GraphRAG 与纯生成，并用评测页展示 Hit@1、引用覆盖和时延。

基线来自 [Chat-BlackMyth](https://github.com/Nijikadesu/Chat-BlackMyth)（MIT）。远程仓库：https://github.com/yoonomi/black-math

## 环境

1. Python 3.10 虚拟环境（仓库内 `.venv`）。
2. Neo4j（bolt://localhost:7687）。有 GDS 更好，没有也能回退为单一社区。
3. 复制 `.env.example` 为 `.env`，填写 `ZHIPU_API_KEY`。DeepSeek / Grok 可选。

```bat
python -m venv .venv
.venv\Scripts\pip install -r requirements-app.txt
copy .env.example .env
```

## 建样例图并试问答

```bat
.venv\Scripts\python graphdemo.py
```

默认语料：前三章 `data/samples/portraits_ch1_3.md`（黑风山 / 黄风岭 / 小西天）。网页点「连接图谱」即可，不必重建。

## 网页

```bat
.venv\Scripts\python webdemo.py
```

打开 http://localhost:7860

- 问答：选模型，先点「初始化 GraphRAG」，再提问。左栏 GraphRAG，右栏纯生成。
- 性能：先跑评测，再点「加载 results.json」。

## 评测

```bat
.venv\Scripts\python eval/run_eval.py
```

结果写入 `eval/results.json`。设计报告见 `docs/设计报告.md`。

## 说明

`.env`、`workspace/` 不入库。全量影神图可自行抓取，不作为演示前提。
