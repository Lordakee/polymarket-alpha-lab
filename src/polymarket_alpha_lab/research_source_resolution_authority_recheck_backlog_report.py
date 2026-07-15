"""Pure report-only resolution authority recheck backlog prioritization."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_RECHECK_BACKLOG_REPORT_CONFIG_VERSION = (
    "research-source-resolution-authority-recheck-backlog-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SIX = Decimal("6.000000")
_DECIMAL_CONTEXT = Context(prec=50, rounding=ROUND_HALF_UP)
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_CANONICAL_DECIMAL_RE = re.compile(r"^(?:0|[1-9][0-9]*)\.[0-9]{6}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "row_count",
    "stale_authority_count",
    "contradiction_pressure_count",
    "rule_ambiguity_count",
    "source_availability_gap_count",
    "reviewer_coverage_gap_count",
    "deadline_proximity_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_recheck_priority_score",
    "max_recheck_priority_score",
    "status",
    "rows",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_DECIMAL_FIELDS = (
    "row_count",
    "stale_authority_count",
    "contradiction_pressure_count",
    "rule_ambiguity_count",
    "source_availability_gap_count",
    "reviewer_coverage_gap_count",
    "deadline_proximity_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_recheck_priority_score",
    "max_recheck_priority_score",
)
_ROW_PAYLOAD_FIELDS = (
    "review_bucket",
    "authority_bucket",
    "authority_age_seconds",
    "authority_freshness_score",
    "contradiction_pressure_score",
    "rule_ambiguity_score",
    "source_availability_score",
    "source_unavailability_score",
    "reviewer_coverage_score",
    "reviewer_coverage_gap_score",
    "deadline_proximity_score",
    "recheck_priority_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_ROW_DECIMAL_FIELDS = (
    "authority_age_seconds",
    "authority_freshness_score",
    "contradiction_pressure_score",
    "rule_ambiguity_score",
    "source_availability_score",
    "source_unavailability_score",
    "reviewer_coverage_score",
    "reviewer_coverage_gap_score",
    "deadline_proximity_score",
    "recheck_priority_score",
)
_ROW_REASON_CODE_GROUPS = (
    (
        "authority_freshness_clear",
        "authority_freshness_watch",
        "authority_freshness_block",
    ),
    (
        "contradiction_pressure_clear",
        "contradiction_pressure_watch",
        "contradiction_pressure_block",
    ),
    (
        "rule_ambiguity_clear",
        "rule_ambiguity_watch",
        "rule_ambiguity_block",
    ),
    (
        "source_availability_clear",
        "source_availability_watch",
        "source_availability_block",
    ),
    (
        "reviewer_coverage_clear",
        "reviewer_coverage_watch",
        "reviewer_coverage_block",
    ),
    (
        "deadline_proximity_clear",
        "deadline_proximity_watch",
        "deadline_proximity_block",
    ),
)
_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_" + "candidate",
    "candidate_" + "id",
    "candidate" + "-",
    "market_" + "id",
    "market_" + "sl" + "ug",
    "market_" + "ques" + "tion",
    "market" + "-",
    "sl" + "ug",
    "ques" + "tion",
    "://",
    "www.",
    "u" + "rl",
    "d" + "sn",
    "tab" + "le",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "li" + "ve",
    "source_" + "text",
    "private_" + "candidate",
    "private_" + "market",
    "private_" + "source",
    "private_" + "resolution",
)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRecheckBacklogConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_RECHECK_BACKLOG_REPORT_CONFIG_VERSION
    )
    fresh_authority_age_seconds: Decimal = Decimal("3600.000000")
    stale_authority_age_seconds: Decimal = Decimal("86400.000000")
    deadline_proximity_window_seconds: Decimal = Decimal("172800.000000")
    watch_priority_score: Decimal = Decimal("0.250000")
    block_priority_score: Decimal = Decimal("0.700000")
    watch_authority_freshness_score: Decimal = Decimal("0.250000")
    block_authority_freshness_score: Decimal = Decimal("1.000000")
    watch_contradiction_pressure_score: Decimal = Decimal("0.300000")
    block_contradiction_pressure_score: Decimal = Decimal("0.700000")
    watch_rule_ambiguity_score: Decimal = Decimal("0.300000")
    block_rule_ambiguity_score: Decimal = Decimal("0.700000")
    min_source_availability_score: Decimal = Decimal("0.700000")
    block_source_availability_score: Decimal = Decimal("0.300000")
    min_reviewer_coverage_score: Decimal = Decimal("0.700000")
    block_reviewer_coverage_score: Decimal = Decimal("0.300000")
    watch_deadline_proximity_score: Decimal = Decimal("0.500000")
    block_deadline_proximity_score: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRecheckBacklogConfig:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRecheckBacklogConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionAuthorityRecheckBacklogConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceResolutionAuthorityRecheckBacklogConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_RECHECK_BACKLOG_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "fresh_authority_age_seconds",
            "stale_authority_age_seconds",
            "deadline_proximity_window_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_priority_score",
            "block_priority_score",
            "watch_authority_freshness_score",
            "block_authority_freshness_score",
            "watch_contradiction_pressure_score",
            "block_contradiction_pressure_score",
            "watch_rule_ambiguity_score",
            "block_rule_ambiguity_score",
            "min_source_availability_score",
            "block_source_availability_score",
            "min_reviewer_coverage_score",
            "block_reviewer_coverage_score",
            "watch_deadline_proximity_score",
            "block_deadline_proximity_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.stale_authority_age_seconds <= self.fresh_authority_age_seconds:
            raise ValueError(
                "stale_authority_age_seconds must exceed fresh_authority_age_seconds",
            )
        if self.block_priority_score <= self.watch_priority_score:
            raise ValueError("block_priority_score must exceed watch_priority_score")
        if (
            self.block_authority_freshness_score
            < self.watch_authority_freshness_score
        ):
            raise ValueError(
                "block_authority_freshness_score must be at least "
                "watch_authority_freshness_score",
            )
        if (
            self.block_contradiction_pressure_score
            < self.watch_contradiction_pressure_score
        ):
            raise ValueError(
                "block_contradiction_pressure_score must be at least "
                "watch_contradiction_pressure_score",
            )
        if self.block_rule_ambiguity_score < self.watch_rule_ambiguity_score:
            raise ValueError(
                "block_rule_ambiguity_score must be at least "
                "watch_rule_ambiguity_score",
            )
        if self.block_source_availability_score > self.min_source_availability_score:
            raise ValueError(
                "block_source_availability_score must not exceed "
                "min_source_availability_score",
            )
        if self.block_reviewer_coverage_score > self.min_reviewer_coverage_score:
            raise ValueError(
                "block_reviewer_coverage_score must not exceed "
                "min_reviewer_coverage_score",
            )
        if self.block_deadline_proximity_score < self.watch_deadline_proximity_score:
            raise ValueError(
                "block_deadline_proximity_score must be at least "
                "watch_deadline_proximity_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRecheckBacklogInput:
    review_bucket: str
    authority_bucket: str
    private_candidate_reference: str
    private_market_reference: str
    private_resolution_material: str
    authority_last_checked_at: datetime
    contradiction_pressure_score: Decimal
    rule_ambiguity_score: Decimal
    source_availability_score: Decimal
    reviewer_coverage_score: Decimal
    resolution_deadline_at: datetime | None = None
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRecheckBacklogInput:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRecheckBacklogInput does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionAuthorityRecheckBacklogInput:
            raise ValueError(
                "input must be exactly "
                "ResearchSourceResolutionAuthorityRecheckBacklogInput",
            )
        for field_name in ("review_bucket", "authority_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "private_candidate_reference",
            "private_market_reference",
            "private_resolution_material",
        ):
            _require_nonempty_text(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "authority_last_checked_at",
            _as_utc("authority_last_checked_at", self.authority_last_checked_at),
        )
        object.__setattr__(
            self,
            "resolution_deadline_at",
            _optional_as_utc("resolution_deadline_at", self.resolution_deadline_at),
        )
        for field_name in (
            "contradiction_pressure_score",
            "rule_ambiguity_score",
            "source_availability_score",
            "reviewer_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRecheckBacklogRow:
    review_bucket: str
    authority_bucket: str
    authority_age_seconds: Decimal
    authority_freshness_score: Decimal
    contradiction_pressure_score: Decimal
    rule_ambiguity_score: Decimal
    source_availability_score: Decimal
    source_unavailability_score: Decimal
    reviewer_coverage_score: Decimal
    reviewer_coverage_gap_score: Decimal
    deadline_proximity_score: Decimal
    recheck_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRecheckBacklogRow:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRecheckBacklogRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionAuthorityRecheckBacklogRow:
            raise ValueError(
                "row must be exactly "
                "ResearchSourceResolutionAuthorityRecheckBacklogRow",
            )
        for field_name in ("review_bucket", "authority_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "authority_age_seconds",
            _require_nonnegative_decimal(
                "authority_age_seconds",
                self.authority_age_seconds,
            ),
        )
        for field_name in (
            "authority_freshness_score",
            "contradiction_pressure_score",
            "rule_ambiguity_score",
            "source_availability_score",
            "source_unavailability_score",
            "reviewer_coverage_score",
            "reviewer_coverage_gap_score",
            "deadline_proximity_score",
            "recheck_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceResolutionAuthorityRecheckBacklogReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    stale_authority_count: Decimal
    contradiction_pressure_count: Decimal
    rule_ambiguity_count: Decimal
    source_availability_gap_count: Decimal
    reviewer_coverage_gap_count: Decimal
    deadline_proximity_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_recheck_priority_score: Decimal
    max_recheck_priority_score: Decimal
    status: str
    rows: tuple[ResearchSourceResolutionAuthorityRecheckBacklogRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceResolutionAuthorityRecheckBacklogReport:
            raise TypeError(
                "ResearchSourceResolutionAuthorityRecheckBacklogReport does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceResolutionAuthorityRecheckBacklogReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceResolutionAuthorityRecheckBacklogReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_RECHECK_BACKLOG_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "row_count",
            "stale_authority_count",
            "contradiction_pressure_count",
            "rule_ambiguity_count",
            "source_availability_gap_count",
            "reviewer_coverage_gap_count",
            "deadline_proximity_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_recheck_priority_score",
            "max_recheck_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report_consistency(self, strict_materialized=True)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(asdict(self))
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        _validate_payload_schema(payload)
        _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
        return payload


def build_research_source_resolution_authority_recheck_backlog_report(
    candidates: Sequence[ResearchSourceResolutionAuthorityRecheckBacklogInput],
    *,
    generated_at: datetime,
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig | None = None,
) -> ResearchSourceResolutionAuthorityRecheckBacklogReport:
    if config is None:
        config = ResearchSourceResolutionAuthorityRecheckBacklogConfig()
    elif type(config) is not ResearchSourceResolutionAuthorityRecheckBacklogConfig:
        raise ValueError(
            "config must be a ResearchSourceResolutionAuthorityRecheckBacklogConfig",
        )
    else:
        config = _reconstruct_config(config)
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    for item in normalized_candidates:
        if item.authority_last_checked_at > generated_at:
            raise ValueError("authority_last_checked_at must not be after generated_at")
    rows = _normalize_rows(
        tuple(_row_for_input(item, config, generated_at) for item in normalized_candidates),
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "row_count": _decimal_count(len(rows)),
        "stale_authority_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.authority_freshness_score >= config.watch_authority_freshness_score
            ),
        ),
        "contradiction_pressure_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.contradiction_pressure_score
                >= config.watch_contradiction_pressure_score
            ),
        ),
        "rule_ambiguity_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.rule_ambiguity_score >= config.watch_rule_ambiguity_score
            ),
        ),
        "source_availability_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.source_availability_score <= config.min_source_availability_score
            ),
        ),
        "reviewer_coverage_gap_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.reviewer_coverage_score <= config.min_reviewer_coverage_score
            ),
        ),
        "deadline_proximity_count": _decimal_count(
            sum(
                1
                for row in rows
                if row.deadline_proximity_score >= config.watch_deadline_proximity_score
            ),
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_recheck_priority_score": _average(
            tuple(row.recheck_priority_score for row in rows),
        ),
        "max_recheck_priority_score": max(
            (row.recheck_priority_score for row in rows),
            default=_ZERO,
        ),
        "status": _report_status(rows),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchSourceResolutionAuthorityRecheckBacklogReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_source_resolution_authority_recheck_backlog_report_payload(
    report: ResearchSourceResolutionAuthorityRecheckBacklogReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchSourceResolutionAuthorityRecheckBacklogReport:
        _require_hard_flags("report", report)
        payload = report.payload
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        _validate_payload_schema(report)
        _require_hard_flags("payload", _DictFlags(report))
        _validate_payload_digest(report)
        payload = _report_from_payload(report).payload
    else:
        raise ValueError(
            "report must be a "
            "ResearchSourceResolutionAuthorityRecheckBacklogReport",
        )
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


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


def _reconstruct_config(
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig,
) -> ResearchSourceResolutionAuthorityRecheckBacklogConfig:
    _require_no_extra_dataclass_attrs("config", config)
    return ResearchSourceResolutionAuthorityRecheckBacklogConfig(
        **_dataclass_field_values(config),
    )


def _reconstruct_input(
    item: ResearchSourceResolutionAuthorityRecheckBacklogInput,
) -> ResearchSourceResolutionAuthorityRecheckBacklogInput:
    _require_no_extra_dataclass_attrs("candidate", item)
    return ResearchSourceResolutionAuthorityRecheckBacklogInput(
        **_dataclass_field_values(item),
    )


def _reconstruct_row(
    row: ResearchSourceResolutionAuthorityRecheckBacklogRow,
) -> ResearchSourceResolutionAuthorityRecheckBacklogRow:
    _require_no_extra_dataclass_attrs("row", row)
    return ResearchSourceResolutionAuthorityRecheckBacklogRow(
        **_dataclass_field_values(row),
    )


def _dataclass_field_values(value: object) -> dict[str, object]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _require_no_extra_dataclass_attrs(label: str, value: object) -> None:
    expected_fields = frozenset(field.name for field in fields(value))
    actual_fields = frozenset(vars(value))
    if actual_fields != expected_fields:
        raise ValueError(f"{label} contains tampered public attributes")


def _row_for_input(
    item: ResearchSourceResolutionAuthorityRecheckBacklogInput,
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig,
    generated_at: datetime,
) -> ResearchSourceResolutionAuthorityRecheckBacklogRow:
    authority_age = _age_seconds(generated_at, item.authority_last_checked_at)
    authority_freshness = _authority_freshness_score(authority_age, config)
    source_unavailability = _ratio_complement(item.source_availability_score)
    reviewer_gap = _ratio_complement(item.reviewer_coverage_score)
    deadline_proximity = _deadline_proximity_score(
        item.resolution_deadline_at,
        config,
        generated_at,
    )
    priority_score = _priority_score(
        authority_freshness_score=authority_freshness,
        contradiction_pressure_score=item.contradiction_pressure_score,
        rule_ambiguity_score=item.rule_ambiguity_score,
        source_unavailability_score=source_unavailability,
        reviewer_coverage_gap_score=reviewer_gap,
        deadline_proximity_score=deadline_proximity,
    )
    status = _row_status(
        authority_freshness_score=authority_freshness,
        contradiction_pressure_score=item.contradiction_pressure_score,
        rule_ambiguity_score=item.rule_ambiguity_score,
        source_availability_score=item.source_availability_score,
        reviewer_coverage_score=item.reviewer_coverage_score,
        deadline_proximity_score=deadline_proximity,
        recheck_priority_score=priority_score,
        config=config,
    )
    return ResearchSourceResolutionAuthorityRecheckBacklogRow(
        review_bucket=item.review_bucket,
        authority_bucket=item.authority_bucket,
        authority_age_seconds=authority_age,
        authority_freshness_score=authority_freshness,
        contradiction_pressure_score=item.contradiction_pressure_score,
        rule_ambiguity_score=item.rule_ambiguity_score,
        source_availability_score=item.source_availability_score,
        source_unavailability_score=source_unavailability,
        reviewer_coverage_score=item.reviewer_coverage_score,
        reviewer_coverage_gap_score=reviewer_gap,
        deadline_proximity_score=deadline_proximity,
        recheck_priority_score=priority_score,
        status=status,
        reason_codes=_row_reason_codes(
            item=item,
            status=status,
            authority_freshness_score=authority_freshness,
            deadline_proximity_score=deadline_proximity,
            config=config,
        ),
    )


def _authority_freshness_score(
    authority_age_seconds: Decimal,
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig,
) -> Decimal:
    if authority_age_seconds <= config.fresh_authority_age_seconds:
        return _ZERO
    if authority_age_seconds >= config.stale_authority_age_seconds:
        return _ONE
    with localcontext(_DECIMAL_CONTEXT):
        denominator = (
            config.stale_authority_age_seconds - config.fresh_authority_age_seconds
        )
        score = (
            authority_age_seconds - config.fresh_authority_age_seconds
        ) / denominator
    return _clamp_ratio(score)


def _deadline_proximity_score(
    resolution_deadline_at: datetime | None,
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig,
    generated_at: datetime,
) -> Decimal:
    if resolution_deadline_at is None:
        return _ZERO
    seconds_until_deadline = _seconds_between(resolution_deadline_at, generated_at)
    if seconds_until_deadline <= _ZERO:
        return _ONE
    if seconds_until_deadline >= config.deadline_proximity_window_seconds:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        score = _ONE - (
            seconds_until_deadline / config.deadline_proximity_window_seconds
        )
    return _clamp_ratio(score)


def _priority_score(
    *,
    authority_freshness_score: Decimal,
    contradiction_pressure_score: Decimal,
    rule_ambiguity_score: Decimal,
    source_unavailability_score: Decimal,
    reviewer_coverage_gap_score: Decimal,
    deadline_proximity_score: Decimal,
) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        score = (
            authority_freshness_score
            + contradiction_pressure_score
            + rule_ambiguity_score
            + source_unavailability_score
            + reviewer_coverage_gap_score
            + deadline_proximity_score
        ) / _SIX
    return _clamp_ratio(score)


def _row_status(
    *,
    authority_freshness_score: Decimal,
    contradiction_pressure_score: Decimal,
    rule_ambiguity_score: Decimal,
    source_availability_score: Decimal,
    reviewer_coverage_score: Decimal,
    deadline_proximity_score: Decimal,
    recheck_priority_score: Decimal,
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig,
) -> str:
    if (
        recheck_priority_score >= config.block_priority_score
        or authority_freshness_score >= config.block_authority_freshness_score
        or contradiction_pressure_score >= config.block_contradiction_pressure_score
        or rule_ambiguity_score >= config.block_rule_ambiguity_score
        or source_availability_score <= config.block_source_availability_score
        or reviewer_coverage_score <= config.block_reviewer_coverage_score
        or deadline_proximity_score >= config.block_deadline_proximity_score
    ):
        return "block"
    if (
        recheck_priority_score >= config.watch_priority_score
        or authority_freshness_score >= config.watch_authority_freshness_score
        or contradiction_pressure_score >= config.watch_contradiction_pressure_score
        or rule_ambiguity_score >= config.watch_rule_ambiguity_score
        or source_availability_score <= config.min_source_availability_score
        or reviewer_coverage_score <= config.min_reviewer_coverage_score
        or deadline_proximity_score >= config.watch_deadline_proximity_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    item: ResearchSourceResolutionAuthorityRecheckBacklogInput,
    status: str,
    authority_freshness_score: Decimal,
    deadline_proximity_score: Decimal,
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig,
) -> tuple[str, ...]:
    return _row_reason_codes_from_scores(
        status=status,
        authority_freshness_score=authority_freshness_score,
        contradiction_pressure_score=item.contradiction_pressure_score,
        rule_ambiguity_score=item.rule_ambiguity_score,
        source_availability_score=item.source_availability_score,
        reviewer_coverage_score=item.reviewer_coverage_score,
        deadline_proximity_score=deadline_proximity_score,
        input_reason_codes=item.reason_codes,
        config=config,
    )


def _row_reason_codes_from_scores(
    *,
    status: str,
    authority_freshness_score: Decimal,
    contradiction_pressure_score: Decimal,
    rule_ambiguity_score: Decimal,
    source_availability_score: Decimal,
    reviewer_coverage_score: Decimal,
    deadline_proximity_score: Decimal,
    input_reason_codes: Sequence[str],
    config: ResearchSourceResolutionAuthorityRecheckBacklogConfig,
) -> tuple[str, ...]:
    reason_codes = {f"authority_recheck_backlog_{status}"}
    if authority_freshness_score >= config.block_authority_freshness_score:
        reason_codes.add("authority_freshness_block")
    elif authority_freshness_score >= config.watch_authority_freshness_score:
        reason_codes.add("authority_freshness_watch")
    else:
        reason_codes.add("authority_freshness_clear")
    if contradiction_pressure_score >= config.block_contradiction_pressure_score:
        reason_codes.add("contradiction_pressure_block")
    elif contradiction_pressure_score >= config.watch_contradiction_pressure_score:
        reason_codes.add("contradiction_pressure_watch")
    else:
        reason_codes.add("contradiction_pressure_clear")
    if rule_ambiguity_score >= config.block_rule_ambiguity_score:
        reason_codes.add("rule_ambiguity_block")
    elif rule_ambiguity_score >= config.watch_rule_ambiguity_score:
        reason_codes.add("rule_ambiguity_watch")
    else:
        reason_codes.add("rule_ambiguity_clear")
    if source_availability_score <= config.block_source_availability_score:
        reason_codes.add("source_availability_block")
    elif source_availability_score <= config.min_source_availability_score:
        reason_codes.add("source_availability_watch")
    else:
        reason_codes.add("source_availability_clear")
    if reviewer_coverage_score <= config.block_reviewer_coverage_score:
        reason_codes.add("reviewer_coverage_block")
    elif reviewer_coverage_score <= config.min_reviewer_coverage_score:
        reason_codes.add("reviewer_coverage_watch")
    else:
        reason_codes.add("reviewer_coverage_clear")
    if deadline_proximity_score >= config.block_deadline_proximity_score:
        reason_codes.add("deadline_proximity_block")
    elif deadline_proximity_score >= config.watch_deadline_proximity_score:
        reason_codes.add("deadline_proximity_watch")
    else:
        reason_codes.add("deadline_proximity_clear")
    for reason_code in _normalize_reason_codes(
        "input_reason_codes",
        input_reason_codes,
        allow_empty=True,
    ):
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _normalize_candidates(
    candidates: Sequence[ResearchSourceResolutionAuthorityRecheckBacklogInput],
) -> tuple[ResearchSourceResolutionAuthorityRecheckBacklogInput, ...]:
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        raise ValueError("candidates must be a sequence")
    normalized: list[ResearchSourceResolutionAuthorityRecheckBacklogInput] = []
    seen: set[tuple[str, str]] = set()
    for item in candidates:
        if type(item) is not ResearchSourceResolutionAuthorityRecheckBacklogInput:
            raise ValueError(
                "candidate must be a "
                "ResearchSourceResolutionAuthorityRecheckBacklogInput",
            )
        item = _reconstruct_input(item)
        _require_hard_flags("candidate", item)
        key = (item.review_bucket, item.authority_bucket)
        if key in seen:
            raise ValueError("duplicate review_bucket and authority_bucket pair")
        seen.add(key)
        normalized.append(item)
    return tuple(sorted(normalized, key=lambda item: (item.review_bucket, item.authority_bucket)))


def _normalize_rows(
    rows: Sequence[ResearchSourceResolutionAuthorityRecheckBacklogRow],
) -> tuple[ResearchSourceResolutionAuthorityRecheckBacklogRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchSourceResolutionAuthorityRecheckBacklogRow] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceResolutionAuthorityRecheckBacklogRow:
            raise ValueError(
                "row must be a ResearchSourceResolutionAuthorityRecheckBacklogRow",
            )
        row = _reconstruct_row(row)
        _require_hard_flags("row", row)
        key = (row.review_bucket, row.authority_bucket)
        if key in seen:
            raise ValueError("duplicate row review_bucket and authority_bucket pair")
        seen.add(key)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _row_sort_key(
    row: ResearchSourceResolutionAuthorityRecheckBacklogRow,
) -> tuple[Decimal, int, str, str]:
    return (
        row.recheck_priority_score.copy_negate(),
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.review_bucket,
        row.authority_bucket,
    )


def _report_reason_codes(
    rows: Sequence[ResearchSourceResolutionAuthorityRecheckBacklogRow],
) -> tuple[str, ...]:
    if not rows:
        return ("authority_recheck_backlog_empty",)
    reason_codes = {f"authority_recheck_backlog_{_report_status(rows)}"}
    for row in rows:
        reason_codes.update(row.reason_codes)
    return tuple(sorted(reason_codes))


def _status_count(
    rows: Sequence[ResearchSourceResolutionAuthorityRecheckBacklogRow],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _report_status(
    rows: Sequence[ResearchSourceResolutionAuthorityRecheckBacklogRow],
) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _average(values: Sequence[Decimal]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        average = sum(values, _ZERO) / _decimal_count(len(values))
    return _quantize(average)


def _validate_row_consistency(
    row: ResearchSourceResolutionAuthorityRecheckBacklogRow,
) -> None:
    if row.source_unavailability_score != _ratio_complement(
        row.source_availability_score,
    ):
        raise ValueError("source_unavailability_score must equal source availability gap")
    if row.reviewer_coverage_gap_score != _ratio_complement(
        row.reviewer_coverage_score,
    ):
        raise ValueError("reviewer_coverage_gap_score must equal reviewer coverage gap")
    expected_score = _priority_score(
        authority_freshness_score=row.authority_freshness_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        rule_ambiguity_score=row.rule_ambiguity_score,
        source_unavailability_score=row.source_unavailability_score,
        reviewer_coverage_gap_score=row.reviewer_coverage_gap_score,
        deadline_proximity_score=row.deadline_proximity_score,
    )
    if row.recheck_priority_score != expected_score:
        raise ValueError("recheck_priority_score must match component scores")
    backlog_reason_codes = {
        f"authority_recheck_backlog_{status}" for status in _STATUSES
    }
    expected_backlog_reason_code = f"authority_recheck_backlog_{row.status}"
    if set(row.reason_codes).intersection(backlog_reason_codes) != {
        expected_backlog_reason_code,
    }:
        raise ValueError("row reason_codes must match status")
    category_severities: list[str] = []
    for reason_code_group in _ROW_REASON_CODE_GROUPS:
        present = set(row.reason_codes).intersection(reason_code_group)
        if len(present) != 1:
            raise ValueError("row reason_codes must contain one code per category")
        category_severities.append(next(iter(present)).rsplit("_", 1)[1])
    if "block" in category_severities and row.status != "block":
        raise ValueError("row status must match block reason_codes")
    if "watch" in category_severities and row.status == "pass":
        raise ValueError("row status must match watch reason_codes")


def _validate_report_consistency(
    report: ResearchSourceResolutionAuthorityRecheckBacklogReport,
    *,
    strict_materialized: bool = False,
) -> None:
    rows = report.rows
    normalized_rows = _normalize_rows(rows)
    if rows != normalized_rows:
        raise ValueError("rows must use canonical order")
    for row in rows:
        _validate_row_consistency(row)
        if strict_materialized:
            _validate_row_materialized_fields(row)
    expected_counts = {
        "row_count": _decimal_count(len(rows)),
        "stale_authority_count": _decimal_count(
            _reason_pressure_count(rows, "authority_freshness"),
        ),
        "contradiction_pressure_count": _decimal_count(
            _reason_pressure_count(rows, "contradiction_pressure"),
        ),
        "rule_ambiguity_count": _decimal_count(
            _reason_pressure_count(rows, "rule_ambiguity"),
        ),
        "source_availability_gap_count": _decimal_count(
            _reason_pressure_count(rows, "source_availability"),
        ),
        "reviewer_coverage_gap_count": _decimal_count(
            _reason_pressure_count(rows, "reviewer_coverage"),
        ),
        "deadline_proximity_count": _decimal_count(
            _reason_pressure_count(rows, "deadline_proximity"),
        ),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
    }
    for field_name, expected_value in expected_counts.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.average_recheck_priority_score != _average(
        tuple(row.recheck_priority_score for row in rows),
    ):
        raise ValueError("average_recheck_priority_score must match rows")
    if report.max_recheck_priority_score != max(
        (row.recheck_priority_score for row in rows),
        default=_ZERO,
    ):
        raise ValueError("max_recheck_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _validate_row_materialized_fields(
    row: ResearchSourceResolutionAuthorityRecheckBacklogRow,
) -> None:
    config = ResearchSourceResolutionAuthorityRecheckBacklogConfig()
    if row.authority_freshness_score != _authority_freshness_score(
        row.authority_age_seconds,
        config,
    ):
        raise ValueError("authority_freshness_score must match authority_age_seconds")
    expected_status = _row_status(
        authority_freshness_score=row.authority_freshness_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        rule_ambiguity_score=row.rule_ambiguity_score,
        source_availability_score=row.source_availability_score,
        reviewer_coverage_score=row.reviewer_coverage_score,
        deadline_proximity_score=row.deadline_proximity_score,
        recheck_priority_score=row.recheck_priority_score,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("row status must match row scores")
    input_reason_codes = tuple(
        reason_code.removeprefix("input_")
        for reason_code in row.reason_codes
        if reason_code.startswith("input_")
    )
    expected_reason_codes = _row_reason_codes_from_scores(
        status=expected_status,
        authority_freshness_score=row.authority_freshness_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        rule_ambiguity_score=row.rule_ambiguity_score,
        source_availability_score=row.source_availability_score,
        reviewer_coverage_score=row.reviewer_coverage_score,
        deadline_proximity_score=row.deadline_proximity_score,
        input_reason_codes=input_reason_codes,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("row reason_codes must match row scores")


def _reason_pressure_count(
    rows: Sequence[ResearchSourceResolutionAuthorityRecheckBacklogRow],
    reason_prefix: str,
) -> int:
    pressure_codes = {f"{reason_prefix}_watch", f"{reason_prefix}_block"}
    return sum(
        1 for row in rows if pressure_codes.intersection(row.reason_codes)
    )


def _report_values_without_digest(
    report: ResearchSourceResolutionAuthorityRecheckBacklogReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(dict(values))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest")
    expected = _report_digest_from_values(unsigned_payload)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_schema("report payload", payload, _REPORT_PAYLOAD_FIELDS)
    _payload_datetime(payload, "generated_at")
    config_version = _payload_string(payload, "config_version")
    if (
        config_version
        != DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_RECHECK_BACKLOG_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in _REPORT_DECIMAL_FIELDS:
        _payload_decimal(payload, field_name)
    _require_status("status", _payload_string(payload, "status"))
    _payload_reason_codes(payload, "reason_codes")
    _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )
    for field_name in ("paper_only", "report_only", "readonly"):
        if type(payload[field_name]) is not bool:
            raise ValueError(f"{field_name} must use canonical boolean schema")
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must use canonical list schema")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError(f"rows[{index}] must use canonical object schema")
        _require_exact_schema(f"rows[{index}]", row, _ROW_PAYLOAD_FIELDS)
        for field_name in ("review_bucket", "authority_bucket"):
            value = _payload_string(row, field_name)
            _require_public_identifier(field_name, value)
            _reject_unsafe_public_string(field_name, value)
        for field_name in _ROW_DECIMAL_FIELDS:
            _payload_decimal(row, field_name)
        _require_status("status", _payload_string(row, "status"))
        _payload_reason_codes(row, "reason_codes")
        for field_name in ("paper_only", "report_only", "readonly"):
            if type(row[field_name]) is not bool:
                raise ValueError(
                    f"rows[{index}].{field_name} must use canonical boolean schema",
                )


def _require_exact_schema(
    label: str,
    payload: dict[str, Any],
    expected_fields: tuple[str, ...],
) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} must use canonical object schema")
    if any(type(key) is not str for key in payload):
        raise ValueError(f"{label} keys must use canonical string schema")
    actual_fields = tuple(payload)
    if frozenset(actual_fields) != frozenset(expected_fields):
        raise ValueError(f"{label} must match exact canonical schema")
    if actual_fields != expected_fields:
        raise ValueError(f"{label} must use canonical field order")


def _payload_string(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must use canonical string schema")
    return value


def _payload_decimal(payload: Mapping[str, Any], field_name: str) -> Decimal:
    value = payload[field_name]
    if type(value) is not str or not _CANONICAL_DECIMAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must use canonical Decimal schema")
    decimal_value = Decimal(value)
    if not decimal_value.is_finite() or decimal_value.is_signed():
        raise ValueError(f"{field_name} must use canonical finite Decimal schema")
    if _quantize(decimal_value).to_eng_string() != value:
        raise ValueError(f"{field_name} must use canonical Decimal schema")
    return decimal_value


def _payload_datetime(payload: Mapping[str, Any], field_name: str) -> datetime:
    value = _payload_string(payload, field_name)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must use canonical datetime schema") from exc
    canonical = _as_utc(field_name, parsed)
    if canonical.isoformat() != value:
        raise ValueError(f"{field_name} must use canonical UTC datetime schema")
    return canonical


def _payload_reason_codes(
    payload: Mapping[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload[field_name]
    if type(value) is not list:
        raise ValueError(f"{field_name} must use canonical list schema")
    normalized = _normalize_reason_codes(
        field_name,
        value,
        allow_empty=False,
    )
    if list(normalized) != value:
        raise ValueError(f"{field_name} must use canonical sorted unique schema")
    return normalized


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceResolutionAuthorityRecheckBacklogReport:
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("rows must use canonical list schema")
    rows = tuple(_row_from_payload(row) for row in rows_value)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("payload rows must use canonical order")
    return ResearchSourceResolutionAuthorityRecheckBacklogReport(
        generated_at=_payload_datetime(payload, "generated_at"),
        config_version=_payload_string(payload, "config_version"),
        row_count=_payload_decimal(payload, "row_count"),
        stale_authority_count=_payload_decimal(
            payload,
            "stale_authority_count",
        ),
        contradiction_pressure_count=_payload_decimal(
            payload,
            "contradiction_pressure_count",
        ),
        rule_ambiguity_count=_payload_decimal(payload, "rule_ambiguity_count"),
        source_availability_gap_count=_payload_decimal(
            payload,
            "source_availability_gap_count",
        ),
        reviewer_coverage_gap_count=_payload_decimal(
            payload,
            "reviewer_coverage_gap_count",
        ),
        deadline_proximity_count=_payload_decimal(
            payload,
            "deadline_proximity_count",
        ),
        pass_count=_payload_decimal(payload, "pass_count"),
        watch_count=_payload_decimal(payload, "watch_count"),
        block_count=_payload_decimal(payload, "block_count"),
        average_recheck_priority_score=_payload_decimal(
            payload,
            "average_recheck_priority_score",
        ),
        max_recheck_priority_score=_payload_decimal(
            payload,
            "max_recheck_priority_score",
        ),
        status=_payload_string(payload, "status"),
        rows=rows,
        reason_codes=_payload_reason_codes(payload, "reason_codes"),
        derived_validation_digest=_payload_string(
            payload,
            "derived_validation_digest",
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _row_from_payload(
    payload: dict[str, Any],
) -> ResearchSourceResolutionAuthorityRecheckBacklogRow:
    return ResearchSourceResolutionAuthorityRecheckBacklogRow(
        review_bucket=_payload_string(payload, "review_bucket"),
        authority_bucket=_payload_string(payload, "authority_bucket"),
        authority_age_seconds=_payload_decimal(payload, "authority_age_seconds"),
        authority_freshness_score=_payload_decimal(
            payload,
            "authority_freshness_score",
        ),
        contradiction_pressure_score=_payload_decimal(
            payload,
            "contradiction_pressure_score",
        ),
        rule_ambiguity_score=_payload_decimal(payload, "rule_ambiguity_score"),
        source_availability_score=_payload_decimal(
            payload,
            "source_availability_score",
        ),
        source_unavailability_score=_payload_decimal(
            payload,
            "source_unavailability_score",
        ),
        reviewer_coverage_score=_payload_decimal(
            payload,
            "reviewer_coverage_score",
        ),
        reviewer_coverage_gap_score=_payload_decimal(
            payload,
            "reviewer_coverage_gap_score",
        ),
        deadline_proximity_score=_payload_decimal(
            payload,
            "deadline_proximity_score",
        ),
        recheck_priority_score=_payload_decimal(
            payload,
            "recheck_priority_score",
        ),
        status=_payload_string(payload, "status"),
        reason_codes=_payload_reason_codes(payload, "reason_codes"),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _json_ready(value: Any) -> Any:
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("Decimal subclasses are not supported")
        return _quantize(value).to_eng_string()
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported JSON payload value {type(value).__name__}")


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize(raw)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must remain positive after quantization")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(raw)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_raw_decimal(field_name, value)
    if raw < _ZERO or raw > _ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(raw)


def _require_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_raw_decimal(field_name, value))


def _require_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative int")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        normalized = value.quantize(_QUANT)
    if normalized == _ZERO:
        return _ZERO
    return normalized


def _clamp_ratio(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _ZERO
    if value > _ONE:
        return _ONE
    return _quantize(value)


def _ratio_complement(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        complement = _ONE - value
    return _clamp_ratio(complement)


def _age_seconds(later: datetime, earlier: datetime) -> Decimal:
    return _seconds_between(later, earlier)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(_DECIMAL_CONTEXT):
        seconds = Decimal(delta.days * 86400 + delta.seconds)
        microseconds = Decimal(delta.microseconds) / Decimal("1000000")
        total_seconds = seconds + microseconds
    return _quantize(total_seconds)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _optional_as_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_nonempty_text(field_name: str, value: object) -> None:
    if type(value) is not str or value.strip() == "":
        raise ValueError(f"{field_name} must be nonempty text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError(f"{field_name} must be a sequence")
    normalized: list[str] = []
    seen: set[str] = set()
    for reason_code in reason_codes:
        if type(reason_code) is not str or not _REASON_CODE_RE.fullmatch(reason_code):
            raise ValueError(f"{field_name} must contain canonical reason codes")
        _reject_unsafe_public_string(field_name, reason_code)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _require_no_extra_dataclass_attrs(label, value)
        for field in fields(value):
            field_value = getattr(value, field.name)
            _reject_unsafe_public_string(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(f"{label}.{field.name}", field_value)
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{label} must not contain raw mappings")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_unsafe_public_string(f"{label}.{key}", key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (tuple, list)):
        if not allow_json_containers:
            for item in value:
                _reject_unsafe_public_payload(label, item)
            return
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if isinstance(value, str):
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, (Decimal, datetime, bool)) or value is None:
        return
    raise ValueError(f"{label} contains unsupported public value")


def _reject_unsafe_public_string(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains unsafe public surface")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_RESOLUTION_AUTHORITY_RECHECK_BACKLOG_REPORT_CONFIG_VERSION",
    "ResearchSourceResolutionAuthorityRecheckBacklogConfig",
    "ResearchSourceResolutionAuthorityRecheckBacklogInput",
    "ResearchSourceResolutionAuthorityRecheckBacklogReport",
    "ResearchSourceResolutionAuthorityRecheckBacklogRow",
    "build_research_source_resolution_authority_recheck_backlog_report",
    "research_source_resolution_authority_recheck_backlog_report_payload",
)
