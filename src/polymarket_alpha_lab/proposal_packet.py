"""Proposal-only human-review packet artifacts for Level 2."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.manual_review_queue import PaperManualReviewQueueItem


__all__ = (
    "TradeProposalPacket",
    "TradeProposalPacketConfig",
    "TradeProposalPacketLog",
    "build_trade_proposal_packet",
)


DEFAULT_PROPOSAL_BOUNDARY_STATEMENT = (
    "This is a proposal-only human-review packet, not an approval workflow, "
    "trade instruction, order instruction, broker request, strategy-promotion "
    "signal, or live-execution signal; no order may leave the system without "
    "explicit human approval."
)
ZERO = Decimal("0")
ONE = Decimal("1")
PROPOSAL_SIDES = ("buy", "sell")


@dataclass(frozen=True)
class TradeProposalPacketConfig:
    config_version: str
    allowed_sides: tuple[str, ...] = PROPOSAL_SIDES
    allowed_intended_order_types: tuple[str, ...] = ("limit", "marketable_limit")
    min_cost_adjusted_edge: Decimal = Decimal("0.0000")
    max_proposal_size: Decimal | None = None
    max_exposure_after_trade: Decimal | None = None
    boundary_statement: str = DEFAULT_PROPOSAL_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _validate_config(self)


@dataclass(frozen=True)
class TradeProposalPacket:
    proposal_packet_id: str
    generated_at: datetime
    proposal_config_version: str
    proposal_only: bool
    human_approval_required: bool
    boundary_statement: str
    source_queue_item_id: str
    source_queue_rank: int
    source_manual_review_status: str
    source_packet_id: str
    source_boundary_statement: str
    source_paper_only: bool
    condition_id: str
    token_id: str
    market_slug: str
    market_url: str
    question: str
    outcome_name: str
    strategy_type: str
    side: str
    intended_order_type: str
    executable_price_assumption: Decimal
    maximum_size: Decimal
    source_max_executable_size: Decimal
    cost_adjusted_edge: Decimal
    theoretical_edge: Decimal | None
    fair_value_estimate: Decimal | None
    model_probability: Decimal | None
    confidence: Decimal | None
    source_score: Decimal
    market_score_total: Decimal | None
    thesis: str
    invalidating_conditions: str
    rule_text_hash: str
    resolution_source: str
    risk_tags: tuple[str, ...]
    exposure_after_trade: Decimal
    exit_rule: str
    reason_trade_could_be_wrong: str
    readiness_summary: str
    risk_summary: str
    evidence_summary: str
    why_in_queue: str
    primary_reason_code: str
    supporting_reason_codes: tuple[str, ...]
    blocking_reason_codes: tuple[str, ...]
    review_focus: tuple[str, ...]
    history_status: str
    forecast_status: str
    history_gate_pass_count: int
    forecast_gate_pass_count: int
    history_gate_fail_count: int
    forecast_gate_fail_count: int
    evidence_scope: str
    risk_gate_passed: bool
    hard_block_count: int

    def __post_init__(self) -> None:
        _validate_packet(self)


@dataclass(frozen=True)
class TradeProposalPacketLog:
    path: Path | str

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))

    def append(self, packet: TradeProposalPacket) -> None:
        if not isinstance(packet, TradeProposalPacket):
            raise ValueError("packet must be a TradeProposalPacket")
        validated = _validate_packet_tree(packet)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_packet(
    queue_item: PaperManualReviewQueueItem,
    *,
    side: str,
    intended_order_type: str,
    maximum_size: Decimal,
    exposure_after_trade: Decimal,
    exit_rule: str,
    reason_trade_could_be_wrong: str,
    config: TradeProposalPacketConfig,
    generated_at: datetime,
) -> TradeProposalPacket:
    item = _clone_queue_item(queue_item)
    _validate_ready_queue_item(item)
    if type(config) is not TradeProposalPacketConfig:
        raise ValueError("config must be a TradeProposalPacketConfig")
    if not isinstance(generated_at, datetime):
        raise ValueError("generated_at must be a datetime")
    generated_at = _as_utc(generated_at)
    _require_canonical_string("side", side)
    _require_canonical_string("intended_order_type", intended_order_type)
    if side not in config.allowed_sides:
        raise ValueError("side is not allowed by config")
    if intended_order_type not in config.allowed_intended_order_types:
        raise ValueError("intended_order_type is not allowed by config")
    _require_positive_decimal("maximum_size", maximum_size)
    _require_nonnegative_decimal("exposure_after_trade", exposure_after_trade)
    _require_canonical_string("exit_rule", exit_rule)
    _require_canonical_string(
        "reason_trade_could_be_wrong",
        reason_trade_could_be_wrong,
    )
    if maximum_size > item.max_executable_size:
        raise ValueError("maximum_size must not exceed source max_executable_size")
    if config.max_proposal_size is not None and maximum_size > config.max_proposal_size:
        raise ValueError("maximum_size exceeds max_proposal_size")
    if item.cost_adjusted_edge < config.min_cost_adjusted_edge:
        raise ValueError("cost_adjusted_edge is below minimum")
    if (
        config.max_exposure_after_trade is not None
        and exposure_after_trade > config.max_exposure_after_trade
    ):
        raise ValueError("exposure_after_trade exceeds maximum")
    packet_id = _proposal_packet_id(
        config_version=config.config_version,
        generated_at=generated_at,
        source_queue_item_id=item.queue_item_id,
        side=side,
        intended_order_type=intended_order_type,
        maximum_size=maximum_size,
        exposure_after_trade=exposure_after_trade,
    )
    return TradeProposalPacket(
        proposal_packet_id=packet_id,
        generated_at=generated_at,
        proposal_config_version=config.config_version,
        proposal_only=True,
        human_approval_required=True,
        boundary_statement=config.boundary_statement,
        source_queue_item_id=item.queue_item_id,
        source_queue_rank=item.rank,
        source_manual_review_status=item.status,
        source_packet_id=item.packet_id,
        source_boundary_statement=item.boundary_statement,
        source_paper_only=item.paper_only,
        condition_id=item.condition_id,
        token_id=item.token_id,
        market_slug=item.market_slug,
        market_url=item.market_url,
        question=item.question,
        outcome_name=item.outcome_name,
        strategy_type=item.strategy_type,
        side=side,
        intended_order_type=intended_order_type,
        executable_price_assumption=item.expected_entry_price,
        maximum_size=maximum_size,
        source_max_executable_size=item.max_executable_size,
        cost_adjusted_edge=item.cost_adjusted_edge,
        theoretical_edge=item.theoretical_edge,
        fair_value_estimate=item.fair_value_estimate,
        model_probability=item.model_probability,
        confidence=item.confidence,
        source_score=item.source_score,
        market_score_total=item.market_score_total,
        thesis=item.thesis,
        invalidating_conditions=item.invalidating_conditions,
        rule_text_hash=item.rule_text_hash,
        resolution_source=item.resolution_source,
        risk_tags=item.risk_tags,
        exposure_after_trade=exposure_after_trade,
        exit_rule=exit_rule,
        reason_trade_could_be_wrong=reason_trade_could_be_wrong,
        readiness_summary=item.readiness_summary,
        risk_summary=item.risk_summary,
        evidence_summary=item.evidence_summary,
        why_in_queue=item.why_in_queue,
        primary_reason_code=item.primary_reason_code,
        supporting_reason_codes=item.supporting_reason_codes,
        blocking_reason_codes=item.blocking_reason_codes,
        review_focus=item.review_focus,
        history_status=item.history_status,
        forecast_status=item.forecast_status,
        history_gate_pass_count=item.history_gate_pass_count,
        forecast_gate_pass_count=item.forecast_gate_pass_count,
        history_gate_fail_count=item.history_gate_fail_count,
        forecast_gate_fail_count=item.forecast_gate_fail_count,
        evidence_scope=item.evidence_scope,
        risk_gate_passed=item.risk_gate_passed,
        hard_block_count=item.hard_block_count,
    )


def _clone_queue_item(item: PaperManualReviewQueueItem) -> PaperManualReviewQueueItem:
    if type(item) is not PaperManualReviewQueueItem:
        raise ValueError("queue_item must be a PaperManualReviewQueueItem")
    return PaperManualReviewQueueItem(
        queue_item_id=item.queue_item_id,
        rank=item.rank,
        status=item.status,
        status_rank=item.status_rank,
        hard_block_count=item.hard_block_count,
        evidence_pass_count=item.evidence_pass_count,
        source_score=item.source_score,
        market_score_total=item.market_score_total,
        queued_at=item.queued_at,
        packet_id=item.packet_id,
        condition_id=item.condition_id,
        token_id=item.token_id,
        market_slug=item.market_slug,
        market_url=item.market_url,
        question=item.question,
        outcome_name=item.outcome_name,
        strategy_type=item.strategy_type,
        risk_tags=item.risk_tags,
        thesis=item.thesis,
        invalidating_conditions=item.invalidating_conditions,
        rule_text_hash=item.rule_text_hash,
        resolution_source=item.resolution_source,
        model_probability=item.model_probability,
        expected_entry_price=item.expected_entry_price,
        fair_value_estimate=item.fair_value_estimate,
        theoretical_edge=item.theoretical_edge,
        cost_adjusted_edge=item.cost_adjusted_edge,
        confidence=item.confidence,
        max_executable_size=item.max_executable_size,
        risk_gate_passed=item.risk_gate_passed,
        risk_reason_codes=item.risk_reason_codes,
        history_status=item.history_status,
        forecast_status=item.forecast_status,
        history_gate_pass_count=item.history_gate_pass_count,
        forecast_gate_pass_count=item.forecast_gate_pass_count,
        history_gate_fail_count=item.history_gate_fail_count,
        forecast_gate_fail_count=item.forecast_gate_fail_count,
        readiness_summary=item.readiness_summary,
        risk_summary=item.risk_summary,
        evidence_summary=item.evidence_summary,
        why_in_queue=item.why_in_queue,
        primary_reason_code=item.primary_reason_code,
        supporting_reason_codes=item.supporting_reason_codes,
        blocking_reason_codes=item.blocking_reason_codes,
        review_focus=item.review_focus,
        evidence_scope=item.evidence_scope,
        boundary_statement=item.boundary_statement,
        paper_only=item.paper_only,
    )


def _validate_ready_queue_item(item: PaperManualReviewQueueItem) -> None:
    if item.status != "paper_review_ready":
        raise ValueError("queue_item must be paper_review_ready")
    if item.paper_only is not True:
        raise ValueError("queue_item must be paper-only")
    if item.risk_gate_passed is not True:
        raise ValueError("queue_item risk gate must have passed")
    if item.hard_block_count != 0:
        raise ValueError("queue_item must not have hard blocks")
    if item.blocking_reason_codes:
        raise ValueError("queue_item must not have blocking reason codes")
    if item.history_status != "paper_review_ready":
        raise ValueError("history_status must be paper_review_ready")
    if item.forecast_status != "paper_review_ready":
        raise ValueError("forecast_status must be paper_review_ready")
    if item.history_gate_fail_count != 0:
        raise ValueError("history_gate_fail_count must be zero")
    if item.forecast_gate_fail_count != 0:
        raise ValueError("forecast_gate_fail_count must be zero")
    if item.market_url == "":
        raise ValueError("market_url is required")
    if item.expected_entry_price is None:
        raise ValueError("expected_entry_price is required")
    _require_decimal("expected_entry_price", item.expected_entry_price)
    if item.expected_entry_price <= ZERO or item.expected_entry_price >= ONE:
        raise ValueError("expected_entry_price must be greater than 0 and less than 1")
    if item.max_executable_size is None:
        raise ValueError("max_executable_size is required")
    _require_positive_decimal("max_executable_size", item.max_executable_size)
    if item.cost_adjusted_edge is None:
        raise ValueError("cost_adjusted_edge is required")
    _require_nonnegative_decimal("cost_adjusted_edge", item.cost_adjusted_edge)
    if not item.risk_tags:
        raise ValueError("risk_tags are required")


def _validate_config(config: TradeProposalPacketConfig) -> None:
    _require_canonical_string("config_version", config.config_version)
    allowed_sides = _normalize_string_tuple("allowed_sides", config.allowed_sides)
    if not allowed_sides:
        raise ValueError("allowed_sides must not be empty")
    if any(side not in PROPOSAL_SIDES for side in allowed_sides):
        raise ValueError("allowed_sides must contain supported proposal sides")
    object.__setattr__(config, "allowed_sides", allowed_sides)
    allowed_order_types = _normalize_string_tuple(
        "allowed_intended_order_types",
        config.allowed_intended_order_types,
    )
    if not allowed_order_types:
        raise ValueError("allowed_intended_order_types must not be empty")
    object.__setattr__(config, "allowed_intended_order_types", allowed_order_types)
    _require_decimal("min_cost_adjusted_edge", config.min_cost_adjusted_edge)
    if config.max_proposal_size is not None:
        _require_positive_decimal("max_proposal_size", config.max_proposal_size)
    if config.max_exposure_after_trade is not None:
        _require_nonnegative_decimal(
            "max_exposure_after_trade",
            config.max_exposure_after_trade,
        )
    _require_boundary_statement(config.boundary_statement)


def _validate_packet(packet: TradeProposalPacket) -> None:
    object.__setattr__(packet, "generated_at", _as_utc(packet.generated_at))
    for field_name in (
        "proposal_packet_id",
        "proposal_config_version",
        "source_queue_item_id",
        "source_manual_review_status",
        "source_packet_id",
        "source_boundary_statement",
        "condition_id",
        "token_id",
        "market_slug",
        "market_url",
        "question",
        "outcome_name",
        "strategy_type",
        "side",
        "intended_order_type",
        "thesis",
        "invalidating_conditions",
        "rule_text_hash",
        "resolution_source",
        "exit_rule",
        "reason_trade_could_be_wrong",
        "readiness_summary",
        "risk_summary",
        "evidence_summary",
        "why_in_queue",
        "primary_reason_code",
        "evidence_scope",
    ):
        _require_canonical_string(field_name, getattr(packet, field_name))
    _require_boundary_statement(packet.boundary_statement)
    if packet.proposal_only is not True:
        raise ValueError("proposal_only must be True")
    if packet.human_approval_required is not True:
        raise ValueError("human_approval_required must be True")
    if packet.source_paper_only is not True:
        raise ValueError("source_paper_only must be True")
    if packet.source_manual_review_status != "paper_review_ready":
        raise ValueError("source_manual_review_status must be paper_review_ready")
    if packet.risk_gate_passed is not True:
        raise ValueError("risk_gate_passed must be True")
    _require_nonnegative_int("hard_block_count", packet.hard_block_count)
    if packet.hard_block_count != 0:
        raise ValueError("hard_block_count must be zero")
    if packet.source_queue_item_id != (
        f"{packet.condition_id}:{packet.token_id}:{packet.source_packet_id}"
    ):
        raise ValueError("source_queue_item_id must match condition_id:token_id:source_packet_id")
    _require_positive_int("source_queue_rank", packet.source_queue_rank)
    if packet.side not in PROPOSAL_SIDES:
        raise ValueError("side must be buy or sell")
    _require_executable_price(packet.executable_price_assumption)
    _require_positive_decimal("maximum_size", packet.maximum_size)
    _require_positive_decimal("source_max_executable_size", packet.source_max_executable_size)
    if packet.maximum_size > packet.source_max_executable_size:
        raise ValueError("maximum_size must be less than or equal to source_max_executable_size")
    _require_nonnegative_decimal("cost_adjusted_edge", packet.cost_adjusted_edge)
    _require_optional_finite_decimal("theoretical_edge", packet.theoretical_edge)
    _require_optional_probability("fair_value_estimate", packet.fair_value_estimate)
    _require_optional_probability("model_probability", packet.model_probability)
    _require_optional_probability("confidence", packet.confidence)
    _require_nonnegative_decimal("source_score", packet.source_score)
    _require_optional_finite_decimal("market_score_total", packet.market_score_total)
    _require_nonnegative_decimal("exposure_after_trade", packet.exposure_after_trade)
    if packet.history_status != "paper_review_ready":
        raise ValueError("history_status must be paper_review_ready")
    if packet.forecast_status != "paper_review_ready":
        raise ValueError("forecast_status must be paper_review_ready")
    _require_nonnegative_int("history_gate_pass_count", packet.history_gate_pass_count)
    _require_nonnegative_int("forecast_gate_pass_count", packet.forecast_gate_pass_count)
    _require_nonnegative_int("history_gate_fail_count", packet.history_gate_fail_count)
    _require_nonnegative_int("forecast_gate_fail_count", packet.forecast_gate_fail_count)
    if packet.history_gate_fail_count != 0:
        raise ValueError("history_gate_fail_count must be zero")
    if packet.forecast_gate_fail_count != 0:
        raise ValueError("forecast_gate_fail_count must be zero")
    object.__setattr__(packet, "risk_tags", _normalize_string_tuple("risk_tags", packet.risk_tags))
    object.__setattr__(
        packet,
        "supporting_reason_codes",
        _normalize_string_tuple("supporting_reason_codes", packet.supporting_reason_codes),
    )
    object.__setattr__(
        packet,
        "blocking_reason_codes",
        _normalize_string_tuple("blocking_reason_codes", packet.blocking_reason_codes),
    )
    object.__setattr__(
        packet,
        "review_focus",
        _normalize_string_tuple("review_focus", packet.review_focus),
    )
    if not packet.risk_tags:
        raise ValueError("risk_tags are required")
    if packet.blocking_reason_codes:
        raise ValueError("blocking_reason_codes must be empty")
    expected_id = _proposal_packet_id(
        config_version=packet.proposal_config_version,
        generated_at=packet.generated_at,
        source_queue_item_id=packet.source_queue_item_id,
        side=packet.side,
        intended_order_type=packet.intended_order_type,
        maximum_size=packet.maximum_size,
        exposure_after_trade=packet.exposure_after_trade,
    )
    if packet.proposal_packet_id != expected_id:
        raise ValueError("proposal_packet_id must match packet fields")


def _validate_packet_tree(packet: TradeProposalPacket) -> TradeProposalPacket:
    return TradeProposalPacket(
        proposal_packet_id=packet.proposal_packet_id,
        generated_at=packet.generated_at,
        proposal_config_version=packet.proposal_config_version,
        proposal_only=packet.proposal_only,
        human_approval_required=packet.human_approval_required,
        boundary_statement=packet.boundary_statement,
        source_queue_item_id=packet.source_queue_item_id,
        source_queue_rank=packet.source_queue_rank,
        source_manual_review_status=packet.source_manual_review_status,
        source_packet_id=packet.source_packet_id,
        source_boundary_statement=packet.source_boundary_statement,
        source_paper_only=packet.source_paper_only,
        condition_id=packet.condition_id,
        token_id=packet.token_id,
        market_slug=packet.market_slug,
        market_url=packet.market_url,
        question=packet.question,
        outcome_name=packet.outcome_name,
        strategy_type=packet.strategy_type,
        side=packet.side,
        intended_order_type=packet.intended_order_type,
        executable_price_assumption=packet.executable_price_assumption,
        maximum_size=packet.maximum_size,
        source_max_executable_size=packet.source_max_executable_size,
        cost_adjusted_edge=packet.cost_adjusted_edge,
        theoretical_edge=packet.theoretical_edge,
        fair_value_estimate=packet.fair_value_estimate,
        model_probability=packet.model_probability,
        confidence=packet.confidence,
        source_score=packet.source_score,
        market_score_total=packet.market_score_total,
        thesis=packet.thesis,
        invalidating_conditions=packet.invalidating_conditions,
        rule_text_hash=packet.rule_text_hash,
        resolution_source=packet.resolution_source,
        risk_tags=packet.risk_tags,
        exposure_after_trade=packet.exposure_after_trade,
        exit_rule=packet.exit_rule,
        reason_trade_could_be_wrong=packet.reason_trade_could_be_wrong,
        readiness_summary=packet.readiness_summary,
        risk_summary=packet.risk_summary,
        evidence_summary=packet.evidence_summary,
        why_in_queue=packet.why_in_queue,
        primary_reason_code=packet.primary_reason_code,
        supporting_reason_codes=packet.supporting_reason_codes,
        blocking_reason_codes=packet.blocking_reason_codes,
        review_focus=packet.review_focus,
        history_status=packet.history_status,
        forecast_status=packet.forecast_status,
        history_gate_pass_count=packet.history_gate_pass_count,
        forecast_gate_pass_count=packet.forecast_gate_pass_count,
        history_gate_fail_count=packet.history_gate_fail_count,
        forecast_gate_fail_count=packet.forecast_gate_fail_count,
        evidence_scope=packet.evidence_scope,
        risk_gate_passed=packet.risk_gate_passed,
        hard_block_count=packet.hard_block_count,
    )


def _proposal_packet_id(
    *,
    config_version: str,
    generated_at: datetime,
    source_queue_item_id: str,
    side: str,
    intended_order_type: str,
    maximum_size: Decimal,
    exposure_after_trade: Decimal,
) -> str:
    raw = "|".join(
        (
            config_version,
            _as_utc(generated_at).isoformat(),
            source_queue_item_id,
            side,
            intended_order_type,
            str(maximum_size),
            str(exposure_after_trade),
        )
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"proposal-{digest}"


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        _require_decimal("JSON Decimal value", value)
        return str(value)
    if isinstance(value, datetime):
        return _as_utc(value).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, dict):
        for key in value:
            if not isinstance(key, str):
                raise ValueError("JSON object keys must be strings")
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_log_path(value: Path | str) -> Path:
    if isinstance(value, str) and not value.strip():
        raise ValueError("path is required")
    try:
        path = Path(value)
    except TypeError as exc:
        raise ValueError("path must be path-like") from exc
    if path.exists() and path.is_dir():
        raise ValueError("path must be a file path")
    _validate_log_parent(path)
    return path


def _validate_log_parent(path: Path) -> None:
    for parent in (path.parent, *path.parent.parents):
        if parent.exists():
            if not parent.is_dir():
                raise ValueError("path parent must be a directory")
            return


def _as_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError("datetime value is required")
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_boundary_statement(value: str) -> None:
    _require_canonical_string("boundary_statement", value)
    lowered = value.lower()
    required_parts = (
        "proposal-only",
        "human-review packet",
        "not an approval workflow",
        "trade instruction",
        "order instruction",
        "broker request",
        "live-execution signal",
        "explicit human approval",
    )
    if any(part not in lowered for part in required_parts):
        raise ValueError("boundary_statement must describe proposal-only human review")


def _normalize_string_tuple(field_name: str, value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    for item in items:
        _require_canonical_string(field_name, item)
    return items


def _require_positive_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_int(field_name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: Decimal) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_optional_finite_decimal(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_decimal(field_name, value)


def _require_probability(field_name: str, value: Decimal) -> None:
    _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")


def _require_optional_probability(field_name: str, value: Decimal | None) -> None:
    if value is not None:
        _require_probability(field_name, value)


def _require_executable_price(value: Decimal) -> None:
    _require_probability("executable_price_assumption", value)
    if value == ZERO or value == ONE:
        raise ValueError("executable_price_assumption must be greater than 0 and less than 1")
