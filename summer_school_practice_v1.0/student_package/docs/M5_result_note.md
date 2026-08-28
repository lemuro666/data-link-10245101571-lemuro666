# M5 异常结果说明

- 批次时间：1710000120
- 四类必做规则是否均运行：已运行 R1 位置缺失、R2 数据延迟、R3 target_id+timestamp 联合键重复、R4 航向越界。
- 告警总数及按类型统计：共 4 条；POSITION_MISSING 1 条，DATA_DELAYED 1 条，DUPLICATE_RECORD 1 条，HEADING_OUT_OF_RANGE 1 条。
- HIGH/MEDIUM 数量：HIGH 1 条，MEDIUM 3 条。
- 正常记录是否被误报：未误报；`780abc` 和第一条 `780aaa` 输出为 NORMAL。
- heading=360 与 heading 为空的处理：`heading=360` 按 `[0, 360)` 规则触发 HEADING_OUT_OF_RANGE；heading 为空表示该字段缺失，不触发航向越界。
- 字段缺失、帧验证失败、来源真实性三者的区别：字段缺失由空值或有效位表达，进入 POSITION_MISSING 等质量规则；帧验证失败只表示 TeachingLink 格式和校验未通过，可选记录为 FRAME_VALIDATION_ERROR；来源真实性不由本实验判断，`message_valid` 只代表课程定义的接收判据。

## 结果核查

`alert_log.csv` 保留逐条告警，`quality_situation.csv` 汇总每条记录的质量状态。状态合成遵循 HIGH 优先于 MEDIUM：存在 HIGH 时 `display_status=ERROR`，无 HIGH 但存在 MEDIUM 时为 `WARNING`，无告警时为 `NORMAL`。
