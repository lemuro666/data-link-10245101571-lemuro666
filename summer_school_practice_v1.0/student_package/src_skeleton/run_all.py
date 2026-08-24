from __future__ import annotations

import csv
import json
from pathlib import Path

from m2_protocol import (
    decode_position_message,
    encode_position_message,
    parse_state_vector,
)
from m3_tracks import (
    build_current_situation,
    build_tracks as build_track_table,
    decode_message_stream,
)
from m4_mapping import map_to_unified, verify_candidate_mapping
from m5_quality import build_quality_situation, check_duplicates, check_record


STUDENT_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = STUDENT_PACKAGE_ROOT / "output"
DATA_ROOT = STUDENT_PACKAGE_ROOT / "data"
SCHEMA_ROOT = STUDENT_PACKAGE_ROOT / "schema"
REFERENCE_ROOT = STUDENT_PACKAGE_ROOT / "reference"

# 解码记录的完整字段顺序（与 templates/decoded_partner_states.csv 一致）。
DECODED_FIELDS = [
    "target_id", "callsign", "timestamp", "timestamp_source", "time_source", "message_seq",
    "lat", "lon", "altitude", "alt_type", "speed", "heading", "vertical_rate", "on_ground",
    "status_flags", "validity_flags", "latitude_code", "longitude_code", "altitude_code",
    "speed_code", "heading_code", "vertical_rate_code", "lat_valid", "lon_valid",
    "altitude_valid", "speed_valid", "heading_valid", "vertical_rate_valid",
    "callsign_valid", "checksum", "expected_checksum", "message_valid",
    "validation_errors", "source",
]

ROUNDTRIP_FIELDS = [
    ("lat", "latitude_code", 0, 180.0 / ((1 << 22) - 1)),
    ("lon", "longitude_code", 1, 360.0 / ((1 << 22) - 1)),
    ("altitude", "altitude_code", 2, 1.0),
    ("speed", "speed_code", 3, 0.1),
    ("heading", "heading_code", 4, 0.01),
    ("vertical_rate", "vertical_rate_code", 5, 0.01),
]

# 流水线中间状态。
_sender_records: list[dict] = []
_encoded_pairs: list[tuple[dict, bytes]] = []
_validation_entries: list[dict] = []


def _cell(value) -> str:
    return "" if value is None else str(value)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: _cell(row.get(key)) for key in fieldnames})


def _write_ndjson(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _decoded_row(record: dict) -> dict:
    return {
        "target_id": record.get("target_id"),
        "callsign": record.get("callsign"),
        "timestamp": record.get("timestamp"),
        "timestamp_source": record.get("time_source"),
        "time_source": record.get("time_source"),
        "message_seq": record.get("message_seq"),
        "lat": record.get("lat"),
        "lon": record.get("lon"),
        "altitude": record.get("altitude"),
        "alt_type": record.get("alt_type"),
        "speed": record.get("speed"),
        "heading": record.get("heading"),
        "vertical_rate": record.get("vertical_rate"),
        "on_ground": record.get("on_ground"),
        "status_flags": record.get("status_flags"),
        "validity_flags": record.get("validity_flags"),
        "latitude_code": record.get("latitude_code"),
        "longitude_code": record.get("longitude_code"),
        "altitude_code": record.get("altitude_code"),
        "speed_code": record.get("speed_code"),
        "heading_code": record.get("heading_code"),
        "vertical_rate_code": record.get("vertical_rate_code"),
        "lat_valid": record.get("lat_valid"),
        "lon_valid": record.get("lon_valid"),
        "altitude_valid": record.get("altitude_valid"),
        "speed_valid": record.get("speed_valid"),
        "heading_valid": record.get("heading_valid"),
        "vertical_rate_valid": record.get("vertical_rate_valid"),
        "callsign_valid": record.get("callsign_valid"),
        "checksum": record.get("checksum"),
        "expected_checksum": record.get("expected_checksum"),
        "message_valid": record.get("message_valid"),
        "validation_errors": ";".join(record.get("validation_errors") or []),
        "source": record.get("source"),
    }


def prepare_output_directory() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def parse() -> None:
    """M2：解析 OpenSky 状态向量为发送方内部记录。"""
    global _sender_records
    raw = json.loads((DATA_ROOT / "raw_states.json").read_text(encoding="utf-8"))
    _sender_records = []
    for index, vector in enumerate(raw["states"], start=1):
        try:
            record = parse_state_vector(vector)
            record["record_no"] = index
            _sender_records.append(record)
        except ValueError as exc:
            _validation_entries.append(
                {
                    "record_no": index,
                    "target_id": _cell(vector[0]),
                    "stage": "parse",
                    "field": "icao24",
                    "problem_type": "INVALID_TARGET_ID",
                    "value": _cell(vector[0]),
                    "description": str(exc),
                }
            )


def _classify_encode_error(record: dict) -> tuple[str, str, str]:
    if record.get("timestamp") is None:
        return "timestamp", "MISSING_REQUIRED", ""
    heading = record.get("heading")
    if heading is not None and (heading < 0.0 or heading >= 360.0):
        return "heading", "RANGE_ERROR", _cell(heading)
    return "record", "ENCODE_ERROR", ""


def encode() -> None:
    """M2：把发送方内部记录封装为 41 字节 TeachingLink 帧。"""
    global _encoded_pairs
    _encoded_pairs = []
    message_seq = 0
    for record in _sender_records:
        try:
            message_seq += 1
            frame = encode_position_message(record, message_seq)
            _encoded_pairs.append((record, frame))
        except ValueError as exc:
            field, problem_type, value = _classify_encode_error(record)
            _validation_entries.append(
                {
                    "record_no": record["record_no"],
                    "target_id": record["target_id"],
                    "stage": "encode",
                    "field": field,
                    "problem_type": problem_type,
                    "value": value,
                    "description": str(exc),
                }
            )
    (OUTPUT_ROOT / "encoded_messages.bin").write_bytes(b"".join(frame for _, frame in _encoded_pairs))


def decode_validate() -> None:
    """M2：解码自有编码帧，生成解码结果、往返报告与校验日志。"""
    decoded = [decode_position_message(frame) for _, frame in _encoded_pairs]
    _write_csv(OUTPUT_ROOT / "decoded_partner_states.csv", DECODED_FIELDS, [_decoded_row(r) for r in decoded])

    roundtrip_rows: list[dict] = []
    for sender, frame in _encoded_pairs:
        received = decode_position_message(frame)
        for field, code_field, flag_bit, tolerance in ROUNDTRIP_FIELDS:
            source_value = sender.get(field)
            decoded_value = received.get(field)
            source_valid = source_value is not None
            decoded_valid = received.get(field + "_valid")
            if source_value is None and decoded_value is None:
                error_cell = ""
                passed = True
            elif source_value is None or decoded_value is None:
                error_cell = "N/A"
                passed = False
            else:
                error = abs(source_value - decoded_value)
                error_cell = f"{error:.6g}/{tolerance:.6g}"
                passed = error <= tolerance + 1e-9
            roundtrip_rows.append(
                {
                    "field": field,
                    "source_value": source_value,
                    "source_valid": source_valid,
                    "protocol_code": received.get(code_field),
                    "flag_bit": flag_bit,
                    "decoded_value": decoded_value,
                    "decoded_valid": decoded_valid,
                    "absolute_error/tolerance": error_cell,
                    "passed": passed,
                }
            )
    _write_csv(
        OUTPUT_ROOT / "roundtrip_report.csv",
        ["field", "source_value", "source_valid", "protocol_code", "flag_bit",
         "decoded_value", "decoded_valid", "absolute_error/tolerance", "passed"],
        roundtrip_rows,
    )

    _write_csv(
        OUTPUT_ROOT / "validation_log.csv",
        ["record_no", "target_id", "stage", "field", "problem_type", "value", "description"],
        _validation_entries,
    )


def build_tracks() -> None:
    """M3：批量解码多时刻消息，生成航迹与当前态势。"""
    data = (DATA_ROOT / "partner_messages_multitime.bin").read_bytes()
    records = decode_message_stream(data)
    _write_csv(OUTPUT_ROOT / "decoded_multitime.csv", DECODED_FIELDS, [_decoded_row(r) for r in records])

    _write_csv(
        OUTPUT_ROOT / "track_table.csv",
        ["target_id", "timestamp", "message_seq", "track_sequence_no",
         "lat", "lon", "altitude", "speed", "heading"],
        build_track_table(records),
    )
    _write_csv(
        OUTPUT_ROOT / "current_situation.csv",
        ["target_id", "callsign", "latest_time", "lat", "lon", "altitude", "speed",
         "heading", "vertical_rate", "on_ground", "track_length", "alt_type",
         "time_source", "message_valid"],
        build_current_situation(records),
    )


def map_unified() -> None:
    """M4：生成候选映射、人工核验映射与统一态势消息。"""
    candidate_path = REFERENCE_ROOT / "pre_generated_mapping_candidate.csv"
    with candidate_path.open("r", encoding="utf-8-sig", newline="") as handle:
        candidate_reader = csv.DictReader(handle)
        candidate_rows = list(candidate_reader)
        candidate_fields = candidate_reader.fieldnames or []

    # 大模型不可用，采用学校预生成候选，并逐条人工核验。
    if candidate_rows:
        _write_csv(OUTPUT_ROOT / "llm_mapping_candidate.csv", list(candidate_fields), candidate_rows)

    verified = verify_candidate_mapping(candidate_rows)
    _write_csv(
        OUTPUT_ROOT / "verified_mapping_table.csv",
        ["source_format", "input_field", "unified_field", "mapping_rule",
         "unit_conversion", "null_strategy", "evidence", "verified"],
        verified,
    )

    with (DATA_ROOT / "m4" / "partner_current_situation.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        partner_rows = list(csv.DictReader(handle))
    unified_rows = [map_to_unified(row, "TeachingLink") for row in partner_rows]
    _write_ndjson(OUTPUT_ROOT / "unified_situation.ndjson", unified_rows)


def check_quality() -> None:
    """M5：一致性检查，生成告警日志与质量态势。"""
    with (DATA_ROOT / "m5" / "anomaly_cases.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        records = list(csv.DictReader(handle))

    alerts: list[dict] = []
    for record in records:
        alerts.extend(check_record(record))
    alerts.extend(check_duplicates(records))

    _write_csv(
        OUTPUT_ROOT / "alert_log.csv",
        ["alert_time", "target_id", "alert_type", "severity", "field", "description"],
        alerts,
    )
    _write_csv(
        OUTPUT_ROOT / "quality_situation.csv",
        ["target_id", "timestamp", "position_valid", "delayed", "duplicate_detected",
         "heading_valid", "message_valid", "anomaly_level", "display_status"],
        build_quality_situation(records, alerts),
    )


def export_results() -> None:
    """M6：汇总关键成果并输出实验摘要。"""
    encoded_bytes = (OUTPUT_ROOT / "encoded_messages.bin").stat().st_size
    multitime_bytes = (DATA_ROOT / "partner_messages_multitime.bin").stat().st_size
    print("=" * 60)
    print("M2-M6 端到端流水线执行完成")
    print(f"  发送方解析记录：{len(_sender_records)} 条")
    print(f"  成功编码帧：{len(_encoded_pairs)} 帧（{encoded_bytes} 字节）")
    print(f"  编码被拒记录：{len(_validation_entries)} 条（见 validation_log.csv）")
    print(f"  多时刻批量解码：{multitime_bytes // 41} 帧")
    print("  成果文件已写入 student_package/output/")
    print("=" * 60)


def run_pipeline() -> None:
    prepare_output_directory()
    parse()
    encode()
    decode_validate()
    build_tracks()
    map_unified()
    check_quality()
    export_results()


def main() -> int:
    try:
        run_pipeline()
    except NotImplementedError as exc:
        print(exc)
        print("当前文件是学生骨架，模块实现完成后再进行端到端运行。")
        return 2
    except Exception as exc:  # noqa: BLE001 - 端到端入口保留兜底日志。
        print(f"流水线执行失败：{exc}")
        raise
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
