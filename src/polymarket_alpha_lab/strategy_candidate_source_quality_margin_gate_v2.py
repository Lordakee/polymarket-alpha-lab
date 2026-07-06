"""Phase 1 paper-only candidate source-quality margin gate."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any, Sequence


DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUALITY_MARGIN_GATE_V2_CONFIG_VERSION = (
    "strategy-candidate-source-quality-margin-gate-v2"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_MINUS_ONE = Decimal("-1.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_SOURCE_KINDS = frozenset(("official", "independent", "weak"))
_GATE_STATUSES = frozenset(("pass", "watch", "blocked"))
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
_NEXT_STEP_BY_STATUS = {
    "pass": "retain_candidate_for_paper_review",
    "watch": "watch_candidate_pending_better_sources",
    "blocked": "block_candidate_until_sources_improve",
}
_REASON_CODE_SEQUENCE = (
    "empty_source_set",
    "insufficient_source_count",
    "weak_source_penalty",
    "official_source_boost",
    "independent_source_boost",
    "insufficient_source_quality_margin",
    "source_quality_margin_watch",
    "source_quality_margin_pass",
)
_DERIVED_VALIDATION_DIGEST_FIELD = "derived_validation_digest"


@dataclass(frozen=True)
class StrategyCandidateSourceQualityMarginGateV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUALITY_MARGIN_GATE_V2_CONFIG_VERSION
    )
    min_source_count: Decimal = Decimal("2.000000")
    min_quality_score: Decimal = Decimal("0.700000")
    min_quality_margin: Decimal = Decimal("0.050000")
    official_source_boost_per_source: Decimal = Decimal("0.080000")
    independent_source_boost_per_source: Decimal = Decimal("0.040000")
    weak_source_penalty_per_source: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateSourceQualityMarginGateV2Config:
            raise TypeError(
                "StrategyCandidateSourceQualityMarginGateV2Config does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateSourceQualityMarginGateV2Config:
            raise ValueError(
                "config must be exactly "
                "StrategyCandidateSourceQualityMarginGateV2Config",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUALITY_MARGIN_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_count_decimal("min_source_count", self.min_source_count),
        )
        for field_name in (
            "min_quality_score",
            "min_quality_margin",
            "official_source_boost_per_source",
            "independent_source_boost_per_source",
            "weak_source_penalty_per_source",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyCandidateSourceQualitySignal:
    candidate_id: str
    source_id: str
    source_kind: str
    observed_at: datetime
    quality_score: Decimal
    public_note: str | None = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateSourceQualitySignal:
            raise TypeError(
                "StrategyCandidateSourceQualitySignal does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateSourceQualitySignal:
            raise ValueError(
                "signal must be exactly StrategyCandidateSourceQualitySignal",
            )
        for field_name in ("candidate_id", "source_id"):
            _require_public_identifier(field_name, getattr(self, field_name))
        _require_source_kind("source_kind", self.source_kind)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "quality_score",
            _require_ratio_decimal("quality_score", self.quality_score),
        )
        object.__setattr__(
            self,
            "public_note",
            _normalize_optional_public_text("public_note", self.public_note),
        )
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class StrategyCandidateSourceQualityPublicPayloadItem:
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateSourceQualityPublicPayloadItem:
            raise TypeError(
                "StrategyCandidateSourceQualityPublicPayloadItem does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateSourceQualityPublicPayloadItem:
            raise ValueError(
                "public payload item must be exactly "
                "StrategyCandidateSourceQualityPublicPayloadItem",
            )
        _require_public_identifier("key", self.key)
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public payload item", self)
        _reject_unsafe_public_payload("public payload item", self)


@dataclass(frozen=True)
class StrategyCandidateSourceQualityMarginGateRow:
    candidate_id: str
    signal_count: Decimal
    required_source_count: Decimal
    official_source_count: Decimal
    independent_source_count: Decimal
    weak_source_count: Decimal
    quality_score_floor: Decimal
    required_margin_score: Decimal
    average_quality_score: Decimal
    official_source_boost: Decimal
    independent_source_boost: Decimal
    weak_source_penalty: Decimal
    adjusted_quality_score: Decimal
    source_quality_margin_score: Decimal
    gate_status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateSourceQualityMarginGateRow:
            raise TypeError(
                "StrategyCandidateSourceQualityMarginGateRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateSourceQualityMarginGateRow:
            raise ValueError(
                "row must be exactly StrategyCandidateSourceQualityMarginGateRow",
            )
        _require_public_identifier("candidate_id", self.candidate_id)
        for field_name in (
            "signal_count",
            "required_source_count",
            "official_source_count",
            "independent_source_count",
            "weak_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.required_source_count <= _ZERO:
            raise ValueError("required_source_count must be positive")
        for field_name in (
            "quality_score_floor",
            "required_margin_score",
            "average_quality_score",
            "official_source_boost",
            "independent_source_boost",
            "weak_source_penalty",
            "adjusted_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_quality_margin_score",
            _require_margin_decimal(
                "source_quality_margin_score",
                self.source_quality_margin_score,
            ),
        )
        _require_gate_status("gate_status", self.gate_status)
        if self.recommended_next_step != _NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyCandidateSourceQualityMarginGateReport:
    generated_at: datetime
    config_version: str
    gate_status: str
    recommended_next_step: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    signal_count: Decimal
    average_source_quality_margin_score: Decimal
    max_weak_source_penalty: Decimal
    rows: tuple[StrategyCandidateSourceQualityMarginGateRow, ...]
    reason_codes: tuple[str, ...]
    public_payload: tuple[StrategyCandidateSourceQualityPublicPayloadItem, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyCandidateSourceQualityMarginGateReport:
            raise TypeError(
                "StrategyCandidateSourceQualityMarginGateReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyCandidateSourceQualityMarginGateReport:
            raise ValueError(
                "report must be exactly StrategyCandidateSourceQualityMarginGateReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUALITY_MARGIN_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_gate_status("gate_status", self.gate_status)
        if self.recommended_next_step != _NEXT_STEP_BY_STATUS[self.gate_status]:
            raise ValueError("recommended_next_step must match gate_status")
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "signal_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_source_quality_margin_score",
            _require_margin_decimal(
                "average_source_quality_margin_score",
                self.average_source_quality_margin_score,
            ),
        )
        object.__setattr__(
            self,
            "max_weak_source_penalty",
            _require_ratio_decimal("max_weak_source_penalty", self.max_weak_source_penalty),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "public_payload",
            _normalize_public_payload(self.public_payload),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")

    @property
    def payload(self) -> dict[str, object]:
        return strategy_candidate_source_quality_margin_gate_v2_payload(self)


def build_strategy_candidate_source_quality_margin_gate_v2(
    signals: Sequence[StrategyCandidateSourceQualitySignal],
    *,
    generated_at: datetime,
    config: StrategyCandidateSourceQualityMarginGateV2Config | None = None,
    public_payload: Sequence[StrategyCandidateSourceQualityPublicPayloadItem] = (),
) -> StrategyCandidateSourceQualityMarginGateReport:
    """Build a local report-only source-quality margin snapshot."""

    if config is None:
        config = StrategyCandidateSourceQualityMarginGateV2Config()
    if type(config) is not StrategyCandidateSourceQualityMarginGateV2Config:
        raise ValueError(
            "config must be a StrategyCandidateSourceQualityMarginGateV2Config",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at:
            raise ValueError("signal observed_at must not be after generated_at")
    payload_items = _normalize_public_payload(public_payload)
    rows = _build_rows(normalized_signals, config)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "gate_status": _report_status(rows),
        "recommended_next_step": _NEXT_STEP_BY_STATUS[_report_status(rows)],
        "candidate_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "blocked_count": _decimal_count(_status_count(rows, "blocked")),
        "signal_count": _decimal_count(len(normalized_signals)),
        "average_source_quality_margin_score": _average_margin(
            tuple(row.source_quality_margin_score for row in rows),
        ),
        "max_weak_source_penalty": max(
            (row.weak_source_penalty for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "public_payload": payload_items,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return StrategyCandidateSourceQualityMarginGateReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def strategy_candidate_source_quality_margin_gate_v2_payload(
    value: StrategyCandidateSourceQualityMarginGateReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is StrategyCandidateSourceQualityMarginGateReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a StrategyCandidateSourceQualityMarginGateReport or dict",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_public_payload_digest(payload)
    return payload


def _build_rows(
    signals: tuple[StrategyCandidateSourceQualitySignal, ...],
    config: StrategyCandidateSourceQualityMarginGateV2Config,
) -> tuple[StrategyCandidateSourceQualityMarginGateRow, ...]:
    grouped: dict[str, list[StrategyCandidateSourceQualitySignal]] = {}
    for signal in signals:
        grouped.setdefault(signal.candidate_id, []).append(signal)
    return tuple(
        _row_for_candidate(candidate_id, tuple(candidate_signals), config)
        for candidate_id, candidate_signals in sorted(grouped.items())
    )


def _row_for_candidate(
    candidate_id: str,
    signals: tuple[StrategyCandidateSourceQualitySignal, ...],
    config: StrategyCandidateSourceQualityMarginGateV2Config,
) -> StrategyCandidateSourceQualityMarginGateRow:
    official_count = _decimal_count(
        len(tuple(signal for signal in signals if signal.source_kind == "official")),
    )
    independent_count = _decimal_count(
        len(tuple(signal for signal in signals if signal.source_kind == "independent")),
    )
    weak_count = _decimal_count(
        len(tuple(signal for signal in signals if signal.source_kind == "weak")),
    )
    average_quality = _average_ratio(tuple(signal.quality_score for signal in signals))
    official_boost = _clamp_ratio(official_count * config.official_source_boost_per_source)
    independent_boost = _clamp_ratio(
        independent_count * config.independent_source_boost_per_source,
    )
    weak_penalty = _clamp_ratio(weak_count * config.weak_source_penalty_per_source)
    adjusted_quality = _clamp_ratio(
        average_quality + official_boost + independent_boost - weak_penalty,
    )
    margin_score = _quantize(adjusted_quality - config.min_quality_score)
    status = _row_status(
        signal_count=_decimal_count(len(signals)),
        required_source_count=config.min_source_count,
        source_quality_margin_score=margin_score,
        required_margin_score=config.min_quality_margin,
    )
    return StrategyCandidateSourceQualityMarginGateRow(
        candidate_id=candidate_id,
        signal_count=_decimal_count(len(signals)),
        required_source_count=config.min_source_count,
        official_source_count=official_count,
        independent_source_count=independent_count,
        weak_source_count=weak_count,
        quality_score_floor=config.min_quality_score,
        required_margin_score=config.min_quality_margin,
        average_quality_score=average_quality,
        official_source_boost=official_boost,
        independent_source_boost=independent_boost,
        weak_source_penalty=weak_penalty,
        adjusted_quality_score=adjusted_quality,
        source_quality_margin_score=margin_score,
        gate_status=status,
        recommended_next_step=_NEXT_STEP_BY_STATUS[status],
        reason_codes=_row_reason_codes(
            signal_count=_decimal_count(len(signals)),
            required_source_count=config.min_source_count,
            official_source_count=official_count,
            independent_source_count=independent_count,
            weak_source_count=weak_count,
            source_quality_margin_score=margin_score,
            required_margin_score=config.min_quality_margin,
        ),
    )


def _row_reason_codes(
    *,
    signal_count: Decimal,
    required_source_count: Decimal,
    official_source_count: Decimal,
    independent_source_count: Decimal,
    weak_source_count: Decimal,
    source_quality_margin_score: Decimal,
    required_margin_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if signal_count == _ZERO:
        reason_codes.append("empty_source_set")
    if signal_count < required_source_count:
        reason_codes.append("insufficient_source_count")
    if weak_source_count > _ZERO:
        reason_codes.append("weak_source_penalty")
    if official_source_count > _ZERO:
        reason_codes.append("official_source_boost")
    if independent_source_count > _ZERO:
        reason_codes.append("independent_source_boost")
    if source_quality_margin_score < _ZERO:
        reason_codes.append("insufficient_source_quality_margin")
    elif source_quality_margin_score < required_margin_score:
        reason_codes.append("source_quality_margin_watch")
    if _row_status(
        signal_count=signal_count,
        required_source_count=required_source_count,
        source_quality_margin_score=source_quality_margin_score,
        required_margin_score=required_margin_score,
    ) == "pass":
        reason_codes.append("source_quality_margin_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    signal_count: Decimal,
    required_source_count: Decimal,
    source_quality_margin_score: Decimal,
    required_margin_score: Decimal,
) -> str:
    if signal_count == _ZERO:
        return "blocked"
    if signal_count < required_source_count:
        return "blocked"
    if source_quality_margin_score < _ZERO:
        return "blocked"
    if source_quality_margin_score < required_margin_score:
        return "watch"
    return "pass"


def _report_status(rows: tuple[StrategyCandidateSourceQualityMarginGateRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.gate_status == "blocked" for row in rows):
        return "blocked"
    if any(row.gate_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyCandidateSourceQualityMarginGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_source_set",)
    reason_codes: list[str] = []
    for code in _REASON_CODE_SEQUENCE:
        if any(code in row.reason_codes for row in rows):
            reason_codes.append(code)
    return tuple(reason_codes)


def _status_count(
    rows: tuple[StrategyCandidateSourceQualityMarginGateRow, ...],
    status: str,
) -> int:
    return len(tuple(row for row in rows if row.gate_status == status))


def _validate_row_consistency(
    row: StrategyCandidateSourceQualityMarginGateRow,
) -> None:
    if (
        row.official_source_count + row.independent_source_count + row.weak_source_count
        != row.signal_count
    ):
        raise ValueError("source kind counts must sum to signal_count")
    expected_adjusted_quality = _clamp_ratio(
        row.average_quality_score
        + row.official_source_boost
        + row.independent_source_boost
        - row.weak_source_penalty,
    )
    if row.adjusted_quality_score != expected_adjusted_quality:
        raise ValueError("adjusted_quality_score must match source quality components")
    expected_margin = _quantize(row.adjusted_quality_score - row.quality_score_floor)
    if row.source_quality_margin_score != expected_margin:
        raise ValueError("source_quality_margin_score must match adjusted score minus floor")
    expected_status = _row_status(
        signal_count=row.signal_count,
        required_source_count=row.required_source_count,
        source_quality_margin_score=row.source_quality_margin_score,
        required_margin_score=row.required_margin_score,
    )
    if row.gate_status != expected_status:
        raise ValueError("gate_status must match source-quality margin rules")
    expected_reason_codes = _row_reason_codes(
        signal_count=row.signal_count,
        required_source_count=row.required_source_count,
        official_source_count=row.official_source_count,
        independent_source_count=row.independent_source_count,
        weak_source_count=row.weak_source_count,
        source_quality_margin_score=row.source_quality_margin_score,
        required_margin_score=row.required_margin_score,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row source-quality margin rules")


def _validate_report_consistency(
    report: StrategyCandidateSourceQualityMarginGateReport,
) -> None:
    if report.candidate_count != _decimal_count(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _decimal_count(_status_count(report.rows, "blocked")):
        raise ValueError("blocked_count must match rows")
    if report.signal_count != sum((row.signal_count for row in report.rows), _ZERO):
        raise ValueError("signal_count must match rows")
    expected_average_margin = _average_margin(
        tuple(row.source_quality_margin_score for row in report.rows),
    )
    if report.average_source_quality_margin_score != expected_average_margin:
        raise ValueError("average_source_quality_margin_score must match rows")
    expected_max_penalty = max(
        (row.weak_source_penalty for row in report.rows),
        default=_ZERO,
    )
    if report.max_weak_source_penalty != expected_max_penalty:
        raise ValueError("max_weak_source_penalty must match rows")
    expected_status = _report_status(report.rows)
    if report.gate_status != expected_status:
        raise ValueError("gate_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_signals(
    signals: Sequence[StrategyCandidateSourceQualitySignal],
) -> tuple[StrategyCandidateSourceQualitySignal, ...]:
    if type(signals) not in (list, tuple):
        raise ValueError("signals must be a list or tuple")
    normalized = tuple(signals)
    for signal in normalized:
        if type(signal) is not StrategyCandidateSourceQualitySignal:
            raise ValueError("signals items must be StrategyCandidateSourceQualitySignal")
        _require_hard_flags("signal", signal)
    return normalized


def _normalize_rows(
    rows: tuple[StrategyCandidateSourceQualityMarginGateRow, ...],
) -> tuple[StrategyCandidateSourceQualityMarginGateRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not StrategyCandidateSourceQualityMarginGateRow:
            raise ValueError("rows items must be StrategyCandidateSourceQualityMarginGateRow")
        _require_hard_flags("row", row)
    candidate_ids = tuple(row.candidate_id for row in normalized)
    if candidate_ids != tuple(sorted(candidate_ids)):
        raise ValueError("rows must be sorted by candidate_id")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("rows candidate_id values must be unique")
    return normalized


def _normalize_public_payload(
    public_payload: Sequence[StrategyCandidateSourceQualityPublicPayloadItem],
) -> tuple[StrategyCandidateSourceQualityPublicPayloadItem, ...]:
    if type(public_payload) not in (list, tuple):
        raise ValueError("public_payload must be a list or tuple")
    normalized = tuple(public_payload)
    for item in normalized:
        if type(item) is not StrategyCandidateSourceQualityPublicPayloadItem:
            raise ValueError(
                "public_payload items must be "
                "StrategyCandidateSourceQualityPublicPayloadItem",
            )
        _require_hard_flags("public payload item", item)
    keys = tuple(item.key for item in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_payload must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_payload keys must be unique")
    return normalized


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of strings") from exc
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        if type(reason_code) is not str or reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_codes must contain known reason codes")
    expected_order = tuple(code for code in _REASON_CODE_SEQUENCE if code in normalized)
    if normalized != expected_order:
        raise ValueError("reason_codes must use canonical ordering")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe detail")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical public text")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} contains unsafe detail")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe detail")
    return value


def _normalize_optional_public_text(field_name: str, value: object) -> str | None:
    if value is None:
        return None
    return _require_public_text(field_name, value)


def _require_source_kind(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _SOURCE_KINDS:
        raise ValueError(f"{field_name} must be official, independent, or weak")


def _require_gate_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _GATE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_margin_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _MINUS_ONE or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between minus one and one")
    return decimal_value


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _clamp_ratio(sum(values, _ZERO) / _decimal_count(len(values)))


def _average_margin(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / _decimal_count(len(values)))


def _clamp_ratio(value: Decimal) -> Decimal:
    return min(max(_quantize(value), _ZERO), _ONE)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.rounding = ROUND_HALF_UP
            return value.quantize(_QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _report_payload_without_digest(
    *,
    generated_at: datetime,
    config_version: str,
    gate_status: str,
    recommended_next_step: str,
    candidate_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    signal_count: Decimal,
    average_source_quality_margin_score: Decimal,
    max_weak_source_penalty: Decimal,
    rows: tuple[StrategyCandidateSourceQualityMarginGateRow, ...],
    reason_codes: tuple[str, ...],
    public_payload: tuple[StrategyCandidateSourceQualityPublicPayloadItem, ...],
    paper_only: bool,
    report_only: bool,
    readonly: bool,
) -> dict[str, object]:
    return {
        "generated_at": _json_ready(generated_at),
        "config_version": config_version,
        "gate_status": gate_status,
        "recommended_next_step": recommended_next_step,
        "candidate_count": _json_ready(candidate_count),
        "pass_count": _json_ready(pass_count),
        "watch_count": _json_ready(watch_count),
        "blocked_count": _json_ready(blocked_count),
        "signal_count": _json_ready(signal_count),
        "average_source_quality_margin_score": _json_ready(
            average_source_quality_margin_score,
        ),
        "max_weak_source_penalty": _json_ready(max_weak_source_penalty),
        "rows": [_row_payload(row) for row in rows],
        "reason_codes": list(reason_codes),
        "public_payload": [_public_payload_item_payload(item) for item in public_payload],
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }


def _row_payload(row: StrategyCandidateSourceQualityMarginGateRow) -> dict[str, object]:
    return {
        "candidate_id": row.candidate_id,
        "signal_count": _json_ready(row.signal_count),
        "required_source_count": _json_ready(row.required_source_count),
        "official_source_count": _json_ready(row.official_source_count),
        "independent_source_count": _json_ready(row.independent_source_count),
        "weak_source_count": _json_ready(row.weak_source_count),
        "quality_score_floor": _json_ready(row.quality_score_floor),
        "required_margin_score": _json_ready(row.required_margin_score),
        "average_quality_score": _json_ready(row.average_quality_score),
        "official_source_boost": _json_ready(row.official_source_boost),
        "independent_source_boost": _json_ready(row.independent_source_boost),
        "weak_source_penalty": _json_ready(row.weak_source_penalty),
        "adjusted_quality_score": _json_ready(row.adjusted_quality_score),
        "source_quality_margin_score": _json_ready(row.source_quality_margin_score),
        "gate_status": row.gate_status,
        "recommended_next_step": row.recommended_next_step,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _public_payload_item_payload(
    item: StrategyCandidateSourceQualityPublicPayloadItem,
) -> dict[str, object]:
    return {
        "key": item.key,
        "value": item.value,
        "paper_only": item.paper_only,
        "report_only": item.report_only,
        "readonly": item.readonly,
    }


def _report_payload(
    report: StrategyCandidateSourceQualityMarginGateReport,
) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        gate_status=report.gate_status,
        recommended_next_step=report.recommended_next_step,
        candidate_count=report.candidate_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        blocked_count=report.blocked_count,
        signal_count=report.signal_count,
        average_source_quality_margin_score=report.average_source_quality_margin_score,
        max_weak_source_penalty=report.max_weak_source_penalty,
        rows=report.rows,
        reason_codes=report.reason_codes,
        public_payload=report.public_payload,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DERIVED_VALIDATION_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_digest(report: StrategyCandidateSourceQualityMarginGateReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "gate_status": report.gate_status,
            "recommended_next_step": report.recommended_next_step,
            "candidate_count": report.candidate_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "blocked_count": report.blocked_count,
            "signal_count": report.signal_count,
            "average_source_quality_margin_score": (
                report.average_source_quality_margin_score
            ),
            "max_weak_source_penalty": report.max_weak_source_penalty,
            "rows": report.rows,
            "reason_codes": report.reason_codes,
            "public_payload": report.public_payload,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: dict[str, object]) -> str:
    payload = _report_payload_without_digest(
        generated_at=_require_mapping_value(values, "generated_at", datetime),
        config_version=_require_mapping_value(values, "config_version", str),
        gate_status=_require_mapping_value(values, "gate_status", str),
        recommended_next_step=_require_mapping_value(values, "recommended_next_step", str),
        candidate_count=_require_mapping_value(values, "candidate_count", Decimal),
        pass_count=_require_mapping_value(values, "pass_count", Decimal),
        watch_count=_require_mapping_value(values, "watch_count", Decimal),
        blocked_count=_require_mapping_value(values, "blocked_count", Decimal),
        signal_count=_require_mapping_value(values, "signal_count", Decimal),
        average_source_quality_margin_score=_require_mapping_value(
            values,
            "average_source_quality_margin_score",
            Decimal,
        ),
        max_weak_source_penalty=_require_mapping_value(
            values,
            "max_weak_source_penalty",
            Decimal,
        ),
        rows=_require_mapping_value(values, "rows", tuple),
        reason_codes=_require_mapping_value(values, "reason_codes", tuple),
        public_payload=_require_mapping_value(values, "public_payload", tuple),
        paper_only=_require_mapping_value(values, "paper_only", bool),
        report_only=_require_mapping_value(values, "report_only", bool),
        readonly=_require_mapping_value(values, "readonly", bool),
    )
    return _digest_payload(payload)


def _require_mapping_value(
    values: dict[str, object],
    key: str,
    expected_type: type,
) -> Any:
    value = values[key]
    if type(value) is not expected_type:
        raise ValueError(f"{key} must be {expected_type.__name__}")
    return value


def _validate_public_payload_digest(payload: dict[str, object]) -> None:
    if _DERIVED_VALIDATION_DIGEST_FIELD not in payload:
        raise ValueError("derived_validation_digest is required")
    _require_digest(
        _DERIVED_VALIDATION_DIGEST_FIELD,
        payload[_DERIVED_VALIDATION_DIGEST_FIELD],
    )
    digest_payload = dict(payload)
    digest_payload.pop(_DERIVED_VALIDATION_DIGEST_FIELD)
    if payload[_DERIVED_VALIDATION_DIGEST_FIELD] != _digest_payload(digest_payload):
        raise ValueError("derived_validation_digest mismatch")


def _digest_payload(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object) -> Any:
    if type(value) is StrategyCandidateSourceQualityMarginGateReport:
        return _report_payload(value)
    if type(value) is StrategyCandidateSourceQualityMarginGateRow:
        return _row_payload(value)
    if type(value) is StrategyCandidateSourceQualityPublicPayloadItem:
        return _public_payload_item_payload(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return _copy_json_object(value)
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    raise ValueError("value is not JSON-ready")


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, nested_value in value.items():
        if type(key) is not str:
            raise ValueError("JSON object keys must be strings")
        copied[key] = _copy_json_value(nested_value)
    return copied


def _copy_json_value(value: object) -> object:
    if type(value) is dict:
        return _copy_json_object(value)
    if type(value) is list:
        return [_copy_json_value(item) for item in value]
    if value is None or type(value) in (str, bool):
        return value
    if isinstance(value, Decimal):
        raise ValueError("JSON payload values must serialize Decimal values as strings")
    if isinstance(value, float) or type(value) is int:
        raise ValueError("JSON payload numeric values must be strings")
    raise ValueError("JSON payload is not JSON-ready")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in (
            StrategyCandidateSourceQualityMarginGateV2Config,
            StrategyCandidateSourceQualitySignal,
            StrategyCandidateSourceQualityPublicPayloadItem,
            StrategyCandidateSourceQualityMarginGateRow,
            StrategyCandidateSourceQualityMarginGateReport,
        ):
            raise ValueError(f"{current_path} must be a supported public dataclass")
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            field_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{current_path} must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{current_path} must be timezone-aware")
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            item_path = f"{current_path}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        if value.strip() != value:
            raise ValueError(f"{current_path} has unsafe public value")
        if "://" in value or "?" in value:
            raise ValueError(f"{current_path} has unsafe public value")
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{current_path} has unsafe public value")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{current_path} must use Decimal-derived string values")
    raise ValueError(f"{current_path} is not JSON-ready")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TERMS)


__all__ = (
    "DEFAULT_STRATEGY_CANDIDATE_SOURCE_QUALITY_MARGIN_GATE_V2_CONFIG_VERSION",
    "StrategyCandidateSourceQualityMarginGateV2Config",
    "StrategyCandidateSourceQualitySignal",
    "StrategyCandidateSourceQualityPublicPayloadItem",
    "StrategyCandidateSourceQualityMarginGateRow",
    "StrategyCandidateSourceQualityMarginGateReport",
    "build_strategy_candidate_source_quality_margin_gate_v2",
    "strategy_candidate_source_quality_margin_gate_v2_payload",
)
