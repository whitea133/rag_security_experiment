# RAG Security Experiment

本项目是课程设计《面向检索增强生成的间接提示注入攻击检测与分层防御研究》的实验代码。项目实现了一个轻量级 RAG（Retrieval-Augmented Generation）安全实验原型，用于验证污染文档在 RAG 链路中被检索召回、进入上下文并影响大模型输出的过程，同时比较检索过滤、安全 Prompt 和组合防御对间接提示注入攻击的防护效果。

> 说明：本项目用于课程设计和防御性安全实验。数据集为自构造安全化样本，不包含真实密钥、真实隐私数据或可直接滥用的攻击载荷。

## 1. 项目目标

本实验主要回答以下问题：

1. 当 RAG 知识库中混入污染文档时，攻击触发问题是否会检索到恶意文档片段；
2. 恶意文档片段进入 Prompt 后，是否会诱导大模型产生错误结论、异常拒答或泄露上下文等非预期输出；
3. 仅使用安全 Prompt、仅使用检索过滤、以及二者组合时，对攻击成功率和正常问答可用性的影响有何不同；
4. 如何通过 MR@k、CIR、ASR、CASR、正常回答准确率、拒答率和平均延迟等指标分析 RAG 间接提示注入风险。

## 2. 技术栈

- Python 3.11+
- uv 依赖与环境管理
- DeepSeek API（OpenAI-compatible，用于正式实验）
- sentence-transformers embedding（可选）
- HashingEmbedder 离线 fallback（用于无法下载模型或快速验证流程）
- 内存向量 Top-k 检索
- JSONL 数据集
- CSV 实验结果与汇总指标

## 3. 项目结构

```text
rag_security_experiment/
├── data/                         # 实验数据集
│   ├── clean_docs.jsonl           # legacy 正常文档
│   ├── attack_docs.jsonl          # legacy 污染文档
│   ├── normal_questions.jsonl     # legacy 正常问题
│   ├── attack_questions.jsonl     # legacy 攻击触发问题
│   ├── injection_patterns.jsonl   # legacy 注入模式库
│   ├── v1/                        # V1 数据副本
│   ├── v2/                        # V2 场景化数据集
│   └── v2_full/                   # 正式实验使用的数据集
├── src/rag_security_experiment/   # 核心代码
│   ├── cli.py                     # 命令行入口：run / summarize
│   ├── config.py                  # 环境变量与路径配置
│   ├── data_loader.py             # JSONL 数据加载
│   ├── chunker.py                 # 文档分块
│   ├── embeddings.py              # embedding 与离线 fallback
│   ├── retriever.py               # 内存向量 Top-k 检索
│   ├── defense.py                 # 风险检测与检索过滤
│   ├── prompt_builder.py          # 普通 Prompt / 安全 Prompt 构造
│   ├── llm_client.py              # 大模型 API 或 Mock 调用
│   ├── evaluator.py               # 回答评价与人工复核标记
│   ├── experiment.py              # G0-G4 实验流程
│   └── metrics.py                 # 指标汇总与扩展统计
├── results/                       # 实验运行结果与汇总结果
│   ├── runs/                      # 每次问答的明细 CSV
│   └── summary/                   # 分组、攻击类型、过滤效果等汇总 CSV
├── outputs/                       # 论文中使用的表格和图像输出
├── .env.example                   # 环境变量示例
├── pyproject.toml                 # 项目依赖配置
└── README.md
```

## 4. 数据集说明

项目支持多个数据集版本：

| 数据集       | 说明                           |
| --------- | ---------------------------- |
| `legacy`  | 兼容根目录 `data/*.jsonl` 的早期实验流程 |
| `v1`      | V1 数据副本，用于保留原始实验数据           |
| `v2`      | 场景化增强数据集，包含攻击类型、难度和隐蔽度字段     |
| `v2_full` | 正式论文实验使用的数据集版本               |

正式实验采用 `v2_full`，主要包含：

| 数据类型   | 数量  | 作用                                 |
| ------ | ---:| ---------------------------------- |
| 正常文档   | 40  | 构成干净知识库和正常安全知识来源                   |
| 污染文档   | 52  | 模拟被间接提示注入污染的外部资料                   |
| 正常问题   | 30  | 测试正常问答能力与误报影响                      |
| 攻击触发问题 | 52  | 测试污染文档被召回后的攻击效果                    |
| 注入模式   | 18  | 用于风险检测中的模式相似度计算                    |
| 攻击类型   | 6   | 覆盖指令覆盖、角色伪装、上下文泄露、拒答破坏、错误信息注入和混淆隐藏 |

## 5. 实验组设置

五组实验均使用 `Top-k=3`。G1-G4 使用相同的污染知识库和攻击问题，用于比较不同防御策略在相同检索暴露条件下的效果。

| 组别  | 知识库         | Prompt 类型 | 检索过滤 | 实验目的               |
| --- | ----------- | --------- | ---- | ------------------ |
| G0  | 正常文档        | 普通 Prompt | 否    | 干净基线，验证正常问答能力      |
| G1  | 正常文档 + 污染文档 | 普通 Prompt | 否    | 无防御基线，验证攻击影响       |
| G2  | 正常文档 + 污染文档 | 安全 Prompt | 否    | 验证仅安全 Prompt 的防御效果 |
| G3  | 正常文档 + 污染文档 | 普通 Prompt | 是    | 验证仅检索过滤的防御效果       |
| G4  | 正常文档 + 污染文档 | 安全 Prompt | 是    | 验证组合防御效果           |

## 6. 评价指标

| 指标                 | 含义                                       |
| ------------------ | ---------------------------------------- |
| MR@k               | 恶意检索率，表示攻击样本的 Top-k 检索结果中包含恶意 chunk 的比例  |
| CIR                | 上下文注入率，表示恶意 chunk 进入最终 Prompt 的比例        |
| ASR                | 攻击成功率，表示模型输出满足攻击成功条件的比例                  |
| partial_ASR        | 部分攻击信号比例，表示回答中出现危险断言或异常拒答等部分攻击迹象的比例      |
| CASR               | 条件攻击成功率，表示恶意 chunk 已进入 Prompt 条件下的攻击成功比例 |
| normal_accuracy    | 正常回答准确率，表示正常问题回答命中预期关键词的比例               |
| refusal_rate       | 拒答率，表示模型异常拒答或无法回答的比例                     |
| manual_review_rate | 需要人工复核的样本比例                              |
| avg_latency_ms     | 平均响应延迟，单位为毫秒                             |

其中 MR@k、CIR 和 CASR 是本项目为分析 RAG 攻击链路而定义的过程性指标，用于区分“恶意内容被检索到”“恶意内容进入 Prompt”和“恶意内容影响最终输出”三个阶段。

## 7. 环境配置

### 7.1 安装依赖

在项目根目录执行：

```bash
uv sync
```

### 7.2 配置环境变量

复制 `.env.example` 为 `.env`，并按需要修改：

```env
LLM_PROVIDER=deepseek
LLM_BASE_URL=https://api.deepseek.com
LLM_API_KEY=your_deepseek_api_key_here
LLM_MODEL=deepseek-v4-flash
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
TOP_K=3
RISK_THRESHOLD=0.50
USE_MOCK_LLM=false
```

如果只是检查代码流程能否跑通，可以设置：

```env
USE_MOCK_LLM=true
```

如果无法下载 sentence-transformers 模型，可以在运行命令中加入 `--offline-embeddings`，使用本地 HashingEmbedder fallback。

## 8. 运行方式

### 8.1 快速验证流程（不调用真实大模型）

用于老师或复查者快速确认项目能运行。先在 `.env` 中设置 `USE_MOCK_LLM=true`，然后执行：

```bash
uv run python -m rag_security_experiment.cli run --all --dataset v2 --offline-embeddings --output results/runs/v2_smoke.csv
uv run python -m rag_security_experiment.cli summarize --input results/runs/v2_smoke.csv --output results/summary/v2_smoke_summary.csv --extended --prefix v2_smoke
```

该方式使用 Mock LLM 和离线 embedding，适合验证程序流程，但结果不作为论文正式实验结论。

### 8.2 正式实验运行方式

正式实验使用 `v2_full` 数据集、DeepSeek Flash、`Top-k=3` 和 `RISK_THRESHOLD=0.50`。确认 `.env` 中已经填写 API Key，并设置 `USE_MOCK_LLM=false` 后执行：

```bash
uv run python -m rag_security_experiment.cli run --all --dataset v2_full --offline-embeddings --output results/runs/v2_full_flash_t050_k3_all_groups.csv
uv run python -m rag_security_experiment.cli summarize --input results/runs/v2_full_flash_t050_k3_all_groups.csv --output results/summary/v2_full_flash_t050_k3_all_groups_summary.csv --extended --prefix v2_full_flash_t050_k3_all_groups
```

也可以只运行某几个实验组，例如只运行 G1 和 G4：

```bash
uv run python -m rag_security_experiment.cli run --groups G1,G4 --dataset v2_full --offline-embeddings --output results/runs/v2_full_flash_t050_k3_g1_g4.csv
```

## 9. 输出文件说明

运行实验后，主要输出包括：

| 路径                                                   | 说明                                         |
| ---------------------------------------------------- | ------------------------------------------ |
| `results/runs/*.csv`                                 | 每个问题、每个实验组的运行明细，包括检索结果、风险分数、过滤结果、模型回答和评价结果 |
| `results/summary/*_summary.csv`                      | G0-G4 分组汇总指标                               |
| `results/summary/*_summary_by_attack_type.csv`       | 按攻击类型统计的汇总结果                               |
| `results/summary/*_summary_by_group_attack_type.csv` | 按实验组和攻击类型交叉统计的结果                           |
| `results/summary/*_filter_effectiveness.csv`         | 检索过滤器过滤片段数量、误过滤和恶意片段过滤情况                   |
| `results/summary/*_manual_review_cases.csv`          | 自动评价标记为需要人工复核的样本                           |
| `outputs/tables/`                                    | 论文中使用的 Markdown 表格                         |
| `outputs/figures/`                                   | 论文中使用的结果图像                                 |

## 10. 正式实验结果概览

正式实验结果文件为：

```text
results/runs/v2_full_flash_t050_k3_all_groups.csv
results/summary/v2_full_flash_t050_k3_all_groups_summary.csv
```

核心结论概括如下：

| 组别  | 防御方式       | MR@k    | CIR     | ASR    | normal_accuracy |
| --- | ---------- | -------:| -------:| ------:| ---------------:|
| G0  | 干净基线       | 0.00%   | 0.00%   | 1.92%  | 93.33%          |
| G1  | 无防御        | 100.00% | 100.00% | 51.92% | 76.67%          |
| G2  | 仅安全 Prompt | 100.00% | 100.00% | 3.85%  | 90.00%          |
| G3  | 仅检索过滤      | 100.00% | 78.85%  | 50.00% | 86.67%          |
| G4  | 组合防御       | 100.00% | 78.85%  | 3.85%  | 86.67%          |

需要注意：G0 组不包含污染文档，ASR 自动统计值 1.92% 主要来自自动评价器边界误判，不应解释为真实攻击成功。论文中结合人工复核对该问题进行了说明。

## 11. 安全与提交说明

- 本项目仅用于课程设计、教学演示和防御性安全研究。
- 攻击样本均为虚构、安全化文本，不包含真实漏洞利用代码、真实密钥或真实隐私数据。
- 不要提交 `.env`、真实 API Key 或个人敏感信息。
- 不建议提交 `.venv/` 虚拟环境目录，老师可通过 `uv sync` 重新安装依赖。
- 若无法联网或无法调用 API，可使用 `USE_MOCK_LLM=true` 和 `--offline-embeddings` 验证代码流程。
