from __future__ import annotations

import math
import struct
from typing import Any

# TeachingLink 教学帧固定约定（见 schema/teaching_message_spec.md）。
FRAME_SIZE = 41
MAGIC = 0x4453
VERSION = 1
MESSAGE_TYPE = 1
MESSAGE_LENGTH = 41

# 22 位经纬度容器范围。
LAT_LON_CODE_MAX = (1 << 22) - 1

# 各物理量的量程（编码前必须显式检查，禁止静默截断）。
LAT_RANGE = (-90.0, 90.0)
LON_RANGE = (-180.0, 180.0)
ALTITUDE_RANGE = (-1000.0, 64535.0)          # altitude_code = Q(alt + 1000)，uint16
SPEED_RANGE = (0.0, 6553.5)                  # speed_code = Q(speed / 0.1)，uint16
HEADING_RANGE = (0.0, 360.0)                 # heading_code = Q(heading / 0.01)，uint16
VERTICAL_RATE_RANGE = (-327.68, 327.67)      # vertical_rate_code = Q((vr + 327.68) / 0.01)


def quantize(value: float) -> int:
    """统一量化函数 Q(y) = floor(y + 0.5)，禁止依赖语言默认 round。"""
    return math.floor(value + 0.5)


def _clean_optional_float(value: Any) -> float | None:
    """把 None、空字符串或空值统一为 None，其余转为 float。"""
    if value is None or value == "":
        return None
    return float(value)


def _clean_optional_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def parse_state_vector(vector: list[Any]) -> dict[str, Any]:
    """将OpenSky状态向量转换为发送方内部结构化记录。

    索引约定见 schema/opensky_field_dictionary.csv。
    """
    # 必需字段：六位十六进制目标标识。
    icao24 = str(vector[0]).strip().lower()
    if len(icao24) != 6:
        raise ValueError(f"icao24 必须为六位十六进制标识：{vector[0]!r}")
    try:
        int(icao24, 16)
    except ValueError as exc:
        raise ValueError(f"icao24 不是合法十六进制：{icao24!r}") from exc

    callsign = vector[1]
    if callsign is None:
        callsign = None
    else:
        callsign = str(callsign).strip()
        if callsign == "":
            callsign = None

    time_position = _clean_optional_int(vector[3])
    last_contact = _clean_optional_int(vector[4])

    # 时间：优先位置时间，必要时回退最近联系时间。
    if time_position is not None:
        timestamp = time_position
        time_source = "position_time"
    elif last_contact is not None:
        timestamp = last_contact
        time_source = "last_contact_fallback"
    else:
        timestamp = None
        time_source = None

    latitude = _clean_optional_float(vector[6])
    longitude = _clean_optional_float(vector[5])
    baro_altitude = _clean_optional_float(vector[7])
    geo_altitude = _clean_optional_float(vector[13])
    velocity = _clean_optional_float(vector[9])
    true_track = _clean_optional_float(vector[10])
    vertical_rate = _clean_optional_float(vector[11])

    # 高度：气压高度优先，为空时回退几何高度。
    if baro_altitude is not None:
        altitude = baro_altitude
        alt_type = "barometric"
    elif geo_altitude is not None:
        altitude = geo_altitude
        alt_type = "geometric"
    else:
        altitude = None
        alt_type = "unknown"

    on_ground = bool(vector[8])

    return {
        "target_id": icao24,
        "callsign": callsign,
        "timestamp": timestamp,
        "time_source": time_source,
        "lat": latitude,
        "lon": longitude,
        "altitude": altitude,
        "alt_type": alt_type,
        "speed": velocity,
        "heading": true_track,
        "vertical_rate": vertical_rate,
        "on_ground": on_ground,
        "source": "OpenSky",
    }


def calculate_checksum(data_without_checksum: bytes) -> int:
    """计算前39字节无符号字节值之和模65536。"""
    return sum(data_without_checksum) % 65536


def _encode_lat_lon_22(value: float | None, low: float, high: float, scale: float) -> bytes:
    """把经纬度编码为 3 字节 22 位容器（最高 2 位保留为 0）。"""
    if value is None:
        return b"\x00\x00\x00"
    if not (low <= value <= high):
        raise ValueError(f"经纬度量程越界：{value} 不在 [{low}, {high}]")
    code = quantize((value - low) / scale * LAT_LON_CODE_MAX)
    if not (0 <= code <= LAT_LON_CODE_MAX):
        raise ValueError(f"经纬度编码越界：{value} -> {code}")
    return code.to_bytes(3, "big")


def _encode_uint16(
    value: float | None,
    low: float,
    high: float,
    scale: float,
    bias: float = 0.0,
    high_inclusive: bool = True,
) -> int:
    """编码为 uint16：code = Q((value + bias) / scale)。"""
    if value is None:
        return 0
    in_range = (low <= value <= high) if high_inclusive else (low <= value < high)
    if not in_range:
        boundary = "]" if high_inclusive else ")"
        raise ValueError(f"字段量程越界：{value} 不在 [{low}, {high}{boundary}")
    code = quantize((value + bias) / scale)
    if not (0 <= code <= 0xFFFF):
        raise ValueError(f"字段编码越界：{value} -> {code}")
    return code


def encode_position_message(record: dict[str, Any], message_seq: int) -> bytes:
    """按41字节TeachingLink格式封装一条位置状态消息。

    任何量程越界或必需字段缺失都抛出 ValueError，由调用方记录到 validation_log。
    """
    target_id = str(record["target_id"]).strip().lower()
    if len(target_id) != 6:
        raise ValueError(f"target_id 必须为六位十六进制标识：{target_id!r}")
    try:
        target_id_int = int(target_id, 16)
    except ValueError as exc:
        raise ValueError(f"target_id 不是合法十六进制：{target_id!r}") from exc

    timestamp = record.get("timestamp")
    if timestamp is None:
        raise ValueError("timestamp 必需字段缺失，无法封装消息")
    timestamp = int(timestamp)
    if not (0 <= timestamp <= 0xFFFFFFFF):
        raise ValueError(f"timestamp 越界：{timestamp}")

    time_source = record.get("time_source") or "position_time"
    alt_type = record.get("alt_type") or "unknown"
    on_ground = bool(record.get("on_ground", False))

    # 呼号：有效时 1-8 字节，不足补 0，不静默截断。
    callsign = record.get("callsign")
    if callsign is None:
        callsign = None
    else:
        callsign = str(callsign).strip()
        if callsign == "":
            callsign = None
    if callsign is not None:
        raw = callsign.encode("ascii")
        if len(raw) == 0 or len(raw) > 8:
            raise ValueError(f"callsign 长度必须为 1-8 字节：{callsign!r}")
        callsign_bytes = raw + b"\x00" * (8 - len(raw))
    else:
        callsign_bytes = b"\x00" * 8

    lat = record.get("lat")
    lon = record.get("lon")
    altitude = record.get("altitude")
    speed = record.get("speed")
    heading = record.get("heading")
    vertical_rate = record.get("vertical_rate")

    lat_code = _encode_lat_lon_22(lat, LAT_RANGE[0], LAT_RANGE[1], LAT_RANGE[1] - LAT_RANGE[0])
    lon_code = _encode_lat_lon_22(lon, LON_RANGE[0], LON_RANGE[1], LON_RANGE[1] - LON_RANGE[0])
    altitude_code = _encode_uint16(altitude, ALTITUDE_RANGE[0], ALTITUDE_RANGE[1], 1.0, 1000.0)
    speed_code = _encode_uint16(speed, SPEED_RANGE[0], SPEED_RANGE[1], 0.1)
    # 航向要求 0 <= heading < 360（上界为开区间）。
    heading_code = _encode_uint16(heading, HEADING_RANGE[0], HEADING_RANGE[1], 0.01, high_inclusive=False)
    vertical_rate_code = _encode_uint16(vertical_rate, VERTICAL_RATE_RANGE[0], VERTICAL_RATE_RANGE[1], 0.01, 327.68)

    # status_flags：bit0=on_ground，bit1=altitude_is_geometric，bit2=timestamp_fallback。
    status_flags = 0
    if on_ground:
        status_flags |= 0x01
    if alt_type == "geometric":
        status_flags |= 0x02
    if time_source == "last_contact_fallback":
        status_flags |= 0x04

    # validity_flags：bit0-6 对应 lat/lon/altitude/speed/heading/vertical_rate/callsign。
    validity_flags = 0
    if lat is not None:
        validity_flags |= 0x01
    if lon is not None:
        validity_flags |= 0x02
    if altitude is not None:
        validity_flags |= 0x04
    if speed is not None:
        validity_flags |= 0x08
    if heading is not None:
        validity_flags |= 0x10
    if vertical_rate is not None:
        validity_flags |= 0x20
    if callsign is not None:
        validity_flags |= 0x40

    buf = bytearray(FRAME_SIZE)
    buf[0:2] = struct.pack(">H", MAGIC)
    buf[2] = VERSION
    buf[3] = MESSAGE_TYPE
    buf[4:6] = struct.pack(">H", MESSAGE_LENGTH)
    buf[6:8] = struct.pack(">H", int(message_seq) % 65536)
    buf[8:12] = struct.pack(">I", timestamp)
    buf[12:15] = target_id_int.to_bytes(3, "big")
    buf[15:23] = callsign_bytes
    buf[23:26] = lat_code
    buf[26:29] = lon_code
    buf[29:31] = struct.pack(">H", altitude_code)
    buf[31:33] = struct.pack(">H", speed_code)
    buf[33:35] = struct.pack(">H", heading_code)
    buf[35:37] = struct.pack(">H", vertical_rate_code)
    buf[37] = status_flags
    buf[38] = validity_flags
    buf[39:41] = struct.pack(">H", calculate_checksum(bytes(buf[0:39])))
    return bytes(buf)


def decode_position_message(data: bytes) -> dict[str, Any]:
    """检查帧接收条件并恢复接收方结构化记录。

    非法帧记录到 validation_errors 并把 message_valid 置为 False，不抛出异常。
    """
    errors: list[str] = []
    error_types: list[str] = []

    if len(data) != FRAME_SIZE:
        return {
            "message_valid": False,
            "validation_errors": [f"帧长度错误：{len(data)} != {FRAME_SIZE}"],
            "validation_error_types": ["LENGTH_ERROR"],
            "target_id": None,
            "callsign": None,
            "timestamp": None,
            "time_source": None,
            "message_seq": None,
            "lat": None, "lon": None, "altitude": None, "alt_type": "unknown",
            "speed": None, "heading": None, "vertical_rate": None,
            "on_ground": False, "status_flags": None, "validity_flags": None,
            "latitude_code": None, "longitude_code": None, "altitude_code": None,
            "speed_code": None, "heading_code": None, "vertical_rate_code": None,
            "lat_valid": False, "lon_valid": False, "altitude_valid": False,
            "speed_valid": False, "heading_valid": False, "vertical_rate_valid": False,
            "callsign_valid": False, "checksum": None, "expected_checksum": None,
            "source": "TeachingLink",
        }

    magic = struct.unpack(">H", data[0:2])[0]
    version = data[2]
    message_type = data[3]
    message_length = struct.unpack(">H", data[4:6])[0]
    message_seq = struct.unpack(">H", data[6:8])[0]
    timestamp = struct.unpack(">I", data[8:12])[0]
    target_id_bytes = data[12:15]
    callsign_bytes = data[15:23]
    lat_code = int.from_bytes(data[23:26], "big")
    lon_code = int.from_bytes(data[26:29], "big")
    altitude_code = struct.unpack(">H", data[29:31])[0]
    speed_code = struct.unpack(">H", data[31:33])[0]
    heading_code = struct.unpack(">H", data[33:35])[0]
    vertical_rate_code = struct.unpack(">H", data[35:37])[0]
    status_flags = data[37]
    validity_flags = data[38]
    checksum = struct.unpack(">H", data[39:41])[0]
    expected_checksum = calculate_checksum(data[0:39])

    # 头字段。
    if magic != MAGIC:
        errors.append(f"magic 错误：{magic:#06x} != {MAGIC:#06x}")
        error_types.append("MAGIC_ERROR")
    if version != VERSION:
        errors.append(f"version 错误：{version} != {VERSION}")
        error_types.append("VERSION_ERROR")
    if message_type != MESSAGE_TYPE:
        errors.append(f"message_type 错误：{message_type} != {MESSAGE_TYPE}")
        error_types.append("MESSAGE_TYPE_ERROR")
    if message_length != MESSAGE_LENGTH:
        errors.append(f"message_length 错误：{message_length} != {MESSAGE_LENGTH}")
        error_types.append("LENGTH_ERROR")
    if checksum != expected_checksum:
        errors.append(f"校验和错误：收到 {checksum:#06x}，期望 {expected_checksum:#06x}")
        error_types.append("CHECKSUM_ERROR")

    # 经纬度容器最高 2 位保留位必须为 0。
    if lat_code >> 22:
        errors.append(f"latitude_code 保留位非零：{lat_code:#08x}")
        error_types.append("RESERVED_BITS_ERROR")
    if lon_code >> 22:
        errors.append(f"longitude_code 保留位非零：{lon_code:#08x}")
        error_types.append("RESERVED_BITS_ERROR")

    # 两个标志字节保留位必须为 0。
    if status_flags & 0xF8:
        errors.append(f"status_flags 保留位非零：{status_flags:#04x}")
        error_types.append("RESERVED_BITS_ERROR")
    if validity_flags & 0x80:
        errors.append(f"validity_flags 保留位非零：{validity_flags:#04x}")
        error_types.append("RESERVED_BITS_ERROR")

    # 必需字段：target_id 必须是合法六位十六进制。
    target_id = target_id_bytes.hex()
    if len(target_id) != 6:
        errors.append(f"target_id 长度错误：{target_id!r}")
    else:
        try:
            int(target_id, 16)
        except ValueError:
            errors.append(f"target_id 不是合法十六进制：{target_id!r}")

    # 逐字段有效性位。
    lat_valid = bool(validity_flags & 0x01)
    lon_valid = bool(validity_flags & 0x02)
    altitude_valid = bool(validity_flags & 0x04)
    speed_valid = bool(validity_flags & 0x08)
    heading_valid = bool(validity_flags & 0x10)
    vertical_rate_valid = bool(validity_flags & 0x20)
    callsign_valid = bool(validity_flags & 0x40)

    # 标志/占位一致性：无效位对应的占位整数必须为 0。
    if not lat_valid and lat_code != 0:
        errors.append(f"latitude 无效但占位非零：{lat_code}")
        error_types.append("FLAG_VALUE_INCONSISTENCY")
    if not lon_valid and lon_code != 0:
        errors.append(f"longitude 无效但占位非零：{lon_code}")
        error_types.append("FLAG_VALUE_INCONSISTENCY")
    if not altitude_valid and altitude_code != 0:
        errors.append(f"altitude 无效但占位非零：{altitude_code}")
        error_types.append("FLAG_VALUE_INCONSISTENCY")
    if not speed_valid and speed_code != 0:
        errors.append(f"speed 无效但占位非零：{speed_code}")
        error_types.append("FLAG_VALUE_INCONSISTENCY")
    if not heading_valid and heading_code != 0:
        errors.append(f"heading 无效但占位非零：{heading_code}")
        error_types.append("FLAG_VALUE_INCONSISTENCY")
    if not vertical_rate_valid and vertical_rate_code != 0:
        errors.append(f"vertical_rate 无效但占位非零：{vertical_rate_code}")
        error_types.append("FLAG_VALUE_INCONSISTENCY")
    if not callsign_valid and callsign_bytes != b"\x00" * 8:
        errors.append("callsign 无效但占位非零")
        error_types.append("FLAG_VALUE_INCONSISTENCY")

    # 恢复物理量。
    lat = lat_code / LAT_LON_CODE_MAX * 180.0 - 90.0 if lat_valid else None
    lon = lon_code / LAT_LON_CODE_MAX * 360.0 - 180.0 if lon_valid else None
    altitude = float(altitude_code) - 1000.0 if altitude_valid else None
    speed = float(speed_code) * 0.1 if speed_valid else None
    heading = float(heading_code) * 0.01 if heading_valid else None
    vertical_rate = float(vertical_rate_code) * 0.01 - 327.68 if vertical_rate_valid else None

    on_ground = bool(status_flags & 0x01)
    if status_flags & 0x02:
        alt_type = "geometric" if altitude_valid else "unknown"
    else:
        alt_type = "barometric" if altitude_valid else "unknown"
    time_source = "last_contact_fallback" if (status_flags & 0x04) else "position_time"

    callsign = callsign_bytes.rstrip(b"\x00").decode("ascii", "replace") if callsign_valid else None
    if callsign == "":
        callsign = None

    return {
        "target_id": target_id,
        "callsign": callsign,
        "timestamp": timestamp,
        "time_source": time_source,
        "message_seq": message_seq,
        "lat": lat,
        "lon": lon,
        "altitude": altitude,
        "alt_type": alt_type,
        "speed": speed,
        "heading": heading,
        "vertical_rate": vertical_rate,
        "on_ground": on_ground,
        "status_flags": status_flags,
        "validity_flags": validity_flags,
        "latitude_code": lat_code,
        "longitude_code": lon_code,
        "altitude_code": altitude_code,
        "speed_code": speed_code,
        "heading_code": heading_code,
        "vertical_rate_code": vertical_rate_code,
        "lat_valid": lat_valid,
        "lon_valid": lon_valid,
        "altitude_valid": altitude_valid,
        "speed_valid": speed_valid,
        "heading_valid": heading_valid,
        "vertical_rate_valid": vertical_rate_valid,
        "callsign_valid": callsign_valid,
        "checksum": checksum,
        "expected_checksum": expected_checksum,
        "message_valid": len(errors) == 0,
        "validation_errors": errors,
        "validation_error_types": error_types,
        "source": "TeachingLink",
    }
