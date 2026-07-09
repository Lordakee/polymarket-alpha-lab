"""Pure report-only research strategy team evidence authority ladder report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_EVIDENCE_AUTHORITY_LADDER_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_TEAM_EVIDENCE_AUTHORITY_LADDER_REPORT_STATUSES",
    "ResearchStrategyTeamEvidenceAuthorityLadderConfig",
    "ResearchStrategyTeamEvidenceAuthorityLadderInput",
    "ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount",
    "ResearchStrategyTeamEvidenceAuthorityLadderReport",
    "ResearchStrategyTeamEvidenceAuthorityLadderRow",
    "build_research_strategy_team_evidence_authority_ladder_report",
    "research_strategy_team_evidence_authority_ladder_report_digest",
    "research_strategy_team_evidence_authority_ladder_report_payload",
    "validate_research_strategy_team_evidence_authority_ladder_public_payload",
    "validate_research_strategy_team_evidence_authority_ladder_report_digest",
)


DEFAULT_RESEARCH_STRATEGY_TEAM_EVIDENCE_AUTHORITY_LADDER_REPORT_CONFIG_VERSION = (
    "research-strategy-team-evidence-authority-ladder-report-v0"
)
RESEARCH_STRATEGY_TEAM_EVIDENCE_AUTHORITY_LADDER_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIX = Decimal("6.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}

NO_INPUTS_REASON = "research_strategy_team_evidence_authority_ladder_no_inputs"
CLEAR_REASON = "research_strategy_team_evidence_authority_ladder_clear"
AUTHORITY_COUNT_BLOCK_REASON = (
    "research_strategy_team_evidence_authority_ladder_authority_count_block"
)
CONFIRMATION_COUNT_BLOCK_REASON = (
    "research_strategy_team_evidence_authority_ladder_confirmation_count_block"
)
PRIMARY_AUTHORITY_BLOCK_REASON = (
    "research_strategy_team_evidence_authority_ladder_primary_authority_block"
)
CORROBORATION_BLOCK_REASON = (
    "research_strategy_team_evidence_authority_ladder_corroboration_block"
)
CONFLICT_BLOCK_REASON = "research_strategy_team_evidence_authority_ladder_conflict_block"
FRESHNESS_BLOCK_REASON = (
    "research_strategy_team_evidence_authority_ladder_freshness_block"
)
SCORE_BLOCK_REASON = "research_strategy_team_evidence_authority_ladder_score_block"
AUTHORITY_COUNT_WATCH_REASON = (
    "research_strategy_team_evidence_authority_ladder_authority_count_watch"
)
CONFIRMATION_COUNT_WATCH_REASON = (
    "research_strategy_team_evidence_authority_ladder_confirmation_count_watch"
)
PRIMARY_AUTHORITY_WATCH_REASON = (
    "research_strategy_team_evidence_authority_ladder_primary_authority_watch"
)
CORROBORATION_WATCH_REASON = (
    "research_strategy_team_evidence_authority_ladder_corroboration_watch"
)
CONFLICT_WATCH_REASON = "research_strategy_team_evidence_authority_ladder_conflict_watch"
FRESHNESS_WATCH_REASON = (
    "research_strategy_team_evidence_authority_ladder_freshness_watch"
)
SCORE_WATCH_REASON = "research_strategy_team_evidence_authority_ladder_score_watch"

ROW_REASON_CODES = (
    CLEAR_REASON,
    AUTHORITY_COUNT_BLOCK_REASON,
    CONFIRMATION_COUNT_BLOCK_REASON,
    PRIMARY_AUTHORITY_BLOCK_REASON,
    CORROBORATION_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    FRESHNESS_BLOCK_REASON,
    SCORE_BLOCK_REASON,
    AUTHORITY_COUNT_WATCH_REASON,
    CONFIRMATION_COUNT_WATCH_REASON,
    PRIMARY_AUTHORITY_WATCH_REASON,
    CORROBORATION_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    FRESHNESS_WATCH_REASON,
    SCORE_WATCH_REASON,
)
REPORT_REASON_PRIORITY = (
    AUTHORITY_COUNT_BLOCK_REASON,
    CONFIRMATION_COUNT_BLOCK_REASON,
    PRIMARY_AUTHORITY_BLOCK_REASON,
    CORROBORATION_BLOCK_REASON,
    CONFLICT_BLOCK_REASON,
    FRESHNESS_BLOCK_REASON,
    SCORE_BLOCK_REASON,
    AUTHORITY_COUNT_WATCH_REASON,
    CONFIRMATION_COUNT_WATCH_REASON,
    PRIMARY_AUTHORITY_WATCH_REASON,
    CORROBORATION_WATCH_REASON,
    CONFLICT_WATCH_REASON,
    FRESHNESS_WATCH_REASON,
    SCORE_WATCH_REASON,
)
REPORT_REASON_CODES = (NO_INPUTS_REASON,) + ROW_REASON_CODES


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_TEXT_PARTS = (
    _join_parts("raw", "_candidate"),
    _join_parts("candidate", "_id"),
    _join_parts("candidate", "-"),
    _join_parts("market", "_id"),
    _join_parts("market", "_slug"),
    _join_parts("market", "_question"),
    _join_parts("ques", "tion"),
    _join_parts("source", "_url"),
    _join_parts("source", "_text"),
    _join_parts("d", "sn"),
    _join_parts("table", "_name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("live", "_surface"),
    _join_parts("position", "_size"),
    _join_parts("rec", "ommendation"),
    _join_parts("rec", "ommend"),
    _join_parts("siz", "ing"),
    _join_parts("auth", "_token"),
    _join_parts("authentication"),
    _join_parts("api", "_key"),
    _join_parts("private", "_key"),
    _join_parts("postgres", "://"),
    _join_parts("mysql", "://"),
    _join_parts("jdbc", ":"),
    _join_parts("http", "://"),
    _join_parts("https", "://"),
    "://",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchStrategyTeamEvidenceAuthorityLadderConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_EVIDENCE_AUTHORITY_LADDER_REPORT_CONFIG_VERSION
    )
    min_authoritative_evidence_count_pass: Decimal = Decimal("3.000000")
    min_authoritative_evidence_count_watch: Decimal = Decimal("2.000000")
    min_independent_confirmation_count_pass: Decimal = Decimal("2.000000")
    min_independent_confirmation_count_watch: Decimal = Decimal("1.000000")
    primary_authority_score_pass_floor: Decimal = Decimal("0.800000")
    primary_authority_score_watch_floor: Decimal = Decimal("0.600000")
    corroboration_strength_pass_floor: Decimal = Decimal("0.800000")
    corroboration_strength_watch_floor: Decimal = Decimal("0.550000")
    conflict_pressure_watch_ceiling: Decimal = Decimal("0.250000")
    conflict_pressure_block_ceiling: Decimal = Decimal("0.500000")
    freshness_score_pass_floor: Decimal = Decimal("0.750000")
    freshness_score_watch_floor: Decimal = Decimal("0.500000")
    authority_ladder_score_pass_floor: Decimal = Decimal("0.750000")
    authority_ladder_score_watch_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamEvidenceAuthorityLadderConfig,
            "config",
        )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_EVIDENCE_AUTHORITY_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_authoritative_evidence_count_pass",
            "min_authoritative_evidence_count_watch",
            "min_independent_confirmation_count_pass",
            "min_independent_confirmation_count_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "primary_authority_score_pass_floor",
            "primary_authority_score_watch_floor",
            "corroboration_strength_pass_floor",
            "corroboration_strength_watch_floor",
            "conflict_pressure_watch_ceiling",
            "conflict_pressure_block_ceiling",
            "freshness_score_pass_floor",
            "freshness_score_watch_floor",
            "authority_ladder_score_pass_floor",
            "authority_ladder_score_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_positive_threshold(
            "min_authoritative_evidence_count_pass",
            self.min_authoritative_evidence_count_pass,
        )
        _require_positive_threshold(
            "min_independent_confirmation_count_pass",
            self.min_independent_confirmation_count_pass,
        )
        _require_at_least(
            "min_authoritative_evidence_count_pass",
            self.min_authoritative_evidence_count_pass,
            self.min_authoritative_evidence_count_watch,
        )
        _require_at_least(
            "min_independent_confirmation_count_pass",
            self.min_independent_confirmation_count_pass,
            self.min_independent_confirmation_count_watch,
        )
        _require_at_least(
            "primary_authority_score_pass_floor",
            self.primary_authority_score_pass_floor,
            self.primary_authority_score_watch_floor,
        )
        _require_at_least(
            "corroboration_strength_pass_floor",
            self.corroboration_strength_pass_floor,
            self.corroboration_strength_watch_floor,
        )
        _require_at_most(
            "conflict_pressure_watch_ceiling",
            self.conflict_pressure_watch_ceiling,
            self.conflict_pressure_block_ceiling,
        )
        _require_at_least(
            "freshness_score_pass_floor",
            self.freshness_score_pass_floor,
            self.freshness_score_watch_floor,
        )
        _require_at_least(
            "authority_ladder_score_pass_floor",
            self.authority_ladder_score_pass_floor,
            self.authority_ladder_score_watch_floor,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyTeamEvidenceAuthorityLadderInput(_FinalPublicDataclass):
    evidence_key: str
    authoritative_evidence_count: Decimal
    independent_confirmation_count: Decimal
    primary_authority_score: Decimal
    corroboration_strength_score: Decimal
    conflict_pressure_score: Decimal
    freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamEvidenceAuthorityLadderInput,
            "input",
        )
        _require_canonical_string("evidence_key", self.evidence_key)
        for field_name in (
            "authoritative_evidence_count",
            "independent_confirmation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "primary_authority_score",
            "corroboration_strength_score",
            "conflict_pressure_score",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyTeamEvidenceAuthorityLadderRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    status: str
    authoritative_evidence_count: Decimal
    independent_confirmation_count: Decimal
    primary_authority_score: Decimal
    corroboration_strength_score: Decimal
    conflict_pressure_score: Decimal
    freshness_score: Decimal
    authority_ladder_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamEvidenceAuthorityLadderRow,
            "row",
        )
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_decimal("aggregate_row_number", self.aggregate_row_number),
        )
        _require_public_digest("aggregate_row_hash", self.aggregate_row_hash)
        _require_status("status", self.status)
        for field_name in (
            "authoritative_evidence_count",
            "independent_confirmation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "primary_authority_score",
            "corroboration_strength_score",
            "conflict_pressure_score",
            "freshness_score",
            "authority_ladder_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount,
            "reason_code_count",
        )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(self, "count", _normalize_positive_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyTeamEvidenceAuthorityLadderReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    evidence_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    authority_attention_count: Decimal
    confirmation_attention_count: Decimal
    primary_authority_attention_count: Decimal
    corroboration_attention_count: Decimal
    conflict_attention_count: Decimal
    freshness_attention_count: Decimal
    mean_authority_ladder_score: Decimal
    lowest_authority_ladder_score: Decimal
    highest_conflict_pressure_score: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyTeamEvidenceAuthorityLadderRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamEvidenceAuthorityLadderReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "evidence_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "authority_attention_count",
            "confirmation_attention_count",
            "primary_authority_attention_count",
            "corroboration_attention_count",
            "conflict_attention_count",
            "freshness_attention_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_authority_ladder_score",
            "lowest_authority_ladder_score",
            "highest_conflict_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_digest("public_digest", self.public_digest)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        if self.public_digest != _computed_report_digest(self):
            raise ValueError("public_digest must match report values")
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    ResearchStrategyTeamEvidenceAuthorityLadderConfig,
    ResearchStrategyTeamEvidenceAuthorityLadderInput,
    ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount,
    ResearchStrategyTeamEvidenceAuthorityLadderReport,
    ResearchStrategyTeamEvidenceAuthorityLadderRow,
)


def build_research_strategy_team_evidence_authority_ladder_report(
    inputs: Iterable[ResearchStrategyTeamEvidenceAuthorityLadderInput],
    *,
    config: ResearchStrategyTeamEvidenceAuthorityLadderConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamEvidenceAuthorityLadderReport:
    if type(config) is not ResearchStrategyTeamEvidenceAuthorityLadderConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamEvidenceAuthorityLadderConfig",
        )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    row_values = sorted(
        (_row_values_for_input(row, config=config) for row in _normalize_inputs(inputs)),
        key=_row_values_sort_key,
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return ResearchStrategyTeamEvidenceAuthorityLadderReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_team_evidence_authority_ladder_report_digest(
    report: ResearchStrategyTeamEvidenceAuthorityLadderReport,
) -> str:
    if type(report) is not ResearchStrategyTeamEvidenceAuthorityLadderReport:
        raise ValueError(
            "report must be a ResearchStrategyTeamEvidenceAuthorityLadderReport",
        )
    validate_research_strategy_team_evidence_authority_ladder_report_digest(report)
    return _computed_report_digest(report)


def research_strategy_team_evidence_authority_ladder_report_payload(
    report: ResearchStrategyTeamEvidenceAuthorityLadderReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyTeamEvidenceAuthorityLadderReport:
        raise ValueError(
            "report must be a ResearchStrategyTeamEvidenceAuthorityLadderReport",
        )
    validate_research_strategy_team_evidence_authority_ladder_report_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_strategy_team_evidence_authority_ladder_public_payload(payload)
    return payload


def validate_research_strategy_team_evidence_authority_ladder_report_digest(
    report: ResearchStrategyTeamEvidenceAuthorityLadderReport,
) -> None:
    if type(report) is not ResearchStrategyTeamEvidenceAuthorityLadderReport:
        raise ValueError(
            "report must be a ResearchStrategyTeamEvidenceAuthorityLadderReport",
        )
    _require_public_digest("public_digest", report.public_digest)
    _revalidate_report_for_payload(report)
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report values")


def validate_research_strategy_team_evidence_authority_ladder_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _require_public_payload_json_types("public payload", payload)
    _verify_public_digest(payload)


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


@dataclass(frozen=True)
class _RowValues:
    aggregate_row_hash: str
    status: str
    authoritative_evidence_count: Decimal
    independent_confirmation_count: Decimal
    primary_authority_score: Decimal
    corroboration_strength_score: Decimal
    conflict_pressure_score: Decimal
    freshness_score: Decimal
    authority_ladder_score: Decimal
    reason_codes: tuple[str, ...]


def _row_values_for_input(
    row: ResearchStrategyTeamEvidenceAuthorityLadderInput,
    *,
    config: ResearchStrategyTeamEvidenceAuthorityLadderConfig,
) -> _RowValues:
    authority_ladder_score = _authority_ladder_score(
        authoritative_evidence_count=row.authoritative_evidence_count,
        independent_confirmation_count=row.independent_confirmation_count,
        primary_authority_score=row.primary_authority_score,
        corroboration_strength_score=row.corroboration_strength_score,
        conflict_pressure_score=row.conflict_pressure_score,
        freshness_score=row.freshness_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        authority_ladder_score=authority_ladder_score,
        config=config,
    )
    return _RowValues(
        aggregate_row_hash=_public_hash(row.evidence_key),
        status=_row_status(reason_codes),
        authoritative_evidence_count=row.authoritative_evidence_count,
        independent_confirmation_count=row.independent_confirmation_count,
        primary_authority_score=row.primary_authority_score,
        corroboration_strength_score=row.corroboration_strength_score,
        conflict_pressure_score=row.conflict_pressure_score,
        freshness_score=row.freshness_score,
        authority_ladder_score=authority_ladder_score,
        reason_codes=reason_codes,
    )


def _row_from_values(
    aggregate_row_number: Decimal,
    values: _RowValues,
) -> ResearchStrategyTeamEvidenceAuthorityLadderRow:
    return ResearchStrategyTeamEvidenceAuthorityLadderRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=values.aggregate_row_hash,
        status=values.status,
        authoritative_evidence_count=values.authoritative_evidence_count,
        independent_confirmation_count=values.independent_confirmation_count,
        primary_authority_score=values.primary_authority_score,
        corroboration_strength_score=values.corroboration_strength_score,
        conflict_pressure_score=values.conflict_pressure_score,
        freshness_score=values.freshness_score,
        authority_ladder_score=values.authority_ladder_score,
        reason_codes=values.reason_codes,
    )


def _row_reason_codes(
    row: ResearchStrategyTeamEvidenceAuthorityLadderInput,
    *,
    authority_ladder_score: Decimal,
    config: ResearchStrategyTeamEvidenceAuthorityLadderConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_floor_reason(
        reasons,
        AUTHORITY_COUNT_BLOCK_REASON,
        AUTHORITY_COUNT_WATCH_REASON,
        row.authoritative_evidence_count,
        config.min_authoritative_evidence_count_pass,
        config.min_authoritative_evidence_count_watch,
    )
    _append_floor_reason(
        reasons,
        CONFIRMATION_COUNT_BLOCK_REASON,
        CONFIRMATION_COUNT_WATCH_REASON,
        row.independent_confirmation_count,
        config.min_independent_confirmation_count_pass,
        config.min_independent_confirmation_count_watch,
    )
    _append_floor_reason(
        reasons,
        PRIMARY_AUTHORITY_BLOCK_REASON,
        PRIMARY_AUTHORITY_WATCH_REASON,
        row.primary_authority_score,
        config.primary_authority_score_pass_floor,
        config.primary_authority_score_watch_floor,
    )
    _append_floor_reason(
        reasons,
        CORROBORATION_BLOCK_REASON,
        CORROBORATION_WATCH_REASON,
        row.corroboration_strength_score,
        config.corroboration_strength_pass_floor,
        config.corroboration_strength_watch_floor,
    )
    if row.conflict_pressure_score >= config.conflict_pressure_block_ceiling:
        reasons.append(CONFLICT_BLOCK_REASON)
    elif row.conflict_pressure_score > config.conflict_pressure_watch_ceiling:
        reasons.append(CONFLICT_WATCH_REASON)
    _append_floor_reason(
        reasons,
        FRESHNESS_BLOCK_REASON,
        FRESHNESS_WATCH_REASON,
        row.freshness_score,
        config.freshness_score_pass_floor,
        config.freshness_score_watch_floor,
    )
    if authority_ladder_score < config.authority_ladder_score_watch_floor:
        reasons.append(SCORE_BLOCK_REASON)
    elif authority_ladder_score < config.authority_ladder_score_pass_floor:
        reasons.append(SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reason for reason in ROW_REASON_CODES if reason in reasons)


def _append_floor_reason(
    reasons: list[str],
    block_reason: str,
    watch_reason: str,
    value: Decimal,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> None:
    if value < watch_floor:
        reasons.append(block_reason)
    elif value < pass_floor:
        reasons.append(watch_reason)


def _authority_ladder_score(
    *,
    authoritative_evidence_count: Decimal,
    independent_confirmation_count: Decimal,
    primary_authority_score: Decimal,
    corroboration_strength_score: Decimal,
    conflict_pressure_score: Decimal,
    freshness_score: Decimal,
    config: ResearchStrategyTeamEvidenceAuthorityLadderConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                _bounded_ratio(
                    authoritative_evidence_count,
                    config.min_authoritative_evidence_count_pass,
                )
                + _bounded_ratio(
                    independent_confirmation_count,
                    config.min_independent_confirmation_count_pass,
                )
                + primary_authority_score
                + corroboration_strength_score
                + _quantize(ONE - conflict_pressure_score)
                + freshness_score
            )
            / SIX,
        )


def _bounded_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        raise ValueError("ratio denominator must be positive")
    with localcontext(DECIMAL_CONTEXT):
        return min(numerator / denominator, ONE).quantize(QUANTUM)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(rows: tuple[ResearchStrategyTeamEvidenceAuthorityLadderRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyTeamEvidenceAuthorityLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    row_reason_codes = frozenset(
        reason
        for row in rows
        for reason in row.reason_codes
        if reason != CLEAR_REASON
    )
    reasons = tuple(reason for reason in REPORT_REASON_PRIORITY if reason in row_reason_codes)
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamEvidenceAuthorityLadderRow, ...],
) -> tuple[ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchStrategyTeamEvidenceAuthorityLadderRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "evidence_item_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "authority_attention_count": _kind_count(rows, "authority_count_"),
        "confirmation_attention_count": _kind_count(rows, "confirmation_count_"),
        "primary_authority_attention_count": _kind_count(rows, "primary_authority_"),
        "corroboration_attention_count": _kind_count(rows, "corroboration_"),
        "conflict_attention_count": _kind_count(rows, "conflict_"),
        "freshness_attention_count": _kind_count(rows, "freshness_"),
        "mean_authority_ladder_score": _mean(
            tuple(row.authority_ladder_score for row in rows),
        ),
        "lowest_authority_ladder_score": _min_decimal(
            tuple(row.authority_ladder_score for row in rows),
        ),
        "highest_conflict_pressure_score": _max_decimal(
            tuple(row.conflict_pressure_score for row in rows),
        ),
        "status": _rollup_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyTeamEvidenceAuthorityLadderInput],
) -> tuple[ResearchStrategyTeamEvidenceAuthorityLadderInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyTeamEvidenceAuthorityLadderInput:
            raise ValueError(
                "inputs must contain ResearchStrategyTeamEvidenceAuthorityLadderInput values",
            )
        _require_hard_flags("input", row)
        _reject_unsafe_public_payload("input", row)
        if row.evidence_key in seen_keys:
            raise ValueError("inputs must not contain duplicate evidence_key values")
        seen_keys.add(row.evidence_key)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyTeamEvidenceAuthorityLadderRow],
) -> tuple[ResearchStrategyTeamEvidenceAuthorityLadderRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyTeamEvidenceAuthorityLadderRow:
            raise ValueError(
                "rows must contain ResearchStrategyTeamEvidenceAuthorityLadderRow values",
            )
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
        if row.aggregate_row_hash in seen_hashes:
            raise ValueError("rows must not contain duplicate aggregate_row_hash values")
        seen_hashes.add(row.aggregate_row_hash)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    rows: Iterable[ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount],
) -> tuple[ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount values",
            )
        if row.reason_code in seen_codes:
            raise ValueError(
                "reason_code_counts must not contain duplicate reason_code values",
            )
        seen_codes.add(row.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _normalize_row_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    _require_reason_codes_tuple("reason_codes", values)
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        if value not in ROW_REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
        if value in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(value)
    expected = tuple(reason for reason in ROW_REASON_CODES if reason in values)
    if values != expected:
        raise ValueError("reason_codes must use canonical sequence")
    return values


def _normalize_report_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    _require_reason_codes_tuple("reason_codes", values)
    if not values:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    for value in values:
        if value not in REPORT_REASON_CODES:
            raise ValueError("reason_codes must contain known reason codes")
        if value in seen:
            raise ValueError("reason_codes must not contain duplicates")
        seen.add(value)
    if values == (NO_INPUTS_REASON,) or values == (CLEAR_REASON,):
        return values
    expected = tuple(reason for reason in REPORT_REASON_PRIORITY if reason in values)
    if values != expected:
        raise ValueError("reason_codes must use canonical sequence")
    return values


def _row_sort_key(
    row: ResearchStrategyTeamEvidenceAuthorityLadderRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -row.conflict_pressure_score,
        -_authority_ladder_gap(row.authority_ladder_score),
        row.aggregate_row_hash,
    )


def _row_values_sort_key(values: _RowValues) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[values.status],
        -values.conflict_pressure_score,
        -_authority_ladder_gap(values.authority_ladder_score),
        values.aggregate_row_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyTeamEvidenceAuthorityLadderRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _kind_count(
    rows: tuple[ResearchStrategyTeamEvidenceAuthorityLadderRow, ...],
    kind: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if any(kind in reason_code for reason_code in row.reason_codes)
        ),
    )


def _validate_row(row: ResearchStrategyTeamEvidenceAuthorityLadderRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    _require_hard_flags("row", row)


def _validate_report(report: ResearchStrategyTeamEvidenceAuthorityLadderReport) -> None:
    rows = report.rows
    if report.evidence_item_count != _count(len(rows)):
        raise ValueError("evidence_item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    for field_name, kind in (
        ("authority_attention_count", "authority_count_"),
        ("confirmation_attention_count", "confirmation_count_"),
        ("primary_authority_attention_count", "primary_authority_"),
        ("corroboration_attention_count", "corroboration_"),
        ("conflict_attention_count", "conflict_"),
        ("freshness_attention_count", "freshness_"),
    ):
        if getattr(report, field_name) != _kind_count(rows, kind):
            raise ValueError(f"{field_name} must match rows")
    if report.mean_authority_ladder_score != _mean(
        tuple(row.authority_ladder_score for row in rows),
    ):
        raise ValueError("mean_authority_ladder_score must match rows")
    if report.lowest_authority_ladder_score != _min_decimal(
        tuple(row.authority_ladder_score for row in rows),
    ):
        raise ValueError("lowest_authority_ladder_score must match rows")
    if report.highest_conflict_pressure_score != _max_decimal(
        tuple(row.conflict_pressure_score for row in rows),
    ):
        raise ValueError("highest_conflict_pressure_score must match rows")
    if report.status != _rollup_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    for index, row in enumerate(rows, start=1):
        if row.aggregate_row_number != _count(index):
            raise ValueError("aggregate_row_number must match rows")


def _revalidate_report_for_payload(
    report: ResearchStrategyTeamEvidenceAuthorityLadderReport,
) -> None:
    _require_exact_type(report, ResearchStrategyTeamEvidenceAuthorityLadderReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    for field_name in (
        "evidence_item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "authority_attention_count",
        "confirmation_attention_count",
        "primary_authority_attention_count",
        "corroboration_attention_count",
        "conflict_attention_count",
        "freshness_attention_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "mean_authority_ladder_score",
        "lowest_authority_ladder_score",
        "highest_conflict_pressure_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _require_public_digest("public_digest", report.public_digest)
    _normalize_report_reason_codes(report.reason_codes)
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in report.reason_code_counts:
        _revalidate_reason_code_count_for_payload(row)
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        _revalidate_row_for_payload(row)
    _validate_report(report)
    _require_hard_flags("report", report)


def _revalidate_row_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyTeamEvidenceAuthorityLadderRow:
        raise ValueError(
            "rows must contain ResearchStrategyTeamEvidenceAuthorityLadderRow values",
        )
    _require_positive_six_decimal_decimal("aggregate_row_number", row.aggregate_row_number)
    _require_public_digest("aggregate_row_hash", row.aggregate_row_hash)
    _require_status("status", row.status)
    for field_name in (
        "authoritative_evidence_count",
        "independent_confirmation_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(row, field_name))
    for field_name in (
        "primary_authority_score",
        "corroboration_strength_score",
        "conflict_pressure_score",
        "freshness_score",
        "authority_ladder_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(row, field_name))
    _normalize_row_reason_codes(row.reason_codes)
    _validate_row(row)


def _revalidate_reason_code_count_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchStrategyTeamEvidenceAuthorityLadderReasonCodeCount values",
        )
    if row.reason_code not in REPORT_REASON_CODES:
        raise ValueError("reason_code must be a known reason code")
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _authority_ladder_gap(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _computed_report_digest(
    report: ResearchStrategyTeamEvidenceAuthorityLadderReport,
) -> str:
    values = {
        field.name: getattr(report, field.name)
        for field in fields(report)
        if field.name != "public_digest"
    }
    return _digest_from_mapping(values)


def _digest_from_mapping(values: dict[str, Any]) -> str:
    ready = _json_ready(values)
    return sha256(
        json.dumps(
            ready,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8"),
    ).hexdigest()


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("public_digest")
    _require_public_digest("public_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("public_digest")
    expected = sha256(
        json.dumps(
            unsigned,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8"),
    ).hexdigest()
    if digest != expected:
        raise ValueError("public_digest must match public payload")
    _require_hard_flags("public payload", _DictFlags(payload))


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("payload contains unknown dataclass")
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is Decimal:
        _require_six_decimal_decimal("JSON Decimal value", value)
        return str(value)
    if type(value) is datetime:
        _require_utc_datetime("JSON datetime value", value)
        return value.isoformat()
    if value is None or type(value) in (bool, str):
        if type(value) is str:
            _require_canonical_string("JSON string value", value)
        return value
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_canonical_string("JSON object key", key)
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (int, float) or isinstance(value, (list, set)):
        raise ValueError("value must use public dataclass fields")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{label} contains unknown dataclass")
        for field in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
            )
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if type(value) in (Decimal, datetime) or value is None or type(value) is bool:
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(f"{label}[{index}]", item)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            try:
                _reject_unsafe_text(label, key)
            except ValueError as exc:
                raise ValueError("public payload contains unsafe text") from exc
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if type(value) in (int, float) or isinstance(value, set):
        raise ValueError(f"{label} must use public dataclass fields")
    raise ValueError(f"{label} has unknown value")


def _require_public_payload_json_types(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _require_public_payload_json_types(f"{label}.{key}", item)
        return
    if type(value) is list:
        for index, item in enumerate(value):
            _require_public_payload_json_types(f"{label}[{index}]", item)
        return
    if type(value) in (bool, str) or value is None:
        return
    raise ValueError(f"{label} must not contain numeric or non-JSON public values")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(piece in lowered for piece in _UNSAFE_TEXT_PARTS):
        raise ValueError(f"{label} contains unsafe text")


def _require_reason_codes_tuple(label: str, values: object) -> None:
    if type(values) is not tuple:
        raise ValueError(f"{label} must be a tuple")
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{label} must contain strings")


def _require_canonical_string(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{label} must be canonical")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{label} must be canonical")
    _reject_unsafe_text(label, value)


def _require_status(label: str, value: object) -> None:
    if type(value) is not str or (
        value not in RESEARCH_STRATEGY_TEAM_EVIDENCE_AUTHORITY_LADDER_REPORT_STATUSES
    ):
        raise ValueError(f"{label} must be pass, watch, or block")


def _require_public_digest(label: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    if len(value) != 64 or value.lower() != value:
        raise ValueError(f"{label} must be a lowercase hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{label} must be a lowercase hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_positive_threshold(label: str, value: Decimal) -> None:
    if value <= ZERO:
        raise ValueError(f"{label} must be positive")


def _require_at_least(label: str, value: Decimal, limit: Decimal) -> None:
    if value < limit:
        raise ValueError(f"{label} must be at least its watch level")


def _require_at_most(label: str, value: Decimal, limit: Decimal) -> None:
    if value > limit:
        raise ValueError(f"{label} must be at most its block level")


def _as_utc(label: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
    return value.astimezone(UTC)


def _require_utc_datetime(label: str, value: object) -> None:
    if type(value) is not datetime:
        raise ValueError(f"{label} must be a datetime")
    if value.tzinfo is not UTC or value.utcoffset() != UTC.utcoffset(value):
        raise ValueError(f"{label} must be UTC")


def _normalize_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    return _quantize(value)


def _normalize_nonnegative_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_decimal(label, value)
    if normalized < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return normalized


def _normalize_positive_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")
    return normalized


def _normalize_probability_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(label, value)
    if normalized > ONE:
        raise ValueError(f"{label} must be between 0 and 1")
    return normalized


def _require_six_decimal_decimal(label: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value != _quantize(value):
        raise ValueError(f"{label} must use six decimal places")


def _require_nonnegative_six_decimal_decimal(label: str, value: object) -> None:
    _require_six_decimal_decimal(label, value)
    if value < ZERO:
        raise ValueError(f"{label} must be nonnegative")


def _require_positive_six_decimal_decimal(label: str, value: object) -> None:
    _require_nonnegative_six_decimal_decimal(label, value)
    if value <= ZERO:
        raise ValueError(f"{label} must be positive")


def _require_probability_six_decimal_decimal(label: str, value: object) -> None:
    _require_nonnegative_six_decimal_decimal(label, value)
    if value > ONE:
        raise ValueError(f"{label} must be between 0 and 1")


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _count(value: int) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)
