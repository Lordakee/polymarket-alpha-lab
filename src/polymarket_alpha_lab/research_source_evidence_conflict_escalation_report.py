"""Report-only escalation snapshot for conflicting research-source evidence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Sequence


DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONFLICT_ESCALATION_CONFIG_VERSION = (
    "research-source-evidence-conflict-escalation-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DECIMAL_CONTEXT_PRECISION = 64
_SECONDS_PER_DAY = Decimal("86400")
_MICROSECONDS_PER_SECOND = Decimal("1000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_REASON_CODE_SEQUENCE = (
    "high_contradiction",
    "high_authority_conflict",
    "freshness_mismatch",
    "corroboration_gap",
    "low_extraction_confidence",
    "deadline_proximity",
    "manual_review_block",
    "manual_review_watch",
    "evidence_conflict_pass",
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "http",
    "://",
    "text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "live",
)


@dataclass(frozen=True)
class ResearchSourceEvidenceConflictEscalationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONFLICT_ESCALATION_CONFIG_VERSION
    )
    freshness_gap_block_seconds: Decimal = Decimal("3600.000000")
    deadline_proximity_seconds: Decimal = Decimal("3600.000000")
    watch_escalation_score: Decimal = Decimal("0.400000")
    block_escalation_score: Decimal = Decimal("0.700000")
    high_contradiction_threshold: Decimal = Decimal("0.700000")
    high_authority_threshold: Decimal = Decimal("0.700000")
    low_extraction_confidence_threshold: Decimal = Decimal("0.500000")
    contradiction_weight: Decimal = Decimal("0.250000")
    authority_weight: Decimal = Decimal("0.250000")
    freshness_weight: Decimal = Decimal("0.025000")
    corroboration_gap_weight: Decimal = Decimal("0.135000")
    extraction_uncertainty_weight: Decimal = Decimal("0.250000")
    deadline_weight: Decimal = Decimal("0.090000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceConflictEscalationConfig:
            raise TypeError(
                "ResearchSourceEvidenceConflictEscalationConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceConflictEscalationConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceEvidenceConflictEscalationConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONFLICT_ESCALATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "freshness_gap_block_seconds",
            "deadline_proximity_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_escalation_score",
            "block_escalation_score",
            "high_contradiction_threshold",
            "high_authority_threshold",
            "low_extraction_confidence_threshold",
            "contradiction_weight",
            "authority_weight",
            "freshness_weight",
            "corroboration_gap_weight",
            "extraction_uncertainty_weight",
            "deadline_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_escalation_score <= self.watch_escalation_score:
            raise ValueError("block_escalation_score must exceed watch_escalation_score")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class EvidenceConflictSignal:
    case_key: str
    evidence_ref_digest: str
    counter_ref_digest: str
    observed_at: datetime
    deadline_at: datetime | None
    contradiction_severity: Decimal
    primary_authority_score: Decimal
    counter_authority_score: Decimal
    freshness_gap_seconds: Decimal
    corroborating_group_count: Decimal
    conflicting_group_count: Decimal
    extraction_confidence: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not EvidenceConflictSignal:
            raise TypeError("EvidenceConflictSignal does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not EvidenceConflictSignal:
            raise ValueError("signal must be exactly EvidenceConflictSignal")
        _require_public_identifier("case_key", self.case_key)
        _require_sha256_digest("evidence_ref_digest", self.evidence_ref_digest)
        _require_sha256_digest("counter_ref_digest", self.counter_ref_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.deadline_at is not None:
            object.__setattr__(
                self,
                "deadline_at",
                _as_utc("deadline_at", self.deadline_at),
            )
        for field_name in (
            "contradiction_severity",
            "primary_authority_score",
            "counter_authority_score",
            "extraction_confidence",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_gap_seconds",
            _require_nonnegative_decimal(
                "freshness_gap_seconds",
                self.freshness_gap_seconds,
            ),
        )
        for field_name in ("corroborating_group_count", "conflicting_group_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("signal", self)
        _reject_unsafe_public_payload("signal", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceConflictEscalationRow:
    case_key: str
    evidence_ref_digest: str
    counter_ref_digest: str
    observed_at: datetime
    deadline_at: datetime | None
    contradiction_pressure: Decimal
    authority_pressure: Decimal
    freshness_pressure: Decimal
    corroboration_gap_pressure: Decimal
    extraction_uncertainty_pressure: Decimal
    deadline_pressure: Decimal
    escalation_score: Decimal
    escalation_status: str
    manual_review_required: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceConflictEscalationRow:
            raise TypeError(
                "ResearchSourceEvidenceConflictEscalationRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceConflictEscalationRow:
            raise ValueError(
                "row must be exactly ResearchSourceEvidenceConflictEscalationRow",
            )
        _require_public_identifier("case_key", self.case_key)
        _require_sha256_digest("evidence_ref_digest", self.evidence_ref_digest)
        _require_sha256_digest("counter_ref_digest", self.counter_ref_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.deadline_at is not None:
            object.__setattr__(
                self,
                "deadline_at",
                _as_utc("deadline_at", self.deadline_at),
            )
        for field_name in (
            "contradiction_pressure",
            "authority_pressure",
            "freshness_pressure",
            "corroboration_gap_pressure",
            "extraction_uncertainty_pressure",
            "deadline_pressure",
            "escalation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("escalation_status", self.escalation_status)
        _require_bool("manual_review_required", self.manual_review_required)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceEvidenceConflictEscalationReport:
    generated_at: datetime
    config_version: str
    escalation_status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    manual_review_count: Decimal
    max_escalation_score: Decimal
    average_escalation_score: Decimal
    rows: tuple[ResearchSourceEvidenceConflictEscalationRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceEvidenceConflictEscalationReport:
            raise TypeError(
                "ResearchSourceEvidenceConflictEscalationReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceEvidenceConflictEscalationReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceEvidenceConflictEscalationReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONFLICT_ESCALATION_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("escalation_status", self.escalation_status)
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
            "manual_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_escalation_score", "average_escalation_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        _revalidate_report_for_payload(self)
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchSourceEvidenceConflictEscalationReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_source_evidence_conflict_escalation_report(
    signals: Sequence[EvidenceConflictSignal],
    *,
    generated_at: datetime,
    config: ResearchSourceEvidenceConflictEscalationConfig | None = None,
) -> ResearchSourceEvidenceConflictEscalationReport:
    """Build a local, readonly snapshot that escalates evidence conflicts."""

    if config is None:
        config = ResearchSourceEvidenceConflictEscalationConfig()
    if type(config) is not ResearchSourceEvidenceConflictEscalationConfig:
        raise ValueError(
            "config must be a ResearchSourceEvidenceConflictEscalationConfig",
        )
    generated_at = _as_utc("generated_at", generated_at)
    normalized_signals = _normalize_signals(signals)
    for signal in normalized_signals:
        if signal.observed_at > generated_at:
            raise ValueError("signal observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_signal(signal, generated_at, config) for signal in normalized_signals),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "escalation_status": _report_status(rows),
        "case_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "manual_review_count": _decimal_count(
            sum(1 for row in rows if row.manual_review_required),
        ),
        "max_escalation_score": max(
            (row.escalation_score for row in rows),
            default=_ZERO,
        ),
        "average_escalation_score": _average(
            tuple(row.escalation_score for row in rows),
        ),
        "rows": rows,
        "reason_codes": _report_reason_codes(rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceEvidenceConflictEscalationReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_from_signal(
    signal: EvidenceConflictSignal,
    generated_at: datetime,
    config: ResearchSourceEvidenceConflictEscalationConfig,
) -> ResearchSourceEvidenceConflictEscalationRow:
    contradiction_pressure = signal.contradiction_severity
    authority_pressure = max(
        signal.primary_authority_score,
        signal.counter_authority_score,
    )
    freshness_pressure = _clamp_ratio(
        _decimal_divide(
            signal.freshness_gap_seconds,
            config.freshness_gap_block_seconds,
        ),
    )
    corroboration_gap_pressure = (
        _ONE
        if signal.conflicting_group_count > signal.corroborating_group_count
        else _ZERO
    )
    extraction_uncertainty_pressure = _decimal_subtract(
        _ONE,
        signal.extraction_confidence,
    )
    deadline_pressure = _deadline_pressure(signal.deadline_at, generated_at, config)
    escalation_score = _weighted_score(
        contradiction_pressure=contradiction_pressure,
        authority_pressure=authority_pressure,
        freshness_pressure=freshness_pressure,
        corroboration_gap_pressure=corroboration_gap_pressure,
        extraction_uncertainty_pressure=extraction_uncertainty_pressure,
        deadline_pressure=deadline_pressure,
        config=config,
    )
    escalation_status = _row_status(
        escalation_score=escalation_score,
        signal=signal,
        config=config,
        freshness_pressure=freshness_pressure,
        corroboration_gap_pressure=corroboration_gap_pressure,
        deadline_pressure=deadline_pressure,
    )
    reason_codes = _row_reason_codes(
        signal=signal,
        config=config,
        freshness_pressure=freshness_pressure,
        corroboration_gap_pressure=corroboration_gap_pressure,
        deadline_pressure=deadline_pressure,
        escalation_status=escalation_status,
    )
    return ResearchSourceEvidenceConflictEscalationRow(
        case_key=signal.case_key,
        evidence_ref_digest=signal.evidence_ref_digest,
        counter_ref_digest=signal.counter_ref_digest,
        observed_at=signal.observed_at,
        deadline_at=signal.deadline_at,
        contradiction_pressure=contradiction_pressure,
        authority_pressure=authority_pressure,
        freshness_pressure=freshness_pressure,
        corroboration_gap_pressure=corroboration_gap_pressure,
        extraction_uncertainty_pressure=extraction_uncertainty_pressure,
        deadline_pressure=deadline_pressure,
        escalation_score=escalation_score,
        escalation_status=escalation_status,
        manual_review_required=escalation_status != "pass",
        reason_codes=reason_codes,
    )


def _weighted_score(
    *,
    contradiction_pressure: Decimal,
    authority_pressure: Decimal,
    freshness_pressure: Decimal,
    corroboration_gap_pressure: Decimal,
    extraction_uncertainty_pressure: Decimal,
    deadline_pressure: Decimal,
    config: ResearchSourceEvidenceConflictEscalationConfig,
) -> Decimal:
    with localcontext() as context:
        _configure_decimal_context(context)
        score = (
            contradiction_pressure * config.contradiction_weight
            + authority_pressure * config.authority_weight
            + freshness_pressure * config.freshness_weight
            + corroboration_gap_pressure * config.corroboration_gap_weight
            + extraction_uncertainty_pressure * config.extraction_uncertainty_weight
            + deadline_pressure * config.deadline_weight
        )
    return _clamp_ratio(score)


def _deadline_pressure(
    deadline_at: datetime | None,
    generated_at: datetime,
    config: ResearchSourceEvidenceConflictEscalationConfig,
) -> Decimal:
    if deadline_at is None:
        return _ZERO
    seconds_until_deadline = _duration_seconds(deadline_at - generated_at)
    if seconds_until_deadline <= _ZERO:
        return _ONE
    return _clamp_ratio(
        _decimal_subtract(
            _ONE,
            _decimal_divide(seconds_until_deadline, config.deadline_proximity_seconds),
        ),
    )


def _row_reason_codes(
    *,
    signal: EvidenceConflictSignal,
    config: ResearchSourceEvidenceConflictEscalationConfig,
    freshness_pressure: Decimal,
    corroboration_gap_pressure: Decimal,
    deadline_pressure: Decimal,
    escalation_status: str,
) -> tuple[str, ...]:
    authority_pressure = max(
        signal.primary_authority_score,
        signal.counter_authority_score,
    )
    reason_codes: list[str] = []
    if signal.contradiction_severity >= config.high_contradiction_threshold:
        reason_codes.append("high_contradiction")
    if authority_pressure >= config.high_authority_threshold:
        reason_codes.append("high_authority_conflict")
    if freshness_pressure >= Decimal("0.750000"):
        reason_codes.append("freshness_mismatch")
    if corroboration_gap_pressure == _ONE:
        reason_codes.append("corroboration_gap")
    if signal.extraction_confidence <= config.low_extraction_confidence_threshold:
        reason_codes.append("low_extraction_confidence")
    if deadline_pressure >= Decimal("0.750000"):
        reason_codes.append("deadline_proximity")
    if escalation_status == "block":
        reason_codes.append("manual_review_block")
    elif escalation_status == "watch":
        reason_codes.append("manual_review_watch")
    else:
        reason_codes.append("evidence_conflict_pass")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(
    *,
    escalation_score: Decimal,
    signal: EvidenceConflictSignal,
    config: ResearchSourceEvidenceConflictEscalationConfig,
    freshness_pressure: Decimal,
    corroboration_gap_pressure: Decimal,
    deadline_pressure: Decimal,
) -> str:
    if escalation_score >= config.block_escalation_score:
        return "block"
    if escalation_score >= config.watch_escalation_score or _has_watch_escalation_pressure(
        signal=signal,
        config=config,
        freshness_pressure=freshness_pressure,
        corroboration_gap_pressure=corroboration_gap_pressure,
        deadline_pressure=deadline_pressure,
    ):
        return "watch"
    return "pass"


def _has_watch_escalation_pressure(
    *,
    signal: EvidenceConflictSignal,
    config: ResearchSourceEvidenceConflictEscalationConfig,
    freshness_pressure: Decimal,
    corroboration_gap_pressure: Decimal,
    deadline_pressure: Decimal,
) -> bool:
    authority_pressure = max(
        signal.primary_authority_score,
        signal.counter_authority_score,
    )
    return (
        signal.contradiction_severity >= config.high_contradiction_threshold
        or authority_pressure >= config.high_authority_threshold
        or freshness_pressure >= Decimal("0.750000")
        or corroboration_gap_pressure == _ONE
        or signal.extraction_confidence <= config.low_extraction_confidence_threshold
        or deadline_pressure >= Decimal("0.750000")
    )


def _report_status(
    rows: tuple[ResearchSourceEvidenceConflictEscalationRow, ...],
) -> str:
    if any(row.escalation_status == "block" for row in rows):
        return "block"
    if any(row.escalation_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceEvidenceConflictEscalationRow, ...],
) -> tuple[str, ...]:
    codes = {code for row in rows for code in row.reason_codes}
    if not codes:
        codes.add("evidence_conflict_pass")
    return _normalize_reason_codes(tuple(codes))


def _status_count(
    rows: tuple[ResearchSourceEvidenceConflictEscalationRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.escalation_status == status)


def _normalize_signals(
    signals: Sequence[EvidenceConflictSignal],
) -> tuple[EvidenceConflictSignal, ...]:
    if isinstance(signals, (str, bytes)):
        raise ValueError("signals must be a sequence of EvidenceConflictSignal items")
    normalized = tuple(signals)
    for signal in normalized:
        if type(signal) is not EvidenceConflictSignal:
            raise ValueError("signals must contain only EvidenceConflictSignal items")
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchSourceEvidenceConflictEscalationRow],
) -> tuple[ResearchSourceEvidenceConflictEscalationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError(
            "rows must be a sequence of "
            "ResearchSourceEvidenceConflictEscalationRow items",
        )
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchSourceEvidenceConflictEscalationRow:
            raise ValueError(
                "rows must contain only "
                "ResearchSourceEvidenceConflictEscalationRow items",
            )
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(row: ResearchSourceEvidenceConflictEscalationRow) -> tuple[object, ...]:
    deadline_at_key = "" if row.deadline_at is None else row.deadline_at.isoformat()
    return (
        row.case_key,
        row.evidence_ref_digest,
        row.counter_ref_digest,
        row.observed_at.isoformat(),
        deadline_at_key,
        row.contradiction_pressure,
        row.authority_pressure,
        row.freshness_pressure,
        row.corroboration_gap_pressure,
        row.extraction_uncertainty_pressure,
        row.deadline_pressure,
        row.escalation_score,
        row.escalation_status,
        row.manual_review_required,
        row.reason_codes,
    )


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be a sequence of strings")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("unsupported reason_code")
        if reason_code not in seen:
            seen.add(reason_code)
            normalized.append(reason_code)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: _REASON_CODE_SEQUENCE.index(reason_code),
        ),
    )


def _validate_row_consistency(row: ResearchSourceEvidenceConflictEscalationRow) -> None:
    if row.escalation_status == "pass" and row.manual_review_required:
        raise ValueError("pass row must not require manual review")
    if row.escalation_status != "pass" and not row.manual_review_required:
        raise ValueError("watch and block rows must require manual review")
    if row.escalation_status == "pass" and row.reason_codes != ("evidence_conflict_pass",):
        raise ValueError("pass row reason_codes must only include evidence_conflict_pass")
    if row.escalation_status == "watch" and "manual_review_watch" not in row.reason_codes:
        raise ValueError("watch row must include manual_review_watch")
    if row.escalation_status == "block" and "manual_review_block" not in row.reason_codes:
        raise ValueError("block row must include manual_review_block")


def _validate_report_consistency(
    report: ResearchSourceEvidenceConflictEscalationReport,
) -> None:
    rows = report.rows
    if report.case_count != _decimal_count(len(rows)):
        raise ValueError("case_count must equal row count")
    if report.pass_count != _decimal_count(_status_count(rows, "pass")):
        raise ValueError("pass_count must equal pass row count")
    if report.watch_count != _decimal_count(_status_count(rows, "watch")):
        raise ValueError("watch_count must equal watch row count")
    if report.block_count != _decimal_count(_status_count(rows, "block")):
        raise ValueError("block_count must equal block row count")
    if report.manual_review_count != _decimal_count(
        sum(1 for row in rows if row.manual_review_required),
    ):
        raise ValueError("manual_review_count must equal manual-review row count")
    if report.max_escalation_score != max(
        (row.escalation_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_escalation_score must equal max row score")
    if report.average_escalation_score != _average(
        tuple(row.escalation_score for row in rows),
    ):
        raise ValueError("average_escalation_score must equal average row score")
    if report.escalation_status != _report_status(rows):
        raise ValueError("escalation_status must equal aggregate row status")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must equal aggregate row reasons")


def _revalidate_report_for_payload(
    report: ResearchSourceEvidenceConflictEscalationReport,
) -> None:
    if type(report) is not ResearchSourceEvidenceConflictEscalationReport:
        raise ValueError(
            "report must be exactly ResearchSourceEvidenceConflictEscalationReport",
        )
    values = _dataclass_field_values(report)
    values["rows"] = _revalidated_rows_for_payload(report.rows)
    ResearchSourceEvidenceConflictEscalationReport(**values)


def _revalidated_rows_for_payload(
    rows: Sequence[ResearchSourceEvidenceConflictEscalationRow],
) -> tuple[ResearchSourceEvidenceConflictEscalationRow, ...]:
    return tuple(
        ResearchSourceEvidenceConflictEscalationRow(**_dataclass_field_values(row))
        for row in _normalize_rows(rows)
    )


def _dataclass_field_values(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _report_values_without_digest(
    report: ResearchSourceEvidenceConflictEscalationReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: dict[str, object]) -> str:
    ready = _json_ready(values)
    payload = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize_decimal(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON numeric values must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize_decimal(Decimal(value))


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext() as context:
        _configure_decimal_context(context)
        average = sum(values, _ZERO) / Decimal(len(values))
    return _quantize_decimal(average)


def _clamp_ratio(value: Decimal) -> Decimal:
    value = _quantize_decimal(value)
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return value


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO or raw_value > _ONE:
        raise ValueError(f"{name} must be between 0.000000 and 1.000000")
    return _quantize_decimal(raw_value)


def _require_nonnegative_decimal(name: str, value: Decimal) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize_decimal(raw_value)


def _require_nonnegative_whole_decimal(name: str, value: Decimal) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if raw_value != raw_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return _quantize_decimal(raw_value)


def _require_positive_decimal(name: str, value: Decimal) -> Decimal:
    raw_value = _require_raw_decimal(name, value)
    if raw_value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    normalized = _quantize_decimal(raw_value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_decimal(name: str, value: Decimal) -> Decimal:
    return _quantize_decimal(_require_raw_decimal(name, value))


def _require_raw_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _decimal_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext() as context:
        _configure_decimal_context(context)
        return numerator / denominator


def _decimal_subtract(minuend: Decimal, subtrahend: Decimal) -> Decimal:
    with localcontext() as context:
        _configure_decimal_context(context)
        return minuend - subtrahend


def _duration_seconds(delta: timedelta) -> Decimal:
    days = getattr(delta, "days")
    seconds = getattr(delta, "seconds")
    microseconds = getattr(delta, "microseconds")
    with localcontext() as context:
        _configure_decimal_context(context)
        total_seconds = (
            Decimal(days) * _SECONDS_PER_DAY
            + Decimal(seconds)
            + Decimal(microseconds) / _MICROSECONDS_PER_SECOND
        )
    return _quantize_decimal(total_seconds)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext() as context:
        _configure_decimal_context(context)
        normalized = value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    if normalized.is_zero():
        return _ZERO
    return normalized


def _configure_decimal_context(context: Any) -> None:
    context.prec = _DECIMAL_CONTEXT_PRECISION
    context.rounding = ROUND_HALF_UP


def _require_public_identifier(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")


def _require_sha256_digest(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not _SHA256_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 digest")


def _require_bool(name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_status(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_hard_flags(name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{name} readonly must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), allow_json_containers=True)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public surface in {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=True,
            )
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError(f"unsafe public surface in {label}")
    if not allow_json_containers:
        for field in fields(value):  # type: ignore[arg-type]
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"unsafe public surface in {label}")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_EVIDENCE_CONFLICT_ESCALATION_CONFIG_VERSION",
    "EvidenceConflictSignal",
    "ResearchSourceEvidenceConflictEscalationConfig",
    "ResearchSourceEvidenceConflictEscalationReport",
    "ResearchSourceEvidenceConflictEscalationRow",
    "build_research_source_evidence_conflict_escalation_report",
)
