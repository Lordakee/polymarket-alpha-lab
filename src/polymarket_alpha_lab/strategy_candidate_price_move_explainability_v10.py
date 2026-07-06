"""Pure paper-only price move explainability reporting for strategy candidates."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any


__all__ = (
    "StrategyCandidatePriceMoveExplainabilityRecord",
    "StrategyCandidatePriceMoveExplainabilityResult",
    "StrategyCandidatePriceMoveExplainabilityReport",
    "build_strategy_candidate_price_move_explainability_report",
    "strategy_candidate_price_move_explainability_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-candidate-price-move-explainability-v10"
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
ONE_HUNDRED = Decimal("100.000000")
TEN_THOUSAND = Decimal("10000.000000")
FRESHNESS_WINDOW_MINUTES = Decimal("360.000000")
MOVE_BPS_EXPLAINED_LIMIT = Decimal("500.000000")
MOVE_BPS_UNEXPLAINED_LIMIT = Decimal("1500.000000")
EXPLAINED_SCORE_MINIMUM = Decimal("0.750000")
WATCH_SCORE_MINIMUM = Decimal("0.450000")
WATCH_FRESHNESS_MINIMUM = Decimal("0.750000")
WATCH_SOURCE_ALIGNMENT_MINIMUM = Decimal("0.800000")
WATCH_LIQUIDITY_SUPPORT_MINIMUM = Decimal("0.800000")
WATCH_REVERSAL_PRESSURE_MAXIMUM = Decimal("0.250000")
UNEXPLAINED_FRESHNESS_MINIMUM = Decimal("0.250000")
UNEXPLAINED_SOURCE_ALIGNMENT_MINIMUM = Decimal("0.500000")
UNEXPLAINED_LIQUIDITY_SUPPORT_MINIMUM = Decimal("0.500000")
UNEXPLAINED_REVERSAL_PRESSURE_MAXIMUM = Decimal("0.750000")
STATUS_REASON_PREFIX = "strategy_candidate_price_move_explainability_"
STATUSES = ("explained", "watch", "unexplained")
UNSAFE_SURFACE_FIELD_FRAGMENTS = (
    "auth",
    "private_key",
    "wallet",
    "account",
    "balance",
    "order",
    "cancel",
    "replace",
    "sign",
    "exchange_mutation",
)


@dataclass(frozen=True)
class StrategyCandidatePriceMoveExplainabilityRecord:
    candidate_id: str
    market_slug: str
    outcome_name: str
    previous_probability: Decimal
    current_probability: Decimal
    evidence_age_minutes: Decimal
    source_alignment_score: Decimal
    liquidity_support_score: Decimal
    reversal_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("previous_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_minutes",
            _normalize_nonnegative_decimal(
                "evidence_age_minutes",
                self.evidence_age_minutes,
            ),
        )
        for field_name in (
            "source_alignment_score",
            "liquidity_support_score",
            "reversal_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("record", self)


@dataclass(frozen=True)
class StrategyCandidatePriceMoveExplainabilityResult:
    candidate_id: str
    market_slug: str
    outcome_name: str
    previous_probability: Decimal
    current_probability: Decimal
    absolute_move_bps: Decimal
    move_bps_explainability_score: Decimal
    evidence_age_minutes: Decimal
    evidence_freshness_score: Decimal
    source_alignment_score: Decimal
    liquidity_support_score: Decimal
    reversal_pressure_score: Decimal
    reversal_relief_score: Decimal
    price_move_explainability_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    result_integrity_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_id", "market_slug", "outcome_name"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("previous_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "absolute_move_bps",
            "move_bps_explainability_score",
            "evidence_freshness_score",
            "source_alignment_score",
            "liquidity_support_score",
            "reversal_pressure_score",
            "reversal_relief_score",
            "price_move_explainability_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_or_bps_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "evidence_age_minutes",
            _normalize_nonnegative_decimal(
                "evidence_age_minutes",
                self.evidence_age_minutes,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.result_integrity_digest == "":
            object.__setattr__(
                self,
                "result_integrity_digest",
                _result_integrity_digest(self),
            )
        else:
            _require_sha256("result_integrity_digest", self.result_integrity_digest)
        _validate_result_consistency(self)
        _require_hard_flags("result", self)


@dataclass(frozen=True)
class StrategyCandidatePriceMoveExplainabilityReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    explained_count: Decimal
    watch_count: Decimal
    unexplained_count: Decimal
    min_price_move_explainability_score: Decimal
    max_absolute_move_bps: Decimal
    min_evidence_freshness_score: Decimal
    min_source_alignment_score: Decimal
    min_liquidity_support_score: Decimal
    max_reversal_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    results: tuple[StrategyCandidatePriceMoveExplainabilityResult, ...]
    report_integrity_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _normalize_datetime(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "explained_count",
            "watch_count",
            "unexplained_count",
            "max_absolute_move_bps",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_price_move_explainability_score",
            "min_evidence_freshness_score",
            "min_source_alignment_score",
            "min_liquidity_support_score",
            "max_reversal_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        if self.report_integrity_digest == "":
            object.__setattr__(
                self,
                "report_integrity_digest",
                _report_integrity_digest(self),
            )
        else:
            _require_sha256("report_integrity_digest", self.report_integrity_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)


def build_strategy_candidate_price_move_explainability_report(
    records: tuple[StrategyCandidatePriceMoveExplainabilityRecord, ...]
    | list[StrategyCandidatePriceMoveExplainabilityRecord],
    *,
    generated_at: datetime,
) -> StrategyCandidatePriceMoveExplainabilityReport:
    """Build a deterministic, side-effect-free explainability report."""

    normalized_records = _normalize_records(records)
    normalized_generated_at = _normalize_datetime(generated_at)
    results = tuple(_result_from_record(record) for record in normalized_records)
    ordered_results = tuple(
        sorted(
            results,
            key=lambda row: (
                _status_sort_key(row.status),
                -row.absolute_move_bps,
                row.candidate_id,
            ),
        ),
    )
    counts = _status_counts(ordered_results)
    report = StrategyCandidatePriceMoveExplainabilityReport(
        generated_at=normalized_generated_at,
        config_version=DEFAULT_CONFIG_VERSION,
        candidate_count=_count_decimal(len(ordered_results)),
        explained_count=_count_decimal(counts["explained"]),
        watch_count=_count_decimal(counts["watch"]),
        unexplained_count=_count_decimal(counts["unexplained"]),
        min_price_move_explainability_score=_min_result_decimal(
            ordered_results,
            "price_move_explainability_score",
        ),
        max_absolute_move_bps=_max_result_decimal(ordered_results, "absolute_move_bps"),
        min_evidence_freshness_score=_min_result_decimal(
            ordered_results,
            "evidence_freshness_score",
        ),
        min_source_alignment_score=_min_result_decimal(
            ordered_results,
            "source_alignment_score",
        ),
        min_liquidity_support_score=_min_result_decimal(
            ordered_results,
            "liquidity_support_score",
        ),
        max_reversal_pressure_score=_max_result_decimal(
            ordered_results,
            "reversal_pressure_score",
        ),
        status=_report_status(ordered_results),
        reason_codes=_report_reason_codes(ordered_results),
        results=ordered_results,
        report_integrity_digest="",
    )
    return StrategyCandidatePriceMoveExplainabilityReport(
        **{
            **asdict(report),
            "generated_at": report.generated_at,
            "reason_codes": report.reason_codes,
            "results": report.results,
            "report_integrity_digest": _report_integrity_digest(report),
        },
    )


def strategy_candidate_price_move_explainability_payload(
    report: StrategyCandidatePriceMoveExplainabilityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCandidatePriceMoveExplainabilityReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("price move explainability report", report)
        ready = _report_payload(report)
        _reject_unsafe_public_payload("price move explainability report", ready)
        return ready
    if type(report) is dict:
        _reject_unsafe_public_payload("price move explainability payload", report)
        ready = _json_ready(report)
        _reject_flag_downgrades("price move explainability payload", ready)
        _reject_unsafe_public_payload("price move explainability payload", ready)
        _require_hard_flags("payload", _DictFlags(ready))
        return ready
    raise ValueError("report must be a StrategyCandidatePriceMoveExplainabilityReport")


def _result_from_record(
    record: StrategyCandidatePriceMoveExplainabilityRecord,
) -> StrategyCandidatePriceMoveExplainabilityResult:
    absolute_move_bps = _absolute_move_bps(
        record.previous_probability,
        record.current_probability,
    )
    move_bps_explainability_score = _move_bps_explainability_score(absolute_move_bps)
    evidence_freshness_score = _evidence_freshness_score(record.evidence_age_minutes)
    reversal_relief_score = _quantize_decimal(
        "reversal_relief_score",
        ONE - record.reversal_pressure_score,
    )
    price_move_explainability_score = _price_move_explainability_score(
        move_bps_explainability_score,
        evidence_freshness_score,
        record.source_alignment_score,
        record.liquidity_support_score,
        reversal_relief_score,
    )
    status = _result_status(
        absolute_move_bps,
        price_move_explainability_score,
        evidence_freshness_score,
        record.source_alignment_score,
        record.liquidity_support_score,
        record.reversal_pressure_score,
    )
    result = StrategyCandidatePriceMoveExplainabilityResult(
        candidate_id=record.candidate_id,
        market_slug=record.market_slug,
        outcome_name=record.outcome_name,
        previous_probability=record.previous_probability,
        current_probability=record.current_probability,
        absolute_move_bps=absolute_move_bps,
        move_bps_explainability_score=move_bps_explainability_score,
        evidence_age_minutes=record.evidence_age_minutes,
        evidence_freshness_score=evidence_freshness_score,
        source_alignment_score=record.source_alignment_score,
        liquidity_support_score=record.liquidity_support_score,
        reversal_pressure_score=record.reversal_pressure_score,
        reversal_relief_score=reversal_relief_score,
        price_move_explainability_score=price_move_explainability_score,
        status=status,
        reason_codes=_result_reason_codes(
            status,
            record.reason_codes,
            absolute_move_bps,
            price_move_explainability_score,
            evidence_freshness_score,
            record.source_alignment_score,
            record.liquidity_support_score,
            record.reversal_pressure_score,
        ),
        result_integrity_digest="",
    )
    return StrategyCandidatePriceMoveExplainabilityResult(
        **{
            **asdict(result),
            "reason_codes": result.reason_codes,
            "result_integrity_digest": _result_integrity_digest(result),
        },
    )


def _validate_result_consistency(
    result: StrategyCandidatePriceMoveExplainabilityResult,
) -> None:
    expected_absolute_move_bps = _absolute_move_bps(
        result.previous_probability,
        result.current_probability,
    )
    if result.absolute_move_bps != expected_absolute_move_bps:
        raise ValueError("absolute_move_bps must match probabilities")
    expected_move_score = _move_bps_explainability_score(result.absolute_move_bps)
    if result.move_bps_explainability_score != expected_move_score:
        raise ValueError("move_bps_explainability_score must match absolute_move_bps")
    expected_freshness = _evidence_freshness_score(result.evidence_age_minutes)
    if result.evidence_freshness_score != expected_freshness:
        raise ValueError("evidence_freshness_score must match evidence_age_minutes")
    expected_relief = _quantize_decimal(
        "reversal_relief_score",
        ONE - result.reversal_pressure_score,
    )
    if result.reversal_relief_score != expected_relief:
        raise ValueError("reversal_relief_score must match reversal_pressure_score")
    expected_score = _price_move_explainability_score(
        result.move_bps_explainability_score,
        result.evidence_freshness_score,
        result.source_alignment_score,
        result.liquidity_support_score,
        result.reversal_relief_score,
    )
    if result.price_move_explainability_score != expected_score:
        raise ValueError("price_move_explainability_score must match components")
    expected_status = _result_status(
        result.absolute_move_bps,
        result.price_move_explainability_score,
        result.evidence_freshness_score,
        result.source_alignment_score,
        result.liquidity_support_score,
        result.reversal_pressure_score,
    )
    if result.status != expected_status:
        raise ValueError("status must match recomputed result status")
    expected_reasons = _result_reason_codes(
        result.status,
        _upstream_reason_codes(result.reason_codes),
        result.absolute_move_bps,
        result.price_move_explainability_score,
        result.evidence_freshness_score,
        result.source_alignment_score,
        result.liquidity_support_score,
        result.reversal_pressure_score,
    )
    if result.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match recomputed reasons")
    if result.result_integrity_digest != _result_integrity_digest(result):
        raise ValueError("result_integrity_digest must match result")


def _validate_report_consistency(
    report: StrategyCandidatePriceMoveExplainabilityReport,
) -> None:
    counts = _status_counts(report.results)
    if report.candidate_count != _count_decimal(len(report.results)):
        raise ValueError("candidate_count must match results")
    if report.explained_count != _count_decimal(counts["explained"]):
        raise ValueError("explained_count must match results")
    if report.watch_count != _count_decimal(counts["watch"]):
        raise ValueError("watch_count must match results")
    if report.unexplained_count != _count_decimal(counts["unexplained"]):
        raise ValueError("unexplained_count must match results")
    if report.min_price_move_explainability_score != _min_result_decimal(
        report.results,
        "price_move_explainability_score",
    ):
        raise ValueError("min_price_move_explainability_score must match results")
    if report.max_absolute_move_bps != _max_result_decimal(
        report.results,
        "absolute_move_bps",
    ):
        raise ValueError("max_absolute_move_bps must match results")
    if report.min_evidence_freshness_score != _min_result_decimal(
        report.results,
        "evidence_freshness_score",
    ):
        raise ValueError("min_evidence_freshness_score must match results")
    if report.min_source_alignment_score != _min_result_decimal(
        report.results,
        "source_alignment_score",
    ):
        raise ValueError("min_source_alignment_score must match results")
    if report.min_liquidity_support_score != _min_result_decimal(
        report.results,
        "liquidity_support_score",
    ):
        raise ValueError("min_liquidity_support_score must match results")
    if report.max_reversal_pressure_score != _max_result_decimal(
        report.results,
        "reversal_pressure_score",
    ):
        raise ValueError("max_reversal_pressure_score must match results")
    if report.status != _report_status(report.results):
        raise ValueError("status must match results")
    if report.reason_codes != _report_reason_codes(report.results):
        raise ValueError("reason_codes must match results")
    if report.report_integrity_digest != _report_integrity_digest(report):
        raise ValueError("report_integrity_digest must match report")


def _absolute_move_bps(previous_probability: Decimal, current_probability: Decimal) -> Decimal:
    if current_probability >= previous_probability:
        probability_delta = current_probability - previous_probability
    else:
        probability_delta = previous_probability - current_probability
    return _quantize_decimal("absolute_move_bps", probability_delta * TEN_THOUSAND)


def _move_bps_explainability_score(absolute_move_bps: Decimal) -> Decimal:
    if absolute_move_bps >= MOVE_BPS_UNEXPLAINED_LIMIT:
        return ZERO
    return _quantize_decimal(
        "move_bps_explainability_score",
        ONE - (absolute_move_bps / Decimal("2000.000000")),
    )


def _evidence_freshness_score(evidence_age_minutes: Decimal) -> Decimal:
    if evidence_age_minutes >= FRESHNESS_WINDOW_MINUTES:
        return ZERO
    return _quantize_decimal(
        "evidence_freshness_score",
        ONE - (evidence_age_minutes / FRESHNESS_WINDOW_MINUTES),
    )


def _price_move_explainability_score(
    move_bps_explainability_score: Decimal,
    evidence_freshness_score: Decimal,
    source_alignment_score: Decimal,
    liquidity_support_score: Decimal,
    reversal_relief_score: Decimal,
) -> Decimal:
    return _quantize_decimal(
        "price_move_explainability_score",
        (
            move_bps_explainability_score * Decimal("0.150000")
            + evidence_freshness_score * Decimal("0.250000")
            + source_alignment_score * Decimal("0.250000")
            + liquidity_support_score * Decimal("0.250000")
            + reversal_relief_score * Decimal("0.100000")
        ),
    )


def _result_status(
    absolute_move_bps: Decimal,
    price_move_explainability_score: Decimal,
    evidence_freshness_score: Decimal,
    source_alignment_score: Decimal,
    liquidity_support_score: Decimal,
    reversal_pressure_score: Decimal,
) -> str:
    if (
        price_move_explainability_score < WATCH_SCORE_MINIMUM
        or absolute_move_bps >= MOVE_BPS_UNEXPLAINED_LIMIT
        or evidence_freshness_score < UNEXPLAINED_FRESHNESS_MINIMUM
        or source_alignment_score < UNEXPLAINED_SOURCE_ALIGNMENT_MINIMUM
        or liquidity_support_score < UNEXPLAINED_LIQUIDITY_SUPPORT_MINIMUM
        or reversal_pressure_score >= UNEXPLAINED_REVERSAL_PRESSURE_MAXIMUM
    ):
        return "unexplained"
    if (
        price_move_explainability_score < EXPLAINED_SCORE_MINIMUM
        or absolute_move_bps > MOVE_BPS_EXPLAINED_LIMIT
        or evidence_freshness_score < WATCH_FRESHNESS_MINIMUM
        or source_alignment_score < WATCH_SOURCE_ALIGNMENT_MINIMUM
        or liquidity_support_score < WATCH_LIQUIDITY_SUPPORT_MINIMUM
        or reversal_pressure_score > WATCH_REVERSAL_PRESSURE_MAXIMUM
    ):
        return "watch"
    return "explained"


def _result_reason_codes(
    status: str,
    upstream_reason_codes: tuple[str, ...],
    absolute_move_bps: Decimal,
    price_move_explainability_score: Decimal,
    evidence_freshness_score: Decimal,
    source_alignment_score: Decimal,
    liquidity_support_score: Decimal,
    reversal_pressure_score: Decimal,
) -> tuple[str, ...]:
    reasons = [f"{STATUS_REASON_PREFIX}{status}", *upstream_reason_codes]
    if status == "explained":
        reasons.append("evidence_supports_probability_move")
        return tuple(dict.fromkeys(reasons))
    if status == "unexplained":
        if absolute_move_bps >= MOVE_BPS_UNEXPLAINED_LIMIT:
            reasons.append("move_bps_unexplained")
        if evidence_freshness_score < UNEXPLAINED_FRESHNESS_MINIMUM:
            reasons.append("evidence_freshness_unexplained")
        if source_alignment_score < UNEXPLAINED_SOURCE_ALIGNMENT_MINIMUM:
            reasons.append("source_alignment_unexplained")
        if liquidity_support_score < UNEXPLAINED_LIQUIDITY_SUPPORT_MINIMUM:
            reasons.append("liquidity_support_unexplained")
        if reversal_pressure_score >= UNEXPLAINED_REVERSAL_PRESSURE_MAXIMUM:
            reasons.append("reversal_pressure_unexplained")
        if price_move_explainability_score < WATCH_SCORE_MINIMUM:
            reasons.append("price_move_explainability_score_unexplained")
        return tuple(dict.fromkeys(reasons))
    if absolute_move_bps > MOVE_BPS_EXPLAINED_LIMIT:
        reasons.append("move_bps_watch")
    if evidence_freshness_score < WATCH_FRESHNESS_MINIMUM:
        reasons.append("evidence_freshness_watch")
    if source_alignment_score < WATCH_SOURCE_ALIGNMENT_MINIMUM:
        reasons.append("source_alignment_watch")
    if liquidity_support_score < WATCH_LIQUIDITY_SUPPORT_MINIMUM:
        reasons.append("liquidity_support_watch")
    if reversal_pressure_score > WATCH_REVERSAL_PRESSURE_MAXIMUM:
        reasons.append("reversal_pressure_watch")
    if price_move_explainability_score < EXPLAINED_SCORE_MINIMUM:
        reasons.append("price_move_explainability_score_watch")
    return tuple(dict.fromkeys(reasons))


def _report_status(
    results: tuple[StrategyCandidatePriceMoveExplainabilityResult, ...],
) -> str:
    if any(result.status == "unexplained" for result in results):
        return "unexplained"
    if any(result.status == "watch" for result in results):
        return "watch"
    return "explained"


def _report_reason_codes(
    results: tuple[StrategyCandidatePriceMoveExplainabilityResult, ...],
) -> tuple[str, ...]:
    ordered: list[str] = []
    for status in ("unexplained", "watch", "explained"):
        for result in results:
            if result.status == status:
                ordered.extend(_report_result_reason_codes(result))
    return tuple(dict.fromkeys(ordered)) or ("strategy_candidate_price_move_explainability_explained",)


def _report_result_reason_codes(
    result: StrategyCandidatePriceMoveExplainabilityResult,
) -> tuple[str, ...]:
    reasons = [f"{STATUS_REASON_PREFIX}{result.status}"]
    if result.status == "explained":
        reasons.append("evidence_supports_probability_move")
        return tuple(reasons)
    if result.status == "unexplained":
        if result.price_move_explainability_score < WATCH_SCORE_MINIMUM:
            reasons.append("price_move_explainability_score_unexplained")
        if result.absolute_move_bps >= MOVE_BPS_UNEXPLAINED_LIMIT:
            reasons.append("move_bps_unexplained")
        if result.evidence_freshness_score < UNEXPLAINED_FRESHNESS_MINIMUM:
            reasons.append("evidence_freshness_unexplained")
        if result.source_alignment_score < UNEXPLAINED_SOURCE_ALIGNMENT_MINIMUM:
            reasons.append("source_alignment_unexplained")
        if result.liquidity_support_score < UNEXPLAINED_LIQUIDITY_SUPPORT_MINIMUM:
            reasons.append("liquidity_support_unexplained")
        if result.reversal_pressure_score >= UNEXPLAINED_REVERSAL_PRESSURE_MAXIMUM:
            reasons.append("reversal_pressure_unexplained")
        return tuple(reasons)
    if result.price_move_explainability_score < EXPLAINED_SCORE_MINIMUM:
        reasons.append("price_move_explainability_score_watch")
    if result.absolute_move_bps > MOVE_BPS_EXPLAINED_LIMIT:
        reasons.append("move_bps_watch")
    if result.evidence_freshness_score < WATCH_FRESHNESS_MINIMUM:
        reasons.append("evidence_freshness_watch")
    if result.source_alignment_score < WATCH_SOURCE_ALIGNMENT_MINIMUM:
        reasons.append("source_alignment_watch")
    if result.liquidity_support_score < WATCH_LIQUIDITY_SUPPORT_MINIMUM:
        reasons.append("liquidity_support_watch")
    if result.reversal_pressure_score > WATCH_REVERSAL_PRESSURE_MAXIMUM:
        reasons.append("reversal_pressure_watch")
    return tuple(reasons)


def _status_counts(
    results: tuple[StrategyCandidatePriceMoveExplainabilityResult, ...],
) -> dict[str, int]:
    return {
        "explained": sum(1 for result in results if result.status == "explained"),
        "watch": sum(1 for result in results if result.status == "watch"),
        "unexplained": sum(1 for result in results if result.status == "unexplained"),
    }


def _status_sort_key(status: str) -> int:
    return {"unexplained": 0, "watch": 1, "explained": 2}[status]


def _upstream_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    upstream = []
    generated_suffixes = (
        "_explained",
        "_watch",
        "_unexplained",
    )
    generated_codes = {
        "evidence_supports_probability_move",
        "move_bps_watch",
        "evidence_freshness_watch",
        "source_alignment_watch",
        "liquidity_support_watch",
        "reversal_pressure_watch",
        "price_move_explainability_score_watch",
        "move_bps_unexplained",
        "evidence_freshness_unexplained",
        "source_alignment_unexplained",
        "liquidity_support_unexplained",
        "reversal_pressure_unexplained",
        "price_move_explainability_score_unexplained",
    }
    for reason_code in reason_codes:
        if reason_code.startswith(STATUS_REASON_PREFIX):
            continue
        if reason_code in generated_codes:
            continue
        if reason_code.endswith(generated_suffixes):
            continue
        upstream.append(reason_code)
    return tuple(upstream)


def _min_result_decimal(
    results: tuple[StrategyCandidatePriceMoveExplainabilityResult, ...],
    field_name: str,
) -> Decimal:
    if not results:
        return ZERO
    return min(getattr(result, field_name) for result in results)


def _max_result_decimal(
    results: tuple[StrategyCandidatePriceMoveExplainabilityResult, ...],
    field_name: str,
) -> Decimal:
    if not results:
        return ZERO
    return max(getattr(result, field_name) for result in results)


def _report_payload(report: StrategyCandidatePriceMoveExplainabilityReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "candidate_count": _count_payload(report.candidate_count),
        "explained_count": _count_payload(report.explained_count),
        "watch_count": _count_payload(report.watch_count),
        "unexplained_count": _count_payload(report.unexplained_count),
        "min_price_move_explainability_score": _decimal_payload(
            report.min_price_move_explainability_score,
        ),
        "max_absolute_move_bps": _decimal_payload(report.max_absolute_move_bps),
        "min_evidence_freshness_score": _decimal_payload(
            report.min_evidence_freshness_score,
        ),
        "min_source_alignment_score": _decimal_payload(
            report.min_source_alignment_score,
        ),
        "min_liquidity_support_score": _decimal_payload(
            report.min_liquidity_support_score,
        ),
        "max_reversal_pressure_score": _decimal_payload(
            report.max_reversal_pressure_score,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "results": [_result_payload(result) for result in report.results],
        "report_integrity_digest": report.report_integrity_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _result_payload(result: StrategyCandidatePriceMoveExplainabilityResult) -> dict[str, Any]:
    return {
        "candidate_id": result.candidate_id,
        "market_slug": result.market_slug,
        "outcome_name": result.outcome_name,
        "previous_probability": _decimal_payload(result.previous_probability),
        "current_probability": _decimal_payload(result.current_probability),
        "absolute_move_bps": _decimal_payload(result.absolute_move_bps),
        "move_bps_explainability_score": _decimal_payload(
            result.move_bps_explainability_score,
        ),
        "evidence_age_minutes": _decimal_payload(result.evidence_age_minutes),
        "evidence_freshness_score": _decimal_payload(result.evidence_freshness_score),
        "source_alignment_score": _decimal_payload(result.source_alignment_score),
        "liquidity_support_score": _decimal_payload(result.liquidity_support_score),
        "reversal_pressure_score": _decimal_payload(result.reversal_pressure_score),
        "reversal_relief_score": _decimal_payload(result.reversal_relief_score),
        "price_move_explainability_score": _decimal_payload(
            result.price_move_explainability_score,
        ),
        "status": result.status,
        "reason_codes": list(result.reason_codes),
        "result_integrity_digest": result.result_integrity_digest,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _result_integrity_digest(
    result: StrategyCandidatePriceMoveExplainabilityResult,
) -> str:
    payload = _result_payload_without_digest(result)
    return _sha256_payload(payload)


def _report_integrity_digest(
    report: StrategyCandidatePriceMoveExplainabilityReport,
) -> str:
    payload = _report_payload_without_digest(report)
    return _sha256_payload(payload)


def _result_payload_without_digest(
    result: StrategyCandidatePriceMoveExplainabilityResult,
) -> dict[str, Any]:
    payload = _result_payload(result)
    payload.pop("result_integrity_digest")
    return payload


def _report_payload_without_digest(
    report: StrategyCandidatePriceMoveExplainabilityReport,
) -> dict[str, Any]:
    payload = _report_payload(report)
    payload.pop("report_integrity_digest")
    return payload


def _sha256_payload(payload: dict[str, Any]) -> str:
    encoded = _canonical_payload(payload).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _canonical_payload(value: Any) -> str:
    if type(value) is dict:
        parts = []
        for key in sorted(value):
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            parts.append(f"{_canonical_payload(key)}:{_canonical_payload(value[key])}")
        return "{" + ",".join(parts) + "}"
    if type(value) is list:
        return "[" + ",".join(_canonical_payload(item) for item in value) + "]"
    if type(value) is str:
        return repr(value)
    if type(value) is bool:
        return "true" if value else "false"
    if value is None:
        return "null"
    raise ValueError("payload value is not canonical")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return _decimal_payload(value)
    if type(value) is datetime:
        return _normalize_datetime(value).isoformat()
    if type(value) is float:
        raise ValueError("JSON value must not be a float")
    if type(value) in (str, bool):
        return value
    if type(value) is int:
        return str(_count_decimal(value))
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_unsafe_surface_fields(label, payload)
    _reject_unsafe_text_values(label, payload)


def _reject_unsafe_surface_fields(label: str, payload: object) -> None:
    if hasattr(payload, "__dataclass_fields__") and not isinstance(payload, type):
        _reject_unsafe_surface_fields(label, asdict(payload))
        return
    if isinstance(payload, dict):
        for key, item in payload.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            normalized_key = key.lower()
            if any(fragment in normalized_key for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
                raise ValueError(f"unsafe live surface field in {label}: {key}")
            _reject_unsafe_surface_fields(label, item)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_surface_fields(label, item)


def _reject_unsafe_text_values(label: str, payload: object) -> None:
    if type(payload) is str:
        normalized = payload.lower()
        if any(fragment in normalized for fragment in UNSAFE_SURFACE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe live surface value in {label}")
        return
    if isinstance(payload, dict):
        for key, item in payload.items():
            _reject_unsafe_text_values(label, key)
            _reject_unsafe_text_values(label, item)
        return
    if isinstance(payload, (list, tuple)):
        for item in payload:
            _reject_unsafe_text_values(label, item)


def _reject_flag_downgrades(label: str, payload: object) -> None:
    if isinstance(payload, dict):
        for field_name in ("paper_only", "report_only", "readonly"):
            if field_name in payload and payload[field_name] is not True:
                raise ValueError(f"{field_name} must be True for {label}")
        for item in payload.values():
            _reject_flag_downgrades(label, item)
        return
    if isinstance(payload, list):
        for item in payload:
            _reject_flag_downgrades(label, item)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _normalize_records(
    records: tuple[StrategyCandidatePriceMoveExplainabilityRecord, ...]
    | list[StrategyCandidatePriceMoveExplainabilityRecord],
) -> tuple[StrategyCandidatePriceMoveExplainabilityRecord, ...]:
    if type(records) not in (tuple, list):
        raise ValueError("records must be a sequence")
    normalized = tuple(records)
    if not normalized:
        raise ValueError("records must not be empty")
    for record in normalized:
        if type(record) is not StrategyCandidatePriceMoveExplainabilityRecord:
            raise ValueError(
                "records must contain StrategyCandidatePriceMoveExplainabilityRecord",
            )
        _require_hard_flags("record", record)
    return normalized


def _normalize_results(
    results: object,
) -> tuple[StrategyCandidatePriceMoveExplainabilityResult, ...]:
    if type(results) is not tuple:
        raise ValueError("results must be a tuple")
    for result in results:
        if type(result) is not StrategyCandidatePriceMoveExplainabilityResult:
            raise ValueError(
                "results must contain StrategyCandidatePriceMoveExplainabilityResult",
            )
        _require_hard_flags("result", result)
    return results


def _normalize_datetime(value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a timezone-aware datetime")
    if value.tzinfo is None:
        raise ValueError("generated_at must be a timezone-aware datetime")
    return value.astimezone(UTC)


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in value:
        _require_canonical_string(field_name, reason_code)
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must be unique")
    return value


def _normalize_probability_or_bps_decimal(field_name: str, value: object) -> Decimal:
    if field_name == "absolute_move_bps":
        return _normalize_nonnegative_decimal(field_name, value)
    return _normalize_probability_decimal(field_name, value)


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be a probability")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(str(value)).quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(value, "f")


def _count_payload(value: Decimal) -> str:
    return format(value.quantize(Decimal("1")), "f")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        expected = ", ".join(allowed_values)
        raise ValueError(f"{field_name} must be one of: {expected}")


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


def __init_subclass__(cls, **kwargs: object) -> None:
    raise TypeError("strategy candidate price move explainability types must not be subclassed")


for _export_name in __all__:
    _export = globals()[_export_name]
    if isinstance(_export, type) and hasattr(_export, "__dataclass_fields__"):
        _export.__init_subclass__ = classmethod(__init_subclass__)
