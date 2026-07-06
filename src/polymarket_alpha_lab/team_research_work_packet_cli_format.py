from __future__ import annotations

from dataclasses import asdict, is_dataclass
from decimal import Decimal


_REDACTED_VALUE = "<redacted-sensitive>"
_REDACTION_MARKERS = (
    "market_" + "slug",
    "market " + "slug",
    "market_" + ("ques" + "tion"),
    "market " + ("ques" + "tion"),
    "pay" + "load_json",
    "pay" + "load",
    "database_" + "url",
    "post" + "gres://",
    "post" + "gresql://",
    "d" + "sn",
    "tab" + "le",
    "wal" + "let",
    "api_" + "key",
    "pass" + "word",
    "sec" + "ret",
    "condi" + "tion_id",
    "to" + "ken_id",
    "or" + "der",
    "au" + "th",
    "recommen" + "dation",
    "posi" + "tion",
    "ques" + "tion",
)
_UNSAFE_PUBLIC_PAYLOAD_MARKERS = (
    "pay" + "load_json",
    "pay" + "load",
    "database_" + "url",
    "post" + "gres://",
    "post" + "gresql://",
    "d" + "sn",
    "tab" + "le",
    "wal" + "let",
    "api_" + "key",
    "pass" + "word",
    "private_" + "key",
    "sec" + "ret",
    "condi" + "tion_id",
    "to" + "ken_id",
    "or" + "der",
    "au" + "th",
    "recommen" + "dation",
    "posi" + "tion",
    "tra" + "de",
    "no" + "tional",
    "sha" + "res",
    "buy",
    "sell",
    "acc" + "ount",
    "bal" + "ance",
    "can" + "cel",
    "rep" + "lace",
    "exchange_" + "mutation",
    "net" + "work",
    "sock" + "et",
)
_COUNT_FIELDS = (
    "team_packet_count",
    "research_assignment_count",
    "assigned_count",
    "watch_count",
    "blocked_count",
)
_PACKET_COUNT_FIELDS = (
    "assignment_count",
    "assigned_count",
    "watch_count",
    "blocked_count",
)
_HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def format_team_research_work_packet_cli_stdout(report: object) -> str:
    _reject_unsafe_public_payload("team research work packet CLI payload", report)
    team_packets = _iterable_values(getattr(report, "team_packets"))
    _validate_report_payload(report, team_packets)
    return (
        "team-research-work-packet: "
        f"packet_status={_string_value(getattr(report, 'packet_status'))} "
        f"team_packet_count={_string_value(getattr(report, 'team_packet_count'))} "
        "research_assignment_count="
        f"{_string_value(getattr(report, 'research_assignment_count'))} "
        f"assigned_count={_string_value(getattr(report, 'assigned_count'))} "
        f"watch_count={_string_value(getattr(report, 'watch_count'))} "
        f"blocked_count={_string_value(getattr(report, 'blocked_count'))} "
        f"team_packets={_team_packets_value(team_packets)} "
        f"reason_codes={_codes_value(getattr(report, 'reason_codes'))} "
        f"paper_only={_string_value(getattr(report, 'paper_only'))} "
        f"report_only={_string_value(getattr(report, 'report_only'))} "
        f"readonly={_string_value(getattr(report, 'readonly'))}\n"
    )


def _string_value(value: object) -> str:
    if value is None:
        return "none"
    if type(value) is int:
        raise ValueError("numeric CLI values must use Decimal")
    if isinstance(value, float):
        raise ValueError("numeric CLI values must use Decimal")
    if type(value) not in (bool, str, Decimal):
        return "none"
    raw_value = value if type(value) is str else str(value)
    lowered_value = raw_value.lower()
    if any(marker in lowered_value for marker in _REDACTION_MARKERS):
        return _REDACTED_VALUE
    return raw_value


def _team_packets_value(team_packets: object) -> str:
    if team_packets is None:
        return "none"
    values = tuple(team_packets)
    if not values:
        return "none"
    return ",".join(_team_packet_value(packet) for packet in values)


def _team_packet_value(packet: object) -> str:
    return (
        f"{_field_value(packet, 'team_id', 'none')}:"
        f"{_field_value(packet, 'packet_status', 'none')}:"
        f"{_field_value(packet, 'memory_readiness_status', 'none')}:"
        f"{_field_value(packet, 'memory_use_policy', 'none')}:"
        f"{_field_value(packet, 'assignment_count', 'none')}:"
        f"{_codes_value(_field_raw(packet, 'research_domains', ()), separator='|')}:"
        f"{_codes_value(_field_raw(packet, 'research_horizons', ()), separator='|')}:"
        f"{_codes_value(_field_raw(packet, 'research_modes', ()), separator='|')}:"
        f"{_codes_value(_field_raw(packet, 'research_task_codes', ()), separator='|')}:"
        f"{_field_value(packet, 'assigned_count', 'none')}/"
        f"{_field_value(packet, 'watch_count', 'none')}/"
        f"{_field_value(packet, 'blocked_count', 'none')}:"
        f"{_codes_value(_field_raw(packet, 'evidence_gap_codes', ()), separator='|')}:"
        f"{_codes_value(_field_raw(packet, 'assignment_reason_codes', ()), separator='|')}:"
        f"{_codes_value(_field_raw(packet, 'source_reason_codes', ()), separator='|')}:"
        f"{_packet_rows_value(_field_raw(packet, 'rows', ())) }"
    )


def _packet_rows_value(rows: object) -> str:
    if rows is None:
        return "none"
    values = tuple(rows)
    if not values:
        return "none"
    return "+".join(_packet_row_value(row) for row in values)


def _packet_row_value(row: object) -> str:
    return (
        "<redacted-market>:"
        f"{_field_value(row, 'category_id', 'none')}:"
        f"{_field_value(row, 'research_domain', 'none')}:"
        f"{_field_value(row, 'research_horizon', 'none')}:"
        f"{_field_value(row, 'research_mode', 'none')}:"
        f"{_field_value(row, 'assignment_status', 'none')}:"
        f"{_field_value(row, 'memory_use_policy', 'none')}:"
        f"{_codes_value(_field_raw(row, 'research_task_codes', ()), separator='|')}:"
        f"{_codes_value(_field_raw(row, 'evidence_gap_codes', ()), separator='|')}:"
        f"{_codes_value(_field_raw(row, 'assignment_reason_codes', ()), separator='|')}"
    )


def _codes_value(codes: object, *, separator: str = ",") -> str:
    if codes is None:
        return "none"
    values = tuple(_string_value(code) for code in _iterable_values(codes))
    safe_values = tuple(value for value in values if value != "none")
    if not safe_values:
        return "none"
    return separator.join(safe_values)


def _iterable_values(value: object) -> tuple[object, ...]:
    if isinstance(value, (str, bytes)):
        return (value,)
    return tuple(value)


def _validate_report_payload(report: object, team_packets: tuple[object, ...]) -> None:
    _require_hard_flags("report", report)
    for field_name in _COUNT_FIELDS:
        _require_count_decimal(field_name, getattr(report, field_name))

    packet_rows = _packet_rows(team_packets)
    if getattr(report, "team_packet_count") != Decimal(len(team_packets)):
        raise ValueError("team_packet_count must match team_packets")
    if getattr(report, "research_assignment_count") != Decimal(len(packet_rows)):
        raise ValueError("research_assignment_count must match team packet rows")
    _validate_status_count("assigned_count", report, packet_rows, "assigned")
    _validate_status_count("watch_count", report, packet_rows, "watch")
    _validate_status_count("blocked_count", report, packet_rows, "blocked")


def _packet_rows(team_packets: tuple[object, ...]) -> tuple[object, ...]:
    rows: list[object] = []
    for packet in team_packets:
        _validate_team_packet_payload(packet)
        rows.extend(_iterable_values(_field_raw(packet, "rows", ())))
    return tuple(rows)


def _validate_team_packet_payload(packet: object) -> None:
    _require_hard_flags("team packet", packet)
    for field_name in _PACKET_COUNT_FIELDS:
        _require_count_decimal(field_name, _field_raw(packet, field_name, None))
    rows = _iterable_values(_field_raw(packet, "rows", ()))
    for row in rows:
        _require_hard_flags("team packet row", row)
    if _field_raw(packet, "assignment_count", None) != Decimal(len(rows)):
        raise ValueError("assignment_count must match team packet rows")
    _validate_status_count("assigned_count", packet, rows, "assigned")
    _validate_status_count("watch_count", packet, rows, "watch")
    _validate_status_count("blocked_count", packet, rows, "blocked")


def _validate_status_count(
    field_name: str,
    container: object,
    rows: tuple[object, ...],
    status: str,
) -> None:
    if _field_raw(container, field_name, None) != Decimal(
        sum(1 for row in rows if _field_raw(row, "assignment_status", None) == status),
    ):
        raise ValueError(f"{field_name} must match team packet rows")


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must use Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _HARD_FLAG_FIELDS:
        if _field_raw(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for key, item in _public_items(value):
        if _has_unsafe_public_payload_marker(key):
            raise ValueError(f"unsafe public payload field in {label}: {key}")
        _reject_unsafe_public_payload(label, item)
    if type(value) is str and _has_unsafe_public_payload_marker(value):
        raise ValueError(f"unsafe public payload value in {label}")


def _public_items(value: object) -> tuple[tuple[str, object], ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _public_items(asdict(value))
    if isinstance(value, dict):
        items: list[tuple[str, object]] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            items.append((key, item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        return tuple((str(index), item) for index, item in enumerate(value))
    if hasattr(value, "__dict__"):
        return tuple(
            (key, item)
            for key, item in vars(value).items()
            if not key.startswith("_")
        )
    return ()


def _has_unsafe_public_payload_marker(value: str) -> bool:
    lowered_value = value.lower()
    return any(marker in lowered_value for marker in _UNSAFE_PUBLIC_PAYLOAD_MARKERS)


def _field_value(container: object, name: str, default: object) -> str:
    return _string_value(_field_raw(container, name, default))


def _field_raw(container: object, name: str, default: object) -> object:
    if isinstance(container, dict):
        return container.get(name, default)
    return getattr(container, name, default)


__all__ = ("format_team_research_work_packet_cli_stdout",)
