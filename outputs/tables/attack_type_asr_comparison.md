# 表：G1 与 G4 不同攻击类型 ASR 对比

> 用途：论文第 5.5 节，用于展示组合防御对不同攻击类型的影响。复制到 Word 后建议改为三线表。

| 攻击类型 | 样本数 | G1 成功数 | G1 ASR | G4 成功数 | G4 ASR | ASR 变化 |
|---|---:|---:|---:|---:|---:|---:|
| context_leakage | 10 | 5 | 50.00% | 0 | 0.00% | -50.00% |
| false_information | 10 | 5 | 50.00% | 0 | 0.00% | -50.00% |
| instruction_override | 5 | 3 | 60.00% | 1 | 20.00% | -40.00% |
| obfuscation | 7 | 5 | 71.43% | 1 | 14.29% | -57.14% |
| refusal_disruption | 10 | 5 | 50.00% | 0 | 0.00% | -50.00% |
| role_impersonation | 10 | 4 | 40.00% | 0 | 0.00% | -40.00% |

注：G4 对大部分攻击类型均将 ASR 降至 0，但对 instruction_override 和 obfuscation 仍存在少量残留风险，可在局限性分析中讨论。
