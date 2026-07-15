"""Record-only human-review decision artifacts for Level 2."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from polymarket_alpha_lab.proposal_packet import TradeProposalPacket


__all__ = (
    "TradeProposalReviewConfig",
    "TradeProposalReviewRecord",
    "TradeProposalReviewLog",
    "build_trade_proposal_review_record",
)


DEFAULT_REVIEW_ATTESTATION = (
    "I reviewed this proposal packet and understand this record is not a "
    "trade instruction, order instruction, broker request, order request, "
    "account action, account authentication, private-key handling, wallet "
    "signature, live-execution signal, manual execution import, credential "
    "request, or automatic order-placement authorization."
)
DEFAULT_REVIEW_BOUNDARY_STATEMENT = (
    "This is a record-only human-review decision artifact, not an approval "
    "workflow, trade instruction, order instruction, broker request, order "
    "request, account action, account authentication, private-key handling, "
    "wallet signature, live-execution signal, credential workflow, manual "
    "execution import, or automatic order-placement authorization."
)
ZERO = Decimal("0")
ONE = Decimal("1")
REVIEW_DECISIONS = ("approved", "rejected")
REVIEW_ID_FIELDS = (
    "review_config_version",
    "recorded_at",
    "source_proposal_packet_id",
    "source_proposal_fingerprint",
    "decision",
    "reviewer_label",
    "review_rationale",
    "review_reason_codes",
    "human_attestation",
)
SOURCE_FINGERPRINT_FIELDS = (
    "source_proposal_packet_id",
    "source_proposal_generated_at",
    "source_proposal_config_version",
    "source_proposal_boundary_statement",
    "source_queue_boundary_statement",
    "source_proposal_only",
    "source_human_approval_required",
    "source_queue_item_id",
    "source_queue_rank",
    "source_manual_review_status",
    "source_packet_id",
    "source_paper_only",
    "condition_id",
    "token_id",
    "market_slug",
    "market_url",
    "question",
    "outcome_name",
    "strategy_type",
    "side",
    "intended_order_type",
    "executable_price_assumption",
    "maximum_size",
    "source_max_executable_size",
    "cost_adjusted_edge",
    "theoretical_edge",
    "fair_value_estimate",
    "model_probability",
    "confidence",
    "source_score",
    "market_score_total",
    "exposure_after_trade",
    "exit_rule",
    "thesis",
    "invalidating_conditions",
    "rule_text_hash",
    "resolution_source",
    "risk_tags",
    "reason_trade_could_be_wrong",
    "readiness_summary",
    "risk_summary",
    "evidence_summary",
    "why_in_queue",
    "primary_reason_code",
    "supporting_reason_codes",
    "review_focus",
    "evidence_scope",
    "history_status",
    "forecast_status",
    "history_gate_pass_count",
    "forecast_gate_pass_count",
    "history_gate_fail_count",
    "forecast_gate_fail_count",
    "risk_gate_passed",
    "hard_block_count",
    "blocking_reason_codes",
)
EPHEMERAL_REVIEW_LOG_WRITE_MODE = "at"


@dataclass(frozen=True)
class TradeProposalReviewConfig:
    config_version: str
    allowed_decisions: tuple[str, ...] = REVIEW_DECISIONS
    required_human_attestation: str = DEFAULT_REVIEW_ATTESTATION
    boundary_statement: str = DEFAULT_REVIEW_BOUNDARY_STATEMENT

    def __post_init__(self) -> None:
        _validate_config(self)


@dataclass(frozen=True)
class TradeProposalReviewRecord:
    review_record_id: str
    recorded_at: datetime
    review_config_version: str
    record_only: bool
    explicit_human_decision: bool
    boundary_statement: str
    source_proposal_packet_id: str
    source_proposal_generated_at: datetime
    source_proposal_config_version: str
    source_proposal_fingerprint: str
    source_proposal_boundary_statement: str
    source_queue_boundary_statement: str
    source_proposal_only: bool
    source_human_approval_required: bool
    source_queue_item_id: str
    source_queue_rank: int
    source_manual_review_status: str
    source_packet_id: str
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
    exposure_after_trade: Decimal
    exit_rule: str
    thesis: str
    invalidating_conditions: str
    rule_text_hash: str
    resolution_source: str
    risk_tags: tuple[str, ...]
    reason_trade_could_be_wrong: str
    readiness_summary: str
    risk_summary: str
    evidence_summary: str
    why_in_queue: str
    primary_reason_code: str
    supporting_reason_codes: tuple[str, ...]
    review_focus: tuple[str, ...]
    evidence_scope: str
    history_status: str
    forecast_status: str
    history_gate_pass_count: int
    forecast_gate_pass_count: int
    history_gate_fail_count: int
    forecast_gate_fail_count: int
    risk_gate_passed: bool
    hard_block_count: int
    blocking_reason_codes: tuple[str, ...]
    decision: str
    reviewer_label: str
    review_rationale: str
    review_reason_codes: tuple[str, ...]
    human_attestation: str

    def __post_init__(self) -> None:
        _validate_record(self)

    def public_safe_payload(self) -> dict[str, Any]:
        """Return report-only review attestation metadata safe for public output."""
        validated = _validate_record_tree(self)
        return _public_safe_review_payload(validated)


@dataclass(frozen=True)
class TradeProposalReviewLog:
    """Legacy ephemeral/local review log, not durable memory or public output."""

    path: Path | str
    storage_scope: str = "ephemeral_local_review_log"
    durable_memory: bool = False
    public_output: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", _normalize_log_path(self.path))
        _validate_ephemeral_review_log_scope(self)

    def record(self, record: TradeProposalReviewRecord) -> None:
        _validate_ephemeral_review_log_scope(self)
        if not isinstance(record, TradeProposalReviewRecord):
            raise ValueError("record must be a TradeProposalReviewRecord")
        validated = _validate_record_tree(record)
        line = json.dumps(_json_ready(asdict(validated)), allow_nan=False, sort_keys=True) + "\n"
        _validate_log_parent(self.path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open(mode=EPHEMERAL_REVIEW_LOG_WRITE_MODE, encoding="utf-8") as handle:
            handle.write(line)


def build_trade_proposal_review_record(
    proposal: TradeProposalPacket,
    *,
    decision: str,
    reviewer_label: str,
    review_rationale: str,
    review_reason_codes: Iterable[str] = (),
    human_attestation: str,
    config: TradeProposalReviewConfig,
    recorded_at: datetime,
) -> TradeProposalReviewRecord:
    source = _clone_proposal_packet(proposal)
    _validate_source_proposal(source)
    if type(config) is not TradeProposalReviewConfig:
        raise ValueError("config must be a TradeProposalReviewConfig")
    if not isinstance(recorded_at, datetime):
        raise ValueError("recorded_at must be a datetime")
    recorded_at = _as_utc(recorded_at)
    _require_canonical_string("decision", decision)
    if decision not in config.allowed_decisions:
        raise ValueError("decision is not allowed by config")
    _require_canonical_string("reviewer_label", reviewer_label)
    _require_canonical_string("review_rationale", review_rationale)
    _require_canonical_string("human_attestation", human_attestation)
    if human_attestation != config.required_human_attestation:
        raise ValueError("human_attestation must match required_human_attestation")
    reason_codes = _normalize_string_tuple("review_reason_codes", review_reason_codes)
    if decision == "approved" and reason_codes:
        raise ValueError("review_reason_codes must be empty when decision is approved")
    if decision == "rejected" and not reason_codes:
        raise ValueError("review_reason_codes are required when decision is rejected")
    fingerprint = _source_proposal_fingerprint(source)
    record_id = _review_record_id(
        review_config_version=config.config_version,
        recorded_at=recorded_at,
        source_proposal_packet_id=source.proposal_packet_id,
        source_proposal_fingerprint=fingerprint,
        decision=decision,
        reviewer_label=reviewer_label,
        review_rationale=review_rationale,
        review_reason_codes=reason_codes,
        human_attestation=human_attestation,
    )
    return TradeProposalReviewRecord(
        review_record_id=record_id,
        recorded_at=recorded_at,
        review_config_version=config.config_version,
        record_only=True,
        explicit_human_decision=True,
        boundary_statement=config.boundary_statement,
        source_proposal_packet_id=source.proposal_packet_id,
        source_proposal_generated_at=source.generated_at,
        source_proposal_config_version=source.proposal_config_version,
        source_proposal_fingerprint=fingerprint,
        source_proposal_boundary_statement=source.boundary_statement,
        source_queue_boundary_statement=source.source_boundary_statement,
        source_proposal_only=source.proposal_only,
        source_human_approval_required=source.human_approval_required,
        source_queue_item_id=source.source_queue_item_id,
        source_queue_rank=source.source_queue_rank,
        source_manual_review_status=source.source_manual_review_status,
        source_packet_id=source.source_packet_id,
        source_paper_only=source.source_paper_only,
        condition_id=source.condition_id,
        token_id=source.token_id,
        market_slug=source.market_slug,
        market_url=source.market_url,
        question=source.question,
        outcome_name=source.outcome_name,
        strategy_type=source.strategy_type,
        side=source.side,
        intended_order_type=source.intended_order_type,
        executable_price_assumption=source.executable_price_assumption,
        maximum_size=source.maximum_size,
        source_max_executable_size=source.source_max_executable_size,
        cost_adjusted_edge=source.cost_adjusted_edge,
        theoretical_edge=source.theoretical_edge,
        fair_value_estimate=source.fair_value_estimate,
        model_probability=source.model_probability,
        confidence=source.confidence,
        source_score=source.source_score,
        market_score_total=source.market_score_total,
        exposure_after_trade=source.exposure_after_trade,
        exit_rule=source.exit_rule,
        thesis=source.thesis,
        invalidating_conditions=source.invalidating_conditions,
        rule_text_hash=source.rule_text_hash,
        resolution_source=source.resolution_source,
        risk_tags=source.risk_tags,
        reason_trade_could_be_wrong=source.reason_trade_could_be_wrong,
        readiness_summary=source.readiness_summary,
        risk_summary=source.risk_summary,
        evidence_summary=source.evidence_summary,
        why_in_queue=source.why_in_queue,
        primary_reason_code=source.primary_reason_code,
        supporting_reason_codes=source.supporting_reason_codes,
        review_focus=source.review_focus,
        evidence_scope=source.evidence_scope,
        history_status=source.history_status,
        forecast_status=source.forecast_status,
        history_gate_pass_count=source.history_gate_pass_count,
        forecast_gate_pass_count=source.forecast_gate_pass_count,
        history_gate_fail_count=source.history_gate_fail_count,
        forecast_gate_fail_count=source.forecast_gate_fail_count,
        risk_gate_passed=source.risk_gate_passed,
        hard_block_count=source.hard_block_count,
        blocking_reason_codes=source.blocking_reason_codes,
        decision=decision,
        reviewer_label=reviewer_label,
        review_rationale=review_rationale,
        review_reason_codes=reason_codes,
        human_attestation=human_attestation,
    )


def _clone_proposal_packet(proposal: TradeProposalPacket) -> TradeProposalPacket:
    if type(proposal) is not TradeProposalPacket:
        raise ValueError("proposal must be a TradeProposalPacket")
    return TradeProposalPacket(
        proposal_packet_id=proposal.proposal_packet_id,
        generated_at=proposal.generated_at,
        proposal_config_version=proposal.proposal_config_version,
        proposal_only=proposal.proposal_only,
        human_approval_required=proposal.human_approval_required,
        boundary_statement=proposal.boundary_statement,
        source_queue_item_id=proposal.source_queue_item_id,
        source_queue_rank=proposal.source_queue_rank,
        source_manual_review_status=proposal.source_manual_review_status,
        source_packet_id=proposal.source_packet_id,
        source_boundary_statement=proposal.source_boundary_statement,
        source_paper_only=proposal.source_paper_only,
        condition_id=proposal.condition_id,
        token_id=proposal.token_id,
        market_slug=proposal.market_slug,
        market_url=proposal.market_url,
        question=proposal.question,
        outcome_name=proposal.outcome_name,
        strategy_type=proposal.strategy_type,
        side=proposal.side,
        intended_order_type=proposal.intended_order_type,
        executable_price_assumption=proposal.executable_price_assumption,
        maximum_size=proposal.maximum_size,
        source_max_executable_size=proposal.source_max_executable_size,
        cost_adjusted_edge=proposal.cost_adjusted_edge,
        theoretical_edge=proposal.theoretical_edge,
        fair_value_estimate=proposal.fair_value_estimate,
        model_probability=proposal.model_probability,
        confidence=proposal.confidence,
        source_score=proposal.source_score,
        market_score_total=proposal.market_score_total,
        thesis=proposal.thesis,
        invalidating_conditions=proposal.invalidating_conditions,
        rule_text_hash=proposal.rule_text_hash,
        resolution_source=proposal.resolution_source,
        risk_tags=proposal.risk_tags,
        exposure_after_trade=proposal.exposure_after_trade,
        exit_rule=proposal.exit_rule,
        reason_trade_could_be_wrong=proposal.reason_trade_could_be_wrong,
        readiness_summary=proposal.readiness_summary,
        risk_summary=proposal.risk_summary,
        evidence_summary=proposal.evidence_summary,
        why_in_queue=proposal.why_in_queue,
        primary_reason_code=proposal.primary_reason_code,
        supporting_reason_codes=proposal.supporting_reason_codes,
        blocking_reason_codes=proposal.blocking_reason_codes,
        review_focus=proposal.review_focus,
        history_status=proposal.history_status,
        forecast_status=proposal.forecast_status,
        history_gate_pass_count=proposal.history_gate_pass_count,
        forecast_gate_pass_count=proposal.forecast_gate_pass_count,
        history_gate_fail_count=proposal.history_gate_fail_count,
        forecast_gate_fail_count=proposal.forecast_gate_fail_count,
        evidence_scope=proposal.evidence_scope,
        risk_gate_passed=proposal.risk_gate_passed,
        hard_block_count=proposal.hard_block_count,
    )


def _validate_source_proposal(proposal: TradeProposalPacket) -> None:
    if proposal.proposal_only is not True:
        raise ValueError("source proposal_only must be True")
    if proposal.human_approval_required is not True:
        raise ValueError("source human_approval_required must be True")
    if proposal.source_paper_only is not True:
        raise ValueError("source_paper_only must be True")
    if proposal.source_manual_review_status != "paper_review_ready":
        raise ValueError("source_manual_review_status must be paper_review_ready")
    if proposal.risk_gate_passed is not True:
        raise ValueError("risk_gate_passed must be True")
    if proposal.hard_block_count != 0:
        raise ValueError("hard_block_count must be zero")
    if proposal.blocking_reason_codes:
        raise ValueError("blocking_reason_codes must be empty")
    if proposal.history_status != "paper_review_ready":
        raise ValueError("history_status must be paper_review_ready")
    if proposal.forecast_status != "paper_review_ready":
        raise ValueError("forecast_status must be paper_review_ready")
    if proposal.history_gate_fail_count != 0:
        raise ValueError("history_gate_fail_count must be zero")
    if proposal.forecast_gate_fail_count != 0:
        raise ValueError("forecast_gate_fail_count must be zero")


def _validate_config(config: TradeProposalReviewConfig) -> None:
    _require_canonical_string("config_version", config.config_version)
    allowed_decisions = _normalize_string_tuple(
        "allowed_decisions",
        config.allowed_decisions,
    )
    if set(allowed_decisions) != set(REVIEW_DECISIONS):
        raise ValueError("allowed_decisions must contain approved and rejected")
    object.__setattr__(config, "allowed_decisions", allowed_decisions)
    _require_canonical_string(
        "required_human_attestation",
        config.required_human_attestation,
    )
    _require_boundary_statement(config.boundary_statement)


def _validate_record(record: TradeProposalReviewRecord) -> None:
    object.__setattr__(record, "recorded_at", _as_utc(record.recorded_at))
    object.__setattr__(
        record,
        "source_proposal_generated_at",
        _as_utc(record.source_proposal_generated_at),
    )
    for field_name in (
        "review_record_id",
        "review_config_version",
        "source_proposal_packet_id",
        "source_proposal_config_version",
        "source_proposal_fingerprint",
        "source_queue_boundary_statement",
        "source_queue_item_id",
        "source_manual_review_status",
        "source_packet_id",
        "condition_id",
        "token_id",
        "market_slug",
        "market_url",
        "question",
        "outcome_name",
        "strategy_type",
        "side",
        "intended_order_type",
        "exit_rule",
        "thesis",
        "invalidating_conditions",
        "rule_text_hash",
        "resolution_source",
        "reason_trade_could_be_wrong",
        "readiness_summary",
        "risk_summary",
        "evidence_summary",
        "why_in_queue",
        "primary_reason_code",
        "evidence_scope",
        "decision",
        "reviewer_label",
        "review_rationale",
        "human_attestation",
    ):
        _require_canonical_string(field_name, getattr(record, field_name))
    _require_boundary_statement(record.boundary_statement)
    _require_source_proposal_boundary_statement(
        record.source_proposal_boundary_statement,
    )
    if record.record_only is not True:
        raise ValueError("record_only must be True")
    if record.explicit_human_decision is not True:
        raise ValueError("explicit_human_decision must be True")
    if record.source_proposal_only is not True:
        raise ValueError("source_proposal_only must be True")
    if record.source_human_approval_required is not True:
        raise ValueError("source_human_approval_required must be True")
    if record.source_paper_only is not True:
        raise ValueError("source_paper_only must be True")
    if record.source_manual_review_status != "paper_review_ready":
        raise ValueError("source_manual_review_status must be paper_review_ready")
    if record.risk_gate_passed is not True:
        raise ValueError("risk_gate_passed must be True")
    _require_nonnegative_int("hard_block_count", record.hard_block_count)
    if record.hard_block_count != 0:
        raise ValueError("hard_block_count must be zero")
    if record.source_queue_item_id != (
        f"{record.condition_id}:{record.token_id}:{record.source_packet_id}"
    ):
        raise ValueError("source_queue_item_id must match condition_id:token_id:source_packet_id")
    _require_positive_int("source_queue_rank", record.source_queue_rank)
    if record.side not in ("buy", "sell"):
        raise ValueError("side must be buy or sell")
    _require_executable_price(record.executable_price_assumption)
    _require_positive_decimal("maximum_size", record.maximum_size)
    _require_positive_decimal("source_max_executable_size", record.source_max_executable_size)
    if record.maximum_size > record.source_max_executable_size:
        raise ValueError("maximum_size must be less than or equal to source_max_executable_size")
    _require_nonnegative_decimal("cost_adjusted_edge", record.cost_adjusted_edge)
    _require_optional_finite_decimal("theoretical_edge", record.theoretical_edge)
    _require_optional_probability("fair_value_estimate", record.fair_value_estimate)
    _require_optional_probability("model_probability", record.model_probability)
    _require_optional_probability("confidence", record.confidence)
    _require_nonnegative_decimal("source_score", record.source_score)
    _require_optional_finite_decimal("market_score_total", record.market_score_total)
    _require_nonnegative_decimal("exposure_after_trade", record.exposure_after_trade)
    if record.history_status != "paper_review_ready":
        raise ValueError("history_status must be paper_review_ready")
    if record.forecast_status != "paper_review_ready":
        raise ValueError("forecast_status must be paper_review_ready")
    _require_nonnegative_int("history_gate_pass_count", record.history_gate_pass_count)
    _require_nonnegative_int("forecast_gate_pass_count", record.forecast_gate_pass_count)
    _require_nonnegative_int("history_gate_fail_count", record.history_gate_fail_count)
    _require_nonnegative_int("forecast_gate_fail_count", record.forecast_gate_fail_count)
    if record.history_gate_fail_count != 0:
        raise ValueError("history_gate_fail_count must be zero")
    if record.forecast_gate_fail_count != 0:
        raise ValueError("forecast_gate_fail_count must be zero")
    object.__setattr__(record, "risk_tags", _normalize_string_tuple("risk_tags", record.risk_tags))
    object.__setattr__(
        record,
        "supporting_reason_codes",
        _normalize_string_tuple("supporting_reason_codes", record.supporting_reason_codes),
    )
    object.__setattr__(
        record,
        "blocking_reason_codes",
        _normalize_string_tuple("blocking_reason_codes", record.blocking_reason_codes),
    )
    object.__setattr__(
        record,
        "review_focus",
        _normalize_string_tuple("review_focus", record.review_focus),
    )
    object.__setattr__(
        record,
        "review_reason_codes",
        _normalize_string_tuple("review_reason_codes", record.review_reason_codes),
    )
    if not record.risk_tags:
        raise ValueError("risk_tags are required")
    if not record.review_focus:
        raise ValueError("review_focus is required")
    if record.blocking_reason_codes:
        raise ValueError("blocking_reason_codes must be empty")
    if record.decision not in REVIEW_DECISIONS:
        raise ValueError("decision must be approved or rejected")
    if record.decision == "approved" and record.review_reason_codes:
        raise ValueError("review_reason_codes must be empty when decision is approved")
    if record.decision == "rejected" and not record.review_reason_codes:
        raise ValueError("review_reason_codes are required when decision is rejected")
    expected_fingerprint = _source_proposal_fingerprint_from_record(record)
    if record.source_proposal_fingerprint != expected_fingerprint:
        raise ValueError("source_proposal_fingerprint must match source fields")
    expected_id = _review_record_id(
        review_config_version=record.review_config_version,
        recorded_at=record.recorded_at,
        source_proposal_packet_id=record.source_proposal_packet_id,
        source_proposal_fingerprint=record.source_proposal_fingerprint,
        decision=record.decision,
        reviewer_label=record.reviewer_label,
        review_rationale=record.review_rationale,
        review_reason_codes=record.review_reason_codes,
        human_attestation=record.human_attestation,
    )
    if record.review_record_id != expected_id:
        raise ValueError("review_record_id must match record fields")


def _validate_record_tree(record: TradeProposalReviewRecord) -> TradeProposalReviewRecord:
    return TradeProposalReviewRecord(
        review_record_id=record.review_record_id,
        recorded_at=record.recorded_at,
        review_config_version=record.review_config_version,
        record_only=record.record_only,
        explicit_human_decision=record.explicit_human_decision,
        boundary_statement=record.boundary_statement,
        source_proposal_packet_id=record.source_proposal_packet_id,
        source_proposal_generated_at=record.source_proposal_generated_at,
        source_proposal_config_version=record.source_proposal_config_version,
        source_proposal_fingerprint=record.source_proposal_fingerprint,
        source_proposal_boundary_statement=record.source_proposal_boundary_statement,
        source_queue_boundary_statement=record.source_queue_boundary_statement,
        source_proposal_only=record.source_proposal_only,
        source_human_approval_required=record.source_human_approval_required,
        source_queue_item_id=record.source_queue_item_id,
        source_queue_rank=record.source_queue_rank,
        source_manual_review_status=record.source_manual_review_status,
        source_packet_id=record.source_packet_id,
        source_paper_only=record.source_paper_only,
        condition_id=record.condition_id,
        token_id=record.token_id,
        market_slug=record.market_slug,
        market_url=record.market_url,
        question=record.question,
        outcome_name=record.outcome_name,
        strategy_type=record.strategy_type,
        side=record.side,
        intended_order_type=record.intended_order_type,
        executable_price_assumption=record.executable_price_assumption,
        maximum_size=record.maximum_size,
        source_max_executable_size=record.source_max_executable_size,
        cost_adjusted_edge=record.cost_adjusted_edge,
        theoretical_edge=record.theoretical_edge,
        fair_value_estimate=record.fair_value_estimate,
        model_probability=record.model_probability,
        confidence=record.confidence,
        source_score=record.source_score,
        market_score_total=record.market_score_total,
        exposure_after_trade=record.exposure_after_trade,
        exit_rule=record.exit_rule,
        thesis=record.thesis,
        invalidating_conditions=record.invalidating_conditions,
        rule_text_hash=record.rule_text_hash,
        resolution_source=record.resolution_source,
        risk_tags=record.risk_tags,
        reason_trade_could_be_wrong=record.reason_trade_could_be_wrong,
        readiness_summary=record.readiness_summary,
        risk_summary=record.risk_summary,
        evidence_summary=record.evidence_summary,
        why_in_queue=record.why_in_queue,
        primary_reason_code=record.primary_reason_code,
        supporting_reason_codes=record.supporting_reason_codes,
        review_focus=record.review_focus,
        evidence_scope=record.evidence_scope,
        history_status=record.history_status,
        forecast_status=record.forecast_status,
        history_gate_pass_count=record.history_gate_pass_count,
        forecast_gate_pass_count=record.forecast_gate_pass_count,
        history_gate_fail_count=record.history_gate_fail_count,
        forecast_gate_fail_count=record.forecast_gate_fail_count,
        risk_gate_passed=record.risk_gate_passed,
        hard_block_count=record.hard_block_count,
        blocking_reason_codes=record.blocking_reason_codes,
        decision=record.decision,
        reviewer_label=record.reviewer_label,
        review_rationale=record.review_rationale,
        review_reason_codes=record.review_reason_codes,
        human_attestation=record.human_attestation,
    )


def _public_safe_review_payload(record: TradeProposalReviewRecord) -> dict[str, Any]:
    payload = {
        "review_record_id": record.review_record_id,
        "recorded_at": record.recorded_at,
        "review_config_version": record.review_config_version,
        "record_only": record.record_only,
        "explicit_human_decision": record.explicit_human_decision,
        "decision": record.decision,
        "review_reason_codes": record.review_reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "public_export_scope": "public_safe_review_attestation",
    }
    _reject_public_payload_export_fields(payload)
    safe_payload = _json_ready(payload)
    if type(safe_payload) is not dict:
        raise ValueError("public_safe_payload must be a dict")
    return safe_payload


def _reject_public_payload_export_fields(payload: dict[str, Any]) -> None:
    forbidden_fields = {
        "condition_id",
        "token_id",
        "market_slug",
        "question",
        "side",
        "intended_order_type",
        "maximum_size",
        "source_max_executable_size",
        "order",
        "trade",
        "size",
    }
    leaked_fields = sorted(forbidden_fields.intersection(payload))
    if leaked_fields:
        raise ValueError(
            "public_safe_payload must not include trade proposal fields: "
            + ", ".join(leaked_fields),
        )


def _validate_ephemeral_review_log_scope(log: TradeProposalReviewLog) -> None:
    if log.storage_scope != "ephemeral_local_review_log":
        raise ValueError("storage_scope must be ephemeral_local_review_log")
    if log.durable_memory is not False:
        raise ValueError("durable_memory must be False")
    if log.public_output is not False:
        raise ValueError("public_output must be False")


def _source_proposal_fingerprint(source: TradeProposalPacket) -> str:
    return _source_proposal_fingerprint_from_values(_source_fields_from_proposal(source))


def _source_proposal_fingerprint_from_record(record: TradeProposalReviewRecord) -> str:
    return _source_proposal_fingerprint_from_values(
        {field_name: getattr(record, field_name) for field_name in SOURCE_FINGERPRINT_FIELDS}
    )


def _source_proposal_fingerprint_from_values(values: dict[str, Any]) -> str:
    raw = json.dumps(
        _json_ready(values),
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"source-proposal-{digest}"


def _source_fields_from_proposal(source: TradeProposalPacket) -> dict[str, Any]:
    return {
        "source_proposal_packet_id": source.proposal_packet_id,
        "source_proposal_generated_at": source.generated_at,
        "source_proposal_config_version": source.proposal_config_version,
        "source_proposal_boundary_statement": source.boundary_statement,
        "source_queue_boundary_statement": source.source_boundary_statement,
        "source_proposal_only": source.proposal_only,
        "source_human_approval_required": source.human_approval_required,
        "source_queue_item_id": source.source_queue_item_id,
        "source_queue_rank": source.source_queue_rank,
        "source_manual_review_status": source.source_manual_review_status,
        "source_packet_id": source.source_packet_id,
        "source_paper_only": source.source_paper_only,
        "condition_id": source.condition_id,
        "token_id": source.token_id,
        "market_slug": source.market_slug,
        "market_url": source.market_url,
        "question": source.question,
        "outcome_name": source.outcome_name,
        "strategy_type": source.strategy_type,
        "side": source.side,
        "intended_order_type": source.intended_order_type,
        "executable_price_assumption": source.executable_price_assumption,
        "maximum_size": source.maximum_size,
        "source_max_executable_size": source.source_max_executable_size,
        "cost_adjusted_edge": source.cost_adjusted_edge,
        "theoretical_edge": source.theoretical_edge,
        "fair_value_estimate": source.fair_value_estimate,
        "model_probability": source.model_probability,
        "confidence": source.confidence,
        "source_score": source.source_score,
        "market_score_total": source.market_score_total,
        "exposure_after_trade": source.exposure_after_trade,
        "exit_rule": source.exit_rule,
        "thesis": source.thesis,
        "invalidating_conditions": source.invalidating_conditions,
        "rule_text_hash": source.rule_text_hash,
        "resolution_source": source.resolution_source,
        "risk_tags": source.risk_tags,
        "reason_trade_could_be_wrong": source.reason_trade_could_be_wrong,
        "readiness_summary": source.readiness_summary,
        "risk_summary": source.risk_summary,
        "evidence_summary": source.evidence_summary,
        "why_in_queue": source.why_in_queue,
        "primary_reason_code": source.primary_reason_code,
        "supporting_reason_codes": source.supporting_reason_codes,
        "review_focus": source.review_focus,
        "evidence_scope": source.evidence_scope,
        "history_status": source.history_status,
        "forecast_status": source.forecast_status,
        "history_gate_pass_count": source.history_gate_pass_count,
        "forecast_gate_pass_count": source.forecast_gate_pass_count,
        "history_gate_fail_count": source.history_gate_fail_count,
        "forecast_gate_fail_count": source.forecast_gate_fail_count,
        "risk_gate_passed": source.risk_gate_passed,
        "hard_block_count": source.hard_block_count,
        "blocking_reason_codes": source.blocking_reason_codes,
    }


def _review_record_id(
    *,
    review_config_version: str,
    recorded_at: datetime,
    source_proposal_packet_id: str,
    source_proposal_fingerprint: str,
    decision: str,
    reviewer_label: str,
    review_rationale: str,
    review_reason_codes: tuple[str, ...],
    human_attestation: str,
) -> str:
    raw = json.dumps(
        _json_ready(
            {
                "review_config_version": review_config_version,
                "recorded_at": recorded_at,
                "source_proposal_packet_id": source_proposal_packet_id,
                "source_proposal_fingerprint": source_proposal_fingerprint,
                "decision": decision,
                "reviewer_label": reviewer_label,
                "review_rationale": review_rationale,
                "review_reason_codes": review_reason_codes,
                "human_attestation": human_attestation,
            }
        ),
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"review-{digest}"


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
        "record-only",
        "human-review decision",
        "not an approval workflow",
        "trade instruction",
        "order instruction",
        "broker request",
        "order request",
        "account action",
        "account authentication",
        "private-key handling",
        "wallet signature",
        "live-execution signal",
        "credential workflow",
        "manual execution import",
        "automatic order-placement authorization",
    )
    if any(part not in lowered for part in required_parts):
        raise ValueError("boundary_statement must describe record-only human review")


def _require_source_proposal_boundary_statement(value: str) -> None:
    _require_canonical_string("source_proposal_boundary_statement", value)
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
        raise ValueError("source_proposal_boundary_statement must describe proposal-only review")


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
