# 基于 GraphRAG 的《黑神话：悟空》影神图多智能体问答系统

浙江理工大学信息学院《创新实践》课程设计。

- 学号：2023337621104
- 姓名：金科丞
- 基线项目：[Chat-BlackMyth](https://github.com/Nijikadesu/Chat-BlackMyth)（MIT）

本仓库在 Chat-BlackMyth 的数据管道、TinyGraph 图谱构建与 Neo4j 存储之上，将单次检索升级为多轮推理智能体：Planner、Dual-Retrieval、Synthesizer-Verifier 协作，按证据缺口拆解子问题，在图谱多跳与文本检索之间动态路由，并给出带引用的可解释答案。

可行性分析报告见 [`docs/2023337621104_金科丞_创新实践可行性分析报告.docx`](docs/2023337621104_金科丞_创新实践可行性分析报告.docx)。基线原 README 见 [`docs/Chat-BlackMyth-README.md`](docs/Chat-BlackMyth-README.md)。

## 目标

用户用自然语言提问，系统在 Neo4j 知识图谱与原文块上完成检索与多跳推理，返回带推理路径和引用的中文答案，并与「无图谱大模型」「原版单次 GraphRAG」对照。

| 子系统 | 职责 |
| --- | --- |
| 知识图谱 | 影神图 Markdown 分块、实体/三元组抽取、Neo4j、Leiden 社区报告 |
| 智能体推理 | 问题路由、子问题生成、双路检索、答案合成与校验 |
| 评估 | 多跳测试集、与基线对照、时延与引用覆盖 |
| 交互 | Gradio 对话、图谱初始化、推理路径展示 |

## 当前进度

- [x] 从 Chat-BlackMyth 建立课程仓库
- [ ] 环境与样例语料，复现 `add_document` / `local_query`
- [ ] 修复 `webdemo.py` 基座切换，跑通双机器人对照
- [ ] 实现 Planner、Dual-Retrieval、Verifier 与迭代控制
- [ ] 推理路径面板与 40 题测试集
- [ ] 对照实验、设计报告与演示视频

## 快速开始

1. 安装 Neo4j 5.24、OpenJDK 17、GDS 2.10.1。
2. 复制环境变量并填写密钥：

```bash
copy .env.example .env
```

至少配置 `ZHIPUAI_API_KEY`、`NEO4J_URL`、`NEO4J_USER`、`NEO4J_PASS`。

3. 安装 Python 依赖（建议 conda 环境 `python>=3.8`）：

```bash
pip install -r requirements.txt
```

4. 抓取影神图语料：

```bash
cd download_data
python get_data_from_url.py
```

5. 命令行或网页演示：

```bash
python -i graphdemo.py
python webdemo.py
```

网页默认地址：<http://localhost:7860>。

全量影神图建图约需数小时。课堂演示请使用小规模样例语料。

## 仓库说明

本仓库由 [Chat-BlackMyth](https://github.com/Nijikadesu/Chat-BlackMyth) 克隆而来，远程 `upstream` 指向该项目。GraphRAG 实现参考 [tiny-graphrag](https://github.com/limafang/tiny-graphrag)。影神图文本来自公开攻略站点，仅作课程教学演示。
