# M6 综合运行说明

## 基本信息

- 姓名：lemuro666
- 学号：10245101571
- GitHub用户名：lemuro666
- Python版本：3.13.3
- 是否使用SQLite：是（M3 OpenSky 真实数据验证写入 `output/received_states.db`；必做结果仍保留 CSV/NDJSON）
- M4候选来源：学校预生成候选（`reference/pre_generated_mapping_candidate.csv`）

## 安装与运行

先按课程包 `environment/README_environment.md` 建立独立 `.venv`（pandas 2.x、matplotlib 3.7+）。在课程包根目录清空 `student_package/output/` 后执行：

```powershell
.\.venv\Scripts\python.exe student_package\src_skeleton\run_all.py
```

## 程序入口

统一入口 `student_package/src_skeleton/run_all.py`，按以下顺序调用各模块：

1. `parse()`：调用 `m2_protocol.parse_state_vector` 解析 `raw_states.json`。
2. `encode()`：调用 `m2_protocol.encode_position_message` 封装 41 字节帧。
3. `decode_validate()`：调用 `m2_protocol.decode_position_message` 解码并生成往返报告与校验日志。
4. `build_tracks()`：调用 `m3_tracks.decode_message_stream / build_tracks / build_current_situation`。
5. `validate_real_opensky()`：读取 `data/opensky_real/source/*.json`，使用本人 M2-M3 代码完成真实数据收发、SQLite 入库和精度报告。
6. `map_unified()`：调用 `m4_mapping.verify_candidate_mapping / map_to_unified`，生成 OpenSky 与 TeachingLink 双来源统一态势。
7. `check_quality()`：调用 `m5_quality.check_record / check_duplicates / build_quality_situation`。
8. `export_results()`：汇总实验摘要。

## 输入文件

- M2：`data/raw_states.json`、`schema/opensky_field_dictionary.csv`、`schema/partner_field_dictionary.csv`、`schema/teaching_message_spec.md`
- M3：`data/partner_messages_multitime.bin`（9 帧、369 字节）
- M3真实验证：`data/opensky_real/source/*.json`
- M4：`output/current_situation.csv`、`data/m4/partner_current_situation.csv`、`schema/unified_model.json`、`reference/pre_generated_mapping_candidate.csv`
- M5：`data/m5/anomaly_cases.csv`、`data/m5/anomaly_rules.csv`

## 输出文件

- `encoded_messages.bin`：M2 编码的 3 帧（123 字节）
- `decoded_partner_states.csv`：M2 解码结果
- `validation_log.csv`：M2 编码被拒记录与接收端坏帧验证记录
- `roundtrip_report.csv`：M2 发送方/接收方往返误差报告
- `decoded_multitime.csv`：M3 批量解码结果（9 帧）
- `track_table.csv`：M3 航迹表
- `current_situation.csv`：M3 当前态势
- `receiver_situation_initial.csv`：OpenSky 真实数据接收前空态势
- `selected_source_states.csv`：OpenSky 真实源状态
- `transmitted_frames.bin`：OpenSky 真实数据模拟发送帧
- `transmission_log.csv`：OpenSky 真实数据逐帧接收日志
- `decoded_states.csv`：OpenSky 真实数据接收端解码结果
- `receiver_situation_final.csv`：OpenSky 真实数据最终当前态势
- `received_states.db`：OpenSky 真实数据 SQLite 接收记录
- `precision_error_report.csv`：OpenSky 真实数据精度误差报告
- `experiment_summary.json`：OpenSky 真实数据验证摘要
- `llm_mapping_candidate.csv`：M4 候选映射
- `verified_mapping_table.csv`：M4 人工核验后的正式映射
- `unified_situation.ndjson`：M4 OpenSky 与 TeachingLink 双来源统一态势消息
- `alert_log.csv`：M5 告警日志
- `quality_situation.csv`：M5 质量态势

## 实验结果

- M2：解析 5 条 OpenSky 状态向量，成功编码 3 帧（123 字节）；2 条源记录被拒（`780bad` 无时间戳、`780bee` 航向 360 越界）；额外构造 7 类坏帧验证长度、头字段、校验和、保留位和有效位/占位一致性，均记录于 `validation_log.csv`；3 帧正常消息全部解码成功，往返误差均不超过一个量化单位。
- M3：批量解码 9 帧（3 个目标 × 3 个时刻），生成航迹 9 条、当前态势 3 条，每目标 `track_length=3`；真实 OpenSky 验证读取 71 条状态向量，发送 71 帧（2911 字节），解码 71 条有效记录，生成 24 个当前目标，SQLite 入库 71 条，426 项精度检查全部通过。
- M4：形成 30 条正式映射（OpenSky 15 条 + TeachingLink 15 条），生成 6 条统一态势消息（OpenSky 3 条 + TeachingLink 3 条）。
- M5：检查 6 条记录，发现 4 条告警：位置缺失 1（HIGH）、数据延迟 1（MEDIUM）、联合键重复 1（MEDIUM）、航向越界 1（MEDIUM）；`display_status` 使用 `ERROR/WARNING/NORMAL`。

## 已知限制

- M4 候选使用学校预生成候选并人工核验，未调用外部大模型。
- TeachingLink 仅为教学自定义协议，`message_valid` 不代表来源真实性或安全完整性。

## 最终提交信息

- 仓库链接：https://github.com/lemuro666/data-link-10245101571-lemuro666.git
- 最终commit ID：（提交后登记）
- 最后检查日期：2026-08-28
