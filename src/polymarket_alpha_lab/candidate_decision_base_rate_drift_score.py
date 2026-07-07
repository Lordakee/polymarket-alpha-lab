"""Paper-only base-rate drift score for prioritizing candidate research."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_CANDIDATE_DECISION_BASE_RATE_DRIFT_SCORE_CONFIG_VERSION = (
    "candidate-decision-base-rate-drift-score-v1"
)
BOUNDARY_STATEMENT = "Paper-only base-rate drift research support; readonly report."

PUBLIC_DATACLASS_NAMES = frozenset(
    (
        "CandidateDecisionBaseRateDriftScoreConfig",
        "CandidateDecisionBaseRateDriftFact",
        "CandidateDecisionBaseRateDriftScoreRow",
        "CandidateDecisionBaseRateDriftScoreReport",
    ),
)
DECIMAL_CONTEXT = Context(prec=64)
SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
SCORE_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

ROW_REASON_CODES = frozenset(
    (
        "base_rate_drift_pass",
        "base_rate_drift_watch",
        "base_rate_drift_block",
        "historical_base_rate_sample_size_below_floor",
        "historical_base_rate_recency_below_floor",
        "historical_event_similarity_below_floor",
        "historical_base_rate_dispersion_above_ceiling",
        "base_rate_quality_below_floor",
        "candidate_drift_explanation_below_floor",
        "candidate_judgment_close_to_base_rate",
        "candidate_judgment_materially_deviates",
        "candidate_judgment_extreme_deviation",
        "candidate_drift_explanation_present",
    ),
)
REPORT_REASON_CODES = frozenset(
    (
        "base_rate_drift_empty",
        "base_rate_drift_report_pass",
        "base_rate_drift_report_watch",
        "base_rate_drift_report_block",
        *ROW_REASON_CODES,
    ),
)
UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "raw_candidate",
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "url",
        "http",
        "www.",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "trading",
        "position",
        "buy",
        "sell",
        "recommendation",
        "recommend",
    ),
)
REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "score_status",
        "row_count",
        "pass_count",
        "watch_count",
        "blocked_count",
        "average_base_rate_drift_magnitude",
        "max_base_rate_drift_magnitude",
        "average_unexplained_drift_score",
        "rows",
        "fact_config_versions",
        "reason_codes",
        "derived_validation_digest",
        "boundary_statement",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "rank",
        "redacted_candidate_key",
        "redacted_event_type_key",
        "observed_at",
        "candidate_current_probability",
        "historical_base_rate_probability",
        "base_rate_drift_magnitude",
        "base_rate_drift_score",
        "historical_sample_size",
        "sample_size_score",
        "historical_recency_score",
        "historical_similarity_score",
        "historical_dispersion_score",
        "dispersion_grounding_score",
        "base_rate_quality_score",
        "drift_explanation_score",
        "unexplained_drift_score",
        "score_status",
        "reason_codes",
        "fact_config_version",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls.__module__ != __name__ or cls.__name__ not in PUBLIC_DATACLASS_NAMES:
            raise TypeError("subclassing is not allowed")


@dataclass(frozen=True)
class CandidateDecisionBaseRateDriftScoreConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CANDIDATE_DECISION_BASE_RATE_DRIFT_SCORE_CONFIG_VERSION
    minimum_historical_sample_size: Decimal = Decimal("50.000000")
    minimum_recency_score: Decimal = Decimal("0.600000")
    minimum_similarity_score: Decimal = Decimal("0.650000")
    maximum_dispersion_score: Decimal = Decimal("0.450000")
    minimum_drift_explanation_score: Decimal = Decimal("0.600000")
    base_rate_quality_floor: Decimal = Decimal("0.700000")
    watch_drift_floor: Decimal = Decimal("0.080000")
    block_drift_floor: Decimal = Decimal("0.180000")
    sample_size_weight: Decimal = Decimal("0.250000")
    recency_weight: Decimal = Decimal("0.250000")
    similarity_weight: Decimal = Decimal("0.250000")
    dispersion_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CandidateDecisionBaseRateDriftScoreConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        object.__setattr__(
            self,
            "minimum_historical_sample_size",
            _require_positive_decimal(
                "minimum_historical_sample_size",
                self.minimum_historical_sample_size,
            ),
        )
        for field_name in (
            "minimum_recency_score",
            "minimum_similarity_score",
            "maximum_dispersion_score",
            "minimum_drift_explanation_score",
            "base_rate_quality_floor",
            "watch_drift_floor",
            "block_drift_floor",
            "sample_size_weight",
            "recency_weight",
            "similarity_weight",
            "dispersion_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionBaseRateDriftFact(_FinalPublicDataclass):
    redacted_candidate_key: str
    redacted_event_type_key: str
    observed_at: datetime
    candidate_current_probability: Decimal
    historical_base_rate_probability: Decimal
    historical_sample_size: Decimal
    historical_recency_score: Decimal
    historical_similarity_score: Decimal
    historical_dispersion_score: Decimal
    drift_explanation_score: Decimal
    fact_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionBaseRateDriftFact, "fact")
        for field_name in ("redacted_candidate_key", "redacted_event_type_key"):
            object.__setattr__(
                self,
                field_name,
                _require_redacted_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fact_config_version",
            _require_public_string("fact_config_version", self.fact_config_version),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "historical_sample_size",
            _require_nonnegative_decimal(
                "historical_sample_size",
                self.historical_sample_size,
            ),
        )
        for field_name in (
            "candidate_current_probability",
            "historical_base_rate_probability",
            "historical_recency_score",
            "historical_similarity_score",
            "historical_dispersion_score",
            "drift_explanation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("fact", self)
        _reject_unsafe_public_payload("fact", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionBaseRateDriftScoreRow(_FinalPublicDataclass):
    rank: Decimal
    redacted_candidate_key: str
    redacted_event_type_key: str
    observed_at: datetime
    candidate_current_probability: Decimal
    historical_base_rate_probability: Decimal
    base_rate_drift_magnitude: Decimal
    base_rate_drift_score: Decimal
    historical_sample_size: Decimal
    sample_size_score: Decimal
    historical_recency_score: Decimal
    historical_similarity_score: Decimal
    historical_dispersion_score: Decimal
    dispersion_grounding_score: Decimal
    base_rate_quality_score: Decimal
    drift_explanation_score: Decimal
    unexplained_drift_score: Decimal
    score_status: str
    reason_codes: tuple[str, ...]
    fact_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionBaseRateDriftScoreRow, "row")
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        for field_name in ("redacted_candidate_key", "redacted_event_type_key"):
            object.__setattr__(
                self,
                field_name,
                _require_redacted_identifier(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fact_config_version",
            _require_public_string("fact_config_version", self.fact_config_version),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "historical_sample_size",
            _require_nonnegative_decimal(
                "historical_sample_size",
                self.historical_sample_size,
            ),
        )
        for field_name in (
            "candidate_current_probability",
            "historical_base_rate_probability",
            "base_rate_drift_magnitude",
            "base_rate_drift_score",
            "sample_size_score",
            "historical_recency_score",
            "historical_similarity_score",
            "historical_dispersion_score",
            "dispersion_grounding_score",
            "base_rate_quality_score",
            "drift_explanation_score",
            "unexplained_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("score_status", self.score_status)
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(self))


@dataclass(frozen=True)
class CandidateDecisionBaseRateDriftScoreReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    score_status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_base_rate_drift_magnitude: Decimal
    max_base_rate_drift_magnitude: Decimal
    average_unexplained_drift_score: Decimal
    rows: tuple[CandidateDecisionBaseRateDriftScoreRow, ...]
    fact_config_versions: tuple[tuple[str, str, str], ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    boundary_statement: str = BOUNDARY_STATEMENT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, CandidateDecisionBaseRateDriftScoreReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("score_status", self.score_status)
        for field_name in ("row_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_base_rate_drift_magnitude",
            "max_base_rate_drift_magnitude",
            "average_unexplained_drift_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "fact_config_versions",
            _require_fact_config_versions(self.fact_config_versions),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        if self.boundary_statement != BOUNDARY_STATEMENT:
            raise ValueError("boundary_statement must match paper-only scope")
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", _payload_value(self))
        _validate_report(self)
        _require_matching_digest(_payload_value(self))


def build_candidate_decision_base_rate_drift_score(
    facts: Iterable[CandidateDecisionBaseRateDriftFact],
    *,
    config: CandidateDecisionBaseRateDriftScoreConfig | None = None,
    generated_at: datetime,
) -> CandidateDecisionBaseRateDriftScoreReport:
    cfg = config or CandidateDecisionBaseRateDriftScoreConfig()
    if type(cfg) is not CandidateDecisionBaseRateDriftScoreConfig:
        raise ValueError(
            "config must be exactly CandidateDecisionBaseRateDriftScoreConfig",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_facts(facts)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_for_fact(rank=index, fact=item, config=cfg)
        for index, item in enumerate(_sorted_facts(normalized), start=1)
    )
    status = _report_status(rows)
    values: dict[str, Any] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "score_status": status,
        "row_count": _count_decimal(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "blocked_count": _status_count(rows, STATUS_BLOCK),
        "average_base_rate_drift_magnitude": _average(
            row.base_rate_drift_magnitude for row in rows
        ),
        "max_base_rate_drift_magnitude": max(
            (row.base_rate_drift_magnitude for row in rows),
            default=ZERO,
        ),
        "average_unexplained_drift_score": _average(
            row.unexplained_drift_score for row in rows
        ),
        "rows": rows,
        "fact_config_versions": tuple(
            sorted(
                (
                    item.redacted_candidate_key,
                    item.redacted_event_type_key,
                    item.fact_config_version,
                )
                for item in normalized
            ),
        ),
        "reason_codes": _report_reason_codes(rows, status),
        "boundary_statement": BOUNDARY_STATEMENT,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    values["derived_validation_digest"] = _derived_validation_digest(payload)
    return CandidateDecisionBaseRateDriftScoreReport(**values)


def candidate_decision_base_rate_drift_score_payload(
    report: CandidateDecisionBaseRateDriftScoreReport,
) -> dict[str, Any]:
    if type(report) is not CandidateDecisionBaseRateDriftScoreReport:
        raise ValueError("report must be exactly CandidateDecisionBaseRateDriftScoreReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    return payload


def validate_candidate_decision_base_rate_drift_score_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a dict")
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_hard_flags(payload)
    _require_matching_digest(payload)
    _report_from_payload(payload)
    return True


def _row_for_fact(
    *,
    rank: int,
    fact: CandidateDecisionBaseRateDriftFact,
    config: CandidateDecisionBaseRateDriftScoreConfig,
) -> CandidateDecisionBaseRateDriftScoreRow:
    drift_magnitude = _base_rate_drift_magnitude(
        fact.candidate_current_probability,
        fact.historical_base_rate_probability,
    )
    drift_score = _base_rate_drift_score(drift_magnitude, config)
    sample_size_score = _sample_size_score(fact.historical_sample_size, config)
    dispersion_grounding_score = _subtract_ratio(ONE, fact.historical_dispersion_score)
    quality_score = _base_rate_quality_score(
        sample_size_score=sample_size_score,
        recency_score=fact.historical_recency_score,
        similarity_score=fact.historical_similarity_score,
        dispersion_grounding_score=dispersion_grounding_score,
        config=config,
    )
    unexplained_drift_score = _unexplained_drift_score(
        drift_score,
        fact.drift_explanation_score,
    )
    status = _row_status(
        base_rate_drift_magnitude=drift_magnitude,
        base_rate_quality_score=quality_score,
        drift_explanation_score=fact.drift_explanation_score,
        config=config,
    )
    return CandidateDecisionBaseRateDriftScoreRow(
        rank=_count_decimal(rank),
        redacted_candidate_key=fact.redacted_candidate_key,
        redacted_event_type_key=fact.redacted_event_type_key,
        observed_at=fact.observed_at,
        candidate_current_probability=fact.candidate_current_probability,
        historical_base_rate_probability=fact.historical_base_rate_probability,
        base_rate_drift_magnitude=drift_magnitude,
        base_rate_drift_score=drift_score,
        historical_sample_size=fact.historical_sample_size,
        sample_size_score=sample_size_score,
        historical_recency_score=fact.historical_recency_score,
        historical_similarity_score=fact.historical_similarity_score,
        historical_dispersion_score=fact.historical_dispersion_score,
        dispersion_grounding_score=dispersion_grounding_score,
        base_rate_quality_score=quality_score,
        drift_explanation_score=fact.drift_explanation_score,
        unexplained_drift_score=unexplained_drift_score,
        score_status=status,
        reason_codes=_row_reason_codes(
            fact=fact,
            sample_size_score=sample_size_score,
            dispersion_grounding_score=dispersion_grounding_score,
            base_rate_drift_magnitude=drift_magnitude,
            base_rate_quality_score=quality_score,
            status=status,
            config=config,
        ),
        fact_config_version=fact.fact_config_version,
    )


def _base_rate_drift_magnitude(
    candidate_current_probability: Decimal,
    historical_base_rate_probability: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            abs(candidate_current_probability - historical_base_rate_probability),
        )


def _base_rate_drift_score(
    base_rate_drift_magnitude: Decimal,
    config: CandidateDecisionBaseRateDriftScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(base_rate_drift_magnitude / config.block_drift_floor)


def _sample_size_score(
    historical_sample_size: Decimal,
    config: CandidateDecisionBaseRateDriftScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(historical_sample_size / config.minimum_historical_sample_size)


def _base_rate_quality_score(
    *,
    sample_size_score: Decimal,
    recency_score: Decimal,
    similarity_score: Decimal,
    dispersion_grounding_score: Decimal,
    config: CandidateDecisionBaseRateDriftScoreConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(
            sample_size_score * config.sample_size_weight
            + recency_score * config.recency_weight
            + similarity_score * config.similarity_weight
            + dispersion_grounding_score * config.dispersion_weight,
        )


def _unexplained_drift_score(
    base_rate_drift_score: Decimal,
    drift_explanation_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(base_rate_drift_score * (ONE - drift_explanation_score))


def _row_status(
    *,
    base_rate_drift_magnitude: Decimal,
    base_rate_quality_score: Decimal,
    drift_explanation_score: Decimal,
    config: CandidateDecisionBaseRateDriftScoreConfig,
) -> str:
    if (
        base_rate_drift_magnitude >= config.block_drift_floor
        or base_rate_quality_score < config.base_rate_quality_floor
        or (
            base_rate_drift_magnitude >= config.watch_drift_floor
            and drift_explanation_score < config.minimum_drift_explanation_score
        )
    ):
        return STATUS_BLOCK
    if base_rate_drift_magnitude >= config.watch_drift_floor:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    fact: CandidateDecisionBaseRateDriftFact,
    sample_size_score: Decimal,
    dispersion_grounding_score: Decimal,
    base_rate_drift_magnitude: Decimal,
    base_rate_quality_score: Decimal,
    status: str,
    config: CandidateDecisionBaseRateDriftScoreConfig,
) -> tuple[str, ...]:
    codes: list[str] = [f"base_rate_drift_{status}"]
    if sample_size_score < ONE:
        codes.append("historical_base_rate_sample_size_below_floor")
    if fact.historical_recency_score < config.minimum_recency_score:
        codes.append("historical_base_rate_recency_below_floor")
    if fact.historical_similarity_score < config.minimum_similarity_score:
        codes.append("historical_event_similarity_below_floor")
    if dispersion_grounding_score < _subtract_ratio(ONE, config.maximum_dispersion_score):
        codes.append("historical_base_rate_dispersion_above_ceiling")
    if base_rate_quality_score < config.base_rate_quality_floor:
        codes.append("base_rate_quality_below_floor")
    if fact.drift_explanation_score < config.minimum_drift_explanation_score:
        codes.append("candidate_drift_explanation_below_floor")
    if base_rate_drift_magnitude >= config.block_drift_floor:
        codes.append("candidate_judgment_extreme_deviation")
    elif base_rate_drift_magnitude >= config.watch_drift_floor:
        codes.append("candidate_judgment_materially_deviates")
        if fact.drift_explanation_score >= config.minimum_drift_explanation_score:
            codes.append("candidate_drift_explanation_present")
    else:
        codes.append("candidate_judgment_close_to_base_rate")
    return tuple(codes)


def _normalize_facts(
    facts: Iterable[CandidateDecisionBaseRateDriftFact],
) -> tuple[CandidateDecisionBaseRateDriftFact, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable")
    try:
        normalized = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not CandidateDecisionBaseRateDriftFact:
            raise ValueError("facts must contain CandidateDecisionBaseRateDriftFact")
        _require_hard_flags("fact", item)
        key = (item.redacted_candidate_key, item.redacted_event_type_key)
        if key in seen:
            raise ValueError("duplicate candidate/event-type fact")
        seen.add(key)
    return normalized


def _sorted_facts(
    facts: tuple[CandidateDecisionBaseRateDriftFact, ...],
) -> tuple[CandidateDecisionBaseRateDriftFact, ...]:
    return tuple(
        sorted(
            facts,
            key=lambda item: (
                item.redacted_candidate_key,
                item.redacted_event_type_key,
                item.observed_at.isoformat(),
            ),
        ),
    )


def _require_rows(
    rows: object,
) -> tuple[CandidateDecisionBaseRateDriftScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not CandidateDecisionBaseRateDriftScoreRow:
            raise ValueError("rows must contain CandidateDecisionBaseRateDriftScoreRow")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=lambda row: row.rank)):
        raise ValueError("rows must be sorted by rank")
    expected_ranks = tuple(_count_decimal(index) for index in range(1, len(normalized) + 1))
    if tuple(row.rank for row in normalized) != expected_ranks:
        raise ValueError("rows must use contiguous ranks")
    return normalized


def _require_fact_config_versions(values: object) -> tuple[tuple[str, str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("fact_config_versions must be a tuple")
    normalized: list[tuple[str, str, str]] = []
    for value in values:
        if type(value) is not tuple or len(value) != 3:
            raise ValueError("fact_config_versions entries must be string triplets")
        redacted_candidate_key, redacted_event_type_key, fact_config_version = value
        normalized.append(
            (
                _require_redacted_identifier(
                    "fact_config_versions",
                    redacted_candidate_key,
                ),
                _require_redacted_identifier(
                    "fact_config_versions",
                    redacted_event_type_key,
                ),
                _require_public_string("fact_config_versions", fact_config_version),
            ),
        )
    result = tuple(normalized)
    if result != tuple(sorted(result)):
        raise ValueError("fact_config_versions must be sorted")
    return result


def _report_status(rows: tuple[CandidateDecisionBaseRateDriftScoreRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.score_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.score_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[CandidateDecisionBaseRateDriftScoreRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("base_rate_drift_empty",)
    codes = [f"base_rate_drift_report_{status}"]
    for row in rows:
        for code in row.reason_codes:
            if code not in codes:
                codes.append(code)
    return tuple(codes)


def _validate_config(config: CandidateDecisionBaseRateDriftScoreConfig) -> None:
    if config.block_drift_floor <= config.watch_drift_floor:
        raise ValueError("block_drift_floor must exceed watch_drift_floor")
    with localcontext(DECIMAL_CONTEXT):
        weight_total = (
            config.sample_size_weight
            + config.recency_weight
            + config.similarity_weight
            + config.dispersion_weight
        )
    if weight_total != ONE:
        raise ValueError("weights must sum to 1.000000")


def _validate_report(report: CandidateDecisionBaseRateDriftScoreReport) -> None:
    rows = report.rows
    for row in rows:
        if row.base_rate_drift_magnitude != _base_rate_drift_magnitude(
            row.candidate_current_probability,
            row.historical_base_rate_probability,
        ):
            raise ValueError("base_rate_drift_magnitude must match row probabilities")
    if report.row_count != _count_decimal(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("blocked_count must match rows")
    if report.score_status != _report_status(rows):
        raise ValueError("score_status must match rows")
    if report.average_base_rate_drift_magnitude != _average(
        row.base_rate_drift_magnitude for row in rows
    ):
        raise ValueError("average_base_rate_drift_magnitude must match rows")
    if report.max_base_rate_drift_magnitude != max(
        (row.base_rate_drift_magnitude for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_base_rate_drift_magnitude must match rows")
    if report.average_unexplained_drift_score != _average(
        row.unexplained_drift_score for row in rows
    ):
        raise ValueError("average_unexplained_drift_score must match rows")
    expected_fact_config_versions = tuple(
        sorted(
            (
                row.redacted_candidate_key,
                row.redacted_event_type_key,
                row.fact_config_version,
            )
            for row in rows
        ),
    )
    if report.fact_config_versions != expected_fact_config_versions:
        raise ValueError("fact_config_versions must match rows")
    if report.reason_codes != _report_reason_codes(rows, report.score_status):
        raise ValueError("reason_codes must match rows")


def _status_count(
    rows: tuple[CandidateDecisionBaseRateDriftScoreRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.score_status == status))


def _average(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(sum(items, ZERO) / Decimal(len(items)))


def _subtract_ratio(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(left - right)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize_decimal(value)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _require_positive_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return value


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _require_public_string(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_redacted_identifier(field_name: str, value: str) -> str:
    value = _require_public_string(field_name, value)
    if not (value.startswith("redacted-") or "-redacted-" in value):
        raise ValueError(f"{field_name} must be a redacted identifier")
    return value


def _require_reason_codes(
    field_name: str,
    values: Iterable[str],
    allowed_codes: frozenset[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not normalized:
        raise ValueError(f"{field_name} must be non-empty")
    seen: set[str] = set()
    for value in normalized:
        _require_public_string(field_name, value)
        if value not in allowed_codes:
            raise ValueError(f"{field_name} contains an unknown reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(value)
    return normalized


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in SCORE_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_payload_hard_flags(payload: dict[str, Any]) -> None:
    for flag in ("paper_only", "report_only", "readonly"):
        if payload.get(flag) is not True:
            raise ValueError(f"payload {flag} must be True")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("payload rows must contain dicts")
        for flag in ("paper_only", "report_only", "readonly"):
            if row.get(flag) is not True:
                raise ValueError(f"payload row {flag} must be True")


def _report_from_payload(payload: dict[str, Any]) -> CandidateDecisionBaseRateDriftScoreReport:
    _require_payload_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    return CandidateDecisionBaseRateDriftScoreReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_public_string("config_version", payload["config_version"]),
        score_status=_payload_public_string("score_status", payload["score_status"]),
        row_count=_payload_decimal("row_count", payload["row_count"]),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        blocked_count=_payload_decimal("blocked_count", payload["blocked_count"]),
        average_base_rate_drift_magnitude=_payload_decimal(
            "average_base_rate_drift_magnitude",
            payload["average_base_rate_drift_magnitude"],
        ),
        max_base_rate_drift_magnitude=_payload_decimal(
            "max_base_rate_drift_magnitude",
            payload["max_base_rate_drift_magnitude"],
        ),
        average_unexplained_drift_score=_payload_decimal(
            "average_unexplained_drift_score",
            payload["average_unexplained_drift_score"],
        ),
        rows=_payload_rows(payload["rows"]),
        fact_config_versions=_payload_fact_config_versions(
            payload["fact_config_versions"],
        ),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        boundary_statement=_payload_public_string(
            "boundary_statement",
            payload["boundary_statement"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _row_from_payload(payload: dict[str, Any]) -> CandidateDecisionBaseRateDriftScoreRow:
    _require_payload_keys("payload row", payload, ROW_PAYLOAD_KEYS)
    return CandidateDecisionBaseRateDriftScoreRow(
        rank=_payload_decimal("rank", payload["rank"]),
        redacted_candidate_key=_payload_redacted_identifier(
            "redacted_candidate_key",
            payload["redacted_candidate_key"],
        ),
        redacted_event_type_key=_payload_redacted_identifier(
            "redacted_event_type_key",
            payload["redacted_event_type_key"],
        ),
        observed_at=_payload_datetime("observed_at", payload["observed_at"]),
        candidate_current_probability=_payload_decimal(
            "candidate_current_probability",
            payload["candidate_current_probability"],
        ),
        historical_base_rate_probability=_payload_decimal(
            "historical_base_rate_probability",
            payload["historical_base_rate_probability"],
        ),
        base_rate_drift_magnitude=_payload_decimal(
            "base_rate_drift_magnitude",
            payload["base_rate_drift_magnitude"],
        ),
        base_rate_drift_score=_payload_decimal(
            "base_rate_drift_score",
            payload["base_rate_drift_score"],
        ),
        historical_sample_size=_payload_decimal(
            "historical_sample_size",
            payload["historical_sample_size"],
        ),
        sample_size_score=_payload_decimal("sample_size_score", payload["sample_size_score"]),
        historical_recency_score=_payload_decimal(
            "historical_recency_score",
            payload["historical_recency_score"],
        ),
        historical_similarity_score=_payload_decimal(
            "historical_similarity_score",
            payload["historical_similarity_score"],
        ),
        historical_dispersion_score=_payload_decimal(
            "historical_dispersion_score",
            payload["historical_dispersion_score"],
        ),
        dispersion_grounding_score=_payload_decimal(
            "dispersion_grounding_score",
            payload["dispersion_grounding_score"],
        ),
        base_rate_quality_score=_payload_decimal(
            "base_rate_quality_score",
            payload["base_rate_quality_score"],
        ),
        drift_explanation_score=_payload_decimal(
            "drift_explanation_score",
            payload["drift_explanation_score"],
        ),
        unexplained_drift_score=_payload_decimal(
            "unexplained_drift_score",
            payload["unexplained_drift_score"],
        ),
        score_status=_payload_public_string("score_status", payload["score_status"]),
        reason_codes=_payload_string_tuple("reason_codes", payload["reason_codes"]),
        fact_config_version=_payload_public_string(
            "fact_config_version",
            payload["fact_config_version"],
        ),
        paper_only=_payload_bool("paper_only", payload["paper_only"]),
        report_only=_payload_bool("report_only", payload["report_only"]),
        readonly=_payload_bool("readonly", payload["readonly"]),
    )


def _payload_rows(value: object) -> tuple[CandidateDecisionBaseRateDriftScoreRow, ...]:
    if type(value) is not list:
        raise ValueError("payload rows must be a list")
    rows: list[CandidateDecisionBaseRateDriftScoreRow] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError("payload rows must contain dicts")
        rows.append(_row_from_payload(item))
    return tuple(rows)


def _payload_fact_config_versions(value: object) -> tuple[tuple[str, str, str], ...]:
    if type(value) is not list:
        raise ValueError("fact_config_versions must be a list")
    normalized: list[tuple[str, str, str]] = []
    for item in value:
        if type(item) is not list or len(item) != 3:
            raise ValueError("fact_config_versions entries must be string triplets")
        normalized.append(
            (
                _payload_redacted_identifier("fact_config_versions", item[0]),
                _payload_redacted_identifier("fact_config_versions", item[1]),
                _payload_public_string("fact_config_versions", item[2]),
            ),
        )
    return tuple(normalized)


def _payload_string_tuple(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(_payload_public_string(field_name, item) for item in value)


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    return _require_decimal(field_name, parsed)


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return _require_public_string(field_name, value)


def _payload_redacted_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return _require_redacted_identifier(field_name, value)


def _payload_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _require_digest(field_name, value)
    return value


def _payload_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a boolean")
    return value


def _require_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = set(payload)
    if actual_keys != expected_keys:
        missing = sorted(expected_keys - actual_keys)
        unexpected = sorted(actual_keys - expected_keys)
        if missing:
            raise ValueError(f"{label} missing keys: {', '.join(missing)}")
        raise ValueError(f"{label} contains unexpected keys: {', '.join(unexpected)}")


def _payload_value(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError("public payload contains unsupported value")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    if type(payload) is dict:
        for key, value in payload.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, value)
        return
    if type(payload) is list:
        for item in payload:
            _reject_unsafe_public_payload(label, item)
        return
    if type(payload) is str:
        _reject_unsafe_public_string(label, payload)
        return
    if type(payload) in (bool,) or payload is None:
        return
    raise ValueError("public payload values must be strings, booleans, lists, or dicts")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lower_value = value.lower()
    if any(term in lower_value for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"unsafe public surface in {field_name}")


def _require_digest(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_matching_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest_value)
    if digest_value != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")


def _derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


__all__ = (
    "DEFAULT_CANDIDATE_DECISION_BASE_RATE_DRIFT_SCORE_CONFIG_VERSION",
    "BOUNDARY_STATEMENT",
    "CandidateDecisionBaseRateDriftScoreConfig",
    "CandidateDecisionBaseRateDriftFact",
    "CandidateDecisionBaseRateDriftScoreRow",
    "CandidateDecisionBaseRateDriftScoreReport",
    "build_candidate_decision_base_rate_drift_score",
    "candidate_decision_base_rate_drift_score_payload",
    "validate_candidate_decision_base_rate_drift_score_payload",
)
