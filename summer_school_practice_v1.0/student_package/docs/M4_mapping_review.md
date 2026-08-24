# M4 AI 辅助映射核验说明

- 候选来源：学校预生成候选（`reference/pre_generated_mapping_candidate.csv`，共 8 条）。
- 使用的提示或候选文件：`reference/pre_generated_mapping_candidate.csv`；权威依据为 `schema/source_field_definitions.md`、`schema/unified_model.json`、`schema/teaching_message_spec.md` 及两个字段字典。
- 发现的字段、单位、层次、有效性或来源问题：
  1. **纬度/经度层次颠倒**：候选把 `latitude_code` 映射为 `position.lon`、把 `longitude_code` 映射为 `position.lat`。已修正为纬度→`position.lat`、经度→`position.lon`。
  2. **高度遗漏物理偏置**：候选写“code 乘 1 米”，遗漏 `-1000 m` 偏置。已修正为 `altitude = altitude_code - 1000`。
  3. **status_flags.bit2 语义错误**：候选把 `status_flags.bit2` 当作 `quality.time_valid`，但 bit2 的真实语义是时间来源（`position_time` / `last_contact_fallback`）。已修正为 `quality.time_source`，`time_valid` 由“时间戳为正整数 + 帧接收结果”决定，时间回退不等于时间无效。
  4. **呼号遗漏有效性位**：候选“去除补 0 后直接映射”未检查 `validity_flags.bit6`。已补充：bit6=0 时置 null。
  5. **候选不完整**：候选仅 8 条，缺失高度类型、速度、航向、垂直速度、地面状态、位置/时间有效性等映射。已依据权威 Schema 补齐为双格式（OpenSky + TeachingLink）共 30 条正式映射。
- 人工修订依据：字段字典的“source/meaning”列、`source_field_definitions.md` 的双格式规则表、`teaching_message_spec.md` 的定点编码与标志位定义。
- 正常样例验证结果：`000001`（全部字段有效、真实零值）映射后 `position_valid=true`、`alt=20`、`speed=20`、`heading=90`，均与解码结果一致。
- 真实零值与缺失值样例验证结果：`000001` 的高度/速度/航向/垂直速度为真实 0 值，编码为有效（`validity_flags=127`）且解码为 0；`780def` 的纬度/经度/速度缺失（`validity_flags=52`），映射后为 `null` 且 `position_valid=false`，未把缺失值误当 0。
- 不应由大模型自行决定的内容：字节序、位宽、比例因子、偏置、保留位、有效性位语义、量程边界等协议约定，以及“真实零值与缺失值”的区分，均以学校 Schema 为准，不由大模型自行推定。
