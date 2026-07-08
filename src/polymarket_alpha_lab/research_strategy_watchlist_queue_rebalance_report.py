"""Pure public-safe research watchlist queue rebalance report."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any, Iterable


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_WATCHLIST_QUEUE_REBALANCE_CONFIG_VERSION",
    "REBALANCE_STATUSES",
    "ResearchStrategyWatchlistQueueEntry",
    "ResearchStrategyWatchlistQueueRebalanceConfig",
    "ResearchStrategyWatchlistQueueRebalanceItem",
    "ResearchStrategyWatchlistQueueRebalanceReport",
    "build_research_strategy_watchlist_queue_rebalance_report",
    "research_strategy_watchlist_queue_rebalance_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_WATCHLIST_QUEUE_REBALANCE_CONFIG_VERSION = (
    "research-strategy-watchlist-queue-rebalance-v0"
)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
REBALANCE_STATUSES = frozenset((PASS_STATUS, WATCH_STATUS, BLOCK_STATUS))

REASON_PREFIX = "research_strategy_watchlist_queue_rebalance_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
PASS_REASON = f"{REASON_PREFIX}pass"
URGENCY_WATCH_REASON = f"{REASON_PREFIX}urgency_watch"
URGENCY_BLOCK_REASON = f"{REASON_PREFIX}urgency_block"
CONFIDENCE_DRIFT_WATCH_REASON = f"{REASON_PREFIX}confidence_drift_watch"
CONFIDENCE_DRIFT_BLOCK_REASON = f"{REASON_PREFIX}confidence_drift_block"
COST_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}cost_pressure_watch"
COST_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}cost_pressure_block"
CAPACITY_WATCH_REASON = f"{REASON_PREFIX}capacity_watch"
CAPACITY_BLOCK_REASON = f"{REASON_PREFIX}capacity_block"
EVIDENCE_REFRESH_DUE_REASON = f"{REASON_PREFIX}evidence_refresh_due"
EVIDENCE_STALE_REASON = f"{REASON_PREFIX}evidence_stale"

REASON_CODE_PRIORITY = (
    NO_INPUTS_REASON,
    URGENCY_BLOCK_REASON,
    CONFIDENCE_DRIFT_BLOCK_REASON,
    COST_PRESSURE_BLOCK_REASON,
    CAPACITY_BLOCK_REASON,
    EVIDENCE_STALE_REASON,
    URGENCY_WATCH_REASON,
    CONFIDENCE_DRIFT_WATCH_REASON,
    COST_PRESSURE_WATCH_REASON,
    CAPACITY_WATCH_REASON,
    EVIDENCE_REFRESH_DUE_REASON,
    PASS_REASON,
)
REASON_CODE_SET = frozenset(REASON_CODE_PRIORITY)

NEXT_STEPS = {
    PASS_STATUS: "retain_report_only_research_watchlist_rebalance",
    WATCH_STATUS: "watch_report_only_research_watchlist_rebalance",
    BLOCK_STATUS: "block_report_only_research_watchlist_rebalance",
}
ROW_NEXT_STEPS = {
    PASS_STATUS: "retain_report_only_watchlist_review",
    WATCH_STATUS: "refresh_evidence_then_reassess",
    BLOCK_STATUS: "pause_until_research_capacity_recovers",
}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MAX_REBALANCE_SCORE = Decimal("0.800000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

URGENCY_WEIGHT = Decimal("0.367812")
EVIDENCE_WEIGHT = Decimal("0.194666")
CONFIDENCE_DRIFT_WEIGHT = Decimal("0.200000")
COST_PRESSURE_WEIGHT = Decimal("0.150000")
CAPACITY_PRESSURE_WEIGHT = Decimal("0.082560")

PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "rebalance_status",
        "next_step",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "capacity_limited_count",
        "stale_evidence_count",
        "high_confidence_drift_count",
        "high_cost_pressure_count",
        "max_rebalance_score",
        "average_rebalance_score",
        "rows",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
        "derived_validation_digest",
    ),
)
PUBLIC_ROW_KEYS = frozenset(
    (
        "public_item_digest",
        "urgency_score",
        "evidence_age_seconds",
        "confidence_score_previous",
        "confidence_score_current",
        "confidence_drift",
        "cost_pressure_score",
        "team_capacity_score",
        "capacity_pressure_score",
        "rebalance_score",
        "rebalance_rank",
        "rebalance_status",
        "queue_rebalance_step",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
UNSAFE_PUBLIC_TERMS = frozenset(
    (
        "unsafe term:api_key",
        "unsafe term:auth",
        "unsafe term:cancel",
        "unsafe term:candidate_id",
        "unsafe term:database",
        "unsafe term:dsn",
        "unsafe term:endpoint",
        "unsafe term:execute",
        "unsafe term:execution",
        "unsafe term:fill",
        "unsafe term:http",
        "unsafe term:live_execution",
        "unsafe term:market_id",
        "unsafe term:market_slug",
        "unsafe term:network",
        "unsafe term:nonce",
        "unsafe term:order",
        "unsafe term:position",
        "unsafe term:position_size",
        "unsafe term:private-key",
        "unsafe term:private_key",
        "unsafe term:question",
        "unsafe term:secret",
        "unsafe term:signature",
        "unsafe term:source_ref",
        "unsafe term:source_text",
        "unsafe term:source_url",
        "unsafe term:sql",
        "unsafe term:submit",
        "unsafe term:token",
        "unsafe term:trade",
        "unsafe term:transfer",
        "unsafe term:url",
        "unsafe term:wallet",
        "unsafe term:wallet_order",
        "unsafe term:websocket",
    ),
)


@dataclass(frozen=True)
class ResearchStrategyWatchlistQueueRebalanceConfig:
    config_version: str = DEFAULT_RESEARCH_STRATEGY_WATCHLIST_QUEUE_REBALANCE_CONFIG_VERSION
    watch_urgency_score: Decimal = Decimal("0.550000")
    block_urgency_score: Decimal = Decimal("0.850000")
    fresh_evidence_max_age_seconds: Decimal = Decimal("86400.000000")
    stale_evidence_age_seconds: Decimal = Decimal("259200.000000")
    watch_confidence_drift: Decimal = Decimal("0.100000")
    block_confidence_drift: Decimal = Decimal("0.250000")
    watch_cost_pressure: Decimal = Decimal("0.500000")
    block_cost_pressure: Decimal = Decimal("0.750000")
    watch_team_capacity: Decimal = Decimal("0.400000")
    block_team_capacity: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyWatchlistQueueRebalanceConfig:
            raise TypeError(
                "ResearchStrategyWatchlistQueueRebalanceConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyWatchlistQueueRebalanceConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_WATCHLIST_QUEUE_REBALANCE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_urgency_score",
            "block_urgency_score",
            "watch_confidence_drift",
            "block_confidence_drift",
            "watch_cost_pressure",
            "block_cost_pressure",
            "watch_team_capacity",
            "block_team_capacity",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fresh_evidence_max_age_seconds",
            "stale_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyWatchlistQueueEntry:
    watchlist_key: str
    urgency_score: Decimal
    evidence_age_seconds: Decimal
    confidence_score_previous: Decimal
    confidence_score_current: Decimal
    cost_pressure_score: Decimal
    team_capacity_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyWatchlistQueueEntry:
            raise TypeError(
                "ResearchStrategyWatchlistQueueEntry does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyWatchlistQueueEntry, "entry")
        _require_canonical_string("watchlist_key", self.watchlist_key)
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        for field_name in (
            "urgency_score",
            "confidence_score_previous",
            "confidence_score_current",
            "cost_pressure_score",
            "team_capacity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("entry", self)


@dataclass(frozen=True)
class ResearchStrategyWatchlistQueueRebalanceItem:
    public_item_digest: str
    urgency_score: Decimal
    evidence_age_seconds: Decimal
    confidence_score_previous: Decimal
    confidence_score_current: Decimal
    confidence_drift: Decimal
    cost_pressure_score: Decimal
    team_capacity_score: Decimal
    capacity_pressure_score: Decimal
    rebalance_score: Decimal
    rebalance_rank: Decimal
    rebalance_status: str
    queue_rebalance_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyWatchlistQueueRebalanceItem:
            raise TypeError(
                "ResearchStrategyWatchlistQueueRebalanceItem does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyWatchlistQueueRebalanceItem, "row")
        _require_digest("public_item_digest", self.public_item_digest)
        object.__setattr__(
            self,
            "evidence_age_seconds",
            _normalize_nonnegative_decimal(
                "evidence_age_seconds",
                self.evidence_age_seconds,
            ),
        )
        for field_name in (
            "urgency_score",
            "confidence_score_previous",
            "confidence_score_current",
            "confidence_drift",
            "cost_pressure_score",
            "team_capacity_score",
            "capacity_pressure_score",
            "rebalance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "rebalance_rank",
            _normalize_positive_count("rebalance_rank", self.rebalance_rank),
        )
        _require_rebalance_status("rebalance_status", self.rebalance_status)
        _require_rebalance_step(self.rebalance_status, self.queue_rebalance_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_item(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyWatchlistQueueRebalanceReport:
    generated_at: datetime
    config_version: str
    rebalance_status: str
    next_step: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    capacity_limited_count: Decimal
    stale_evidence_count: Decimal
    high_confidence_drift_count: Decimal
    high_cost_pressure_count: Decimal
    max_rebalance_score: Decimal
    average_rebalance_score: Decimal
    rows: tuple[ResearchStrategyWatchlistQueueRebalanceItem, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyWatchlistQueueRebalanceReport:
            raise TypeError(
                "ResearchStrategyWatchlistQueueRebalanceReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyWatchlistQueueRebalanceReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_rebalance_status("rebalance_status", self.rebalance_status)
        _require_canonical_string("next_step", self.next_step)
        for field_name in (
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "capacity_limited_count",
            "stale_evidence_count",
            "high_confidence_drift_count",
            "high_cost_pressure_count",
            "max_rebalance_score",
            "average_rebalance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_watchlist_queue_rebalance_report_payload(self)


def build_research_strategy_watchlist_queue_rebalance_report(
    entries: Iterable[ResearchStrategyWatchlistQueueEntry],
    *,
    config: ResearchStrategyWatchlistQueueRebalanceConfig,
    generated_at: datetime,
) -> ResearchStrategyWatchlistQueueRebalanceReport:
    if type(config) is not ResearchStrategyWatchlistQueueRebalanceConfig:
        raise ValueError("config must be a ResearchStrategyWatchlistQueueRebalanceConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_entries = _normalize_entries(entries)
    scored_rows = tuple(_item_from_entry(entry, config) for entry in source_entries)
    rows = tuple(
        ResearchStrategyWatchlistQueueRebalanceItem(
            public_item_digest=row.public_item_digest,
            urgency_score=row.urgency_score,
            evidence_age_seconds=row.evidence_age_seconds,
            confidence_score_previous=row.confidence_score_previous,
            confidence_score_current=row.confidence_score_current,
            confidence_drift=row.confidence_drift,
            cost_pressure_score=row.cost_pressure_score,
            team_capacity_score=row.team_capacity_score,
            capacity_pressure_score=row.capacity_pressure_score,
            rebalance_score=row.rebalance_score,
            rebalance_rank=_count_decimal(index),
            rebalance_status=row.rebalance_status,
            queue_rebalance_step=row.queue_rebalance_step,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(scored_rows, key=_row_sort_key), start=1)
    )
    reason_codes = _combined_reason_codes(rows)
    return ResearchStrategyWatchlistQueueRebalanceReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rebalance_status=_report_status(rows),
        next_step=NEXT_STEPS[_report_status(rows)],
        input_count=_count_decimal(len(source_entries)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        capacity_limited_count=_reason_count(rows, CAPACITY_WATCH_REASON)
        + _reason_count(rows, CAPACITY_BLOCK_REASON),
        stale_evidence_count=_reason_count(rows, EVIDENCE_REFRESH_DUE_REASON)
        + _reason_count(rows, EVIDENCE_STALE_REASON),
        high_confidence_drift_count=_reason_count(rows, CONFIDENCE_DRIFT_WATCH_REASON)
        + _reason_count(rows, CONFIDENCE_DRIFT_BLOCK_REASON),
        high_cost_pressure_count=_reason_count(rows, COST_PRESSURE_WATCH_REASON)
        + _reason_count(rows, COST_PRESSURE_BLOCK_REASON),
        max_rebalance_score=max((row.rebalance_score for row in rows), default=ZERO),
        average_rebalance_score=_ratio(
            _sum_decimal(row.rebalance_score for row in rows),
            _count_decimal(len(rows)),
        ),
        rows=rows,
        reason_codes=reason_codes,
    )


def research_strategy_watchlist_queue_rebalance_report_payload(
    report: ResearchStrategyWatchlistQueueRebalanceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyWatchlistQueueRebalanceReport:
        return _report_payload(report, include_digest=True)
    if type(report) is dict:
        return _validated_public_payload(report)
    raise ValueError("report must be a ResearchStrategyWatchlistQueueRebalanceReport")


def _item_from_entry(
    entry: ResearchStrategyWatchlistQueueEntry,
    config: ResearchStrategyWatchlistQueueRebalanceConfig,
) -> ResearchStrategyWatchlistQueueRebalanceItem:
    reason_codes = _entry_reason_codes(entry, config)
    status = _item_status(reason_codes)
    return ResearchStrategyWatchlistQueueRebalanceItem(
        public_item_digest=_public_item_digest(entry.watchlist_key),
        urgency_score=entry.urgency_score,
        evidence_age_seconds=entry.evidence_age_seconds,
        confidence_score_previous=entry.confidence_score_previous,
        confidence_score_current=entry.confidence_score_current,
        confidence_drift=_confidence_drift(entry),
        cost_pressure_score=entry.cost_pressure_score,
        team_capacity_score=entry.team_capacity_score,
        capacity_pressure_score=_capacity_pressure(entry),
        rebalance_score=_rebalance_score(entry, config),
        rebalance_rank=ONE,
        rebalance_status=status,
        queue_rebalance_step=ROW_NEXT_STEPS[status],
        reason_codes=reason_codes,
    )


def _entry_reason_codes(
    entry: ResearchStrategyWatchlistQueueEntry,
    config: ResearchStrategyWatchlistQueueRebalanceConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    confidence_drift = _confidence_drift(entry)
    if entry.urgency_score >= config.block_urgency_score:
        reason_codes.append(URGENCY_BLOCK_REASON)
    elif entry.urgency_score >= config.watch_urgency_score:
        reason_codes.append(URGENCY_WATCH_REASON)
    if confidence_drift >= config.block_confidence_drift:
        reason_codes.append(CONFIDENCE_DRIFT_BLOCK_REASON)
    elif confidence_drift >= config.watch_confidence_drift:
        reason_codes.append(CONFIDENCE_DRIFT_WATCH_REASON)
    if entry.cost_pressure_score >= config.block_cost_pressure:
        reason_codes.append(COST_PRESSURE_BLOCK_REASON)
    elif entry.cost_pressure_score >= config.watch_cost_pressure:
        reason_codes.append(COST_PRESSURE_WATCH_REASON)
    if entry.team_capacity_score <= config.block_team_capacity:
        reason_codes.append(CAPACITY_BLOCK_REASON)
    elif entry.team_capacity_score <= config.watch_team_capacity:
        reason_codes.append(CAPACITY_WATCH_REASON)
    if entry.evidence_age_seconds >= config.stale_evidence_age_seconds:
        reason_codes.append(EVIDENCE_STALE_REASON)
    elif entry.evidence_age_seconds > config.fresh_evidence_max_age_seconds:
        reason_codes.append(EVIDENCE_REFRESH_DUE_REASON)
    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes(tuple(reason_codes), require_nonempty=True)


def _rebalance_score(
    entry: ResearchStrategyWatchlistQueueEntry,
    config: ResearchStrategyWatchlistQueueRebalanceConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            URGENCY_WEIGHT * entry.urgency_score
            + EVIDENCE_WEIGHT * _evidence_pressure(entry, config)
            + CONFIDENCE_DRIFT_WEIGHT * _confidence_drift(entry)
            + COST_PRESSURE_WEIGHT * entry.cost_pressure_score
            + CAPACITY_PRESSURE_WEIGHT * _capacity_pressure(entry)
        )
    return _normalize_probability(
        "rebalance_score",
        min(_quantize_decimal(score), MAX_REBALANCE_SCORE),
    )


def _evidence_pressure(
    entry: ResearchStrategyWatchlistQueueEntry,
    config: ResearchStrategyWatchlistQueueRebalanceConfig,
) -> Decimal:
    if config.stale_evidence_age_seconds <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_probability(
            "evidence_pressure",
            _clamp_ratio(entry.evidence_age_seconds / config.stale_evidence_age_seconds),
        )


def _confidence_drift(entry: ResearchStrategyWatchlistQueueEntry) -> Decimal:
    return _quantize_probability(
        "confidence_drift",
        abs(entry.confidence_score_current - entry.confidence_score_previous),
    )


def _capacity_pressure(entry: ResearchStrategyWatchlistQueueEntry) -> Decimal:
    return _quantize_probability("capacity_pressure_score", ONE - entry.team_capacity_score)


def _public_item_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _item_status(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code
        in {
            URGENCY_BLOCK_REASON,
            CONFIDENCE_DRIFT_BLOCK_REASON,
            COST_PRESSURE_BLOCK_REASON,
            CAPACITY_BLOCK_REASON,
        }
        for reason_code in reason_codes
    ):
        return BLOCK_STATUS
    if reason_codes != (PASS_REASON,):
        return WATCH_STATUS
    return PASS_STATUS


def _report_status(
    rows: tuple[ResearchStrategyWatchlistQueueRebalanceItem, ...],
) -> str:
    if any(row.rebalance_status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.rebalance_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _combined_reason_codes(
    rows: tuple[ResearchStrategyWatchlistQueueRebalanceItem, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    found = {reason_code for row in rows for reason_code in row.reason_codes}
    return tuple(reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in found)


def _row_sort_key(
    row: ResearchStrategyWatchlistQueueRebalanceItem,
) -> tuple[Decimal, str]:
    return (-row.rebalance_score, row.public_item_digest)


def _normalize_entries(
    entries: Iterable[ResearchStrategyWatchlistQueueEntry],
) -> tuple[ResearchStrategyWatchlistQueueEntry, ...]:
    normalized = tuple(entries)
    seen: set[str] = set()
    for entry in normalized:
        if type(entry) is not ResearchStrategyWatchlistQueueEntry:
            raise ValueError("entries must contain ResearchStrategyWatchlistQueueEntry")
        _require_hard_flags("entry", entry)
        digest = _public_item_digest(entry.watchlist_key)
        if digest in seen:
            raise ValueError("entries must be unique")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchStrategyWatchlistQueueRebalanceItem, ...],
) -> tuple[ResearchStrategyWatchlistQueueRebalanceItem, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchStrategyWatchlistQueueRebalanceItem] = []
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyWatchlistQueueRebalanceItem:
            raise ValueError(
                "rows must contain ResearchStrategyWatchlistQueueRebalanceItem",
            )
        _require_hard_flags("row", row)
        if row.public_item_digest in seen:
            raise ValueError("rows must be unique")
        seen.add(row.public_item_digest)
        normalized.append(row)
    return tuple(normalized)


def _validate_config(config: ResearchStrategyWatchlistQueueRebalanceConfig) -> None:
    if config.watch_urgency_score > config.block_urgency_score:
        raise ValueError("watch_urgency_score must not exceed block_urgency_score")
    if config.fresh_evidence_max_age_seconds >= config.stale_evidence_age_seconds:
        raise ValueError(
            "fresh_evidence_max_age_seconds must be below stale_evidence_age_seconds",
        )
    if config.watch_confidence_drift > config.block_confidence_drift:
        raise ValueError("watch_confidence_drift must not exceed block_confidence_drift")
    if config.watch_cost_pressure > config.block_cost_pressure:
        raise ValueError("watch_cost_pressure must not exceed block_cost_pressure")
    if config.block_team_capacity > config.watch_team_capacity:
        raise ValueError("block_team_capacity must not exceed watch_team_capacity")


def _validate_item(item: ResearchStrategyWatchlistQueueRebalanceItem) -> None:
    if item.confidence_drift != _quantize_probability(
        "confidence_drift",
        abs(item.confidence_score_current - item.confidence_score_previous),
    ):
        raise ValueError("confidence_drift must match confidence scores")
    if item.capacity_pressure_score != _quantize_probability(
        "capacity_pressure_score",
        ONE - item.team_capacity_score,
    ):
        raise ValueError("capacity_pressure_score must match team_capacity_score")
    if item.queue_rebalance_step != ROW_NEXT_STEPS[item.rebalance_status]:
        raise ValueError("queue_rebalance_step must match rebalance_status")
    if item.rebalance_status != _item_status(item.reason_codes):
        raise ValueError("rebalance_status must match reason_codes")


def _validate_report(report: ResearchStrategyWatchlistQueueRebalanceReport) -> None:
    if report.next_step != NEXT_STEPS[report.rebalance_status]:
        raise ValueError("next_step must match rebalance_status")
    expected_input_count = _count_decimal(len(report.rows))
    if report.input_count < expected_input_count:
        raise ValueError("input_count must be at least rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    if report.capacity_limited_count != (
        _reason_count(report.rows, CAPACITY_WATCH_REASON)
        + _reason_count(report.rows, CAPACITY_BLOCK_REASON)
    ):
        raise ValueError("capacity_limited_count must match rows")
    if report.stale_evidence_count != (
        _reason_count(report.rows, EVIDENCE_REFRESH_DUE_REASON)
        + _reason_count(report.rows, EVIDENCE_STALE_REASON)
    ):
        raise ValueError("stale_evidence_count must match rows")
    if report.high_confidence_drift_count != (
        _reason_count(report.rows, CONFIDENCE_DRIFT_WATCH_REASON)
        + _reason_count(report.rows, CONFIDENCE_DRIFT_BLOCK_REASON)
    ):
        raise ValueError("high_confidence_drift_count must match rows")
    if report.high_cost_pressure_count != (
        _reason_count(report.rows, COST_PRESSURE_WATCH_REASON)
        + _reason_count(report.rows, COST_PRESSURE_BLOCK_REASON)
    ):
        raise ValueError("high_cost_pressure_count must match rows")
    sorted_rows = tuple(sorted(report.rows, key=_row_sort_key))
    for index, row in enumerate(report.rows, start=1):
        if row != sorted_rows[index - 1] or row.rebalance_rank != _count_decimal(index):
            raise ValueError("rows must follow deterministic sequence")
    if report.rebalance_status != _report_status(report.rows):
        raise ValueError("rebalance_status must match rows")
    if report.max_rebalance_score != max(
        (row.rebalance_score for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_rebalance_score must match rows")
    expected_average = _ratio(
        _sum_decimal(row.rebalance_score for row in report.rows),
        _count_decimal(len(report.rows)),
    )
    if report.average_rebalance_score != expected_average:
        raise ValueError("average_rebalance_score must match rows")
    if report.reason_codes != _combined_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _report_payload(
    report: ResearchStrategyWatchlistQueueRebalanceReport,
    *,
    include_digest: bool,
) -> dict[str, Any]:
    _require_hard_flags("report", report)
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "rebalance_status": report.rebalance_status,
        "next_step": report.next_step,
        "input_count": _decimal_string(report.input_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "capacity_limited_count": _decimal_string(report.capacity_limited_count),
        "stale_evidence_count": _decimal_string(report.stale_evidence_count),
        "high_confidence_drift_count": _decimal_string(
            report.high_confidence_drift_count,
        ),
        "high_cost_pressure_count": _decimal_string(report.high_cost_pressure_count),
        "max_rebalance_score": _decimal_string(report.max_rebalance_score),
        "average_rebalance_score": _decimal_string(report.average_rebalance_score),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(row: ResearchStrategyWatchlistQueueRebalanceItem) -> dict[str, Any]:
    _require_hard_flags("row", row)
    return {
        "public_item_digest": row.public_item_digest,
        "urgency_score": _decimal_string(row.urgency_score),
        "evidence_age_seconds": _decimal_string(row.evidence_age_seconds),
        "confidence_score_previous": _decimal_string(row.confidence_score_previous),
        "confidence_score_current": _decimal_string(row.confidence_score_current),
        "confidence_drift": _decimal_string(row.confidence_drift),
        "cost_pressure_score": _decimal_string(row.cost_pressure_score),
        "team_capacity_score": _decimal_string(row.team_capacity_score),
        "capacity_pressure_score": _decimal_string(row.capacity_pressure_score),
        "rebalance_score": _decimal_string(row.rebalance_score),
        "rebalance_rank": _decimal_string(row.rebalance_rank),
        "rebalance_status": row.rebalance_status,
        "queue_rebalance_step": row.queue_rebalance_step,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validated_public_payload(payload: dict[str, Any]) -> dict[str, Any]:
    _reject_unsafe_public_payload(payload)
    _require_public_payload_keys(payload)
    digest = _public_string(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    _require_digest("derived_validation_digest", digest)
    if digest != _public_payload_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    rows = tuple(_public_payload_row(row) for row in payload["rows"])
    report = ResearchStrategyWatchlistQueueRebalanceReport(
        generated_at=_public_datetime(payload["generated_at"]),
        config_version=_public_string("config_version", payload["config_version"]),
        rebalance_status=_public_string("rebalance_status", payload["rebalance_status"]),
        next_step=_public_string("next_step", payload["next_step"]),
        input_count=_public_decimal("input_count", payload["input_count"]),
        pass_count=_public_decimal("pass_count", payload["pass_count"]),
        watch_count=_public_decimal("watch_count", payload["watch_count"]),
        block_count=_public_decimal("block_count", payload["block_count"]),
        capacity_limited_count=_public_decimal(
            "capacity_limited_count",
            payload["capacity_limited_count"],
        ),
        stale_evidence_count=_public_decimal(
            "stale_evidence_count",
            payload["stale_evidence_count"],
        ),
        high_confidence_drift_count=_public_decimal(
            "high_confidence_drift_count",
            payload["high_confidence_drift_count"],
        ),
        high_cost_pressure_count=_public_decimal(
            "high_cost_pressure_count",
            payload["high_cost_pressure_count"],
        ),
        max_rebalance_score=_public_decimal(
            "max_rebalance_score",
            payload["max_rebalance_score"],
        ),
        average_rebalance_score=_public_decimal(
            "average_rebalance_score",
            payload["average_rebalance_score"],
        ),
        rows=rows,
        reason_codes=_public_reason_codes(payload["reason_codes"]),
        derived_validation_digest=digest,
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )
    return _report_payload(report, include_digest=True)


def _public_payload_row(payload: object) -> ResearchStrategyWatchlistQueueRebalanceItem:
    if type(payload) is not dict:
        raise ValueError("rows must contain dict payloads")
    _require_public_row_keys(payload)
    return ResearchStrategyWatchlistQueueRebalanceItem(
        public_item_digest=_public_string("public_item_digest", payload["public_item_digest"]),
        urgency_score=_public_decimal("urgency_score", payload["urgency_score"]),
        evidence_age_seconds=_public_decimal(
            "evidence_age_seconds",
            payload["evidence_age_seconds"],
        ),
        confidence_score_previous=_public_decimal(
            "confidence_score_previous",
            payload["confidence_score_previous"],
        ),
        confidence_score_current=_public_decimal(
            "confidence_score_current",
            payload["confidence_score_current"],
        ),
        confidence_drift=_public_decimal("confidence_drift", payload["confidence_drift"]),
        cost_pressure_score=_public_decimal(
            "cost_pressure_score",
            payload["cost_pressure_score"],
        ),
        team_capacity_score=_public_decimal(
            "team_capacity_score",
            payload["team_capacity_score"],
        ),
        capacity_pressure_score=_public_decimal(
            "capacity_pressure_score",
            payload["capacity_pressure_score"],
        ),
        rebalance_score=_public_decimal("rebalance_score", payload["rebalance_score"]),
        rebalance_rank=_public_decimal("rebalance_rank", payload["rebalance_rank"]),
        rebalance_status=_public_string("rebalance_status", payload["rebalance_status"]),
        queue_rebalance_step=_public_string(
            "queue_rebalance_step",
            payload["queue_rebalance_step"],
        ),
        reason_codes=_public_reason_codes(payload["reason_codes"]),
        paper_only=_public_true("paper_only", payload["paper_only"]),
        report_only=_public_true("report_only", payload["report_only"]),
        readonly=_public_true("readonly", payload["readonly"]),
    )


def _require_public_payload_keys(payload: dict[str, Any]) -> None:
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest is required")
    missing = PUBLIC_PAYLOAD_KEYS - payload.keys()
    if missing:
        raise ValueError("public payload is missing required fields")
    extra = payload.keys() - PUBLIC_PAYLOAD_KEYS
    if extra:
        raise ValueError("public payload contains unsupported fields")


def _require_public_row_keys(payload: dict[str, Any]) -> None:
    missing = PUBLIC_ROW_KEYS - payload.keys()
    if missing:
        raise ValueError("row payload is missing required fields")
    extra = payload.keys() - PUBLIC_ROW_KEYS
    if extra:
        raise ValueError("row payload contains unsupported fields")


def _derived_validation_digest(
    report: ResearchStrategyWatchlistQueueRebalanceReport,
) -> str:
    return _public_payload_digest(_report_payload(report, include_digest=False))


def _public_payload_digest(payload: dict[str, Any]) -> str:
    return sha256(repr(_canonical_payload_value(payload)).encode("utf-8")).hexdigest()


def _canonical_payload_value(value: object) -> object:
    if type(value) is dict:
        return tuple(
            (key, _canonical_payload_value(value[key]))
            for key in sorted(value)
            if key != "derived_validation_digest"
        )
    if type(value) is list:
        return tuple(_canonical_payload_value(item) for item in value)
    if type(value) in {str, bool}:
        return value
    raise ValueError("public payload numeric values must be Decimal-derived strings")


def _reject_unsafe_public_payload(value: object) -> None:
    if type(value) is dict:
        for key, nested in value.items():
            _reject_unsafe_public_text(key)
            _reject_unsafe_public_payload(nested)
        return
    if type(value) is list:
        for nested in value:
            _reject_unsafe_public_payload(nested)
        return
    if type(value) is str:
        _reject_unsafe_public_text(value)
        return
    if type(value) is bool:
        return
    raise ValueError("public payload numeric values must be Decimal-derived strings")


def _reject_unsafe_public_text(value: str) -> None:
    normalized = value.lower()
    for prefixed_term in UNSAFE_PUBLIC_TERMS:
        term = prefixed_term.removeprefix("unsafe term:")
        if term in normalized:
            raise ValueError("unsafe public payload surface")


def _public_datetime(value: object) -> datetime:
    if type(value) is not str:
        raise ValueError("generated_at must be a string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("generated_at must be an ISO datetime") from exc
    return _as_utc("generated_at", parsed)


def _public_string(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    return value


def _public_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal-derived string") from exc
    normalized = _normalize_decimal(field_name, decimal_value)
    if _decimal_string(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal-derived string")
    return normalized


def _public_true(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _public_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must be a list")
    return tuple(_public_string("reason_code", reason_code) for reason_code in value)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a 64-character hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a 64-character hex digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_rebalance_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REBALANCE_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_rebalance_step(status: str, value: object) -> None:
    _require_canonical_string("queue_rebalance_step", value)
    if value != ROW_NEXT_STEPS[status]:
        raise ValueError("queue_rebalance_step must match rebalance_status")


def _normalize_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in reason_codes:
        if reason_code not in REASON_CODE_SET:
            raise ValueError("reason_codes contains unsupported value")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(
        reason_code for reason_code in REASON_CODE_PRIORITY if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent != -6:
        raise ValueError(f"{field_name} must use six decimal places")
    return _quantize_decimal(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _quantize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _quantize_decimal(value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1")
    return decimal_value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _quantize_decimal(value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _decimal_string(value: Decimal) -> str:
    return format(value, ".6f")


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return value


def _status_count(
    rows: tuple[ResearchStrategyWatchlistQueueRebalanceItem, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.rebalance_status == status))


def _reason_count(
    rows: tuple[ResearchStrategyWatchlistQueueRebalanceItem, ...],
    reason_code: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize_decimal(total + value)
    return total


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(numerator / denominator)
