"""Pure reducer for strategy news and evidence quality reconciliation."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_STRATEGY_NEWS_EVIDENCE_RECONCILIATION_CONFIG_VERSION = (
    "research-strategy-news-evidence-reconciliation-v1"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIX = Decimal("6.000000")
_SECONDS_PER_MINUTE = Decimal("60.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("pass", "watch", "block")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_HEX_CHARS = frozenset("0123456789abcdef")
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_BLOCK_REASONS = frozenset(
    (
        "news_freshness_block",
        "source_class_quorum_block",
        "claim_consistency_block",
        "contradiction_pressure_block",
        "specialist_review_age_block",
        "manual_escalation_urgency_block",
    ),
)
_PASS_REASONS = frozenset(("news_evidence_reconciliation_pass",))
_REASON_PRIORITY = (
    "news_freshness_block",
    "news_freshness_watch",
    "source_class_quorum_block",
    "source_class_quorum_watch",
    "claim_consistency_block",
    "claim_consistency_watch",
    "contradiction_pressure_block",
    "contradiction_pressure_watch",
    "specialist_review_age_block",
    "specialist_review_age_watch",
    "manual_escalation_urgency_block",
    "manual_escalation_urgency_watch",
    "news_evidence_reconciliation_pass",
    "news_evidence_reconciliation_empty",
)
_UNSAFE_KEY_FRAGMENTS = (
    "private",
    "candidate",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_url",
    "source_text",
    "url",
    "dsn",
    "table",
    "tok" "en",
    "sec" "ret",
)
_UNSAFE_TEXT_FRAGMENTS = (
    "://",
    "tok" "en",
    "sec" "ret",
    "pass" "word",
    "cred" "ential",
    "private" "_" "key",
    "api" "_" "key",
    "bear" "er",
    "wal" "let",
    "au" "th",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "sign" "ing",
    "data" "base",
    "net" "work",
    "dsn",
)


@dataclass(frozen=True)
class ResearchStrategyNewsEvidenceReconciliationConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_NEWS_EVIDENCE_RECONCILIATION_CONFIG_VERSION
    )
    news_watch_age_minutes: Decimal = Decimal("60.000000")
    news_block_age_minutes: Decimal = Decimal("180.000000")
    source_class_pass_floor: Decimal = Decimal("3")
    source_class_block_floor: Decimal = Decimal("2")
    claim_consistency_watch_floor: Decimal = Decimal("0.750000")
    claim_consistency_block_floor: Decimal = Decimal("0.500000")
    contradiction_pressure_watch_threshold: Decimal = Decimal("0.250000")
    contradiction_pressure_block_threshold: Decimal = Decimal("0.600000")
    specialist_review_watch_age_minutes: Decimal = Decimal("120.000000")
    specialist_review_block_age_minutes: Decimal = Decimal("360.000000")
    manual_escalation_watch_urgency: Decimal = Decimal("0.500000")
    manual_escalation_block_urgency: Decimal = Decimal("0.900000")
    manual_escalation_window_minutes: Decimal = Decimal("120.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "news_watch_age_minutes",
            "news_block_age_minutes",
            "specialist_review_watch_age_minutes",
            "specialist_review_block_age_minutes",
            "manual_escalation_window_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_class_pass_floor", "source_class_block_floor"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "claim_consistency_watch_floor",
            "claim_consistency_block_floor",
            "contradiction_pressure_watch_threshold",
            "contradiction_pressure_block_threshold",
            "manual_escalation_watch_urgency",
            "manual_escalation_block_urgency",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.news_watch_age_minutes > self.news_block_age_minutes:
            raise ValueError("news watch age must not exceed block age")
        if self.source_class_block_floor > self.source_class_pass_floor:
            raise ValueError("source_class_block_floor must not exceed pass floor")
        if self.claim_consistency_block_floor > self.claim_consistency_watch_floor:
            raise ValueError("claim consistency block floor must not exceed watch floor")
        if (
            self.contradiction_pressure_watch_threshold
            > self.contradiction_pressure_block_threshold
        ):
            raise ValueError("contradiction watch threshold must not exceed block threshold")
        if (
            self.specialist_review_watch_age_minutes
            > self.specialist_review_block_age_minutes
        ):
            raise ValueError("specialist review watch age must not exceed block age")
        if self.manual_escalation_watch_urgency > self.manual_escalation_block_urgency:
            raise ValueError("manual escalation watch urgency must not exceed block urgency")
        require_paper_only_flags("news evidence config", self)


@dataclass(frozen=True)
class ResearchStrategyNewsEvidenceReconciliationInput:
    private_candidate_reference: str
    private_market_reference: str
    private_market_question: str
    private_source_reference: str
    private_source_text: str
    latest_news_at: datetime
    source_class_count: Decimal
    claim_count: Decimal
    consistent_claim_count: Decimal
    contradicted_claim_count: Decimal
    unresolved_contradiction_count: Decimal
    specialist_reviewed_at: datetime | None
    manual_escalation_due_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_market_question",
            "private_source_reference",
            "private_source_text",
        ):
            _require_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "latest_news_at", _as_utc("latest_news_at", self.latest_news_at))
        for field_name in (
            "source_class_count",
            "consistent_claim_count",
            "contradicted_claim_count",
            "unresolved_contradiction_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "claim_count",
            _normalize_positive_count("claim_count", self.claim_count),
        )
        if self.consistent_claim_count > self.claim_count:
            raise ValueError("consistent_claim_count must not exceed claim_count")
        if self.contradicted_claim_count > self.claim_count:
            raise ValueError("contradicted_claim_count must not exceed claim_count")
        if self.unresolved_contradiction_count > self.contradicted_claim_count:
            raise ValueError(
                "unresolved_contradiction_count must not exceed contradicted_claim_count",
            )
        if self.specialist_reviewed_at is not None:
            object.__setattr__(
                self,
                "specialist_reviewed_at",
                _as_utc("specialist_reviewed_at", self.specialist_reviewed_at),
            )
        if self.manual_escalation_due_at is not None:
            object.__setattr__(
                self,
                "manual_escalation_due_at",
                _as_utc("manual_escalation_due_at", self.manual_escalation_due_at),
            )
        require_paper_only_flags("news evidence input", self)


@dataclass(frozen=True)
class ResearchStrategyNewsEvidenceReconciliationResult:
    aggregate_row_number: Decimal
    evidence_group_hash: str
    source_bundle_hash: str
    news_age_minutes: Decimal
    news_freshness_score: Decimal
    source_class_count: Decimal
    source_class_quorum_score: Decimal
    claim_count: Decimal
    claim_consistency_ratio: Decimal
    contradiction_pressure: Decimal
    specialist_review_age_minutes: Decimal | None
    specialist_review_freshness_score: Decimal
    manual_escalation_urgency: Decimal
    reconciliation_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_count("aggregate_row_number", self.aggregate_row_number),
        )
        _require_digest("evidence_group_hash", self.evidence_group_hash)
        _require_digest("source_bundle_hash", self.source_bundle_hash)
        for field_name in ("news_age_minutes",):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("source_class_count", "claim_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.claim_count == _ZERO:
            raise ValueError("claim_count must be positive")
        for field_name in (
            "news_freshness_score",
            "source_class_quorum_score",
            "claim_consistency_ratio",
            "contradiction_pressure",
            "specialist_review_freshness_score",
            "manual_escalation_urgency",
            "reconciliation_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.specialist_review_age_minutes is not None:
            object.__setattr__(
                self,
                "specialist_review_age_minutes",
                _normalize_nonnegative_decimal(
                    "specialist_review_age_minutes",
                    self.specialist_review_age_minutes,
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_result_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_result(self)
        require_paper_only_flags("news evidence result", self)


@dataclass(frozen=True)
class ResearchStrategyNewsEvidenceReconciliationReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_reconciliation_quality_score: Decimal | None
    max_contradiction_pressure: Decimal | None
    max_manual_escalation_urgency: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    results: tuple[ResearchStrategyNewsEvidenceReconciliationResult, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_reconciliation_quality_score",
            "max_contradiction_pressure",
            "max_manual_escalation_urgency",
        ):
            field_value = getattr(self, field_name)
            if field_value is not None:
                object.__setattr__(
                    self,
                    field_name,
                    _normalize_unit_decimal(field_name, field_value),
                )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "results", _normalize_results(self.results))
        _require_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        require_paper_only_flags("news evidence report", self)


def build_research_strategy_news_evidence_reconciliation_report(
    items: Iterable[ResearchStrategyNewsEvidenceReconciliationInput],
    *,
    config: ResearchStrategyNewsEvidenceReconciliationConfig,
    generated_at: datetime,
) -> ResearchStrategyNewsEvidenceReconciliationReport:
    if type(config) is not ResearchStrategyNewsEvidenceReconciliationConfig:
        raise ValueError(
            "config must be a ResearchStrategyNewsEvidenceReconciliationConfig",
        )
    require_paper_only_flags("news evidence config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_inputs(items)
    drafts = tuple(
        _result_from_input(item, config=config, generated_at=generated_at_utc)
        for item in normalized_items
    )
    results = tuple(
        _renumber_result(row, _count(index))
        for index, row in enumerate(sorted(drafts, key=_result_sort_key), start=1)
    )
    item_count = _count(len(results))
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "item_count": item_count,
        "pass_count": _result_status_count(results, "pass"),
        "watch_count": _result_status_count(results, "watch"),
        "block_count": _result_status_count(results, "block"),
        "average_reconciliation_quality_score": (
            None
            if not results
            else _ratio(
                sum(row.reconciliation_quality_score for row in results),
                item_count,
            )
        ),
        "max_contradiction_pressure": (
            None if not results else max(row.contradiction_pressure for row in results)
        ),
        "max_manual_escalation_urgency": (
            None if not results else max(row.manual_escalation_urgency for row in results)
        ),
        "status": _report_status(results),
        "reason_codes": _report_reason_codes(results),
        "results": results,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyNewsEvidenceReconciliationReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_news_evidence_reconciliation_report_payload(
    report: ResearchStrategyNewsEvidenceReconciliationReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyNewsEvidenceReconciliationReport:
        require_paper_only_flags("news evidence report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyNewsEvidenceReconciliationReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    require_paper_only_flags("news evidence payload", _PayloadFlags(payload))
    _validate_payload_statuses(payload)
    _validate_payload_digests(payload)
    return payload


@dataclass(frozen=True)
class _PayloadFlags:
    payload: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.payload.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.payload.get("report_only")

    @property
    def readonly(self) -> object:
        return self.payload.get("readonly")


def _normalize_inputs(
    items: Iterable[ResearchStrategyNewsEvidenceReconciliationInput],
) -> tuple[ResearchStrategyNewsEvidenceReconciliationInput, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyNewsEvidenceReconciliationInput:
            raise ValueError(
                "items must contain ResearchStrategyNewsEvidenceReconciliationInput",
            )
        require_paper_only_flags("news evidence input", item)
        fingerprint = _input_fingerprint(item)
        if fingerprint in seen:
            raise ValueError("input fingerprints must be unique")
        seen.add(fingerprint)
    return normalized


def _result_from_input(
    item: ResearchStrategyNewsEvidenceReconciliationInput,
    *,
    config: ResearchStrategyNewsEvidenceReconciliationConfig,
    generated_at: datetime,
) -> ResearchStrategyNewsEvidenceReconciliationResult:
    if item.latest_news_at > generated_at:
        raise ValueError("latest_news_at must not be after generated_at")
    news_age_minutes = _age_minutes(generated_at, item.latest_news_at)
    news_freshness_score = _freshness_score(news_age_minutes, config.news_block_age_minutes)
    source_class_quorum_score = _capped_ratio(
        item.source_class_count,
        config.source_class_pass_floor,
    )
    claim_consistency_ratio = _ratio(item.consistent_claim_count, item.claim_count)
    contradiction_pressure = _ratio(item.contradicted_claim_count, item.claim_count)
    if item.specialist_reviewed_at is None:
        specialist_review_age_minutes = None
        specialist_review_freshness_score = _ZERO
    else:
        if item.specialist_reviewed_at > generated_at:
            raise ValueError("specialist_reviewed_at must not be after generated_at")
        specialist_review_age_minutes = _age_minutes(
            generated_at,
            item.specialist_reviewed_at,
        )
        specialist_review_freshness_score = _freshness_score(
            specialist_review_age_minutes,
            config.specialist_review_block_age_minutes,
        )
    manual_escalation_urgency = _manual_escalation_urgency(
        generated_at=generated_at,
        due_at=item.manual_escalation_due_at,
        window_minutes=config.manual_escalation_window_minutes,
    )
    reason_codes = _result_reason_codes(
        news_age_minutes=news_age_minutes,
        source_class_count=item.source_class_count,
        claim_consistency_ratio=claim_consistency_ratio,
        contradiction_pressure=contradiction_pressure,
        specialist_review_age_minutes=specialist_review_age_minutes,
        manual_escalation_urgency=manual_escalation_urgency,
        config=config,
    )
    result_values = {
        "aggregate_row_number": _ONE,
        "evidence_group_hash": _hash_private_values(
            item.private_candidate_reference,
            item.private_market_reference,
            item.private_market_question,
        ),
        "source_bundle_hash": _hash_private_values(
            item.private_source_reference,
            item.private_source_text,
        ),
        "news_age_minutes": news_age_minutes,
        "news_freshness_score": news_freshness_score,
        "source_class_count": item.source_class_count,
        "source_class_quorum_score": source_class_quorum_score,
        "claim_count": item.claim_count,
        "claim_consistency_ratio": claim_consistency_ratio,
        "contradiction_pressure": contradiction_pressure,
        "specialist_review_age_minutes": specialist_review_age_minutes,
        "specialist_review_freshness_score": specialist_review_freshness_score,
        "manual_escalation_urgency": manual_escalation_urgency,
        "reconciliation_quality_score": _quality_score(
            news_freshness_score=news_freshness_score,
            source_class_quorum_score=source_class_quorum_score,
            claim_consistency_ratio=claim_consistency_ratio,
            contradiction_pressure=contradiction_pressure,
            specialist_review_freshness_score=specialist_review_freshness_score,
            manual_escalation_urgency=manual_escalation_urgency,
        ),
        "status": _status_from_reasons(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyNewsEvidenceReconciliationResult(
        **result_values,
        validation_digest=_validation_digest(_row_digest_values_from_dict(result_values)),
    )


def _renumber_result(
    row: ResearchStrategyNewsEvidenceReconciliationResult,
    aggregate_row_number: Decimal,
) -> ResearchStrategyNewsEvidenceReconciliationResult:
    return ResearchStrategyNewsEvidenceReconciliationResult(
        aggregate_row_number=aggregate_row_number,
        evidence_group_hash=row.evidence_group_hash,
        source_bundle_hash=row.source_bundle_hash,
        news_age_minutes=row.news_age_minutes,
        news_freshness_score=row.news_freshness_score,
        source_class_count=row.source_class_count,
        source_class_quorum_score=row.source_class_quorum_score,
        claim_count=row.claim_count,
        claim_consistency_ratio=row.claim_consistency_ratio,
        contradiction_pressure=row.contradiction_pressure,
        specialist_review_age_minutes=row.specialist_review_age_minutes,
        specialist_review_freshness_score=row.specialist_review_freshness_score,
        manual_escalation_urgency=row.manual_escalation_urgency,
        reconciliation_quality_score=row.reconciliation_quality_score,
        status=row.status,
        reason_codes=row.reason_codes,
        validation_digest=row.validation_digest,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )


def _result_reason_codes(
    *,
    news_age_minutes: Decimal,
    source_class_count: Decimal,
    claim_consistency_ratio: Decimal,
    contradiction_pressure: Decimal,
    specialist_review_age_minutes: Decimal | None,
    manual_escalation_urgency: Decimal,
    config: ResearchStrategyNewsEvidenceReconciliationConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if news_age_minutes > config.news_block_age_minutes:
        reasons.append("news_freshness_block")
    elif news_age_minutes > config.news_watch_age_minutes:
        reasons.append("news_freshness_watch")
    if source_class_count < config.source_class_block_floor:
        reasons.append("source_class_quorum_block")
    elif source_class_count < config.source_class_pass_floor:
        reasons.append("source_class_quorum_watch")
    if claim_consistency_ratio < config.claim_consistency_block_floor:
        reasons.append("claim_consistency_block")
    elif claim_consistency_ratio < config.claim_consistency_watch_floor:
        reasons.append("claim_consistency_watch")
    if contradiction_pressure >= config.contradiction_pressure_block_threshold:
        reasons.append("contradiction_pressure_block")
    elif contradiction_pressure >= config.contradiction_pressure_watch_threshold:
        reasons.append("contradiction_pressure_watch")
    if specialist_review_age_minutes is None:
        reasons.append("specialist_review_age_block")
    elif specialist_review_age_minutes > config.specialist_review_block_age_minutes:
        reasons.append("specialist_review_age_block")
    elif specialist_review_age_minutes > config.specialist_review_watch_age_minutes:
        reasons.append("specialist_review_age_watch")
    if manual_escalation_urgency >= config.manual_escalation_block_urgency:
        reasons.append("manual_escalation_urgency_block")
    elif manual_escalation_urgency >= config.manual_escalation_watch_urgency:
        reasons.append("manual_escalation_urgency_watch")
    if not reasons:
        return ("news_evidence_reconciliation_pass",)
    return tuple(sorted(reasons, key=_reason_key))


def _manual_escalation_urgency(
    *,
    generated_at: datetime,
    due_at: datetime | None,
    window_minutes: Decimal,
) -> Decimal:
    if due_at is None:
        return _ONE
    minutes_until_due = _signed_minutes(due_at, generated_at)
    if minutes_until_due <= _ZERO:
        return _ONE
    if minutes_until_due >= window_minutes:
        return _ZERO
    return _quantize(_ONE - _ratio(minutes_until_due, window_minutes))


def _quality_score(
    *,
    news_freshness_score: Decimal,
    source_class_quorum_score: Decimal,
    claim_consistency_ratio: Decimal,
    contradiction_pressure: Decimal,
    specialist_review_freshness_score: Decimal,
    manual_escalation_urgency: Decimal,
) -> Decimal:
    return _ratio(
        news_freshness_score
        + source_class_quorum_score
        + claim_consistency_ratio
        + (_ONE - contradiction_pressure)
        + specialist_review_freshness_score
        + (_ONE - manual_escalation_urgency),
        _SIX,
    )


def _freshness_score(age_minutes: Decimal, block_age_minutes: Decimal) -> Decimal:
    if age_minutes >= block_age_minutes:
        return _ZERO
    return _quantize(_ONE - _ratio(age_minutes, block_age_minutes))


def _report_status(
    results: tuple[ResearchStrategyNewsEvidenceReconciliationResult, ...],
) -> str:
    if not results:
        return "block"
    if any(row.status == "block" for row in results):
        return "block"
    if any(row.status == "watch" for row in results):
        return "watch"
    return "pass"


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes != ("news_evidence_reconciliation_pass",):
        return "watch"
    return "pass"


def _report_reason_codes(
    results: tuple[ResearchStrategyNewsEvidenceReconciliationResult, ...],
) -> tuple[str, ...]:
    if not results:
        return ("news_evidence_reconciliation_empty",)
    reasons = tuple(
        sorted(
            {
                reason
                for row in results
                for reason in row.reason_codes
            },
            key=_reason_key,
        ),
    )
    if reasons:
        return reasons
    return ("news_evidence_reconciliation_pass",)


def _result_status_count(
    results: tuple[ResearchStrategyNewsEvidenceReconciliationResult, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in results if row.status == status))


def _normalize_results(
    results: object,
) -> tuple[ResearchStrategyNewsEvidenceReconciliationResult, ...]:
    if isinstance(results, (str, bytes)):
        raise ValueError("results must be an iterable")
    try:
        normalized = tuple(results)
    except TypeError as exc:
        raise ValueError("results must be an iterable") from exc
    seen_keys: set[tuple[int, str, str]] = set()
    for index, row in enumerate(normalized, start=1):
        if type(row) is not ResearchStrategyNewsEvidenceReconciliationResult:
            raise ValueError(
                "results must contain ResearchStrategyNewsEvidenceReconciliationResult",
            )
        if row.aggregate_row_number != _count(index):
            raise ValueError("results must be sorted deterministically")
        row_key = _result_sort_key(row)
        if row_key in seen_keys:
            raise ValueError("results must be sorted deterministically")
        seen_keys.add(row_key)
    if normalized != tuple(sorted(normalized, key=_result_sort_key)):
        raise ValueError("results must be sorted deterministically")
    return normalized


def _validate_result(row: ResearchStrategyNewsEvidenceReconciliationResult) -> None:
    expected_score = _quality_score(
        news_freshness_score=row.news_freshness_score,
        source_class_quorum_score=row.source_class_quorum_score,
        claim_consistency_ratio=row.claim_consistency_ratio,
        contradiction_pressure=row.contradiction_pressure,
        specialist_review_freshness_score=row.specialist_review_freshness_score,
        manual_escalation_urgency=row.manual_escalation_urgency,
    )
    if row.reconciliation_quality_score != expected_score:
        raise ValueError("reconciliation_quality_score must match component scores")
    if row.status != _status_from_reasons(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchStrategyNewsEvidenceReconciliationReport) -> None:
    if report.item_count != _count(len(report.results)):
        raise ValueError("item_count must match results")
    if report.pass_count != _result_status_count(report.results, "pass"):
        raise ValueError("pass_count must match results")
    if report.watch_count != _result_status_count(report.results, "watch"):
        raise ValueError("watch_count must match results")
    if report.block_count != _result_status_count(report.results, "block"):
        raise ValueError("block_count must match results")
    if report.results:
        expected_average = _ratio(
            sum(row.reconciliation_quality_score for row in report.results),
            report.item_count,
        )
        expected_max_pressure = max(row.contradiction_pressure for row in report.results)
        expected_max_urgency = max(row.manual_escalation_urgency for row in report.results)
    else:
        expected_average = None
        expected_max_pressure = None
        expected_max_urgency = None
    if report.average_reconciliation_quality_score != expected_average:
        raise ValueError("average_reconciliation_quality_score must match results")
    if report.max_contradiction_pressure != expected_max_pressure:
        raise ValueError("max_contradiction_pressure must match results")
    if report.max_manual_escalation_urgency != expected_max_urgency:
        raise ValueError("max_manual_escalation_urgency must match results")
    if report.status != _report_status(report.results):
        raise ValueError("status must match results")
    if report.reason_codes != _report_reason_codes(report.results):
        raise ValueError("reason_codes must match results")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _validate_payload_statuses(payload: dict[str, Any]) -> None:
    status = payload.get("status")
    if status not in _STATUSES:
        raise ValueError("status must be pass, watch, or block")
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("results must be a list")
    for row in results:
        if type(row) is not dict:
            raise ValueError("results must contain objects")
        row_status = row.get("status")
        if row_status not in _STATUSES:
            raise ValueError("status must be pass, watch, or block")


def _validate_payload_digests(payload: dict[str, Any]) -> None:
    results = payload.get("results")
    if not isinstance(results, list):
        raise ValueError("results must be a list")
    for row in results:
        if type(row) is not dict:
            raise ValueError("results must contain objects")
        digest = row.get("validation_digest")
        if type(digest) is not str:
            raise ValueError("validation_digest must be a sha256 hex digest")
        _require_digest("validation_digest", digest)
        if digest != _validation_digest(_row_digest_values_from_dict(row)):
            raise ValueError("validation_digest must match row payload")
    report_digest = payload.get("validation_digest")
    if type(report_digest) is not str:
        raise ValueError("validation_digest must be a sha256 hex digest")
    _require_digest("validation_digest", report_digest)
    if report_digest != _validation_digest(_report_digest_values_from_dict(payload)):
        raise ValueError("validation_digest must match report payload")


def _result_sort_key(
    row: ResearchStrategyNewsEvidenceReconciliationResult,
) -> tuple[int, str, str]:
    return (
        _STATUS_WEIGHT[row.status],
        row.evidence_group_hash,
        row.source_bundle_hash,
    )


def _reason_key(reason_code: str) -> tuple[int, str]:
    try:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    except ValueError:
        return (len(_REASON_PRIORITY), reason_code)


def _row_digest_values(row: ResearchStrategyNewsEvidenceReconciliationResult) -> dict[str, Any]:
    return _row_digest_values_from_dict(asdict(row))


def _row_digest_values_from_dict(values: dict[str, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, value in values.items():
        if key in {"aggregate_row_number", "validation_digest"}:
            continue
        ready[key] = value
    return ready


def _report_digest_values(report: ResearchStrategyNewsEvidenceReconciliationReport) -> dict[str, Any]:
    return _report_digest_values_from_dict(asdict(report))


def _report_digest_values_from_dict(values: dict[str, Any]) -> dict[str, Any]:
    ready: dict[str, Any] = {}
    for key, value in values.items():
        if key == "validation_digest":
            continue
        ready[key] = value
    return ready


def _age_minutes(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    value = Decimal(str(delta.total_seconds())) / _SECONDS_PER_MINUTE
    return _normalize_nonnegative_decimal("age_minutes", _quantize(value))


def _signed_minutes(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    value = Decimal(str(delta.total_seconds())) / _SECONDS_PER_MINUTE
    return _quantize(value)


def _input_fingerprint(item: ResearchStrategyNewsEvidenceReconciliationInput) -> str:
    return _hash_private_values(
        item.private_candidate_reference,
        item.private_market_reference,
        item.private_market_question,
        item.private_source_reference,
        item.private_source_text,
    )


def _hash_private_values(*values: str) -> str:
    encoded = json.dumps(tuple(values), sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an integer")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > _ONE:
        return _ONE
    return value


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _normalize_positive_count(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return value.quantize(_COUNT_QUANTUM)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return decimal_value


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    if value < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(value)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(name, value)
    if decimal_value > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)


def _normalize_result_reason_codes(name: str, value: object) -> tuple[str, ...]:
    reasons = _normalize_reason_codes(name, value)
    if not reasons:
        raise ValueError(f"{name} must not be empty")
    if reasons != tuple(sorted(reasons, key=_reason_key)):
        raise ValueError(f"{name} must use deterministic sequence")
    if any(reason in _PASS_REASONS for reason in reasons) and len(reasons) > 1:
        raise ValueError(f"{name} pass reason must stand alone")
    return reasons


def _normalize_report_reason_codes(name: str, value: object) -> tuple[str, ...]:
    reasons = _normalize_reason_codes(name, value)
    if not reasons:
        raise ValueError(f"{name} must not be empty")
    if reasons != tuple(sorted(reasons, key=_reason_key)):
        raise ValueError(f"{name} must use deterministic sequence")
    return reasons


def _normalize_reason_codes(name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        items = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    normalized = tuple(_require_public_text(name, item) for item in items)
    if len(normalized) != len(set(normalized)):
        raise ValueError(f"{name} must be unique")
    return normalized


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> None:
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_digest(name: str, value: object) -> None:
    _require_public_text(name, value)
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_public_text(name: str, value: object) -> str:
    text = _require_text(name, value)
    if _has_unsafe_text(text):
        raise ValueError(f"{name} contains unsafe public text")
    return text


def _require_text(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")
    return value


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("numeric values must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime values must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric values must be Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_key(key):
                raise ValueError("unsafe field in public payload")
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str and _has_unsafe_text(value):
        raise ValueError("unsafe value in public payload")


def _has_unsafe_key(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_KEY_FRAGMENTS)


def _has_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_NEWS_EVIDENCE_RECONCILIATION_CONFIG_VERSION",
    "ResearchStrategyNewsEvidenceReconciliationConfig",
    "ResearchStrategyNewsEvidenceReconciliationInput",
    "ResearchStrategyNewsEvidenceReconciliationReport",
    "ResearchStrategyNewsEvidenceReconciliationResult",
    "build_research_strategy_news_evidence_reconciliation_report",
    "research_strategy_news_evidence_reconciliation_report_payload",
)
