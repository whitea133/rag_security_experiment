# 表：检索过滤器效果

> 用途：论文第 5.5 节，用于说明风险检测与检索过滤模块的作用。复制到 Word 后建议改为三线表。

| 组别 | filtered_run_rate | avg_filtered_chunks | filtered_chunks | filtered_malicious_chunks | filtered_clean_chunks | attack_filtered_run_rate | normal_filtered_run_rate |
|---|---:|---:|---:|---:|---:|---:|---:|
| G3 | 81.71% | 1.49 | 122 | 121 | 1 | 80.77% | 83.33% |
| G4 | 81.71% | 1.49 | 122 | 121 | 1 | 80.77% | 83.33% |

补充指标：

| 指标 | 数值 | 说明 |
|---|---:|---|
| 过滤结果中恶意 chunk 占比 | 99.18% | 121 / 122 |
| 正常 chunk 误过滤数 | 1 | 当前数据集下误过滤较少 |
| 攻击问题中被过滤的恶意 chunk 数 | 83 | 攻击样本中被过滤的恶意 chunk 总量 |
| 正常问题中被误过滤的正常 chunk 数 | 1 | 正常样本中被过滤的 clean chunk 数量 |

注：G3 和 G4 使用相同检索过滤模块，因此过滤统计一致。该表说明过滤器能较有针对性地过滤恶意 chunk，但结合 G3 的 ASR=50.00% 可知，单独过滤不足以稳定防御残留恶意内容，还需要 Prompt 层面的指令/数据隔离。
