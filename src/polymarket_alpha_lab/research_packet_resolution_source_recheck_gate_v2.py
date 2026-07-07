"""Pure Phase 1 recheck gate for resolution source packets."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_RECHECK_GATE_V2_CONFIG_VERSION = (
    "research-packet-resolution-source-recheck-gate-v2-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)

PASS_REASON = "resolution_source_recheck_gate_pass"
WATCH_REASON = "resolution_source_recheck_gate_watch"
BLOCKED_REASON = "resolution_source_recheck_gate_blocked"
MISSING_OFFICIAL_REASON = "missing_official_resolution_source"
STALE_OFFICIAL_REASON = "official_resolution_source_stale"
HIGH_CONTRADICTION_REASON = "high_resolution_source_contradiction"
MEDIUM_CONTRADICTION_REASON = "medium_resolution_source_contradiction"
AMBIGUOUS_RULE_REASON = "ambiguous_resolution_rule"
MARKET_CLOSE_REASON = "market_close_recheck_window"
INCOMPLETE_EVIDENCE_REASON = "incomplete_evidence_chain"
RISK_WATCH_REASON = "recheck_risk_score_watch"
RISK_BLOCKED_REASON = "recheck_risk_score_blocked"

STATUS_REASON_CODES = (PASS_REASON, WATCH_REASON, BLOCKED_REASON)
DETAIL_REASON_CODES = (
    MISSING_OFFICIAL_REASON,
    STALE_OFFICIAL_REASON,
    HIGH_CONTRADICTION_REASON,
    MEDIUM_CONTRADICTION_REASON,
    AMBIGUOUS_RULE_REASON,
    MARKET_CLOSE_REASON,
    INCOMPLETE_EVIDENCE_REASON,
    RISK_WATCH_REASON,
    RISK_BLOCKED_REASON,
)
REASON_CODES = (*STATUS_REASON_CODES, *DETAIL_REASON_CODES)
HARD_BLOCK_REASONS = frozenset(
    (
        MISSING_OFFICIAL_REASON,
        STALE_OFFICIAL_REASON,
        HIGH_CONTRADICTION_REASON,
        MARKET_CLOSE_REASON,
        RISK_BLOCKED_REASON,
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_RECHECK_GATE_V2_CONFIG_VERSION",
    "ResearchPacketResolutionSourceRecheckGateV2Config",
    "ResearchPacketResolutionSourceRecheckGateV2Input",
    "ResearchPacketResolutionSourceRecheckGateV2Decision",
    "evaluate_research_packet_resolution_source_recheck_gate_v2",
    "research_packet_resolution_source_recheck_gate_v2_payload",
)


@dataclass(frozen=True)
class ResearchPacketResolutionSourceRecheckGateV2Config:
    config_version: str = (
        DEFAULT_RESEARCH_PACKET_RESOLUTION_SOURCE_RECHECK_GATE_V2_CONFIG_VERSION
    )
    official_stale_after_seconds: Decimal = Decimal("86400.000000")
    market_close_watch_window_seconds: Decimal = Decimal("86400.000000")
    market_close_block_window_seconds: Decimal = Decimal("3600.000000")
    watch_score_threshold: Decimal = Decimal("0.250000")
    blocked_score_threshold: Decimal = Decimal("0.650000")
    contradiction_watch_threshold: Decimal = Decimal("0.300000")
    contradiction_block_threshold: Decimal = Decimal("0.800000")
    rule_ambiguity_watch_threshold: Decimal = Decimal("0.500000")
    evidence_chain_min_completeness: Decimal = Decimal("0.800000")
    official_age_weight: Decimal = Decimal("0.250000")
    contradiction_weight: Decimal = Decimal("0.300000")
    rule_ambiguity_weight: Decimal = Decimal("0.200000")
    market_close_weight: Decimal = Decimal("0.150000")
    evidence_chain_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        for field_name in (
            "official_stale_after_seconds",
            "market_close_watch_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _positive_seconds(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "market_close_block_window_seconds",
            _nonnegative_seconds(
                "market_close_block_window_seconds",
                self.market_close_block_window_seconds,
            ),
        )
        for field_name in (
            "watch_score_threshold",
            "blocked_score_threshold",
            "contradiction_watch_threshold",
            "contradiction_block_threshold",
            "rule_ambiguity_watch_threshold",
            "evidence_chain_min_completeness",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "official_age_weight",
            "contradiction_weight",
            "rule_ambiguity_weight",
            "market_close_weight",
            "evidence_chain_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        reject_unsafe_surface_fields(
            "ResearchPacketResolutionSourceRecheckGateV2Config",
            self,
        )
        require_paper_only_flags(
            "ResearchPacketResolutionSourceRecheckGateV2Config",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketResolutionSourceRecheckGateV2Input:
    packet_id: str
    market_id: str
    official_source_checked_at: datetime | None
    market_closes_at: datetime
    contradiction_severity_score: Decimal
    rule_ambiguity_score: Decimal
    evidence_chain_completeness_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("packet_id", self.packet_id)
        _require_text("market_id", self.market_id)
        object.__setattr__(
            self,
            "official_source_checked_at",
            _optional_utc(
                "official_source_checked_at",
                self.official_source_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "market_closes_at",
            _as_utc("market_closes_at", self.market_closes_at),
        )
        for field_name in (
            "contradiction_severity_score",
            "rule_ambiguity_score",
            "evidence_chain_completeness_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        reject_unsafe_surface_fields(
            "ResearchPacketResolutionSourceRecheckGateV2Input",
            self,
        )
        require_paper_only_flags(
            "ResearchPacketResolutionSourceRecheckGateV2Input",
            self,
        )


@dataclass(frozen=True)
class ResearchPacketResolutionSourceRecheckGateV2Decision:
    packet_id: str
    market_id: str
    generated_at: datetime
    official_source_checked_at: datetime | None
    market_closes_at: datetime
    gate_status: str
    recheck_required: bool
    official_source_age_seconds: Decimal | None
    seconds_until_market_close: Decimal
    official_source_age_score: Decimal
    contradiction_severity_score: Decimal
    rule_ambiguity_score: Decimal
    market_close_proximity_score: Decimal
    evidence_chain_missing_score: Decimal
    risk_score: Decimal
    reason_codes: tuple[str, ...]
    decision_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("packet_id", self.packet_id)
        _require_text("market_id", self.market_id)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "official_source_checked_at",
            _optional_utc(
                "official_source_checked_at",
                self.official_source_checked_at,
            ),
        )
        object.__setattr__(
            self,
            "market_closes_at",
            _as_utc("market_closes_at", self.market_closes_at),
        )
        _require_status("gate_status", self.gate_status)
        _require_bool("recheck_required", self.recheck_required)
        object.__setattr__(
            self,
            "official_source_age_seconds",
            _optional_nonnegative_seconds(
                "official_source_age_seconds",
                self.official_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "seconds_until_market_close",
            _nonnegative_seconds(
                "seconds_until_market_close",
                self.seconds_until_market_close,
            ),
        )
        for field_name in (
            "official_source_age_score",
            "contradiction_severity_score",
            "rule_ambiguity_score",
            "market_close_proximity_score",
            "evidence_chain_missing_score",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_digest("decision_digest", self.decision_digest)
        _validate_decision(self)
        reject_unsafe_surface_fields(
            "ResearchPacketResolutionSourceRecheckGateV2Decision",
            self,
        )
        require_paper_only_flags(
            "ResearchPacketResolutionSourceRecheckGateV2Decision",
            self,
        )


def evaluate_research_packet_resolution_source_recheck_gate_v2(
    row: object,
    *,
    config: ResearchPacketResolutionSourceRecheckGateV2Config,
    generated_at: datetime,
) -> ResearchPacketResolutionSourceRecheckGateV2Decision:
    if type(config) is not ResearchPacketResolutionSourceRecheckGateV2Config:
        raise ValueError(
            "config must be a ResearchPacketResolutionSourceRecheckGateV2Config",
        )
    if type(row) is not ResearchPacketResolutionSourceRecheckGateV2Input:
        raise ValueError("row must be a ResearchPacketResolutionSourceRecheckGateV2Input")
    require_paper_only_flags(
        "ResearchPacketResolutionSourceRecheckGateV2Config",
        config,
    )
    require_paper_only_flags("ResearchPacketResolutionSourceRecheckGateV2Input", row)

    generated_at_utc = _as_utc("generated_at", generated_at)
    official_age_seconds = _official_age_seconds(row, generated_at_utc)
    seconds_until_market_close = _seconds_until_market_close(
        row.market_closes_at,
        generated_at_utc,
    )
    official_source_age_score = _official_source_age_score(
        official_age_seconds,
        config.official_stale_after_seconds,
    )
    market_close_proximity_score = _market_close_proximity_score(
        seconds_until_market_close,
        config.market_close_watch_window_seconds,
    )
    evidence_chain_missing_score = _quantize(
        ONE - row.evidence_chain_completeness_ratio,
    )
    risk_score = _risk_score(
        config,
        official_source_age_score=official_source_age_score,
        contradiction_severity_score=row.contradiction_severity_score,
        rule_ambiguity_score=row.rule_ambiguity_score,
        market_close_proximity_score=market_close_proximity_score,
        evidence_chain_missing_score=evidence_chain_missing_score,
    )
    reason_codes = _decision_reason_codes(
        row,
        config=config,
        official_age_seconds=official_age_seconds,
        seconds_until_market_close=seconds_until_market_close,
        risk_score=risk_score,
    )
    gate_status = _status_from_reason_codes(reason_codes)
    digest = _decision_digest(
        row,
        config=config,
        generated_at=generated_at_utc,
        gate_status=gate_status,
        official_source_age_seconds=official_age_seconds,
        seconds_until_market_close=seconds_until_market_close,
        official_source_age_score=official_source_age_score,
        market_close_proximity_score=market_close_proximity_score,
        evidence_chain_missing_score=evidence_chain_missing_score,
        risk_score=risk_score,
        reason_codes=reason_codes,
    )
    return ResearchPacketResolutionSourceRecheckGateV2Decision(
        packet_id=row.packet_id,
        market_id=row.market_id,
        generated_at=generated_at_utc,
        official_source_checked_at=row.official_source_checked_at,
        market_closes_at=row.market_closes_at,
        gate_status=gate_status,
        recheck_required=gate_status != PASS_STATUS,
        official_source_age_seconds=official_age_seconds,
        seconds_until_market_close=seconds_until_market_close,
        official_source_age_score=official_source_age_score,
        contradiction_severity_score=row.contradiction_severity_score,
        rule_ambiguity_score=row.rule_ambiguity_score,
        market_close_proximity_score=market_close_proximity_score,
        evidence_chain_missing_score=evidence_chain_missing_score,
        risk_score=risk_score,
        reason_codes=reason_codes,
        decision_digest=digest,
    )


def research_packet_resolution_source_recheck_gate_v2_payload(
    decision: ResearchPacketResolutionSourceRecheckGateV2Decision,
) -> dict[str, Any]:
    if type(decision) is not ResearchPacketResolutionSourceRecheckGateV2Decision:
        raise ValueError(
            "decision must be a ResearchPacketResolutionSourceRecheckGateV2Decision",
        )
    require_paper_only_flags(
        "ResearchPacketResolutionSourceRecheckGateV2Decision",
        decision,
    )
    reject_unsafe_surface_fields(
        "ResearchPacketResolutionSourceRecheckGateV2Decision",
        decision,
    )
    payload = json_ready_no_floats(decision)
    if type(payload) is not dict:
        raise ValueError("decision payload must be a JSON object")
    reject_unsafe_surface_fields(
        "research packet resolution source recheck gate v2 payload",
        payload,
    )
    return payload


def _official_age_seconds(
    row: ResearchPacketResolutionSourceRecheckGateV2Input,
    generated_at: datetime,
) -> Decimal | None:
    if row.official_source_checked_at is None:
        return None
    if row.official_source_checked_at > generated_at:
        raise ValueError("official_source_checked_at must not be after generated_at")
    return _duration_seconds(row.official_source_checked_at, generated_at)


def _seconds_until_market_close(market_closes_at: datetime, generated_at: datetime) -> Decimal:
    if market_closes_at <= generated_at:
        return ZERO
    return _duration_seconds(generated_at, market_closes_at)


def _official_source_age_score(
    official_age_seconds: Decimal | None,
    stale_after_seconds: Decimal,
) -> Decimal:
    if official_age_seconds is None:
        return ONE
    return _bounded_ratio(official_age_seconds, stale_after_seconds)


def _market_close_proximity_score(
    seconds_until_market_close: Decimal,
    watch_window_seconds: Decimal,
) -> Decimal:
    if seconds_until_market_close >= watch_window_seconds:
        return ZERO
    return _bounded_ratio(
        watch_window_seconds - seconds_until_market_close,
        watch_window_seconds,
    )


def _risk_score(
    config: ResearchPacketResolutionSourceRecheckGateV2Config,
    *,
    official_source_age_score: Decimal,
    contradiction_severity_score: Decimal,
    rule_ambiguity_score: Decimal,
    market_close_proximity_score: Decimal,
    evidence_chain_missing_score: Decimal,
) -> Decimal:
    weighted_sum = (
        official_source_age_score * config.official_age_weight
        + contradiction_severity_score * config.contradiction_weight
        + rule_ambiguity_score * config.rule_ambiguity_weight
        + market_close_proximity_score * config.market_close_weight
        + evidence_chain_missing_score * config.evidence_chain_weight
    )
    total_weight = _total_weight(config)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(weighted_sum / total_weight)


def _decision_reason_codes(
    row: ResearchPacketResolutionSourceRecheckGateV2Input,
    *,
    config: ResearchPacketResolutionSourceRecheckGateV2Config,
    official_age_seconds: Decimal | None,
    seconds_until_market_close: Decimal,
    risk_score: Decimal,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    if row.official_source_checked_at is None:
        detail_reasons.append(MISSING_OFFICIAL_REASON)
    elif official_age_seconds is not None and official_age_seconds >= (
        config.official_stale_after_seconds
    ):
        detail_reasons.append(STALE_OFFICIAL_REASON)

    if row.contradiction_severity_score >= config.contradiction_block_threshold:
        detail_reasons.append(HIGH_CONTRADICTION_REASON)
    elif row.contradiction_severity_score >= config.contradiction_watch_threshold:
        detail_reasons.append(MEDIUM_CONTRADICTION_REASON)

    if row.rule_ambiguity_score >= config.rule_ambiguity_watch_threshold:
        detail_reasons.append(AMBIGUOUS_RULE_REASON)
    if seconds_until_market_close <= config.market_close_block_window_seconds:
        detail_reasons.append(MARKET_CLOSE_REASON)
    if row.evidence_chain_completeness_ratio < config.evidence_chain_min_completeness:
        detail_reasons.append(INCOMPLETE_EVIDENCE_REASON)

    has_hard_block = any(reason in HARD_BLOCK_REASONS for reason in detail_reasons)
    if risk_score >= config.blocked_score_threshold:
        detail_reasons.append(RISK_BLOCKED_REASON)
    elif not has_hard_block and risk_score >= config.watch_score_threshold:
        detail_reasons.append(RISK_WATCH_REASON)

    if not detail_reasons:
        return (PASS_REASON,)
    status = _detail_status(tuple(detail_reasons))
    return (_status_reason(status), *detail_reasons)


def _detail_status(detail_reasons: tuple[str, ...]) -> str:
    if any(reason in HARD_BLOCK_REASONS for reason in detail_reasons):
        return BLOCKED_STATUS
    return WATCH_STATUS


def _status_reason(status: str) -> str:
    if status == BLOCKED_STATUS:
        return BLOCKED_REASON
    if status == WATCH_STATUS:
        return WATCH_REASON
    return PASS_REASON


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == BLOCKED_REASON:
        return BLOCKED_STATUS
    if reason_codes[0] == WATCH_REASON:
        return WATCH_STATUS
    return PASS_STATUS


def _decision_digest(
    row: ResearchPacketResolutionSourceRecheckGateV2Input,
    *,
    config: ResearchPacketResolutionSourceRecheckGateV2Config,
    generated_at: datetime,
    gate_status: str,
    official_source_age_seconds: Decimal | None,
    seconds_until_market_close: Decimal,
    official_source_age_score: Decimal,
    market_close_proximity_score: Decimal,
    evidence_chain_missing_score: Decimal,
    risk_score: Decimal,
    reason_codes: tuple[str, ...],
) -> str:
    parts = (
        f"config_version={config.config_version}",
        f"packet_id={row.packet_id}",
        f"market_id={row.market_id}",
        f"generated_at={_datetime_key(generated_at)}",
        f"official_source_checked_at={_optional_datetime_key(row.official_source_checked_at)}",
        f"market_closes_at={_datetime_key(row.market_closes_at)}",
        f"gate_status={gate_status}",
        f"official_source_age_seconds={_optional_decimal_key(official_source_age_seconds)}",
        f"seconds_until_market_close={seconds_until_market_close}",
        f"official_source_age_score={official_source_age_score}",
        f"contradiction_severity_score={row.contradiction_severity_score}",
        f"rule_ambiguity_score={row.rule_ambiguity_score}",
        f"market_close_proximity_score={market_close_proximity_score}",
        f"evidence_chain_completeness_ratio={row.evidence_chain_completeness_ratio}",
        f"evidence_chain_missing_score={evidence_chain_missing_score}",
        f"risk_score={risk_score}",
        f"reason_codes={','.join(reason_codes)}",
    )
    return sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _duration_seconds(started_at: datetime, finished_at: datetime) -> Decimal:
    start = _as_utc("started_at", started_at)
    finish = _as_utc("finished_at", finished_at)
    delta = finish - start
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    if seconds < ZERO:
        raise ValueError("duration seconds must be nonnegative")
    return _quantize(seconds)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        ratio = _quantize(numerator / denominator)
    if ratio < ZERO:
        return ZERO
    if ratio > ONE:
        return ONE
    return ratio


def _total_weight(config: ResearchPacketResolutionSourceRecheckGateV2Config) -> Decimal:
    return _quantize(
        config.official_age_weight
        + config.contradiction_weight
        + config.rule_ambiguity_weight
        + config.market_close_weight
        + config.evidence_chain_weight,
    )


def _validate_config(config: ResearchPacketResolutionSourceRecheckGateV2Config) -> None:
    if config.market_close_block_window_seconds > config.market_close_watch_window_seconds:
        raise ValueError(
            "market_close_block_window_seconds must be <= market_close_watch_window_seconds",
        )
    if config.watch_score_threshold >= config.blocked_score_threshold:
        raise ValueError("watch_score_threshold must be less than blocked_score_threshold")
    if config.contradiction_watch_threshold >= config.contradiction_block_threshold:
        raise ValueError(
            "contradiction_watch_threshold must be less than contradiction_block_threshold",
        )
    if _total_weight(config) <= ZERO:
        raise ValueError("score weights must include at least one positive Decimal")


def _validate_decision(
    decision: ResearchPacketResolutionSourceRecheckGateV2Decision,
) -> None:
    expected_status = _status_from_reason_codes(decision.reason_codes)
    if decision.gate_status != expected_status:
        raise ValueError("gate_status must match reason_codes")
    if decision.recheck_required is not (decision.gate_status != PASS_STATUS):
        raise ValueError("recheck_required must match gate_status")
    if (decision.official_source_checked_at is None) != (
        decision.official_source_age_seconds is None
    ):
        raise ValueError(
            "official_source_age_seconds must match official_source_checked_at",
        )


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    previous_rank: int | None = None
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        rank = REASON_CODES.index(reason_code)
        if previous_rank is not None and rank <= previous_rank:
            raise ValueError("reason_codes must follow reason code rank")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        previous_rank = rank
        seen.add(reason_code)
    if reason_codes[0] not in STATUS_REASON_CODES:
        raise ValueError("reason_codes must begin with a gate status reason")
    if reason_codes[0] == PASS_REASON and len(reason_codes) != 1:
        raise ValueError("pass reason_codes must stand alone")
    if reason_codes[0] != PASS_REASON and len(reason_codes) == 1:
        raise ValueError("watch or blocked reason_codes require detail reasons")
    return reason_codes


def _require_reason_code(name: str, value: object) -> None:
    _require_text(name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{name} must be a known reason code")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or blocked")


def _require_bool(name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{name} must be a bool")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{name} must be a 64-character hex string")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase hex string")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a canonical nonblank string")


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_utc(name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(name, value)


def _optional_nonnegative_seconds(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _nonnegative_seconds(name, value)


def _positive_seconds(name: str, value: object) -> Decimal:
    seconds = _nonnegative_seconds(name, value)
    if seconds <= ZERO:
        raise ValueError(f"{name} must be positive")
    return seconds


def _nonnegative_seconds(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _ratio_decimal(name: str, value: object) -> Decimal:
    normalized = _decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{name} must be quantizable") from exc


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _datetime_key(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _optional_datetime_key(value: datetime | None) -> str:
    if value is None:
        return "<none>"
    return _datetime_key(value)


def _optional_decimal_key(value: Decimal | None) -> str:
    if value is None:
        return "<none>"
    return str(value)
