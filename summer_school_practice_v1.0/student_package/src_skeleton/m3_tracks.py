from __future__ import annotations

import sqlite3
from typing import Any

from m2_protocol import decode_position_message


def decode_message_stream(data: bytes, frame_size: int = 41) -> list[dict[str, Any]]:
    """按固定帧长批量解码；记录并忽略不完整尾帧。

    返回完整帧的解码记录；不完整尾帧不进入记录列表（调用方可通过帧数
    data 长度 / frame_size 的余数得知，尾帧已在此打印记录）。
    """
    records: list[dict[str, Any]] = []
    full_frames = len(data) // frame_size
    remainder = len(data) % frame_size
    for index in range(full_frames):
        frame = data[index * frame_size:(index + 1) * frame_size]
        records.append(decode_position_message(frame))
    if remainder:
        print(f"[M3] 忽略不完整尾帧：{remainder} 字节（总 {len(data)} 字节）")
    return records


def save_records_to_sqlite(records: list[dict[str, Any]], db_path: str) -> None:
    """选做：保存接收记录，None 必须写为 NULL。

    表结构见 schema/optional_db_schema.sql。
    """
    connection = sqlite3.connect(db_path)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS state_record (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id TEXT,
                callsign TEXT NULL,
                timestamp INTEGER,
                timestamp_source TEXT,
                message_seq INTEGER,
                lat REAL NULL,
                lon REAL NULL,
                altitude REAL NULL,
                alt_type TEXT NULL,
                speed REAL NULL,
                heading REAL NULL,
                vertical_rate REAL NULL,
                on_ground INTEGER,
                status_flags INTEGER,
                validity_flags INTEGER,
                message_valid INTEGER,
                source TEXT
            )
            """
        )
        for record in records:
            connection.execute(
                """
                INSERT INTO state_record (
                    target_id, callsign, timestamp, timestamp_source, message_seq,
                    lat, lon, altitude, alt_type, speed, heading, vertical_rate,
                    on_ground, status_flags, validity_flags, message_valid, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.get("target_id"),
                    record.get("callsign"),
                    record.get("timestamp"),
                    record.get("time_source"),
                    record.get("message_seq"),
                    record.get("lat"),
                    record.get("lon"),
                    record.get("altitude"),
                    record.get("alt_type"),
                    record.get("speed"),
                    record.get("heading"),
                    record.get("vertical_rate"),
                    int(bool(record.get("on_ground"))),
                    record.get("status_flags"),
                    record.get("validity_flags"),
                    int(bool(record.get("message_valid"))),
                    record.get("source"),
                ),
            )
        connection.commit()
    finally:
        connection.close()


def _acceptable(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [record for record in records if record.get("message_valid")]


def build_tracks(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """仅使用可接受记录，按 target_id 分组并按 timestamp 排序，生成从 1 开始的 track_sequence_no。"""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in _acceptable(records):
        grouped.setdefault(record["target_id"], []).append(record)

    rows: list[dict[str, Any]] = []
    for target_id in sorted(grouped):
        ordered = sorted(grouped[target_id], key=lambda r: (r.get("timestamp") or 0, r.get("message_seq") or 0))
        for sequence, record in enumerate(ordered, start=1):
            rows.append(
                {
                    "target_id": target_id,
                    "timestamp": record.get("timestamp"),
                    "message_seq": record.get("message_seq"),
                    "track_sequence_no": sequence,
                    "lat": record.get("lat"),
                    "lon": record.get("lon"),
                    "altitude": record.get("altitude"),
                    "speed": record.get("speed"),
                    "heading": record.get("heading"),
                }
            )
    return rows


def build_current_situation(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """每个目标保留时间最新的可接受记录；可选字段缺失仍可入选。"""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in _acceptable(records):
        grouped.setdefault(record["target_id"], []).append(record)

    rows: list[dict[str, Any]] = []
    for target_id in sorted(grouped):
        ordered = sorted(grouped[target_id], key=lambda r: (r.get("timestamp") or 0, r.get("message_seq") or 0))
        latest = ordered[-1]
        rows.append(
            {
                "target_id": target_id,
                "callsign": latest.get("callsign"),
                "latest_time": latest.get("timestamp"),
                "lat": latest.get("lat"),
                "lon": latest.get("lon"),
                "altitude": latest.get("altitude"),
                "speed": latest.get("speed"),
                "heading": latest.get("heading"),
                "vertical_rate": latest.get("vertical_rate"),
                "on_ground": latest.get("on_ground"),
                "track_length": len(ordered),
                "alt_type": latest.get("alt_type"),
                "time_source": latest.get("time_source"),
                "message_valid": latest.get("message_valid"),
            }
        )
    return rows
