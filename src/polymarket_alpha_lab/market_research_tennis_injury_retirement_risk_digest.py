"""Pure Phase 1 tennis injury retirement risk digest reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256


DEFAULT_MARKET_RESEARCH_TENNIS_INJURY_RETIREMENT_RISK_DIGEST_CONFIG_VERSION = (
    "market-research-tennis-injury-retirement-risk-digest-v0"
)

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
DIGEST_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)

NO_INPUTS_REASON = "market_research_tennis_injury_retirement_risk_digest_no_inputs"
READY_REASON = "market_research_tennis_injury_retirement_risk_digest_ready"
CONFLICTING_SOURCES_REASON = (
    "market_research_tennis_injury_retirement_risk_digest_conflicting_sources"
)
HIGH_INJURY_SEVERITY_REASON = (
    "market_research_tennis_injury_retirement_risk_digest_high_injury_severity"
)
HIGH_RETIREMENT_RISK_REASON = (
    "market_research_tennis_injury_retirement_risk_digest_high_retirement_risk"
)
LIQUIDITY_GAP_REASON = (
    "market_research_tennis_injury_retirement_risk_digest_liquidity_gap"
)
LOW_CONFIRMATION_REASON = (
    "market_research_tennis_injury_retirement_risk_digest_low_confirmation"
)
LOW_INJURY_CONFIDENCE_REASON = (
    "market_research_tennis_injury_retirement_risk_digest_low_injury_confidence"
)
SOURCE_GAP_REASON = "market_research_tennis_injury_retirement_risk_digest_source_gap"
STALE_SIGNAL_REASON = (
    "market_research_tennis_injury_retirement_risk_digest_stale_signal"
)

REASON_CODE_SEQUENCE = (
    HIGH_RETIREMENT_RISK_REASON,
    HIGH_INJURY_SEVERITY_REASON,
    LIQUIDITY_GAP_REASON,
    LOW_CONFIRMATION_REASON,
    LOW_INJURY_CONFIDENCE_REASON,
    CONFLICTING_SOURCES_REASON,
    READY_REASON,
    SOURCE_GAP_REASON,
    STALE_SIGNAL_REASON,
    NO_INPUTS_REASON,
)
ROW_REASON_CODE_SEQUENCE = (
    CONFLICTING_SOURCES_REASON,
    HIGH_INJURY_SEVERITY_REASON,
    HIGH_RETIREMENT_RISK_REASON,
    LIQUIDITY_GAP_REASON,
    LOW_CONFIRMATION_REASON,
    LOW_INJURY_CONFIDENCE_REASON,
    SOURCE_GAP_REASON,
    STALE_SIGNAL_REASON,
    READY_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_TEXT_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("ex", "change"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_TENNIS_INJURY_RETIREMENT_RISK_DIGEST_CONFIG_VERSION",
    "MarketResearchTennisInjuryRetirementRiskDigestConfig",
    "MarketResearchTennisInjuryRetirementRiskDigestItem",
    "MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount",
    "MarketResearchTennisInjuryRetirementRiskDigestReport",
    "MarketResearchTennisInjuryRetirementRiskDigestRow",
    "build_market_research_tennis_injury_retirement_risk_digest",
    "market_research_tennis_injury_retirement_risk_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchTennisInjuryRetirementRiskDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_TENNIS_INJURY_RETIREMENT_RISK_DIGEST_CONFIG_VERSION
    )
    max_signal_age_seconds: Decimal = Decimal("3600.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_confirmation_ratio: Decimal = Decimal("0.600000")
    min_injury_confidence_score: Decimal = Decimal("0.650000")
    high_injury_severity_threshold: Decimal = Decimal("0.750000")
    high_retirement_risk_threshold: Decimal = Decimal("0.700000")
    min_market_liquidity_score: Decimal = Decimal("0.550000")
    max_conflicting_source_count: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_signal_age_seconds",
            "min_source_count",
            "min_independent_source_count",
            "max_conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_confirmation_ratio",
            "min_injury_confidence_score",
            "high_injury_severity_threshold",
            "high_retirement_risk_threshold",
            "min_market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.max_signal_age_seconds <= ZERO:
            raise ValueError("max_signal_age_seconds must be positive")
        if self.min_source_count <= ZERO:
            raise ValueError("min_source_count must be positive")
        if self.min_independent_source_count <= ZERO:
            raise ValueError("min_independent_source_count must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchTennisInjuryRetirementRiskDigestItem(_NoSubclass):
    condition_id: str
    tennis_event_key: str
    tour_key: str
    tournament_key: str
    round_key: str
    player_key: str
    opponent_key: str
    injury_key: str
    public_signal_reference: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    confirmed_source_count: Decimal
    conflicting_source_count: Decimal
    injury_confidence_score: Decimal
    injury_severity_score: Decimal
    retirement_risk_score: Decimal
    market_liquidity_score: Decimal
    item_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "tennis_event_key",
            "tour_key",
            "tournament_key",
            "round_key",
            "player_key",
            "opponent_key",
            "injury_key",
            "item_config_version",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_reference_is_redacted_safe(
            "public_signal_reference",
            self.public_signal_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "independent_source_count",
            "confirmed_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "injury_confidence_score",
            "injury_severity_score",
            "retirement_risk_score",
            "market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        if self.confirmed_source_count > self.source_count:
            raise ValueError("confirmed_source_count must not exceed source_count")
        if self.conflicting_source_count > self.source_count:
            raise ValueError("conflicting_source_count must not exceed source_count")
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class MarketResearchTennisInjuryRetirementRiskDigestRow(_NoSubclass):
    condition_id: str
    tennis_event_key: str
    tour_key: str
    tournament_key: str
    round_key: str
    player_key: str
    opponent_key: str
    injury_key: str
    digest_status: str
    observed_at: datetime
    signal_age_seconds: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    confirmed_source_count: Decimal
    conflicting_source_count: Decimal
    source_diversity_ratio: Decimal
    confirmation_ratio: Decimal
    injury_confidence_score: Decimal
    injury_severity_score: Decimal
    retirement_risk_score: Decimal
    market_liquidity_score: Decimal
    redacted_public_signal_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "tennis_event_key",
            "tour_key",
            "tournament_key",
            "round_key",
            "player_key",
            "opponent_key",
            "injury_key",
        ):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "signal_age_seconds",
            "source_count",
            "independent_source_count",
            "confirmed_source_count",
            "conflicting_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_diversity_ratio",
            "confirmation_ratio",
            "injury_confidence_score",
            "injury_severity_score",
            "retirement_risk_score",
            "market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_redacted_reference(
            "redacted_public_signal_reference",
            self.redacted_public_signal_reference,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=ROW_REASON_CODE_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    item_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "item_ratio",
            _require_ratio_decimal("item_ratio", self.item_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchTennisInjuryRetirementRiskDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    item_count: Decimal
    ready_item_count: Decimal
    watch_item_count: Decimal
    blocked_item_count: Decimal
    stale_signal_item_count: Decimal
    source_gap_item_count: Decimal
    confirmation_gap_item_count: Decimal
    conflict_item_count: Decimal
    low_injury_confidence_item_count: Decimal
    high_injury_severity_item_count: Decimal
    high_retirement_risk_item_count: Decimal
    liquidity_gap_item_count: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    confirmed_source_count: Decimal
    conflicting_source_count: Decimal
    confirmation_ratio: Decimal
    source_diversity_ratio: Decimal
    average_retirement_risk_score: Decimal
    max_signal_age_seconds: Decimal
    min_source_count: Decimal
    min_independent_source_count: Decimal
    min_confirmation_ratio: Decimal
    min_injury_confidence_score: Decimal
    high_injury_severity_threshold: Decimal
    high_retirement_risk_threshold: Decimal
    min_market_liquidity_score: Decimal
    max_conflicting_source_count: Decimal
    max_observed_signal_age_seconds: Decimal
    rows: tuple[MarketResearchTennisInjuryRetirementRiskDigestRow, ...]
    item_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[
        MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "item_count",
            "ready_item_count",
            "watch_item_count",
            "blocked_item_count",
            "stale_signal_item_count",
            "source_gap_item_count",
            "confirmation_gap_item_count",
            "conflict_item_count",
            "low_injury_confidence_item_count",
            "high_injury_severity_item_count",
            "high_retirement_risk_item_count",
            "liquidity_gap_item_count",
            "source_count",
            "independent_source_count",
            "confirmed_source_count",
            "conflicting_source_count",
            "average_retirement_risk_score",
            "max_signal_age_seconds",
            "min_source_count",
            "min_independent_source_count",
            "max_conflicting_source_count",
            "max_observed_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "confirmation_ratio",
            "source_diversity_ratio",
            "min_confirmation_ratio",
            "min_injury_confidence_score",
            "high_injury_severity_threshold",
            "high_retirement_risk_threshold",
            "min_market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "item_config_versions",
            _normalize_item_config_versions(self.item_config_versions),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, sequence=REASON_CODE_SEQUENCE),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_tennis_injury_retirement_risk_digest(
    items: Iterable[MarketResearchTennisInjuryRetirementRiskDigestItem],
    *,
    config: MarketResearchTennisInjuryRetirementRiskDigestConfig | None = None,
    generated_at: datetime,
) -> MarketResearchTennisInjuryRetirementRiskDigestReport:
    cfg = config or MarketResearchTennisInjuryRetirementRiskDigestConfig()
    if type(cfg) is not MarketResearchTennisInjuryRetirementRiskDigestConfig:
        raise ValueError(
            "config must be exactly MarketResearchTennisInjuryRetirementRiskDigestConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = tuple(
        _row_for_item(item, config=cfg, generated_at=generated_at_utc)
        for item in normalized_items
    )
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                _row_sort_value(row),
                row.tennis_event_key,
                row.condition_id,
            ),
        ),
    )
    report_status = _report_status(sorted_rows)
    source_count = _decimal_sum(row.source_count for row in sorted_rows)
    independent_source_count = _decimal_sum(
        row.independent_source_count for row in sorted_rows
    )
    confirmed_source_count = _decimal_sum(
        row.confirmed_source_count for row in sorted_rows
    )
    return MarketResearchTennisInjuryRetirementRiskDigestReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        digest_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        item_count=_decimal_count(len(sorted_rows)),
        ready_item_count=_decimal_count(
            sum(row.digest_status == STATUS_READY for row in sorted_rows),
        ),
        watch_item_count=_decimal_count(
            sum(row.digest_status == STATUS_WATCH for row in sorted_rows),
        ),
        blocked_item_count=_decimal_count(
            sum(row.digest_status == STATUS_BLOCKED for row in sorted_rows),
        ),
        stale_signal_item_count=_count_rows_with(sorted_rows, STALE_SIGNAL_REASON),
        source_gap_item_count=_count_rows_with(sorted_rows, SOURCE_GAP_REASON),
        confirmation_gap_item_count=_count_rows_with(
            sorted_rows,
            LOW_CONFIRMATION_REASON,
        ),
        conflict_item_count=_count_rows_with(sorted_rows, CONFLICTING_SOURCES_REASON),
        low_injury_confidence_item_count=_count_rows_with(
            sorted_rows,
            LOW_INJURY_CONFIDENCE_REASON,
        ),
        high_injury_severity_item_count=_count_rows_with(
            sorted_rows,
            HIGH_INJURY_SEVERITY_REASON,
        ),
        high_retirement_risk_item_count=_count_rows_with(
            sorted_rows,
            HIGH_RETIREMENT_RISK_REASON,
        ),
        liquidity_gap_item_count=_count_rows_with(sorted_rows, LIQUIDITY_GAP_REASON),
        source_count=source_count,
        independent_source_count=independent_source_count,
        confirmed_source_count=confirmed_source_count,
        conflicting_source_count=_decimal_sum(
            row.conflicting_source_count for row in sorted_rows
        ),
        confirmation_ratio=_ratio(confirmed_source_count, source_count),
        source_diversity_ratio=_ratio(independent_source_count, source_count),
        average_retirement_risk_score=_ratio(
            _decimal_sum(row.retirement_risk_score for row in sorted_rows),
            _decimal_count(len(sorted_rows)),
        ),
        max_signal_age_seconds=cfg.max_signal_age_seconds,
        min_source_count=cfg.min_source_count,
        min_independent_source_count=cfg.min_independent_source_count,
        min_confirmation_ratio=cfg.min_confirmation_ratio,
        min_injury_confidence_score=cfg.min_injury_confidence_score,
        high_injury_severity_threshold=cfg.high_injury_severity_threshold,
        high_retirement_risk_threshold=cfg.high_retirement_risk_threshold,
        min_market_liquidity_score=cfg.min_market_liquidity_score,
        max_conflicting_source_count=cfg.max_conflicting_source_count,
        max_observed_signal_age_seconds=max(
            (row.signal_age_seconds for row in sorted_rows),
            default=ZERO,
        ),
        rows=sorted_rows,
        item_config_versions=tuple(
            sorted(
                (item.tennis_event_key, item.item_config_version)
                for item in normalized_items
            ),
        ),
        reason_code_counts=_reason_code_counts(sorted_rows),
        reason_codes=_summary_reason_codes(sorted_rows),
    )


def market_research_tennis_injury_retirement_risk_digest_payload(
    report: MarketResearchTennisInjuryRetirementRiskDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchTennisInjuryRetirementRiskDigestReport:
        raise ValueError(
            "report must be exactly MarketResearchTennisInjuryRetirementRiskDigestReport",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def _row_for_item(
    item: MarketResearchTennisInjuryRetirementRiskDigestItem,
    *,
    config: MarketResearchTennisInjuryRetirementRiskDigestConfig,
    generated_at: datetime,
) -> MarketResearchTennisInjuryRetirementRiskDigestRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    signal_age_seconds = _age_seconds(generated_at, item.observed_at)
    confirmation_ratio = _ratio(item.confirmed_source_count, item.source_count)
    source_diversity_ratio = _ratio(item.independent_source_count, item.source_count)
    reason_codes = _row_reason_codes(
        item=item,
        config=config,
        signal_age_seconds=signal_age_seconds,
        confirmation_ratio=confirmation_ratio,
    )
    return MarketResearchTennisInjuryRetirementRiskDigestRow(
        condition_id=item.condition_id,
        tennis_event_key=item.tennis_event_key,
        tour_key=item.tour_key,
        tournament_key=item.tournament_key,
        round_key=item.round_key,
        player_key=item.player_key,
        opponent_key=item.opponent_key,
        injury_key=item.injury_key,
        digest_status=_row_status(reason_codes),
        observed_at=item.observed_at,
        signal_age_seconds=signal_age_seconds,
        source_count=item.source_count,
        independent_source_count=item.independent_source_count,
        confirmed_source_count=item.confirmed_source_count,
        conflicting_source_count=item.conflicting_source_count,
        source_diversity_ratio=source_diversity_ratio,
        confirmation_ratio=confirmation_ratio,
        injury_confidence_score=item.injury_confidence_score,
        injury_severity_score=item.injury_severity_score,
        retirement_risk_score=item.retirement_risk_score,
        market_liquidity_score=item.market_liquidity_score,
        redacted_public_signal_reference=_redacted_reference(item.public_signal_reference),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: MarketResearchTennisInjuryRetirementRiskDigestItem,
    config: MarketResearchTennisInjuryRetirementRiskDigestConfig,
    signal_age_seconds: Decimal,
    confirmation_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.conflicting_source_count > config.max_conflicting_source_count:
        reasons.append(CONFLICTING_SOURCES_REASON)
    if item.injury_severity_score >= config.high_injury_severity_threshold:
        reasons.append(HIGH_INJURY_SEVERITY_REASON)
    if item.retirement_risk_score >= config.high_retirement_risk_threshold:
        reasons.append(HIGH_RETIREMENT_RISK_REASON)
    if item.market_liquidity_score < config.min_market_liquidity_score:
        reasons.append(LIQUIDITY_GAP_REASON)
    if confirmation_ratio < config.min_confirmation_ratio:
        reasons.append(LOW_CONFIRMATION_REASON)
    if item.injury_confidence_score < config.min_injury_confidence_score:
        reasons.append(LOW_INJURY_CONFIDENCE_REASON)
    if (
        item.source_count < config.min_source_count
        or item.independent_source_count < config.min_independent_source_count
    ):
        reasons.append(SOURCE_GAP_REASON)
    if signal_age_seconds > config.max_signal_age_seconds:
        reasons.append(STALE_SIGNAL_REASON)
    if not reasons:
        reasons.append(READY_REASON)
    return tuple(reason for reason in ROW_REASON_CODE_SEQUENCE if reason in reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        CONFLICTING_SOURCES_REASON in reason_codes
        or HIGH_RETIREMENT_RISK_REASON in reason_codes
    ):
        return STATUS_BLOCKED
    if reason_codes == (READY_REASON,):
        return STATUS_READY
    return STATUS_WATCH


def _report_status(
    rows: tuple[MarketResearchTennisInjuryRetirementRiskDigestRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.digest_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_READY:
        return "allow_report_only_market_research_tennis_injury_retirement_risk_digest"
    if status == STATUS_WATCH:
        return "monitor_report_only_market_research_tennis_injury_retirement_risk_digest"
    return "block_report_only_market_research_tennis_injury_retirement_risk_digest"


def _summary_reason_codes(
    rows: tuple[MarketResearchTennisInjuryRetirementRiskDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    seen = {reason for row in rows for reason in row.reason_codes}
    return tuple(reason for reason in REASON_CODE_SEQUENCE if reason in seen)


def _reason_code_counts(
    rows: tuple[MarketResearchTennisInjuryRetirementRiskDigestRow, ...],
) -> tuple[MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                item_ratio=ZERO,
            ),
        )
    total = _decimal_count(len(rows))
    counts: list[MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount] = []
    for reason_code in REASON_CODE_SEQUENCE:
        count = _count_rows_with(rows, reason_code)
        if count > ZERO:
            counts.append(
                MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                    item_ratio=_ratio(count, total),
                ),
            )
    return tuple(counts)


def _count_rows_with(
    rows: tuple[MarketResearchTennisInjuryRetirementRiskDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(reason_code in row.reason_codes for row in rows))


def _validate_row(row: MarketResearchTennisInjuryRetirementRiskDigestRow) -> None:
    if row.independent_source_count > row.source_count:
        raise ValueError("independent_source_count must not exceed source_count")
    if row.confirmed_source_count > row.source_count:
        raise ValueError("confirmed_source_count must not exceed source_count")
    if row.conflicting_source_count > row.source_count:
        raise ValueError("conflicting_source_count must not exceed source_count")
    if row.source_diversity_ratio != _ratio(
        row.independent_source_count,
        row.source_count,
    ):
        raise ValueError("source_diversity_ratio must match source counts")
    if row.confirmation_ratio != _ratio(row.confirmed_source_count, row.source_count):
        raise ValueError("confirmation_ratio must match source counts")
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")


def _validate_report(report: MarketResearchTennisInjuryRetirementRiskDigestReport) -> None:
    if report.recommended_next_step != _recommended_next_step(report.digest_status):
        raise ValueError("recommended_next_step must match digest_status")
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    if report.ready_item_count != _decimal_count(
        sum(row.digest_status == STATUS_READY for row in report.rows),
    ):
        raise ValueError("ready_item_count must match rows")
    if report.watch_item_count != _decimal_count(
        sum(row.digest_status == STATUS_WATCH for row in report.rows),
    ):
        raise ValueError("watch_item_count must match rows")
    if report.blocked_item_count != _decimal_count(
        sum(row.digest_status == STATUS_BLOCKED for row in report.rows),
    ):
        raise ValueError("blocked_item_count must match rows")
    if report.digest_status != _report_status(report.rows):
        raise ValueError("digest_status must match rows")
    reason_count_fields = (
        (report.stale_signal_item_count, STALE_SIGNAL_REASON, "stale_signal_item_count"),
        (report.source_gap_item_count, SOURCE_GAP_REASON, "source_gap_item_count"),
        (
            report.confirmation_gap_item_count,
            LOW_CONFIRMATION_REASON,
            "confirmation_gap_item_count",
        ),
        (report.conflict_item_count, CONFLICTING_SOURCES_REASON, "conflict_item_count"),
        (
            report.low_injury_confidence_item_count,
            LOW_INJURY_CONFIDENCE_REASON,
            "low_injury_confidence_item_count",
        ),
        (
            report.high_injury_severity_item_count,
            HIGH_INJURY_SEVERITY_REASON,
            "high_injury_severity_item_count",
        ),
        (
            report.high_retirement_risk_item_count,
            HIGH_RETIREMENT_RISK_REASON,
            "high_retirement_risk_item_count",
        ),
        (
            report.liquidity_gap_item_count,
            LIQUIDITY_GAP_REASON,
            "liquidity_gap_item_count",
        ),
    )
    for actual_count, reason_code, field_name in reason_count_fields:
        if actual_count != _count_rows_with(report.rows, reason_code):
            raise ValueError(f"{field_name} must match rows")
    if report.source_count != _decimal_sum(row.source_count for row in report.rows):
        raise ValueError("source_count must match rows")
    if report.independent_source_count != _decimal_sum(
        row.independent_source_count for row in report.rows
    ):
        raise ValueError("independent_source_count must match rows")
    if report.confirmed_source_count != _decimal_sum(
        row.confirmed_source_count for row in report.rows
    ):
        raise ValueError("confirmed_source_count must match rows")
    if report.conflicting_source_count != _decimal_sum(
        row.conflicting_source_count for row in report.rows
    ):
        raise ValueError("conflicting_source_count must match rows")
    if report.confirmation_ratio != _ratio(
        report.confirmed_source_count,
        report.source_count,
    ):
        raise ValueError("confirmation_ratio must match source counts")
    if report.source_diversity_ratio != _ratio(
        report.independent_source_count,
        report.source_count,
    ):
        raise ValueError("source_diversity_ratio must match source counts")
    if report.average_retirement_risk_score != _ratio(
        _decimal_sum(row.retirement_risk_score for row in report.rows),
        report.item_count,
    ):
        raise ValueError("average_retirement_risk_score must match rows")
    if report.max_observed_signal_age_seconds != max(
        (row.signal_age_seconds for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_observed_signal_age_seconds must match rows")
    if (
        report.item_config_versions
        and len(report.item_config_versions) != len(report.rows)
    ):
        raise ValueError("item_config_versions must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")


def _normalize_items(
    items: Iterable[MarketResearchTennisInjuryRetirementRiskDigestItem],
) -> tuple[MarketResearchTennisInjuryRetirementRiskDigestItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must contain tennis injury retirement risk rows")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must contain tennis injury retirement risk rows") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchTennisInjuryRetirementRiskDigestItem:
            raise ValueError(
                "items must contain MarketResearchTennisInjuryRetirementRiskDigestItem",
            )
        if item.tennis_event_key in seen:
            raise ValueError("tennis_event_key values must be unique")
        seen.add(item.tennis_event_key)
        _require_hard_flags("item", item)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[MarketResearchTennisInjuryRetirementRiskDigestRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must contain tennis injury retirement risk digest rows")
    try:
        normalized = tuple(rows)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("rows must contain tennis injury retirement risk digest rows") from exc
    for row in normalized:
        if type(row) is not MarketResearchTennisInjuryRetirementRiskDigestRow:
            raise ValueError(
                "rows must contain MarketResearchTennisInjuryRetirementRiskDigestRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda row: (
                _row_sort_value(row),
                row.tennis_event_key,
                row.condition_id,
            ),
        ),
    ):
        raise ValueError("rows must be sorted deterministically")
    if len({row.tennis_event_key for row in normalized}) != len(normalized):
        raise ValueError("tennis_event_key values must be unique")
    return normalized


def _normalize_item_config_versions(value: object) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("item_config_versions must contain pairs")
    try:
        normalized = tuple(tuple(item) for item in value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("item_config_versions must contain pairs") from exc
    seen: set[str] = set()
    for item in normalized:
        if len(item) != 2:
            raise ValueError("item_config_versions must contain pairs")
        item_key, config_version = item
        _require_public_string("item_config_versions item_key", item_key)
        _require_canonical_string("item_config_versions config_version", config_version)
        if item_key in seen:
            raise ValueError("item_config_versions item keys must be unique")
        seen.add(item_key)
    if normalized != tuple(sorted(normalized)):
        raise ValueError("item_config_versions must be sorted")
    return normalized


def _normalize_reason_code_counts(
    value: object,
) -> tuple[MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must contain reason code counts")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_code_counts must contain reason code counts") from exc
    for item in normalized:
        if type(item) is not MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchTennisInjuryRetirementRiskDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    if normalized != tuple(
        sorted(normalized, key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by reason code sequence")
    return normalized


def _normalize_reason_codes(
    value: object,
    *,
    sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must contain reason code strings")
    try:
        normalized = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("reason_codes must contain reason code strings") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    reason_sequence = {reason_code: index for index, reason_code in enumerate(sequence)}
    if normalized and normalized != tuple(
        sorted(normalized, key=lambda reason_code: reason_sequence[reason_code]),
    ):
        raise ValueError("reason_codes must be sorted")
    return normalized


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        micros = Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND
        return _quantize(seconds + micros)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _decimal_sum(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _row_sort_value(row: MarketResearchTennisInjuryRetirementRiskDigestRow) -> int:
    if row.digest_status == STATUS_BLOCKED:
        return 0
    if row.digest_status == STATUS_WATCH:
        return 1
    return 2


def _redacted_reference(value: str) -> str:
    if _is_reference_safe(value):
        return value
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()[:12]}"


def _is_reference_safe(value: str) -> bool:
    lowered = value.lower()
    return not any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)


def _require_reference_is_redacted_safe(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not _is_reference_safe(value) and "://" not in value:
        raise ValueError(f"{field_name} must be redacted")


def _require_redacted_reference(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value.startswith("sha256:"):
        digest = value.removeprefix("sha256:")
        if len(digest) != 12 or not all(character in "0123456789abcdef" for character in digest):
            raise ValueError(f"{field_name} must be redacted")
        return
    if not _is_reference_safe(value):
        raise ValueError(f"{field_name} must be redacted")


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in DIGEST_STATUSES:
        raise ValueError(f"{field_name} must contain a known digest status")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must contain a known reason code")


def _require_public_string(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if not _is_reference_safe(value):
        raise ValueError(f"{field_name} must be redacted")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value
