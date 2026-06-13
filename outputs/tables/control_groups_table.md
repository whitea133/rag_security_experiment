# 表：实验对照组设置

> 用途：论文第 5.2 节“实验数据集与对照组设置”。复制到 Word 后建议改为三线表。

| 组别 | 知识库 | Prompt 类型 | 检索过滤 | 实验目的 |
|---|---|---|---|---|
| G0 | clean docs | 普通 Prompt | 否 | 干净知识库基线，验证 RAG 原型正常问答能力 |
| G1 | clean + attack docs | 普通 Prompt | 否 | 无防御攻击基线，验证污染文档对 RAG 输出的影响 |
| G2 | clean + attack docs | 安全 Prompt | 否 | Prompt-only 防御，验证上下文隔离提示的效果 |
| G3 | clean + attack docs | 普通 Prompt | 是 | 检索过滤-only 防御，验证风险检测与过滤模块效果 |
| G4 | clean + attack docs | 安全 Prompt | 是 | 组合防御，验证检索过滤与安全 Prompt 的纵深防御效果 |

注：G1-G4 使用相同污染知识库、相同 Top-k 检索参数和相同攻击问题；G3 与 G4 使用相同检索过滤模块，区别在于 G3 使用普通 Prompt，G4 使用安全 Prompt。
