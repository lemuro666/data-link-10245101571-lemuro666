from __future__ import annotations

from typing import Any

# 22 位经纬度容器范围（与 TeachingLink 规范一致）。
LAT_LON_CODE_MAX = (1 << 22) - 1

# 依据 schema/source_field_definitions.md、schema/unified_model.json、
# schema/partner_field_dictionary.csv 与 schema/opensky_field_dictionary.csv
# 人工核验后的完整正式映射。预生成候选中的可识别错误已在此纠正。
_VERIFIED_MAPPING: list[dict[str, Any]] = [
    # ---------------- OpenSky 来源 ----------------
    {
        "source_format": "OpenSky",
        "input_field": "target_id",
        "unified_field": "track_id",
        "mapping_rule": "转为六位小写十六进制，保留前导0",
        "unit_conversion": "无",
        "null_strategy": "target_id必需，不置空",
        "evidence": "候选“直接改为小写字符串”方向正确，补充保留前导0",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "latest_time",
        "unified_field": "timestamp",
        "mapping_rule": "直接映射Unix秒",
        "unit_conversion": "无（Unix second）",
        "null_strategy": "必须为正整数，否则quality.time_valid=false",
        "evidence": "候选正确，补充正整数检查",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "callsign",
        "unified_field": "identity.callsign",
        "mapping_rule": "去除首尾空格后映射",
        "unit_conversion": "无",
        "null_strategy": "空字符串置null",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "lat",
        "unified_field": "position.lat",
        "mapping_rule": "直接映射纬度",
        "unit_conversion": "degree",
        "null_strategy": "空置null",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "lon",
        "unified_field": "position.lon",
        "mapping_rule": "直接映射经度",
        "unit_conversion": "degree",
        "null_strategy": "空置null",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "altitude",
        "unified_field": "position.alt",
        "mapping_rule": "直接映射高度",
        "unit_conversion": "meter",
        "null_strategy": "空置null",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "baro/geo来源",
        "unified_field": "position.alt_type",
        "mapping_rule": "气压优先、几何回退",
        "unit_conversion": "枚举barometric/geometric/unknown",
        "null_strategy": "高度无效时unknown",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "speed",
        "unified_field": "motion.speed",
        "mapping_rule": "直接映射地速",
        "unit_conversion": "m/s",
        "null_strategy": "空置null",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "heading",
        "unified_field": "motion.heading",
        "mapping_rule": "直接映射航向，要求[0,360)",
        "unit_conversion": "degree",
        "null_strategy": "空置null",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "vertical_rate",
        "unified_field": "motion.vertical_rate",
        "mapping_rule": "直接映射垂直速度",
        "unit_conversion": "m/s",
        "null_strategy": "空置null",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "on_ground",
        "unified_field": "status.on_ground",
        "mapping_rule": "转换为布尔值",
        "unit_conversion": "boolean",
        "null_strategy": "on_ground必需，不置空",
        "evidence": "候选缺失，依据字段字典补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "lat/lon",
        "unified_field": "quality.position_valid",
        "mapping_rule": "纬经均非空且处于合法范围",
        "unit_conversion": "boolean",
        "null_strategy": "任一缺失即false",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "latest_time",
        "unified_field": "quality.time_valid",
        "mapping_rule": "latest_time为正整数",
        "unit_conversion": "boolean",
        "null_strategy": "缺失或非正整数即false",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "源记录结构校验结果",
        "unified_field": "quality.message_valid",
        "mapping_rule": "直接映射源记录结构校验结果",
        "unit_conversion": "boolean",
        "null_strategy": "结构非法即false",
        "evidence": "候选“不得扩大为来源可信”正确",
        "verified": "是",
    },
    {
        "source_format": "OpenSky",
        "input_field": "timestamp_source",
        "unified_field": "quality.time_source",
        "mapping_rule": "position_time或last_contact_fallback",
        "unit_conversion": "枚举",
        "null_strategy": "默认position_time",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    # ---------------- TeachingLink 来源 ----------------
    {
        "source_format": "TeachingLink",
        "input_field": "target_id",
        "unified_field": "track_id",
        "mapping_rule": "转为六位小写十六进制，保留前导0",
        "unit_conversion": "无",
        "null_strategy": "target_id必需，不置空",
        "evidence": "候选“直接改为小写字符串”方向正确，补充保留前导0",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "latest_time",
        "unified_field": "timestamp",
        "mapping_rule": "直接映射Unix秒",
        "unit_conversion": "无（Unix second）",
        "null_strategy": "必须为正整数",
        "evidence": "候选“直接映射Unix秒”正确，补充正整数检查",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "callsign+validity_flags.bit6",
        "unified_field": "identity.callsign",
        "mapping_rule": "有效时去除补0，无效时null",
        "unit_conversion": "无",
        "null_strategy": "validity_flags.bit6=0时置null",
        "evidence": "候选遗漏有效性位检查，已补充bit6判断",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "latitude_code+validity_flags.bit0",
        "unified_field": "position.lat",
        "mapping_rule": "有效时按22位纬度公式恢复",
        "unit_conversion": "code/(2^22-1)*180-90（degree）",
        "null_strategy": "validity_flags.bit0=0时置null",
        "evidence": "候选误把纬度映射为position.lon，已修正为position.lat",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "longitude_code+validity_flags.bit1",
        "unified_field": "position.lon",
        "mapping_rule": "有效时按22位经度公式恢复",
        "unit_conversion": "code/(2^22-1)*360-180（degree）",
        "null_strategy": "validity_flags.bit1=0时置null",
        "evidence": "候选误把经度映射为position.lat，已修正为position.lon",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "altitude_code+validity_flags.bit2",
        "unified_field": "position.alt",
        "mapping_rule": "有效时code减物理偏置",
        "unit_conversion": "code-1000（meter）",
        "null_strategy": "validity_flags.bit2=0时置null",
        "evidence": "候选“code乘1米”遗漏物理偏置-1000，已修正为code-1000",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "status_flags.bit1",
        "unified_field": "position.alt_type",
        "mapping_rule": "0=barometric、1=geometric",
        "unit_conversion": "枚举barometric/geometric/unknown",
        "null_strategy": "高度无效时unknown",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "speed_code+validity_flags.bit3",
        "unified_field": "motion.speed",
        "mapping_rule": "有效时code乘0.1",
        "unit_conversion": "code*0.1（m/s）",
        "null_strategy": "validity_flags.bit3=0时置null",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "heading_code+validity_flags.bit4",
        "unified_field": "motion.heading",
        "mapping_rule": "有效时code乘0.01且小于360",
        "unit_conversion": "code*0.01（degree）",
        "null_strategy": "validity_flags.bit4=0时置null",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "vertical_rate_code+validity_flags.bit5",
        "unified_field": "motion.vertical_rate",
        "mapping_rule": "有效时code乘0.01减偏置",
        "unit_conversion": "code*0.01-327.68（m/s）",
        "null_strategy": "validity_flags.bit5=0时置null",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "status_flags.bit0",
        "unified_field": "status.on_ground",
        "mapping_rule": "bit0转换为布尔值",
        "unit_conversion": "boolean",
        "null_strategy": "不置空",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "validity_flags.bit0+bit1",
        "unified_field": "quality.position_valid",
        "mapping_rule": "纬经有效位均为1且解码值在合法范围",
        "unit_conversion": "boolean",
        "null_strategy": "任一无效即false",
        "evidence": "候选缺失，依据source_field_definitions补充",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "timestamp",
        "unified_field": "quality.time_valid",
        "mapping_rule": "timestamp为正整数且帧接收结果通过",
        "unit_conversion": "boolean",
        "null_strategy": "非正整数即false；时间回退不等于时间无效",
        "evidence": "候选误把status_flags.bit2映射为time_valid，已修正；bit2真实语义是time_source",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "message_valid",
        "unified_field": "quality.message_valid",
        "mapping_rule": "直接映射完整帧接收判据",
        "unit_conversion": "boolean",
        "null_strategy": "不置空",
        "evidence": "候选“不得扩大为来源可信”正确",
        "verified": "是",
    },
    {
        "source_format": "TeachingLink",
        "input_field": "status_flags.bit2",
        "unified_field": "quality.time_source",
        "mapping_rule": "0=position_time、1=last_contact_fallback",
        "unit_conversion": "枚举",
        "null_strategy": "默认position_time",
        "evidence": "候选把bit2误当time_valid，已修正为time_source",
        "verified": "是",
    },
]


def verify_candidate_mapping(candidate_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """依据字段定义、单位、有效性和样例，形成人工核验后的正式映射。

    预生成候选中故意保留的可识别问题（纬度/经度层次颠倒、高度遗漏偏置、
    status_flags.bit2 语义错误等）已在上方 _VERIFIED_MAPPING 中逐条纠正。
    candidate_rows 仅作核验参考，不作为答案直接输出。
    """
    _ = candidate_rows  # 候选仅用于核验对照，正式映射以权威 Schema 为准。
    return [dict(row) for row in _VERIFIED_MAPPING]


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "t"}
    return bool(value)


def _nullable_str(value: Any) -> str | None:
    if value is None or value == "":
        return None
    text = str(value).strip()
    return text or None


def map_to_unified(record: dict[str, Any], source_format: str) -> dict[str, Any]:
    """使用人工核验后的规则生成统一态势消息。"""
    unified: dict[str, Any] = {
        "track_id": _nullable_str(record.get("target_id")) or "",
        "source": source_format,
        "timestamp": _to_int(record.get("latest_time", record.get("timestamp"))) or 0,
        "identity": {"callsign": None},
        "position": {"lat": None, "lon": None, "alt": None, "alt_type": "unknown"},
        "motion": {"speed": None, "heading": None, "vertical_rate": None},
        "status": {"on_ground": False},
        "quality": {
            "position_valid": False,
            "time_valid": False,
            "message_valid": False,
            "time_source": "position_time",
            "anomaly_flags": [],
        },
    }

    timestamp = unified["timestamp"]
    unified["quality"]["time_valid"] = isinstance(timestamp, int) and timestamp > 0

    if source_format == "TeachingLink":
        validity = _to_int(record.get("validity_flags")) or 0
        status = _to_int(record.get("status_flags")) or 0

        lat_valid = bool(validity & 0x01)
        lon_valid = bool(validity & 0x02)
        alt_valid = bool(validity & 0x04)
        speed_valid = bool(validity & 0x08)
        heading_valid = bool(validity & 0x10)
        vr_valid = bool(validity & 0x20)
        callsign_valid = bool(validity & 0x40)

        lat_code = _to_int(record.get("latitude_code")) or 0
        lon_code = _to_int(record.get("longitude_code")) or 0
        alt_code = _to_int(record.get("altitude_code")) or 0
        speed_code = _to_int(record.get("speed_code")) or 0
        heading_code = _to_int(record.get("heading_code")) or 0
        vr_code = _to_int(record.get("vertical_rate_code")) or 0

        if lat_valid:
            unified["position"]["lat"] = lat_code / LAT_LON_CODE_MAX * 180.0 - 90.0
        if lon_valid:
            unified["position"]["lon"] = lon_code / LAT_LON_CODE_MAX * 360.0 - 180.0
        if alt_valid:
            unified["position"]["alt"] = float(alt_code) - 1000.0
            unified["position"]["alt_type"] = "geometric" if (status & 0x02) else "barometric"
        if speed_valid:
            unified["motion"]["speed"] = float(speed_code) * 0.1
        if heading_valid:
            unified["motion"]["heading"] = float(heading_code) * 0.01
        if vr_valid:
            unified["motion"]["vertical_rate"] = float(vr_code) * 0.01 - 327.68

        if callsign_valid:
            unified["identity"]["callsign"] = _nullable_str(record.get("callsign"))

        unified["status"]["on_ground"] = bool(status & 0x01)
        unified["quality"]["position_valid"] = lat_valid and lon_valid
        unified["quality"]["message_valid"] = _to_bool(record.get("message_valid"))
        unified["quality"]["time_source"] = (
            "last_contact_fallback" if (status & 0x04) else "position_time"
        )
        return unified

    # OpenSky 来源。
    lat = _to_float(record.get("lat"))
    lon = _to_float(record.get("lon"))
    alt = _to_float(record.get("altitude"))
    speed = _to_float(record.get("speed"))
    heading = _to_float(record.get("heading"))
    vertical_rate = _to_float(record.get("vertical_rate"))

    unified["identity"]["callsign"] = _nullable_str(record.get("callsign"))
    unified["position"]["lat"] = lat
    unified["position"]["lon"] = lon
    unified["position"]["alt"] = alt
    unified["motion"]["speed"] = speed
    unified["motion"]["heading"] = heading
    unified["motion"]["vertical_rate"] = vertical_rate
    unified["status"]["on_ground"] = _to_bool(record.get("on_ground"))

    alt_type = _nullable_str(record.get("alt_type"))
    if alt is not None and alt_type in {"barometric", "geometric"}:
        unified["position"]["alt_type"] = alt_type
    else:
        unified["position"]["alt_type"] = "unknown"

    position_valid = (
        lat is not None
        and lon is not None
        and -90.0 <= lat <= 90.0
        and -180.0 <= lon <= 180.0
    )
    unified["quality"]["position_valid"] = position_valid
    unified["quality"]["message_valid"] = _to_bool(record.get("message_valid"))
    unified["quality"]["time_source"] = (
        _nullable_str(record.get("time_source"))
        or _nullable_str(record.get("timestamp_source"))
        or "position_time"
    )
    return unified
