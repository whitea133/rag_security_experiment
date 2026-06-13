# 表：V2-full 数据集规模

> 用途：论文第 5.2 节“实验数据集与对照组设置”。复制到 Word 后建议改为三线表。

| 数据类型 | 数量 | 说明 |
|---|---:|---|
| 正常文档 clean docs | 40 | 网络安全知识库中的正常资料片段 |
| 污染文档 attack docs | 52 | 含间接提示注入内容的污染资料片段 |
| 正常问题 normal questions | 30 | 用于测试正常问答能力和误报影响 |
| 攻击触发问题 attack questions | 52 | 用于测试污染文档进入上下文后的攻击效果 |
| 注入模式 patterns | 18 | 用于风险检测的注入模式库 |
| 攻击类型 attack types | 6 | 覆盖指令覆盖、角色伪装、上下文泄露、拒答破坏、错误信息注入和混淆隐藏 |

攻击类型包括：

| attack_type | 中文说明 |
|---|---|
| instruction_override | 指令覆盖型 |
| role_impersonation | 角色伪装型 |
| context_leakage | 上下文泄露诱导型 |
| refusal_disruption | 拒答破坏型 |
| false_information | 错误信息注入型 |
| obfuscation | 混淆隐藏型 |

注：V2-full 是课程设计场景化自构造数据集，攻击样本均为虚构和安全化表达，不包含真实密钥、真实隐私或可直接滥用载荷。
