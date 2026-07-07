"""Pure Phase 1 research packet source freshness/staleness gate."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
import hashlib
import json
from types import MappingProxyType
from typing import Any


ZERO = Decimal("0.000000")
VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_CONFIG_VERSION = "research-packet-source-freshness-staleness-gate-v2"

ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty", "pass", "watch", "block")

PASS_REASON = "source_freshness_pass"
NEWEST_STALE_REASON = "newest_source_stale"
STALE_GAP_REASON = "stale_source_gap"
OFFICIAL_GAP_REASON = "official_source_gap"
SOURCE_FAMILY_GAP_REASON = "source_family_gap"

REASON_CODE_PRIORITY = (
    PASS_REASON,
    NEWEST_STALE_REASON,
    STALE_GAP_REASON,
    OFFICIAL_GAP_REASON,
    SOURCE_FAMILY_GAP_REASON,
)
REASON_CODES = frozenset(REASON_CODE_PRIORITY)
BLOCKING_REASON_CODES = frozenset(
    (
        NEWEST_STALE_REASON,
        OFFICIAL_GAP_REASON,
        SOURCE_FAMILY_GAP_REASON,
    ),
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessStalenessGateV2Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    min_official_source_count: Decimal = Decimal("1")
    min_independent_source_family_count: Decimal = Decimal("2")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "min_official_source_count",
            "min_independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessStalenessGateV2Input:
    packet_id: str
    event_slug: str
    category: str
    newest_source_at: datetime
    oldest_source_at: datetime
    official_source_count: Decimal
    independent_source_family_count: Decimal
    required_freshness_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "newest_source_at",
            _as_utc("newest_source_at", self.newest_source_at),
        )
        object.__setattr__(
            self,
            "oldest_source_at",
            _as_utc("oldest_source_at", self.oldest_source_at),
        )
        if self.oldest_source_at > self.newest_source_at:
            raise ValueError("oldest_source_at must not be after newest_source_at")
        for field_name in (
            "official_source_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "required_freshness_seconds",
            _normalize_positive_decimal(
                "required_freshness_seconds",
                self.required_freshness_seconds,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(self))


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessStalenessGateV2Row:
    packet_id: str
    event_slug: str
    category: str
    newest_source_at: datetime
    oldest_source_at: datetime
    official_source_count: Decimal
    independent_source_family_count: Decimal
    required_freshness_seconds: Decimal
    newest_source_age_seconds: Decimal
    oldest_source_age_seconds: Decimal
    stale_source_gap: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("packet_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "newest_source_at",
            _as_utc("newest_source_at", self.newest_source_at),
        )
        object.__setattr__(
            self,
            "oldest_source_at",
            _as_utc("oldest_source_at", self.oldest_source_at),
        )
        if self.oldest_source_at > self.newest_source_at:
            raise ValueError("oldest_source_at must not be after newest_source_at")
        for field_name in (
            "official_source_count",
            "independent_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_freshness_seconds",
            "newest_source_age_seconds",
            "oldest_source_age_seconds",
            "stale_source_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_freshness_seconds <= ZERO:
            raise ValueError("required_freshness_seconds must be positive")
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchPacketSourceFreshnessStalenessGateV2Report:
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_packet_count: Decimal
    watch_packet_count: Decimal
    block_packet_count: Decimal
    stale_packet_count: Decimal
    official_source_gap_count: Decimal
    source_family_gap_count: Decimal
    max_oldest_source_age_seconds: Decimal
    report_status: str
    reason_code_counts: Mapping[str, Decimal]
    rows: tuple[ResearchPacketSourceFreshnessStalenessGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "packet_count",
            "pass_packet_count",
            "watch_packet_count",
            "block_packet_count",
            "stale_packet_count",
            "official_source_gap_count",
            "source_family_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_oldest_source_age_seconds",
            _normalize_nonnegative_decimal(
                "max_oldest_source_age_seconds",
                self.max_oldest_source_age_seconds,
            ),
        )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_packet_source_freshness_staleness_gate_v2_public_payload(self)


def build_research_packet_source_freshness_staleness_gate_v2(
    packets: Iterable[ResearchPacketSourceFreshnessStalenessGateV2Input],
    *,
    generated_at: datetime,
    config: ResearchPacketSourceFreshnessStalenessGateV2Config,
) -> ResearchPacketSourceFreshnessStalenessGateV2Report:
    if type(config) is not ResearchPacketSourceFreshnessStalenessGateV2Config:
        raise ValueError(
            "config must be a ResearchPacketSourceFreshnessStalenessGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_packets = _normalize_inputs(packets, generated_at=generated_at_utc)
    rows = tuple(
        sorted(
            (
                _row_for_input(
                    packet,
                    generated_at=generated_at_utc,
                    config=config,
                )
                for packet in normalized_packets
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchPacketSourceFreshnessStalenessGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        packet_count=_count(len(rows)),
        pass_packet_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_packet_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_packet_count=_count(sum(1 for row in rows if row.status == "block")),
        stale_packet_count=_count(
            sum(1 for row in rows if STALE_GAP_REASON in row.reason_codes),
        ),
        official_source_gap_count=_count(
            sum(1 for row in rows if OFFICIAL_GAP_REASON in row.reason_codes),
        ),
        source_family_gap_count=_count(
            sum(1 for row in rows if SOURCE_FAMILY_GAP_REASON in row.reason_codes),
        ),
        max_oldest_source_age_seconds=_max_decimal(
            row.oldest_source_age_seconds for row in rows
        ),
        report_status=_report_status_from_rows(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_packet_source_freshness_staleness_gate_v2_public_payload(
    value: ResearchPacketSourceFreshnessStalenessGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchPacketSourceFreshnessStalenessGateV2Report:
        _validate_report(value)
        _validate_derived_validation_digest(value)
        payload = _payload_value(value)
    elif type(value) is dict:
        payload = value
    else:
        raise ValueError(
            "value must be a ResearchPacketSourceFreshnessStalenessGateV2Report or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    validate_research_packet_source_freshness_staleness_gate_v2_public_payload(payload)
    return dict(payload)


def validate_research_packet_source_freshness_staleness_gate_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_flags(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_input(
    packet: ResearchPacketSourceFreshnessStalenessGateV2Input,
    *,
    generated_at: datetime,
    config: ResearchPacketSourceFreshnessStalenessGateV2Config,
) -> ResearchPacketSourceFreshnessStalenessGateV2Row:
    newest_source_age_seconds = _seconds_between(packet.newest_source_at, generated_at)
    oldest_source_age_seconds = _seconds_between(packet.oldest_source_at, generated_at)
    stale_source_gap = _nonnegative_decimal_delta(
        oldest_source_age_seconds,
        packet.required_freshness_seconds,
    )
    reason_codes = _row_reason_codes(
        packet,
        newest_source_age_seconds=newest_source_age_seconds,
        stale_source_gap=stale_source_gap,
        config=config,
    )
    return ResearchPacketSourceFreshnessStalenessGateV2Row(
        packet_id=packet.packet_id,
        event_slug=packet.event_slug,
        category=packet.category,
        newest_source_at=packet.newest_source_at,
        oldest_source_at=packet.oldest_source_at,
        official_source_count=packet.official_source_count,
        independent_source_family_count=packet.independent_source_family_count,
        required_freshness_seconds=packet.required_freshness_seconds,
        newest_source_age_seconds=newest_source_age_seconds,
        oldest_source_age_seconds=oldest_source_age_seconds,
        stale_source_gap=stale_source_gap,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    packet: ResearchPacketSourceFreshnessStalenessGateV2Input,
    *,
    newest_source_age_seconds: Decimal,
    stale_source_gap: Decimal,
    config: ResearchPacketSourceFreshnessStalenessGateV2Config,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if newest_source_age_seconds > packet.required_freshness_seconds:
        reasons.append(NEWEST_STALE_REASON)
    if stale_source_gap > ZERO:
        reasons.append(STALE_GAP_REASON)
    if packet.official_source_count < config.min_official_source_count:
        reasons.append(OFFICIAL_GAP_REASON)
    if (
        packet.independent_source_family_count
        < config.min_independent_source_family_count
    ):
        reasons.append(SOURCE_FAMILY_GAP_REASON)
    if not reasons:
        return (PASS_REASON,)
    return _normalize_reason_codes("reason_codes", tuple(reasons))


def _normalize_inputs(
    value: Iterable[ResearchPacketSourceFreshnessStalenessGateV2Input],
    *,
    generated_at: datetime,
) -> tuple[ResearchPacketSourceFreshnessStalenessGateV2Input, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("packets must be an iterable")
    try:
        packets = tuple(value)
    except TypeError as exc:
        raise ValueError("packets must be an iterable") from exc
    seen_packet_ids: set[str] = set()
    for packet in packets:
        if type(packet) is not ResearchPacketSourceFreshnessStalenessGateV2Input:
            raise ValueError(
                "packets must contain ResearchPacketSourceFreshnessStalenessGateV2Input values",
            )
        _require_hard_flags("packet", packet)
        if packet.packet_id in seen_packet_ids:
            raise ValueError("packet_id values must be unique")
        seen_packet_ids.add(packet.packet_id)
        if packet.newest_source_at > generated_at:
            raise ValueError("newest_source_at must not be after generated_at")
        if packet.oldest_source_at > generated_at:
            raise ValueError("oldest_source_at must not be after generated_at")
    return tuple(sorted(packets, key=_input_sort_key))


def _normalize_rows(
    value: Iterable[ResearchPacketSourceFreshnessStalenessGateV2Row],
) -> tuple[ResearchPacketSourceFreshnessStalenessGateV2Row, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_packet_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketSourceFreshnessStalenessGateV2Row:
            raise ValueError(
                "rows must contain ResearchPacketSourceFreshnessStalenessGateV2Row values",
            )
        _require_hard_flags("row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("row packet_id values must be unique")
        seen_packet_ids.add(row.packet_id)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _validate_report(report: ResearchPacketSourceFreshnessStalenessGateV2Report) -> None:
    rows = report.rows
    if report.packet_count != _count(len(rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_packet_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_packet_count must match rows")
    if report.watch_packet_count != _count(
        sum(1 for row in rows if row.status == "watch"),
    ):
        raise ValueError("watch_packet_count must match rows")
    if report.block_packet_count != _count(
        sum(1 for row in rows if row.status == "block"),
    ):
        raise ValueError("block_packet_count must match rows")
    if report.stale_packet_count != _count(
        sum(1 for row in rows if STALE_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("stale_packet_count must match rows")
    if report.official_source_gap_count != _count(
        sum(1 for row in rows if OFFICIAL_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("official_source_gap_count must match rows")
    if report.source_family_gap_count != _count(
        sum(1 for row in rows if SOURCE_FAMILY_GAP_REASON in row.reason_codes),
    ):
        raise ValueError("source_family_gap_count must match rows")
    if report.max_oldest_source_age_seconds != _max_decimal(
        row.oldest_source_age_seconds for row in rows
    ):
        raise ValueError("max_oldest_source_age_seconds must match rows")
    if report.report_status != _report_status_from_rows(rows):
        raise ValueError("report_status must match rows")
    if dict(report.reason_code_counts) != dict(_reason_code_counts(rows)):
        raise ValueError("reason_code_counts must match rows")


def _set_or_validate_derived_validation_digest(
    report: ResearchPacketSourceFreshnessStalenessGateV2Report,
) -> None:
    current = report.derived_validation_digest
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report fields")


def _validate_derived_validation_digest(
    report: ResearchPacketSourceFreshnessStalenessGateV2Report,
) -> None:
    current = _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if current != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _derived_validation_digest(value: object) -> str:
    payload = _without_derived_validation_digest(_payload_value(value))
    encoded = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _without_derived_validation_digest(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_derived_validation_digest(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_derived_validation_digest(item) for item in value]
    return value


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if isinstance(value, Mapping):
        return {
            key: _payload_value(value[key])
            for key in sorted(value, key=_mapping_sort_key(value))
        }
    return value


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if value is None or type(value) is bool:
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public payload value in {path or label}")
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError(f"{path or label} must use Decimal strings, not numeric values")
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public payload key in {label}: {key}")
            item_path = key if not path else f"{path}.{key}"
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public JSON serializable")


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_nonnegative_decimal(
        "source_age_seconds",
        Decimal(str((end - start).total_seconds())),
    )


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = value.quantize(COUNT_QUANTUM)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _nonnegative_decimal_delta(value: Decimal, offset: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        result = value - offset
    if result <= ZERO:
        return ZERO
    return _normalize_nonnegative_decimal("stale_source_gap", result)


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    return max(tuple(values), default=ZERO)


def _normalize_reason_codes(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of reason codes")
    try:
        codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of reason codes") from exc
    if not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        if type(code) is not str or not code:
            raise ValueError(f"{field_name} must contain non-empty strings")
        if code not in REASON_CODES:
            raise ValueError(f"{field_name} contains an unknown reason code")
    active_codes = [code for code in codes if code != PASS_REASON]
    if PASS_REASON in codes and active_codes:
        raise ValueError(f"{field_name} pass reason must stand alone")
    return tuple(sorted(set(codes), key=REASON_CODE_PRIORITY.index))


def _normalize_reason_code_counts(
    value: Mapping[str, Decimal],
) -> Mapping[str, Decimal]:
    if not isinstance(value, Mapping):
        raise ValueError("reason_code_counts must be a mapping")
    normalized: dict[str, Decimal] = {}
    for code, count in value.items():
        if type(code) is not str or code not in REASON_CODES:
            raise ValueError("reason_code_counts contains an unknown reason code")
        normalized[code] = _normalize_count(f"reason_code_counts.{code}", count)
    return MappingProxyType(
        {
            code: normalized[code]
            for code in sorted(normalized, key=_reason_code_sort_index)
        },
    )


def _reason_code_counts(
    rows: tuple[ResearchPacketSourceFreshnessStalenessGateV2Row, ...],
) -> Mapping[str, Decimal]:
    counts: dict[str, int] = {}
    for row in rows:
        for code in row.reason_codes:
            counts[code] = counts.get(code, 0) + 1
    return _normalize_reason_code_counts(
        {code: _count(count) for code, count in counts.items()},
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (PASS_REASON,):
        return "pass"
    if any(code in BLOCKING_REASON_CODES for code in reason_codes):
        return "block"
    return "watch"


def _report_status_from_rows(
    rows: tuple[ResearchPacketSourceFreshnessStalenessGateV2Row, ...],
) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _require_member(field_name: str, value: object, members: tuple[str, ...]) -> None:
    if type(value) is not str or value not in members:
        raise ValueError(f"{field_name} must be one of {members}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be a canonical string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public content")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _input_sort_key(
    packet: ResearchPacketSourceFreshnessStalenessGateV2Input,
) -> tuple[str, str, str]:
    return (packet.category, packet.event_slug, packet.packet_id)


def _row_sort_key(
    row: ResearchPacketSourceFreshnessStalenessGateV2Row,
) -> tuple[str, str, str]:
    return (row.category, row.event_slug, row.packet_id)


def _reason_code_sort_index(code: str) -> int:
    if code not in REASON_CODES:
        raise ValueError("unknown reason code")
    return REASON_CODE_PRIORITY.index(code)


def _mapping_sort_key(value: Mapping[str, object]) -> Any:
    if all(type(key) is str and key in REASON_CODES for key in value):
        return _reason_code_sort_index
    return str


__all__ = (
    "ResearchPacketSourceFreshnessStalenessGateV2Config",
    "ResearchPacketSourceFreshnessStalenessGateV2Input",
    "ResearchPacketSourceFreshnessStalenessGateV2Report",
    "ResearchPacketSourceFreshnessStalenessGateV2Row",
    "build_research_packet_source_freshness_staleness_gate_v2",
    "research_packet_source_freshness_staleness_gate_v2_public_payload",
    "validate_research_packet_source_freshness_staleness_gate_v2_public_payload",
)
