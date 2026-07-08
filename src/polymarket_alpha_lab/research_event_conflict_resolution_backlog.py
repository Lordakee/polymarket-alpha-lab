"""Report-only research event conflict resolution backlog."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_EVENT_CONFLICT_RESOLUTION_BACKLOG_CONFIG_VERSION = (
    "research-event-conflict-resolution-backlog"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_STATUSES = frozenset(("pass", "watch", "block"))
_CONFLICT_TYPES = frozenset(
    (
        "evidence_conflict",
        "team_disagreement",
        "rule_ambiguity",
    ),
)
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source",
    "ref",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommend",
    "settle",
    "settlement",
    "live",
    "auth",
)
_REASON_CODE_SEQUENCE = (
    "no_conflict_backlog",
    "evidence_conflict",
    "team_disagreement",
    "rule_ambiguity",
    "conflict_count_watch",
    "conflict_count_block",
    "severity_watch",
    "severity_block",
)


@dataclass(frozen=True)
class ResearchEventConflictResolutionBacklogConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_CONFLICT_RESOLUTION_BACKLOG_CONFIG_VERSION
    watch_severity_score: Decimal = Decimal("0.250000")
    block_severity_score: Decimal = Decimal("0.800000")
    watch_conflict_count: Decimal = Decimal("1.000000")
    block_conflict_count: Decimal = Decimal("3.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventConflictResolutionBacklogConfig:
            raise TypeError(
                "ResearchEventConflictResolutionBacklogConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventConflictResolutionBacklogConfig:
            raise ValueError(
                "config must be exactly ResearchEventConflictResolutionBacklogConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CONFLICT_RESOLUTION_BACKLOG_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("watch_severity_score", "block_severity_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("watch_conflict_count", "block_conflict_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.watch_severity_score > self.block_severity_score:
            raise ValueError("watch_severity_score must be at most block_severity_score")
        if self.watch_conflict_count > self.block_conflict_count:
            raise ValueError("watch_conflict_count must be at most block_conflict_count")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventConflictResolutionBacklogSignal:
    review_key: str
    conflict_type: str
    conflict_count: Decimal
    severity_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventConflictResolutionBacklogSignal:
            raise TypeError(
                "ResearchEventConflictResolutionBacklogSignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventConflictResolutionBacklogSignal:
            raise ValueError(
                "signal must be exactly ResearchEventConflictResolutionBacklogSignal",
            )
        _require_public_identifier("review_key", self.review_key)
        _require_conflict_type("conflict_type", self.conflict_type)
        object.__setattr__(
            self,
            "conflict_count",
            _require_nonnegative_count_decimal("conflict_count", self.conflict_count),
        )
        object.__setattr__(
            self,
            "severity_score",
            _require_ratio_decimal("severity_score", self.severity_score),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class ResearchEventConflictResolutionBacklogPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventConflictResolutionBacklogPublicPayloadItem:
            raise TypeError(
                "ResearchEventConflictResolutionBacklogPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventConflictResolutionBacklogPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEventConflictResolutionBacklogPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventConflictResolutionBacklogRow:
    review_key: str
    conflict_type: str
    conflict_count: Decimal
    severity_score: Decimal
    public_status: str
    reason_codes: tuple[str, ...]
    first_observed_at: datetime
    latest_observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventConflictResolutionBacklogRow:
            raise TypeError(
                "ResearchEventConflictResolutionBacklogRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventConflictResolutionBacklogRow:
            raise ValueError("row must be exactly ResearchEventConflictResolutionBacklogRow")
        _require_public_identifier("review_key", self.review_key)
        _require_conflict_type("conflict_type", self.conflict_type)
        object.__setattr__(
            self,
            "conflict_count",
            _require_nonnegative_count_decimal("conflict_count", self.conflict_count),
        )
        object.__setattr__(
            self,
            "severity_score",
            _require_ratio_decimal("severity_score", self.severity_score),
        )
        _require_public_status("public_status", self.public_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "first_observed_at",
            _as_utc("first_observed_at", self.first_observed_at),
        )
        object.__setattr__(
            self,
            "latest_observed_at",
            _as_utc("latest_observed_at", self.latest_observed_at),
        )
        if self.first_observed_at > self.latest_observed_at:
            raise ValueError("first_observed_at must be at or before latest_observed_at")
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventConflictResolutionBacklogReport:
    generated_at: datetime
    config_version: str
    public_status: str
    review_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_conflict_count: Decimal
    max_severity_score: Decimal
    rows: tuple[ResearchEventConflictResolutionBacklogRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchEventConflictResolutionBacklogPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventConflictResolutionBacklogReport:
            raise TypeError(
                "ResearchEventConflictResolutionBacklogReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventConflictResolutionBacklogReport:
            raise ValueError(
                "report must be exactly ResearchEventConflictResolutionBacklogReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_CONFLICT_RESOLUTION_BACKLOG_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_public_status("public_status", self.public_status)
        for field_name in ("review_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "total_conflict_count",
            _require_nonnegative_count_decimal(
                "total_conflict_count",
                self.total_conflict_count,
            ),
        )
        object.__setattr__(
            self,
            "max_severity_score",
            _require_ratio_decimal("max_severity_score", self.max_severity_score),
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
            "ResearchEventConflictResolutionBacklogReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_event_conflict_resolution_backlog_report(
    signals: Sequence[ResearchEventConflictResolutionBacklogSignal],
    *,
    generated_at: datetime,
    config: ResearchEventConflictResolutionBacklogConfig | None = None,
    public_payload: Sequence[ResearchEventConflictResolutionBacklogPublicPayloadItem] = (),
) -> ResearchEventConflictResolutionBacklogReport:
    """Build a local, report-only conflict resolution backlog snapshot."""

    if config is None:
        config = ResearchEventConflictResolutionBacklogConfig()
    if type(config) is not ResearchEventConflictResolutionBacklogConfig:
        raise ValueError("config must be a ResearchEventConflictResolutionBacklogConfig")
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at:
            raise ValueError("signal observed_at must not be after generated_at")
    rows = _build_rows(normalized_signals, config)
    payload_items = _normalize_public_payload(public_payload)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "public_status": _report_status(rows),
        "review_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "total_conflict_count": _sum_counts(tuple(row.conflict_count for row in rows)),
        "max_severity_score": max(
            (row.severity_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventConflictResolutionBacklogReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_conflict_resolution_backlog_payload(
    report: ResearchEventConflictResolutionBacklogReport,
) -> dict[str, object]:
    if type(report) is not ResearchEventConflictResolutionBacklogReport:
        raise ValueError("report must be a ResearchEventConflictResolutionBacklogReport")
    return report.payload


def _build_rows(
    signals: tuple[ResearchEventConflictResolutionBacklogSignal, ...],
    config: ResearchEventConflictResolutionBacklogConfig,
) -> tuple[ResearchEventConflictResolutionBacklogRow, ...]:
    grouped: dict[tuple[str, str], list[ResearchEventConflictResolutionBacklogSignal]] = {}
    for signal in signals:
        grouped.setdefault((signal.review_key, signal.conflict_type), []).append(signal)
    rows = [
        _row_for_group(review_key, conflict_type, tuple(items), config)
        for (review_key, conflict_type), items in sorted(grouped.items())
    ]
    return tuple(rows)


def _row_for_group(
    review_key: str,
    conflict_type: str,
    signals: tuple[ResearchEventConflictResolutionBacklogSignal, ...],
    config: ResearchEventConflictResolutionBacklogConfig,
) -> ResearchEventConflictResolutionBacklogRow:
    conflict_count = _sum_counts(tuple(signal.conflict_count for signal in signals))
    severity_score = max((signal.severity_score for signal in signals), default=_ZERO)
    public_status = _row_status(
        conflict_count=conflict_count,
        severity_score=severity_score,
        config=config,
    )
    observed_values = tuple(signal.observed_at for signal in signals)
    return ResearchEventConflictResolutionBacklogRow(
        review_key=review_key,
        conflict_type=conflict_type,
        conflict_count=conflict_count,
        severity_score=severity_score,
        public_status=public_status,
        reason_codes=_row_reason_codes(
            conflict_type=conflict_type,
            conflict_count=conflict_count,
            severity_score=severity_score,
            public_status=public_status,
            config=config,
        ),
        first_observed_at=min(observed_values),
        latest_observed_at=max(observed_values),
    )


def _row_status(
    *,
    conflict_count: Decimal,
    severity_score: Decimal,
    config: ResearchEventConflictResolutionBacklogConfig,
) -> str:
    if conflict_count >= config.block_conflict_count:
        return "block"
    if severity_score >= config.block_severity_score:
        return "block"
    if conflict_count >= config.watch_conflict_count:
        return "watch"
    if severity_score >= config.watch_severity_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    conflict_type: str,
    conflict_count: Decimal,
    severity_score: Decimal,
    public_status: str,
    config: ResearchEventConflictResolutionBacklogConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if public_status == "pass":
        reason_codes.append("no_conflict_backlog")
    else:
        reason_codes.append(conflict_type)
        if conflict_count >= config.block_conflict_count:
            reason_codes.append("conflict_count_block")
        elif conflict_count >= config.watch_conflict_count:
            reason_codes.append("conflict_count_watch")
        if severity_score >= config.block_severity_score:
            reason_codes.append("severity_block")
        elif severity_score >= config.watch_severity_score:
            reason_codes.append("severity_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchEventConflictResolutionBacklogRow, ...]) -> str:
    if any(row.public_status == "block" for row in rows):
        return "block"
    if any(row.public_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventConflictResolutionBacklogRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_conflict_backlog",)
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in reason_codes:
                reason_codes.append(reason_code)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchEventConflictResolutionBacklogRow, ...],
    public_status: str,
) -> int:
    return sum(1 for row in rows if row.public_status == public_status)


def _normalize_signals(
    signals: Sequence[ResearchEventConflictResolutionBacklogSignal],
) -> tuple[ResearchEventConflictResolutionBacklogSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Sequence):
        raise ValueError("signals must be a sequence")
    normalized = tuple(signals)
    for signal in normalized:
        if type(signal) is not ResearchEventConflictResolutionBacklogSignal:
            raise ValueError(
                "signals must contain ResearchEventConflictResolutionBacklogSignal values",
            )
        _require_hard_flags("signal", signal)
        _reject_unsafe_public_payload("signal", signal)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.review_key,
                item.conflict_type,
                item.observed_at,
                item.conflict_count,
                item.severity_score,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchEventConflictResolutionBacklogRow],
) -> tuple[ResearchEventConflictResolutionBacklogRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventConflictResolutionBacklogRow:
            raise ValueError(
                "rows must contain ResearchEventConflictResolutionBacklogRow values",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    return tuple(sorted(normalized, key=lambda row: (row.review_key, row.conflict_type)))


def _normalize_public_payload(
    items: Sequence[ResearchEventConflictResolutionBacklogPublicPayloadItem],
) -> tuple[ResearchEventConflictResolutionBacklogPublicPayloadItem, ...]:
    if isinstance(items, (str, bytes)) or not isinstance(items, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized = tuple(items)
    seen_keys: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchEventConflictResolutionBacklogPublicPayloadItem:
            raise ValueError(
                "public_payload must contain "
                "ResearchEventConflictResolutionBacklogPublicPayloadItem values",
            )
        if item.key in seen_keys:
            raise ValueError("public_payload keys must be unique")
        seen_keys.add(item.key)
        _require_hard_flags("public payload item", item)
        _reject_unsafe_public_payload("public payload item", item)
    return tuple(sorted(normalized, key=lambda item: (item.key, item.value)))


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
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return tuple(
        reason_code for reason_code in _REASON_CODE_SEQUENCE if reason_code in normalized
    )


def _validate_row_consistency(row: ResearchEventConflictResolutionBacklogRow) -> None:
    if row.public_status == "pass" and row.reason_codes != ("no_conflict_backlog",):
        raise ValueError("reason_codes must match public_status")
    if row.public_status != "pass" and "no_conflict_backlog" in row.reason_codes:
        raise ValueError("reason_codes must match public_status")
    if row.public_status != "pass" and row.conflict_type not in row.reason_codes:
        raise ValueError("reason_codes must include conflict_type")


def _validate_report_consistency(
    report: ResearchEventConflictResolutionBacklogReport,
) -> None:
    if report.review_count != _decimal_count(len(report.rows)):
        raise ValueError("review_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")
    if report.total_conflict_count != _sum_counts(
        tuple(row.conflict_count for row in report.rows),
    ):
        raise ValueError("total_conflict_count must match rows")
    if report.max_severity_score != max(
        (row.severity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_severity_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    if len(normalized) > 240:
        raise ValueError(f"{field_name} must be 240 characters or fewer")
    return normalized


def _require_conflict_type(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    if value not in _CONFLICT_TYPES:
        raise ValueError(f"{field_name} must be a known conflict type")


def _require_public_status(field_name: str, value: object) -> None:
    _require_public_identifier(field_name, value)
    if value not in _PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        field_value = getattr(value, field_name, None)
        if type(field_value) is not bool or field_value is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > _ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    return sum(values, _ZERO).quantize(_QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _report_values_without_digest(
    report: ResearchEventConflictResolutionBacklogReport,
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


def _reject_unsafe_public_string(path: str, value: str) -> None:
    lowered = value.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_EVENT_CONFLICT_RESOLUTION_BACKLOG_CONFIG_VERSION",
    "ResearchEventConflictResolutionBacklogConfig",
    "ResearchEventConflictResolutionBacklogPublicPayloadItem",
    "ResearchEventConflictResolutionBacklogReport",
    "ResearchEventConflictResolutionBacklogRow",
    "ResearchEventConflictResolutionBacklogSignal",
    "build_research_event_conflict_resolution_backlog_report",
    "research_event_conflict_resolution_backlog_payload",
)
