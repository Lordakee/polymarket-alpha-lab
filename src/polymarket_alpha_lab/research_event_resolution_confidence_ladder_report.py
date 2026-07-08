"""Report-only event resolution confidence ladder."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_LADDER_CONFIG_VERSION = (
    "research-event-resolution-confidence-ladder-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_LADDER_STATUSES = frozenset(("pass", "watch", "block"))
_REVIEW_STATUSES = frozenset(("reviewed", "pending", "unreviewed"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "market",
    "question",
    "source",
    "url",
    "text",
    "dsn",
    "table",
    "token",
    "buy",
    "sell",
    "trade",
    "recommend",
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
)
_REASON_CODE_SEQUENCE = (
    "empty_events",
    "official_evidence_gap",
    "alternative_evidence_gap",
    "dispute_risk_watch",
    "dispute_risk_block",
    "timeliness_gap",
    "review_pending_watch",
    "review_unreviewed_block",
    "resolution_confidence_watch",
    "resolution_confidence_pass",
)


@dataclass(frozen=True)
class ResearchEventResolutionConfidenceLadderConfig:
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_LADDER_CONFIG_VERSION
    )
    min_official_evidence_score: Decimal = Decimal("0.650000")
    min_alternative_evidence_score: Decimal = Decimal("0.500000")
    max_dispute_risk_watch: Decimal = Decimal("0.400000")
    max_dispute_risk_block: Decimal = Decimal("0.800000")
    min_freshness_score: Decimal = Decimal("0.600000")
    min_pass_confidence_score: Decimal = Decimal("0.750000")
    official_evidence_weight: Decimal = Decimal("0.500000")
    alternative_evidence_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.200000")
    dispute_risk_penalty_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConfidenceLadderConfig:
            raise TypeError(
                "ResearchEventResolutionConfidenceLadderConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionConfidenceLadderConfig:
            raise ValueError(
                "config must be exactly ResearchEventResolutionConfidenceLadderConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_official_evidence_score",
            "min_alternative_evidence_score",
            "max_dispute_risk_watch",
            "max_dispute_risk_block",
            "min_freshness_score",
            "min_pass_confidence_score",
            "official_evidence_weight",
            "alternative_evidence_weight",
            "freshness_weight",
            "dispute_risk_penalty_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_dispute_risk_watch >= self.max_dispute_risk_block:
            raise ValueError("max_dispute_risk_watch must be below block threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventResolutionConfidenceSignal:
    event_id: str
    official_evidence_score: Decimal
    alternative_evidence_score: Decimal
    dispute_risk_score: Decimal
    freshness_score: Decimal
    review_status: str
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConfidenceSignal:
            raise TypeError(
                "ResearchEventResolutionConfidenceSignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionConfidenceSignal:
            raise ValueError(
                "signal must be exactly ResearchEventResolutionConfidenceSignal",
            )
        _require_public_identifier("event_id", self.event_id)
        for field_name in (
            "official_evidence_score",
            "alternative_evidence_score",
            "dispute_risk_score",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_review_status("review_status", self.review_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class ResearchEventResolutionConfidenceLadderPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConfidenceLadderPublicPayloadItem:
            raise TypeError(
                "ResearchEventResolutionConfidenceLadderPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionConfidenceLadderPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "ResearchEventResolutionConfidenceLadderPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_value("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class ResearchEventResolutionConfidenceLadderRow:
    event_id: str
    official_evidence_score: Decimal
    alternative_evidence_score: Decimal
    dispute_risk_score: Decimal
    freshness_score: Decimal
    review_status: str
    resolution_confidence_score: Decimal
    ladder_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConfidenceLadderRow:
            raise TypeError(
                "ResearchEventResolutionConfidenceLadderRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionConfidenceLadderRow:
            raise ValueError(
                "row must be exactly ResearchEventResolutionConfidenceLadderRow",
            )
        _require_public_identifier("event_id", self.event_id)
        for field_name in (
            "official_evidence_score",
            "alternative_evidence_score",
            "dispute_risk_score",
            "freshness_score",
            "resolution_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_review_status("review_status", self.review_status)
        _require_ladder_status("ladder_status", self.ladder_status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventResolutionConfidenceLadderReport:
    generated_at: datetime
    config_version: str
    ladder_status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_resolution_confidence_score: Decimal
    max_dispute_risk_score: Decimal
    rows: tuple[ResearchEventResolutionConfidenceLadderRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[ResearchEventResolutionConfidenceLadderPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventResolutionConfidenceLadderReport:
            raise TypeError(
                "ResearchEventResolutionConfidenceLadderReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventResolutionConfidenceLadderReport:
            raise ValueError(
                "report must be exactly ResearchEventResolutionConfidenceLadderReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_LADDER_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_ladder_status("ladder_status", self.ladder_status)
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_resolution_confidence_score",
            "max_dispute_risk_score",
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
            "ResearchEventResolutionConfidenceLadderReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_event_resolution_confidence_ladder_report(
    signals: Sequence[ResearchEventResolutionConfidenceSignal],
    *,
    generated_at: datetime,
    config: ResearchEventResolutionConfidenceLadderConfig | None = None,
    public_payload: Sequence[ResearchEventResolutionConfidenceLadderPublicPayloadItem] = (),
) -> ResearchEventResolutionConfidenceLadderReport:
    """Build a local report-only resolution confidence ladder snapshot."""

    if config is None:
        config = ResearchEventResolutionConfidenceLadderConfig()
    if type(config) is not ResearchEventResolutionConfidenceLadderConfig:
        raise ValueError(
            "config must be a ResearchEventResolutionConfidenceLadderConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for item in normalized_signals:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = tuple(_row_for_signal(signal, config) for signal in normalized_signals)
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "ladder_status": _report_status(rows),
        "event_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_resolution_confidence_score": _average(
            tuple(row.resolution_confidence_score for row in rows),
        ),
        "max_dispute_risk_score": max(
            (row.dispute_risk_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventResolutionConfidenceLadderReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_signal(
    signal: ResearchEventResolutionConfidenceSignal,
    config: ResearchEventResolutionConfidenceLadderConfig,
) -> ResearchEventResolutionConfidenceLadderRow:
    confidence_score = _resolution_confidence_score(signal, config)
    ladder_status = _row_status(
        signal,
        confidence_score=confidence_score,
        config=config,
    )
    return ResearchEventResolutionConfidenceLadderRow(
        event_id=signal.event_id,
        official_evidence_score=signal.official_evidence_score,
        alternative_evidence_score=signal.alternative_evidence_score,
        dispute_risk_score=signal.dispute_risk_score,
        freshness_score=signal.freshness_score,
        review_status=signal.review_status,
        resolution_confidence_score=confidence_score,
        ladder_status=ladder_status,
        reason_codes=_row_reason_codes(
            signal,
            confidence_score=confidence_score,
            ladder_status=ladder_status,
            config=config,
        ),
    )


def _resolution_confidence_score(
    signal: ResearchEventResolutionConfidenceSignal,
    config: ResearchEventResolutionConfidenceLadderConfig,
) -> Decimal:
    return _clamp_ratio(
        (signal.official_evidence_score * config.official_evidence_weight)
        + (signal.alternative_evidence_score * config.alternative_evidence_weight)
        + (signal.freshness_score * config.freshness_weight)
        - (signal.dispute_risk_score * config.dispute_risk_penalty_weight),
    )


def _row_status(
    signal: ResearchEventResolutionConfidenceSignal,
    *,
    confidence_score: Decimal,
    config: ResearchEventResolutionConfidenceLadderConfig,
) -> str:
    if (
        signal.dispute_risk_score >= config.max_dispute_risk_block
        or signal.review_status == "unreviewed"
    ):
        return "block"
    if (
        signal.official_evidence_score >= config.min_official_evidence_score
        and signal.alternative_evidence_score >= config.min_alternative_evidence_score
        and signal.dispute_risk_score <= config.max_dispute_risk_watch
        and signal.freshness_score >= config.min_freshness_score
        and signal.review_status == "reviewed"
        and confidence_score >= config.min_pass_confidence_score
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    signal: ResearchEventResolutionConfidenceSignal,
    *,
    confidence_score: Decimal,
    ladder_status: str,
    config: ResearchEventResolutionConfidenceLadderConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal.official_evidence_score < config.min_official_evidence_score:
        reason_codes.append("official_evidence_gap")
    if signal.alternative_evidence_score < config.min_alternative_evidence_score:
        reason_codes.append("alternative_evidence_gap")
    if signal.dispute_risk_score >= config.max_dispute_risk_block:
        reason_codes.append("dispute_risk_block")
    elif signal.dispute_risk_score > config.max_dispute_risk_watch:
        reason_codes.append("dispute_risk_watch")
    if signal.freshness_score < config.min_freshness_score:
        reason_codes.append("timeliness_gap")
    if signal.review_status == "pending":
        reason_codes.append("review_pending_watch")
    if signal.review_status == "unreviewed":
        reason_codes.append("review_unreviewed_block")
    if ladder_status == "pass":
        reason_codes.append("resolution_confidence_pass")
    elif ladder_status == "watch" and confidence_score < config.min_pass_confidence_score:
        reason_codes.append("resolution_confidence_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(
    rows: tuple[ResearchEventResolutionConfidenceLadderRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.ladder_status == "block" for row in rows):
        return "block"
    if any(row.ladder_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchEventResolutionConfidenceLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_events",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchEventResolutionConfidenceLadderRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.ladder_status == status)


def _validate_row_consistency(row: ResearchEventResolutionConfidenceLadderRow) -> None:
    if row.ladder_status == "pass" and "resolution_confidence_pass" not in row.reason_codes:
        raise ValueError("pass rows must include resolution_confidence_pass")
    if row.ladder_status != "pass" and "resolution_confidence_pass" in row.reason_codes:
        raise ValueError("non-pass rows must not include resolution_confidence_pass")
    if row.ladder_status == "block" and not (
        "dispute_risk_block" in row.reason_codes
        or "review_unreviewed_block" in row.reason_codes
    ):
        raise ValueError("block rows must identify a block reason")


def _validate_report_consistency(
    report: ResearchEventResolutionConfidenceLadderReport,
) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_resolution_confidence_score != _average(
        tuple(row.resolution_confidence_score for row in report.rows),
    ):
        raise ValueError("average_resolution_confidence_score must match rows")
    expected_max_risk = max((row.dispute_risk_score for row in report.rows), default=_ZERO)
    if report.max_dispute_risk_score != expected_max_risk:
        raise ValueError("max_dispute_risk_score must match rows")
    if report.ladder_status != _report_status(report.rows):
        raise ValueError("ladder_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_signals(
    signals: Sequence[ResearchEventResolutionConfidenceSignal],
) -> tuple[ResearchEventResolutionConfidenceSignal, ...]:
    if isinstance(signals, (str, bytes)) or not isinstance(signals, Sequence):
        raise ValueError("signals must be a sequence")
    normalized: list[ResearchEventResolutionConfidenceSignal] = []
    for item in signals:
        if type(item) is not ResearchEventResolutionConfidenceSignal:
            raise ValueError(
                "signals items must be ResearchEventResolutionConfidenceSignal",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.event_id,
                item.observed_at,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchEventResolutionConfidenceLadderRow],
) -> tuple[ResearchEventResolutionConfidenceLadderRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchEventResolutionConfidenceLadderRow] = []
    for row in rows:
        if type(row) is not ResearchEventResolutionConfidenceLadderRow:
            raise ValueError(
                "rows must contain ResearchEventResolutionConfidenceLadderRow",
            )
        normalized.append(row)
    return tuple(sorted(normalized, key=lambda row: row.event_id))


def _normalize_public_payload(
    public_payload: Sequence[ResearchEventResolutionConfidenceLadderPublicPayloadItem],
) -> tuple[ResearchEventResolutionConfidenceLadderPublicPayloadItem, ...]:
    if isinstance(public_payload, (str, bytes)) or not isinstance(public_payload, Sequence):
        raise ValueError("public_payload must be a sequence")
    normalized: list[ResearchEventResolutionConfidenceLadderPublicPayloadItem] = []
    for item in public_payload:
        if type(item) is not ResearchEventResolutionConfidenceLadderPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "ResearchEventResolutionConfidenceLadderPublicPayloadItem",
            )
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: item.key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_value(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public value")
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


def _require_ladder_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _LADDER_STATUSES:
        raise ValueError(f"{field_name} must be a known ladder status")
    return value


def _require_review_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _REVIEW_STATUSES:
        raise ValueError(f"{field_name} must be a known review status")
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


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
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
    report: ResearchEventResolutionConfidenceLadderReport,
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
    "DEFAULT_RESEARCH_EVENT_RESOLUTION_CONFIDENCE_LADDER_CONFIG_VERSION",
    "ResearchEventResolutionConfidenceLadderConfig",
    "ResearchEventResolutionConfidenceLadderPublicPayloadItem",
    "ResearchEventResolutionConfidenceLadderReport",
    "ResearchEventResolutionConfidenceLadderRow",
    "ResearchEventResolutionConfidenceSignal",
    "build_research_event_resolution_confidence_ladder_report",
)
