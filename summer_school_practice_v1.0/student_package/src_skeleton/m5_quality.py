from __future__ import annotations

from typing import Any

BATCH_TIME = 1710000120
DELAY_THRESHOLD_SECONDS = 60


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


def check_record(record: dict[str, Any], batch_time: int = BATCH_TIME) -> list[dict[str, Any]]:
    """检查位置缺失（R1）、时间延迟（R2）和航向越界（R4）。"""
    alerts: list[dict[str, Any]] = []
    target_id = record.get("target_id")
    lat = _to_float(record.get("lat"))
    lon = _to_float(record.get("lon"))
    heading = _to_float(record.get("heading"))
    timestamp = _to_int(record.get("timestamp"))

    # R1：位置缺失。
    if lat is None or lon is None:
        missing = []
        if lat is None:
            missing.append("lat")
        if lon is None:
            missing.append("lon")
        field = "lat/lon" if len(missing) == 2 else missing[0]
        alerts.append(
            {
                "alert_time": batch_time,
                "target_id": target_id,
                "alert_type": "POSITION_MISSING",
                "severity": "HIGH",
                "field": field,
                "description": f"{field} 为空",
            }
        )

    # R2：数据延迟。
    if timestamp is not None and batch_time - timestamp > DELAY_THRESHOLD_SECONDS:
        alerts.append(
            {
                "alert_time": batch_time,
                "target_id": target_id,
                "alert_type": "DATA_DELAYED",
                "severity": "MEDIUM",
                "field": "timestamp",
                "description": f"延迟 {batch_time - timestamp} 秒，超过 {DELAY_THRESHOLD_SECONDS} 秒",
            }
        )

    # R4：航向越界。
    if heading is not None and (heading < 0.0 or heading >= 360.0):
        alerts.append(
            {
                "alert_time": batch_time,
                "target_id": target_id,
                "alert_type": "HEADING_OUT_OF_RANGE",
                "severity": "MEDIUM",
                "field": "heading",
                "description": f"航向 {heading} 超出 [0, 360)",
            }
        )

    return alerts


def check_duplicates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """使用 target_id+timestamp 联合键检查重复（R3）。"""
    alerts: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any]] = set()
    for index, record in enumerate(records, start=1):
        target_id = record.get("target_id")
        timestamp = _to_int(record.get("timestamp"))
        key = (target_id, timestamp)
        if key in seen:
            alerts.append(
                {
                    "alert_time": BATCH_TIME,
                    "target_id": target_id,
                    "alert_type": "DUPLICATE_RECORD",
                    "severity": "MEDIUM",
                    "field": "target_id+timestamp",
                    "description": f"与前面记录重复：target_id={target_id}，timestamp={timestamp}",
                }
            )
        else:
            seen.add(key)
    return alerts


def build_quality_situation(records: list[dict[str, Any]], alerts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """按 HIGH > MEDIUM > NONE 合成质量态势。"""
    # 依据规则直接对每条记录判型，避免重复记录在告警-记录对应上的歧义。
    # alerts 用于汇总说明，判型结果与 check_record/check_duplicates 一致。
    severity_rank = {"HIGH": 3, "MEDIUM": 2, "NONE": 1}

    seen: set[tuple[Any, Any]] = set()
    rows: list[dict[str, Any]] = []
    for record in records:
        target_id = record.get("target_id")
        timestamp = _to_int(record.get("timestamp"))
        lat = _to_float(record.get("lat"))
        lon = _to_float(record.get("lon"))
        heading = _to_float(record.get("heading"))
        message_valid = _to_bool(record.get("message_valid"))

        position_valid = lat is not None and lon is not None
        delayed = timestamp is not None and BATCH_TIME - timestamp > DELAY_THRESHOLD_SECONDS
        key = (target_id, timestamp)
        duplicate_detected = key in seen
        seen.add(key)
        heading_valid = heading is not None and 0.0 <= heading < 360.0

        issues: list[str] = []
        anomaly_level = "NONE"
        if not position_valid:
            anomaly_level = "HIGH"
            issues.append("位置缺失")
        if delayed or duplicate_detected or not heading_valid:
            if severity_rank["MEDIUM"] > severity_rank[anomaly_level]:
                anomaly_level = "MEDIUM"
            if delayed:
                issues.append("数据延迟")
            if duplicate_detected:
                issues.append("重复记录")
            if not heading_valid:
                issues.append("航向越界")

        rows.append(
            {
                "target_id": target_id,
                "timestamp": timestamp,
                "position_valid": position_valid,
                "delayed": delayed,
                "duplicate_detected": duplicate_detected,
                "heading_valid": heading_valid,
                "message_valid": message_valid,
                "anomaly_level": anomaly_level,
                "display_status": "；".join(issues) if issues else "正常",
            }
        )

    _ = alerts
    return rows
