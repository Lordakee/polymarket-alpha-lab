from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_WATCHLIST_V2_CONFIG_VERSION = (
    "research-packet-resolution-outcome-watchlist-v2"
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_READY = "ready"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
PHASE1_STATUSES = (STATUS_READY, STATUS_WATCH, STATUS_BLOCKED)
_STATUS_SEVERITY = {
    STATUS_READY: 0,
    STATUS_WATCH: 1,
    STATUS_BLOCKED: 2,
}
_STATUS_SORT_RANK = {
    STATUS_BLOCKED: 0,
    STATUS_WATCH: 1,
    STATUS_READY: 2,
}

OFFICIAL_READY_REASON = "official_outcome_source_ready"
OFFICIAL_PARTIAL_REASON = "official_outcome_source_partial"
OFFICIAL_ABSENT_REASON = "official_outcome_source_absent"
AMBIGUITY_CLEAR_REASON = "resolution_ambiguity_clear"
AMBIGUITY_WATCH_REASON = "resolution_ambiguity_watch"
AMBIGUITY_BLOCKED_REASON = "resolution_ambiguity_blocked"
CONTRADICTIONS_ABSENT_REASON = "unresolved_contradictions_absent"
CONTRADICTIONS_PRESENT_REASON = "unresolved_contradictions_present"
CONTRADICTIONS_BLOCKING_REASON = "unresolved_contradictions_blocking"
SETTLEMENT_CLEAR_REASON = "settlement_lag_clear"
SETTLEMENT_WATCH_REASON = "settlement_lag_watch"
SETTLEMENT_BLOCKED_REASON = "settlement_lag_blocked"
EVIDENCE_COMPLETE_REASON = "resolution_evidence_complete"
EVIDENCE_INCOMPLETE_REASON = "resolution_evidence_incomplete"
EVIDENCE_ABSENT_REASON = "resolution_evidence_absent"
CLOSE_CLEAR_REASON = "close_time_clear"
CLOSE_NEAR_REASON = "close_time_near"
CLOSE_ELAPSED_REASON = "close_time_elapsed"
EMPTY_INPUT_REASON = "research_packet_resolution_outcome_watchlist_v2_empty_input"
CLEAR_REPORT_REASON = "phase1_resolution_outcome_watchlist_clear"

ROW_REASON_CODES = (
    OFFICIAL_READY_REASON,
    OFFICIAL_PARTIAL_REASON,
    OFFICIAL_ABSENT_REASON,
    AMBIGUITY_CLEAR_REASON,
    AMBIGUITY_WATCH_REASON,
    AMBIGUITY_BLOCKED_REASON,
    CONTRADICTIONS_ABSENT_REASON,
    CONTRADICTIONS_PRESENT_REASON,
    CONTRADICTIONS_BLOCKING_REASON,
    SETTLEMENT_CLEAR_REASON,
    SETTLEMENT_WATCH_REASON,
    SETTLEMENT_BLOCKED_REASON,
    EVIDENCE_COMPLETE_REASON,
    EVIDENCE_INCOMPLETE_REASON,
    EVIDENCE_ABSENT_REASON,
    CLOSE_CLEAR_REASON,
    CLOSE_NEAR_REASON,
    CLOSE_ELAPSED_REASON,
)
REPORT_REASON_CODES = ROW_REASON_CODES + (EMPTY_INPUT_REASON, CLEAR_REPORT_REASON)
_ROW_REASON_SET = frozenset(ROW_REASON_CODES)
_REPORT_REASON_SET = frozenset(REPORT_REASON_CODES)
_REASON_SORT_RANK = {reason_code: index for index, reason_code in enumerate(REPORT_REASON_CODES)}
_REASON_STATUS = {
    OFFICIAL_READY_REASON: STATUS_READY,
    OFFICIAL_PARTIAL_REASON: STATUS_WATCH,
    OFFICIAL_ABSENT_REASON: STATUS_BLOCKED,
    AMBIGUITY_CLEAR_REASON: STATUS_READY,
    AMBIGUITY_WATCH_REASON: STATUS_WATCH,
    AMBIGUITY_BLOCKED_REASON: STATUS_BLOCKED,
    CONTRADICTIONS_ABSENT_REASON: STATUS_READY,
    CONTRADICTIONS_PRESENT_REASON: STATUS_WATCH,
    CONTRADICTIONS_BLOCKING_REASON: STATUS_BLOCKED,
    SETTLEMENT_CLEAR_REASON: STATUS_READY,
    SETTLEMENT_WATCH_REASON: STATUS_WATCH,
    SETTLEMENT_BLOCKED_REASON: STATUS_BLOCKED,
    EVIDENCE_COMPLETE_REASON: STATUS_READY,
    EVIDENCE_INCOMPLETE_REASON: STATUS_WATCH,
    EVIDENCE_ABSENT_REASON: STATUS_BLOCKED,
    CLOSE_CLEAR_REASON: STATUS_READY,
    CLOSE_NEAR_REASON: STATUS_WATCH,
    CLOSE_ELAPSED_REASON: STATUS_BLOCKED,
}
_RISK_REASON_CODES = frozenset(
    reason_code
    for reason_code, status in _REASON_STATUS.items()
    if status != STATUS_READY
)

REPORT_DECIMAL_FIELDS = (
    "market_count",
    "ready_market_count",
    "watch_market_count",
    "blocked_market_count",
    "attention_market_count",
    "official_source_gap_market_count",
    "ambiguity_watch_market_count",
    "contradiction_market_count",
    "settlement_lag_market_count",
    "evidence_gap_market_count",
    "near_close_market_count",
    "max_priority_score",
    "average_priority_score",
)

_UNSAFE_PUBLIC_TOKENS = (
    "api_key",
    "auth",
    "credential",
    "database",
    "db_",
    "execution",
    "live_trading",
    "order",
    "private",
    "secret",
    "sql",
    "token",
    "trade",
    "trading",
    "wallet",
)


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeWatchlistV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_WATCHLIST_V2_CONFIG_VERSION
    )
    close_watch_window_seconds: Decimal = Decimal("86400.000000")
    min_official_outcome_source_readiness_ratio: Decimal = Decimal("1.000000")
    watch_ambiguity_score: Decimal = Decimal("0.250000")
    blocked_ambiguity_score: Decimal = Decimal("0.750000")
    blocked_contradiction_count: Decimal = Decimal("3.000000")
    watch_settlement_lag_seconds: Decimal = Decimal("900.000000")
    blocked_settlement_lag_seconds: Decimal = Decimal("3600.000000")
    min_evidence_completeness_ratio: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(
            self,
            ResearchPacketResolutionOutcomeWatchlistV2Config,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_WATCHLIST_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "close_watch_window_seconds",
            "watch_settlement_lag_seconds",
            "blocked_settlement_lag_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.close_watch_window_seconds <= ZERO:
            raise ValueError("close_watch_window_seconds must be positive")
        for field_name in (
            "min_official_outcome_source_readiness_ratio",
            "watch_ambiguity_score",
            "blocked_ambiguity_score",
            "min_evidence_completeness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "blocked_contradiction_count",
            _normalize_count_decimal(
                "blocked_contradiction_count",
                self.blocked_contradiction_count,
            ),
        )
        if self.blocked_contradiction_count <= ZERO:
            raise ValueError("blocked_contradiction_count must be positive")
        if self.watch_ambiguity_score > self.blocked_ambiguity_score:
            raise ValueError("watch_ambiguity_score must not exceed blocked_ambiguity_score")
        if self.watch_settlement_lag_seconds > self.blocked_settlement_lag_seconds:
            raise ValueError(
                "watch_settlement_lag_seconds must not exceed blocked_settlement_lag_seconds",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeWatchlistV2Market:
    packet_id: str
    market_id: str
    event_slug: str
    close_time: datetime
    official_outcome_source_count: Decimal
    ready_official_outcome_source_count: Decimal
    ambiguity_score: Decimal
    unresolved_contradiction_count: Decimal
    settlement_lag_seconds: Decimal
    evidence_completeness_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(
            self,
            ResearchPacketResolutionOutcomeWatchlistV2Market,
            "market",
        )
        for field_name in ("packet_id", "market_id", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "close_time", _as_utc("close_time", self.close_time))
        for field_name in (
            "official_outcome_source_count",
            "ready_official_outcome_source_count",
            "unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.ready_official_outcome_source_count > self.official_outcome_source_count:
            raise ValueError(
                "ready_official_outcome_source_count must not exceed official_outcome_source_count",
            )
        object.__setattr__(
            self,
            "ambiguity_score",
            _normalize_ratio_decimal("ambiguity_score", self.ambiguity_score),
        )
        object.__setattr__(
            self,
            "settlement_lag_seconds",
            _normalize_nonnegative_decimal(
                "settlement_lag_seconds",
                self.settlement_lag_seconds,
            ),
        )
        object.__setattr__(
            self,
            "evidence_completeness_ratio",
            _normalize_ratio_decimal(
                "evidence_completeness_ratio",
                self.evidence_completeness_ratio,
            ),
        )
        _require_hard_flags("market", self)
        _reject_unsafe_public_payload("market", self)


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeWatchlistV2Row:
    packet_id: str
    market_id: str
    event_slug: str
    close_time: datetime
    seconds_until_close: Decimal
    official_outcome_source_count: Decimal
    ready_official_outcome_source_count: Decimal
    official_outcome_source_readiness_ratio: Decimal
    ambiguity_score: Decimal
    unresolved_contradiction_count: Decimal
    settlement_lag_seconds: Decimal
    evidence_completeness_ratio: Decimal
    phase1_status: str
    phase1_priority_score: Decimal
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(
            self,
            ResearchPacketResolutionOutcomeWatchlistV2Row,
            "row",
        )
        for field_name in ("packet_id", "market_id", "event_slug"):
            _require_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "close_time", _as_utc("close_time", self.close_time))
        object.__setattr__(
            self,
            "seconds_until_close",
            _normalize_decimal("seconds_until_close", self.seconds_until_close),
        )
        for field_name in (
            "official_outcome_source_count",
            "ready_official_outcome_source_count",
            "unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        if self.ready_official_outcome_source_count > self.official_outcome_source_count:
            raise ValueError(
                "ready_official_outcome_source_count must not exceed official_outcome_source_count",
            )
        for field_name in (
            "official_outcome_source_readiness_ratio",
            "ambiguity_score",
            "evidence_completeness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_lag_seconds",
            _normalize_nonnegative_decimal(
                "settlement_lag_seconds",
                self.settlement_lag_seconds,
            ),
        )
        _require_choice("phase1_status", self.phase1_status, PHASE1_STATUSES)
        object.__setattr__(
            self,
            "phase1_priority_score",
            _normalize_nonnegative_decimal(
                "phase1_priority_score",
                self.phase1_priority_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _ROW_REASON_SET),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _set_or_validate_digest(self, "row")
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount:
    reason_code: str
    market_count: Decimal
    market_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(
            self,
            ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code, _REPORT_REASON_SET)
        object.__setattr__(
            self,
            "market_count",
            _normalize_count_decimal("market_count", self.market_count),
        )
        if self.market_count <= ZERO:
            raise ValueError("market_count must be positive")
        object.__setattr__(
            self,
            "market_ratio",
            _normalize_ratio_decimal("market_ratio", self.market_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchPacketResolutionOutcomeWatchlistV2Report:
    generated_at: datetime
    config_version: str
    report_status: str
    recommended_next_step: str
    market_count: Decimal
    ready_market_count: Decimal
    watch_market_count: Decimal
    blocked_market_count: Decimal
    attention_market_count: Decimal
    official_source_gap_market_count: Decimal
    ambiguity_watch_market_count: Decimal
    contradiction_market_count: Decimal
    settlement_lag_market_count: Decimal
    evidence_gap_market_count: Decimal
    near_close_market_count: Decimal
    max_priority_score: Decimal
    average_priority_score: Decimal
    rows: tuple[ResearchPacketResolutionOutcomeWatchlistV2Row, ...]
    reason_code_counts: tuple[
        ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_dataclass_type(
            self,
            ResearchPacketResolutionOutcomeWatchlistV2Report,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_PACKET_RESOLUTION_OUTCOME_WATCHLIST_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_choice("report_status", self.report_status, PHASE1_STATUSES)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        for field_name in REPORT_DECIMAL_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, _REPORT_REASON_SET),
        )
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _set_or_validate_digest(self, "report")
        _validate_report_consistency(self)


def build_research_packet_resolution_outcome_watchlist_v2_report(
    markets: Iterable[ResearchPacketResolutionOutcomeWatchlistV2Market],
    *,
    config: ResearchPacketResolutionOutcomeWatchlistV2Config | None = None,
    generated_at: datetime,
) -> ResearchPacketResolutionOutcomeWatchlistV2Report:
    cfg = config or ResearchPacketResolutionOutcomeWatchlistV2Config()
    if type(cfg) is not ResearchPacketResolutionOutcomeWatchlistV2Config:
        raise ValueError(
            "config must be exactly ResearchPacketResolutionOutcomeWatchlistV2Config",
        )
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_markets = _normalize_markets(markets)
    rows = tuple(
        sorted(
            (
                _row_from_market(market, config=cfg, generated_at=generated_at_utc)
                for market in normalized_markets
            ),
            key=_row_sort_key,
        ),
    )
    report_status = _report_status(rows)
    market_count = _count_decimal(len(rows))
    return ResearchPacketResolutionOutcomeWatchlistV2Report(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        report_status=report_status,
        recommended_next_step=_recommended_next_step(report_status),
        market_count=market_count,
        ready_market_count=_status_count(rows, STATUS_READY),
        watch_market_count=_status_count(rows, STATUS_WATCH),
        blocked_market_count=_status_count(rows, STATUS_BLOCKED),
        attention_market_count=_attention_count(rows),
        official_source_gap_market_count=_reason_market_count(
            rows,
            (OFFICIAL_PARTIAL_REASON, OFFICIAL_ABSENT_REASON),
        ),
        ambiguity_watch_market_count=_reason_market_count(
            rows,
            (AMBIGUITY_WATCH_REASON, AMBIGUITY_BLOCKED_REASON),
        ),
        contradiction_market_count=_reason_market_count(
            rows,
            (CONTRADICTIONS_PRESENT_REASON, CONTRADICTIONS_BLOCKING_REASON),
        ),
        settlement_lag_market_count=_reason_market_count(
            rows,
            (SETTLEMENT_WATCH_REASON, SETTLEMENT_BLOCKED_REASON),
        ),
        evidence_gap_market_count=_reason_market_count(
            rows,
            (EVIDENCE_INCOMPLETE_REASON, EVIDENCE_ABSENT_REASON),
        ),
        near_close_market_count=_reason_market_count(
            rows,
            (CLOSE_NEAR_REASON, CLOSE_ELAPSED_REASON),
        ),
        max_priority_score=max(
            (row.phase1_priority_score for row in rows),
            default=ZERO,
        ),
        average_priority_score=_average_decimal(
            row.phase1_priority_score for row in rows
        ),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, market_count),
        reason_codes=_report_reason_codes(rows),
    )


def research_packet_resolution_outcome_watchlist_v2_payload(
    report: ResearchPacketResolutionOutcomeWatchlistV2Report | Mapping[str, Any],
) -> dict[str, Any]:
    if isinstance(report, Mapping):
        return validate_research_packet_resolution_outcome_watchlist_v2_public_payload(
            report,
        )
    if type(report) is not ResearchPacketResolutionOutcomeWatchlistV2Report:
        raise ValueError(
            "report must be exactly ResearchPacketResolutionOutcomeWatchlistV2Report",
        )
    _require_payload_safe_value("report", report)
    return _json_ready(report)


def validate_research_packet_resolution_outcome_watchlist_v2_public_payload(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise ValueError("payload must be a mapping")
    _reject_unsafe_public_payload("payload", payload)
    report = _report_from_payload(payload)
    ready_payload = _json_ready(report)
    if ready_payload != dict(payload):
        raise ValueError("payload must be constructor-normalized")
    return ready_payload


def _row_from_market(
    market: ResearchPacketResolutionOutcomeWatchlistV2Market,
    *,
    config: ResearchPacketResolutionOutcomeWatchlistV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionOutcomeWatchlistV2Row:
    seconds_until_close = _seconds_between(generated_at, market.close_time)
    official_ratio = _ratio(
        market.ready_official_outcome_source_count,
        market.official_outcome_source_count,
    )
    reason_codes = _row_reason_codes(
        market,
        official_ratio=official_ratio,
        seconds_until_close=seconds_until_close,
        config=config,
    )
    return ResearchPacketResolutionOutcomeWatchlistV2Row(
        packet_id=market.packet_id,
        market_id=market.market_id,
        event_slug=market.event_slug,
        close_time=market.close_time,
        seconds_until_close=seconds_until_close,
        official_outcome_source_count=market.official_outcome_source_count,
        ready_official_outcome_source_count=market.ready_official_outcome_source_count,
        official_outcome_source_readiness_ratio=official_ratio,
        ambiguity_score=market.ambiguity_score,
        unresolved_contradiction_count=market.unresolved_contradiction_count,
        settlement_lag_seconds=market.settlement_lag_seconds,
        evidence_completeness_ratio=market.evidence_completeness_ratio,
        phase1_status=_status_from_reason_codes(reason_codes),
        phase1_priority_score=_priority_score(
            market,
            official_ratio=official_ratio,
            seconds_until_close=seconds_until_close,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    market: ResearchPacketResolutionOutcomeWatchlistV2Market,
    *,
    official_ratio: Decimal,
    seconds_until_close: Decimal,
    config: ResearchPacketResolutionOutcomeWatchlistV2Config,
) -> tuple[str, ...]:
    official_reason: str
    if (
        market.official_outcome_source_count == ZERO
        or market.ready_official_outcome_source_count == ZERO
    ):
        official_reason = OFFICIAL_ABSENT_REASON
    elif official_ratio < config.min_official_outcome_source_readiness_ratio:
        official_reason = OFFICIAL_PARTIAL_REASON
    else:
        official_reason = OFFICIAL_READY_REASON

    if market.ambiguity_score >= config.blocked_ambiguity_score:
        ambiguity_reason = AMBIGUITY_BLOCKED_REASON
    elif market.ambiguity_score > config.watch_ambiguity_score:
        ambiguity_reason = AMBIGUITY_WATCH_REASON
    else:
        ambiguity_reason = AMBIGUITY_CLEAR_REASON

    if market.unresolved_contradiction_count >= config.blocked_contradiction_count:
        contradiction_reason = CONTRADICTIONS_BLOCKING_REASON
    elif market.unresolved_contradiction_count > ZERO:
        contradiction_reason = CONTRADICTIONS_PRESENT_REASON
    else:
        contradiction_reason = CONTRADICTIONS_ABSENT_REASON

    if market.settlement_lag_seconds >= config.blocked_settlement_lag_seconds:
        settlement_reason = SETTLEMENT_BLOCKED_REASON
    elif market.settlement_lag_seconds > config.watch_settlement_lag_seconds:
        settlement_reason = SETTLEMENT_WATCH_REASON
    else:
        settlement_reason = SETTLEMENT_CLEAR_REASON

    if market.evidence_completeness_ratio >= config.min_evidence_completeness_ratio:
        evidence_reason = EVIDENCE_COMPLETE_REASON
    elif market.evidence_completeness_ratio == ZERO:
        evidence_reason = EVIDENCE_ABSENT_REASON
    else:
        evidence_reason = EVIDENCE_INCOMPLETE_REASON

    if seconds_until_close <= ZERO:
        close_reason = CLOSE_ELAPSED_REASON
    elif seconds_until_close <= config.close_watch_window_seconds:
        close_reason = CLOSE_NEAR_REASON
    else:
        close_reason = CLOSE_CLEAR_REASON

    return (
        official_reason,
        ambiguity_reason,
        contradiction_reason,
        settlement_reason,
        evidence_reason,
        close_reason,
    )


def _priority_score(
    market: ResearchPacketResolutionOutcomeWatchlistV2Market,
    *,
    official_ratio: Decimal,
    seconds_until_close: Decimal,
    config: ResearchPacketResolutionOutcomeWatchlistV2Config,
) -> Decimal:
    official_gap = ONE - official_ratio
    contradiction_pressure = _bounded_ratio(
        market.unresolved_contradiction_count,
        config.blocked_contradiction_count,
    )
    settlement_pressure = _bounded_ratio(
        market.settlement_lag_seconds,
        config.blocked_settlement_lag_seconds,
    )
    evidence_gap = ONE - market.evidence_completeness_ratio
    if seconds_until_close <= ZERO:
        close_pressure = ONE
    elif seconds_until_close >= config.close_watch_window_seconds:
        close_pressure = ZERO
    else:
        close_pressure = ONE - _bounded_ratio(
            seconds_until_close,
            config.close_watch_window_seconds,
        )
    score = (
        (official_gap * Decimal("20"))
        + (market.ambiguity_score * Decimal("20"))
        + (contradiction_pressure * Decimal("20"))
        + (settlement_pressure * Decimal("10"))
        + (evidence_gap * Decimal("20"))
        + (close_pressure * Decimal("10"))
    )
    return _normalize_nonnegative_decimal("phase1_priority_score", score)


def _normalize_markets(
    markets: Iterable[ResearchPacketResolutionOutcomeWatchlistV2Market],
) -> tuple[ResearchPacketResolutionOutcomeWatchlistV2Market, ...]:
    if isinstance(markets, (str, bytes, Mapping)):
        raise ValueError("markets must be an iterable of market rows")
    rows = tuple(markets)
    seen_packet_ids: set[str] = set()
    seen_market_ids: set[str] = set()
    for row in rows:
        if type(row) is not ResearchPacketResolutionOutcomeWatchlistV2Market:
            raise ValueError(
                "markets must contain ResearchPacketResolutionOutcomeWatchlistV2Market",
            )
        _require_hard_flags("market", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("packet_id values must be unique")
        if row.market_id in seen_market_ids:
            raise ValueError("market_id values must be unique")
        seen_packet_ids.add(row.packet_id)
        seen_market_ids.add(row.market_id)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[ResearchPacketResolutionOutcomeWatchlistV2Row, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    seen_packet_ids: set[str] = set()
    seen_market_ids: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketResolutionOutcomeWatchlistV2Row:
            raise ValueError(
                "rows must contain ResearchPacketResolutionOutcomeWatchlistV2Row",
            )
        _require_hard_flags("row", row)
        if row.packet_id in seen_packet_ids:
            raise ValueError("row packet_id values must be unique")
        if row.market_id in seen_market_ids:
            raise ValueError("row market_id values must be unique")
        seen_packet_ids.add(row.packet_id)
        seen_market_ids.add(row.market_id)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sorting")
    return normalized


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("reason_code_counts must be a tuple or list")
    normalized = tuple(rows)
    seen_reason_codes: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    if normalized != tuple(sorted(normalized, key=lambda row: row.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sorting")
    return normalized


def _row_sort_key(
    row: ResearchPacketResolutionOutcomeWatchlistV2Row,
) -> tuple[int, Decimal, datetime, str, str]:
    return (
        _STATUS_SORT_RANK[row.phase1_status],
        -row.phase1_priority_score,
        row.close_time,
        row.packet_id,
        row.market_id,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    severity = max(_STATUS_SEVERITY[_REASON_STATUS[reason]] for reason in reason_codes)
    if severity == _STATUS_SEVERITY[STATUS_BLOCKED]:
        return STATUS_BLOCKED
    if severity == _STATUS_SEVERITY[STATUS_WATCH]:
        return STATUS_WATCH
    return STATUS_READY


def _report_status(
    rows: tuple[ResearchPacketResolutionOutcomeWatchlistV2Row, ...],
) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.phase1_status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.phase1_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_READY


def _recommended_next_step(status: str) -> str:
    if status == STATUS_READY:
        return "continue_phase1_resolution_outcome_monitoring"
    if status == STATUS_WATCH:
        return "refresh_phase1_resolution_outcome_sources"
    if status == STATUS_BLOCKED:
        return "escalate_phase1_resolution_outcome_review"
    raise ValueError("status must be ready, watch, or blocked")


def _report_reason_codes(
    rows: tuple[ResearchPacketResolutionOutcomeWatchlistV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_INPUT_REASON,)
    risk_reasons = {
        reason
        for row in rows
        for reason in row.reason_codes
        if reason in _RISK_REASON_CODES
    }
    if not risk_reasons:
        return (CLEAR_REPORT_REASON,)
    return tuple(sorted(risk_reasons, key=_reason_sort_key))


def _reason_code_counts(
    rows: tuple[ResearchPacketResolutionOutcomeWatchlistV2Row, ...],
    market_count: Decimal,
) -> tuple[ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount(
                reason_code=EMPTY_INPUT_REASON,
                market_count=ONE,
                market_ratio=ONE,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount(
            reason_code=reason_code,
            market_count=count,
            market_ratio=_ratio(count, market_count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _status_count(
    rows: tuple[ResearchPacketResolutionOutcomeWatchlistV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.phase1_status == status))


def _attention_count(
    rows: tuple[ResearchPacketResolutionOutcomeWatchlistV2Row, ...],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.phase1_status != STATUS_READY))


def _reason_market_count(
    rows: tuple[ResearchPacketResolutionOutcomeWatchlistV2Row, ...],
    reason_codes: tuple[str, ...],
) -> Decimal:
    reason_set = frozenset(reason_codes)
    return _count_decimal(
        sum(1 for row in rows if any(reason in reason_set for reason in row.reason_codes)),
    )


def _validate_row_consistency(
    row: ResearchPacketResolutionOutcomeWatchlistV2Row,
) -> None:
    if row.phase1_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("phase1_status must match reason_codes")
    if (
        row.official_outcome_source_count == ZERO
        and row.official_outcome_source_readiness_ratio != ZERO
    ):
        raise ValueError(
            "official_outcome_source_readiness_ratio must be zero when no official source exists",
        )
    if row.official_outcome_source_count > ZERO:
        expected_ratio = _ratio(
            row.ready_official_outcome_source_count,
            row.official_outcome_source_count,
        )
        if row.official_outcome_source_readiness_ratio != expected_ratio:
            raise ValueError("official_outcome_source_readiness_ratio must match counts")


def _validate_report_consistency(
    report: ResearchPacketResolutionOutcomeWatchlistV2Report,
) -> None:
    market_count = _count_decimal(len(report.rows))
    expected_values = {
        "market_count": market_count,
        "ready_market_count": _status_count(report.rows, STATUS_READY),
        "watch_market_count": _status_count(report.rows, STATUS_WATCH),
        "blocked_market_count": _status_count(report.rows, STATUS_BLOCKED),
        "attention_market_count": _attention_count(report.rows),
        "official_source_gap_market_count": _reason_market_count(
            report.rows,
            (OFFICIAL_PARTIAL_REASON, OFFICIAL_ABSENT_REASON),
        ),
        "ambiguity_watch_market_count": _reason_market_count(
            report.rows,
            (AMBIGUITY_WATCH_REASON, AMBIGUITY_BLOCKED_REASON),
        ),
        "contradiction_market_count": _reason_market_count(
            report.rows,
            (CONTRADICTIONS_PRESENT_REASON, CONTRADICTIONS_BLOCKING_REASON),
        ),
        "settlement_lag_market_count": _reason_market_count(
            report.rows,
            (SETTLEMENT_WATCH_REASON, SETTLEMENT_BLOCKED_REASON),
        ),
        "evidence_gap_market_count": _reason_market_count(
            report.rows,
            (EVIDENCE_INCOMPLETE_REASON, EVIDENCE_ABSENT_REASON),
        ),
        "near_close_market_count": _reason_market_count(
            report.rows,
            (CLOSE_NEAR_REASON, CLOSE_ELAPSED_REASON),
        ),
        "max_priority_score": max(
            (row.phase1_priority_score for row in report.rows),
            default=ZERO,
        ),
        "average_priority_score": _average_decimal(
            row.phase1_priority_score for row in report.rows
        ),
    }
    for field_name, expected_value in expected_values.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.recommended_next_step != _recommended_next_step(report.report_status):
        raise ValueError("recommended_next_step must match report_status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.market_count):
        raise ValueError("reason_code_counts must match rows")


def _require_exact_dataclass_type(value: object, expected_type: type, field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    _reject_unsafe_public_text(field_name, value, value_label="value")


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_reason_codes: frozenset[str],
) -> None:
    _require_public_string(field_name, value)
    if value not in allowed_reason_codes:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_choice(field_name: str, value: object, allowed_values: tuple[str, ...]) -> None:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {', '.join(allowed_values)}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    try:
        return decimal_value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must quantize to six decimals") from exc


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-count Decimal")
    return decimal_value


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    return _normalize_decimal(
        "seconds_until_close",
        Decimal(str((end - start).total_seconds())),
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _normalize_ratio_decimal("ratio", numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    value = numerator / denominator
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _normalize_ratio_decimal("bounded_ratio", value)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANT)


def _average_decimal(values: Iterable[Decimal]) -> Decimal:
    normalized_values = tuple(values)
    if not normalized_values:
        return ZERO
    return _normalize_nonnegative_decimal(
        "average_priority_score",
        sum(normalized_values, ZERO) / _count_decimal(len(normalized_values)),
    )


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: frozenset[str],
) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a tuple or list")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code, allowed_reason_codes)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    return reason_codes


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    return (_REASON_SORT_RANK.get(reason_code, len(_REASON_SORT_RANK)), reason_code)


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        flag_value = getattr(value, flag_name)
        if type(flag_value) is not bool:
            raise ValueError(f"{label} {flag_name} must be a bool")
        if flag_value is not True:
            raise ValueError(f"{flag_name} must be True")


def _reject_unsafe_public_payload(field_name: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{field_name} contains non-string public field")
            _reject_unsafe_public_text(key, key, value_label="field")
            _reject_unsafe_public_payload(f"{field_name}.{key}", item)
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{field_name}[{index}]", item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(field_name, value, value_label="value")


def _reject_unsafe_public_text(
    field_name: str,
    value: str,
    *,
    value_label: str,
) -> None:
    lowered = value.lower()
    for token in _UNSAFE_PUBLIC_TOKENS:
        if token in lowered:
            if value_label == "field":
                raise ValueError(f"{field_name} has unsafe public field")
            raise ValueError(f"{field_name} has unsafe public value")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    _reject_unsafe_public_payload(field_name, value)
    if is_dataclass(value) and not isinstance(value, type):
        _require_hard_flags(field_name, value)
        if hasattr(value, "derived_validation_digest"):
            _set_or_validate_digest(value, field_name)
        for field in fields(value):
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is Decimal:
        _normalize_decimal(field_name, value)
        return
    if type(value) is datetime:
        normalized = _as_utc(field_name, value)
        if normalized.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) is str or type(value) is bool or value is None:
        return
    if type(value) is int:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    if isinstance(value, float):
        raise ValueError(f"{field_name} must not be a float")
    raise ValueError(f"{field_name} must remain constructor-normalized")


def _set_or_validate_digest(value: object, label: str) -> None:
    digest = getattr(value, "derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _digest_for_dataclass(value)
    if digest == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    if digest != expected:
        raise ValueError(f"derived_validation_digest must match {label}")


def _digest_for_dataclass(value: object) -> str:
    payload: dict[str, Any] = {}
    for field in fields(value):
        if field.name == "derived_validation_digest":
            continue
        payload[field.name] = _json_ready(getattr(value, field.name))
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is str or type(value) is bool or value is None:
        return value
    raise ValueError("value must be json-ready")


def _report_from_payload(
    payload: Mapping[str, Any],
) -> ResearchPacketResolutionOutcomeWatchlistV2Report:
    _require_payload_keys(
        "payload",
        payload,
        (
            "generated_at",
            "config_version",
            "report_status",
            "recommended_next_step",
            "market_count",
            "ready_market_count",
            "watch_market_count",
            "blocked_market_count",
            "attention_market_count",
            "official_source_gap_market_count",
            "ambiguity_watch_market_count",
            "contradiction_market_count",
            "settlement_lag_market_count",
            "evidence_gap_market_count",
            "near_close_market_count",
            "max_priority_score",
            "average_priority_score",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    return ResearchPacketResolutionOutcomeWatchlistV2Report(
        generated_at=_datetime_from_payload("generated_at", payload["generated_at"]),
        config_version=_string_from_payload("config_version", payload["config_version"]),
        report_status=_string_from_payload("report_status", payload["report_status"]),
        recommended_next_step=_string_from_payload(
            "recommended_next_step",
            payload["recommended_next_step"],
        ),
        market_count=_decimal_from_payload("market_count", payload["market_count"]),
        ready_market_count=_decimal_from_payload(
            "ready_market_count",
            payload["ready_market_count"],
        ),
        watch_market_count=_decimal_from_payload(
            "watch_market_count",
            payload["watch_market_count"],
        ),
        blocked_market_count=_decimal_from_payload(
            "blocked_market_count",
            payload["blocked_market_count"],
        ),
        attention_market_count=_decimal_from_payload(
            "attention_market_count",
            payload["attention_market_count"],
        ),
        official_source_gap_market_count=_decimal_from_payload(
            "official_source_gap_market_count",
            payload["official_source_gap_market_count"],
        ),
        ambiguity_watch_market_count=_decimal_from_payload(
            "ambiguity_watch_market_count",
            payload["ambiguity_watch_market_count"],
        ),
        contradiction_market_count=_decimal_from_payload(
            "contradiction_market_count",
            payload["contradiction_market_count"],
        ),
        settlement_lag_market_count=_decimal_from_payload(
            "settlement_lag_market_count",
            payload["settlement_lag_market_count"],
        ),
        evidence_gap_market_count=_decimal_from_payload(
            "evidence_gap_market_count",
            payload["evidence_gap_market_count"],
        ),
        near_close_market_count=_decimal_from_payload(
            "near_close_market_count",
            payload["near_close_market_count"],
        ),
        max_priority_score=_decimal_from_payload(
            "max_priority_score",
            payload["max_priority_score"],
        ),
        average_priority_score=_decimal_from_payload(
            "average_priority_score",
            payload["average_priority_score"],
        ),
        rows=tuple(_row_from_payload(row) for row in _sequence_payload("rows", payload["rows"])),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(row)
            for row in _sequence_payload(
                "reason_code_counts",
                payload["reason_code_counts"],
            )
        ),
        reason_codes=tuple(
            _string_from_payload(f"reason_codes[{index}]", item)
            for index, item in enumerate(
                _sequence_payload("reason_codes", payload["reason_codes"]),
            )
        ),
        derived_validation_digest=_string_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _row_from_payload(
    payload: object,
) -> ResearchPacketResolutionOutcomeWatchlistV2Row:
    if not isinstance(payload, Mapping):
        raise ValueError("row payload must be a mapping")
    _require_payload_keys(
        "row payload",
        payload,
        (
            "packet_id",
            "market_id",
            "event_slug",
            "close_time",
            "seconds_until_close",
            "official_outcome_source_count",
            "ready_official_outcome_source_count",
            "official_outcome_source_readiness_ratio",
            "ambiguity_score",
            "unresolved_contradiction_count",
            "settlement_lag_seconds",
            "evidence_completeness_ratio",
            "phase1_status",
            "phase1_priority_score",
            "reason_codes",
            "derived_validation_digest",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    return ResearchPacketResolutionOutcomeWatchlistV2Row(
        packet_id=_string_from_payload("packet_id", payload["packet_id"]),
        market_id=_string_from_payload("market_id", payload["market_id"]),
        event_slug=_string_from_payload("event_slug", payload["event_slug"]),
        close_time=_datetime_from_payload("close_time", payload["close_time"]),
        seconds_until_close=_decimal_from_payload(
            "seconds_until_close",
            payload["seconds_until_close"],
        ),
        official_outcome_source_count=_decimal_from_payload(
            "official_outcome_source_count",
            payload["official_outcome_source_count"],
        ),
        ready_official_outcome_source_count=_decimal_from_payload(
            "ready_official_outcome_source_count",
            payload["ready_official_outcome_source_count"],
        ),
        official_outcome_source_readiness_ratio=_decimal_from_payload(
            "official_outcome_source_readiness_ratio",
            payload["official_outcome_source_readiness_ratio"],
        ),
        ambiguity_score=_decimal_from_payload("ambiguity_score", payload["ambiguity_score"]),
        unresolved_contradiction_count=_decimal_from_payload(
            "unresolved_contradiction_count",
            payload["unresolved_contradiction_count"],
        ),
        settlement_lag_seconds=_decimal_from_payload(
            "settlement_lag_seconds",
            payload["settlement_lag_seconds"],
        ),
        evidence_completeness_ratio=_decimal_from_payload(
            "evidence_completeness_ratio",
            payload["evidence_completeness_ratio"],
        ),
        phase1_status=_string_from_payload("phase1_status", payload["phase1_status"]),
        phase1_priority_score=_decimal_from_payload(
            "phase1_priority_score",
            payload["phase1_priority_score"],
        ),
        reason_codes=tuple(
            _string_from_payload(f"reason_codes[{index}]", item)
            for index, item in enumerate(
                _sequence_payload("reason_codes", payload["reason_codes"]),
            )
        ),
        derived_validation_digest=_string_from_payload(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _reason_code_count_from_payload(
    payload: object,
) -> ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount:
    if not isinstance(payload, Mapping):
        raise ValueError("reason_code_count payload must be a mapping")
    _require_payload_keys(
        "reason_code_count payload",
        payload,
        (
            "reason_code",
            "market_count",
            "market_ratio",
            "paper_only",
            "report_only",
            "readonly",
        ),
    )
    return ResearchPacketResolutionOutcomeWatchlistV2ReasonCodeCount(
        reason_code=_string_from_payload("reason_code", payload["reason_code"]),
        market_count=_decimal_from_payload("market_count", payload["market_count"]),
        market_ratio=_decimal_from_payload("market_ratio", payload["market_ratio"]),
        paper_only=_bool_from_payload("paper_only", payload["paper_only"]),
        report_only=_bool_from_payload("report_only", payload["report_only"]),
        readonly=_bool_from_payload("readonly", payload["readonly"]),
    )


def _require_payload_keys(
    label: str,
    payload: Mapping[str, Any],
    expected_keys: tuple[str, ...],
) -> None:
    actual_keys = tuple(payload.keys())
    if set(actual_keys) != set(expected_keys):
        raise ValueError(f"{label} fields must match the public schema")
    if actual_keys != expected_keys:
        raise ValueError(f"{label} fields must use deterministic ordering")


def _sequence_payload(field_name: str, value: object) -> tuple[Any, ...]:
    if type(value) not in (tuple, list):
        raise ValueError(f"{field_name} must be a list")
    return tuple(value)


def _string_from_payload(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    return value


def _bool_from_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    return _normalize_decimal(field_name, decimal_value)


def _datetime_from_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)
