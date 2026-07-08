"""Pure packet completeness report for manual review."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_RESEARCH_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION",
    "ResearchStrategyResearchPacketCandidate",
    "ResearchStrategyResearchPacketCompletenessConfig",
    "ResearchStrategyResearchPacketCompletenessReport",
    "ResearchStrategyResearchPacketCompletenessRow",
    "build_research_strategy_research_packet_completeness_report",
    "research_strategy_research_packet_completeness_report_digest",
    "research_strategy_research_packet_completeness_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_RESEARCH_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION = (
    "research-strategy-research-packet-completeness-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX = Decimal("6.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_PACKETS_REASON = "research_packet_completeness_no_packets"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "packet_count",
    "pass_count",
    "watch_count",
    "block_count",
    "min_completeness_score",
    "status",
    "manual_decision_review_state",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_PRIORITY = (
    "evidence_item_count_block",
    "independent_source_count_block",
    "source_diversity_block",
    "cost_sanity_block",
    "resolution_rule_review_block",
    "specialist_memory_coverage_block",
    "unresolved_packet_gap_block",
    "research_packet_completeness_block",
    "evidence_item_count_watch",
    "independent_source_count_watch",
    "source_diversity_watch",
    "cost_sanity_watch",
    "resolution_rule_review_watch",
    "specialist_memory_coverage_watch",
    "unresolved_packet_gap_watch",
    "research_packet_completeness_watch",
    "research_packet_completeness_pass",
    NO_PACKETS_REASON,
)
UNSAFE_TEXT_FRAGMENTS = (
    "li" "ve",
    "au" "th",
    "wal" "let",
    "bro" "ker",
    "or" "der",
    "can" "cel",
    "re" "place",
    "ex" "change",
    "private" "_" "key",
    "api" "_" "key",
    "sec" "ret",
    "po" "sition",
    "b" "uy",
    "se" "ll",
    "reco" "mmend",
    "siz" "ing",
    "data" "base",
    "net" "work",
    "req" "uests",
    "ht" "tp",
    "sock" "et",
    "sub" "process",
    "tr" "ade",
    "://",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyResearchPacketCompletenessConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_RESEARCH_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    min_evidence_item_count: Decimal = Decimal("4.000000")
    evidence_item_count_pass_floor: Decimal = Decimal("6.000000")
    min_independent_source_count: Decimal = Decimal("2.000000")
    independent_source_count_pass_floor: Decimal = Decimal("3.000000")
    source_diversity_watch_floor: Decimal = Decimal("0.700000")
    source_diversity_block_floor: Decimal = Decimal("0.400000")
    cost_sanity_watch_floor: Decimal = Decimal("0.700000")
    cost_sanity_block_floor: Decimal = Decimal("0.400000")
    resolution_rule_review_watch_floor: Decimal = Decimal("0.750000")
    resolution_rule_review_block_floor: Decimal = Decimal("0.500000")
    specialist_memory_coverage_watch_floor: Decimal = Decimal("0.750000")
    specialist_memory_coverage_block_floor: Decimal = Decimal("0.500000")
    unresolved_packet_gap_watch_ceiling: Decimal = Decimal("0.000000")
    unresolved_packet_gap_block_ceiling: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyResearchPacketCompletenessConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "min_evidence_item_count",
            "evidence_item_count_pass_floor",
            "min_independent_source_count",
            "independent_source_count_pass_floor",
            "unresolved_packet_gap_watch_ceiling",
            "unresolved_packet_gap_block_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_diversity_watch_floor",
            "source_diversity_block_floor",
            "cost_sanity_watch_floor",
            "cost_sanity_block_floor",
            "resolution_rule_review_watch_floor",
            "resolution_rule_review_block_floor",
            "specialist_memory_coverage_watch_floor",
            "specialist_memory_coverage_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "evidence_item_count_pass_floor",
            self.evidence_item_count_pass_floor,
            self.min_evidence_item_count,
        )
        _require_at_least(
            "independent_source_count_pass_floor",
            self.independent_source_count_pass_floor,
            self.min_independent_source_count,
        )
        _require_at_least(
            "source_diversity_watch_floor",
            self.source_diversity_watch_floor,
            self.source_diversity_block_floor,
        )
        _require_at_least(
            "cost_sanity_watch_floor",
            self.cost_sanity_watch_floor,
            self.cost_sanity_block_floor,
        )
        _require_at_least(
            "resolution_rule_review_watch_floor",
            self.resolution_rule_review_watch_floor,
            self.resolution_rule_review_block_floor,
        )
        _require_at_least(
            "specialist_memory_coverage_watch_floor",
            self.specialist_memory_coverage_watch_floor,
            self.specialist_memory_coverage_block_floor,
        )
        _require_at_most(
            "unresolved_packet_gap_watch_ceiling",
            self.unresolved_packet_gap_watch_ceiling,
            self.unresolved_packet_gap_block_ceiling,
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyResearchPacketCandidate(_FinalDataclass):
    packet_ref: str
    evidence_item_count: Decimal
    independent_source_count: Decimal
    source_diversity_score: Decimal
    cost_sanity_score: Decimal
    resolution_rule_review_score: Decimal
    specialist_memory_coverage_score: Decimal
    unresolved_packet_gap_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyResearchPacketCandidate, "candidate")
        _require_public_text("packet_ref", self.packet_ref)
        for field_name in (
            "evidence_item_count",
            "independent_source_count",
            "unresolved_packet_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.evidence_item_count:
            raise ValueError("independent_source_count must not exceed evidence_item_count")
        for field_name in (
            "source_diversity_score",
            "cost_sanity_score",
            "resolution_rule_review_score",
            "specialist_memory_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_hard_phase_flags("candidate", self)


@dataclass(frozen=True)
class ResearchStrategyResearchPacketCompletenessRow(_FinalDataclass):
    packet_ref: str
    evidence_item_count: Decimal
    independent_source_count: Decimal
    source_diversity_score: Decimal
    cost_sanity_score: Decimal
    resolution_rule_review_score: Decimal
    specialist_memory_coverage_score: Decimal
    unresolved_packet_gap_count: Decimal
    evidence_coverage_ratio: Decimal
    independent_source_ratio: Decimal
    completeness_score: Decimal
    status: str
    manual_decision_review_state: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyResearchPacketCompletenessRow, "row")
        _require_public_text("packet_ref", self.packet_ref)
        for field_name in (
            "evidence_item_count",
            "independent_source_count",
            "unresolved_packet_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.independent_source_count > self.evidence_item_count:
            raise ValueError("independent_source_count must not exceed evidence_item_count")
        for field_name in (
            "source_diversity_score",
            "cost_sanity_score",
            "resolution_rule_review_score",
            "specialist_memory_coverage_score",
            "evidence_coverage_ratio",
            "independent_source_ratio",
            "completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_manual_state("manual_decision_review_state", self.manual_decision_review_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        _require_hard_phase_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyResearchPacketCompletenessReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    packet_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    min_completeness_score: Decimal | None
    status: str
    manual_decision_review_state: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyResearchPacketCompletenessRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyResearchPacketCompletenessReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in ("packet_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.min_completeness_score is not None:
            object.__setattr__(
                self,
                "min_completeness_score",
                _normalize_ratio("min_completeness_score", self.min_completeness_score),
            )
        _require_status("status", self.status)
        _require_manual_state("manual_decision_review_state", self.manual_decision_review_state)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_phase_flags("report", self)
        _validate_report(self)


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def build_research_strategy_research_packet_completeness_report(
    candidates: Iterable[ResearchStrategyResearchPacketCandidate],
    *,
    config: ResearchStrategyResearchPacketCompletenessConfig,
    generated_at: datetime,
) -> ResearchStrategyResearchPacketCompletenessReport:
    if type(config) is not ResearchStrategyResearchPacketCompletenessConfig:
        raise ValueError(
            "config must be a ResearchStrategyResearchPacketCompletenessConfig",
        )
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    candidate_rows = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (_row_from_candidate(candidate, config=config) for candidate in candidate_rows),
            key=_row_sort_key,
        ),
    )
    report_status = _report_status(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "packet_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "min_completeness_score": (
            None if not rows else min(row.completeness_score for row in rows)
        ),
        "status": report_status,
        "manual_decision_review_state": _manual_state(report_status),
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyResearchPacketCompletenessReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_strategy_research_packet_completeness_report_payload(
    report: ResearchStrategyResearchPacketCompletenessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyResearchPacketCompletenessReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyResearchPacketCompletenessReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    return payload


def research_strategy_research_packet_completeness_report_digest(
    report: ResearchStrategyResearchPacketCompletenessReport,
) -> dict[str, Any]:
    payload = research_strategy_research_packet_completeness_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


def _row_from_candidate(
    candidate: ResearchStrategyResearchPacketCandidate,
    *,
    config: ResearchStrategyResearchPacketCompletenessConfig,
) -> ResearchStrategyResearchPacketCompletenessRow:
    evidence_coverage_ratio = _capped_ratio(
        candidate.evidence_item_count,
        config.evidence_item_count_pass_floor,
    )
    independent_source_ratio = _capped_ratio(
        candidate.independent_source_count,
        config.independent_source_count_pass_floor,
    )
    reason_codes = _row_reason_codes(candidate, config=config)
    row_status = _row_status(reason_codes)
    row_values = {
        "packet_ref": candidate.packet_ref,
        "evidence_item_count": candidate.evidence_item_count,
        "independent_source_count": candidate.independent_source_count,
        "source_diversity_score": candidate.source_diversity_score,
        "cost_sanity_score": candidate.cost_sanity_score,
        "resolution_rule_review_score": candidate.resolution_rule_review_score,
        "specialist_memory_coverage_score": candidate.specialist_memory_coverage_score,
        "unresolved_packet_gap_count": candidate.unresolved_packet_gap_count,
        "evidence_coverage_ratio": evidence_coverage_ratio,
        "independent_source_ratio": independent_source_ratio,
        "completeness_score": _completeness_score(
            (
                evidence_coverage_ratio,
                independent_source_ratio,
                candidate.source_diversity_score,
                candidate.cost_sanity_score,
                candidate.resolution_rule_review_score,
                candidate.specialist_memory_coverage_score,
            ),
        ),
        "status": row_status,
        "manual_decision_review_state": _manual_state(row_status),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyResearchPacketCompletenessRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    candidate: ResearchStrategyResearchPacketCandidate,
    *,
    config: ResearchStrategyResearchPacketCompletenessConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if candidate.evidence_item_count < config.min_evidence_item_count:
        block_reasons.append("evidence_item_count_block")
    elif candidate.evidence_item_count < config.evidence_item_count_pass_floor:
        watch_reasons.append("evidence_item_count_watch")
    if candidate.independent_source_count < config.min_independent_source_count:
        block_reasons.append("independent_source_count_block")
    elif candidate.independent_source_count < config.independent_source_count_pass_floor:
        watch_reasons.append("independent_source_count_watch")
    if candidate.source_diversity_score < config.source_diversity_block_floor:
        block_reasons.append("source_diversity_block")
    elif candidate.source_diversity_score < config.source_diversity_watch_floor:
        watch_reasons.append("source_diversity_watch")
    if candidate.cost_sanity_score < config.cost_sanity_block_floor:
        block_reasons.append("cost_sanity_block")
    elif candidate.cost_sanity_score < config.cost_sanity_watch_floor:
        watch_reasons.append("cost_sanity_watch")
    if candidate.resolution_rule_review_score < config.resolution_rule_review_block_floor:
        block_reasons.append("resolution_rule_review_block")
    elif candidate.resolution_rule_review_score < config.resolution_rule_review_watch_floor:
        watch_reasons.append("resolution_rule_review_watch")
    if (
        candidate.specialist_memory_coverage_score
        < config.specialist_memory_coverage_block_floor
    ):
        block_reasons.append("specialist_memory_coverage_block")
    elif (
        candidate.specialist_memory_coverage_score
        < config.specialist_memory_coverage_watch_floor
    ):
        watch_reasons.append("specialist_memory_coverage_watch")
    if candidate.unresolved_packet_gap_count >= config.unresolved_packet_gap_block_ceiling:
        block_reasons.append("unresolved_packet_gap_block")
    elif candidate.unresolved_packet_gap_count > config.unresolved_packet_gap_watch_ceiling:
        watch_reasons.append("unresolved_packet_gap_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("research_packet_completeness_pass",)
    return _normalize_reason_codes(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchStrategyResearchPacketCompletenessRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _manual_state(status: str) -> str:
    if status == "block":
        return "manual_decision_review_block"
    if status == "watch":
        return "manual_decision_review_watch"
    return "manual_decision_review_ready"


def _report_reason_codes(
    rows: tuple[ResearchStrategyResearchPacketCompletenessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_PACKETS_REASON,)
    status = _report_status(rows)
    values = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "research_packet_completeness_pass"
    )
    return _normalize_reason_codes((*values, f"research_packet_completeness_{status}"))


def _completeness_score(values: tuple[Decimal, ...]) -> Decimal:
    return _ratio(_sum_decimal(values), SIX)


def _normalize_candidates(
    candidates: Iterable[ResearchStrategyResearchPacketCandidate],
) -> tuple[ResearchStrategyResearchPacketCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        values = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for candidate in values:
        if type(candidate) is not ResearchStrategyResearchPacketCandidate:
            raise ValueError(
                "candidates must contain ResearchStrategyResearchPacketCandidate",
            )
        _require_hard_phase_flags("candidate", candidate)
        if candidate.packet_ref in seen:
            raise ValueError("packet_ref values must be unique")
        seen.add(candidate.packet_ref)
    return values


def _normalize_rows(
    rows: Iterable[ResearchStrategyResearchPacketCompletenessRow],
) -> tuple[ResearchStrategyResearchPacketCompletenessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyResearchPacketCompletenessRow:
            raise ValueError(
                "rows must contain ResearchStrategyResearchPacketCompletenessRow",
            )
        _require_hard_phase_flags("row", row)
        if row.packet_ref in seen:
            raise ValueError("packet_ref values must be unique")
        seen.add(row.packet_ref)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _validate_row(row: ResearchStrategyResearchPacketCompletenessRow) -> None:
    expected_completeness = _completeness_score(
        (
            row.evidence_coverage_ratio,
            row.independent_source_ratio,
            row.source_diversity_score,
            row.cost_sanity_score,
            row.resolution_rule_review_score,
            row.specialist_memory_coverage_score,
        ),
    )
    if row.completeness_score != expected_completeness:
        raise ValueError("completeness_score must match component scores")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.manual_decision_review_state != _manual_state(row.status):
        raise ValueError("manual_decision_review_state must match status")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchStrategyResearchPacketCompletenessReport) -> None:
    if report.packet_count != _count(len(report.rows)):
        raise ValueError("packet_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    expected_min = None if not report.rows else min(row.completeness_score for row in report.rows)
    if report.min_completeness_score != expected_min:
        raise ValueError("min_completeness_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.manual_decision_review_state != _manual_state(report.status):
        raise ValueError("manual_decision_review_state must match status")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(row: ResearchStrategyResearchPacketCompletenessRow) -> dict[str, Any]:
    return {
        "packet_ref": row.packet_ref,
        "evidence_item_count": row.evidence_item_count,
        "independent_source_count": row.independent_source_count,
        "source_diversity_score": row.source_diversity_score,
        "cost_sanity_score": row.cost_sanity_score,
        "resolution_rule_review_score": row.resolution_rule_review_score,
        "specialist_memory_coverage_score": row.specialist_memory_coverage_score,
        "unresolved_packet_gap_count": row.unresolved_packet_gap_count,
        "evidence_coverage_ratio": row.evidence_coverage_ratio,
        "independent_source_ratio": row.independent_source_ratio,
        "completeness_score": row.completeness_score,
        "status": row.status,
        "manual_decision_review_state": row.manual_decision_review_state,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchStrategyResearchPacketCompletenessReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "packet_count": report.packet_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "min_completeness_score": report.min_completeness_score,
        "status": report.status,
        "manual_decision_review_state": report.manual_decision_review_state,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_sort_key(
    row: ResearchStrategyResearchPacketCompletenessRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_WEIGHT[row.status], row.completeness_score, row.packet_ref)


def _status_count(
    rows: tuple[ResearchStrategyResearchPacketCompletenessRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(values)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    for reason_code in reason_codes:
        _require_public_text("reason_codes", reason_code)
        compact = "".join(part for part in reason_code if part != "_")
        if not compact.isalnum() or reason_code.lower() != reason_code:
            raise ValueError("reason_codes must be lowercase snake case")
    normalized = tuple(sorted(dict.fromkeys(reason_codes), key=_reason_sort_key))
    if "research_packet_completeness_pass" in normalized and len(normalized) != 1:
        raise ValueError("research_packet_completeness_pass must stand alone")
    if NO_PACKETS_REASON in normalized and len(normalized) != 1:
        raise ValueError("no packets reason must stand alone")
    return normalized


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    if reason_code in REASON_PRIORITY:
        return (REASON_PRIORITY.index(reason_code), reason_code)
    return (len(REASON_PRIORITY), reason_code)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += _normalize_decimal("sum value", value)
    return _quantize(total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= ZERO:
        raise ValueError("denominator must be positive")
    numerator = _normalize_decimal("numerator", numerator)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    value = _ratio(numerator, denominator)
    if value > ONE:
        return ONE
    return value


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{name} must be an integer")
    return normalized.quantize(COUNT_QUANTUM)


def _normalize_ratio(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(normalized)


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_at_least(name: str, value: Decimal, floor: Decimal) -> None:
    if value < floor:
        raise ValueError(f"{name} must be at least its paired floor")


def _require_at_most(name: str, value: Decimal, ceiling: Decimal) -> None:
    if value > ceiling:
        raise ValueError(f"{name} must be at most its paired ceiling")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_manual_state(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in {
        "manual_decision_review_ready",
        "manual_decision_review_watch",
        "manual_decision_review_block",
    }:
        raise ValueError(f"{name} must be a manual decision review state")


def _require_text(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty canonical string")


def _require_public_text(name: str, value: object) -> None:
    _require_text(name, value)
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{name} contains unsafe public text")


def _require_digest(name: str, value: object) -> None:
    _require_text(name, value)
    if len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _require_hard_phase_flags(name: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _validation_digest(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if hasattr(value, "__dataclass_fields__") and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is bool:
        return value
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _require_public_text("payload key", key)
            _reject_unsafe_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_payload(item)
        return
    if type(value) is str:
        _require_public_text("payload value", value)
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("payload contains unsupported value")
