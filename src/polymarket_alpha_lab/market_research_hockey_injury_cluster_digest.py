"""Pure reducer for report-only hockey injury cluster digest reports."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
from hashlib import sha256


DEFAULT_MARKET_RESEARCH_HOCKEY_INJURY_CLUSTER_DIGEST_CONFIG_VERSION = (
    "market-research-hockey-injury-cluster-digest-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX_PLACES = Decimal("0.000001")
MICROSECONDS_PER_SECOND = Decimal("1000000")

READY_REASON = "market_research_hockey_injury_cluster_digest_ready"
NO_INPUTS_REASON = "market_research_hockey_injury_cluster_digest_no_inputs"
HIGH_CLUSTER_SEVERITY_REASON = (
    "market_research_hockey_injury_cluster_digest_high_cluster_severity"
)
LIQUIDITY_GAP_REASON = "market_research_hockey_injury_cluster_digest_liquidity_gap"
LOW_CLUSTER_CONFIDENCE_REASON = (
    "market_research_hockey_injury_cluster_digest_low_cluster_confidence"
)
SOURCE_GAP_REASON = "market_research_hockey_injury_cluster_digest_source_gap"
STALE_CLUSTER_REASON = "market_research_hockey_injury_cluster_digest_stale_cluster"
THIN_CLUSTER_REASON = "market_research_hockey_injury_cluster_digest_thin_cluster"

REASON_CODES = (
    HIGH_CLUSTER_SEVERITY_REASON,
    LIQUIDITY_GAP_REASON,
    LOW_CLUSTER_CONFIDENCE_REASON,
    READY_REASON,
    SOURCE_GAP_REASON,
    STALE_CLUSTER_REASON,
    THIN_CLUSTER_REASON,
    NO_INPUTS_REASON,
)

NEXT_STEPS = {
    "ready": "allow_report_only_market_research_hockey_injury_cluster_digest",
    "watch": "watch_report_only_market_research_hockey_injury_cluster_digest",
    "blocked": "block_report_only_market_research_hockey_injury_cluster_digest",
}


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
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
        _join_parts("sec", "ret"),
        _join_parts("to", "ken"),
        _join_parts("pri", "vate"),
        _join_parts("api_", "key"),
    ),
)

LIVE_ACTION_REFERENCE_FRAGMENTS = frozenset(
    (
        _join_parts("au", "th"),
        _join_parts("bro", "ker"),
        _join_parts("sig", "ning"),
        _join_parts("sub", "mit"),
        _join_parts("can", "cel"),
        _join_parts("wal", "let"),
        _join_parts("acc", "ount"),
        _join_parts("ad", "vice"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("pay", "load"),
    ),
)

__all__ = (
    "DEFAULT_MARKET_RESEARCH_HOCKEY_INJURY_CLUSTER_DIGEST_CONFIG_VERSION",
    "MarketResearchHockeyInjuryClusterDigestConfig",
    "MarketResearchHockeyInjuryClusterDigestItem",
    "MarketResearchHockeyInjuryClusterDigestReasonCodeCount",
    "MarketResearchHockeyInjuryClusterDigestReport",
    "MarketResearchHockeyInjuryClusterDigestRow",
    "build_market_research_hockey_injury_cluster_digest",
    "market_research_hockey_injury_cluster_digest_payload",
)


class _NoSubclass:
    def __init_subclass__(cls) -> None:
        if _NoSubclass not in cls.__bases__:
            raise TypeError(f"{cls.__name__} does not support subclassing")


@dataclass(frozen=True)
class MarketResearchHockeyInjuryClusterDigestConfig(_NoSubclass):
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_HOCKEY_INJURY_CLUSTER_DIGEST_CONFIG_VERSION
    )
    max_cluster_age_seconds: Decimal = Decimal("5400.000000")
    critical_cluster_age_seconds: Decimal = Decimal("1800.000000")
    min_source_count: Decimal = Decimal("2.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    min_team_injury_count: Decimal = Decimal("2.000000")
    min_cluster_confidence_score: Decimal = Decimal("0.650000")
    high_cluster_severity_threshold: Decimal = Decimal("0.750000")
    min_market_liquidity_score: Decimal = Decimal("0.550000")
    confidence_decay_per_stale_cluster: Decimal = Decimal("0.180000")
    confidence_decay_per_source_gap: Decimal = Decimal("0.120000")
    confidence_decay_per_thin_cluster: Decimal = Decimal("0.090000")
    confidence_decay_per_liquidity_gap: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_cluster_age_seconds",
            "critical_cluster_age_seconds",
            "min_source_count",
            "min_independent_source_count",
            "min_team_injury_count",
            "confidence_decay_per_stale_cluster",
            "confidence_decay_per_source_gap",
            "confidence_decay_per_thin_cluster",
            "confidence_decay_per_liquidity_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_cluster_confidence_score",
            "high_cluster_severity_threshold",
            "min_market_liquidity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketResearchHockeyInjuryClusterDigestItem(_NoSubclass):
    condition_id: str
    hockey_event_key: str
    league_key: str
    team_key: str
    opponent_key: str
    injury_cluster_key: str
    public_news_reference: str
    observed_at: datetime
    source_count: Decimal
    independent_source_count: Decimal
    team_injury_count: Decimal
    cluster_confidence_score: Decimal
    cluster_severity_score: Decimal
    market_liquidity_score: Decimal
    base_confidence_score: Decimal
    item_config_version: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "hockey_event_key",
            "league_key",
            "team_key",
            "opponent_key",
            "injury_cluster_key",
            "item_config_version",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_public_news_reference(
            "public_news_reference",
            self.public_news_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "source_count",
            "independent_source_count",
            "team_injury_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cluster_confidence_score",
            "cluster_severity_score",
            "market_liquidity_score",
            "base_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.source_count:
            raise ValueError("independent_source_count must not exceed source_count")
        _require_hard_flags("item", self)


@dataclass(frozen=True)
class MarketResearchHockeyInjuryClusterDigestRow(_NoSubclass):
    condition_id: str
    hockey_event_key: str
    league_key: str
    team_key: str
    opponent_key: str
    injury_cluster_key: str
    digest_status: str
    observed_at: datetime
    cluster_age_seconds: Decimal
    source_count: Decimal
    independent_source_count: Decimal
    source_diversity_ratio: Decimal
    team_injury_count: Decimal
    cluster_confidence_score: Decimal
    cluster_severity_score: Decimal
    market_liquidity_score: Decimal
    base_confidence_score: Decimal
    confidence_decay_score: Decimal
    confidence_score: Decimal
    redacted_public_news_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "condition_id",
            "hockey_event_key",
            "league_key",
            "team_key",
            "opponent_key",
            "injury_cluster_key",
            "redacted_public_news_reference",
        ):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_digest_status("digest_status", self.digest_status)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "cluster_age_seconds",
            "source_count",
            "independent_source_count",
            "team_injury_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_diversity_ratio",
            "cluster_confidence_score",
            "cluster_severity_score",
            "market_liquidity_score",
            "base_confidence_score",
            "confidence_decay_score",
            "confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class MarketResearchHockeyInjuryClusterDigestReasonCodeCount(_NoSubclass):
    reason_code: str
    count: Decimal
    item_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_digest_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_nonnegative_decimal("count", self.count))
        object.__setattr__(
            self,
            "item_ratio",
            _require_ratio_decimal("item_ratio", self.item_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketResearchHockeyInjuryClusterDigestReport(_NoSubclass):
    generated_at: datetime
    config_version: str
    digest_status: str
    recommended_next_step: str
    item_count: Decimal
    ready_item_count: Decimal
    watch_item_count: Decimal
    blocked_item_count: Decimal
    stale_cluster_item_count: Decimal
    source_gap_item_count: Decimal
    thin_cluster_item_count: Decimal
    low_cluster_confidence_item_count: Decimal
    high_cluster_severity_item_count: Decimal
    liquidity_gap_item_count: Decimal
    average_confidence_score: Decimal
    max_cluster_age_seconds: Decimal
    critical_cluster_age_seconds: Decimal
    min_source_count: Decimal
    min_independent_source_count: Decimal
    min_team_injury_count: Decimal
    min_cluster_confidence_score: Decimal
    high_cluster_severity_threshold: Decimal
    min_market_liquidity_score: Decimal
    max_observed_cluster_age_seconds: Decimal
    rows: tuple[MarketResearchHockeyInjuryClusterDigestRow, ...]
    item_config_versions: tuple[tuple[str, str], ...]
    reason_code_counts: tuple[MarketResearchHockeyInjuryClusterDigestReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_digest_status("digest_status", self.digest_status)
        _require_canonical_string("recommended_next_step", self.recommended_next_step)
        for field_name in (
            "item_count",
            "ready_item_count",
            "watch_item_count",
            "blocked_item_count",
            "stale_cluster_item_count",
            "source_gap_item_count",
            "thin_cluster_item_count",
            "low_cluster_confidence_item_count",
            "high_cluster_severity_item_count",
            "liquidity_gap_item_count",
            "max_cluster_age_seconds",
            "critical_cluster_age_seconds",
            "min_source_count",
            "min_independent_source_count",
            "min_team_injury_count",
            "max_observed_cluster_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_confidence_score",
            "min_cluster_confidence_score",
            "high_cluster_severity_threshold",
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
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)


def build_market_research_hockey_injury_cluster_digest(
    items: list[MarketResearchHockeyInjuryClusterDigestItem]
    | tuple[MarketResearchHockeyInjuryClusterDigestItem, ...],
    *,
    config: MarketResearchHockeyInjuryClusterDigestConfig,
    generated_at: datetime,
) -> MarketResearchHockeyInjuryClusterDigestReport:
    if type(config) is not MarketResearchHockeyInjuryClusterDigestConfig:
        raise ValueError("config must be a MarketResearchHockeyInjuryClusterDigestConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = _rows(normalized_items, config=config, generated_at=generated_at_utc)
    item_count = _decimal_count(len(rows))
    ready_item_count = _decimal_count(
        sum(1 for row in rows if row.digest_status == "ready")
    )
    watch_item_count = _decimal_count(
        sum(1 for row in rows if row.digest_status == "watch")
    )
    blocked_item_count = _decimal_count(
        sum(1 for row in rows if row.digest_status == "blocked")
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                item_ratio=ZERO,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    confidence_score = _sum_decimal(row.confidence_score for row in rows)
    digest_status = _report_status(
        ready_count=ready_item_count,
        watch_count=watch_item_count,
        blocked_count=blocked_item_count,
        item_count=item_count,
    )

    return MarketResearchHockeyInjuryClusterDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        digest_status=digest_status,
        recommended_next_step=NEXT_STEPS[digest_status],
        item_count=item_count,
        ready_item_count=ready_item_count,
        watch_item_count=watch_item_count,
        blocked_item_count=blocked_item_count,
        stale_cluster_item_count=_item_count_with(rows, STALE_CLUSTER_REASON),
        source_gap_item_count=_item_count_with(rows, SOURCE_GAP_REASON),
        thin_cluster_item_count=_item_count_with(rows, THIN_CLUSTER_REASON),
        low_cluster_confidence_item_count=_item_count_with(
            rows,
            LOW_CLUSTER_CONFIDENCE_REASON,
        ),
        high_cluster_severity_item_count=_item_count_with(
            rows,
            HIGH_CLUSTER_SEVERITY_REASON,
        ),
        liquidity_gap_item_count=_item_count_with(rows, LIQUIDITY_GAP_REASON),
        average_confidence_score=_ratio(confidence_score, item_count),
        max_cluster_age_seconds=_six(config.max_cluster_age_seconds),
        critical_cluster_age_seconds=_six(config.critical_cluster_age_seconds),
        min_source_count=_six(config.min_source_count),
        min_independent_source_count=_six(config.min_independent_source_count),
        min_team_injury_count=_six(config.min_team_injury_count),
        min_cluster_confidence_score=_six(config.min_cluster_confidence_score),
        high_cluster_severity_threshold=_six(config.high_cluster_severity_threshold),
        min_market_liquidity_score=_six(config.min_market_liquidity_score),
        max_observed_cluster_age_seconds=_max_decimal(
            row.cluster_age_seconds for row in rows
        ),
        rows=rows,
        item_config_versions=_item_config_versions(normalized_items),
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def market_research_hockey_injury_cluster_digest_payload(
    report: MarketResearchHockeyInjuryClusterDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketResearchHockeyInjuryClusterDigestReport:
        raise ValueError("report must be a MarketResearchHockeyInjuryClusterDigestReport")
    _require_hard_flags("report", report)
    value = _payload_value(asdict(report))
    if type(value) is not dict:
        raise ValueError("report output must be a dict")
    return value


def _normalize_items(
    items: list[MarketResearchHockeyInjuryClusterDigestItem]
    | tuple[MarketResearchHockeyInjuryClusterDigestItem, ...],
) -> tuple[MarketResearchHockeyInjuryClusterDigestItem, ...]:
    if type(items) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    normalized = tuple(items)
    seen_event_keys: set[str] = set()
    for item in normalized:
        if type(item) is not MarketResearchHockeyInjuryClusterDigestItem:
            raise ValueError("items must contain MarketResearchHockeyInjuryClusterDigestItem")
        _require_hard_flags("item", item)
        if item.hockey_event_key in seen_event_keys:
            raise ValueError("hockey_event_key values must be unique")
        seen_event_keys.add(item.hockey_event_key)
    return normalized


def _rows(
    items: tuple[MarketResearchHockeyInjuryClusterDigestItem, ...],
    *,
    config: MarketResearchHockeyInjuryClusterDigestConfig,
    generated_at: datetime,
) -> tuple[MarketResearchHockeyInjuryClusterDigestRow, ...]:
    built_rows = []
    for item in items:
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be in the future")
        age = _age_seconds(generated_at, item.observed_at)
        reason_codes = _row_reason_codes(item, config=config, cluster_age_seconds=age)
        confidence_decay = _confidence_decay_score(reason_codes, config)
        built_rows.append(
            MarketResearchHockeyInjuryClusterDigestRow(
                condition_id=item.condition_id,
                hockey_event_key=item.hockey_event_key,
                league_key=item.league_key,
                team_key=item.team_key,
                opponent_key=item.opponent_key,
                injury_cluster_key=item.injury_cluster_key,
                digest_status=_row_status(reason_codes),
                observed_at=item.observed_at,
                cluster_age_seconds=age,
                source_count=_six(item.source_count),
                independent_source_count=_six(item.independent_source_count),
                source_diversity_ratio=_source_diversity_ratio(item),
                team_injury_count=_six(item.team_injury_count),
                cluster_confidence_score=_six(item.cluster_confidence_score),
                cluster_severity_score=_six(item.cluster_severity_score),
                market_liquidity_score=_six(item.market_liquidity_score),
                base_confidence_score=_six(item.base_confidence_score),
                confidence_decay_score=confidence_decay,
                confidence_score=_confidence_score(
                    item.base_confidence_score,
                    confidence_decay,
                ),
                redacted_public_news_reference=_redacted_public_reference(
                    item.public_news_reference,
                ),
                reason_codes=reason_codes,
            )
        )
    return tuple(sorted(built_rows, key=_row_sort_key))


def _row_reason_codes(
    item: MarketResearchHockeyInjuryClusterDigestItem,
    *,
    config: MarketResearchHockeyInjuryClusterDigestConfig,
    cluster_age_seconds: Decimal,
) -> tuple[str, ...]:
    reason_codes = []
    if item.cluster_severity_score >= config.high_cluster_severity_threshold:
        reason_codes.append(HIGH_CLUSTER_SEVERITY_REASON)
    if item.market_liquidity_score < config.min_market_liquidity_score:
        reason_codes.append(LIQUIDITY_GAP_REASON)
    if item.cluster_confidence_score < config.min_cluster_confidence_score:
        reason_codes.append(LOW_CLUSTER_CONFIDENCE_REASON)
    if item.independent_source_count < config.min_independent_source_count:
        reason_codes.append(SOURCE_GAP_REASON)
    if item.source_count < config.min_source_count and SOURCE_GAP_REASON not in reason_codes:
        reason_codes.append(SOURCE_GAP_REASON)
    if cluster_age_seconds > config.max_cluster_age_seconds:
        reason_codes.append(STALE_CLUSTER_REASON)
    if item.team_injury_count < config.min_team_injury_count:
        reason_codes.append(THIN_CLUSTER_REASON)
    if not reason_codes:
        reason_codes.append(READY_REASON)
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (READY_REASON,):
        return "ready"
    if any(
        reason_code
        in (
            SOURCE_GAP_REASON,
            STALE_CLUSTER_REASON,
            THIN_CLUSTER_REASON,
        )
        for reason_code in reason_codes
    ):
        return "blocked"
    return "watch"


def _report_status(
    *,
    ready_count: Decimal,
    watch_count: Decimal,
    blocked_count: Decimal,
    item_count: Decimal,
) -> str:
    if item_count == ZERO:
        return "blocked"
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    if ready_count == item_count:
        return "ready"
    return "blocked"


def _reason_code_counts(
    rows: tuple[MarketResearchHockeyInjuryClusterDigestRow, ...],
) -> tuple[MarketResearchHockeyInjuryClusterDigestReasonCodeCount, ...]:
    if not rows:
        return (
            MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                item_ratio=ZERO,
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    item_count = _decimal_count(len(rows))
    return tuple(
        MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            item_ratio=_ratio(_decimal_count(counts[reason_code]), item_count),
        )
        for reason_code in REASON_CODES
        if reason_code in counts
    )


def _confidence_decay_score(
    reason_codes: tuple[str, ...],
    config: MarketResearchHockeyInjuryClusterDigestConfig,
) -> Decimal:
    decay = ZERO
    if STALE_CLUSTER_REASON in reason_codes:
        decay += config.confidence_decay_per_stale_cluster
    if SOURCE_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_source_gap
    if THIN_CLUSTER_REASON in reason_codes:
        decay += config.confidence_decay_per_thin_cluster
    if LIQUIDITY_GAP_REASON in reason_codes:
        decay += config.confidence_decay_per_liquidity_gap
    return _six(decay)


def _confidence_score(base_confidence_score: Decimal, decay: Decimal) -> Decimal:
    score = base_confidence_score - decay
    if score < ZERO:
        return ZERO
    return _six(score)


def _source_diversity_ratio(
    item: MarketResearchHockeyInjuryClusterDigestItem,
) -> Decimal:
    return _ratio(item.independent_source_count, item.source_count)


def _item_count_with(
    rows: tuple[MarketResearchHockeyInjuryClusterDigestRow, ...],
    reason_code: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if reason_code in row.reason_codes))


def _item_config_versions(
    items: tuple[MarketResearchHockeyInjuryClusterDigestItem, ...],
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((item.hockey_event_key, item.item_config_version) for item in items))


def _normalize_rows(
    rows: tuple[MarketResearchHockeyInjuryClusterDigestRow, ...],
) -> tuple[MarketResearchHockeyInjuryClusterDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not MarketResearchHockeyInjuryClusterDigestRow:
            raise ValueError("rows must contain MarketResearchHockeyInjuryClusterDigestRow")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_item_config_versions(
    values: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, str], ...]:
    if type(values) is not tuple:
        raise ValueError("item_config_versions must be a tuple")
    normalized = []
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise ValueError("item_config_versions must contain 2-tuples")
        hockey_event_key, config_version = value
        _require_canonical_string("hockey_event_key", hockey_event_key)
        _require_canonical_string("item_config_version", config_version)
        normalized.append((hockey_event_key, config_version))
    if tuple(normalized) != tuple(sorted(normalized)):
        raise ValueError("item_config_versions must be sorted")
    return tuple(normalized)


def _normalize_reason_code_counts(
    values: tuple[MarketResearchHockeyInjuryClusterDigestReasonCodeCount, ...],
) -> tuple[MarketResearchHockeyInjuryClusterDigestReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not MarketResearchHockeyInjuryClusterDigestReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketResearchHockeyInjuryClusterDigestReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
    if values != tuple(sorted(values, key=lambda value: REASON_CODES.index(value.reason_code))):
        raise ValueError("reason_code_counts must be sorted by reason code rank")
    return values


def _row_sort_key(
    row: MarketResearchHockeyInjuryClusterDigestRow,
) -> tuple[int, str, str]:
    return (_status_rank(row.digest_status), row.hockey_event_key, row.condition_id)


def _validate_row_consistency(
    row: MarketResearchHockeyInjuryClusterDigestRow,
) -> None:
    if row.digest_status != _row_status(row.reason_codes):
        raise ValueError("digest_status must match reason_codes")
    if row.reason_codes == (NO_INPUTS_REASON,):
        raise ValueError("reason_codes cannot contain no inputs for a row")


def _validate_report_consistency(
    report: MarketResearchHockeyInjuryClusterDigestReport,
) -> None:
    if report.item_count != _decimal_count(len(report.rows)):
        raise ValueError("item_count must match rows")
    expected_ready = _decimal_count(
        sum(1 for row in report.rows if row.digest_status == "ready")
    )
    expected_watch = _decimal_count(
        sum(1 for row in report.rows if row.digest_status == "watch")
    )
    expected_blocked = _decimal_count(
        sum(1 for row in report.rows if row.digest_status == "blocked")
    )
    if report.ready_item_count != expected_ready:
        raise ValueError("ready_item_count must match rows")
    if report.watch_item_count != expected_watch:
        raise ValueError("watch_item_count must match rows")
    if report.blocked_item_count != expected_blocked:
        raise ValueError("blocked_item_count must match rows")
    if report.stale_cluster_item_count != _item_count_with(report.rows, STALE_CLUSTER_REASON):
        raise ValueError("stale_cluster_item_count must match rows")
    if report.source_gap_item_count != _item_count_with(report.rows, SOURCE_GAP_REASON):
        raise ValueError("source_gap_item_count must match rows")
    if report.thin_cluster_item_count != _item_count_with(report.rows, THIN_CLUSTER_REASON):
        raise ValueError("thin_cluster_item_count must match rows")
    if report.low_cluster_confidence_item_count != _item_count_with(
        report.rows,
        LOW_CLUSTER_CONFIDENCE_REASON,
    ):
        raise ValueError("low_cluster_confidence_item_count must match rows")
    if report.high_cluster_severity_item_count != _item_count_with(
        report.rows,
        HIGH_CLUSTER_SEVERITY_REASON,
    ):
        raise ValueError("high_cluster_severity_item_count must match rows")
    if report.liquidity_gap_item_count != _item_count_with(report.rows, LIQUIDITY_GAP_REASON):
        raise ValueError("liquidity_gap_item_count must match rows")
    confidence_score = _sum_decimal(row.confidence_score for row in report.rows)
    if report.average_confidence_score != _ratio(confidence_score, report.item_count):
        raise ValueError("average_confidence_score must match rows")
    if report.max_observed_cluster_age_seconds != _max_decimal(
        row.cluster_age_seconds for row in report.rows
    ):
        raise ValueError("max_observed_cluster_age_seconds must match rows")
    expected_reason_code_counts = _reason_code_counts(report.rows)
    if report.rows:
        if report.reason_code_counts != expected_reason_code_counts:
            raise ValueError("reason_code_counts must summarize rows")
        expected_reason_codes = tuple(item.reason_code for item in expected_reason_code_counts)
    else:
        expected_reason_code_counts = (
            MarketResearchHockeyInjuryClusterDigestReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                item_ratio=ZERO,
            ),
        )
        expected_reason_codes = (NO_INPUTS_REASON,)
        if report.reason_code_counts != expected_reason_code_counts:
            raise ValueError("reason_code_counts must summarize no inputs")
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        ready_count=report.ready_item_count,
        watch_count=report.watch_item_count,
        blocked_count=report.blocked_item_count,
        item_count=report.item_count,
    )
    if report.digest_status != expected_status:
        raise ValueError("digest_status must match rows")
    if report.recommended_next_step != NEXT_STEPS[report.digest_status]:
        raise ValueError("recommended_next_step must match digest_status")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized = tuple(reason_codes)
    for reason_code in normalized:
        _require_digest_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _require_digest_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_digest_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in NEXT_STEPS:
        raise ValueError(f"{field_name} must be ready, watch, or blocked")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical non-empty string")


def _require_public_news_reference(field_name: str, value: str) -> None:
    _require_canonical_string(field_name, value)
    lower = value.lower()
    for fragment in LIVE_ACTION_REFERENCE_FRAGMENTS:
        if fragment in lower:
            raise ValueError(f"{field_name} contains unsafe text")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    try:
        if not value.is_finite() or value < ZERO:
            raise ValueError(f"{field_name} must be nonnegative")
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be nonnegative") from exc
    return _six(value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    total_microseconds = (
        (Decimal(delta.days) * Decimal("86400") * MICROSECONDS_PER_SECOND)
        + (Decimal(delta.seconds) * MICROSECONDS_PER_SECOND)
        + Decimal(delta.microseconds)
    )
    return _six(total_microseconds / MICROSECONDS_PER_SECOND)


def _decimal_count(value: int) -> Decimal:
    return _six(Decimal(value))


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _six(total)


def _max_decimal(values: object) -> Decimal:
    maximum = ZERO
    for value in values:
        if value > maximum:
            maximum = value
    return _six(maximum)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _six(numerator / denominator)


def _six(value: Decimal) -> Decimal:
    return value.quantize(SIX_PLACES, rounding=ROUND_HALF_EVEN)


def _status_rank(status: str) -> int:
    return {"blocked": 0, "watch": 1, "ready": 2}[status]


def _redacted_public_reference(value: str) -> str:
    lower = value.lower()
    if "://" in lower or any(fragment in lower for fragment in UNSAFE_TEXT_FRAGMENTS):
        digest = sha256(value.encode("utf-8")).hexdigest()[:12]
        return f"sha256:{digest}"
    return value


def _payload_value(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, bool):
        return value
    if isinstance(value, float | int):
        raise ValueError("report output numeric values must be Decimal")
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _payload_value(item) for key, item in value.items()}
    return value
