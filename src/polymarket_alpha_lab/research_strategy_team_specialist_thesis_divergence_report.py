"""Report-only reducer for strategy team specialist thesis divergence."""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_THESIS_DIVERGENCE_CONFIG_VERSION",
    "ResearchStrategyTeamSpecialistThesisDivergenceConfig",
    "ResearchStrategyTeamSpecialistThesisDivergenceInput",
    "ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount",
    "ResearchStrategyTeamSpecialistThesisDivergenceReport",
    "ResearchStrategyTeamSpecialistThesisDivergenceRow",
    "build_research_strategy_team_specialist_thesis_divergence_report",
    "research_strategy_team_specialist_thesis_divergence_report_digest",
    "research_strategy_team_specialist_thesis_divergence_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_THESIS_DIVERGENCE_CONFIG_VERSION = (
    "research-strategy-team-specialist-thesis-divergence-report-v1"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
_PASS_REASON = "specialist_thesis_divergence_pass"
_EMPTY_REASON = "no_specialist_thesis_divergence_inputs"
_ROW_REASON_PRIORITY = (
    "specialist_probability_gap_block",
    "team_consensus_gap_block",
    "evidence_alignment_gap_block",
    "resolution_rule_gap_block",
    "thesis_divergence_score_block",
    "specialist_probability_gap_watch",
    "team_consensus_gap_watch",
    "evidence_alignment_gap_watch",
    "resolution_rule_gap_watch",
    "thesis_divergence_score_watch",
    _PASS_REASON,
    _EMPTY_REASON,
)
_HEX_CHARS = frozenset("0123456789abcdef")


def _join(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        _join("raw", "_candidate", "_id"),
        _join("candidate", "_id"),
        _join("market", "_id"),
        _join("market", "_slug"),
        "slug",
        _join("ques", "tion"),
        _join("source", "_url"),
        _join("source", "_text"),
        _join("http", "://"),
        _join("https", "://"),
        _join("postgres", "://"),
        _join("d", "sn"),
        _join("table", "_name"),
        _join("tok", "en"),
        "wallet",
        "order",
        "trade",
        _join("live", " trading"),
        "live",
        "position",
        "sizing",
        "recommend",
        "buy",
        "sell",
        "execute",
        "execution",
        "auth",
        "secret",
        _join("api", "_key"),
        _join("private", "_key"),
    ),
)
_CONFIG_PAYLOAD_KEYS = frozenset(
    (
        "config_version",
        "specialist_gap_weight",
        "consensus_gap_weight",
        "evidence_gap_weight",
        "resolution_gap_weight",
        "pass_specialist_gap_ceiling",
        "block_specialist_gap_floor",
        "pass_consensus_gap_ceiling",
        "block_consensus_gap_floor",
        "pass_evidence_gap_ceiling",
        "block_evidence_gap_floor",
        "pass_resolution_gap_ceiling",
        "block_resolution_gap_floor",
        "pass_divergence_score_ceiling",
        "block_divergence_score_floor",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REPORT_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "config",
        "report_status",
        "thesis_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_thesis_divergence_score",
        "max_thesis_divergence_score",
        "max_specialist_probability_gap",
        "max_consensus_gap",
        "reason_codes",
        "rows",
        "reason_code_counts",
        "public_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_ROW_PAYLOAD_KEYS = frozenset(
    (
        "thesis_digest",
        "team_code",
        "lead_specialist_code",
        "challenger_specialist_code",
        "observed_at",
        "lead_thesis_probability",
        "challenger_thesis_probability",
        "team_consensus_probability",
        "evidence_alignment_score",
        "resolution_rule_clarity_score",
        "specialist_probability_gap",
        "lead_consensus_gap",
        "challenger_consensus_gap",
        "max_consensus_gap",
        "evidence_alignment_gap",
        "resolution_rule_gap",
        "thesis_divergence_score",
        "status",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistThesisDivergenceConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_THESIS_DIVERGENCE_CONFIG_VERSION
    )
    specialist_gap_weight: Decimal = Decimal("0.400000")
    consensus_gap_weight: Decimal = Decimal("0.250000")
    evidence_gap_weight: Decimal = Decimal("0.200000")
    resolution_gap_weight: Decimal = Decimal("0.150000")
    pass_specialist_gap_ceiling: Decimal = Decimal("0.100000")
    block_specialist_gap_floor: Decimal = Decimal("0.300000")
    pass_consensus_gap_ceiling: Decimal = Decimal("0.150000")
    block_consensus_gap_floor: Decimal = Decimal("0.350000")
    pass_evidence_gap_ceiling: Decimal = Decimal("0.200000")
    block_evidence_gap_floor: Decimal = Decimal("0.500000")
    pass_resolution_gap_ceiling: Decimal = Decimal("0.200000")
    block_resolution_gap_floor: Decimal = Decimal("0.500000")
    pass_divergence_score_ceiling: Decimal = Decimal("0.150000")
    block_divergence_score_floor: Decimal = Decimal("0.350000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchStrategyTeamSpecialistThesisDivergenceConfig "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistThesisDivergenceConfig,
            "config",
        )
        _require_supported_config_version(self.config_version)
        for field_name in (
            "specialist_gap_weight",
            "consensus_gap_weight",
            "evidence_gap_weight",
            "resolution_gap_weight",
            "pass_specialist_gap_ceiling",
            "block_specialist_gap_floor",
            "pass_consensus_gap_ceiling",
            "block_consensus_gap_floor",
            "pass_evidence_gap_ceiling",
            "block_evidence_gap_floor",
            "pass_resolution_gap_ceiling",
            "block_resolution_gap_floor",
            "pass_divergence_score_ceiling",
            "block_divergence_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "specialist_gap_weight",
            "consensus_gap_weight",
            "evidence_gap_weight",
            "resolution_gap_weight",
        ):
            if getattr(self, field_name) <= _ZERO:
                raise ValueError(f"{field_name} must be positive")
        if _quantize(
            self.specialist_gap_weight
            + self.consensus_gap_weight
            + self.evidence_gap_weight
            + self.resolution_gap_weight,
        ) != _ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_ordered_thresholds(
            "pass_specialist_gap_ceiling",
            self.pass_specialist_gap_ceiling,
            "block_specialist_gap_floor",
            self.block_specialist_gap_floor,
        )
        _require_ordered_thresholds(
            "pass_consensus_gap_ceiling",
            self.pass_consensus_gap_ceiling,
            "block_consensus_gap_floor",
            self.block_consensus_gap_floor,
        )
        _require_ordered_thresholds(
            "pass_evidence_gap_ceiling",
            self.pass_evidence_gap_ceiling,
            "block_evidence_gap_floor",
            self.block_evidence_gap_floor,
        )
        _require_ordered_thresholds(
            "pass_resolution_gap_ceiling",
            self.pass_resolution_gap_ceiling,
            "block_resolution_gap_floor",
            self.block_resolution_gap_floor,
        )
        _require_ordered_thresholds(
            "pass_divergence_score_ceiling",
            self.pass_divergence_score_ceiling,
            "block_divergence_score_floor",
            self.block_divergence_score_floor,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistThesisDivergenceInput:
    thesis_ref: str
    team_code: str
    lead_specialist_code: str
    challenger_specialist_code: str
    lead_thesis_probability: Decimal
    challenger_thesis_probability: Decimal
    team_consensus_probability: Decimal
    evidence_alignment_score: Decimal
    resolution_rule_clarity_score: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchStrategyTeamSpecialistThesisDivergenceInput "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistThesisDivergenceInput,
            "input",
        )
        _require_private_identifier("thesis_ref", self.thesis_ref)
        for field_name in (
            "team_code",
            "lead_specialist_code",
            "challenger_specialist_code",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        for field_name in (
            "lead_thesis_probability",
            "challenger_thesis_probability",
            "team_consensus_probability",
            "evidence_alignment_score",
            "resolution_rule_clarity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistThesisDivergenceRow:
    thesis_digest: str
    team_code: str
    lead_specialist_code: str
    challenger_specialist_code: str
    observed_at: datetime
    lead_thesis_probability: Decimal
    challenger_thesis_probability: Decimal
    team_consensus_probability: Decimal
    evidence_alignment_score: Decimal
    resolution_rule_clarity_score: Decimal
    specialist_probability_gap: Decimal
    lead_consensus_gap: Decimal
    challenger_consensus_gap: Decimal
    max_consensus_gap: Decimal
    evidence_alignment_gap: Decimal
    resolution_rule_gap: Decimal
    thesis_divergence_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchStrategyTeamSpecialistThesisDivergenceRow "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistThesisDivergenceRow,
            "row",
        )
        _require_digest_label("thesis_digest", self.thesis_digest)
        for field_name in (
            "team_code",
            "lead_specialist_code",
            "challenger_specialist_code",
        ):
            _require_public_text(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "lead_thesis_probability",
            "challenger_thesis_probability",
            "team_consensus_probability",
            "evidence_alignment_score",
            "resolution_rule_clarity_score",
            "specialist_probability_gap",
            "lead_consensus_gap",
            "challenger_consensus_gap",
            "max_consensus_gap",
            "evidence_alignment_gap",
            "resolution_rule_gap",
            "thesis_divergence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_digest("validation_digest", self.validation_digest)
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        object.__setattr__(self, "row_ratio", _normalize_ratio("row_ratio", self.row_ratio))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyTeamSpecialistThesisDivergenceReport:
    generated_at: datetime
    config_version: str
    config: ResearchStrategyTeamSpecialistThesisDivergenceConfig
    report_status: str
    thesis_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_thesis_divergence_score: Decimal
    max_thesis_divergence_score: Decimal
    max_specialist_probability_gap: Decimal
    max_consensus_gap: Decimal
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchStrategyTeamSpecialistThesisDivergenceRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount,
        ...,
    ]
    public_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchStrategyTeamSpecialistThesisDivergenceReport "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamSpecialistThesisDivergenceReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_supported_config_version(self.config_version)
        _validate_config(self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_status("report_status", self.report_status)
        for field_name in (
            "thesis_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_thesis_divergence_score",
            "max_thesis_divergence_score",
            "max_specialist_probability_gap",
            "max_consensus_gap",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _require_digest("public_digest", self.public_digest)
        _require_hard_flags("report", self)
        _validate_report(self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_team_specialist_thesis_divergence_report_payload(self)


def build_research_strategy_team_specialist_thesis_divergence_report(
    items: Iterable[ResearchStrategyTeamSpecialistThesisDivergenceInput],
    *,
    config: ResearchStrategyTeamSpecialistThesisDivergenceConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamSpecialistThesisDivergenceReport:
    if type(config) is not ResearchStrategyTeamSpecialistThesisDivergenceConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamSpecialistThesisDivergenceConfig",
        )
    _validate_config(config)
    generated_at = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(items)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in inputs),
            key=_row_sort_key,
        ),
    )
    report_values = _report_values(
        generated_at=generated_at,
        config_version=config.config_version,
        config=config,
        rows=rows,
    )
    return ResearchStrategyTeamSpecialistThesisDivergenceReport(
        **report_values,
        public_digest=_digest_from_mapping(report_values),
    )


def research_strategy_team_specialist_thesis_divergence_report_digest(
    report: ResearchStrategyTeamSpecialistThesisDivergenceReport,
) -> str:
    if type(report) is not ResearchStrategyTeamSpecialistThesisDivergenceReport:
        raise ValueError(
            "report must be a ResearchStrategyTeamSpecialistThesisDivergenceReport",
        )
    _validate_report(report)
    return report.public_digest


def research_strategy_team_specialist_thesis_divergence_report_payload(
    report: ResearchStrategyTeamSpecialistThesisDivergenceReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTeamSpecialistThesisDivergenceReport:
        _validate_report(report)
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchStrategyTeamSpecialistThesisDivergenceReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_payload("payload", payload)
    _reject_flag_downgrades("payload", payload)
    _require_payload_flags(payload)
    _validate_public_payload(payload)
    return _json_ready(payload)


def _normalize_inputs(
    items: Iterable[ResearchStrategyTeamSpecialistThesisDivergenceInput],
) -> tuple[ResearchStrategyTeamSpecialistThesisDivergenceInput, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("items must be an iterable")
    try:
        rows = tuple(items)
    except TypeError as exc:
        raise ValueError("items must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamSpecialistThesisDivergenceInput:
            raise ValueError(
                "items must contain ResearchStrategyTeamSpecialistThesisDivergenceInput",
            )
        _require_hard_flags("input", row)
        if row.thesis_ref in seen_refs:
            raise ValueError("thesis_ref values must be unique")
        seen_refs.add(row.thesis_ref)
    return rows


def _row_from_input(
    item: ResearchStrategyTeamSpecialistThesisDivergenceInput,
    *,
    config: ResearchStrategyTeamSpecialistThesisDivergenceConfig,
) -> ResearchStrategyTeamSpecialistThesisDivergenceRow:
    specialist_probability_gap = _absolute_gap(
        item.lead_thesis_probability,
        item.challenger_thesis_probability,
    )
    lead_consensus_gap = _absolute_gap(
        item.lead_thesis_probability,
        item.team_consensus_probability,
    )
    challenger_consensus_gap = _absolute_gap(
        item.challenger_thesis_probability,
        item.team_consensus_probability,
    )
    max_consensus_gap = max(lead_consensus_gap, challenger_consensus_gap)
    evidence_alignment_gap = _quantize(_ONE - item.evidence_alignment_score)
    resolution_rule_gap = _quantize(_ONE - item.resolution_rule_clarity_score)
    thesis_divergence_score = _divergence_score(
        specialist_probability_gap=specialist_probability_gap,
        max_consensus_gap=max_consensus_gap,
        evidence_alignment_gap=evidence_alignment_gap,
        resolution_rule_gap=resolution_rule_gap,
        config=config,
    )
    reason_codes = _row_reason_codes(
        specialist_probability_gap=specialist_probability_gap,
        max_consensus_gap=max_consensus_gap,
        evidence_alignment_gap=evidence_alignment_gap,
        resolution_rule_gap=resolution_rule_gap,
        thesis_divergence_score=thesis_divergence_score,
        config=config,
    )
    row_values = {
        "thesis_digest": _digest_label(item.thesis_ref),
        "team_code": item.team_code,
        "lead_specialist_code": item.lead_specialist_code,
        "challenger_specialist_code": item.challenger_specialist_code,
        "observed_at": item.observed_at,
        "lead_thesis_probability": item.lead_thesis_probability,
        "challenger_thesis_probability": item.challenger_thesis_probability,
        "team_consensus_probability": item.team_consensus_probability,
        "evidence_alignment_score": item.evidence_alignment_score,
        "resolution_rule_clarity_score": item.resolution_rule_clarity_score,
        "specialist_probability_gap": specialist_probability_gap,
        "lead_consensus_gap": lead_consensus_gap,
        "challenger_consensus_gap": challenger_consensus_gap,
        "max_consensus_gap": max_consensus_gap,
        "evidence_alignment_gap": evidence_alignment_gap,
        "resolution_rule_gap": resolution_rule_gap,
        "thesis_divergence_score": thesis_divergence_score,
        "status": _status_from_reason_codes(reason_codes),
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyTeamSpecialistThesisDivergenceRow(
        **row_values,
        validation_digest=_digest_from_mapping(row_values),
    )


def _divergence_score(
    *,
    specialist_probability_gap: Decimal,
    max_consensus_gap: Decimal,
    evidence_alignment_gap: Decimal,
    resolution_rule_gap: Decimal,
    config: ResearchStrategyTeamSpecialistThesisDivergenceConfig,
) -> Decimal:
    return _quantize(
        (specialist_probability_gap * config.specialist_gap_weight)
        + (max_consensus_gap * config.consensus_gap_weight)
        + (evidence_alignment_gap * config.evidence_gap_weight)
        + (resolution_rule_gap * config.resolution_gap_weight),
    )


def _row_reason_codes(
    *,
    specialist_probability_gap: Decimal,
    max_consensus_gap: Decimal,
    evidence_alignment_gap: Decimal,
    resolution_rule_gap: Decimal,
    thesis_divergence_score: Decimal,
    config: ResearchStrategyTeamSpecialistThesisDivergenceConfig,
) -> tuple[str, ...]:
    block_reasons: list[str] = []
    watch_reasons: list[str] = []
    _append_threshold_reason(
        block_reasons,
        watch_reasons,
        value=specialist_probability_gap,
        pass_ceiling=config.pass_specialist_gap_ceiling,
        block_floor=config.block_specialist_gap_floor,
        block_reason="specialist_probability_gap_block",
        watch_reason="specialist_probability_gap_watch",
    )
    _append_threshold_reason(
        block_reasons,
        watch_reasons,
        value=max_consensus_gap,
        pass_ceiling=config.pass_consensus_gap_ceiling,
        block_floor=config.block_consensus_gap_floor,
        block_reason="team_consensus_gap_block",
        watch_reason="team_consensus_gap_watch",
    )
    _append_threshold_reason(
        block_reasons,
        watch_reasons,
        value=evidence_alignment_gap,
        pass_ceiling=config.pass_evidence_gap_ceiling,
        block_floor=config.block_evidence_gap_floor,
        block_reason="evidence_alignment_gap_block",
        watch_reason="evidence_alignment_gap_watch",
    )
    _append_threshold_reason(
        block_reasons,
        watch_reasons,
        value=resolution_rule_gap,
        pass_ceiling=config.pass_resolution_gap_ceiling,
        block_floor=config.block_resolution_gap_floor,
        block_reason="resolution_rule_gap_block",
        watch_reason="resolution_rule_gap_watch",
    )
    _append_threshold_reason(
        block_reasons,
        watch_reasons,
        value=thesis_divergence_score,
        pass_ceiling=config.pass_divergence_score_ceiling,
        block_floor=config.block_divergence_score_floor,
        block_reason="thesis_divergence_score_block",
        watch_reason="thesis_divergence_score_watch",
    )
    reason_codes = tuple(block_reasons + watch_reasons)
    if not reason_codes:
        reason_codes = (_PASS_REASON,)
    return _normalize_reason_codes("reason_codes", reason_codes)


def _append_threshold_reason(
    block_reasons: list[str],
    watch_reasons: list[str],
    *,
    value: Decimal,
    pass_ceiling: Decimal,
    block_floor: Decimal,
    block_reason: str,
    watch_reason: str,
) -> None:
    if value >= block_floor:
        block_reasons.append(block_reason)
    elif value > pass_ceiling:
        watch_reasons.append(watch_reason)


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    config: ResearchStrategyTeamSpecialistThesisDivergenceConfig,
    rows: tuple[ResearchStrategyTeamSpecialistThesisDivergenceRow, ...],
) -> dict[str, Any]:
    reason_codes = _report_reason_codes(rows)
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "config": config,
        "report_status": _report_status(rows),
        "thesis_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_thesis_divergence_score": _average_or_zero(
            tuple(row.thesis_divergence_score for row in rows),
        ),
        "max_thesis_divergence_score": _max_or_zero(
            tuple(row.thesis_divergence_score for row in rows),
        ),
        "max_specialist_probability_gap": _max_or_zero(
            tuple(row.specialist_probability_gap for row in rows),
        ),
        "max_consensus_gap": _max_or_zero(tuple(row.max_consensus_gap for row in rows)),
        "reason_codes": reason_codes,
        "rows": rows,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_config(
    config: ResearchStrategyTeamSpecialistThesisDivergenceConfig,
) -> None:
    _require_exact_type(
        config,
        ResearchStrategyTeamSpecialistThesisDivergenceConfig,
        "config",
    )
    _require_supported_config_version(config.config_version)
    for field_name in (
        "specialist_gap_weight",
        "consensus_gap_weight",
        "evidence_gap_weight",
        "resolution_gap_weight",
        "pass_specialist_gap_ceiling",
        "block_specialist_gap_floor",
        "pass_consensus_gap_ceiling",
        "block_consensus_gap_floor",
        "pass_evidence_gap_ceiling",
        "block_evidence_gap_floor",
        "pass_resolution_gap_ceiling",
        "block_resolution_gap_floor",
        "pass_divergence_score_ceiling",
        "block_divergence_score_floor",
    ):
        value = getattr(config, field_name)
        if value != _normalize_ratio(field_name, value):
            raise ValueError(f"{field_name} must be normalized")
    for field_name in (
        "specialist_gap_weight",
        "consensus_gap_weight",
        "evidence_gap_weight",
        "resolution_gap_weight",
    ):
        if getattr(config, field_name) <= _ZERO:
            raise ValueError(f"{field_name} must be positive")
    if _quantize(
        config.specialist_gap_weight
        + config.consensus_gap_weight
        + config.evidence_gap_weight
        + config.resolution_gap_weight,
    ) != _ONE:
        raise ValueError("weights must sum to 1.000000")
    _require_ordered_thresholds(
        "pass_specialist_gap_ceiling",
        config.pass_specialist_gap_ceiling,
        "block_specialist_gap_floor",
        config.block_specialist_gap_floor,
    )
    _require_ordered_thresholds(
        "pass_consensus_gap_ceiling",
        config.pass_consensus_gap_ceiling,
        "block_consensus_gap_floor",
        config.block_consensus_gap_floor,
    )
    _require_ordered_thresholds(
        "pass_evidence_gap_ceiling",
        config.pass_evidence_gap_ceiling,
        "block_evidence_gap_floor",
        config.block_evidence_gap_floor,
    )
    _require_ordered_thresholds(
        "pass_resolution_gap_ceiling",
        config.pass_resolution_gap_ceiling,
        "block_resolution_gap_floor",
        config.block_resolution_gap_floor,
    )
    _require_ordered_thresholds(
        "pass_divergence_score_ceiling",
        config.pass_divergence_score_ceiling,
        "block_divergence_score_floor",
        config.block_divergence_score_floor,
    )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)


def _validate_row(row: ResearchStrategyTeamSpecialistThesisDivergenceRow) -> None:
    if row.specialist_probability_gap != _absolute_gap(
        row.lead_thesis_probability,
        row.challenger_thesis_probability,
    ):
        raise ValueError("specialist_probability_gap must match probabilities")
    if row.lead_consensus_gap != _absolute_gap(
        row.lead_thesis_probability,
        row.team_consensus_probability,
    ):
        raise ValueError("lead_consensus_gap must match probabilities")
    if row.challenger_consensus_gap != _absolute_gap(
        row.challenger_thesis_probability,
        row.team_consensus_probability,
    ):
        raise ValueError("challenger_consensus_gap must match probabilities")
    if row.max_consensus_gap != max(row.lead_consensus_gap, row.challenger_consensus_gap):
        raise ValueError("max_consensus_gap must match consensus gaps")
    if row.evidence_alignment_gap != _quantize(_ONE - row.evidence_alignment_score):
        raise ValueError("evidence_alignment_gap must match evidence score")
    if row.resolution_rule_gap != _quantize(_ONE - row.resolution_rule_clarity_score):
        raise ValueError("resolution_rule_gap must match resolution score")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.validation_digest != _digest_from_mapping(_row_digest_values(row)):
        raise ValueError("validation_digest must match row payload")


def _validate_row_against_config(
    row: ResearchStrategyTeamSpecialistThesisDivergenceRow,
    config: ResearchStrategyTeamSpecialistThesisDivergenceConfig,
) -> None:
    expected_score = _divergence_score(
        specialist_probability_gap=row.specialist_probability_gap,
        max_consensus_gap=row.max_consensus_gap,
        evidence_alignment_gap=row.evidence_alignment_gap,
        resolution_rule_gap=row.resolution_rule_gap,
        config=config,
    )
    if row.thesis_divergence_score != expected_score:
        raise ValueError("thesis_divergence_score must match config and row gaps")
    expected_reason_codes = _row_reason_codes(
        specialist_probability_gap=row.specialist_probability_gap,
        max_consensus_gap=row.max_consensus_gap,
        evidence_alignment_gap=row.evidence_alignment_gap,
        resolution_rule_gap=row.resolution_rule_gap,
        thesis_divergence_score=row.thesis_divergence_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match config and row values")


def _validate_report(
    report: ResearchStrategyTeamSpecialistThesisDivergenceReport,
) -> None:
    rows = report.rows
    _require_hard_flags("report", report)
    _validate_config(report.config)
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    for row in rows:
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
        _validate_row(row)
        _validate_row_against_config(row, report.config)
    if report.thesis_count != _count(len(rows)):
        raise ValueError("thesis_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_thesis_divergence_score != _average_or_zero(
        tuple(row.thesis_divergence_score for row in rows),
    ):
        raise ValueError("average_thesis_divergence_score must match rows")
    if report.max_thesis_divergence_score != _max_or_zero(
        tuple(row.thesis_divergence_score for row in rows),
    ):
        raise ValueError("max_thesis_divergence_score must match rows")
    if report.max_specialist_probability_gap != _max_or_zero(
        tuple(row.specialist_probability_gap for row in rows),
    ):
        raise ValueError("max_specialist_probability_gap must match rows")
    if report.max_consensus_gap != _max_or_zero(tuple(row.max_consensus_gap for row in rows)):
        raise ValueError("max_consensus_gap must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report payload")


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _require_exact_payload_keys("public payload", payload, _REPORT_PAYLOAD_KEYS)
    _require_payload_flags(payload)
    _require_status("report_status", payload.get("report_status"))
    _require_payload_reason_codes("reason_codes", payload.get("reason_codes"))
    config = _config_from_public_payload(payload.get("config"))
    rows_payload = payload.get("rows")
    if type(rows_payload) is not list:
        raise ValueError("rows must be a list in public payload")
    rows = tuple(_row_from_public_payload(row) for row in rows_payload)
    reason_code_counts_payload = payload.get("reason_code_counts")
    if type(reason_code_counts_payload) is not list:
        raise ValueError("reason_code_counts must be a list in public payload")
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(item)
        for item in reason_code_counts_payload
    )
    supplied_digest = payload.get("public_digest")
    _require_digest("public_digest", supplied_digest)
    if supplied_digest != _payload_report_digest(payload):
        raise ValueError("public_digest must match public payload")
    reconstructed = ResearchStrategyTeamSpecialistThesisDivergenceReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            payload.get("generated_at"),
        ),
        config_version=_require_supported_config_version(
            payload.get("config_version"),
        ),
        config=config,
        report_status=_require_status(
            "report_status",
            payload.get("report_status"),
        ),
        thesis_count=_decimal_from_public_payload(
            "thesis_count",
            payload.get("thesis_count"),
            count=True,
        ),
        pass_count=_decimal_from_public_payload(
            "pass_count",
            payload.get("pass_count"),
            count=True,
        ),
        watch_count=_decimal_from_public_payload(
            "watch_count",
            payload.get("watch_count"),
            count=True,
        ),
        block_count=_decimal_from_public_payload(
            "block_count",
            payload.get("block_count"),
            count=True,
        ),
        average_thesis_divergence_score=_decimal_from_public_payload(
            "average_thesis_divergence_score",
            payload.get("average_thesis_divergence_score"),
        ),
        max_thesis_divergence_score=_decimal_from_public_payload(
            "max_thesis_divergence_score",
            payload.get("max_thesis_divergence_score"),
        ),
        max_specialist_probability_gap=_decimal_from_public_payload(
            "max_specialist_probability_gap",
            payload.get("max_specialist_probability_gap"),
        ),
        max_consensus_gap=_decimal_from_public_payload(
            "max_consensus_gap",
            payload.get("max_consensus_gap"),
        ),
        reason_codes=_require_payload_reason_codes(
            "reason_codes",
            payload.get("reason_codes"),
        ),
        rows=rows,
        reason_code_counts=reason_code_counts,
        public_digest=supplied_digest,
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    if _json_ready(reconstructed) != payload:
        raise ValueError("public payload must use canonical values")


def _config_from_public_payload(
    value: object,
) -> ResearchStrategyTeamSpecialistThesisDivergenceConfig:
    if type(value) is not dict:
        raise ValueError("config must be an object in public payload")
    _require_exact_payload_keys("config payload", value, _CONFIG_PAYLOAD_KEYS)
    _require_payload_flags(value)
    config = ResearchStrategyTeamSpecialistThesisDivergenceConfig(
        config_version=_require_supported_config_version(value.get("config_version")),
        specialist_gap_weight=_decimal_from_public_payload(
            "specialist_gap_weight",
            value.get("specialist_gap_weight"),
        ),
        consensus_gap_weight=_decimal_from_public_payload(
            "consensus_gap_weight",
            value.get("consensus_gap_weight"),
        ),
        evidence_gap_weight=_decimal_from_public_payload(
            "evidence_gap_weight",
            value.get("evidence_gap_weight"),
        ),
        resolution_gap_weight=_decimal_from_public_payload(
            "resolution_gap_weight",
            value.get("resolution_gap_weight"),
        ),
        pass_specialist_gap_ceiling=_decimal_from_public_payload(
            "pass_specialist_gap_ceiling",
            value.get("pass_specialist_gap_ceiling"),
        ),
        block_specialist_gap_floor=_decimal_from_public_payload(
            "block_specialist_gap_floor",
            value.get("block_specialist_gap_floor"),
        ),
        pass_consensus_gap_ceiling=_decimal_from_public_payload(
            "pass_consensus_gap_ceiling",
            value.get("pass_consensus_gap_ceiling"),
        ),
        block_consensus_gap_floor=_decimal_from_public_payload(
            "block_consensus_gap_floor",
            value.get("block_consensus_gap_floor"),
        ),
        pass_evidence_gap_ceiling=_decimal_from_public_payload(
            "pass_evidence_gap_ceiling",
            value.get("pass_evidence_gap_ceiling"),
        ),
        block_evidence_gap_floor=_decimal_from_public_payload(
            "block_evidence_gap_floor",
            value.get("block_evidence_gap_floor"),
        ),
        pass_resolution_gap_ceiling=_decimal_from_public_payload(
            "pass_resolution_gap_ceiling",
            value.get("pass_resolution_gap_ceiling"),
        ),
        block_resolution_gap_floor=_decimal_from_public_payload(
            "block_resolution_gap_floor",
            value.get("block_resolution_gap_floor"),
        ),
        pass_divergence_score_ceiling=_decimal_from_public_payload(
            "pass_divergence_score_ceiling",
            value.get("pass_divergence_score_ceiling"),
        ),
        block_divergence_score_floor=_decimal_from_public_payload(
            "block_divergence_score_floor",
            value.get("block_divergence_score_floor"),
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )
    if _json_ready(config) != value:
        raise ValueError("config payload must use canonical values")
    return config


def _row_from_public_payload(
    value: object,
) -> ResearchStrategyTeamSpecialistThesisDivergenceRow:
    if type(value) is not dict:
        raise ValueError("rows must contain objects in public payload")
    _require_exact_payload_keys("row payload", value, _ROW_PAYLOAD_KEYS)
    _require_payload_flags(value)
    thesis_digest = value.get("thesis_digest")
    _require_digest_label("thesis_digest", thesis_digest)
    validation_digest = value.get("validation_digest")
    _require_digest("validation_digest", validation_digest)
    if validation_digest != _payload_row_digest(value):
        raise ValueError("validation_digest must match row payload")
    return ResearchStrategyTeamSpecialistThesisDivergenceRow(
        thesis_digest=thesis_digest,
        team_code=_require_public_text("team_code", value.get("team_code")),
        lead_specialist_code=_require_public_text(
            "lead_specialist_code",
            value.get("lead_specialist_code"),
        ),
        challenger_specialist_code=_require_public_text(
            "challenger_specialist_code",
            value.get("challenger_specialist_code"),
        ),
        observed_at=_datetime_from_public_payload(
            "observed_at",
            value.get("observed_at"),
        ),
        lead_thesis_probability=_decimal_from_public_payload(
            "lead_thesis_probability",
            value.get("lead_thesis_probability"),
        ),
        challenger_thesis_probability=_decimal_from_public_payload(
            "challenger_thesis_probability",
            value.get("challenger_thesis_probability"),
        ),
        team_consensus_probability=_decimal_from_public_payload(
            "team_consensus_probability",
            value.get("team_consensus_probability"),
        ),
        evidence_alignment_score=_decimal_from_public_payload(
            "evidence_alignment_score",
            value.get("evidence_alignment_score"),
        ),
        resolution_rule_clarity_score=_decimal_from_public_payload(
            "resolution_rule_clarity_score",
            value.get("resolution_rule_clarity_score"),
        ),
        specialist_probability_gap=_decimal_from_public_payload(
            "specialist_probability_gap",
            value.get("specialist_probability_gap"),
        ),
        lead_consensus_gap=_decimal_from_public_payload(
            "lead_consensus_gap",
            value.get("lead_consensus_gap"),
        ),
        challenger_consensus_gap=_decimal_from_public_payload(
            "challenger_consensus_gap",
            value.get("challenger_consensus_gap"),
        ),
        max_consensus_gap=_decimal_from_public_payload(
            "max_consensus_gap",
            value.get("max_consensus_gap"),
        ),
        evidence_alignment_gap=_decimal_from_public_payload(
            "evidence_alignment_gap",
            value.get("evidence_alignment_gap"),
        ),
        resolution_rule_gap=_decimal_from_public_payload(
            "resolution_rule_gap",
            value.get("resolution_rule_gap"),
        ),
        thesis_divergence_score=_decimal_from_public_payload(
            "thesis_divergence_score",
            value.get("thesis_divergence_score"),
        ),
        status=_require_status("status", value.get("status")),
        reason_codes=_require_payload_reason_codes(
            "reason_codes",
            value.get("reason_codes"),
        ),
        validation_digest=validation_digest,
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _reason_code_count_from_public_payload(
    value: object,
) -> ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain objects in public payload")
    _require_exact_payload_keys(
        "reason code count payload",
        value,
        _REASON_CODE_COUNT_PAYLOAD_KEYS,
    )
    _require_payload_flags(value)
    return ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount(
        reason_code=_require_payload_reason_codes(
            "reason_code",
            [value.get("reason_code")],
        )[0],
        count=_decimal_from_public_payload(
            "count",
            value.get("count"),
            count=True,
        ),
        row_ratio=_decimal_from_public_payload(
            "row_ratio",
            value.get("row_ratio"),
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _decimal_from_public_payload(
    field_name: str,
    value: object,
    *,
    count: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = (
        _normalize_count(field_name, parsed)
        if count
        else _normalize_ratio(field_name, parsed)
    )
    if format(normalized, "f") != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _datetime_from_public_payload(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be a canonical UTC datetime string",
        ) from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _row_digest_values(
    row: ResearchStrategyTeamSpecialistThesisDivergenceRow,
) -> dict[str, Any]:
    return {
        "thesis_digest": row.thesis_digest,
        "team_code": row.team_code,
        "lead_specialist_code": row.lead_specialist_code,
        "challenger_specialist_code": row.challenger_specialist_code,
        "observed_at": row.observed_at,
        "lead_thesis_probability": row.lead_thesis_probability,
        "challenger_thesis_probability": row.challenger_thesis_probability,
        "team_consensus_probability": row.team_consensus_probability,
        "evidence_alignment_score": row.evidence_alignment_score,
        "resolution_rule_clarity_score": row.resolution_rule_clarity_score,
        "specialist_probability_gap": row.specialist_probability_gap,
        "lead_consensus_gap": row.lead_consensus_gap,
        "challenger_consensus_gap": row.challenger_consensus_gap,
        "max_consensus_gap": row.max_consensus_gap,
        "evidence_alignment_gap": row.evidence_alignment_gap,
        "resolution_rule_gap": row.resolution_rule_gap,
        "thesis_divergence_score": row.thesis_divergence_score,
        "status": row.status,
        "reason_codes": row.reason_codes,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_digest_values(
    report: ResearchStrategyTeamSpecialistThesisDivergenceReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "config": report.config,
        "report_status": report.report_status,
        "thesis_count": report.thesis_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "average_thesis_divergence_score": report.average_thesis_divergence_score,
        "max_thesis_divergence_score": report.max_thesis_divergence_score,
        "max_specialist_probability_gap": report.max_specialist_probability_gap,
        "max_consensus_gap": report.max_consensus_gap,
        "reason_codes": report.reason_codes,
        "rows": report.rows,
        "reason_code_counts": report.reason_code_counts,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _computed_report_digest(
    report: ResearchStrategyTeamSpecialistThesisDivergenceReport,
) -> str:
    return _digest_from_mapping(_report_digest_values(report))


def _payload_row_digest(row: dict[str, Any]) -> str:
    return _digest_from_mapping({key: value for key, value in row.items() if key != "validation_digest"})


def _payload_report_digest(payload: dict[str, Any]) -> str:
    return _digest_from_mapping({key: value for key, value in payload.items() if key != "public_digest"})


def _digest_from_mapping(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    encoded = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _digest_label(value: str) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("utf-8")
    return f"sha256:{sha256(encoded).hexdigest()}"


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(value, "f")
    if type(value) is datetime:
        _require_aware_datetime("JSON datetime value", value)
        return value.astimezone(UTC).isoformat()
    if value is None or type(value) is bool:
        return value
    if type(value) is str:
        _require_public_text("JSON string value", value)
        return value
    if type(value) in (int, float):
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_public_text("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _normalize_rows(
    rows: tuple[ResearchStrategyTeamSpecialistThesisDivergenceRow, ...],
) -> tuple[ResearchStrategyTeamSpecialistThesisDivergenceRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchStrategyTeamSpecialistThesisDivergenceRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamSpecialistThesisDivergenceRow",
            )
        _require_hard_flags("row", row)
        _validate_row(row)
    thesis_digests = tuple(row.thesis_digest for row in rows)
    if len(set(thesis_digests)) != len(thesis_digests):
        raise ValueError("thesis_digest values must be unique")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    items: tuple[
        ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount, ...]:
    if type(items) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in items:
        if type(item) is not ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    return items


def _normalize_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not tuple or not reason_codes:
        raise ValueError(f"{field_name} must be a non-empty tuple")
    normalized = tuple(_require_reason_code(field_name, value) for value in reason_codes)
    unknown = tuple(value for value in normalized if value not in _ROW_REASON_PRIORITY)
    if unknown:
        raise ValueError(f"{field_name} contains unsupported reason code")
    if len(tuple(dict.fromkeys(normalized))) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(normalized, key=_reason_rank))


def _require_payload_reason_codes(field_name: str, reason_codes: object) -> tuple[str, ...]:
    if type(reason_codes) is not list or not reason_codes:
        raise ValueError(f"{field_name} must be a non-empty list in public payload")
    return _normalize_reason_codes(field_name, tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamSpecialistThesisDivergenceRow, ...],
    report_reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount(
                reason_code=_EMPTY_REASON,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    total = _count(len(rows))
    return tuple(
        ResearchStrategyTeamSpecialistThesisDivergenceReasonCodeCount(
            reason_code=reason_code,
            count=count,
            row_ratio=_ratio(count, total),
        )
        for reason_code in report_reason_codes
        for count in (_count(sum(1 for row in rows if reason_code in row.reason_codes)),)
        if count > _ZERO
    )


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamSpecialistThesisDivergenceRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    reasons = tuple(reason for row in rows for reason in row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(dict.fromkeys(reasons)))


def _report_status(
    rows: tuple[ResearchStrategyTeamSpecialistThesisDivergenceRow, ...],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _row_sort_key(
    row: ResearchStrategyTeamSpecialistThesisDivergenceRow,
) -> tuple[int, Decimal, str]:
    return (
        _STATUS_RANK[row.status],
        _ONE - row.thesis_divergence_score,
        row.thesis_digest,
    )


def _status_count(
    rows: tuple[ResearchStrategyTeamSpecialistThesisDivergenceRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _average_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _ratio(sum(values, _ZERO), _count(len(values)))


def _max_or_zero(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(max(values))


def _absolute_gap(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(abs(left - right))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        raise ValueError("ratio denominator must be non-zero")
    return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a non-negative int")
    return _quantize(Decimal(value))


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal count")
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _normalize_ratio(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    normalized = _quantize(value)
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError("value must be a Decimal")
    if not value.is_finite():
        raise ValueError("value must be finite")
    try:
        return value.quantize(_QUANT, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("value must be quantizable to six decimal places") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_aware_datetime(field_name: str, value: datetime) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_private_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty without surrounding whitespace")
    if _has_unsafe_fragment(value):
        raise ValueError(f"unsafe value in {field_name}")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    value = _require_public_text(field_name, value)
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    if not all(character == "_" or character.isalnum() for character in value):
        raise ValueError(f"{field_name} must contain reason code text")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_RANK:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_supported_config_version(value: object) -> str:
    config_version = _require_public_text("config_version", value)
    if (
        config_version
        != DEFAULT_RESEARCH_STRATEGY_TEAM_SPECIALIST_THESIS_DIVERGENCE_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    return config_version


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64 or any(char not in _HEX_CHARS for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_digest_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a sha256 digest label")
    _require_digest(field_name, value.removeprefix("sha256:"))


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for {label}")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True for payload")


def _require_exact_payload_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    if frozenset(payload) != expected_keys:
        raise ValueError(f"{label} contains unexpected fields")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, _json_ready(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _require_ordered_thresholds(
    pass_name: str,
    pass_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if pass_value >= block_value:
        raise ValueError(f"{pass_name} must be less than {block_name}")


def _reason_rank(reason_code: str) -> int:
    return _ROW_REASON_PRIORITY.index(reason_code)
