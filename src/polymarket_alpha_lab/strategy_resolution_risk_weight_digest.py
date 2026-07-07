"""Paper-only reducer for strategy resolution-risk weights."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256


__all__ = (
    "StrategyResolutionRiskWeightCandidate",
    "StrategyResolutionRiskWeightDigestConfig",
    "StrategyResolutionRiskWeightDigestReport",
    "StrategyResolutionRiskWeightDigestRow",
    "StrategyResolutionRiskWeightReasonCodeCount",
    "build_strategy_resolution_risk_weight_digest",
    "strategy_resolution_risk_weight_digest_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-resolution-risk-weight-digest-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)


def _term(*parts: str) -> str:
    return "".join(parts)


ROW_STATUS_VALUES = ("pass", "watch", "block")
REPORT_STATUS_VALUES = ("pass", "watch", "blocked")
STATUS_SORT_PRIORITY = {"pass": 0, "watch": 1, "block": 2}

EMPTY_REASON_CODE = "strategy_resolution_risk_weight_digest_empty"
PASS_REASON_CODE = "strategy_resolution_risk_weight_pass"
WATCH_REASON_CODE = "strategy_resolution_risk_weight_watch"
BLOCK_REASON_CODE = "strategy_resolution_risk_weight_block"
RULE_AMBIGUITY_HIGH_REASON_CODE = "rule_ambiguity_high"
RULE_AMBIGUITY_CONTAINED_REASON_CODE = "rule_ambiguity_contained"
SOURCE_AUTHORITY_LOW_REASON_CODE = "source_authority_low"
SOURCE_AUTHORITY_STRONG_REASON_CODE = "source_authority_strong"
DISPUTE_PRESSURE_HIGH_REASON_CODE = "dispute_pressure_high"
DISPUTE_PRESSURE_CONTAINED_REASON_CODE = "dispute_pressure_contained"
EVIDENCE_QUORUM_LOW_REASON_CODE = "evidence_quorum_low"
EVIDENCE_QUORUM_MET_REASON_CODE = "evidence_quorum_met"
ACKNOWLEDGEMENT_LAG_HIGH_REASON_CODE = "acknowledgement_lag_high"
ACKNOWLEDGEMENT_LAG_CONTAINED_REASON_CODE = "acknowledgement_lag_contained"
SETTLEMENT_DELAY_HIGH_REASON_CODE = "settlement_delay_high"
SETTLEMENT_DELAY_CONTAINED_REASON_CODE = "settlement_delay_contained"

TERMINAL_REASON_CODES = (
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    BLOCK_REASON_CODE,
)
QUALITY_REASON_CODES = (
    RULE_AMBIGUITY_HIGH_REASON_CODE,
    RULE_AMBIGUITY_CONTAINED_REASON_CODE,
    SOURCE_AUTHORITY_LOW_REASON_CODE,
    SOURCE_AUTHORITY_STRONG_REASON_CODE,
    DISPUTE_PRESSURE_HIGH_REASON_CODE,
    DISPUTE_PRESSURE_CONTAINED_REASON_CODE,
    EVIDENCE_QUORUM_LOW_REASON_CODE,
    EVIDENCE_QUORUM_MET_REASON_CODE,
    ACKNOWLEDGEMENT_LAG_HIGH_REASON_CODE,
    ACKNOWLEDGEMENT_LAG_CONTAINED_REASON_CODE,
    SETTLEMENT_DELAY_HIGH_REASON_CODE,
    SETTLEMENT_DELAY_CONTAINED_REASON_CODE,
)
ALL_REASON_CODES = (
    EMPTY_REASON_CODE,
    *TERMINAL_REASON_CODES,
    *QUALITY_REASON_CODES,
)
REPORT_REASON_PRIORITY = (
    PASS_REASON_CODE,
    WATCH_REASON_CODE,
    BLOCK_REASON_CODE,
    RULE_AMBIGUITY_HIGH_REASON_CODE,
    SOURCE_AUTHORITY_LOW_REASON_CODE,
    DISPUTE_PRESSURE_HIGH_REASON_CODE,
    EVIDENCE_QUORUM_LOW_REASON_CODE,
    ACKNOWLEDGEMENT_LAG_HIGH_REASON_CODE,
    SETTLEMENT_DELAY_HIGH_REASON_CODE,
    EMPTY_REASON_CODE,
)
SENSITIVE_REFERENCE_TOKENS = (
    _term("api", "_key"),
    "bearer",
    "dsn",
    "key",
    "password",
    _term("priv", "ate"),
    _term("sec", "ret"),
    _term("tok", "en"),
    _term("wal", "let"),
)
UNSAFE_REFERENCE_TOKENS = (
    _term("au", "thor", "ization"),
    _term("/", "au", "th"),
    _term("au", "th", "="),
    _term("au", "th", ":"),
    _term("au", "th", "_"),
    _term("bro", "ker"),
    _term("or", "der"),
    _term("can", "cel"),
    _term("rep", "lace"),
    _term("sig", "n"),
    _term("tra", "de"),
)
PUBLIC_STRING_UNSAFE_TOKENS = (
    _term("api", "_key"),
    "bearer",
    "dsn",
    "password",
    _term("priv", "ate"),
    _term("sec", "ret"),
    _term("tok", "en"),
    _term("wal", "let"),
    *UNSAFE_REFERENCE_TOKENS,
)


@dataclass(frozen=True)
class StrategyResolutionRiskWeightDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    max_acknowledgement_lag_seconds: Decimal = Decimal("21600.000000")
    max_settlement_delay_seconds: Decimal = Decimal("86400.000000")
    min_pass_resolution_weight: Decimal = Decimal("0.700000")
    min_watch_resolution_weight: Decimal = Decimal("0.400000")
    min_source_authority: Decimal = Decimal("0.600000")
    min_evidence_quorum: Decimal = Decimal("0.600000")
    max_rule_ambiguity: Decimal = Decimal("0.300000")
    max_dispute_pressure: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "max_acknowledgement_lag_seconds",
            "max_settlement_delay_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_resolution_weight",
            "min_watch_resolution_weight",
            "min_source_authority",
            "min_evidence_quorum",
            "max_rule_ambiguity",
            "max_dispute_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_pass_resolution_weight < self.min_watch_resolution_weight:
            raise ValueError("min_pass_resolution_weight must not be below watch threshold")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyResolutionRiskWeightCandidate:
    strategy_id: str
    candidate_id: str
    market_slug: str
    source_reference: str
    observed_at: datetime
    rule_ambiguity: Decimal
    source_authority: Decimal
    dispute_pressure: Decimal
    evidence_quorum: Decimal
    acknowledgement_lag_seconds: Decimal
    settlement_delay_seconds: Decimal
    base_strategy_weight: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("strategy_id", self.strategy_id)
        _require_public_string("candidate_id", self.candidate_id)
        _require_public_string("market_slug", self.market_slug)
        _require_canonical_string("source_reference", self.source_reference)
        object.__setattr__(
            self,
            "source_reference",
            _redacted_reference(self.source_reference),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "rule_ambiguity",
            "source_authority",
            "dispute_pressure",
            "evidence_quorum",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "acknowledgement_lag_seconds",
            "settlement_delay_seconds",
            "base_strategy_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_safety_flags("candidate", self)


@dataclass(frozen=True)
class StrategyResolutionRiskWeightDigestRow:
    strategy_id: str
    candidate_id: str
    market_slug: str
    redacted_source_reference: str
    observed_at: datetime
    rule_ambiguity: Decimal
    source_authority: Decimal
    dispute_pressure: Decimal
    evidence_quorum: Decimal
    acknowledgement_lag_seconds: Decimal
    settlement_delay_seconds: Decimal
    base_strategy_weight: Decimal
    resolution_quality_score: Decimal
    resolution_risk_weight: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_string("strategy_id", self.strategy_id)
        _require_public_string("candidate_id", self.candidate_id)
        _require_public_string("market_slug", self.market_slug)
        _require_public_string("redacted_source_reference", self.redacted_source_reference)
        _require_redacted_reference(self.redacted_source_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "rule_ambiguity",
            "source_authority",
            "dispute_pressure",
            "evidence_quorum",
            "resolution_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "acknowledgement_lag_seconds",
            "settlement_delay_seconds",
            "base_strategy_weight",
            "resolution_risk_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUS_VALUES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _require_safety_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class StrategyResolutionRiskWeightReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        if self.reason_code in TERMINAL_REASON_CODES or self.reason_code == EMPTY_REASON_CODE:
            raise ValueError("reason_code count must use risk reason codes")
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count_decimal("count", self.count),
        )
        _require_safety_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyResolutionRiskWeightDigestReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_base_strategy_weight: Decimal
    total_resolution_risk_weight: Decimal
    average_resolution_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyResolutionRiskWeightReasonCodeCount, ...]
    rows: tuple[StrategyResolutionRiskWeightDigestRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_base_strategy_weight",
            "total_resolution_risk_weight",
            "average_resolution_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUS_VALUES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _normalize_sha256(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _require_safety_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)


def build_strategy_resolution_risk_weight_digest(
    candidates: Iterable[object],
    *,
    config: StrategyResolutionRiskWeightDigestConfig,
    generated_at: datetime,
) -> StrategyResolutionRiskWeightDigestReport:
    if type(config) is not StrategyResolutionRiskWeightDigestConfig:
        raise ValueError("config must be a StrategyResolutionRiskWeightDigestConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_safety_flags("config", config)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_row_from_candidate(candidate, config=config) for candidate in source_candidates),
            key=_row_sort_key,
        ),
    )
    return StrategyResolutionRiskWeightDigestReport(
        generated_at=generated_at,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_base_strategy_weight=_sum_decimal(row.base_strategy_weight for row in rows),
        total_resolution_risk_weight=_sum_decimal(
            row.resolution_risk_weight for row in rows
        ),
        average_resolution_quality_score=_average_resolution_quality_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_resolution_risk_weight_digest_payload(
    report: StrategyResolutionRiskWeightDigestReport,
) -> dict[str, object]:
    if type(report) is not StrategyResolutionRiskWeightDigestReport:
        raise ValueError("report must be a StrategyResolutionRiskWeightDigestReport")
    _require_safety_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _validate_report(report)
    payload = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _count_payload(report.candidate_count),
        "pass_count": _count_payload(report.pass_count),
        "watch_count": _count_payload(report.watch_count),
        "block_count": _count_payload(report.block_count),
        "total_base_strategy_weight": _decimal_payload(report.total_base_strategy_weight),
        "total_resolution_risk_weight": _decimal_payload(
            report.total_resolution_risk_weight,
        ),
        "average_resolution_quality_score": _decimal_payload(
            report.average_resolution_quality_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "derived_validation_digest": report.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload("public payload", payload)
    return payload


def _reason_code_count_payload(
    row: StrategyResolutionRiskWeightReasonCodeCount,
) -> dict[str, object]:
    _require_safety_flags("reason_code_count", row)
    _reject_unsafe_public_payload("reason_code_count", row)
    return {
        "reason_code": row.reason_code,
        "count": _count_payload(row.count),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: StrategyResolutionRiskWeightDigestRow) -> dict[str, object]:
    _require_safety_flags("row", row)
    _validate_row(row)
    _reject_unsafe_public_payload("row", row)
    return {
        "strategy_id": row.strategy_id,
        "candidate_id": row.candidate_id,
        "market_slug": row.market_slug,
        "redacted_source_reference": row.redacted_source_reference,
        "observed_at": row.observed_at.isoformat(),
        "rule_ambiguity": _decimal_payload(row.rule_ambiguity),
        "source_authority": _decimal_payload(row.source_authority),
        "dispute_pressure": _decimal_payload(row.dispute_pressure),
        "evidence_quorum": _decimal_payload(row.evidence_quorum),
        "acknowledgement_lag_seconds": _decimal_payload(
            row.acknowledgement_lag_seconds,
        ),
        "settlement_delay_seconds": _decimal_payload(row.settlement_delay_seconds),
        "base_strategy_weight": _decimal_payload(row.base_strategy_weight),
        "resolution_quality_score": _decimal_payload(row.resolution_quality_score),
        "resolution_risk_weight": _decimal_payload(row.resolution_risk_weight),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "derived_validation_digest": row.derived_validation_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_candidate(
    candidate: StrategyResolutionRiskWeightCandidate,
    *,
    config: StrategyResolutionRiskWeightDigestConfig,
) -> StrategyResolutionRiskWeightDigestRow:
    resolution_quality_score = _resolution_quality_score(candidate, config=config)
    resolution_risk_weight = _multiply_decimal(
        candidate.base_strategy_weight,
        resolution_quality_score,
    )
    status, terminal_reason = _status_and_reason(
        resolution_risk_weight=resolution_risk_weight,
        candidate=candidate,
        config=config,
    )
    return StrategyResolutionRiskWeightDigestRow(
        strategy_id=candidate.strategy_id,
        candidate_id=candidate.candidate_id,
        market_slug=candidate.market_slug,
        redacted_source_reference=candidate.source_reference,
        observed_at=candidate.observed_at,
        rule_ambiguity=candidate.rule_ambiguity,
        source_authority=candidate.source_authority,
        dispute_pressure=candidate.dispute_pressure,
        evidence_quorum=candidate.evidence_quorum,
        acknowledgement_lag_seconds=candidate.acknowledgement_lag_seconds,
        settlement_delay_seconds=candidate.settlement_delay_seconds,
        base_strategy_weight=candidate.base_strategy_weight,
        resolution_quality_score=resolution_quality_score,
        resolution_risk_weight=resolution_risk_weight,
        status=status,
        reason_codes=_normalize_reason_codes(
            (
                terminal_reason,
                *_risk_reason_codes(candidate, config=config),
            ),
            require_nonempty=True,
        ),
    )


def _resolution_quality_score(
    candidate: StrategyResolutionRiskWeightCandidate,
    *,
    config: StrategyResolutionRiskWeightDigestConfig,
) -> Decimal:
    acknowledgement_quality = _delay_quality(
        candidate.acknowledgement_lag_seconds,
        max_seconds=config.max_acknowledgement_lag_seconds,
    )
    settlement_quality = _delay_quality(
        candidate.settlement_delay_seconds,
        max_seconds=config.max_settlement_delay_seconds,
    )
    with localcontext(DECIMAL_CONTEXT):
        quality = (
            ((ONE - candidate.rule_ambiguity) * Decimal("0.220000"))
            + (candidate.source_authority * Decimal("0.220000"))
            + ((ONE - candidate.dispute_pressure) * Decimal("0.180000"))
            + (candidate.evidence_quorum * Decimal("0.180000"))
            + (acknowledgement_quality * Decimal("0.100000"))
            + (settlement_quality * Decimal("0.100000"))
        )
    return _normalize_probability_decimal("resolution_quality_score", quality)


def _delay_quality(value: Decimal, *, max_seconds: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        if value <= max_seconds:
            quality = ONE - ((value / max_seconds) * Decimal("0.500000"))
            return _normalize_probability_decimal("delay_quality", quality)
        pressure = (value - max_seconds) / max_seconds
        if pressure > Decimal("12.000000"):
            pressure = Decimal("12.000000")
        quality = Decimal("0.500000") / (ONE + pressure)
        return _normalize_probability_decimal("delay_quality", quality)


def _status_and_reason(
    *,
    resolution_risk_weight: Decimal,
    candidate: StrategyResolutionRiskWeightCandidate,
    config: StrategyResolutionRiskWeightDigestConfig,
) -> tuple[str, str]:
    if (
        resolution_risk_weight < config.min_watch_resolution_weight
        or candidate.rule_ambiguity > config.max_rule_ambiguity
        or candidate.source_authority < config.min_source_authority
        or candidate.dispute_pressure > config.max_dispute_pressure
        or candidate.evidence_quorum < config.min_evidence_quorum
        or candidate.acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds
        or candidate.settlement_delay_seconds > config.max_settlement_delay_seconds
    ):
        if (
            candidate.rule_ambiguity > config.max_rule_ambiguity
            or candidate.source_authority < config.min_source_authority
            or candidate.dispute_pressure > config.max_dispute_pressure
            or candidate.evidence_quorum < config.min_evidence_quorum
        ):
            return "block", BLOCK_REASON_CODE
        if resolution_risk_weight < config.min_watch_resolution_weight:
            return "block", BLOCK_REASON_CODE
        return "watch", WATCH_REASON_CODE
    if resolution_risk_weight >= config.min_pass_resolution_weight:
        return "pass", PASS_REASON_CODE
    return "watch", WATCH_REASON_CODE


def _risk_reason_codes(
    candidate: StrategyResolutionRiskWeightCandidate,
    *,
    config: StrategyResolutionRiskWeightDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.rule_ambiguity > config.max_rule_ambiguity:
        reason_codes.append(RULE_AMBIGUITY_HIGH_REASON_CODE)
    else:
        reason_codes.append(RULE_AMBIGUITY_CONTAINED_REASON_CODE)
    if candidate.source_authority < config.min_source_authority:
        reason_codes.append(SOURCE_AUTHORITY_LOW_REASON_CODE)
    else:
        reason_codes.append(SOURCE_AUTHORITY_STRONG_REASON_CODE)
    if candidate.dispute_pressure > config.max_dispute_pressure:
        reason_codes.append(DISPUTE_PRESSURE_HIGH_REASON_CODE)
    else:
        reason_codes.append(DISPUTE_PRESSURE_CONTAINED_REASON_CODE)
    if candidate.evidence_quorum < config.min_evidence_quorum:
        reason_codes.append(EVIDENCE_QUORUM_LOW_REASON_CODE)
    else:
        reason_codes.append(EVIDENCE_QUORUM_MET_REASON_CODE)
    if candidate.acknowledgement_lag_seconds > config.max_acknowledgement_lag_seconds:
        reason_codes.append(ACKNOWLEDGEMENT_LAG_HIGH_REASON_CODE)
    else:
        reason_codes.append(ACKNOWLEDGEMENT_LAG_CONTAINED_REASON_CODE)
    if candidate.settlement_delay_seconds > config.max_settlement_delay_seconds:
        reason_codes.append(SETTLEMENT_DELAY_HIGH_REASON_CODE)
    else:
        reason_codes.append(SETTLEMENT_DELAY_CONTAINED_REASON_CODE)
    return tuple(reason_codes)


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[StrategyResolutionRiskWeightCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    normalized = tuple(_candidate_from_supplied_row(row) for row in rows)
    seen_candidate_ids: set[str] = set()
    for row in normalized:
        if row.candidate_id in seen_candidate_ids:
            raise ValueError("duplicate candidate_id")
        seen_candidate_ids.add(row.candidate_id)
    return normalized


def _candidate_from_supplied_row(row: object) -> StrategyResolutionRiskWeightCandidate:
    if type(row) is StrategyResolutionRiskWeightCandidate:
        _require_safety_flags("candidate", row)
        return row
    raise ValueError("candidates must contain StrategyResolutionRiskWeightCandidate")


def _normalize_rows(value: object) -> tuple[StrategyResolutionRiskWeightDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyResolutionRiskWeightDigestRow:
            raise ValueError("rows must contain StrategyResolutionRiskWeightDigestRow")
        _require_safety_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyResolutionRiskWeightReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen_reason_codes: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in rows:
        if type(row) is not StrategyResolutionRiskWeightReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StrategyResolutionRiskWeightReasonCodeCount",
            )
        _require_safety_flags("reason_code_count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must be deterministically sorted")
        previous_key = key
        seen_reason_codes.add(row.reason_code)
    return rows


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
    return reason_codes


def _row_sort_key(
    row: StrategyResolutionRiskWeightDigestRow,
) -> tuple[int, Decimal, Decimal, str, str, str]:
    return (
        STATUS_SORT_PRIORITY[row.status],
        -row.resolution_risk_weight,
        -row.resolution_quality_score,
        row.strategy_id,
        row.candidate_id,
        row.market_slug,
    )


def _status_count(
    rows: tuple[StrategyResolutionRiskWeightDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average_resolution_quality_score(
    rows: tuple[StrategyResolutionRiskWeightDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _ratio_decimal(
        _sum_decimal(row.resolution_quality_score for row in rows),
        _count_decimal(len(rows)),
    )


def _report_status(rows: tuple[StrategyResolutionRiskWeightDigestRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows) or not rows:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyResolutionRiskWeightDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    return tuple(reason_code for reason_code in REPORT_REASON_PRIORITY if reason_code in observed)


def _reason_code_counts(
    rows: tuple[StrategyResolutionRiskWeightDigestRow, ...],
) -> tuple[StrategyResolutionRiskWeightReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    excluded = set(TERMINAL_REASON_CODES) | {EMPTY_REASON_CODE}
    for row in rows:
        counts.update(
            reason_code for reason_code in row.reason_codes if reason_code not in excluded
        )
    return tuple(
        StrategyResolutionRiskWeightReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
        if reason_code.endswith("_high") or reason_code.endswith("_low")
    )


def _validate_row(row: StrategyResolutionRiskWeightDigestRow) -> None:
    if row.resolution_risk_weight != _multiply_decimal(
        row.base_strategy_weight,
        row.resolution_quality_score,
    ):
        raise ValueError("resolution_risk_weight must match base weight and quality score")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyResolutionRiskWeightDigestReport) -> None:
    for row in report.rows:
        _validate_row(row)
        _require_safety_flags("row", row)
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.total_base_strategy_weight != _sum_decimal(
        row.base_strategy_weight for row in report.rows
    ):
        raise ValueError("total_base_strategy_weight must match rows")
    if report.total_resolution_risk_weight != _sum_decimal(
        row.resolution_risk_weight for row in report.rows
    ):
        raise ValueError("total_resolution_risk_weight must match rows")
    if report.average_resolution_quality_score != _average_resolution_quality_score(
        report.rows,
    ):
        raise ValueError("average_resolution_quality_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in ALL_REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed!r}")


def _normalize_sha256(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex string")
    normalized = value.lower()
    try:
        int(normalized, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a sha256 hex string") from exc
    if value != normalized:
        raise ValueError(f"{field_name} must be a sha256 hex string")
    return normalized


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if _public_string_has_unsafe_text(value):
        raise ValueError(f"{field_name} must not expose unsafe public text")


def _public_string_has_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in PUBLIC_STRING_UNSAFE_TOKENS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return value


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return value.quantize(Decimal("1"))


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    value = _normalize_count_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must be quantizable") from exc


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(Decimal("1"))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return total.quantize(QUANTUM)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (left * right).quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return str(value.quantize(QUANTUM))


def _count_payload(value: Decimal) -> str:
    return str(value.quantize(Decimal("1")))


def _row_derived_validation_digest(
    row: StrategyResolutionRiskWeightDigestRow,
) -> str:
    return _validation_digest(
        "row_derived",
        (
            f"strategy_id={row.strategy_id}",
            f"candidate_id={row.candidate_id}",
            f"market_slug={row.market_slug}",
            f"redacted_source_reference={row.redacted_source_reference}",
            f"observed_at={row.observed_at.isoformat()}",
            f"rule_ambiguity={row.rule_ambiguity}",
            f"source_authority={row.source_authority}",
            f"dispute_pressure={row.dispute_pressure}",
            f"evidence_quorum={row.evidence_quorum}",
            f"acknowledgement_lag_seconds={row.acknowledgement_lag_seconds}",
            f"settlement_delay_seconds={row.settlement_delay_seconds}",
            f"base_strategy_weight={row.base_strategy_weight}",
            f"resolution_quality_score={row.resolution_quality_score}",
            f"resolution_risk_weight={row.resolution_risk_weight}",
            f"status={row.status}",
            f"reason_codes={_digest_tuple(row.reason_codes)}",
            f"paper_only={row.paper_only}",
            f"report_only={row.report_only}",
            f"readonly={row.readonly}",
        ),
    )


def _report_derived_validation_digest(
    report: StrategyResolutionRiskWeightDigestReport,
) -> str:
    return _validation_digest(
        "report_derived",
        (
            f"generated_at={report.generated_at.isoformat()}",
            f"config_version={report.config_version}",
            f"candidate_count={report.candidate_count}",
            f"pass_count={report.pass_count}",
            f"watch_count={report.watch_count}",
            f"block_count={report.block_count}",
            f"total_base_strategy_weight={report.total_base_strategy_weight}",
            f"total_resolution_risk_weight={report.total_resolution_risk_weight}",
            f"average_resolution_quality_score={report.average_resolution_quality_score}",
            f"status={report.status}",
            f"reason_codes={_digest_tuple(report.reason_codes)}",
            "reason_code_counts="
            f"{_digest_tuple(tuple(_reason_code_count_digest(row) for row in report.reason_code_counts))}",
            "row_derived_validation_digests="
            f"{_digest_tuple(tuple(row.derived_validation_digest for row in report.rows))}",
            f"paper_only={report.paper_only}",
            f"report_only={report.report_only}",
            f"readonly={report.readonly}",
        ),
    )


def _reason_code_count_digest(
    row: StrategyResolutionRiskWeightReasonCodeCount,
) -> str:
    return f"{row.reason_code}:{row.count}:{row.paper_only}:{row.report_only}:{row.readonly}"


def _validation_digest(label: str, values: tuple[str, ...]) -> str:
    return sha256((f"{label}|" + "|".join(values)).encode("utf-8")).hexdigest()


def _digest_tuple(values: tuple[str, ...]) -> str:
    return ",".join(values)


def _redacted_reference(value: str) -> str:
    if _reference_requires_redaction(value):
        digest = sha256(value.encode("utf-8")).hexdigest()[:16]
        return f"source_ref_{digest}"
    return value


def _require_redacted_reference(value: str) -> None:
    if _reference_requires_redaction(value):
        raise ValueError("source_reference must be redacted")


def _reference_requires_redaction(value: str) -> bool:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered:
        return True
    return any(
        token in lowered
        for token in (*SENSITIVE_REFERENCE_TOKENS, *UNSAFE_REFERENCE_TOKENS)
    )


def _require_safety_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
) -> None:
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        for field_name in value.__dataclass_fields__:
            item_path = field_name if not path else f"{path}.{field_name}"
            if _public_string_has_unsafe_text(field_name):
                raise ValueError(f"{item_path} has unsafe public field")
            if field_name in ("paper_only", "report_only", "readonly"):
                if getattr(value, field_name) is not True:
                    raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(label, getattr(value, field_name), item_path)
        return
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        if value.tzinfo is not UTC:
            raise ValueError(f"{path or label} must already be UTC")
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived values")
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is str:
        lowered = value.lower()
        if "://" in lowered or "?" in lowered or _public_string_has_unsafe_text(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) in (list, tuple):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _public_string_has_unsafe_text(key):
                raise ValueError(f"{item_path} has unsafe public field")
            if key in ("paper_only", "report_only", "readonly") and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not public-payload serializable")
