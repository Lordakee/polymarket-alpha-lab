"""Pure report-only research strategy domain evidence quorum decay report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any, final


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_STATUSES",
    "ResearchStrategyDomainEvidenceQuorumDecayConfig",
    "ResearchStrategyDomainEvidenceQuorumDecayInput",
    "ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount",
    "ResearchStrategyDomainEvidenceQuorumDecayReport",
    "ResearchStrategyDomainEvidenceQuorumDecayRow",
    "build_research_strategy_domain_evidence_quorum_decay_report",
    "research_strategy_domain_evidence_quorum_decay_report_digest",
    "research_strategy_domain_evidence_quorum_decay_report_payload",
    "validate_research_strategy_domain_evidence_quorum_decay_public_payload",
    "validate_research_strategy_domain_evidence_quorum_decay_report_digest",
)


DEFAULT_RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_CONFIG_VERSION = (
    "research-strategy-domain-evidence-quorum-decay-report-v0"
)
RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SEVEN = Decimal("7.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
MANUAL_REVIEW_PRIORITIES = ("routine", "priority", "urgent")
MANUAL_REVIEW_PRIORITY_BY_STATUS = {
    "pass": "routine",
    "watch": "priority",
    "block": "urgent",
}

NO_INPUTS_REASON = "research_strategy_domain_evidence_quorum_decay_no_inputs"
CLEAR_REASON = "research_strategy_domain_evidence_quorum_decay_clear"
DOMAIN_QUORUM_BLOCK_REASON = (
    "research_strategy_domain_evidence_quorum_decay_domain_quorum_block"
)
EVIDENCE_QUORUM_BLOCK_REASON = (
    "research_strategy_domain_evidence_quorum_decay_evidence_quorum_block"
)
SOURCE_FAMILY_BLOCK_REASON = (
    "research_strategy_domain_evidence_quorum_decay_source_family_block"
)
FRESHNESS_DECAY_BLOCK_REASON = (
    "research_strategy_domain_evidence_quorum_decay_freshness_decay_block"
)
CONSENSUS_SUPPORT_BLOCK_REASON = (
    "research_strategy_domain_evidence_quorum_decay_consensus_support_block"
)
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "research_strategy_domain_evidence_quorum_decay_contradiction_pressure_block"
)
SOURCE_AUTHORITY_BLOCK_REASON = (
    "research_strategy_domain_evidence_quorum_decay_source_authority_block"
)
SCORE_BLOCK_REASON = "research_strategy_domain_evidence_quorum_decay_score_block"
DOMAIN_QUORUM_WATCH_REASON = (
    "research_strategy_domain_evidence_quorum_decay_domain_quorum_watch"
)
EVIDENCE_QUORUM_WATCH_REASON = (
    "research_strategy_domain_evidence_quorum_decay_evidence_quorum_watch"
)
SOURCE_FAMILY_WATCH_REASON = (
    "research_strategy_domain_evidence_quorum_decay_source_family_watch"
)
FRESHNESS_DECAY_WATCH_REASON = (
    "research_strategy_domain_evidence_quorum_decay_freshness_decay_watch"
)
CONSENSUS_SUPPORT_WATCH_REASON = (
    "research_strategy_domain_evidence_quorum_decay_consensus_support_watch"
)
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "research_strategy_domain_evidence_quorum_decay_contradiction_pressure_watch"
)
SOURCE_AUTHORITY_WATCH_REASON = (
    "research_strategy_domain_evidence_quorum_decay_source_authority_watch"
)
SCORE_WATCH_REASON = "research_strategy_domain_evidence_quorum_decay_score_watch"

ROW_REASON_CODES = (
    CLEAR_REASON,
    DOMAIN_QUORUM_BLOCK_REASON,
    EVIDENCE_QUORUM_BLOCK_REASON,
    SOURCE_FAMILY_BLOCK_REASON,
    FRESHNESS_DECAY_BLOCK_REASON,
    CONSENSUS_SUPPORT_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    SOURCE_AUTHORITY_BLOCK_REASON,
    SCORE_BLOCK_REASON,
    DOMAIN_QUORUM_WATCH_REASON,
    EVIDENCE_QUORUM_WATCH_REASON,
    SOURCE_FAMILY_WATCH_REASON,
    FRESHNESS_DECAY_WATCH_REASON,
    CONSENSUS_SUPPORT_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    SOURCE_AUTHORITY_WATCH_REASON,
    SCORE_WATCH_REASON,
)
REPORT_REASON_PRIORITY = (
    DOMAIN_QUORUM_BLOCK_REASON,
    EVIDENCE_QUORUM_BLOCK_REASON,
    SOURCE_FAMILY_BLOCK_REASON,
    FRESHNESS_DECAY_BLOCK_REASON,
    CONSENSUS_SUPPORT_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    SOURCE_AUTHORITY_BLOCK_REASON,
    SCORE_BLOCK_REASON,
    DOMAIN_QUORUM_WATCH_REASON,
    EVIDENCE_QUORUM_WATCH_REASON,
    SOURCE_FAMILY_WATCH_REASON,
    FRESHNESS_DECAY_WATCH_REASON,
    CONSENSUS_SUPPORT_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    SOURCE_AUTHORITY_WATCH_REASON,
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
    _join_parts("source", "_id"),
    _join_parts("source", "_name"),
    _join_parts("source", "_ref"),
    _join_parts("private", "-source"),
    _join_parts("private", "_source"),
    _join_parts("team", "_id"),
    _join_parts("team", "_key"),
    _join_parts("team", "_name"),
    _join_parts("team", "_ref"),
    _join_parts("private", "-team"),
    _join_parts("private", "_team"),
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
    __slots__ = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEvidenceQuorumDecayConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_CONFIG_VERSION
    )
    min_domain_count_pass: Decimal = Decimal("3.000000")
    min_domain_count_watch: Decimal = Decimal("2.000000")
    min_independent_evidence_count_pass: Decimal = Decimal("5.000000")
    min_independent_evidence_count_watch: Decimal = Decimal("3.000000")
    min_source_family_count_pass: Decimal = Decimal("3.000000")
    min_source_family_count_watch: Decimal = Decimal("2.000000")
    max_latest_evidence_age_seconds_pass: Decimal = Decimal("1800.000000")
    max_latest_evidence_age_seconds_watch: Decimal = Decimal("7200.000000")
    domain_consensus_score_pass_floor: Decimal = Decimal("0.800000")
    domain_consensus_score_watch_floor: Decimal = Decimal("0.600000")
    contradiction_pressure_watch_ceiling: Decimal = Decimal("0.250000")
    contradiction_pressure_block_ceiling: Decimal = Decimal("0.500000")
    source_authority_score_pass_floor: Decimal = Decimal("0.750000")
    source_authority_score_watch_floor: Decimal = Decimal("0.500000")
    quorum_decay_score_pass_floor: Decimal = Decimal("0.750000")
    quorum_decay_score_watch_floor: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEvidenceQuorumDecayConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_domain_count_pass",
            "min_domain_count_watch",
            "min_independent_evidence_count_pass",
            "min_independent_evidence_count_watch",
            "min_source_family_count_pass",
            "min_source_family_count_watch",
            "max_latest_evidence_age_seconds_pass",
            "max_latest_evidence_age_seconds_watch",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "domain_consensus_score_pass_floor",
            "domain_consensus_score_watch_floor",
            "contradiction_pressure_watch_ceiling",
            "contradiction_pressure_block_ceiling",
            "source_authority_score_pass_floor",
            "source_authority_score_watch_floor",
            "quorum_decay_score_pass_floor",
            "quorum_decay_score_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_least(
            "min_domain_count_pass",
            self.min_domain_count_pass,
            self.min_domain_count_watch,
        )
        _require_at_least(
            "min_independent_evidence_count_pass",
            self.min_independent_evidence_count_pass,
            self.min_independent_evidence_count_watch,
        )
        _require_at_least(
            "min_source_family_count_pass",
            self.min_source_family_count_pass,
            self.min_source_family_count_watch,
        )
        if (
            self.max_latest_evidence_age_seconds_pass
            >= self.max_latest_evidence_age_seconds_watch
        ):
            raise ValueError(
                "max_latest_evidence_age_seconds_pass must be below its watch level",
            )
        _require_at_least(
            "domain_consensus_score_pass_floor",
            self.domain_consensus_score_pass_floor,
            self.domain_consensus_score_watch_floor,
        )
        _require_at_most(
            "contradiction_pressure_watch_ceiling",
            self.contradiction_pressure_watch_ceiling,
            self.contradiction_pressure_block_ceiling,
        )
        _require_at_least(
            "source_authority_score_pass_floor",
            self.source_authority_score_pass_floor,
            self.source_authority_score_watch_floor,
        )
        _require_at_least(
            "quorum_decay_score_pass_floor",
            self.quorum_decay_score_pass_floor,
            self.quorum_decay_score_watch_floor,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEvidenceQuorumDecayInput(_FinalPublicDataclass):
    domain_evidence_key: str
    domain_count: Decimal
    independent_evidence_count: Decimal
    source_family_count: Decimal
    latest_evidence_age_seconds: Decimal
    domain_consensus_score: Decimal
    contradiction_pressure_score: Decimal
    source_authority_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEvidenceQuorumDecayInput, "input")
        _require_canonical_string("domain_evidence_key", self.domain_evidence_key)
        for field_name in (
            "domain_count",
            "independent_evidence_count",
            "source_family_count",
            "latest_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "domain_consensus_score",
            "contradiction_pressure_score",
            "source_authority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEvidenceQuorumDecayRow(_FinalPublicDataclass):
    aggregate_row_number: Decimal
    aggregate_row_hash: str
    status: str
    manual_review_priority: str
    domain_count: Decimal
    independent_evidence_count: Decimal
    source_family_count: Decimal
    latest_evidence_age_seconds: Decimal
    freshness_decay_score: Decimal
    domain_consensus_score: Decimal
    contradiction_pressure_score: Decimal
    source_authority_score: Decimal
    quorum_decay_score: Decimal
    manual_review_priority_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEvidenceQuorumDecayRow, "row")
        object.__setattr__(
            self,
            "aggregate_row_number",
            _normalize_positive_decimal("aggregate_row_number", self.aggregate_row_number),
        )
        _require_public_digest("aggregate_row_hash", self.aggregate_row_hash)
        _require_status("status", self.status)
        _require_manual_review_priority(
            "manual_review_priority",
            self.manual_review_priority,
        )
        for field_name in (
            "domain_count",
            "independent_evidence_count",
            "source_family_count",
            "latest_evidence_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_decay_score",
            "domain_consensus_score",
            "contradiction_pressure_score",
            "source_authority_score",
            "quorum_decay_score",
            "manual_review_priority_score",
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


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount,
            "reason_code_count",
        )
        if type(self.reason_code) is not str or self.reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be a known reason code")
        object.__setattr__(self, "count", _normalize_positive_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyDomainEvidenceQuorumDecayReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchStrategyDomainEvidenceQuorumDecayConfig
    domain_evidence_item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    domain_quorum_attention_count: Decimal
    evidence_quorum_attention_count: Decimal
    source_family_attention_count: Decimal
    freshness_decay_attention_count: Decimal
    consensus_support_attention_count: Decimal
    contradiction_pressure_attention_count: Decimal
    source_authority_attention_count: Decimal
    score_attention_count: Decimal
    manual_review_required_count: Decimal
    mean_quorum_decay_score: Decimal
    lowest_quorum_decay_score: Decimal
    highest_contradiction_pressure_score: Decimal
    highest_manual_review_priority_score: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchStrategyDomainEvidenceQuorumDecayRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyDomainEvidenceQuorumDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_exact_type(
            self.config,
            ResearchStrategyDomainEvidenceQuorumDecayConfig,
            "config",
        )
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        _require_hard_flags("config", self.config)
        for field_name in (
            "domain_evidence_item_count",
            "pass_count",
            "watch_count",
            "block_count",
            "domain_quorum_attention_count",
            "evidence_quorum_attention_count",
            "source_family_attention_count",
            "freshness_decay_attention_count",
            "consensus_support_attention_count",
            "contradiction_pressure_attention_count",
            "source_authority_attention_count",
            "score_attention_count",
            "manual_review_required_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_quorum_decay_score",
            "lowest_quorum_decay_score",
            "highest_contradiction_pressure_score",
            "highest_manual_review_priority_score",
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
    ResearchStrategyDomainEvidenceQuorumDecayConfig,
    ResearchStrategyDomainEvidenceQuorumDecayInput,
    ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount,
    ResearchStrategyDomainEvidenceQuorumDecayReport,
    ResearchStrategyDomainEvidenceQuorumDecayRow,
)


def build_research_strategy_domain_evidence_quorum_decay_report(
    inputs: Iterable[ResearchStrategyDomainEvidenceQuorumDecayInput],
    *,
    config: ResearchStrategyDomainEvidenceQuorumDecayConfig,
    generated_at: datetime,
) -> ResearchStrategyDomainEvidenceQuorumDecayReport:
    if type(config) is not ResearchStrategyDomainEvidenceQuorumDecayConfig:
        raise ValueError(
            "config must be a ResearchStrategyDomainEvidenceQuorumDecayConfig",
        )
    _revalidate_config_for_payload(config)
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
        config=config,
        rows=rows,
    )
    return ResearchStrategyDomainEvidenceQuorumDecayReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def research_strategy_domain_evidence_quorum_decay_report_digest(
    report: ResearchStrategyDomainEvidenceQuorumDecayReport,
) -> str:
    if type(report) is not ResearchStrategyDomainEvidenceQuorumDecayReport:
        raise ValueError(
            "report must be a ResearchStrategyDomainEvidenceQuorumDecayReport",
        )
    validate_research_strategy_domain_evidence_quorum_decay_report_digest(report)
    return _computed_report_digest(report)


def research_strategy_domain_evidence_quorum_decay_report_payload(
    report: ResearchStrategyDomainEvidenceQuorumDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyDomainEvidenceQuorumDecayReport:
        raise ValueError(
            "report must be a ResearchStrategyDomainEvidenceQuorumDecayReport",
        )
    validate_research_strategy_domain_evidence_quorum_decay_report_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_strategy_domain_evidence_quorum_decay_public_payload(payload)
    return payload


def validate_research_strategy_domain_evidence_quorum_decay_report_digest(
    report: ResearchStrategyDomainEvidenceQuorumDecayReport,
) -> None:
    if type(report) is not ResearchStrategyDomainEvidenceQuorumDecayReport:
        raise ValueError(
            "report must be a ResearchStrategyDomainEvidenceQuorumDecayReport",
        )
    _require_public_digest("public_digest", report.public_digest)
    _revalidate_report_for_payload(report)
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report values")


def validate_research_strategy_domain_evidence_quorum_decay_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _validate_public_payload_schema(payload)
    _verify_public_digest(payload)
    validated_report = _report_from_public_payload(payload)
    if payload != _json_ready(validated_report):
        raise ValueError("public payload must use canonical schema values")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_payload_schema(
        "public payload",
        payload,
        ResearchStrategyDomainEvidenceQuorumDecayReport,
    )
    config = payload["config"]
    if type(config) is not dict:
        raise ValueError("config payload must be a JSON object")
    _require_exact_payload_schema(
        "config payload",
        config,
        ResearchStrategyDomainEvidenceQuorumDecayConfig,
    )
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        _require_exact_payload_schema(
            "row payload",
            row,
            ResearchStrategyDomainEvidenceQuorumDecayRow,
        )
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for reason_code_count in reason_code_counts:
        if type(reason_code_count) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_exact_payload_schema(
            "reason code count payload",
            reason_code_count,
            ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount,
        )


def _require_exact_payload_schema(
    label: str,
    payload: dict[str, Any],
    expected_type: type[object],
) -> None:
    expected_fields = tuple(field.name for field in fields(expected_type))
    if type(payload) is not dict or tuple(payload) != expected_fields:
        raise ValueError(f"{label} must use exact canonical schema")


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainEvidenceQuorumDecayReport:
    config = _config_from_public_payload(payload["config"])
    return ResearchStrategyDomainEvidenceQuorumDecayReport(
        generated_at=_datetime_from_public_payload(
            "generated_at",
            payload["generated_at"],
        ),
        config_version=_string_from_public_payload(
            "config_version",
            payload["config_version"],
        ),
        config=config,
        domain_evidence_item_count=_nonnegative_decimal_from_public_payload(
            "domain_evidence_item_count",
            payload["domain_evidence_item_count"],
        ),
        pass_count=_nonnegative_decimal_from_public_payload(
            "pass_count",
            payload["pass_count"],
        ),
        watch_count=_nonnegative_decimal_from_public_payload(
            "watch_count",
            payload["watch_count"],
        ),
        block_count=_nonnegative_decimal_from_public_payload(
            "block_count",
            payload["block_count"],
        ),
        domain_quorum_attention_count=_nonnegative_decimal_from_public_payload(
            "domain_quorum_attention_count",
            payload["domain_quorum_attention_count"],
        ),
        evidence_quorum_attention_count=_nonnegative_decimal_from_public_payload(
            "evidence_quorum_attention_count",
            payload["evidence_quorum_attention_count"],
        ),
        source_family_attention_count=_nonnegative_decimal_from_public_payload(
            "source_family_attention_count",
            payload["source_family_attention_count"],
        ),
        freshness_decay_attention_count=_nonnegative_decimal_from_public_payload(
            "freshness_decay_attention_count",
            payload["freshness_decay_attention_count"],
        ),
        consensus_support_attention_count=_nonnegative_decimal_from_public_payload(
            "consensus_support_attention_count",
            payload["consensus_support_attention_count"],
        ),
        contradiction_pressure_attention_count=(
            _nonnegative_decimal_from_public_payload(
                "contradiction_pressure_attention_count",
                payload["contradiction_pressure_attention_count"],
            )
        ),
        source_authority_attention_count=_nonnegative_decimal_from_public_payload(
            "source_authority_attention_count",
            payload["source_authority_attention_count"],
        ),
        score_attention_count=_nonnegative_decimal_from_public_payload(
            "score_attention_count",
            payload["score_attention_count"],
        ),
        manual_review_required_count=_nonnegative_decimal_from_public_payload(
            "manual_review_required_count",
            payload["manual_review_required_count"],
        ),
        mean_quorum_decay_score=_probability_from_public_payload(
            "mean_quorum_decay_score",
            payload["mean_quorum_decay_score"],
        ),
        lowest_quorum_decay_score=_probability_from_public_payload(
            "lowest_quorum_decay_score",
            payload["lowest_quorum_decay_score"],
        ),
        highest_contradiction_pressure_score=_probability_from_public_payload(
            "highest_contradiction_pressure_score",
            payload["highest_contradiction_pressure_score"],
        ),
        highest_manual_review_priority_score=_probability_from_public_payload(
            "highest_manual_review_priority_score",
            payload["highest_manual_review_priority_score"],
        ),
        status=_status_from_public_payload("status", payload["status"]),
        public_digest=_digest_from_public_payload(
            "public_digest",
            payload["public_digest"],
        ),
        reason_codes=_reason_codes_from_public_payload(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_public_payload(value)
            for value in payload["reason_code_counts"]
        ),
        rows=tuple(_row_from_public_payload(value) for value in payload["rows"]),
        paper_only=_true_from_public_payload("paper_only", payload["paper_only"]),
        report_only=_true_from_public_payload("report_only", payload["report_only"]),
        readonly=_true_from_public_payload("readonly", payload["readonly"]),
    )


def _config_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainEvidenceQuorumDecayConfig:
    return ResearchStrategyDomainEvidenceQuorumDecayConfig(
        config_version=_string_from_public_payload(
            "config.config_version",
            payload["config_version"],
        ),
        min_domain_count_pass=_positive_decimal_from_public_payload(
            "config.min_domain_count_pass",
            payload["min_domain_count_pass"],
        ),
        min_domain_count_watch=_positive_decimal_from_public_payload(
            "config.min_domain_count_watch",
            payload["min_domain_count_watch"],
        ),
        min_independent_evidence_count_pass=_positive_decimal_from_public_payload(
            "config.min_independent_evidence_count_pass",
            payload["min_independent_evidence_count_pass"],
        ),
        min_independent_evidence_count_watch=_positive_decimal_from_public_payload(
            "config.min_independent_evidence_count_watch",
            payload["min_independent_evidence_count_watch"],
        ),
        min_source_family_count_pass=_positive_decimal_from_public_payload(
            "config.min_source_family_count_pass",
            payload["min_source_family_count_pass"],
        ),
        min_source_family_count_watch=_positive_decimal_from_public_payload(
            "config.min_source_family_count_watch",
            payload["min_source_family_count_watch"],
        ),
        max_latest_evidence_age_seconds_pass=_positive_decimal_from_public_payload(
            "config.max_latest_evidence_age_seconds_pass",
            payload["max_latest_evidence_age_seconds_pass"],
        ),
        max_latest_evidence_age_seconds_watch=_positive_decimal_from_public_payload(
            "config.max_latest_evidence_age_seconds_watch",
            payload["max_latest_evidence_age_seconds_watch"],
        ),
        domain_consensus_score_pass_floor=_probability_from_public_payload(
            "config.domain_consensus_score_pass_floor",
            payload["domain_consensus_score_pass_floor"],
        ),
        domain_consensus_score_watch_floor=_probability_from_public_payload(
            "config.domain_consensus_score_watch_floor",
            payload["domain_consensus_score_watch_floor"],
        ),
        contradiction_pressure_watch_ceiling=_probability_from_public_payload(
            "config.contradiction_pressure_watch_ceiling",
            payload["contradiction_pressure_watch_ceiling"],
        ),
        contradiction_pressure_block_ceiling=_probability_from_public_payload(
            "config.contradiction_pressure_block_ceiling",
            payload["contradiction_pressure_block_ceiling"],
        ),
        source_authority_score_pass_floor=_probability_from_public_payload(
            "config.source_authority_score_pass_floor",
            payload["source_authority_score_pass_floor"],
        ),
        source_authority_score_watch_floor=_probability_from_public_payload(
            "config.source_authority_score_watch_floor",
            payload["source_authority_score_watch_floor"],
        ),
        quorum_decay_score_pass_floor=_probability_from_public_payload(
            "config.quorum_decay_score_pass_floor",
            payload["quorum_decay_score_pass_floor"],
        ),
        quorum_decay_score_watch_floor=_probability_from_public_payload(
            "config.quorum_decay_score_watch_floor",
            payload["quorum_decay_score_watch_floor"],
        ),
        paper_only=_true_from_public_payload(
            "config.paper_only",
            payload["paper_only"],
        ),
        report_only=_true_from_public_payload(
            "config.report_only",
            payload["report_only"],
        ),
        readonly=_true_from_public_payload(
            "config.readonly",
            payload["readonly"],
        ),
    )


def _row_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainEvidenceQuorumDecayRow:
    return ResearchStrategyDomainEvidenceQuorumDecayRow(
        aggregate_row_number=_positive_decimal_from_public_payload(
            "row.aggregate_row_number",
            payload["aggregate_row_number"],
        ),
        aggregate_row_hash=_digest_from_public_payload(
            "row.aggregate_row_hash",
            payload["aggregate_row_hash"],
        ),
        status=_status_from_public_payload("row.status", payload["status"]),
        manual_review_priority=_manual_review_priority_from_public_payload(
            "row.manual_review_priority",
            payload["manual_review_priority"],
        ),
        domain_count=_nonnegative_decimal_from_public_payload(
            "row.domain_count",
            payload["domain_count"],
        ),
        independent_evidence_count=_nonnegative_decimal_from_public_payload(
            "row.independent_evidence_count",
            payload["independent_evidence_count"],
        ),
        source_family_count=_nonnegative_decimal_from_public_payload(
            "row.source_family_count",
            payload["source_family_count"],
        ),
        latest_evidence_age_seconds=_nonnegative_decimal_from_public_payload(
            "row.latest_evidence_age_seconds",
            payload["latest_evidence_age_seconds"],
        ),
        freshness_decay_score=_probability_from_public_payload(
            "row.freshness_decay_score",
            payload["freshness_decay_score"],
        ),
        domain_consensus_score=_probability_from_public_payload(
            "row.domain_consensus_score",
            payload["domain_consensus_score"],
        ),
        contradiction_pressure_score=_probability_from_public_payload(
            "row.contradiction_pressure_score",
            payload["contradiction_pressure_score"],
        ),
        source_authority_score=_probability_from_public_payload(
            "row.source_authority_score",
            payload["source_authority_score"],
        ),
        quorum_decay_score=_probability_from_public_payload(
            "row.quorum_decay_score",
            payload["quorum_decay_score"],
        ),
        manual_review_priority_score=_probability_from_public_payload(
            "row.manual_review_priority_score",
            payload["manual_review_priority_score"],
        ),
        reason_codes=_reason_codes_from_public_payload(
            "row.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_true_from_public_payload(
            "row.paper_only",
            payload["paper_only"],
        ),
        report_only=_true_from_public_payload(
            "row.report_only",
            payload["report_only"],
        ),
        readonly=_true_from_public_payload("row.readonly", payload["readonly"]),
    )


def _reason_code_count_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount:
    return ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount(
        reason_code=_string_from_public_payload(
            "reason_code_count.reason_code",
            payload["reason_code"],
        ),
        count=_positive_decimal_from_public_payload(
            "reason_code_count.count",
            payload["count"],
        ),
        paper_only=_true_from_public_payload(
            "reason_code_count.paper_only",
            payload["paper_only"],
        ),
        report_only=_true_from_public_payload(
            "reason_code_count.report_only",
            payload["report_only"],
        ),
        readonly=_true_from_public_payload(
            "reason_code_count.readonly",
            payload["readonly"],
        ),
    )


def _decimal_from_public_payload(label: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{label} must be a canonical Decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{label} must be a canonical Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{label} must be finite")
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{label} must not use signed zero")
    if parsed.as_tuple().exponent != -6 or str(parsed) != value:
        raise ValueError(f"{label} must be a canonical Decimal string")
    _require_six_decimal_decimal(label, parsed)
    return parsed


def _nonnegative_decimal_from_public_payload(
    label: str,
    value: object,
) -> Decimal:
    parsed = _decimal_from_public_payload(label, value)
    _require_nonnegative_six_decimal_decimal(label, parsed)
    return parsed


def _positive_decimal_from_public_payload(label: str, value: object) -> Decimal:
    parsed = _decimal_from_public_payload(label, value)
    _require_positive_six_decimal_decimal(label, parsed)
    return parsed


def _probability_from_public_payload(label: str, value: object) -> Decimal:
    parsed = _decimal_from_public_payload(label, value)
    _require_probability_six_decimal_decimal(label, parsed)
    return parsed


def _datetime_from_public_payload(label: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{label} must be a canonical UTC datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a canonical UTC datetime") from exc
    _require_utc_datetime(label, parsed)
    if parsed.isoformat() != value:
        raise ValueError(f"{label} must be a canonical UTC datetime")
    return parsed


def _string_from_public_payload(label: str, value: object) -> str:
    _require_canonical_string(label, value)
    return value


def _status_from_public_payload(label: str, value: object) -> str:
    _require_status(label, value)
    return value


def _manual_review_priority_from_public_payload(
    label: str,
    value: object,
) -> str:
    _require_manual_review_priority(label, value)
    return value


def _digest_from_public_payload(label: str, value: object) -> str:
    _require_public_digest(label, value)
    return value


def _reason_codes_from_public_payload(
    label: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    result = tuple(value)
    _require_reason_codes_tuple(label, result)
    return result


def _true_from_public_payload(label: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{label} must be True")
    return True


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
    manual_review_priority: str
    domain_count: Decimal
    independent_evidence_count: Decimal
    source_family_count: Decimal
    latest_evidence_age_seconds: Decimal
    freshness_decay_score: Decimal
    domain_consensus_score: Decimal
    contradiction_pressure_score: Decimal
    source_authority_score: Decimal
    quorum_decay_score: Decimal
    manual_review_priority_score: Decimal
    reason_codes: tuple[str, ...]


def _row_values_for_input(
    row: ResearchStrategyDomainEvidenceQuorumDecayInput,
    *,
    config: ResearchStrategyDomainEvidenceQuorumDecayConfig,
) -> _RowValues:
    freshness_decay_score = _freshness_decay_score(
        row.latest_evidence_age_seconds,
        config.max_latest_evidence_age_seconds_watch,
    )
    quorum_decay_score = _quorum_decay_score(
        domain_count=row.domain_count,
        independent_evidence_count=row.independent_evidence_count,
        source_family_count=row.source_family_count,
        freshness_decay_score=freshness_decay_score,
        domain_consensus_score=row.domain_consensus_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        source_authority_score=row.source_authority_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        row,
        freshness_decay_score=freshness_decay_score,
        quorum_decay_score=quorum_decay_score,
        config=config,
    )
    status = _row_status(reason_codes)
    manual_review_priority_score = _manual_review_priority_score(
        freshness_decay_score=freshness_decay_score,
        quorum_decay_score=quorum_decay_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
    )
    return _RowValues(
        aggregate_row_hash=_public_hash(row.domain_evidence_key),
        status=status,
        manual_review_priority=_manual_review_priority(status),
        domain_count=row.domain_count,
        independent_evidence_count=row.independent_evidence_count,
        source_family_count=row.source_family_count,
        latest_evidence_age_seconds=row.latest_evidence_age_seconds,
        freshness_decay_score=freshness_decay_score,
        domain_consensus_score=row.domain_consensus_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        source_authority_score=row.source_authority_score,
        quorum_decay_score=quorum_decay_score,
        manual_review_priority_score=manual_review_priority_score,
        reason_codes=reason_codes,
    )


def _row_from_values(
    aggregate_row_number: Decimal,
    values: _RowValues,
) -> ResearchStrategyDomainEvidenceQuorumDecayRow:
    return ResearchStrategyDomainEvidenceQuorumDecayRow(
        aggregate_row_number=aggregate_row_number,
        aggregate_row_hash=values.aggregate_row_hash,
        status=values.status,
        manual_review_priority=values.manual_review_priority,
        domain_count=values.domain_count,
        independent_evidence_count=values.independent_evidence_count,
        source_family_count=values.source_family_count,
        latest_evidence_age_seconds=values.latest_evidence_age_seconds,
        freshness_decay_score=values.freshness_decay_score,
        domain_consensus_score=values.domain_consensus_score,
        contradiction_pressure_score=values.contradiction_pressure_score,
        source_authority_score=values.source_authority_score,
        quorum_decay_score=values.quorum_decay_score,
        manual_review_priority_score=values.manual_review_priority_score,
        reason_codes=values.reason_codes,
    )


def _row_reason_codes(
    row: (
        ResearchStrategyDomainEvidenceQuorumDecayInput
        | ResearchStrategyDomainEvidenceQuorumDecayRow
    ),
    *,
    freshness_decay_score: Decimal,
    quorum_decay_score: Decimal,
    config: ResearchStrategyDomainEvidenceQuorumDecayConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_floor_reason(
        reasons,
        DOMAIN_QUORUM_BLOCK_REASON,
        DOMAIN_QUORUM_WATCH_REASON,
        row.domain_count,
        config.min_domain_count_pass,
        config.min_domain_count_watch,
    )
    _append_floor_reason(
        reasons,
        EVIDENCE_QUORUM_BLOCK_REASON,
        EVIDENCE_QUORUM_WATCH_REASON,
        row.independent_evidence_count,
        config.min_independent_evidence_count_pass,
        config.min_independent_evidence_count_watch,
    )
    _append_floor_reason(
        reasons,
        SOURCE_FAMILY_BLOCK_REASON,
        SOURCE_FAMILY_WATCH_REASON,
        row.source_family_count,
        config.min_source_family_count_pass,
        config.min_source_family_count_watch,
    )
    if row.latest_evidence_age_seconds > config.max_latest_evidence_age_seconds_watch:
        reasons.append(FRESHNESS_DECAY_BLOCK_REASON)
    elif row.latest_evidence_age_seconds > config.max_latest_evidence_age_seconds_pass:
        reasons.append(FRESHNESS_DECAY_WATCH_REASON)
    _append_floor_reason(
        reasons,
        CONSENSUS_SUPPORT_BLOCK_REASON,
        CONSENSUS_SUPPORT_WATCH_REASON,
        row.domain_consensus_score,
        config.domain_consensus_score_pass_floor,
        config.domain_consensus_score_watch_floor,
    )
    if row.contradiction_pressure_score >= config.contradiction_pressure_block_ceiling:
        reasons.append(CONTRADICTION_PRESSURE_BLOCK_REASON)
    elif row.contradiction_pressure_score > config.contradiction_pressure_watch_ceiling:
        reasons.append(CONTRADICTION_PRESSURE_WATCH_REASON)
    _append_floor_reason(
        reasons,
        SOURCE_AUTHORITY_BLOCK_REASON,
        SOURCE_AUTHORITY_WATCH_REASON,
        row.source_authority_score,
        config.source_authority_score_pass_floor,
        config.source_authority_score_watch_floor,
    )
    if quorum_decay_score < config.quorum_decay_score_watch_floor:
        reasons.append(SCORE_BLOCK_REASON)
    elif quorum_decay_score < config.quorum_decay_score_pass_floor:
        reasons.append(SCORE_WATCH_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    _ = freshness_decay_score
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


def _freshness_decay_score(age_seconds: Decimal, watch_ceiling: Decimal) -> Decimal:
    if watch_ceiling <= ZERO:
        raise ValueError("watch ceiling must be positive")
    with localcontext(DECIMAL_CONTEXT):
        raw_score = ONE - (age_seconds / watch_ceiling)
    if raw_score <= ZERO:
        return ZERO
    return min(_quantize(raw_score), ONE)


def _quorum_decay_score(
    *,
    domain_count: Decimal,
    independent_evidence_count: Decimal,
    source_family_count: Decimal,
    freshness_decay_score: Decimal,
    domain_consensus_score: Decimal,
    contradiction_pressure_score: Decimal,
    source_authority_score: Decimal,
    config: ResearchStrategyDomainEvidenceQuorumDecayConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (
                _bounded_ratio(domain_count, config.min_domain_count_pass)
                + _bounded_ratio(
                    independent_evidence_count,
                    config.min_independent_evidence_count_pass,
                )
                + _bounded_ratio(source_family_count, config.min_source_family_count_pass)
                + freshness_decay_score
                + domain_consensus_score
                + _quantize(ONE - contradiction_pressure_score)
                + source_authority_score
            )
            / SEVEN,
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


def _manual_review_priority(status: str) -> str:
    return MANUAL_REVIEW_PRIORITY_BY_STATUS[status]


def _manual_review_priority_score(
    *,
    freshness_decay_score: Decimal,
    quorum_decay_score: Decimal,
    contradiction_pressure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return max(
            _quantize(ONE - freshness_decay_score),
            _quantize(ONE - quorum_decay_score),
            contradiction_pressure_score,
        )


def _rollup_status(rows: tuple[ResearchStrategyDomainEvidenceQuorumDecayRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyDomainEvidenceQuorumDecayRow, ...],
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
    rows: tuple[ResearchStrategyDomainEvidenceQuorumDecayRow, ...],
) -> tuple[ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=COUNT_QUANTUM,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount(
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
    config: ResearchStrategyDomainEvidenceQuorumDecayConfig,
    rows: tuple[ResearchStrategyDomainEvidenceQuorumDecayRow, ...],
) -> dict[str, Any]:
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "config": config,
        "domain_evidence_item_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "domain_quorum_attention_count": _kind_count(rows, "domain_quorum_"),
        "evidence_quorum_attention_count": _kind_count(rows, "evidence_quorum_"),
        "source_family_attention_count": _kind_count(rows, "source_family_"),
        "freshness_decay_attention_count": _kind_count(rows, "freshness_decay_"),
        "consensus_support_attention_count": _kind_count(rows, "consensus_support_"),
        "contradiction_pressure_attention_count": _kind_count(
            rows,
            "contradiction_pressure_",
        ),
        "source_authority_attention_count": _kind_count(rows, "source_authority_"),
        "score_attention_count": _kind_count(rows, "score_"),
        "manual_review_required_count": _count(
            sum(1 for row in rows if row.manual_review_priority != "routine"),
        ),
        "mean_quorum_decay_score": _mean(tuple(row.quorum_decay_score for row in rows)),
        "lowest_quorum_decay_score": _min_decimal(
            tuple(row.quorum_decay_score for row in rows),
        ),
        "highest_contradiction_pressure_score": _max_decimal(
            tuple(row.contradiction_pressure_score for row in rows),
        ),
        "highest_manual_review_priority_score": _max_decimal(
            tuple(row.manual_review_priority_score for row in rows),
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
    inputs: Iterable[ResearchStrategyDomainEvidenceQuorumDecayInput],
) -> tuple[ResearchStrategyDomainEvidenceQuorumDecayInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_keys: set[str] = set()
    for row in rows:
        if type(row) is not ResearchStrategyDomainEvidenceQuorumDecayInput:
            raise ValueError(
                "inputs must contain ResearchStrategyDomainEvidenceQuorumDecayInput values",
            )
        _revalidate_input_for_payload(row)
        if row.domain_evidence_key in seen_keys:
            raise ValueError("inputs must not contain duplicate domain_evidence_key values")
        seen_keys.add(row.domain_evidence_key)
    return rows


def _normalize_rows(
    rows: Iterable[ResearchStrategyDomainEvidenceQuorumDecayRow],
) -> tuple[ResearchStrategyDomainEvidenceQuorumDecayRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_hashes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyDomainEvidenceQuorumDecayRow:
            raise ValueError(
                "rows must contain ResearchStrategyDomainEvidenceQuorumDecayRow values",
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
    rows: Iterable[ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount],
) -> tuple[ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_codes: set[str] = set()
    for row in values:
        if type(row) is not ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount values",
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
    row: ResearchStrategyDomainEvidenceQuorumDecayRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -row.manual_review_priority_score,
        -STATUS_WEIGHT[row.status],
        -row.contradiction_pressure_score,
        -_quorum_decay_gap(row.quorum_decay_score),
        row.aggregate_row_hash,
    )


def _row_values_sort_key(
    values: _RowValues,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        -values.manual_review_priority_score,
        -STATUS_WEIGHT[values.status],
        -values.contradiction_pressure_score,
        -_quorum_decay_gap(values.quorum_decay_score),
        values.aggregate_row_hash,
    )


def _status_count(
    rows: tuple[ResearchStrategyDomainEvidenceQuorumDecayRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _kind_count(
    rows: tuple[ResearchStrategyDomainEvidenceQuorumDecayRow, ...],
    kind: str,
) -> Decimal:
    reason_prefix = "research_strategy_domain_evidence_quorum_decay_" + kind
    return _count(
        sum(
            1
            for row in rows
            if any(
                reason_code.startswith(reason_prefix)
                for reason_code in row.reason_codes
            )
        ),
    )


def _validate_row(row: ResearchStrategyDomainEvidenceQuorumDecayRow) -> None:
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.manual_review_priority != _manual_review_priority(row.status):
        raise ValueError("manual_review_priority must match status")
    expected_priority_score = _manual_review_priority_score(
        freshness_decay_score=row.freshness_decay_score,
        quorum_decay_score=row.quorum_decay_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
    )
    if row.manual_review_priority_score != expected_priority_score:
        raise ValueError("manual_review_priority_score must match row fields")
    _require_hard_flags("row", row)


def _validate_row_against_config(
    row: ResearchStrategyDomainEvidenceQuorumDecayRow,
    config: ResearchStrategyDomainEvidenceQuorumDecayConfig,
) -> None:
    expected_freshness = _freshness_decay_score(
        row.latest_evidence_age_seconds,
        config.max_latest_evidence_age_seconds_watch,
    )
    if row.freshness_decay_score != expected_freshness:
        raise ValueError("freshness_decay_score must match config and row fields")
    expected_quorum_score = _quorum_decay_score(
        domain_count=row.domain_count,
        independent_evidence_count=row.independent_evidence_count,
        source_family_count=row.source_family_count,
        freshness_decay_score=expected_freshness,
        domain_consensus_score=row.domain_consensus_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        source_authority_score=row.source_authority_score,
        config=config,
    )
    if row.quorum_decay_score != expected_quorum_score:
        raise ValueError("quorum_decay_score must match config and row fields")
    expected_reason_codes = _row_reason_codes(
        row,
        freshness_decay_score=expected_freshness,
        quorum_decay_score=expected_quorum_score,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match config and row fields")
    expected_status = _row_status(expected_reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match config and row fields")
    expected_priority = _manual_review_priority(expected_status)
    if row.manual_review_priority != expected_priority:
        raise ValueError("manual_review_priority must match config and row fields")
    expected_priority_score = _manual_review_priority_score(
        freshness_decay_score=expected_freshness,
        quorum_decay_score=expected_quorum_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
    )
    if row.manual_review_priority_score != expected_priority_score:
        raise ValueError(
            "manual_review_priority_score must match config and row fields",
        )


def _validate_report(report: ResearchStrategyDomainEvidenceQuorumDecayReport) -> None:
    rows = report.rows
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    for row in rows:
        _validate_row_against_config(row, report.config)
    if report.domain_evidence_item_count != _count(len(rows)):
        raise ValueError("domain_evidence_item_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    for field_name, kind in (
        ("domain_quorum_attention_count", "domain_quorum_"),
        ("evidence_quorum_attention_count", "evidence_quorum_"),
        ("source_family_attention_count", "source_family_"),
        ("freshness_decay_attention_count", "freshness_decay_"),
        ("consensus_support_attention_count", "consensus_support_"),
        ("contradiction_pressure_attention_count", "contradiction_pressure_"),
        ("source_authority_attention_count", "source_authority_"),
        ("score_attention_count", "score_"),
    ):
        if getattr(report, field_name) != _kind_count(rows, kind):
            raise ValueError(f"{field_name} must match rows")
    expected_manual_review_count = _count(
        sum(1 for row in rows if row.manual_review_priority != "routine"),
    )
    if report.manual_review_required_count != expected_manual_review_count:
        raise ValueError("manual_review_required_count must match rows")
    if report.mean_quorum_decay_score != _mean(
        tuple(row.quorum_decay_score for row in rows),
    ):
        raise ValueError("mean_quorum_decay_score must match rows")
    if report.lowest_quorum_decay_score != _min_decimal(
        tuple(row.quorum_decay_score for row in rows),
    ):
        raise ValueError("lowest_quorum_decay_score must match rows")
    if report.highest_contradiction_pressure_score != _max_decimal(
        tuple(row.contradiction_pressure_score for row in rows),
    ):
        raise ValueError("highest_contradiction_pressure_score must match rows")
    if report.highest_manual_review_priority_score != _max_decimal(
        tuple(row.manual_review_priority_score for row in rows),
    ):
        raise ValueError("highest_manual_review_priority_score must match rows")
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
    report: ResearchStrategyDomainEvidenceQuorumDecayReport,
) -> None:
    _require_exact_type(report, ResearchStrategyDomainEvidenceQuorumDecayReport, "report")
    _require_utc_datetime("generated_at", report.generated_at)
    _require_canonical_string("config_version", report.config_version)
    _require_exact_type(
        report.config,
        ResearchStrategyDomainEvidenceQuorumDecayConfig,
        "config",
    )
    _revalidate_config_for_payload(report.config)
    if report.config_version != report.config.config_version:
        raise ValueError("config_version must match config")
    for field_name in (
        "domain_evidence_item_count",
        "pass_count",
        "watch_count",
        "block_count",
        "domain_quorum_attention_count",
        "evidence_quorum_attention_count",
        "source_family_attention_count",
        "freshness_decay_attention_count",
        "consensus_support_attention_count",
        "contradiction_pressure_attention_count",
        "source_authority_attention_count",
        "score_attention_count",
        "manual_review_required_count",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(report, field_name))
    for field_name in (
        "mean_quorum_decay_score",
        "lowest_quorum_decay_score",
        "highest_contradiction_pressure_score",
        "highest_manual_review_priority_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(report, field_name))
    _require_status("status", report.status)
    _require_public_digest("public_digest", report.public_digest)
    _normalize_report_reason_codes(report.reason_codes)
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in report.reason_code_counts:
        _revalidate_reason_code_count_for_payload(row)
    _normalize_reason_code_counts(report.reason_code_counts)
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        _revalidate_row_for_payload(row)
    _normalize_rows(report.rows)
    _validate_report(report)
    _require_hard_flags("report", report)


def _revalidate_config_for_payload(
    config: ResearchStrategyDomainEvidenceQuorumDecayConfig,
) -> None:
    _require_exact_type(
        config,
        ResearchStrategyDomainEvidenceQuorumDecayConfig,
        "config",
    )
    _require_canonical_string("config_version", config.config_version)
    if (
        config.config_version
        != DEFAULT_RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "min_domain_count_pass",
        "min_domain_count_watch",
        "min_independent_evidence_count_pass",
        "min_independent_evidence_count_watch",
        "min_source_family_count_pass",
        "min_source_family_count_watch",
        "max_latest_evidence_age_seconds_pass",
        "max_latest_evidence_age_seconds_watch",
    ):
        _require_positive_six_decimal_decimal(
            field_name,
            getattr(config, field_name),
        )
    for field_name in (
        "domain_consensus_score_pass_floor",
        "domain_consensus_score_watch_floor",
        "contradiction_pressure_watch_ceiling",
        "contradiction_pressure_block_ceiling",
        "source_authority_score_pass_floor",
        "source_authority_score_watch_floor",
        "quorum_decay_score_pass_floor",
        "quorum_decay_score_watch_floor",
    ):
        _require_probability_six_decimal_decimal(
            field_name,
            getattr(config, field_name),
        )
    _require_at_least(
        "min_domain_count_pass",
        config.min_domain_count_pass,
        config.min_domain_count_watch,
    )
    _require_at_least(
        "min_independent_evidence_count_pass",
        config.min_independent_evidence_count_pass,
        config.min_independent_evidence_count_watch,
    )
    _require_at_least(
        "min_source_family_count_pass",
        config.min_source_family_count_pass,
        config.min_source_family_count_watch,
    )
    if (
        config.max_latest_evidence_age_seconds_pass
        >= config.max_latest_evidence_age_seconds_watch
    ):
        raise ValueError(
            "max_latest_evidence_age_seconds_pass must be below its watch level",
        )
    _require_at_least(
        "domain_consensus_score_pass_floor",
        config.domain_consensus_score_pass_floor,
        config.domain_consensus_score_watch_floor,
    )
    _require_at_most(
        "contradiction_pressure_watch_ceiling",
        config.contradiction_pressure_watch_ceiling,
        config.contradiction_pressure_block_ceiling,
    )
    _require_at_least(
        "source_authority_score_pass_floor",
        config.source_authority_score_pass_floor,
        config.source_authority_score_watch_floor,
    )
    _require_at_least(
        "quorum_decay_score_pass_floor",
        config.quorum_decay_score_pass_floor,
        config.quorum_decay_score_watch_floor,
    )
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)


def _revalidate_input_for_payload(
    row: ResearchStrategyDomainEvidenceQuorumDecayInput,
) -> None:
    _require_exact_type(
        row,
        ResearchStrategyDomainEvidenceQuorumDecayInput,
        "input",
    )
    _require_canonical_string("domain_evidence_key", row.domain_evidence_key)
    for field_name in (
        "domain_count",
        "independent_evidence_count",
        "source_family_count",
        "latest_evidence_age_seconds",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(row, field_name))
    for field_name in (
        "domain_consensus_score",
        "contradiction_pressure_score",
        "source_authority_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(row, field_name))
    _require_hard_flags("input", row)
    _reject_unsafe_public_payload("input", row)


def _revalidate_row_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyDomainEvidenceQuorumDecayRow:
        raise ValueError(
            "rows must contain ResearchStrategyDomainEvidenceQuorumDecayRow values",
        )
    _require_positive_six_decimal_decimal("aggregate_row_number", row.aggregate_row_number)
    _require_public_digest("aggregate_row_hash", row.aggregate_row_hash)
    _require_status("status", row.status)
    _require_manual_review_priority(
        "manual_review_priority",
        row.manual_review_priority,
    )
    for field_name in (
        "domain_count",
        "independent_evidence_count",
        "source_family_count",
        "latest_evidence_age_seconds",
    ):
        _require_nonnegative_six_decimal_decimal(field_name, getattr(row, field_name))
    for field_name in (
        "freshness_decay_score",
        "domain_consensus_score",
        "contradiction_pressure_score",
        "source_authority_score",
        "quorum_decay_score",
        "manual_review_priority_score",
    ):
        _require_probability_six_decimal_decimal(field_name, getattr(row, field_name))
    _normalize_row_reason_codes(row.reason_codes)
    _validate_row(row)


def _revalidate_reason_code_count_for_payload(row: object) -> None:
    if type(row) is not ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount:
        raise ValueError(
            "reason_code_counts must contain "
            "ResearchStrategyDomainEvidenceQuorumDecayReasonCodeCount values",
        )
    if type(row.reason_code) is not str or row.reason_code not in REPORT_REASON_CODES:
        raise ValueError("reason_code must be a known reason code")
    _require_positive_six_decimal_decimal("count", row.count)
    _require_hard_flags("reason_code_count", row)


def _quorum_decay_gap(value: Decimal) -> Decimal:
    return _quantize(ONE - value)


def _public_hash(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _computed_report_digest(
    report: ResearchStrategyDomainEvidenceQuorumDecayReport,
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
        value not in RESEARCH_STRATEGY_DOMAIN_EVIDENCE_QUORUM_DECAY_REPORT_STATUSES
    ):
        raise ValueError(f"{label} must be pass, watch, or block")


def _require_manual_review_priority(label: str, value: object) -> None:
    if type(value) is not str or value not in MANUAL_REVIEW_PRIORITIES:
        raise ValueError(f"{label} must be routine, priority, or urgent")


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
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{label} must not use signed zero")
    return _quantize(value)


def _normalize_nonnegative_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{label} must not use signed zero")
    if value < ZERO:
        raise ValueError(f"{label} must be nonnegative")
    return _quantize(value)


def _normalize_positive_decimal(label: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(label, value)
    if normalized <= ZERO:
        raise ValueError(f"{label} must be positive")
    return normalized


def _normalize_probability_decimal(label: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{label} must not use signed zero")
    if value < ZERO or value > ONE:
        raise ValueError(f"{label} must be between 0 and 1")
    return _quantize(value)


def _require_six_decimal_decimal(label: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{label} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{label} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{label} must not use signed zero")
    if value.as_tuple().exponent != -6 or value != _quantize(value):
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
