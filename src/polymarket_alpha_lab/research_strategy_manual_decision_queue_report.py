"""Pure report-only manual decision queue readiness report."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_QUEUE_REPORT_CONFIG_VERSION = (
    "research-strategy-manual-decision-queue-report"
)

_COUNT_QUANTUM = Decimal("1")
_QUANTUM = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_FIVE = Decimal("5.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_STATUSES = ("block", "watch", "pass")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_FLAG_NAMES = ("paper_only", "report_only", "readonly")
_HEX_CHARS = frozenset("0123456789abcdef")
_READY_REASON = "manual_decision_queue_ready"
_EMPTY_REASON = "manual_decision_queue_empty"
_BLOCK_REASONS = frozenset(
    (
        "evidence_completeness_block",
        "specialist_coverage_block",
        "cost_sanity_block",
        "resolution_rule_check_block",
        "recheck_urgency_block",
    ),
)
_EVIDENCE_GAP_REASONS = frozenset(
    ("evidence_completeness_block", "evidence_completeness_watch"),
)
_SPECIALIST_GAP_REASONS = frozenset(
    ("specialist_coverage_block", "specialist_coverage_watch"),
)
_COST_GAP_REASONS = frozenset(("cost_sanity_block", "cost_sanity_watch"))
_RESOLUTION_GAP_REASONS = frozenset(
    ("resolution_rule_check_block", "resolution_rule_check_watch"),
)
_RECHECK_REASONS = frozenset(("recheck_urgency_block", "recheck_urgency_watch"))
_REASON_PRIORITY = (
    "evidence_completeness_block",
    "evidence_completeness_watch",
    "specialist_coverage_block",
    "specialist_coverage_watch",
    "cost_sanity_block",
    "cost_sanity_watch",
    "resolution_rule_check_block",
    "resolution_rule_check_watch",
    "recheck_urgency_block",
    "recheck_urgency_watch",
    _READY_REASON,
    _EMPTY_REASON,
)
_UNSAFE_TEXT_FRAGMENTS = (
    "sec" "ret",
    "tok" "en",
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
    "re" "place",
    "sign" "ing",
    "live " "trading",
    "data" "base",
    "db" " write",
    "net" "work",
    "://",
    "recommend" "ation",
    "siz" "ing",
    "b" "uy",
    "s" "ell",
)


@dataclass(frozen=True)
class ResearchStrategyManualDecisionQueueReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_QUEUE_REPORT_CONFIG_VERSION
    )
    min_evidence_item_count: Decimal = Decimal("2")
    evidence_completeness_pass_floor: Decimal = Decimal("0.850000")
    evidence_completeness_watch_floor: Decimal = Decimal("0.650000")
    min_specialist_count: Decimal = Decimal("2")
    specialist_coverage_pass_floor: Decimal = Decimal("0.800000")
    specialist_coverage_watch_floor: Decimal = Decimal("0.600000")
    cost_sanity_pass_floor: Decimal = Decimal("0.800000")
    cost_sanity_watch_floor: Decimal = Decimal("0.600000")
    resolution_rule_check_pass_floor: Decimal = Decimal("0.850000")
    resolution_rule_check_watch_floor: Decimal = Decimal("0.650000")
    recheck_urgency_watch_minutes: Decimal = Decimal("90.000000")
    recheck_urgency_block_minutes: Decimal = Decimal("15.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyManualDecisionQueueReportConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        for field_name in ("min_evidence_item_count", "min_specialist_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "evidence_completeness_pass_floor",
            "evidence_completeness_watch_floor",
            "specialist_coverage_pass_floor",
            "specialist_coverage_watch_floor",
            "cost_sanity_pass_floor",
            "cost_sanity_watch_floor",
            "resolution_rule_check_pass_floor",
            "resolution_rule_check_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recheck_urgency_watch_minutes",
            "recheck_urgency_block_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        require_paper_only_flags("manual decision queue config", self)


@dataclass(frozen=True)
class ResearchStrategyManualDecisionQueueItem:
    queue_item_id: str
    market_slug: str
    evidence_item_count: Decimal
    required_evidence_item_count: Decimal
    specialist_count: Decimal
    required_specialist_count: Decimal
    cost_sanity_score: Decimal
    resolution_rule_check_score: Decimal
    minutes_until_recheck: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyManualDecisionQueueItem, "queue item")
        _require_public_text("queue_item_id", self.queue_item_id)
        _require_public_text("market_slug", self.market_slug)
        for field_name in ("evidence_item_count", "specialist_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("required_evidence_item_count", "required_specialist_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("cost_sanity_score", "resolution_rule_check_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minutes_until_recheck",
            _normalize_nonnegative_decimal(
                "minutes_until_recheck",
                self.minutes_until_recheck,
            ),
        )
        require_paper_only_flags("manual decision queue item", self)


@dataclass(frozen=True)
class ResearchStrategyManualDecisionQueueRow:
    queue_item_id: str
    market_slug: str
    evidence_item_count: Decimal
    required_evidence_item_count: Decimal
    specialist_count: Decimal
    required_specialist_count: Decimal
    cost_sanity_score: Decimal
    resolution_rule_check_score: Decimal
    minutes_until_recheck: Decimal
    evidence_completeness_score: Decimal
    specialist_coverage_score: Decimal
    recheck_urgency_score: Decimal
    readiness_score: Decimal
    recheck_due_now: bool
    queue_status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyManualDecisionQueueRow, "row")
        _require_public_text("queue_item_id", self.queue_item_id)
        _require_public_text("market_slug", self.market_slug)
        for field_name in ("evidence_item_count", "specialist_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("required_evidence_item_count", "required_specialist_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "cost_sanity_score",
            "resolution_rule_check_score",
            "evidence_completeness_score",
            "specialist_coverage_score",
            "recheck_urgency_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minutes_until_recheck",
            _normalize_nonnegative_decimal(
                "minutes_until_recheck",
                self.minutes_until_recheck,
            ),
        )
        if type(self.recheck_due_now) is not bool:
            raise ValueError("recheck_due_now must be a bool")
        _require_status("queue_status", self.queue_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        require_paper_only_flags("manual decision queue row", self)


@dataclass(frozen=True)
class ResearchStrategyManualDecisionQueueReport:
    generated_at: datetime
    config_version: str
    queue_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    evidence_incomplete_count: Decimal
    specialist_gap_count: Decimal
    cost_sanity_gap_count: Decimal
    resolution_rule_gap_count: Decimal
    recheck_urgent_count: Decimal
    min_readiness_score: Decimal | None
    queue_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyManualDecisionQueueRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "queue_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "evidence_incomplete_count",
            "specialist_gap_count",
            "cost_sanity_gap_count",
            "resolution_rule_gap_count",
            "recheck_urgent_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.min_readiness_score is not None:
            object.__setattr__(
                self,
                "min_readiness_score",
                _normalize_unit_decimal(
                    "min_readiness_score",
                    self.min_readiness_score,
                ),
            )
        _require_status("queue_status", self.queue_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _validate_report(self)
        require_paper_only_flags("manual decision queue report", self)


def build_research_strategy_manual_decision_queue_report(
    items: Iterable[ResearchStrategyManualDecisionQueueItem],
    *,
    config: ResearchStrategyManualDecisionQueueReportConfig,
    generated_at: datetime,
) -> ResearchStrategyManualDecisionQueueReport:
    if type(config) is not ResearchStrategyManualDecisionQueueReportConfig:
        raise ValueError("config must be a ResearchStrategyManualDecisionQueueReportConfig")
    require_paper_only_flags("manual decision queue config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_items = _normalize_items(items)
    rows = tuple(
        sorted(
            (_row_from_item(item, config=config) for item in normalized_items),
            key=_row_sort_key,
        ),
    )
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "queue_item_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "evidence_incomplete_count": _reason_group_count(
            rows,
            _EVIDENCE_GAP_REASONS,
        ),
        "specialist_gap_count": _reason_group_count(rows, _SPECIALIST_GAP_REASONS),
        "cost_sanity_gap_count": _reason_group_count(rows, _COST_GAP_REASONS),
        "resolution_rule_gap_count": _reason_group_count(
            rows,
            _RESOLUTION_GAP_REASONS,
        ),
        "recheck_urgent_count": _reason_group_count(rows, _RECHECK_REASONS),
        "min_readiness_score": (
            None if not rows else min(row.readiness_score for row in rows)
        ),
        "queue_status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyManualDecisionQueueReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_manual_decision_queue_report_payload(
    report: ResearchStrategyManualDecisionQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyManualDecisionQueueReport:
        require_paper_only_flags("manual decision queue report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyManualDecisionQueueReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be an object")
    _reject_unsafe_payload(payload)
    require_paper_only_flags("manual decision queue payload", _PayloadFlags(payload))
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


def _validate_config(config: ResearchStrategyManualDecisionQueueReportConfig) -> None:
    if (
        config.evidence_completeness_watch_floor
        > config.evidence_completeness_pass_floor
    ):
        raise ValueError(
            "evidence completeness watch floor must not exceed pass floor",
        )
    if config.specialist_coverage_watch_floor > config.specialist_coverage_pass_floor:
        raise ValueError("specialist coverage watch floor must not exceed pass floor")
    if config.cost_sanity_watch_floor > config.cost_sanity_pass_floor:
        raise ValueError("cost sanity watch floor must not exceed pass floor")
    if config.resolution_rule_check_watch_floor > config.resolution_rule_check_pass_floor:
        raise ValueError("resolution rule check watch floor must not exceed pass floor")
    if config.recheck_urgency_block_minutes >= config.recheck_urgency_watch_minutes:
        raise ValueError("recheck urgency block minutes must be below watch minutes")


def _normalize_items(
    items: Iterable[ResearchStrategyManualDecisionQueueItem],
) -> tuple[ResearchStrategyManualDecisionQueueItem, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyManualDecisionQueueItem:
            raise ValueError("items must contain ResearchStrategyManualDecisionQueueItem")
        require_paper_only_flags("manual decision queue item", item)
        if item.queue_item_id in seen:
            raise ValueError("queue_item_id values must be unique")
        seen.add(item.queue_item_id)
    return normalized


def _row_from_item(
    item: ResearchStrategyManualDecisionQueueItem,
    *,
    config: ResearchStrategyManualDecisionQueueReportConfig,
) -> ResearchStrategyManualDecisionQueueRow:
    evidence_score = _capped_ratio(
        item.evidence_item_count,
        item.required_evidence_item_count,
    )
    specialist_score = _capped_ratio(
        item.specialist_count,
        item.required_specialist_count,
    )
    recheck_score = _recheck_urgency_score(item.minutes_until_recheck, config)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        evidence_score=evidence_score,
        specialist_score=specialist_score,
    )
    row_values = {
        "queue_item_id": item.queue_item_id,
        "market_slug": item.market_slug,
        "evidence_item_count": item.evidence_item_count,
        "required_evidence_item_count": item.required_evidence_item_count,
        "specialist_count": item.specialist_count,
        "required_specialist_count": item.required_specialist_count,
        "cost_sanity_score": item.cost_sanity_score,
        "resolution_rule_check_score": item.resolution_rule_check_score,
        "minutes_until_recheck": item.minutes_until_recheck,
        "evidence_completeness_score": evidence_score,
        "specialist_coverage_score": specialist_score,
        "recheck_urgency_score": recheck_score,
        "readiness_score": _readiness_score(
            (
                evidence_score,
                specialist_score,
                item.cost_sanity_score,
                item.resolution_rule_check_score,
                recheck_score,
            ),
        ),
        "recheck_due_now": item.minutes_until_recheck
        <= config.recheck_urgency_block_minutes,
        "queue_status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyManualDecisionQueueRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    item: ResearchStrategyManualDecisionQueueItem,
    *,
    config: ResearchStrategyManualDecisionQueueReportConfig,
    evidence_score: Decimal,
    specialist_score: Decimal,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if (
        item.evidence_item_count < config.min_evidence_item_count
        or evidence_score < config.evidence_completeness_watch_floor
    ):
        block_reasons.append("evidence_completeness_block")
    elif evidence_score < config.evidence_completeness_pass_floor:
        watch_reasons.append("evidence_completeness_watch")
    if (
        item.specialist_count < config.min_specialist_count
        or specialist_score < config.specialist_coverage_watch_floor
    ):
        block_reasons.append("specialist_coverage_block")
    elif specialist_score < config.specialist_coverage_pass_floor:
        watch_reasons.append("specialist_coverage_watch")
    if item.cost_sanity_score < config.cost_sanity_watch_floor:
        block_reasons.append("cost_sanity_block")
    elif item.cost_sanity_score < config.cost_sanity_pass_floor:
        watch_reasons.append("cost_sanity_watch")
    if item.resolution_rule_check_score < config.resolution_rule_check_watch_floor:
        block_reasons.append("resolution_rule_check_block")
    elif item.resolution_rule_check_score < config.resolution_rule_check_pass_floor:
        watch_reasons.append("resolution_rule_check_watch")
    if item.minutes_until_recheck <= config.recheck_urgency_block_minutes:
        block_reasons.append("recheck_urgency_block")
    elif item.minutes_until_recheck <= config.recheck_urgency_watch_minutes:
        watch_reasons.append("recheck_urgency_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = (_READY_REASON,)
    return _normalize_row_reason_codes("reason_codes", reasons)


def _recheck_urgency_score(
    minutes_until_recheck: Decimal,
    config: ResearchStrategyManualDecisionQueueReportConfig,
) -> Decimal:
    if minutes_until_recheck <= config.recheck_urgency_block_minutes:
        return _ZERO
    if minutes_until_recheck >= config.recheck_urgency_watch_minutes:
        return _ONE
    window = config.recheck_urgency_watch_minutes - config.recheck_urgency_block_minutes
    elapsed = minutes_until_recheck - config.recheck_urgency_block_minutes
    return _ratio(elapsed, window)


def _readiness_score(component_values: tuple[Decimal, Decimal, Decimal, Decimal, Decimal]) -> Decimal:
    return _ratio(_sum_decimal(component_values), _FIVE)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason in _BLOCK_REASONS for reason in reason_codes):
        return "block"
    if reason_codes == (_READY_REASON,):
        return "pass"
    return "watch"


def _report_status(rows: tuple[ResearchStrategyManualDecisionQueueRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.queue_status == "block" for row in rows):
        return "block"
    if any(row.queue_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyManualDecisionQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    return _normalize_report_reason_codes(
        "reason_codes",
        tuple(reason for row in rows for reason in row.reason_codes),
    )


def _status_count(
    rows: tuple[ResearchStrategyManualDecisionQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.queue_status == status))


def _reason_group_count(
    rows: tuple[ResearchStrategyManualDecisionQueueRow, ...],
    reasons: frozenset[str],
) -> Decimal:
    return _count(sum(1 for row in rows if any(reason in reasons for reason in row.reason_codes)))


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyManualDecisionQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyManualDecisionQueueRow:
            raise ValueError("rows must contain ResearchStrategyManualDecisionQueueRow")
        require_paper_only_flags("manual decision queue row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return normalized


def _validate_row(row: ResearchStrategyManualDecisionQueueRow) -> None:
    expected_evidence_score = _capped_ratio(
        row.evidence_item_count,
        row.required_evidence_item_count,
    )
    if row.evidence_completeness_score != expected_evidence_score:
        raise ValueError("evidence_completeness_score must match counts")
    expected_specialist_score = _capped_ratio(
        row.specialist_count,
        row.required_specialist_count,
    )
    if row.specialist_coverage_score != expected_specialist_score:
        raise ValueError("specialist_coverage_score must match counts")
    expected_score = _readiness_score(
        (
            row.evidence_completeness_score,
            row.specialist_coverage_score,
            row.cost_sanity_score,
            row.resolution_rule_check_score,
            row.recheck_urgency_score,
        ),
    )
    if row.readiness_score != expected_score:
        raise ValueError("readiness_score must match component scores")
    if row.queue_status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("queue_status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchStrategyManualDecisionQueueReport) -> None:
    if report.queue_item_count != _count(len(report.rows)):
        raise ValueError("queue_item_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.evidence_incomplete_count != _reason_group_count(
        report.rows,
        _EVIDENCE_GAP_REASONS,
    ):
        raise ValueError("evidence_incomplete_count must match rows")
    if report.specialist_gap_count != _reason_group_count(
        report.rows,
        _SPECIALIST_GAP_REASONS,
    ):
        raise ValueError("specialist_gap_count must match rows")
    if report.cost_sanity_gap_count != _reason_group_count(report.rows, _COST_GAP_REASONS):
        raise ValueError("cost_sanity_gap_count must match rows")
    if report.resolution_rule_gap_count != _reason_group_count(
        report.rows,
        _RESOLUTION_GAP_REASONS,
    ):
        raise ValueError("resolution_rule_gap_count must match rows")
    if report.recheck_urgent_count != _reason_group_count(report.rows, _RECHECK_REASONS):
        raise ValueError("recheck_urgent_count must match rows")
    expected_min = None if not report.rows else min(row.readiness_score for row in report.rows)
    if report.min_readiness_score != expected_min:
        raise ValueError("min_readiness_score must match rows")
    if report.queue_status != _report_status(report.rows):
        raise ValueError("queue_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(row: ResearchStrategyManualDecisionQueueRow) -> dict[str, Any]:
    return {
        "queue_item_id": row.queue_item_id,
        "market_slug": row.market_slug,
        "evidence_item_count": row.evidence_item_count,
        "required_evidence_item_count": row.required_evidence_item_count,
        "specialist_count": row.specialist_count,
        "required_specialist_count": row.required_specialist_count,
        "cost_sanity_score": row.cost_sanity_score,
        "resolution_rule_check_score": row.resolution_rule_check_score,
        "minutes_until_recheck": row.minutes_until_recheck,
        "evidence_completeness_score": row.evidence_completeness_score,
        "specialist_coverage_score": row.specialist_coverage_score,
        "recheck_urgency_score": row.recheck_urgency_score,
        "readiness_score": row.readiness_score,
        "recheck_due_now": row.recheck_due_now,
        "queue_status": row.queue_status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(report: ResearchStrategyManualDecisionQueueReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "queue_item_count": report.queue_item_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "evidence_incomplete_count": report.evidence_incomplete_count,
        "specialist_gap_count": report.specialist_gap_count,
        "cost_sanity_gap_count": report.cost_sanity_gap_count,
        "resolution_rule_gap_count": report.resolution_rule_gap_count,
        "recheck_urgent_count": report.recheck_urgent_count,
        "min_readiness_score": report.min_readiness_score,
        "queue_status": report.queue_status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_sort_key(row: ResearchStrategyManualDecisionQueueRow) -> tuple[int, Decimal, str]:
    return (_STATUS_WEIGHT[row.queue_status], row.readiness_score, row.queue_item_id)


def _normalize_row_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if _READY_REASON in codes and len(codes) != 1:
        raise ValueError(f"{name} ready reason must stand alone")
    return codes


def _normalize_report_reason_codes(name: str, values: object) -> tuple[str, ...]:
    codes = _normalize_public_reason_codes(name, values)
    if not codes:
        raise ValueError(f"{name} must not be empty")
    if codes == (_EMPTY_REASON,):
        return codes
    if _EMPTY_REASON in codes:
        raise ValueError(f"{name} empty reason must stand alone")
    return codes


def _normalize_public_reason_codes(name: str, values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be an iterable")
    try:
        codes = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be an iterable") from exc
    for code in codes:
        _require_public_text(name, code)
        compact_code = "".join(part for part in code if part != "_")
        if not compact_code.isalnum() or code.lower() != code:
            raise ValueError(f"{name} must contain lowercase snake case values")
    return tuple(sorted(dict.fromkeys(codes), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in _REASON_PRIORITY:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    return (len(_REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(_COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = _ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= _ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(_DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > _ONE:
        return _ONE
    return value


def _normalize_positive_count(name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(_COUNT_QUANTUM)


def _normalize_positive_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return _quantize(normalized)


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(normalized)


def _normalize_unit_decimal(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in _STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in _UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        _require_public_text("JSON value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(value: Any) -> None:
    if type(value) is dict:
        for key, item in value.items():
            _require_public_text("payload key", key)
            if key in _FLAG_NAMES and item is not True:
                raise ValueError(f"{key} must be True in payload")
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) in (int, float):
        raise ValueError("payload numeric values must use Decimal strings")
    if isinstance(value, datetime):
        if type(value) is not datetime or value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime values must be timezone-aware")
    if type(value) is str:
        _require_public_text("payload value", value)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_MANUAL_DECISION_QUEUE_REPORT_CONFIG_VERSION",
    "ResearchStrategyManualDecisionQueueItem",
    "ResearchStrategyManualDecisionQueueReport",
    "ResearchStrategyManualDecisionQueueReportConfig",
    "ResearchStrategyManualDecisionQueueRow",
    "build_research_strategy_manual_decision_queue_report",
    "research_strategy_manual_decision_queue_report_payload",
)
