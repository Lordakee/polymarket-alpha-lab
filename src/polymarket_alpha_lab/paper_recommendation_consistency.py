"""Standalone consistency reducer for supplied paper recommendation facts."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal


__all__ = (
    "PaperRecommendationConsistencyFact",
    "PaperRecommendationConsistencyConfig",
    "PaperRecommendationConsistencyRow",
    "PaperRecommendationConsistencyReport",
    "build_paper_recommendation_consistency_report",
)


ZERO = Decimal("0")
QUANTUM = Decimal("0.000001")
STATUSES = ("pass", "watch", "blocked")
PASS_REASON_CODE = "recommendation_consistency_passed"
EMPTY_REASON_CODE = "empty_recommendation_facts"
BLOCKING_REASON_CODES = (
    "edge_spread_exceeds_consistency_cap",
    "score_spread_exceeds_consistency_cap",
)
WATCH_REASON_CODES = (
    "missing_recommendation_sources",
    "recommendation_status_disagreement",
)
REPORT_REASON_CODES = (
    EMPTY_REASON_CODE,
    *BLOCKING_REASON_CODES,
    *WATCH_REASON_CODES,
    PASS_REASON_CODE,
)


@dataclass(frozen=True)
class PaperRecommendationConsistencyFact:
    market_slug: str
    side: str
    source_name: str
    action_or_status: str
    net_probability_edge: Decimal
    recommendation_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("side", self.side)
        _require_canonical_string("source_name", self.source_name)
        _require_canonical_string("action_or_status", self.action_or_status)
        object.__setattr__(
            self,
            "net_probability_edge",
            _quantize_decimal("net_probability_edge", self.net_probability_edge),
        )
        object.__setattr__(
            self,
            "recommendation_score",
            _quantize_nonnegative_decimal(
                "recommendation_score",
                self.recommendation_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_source_reason_codes(self.reason_codes),
        )
        _validate_hard_flags(self)


@dataclass(frozen=True)
class PaperRecommendationConsistencyConfig:
    config_version: str
    max_edge_spread: Decimal
    max_score_spread: Decimal
    min_source_count: int

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_quantized_nonnegative_decimal("max_edge_spread", self.max_edge_spread)
        _require_quantized_nonnegative_decimal(
            "max_score_spread",
            self.max_score_spread,
        )
        _require_positive_int("min_source_count", self.min_source_count)


@dataclass(frozen=True)
class PaperRecommendationConsistencyRow:
    market_slug: str
    side: str
    source_count: int
    distinct_statuses: tuple[str, ...]
    edge_min: Decimal
    edge_max: Decimal
    edge_spread: Decimal
    score_min: Decimal
    score_max: Decimal
    score_spread: Decimal
    consistency_status: str
    reason_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("side", self.side)
        _require_positive_int("source_count", self.source_count)
        object.__setattr__(
            self,
            "distinct_statuses",
            _normalize_distinct_statuses(self.distinct_statuses),
        )
        _require_quantized_decimal("edge_min", self.edge_min)
        _require_quantized_decimal("edge_max", self.edge_max)
        _require_quantized_nonnegative_decimal("edge_spread", self.edge_spread)
        _require_quantized_nonnegative_decimal("score_min", self.score_min)
        _require_quantized_nonnegative_decimal("score_max", self.score_max)
        _require_quantized_nonnegative_decimal("score_spread", self.score_spread)
        _require_status("consistency_status", self.consistency_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)


@dataclass(frozen=True)
class PaperRecommendationConsistencyReport:
    generated_at: datetime
    config_version: str
    group_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    consistency_status: str
    consistency_rows: tuple[PaperRecommendationConsistencyRow, ...]
    reason_codes: tuple[str, ...]
    max_edge_spread: Decimal
    max_score_spread: Decimal
    min_source_count: int
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_nonnegative_int("group_count", self.group_count)
        _require_nonnegative_int("pass_count", self.pass_count)
        _require_nonnegative_int("watch_count", self.watch_count)
        _require_nonnegative_int("blocked_count", self.blocked_count)
        _require_status("consistency_status", self.consistency_status)
        object.__setattr__(
            self,
            "consistency_rows",
            _normalize_rows(self.consistency_rows),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        _require_quantized_nonnegative_decimal("max_edge_spread", self.max_edge_spread)
        _require_quantized_nonnegative_decimal(
            "max_score_spread",
            self.max_score_spread,
        )
        _require_positive_int("min_source_count", self.min_source_count)
        _validate_report_consistency(self)
        _validate_hard_flags(self)


def build_paper_recommendation_consistency_report(
    facts: Iterable[PaperRecommendationConsistencyFact],
    *,
    config: PaperRecommendationConsistencyConfig,
    generated_at: datetime,
) -> PaperRecommendationConsistencyReport:
    if type(config) is not PaperRecommendationConsistencyConfig:
        raise ValueError("config must be a PaperRecommendationConsistencyConfig")

    generated_at = _as_utc(generated_at)
    normalized_facts = _normalize_facts(facts)
    rows = _build_rows(normalized_facts, config)
    pass_count = _row_status_count(rows, "pass")
    watch_count = _row_status_count(rows, "watch")
    blocked_count = _row_status_count(rows, "blocked")

    return PaperRecommendationConsistencyReport(
        generated_at=generated_at,
        config_version=config.config_version,
        group_count=len(rows),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        consistency_status=_report_status(rows),
        consistency_rows=rows,
        reason_codes=_report_reason_codes(rows),
        max_edge_spread=config.max_edge_spread,
        max_score_spread=config.max_score_spread,
        min_source_count=config.min_source_count,
    )


def _build_rows(
    facts: tuple[PaperRecommendationConsistencyFact, ...],
    config: PaperRecommendationConsistencyConfig,
) -> tuple[PaperRecommendationConsistencyRow, ...]:
    grouped: dict[
        tuple[str, str],
        list[PaperRecommendationConsistencyFact],
    ] = {}
    for fact in facts:
        grouped.setdefault((fact.market_slug, fact.side), []).append(fact)

    return tuple(
        _build_row(market_slug, side, tuple(grouped[(market_slug, side)]), config)
        for market_slug, side in sorted(grouped)
    )


def _build_row(
    market_slug: str,
    side: str,
    facts: tuple[PaperRecommendationConsistencyFact, ...],
    config: PaperRecommendationConsistencyConfig,
) -> PaperRecommendationConsistencyRow:
    edges = tuple(fact.net_probability_edge for fact in facts)
    scores = tuple(fact.recommendation_score for fact in facts)
    edge_min = min(edges)
    edge_max = max(edges)
    score_min = min(scores)
    score_max = max(scores)
    edge_spread = _quantize_nonnegative_decimal("edge_spread", edge_max - edge_min)
    score_spread = _quantize_nonnegative_decimal("score_spread", score_max - score_min)
    distinct_statuses = tuple(sorted({fact.action_or_status for fact in facts}))
    source_count = len({fact.source_name for fact in facts})
    reason_codes = _row_reason_codes(
        source_count=source_count,
        distinct_statuses=distinct_statuses,
        edge_spread=edge_spread,
        score_spread=score_spread,
        config=config,
    )

    return PaperRecommendationConsistencyRow(
        market_slug=market_slug,
        side=side,
        source_count=source_count,
        distinct_statuses=distinct_statuses,
        edge_min=edge_min,
        edge_max=edge_max,
        edge_spread=edge_spread,
        score_min=score_min,
        score_max=score_max,
        score_spread=score_spread,
        consistency_status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    source_count: int,
    distinct_statuses: tuple[str, ...],
    edge_spread: Decimal,
    score_spread: Decimal,
    config: PaperRecommendationConsistencyConfig,
) -> tuple[str, ...]:
    blocking_reasons: list[str] = []
    watch_reasons: list[str] = []

    if edge_spread > config.max_edge_spread:
        blocking_reasons.append("edge_spread_exceeds_consistency_cap")
    if score_spread > config.max_score_spread:
        blocking_reasons.append("score_spread_exceeds_consistency_cap")
    if source_count < config.min_source_count:
        watch_reasons.append("missing_recommendation_sources")
    if len(distinct_statuses) > 1:
        watch_reasons.append("recommendation_status_disagreement")

    reason_codes = tuple(blocking_reasons + watch_reasons)
    if reason_codes:
        return reason_codes
    return (PASS_REASON_CODE,)


def _report_status(rows: tuple[PaperRecommendationConsistencyRow, ...]) -> str:
    if not rows:
        return "blocked"
    if any(row.consistency_status == "blocked" for row in rows):
        return "blocked"
    if any(row.consistency_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[PaperRecommendationConsistencyRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)

    active = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON_CODE
    }
    if not active:
        return (PASS_REASON_CODE,)
    return tuple(reason_code for reason_code in REPORT_REASON_CODES if reason_code in active)


def _row_status_count(
    rows: tuple[PaperRecommendationConsistencyRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.consistency_status == status)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if EMPTY_REASON_CODE in reason_codes:
        return "blocked"
    if any(reason_code in BLOCKING_REASON_CODES for reason_code in reason_codes):
        return "blocked"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _validate_row_consistency(row: PaperRecommendationConsistencyRow) -> None:
    if row.edge_min > row.edge_max:
        raise ValueError("edge_min must be at most edge_max")
    if row.score_min > row.score_max:
        raise ValueError("score_min must be at most score_max")
    if row.edge_spread != _quantize_nonnegative_decimal(
        "edge_spread",
        row.edge_max - row.edge_min,
    ):
        raise ValueError("edge_spread must match edge_min and edge_max")
    if row.score_spread != _quantize_nonnegative_decimal(
        "score_spread",
        row.score_max - row.score_min,
    ):
        raise ValueError("score_spread must match score_min and score_max")
    if row.consistency_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("reason_codes must match consistency_status")


def _validate_report_consistency(report: PaperRecommendationConsistencyReport) -> None:
    rows = report.consistency_rows
    if report.group_count != len(rows):
        raise ValueError("group_count must match consistency_rows")
    if report.pass_count != _row_status_count(rows, "pass"):
        raise ValueError("pass_count must match consistency_rows")
    if report.watch_count != _row_status_count(rows, "watch"):
        raise ValueError("watch_count must match consistency_rows")
    if report.blocked_count != _row_status_count(rows, "blocked"):
        raise ValueError("blocked_count must match consistency_rows")
    if report.consistency_status != _report_status(rows):
        raise ValueError("consistency_status must match consistency_rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match consistency_rows")


def _normalize_facts(
    facts: Iterable[PaperRecommendationConsistencyFact],
) -> tuple[PaperRecommendationConsistencyFact, ...]:
    if isinstance(facts, (str, bytes)):
        raise ValueError("facts must be an iterable of PaperRecommendationConsistencyFact")
    try:
        normalized = tuple(facts)
    except TypeError as exc:
        raise ValueError(
            "facts must be an iterable of PaperRecommendationConsistencyFact",
        ) from exc
    for fact in normalized:
        if type(fact) is not PaperRecommendationConsistencyFact:
            raise ValueError(
                "facts must contain PaperRecommendationConsistencyFact values",
            )
        _validate_hard_flags(fact)
    return normalized


def _normalize_rows(
    rows: tuple[PaperRecommendationConsistencyRow, ...],
) -> tuple[PaperRecommendationConsistencyRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("consistency_rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("consistency_rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not PaperRecommendationConsistencyRow:
            raise ValueError(
                "consistency_rows must contain PaperRecommendationConsistencyRow values",
            )
    if normalized != tuple(sorted(normalized, key=lambda row: (row.market_slug, row.side))):
        raise ValueError("consistency_rows must be sorted by market_slug and side")
    return normalized


def _normalize_source_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "reason_codes",
        value,
        require_nonempty=True,
        require_unique=True,
        sort_items=False,
    )


def _normalize_distinct_statuses(value: tuple[str, ...]) -> tuple[str, ...]:
    return _normalize_string_tuple(
        "distinct_statuses",
        value,
        require_nonempty=True,
        require_unique=True,
        sort_items=True,
    )


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    items = _normalize_string_tuple(
        "reason_codes",
        value,
        require_nonempty=True,
        require_unique=True,
        sort_items=False,
    )
    allowed = set((*BLOCKING_REASON_CODES, *WATCH_REASON_CODES, PASS_REASON_CODE))
    if any(item not in allowed for item in items):
        raise ValueError("reason_codes must match consistency semantics")
    if PASS_REASON_CODE in items and items != (PASS_REASON_CODE,):
        raise ValueError("reason_codes must not mix pass with watch or blocked reasons")
    return items


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    items = _normalize_string_tuple(
        "reason_codes",
        value,
        require_nonempty=True,
        require_unique=True,
        sort_items=False,
    )
    allowed = set(REPORT_REASON_CODES)
    if any(item not in allowed for item in items):
        raise ValueError("reason_codes must match consistency semantics")
    if PASS_REASON_CODE in items and items != (PASS_REASON_CODE,):
        raise ValueError("reason_codes must not mix pass with watch or blocked reasons")
    if EMPTY_REASON_CODE in items and items != (EMPTY_REASON_CODE,):
        raise ValueError("reason_codes must not mix empty facts with row reasons")
    return items


def _normalize_string_tuple(
    field_name: str,
    value: tuple[str, ...],
    *,
    require_nonempty: bool,
    require_unique: bool,
    sort_items: bool,
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if require_nonempty and not items:
        raise ValueError(f"{field_name} must contain at least one value")
    if require_unique and len(set(items)) != len(items):
        raise ValueError(f"{field_name} must not contain duplicates")
    for item in items:
        _require_canonical_string(field_name, item)
    if sort_items:
        return tuple(sorted(items))
    return items


def _as_utc(value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _validate_hard_flags(value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_quantized_decimal(field_name: str, value: object) -> None:
    _require_decimal(field_name, value)
    if value != _quantize_decimal(field_name, value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _require_quantized_nonnegative_decimal(field_name: str, value: object) -> None:
    _require_nonnegative_decimal(field_name, value)
    if value != _quantize_nonnegative_decimal(field_name, value):
        raise ValueError(f"{field_name} must be quantized to 0.000001")


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _quantize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    _require_nonnegative_decimal(field_name, value)
    return value.quantize(QUANTUM)


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_positive_int(field_name: str, value: object) -> None:
    _require_nonnegative_int(field_name, value)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
