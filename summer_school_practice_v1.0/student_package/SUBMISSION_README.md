# M6 综合运行说明

## 基本信息

- 姓名：lemuro666
- 学号：10245101571
- GitHub用户名：lemuro666
- Python版本：3.13.3
- 是否使用SQLite：否（SQLite 为选做路径，必做结果全部使用 CSV/NDJSON）
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
5. `map_unified()`：调用 `m4_mapping.verify_candidate_mapping / map_to_unified`。
6. `check_quality()`：调用 `m5_quality.check_record / check_duplicates / build_quality_situation`。
7. `export_results()`：汇总实验摘要。

## 输入文件

- M2：`data/raw_states.json`、`schema/opensky_field_dictionary.csv`、`schema/partner_field_dictionary.csv`、`schema/teaching_message_spec.md`
- M3：`data/partner_messages_multitime.bin`（9 帧、369 字节）
- M4：`data/m4/partner_current_situation.csv`、`schema/unified_model.json`、`reference/pre_generated_mapping_candidate.csv`
- M5：`data/m5/anomaly_cases.csv`、`data/m5/anomaly_rules.csv`

## 输出文件

- `encoded_messages.bin`：M2 编码的 3 帧（123 字节）
- `decoded_partner_states.csv`：M2 解码结果
- `validation_log.csv`：M2 编码被拒记录
- `roundtrip_report.csv`：M2 发送方/接收方往返误差报告
- `decoded_multitime.csv`：M3 批量解码结果（9 帧）
- `track_table.csv`：M3 航迹表
- `current_situation.csv`：M3 当前态势
- `llm_mapping_candidate.csv`：M4 候选映射
- `verified_mapping_table.csv`：M4 人工核验后的正式映射
- `unified_situation.ndjson`：M4 统一态势消息
- `alert_log.csv`：M5 告警日志
- `quality_situation.csv`：M5 质量态势

## 实验结果

- M2：解析 5 条 OpenSky 状态向量，成功编码 3 帧（123 字节）；2 条被拒（`780bad` 无时间戳、`780bee` 航向 360 越界），记录于 `validation_log.csv`；3 帧全部解码成功，往返误差均不超过一个量化单位。
- M3：批量解码 9 帧（3 个目标 × 3 个时刻），生成航迹 9 条、当前态势 3 条，每目标 `track_length=3`。
- M4：形成 30 条正式映射（OpenSky 15 条 + TeachingLink 15 条），生成 3 条统一态势消息。
- M5：检查 6 条记录，发现 4 条告警：位置缺失 1（HIGH）、数据延迟 1（MEDIUM）、联合键重复 1（MEDIUM）、航向越界 1（MEDIUM）。

## 已知限制

- 未使用 SQLite（选做路径），必做结果均使用 CSV/NDJSON 并已确认可重新读取。
- M4 候选使用学校预生成候选并人工核验，未调用外部大模型。
- TeachingLink 仅为教学自定义协议，`message_valid` 不代表来源真实性或安全完整性。

## 最终提交信息

- 仓库链接：https://github.com/lemuro666/data-link-10245101571-lemuro666.git
- 最终commit ID：（提交后登记）
- 最后检查日期：（提交后登记）
