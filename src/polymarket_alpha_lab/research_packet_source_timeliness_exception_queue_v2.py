"""Phase 1 report-only source timeliness exception queue."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_PACKET_SOURCE_TIMELINESS_EXCEPTION_QUEUE_V2_CONFIG_VERSION = (
    "research-packet-source-timeliness-exception-queue-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_QUEUE_STATES = frozenset(("current", "watch", "urgent"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
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
_REASON_CODE_SEQUENCE = (
    "source_timely",
    "source_stale_penalty",
    "urgent_refresh_requested",
    "urgent_refresh_boost",
    "timeliness_exception_current",
    "timeliness_exception_watch",
    "timeliness_exception_urgent",
)


@dataclass(frozen=True)
class ResearchPacketSourceTimelinessExceptionQueueConfig:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_SOURCE_TIMELINESS_EXCEPTION_QUEUE_V2_CONFIG_VERSION
    )
    watch_exception_score: Decimal = Decimal("0.400000")
    urgent_exception_score: Decimal = Decimal("0.800000")
    stale_penalty_weight: Decimal = Decimal("0.600000")
    urgent_refresh_boost: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceTimelinessExceptionQueueConfig:
            raise TypeError(
                "ResearchPacketSourceTimelinessExceptionQueueConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceTimelinessExceptionQueueConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchPacketSourceTimelinessExceptionQueueConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_TIMELINESS_EXCEPTION_QUEUE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_exception_score",
            "urgent_exception_score",
            "stale_penalty_weight",
            "urgent_refresh_boost",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_exception_score > self.urgent_exception_score:
            raise ValueError("watch_exception_score must not exceed urgent_exception_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot:
    packet_id: str
    source_id: str
    observed_at: datetime
    expected_refresh_seconds: Decimal
    urgent_refresh_requested: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot:
            raise TypeError(
                "ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot does "
                "not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot:
            raise ValueError(
                "source snapshot must be exactly "
                "ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot",
            )
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("source_id", self.source_id)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "expected_refresh_seconds",
            _require_positive_decimal(
                "expected_refresh_seconds",
                self.expected_refresh_seconds,
            ),
        )
        _require_bool("urgent_refresh_requested", self.urgent_refresh_requested)
        _require_hard_flags("source snapshot", self)
        _reject_unsafe_public_payload("source snapshot", self)


@dataclass(frozen=True)
class ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem:
            raise TypeError(
                "ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchPacketSourceTimelinessExceptionQueueRow:
    packet_id: str
    source_id: str
    rank: Decimal
    age_seconds: Decimal
    expected_refresh_seconds: Decimal
    overdue_seconds: Decimal
    stale_age_ratio: Decimal
    stale_source_penalty: Decimal
    urgent_refresh_boost: Decimal
    timeliness_exception_score: Decimal
    queue_state: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceTimelinessExceptionQueueRow:
            raise TypeError(
                "ResearchPacketSourceTimelinessExceptionQueueRow does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceTimelinessExceptionQueueRow:
            raise ValueError(
                "row must be exactly ResearchPacketSourceTimelinessExceptionQueueRow",
            )
        _require_public_identifier("packet_id", self.packet_id)
        _require_public_identifier("source_id", self.source_id)
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in (
            "age_seconds",
            "overdue_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_refresh_seconds",
            _require_positive_decimal(
                "expected_refresh_seconds",
                self.expected_refresh_seconds,
            ),
        )
        for field_name in (
            "stale_age_ratio",
            "stale_source_penalty",
            "urgent_refresh_boost",
            "timeliness_exception_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_queue_state("queue_state", self.queue_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchPacketSourceTimelinessExceptionQueueReport:
    generated_at: datetime
    config_version: str
    queue_status: str
    source_count: Decimal
    current_count: Decimal
    watch_count: Decimal
    urgent_count: Decimal
    average_timeliness_exception_score: Decimal
    max_timeliness_exception_score: Decimal
    rows: tuple[ResearchPacketSourceTimelinessExceptionQueueRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[
        ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem,
        ...,
    ]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchPacketSourceTimelinessExceptionQueueReport:
            raise TypeError(
                "ResearchPacketSourceTimelinessExceptionQueueReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchPacketSourceTimelinessExceptionQueueReport:
            raise ValueError(
                "report must be exactly "
                "ResearchPacketSourceTimelinessExceptionQueueReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_SOURCE_TIMELINESS_EXCEPTION_QUEUE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_queue_state("queue_status", self.queue_status)
        for field_name in (
            "source_count",
            "current_count",
            "watch_count",
            "urgent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_timeliness_exception_score",
            "max_timeliness_exception_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchPacketSourceTimelinessExceptionQueueReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_packet_source_timeliness_exception_queue_v2_report(
    sources: Sequence[ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot],
    *,
    generated_at: datetime,
    config: ResearchPacketSourceTimelinessExceptionQueueConfig | None = None,
    public_payload: Sequence[
        ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem
    ] = (),
) -> ResearchPacketSourceTimelinessExceptionQueueReport:
    """Build a local report-only source timeliness exception queue."""

    if config is None:
        config = ResearchPacketSourceTimelinessExceptionQueueConfig()
    if type(config) is not ResearchPacketSourceTimelinessExceptionQueueConfig:
        raise ValueError(
            "config must be a ResearchPacketSourceTimelinessExceptionQueueConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_sources = _normalize_sources(sources)
    for source in normalized_sources:
        if source.observed_at > generated_at:
            raise ValueError("source observed_at must not be after generated_at")
    rows = _rank_rows(
        tuple(_unranked_row_for_source(source, generated_at, config) for source in normalized_sources),
    )
    payload_items = _normalize_public_payload(public_payload)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "queue_status": _report_status(rows),
        "source_count": _decimal_count(len(rows)),
        "current_count": _decimal_count(_state_count(rows, "current")),
        "watch_count": _decimal_count(_state_count(rows, "watch")),
        "urgent_count": _decimal_count(_state_count(rows, "urgent")),
        "average_timeliness_exception_score": _average(
            tuple(row.timeliness_exception_score for row in rows),
        ),
        "max_timeliness_exception_score": max(
            (row.timeliness_exception_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchPacketSourceTimelinessExceptionQueueReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _unranked_row_for_source(
    source: ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot,
    generated_at: datetime,
    config: ResearchPacketSourceTimelinessExceptionQueueConfig,
) -> ResearchPacketSourceTimelinessExceptionQueueRow:
    age_seconds = _quantize(
        Decimal(str((generated_at - source.observed_at).total_seconds())),
    )
    overdue_seconds = _quantize(max(age_seconds - source.expected_refresh_seconds, _ZERO))
    stale_age_ratio = _clamp_ratio(overdue_seconds / source.expected_refresh_seconds)
    stale_source_penalty = _clamp_ratio(stale_age_ratio * config.stale_penalty_weight)
    urgent_refresh_boost = (
        config.urgent_refresh_boost if source.urgent_refresh_requested else _ZERO
    )
    timeliness_exception_score = _clamp_ratio(
        stale_source_penalty + urgent_refresh_boost,
    )
    queue_state = _row_state(
        timeliness_exception_score=timeliness_exception_score,
        config=config,
    )
    return ResearchPacketSourceTimelinessExceptionQueueRow(
        packet_id=source.packet_id,
        source_id=source.source_id,
        rank=_ONE,
        age_seconds=age_seconds,
        expected_refresh_seconds=source.expected_refresh_seconds,
        overdue_seconds=overdue_seconds,
        stale_age_ratio=stale_age_ratio,
        stale_source_penalty=stale_source_penalty,
        urgent_refresh_boost=urgent_refresh_boost,
        timeliness_exception_score=timeliness_exception_score,
        queue_state=queue_state,
        reason_codes=_row_reason_codes(
            overdue_seconds=overdue_seconds,
            stale_source_penalty=stale_source_penalty,
            urgent_refresh_requested=source.urgent_refresh_requested,
            urgent_refresh_boost=urgent_refresh_boost,
            queue_state=queue_state,
        ),
    )


def _rank_rows(
    rows: tuple[ResearchPacketSourceTimelinessExceptionQueueRow, ...],
) -> tuple[ResearchPacketSourceTimelinessExceptionQueueRow, ...]:
    ranked_rows: list[ResearchPacketSourceTimelinessExceptionQueueRow] = []
    for index, row in enumerate(
        sorted(
            rows,
            key=lambda item: (
                -item.timeliness_exception_score,
                item.packet_id,
                item.source_id,
            ),
        ),
        start=1,
    ):
        values = asdict(row)
        values["rank"] = _decimal_count(index)
        ranked_rows.append(ResearchPacketSourceTimelinessExceptionQueueRow(**values))
    return tuple(ranked_rows)


def _row_state(
    *,
    timeliness_exception_score: Decimal,
    config: ResearchPacketSourceTimelinessExceptionQueueConfig,
) -> str:
    if timeliness_exception_score >= config.urgent_exception_score:
        return "urgent"
    if timeliness_exception_score >= config.watch_exception_score:
        return "watch"
    return "current"


def _row_reason_codes(
    *,
    overdue_seconds: Decimal,
    stale_source_penalty: Decimal,
    urgent_refresh_requested: bool,
    urgent_refresh_boost: Decimal,
    queue_state: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if overdue_seconds == _ZERO:
        reason_codes.append("source_timely")
    if stale_source_penalty > _ZERO:
        reason_codes.append("source_stale_penalty")
    if urgent_refresh_requested:
        reason_codes.append("urgent_refresh_requested")
    if urgent_refresh_boost > _ZERO:
        reason_codes.append("urgent_refresh_boost")
    reason_codes.append(f"timeliness_exception_{queue_state}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchPacketSourceTimelinessExceptionQueueRow, ...],
) -> str:
    if any(row.queue_state == "urgent" for row in rows):
        return "urgent"
    if any(row.queue_state == "watch" for row in rows):
        return "watch"
    return "current"


def _report_reason_codes(
    rows: tuple[ResearchPacketSourceTimelinessExceptionQueueRow, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    if not reason_codes:
        reason_codes.append("timeliness_exception_current")
    return _normalize_reason_codes(tuple(reason_codes))


def _state_count(
    rows: tuple[ResearchPacketSourceTimelinessExceptionQueueRow, ...],
    queue_state: str,
) -> int:
    return sum(1 for row in rows if row.queue_state == queue_state)


def _validate_row_consistency(
    row: ResearchPacketSourceTimelinessExceptionQueueRow,
) -> None:
    expected_overdue = _quantize(max(row.age_seconds - row.expected_refresh_seconds, _ZERO))
    if row.overdue_seconds != expected_overdue:
        raise ValueError("overdue_seconds must match age less expected refresh seconds")
    expected_stale_ratio = _clamp_ratio(row.overdue_seconds / row.expected_refresh_seconds)
    if row.stale_age_ratio != expected_stale_ratio:
        raise ValueError("stale_age_ratio must match overdue age ratio")
    expected_score = _clamp_ratio(row.stale_source_penalty + row.urgent_refresh_boost)
    if row.timeliness_exception_score != expected_score:
        raise ValueError("timeliness_exception_score must match score components")
    state_reason_code = f"timeliness_exception_{row.queue_state}"
    if state_reason_code not in row.reason_codes:
        raise ValueError("queue_state must have a matching reason code")
    if row.overdue_seconds == _ZERO and "source_timely" not in row.reason_codes:
        raise ValueError("timely rows must include source_timely")
    if row.stale_source_penalty > _ZERO and "source_stale_penalty" not in row.reason_codes:
        raise ValueError("stale rows must include source_stale_penalty")
    if row.urgent_refresh_boost > _ZERO and "urgent_refresh_boost" not in row.reason_codes:
        raise ValueError("boosted rows must include urgent_refresh_boost")


def _validate_report_consistency(
    report: ResearchPacketSourceTimelinessExceptionQueueReport,
) -> None:
    if report.source_count != _decimal_count(len(report.rows)):
        raise ValueError("source_count must match rows")
    if report.current_count != _decimal_count(_state_count(report.rows, "current")):
        raise ValueError("current_count must match rows")
    if report.watch_count != _decimal_count(_state_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.urgent_count != _decimal_count(_state_count(report.rows, "urgent")):
        raise ValueError("urgent_count must match rows")
    if report.average_timeliness_exception_score != _average(
        tuple(row.timeliness_exception_score for row in report.rows),
    ):
        raise ValueError("average_timeliness_exception_score must match rows")
    expected_max_score = max(
        (row.timeliness_exception_score for row in report.rows),
        default=_ZERO,
    )
    if report.max_timeliness_exception_score != expected_max_score:
        raise ValueError("max_timeliness_exception_score must match rows")
    if report.queue_status != _report_status(report.rows):
        raise ValueError("queue_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_sources(
    sources: Sequence[ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot],
) -> tuple[ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot, ...]:
    if isinstance(sources, (str, bytes)) or not isinstance(sources, Sequence):
        raise ValueError("sources must be a sequence")
    normalized: list[ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot] = []
    for source in sources:
        if type(source) is not ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot:
            raise ValueError(
                "sources must contain "
                "ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot",
            )
        normalized.append(source)
    return tuple(
        sorted(
            normalized,
            key=lambda source: (source.packet_id, source.source_id, source.observed_at),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchPacketSourceTimelinessExceptionQueueRow],
) -> tuple[ResearchPacketSourceTimelinessExceptionQueueRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchPacketSourceTimelinessExceptionQueueRow] = []
    for row in rows:
        if type(row) is not ResearchPacketSourceTimelinessExceptionQueueRow:
            raise ValueError(
                "rows must contain ResearchPacketSourceTimelinessExceptionQueueRow",
            )
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.rank,
                -row.timeliness_exception_score,
                row.packet_id,
                row.source_id,
            ),
        ),
    )


def _normalize_public_payload(
    public_payload: Sequence[
        ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem
    ],
) -> tuple[ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_queue_state(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _QUEUE_STATES:
        raise ValueError(f"{field_name} must be a known queue state")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchPacketSourceTimelinessExceptionQueueReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


__all__ = (
    "DEFAULT_RESEARCH_PACKET_SOURCE_TIMELINESS_EXCEPTION_QUEUE_V2_CONFIG_VERSION",
    "ResearchPacketSourceTimelinessExceptionQueueConfig",
    "ResearchPacketSourceTimelinessExceptionQueuePublicPayloadItem",
    "ResearchPacketSourceTimelinessExceptionQueueReport",
    "ResearchPacketSourceTimelinessExceptionQueueRow",
    "ResearchPacketSourceTimelinessExceptionQueueSourceSnapshot",
    "build_research_packet_source_timeliness_exception_queue_v2_report",
)
