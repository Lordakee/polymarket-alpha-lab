"""Pure aggregate resolution verification packet completeness report."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_VERIFICATION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION",
    "ResearchResolutionVerificationPacketAggregate",
    "ResearchResolutionVerificationPacketCompletenessConfig",
    "ResearchResolutionVerificationPacketCompletenessReport",
    "ResearchResolutionVerificationPacketCompletenessRow",
    "build_research_resolution_verification_packet_completeness_report",
    "research_resolution_verification_packet_completeness_report_digest",
    "research_resolution_verification_packet_completeness_report_payload",
)


DEFAULT_RESEARCH_RESOLUTION_VERIFICATION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION = (
    "research-resolution-verification-packet-completeness-report-v0"
)

QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FIVE = Decimal("5.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}
NO_PACKETS_REASON = "resolution_verification_packet_completeness_no_packets"
SUMMARY_KEYS = (
    "generated_at",
    "config_version",
    "packet_group_count",
    "pass_count",
    "watch_count",
    "block_count",
    "required_rule_citation_count",
    "cited_rule_count",
    "verification_source_count",
    "agreeing_source_count",
    "evidence_item_count",
    "stale_evidence_count",
    "ambiguity_flag_count",
    "pending_recheck_count",
    "rule_citation_coverage_ratio",
    "source_agreement_ratio",
    "stale_evidence_pressure_ratio",
    "ambiguity_flag_pressure_ratio",
    "recheck_urgency_ratio",
    "min_completeness_score",
    "status",
    "reason_codes",
    "validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_PRIORITY = (
    "rule_citation_coverage_block",
    "source_agreement_block",
    "stale_evidence_pressure_block",
    "ambiguity_flag_pressure_block",
    "recheck_urgency_block",
    "resolution_verification_packet_completeness_block",
    "rule_citation_coverage_watch",
    "source_agreement_watch",
    "stale_evidence_pressure_watch",
    "ambiguity_flag_pressure_watch",
    "recheck_urgency_watch",
    "resolution_verification_packet_completeness_watch",
    "resolution_verification_packet_completeness_pass",
    NO_PACKETS_REASON,
)
UNSAFE_TEXT_FRAGMENTS = (
    "market" "_" "id",
    "market" "-" "id",
    "sl" "ug",
    "ques" "tion",
    "source" "_" "url",
    "source" "-" "url",
    "source" "_" "text",
    "source" "-" "text",
    "raw" "_" "source",
    "raw" "-" "source",
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
class ResearchResolutionVerificationPacketCompletenessConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_RESOLUTION_VERIFICATION_PACKET_COMPLETENESS_REPORT_CONFIG_VERSION
    )
    minimum_rule_citation_coverage_ratio: Decimal = Decimal("1.000000")
    block_rule_citation_coverage_ratio: Decimal = Decimal("0.750000")
    minimum_source_agreement_ratio: Decimal = Decimal("0.800000")
    block_source_agreement_ratio: Decimal = Decimal("0.500000")
    watch_stale_evidence_pressure_ratio: Decimal = Decimal("0.250000")
    block_stale_evidence_pressure_ratio: Decimal = Decimal("0.500000")
    watch_ambiguity_flag_pressure_ratio: Decimal = Decimal("0.100000")
    block_ambiguity_flag_pressure_ratio: Decimal = Decimal("0.250000")
    watch_recheck_urgency_ratio: Decimal = Decimal("0.200000")
    block_recheck_urgency_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionVerificationPacketCompletenessConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "minimum_rule_citation_coverage_ratio",
            "block_rule_citation_coverage_ratio",
            "minimum_source_agreement_ratio",
            "block_source_agreement_ratio",
            "watch_stale_evidence_pressure_ratio",
            "block_stale_evidence_pressure_ratio",
            "watch_ambiguity_flag_pressure_ratio",
            "block_ambiguity_flag_pressure_ratio",
            "watch_recheck_urgency_ratio",
            "block_recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_lower_threshold_pair(
            "block_rule_citation_coverage_ratio",
            self.block_rule_citation_coverage_ratio,
            "minimum_rule_citation_coverage_ratio",
            self.minimum_rule_citation_coverage_ratio,
        )
        _require_lower_threshold_pair(
            "block_source_agreement_ratio",
            self.block_source_agreement_ratio,
            "minimum_source_agreement_ratio",
            self.minimum_source_agreement_ratio,
        )
        _require_upper_threshold_pair(
            "watch_stale_evidence_pressure_ratio",
            self.watch_stale_evidence_pressure_ratio,
            "block_stale_evidence_pressure_ratio",
            self.block_stale_evidence_pressure_ratio,
        )
        _require_upper_threshold_pair(
            "watch_ambiguity_flag_pressure_ratio",
            self.watch_ambiguity_flag_pressure_ratio,
            "block_ambiguity_flag_pressure_ratio",
            self.block_ambiguity_flag_pressure_ratio,
        )
        _require_upper_threshold_pair(
            "watch_recheck_urgency_ratio",
            self.watch_recheck_urgency_ratio,
            "block_recheck_urgency_ratio",
            self.block_recheck_urgency_ratio,
        )
        _require_hard_phase_flags("config", self)


@dataclass(frozen=True)
class ResearchResolutionVerificationPacketAggregate(_FinalDataclass):
    packet_group_ref: str
    required_rule_citation_count: Decimal
    cited_rule_count: Decimal
    verification_source_count: Decimal
    agreeing_source_count: Decimal
    evidence_item_count: Decimal
    stale_evidence_count: Decimal = ZERO
    ambiguity_flag_count: Decimal = ZERO
    pending_recheck_count: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchResolutionVerificationPacketAggregate, "aggregate")
        _require_public_text("packet_group_ref", self.packet_group_ref)
        for field_name in (
            "required_rule_citation_count",
            "cited_rule_count",
            "verification_source_count",
            "evidence_item_count",
            "stale_evidence_count",
            "ambiguity_flag_count",
            "pending_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "agreeing_source_count",
            _normalize_nonnegative_count(
                "source_agreement_count",
                self.agreeing_source_count,
            ),
        )
        _validate_aggregate(self)
        _require_hard_phase_flags("aggregate", self)


@dataclass(frozen=True)
class ResearchResolutionVerificationPacketCompletenessRow(_FinalDataclass):
    packet_group_ref: str
    required_rule_citation_count: Decimal
    cited_rule_count: Decimal
    verification_source_count: Decimal
    agreeing_source_count: Decimal
    evidence_item_count: Decimal
    stale_evidence_count: Decimal
    ambiguity_flag_count: Decimal
    pending_recheck_count: Decimal
    rule_citation_coverage_ratio: Decimal
    source_agreement_ratio: Decimal
    stale_evidence_pressure_ratio: Decimal
    ambiguity_flag_pressure_ratio: Decimal
    recheck_urgency_ratio: Decimal
    completeness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionVerificationPacketCompletenessRow,
            "row",
        )
        _require_public_text("packet_group_ref", self.packet_group_ref)
        for field_name in (
            "required_rule_citation_count",
            "cited_rule_count",
            "verification_source_count",
            "agreeing_source_count",
            "evidence_item_count",
            "stale_evidence_count",
            "ambiguity_flag_count",
            "pending_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_citation_coverage_ratio",
            "source_agreement_ratio",
            "stale_evidence_pressure_ratio",
            "ambiguity_flag_pressure_ratio",
            "recheck_urgency_ratio",
            "completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_digest("validation_digest", self.validation_digest)
        _validate_row(self)
        _require_hard_phase_flags("row", self)


@dataclass(frozen=True)
class ResearchResolutionVerificationPacketCompletenessReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    packet_group_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    required_rule_citation_count: Decimal
    cited_rule_count: Decimal
    verification_source_count: Decimal
    agreeing_source_count: Decimal
    evidence_item_count: Decimal
    stale_evidence_count: Decimal
    ambiguity_flag_count: Decimal
    pending_recheck_count: Decimal
    rule_citation_coverage_ratio: Decimal
    source_agreement_ratio: Decimal
    stale_evidence_pressure_ratio: Decimal
    ambiguity_flag_pressure_ratio: Decimal
    recheck_urgency_ratio: Decimal
    min_completeness_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchResolutionVerificationPacketCompletenessRow, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchResolutionVerificationPacketCompletenessReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        for field_name in (
            "packet_group_count",
            "pass_count",
            "watch_count",
            "block_count",
            "required_rule_citation_count",
            "cited_rule_count",
            "verification_source_count",
            "agreeing_source_count",
            "evidence_item_count",
            "stale_evidence_count",
            "ambiguity_flag_count",
            "pending_recheck_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "rule_citation_coverage_ratio",
            "source_agreement_ratio",
            "stale_evidence_pressure_ratio",
            "ambiguity_flag_pressure_ratio",
            "recheck_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        if self.min_completeness_score is not None:
            object.__setattr__(
                self,
                "min_completeness_score",
                _normalize_ratio("min_completeness_score", self.min_completeness_score),
            )
        _require_status("status", self.status)
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


def build_research_resolution_verification_packet_completeness_report(
    aggregates: Iterable[ResearchResolutionVerificationPacketAggregate],
    *,
    config: ResearchResolutionVerificationPacketCompletenessConfig,
    generated_at: datetime,
) -> ResearchResolutionVerificationPacketCompletenessReport:
    if type(config) is not ResearchResolutionVerificationPacketCompletenessConfig:
        raise ValueError(
            "config must be a ResearchResolutionVerificationPacketCompletenessConfig",
        )
    _require_hard_phase_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    aggregate_rows = _normalize_aggregates(aggregates)
    rows = tuple(
        sorted(
            (_row_from_aggregate(aggregate, config=config) for aggregate in aggregate_rows),
            key=_row_sort_key,
        ),
    )
    report_status = _report_status(rows)
    report_values = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "packet_group_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "required_rule_citation_count": _row_sum(
            rows,
            "required_rule_citation_count",
        ),
        "cited_rule_count": _row_sum(rows, "cited_rule_count"),
        "verification_source_count": _row_sum(rows, "verification_source_count"),
        "agreeing_source_count": _row_sum(rows, "agreeing_source_count"),
        "evidence_item_count": _row_sum(rows, "evidence_item_count"),
        "stale_evidence_count": _row_sum(rows, "stale_evidence_count"),
        "ambiguity_flag_count": _row_sum(rows, "ambiguity_flag_count"),
        "pending_recheck_count": _row_sum(rows, "pending_recheck_count"),
        "min_completeness_score": (
            None if not rows else min(row.completeness_score for row in rows)
        ),
        "status": report_status,
        "reason_codes": _report_reason_codes(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    report_values.update(_report_ratios(report_values))
    return ResearchResolutionVerificationPacketCompletenessReport(
        **report_values,
        validation_digest=_validation_digest(report_values),
    )


def research_resolution_verification_packet_completeness_report_payload(
    report: ResearchResolutionVerificationPacketCompletenessReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchResolutionVerificationPacketCompletenessReport:
        _require_hard_phase_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchResolutionVerificationPacketCompletenessReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_payload(payload)
    _require_hard_phase_flags("payload", _DictFlags(payload))
    return payload


def research_resolution_verification_packet_completeness_report_digest(
    report: ResearchResolutionVerificationPacketCompletenessReport,
) -> dict[str, Any]:
    payload = research_resolution_verification_packet_completeness_report_payload(report)
    return {key: payload[key] for key in SUMMARY_KEYS}


def _row_from_aggregate(
    aggregate: ResearchResolutionVerificationPacketAggregate,
    *,
    config: ResearchResolutionVerificationPacketCompletenessConfig,
) -> ResearchResolutionVerificationPacketCompletenessRow:
    rule_citation_coverage_ratio = _bounded_ratio(
        aggregate.cited_rule_count,
        aggregate.required_rule_citation_count,
    )
    source_agreement_ratio = _bounded_ratio(
        aggregate.agreeing_source_count,
        aggregate.verification_source_count,
    )
    stale_evidence_pressure_ratio = _bounded_ratio(
        aggregate.stale_evidence_count,
        aggregate.evidence_item_count,
    )
    ambiguity_flag_pressure_ratio = _bounded_ratio(
        aggregate.ambiguity_flag_count,
        aggregate.evidence_item_count,
    )
    recheck_urgency_ratio = _bounded_ratio(
        aggregate.pending_recheck_count,
        aggregate.evidence_item_count,
    )
    reason_codes = _row_reason_codes(
        rule_citation_coverage_ratio=rule_citation_coverage_ratio,
        source_agreement_ratio=source_agreement_ratio,
        stale_evidence_pressure_ratio=stale_evidence_pressure_ratio,
        ambiguity_flag_pressure_ratio=ambiguity_flag_pressure_ratio,
        recheck_urgency_ratio=recheck_urgency_ratio,
        config=config,
    )
    row_status = _row_status(reason_codes)
    row_values = {
        "packet_group_ref": aggregate.packet_group_ref,
        "required_rule_citation_count": aggregate.required_rule_citation_count,
        "cited_rule_count": aggregate.cited_rule_count,
        "verification_source_count": aggregate.verification_source_count,
        "agreeing_source_count": aggregate.agreeing_source_count,
        "evidence_item_count": aggregate.evidence_item_count,
        "stale_evidence_count": aggregate.stale_evidence_count,
        "ambiguity_flag_count": aggregate.ambiguity_flag_count,
        "pending_recheck_count": aggregate.pending_recheck_count,
        "rule_citation_coverage_ratio": rule_citation_coverage_ratio,
        "source_agreement_ratio": source_agreement_ratio,
        "stale_evidence_pressure_ratio": stale_evidence_pressure_ratio,
        "ambiguity_flag_pressure_ratio": ambiguity_flag_pressure_ratio,
        "recheck_urgency_ratio": recheck_urgency_ratio,
        "completeness_score": _completeness_score(
            rule_citation_coverage_ratio=rule_citation_coverage_ratio,
            source_agreement_ratio=source_agreement_ratio,
            stale_evidence_pressure_ratio=stale_evidence_pressure_ratio,
            ambiguity_flag_pressure_ratio=ambiguity_flag_pressure_ratio,
            recheck_urgency_ratio=recheck_urgency_ratio,
        ),
        "status": row_status,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchResolutionVerificationPacketCompletenessRow(
        **row_values,
        validation_digest=_validation_digest(row_values),
    )


def _row_reason_codes(
    *,
    rule_citation_coverage_ratio: Decimal,
    source_agreement_ratio: Decimal,
    stale_evidence_pressure_ratio: Decimal,
    ambiguity_flag_pressure_ratio: Decimal,
    recheck_urgency_ratio: Decimal,
    config: ResearchResolutionVerificationPacketCompletenessConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    if rule_citation_coverage_ratio < config.block_rule_citation_coverage_ratio:
        block_reasons.append("rule_citation_coverage_block")
    elif rule_citation_coverage_ratio < config.minimum_rule_citation_coverage_ratio:
        watch_reasons.append("rule_citation_coverage_watch")
    if source_agreement_ratio < config.block_source_agreement_ratio:
        block_reasons.append("source_agreement_block")
    elif source_agreement_ratio < config.minimum_source_agreement_ratio:
        watch_reasons.append("source_agreement_watch")
    if stale_evidence_pressure_ratio >= config.block_stale_evidence_pressure_ratio:
        block_reasons.append("stale_evidence_pressure_block")
    elif stale_evidence_pressure_ratio >= config.watch_stale_evidence_pressure_ratio:
        watch_reasons.append("stale_evidence_pressure_watch")
    if ambiguity_flag_pressure_ratio >= config.block_ambiguity_flag_pressure_ratio:
        block_reasons.append("ambiguity_flag_pressure_block")
    elif ambiguity_flag_pressure_ratio >= config.watch_ambiguity_flag_pressure_ratio:
        watch_reasons.append("ambiguity_flag_pressure_watch")
    if recheck_urgency_ratio >= config.block_recheck_urgency_ratio:
        block_reasons.append("recheck_urgency_block")
    elif recheck_urgency_ratio >= config.watch_recheck_urgency_ratio:
        watch_reasons.append("recheck_urgency_watch")
    reasons = tuple(block_reasons + watch_reasons)
    if not reasons:
        reasons = ("resolution_verification_packet_completeness_pass",)
    return _normalize_reason_codes(reasons)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchResolutionVerificationPacketCompletenessRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionVerificationPacketCompletenessRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_PACKETS_REASON,)
    status = _report_status(rows)
    values = tuple(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != "resolution_verification_packet_completeness_pass"
    )
    return _normalize_reason_codes(
        (*values, f"resolution_verification_packet_completeness_{status}"),
    )


def _completeness_score(
    *,
    rule_citation_coverage_ratio: Decimal,
    source_agreement_ratio: Decimal,
    stale_evidence_pressure_ratio: Decimal,
    ambiguity_flag_pressure_ratio: Decimal,
    recheck_urgency_ratio: Decimal,
) -> Decimal:
    return _ratio(
        _sum_decimal(
            (
                rule_citation_coverage_ratio,
                source_agreement_ratio,
                ONE - stale_evidence_pressure_ratio,
                ONE - ambiguity_flag_pressure_ratio,
                ONE - recheck_urgency_ratio,
            ),
        ),
        FIVE,
    )


def _normalize_aggregates(
    aggregates: Iterable[ResearchResolutionVerificationPacketAggregate],
) -> tuple[ResearchResolutionVerificationPacketAggregate, ...]:
    if isinstance(aggregates, (str, bytes)):
        raise ValueError("aggregates must be an iterable")
    try:
        values = tuple(aggregates)
    except TypeError as exc:
        raise ValueError("aggregates must be an iterable") from exc
    seen: set[str] = set()
    for aggregate in values:
        if type(aggregate) is not ResearchResolutionVerificationPacketAggregate:
            raise ValueError(
                "aggregates must contain ResearchResolutionVerificationPacketAggregate",
            )
        _require_hard_phase_flags("aggregate", aggregate)
        if aggregate.packet_group_ref in seen:
            raise ValueError("packet_group_ref values must be unique")
        seen.add(aggregate.packet_group_ref)
    return values


def _normalize_rows(
    rows: Iterable[ResearchResolutionVerificationPacketCompletenessRow],
) -> tuple[ResearchResolutionVerificationPacketCompletenessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ResearchResolutionVerificationPacketCompletenessRow:
            raise ValueError(
                "rows must contain ResearchResolutionVerificationPacketCompletenessRow",
            )
        _require_hard_phase_flags("row", row)
        if row.packet_group_ref in seen:
            raise ValueError("packet_group_ref values must be unique")
        seen.add(row.packet_group_ref)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    return values


def _validate_aggregate(aggregate: ResearchResolutionVerificationPacketAggregate) -> None:
    if aggregate.cited_rule_count > aggregate.required_rule_citation_count:
        raise ValueError("cited_rule_count must not exceed required_rule_citation_count")
    if aggregate.agreeing_source_count > aggregate.verification_source_count:
        raise ValueError("source_agreement_count must not exceed verification_source_count")
    if aggregate.stale_evidence_count > aggregate.evidence_item_count:
        raise ValueError("stale_evidence_count must not exceed evidence_item_count")
    if aggregate.ambiguity_flag_count > aggregate.evidence_item_count:
        raise ValueError("ambiguity_flag_count must not exceed evidence_item_count")
    if aggregate.pending_recheck_count > aggregate.evidence_item_count:
        raise ValueError("pending_recheck_count must not exceed evidence_item_count")


def _validate_row(row: ResearchResolutionVerificationPacketCompletenessRow) -> None:
    _validate_aggregate(
        ResearchResolutionVerificationPacketAggregate(
            packet_group_ref=row.packet_group_ref,
            required_rule_citation_count=row.required_rule_citation_count,
            cited_rule_count=row.cited_rule_count,
            verification_source_count=row.verification_source_count,
            agreeing_source_count=row.agreeing_source_count,
            evidence_item_count=row.evidence_item_count,
            stale_evidence_count=row.stale_evidence_count,
            ambiguity_flag_count=row.ambiguity_flag_count,
            pending_recheck_count=row.pending_recheck_count,
        ),
    )
    if row.rule_citation_coverage_ratio != _bounded_ratio(
        row.cited_rule_count,
        row.required_rule_citation_count,
    ):
        raise ValueError("rule_citation_coverage_ratio must match counts")
    if row.source_agreement_ratio != _bounded_ratio(
        row.agreeing_source_count,
        row.verification_source_count,
    ):
        raise ValueError("source_agreement_ratio must match counts")
    if row.stale_evidence_pressure_ratio != _bounded_ratio(
        row.stale_evidence_count,
        row.evidence_item_count,
    ):
        raise ValueError("stale_evidence_pressure_ratio must match counts")
    if row.ambiguity_flag_pressure_ratio != _bounded_ratio(
        row.ambiguity_flag_count,
        row.evidence_item_count,
    ):
        raise ValueError("ambiguity_flag_pressure_ratio must match counts")
    if row.recheck_urgency_ratio != _bounded_ratio(
        row.pending_recheck_count,
        row.evidence_item_count,
    ):
        raise ValueError("recheck_urgency_ratio must match counts")
    expected_completeness = _completeness_score(
        rule_citation_coverage_ratio=row.rule_citation_coverage_ratio,
        source_agreement_ratio=row.source_agreement_ratio,
        stale_evidence_pressure_ratio=row.stale_evidence_pressure_ratio,
        ambiguity_flag_pressure_ratio=row.ambiguity_flag_pressure_ratio,
        recheck_urgency_ratio=row.recheck_urgency_ratio,
    )
    if row.completeness_score != expected_completeness:
        raise ValueError("completeness_score must match component ratios")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _validation_digest(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_report(report: ResearchResolutionVerificationPacketCompletenessReport) -> None:
    if report.packet_group_count != _count(len(report.rows)):
        raise ValueError("packet_group_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    for field_name in (
        "required_rule_citation_count",
        "cited_rule_count",
        "verification_source_count",
        "agreeing_source_count",
        "evidence_item_count",
        "stale_evidence_count",
        "ambiguity_flag_count",
        "pending_recheck_count",
    ):
        if getattr(report, field_name) != _row_sum(report.rows, field_name):
            raise ValueError(f"{field_name} must match rows")
    for field_name, expected_value in _report_ratios(_report_digest_values(report)).items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match aggregate counts")
    expected_min = None if not report.rows else min(row.completeness_score for row in report.rows)
    if report.min_completeness_score != expected_min:
        raise ValueError("min_completeness_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.validation_digest != _validation_digest(_report_digest_values(report)):
        raise ValueError("validation_digest must match report payload")


def _row_digest_values(
    row: ResearchResolutionVerificationPacketCompletenessRow,
) -> dict[str, Any]:
    return {
        "packet_group_ref": row.packet_group_ref,
        "required_rule_citation_count": row.required_rule_citation_count,
        "cited_rule_count": row.cited_rule_count,
        "verification_source_count": row.verification_source_count,
        "agreeing_source_count": row.agreeing_source_count,
        "evidence_item_count": row.evidence_item_count,
        "stale_evidence_count": row.stale_evidence_count,
        "ambiguity_flag_count": row.ambiguity_flag_count,
        "pending_recheck_count": row.pending_recheck_count,
        "rule_citation_coverage_ratio": row.rule_citation_coverage_ratio,
        "source_agreement_ratio": row.source_agreement_ratio,
        "stale_evidence_pressure_ratio": row.stale_evidence_pressure_ratio,
        "ambiguity_flag_pressure_ratio": row.ambiguity_flag_pressure_ratio,
        "recheck_urgency_ratio": row.recheck_urgency_ratio,
        "completeness_score": row.completeness_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchResolutionVerificationPacketCompletenessReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "packet_group_count": report.packet_group_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "required_rule_citation_count": report.required_rule_citation_count,
        "cited_rule_count": report.cited_rule_count,
        "verification_source_count": report.verification_source_count,
        "agreeing_source_count": report.agreeing_source_count,
        "evidence_item_count": report.evidence_item_count,
        "stale_evidence_count": report.stale_evidence_count,
        "ambiguity_flag_count": report.ambiguity_flag_count,
        "pending_recheck_count": report.pending_recheck_count,
        "rule_citation_coverage_ratio": report.rule_citation_coverage_ratio,
        "source_agreement_ratio": report.source_agreement_ratio,
        "stale_evidence_pressure_ratio": report.stale_evidence_pressure_ratio,
        "ambiguity_flag_pressure_ratio": report.ambiguity_flag_pressure_ratio,
        "recheck_urgency_ratio": report.recheck_urgency_ratio,
        "min_completeness_score": report.min_completeness_score,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_ratios(values: Mapping[str, Any]) -> dict[str, Decimal]:
    return {
        "rule_citation_coverage_ratio": _bounded_ratio(
            values["cited_rule_count"],
            values["required_rule_citation_count"],
        ),
        "source_agreement_ratio": _bounded_ratio(
            values["agreeing_source_count"],
            values["verification_source_count"],
        ),
        "stale_evidence_pressure_ratio": _bounded_ratio(
            values["stale_evidence_count"],
            values["evidence_item_count"],
        ),
        "ambiguity_flag_pressure_ratio": _bounded_ratio(
            values["ambiguity_flag_count"],
            values["evidence_item_count"],
        ),
        "recheck_urgency_ratio": _bounded_ratio(
            values["pending_recheck_count"],
            values["evidence_item_count"],
        ),
    }


def _row_sort_key(
    row: ResearchResolutionVerificationPacketCompletenessRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_WEIGHT[row.status], row.completeness_score, row.packet_group_ref)


def _row_sum(
    rows: tuple[ResearchResolutionVerificationPacketCompletenessRow, ...],
    field_name: str,
) -> Decimal:
    return _sum_decimal(tuple(getattr(row, field_name) for row in rows))


def _status_count(
    rows: tuple[ResearchResolutionVerificationPacketCompletenessRow, ...],
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
    if (
        "resolution_verification_packet_completeness_pass" in normalized
        and len(normalized) != 1
    ):
        raise ValueError("pass reason must stand alone")
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
    numerator = _normalize_decimal("numerator", numerator)
    denominator = _normalize_decimal("denominator", denominator)
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
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


def _require_lower_threshold_pair(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{lower_name} must be below {upper_name}")


def _require_upper_threshold_pair(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if upper_value <= lower_value:
        raise ValueError(f"{upper_name} must exceed {lower_name}")


def _require_status(name: str, value: object) -> None:
    _require_public_text(name, value)
    if value not in PUBLIC_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


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
