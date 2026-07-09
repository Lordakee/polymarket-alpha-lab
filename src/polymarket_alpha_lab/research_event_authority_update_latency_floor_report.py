"""Readonly event authority update latency floor report reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_AUTHORITY_UPDATE_LATENCY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-event-authority-update-latency-floor-report-v0"
)

SIX = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SHA256_HEX_LENGTH = 64

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

EMPTY_REASON = "research_event_authority_update_latency_floor_empty"
PASS_REASON = "authority_update_latency_floor_pass"
WATCH_REASON = "authority_update_latency_floor_watch"
BLOCK_REASON = "authority_update_latency_floor_block"
ROW_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCK_REASON)
REPORT_REASON_CODES = (EMPTY_REASON, BLOCK_REASON, WATCH_REASON, PASS_REASON)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("cand", "idate"),
    _join_parts("mark", "et"),
    _join_parts("sl", "ug"),
    _join_parts("que", "stion"),
    _join_parts("ur", "l"),
    _join_parts("te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("siz", "ing"),
    _join_parts("recomm", "endation"),
    "://",
    "http",
    "www.",
    "postgres://",
    "mysql://",
    "jdbc:",
)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_AUTHORITY_UPDATE_LATENCY_FLOOR_REPORT_CONFIG_VERSION",
    "ResearchEventAuthorityUpdateLatencyFloorConfig",
    "ResearchEventAuthorityUpdateLatencyFloorObservation",
    "ResearchEventAuthorityUpdateLatencyFloorRow",
    "ResearchEventAuthorityUpdateLatencyFloorReport",
    "build_research_event_authority_update_latency_floor_report",
    "research_event_authority_update_latency_floor_report_digest",
    "research_event_authority_update_latency_floor_report_payload",
    "validate_research_event_authority_update_latency_floor_report_digest",
    "validate_research_event_authority_update_latency_floor_report_payload",
)


@dataclass(frozen=True)
class ResearchEventAuthorityUpdateLatencyFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_AUTHORITY_UPDATE_LATENCY_FLOOR_REPORT_CONFIG_VERSION
    )
    pass_latency_floor_seconds: Decimal = Decimal("900.000000")
    watch_latency_floor_seconds: Decimal = Decimal("300.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityUpdateLatencyFloorConfig:
            raise TypeError(
                "ResearchEventAuthorityUpdateLatencyFloorConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventAuthorityUpdateLatencyFloorConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_AUTHORITY_UPDATE_LATENCY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "pass_latency_floor_seconds",
            _require_positive_decimal(
                "pass_latency_floor_seconds",
                self.pass_latency_floor_seconds,
            ),
        )
        object.__setattr__(
            self,
            "watch_latency_floor_seconds",
            _require_positive_decimal(
                "watch_latency_floor_seconds",
                self.watch_latency_floor_seconds,
            ),
        )
        if self.watch_latency_floor_seconds >= self.pass_latency_floor_seconds:
            raise ValueError(
                "watch_latency_floor_seconds must be less than "
                "pass_latency_floor_seconds",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventAuthorityUpdateLatencyFloorObservation:
    event_digest: str
    authority_digest: str
    observed_at: datetime
    authority_update_latency_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityUpdateLatencyFloorObservation:
            raise TypeError(
                "ResearchEventAuthorityUpdateLatencyFloorObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventAuthorityUpdateLatencyFloorObservation,
            "observation",
        )
        _require_sha256("event_digest", self.event_digest)
        _require_sha256("authority_digest", self.authority_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "authority_update_latency_seconds",
            _require_nonnegative_decimal(
                "authority_update_latency_seconds",
                self.authority_update_latency_seconds,
            ),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventAuthorityUpdateLatencyFloorRow:
    rank: Decimal
    event_digest: str
    authority_digest: str
    observed_at: datetime
    authority_update_latency_seconds: Decimal
    latency_floor_gap_seconds: Decimal
    latency_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityUpdateLatencyFloorRow:
            raise TypeError(
                "ResearchEventAuthorityUpdateLatencyFloorRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventAuthorityUpdateLatencyFloorRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        _require_sha256("event_digest", self.event_digest)
        _require_sha256("authority_digest", self.authority_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "authority_update_latency_seconds",
            "latency_floor_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latency_floor_score",
            _require_ratio_decimal("latency_floor_score", self.latency_floor_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class ResearchEventAuthorityUpdateLatencyFloorReport:
    generated_at: datetime
    config_version: str
    status: str
    event_count: Decimal
    pass_event_count: Decimal
    watch_event_count: Decimal
    block_event_count: Decimal
    below_latency_floor_event_count: Decimal
    minimum_authority_update_latency_seconds: Decimal
    maximum_latency_floor_gap_seconds: Decimal
    average_latency_floor_score: Decimal
    rows: tuple[ResearchEventAuthorityUpdateLatencyFloorRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventAuthorityUpdateLatencyFloorReport:
            raise TypeError(
                "ResearchEventAuthorityUpdateLatencyFloorReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventAuthorityUpdateLatencyFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("status", self.status)
        for field_name in (
            "event_count",
            "pass_event_count",
            "watch_event_count",
            "block_event_count",
            "below_latency_floor_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "minimum_authority_update_latency_seconds",
            "maximum_latency_floor_gap_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_latency_floor_score",
            _require_ratio_decimal(
                "average_latency_floor_score",
                self.average_latency_floor_score,
            ),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        _require_sha256("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_authority_update_latency_floor_report_payload(self)


def build_research_event_authority_update_latency_floor_report(
    observations: Iterable[ResearchEventAuthorityUpdateLatencyFloorObservation],
    *,
    config: ResearchEventAuthorityUpdateLatencyFloorConfig | None = None,
    generated_at: datetime,
) -> ResearchEventAuthorityUpdateLatencyFloorReport:
    cfg = config or ResearchEventAuthorityUpdateLatencyFloorConfig()
    _require_exact_type(cfg, ResearchEventAuthorityUpdateLatencyFloorConfig, "config")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_for_observation(observation=item, config=cfg)
        for item in _sorted_observations(normalized, cfg)
    )
    ranked_rows = tuple(
        _ranked_row(index=index, row=row) for index, row in enumerate(rows, start=1)
    )
    status = _report_status(ranked_rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "status": status,
        "event_count": _count_decimal(len(ranked_rows)),
        "pass_event_count": _status_count(ranked_rows, STATUS_PASS),
        "watch_event_count": _status_count(ranked_rows, STATUS_WATCH),
        "block_event_count": _status_count(ranked_rows, STATUS_BLOCK),
        "below_latency_floor_event_count": _below_floor_count(ranked_rows),
        "minimum_authority_update_latency_seconds": min(
            (row.authority_update_latency_seconds for row in ranked_rows),
            default=ZERO,
        ),
        "maximum_latency_floor_gap_seconds": max(
            (row.latency_floor_gap_seconds for row in ranked_rows),
            default=ZERO,
        ),
        "average_latency_floor_score": _average(
            row.latency_floor_score for row in ranked_rows
        ),
        "rows": ranked_rows,
        "reason_codes": _report_reason_codes(ranked_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return ResearchEventAuthorityUpdateLatencyFloorReport(**values)


def research_event_authority_update_latency_floor_report_digest(
    report: ResearchEventAuthorityUpdateLatencyFloorReport,
) -> str:
    _require_exact_type(
        report,
        ResearchEventAuthorityUpdateLatencyFloorReport,
        "report",
    )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return _derived_validation_digest(payload)


def validate_research_event_authority_update_latency_floor_report_digest(
    report: ResearchEventAuthorityUpdateLatencyFloorReport,
) -> bool:
    _require_exact_type(
        report,
        ResearchEventAuthorityUpdateLatencyFloorReport,
        "report",
    )
    _require_hard_flags("report", report)
    _require_matching_digest(_payload_value(report))
    return True


def research_event_authority_update_latency_floor_report_payload(
    report: ResearchEventAuthorityUpdateLatencyFloorReport,
) -> dict[str, Any]:
    _require_exact_type(
        report,
        ResearchEventAuthorityUpdateLatencyFloorReport,
        "report",
    )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_matching_digest(payload)
    return payload


def validate_research_event_authority_update_latency_floor_report_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return True


def _row_for_observation(
    *,
    observation: ResearchEventAuthorityUpdateLatencyFloorObservation,
    config: ResearchEventAuthorityUpdateLatencyFloorConfig,
) -> ResearchEventAuthorityUpdateLatencyFloorRow:
    gap = max(
        ZERO,
        _six(config.pass_latency_floor_seconds - observation.authority_update_latency_seconds),
    )
    score = _latency_floor_score(
        observation.authority_update_latency_seconds,
        config.pass_latency_floor_seconds,
    )
    status = _row_status(observation.authority_update_latency_seconds, config)
    return ResearchEventAuthorityUpdateLatencyFloorRow(
        rank=ONE,
        event_digest=observation.event_digest,
        authority_digest=observation.authority_digest,
        observed_at=observation.observed_at,
        authority_update_latency_seconds=observation.authority_update_latency_seconds,
        latency_floor_gap_seconds=gap,
        latency_floor_score=score,
        status=status,
        reason_codes=(_row_reason_code(status),),
    )


def _ranked_row(
    *,
    index: int,
    row: ResearchEventAuthorityUpdateLatencyFloorRow,
) -> ResearchEventAuthorityUpdateLatencyFloorRow:
    return ResearchEventAuthorityUpdateLatencyFloorRow(
        rank=_count_decimal(index),
        event_digest=row.event_digest,
        authority_digest=row.authority_digest,
        observed_at=row.observed_at,
        authority_update_latency_seconds=row.authority_update_latency_seconds,
        latency_floor_gap_seconds=row.latency_floor_gap_seconds,
        latency_floor_score=row.latency_floor_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _latency_floor_score(latency_seconds: Decimal, pass_floor_seconds: Decimal) -> Decimal:
    return _clamp_ratio(latency_seconds / pass_floor_seconds)


def _row_status(
    latency_seconds: Decimal,
    config: ResearchEventAuthorityUpdateLatencyFloorConfig,
) -> str:
    if latency_seconds < config.watch_latency_floor_seconds:
        return STATUS_BLOCK
    if latency_seconds < config.pass_latency_floor_seconds:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_code(status: str) -> str:
    if status == STATUS_BLOCK:
        return BLOCK_REASON
    if status == STATUS_WATCH:
        return WATCH_REASON
    return PASS_REASON


def _normalize_observations(
    observations: Iterable[ResearchEventAuthorityUpdateLatencyFloorObservation],
) -> tuple[ResearchEventAuthorityUpdateLatencyFloorObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observations")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable of observations") from exc
    for item in normalized:
        _require_exact_type(
            item,
            ResearchEventAuthorityUpdateLatencyFloorObservation,
            "observation",
        )
        _require_hard_flags("observation", item)
    keys = tuple((item.event_digest, item.authority_digest) for item in normalized)
    if len(set(keys)) != len(keys):
        raise ValueError("observations must not contain duplicate digests")
    return normalized


def _sorted_observations(
    observations: tuple[ResearchEventAuthorityUpdateLatencyFloorObservation, ...],
    config: ResearchEventAuthorityUpdateLatencyFloorConfig,
) -> tuple[ResearchEventAuthorityUpdateLatencyFloorObservation, ...]:
    return tuple(
        sorted(
            observations,
            key=lambda item: (
                _status_rank(_row_status(item.authority_update_latency_seconds, config)),
                item.authority_update_latency_seconds,
                item.event_digest,
                item.authority_digest,
            ),
        ),
    )


def _require_rows(
    rows: tuple[ResearchEventAuthorityUpdateLatencyFloorRow, ...],
) -> tuple[ResearchEventAuthorityUpdateLatencyFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for index, row in enumerate(rows, start=1):
        _require_exact_type(row, ResearchEventAuthorityUpdateLatencyFloorRow, "row")
        _require_hard_flags("row", row)
        if row.rank != _count_decimal(index):
            raise ValueError("row ranks must be sequential")
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.status),
                row.authority_update_latency_seconds,
                row.event_digest,
                row.authority_digest,
            ),
        ),
    )
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by status and latency")
    return rows


def _status_rank(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    if status == STATUS_PASS:
        return 2
    raise ValueError("status must be one of pass, watch, block")


def _status_count(
    rows: tuple[ResearchEventAuthorityUpdateLatencyFloorRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _below_floor_count(
    rows: tuple[ResearchEventAuthorityUpdateLatencyFloorRow, ...],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.latency_floor_gap_seconds > ZERO))


def _report_status(rows: tuple[ResearchEventAuthorityUpdateLatencyFloorRow, ...]) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchEventAuthorityUpdateLatencyFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    present = {code for row in rows for code in row.reason_codes}
    return tuple(code for code in (BLOCK_REASON, WATCH_REASON, PASS_REASON) if code in present)


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _six(sum(items, ZERO) / Decimal(len(items)))


def _validate_report(report: ResearchEventAuthorityUpdateLatencyFloorReport) -> None:
    rows = report.rows
    _require_decimal_equal("event_count", report.event_count, _count_decimal(len(rows)))
    _require_decimal_equal(
        "pass_event_count",
        report.pass_event_count,
        _status_count(rows, STATUS_PASS),
    )
    _require_decimal_equal(
        "watch_event_count",
        report.watch_event_count,
        _status_count(rows, STATUS_WATCH),
    )
    _require_decimal_equal(
        "block_event_count",
        report.block_event_count,
        _status_count(rows, STATUS_BLOCK),
    )
    _require_decimal_equal(
        "below_latency_floor_event_count",
        report.below_latency_floor_event_count,
        _below_floor_count(rows),
    )
    _require_decimal_equal(
        "minimum_authority_update_latency_seconds",
        report.minimum_authority_update_latency_seconds,
        min((row.authority_update_latency_seconds for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "maximum_latency_floor_gap_seconds",
        report.maximum_latency_floor_gap_seconds,
        max((row.latency_floor_gap_seconds for row in rows), default=ZERO),
    )
    _require_decimal_equal(
        "average_latency_floor_score",
        report.average_latency_floor_score,
        _average(row.latency_floor_score for row in rows),
    )
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(
            {field.name: getattr(value, field.name) for field in fields(value)}
        )
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("public payload Decimal values must be finite")
        return format(value, "f")
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is str:
        _require_safe_public_value("public payload value", value)
        return value
    if type(value) is bool or value is None:
        return value
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is tuple or type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is dict:
        payload: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_value("public payload key", key)
            payload[key] = _payload_value(item)
        return payload
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(name: str, value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _require_safe_public_value(f"{name} key", key)
            _reject_unsafe_public_payload(f"{name}.{key}", item)
        return
    if type(value) is list:
        for item in value:
            _reject_unsafe_public_payload(name, item)
        return
    if type(value) is str:
        _require_safe_public_value(name, value)
        return
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must use Decimal strings")
    if type(value) is bool or value is None:
        return
    raise ValueError("public payload contains unsupported value")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"payload {flag_name} must be True")
    rows = payload.get("rows", [])
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must be dicts")
        for flag_name in ("paper_only", "report_only", "readonly"):
            if row.get(flag_name) is not True:
                raise ValueError(f"payload row {flag_name} must be True")


def _require_safe_public_value(name: str, value: str) -> None:
    lower = value.lower()
    if any(fragment in lower for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public surface")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    material = {key: value for key, value in payload.items() if key != "derived_validation_digest"}
    return sha256(
        json.dumps(material, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_matching_digest(payload: Any) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_sha256("derived_validation_digest", payload["derived_validation_digest"])
    if payload["derived_validation_digest"] != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_public_string(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be non-empty")
    if value.strip() != value:
        raise ValueError(f"{name} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{name} must be canonical")
    _require_safe_public_value(name, value)
    return value


def _require_sha256(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a sha256 digest string")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{name} must be a sha256 digest string")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{name} must be a sha256 digest string") from exc
    _require_safe_public_value(name, value)
    return value


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _six(value)


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return decimal_value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _require_nonnegative_count(name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_decimal(name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole count")
    return decimal_value


def _require_decimal_equal(name: str, actual: Decimal, expected: Decimal) -> None:
    if actual != _six(expected):
        raise ValueError(f"{name} must equal derived value")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of {STATUSES}")


def _require_reason_codes(
    name: str,
    values: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    if not values:
        raise ValueError(f"{name} must be nonempty")
    for value in values:
        if type(value) is not str or value not in allowed:
            raise ValueError(f"{name} contains an unknown reason code")
        _require_safe_public_value(name, value)
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")
    return values


def _require_hard_flags(name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{name} {flag_name} must be True")


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return Decimal(value).quantize(SIX)


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX)


def _clamp_ratio(value: Decimal) -> Decimal:
    return _six(max(ZERO, min(ONE, value)))
