"""Paper-only Phase 1 research time-decay priority digest."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from decimal import Context, Decimal, InvalidOperation, localcontext


__all__ = (
    "MarketEventTimeDecayPriorityDigestCandidate",
    "MarketEventTimeDecayPriorityDigestConfig",
    "MarketEventTimeDecayPriorityDigestReport",
    "MarketEventTimeDecayPriorityDigestRow",
    "build_market_event_time_decay_priority_digest",
    "market_event_time_decay_priority_digest_payload",
)


DEFAULT_CONFIG_VERSION = "market-event-time-decay-priority-digest-v0"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1.000000")
REDACTED_MARKET_REF_PREFIX = "redacted_market_ref_"
RESEARCH_PRIORITY_SUPPORT = "phase_1_research_priority_only_no_execution"

ROW_STATUSES = ("research_now", "block", "watch", "no_action")
REPORT_STATUSES = ("research_now", "watch", "block", "no_action")
ROW_STATUS_SORT_PRIORITY = {
    "research_now": 0,
    "block": 1,
    "watch": 2,
    "no_action": 3,
}

EMPTY_REASON_CODE = "market_event_time_decay_priority_digest_empty"
RESEARCH_NOW_REASON_CODE = "research_time_decay_research_now"
WATCH_REASON_CODE = "research_time_decay_watch"
BLOCK_REASON_CODE = "research_blocked_evidence_stale"
NO_ACTION_REASON_CODE = "research_time_decay_no_action"

REPORT_REASON_PRIORITY = (
    BLOCK_REASON_CODE,
    RESEARCH_NOW_REASON_CODE,
    WATCH_REASON_CODE,
    NO_ACTION_REASON_CODE,
    "evidence_refresh_overdue",
    "evidence_staleness_blocking",
    "close_window_urgent",
    "catalyst_window_active",
    "liquidity_decay_risk_high",
    "settlement_revision_window_short",
    EMPTY_REASON_CODE,
)

DECIMAL_CONTEXT = Context(prec=64)

UNSAFE_FIELD_FRAGMENTS = (
    "auth",
    "authorization",
    "private_key",
    "api_key",
    "secret",
    "bearer",
    "password",
    "wallet",
    "account",
    "recommend",
    "order",
    "cancel",
    "replace",
    "sign",
    "trade",
    "trading",
    "live-trading",
    "live_trading",
    "live trading",
    "position",
    "sizing",
    "notional",
    "stake",
    "shares",
    "quantity",
    "buy",
    "sell",
    "bid",
    "ask",
    "broker",
    "exchange_mutation",
    "market_id",
    "condition_id",
    "token_id",
    "slug",
    "question",
    "url",
    "uri",
    "endpoint",
    "clob",
    "candidate_id",
    "candidate_ref",
    "candidate_slug",
    "candidate_question",
    "source_id",
    "source_ref",
    "source_slug",
    "source_question",
    "source_url",
    "source_uri",
    "network",
    "request",
    "database",
    "db",
    "sqlite",
    "postgres",
    "mysql",
    "redis",
    "env",
    "environment",
    "dotenv",
    "file",
    "path",
    "persist",
    "persistence",
    "write",
)

UNSAFE_VALUE_TOKENS = (
    "auth",
    "authorization",
    "secret",
    "token",
    "private",
    "bearer",
    "password",
    "wallet",
    "account",
    "recommend",
    "order",
    "cancel",
    "replace",
    "live-trading",
    "live_trading",
    "live trading",
    "trade",
    "trading",
    "position",
    "sizing",
    "notional",
    "stake",
    "shares",
    "quantity",
    "buy",
    "sell",
    "bid",
    "ask",
    "slug",
    "question",
    "market_id",
    "condition_id",
    "token_id",
    "source",
    "raw_text",
    "raw text",
    "polymarket.com",
    "clob",
    "candidate_id",
    "candidate_ref",
    "candidate_slug",
    "candidate_question",
    "source_feed",
    "source_id",
    "source_ref",
    "source_slug",
    "source_question",
    "source_url",
    "source_uri",
    "network",
    "request",
    "database",
    "db",
    "sqlite",
    "postgres",
    "mysql",
    "redis",
    "env",
    "environment",
    "dotenv",
    "file",
    "path",
    "persist",
    "persistence",
    "write",
)


@dataclass(frozen=True)
class MarketEventTimeDecayPriorityDigestConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    research_now_score: Decimal = Decimal("0.650000")
    watch_score: Decimal = Decimal("0.350000")
    close_watch_hours: Decimal = Decimal("72.000000")
    last_evidence_refresh_block_hours: Decimal = Decimal("48.000000")
    catalyst_soon_hours: Decimal = Decimal("24.000000")
    settlement_revision_short_hours: Decimal = Decimal("24.000000")
    evidence_staleness_block: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketEventTimeDecayPriorityDigestConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _reject_unsafe_string("config_version", self.config_version)
        for field_name in (
            "research_now_score",
            "watch_score",
            "evidence_staleness_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "close_watch_hours",
            "last_evidence_refresh_block_hours",
            "catalyst_soon_hours",
            "settlement_revision_short_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.research_now_score < self.watch_score:
            raise ValueError("research_now_score must be at least watch_score")
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class MarketEventTimeDecayPriorityDigestCandidate:
    redacted_market_ref: str
    hours_to_close: Decimal
    last_evidence_refresh_age_hours: Decimal
    upcoming_catalyst_hours: Decimal
    liquidity_decay_risk: Decimal
    settlement_revision_window_hours: Decimal
    evidence_staleness: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketEventTimeDecayPriorityDigestCandidate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_redacted_market_ref(self.redacted_market_ref)
        for field_name in (
            "hours_to_close",
            "last_evidence_refresh_age_hours",
            "upcoming_catalyst_hours",
            "settlement_revision_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("liquidity_decay_risk", "evidence_staleness"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("candidate", self)


@dataclass(frozen=True)
class MarketEventTimeDecayPriorityDigestRow:
    redacted_market_ref: str
    hours_to_close: Decimal
    last_evidence_refresh_age_hours: Decimal
    upcoming_catalyst_hours: Decimal
    liquidity_decay_risk: Decimal
    settlement_revision_window_hours: Decimal
    evidence_staleness: Decimal
    close_time_pressure: Decimal
    evidence_refresh_pressure: Decimal
    catalyst_pressure: Decimal
    liquidity_decay_pressure: Decimal
    settlement_revision_pressure: Decimal
    evidence_staleness_pressure: Decimal
    priority_score: Decimal
    research_priority_status: str
    reason_codes: tuple[str, ...]
    research_priority_support: str = RESEARCH_PRIORITY_SUPPORT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketEventTimeDecayPriorityDigestRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_redacted_market_ref(self.redacted_market_ref)
        for field_name in (
            "hours_to_close",
            "last_evidence_refresh_age_hours",
            "upcoming_catalyst_hours",
            "settlement_revision_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "liquidity_decay_risk",
            "evidence_staleness",
            "close_time_pressure",
            "evidence_refresh_pressure",
            "catalyst_pressure",
            "liquidity_decay_pressure",
            "settlement_revision_pressure",
            "evidence_staleness_pressure",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member(
            "research_priority_status",
            self.research_priority_status,
            ROW_STATUSES,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if self.research_priority_support != RESEARCH_PRIORITY_SUPPORT:
            raise ValueError("research_priority_support must be research-only")
        _require_safety_flags("row", self)


@dataclass(frozen=True)
class MarketEventTimeDecayPriorityDigestReport:
    config_version: str
    candidate_count: Decimal
    research_now_count: Decimal
    block_count: Decimal
    watch_count: Decimal
    no_action_count: Decimal
    max_priority_score: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[MarketEventTimeDecayPriorityDigestRow, ...]
    research_priority_support: str = RESEARCH_PRIORITY_SUPPORT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "MarketEventTimeDecayPriorityDigestReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _reject_unsafe_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "research_now_count",
            "block_count",
            "watch_count",
            "no_action_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_priority_score", "average_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, REPORT_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if self.research_priority_support != RESEARCH_PRIORITY_SUPPORT:
            raise ValueError("research_priority_support must be research-only")
        _validate_report(self)
        _require_safety_flags("report", self)


def build_market_event_time_decay_priority_digest(
    candidates: Iterable[object],
    *,
    config: MarketEventTimeDecayPriorityDigestConfig,
) -> MarketEventTimeDecayPriorityDigestReport:
    if type(config) is not MarketEventTimeDecayPriorityDigestConfig:
        raise ValueError(
            "config must be a MarketEventTimeDecayPriorityDigestConfig",
        )
    _require_safety_flags("config", config)
    source_candidates = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_row_from_candidate(candidate, config=config) for candidate in source_candidates),
            key=_row_sort_key,
        ),
    )
    return MarketEventTimeDecayPriorityDigestReport(
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        research_now_count=_status_count(rows, "research_now"),
        block_count=_status_count(rows, "block"),
        watch_count=_status_count(rows, "watch"),
        no_action_count=_status_count(rows, "no_action"),
        max_priority_score=_max_priority_score(rows),
        average_priority_score=_average_priority_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def market_event_time_decay_priority_digest_payload(
    report: MarketEventTimeDecayPriorityDigestReport,
) -> dict[str, object]:
    if type(report) is not MarketEventTimeDecayPriorityDigestReport:
        raise ValueError(
            "report must be a MarketEventTimeDecayPriorityDigestReport",
        )
    _require_safety_flags("report", report)
    payload: dict[str, object] = {
        "config_version": report.config_version,
        "candidate_count": _count_payload(report.candidate_count),
        "research_now_count": _count_payload(report.research_now_count),
        "block_count": _count_payload(report.block_count),
        "watch_count": _count_payload(report.watch_count),
        "no_action_count": _count_payload(report.no_action_count),
        "max_priority_score": _decimal_payload(report.max_priority_score),
        "average_priority_score": _decimal_payload(report.average_priority_score),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "research_priority_support": report.research_priority_support,
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload(
        "market_event_time_decay_priority_digest_payload",
        payload,
    )
    return payload


def _row_payload(row: MarketEventTimeDecayPriorityDigestRow) -> dict[str, object]:
    _require_safety_flags("row", row)
    return {
        "redacted_market_ref": row.redacted_market_ref,
        "hours_to_close": _decimal_payload(row.hours_to_close),
        "last_evidence_refresh_age_hours": _decimal_payload(
            row.last_evidence_refresh_age_hours,
        ),
        "upcoming_catalyst_hours": _decimal_payload(row.upcoming_catalyst_hours),
        "liquidity_decay_risk": _decimal_payload(row.liquidity_decay_risk),
        "settlement_revision_window_hours": _decimal_payload(
            row.settlement_revision_window_hours,
        ),
        "evidence_staleness": _decimal_payload(row.evidence_staleness),
        "close_time_pressure": _decimal_payload(row.close_time_pressure),
        "evidence_refresh_pressure": _decimal_payload(row.evidence_refresh_pressure),
        "catalyst_pressure": _decimal_payload(row.catalyst_pressure),
        "liquidity_decay_pressure": _decimal_payload(row.liquidity_decay_pressure),
        "settlement_revision_pressure": _decimal_payload(
            row.settlement_revision_pressure,
        ),
        "evidence_staleness_pressure": _decimal_payload(
            row.evidence_staleness_pressure,
        ),
        "priority_score": _decimal_payload(row.priority_score),
        "research_priority_status": row.research_priority_status,
        "reason_codes": list(row.reason_codes),
        "research_priority_support": row.research_priority_support,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_from_candidate(
    candidate: MarketEventTimeDecayPriorityDigestCandidate,
    *,
    config: MarketEventTimeDecayPriorityDigestConfig,
) -> MarketEventTimeDecayPriorityDigestRow:
    close_time_pressure = _inverse_hours_pressure(
        candidate.hours_to_close,
        config.close_watch_hours,
    )
    evidence_refresh_pressure = _capped_ratio(
        candidate.last_evidence_refresh_age_hours,
        config.last_evidence_refresh_block_hours,
    )
    catalyst_pressure = _inverse_hours_pressure(
        candidate.upcoming_catalyst_hours,
        config.catalyst_soon_hours,
    )
    settlement_revision_pressure = _inverse_hours_pressure(
        candidate.settlement_revision_window_hours,
        config.settlement_revision_short_hours,
    )
    priority_score = _priority_score(
        close_time_pressure=close_time_pressure,
        evidence_refresh_pressure=evidence_refresh_pressure,
        catalyst_pressure=catalyst_pressure,
        liquidity_decay_pressure=candidate.liquidity_decay_risk,
        settlement_revision_pressure=settlement_revision_pressure,
        evidence_staleness_pressure=candidate.evidence_staleness,
    )
    research_priority_status, terminal_reason = _priority_status_and_reason(
        candidate=candidate,
        priority_score=priority_score,
        config=config,
    )
    return MarketEventTimeDecayPriorityDigestRow(
        redacted_market_ref=candidate.redacted_market_ref,
        hours_to_close=candidate.hours_to_close,
        last_evidence_refresh_age_hours=candidate.last_evidence_refresh_age_hours,
        upcoming_catalyst_hours=candidate.upcoming_catalyst_hours,
        liquidity_decay_risk=candidate.liquidity_decay_risk,
        settlement_revision_window_hours=candidate.settlement_revision_window_hours,
        evidence_staleness=candidate.evidence_staleness,
        close_time_pressure=close_time_pressure,
        evidence_refresh_pressure=evidence_refresh_pressure,
        catalyst_pressure=catalyst_pressure,
        liquidity_decay_pressure=candidate.liquidity_decay_risk,
        settlement_revision_pressure=settlement_revision_pressure,
        evidence_staleness_pressure=candidate.evidence_staleness,
        priority_score=priority_score,
        research_priority_status=research_priority_status,
        reason_codes=_normalize_reason_codes(
            (
                *candidate.reason_codes,
                terminal_reason,
                *_timing_reason_codes(candidate, config=config),
            ),
            require_nonempty=True,
        ),
    )


def _priority_score(
    *,
    close_time_pressure: Decimal,
    evidence_refresh_pressure: Decimal,
    catalyst_pressure: Decimal,
    liquidity_decay_pressure: Decimal,
    settlement_revision_pressure: Decimal,
    evidence_staleness_pressure: Decimal,
) -> Decimal:
    score = _sum_decimal(
        (
            _multiply_decimal(close_time_pressure, Decimal("0.300000")),
            _multiply_decimal(evidence_refresh_pressure, Decimal("0.200000")),
            _multiply_decimal(catalyst_pressure, Decimal("0.150000")),
            _multiply_decimal(liquidity_decay_pressure, Decimal("0.150000")),
            _multiply_decimal(settlement_revision_pressure, Decimal("0.100000")),
            _multiply_decimal(evidence_staleness_pressure, Decimal("0.100000")),
        ),
    )
    return _clamp_probability(score)


def _priority_status_and_reason(
    *,
    candidate: MarketEventTimeDecayPriorityDigestCandidate,
    priority_score: Decimal,
    config: MarketEventTimeDecayPriorityDigestConfig,
) -> tuple[str, str]:
    if (
        candidate.last_evidence_refresh_age_hours
        >= config.last_evidence_refresh_block_hours
        or candidate.evidence_staleness >= config.evidence_staleness_block
    ):
        return "block", BLOCK_REASON_CODE
    if priority_score >= config.research_now_score:
        return "research_now", RESEARCH_NOW_REASON_CODE
    if priority_score >= config.watch_score:
        return "watch", WATCH_REASON_CODE
    return "no_action", NO_ACTION_REASON_CODE


def _timing_reason_codes(
    candidate: MarketEventTimeDecayPriorityDigestCandidate,
    *,
    config: MarketEventTimeDecayPriorityDigestConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if candidate.hours_to_close <= Decimal("24.000000"):
        reason_codes.append("close_window_urgent")
    elif candidate.hours_to_close <= config.close_watch_hours:
        reason_codes.append("close_window_active")
    else:
        reason_codes.append("close_window_distant")

    if (
        candidate.last_evidence_refresh_age_hours
        >= config.last_evidence_refresh_block_hours
    ):
        reason_codes.append("evidence_refresh_overdue")
    elif candidate.last_evidence_refresh_age_hours >= Decimal("12.000000"):
        reason_codes.append("evidence_refresh_aging")
    else:
        reason_codes.append("evidence_refresh_recent")

    if candidate.upcoming_catalyst_hours <= config.catalyst_soon_hours:
        reason_codes.append("catalyst_window_active")
    else:
        reason_codes.append("catalyst_window_distant")

    if candidate.liquidity_decay_risk >= Decimal("0.700000"):
        reason_codes.append("liquidity_decay_risk_high")
    else:
        reason_codes.append("liquidity_decay_risk_contained")

    if (
        candidate.settlement_revision_window_hours
        <= config.settlement_revision_short_hours
    ):
        reason_codes.append("settlement_revision_window_short")
    else:
        reason_codes.append("settlement_revision_window_open")

    if candidate.evidence_staleness >= config.evidence_staleness_block:
        reason_codes.append("evidence_staleness_blocking")
    elif candidate.evidence_staleness >= Decimal("0.700000"):
        reason_codes.append("evidence_staleness_high")
    else:
        reason_codes.append("evidence_staleness_contained")

    return tuple(reason_codes)


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[MarketEventTimeDecayPriorityDigestCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        rows = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    normalized = tuple(_candidate_from_supplied_row(row) for row in rows)
    seen: set[str] = set()
    for row in normalized:
        if row.redacted_market_ref in seen:
            raise ValueError("duplicate redacted_market_ref")
        seen.add(row.redacted_market_ref)
    return normalized


def _candidate_from_supplied_row(
    row: object,
) -> MarketEventTimeDecayPriorityDigestCandidate:
    if type(row) is MarketEventTimeDecayPriorityDigestCandidate:
        _require_safety_flags("candidate", row)
        return row
    raise ValueError(
        "candidates must contain MarketEventTimeDecayPriorityDigestCandidate",
    )


def _normalize_rows(
    rows: object,
) -> tuple[MarketEventTimeDecayPriorityDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketEventTimeDecayPriorityDigestRow:
            raise ValueError(
                "rows must contain MarketEventTimeDecayPriorityDigestRow",
            )
        _require_safety_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return normalized


def _row_sort_key(
    row: MarketEventTimeDecayPriorityDigestRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        ROW_STATUS_SORT_PRIORITY[row.research_priority_status],
        -row.priority_score,
        row.hours_to_close,
        row.upcoming_catalyst_hours,
        row.redacted_market_ref,
    )


def _status_count(
    rows: tuple[MarketEventTimeDecayPriorityDigestRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if row.research_priority_status == status),
    )


def _max_priority_score(
    rows: tuple[MarketEventTimeDecayPriorityDigestRow, ...],
) -> Decimal:
    if not rows:
        return _zero()
    return max(row.priority_score for row in rows)


def _average_priority_score(
    rows: tuple[MarketEventTimeDecayPriorityDigestRow, ...],
) -> Decimal:
    if not rows:
        return _zero()
    return _ratio_decimal(
        _sum_decimal(row.priority_score for row in rows),
        _count_decimal(len(rows)),
    )


def _report_status(rows: tuple[MarketEventTimeDecayPriorityDigestRow, ...]) -> str:
    if any(row.research_priority_status == "block" for row in rows):
        return "block"
    if any(row.research_priority_status == "research_now" for row in rows):
        return "research_now"
    if any(row.research_priority_status == "watch" for row in rows):
        return "watch"
    return "no_action"


def _report_reason_codes(
    rows: tuple[MarketEventTimeDecayPriorityDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    observed: set[str] = set()
    for row in rows:
        observed.update(row.reason_codes)
    prioritized = tuple(
        reason_code
        for reason_code in REPORT_REASON_PRIORITY
        if reason_code in observed
    )
    extras = tuple(sorted(observed.difference(REPORT_REASON_PRIORITY)))
    return prioritized + extras


def _validate_report(report: MarketEventTimeDecayPriorityDigestReport) -> None:
    if report.candidate_count != _count_decimal(len(report.rows)):
        raise ValueError("candidate_count must match rows")
    if report.research_now_count != _status_count(report.rows, "research_now"):
        raise ValueError("research_now_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.no_action_count != _status_count(report.rows, "no_action"):
        raise ValueError("no_action_count must match rows")
    if report.max_priority_score != _max_priority_score(report.rows):
        raise ValueError("max_priority_score must match rows")
    if report.average_priority_score != _average_priority_score(report.rows):
        raise ValueError("average_priority_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _require_safety_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only") is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only") is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly") is not True:
        raise ValueError(f"readonly must be True for {label}")
    _reject_unsafe_fields(label, value)
    _reject_unsafe_strings(label, value)


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    _reject_unsafe_fields(label, payload)
    _reject_unsafe_strings(label, payload)


def _reject_unsafe_fields(label: str, payload: object) -> None:
    for key in _iter_keys(payload):
        normalized_key = key.lower()
        if any(fragment in normalized_key for fragment in UNSAFE_FIELD_FRAGMENTS):
            raise ValueError(f"unsafe surface field in {label}: {key}")


def _reject_unsafe_strings(label: str, payload: object) -> None:
    for value in _iter_strings(payload):
        _reject_unsafe_string(label, value)


def _reject_unsafe_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if _contains_url(value):
        raise ValueError(f"{field_name} must not contain URLs")
    if any(token in lowered for token in UNSAFE_VALUE_TOKENS):
        raise ValueError(f"{field_name} must not expose unsafe tokens")


def _iter_keys(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_keys(asdict(value))
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            keys.append(key)
            keys.extend(_iter_keys(item))
        return tuple(keys)
    if isinstance(value, (list, tuple)):
        keys = []
        for item in value:
            keys.extend(_iter_keys(item))
        return tuple(keys)
    return ()


def _iter_strings(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_strings(asdict(value))
    if isinstance(value, dict):
        strings: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            strings.append(key)
            strings.extend(_iter_strings(item))
        return tuple(strings)
    if isinstance(value, (list, tuple)):
        strings = []
        for item in value:
            strings.extend(_iter_strings(item))
        return tuple(strings)
    if type(value) is str:
        return (value,)
    return ()


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")


def _require_redacted_market_ref(value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("redacted_market_ref must be a canonical string")
    if _contains_url(value):
        raise ValueError("redacted_market_ref must not contain URLs")
    if not value.startswith(REDACTED_MARKET_REF_PREFIX):
        raise ValueError("redacted_market_ref must be redacted")
    if value != value.lower():
        raise ValueError("redacted_market_ref must be lowercase")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("redacted_market_ref must be canonical")
    _reject_unsafe_string("redacted_market_ref", value)


def _contains_url(value: str) -> bool:
    lowered = value.lower()
    return (
        "://" in lowered
        or lowered.startswith("www.")
        or "polymarket.com" in lowered
    )


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a nonnegative count Decimal")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _normalize_reason_codes(
    values: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_canonical_reason_code("reason_codes", reason_code)
        _reject_unsafe_string("reason_codes", reason_code)
    return tuple(dict.fromkeys(reason_codes))


def _require_canonical_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value != value.lower() or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")


def _inverse_hours_pressure(value: Decimal, scale: Decimal) -> Decimal:
    if value >= scale:
        return _zero()
    return _clamp_probability(_ratio_decimal(_subtract_decimal(scale, value), scale))


def _capped_ratio(value: Decimal, scale: Decimal) -> Decimal:
    if value >= scale:
        return ONE.quantize(QUANTUM)
    return _clamp_probability(_ratio_decimal(value, scale))


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _normalize_decimal("probability", value)
    if normalized < ZERO:
        return _zero()
    if normalized > ONE:
        return ONE.quantize(QUANTUM)
    return normalized


def _subtract_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first - second).quantize(QUANTUM)


def _multiply_decimal(first: Decimal, second: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (first * second).quantize(QUANTUM)


def _ratio_decimal(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for value in values:
            total += value
        return total.quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _zero() -> Decimal:
    return ZERO.quantize(QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value), "f")


def _count_payload(value: Decimal) -> str:
    return _decimal_payload(_normalize_count_decimal("payload count", value))
