from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext

from polymarket_alpha_lab.autonomous_market_scorer import (
    AutonomousMarketScorerReport,
    AutonomousMarketScoreRow,
)


SCORE_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
DECIMAL_CONTEXT = Context(prec=64)
COMPONENT_DIRECTIONS = ("positive", "negative", "neutral")
SCORE_STATUSES = ("pass", "watch", "blocked")
BASE_FLAGS = ("paper_only", "readonly", "report_only")
UNSAFE_FLAGS = frozenset(
    {
        "live_trading",
        "auth_required",
        "wallet_connected",
        "private_key_present",
        "sign_order",
        "submit_order",
        "cancel_order",
        "network_mutation",
        "exchange_write",
    },
)


@dataclass(frozen=True)
class PaperRecommendationScoreComponent:
    component_name: str
    contribution: Decimal
    direction: str
    reason_code: str
    flags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_canonical_string("component_name", self.component_name)
        _require_decimal("contribution", self.contribution)
        if self.direction not in COMPONENT_DIRECTIONS:
            raise ValueError("direction must be positive, negative, or neutral")
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(self, "flags", _normalize_flags(self.flags))


@dataclass(frozen=True)
class PaperRecommendationScoreExplanationRow:
    market_slug: str
    side: str
    total_score: Decimal
    score_status: str
    components: tuple[PaperRecommendationScoreComponent, ...]
    reason_codes: tuple[str, ...]
    flags: tuple[str, ...] = BASE_FLAGS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_slug", self.market_slug)
        _require_canonical_string("side", self.side)
        object.__setattr__(
            self,
            "total_score",
            _normalize_score_decimal("total_score", self.total_score),
        )
        if self.score_status not in SCORE_STATUSES:
            raise ValueError("score_status must be pass, watch, or blocked")
        components = _normalize_components(self.components)
        object.__setattr__(self, "components", components)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "flags", _normalize_flags(self.flags))
        _validate_row_component_names(components)
        _validate_total_score(self.total_score, components)
        _validate_hard_flags(self)


@dataclass(frozen=True)
class PaperRecommendationScoreExplanationReport:
    generated_at: datetime
    config_version: str
    row_count: int
    pass_count: int
    watch_count: int
    blocked_count: int
    average_total_score: Decimal | None
    top_total_score: Decimal | None
    rows: tuple[PaperRecommendationScoreExplanationRow, ...]
    flags: tuple[str, ...] = BASE_FLAGS
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self.generated_at) is not datetime:
            raise ValueError("generated_at must be a datetime")
        object.__setattr__(self, "generated_at", _as_utc(self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "average_total_score",
            _normalize_optional_score_decimal(
                "average_total_score",
                self.average_total_score,
            ),
        )
        object.__setattr__(
            self,
            "top_total_score",
            _normalize_optional_score_decimal("top_total_score", self.top_total_score),
        )
        rows = _normalize_rows(self.rows)
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "flags", _normalize_flags(self.flags))
        _validate_report_consistency(self)
        _validate_hard_flags(self)


def build_paper_recommendation_score_explanation_report(
    *,
    generated_at: datetime,
    config_version: str,
    rows: Iterable[PaperRecommendationScoreExplanationRow],
) -> PaperRecommendationScoreExplanationReport:
    """Build a supplied-input score explanation report for paper recommendations."""

    if type(generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    _require_canonical_string("config_version", config_version)
    normalized_rows = _normalize_rows(rows)
    sorted_rows = tuple(
        sorted(
            normalized_rows,
            key=lambda row: (-row.total_score, row.market_slug, row.side),
        ),
    )
    pass_count = sum(1 for row in sorted_rows if row.score_status == "pass")
    watch_count = sum(1 for row in sorted_rows if row.score_status == "watch")
    blocked_count = sum(1 for row in sorted_rows if row.score_status == "blocked")
    return PaperRecommendationScoreExplanationReport(
        generated_at=generated_at,
        config_version=config_version,
        row_count=len(sorted_rows),
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        average_total_score=_average_score(row.total_score for row in sorted_rows),
        top_total_score=sorted_rows[0].total_score if sorted_rows else None,
        rows=sorted_rows,
        flags=_report_flags(sorted_rows),
    )


def build_autonomous_market_scorer_score_explanation_report(
    report: AutonomousMarketScorerReport,
) -> PaperRecommendationScoreExplanationReport:
    """Bridge an autonomous market scorer report into a report-only explanation."""

    if type(report) is not AutonomousMarketScorerReport:
        raise ValueError("report must be an AutonomousMarketScorerReport")
    return build_paper_recommendation_score_explanation_report(
        generated_at=report.generated_at,
        config_version=report.config_version,
        rows=(
            _autonomous_market_score_row_to_explanation_row(row)
            for row in report.score_rows
        ),
    )


def _autonomous_market_score_row_to_explanation_row(
    row: AutonomousMarketScoreRow,
) -> PaperRecommendationScoreExplanationRow:
    return PaperRecommendationScoreExplanationRow(
        market_slug=row.market_slug,
        side=row.scoring_side,
        total_score=row.total_score,
        score_status=_autonomous_market_score_status(row.score_status),
        components=(
            PaperRecommendationScoreComponent(
                component_name="autonomous_market_scorer_total",
                contribution=row.total_score,
                direction="positive" if row.total_score > ZERO else "neutral",
                reason_code=_autonomous_market_score_component_reason_code(
                    row.reason_codes,
                ),
                flags=("autonomous_market_scorer_explanation",),
            ),
        ),
        reason_codes=row.reason_codes,
        flags=("autonomous_market_scorer_explanation",),
    )


def _autonomous_market_score_status(score_status: str) -> str:
    if score_status == "scored":
        return "pass"
    if score_status == "skipped":
        return "watch"
    if score_status == "blocked":
        return "blocked"
    raise ValueError("score_status must be scored, skipped, or blocked")


def _autonomous_market_score_component_reason_code(
    reason_codes: tuple[str, ...],
) -> str:
    return reason_codes[0] if reason_codes else "autonomous_market_scorer_total_score"


def _normalize_components(
    components: Iterable[PaperRecommendationScoreComponent],
) -> tuple[PaperRecommendationScoreComponent, ...]:
    if isinstance(components, (str, bytes)):
        raise ValueError(
            "components must be an iterable of PaperRecommendationScoreComponent values",
        )
    try:
        items = tuple(components)
    except TypeError as exc:
        raise ValueError(
            "components must be an iterable of PaperRecommendationScoreComponent values",
        ) from exc
    for component in items:
        if type(component) is not PaperRecommendationScoreComponent:
            raise ValueError(
                "components must contain only PaperRecommendationScoreComponent values",
            )
    return items


def _normalize_rows(
    rows: Iterable[PaperRecommendationScoreExplanationRow],
) -> tuple[PaperRecommendationScoreExplanationRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError(
            "rows must be an iterable of PaperRecommendationScoreExplanationRow values",
        )
    try:
        items = tuple(rows)
    except TypeError as exc:
        raise ValueError(
            "rows must be an iterable of PaperRecommendationScoreExplanationRow values",
        ) from exc
    for row in items:
        if type(row) is not PaperRecommendationScoreExplanationRow:
            raise ValueError(
                "rows must contain only PaperRecommendationScoreExplanationRow values",
            )
    return items


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of canonical strings")
    try:
        items = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(
            "reason_codes must be an iterable of canonical strings",
        ) from exc
    for item in items:
        _require_canonical_string("reason_code", item)
    return tuple(sorted(set(items)))


def _normalize_flags(flags: Iterable[str]) -> tuple[str, ...]:
    if isinstance(flags, (str, bytes)):
        raise ValueError("flags must be an iterable of canonical strings")
    try:
        items = tuple(flags)
    except TypeError as exc:
        raise ValueError("flags must be an iterable of canonical strings") from exc
    for item in items:
        _require_canonical_string("flag", item)
        if item in UNSAFE_FLAGS:
            raise ValueError(f"unsafe flag is not allowed: {item}")
    return tuple(sorted(set(items)))


def _validate_row_component_names(
    components: tuple[PaperRecommendationScoreComponent, ...],
) -> None:
    seen: set[str] = set()
    for component in components:
        if component.component_name in seen:
            raise ValueError("duplicate component_name values are not allowed per row")
        seen.add(component.component_name)


def _validate_total_score(
    total_score: Decimal,
    components: tuple[PaperRecommendationScoreComponent, ...],
) -> None:
    component_total = _sum_scores(component.contribution for component in components)
    if component_total != total_score:
        raise ValueError("total_score must equal quantized component contributions")


def _validate_report_consistency(
    report: PaperRecommendationScoreExplanationReport,
) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows length")
    if report.pass_count != sum(1 for row in report.rows if row.score_status == "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != sum(
        1 for row in report.rows if row.score_status == "watch"
    ):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != sum(
        1 for row in report.rows if row.score_status == "blocked"
    ):
        raise ValueError("blocked_count must match rows")
    if report.average_total_score != _average_score(
        row.total_score for row in report.rows
    ):
        raise ValueError("average_total_score must match rows")
    expected_top = report.rows[0].total_score if report.rows else None
    if report.top_total_score != expected_top:
        raise ValueError("top_total_score must match rows")


def _report_flags(
    rows: tuple[PaperRecommendationScoreExplanationRow, ...],
) -> tuple[str, ...]:
    flags = set(BASE_FLAGS)
    for row in rows:
        flags.update(row.flags)
        for component in row.components:
            flags.update(component.flags)
    return tuple(sorted(flags))


def _average_score(values: Iterable[Decimal]) -> Decimal | None:
    items = tuple(values)
    if not items:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return (sum(items, ZERO) / Decimal(len(items))).quantize(SCORE_QUANTUM)


def _sum_scores(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return sum(values, ZERO).quantize(SCORE_QUANTUM)


def _normalize_score_decimal(field_name: str, value: Decimal) -> Decimal:
    _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(SCORE_QUANTUM)


def _normalize_optional_score_decimal(
    field_name: str,
    value: Decimal | None,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_score_decimal(field_name, value)


def _require_decimal(field_name: str, value: Decimal) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("datetime values must be timezone-aware")
    return value.astimezone(UTC)


def _validate_hard_flags(value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only") is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly") is not True:
        raise ValueError("readonly must be True")
