"""Pure typed research decision bundle v7 reducer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any


__all__ = (
    "StrategyResearchDecisionBundleV7",
    "StrategyResearchDecisionBundleV7AuditPacketSummary",
    "StrategyResearchDecisionBundleV7Config",
    "StrategyResearchDecisionBundleV7MispricingWindowSummary",
    "StrategyResearchDecisionBundleV7ReadinessSummary",
    "StrategyResearchDecisionBundleV7SizingSummary",
    "StrategyResearchDecisionBundleV7SourceReliabilitySummary",
    "StrategyResearchDecisionBundleV7WatchlistSummary",
    "build_strategy_research_decision_bundle_v7",
    "strategy_research_decision_bundle_v7_payload",
)


DEFAULT_CONFIG_VERSION = "strategy-research-decision-bundle-v7"
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

READINESS_STATUSES = ("ready", "watch", "blocked")
WATCHLIST_STATUSES = (
    "clear",
    "wait_for_price",
    "wait_for_source",
    "wait_for_liquidity",
    "wait_for_resolution_clarity",
    "drop",
)
WINDOW_STATUSES = ("open", "watch", "closed")
MISPRICED_SIDES = ("yes", "no", "none")
RELIABILITY_STATUSES = ("pass", "watch", "blocked")
SIZING_STATUSES = ("pass", "watch", "blocked")
AUDIT_PACKET_STATUSES = ("ready", "watch", "blocked")
AUDIT_RECOMMENDATIONS = ("enter", "watch", "skip")
BUNDLE_STATUSES = ("ready", "watch", "blocked")


@dataclass(frozen=True)
class StrategyResearchDecisionBundleV7Config:
    config_version: str = DEFAULT_CONFIG_VERSION
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        _require_safety_flags("config", self)


@dataclass(frozen=True)
class StrategyResearchDecisionBundleV7ReadinessSummary:
    candidate_id: str
    market_slug: str
    readiness_status: str
    candidate_count: Decimal
    ready_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("readiness_status", self.readiness_status, READINESS_STATUSES)
        for field_name in (
            "candidate_count",
            "ready_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_readiness_summary(self)
        _require_safety_flags("readiness", self)


@dataclass(frozen=True)
class StrategyResearchDecisionBundleV7WatchlistSummary:
    candidate_id: str
    market_slug: str
    watchlist_status: str
    next_review_minutes: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("watchlist_status", self.watchlist_status, WATCHLIST_STATUSES)
        object.__setattr__(
            self,
            "next_review_minutes",
            _normalize_count("next_review_minutes", self.next_review_minutes),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("watchlist", self)


@dataclass(frozen=True)
class StrategyResearchDecisionBundleV7MispricingWindowSummary:
    candidate_id: str
    market_slug: str
    window_status: str
    mispriced_side: str
    probability_gap: Decimal
    abs_probability_gap: Decimal
    cost_adjusted_edge: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("window_status", self.window_status, WINDOW_STATUSES)
        _require_member("mispriced_side", self.mispriced_side, MISPRICED_SIDES)
        object.__setattr__(
            self,
            "probability_gap",
            _normalize_signed_probability("probability_gap", self.probability_gap),
        )
        object.__setattr__(
            self,
            "abs_probability_gap",
            _normalize_probability("abs_probability_gap", self.abs_probability_gap),
        )
        object.__setattr__(
            self,
            "cost_adjusted_edge",
            _normalize_signed_probability("cost_adjusted_edge", self.cost_adjusted_edge),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_mispricing_window_summary(self)
        _require_safety_flags("mispricing_window", self)


@dataclass(frozen=True)
class StrategyResearchDecisionBundleV7SourceReliabilitySummary:
    candidate_id: str
    market_slug: str
    source_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_source_weight: Decimal
    reliability_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        for field_name in ("source_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_source_weight",
            _normalize_probability("average_source_weight", self.average_source_weight),
        )
        _require_member("reliability_status", self.reliability_status, RELIABILITY_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_source_reliability_summary(self)
        _require_safety_flags("source_reliability", self)


@dataclass(frozen=True)
class StrategyResearchDecisionBundleV7SizingSummary:
    candidate_id: str
    market_slug: str
    sizing_status: str
    binding_capacity: Decimal
    paper_notional: Decimal
    resolution_risk: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("sizing_status", self.sizing_status, SIZING_STATUSES)
        for field_name in ("binding_capacity", "paper_notional"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "resolution_risk",
            _normalize_probability("resolution_risk", self.resolution_risk),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_sizing_summary(self)
        _require_safety_flags("sizing", self)


@dataclass(frozen=True)
class StrategyResearchDecisionBundleV7AuditPacketSummary:
    candidate_id: str
    market_slug: str
    packet_status: str
    recommendation: str
    forecast_edge: Decimal
    cost_adjusted_edge: Decimal
    source_quality_score: Decimal
    resolution_risk_score: Decimal
    required_human_review: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("candidate_id", self.candidate_id)
        _require_canonical_string("market_slug", self.market_slug)
        _require_member("packet_status", self.packet_status, AUDIT_PACKET_STATUSES)
        _require_member("recommendation", self.recommendation, AUDIT_RECOMMENDATIONS)
        for field_name in ("forecast_edge", "cost_adjusted_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_quality_score", "resolution_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_bool("required_human_review", self.required_human_review)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_safety_flags("audit_packet", self)


@dataclass(frozen=True)
class StrategyResearchDecisionBundleV7:
    generated_at: datetime
    config_version: str
    candidate_id: str
    market_slug: str
    bundle_status: str
    required_human_review: bool
    readiness: StrategyResearchDecisionBundleV7ReadinessSummary
    watchlist: StrategyResearchDecisionBundleV7WatchlistSummary
    mispricing_window: StrategyResearchDecisionBundleV7MispricingWindowSummary
    source_reliability: StrategyResearchDecisionBundleV7SourceReliabilitySummary
    sizing: StrategyResearchDecisionBundleV7SizingSummary
    audit_packet: StrategyResearchDecisionBundleV7AuditPacketSummary
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        for field_name in ("config_version", "candidate_id", "market_slug"):
            _require_canonical_string(field_name, getattr(self, field_name))
        _require_member("bundle_status", self.bundle_status, BUNDLE_STATUSES)
        _require_bool("required_human_review", self.required_human_review)
        _require_component(
            "readiness",
            self.readiness,
            StrategyResearchDecisionBundleV7ReadinessSummary,
        )
        _require_component(
            "watchlist",
            self.watchlist,
            StrategyResearchDecisionBundleV7WatchlistSummary,
        )
        _require_component(
            "mispricing_window",
            self.mispricing_window,
            StrategyResearchDecisionBundleV7MispricingWindowSummary,
        )
        _require_component(
            "source_reliability",
            self.source_reliability,
            StrategyResearchDecisionBundleV7SourceReliabilitySummary,
        )
        _require_component(
            "sizing",
            self.sizing,
            StrategyResearchDecisionBundleV7SizingSummary,
        )
        _require_component(
            "audit_packet",
            self.audit_packet,
            StrategyResearchDecisionBundleV7AuditPacketSummary,
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_bundle(self)
        _require_safety_flags("bundle", self)


def build_strategy_research_decision_bundle_v7(
    *,
    readiness: StrategyResearchDecisionBundleV7ReadinessSummary,
    watchlist: StrategyResearchDecisionBundleV7WatchlistSummary,
    mispricing_window: StrategyResearchDecisionBundleV7MispricingWindowSummary,
    source_reliability: StrategyResearchDecisionBundleV7SourceReliabilitySummary,
    sizing: StrategyResearchDecisionBundleV7SizingSummary,
    audit_packet: StrategyResearchDecisionBundleV7AuditPacketSummary,
    config: StrategyResearchDecisionBundleV7Config,
    generated_at: datetime,
) -> StrategyResearchDecisionBundleV7:
    _require_component(
        "readiness",
        readiness,
        StrategyResearchDecisionBundleV7ReadinessSummary,
    )
    _require_component(
        "watchlist",
        watchlist,
        StrategyResearchDecisionBundleV7WatchlistSummary,
    )
    _require_component(
        "mispricing_window",
        mispricing_window,
        StrategyResearchDecisionBundleV7MispricingWindowSummary,
    )
    _require_component(
        "source_reliability",
        source_reliability,
        StrategyResearchDecisionBundleV7SourceReliabilitySummary,
    )
    _require_component("sizing", sizing, StrategyResearchDecisionBundleV7SizingSummary)
    _require_component(
        "audit_packet",
        audit_packet,
        StrategyResearchDecisionBundleV7AuditPacketSummary,
    )
    _require_component("config", config, StrategyResearchDecisionBundleV7Config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    status = _bundle_status(
        readiness=readiness,
        watchlist=watchlist,
        mispricing_window=mispricing_window,
        source_reliability=source_reliability,
        sizing=sizing,
        audit_packet=audit_packet,
    )
    human_review = _required_human_review(status, audit_packet)

    return StrategyResearchDecisionBundleV7(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_id=readiness.candidate_id,
        market_slug=readiness.market_slug,
        bundle_status=status,
        required_human_review=human_review,
        readiness=readiness,
        watchlist=watchlist,
        mispricing_window=mispricing_window,
        source_reliability=source_reliability,
        sizing=sizing,
        audit_packet=audit_packet,
        reason_codes=_bundle_reason_codes(
            bundle_status=status,
            required_human_review=human_review,
            readiness=readiness,
            watchlist=watchlist,
            mispricing_window=mispricing_window,
            source_reliability=source_reliability,
            sizing=sizing,
            audit_packet=audit_packet,
        ),
    )


def strategy_research_decision_bundle_v7_payload(
    bundle: StrategyResearchDecisionBundleV7,
) -> dict[str, Any]:
    if type(bundle) is not StrategyResearchDecisionBundleV7:
        raise ValueError("bundle must be a StrategyResearchDecisionBundleV7")
    _require_safety_flags("bundle", bundle)
    return {
        "generated_at": bundle.generated_at.isoformat(),
        "config_version": bundle.config_version,
        "candidate_id": bundle.candidate_id,
        "market_slug": bundle.market_slug,
        "bundle_status": bundle.bundle_status,
        "required_human_review": bundle.required_human_review,
        "readiness": _readiness_payload(bundle.readiness),
        "watchlist": _watchlist_payload(bundle.watchlist),
        "mispricing_window": _mispricing_window_payload(bundle.mispricing_window),
        "source_reliability": _source_reliability_payload(bundle.source_reliability),
        "sizing": _sizing_payload(bundle.sizing),
        "audit_packet": _audit_packet_payload(bundle.audit_packet),
        "reason_codes": list(bundle.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _readiness_payload(
    value: StrategyResearchDecisionBundleV7ReadinessSummary,
) -> dict[str, Any]:
    _require_safety_flags("readiness", value)
    return {
        "candidate_id": value.candidate_id,
        "market_slug": value.market_slug,
        "readiness_status": value.readiness_status,
        "candidate_count": _count_payload(value.candidate_count),
        "ready_count": _count_payload(value.ready_count),
        "watch_count": _count_payload(value.watch_count),
        "blocked_count": _count_payload(value.blocked_count),
        "reason_codes": list(value.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _watchlist_payload(
    value: StrategyResearchDecisionBundleV7WatchlistSummary,
) -> dict[str, Any]:
    _require_safety_flags("watchlist", value)
    return {
        "candidate_id": value.candidate_id,
        "market_slug": value.market_slug,
        "watchlist_status": value.watchlist_status,
        "next_review_minutes": _count_payload(value.next_review_minutes),
        "reason_codes": list(value.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _mispricing_window_payload(
    value: StrategyResearchDecisionBundleV7MispricingWindowSummary,
) -> dict[str, Any]:
    _require_safety_flags("mispricing_window", value)
    return {
        "candidate_id": value.candidate_id,
        "market_slug": value.market_slug,
        "window_status": value.window_status,
        "mispriced_side": value.mispriced_side,
        "probability_gap": _decimal_payload(value.probability_gap),
        "abs_probability_gap": _decimal_payload(value.abs_probability_gap),
        "cost_adjusted_edge": _decimal_payload(value.cost_adjusted_edge),
        "reason_codes": list(value.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _source_reliability_payload(
    value: StrategyResearchDecisionBundleV7SourceReliabilitySummary,
) -> dict[str, Any]:
    _require_safety_flags("source_reliability", value)
    return {
        "candidate_id": value.candidate_id,
        "market_slug": value.market_slug,
        "source_count": _count_payload(value.source_count),
        "pass_count": _count_payload(value.pass_count),
        "watch_count": _count_payload(value.watch_count),
        "block_count": _count_payload(value.block_count),
        "average_source_weight": _decimal_payload(value.average_source_weight),
        "reliability_status": value.reliability_status,
        "reason_codes": list(value.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _sizing_payload(value: StrategyResearchDecisionBundleV7SizingSummary) -> dict[str, Any]:
    _require_safety_flags("sizing", value)
    return {
        "candidate_id": value.candidate_id,
        "market_slug": value.market_slug,
        "sizing_status": value.sizing_status,
        "binding_capacity": _decimal_payload(value.binding_capacity),
        "paper_notional": _decimal_payload(value.paper_notional),
        "resolution_risk": _decimal_payload(value.resolution_risk),
        "reason_codes": list(value.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _audit_packet_payload(
    value: StrategyResearchDecisionBundleV7AuditPacketSummary,
) -> dict[str, Any]:
    _require_safety_flags("audit_packet", value)
    return {
        "candidate_id": value.candidate_id,
        "market_slug": value.market_slug,
        "packet_status": value.packet_status,
        "recommendation": value.recommendation,
        "forecast_edge": _decimal_payload(value.forecast_edge),
        "cost_adjusted_edge": _decimal_payload(value.cost_adjusted_edge),
        "source_quality_score": _decimal_payload(value.source_quality_score),
        "resolution_risk_score": _decimal_payload(value.resolution_risk_score),
        "required_human_review": value.required_human_review,
        "reason_codes": list(value.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _bundle_status(
    *,
    readiness: StrategyResearchDecisionBundleV7ReadinessSummary,
    watchlist: StrategyResearchDecisionBundleV7WatchlistSummary,
    mispricing_window: StrategyResearchDecisionBundleV7MispricingWindowSummary,
    source_reliability: StrategyResearchDecisionBundleV7SourceReliabilitySummary,
    sizing: StrategyResearchDecisionBundleV7SizingSummary,
    audit_packet: StrategyResearchDecisionBundleV7AuditPacketSummary,
) -> str:
    if (
        readiness.readiness_status == "blocked"
        or watchlist.watchlist_status == "drop"
        or mispricing_window.window_status == "closed"
        or source_reliability.reliability_status == "blocked"
        or sizing.sizing_status == "blocked"
        or audit_packet.packet_status == "blocked"
        or audit_packet.recommendation == "skip"
    ):
        return "blocked"
    if (
        readiness.readiness_status == "watch"
        or watchlist.watchlist_status != "clear"
        or mispricing_window.window_status == "watch"
        or source_reliability.reliability_status == "watch"
        or sizing.sizing_status == "watch"
        or audit_packet.packet_status == "watch"
        or audit_packet.recommendation == "watch"
        or audit_packet.required_human_review
    ):
        return "watch"
    return "ready"


def _required_human_review(
    bundle_status: str,
    audit_packet: StrategyResearchDecisionBundleV7AuditPacketSummary,
) -> bool:
    return bundle_status != "ready" or audit_packet.required_human_review


def _bundle_reason_codes(
    *,
    bundle_status: str,
    required_human_review: bool,
    readiness: StrategyResearchDecisionBundleV7ReadinessSummary,
    watchlist: StrategyResearchDecisionBundleV7WatchlistSummary,
    mispricing_window: StrategyResearchDecisionBundleV7MispricingWindowSummary,
    source_reliability: StrategyResearchDecisionBundleV7SourceReliabilitySummary,
    sizing: StrategyResearchDecisionBundleV7SizingSummary,
    audit_packet: StrategyResearchDecisionBundleV7AuditPacketSummary,
) -> tuple[str, ...]:
    reason_codes = [
        f"strategy_research_decision_bundle_v7_{bundle_status}",
    ]
    if required_human_review:
        reason_codes.append("human_review_required")
    reason_codes.extend(
        (
            f"readiness_{readiness.readiness_status}",
            f"watchlist_{watchlist.watchlist_status}",
            f"mispricing_window_{mispricing_window.window_status}",
            f"source_reliability_{source_reliability.reliability_status}",
            f"sizing_{sizing.sizing_status}",
            f"audit_packet_{audit_packet.packet_status}",
        ),
    )
    for component_reason_codes in (
        readiness.reason_codes,
        watchlist.reason_codes,
        mispricing_window.reason_codes,
        source_reliability.reason_codes,
        sizing.reason_codes,
        audit_packet.reason_codes,
    ):
        reason_codes.extend(component_reason_codes)
    return _unique_reason_codes(tuple(reason_codes))


def _validate_bundle(bundle: StrategyResearchDecisionBundleV7) -> None:
    _validate_component_identity(bundle)
    expected_status = _bundle_status(
        readiness=bundle.readiness,
        watchlist=bundle.watchlist,
        mispricing_window=bundle.mispricing_window,
        source_reliability=bundle.source_reliability,
        sizing=bundle.sizing,
        audit_packet=bundle.audit_packet,
    )
    expected_human_review = _required_human_review(expected_status, bundle.audit_packet)
    if (
        bundle.bundle_status != expected_status
        or bundle.required_human_review != expected_human_review
    ):
        raise ValueError("bundle_status and required_human_review must match component state")
    expected_reason_codes = _bundle_reason_codes(
        bundle_status=expected_status,
        required_human_review=expected_human_review,
        readiness=bundle.readiness,
        watchlist=bundle.watchlist,
        mispricing_window=bundle.mispricing_window,
        source_reliability=bundle.source_reliability,
        sizing=bundle.sizing,
        audit_packet=bundle.audit_packet,
    )
    if bundle.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match component state")


def _validate_component_identity(bundle: StrategyResearchDecisionBundleV7) -> None:
    for component in (
        bundle.watchlist,
        bundle.mispricing_window,
        bundle.source_reliability,
        bundle.sizing,
        bundle.audit_packet,
    ):
        if (
            component.candidate_id != bundle.readiness.candidate_id
            or component.market_slug != bundle.readiness.market_slug
        ):
            raise ValueError("component identity must match readiness")
    if (
        bundle.candidate_id != bundle.readiness.candidate_id
        or bundle.market_slug != bundle.readiness.market_slug
    ):
        raise ValueError("component identity must match readiness")


def _validate_readiness_summary(
    value: StrategyResearchDecisionBundleV7ReadinessSummary,
) -> None:
    if value.candidate_count != value.ready_count + value.watch_count + value.blocked_count:
        raise ValueError("candidate_count must match readiness counts")
    if value.blocked_count > Decimal("0"):
        expected_status = "blocked"
    elif value.watch_count > Decimal("0") or value.ready_count != value.candidate_count:
        expected_status = "watch"
    else:
        expected_status = "ready"
    if value.readiness_status != expected_status:
        raise ValueError("readiness_status must match counts")


def _validate_mispricing_window_summary(
    value: StrategyResearchDecisionBundleV7MispricingWindowSummary,
) -> None:
    if value.abs_probability_gap != abs(value.probability_gap).quantize(QUANTUM):
        raise ValueError("abs_probability_gap must match probability_gap")
    expected_side = "none"
    if value.probability_gap > ZERO:
        expected_side = "yes"
    elif value.probability_gap < ZERO:
        expected_side = "no"
    if value.mispriced_side != expected_side:
        raise ValueError("mispriced_side must match probability_gap")


def _validate_source_reliability_summary(
    value: StrategyResearchDecisionBundleV7SourceReliabilitySummary,
) -> None:
    if value.source_count != value.pass_count + value.watch_count + value.block_count:
        raise ValueError("source_count must match reliability counts")
    if value.block_count > Decimal("0"):
        expected_status = "blocked"
    elif value.watch_count > Decimal("0"):
        expected_status = "watch"
    else:
        expected_status = "pass"
    if value.reliability_status != expected_status:
        raise ValueError("reliability_status must match counts")


def _validate_sizing_summary(value: StrategyResearchDecisionBundleV7SizingSummary) -> None:
    if value.paper_notional > value.binding_capacity:
        raise ValueError("paper_notional cannot exceed binding_capacity")
    if value.sizing_status == "blocked" and value.paper_notional != ZERO:
        raise ValueError("blocked sizing must have zero paper_notional")


def _require_component(
    field_name: str,
    value: object,
    expected_type: type[object],
) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")
    _require_safety_flags(field_name, value)


def _require_safety_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")


def _require_bool(field_name: str, value: object) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    for reason_code in value:
        _require_reason_code(reason_code)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique")
    return value


def _unique_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    for reason_code in value:
        _require_reason_code(reason_code)
    return tuple(dict.fromkeys(value))


def _require_reason_code(value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError("reason_codes must contain canonical reason codes")
    if value.lower() != value:
        raise ValueError("reason_codes must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part.lower() != part:
            raise ValueError("reason_codes must contain canonical reason codes")


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value, COUNT_QUANTUM)
    if decimal < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value, QUANTUM)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value, QUANTUM)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be a probability Decimal")
    return decimal


def _normalize_signed_probability(field_name: str, value: object) -> Decimal:
    decimal = _normalize_decimal(field_name, value, QUANTUM)
    if decimal < -ONE or decimal > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal


def _normalize_decimal(field_name: str, value: object, quantum: Decimal) -> Decimal:
    if isinstance(value, Decimal) and type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(quantum)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal_payload(value: Decimal) -> str:
    return format(_normalize_decimal("payload decimal", value, QUANTUM), "f")


def _count_payload(value: Decimal) -> str:
    return format(_normalize_count("payload count", value), "f")
