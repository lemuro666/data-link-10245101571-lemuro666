# M1 系统处理流程

## 完整处理流程

```text
OpenSky 离线数据（raw_states.json，状态向量数组）
        │
        ▼
发送方解析与内部状态（按字段字典：索引、必需/可空字段、来源回退、量程检查）
        │
        ▼
发送方内部结构化记录（target_id/callsign/timestamp/位置/运动/状态）
        │
        ▼
TeachingLink 消息封装（41 字节大端帧：定点量化、有效性标志、教学校验和）
        │
        ▼
模拟传输（encoded_messages.bin；partner_messages_sample.bin / multitime.bin）
        │
        ▼
接收方解封与校验（长度、magic、version、message_type、校验和、保留位、标志一致性、必需字段）
        │
        ▼
接收方内部记录（decoded_partner_states.csv / decoded_multitime.csv）
        │
        ▼
CSV / SQLite（选做）持久化
        │
        ▼
航迹关联与当前态势（track_table.csv / current_situation.csv）
        │
        ▼
双格式语义映射 + 人工核验（llm_mapping_candidate.csv -> verified_mapping_table.csv）
        │
        ▼
统一态势消息（unified_situation.ndjson）
        │
        ▼
一致性检查（位置缺失 / 延迟 / 联合键重复 / 航向越界）
        │
        ▼
态势结果与告警（alert_log.csv / quality_situation.csv）
```

## 各步骤输入与输出

| 步骤 | 输入 | 输出 |
|---|---|---|
| 发送方解析 | `raw_states.json`、字段字典 | 发送方内部结构化记录 |
| 消息封装 | 内部结构化记录、41 字节规范 | `encoded_messages.bin` |
| 接收方解封校验 | 二进制消息流 | 接收方内部记录、`validation_log.csv` |
| 存储 | 接收方内部记录 | CSV；SQLite（选做） |
| 航迹/态势 | 多时刻解码记录 | `track_table.csv`、`current_situation.csv` |
| 语义映射 | 字段定义、`unified_model.json`、候选映射 | `verified_mapping_table.csv`、`unified_situation.ndjson` |
| 一致性检查 | 异常样例、异常规则 | `alert_log.csv`、`quality_situation.csv` |

## 自查

- [x] 区分外部原始数据、传输帧和接收方内部记录
- [x] 覆盖发送、传输、接收、存储、航迹、映射和检查
- [x] TeachingLink 仅为教学自定义协议，未描述为真实装备或行业标准协议
