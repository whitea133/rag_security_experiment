# RAG Security Experiment

这是《面向大模型 RAG 的间接提示注入攻击检测与防御系统设计》的 V1 实验项目。

项目目标是构建一个轻量级 embedding-based RAG 原型，用自构造数据验证：污染文档 chunk 被检索进入上下文后，可能诱导大模型产生非预期输出；检索后过滤、Prompt 隔离和组合防御可以降低攻击成功率。

## 技术栈

- Python 3.11+
- uv
- DeepSeek API（OpenAI-compatible）
- sentence-transformers embedding
- 内存向量 Top-k 检索
- JSONL 数据集
- CSV 实验结果

## 运行方式

复制 `.env.example` 为 `.env`，填写 DeepSeek API Key。若只是调通流程，可设置 `USE_MOCK_LLM=true` 使用 Mock 输出。

```bash
uv sync
uv run python -m rag_security_experiment.cli run --all
uv run python -m rag_security_experiment.cli summarize
```

V2 数据集支持通过 `--dataset` 选择版本，保留 `legacy` 兼容旧数据路径：

```bash
USE_MOCK_LLM=true uv run python -m rag_security_experiment.cli run --all --dataset v2 --offline-embeddings --output results/runs/v2_smoke.csv
uv run python -m rag_security_experiment.cli summarize --input results/runs/v2_smoke.csv --output results/summary/v2_smoke_summary.csv --extended --prefix v2_smoke
```

正式实验建议沿用已调好的参数：`TOP_K=3`、`RISK_THRESHOLD=0.50`。

## 数据集版本

- `legacy`：兼容根目录 `data/*.jsonl`，对应 V1 原始流程。
- `v1`：保存 V1 数据副本，避免后续改动覆盖原始实验。
- `v2`：场景化增强数据集，包含更真实的安全知识库片段、污染文档、攻击类型字段、难度和隐蔽度字段。

V2 仍是课程设计用的自构造数据集，不声称为真实攻击数据集。当前环境下可使用 `--offline-embeddings` 的 HashingEmbedder fallback 验证流程；论文中需要说明其语义检索能力弱于真实中文 embedding。

## 实验组

| 组别 | 知识库 | Prompt | 检索过滤 | 用途 |
|---|---|---|---|---|
| G0 | clean docs | 普通 | 否 | 干净 RAG 基线 |
| G1 | clean + attack docs | 普通 | 否 | 无防御攻击基线 |
| G2 | clean + attack docs | 安全 | 否 | Prompt-only 防御 |
| G3 | clean + attack docs | 普通 | 是 | 检索过滤防御 |
| G4 | clean + attack docs | 安全 | 是 | 组合防御 |

## 安全说明

本项目仅用于课程设计和防御性安全实验。攻击样本均为虚构、安全化示例，不包含真实密钥、真实隐私或可直接滥用的攻击载荷。真实 API Key 只能放在本地 `.env` 中，不要提交、截图或写入论文。
