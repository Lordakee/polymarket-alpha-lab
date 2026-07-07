"""Pure Phase 1 candidate similar event memory digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any

from polymarket_alpha_lab.team_taxonomy import require_team_id


DEFAULT_CANDIDATE_SIMILAR_EVENT_MEMORY_DIGEST_CONFIG_VERSION = (
    "candidate-similar-event-memory-digest-v0"
)

SUPPORT_STATUSES = ("pass", "watch", "block")
PASS_REASON = "similar_event_memory_pass"
WATCH_REASON = "similar_event_memory_watch"
BLOCK_REASON = "similar_event_memory_block"
EMPTY_ROW_REASON = "similar_event_memory_empty"
EMPTY_REPORT_REASON = "candidate_similar_event_memory_digest_empty"

REASON_CODES = (
    PASS_REASON,
    WATCH_REASON,
    BLOCK_REASON,
    EMPTY_ROW_REASON,
    "similar_event_count_low",
    "similar_event_count_watch",
    "median_similarity_low",
    "median_similarity_watch",
    "settlement_quality_low",
    "settlement_quality_watch",
    "recency_low",
    "recency_watch",
    "outcome_dispersion_high",
    "outcome_dispersion_watch",
    "base_rate_extreme",
    EMPTY_REPORT_REASON,
)

COUNT_QUANTUM = Decimal("0.000001")
RATIO_QUANTUM = Decimal("0.000001")
INTEGER_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
HALF = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

DEFAULT_MIN_PASS_SIMILAR_EVENT_COUNT = Decimal("5.000000")
DEFAULT_MIN_WATCH_SIMILAR_EVENT_COUNT = Decimal("2.000000")
DEFAULT_MIN_PASS_MEDIAN_SIMILARITY = Decimal("0.720000")
DEFAULT_MIN_WATCH_MEDIAN_SIMILARITY = Decimal("0.550000")
DEFAULT_MIN_PASS_SETTLEMENT_QUALITY = Decimal("0.800000")
DEFAULT_MIN_WATCH_SETTLEMENT_QUALITY = Decimal("0.600000")
DEFAULT_MIN_PASS_RECENCY_SCORE = Decimal("0.650000")
DEFAULT_MIN_WATCH_RECENCY_SCORE = Decimal("0.400000")
DEFAULT_MAX_PASS_OUTCOME_DISPERSION = Decimal("0.500000")
DEFAULT_MAX_WATCH_OUTCOME_DISPERSION = Decimal("0.750000")
DEFAULT_EXTREME_BASE_RATE_LOW = Decimal("0.050000")
DEFAULT_EXTREME_BASE_RATE_HIGH = Decimal("0.950000")

STATUS_SORT_WEIGHT = {
    "block": Decimal("0"),
    "watch": Decimal("1"),
    "pass": Decimal("2"),
}
STATUS_REASON = {
    "pass": PASS_REASON,
    "watch": WATCH_REASON,
    "block": BLOCK_REASON,
}
UNSAFE_PUBLIC_SURFACE_FRAGMENTS = (
    "candidate" "_" "id",
    "candidate" "-" "id",
    "raw" "_" "candidate",
    "raw" "-" "candidate",
    "event" "_" "id",
    "event" "-" "id",
    "event" "_" "slug",
    "event" "-" "slug",
    "market" "_" "id",
    "market" "-" "id",
    "market" "_" "slug",
    "market" "-" "slug",
    "condition" "_" "id",
    "condition" "-" "id",
    "ques" "tion",
    "source" "_" "ref",
    "source" "-" "ref",
    "source" "_" "reference",
    "source" "-" "reference",
    "source" "_" "u" "rl",
    "source" "-" "u" "rl",
    "u" "rl",
    "u" "ri",
    "h" "ttp",
    "h" "ttps",
    "raw" "_" "text",
    "raw" "-" "text",
    "source" "_" "text",
    "source" "-" "text",
    "pro" "mpt",
    "body" "_" "text",
    "body" "-" "text",
    "d" "sn",
    "database" "_" "u" "rl",
    "database" "-" "u" "rl",
    "post" "gres",
    "post" "gresql",
    "table" "_" "name",
    "table" "-" "name",
    "sec" "ret",
    "to" "ken",
    "private" "_" "key",
    "au" "th",
    "au" "th" "_" "to" "ken",
    "wal" "let",
    "acc" "ount",
    "tra" "de",
    "tra" "ding",
    "b" "uy",
    "se" "ll",
    "or" "der",
    "sub" "mit",
    "si" "gn",
    "can" "cel",
    "re" "place",
    "ex" "change",
    "pos" "ition",
    "si" "ze",
    "pri" "ce",
    "sta" "ke",
    "sha" "res",
    "payload",
    "ac" "tion",
    "re" "commend",
)
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_CANDIDATE_SIMILAR_EVENT_MEMORY_DIGEST_CONFIG_VERSION",
    "CandidateSimilarEventMemoryDigestConfig",
    "CandidateSimilarEventTeamMemoryBaseline",
    "CandidateSimilarEventMemoryFacts",
    "CandidateSimilarEventMemoryDigestRow",
    "CandidateSimilarEventMemoryReasonCodeCount",
    "CandidateSimilarEventMemoryDigestReport",
    "build_candidate_similar_event_memory_digest",
    "candidate_similar_event_memory_digest_payload",
)


@dataclass(frozen=True)
class CandidateSimilarEventMemoryDigestConfig:
    config_version: str = DEFAULT_CANDIDATE_SIMILAR_EVENT_MEMORY_DIGEST_CONFIG_VERSION
    min_pass_similar_event_count: Decimal = DEFAULT_MIN_PASS_SIMILAR_EVENT_COUNT
    min_watch_similar_event_count: Decimal = DEFAULT_MIN_WATCH_SIMILAR_EVENT_COUNT
    min_pass_median_similarity: Decimal = DEFAULT_MIN_PASS_MEDIAN_SIMILARITY
    min_watch_median_similarity: Decimal = DEFAULT_MIN_WATCH_MEDIAN_SIMILARITY
    min_pass_settlement_quality: Decimal = DEFAULT_MIN_PASS_SETTLEMENT_QUALITY
    min_watch_settlement_quality: Decimal = DEFAULT_MIN_WATCH_SETTLEMENT_QUALITY
    min_pass_recency_score: Decimal = DEFAULT_MIN_PASS_RECENCY_SCORE
    min_watch_recency_score: Decimal = DEFAULT_MIN_WATCH_RECENCY_SCORE
    max_pass_outcome_dispersion: Decimal = DEFAULT_MAX_PASS_OUTCOME_DISPERSION
    max_watch_outcome_dispersion: Decimal = DEFAULT_MAX_WATCH_OUTCOME_DISPERSION
    extreme_base_rate_low: Decimal = DEFAULT_EXTREME_BASE_RATE_LOW
    extreme_base_rate_high: Decimal = DEFAULT_EXTREME_BASE_RATE_HIGH
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateSimilarEventMemoryDigestConfig:
            raise TypeError(
                "CandidateSimilarEventMemoryDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateSimilarEventMemoryDigestConfig:
            raise ValueError(
                "config must be exactly CandidateSimilarEventMemoryDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_SIMILAR_EVENT_MEMORY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_similar_event_count",
            "min_watch_similar_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_median_similarity",
            "min_watch_median_similarity",
            "min_pass_settlement_quality",
            "min_watch_settlement_quality",
            "min_pass_recency_score",
            "min_watch_recency_score",
            "max_pass_outcome_dispersion",
            "max_watch_outcome_dispersion",
            "extreme_base_rate_low",
            "extreme_base_rate_high",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class CandidateSimilarEventTeamMemoryBaseline:
    team_id: str
    historical_candidate_count: Decimal
    historical_pass_ratio: Decimal
    historical_watch_ratio: Decimal
    historical_block_ratio: Decimal
    historical_average_memory_support_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateSimilarEventTeamMemoryBaseline:
            raise TypeError(
                "CandidateSimilarEventTeamMemoryBaseline does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateSimilarEventTeamMemoryBaseline:
            raise ValueError(
                "team memory baseline must be exactly "
                "CandidateSimilarEventTeamMemoryBaseline",
            )
        object.__setattr__(self, "team_id", _require_safe_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "historical_candidate_count",
            _normalize_nonnegative_count(
                "historical_candidate_count",
                self.historical_candidate_count,
            ),
        )
        for field_name in (
            "historical_pass_ratio",
            "historical_watch_ratio",
            "historical_block_ratio",
            "historical_average_memory_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _validate_team_memory_baseline(self)
        _require_hard_flags("team memory baseline", self)


@dataclass(frozen=True)
class CandidateSimilarEventMemoryFacts:
    redacted_candidate_ref: str
    team_id: str
    similar_event_count: Decimal
    median_similarity: Decimal
    median_base_rate: Decimal
    outcome_dispersion: Decimal
    average_settlement_quality: Decimal
    recency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateSimilarEventMemoryFacts:
            raise TypeError(
                "CandidateSimilarEventMemoryFacts does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateSimilarEventMemoryFacts:
            raise ValueError("facts must be exactly CandidateSimilarEventMemoryFacts")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        object.__setattr__(self, "team_id", _require_safe_team_id("team_id", self.team_id))
        object.__setattr__(
            self,
            "similar_event_count",
            _normalize_nonnegative_count(
                "similar_event_count",
                self.similar_event_count,
            ),
        )
        for field_name in (
            "median_similarity",
            "median_base_rate",
            "outcome_dispersion",
            "average_settlement_quality",
            "recency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("facts", self)


@dataclass(frozen=True)
class CandidateSimilarEventMemoryDigestRow:
    redacted_candidate_ref: str
    team_id: str
    support_status: str
    similar_event_count: Decimal
    median_similarity: Decimal
    median_base_rate: Decimal
    outcome_dispersion: Decimal
    average_settlement_quality: Decimal
    recency_score: Decimal
    memory_support_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateSimilarEventMemoryDigestRow:
            raise TypeError(
                "CandidateSimilarEventMemoryDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateSimilarEventMemoryDigestRow:
            raise ValueError("row must be exactly CandidateSimilarEventMemoryDigestRow")
        object.__setattr__(
            self,
            "redacted_candidate_ref",
            _require_redacted_candidate_ref(
                "redacted_candidate_ref",
                self.redacted_candidate_ref,
            ),
        )
        object.__setattr__(self, "team_id", _require_safe_team_id("team_id", self.team_id))
        _require_support_status("support_status", self.support_status)
        object.__setattr__(
            self,
            "similar_event_count",
            _normalize_nonnegative_count(
                "similar_event_count",
                self.similar_event_count,
            ),
        )
        for field_name in (
            "median_similarity",
            "median_base_rate",
            "outcome_dispersion",
            "average_settlement_quality",
            "recency_score",
            "memory_support_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                require_nonempty=True,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class CandidateSimilarEventMemoryReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateSimilarEventMemoryReasonCodeCount:
            raise TypeError(
                "CandidateSimilarEventMemoryReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateSimilarEventMemoryReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "CandidateSimilarEventMemoryReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        object.__setattr__(
            self,
            "candidate_ratio",
            _normalize_ratio("candidate_ratio", self.candidate_ratio),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class CandidateSimilarEventMemoryDigestReport:
    generated_at: datetime
    config_version: str
    support_status: str
    report_status: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    team_count: Decimal
    average_memory_support_score: Decimal
    historical_candidate_count: Decimal
    historical_average_memory_support_score: Decimal
    memory_support_score_delta: Decimal
    pass_ratio_delta: Decimal
    block_ratio_delta: Decimal
    team_memory_baselines: tuple[CandidateSimilarEventTeamMemoryBaseline, ...]
    rows: tuple[CandidateSimilarEventMemoryDigestRow, ...]
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[CandidateSimilarEventMemoryReasonCodeCount, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not CandidateSimilarEventMemoryDigestReport:
            raise TypeError(
                "CandidateSimilarEventMemoryDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not CandidateSimilarEventMemoryDigestReport:
            raise ValueError(
                "report must be exactly CandidateSimilarEventMemoryDigestReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_CANDIDATE_SIMILAR_EVENT_MEMORY_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_support_status("support_status", self.support_status)
        _require_support_status("report_status", self.report_status)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
            "team_count",
            "historical_candidate_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_support_score",
            _normalize_ratio(
                "average_memory_support_score",
                self.average_memory_support_score,
            ),
        )
        object.__setattr__(
            self,
            "historical_average_memory_support_score",
            _normalize_ratio(
                "historical_average_memory_support_score",
                self.historical_average_memory_support_score,
            ),
        )
        for field_name in (
            "memory_support_score_delta",
            "pass_ratio_delta",
            "block_ratio_delta",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_delta(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_memory_baselines",
            _normalize_team_memory_baselines(self.team_memory_baselines),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                require_nonempty=True,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_candidate_similar_event_memory_digest(
    facts: Iterable[CandidateSimilarEventMemoryFacts],
    *,
    generated_at: datetime,
    config: CandidateSimilarEventMemoryDigestConfig | None = None,
    team_memory_baselines: Iterable[CandidateSimilarEventTeamMemoryBaseline] = (),
) -> CandidateSimilarEventMemoryDigestReport:
    cfg = config or CandidateSimilarEventMemoryDigestConfig()
    if type(cfg) is not CandidateSimilarEventMemoryDigestConfig:
        raise ValueError("config must be a CandidateSimilarEventMemoryDigestConfig")
    _require_hard_flags("config", cfg)
    generated = _as_utc("generated_at", generated_at)
    normalized_facts = _normalize_facts(facts)
    normalized_baselines = _normalize_team_memory_baselines(team_memory_baselines)
    rows = tuple(sorted((_build_row(item, cfg) for item in normalized_facts), key=_row_sort_key))
    _validate_team_memory_baseline_coverage(rows, normalized_baselines)
    reason_codes = _combined_reason_codes(rows)
    historical_candidate_count = _sum_counts(
        tuple(baseline.historical_candidate_count for baseline in normalized_baselines),
    )
    historical_average_memory_support_score = _weighted_historical_ratio(
        normalized_baselines,
        "historical_average_memory_support_score",
    )
    has_historical_memory = historical_candidate_count > ZERO
    current_average_memory_support_score = _average_ratio(
        tuple(row.memory_support_score for row in rows),
    )
    current_pass_ratio = _ratio(_status_count(rows, "pass"), _count_decimal(len(rows)))
    current_block_ratio = _ratio(_status_count(rows, "block"), _count_decimal(len(rows)))
    support_status = _support_status(rows)

    return CandidateSimilarEventMemoryDigestReport(
        generated_at=generated,
        config_version=cfg.config_version,
        support_status=support_status,
        report_status=support_status,
        candidate_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        team_count=_count_decimal(len({row.team_id for row in rows})),
        average_memory_support_score=current_average_memory_support_score,
        historical_candidate_count=historical_candidate_count,
        historical_average_memory_support_score=historical_average_memory_support_score,
        memory_support_score_delta=_ratio_delta(
            current_average_memory_support_score,
            historical_average_memory_support_score,
        ) if has_historical_memory else ZERO,
        pass_ratio_delta=_ratio_delta(
            current_pass_ratio,
            _weighted_historical_ratio(normalized_baselines, "historical_pass_ratio"),
        ) if has_historical_memory else ZERO,
        block_ratio_delta=_ratio_delta(
            current_block_ratio,
            _weighted_historical_ratio(normalized_baselines, "historical_block_ratio"),
        ) if has_historical_memory else ZERO,
        team_memory_baselines=normalized_baselines,
        rows=rows,
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes, rows),
    )


def candidate_similar_event_memory_digest_payload(
    report: CandidateSimilarEventMemoryDigestReport,
) -> dict[str, Any]:
    if type(report) is not CandidateSimilarEventMemoryDigestReport:
        raise ValueError("report must be a CandidateSimilarEventMemoryDigestReport")
    _require_hard_flags("report", report)
    payload = _json_compatible(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _build_row(
    facts: CandidateSimilarEventMemoryFacts,
    config: CandidateSimilarEventMemoryDigestConfig,
) -> CandidateSimilarEventMemoryDigestRow:
    support_status = _row_support_status(facts, config)
    return CandidateSimilarEventMemoryDigestRow(
        redacted_candidate_ref=facts.redacted_candidate_ref,
        team_id=facts.team_id,
        support_status=support_status,
        similar_event_count=facts.similar_event_count,
        median_similarity=facts.median_similarity,
        median_base_rate=facts.median_base_rate,
        outcome_dispersion=facts.outcome_dispersion,
        average_settlement_quality=facts.average_settlement_quality,
        recency_score=facts.recency_score,
        memory_support_score=_memory_support_score(facts, config),
        reason_codes=_row_reason_codes(facts, support_status, config),
    )


def _row_support_status(
    facts: CandidateSimilarEventMemoryFacts,
    config: CandidateSimilarEventMemoryDigestConfig,
) -> str:
    if (
        facts.similar_event_count < config.min_watch_similar_event_count
        or facts.median_similarity < config.min_watch_median_similarity
        or facts.average_settlement_quality < config.min_watch_settlement_quality
        or facts.recency_score < config.min_watch_recency_score
        or facts.outcome_dispersion > config.max_watch_outcome_dispersion
    ):
        return "block"
    if (
        facts.similar_event_count >= config.min_pass_similar_event_count
        and facts.median_similarity >= config.min_pass_median_similarity
        and facts.average_settlement_quality >= config.min_pass_settlement_quality
        and facts.recency_score >= config.min_pass_recency_score
        and facts.outcome_dispersion <= config.max_pass_outcome_dispersion
        and not _is_extreme_base_rate(facts.median_base_rate, config)
    ):
        return "pass"
    return "watch"


def _row_reason_codes(
    facts: CandidateSimilarEventMemoryFacts,
    support_status: str,
    config: CandidateSimilarEventMemoryDigestConfig,
) -> tuple[str, ...]:
    found: list[str] = [STATUS_REASON[support_status]]
    if facts.similar_event_count == ZERO:
        found.append(EMPTY_ROW_REASON)
    if facts.similar_event_count < config.min_watch_similar_event_count:
        found.append("similar_event_count_low")
    elif facts.similar_event_count < config.min_pass_similar_event_count:
        found.append("similar_event_count_watch")
    if facts.median_similarity < config.min_watch_median_similarity:
        found.append("median_similarity_low")
    elif facts.median_similarity < config.min_pass_median_similarity:
        found.append("median_similarity_watch")
    if facts.average_settlement_quality < config.min_watch_settlement_quality:
        found.append("settlement_quality_low")
    elif facts.average_settlement_quality < config.min_pass_settlement_quality:
        found.append("settlement_quality_watch")
    if facts.recency_score < config.min_watch_recency_score:
        found.append("recency_low")
    elif facts.recency_score < config.min_pass_recency_score:
        found.append("recency_watch")
    if facts.outcome_dispersion > config.max_watch_outcome_dispersion:
        found.append("outcome_dispersion_high")
    elif facts.outcome_dispersion > config.max_pass_outcome_dispersion:
        found.append("outcome_dispersion_watch")
    if _is_extreme_base_rate(facts.median_base_rate, config):
        found.append("base_rate_extreme")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in found)


def _memory_support_score(
    facts: CandidateSimilarEventMemoryFacts,
    config: CandidateSimilarEventMemoryDigestConfig,
) -> Decimal:
    count_score = _capped_ratio(
        facts.similar_event_count,
        config.min_pass_similar_event_count,
    )
    outcome_stability = (ONE - facts.outcome_dispersion).quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return (
            (facts.median_similarity * Decimal("0.300000"))
            + (facts.average_settlement_quality * Decimal("0.250000"))
            + (facts.recency_score * Decimal("0.200000"))
            + (outcome_stability * Decimal("0.100000"))
            + (_base_rate_balance_score(facts.median_base_rate) * Decimal("0.100000"))
            + (count_score * Decimal("0.050000"))
        ).quantize(RATIO_QUANTUM)


def _base_rate_balance_score(base_rate: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        distance = abs(base_rate - HALF)
        return (ONE - (distance / HALF)).quantize(RATIO_QUANTUM)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio <= ZERO:
        return ZERO
    if ratio >= ONE:
        return ONE
    return ratio.quantize(RATIO_QUANTUM)


def _is_extreme_base_rate(
    median_base_rate: Decimal,
    config: CandidateSimilarEventMemoryDigestConfig,
) -> bool:
    return (
        median_base_rate <= config.extreme_base_rate_low
        or median_base_rate >= config.extreme_base_rate_high
    )


def _support_status(rows: tuple[CandidateSimilarEventMemoryDigestRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.support_status == "block" for row in rows):
        return "block"
    if any(row.support_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _combined_reason_codes(
    rows: tuple[CandidateSimilarEventMemoryDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON,)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in found)


def _reason_code_counts(
    reason_codes: tuple[str, ...],
    rows: tuple[CandidateSimilarEventMemoryDigestRow, ...],
) -> tuple[CandidateSimilarEventMemoryReasonCodeCount, ...]:
    candidate_count = _count_decimal(len(rows))
    if reason_codes == (EMPTY_REPORT_REASON,):
        return (
            CandidateSimilarEventMemoryReasonCodeCount(
                reason_code=EMPTY_REPORT_REASON,
                count=ONE,
                candidate_ratio=ZERO,
            ),
        )
    return tuple(
        CandidateSimilarEventMemoryReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(
                sum(1 for row in rows if reason_code in row.reason_codes),
            ),
            candidate_ratio=_ratio(
                _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes)),
                candidate_count,
            ),
        )
        for reason_code in reason_codes
    )


def _row_sort_key(
    row: CandidateSimilarEventMemoryDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_SORT_WEIGHT[row.support_status],
        -row.memory_support_score,
        row.team_id,
        row.redacted_candidate_ref,
    )


def _status_count(
    rows: tuple[CandidateSimilarEventMemoryDigestRow, ...],
    support_status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.support_status == support_status))


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(COUNT_QUANTUM)


def _weighted_historical_ratio(
    baselines: tuple[CandidateSimilarEventTeamMemoryBaseline, ...],
    field_name: str,
) -> Decimal:
    total_count = _sum_counts(
        tuple(baseline.historical_candidate_count for baseline in baselines),
    )
    if total_count == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        weighted_sum = sum(
            (
                baseline.historical_candidate_count
                * getattr(baseline, field_name)
            )
            for baseline in baselines
        )
        return (weighted_sum / total_count).quantize(RATIO_QUANTUM)


def _ratio_delta(current: Decimal, historical: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (current - historical).quantize(RATIO_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _normalize_facts(
    facts: Iterable[CandidateSimilarEventMemoryFacts],
) -> tuple[CandidateSimilarEventMemoryFacts, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must contain CandidateSimilarEventMemoryFacts rows")
    try:
        normalized = tuple(facts)
    except TypeError as exc:
        raise ValueError("facts must contain CandidateSimilarEventMemoryFacts rows") from exc
    seen_refs: set[str] = set()
    for item in normalized:
        if type(item) is not CandidateSimilarEventMemoryFacts:
            raise ValueError("facts must contain CandidateSimilarEventMemoryFacts rows")
        _require_hard_flags("facts", item)
        if item.redacted_candidate_ref in seen_refs:
            raise ValueError("facts must not contain duplicate redacted_candidate_ref values")
        seen_refs.add(item.redacted_candidate_ref)
    return normalized


def _normalize_team_memory_baselines(
    baselines: Iterable[CandidateSimilarEventTeamMemoryBaseline],
) -> tuple[CandidateSimilarEventTeamMemoryBaseline, ...]:
    if isinstance(baselines, (str, bytes)):
        raise ValueError(
            "team_memory_baselines must contain "
            "CandidateSimilarEventTeamMemoryBaseline rows",
        )
    try:
        normalized = tuple(baselines)
    except TypeError as exc:
        raise ValueError(
            "team_memory_baselines must contain "
            "CandidateSimilarEventTeamMemoryBaseline rows",
        ) from exc
    seen_team_ids: set[str] = set()
    for baseline in normalized:
        if type(baseline) is not CandidateSimilarEventTeamMemoryBaseline:
            raise ValueError(
                "team_memory_baselines must contain "
                "CandidateSimilarEventTeamMemoryBaseline rows",
            )
        _require_hard_flags("team memory baseline", baseline)
        if baseline.team_id in seen_team_ids:
            raise ValueError("team_memory_baselines must not contain duplicate team_id values")
        seen_team_ids.add(baseline.team_id)
    return tuple(sorted(normalized, key=lambda baseline: baseline.team_id))


def _validate_team_memory_baseline_coverage(
    rows: tuple[CandidateSimilarEventMemoryDigestRow, ...],
    baselines: tuple[CandidateSimilarEventTeamMemoryBaseline, ...],
) -> None:
    if not baselines:
        return
    row_team_ids = {row.team_id for row in rows}
    baseline_team_ids = {baseline.team_id for baseline in baselines}
    if baseline_team_ids != row_team_ids:
        raise ValueError("team_memory_baselines must match digest row team_id values")


def _normalize_rows(
    rows: tuple[CandidateSimilarEventMemoryDigestRow, ...],
) -> tuple[CandidateSimilarEventMemoryDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not CandidateSimilarEventMemoryDigestRow:
            raise ValueError("rows must contain CandidateSimilarEventMemoryDigestRow values")
        _require_hard_flags("row", row)
        if row.redacted_candidate_ref in seen_refs:
            raise ValueError("rows must not contain duplicate redacted_candidate_ref values")
        seen_refs.add(row.redacted_candidate_ref)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    values: tuple[CandidateSimilarEventMemoryReasonCodeCount, ...],
) -> tuple[CandidateSimilarEventMemoryReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not CandidateSimilarEventMemoryReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
        _require_hard_flags("reason code count", value)
        if value.reason_code in seen:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen.add(value.reason_code)
    if values != tuple(sorted(values, key=lambda value: REASON_CODES.index(value.reason_code))):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return values


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    *,
    require_nonempty: bool = False,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for value in values:
        _require_reason_code(field_name, value)
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(value)
    if require_nonempty and not values:
        raise ValueError(f"{field_name} must not be empty")
    normalized = tuple(values)
    if normalized != tuple(reason_code for reason_code in REASON_CODES if reason_code in seen):
        raise ValueError(f"{field_name} must be sorted deterministically")
    return normalized


def _validate_config(config: CandidateSimilarEventMemoryDigestConfig) -> None:
    if config.min_watch_similar_event_count > config.min_pass_similar_event_count:
        raise ValueError("min_watch_similar_event_count must be <= pass threshold")
    if config.min_watch_median_similarity > config.min_pass_median_similarity:
        raise ValueError("min_watch_median_similarity must be <= pass threshold")
    if config.min_watch_settlement_quality > config.min_pass_settlement_quality:
        raise ValueError("min_watch_settlement_quality must be <= pass threshold")
    if config.min_watch_recency_score > config.min_pass_recency_score:
        raise ValueError("min_watch_recency_score must be <= pass threshold")
    if config.max_watch_outcome_dispersion < config.max_pass_outcome_dispersion:
        raise ValueError("max_watch_outcome_dispersion must be >= pass threshold")
    if config.extreme_base_rate_low >= config.extreme_base_rate_high:
        raise ValueError("extreme_base_rate_low must be below high threshold")


def _validate_team_memory_baseline(
    baseline: CandidateSimilarEventTeamMemoryBaseline,
) -> None:
    if baseline.historical_candidate_count == ZERO:
        if (
            baseline.historical_pass_ratio != ZERO
            or baseline.historical_watch_ratio != ZERO
            or baseline.historical_block_ratio != ZERO
            or baseline.historical_average_memory_support_score != ZERO
        ):
            raise ValueError("zero historical_candidate_count requires zero historical ratios")
        return
    status_ratio_total = _ratio_delta(
        (
            baseline.historical_pass_ratio
            + baseline.historical_watch_ratio
            + baseline.historical_block_ratio
        ),
        ONE,
    )
    if status_ratio_total != ZERO:
        raise ValueError("historical status ratios must sum to one")


def _validate_row(row: CandidateSimilarEventMemoryDigestRow) -> None:
    expected_status_reason = STATUS_REASON[row.support_status]
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include support status reason")
    if row.support_status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("reason_codes must match pass support status")
    if row.support_status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("reason_codes must match support status")


def _validate_report(report: CandidateSimilarEventMemoryDigestReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.team_count != _count_decimal(len({row.team_id for row in report.rows})):
        raise ValueError("team_count must match rows")
    if report.support_status != _support_status(report.rows):
        raise ValueError("support_status must match rows")
    if report.report_status != report.support_status:
        raise ValueError("report_status must match support_status")
    if report.average_memory_support_score != _average_ratio(
        tuple(row.memory_support_score for row in report.rows),
    ):
        raise ValueError("average_memory_support_score must match rows")
    _validate_team_memory_baseline_coverage(report.rows, report.team_memory_baselines)
    if report.historical_candidate_count != _sum_counts(
        tuple(
            baseline.historical_candidate_count
            for baseline in report.team_memory_baselines
        ),
    ):
        raise ValueError("historical_candidate_count must match team_memory_baselines")
    if report.historical_average_memory_support_score != _weighted_historical_ratio(
        report.team_memory_baselines,
        "historical_average_memory_support_score",
    ):
        raise ValueError(
            "historical_average_memory_support_score must match team_memory_baselines",
        )
    if report.historical_candidate_count == ZERO:
        if report.memory_support_score_delta != ZERO:
            raise ValueError("memory_support_score_delta must be zero without history")
        if report.pass_ratio_delta != ZERO:
            raise ValueError("pass_ratio_delta must be zero without history")
        if report.block_ratio_delta != ZERO:
            raise ValueError("block_ratio_delta must be zero without history")
        if report.reason_codes != _combined_reason_codes(report.rows):
            raise ValueError("reason_codes must match rows")
        if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
            raise ValueError("reason_code_counts must match reason_codes")
        return
    if report.memory_support_score_delta != _ratio_delta(
        report.average_memory_support_score,
        report.historical_average_memory_support_score,
    ):
        raise ValueError("memory_support_score_delta must match historical comparison")
    if report.pass_ratio_delta != _ratio_delta(
        _ratio(report.pass_count, report.candidate_count),
        _weighted_historical_ratio(report.team_memory_baselines, "historical_pass_ratio"),
    ):
        raise ValueError("pass_ratio_delta must match historical comparison")
    if report.block_ratio_delta != _ratio_delta(
        _ratio(report.block_count, report.candidate_count),
        _weighted_historical_ratio(report.team_memory_baselines, "historical_block_ratio"),
    ):
        raise ValueError("block_ratio_delta must match historical comparison")
    if report.reason_codes != _combined_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes, report.rows):
        raise ValueError("reason_code_counts must match reason_codes")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.quantize(INTEGER_QUANTUM):
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_ratio_delta(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < -ONE or normalized > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            normalized = +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    return normalized.quantize(RATIO_QUANTUM)


def _require_redacted_candidate_ref(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_safe_team_id(field_name: str, value: object) -> str:
    team_id = require_team_id(field_name, value)
    _reject_unsafe_public_text(field_name, team_id)
    return team_id


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")
    if _CANONICAL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be canonical lowercase text")


def _require_support_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SUPPORT_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name, None)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _json_compatible(value: Any) -> Any:
    if isinstance(value, dict):
        converted: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            converted[key] = _json_compatible(item)
        return converted
    if isinstance(value, tuple):
        return [_json_compatible(item) for item in value]
    if isinstance(value, list):
        return [_json_compatible(item) for item in value]
    if type(value) is Decimal:
        return format(value.quantize(RATIO_QUANTUM), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or value is None or type(value) is str:
        return value
    if type(value) in {float, int}:
        raise ValueError("payload contains a non-Decimal numeric value")
    raise ValueError("payload contains an unsupported value")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")
