"""Pure report-only team claim authority memory floor reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-strategy-team-claim-authority-memory-floor-report-v0"
)

TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_INPUTS_REASON = "no_team_claim_authority_memory_floor_inputs"
PASS_REASON = "team_claim_authority_memory_floor_pass"
WATCH_REASON = "team_claim_authority_memory_floor_watch"
BLOCK_REASON = "team_claim_authority_memory_floor_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    BLOCK_REASON,
    "team_authority_score_block",
    "claim_memory_score_block",
    "memory_age_block",
    "cross_team_support_count_block",
    "contradiction_pressure_block",
    WATCH_REASON,
    "team_authority_score_watch",
    "claim_memory_score_watch",
    "memory_age_watch",
    "cross_team_support_count_watch",
    "contradiction_pressure_watch",
    PASS_REASON,
)

STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_DECIMAL_RE = re.compile(r"^-?(?:0|[1-9][0-9]*)\.[0-9]{6}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_",
    "candidate",
    "market",
    "source",
    "url",
    "text",
    "dsn",
    "postgres://",
    "table",
    "token",
    "private_",
    "secret",
    "://",
)

CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "min_pass_team_authority_score",
    "min_watch_team_authority_score",
    "min_pass_claim_memory_score",
    "min_watch_claim_memory_score",
    "max_pass_memory_age_seconds",
    "max_watch_memory_age_seconds",
    "min_pass_cross_team_support_count",
    "min_watch_cross_team_support_count",
    "max_pass_contradiction_pressure",
    "max_watch_contradiction_pressure",
    "team_authority_weight",
    "claim_memory_weight",
    "freshness_weight",
    "support_weight",
    "contradiction_relief_weight",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_authority_memory_floor_score",
    "min_team_authority_score",
    "min_claim_memory_score",
    "max_memory_age_seconds",
    "max_contradiction_pressure",
    "status",
    "rows",
    "reason_code_counts",
    "reason_codes",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_FIELDS = (
    "row_label",
    "public_team_bucket",
    "public_claim_bucket",
    "team_authority_score",
    "claim_memory_score",
    "memory_age_seconds",
    "memory_freshness_score",
    "cross_team_support_count",
    "support_score",
    "contradiction_pressure",
    "authority_memory_floor_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
REASON_COUNT_PAYLOAD_FIELDS = (
    "reason_code",
    "count",
    "row_ratio",
    "paper_only",
    "report_only",
    "readonly",
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION",
    "TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_STATUSES",
    "ResearchStrategyTeamClaimAuthorityMemoryFloorConfig",
    "ResearchStrategyTeamClaimAuthorityMemoryFloorInput",
    "ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount",
    "ResearchStrategyTeamClaimAuthorityMemoryFloorReport",
    "ResearchStrategyTeamClaimAuthorityMemoryFloorRow",
    "build_research_strategy_team_claim_authority_memory_floor_report",
    "research_strategy_team_claim_authority_memory_floor_report_digest",
    "research_strategy_team_claim_authority_memory_floor_report_payload",
    "validate_research_strategy_team_claim_authority_memory_floor_report_payload",
)


@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamClaimAuthorityMemoryFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION
    )
    min_pass_team_authority_score: Decimal = Decimal("0.800000")
    min_watch_team_authority_score: Decimal = Decimal("0.550000")
    min_pass_claim_memory_score: Decimal = Decimal("0.750000")
    min_watch_claim_memory_score: Decimal = Decimal("0.500000")
    max_pass_memory_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("259200.000000")
    min_pass_cross_team_support_count: Decimal = Decimal("2.000000")
    min_watch_cross_team_support_count: Decimal = Decimal("1.000000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.150000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.350000")
    team_authority_weight: Decimal = Decimal("0.300000")
    claim_memory_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.150000")
    support_weight: Decimal = Decimal("0.150000")
    contradiction_relief_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamClaimAuthorityMemoryFloorConfig:
            raise TypeError(
                "ResearchStrategyTeamClaimAuthorityMemoryFloorConfig "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_team_authority_score",
            "min_watch_team_authority_score",
            "min_pass_claim_memory_score",
            "min_watch_claim_memory_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "team_authority_weight",
            "claim_memory_weight",
            "freshness_weight",
            "support_weight",
            "contradiction_relief_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_amount(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_cross_team_support_count",
            "min_watch_cross_team_support_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count(field_name, getattr(self, field_name)),
            )
        if self.min_watch_team_authority_score > self.min_pass_team_authority_score:
            raise ValueError(
                "team authority watch threshold must not exceed pass threshold",
            )
        if self.min_watch_claim_memory_score > self.min_pass_claim_memory_score:
            raise ValueError(
                "claim memory watch threshold must not exceed pass threshold",
            )
        if self.max_pass_memory_age_seconds > self.max_watch_memory_age_seconds:
            raise ValueError("memory age pass threshold must not exceed watch threshold")
        if (
            self.min_watch_cross_team_support_count
            > self.min_pass_cross_team_support_count
        ):
            raise ValueError("support watch threshold must not exceed pass threshold")
        if self.max_pass_contradiction_pressure > self.max_watch_contradiction_pressure:
            raise ValueError(
                "contradiction pressure pass threshold must not exceed watch threshold",
            )
        with localcontext(DECIMAL_CONTEXT):
            weight_sum = _quantize(
                self.team_authority_weight
                + self.claim_memory_weight
                + self.freshness_weight
                + self.support_weight
                + self.contradiction_relief_weight,
            )
        if weight_sum != ONE:
            raise ValueError("floor score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamClaimAuthorityMemoryFloorInput:
    private_subject_ref: str
    private_evidence_ref: str
    private_memory_ref: str
    public_team_bucket: str
    public_claim_bucket: str
    team_authority_score: Decimal
    claim_memory_score: Decimal
    memory_age_seconds: Decimal
    cross_team_support_count: Decimal
    contradiction_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamClaimAuthorityMemoryFloorInput:
            raise TypeError(
                "ResearchStrategyTeamClaimAuthorityMemoryFloorInput "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamClaimAuthorityMemoryFloorInput,
            "input",
        )
        for field_name in (
            "private_subject_ref",
            "private_evidence_ref",
            "private_memory_ref",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        for field_name in ("public_team_bucket", "public_claim_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "team_authority_score",
            "claim_memory_score",
            "contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_nonnegative_amount(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "cross_team_support_count",
            _normalize_nonnegative_count(
                "cross_team_support_count",
                self.cross_team_support_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamClaimAuthorityMemoryFloorRow:
    row_label: str
    public_team_bucket: str
    public_claim_bucket: str
    team_authority_score: Decimal
    claim_memory_score: Decimal
    memory_age_seconds: Decimal
    memory_freshness_score: Decimal
    cross_team_support_count: Decimal
    support_score: Decimal
    contradiction_pressure: Decimal
    authority_memory_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamClaimAuthorityMemoryFloorRow:
            raise TypeError(
                "ResearchStrategyTeamClaimAuthorityMemoryFloorRow "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyTeamClaimAuthorityMemoryFloorRow, "row")
        _require_public_identifier("row_label", self.row_label)
        if not self.row_label.startswith(
            "redacted-team-claim-authority-memory-floor-",
        ):
            raise ValueError("row_label must be redacted")
        for field_name in ("public_team_bucket", "public_claim_bucket"):
            _require_public_identifier(field_name, getattr(self, field_name))
            _reject_unsafe_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "team_authority_score",
            "claim_memory_score",
            "memory_freshness_score",
            "support_score",
            "contradiction_pressure",
            "authority_memory_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_nonnegative_amount(
                "memory_age_seconds",
                self.memory_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "cross_team_support_count",
            _normalize_nonnegative_count(
                "cross_team_support_count",
                self.cross_team_support_count,
            ),
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


@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount:
            raise TypeError(
                "ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategyTeamClaimAuthorityMemoryFloorReport:
    generated_at: datetime
    config_version: str
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_memory_floor_score: Decimal | None
    min_team_authority_score: Decimal
    min_claim_memory_score: Decimal
    max_memory_age_seconds: Decimal
    max_contradiction_pressure: Decimal
    status: str
    rows: tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategyTeamClaimAuthorityMemoryFloorReport:
            raise TypeError(
                "ResearchStrategyTeamClaimAuthorityMemoryFloorReport "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyTeamClaimAuthorityMemoryFloorReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(self, "config", _revalidated_config(self.config))
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_authority_memory_floor_score",
            _normalize_optional_probability(
                "average_authority_memory_floor_score",
                self.average_authority_memory_floor_score,
            ),
        )
        for field_name in (
            "min_team_authority_score",
            "min_claim_memory_score",
            "max_contradiction_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_memory_age_seconds",
            _normalize_nonnegative_amount(
                "max_memory_age_seconds",
                self.max_memory_age_seconds,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_team_claim_authority_memory_floor_report_payload(self)


def build_research_strategy_team_claim_authority_memory_floor_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
    generated_at: datetime,
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorReport:
    if type(config) is not ResearchStrategyTeamClaimAuthorityMemoryFloorConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamClaimAuthorityMemoryFloorConfig",
        )
    config = _revalidated_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in input_items),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategyTeamClaimAuthorityMemoryFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_authority_memory_floor_score=_average_row_value(
            rows,
            "authority_memory_floor_score",
        ),
        min_team_authority_score=_minimum_row_value(rows, "team_authority_score"),
        min_claim_memory_score=_minimum_row_value(rows, "claim_memory_score"),
        max_memory_age_seconds=_maximum_row_value(rows, "memory_age_seconds"),
        max_contradiction_pressure=_maximum_row_value(rows, "contradiction_pressure"),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_team_claim_authority_memory_floor_report_payload(
    report: ResearchStrategyTeamClaimAuthorityMemoryFloorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyTeamClaimAuthorityMemoryFloorReport:
        _require_hard_flags("report", report)
        _validate_report_consistency(report)
        expected_digest = _report_digest(report)
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
    elif type(report) is dict:
        payload = report
    else:
        raise ValueError(
            "report must be a ResearchStrategyTeamClaimAuthorityMemoryFloorReport",
        )
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _reject_raw_public_numbers("payload", payload)
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_payload_digest(payload)
    _report_from_payload(payload)
    return payload


def research_strategy_team_claim_authority_memory_floor_report_digest(
    report: ResearchStrategyTeamClaimAuthorityMemoryFloorReport,
) -> str:
    payload = research_strategy_team_claim_authority_memory_floor_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    return digest


def validate_research_strategy_team_claim_authority_memory_floor_report_payload(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        research_strategy_team_claim_authority_memory_floor_report_payload(payload)
    except (TypeError, ValueError):
        return False
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


def _revalidated_config(
    config: object,
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorConfig:
    if type(config) is not ResearchStrategyTeamClaimAuthorityMemoryFloorConfig:
        raise ValueError(
            "config must be a ResearchStrategyTeamClaimAuthorityMemoryFloorConfig",
        )
    try:
        canonical = ResearchStrategyTeamClaimAuthorityMemoryFloorConfig(
            config_version=config.config_version,
            min_pass_team_authority_score=config.min_pass_team_authority_score,
            min_watch_team_authority_score=config.min_watch_team_authority_score,
            min_pass_claim_memory_score=config.min_pass_claim_memory_score,
            min_watch_claim_memory_score=config.min_watch_claim_memory_score,
            max_pass_memory_age_seconds=config.max_pass_memory_age_seconds,
            max_watch_memory_age_seconds=config.max_watch_memory_age_seconds,
            min_pass_cross_team_support_count=config.min_pass_cross_team_support_count,
            min_watch_cross_team_support_count=config.min_watch_cross_team_support_count,
            max_pass_contradiction_pressure=config.max_pass_contradiction_pressure,
            max_watch_contradiction_pressure=config.max_watch_contradiction_pressure,
            team_authority_weight=config.team_authority_weight,
            claim_memory_weight=config.claim_memory_weight,
            freshness_weight=config.freshness_weight,
            support_weight=config.support_weight,
            contradiction_relief_weight=config.contradiction_relief_weight,
            paper_only=config.paper_only,
            report_only=config.report_only,
            readonly=config.readonly,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("config must be revalidated") from exc
    if config != canonical:
        raise ValueError("config must be constructor-normalized")
    return canonical


def _revalidated_input(
    item: object,
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorInput:
    if type(item) is not ResearchStrategyTeamClaimAuthorityMemoryFloorInput:
        raise ValueError(
            "inputs must contain ResearchStrategyTeamClaimAuthorityMemoryFloorInput",
        )
    try:
        canonical = ResearchStrategyTeamClaimAuthorityMemoryFloorInput(
            private_subject_ref=item.private_subject_ref,
            private_evidence_ref=item.private_evidence_ref,
            private_memory_ref=item.private_memory_ref,
            public_team_bucket=item.public_team_bucket,
            public_claim_bucket=item.public_claim_bucket,
            team_authority_score=item.team_authority_score,
            claim_memory_score=item.claim_memory_score,
            memory_age_seconds=item.memory_age_seconds,
            cross_team_support_count=item.cross_team_support_count,
            contradiction_pressure=item.contradiction_pressure,
            reason_codes=item.reason_codes,
            paper_only=item.paper_only,
            report_only=item.report_only,
            readonly=item.readonly,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("input must be revalidated") from exc
    if item != canonical:
        raise ValueError("input must be constructor-normalized")
    return canonical


def _revalidated_row(
    row: ResearchStrategyTeamClaimAuthorityMemoryFloorRow,
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorRow:
    if type(row) is not ResearchStrategyTeamClaimAuthorityMemoryFloorRow:
        raise ValueError(
            "rows must contain ResearchStrategyTeamClaimAuthorityMemoryFloorRow",
        )
    canonical = ResearchStrategyTeamClaimAuthorityMemoryFloorRow(
        row_label=row.row_label,
        public_team_bucket=row.public_team_bucket,
        public_claim_bucket=row.public_claim_bucket,
        team_authority_score=row.team_authority_score,
        claim_memory_score=row.claim_memory_score,
        memory_age_seconds=row.memory_age_seconds,
        memory_freshness_score=row.memory_freshness_score,
        cross_team_support_count=row.cross_team_support_count,
        support_score=row.support_score,
        contradiction_pressure=row.contradiction_pressure,
        authority_memory_floor_score=row.authority_memory_floor_score,
        status=row.status,
        reason_codes=row.reason_codes,
        paper_only=row.paper_only,
        report_only=row.report_only,
        readonly=row.readonly,
    )
    if row != canonical:
        raise ValueError("row must be constructor-normalized")
    return canonical


def _row_from_input(
    item: ResearchStrategyTeamClaimAuthorityMemoryFloorInput,
    *,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorRow:
    freshness_score = _freshness_score(item.memory_age_seconds, config)
    support_score = _support_score(item.cross_team_support_count, config)
    floor_score = _authority_memory_floor_score(
        team_authority_score=item.team_authority_score,
        claim_memory_score=item.claim_memory_score,
        memory_freshness_score=freshness_score,
        support_score=support_score,
        contradiction_pressure=item.contradiction_pressure,
        config=config,
    )
    status = _row_status(item, config=config)
    return ResearchStrategyTeamClaimAuthorityMemoryFloorRow(
        row_label=(
            "redacted-team-claim-authority-memory-floor-"
            f"{_private_ref_digest(_private_ref_material(item))[:16]}"
        ),
        public_team_bucket=item.public_team_bucket,
        public_claim_bucket=item.public_claim_bucket,
        team_authority_score=item.team_authority_score,
        claim_memory_score=item.claim_memory_score,
        memory_age_seconds=item.memory_age_seconds,
        memory_freshness_score=freshness_score,
        cross_team_support_count=item.cross_team_support_count,
        support_score=support_score,
        contradiction_pressure=item.contradiction_pressure,
        authority_memory_floor_score=floor_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _freshness_score(
    memory_age_seconds: Decimal,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = ONE - (memory_age_seconds / config.max_watch_memory_age_seconds)
    return _clamp_probability(score)


def _support_score(
    cross_team_support_count: Decimal,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = cross_team_support_count / config.min_pass_cross_team_support_count
    return _clamp_probability(score)


def _authority_memory_floor_score(
    *,
    team_authority_score: Decimal,
    claim_memory_score: Decimal,
    memory_freshness_score: Decimal,
    support_score: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            team_authority_score * config.team_authority_weight
            + claim_memory_score * config.claim_memory_weight
            + memory_freshness_score * config.freshness_weight
            + support_score * config.support_weight
            + (ONE - contradiction_pressure) * config.contradiction_relief_weight
        )
    return _quantize(value)


def _row_status(
    item: ResearchStrategyTeamClaimAuthorityMemoryFloorInput,
    *,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> str:
    return _status_for_values(
        team_authority_score=item.team_authority_score,
        claim_memory_score=item.claim_memory_score,
        memory_age_seconds=item.memory_age_seconds,
        cross_team_support_count=item.cross_team_support_count,
        contradiction_pressure=item.contradiction_pressure,
        config=config,
    )


def _status_for_values(
    *,
    team_authority_score: Decimal,
    claim_memory_score: Decimal,
    memory_age_seconds: Decimal,
    cross_team_support_count: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> str:
    if (
        team_authority_score < config.min_watch_team_authority_score
        or claim_memory_score < config.min_watch_claim_memory_score
        or memory_age_seconds > config.max_watch_memory_age_seconds
        or cross_team_support_count < config.min_watch_cross_team_support_count
        or contradiction_pressure > config.max_watch_contradiction_pressure
    ):
        return "block"
    if (
        team_authority_score < config.min_pass_team_authority_score
        or claim_memory_score < config.min_pass_claim_memory_score
        or memory_age_seconds > config.max_pass_memory_age_seconds
        or cross_team_support_count < config.min_pass_cross_team_support_count
        or contradiction_pressure > config.max_pass_contradiction_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategyTeamClaimAuthorityMemoryFloorInput,
    *,
    status: str,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> tuple[str, ...]:
    return _row_reason_codes_for_values(
        team_authority_score=item.team_authority_score,
        claim_memory_score=item.claim_memory_score,
        memory_age_seconds=item.memory_age_seconds,
        cross_team_support_count=item.cross_team_support_count,
        contradiction_pressure=item.contradiction_pressure,
        input_reason_codes=item.reason_codes,
        status=status,
        config=config,
    )


def _row_reason_codes_for_values(
    *,
    team_authority_score: Decimal,
    claim_memory_score: Decimal,
    memory_age_seconds: Decimal,
    cross_team_support_count: Decimal,
    contradiction_pressure: Decimal,
    input_reason_codes: tuple[str, ...],
    status: str,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> tuple[str, ...]:
    codes = {f"team_claim_authority_memory_floor_{status}"}
    if status == "block":
        if team_authority_score < config.min_watch_team_authority_score:
            codes.add("team_authority_score_block")
        if claim_memory_score < config.min_watch_claim_memory_score:
            codes.add("claim_memory_score_block")
        if memory_age_seconds > config.max_watch_memory_age_seconds:
            codes.add("memory_age_block")
        if cross_team_support_count < config.min_watch_cross_team_support_count:
            codes.add("cross_team_support_count_block")
        if contradiction_pressure > config.max_watch_contradiction_pressure:
            codes.add("contradiction_pressure_block")
    elif status == "watch":
        if team_authority_score < config.min_pass_team_authority_score:
            codes.add("team_authority_score_watch")
        if claim_memory_score < config.min_pass_claim_memory_score:
            codes.add("claim_memory_score_watch")
        if memory_age_seconds > config.max_pass_memory_age_seconds:
            codes.add("memory_age_watch")
        if cross_team_support_count < config.min_pass_cross_team_support_count:
            codes.add("cross_team_support_count_watch")
        if contradiction_pressure > config.max_pass_contradiction_pressure:
            codes.add("contradiction_pressure_watch")
    codes.update(f"input_{code}" for code in input_reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _summary_reason_codes(
    rows: tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    codes = {
        code
        for row in rows
        for code in row.reason_codes
        if not code.startswith("input_")
    }
    if any(row.status != "pass" for row in rows):
        codes.discard(PASS_REASON)
    if not codes:
        codes.add(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts = Counter(
        code
        for row in rows
        for code in row.reason_codes
        if code in reason_codes
    )
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount(
            reason_code=code,
            count=_decimal_count(counts[code]),
            row_ratio=_quantize(_decimal_count(counts[code]) / row_count),
        )
        for code in reason_codes
    )


def _summary_status(
    rows: tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_row_value(
    rows: tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        value = sum(getattr(row, field_name) for row in rows) / _decimal_count(len(rows))
    return _quantize(value)


def _minimum_row_value(
    rows: tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...],
    field_name: str,
) -> Decimal:
    return min((getattr(row, field_name) for row in rows), default=ZERO)


def _maximum_row_value(
    rows: tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...],
    field_name: str,
) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO)


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorInput, ...]:
    items = tuple(inputs)
    return tuple(_revalidated_input(item) for item in items)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchStrategyTeamClaimAuthorityMemoryFloorRow, "row")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount",
            )
    normalized = tuple(sorted(counts, key=lambda count: _reason_sort_key(count.reason_code)))
    if tuple(count.reason_code for count in normalized) != tuple(
        count.reason_code for count in counts
    ):
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _validate_row_consistency(
    row: ResearchStrategyTeamClaimAuthorityMemoryFloorRow,
) -> None:
    expected_status_code = f"team_claim_authority_memory_floor_{row.status}"
    if not row.reason_codes or row.reason_codes[0] != expected_status_code:
        raise ValueError("reason_codes must start with the row status reason")
    if row.status == "pass" and any(
        code.endswith(("_watch", "_block")) for code in row.reason_codes
    ):
        raise ValueError("status pass rows must not include watch or block reasons")


def _validate_report_consistency(
    report: ResearchStrategyTeamClaimAuthorityMemoryFloorReport,
) -> None:
    if _as_utc("generated_at", report.generated_at) != report.generated_at:
        raise ValueError("generated_at must be canonical UTC")
    config = _revalidated_config(report.config)
    if report.config_version != config.config_version:
        raise ValueError("config_version must match config")
    for row in report.rows:
        _revalidated_row(row)
        _validate_row_against_config(row, config=config)
    expected_rows = tuple(sorted(report.rows, key=_row_sort_key))
    if report.rows != expected_rows:
        raise ValueError("rows must be sorted deterministically")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_authority_memory_floor_score != _average_row_value(
        report.rows,
        "authority_memory_floor_score",
    ):
        raise ValueError("average_authority_memory_floor_score must match rows")
    if report.min_team_authority_score != _minimum_row_value(
        report.rows,
        "team_authority_score",
    ):
        raise ValueError("min_team_authority_score must match rows")
    if report.min_claim_memory_score != _minimum_row_value(
        report.rows,
        "claim_memory_score",
    ):
        raise ValueError("min_claim_memory_score must match rows")
    if report.max_memory_age_seconds != _maximum_row_value(
        report.rows,
        "memory_age_seconds",
    ):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.max_contradiction_pressure != _maximum_row_value(
        report.rows,
        "contradiction_pressure",
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    expected_counts = _reason_code_counts(report.rows, report.reason_codes)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")


def _validate_row_against_config(
    row: ResearchStrategyTeamClaimAuthorityMemoryFloorRow,
    *,
    config: ResearchStrategyTeamClaimAuthorityMemoryFloorConfig,
) -> None:
    expected_freshness_score = _freshness_score(row.memory_age_seconds, config)
    if row.memory_freshness_score != expected_freshness_score:
        raise ValueError("memory_freshness_score must match row inputs and config")
    expected_support_score = _support_score(row.cross_team_support_count, config)
    if row.support_score != expected_support_score:
        raise ValueError("support_score must match row inputs and config")
    expected_floor_score = _authority_memory_floor_score(
        team_authority_score=row.team_authority_score,
        claim_memory_score=row.claim_memory_score,
        memory_freshness_score=row.memory_freshness_score,
        support_score=row.support_score,
        contradiction_pressure=row.contradiction_pressure,
        config=config,
    )
    if row.authority_memory_floor_score != expected_floor_score:
        raise ValueError("authority_memory_floor_score must match row inputs and config")
    expected_status = _status_for_values(
        team_authority_score=row.team_authority_score,
        claim_memory_score=row.claim_memory_score,
        memory_age_seconds=row.memory_age_seconds,
        cross_team_support_count=row.cross_team_support_count,
        contradiction_pressure=row.contradiction_pressure,
        config=config,
    )
    if row.status != expected_status:
        raise ValueError("status must match row inputs and config")
    input_reason_codes = tuple(
        code.removeprefix("input_")
        for code in row.reason_codes
        if code.startswith("input_")
    )
    expected_reason_codes = _row_reason_codes_for_values(
        team_authority_score=row.team_authority_score,
        claim_memory_score=row.claim_memory_score,
        memory_age_seconds=row.memory_age_seconds,
        cross_team_support_count=row.cross_team_support_count,
        contradiction_pressure=row.contradiction_pressure,
        input_reason_codes=input_reason_codes,
        status=expected_status,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs and config")


def _row_sort_key(row: ResearchStrategyTeamClaimAuthorityMemoryFloorRow) -> tuple[str, ...]:
    return (row.public_team_bucket, row.public_claim_bucket, row.row_label)


def _private_ref_material(
    item: ResearchStrategyTeamClaimAuthorityMemoryFloorInput,
) -> str:
    return "\x1f".join(
        (
            item.private_subject_ref,
            item.private_evidence_ref,
            item.private_memory_ref,
        ),
    )


def _private_ref_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _report_digest(report: ResearchStrategyTeamClaimAuthorityMemoryFloorReport) -> str:
    payload = _payload_value(report, include_digest=False)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(
        unsigned,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    if sha256(encoded.encode("utf-8")).hexdigest() != digest:
        raise ValueError("derived_validation_digest must match payload")


def _report_from_payload(
    payload: dict[str, Any],
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorReport:
    values = _require_exact_payload_fields(
        "report payload",
        payload,
        REPORT_PAYLOAD_FIELDS,
    )
    rows_value = _require_payload_list("rows", values["rows"])
    reason_count_value = _require_payload_list(
        "reason_code_counts",
        values["reason_code_counts"],
    )
    reason_codes_value = _require_payload_list("reason_codes", values["reason_codes"])
    rows = tuple(
        _row_from_payload(item, index=index)
        for index, item in enumerate(rows_value)
    )
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    reason_code_counts = tuple(
        _reason_code_count_from_payload(item, index=index)
        for index, item in enumerate(reason_count_value)
    )
    return ResearchStrategyTeamClaimAuthorityMemoryFloorReport(
        generated_at=_payload_datetime("generated_at", values["generated_at"]),
        config_version=_payload_string("config_version", values["config_version"]),
        config=_config_from_payload(values["config"]),
        row_count=_payload_decimal("row_count", values["row_count"]),
        pass_count=_payload_decimal("pass_count", values["pass_count"]),
        watch_count=_payload_decimal("watch_count", values["watch_count"]),
        block_count=_payload_decimal("block_count", values["block_count"]),
        average_authority_memory_floor_score=_payload_optional_decimal(
            "average_authority_memory_floor_score",
            values["average_authority_memory_floor_score"],
        ),
        min_team_authority_score=_payload_decimal(
            "min_team_authority_score",
            values["min_team_authority_score"],
        ),
        min_claim_memory_score=_payload_decimal(
            "min_claim_memory_score",
            values["min_claim_memory_score"],
        ),
        max_memory_age_seconds=_payload_decimal(
            "max_memory_age_seconds",
            values["max_memory_age_seconds"],
        ),
        max_contradiction_pressure=_payload_decimal(
            "max_contradiction_pressure",
            values["max_contradiction_pressure"],
        ),
        status=_payload_string("status", values["status"]),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_payload_reason_codes("reason_codes", reason_codes_value),
        derived_validation_digest=_payload_digest(
            "derived_validation_digest",
            values["derived_validation_digest"],
        ),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _config_from_payload(
    value: object,
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorConfig:
    values = _require_exact_payload_fields("config payload", value, CONFIG_PAYLOAD_FIELDS)
    return ResearchStrategyTeamClaimAuthorityMemoryFloorConfig(
        config_version=_payload_string("config_version", values["config_version"]),
        min_pass_team_authority_score=_payload_decimal(
            "min_pass_team_authority_score",
            values["min_pass_team_authority_score"],
        ),
        min_watch_team_authority_score=_payload_decimal(
            "min_watch_team_authority_score",
            values["min_watch_team_authority_score"],
        ),
        min_pass_claim_memory_score=_payload_decimal(
            "min_pass_claim_memory_score",
            values["min_pass_claim_memory_score"],
        ),
        min_watch_claim_memory_score=_payload_decimal(
            "min_watch_claim_memory_score",
            values["min_watch_claim_memory_score"],
        ),
        max_pass_memory_age_seconds=_payload_decimal(
            "max_pass_memory_age_seconds",
            values["max_pass_memory_age_seconds"],
        ),
        max_watch_memory_age_seconds=_payload_decimal(
            "max_watch_memory_age_seconds",
            values["max_watch_memory_age_seconds"],
        ),
        min_pass_cross_team_support_count=_payload_decimal(
            "min_pass_cross_team_support_count",
            values["min_pass_cross_team_support_count"],
        ),
        min_watch_cross_team_support_count=_payload_decimal(
            "min_watch_cross_team_support_count",
            values["min_watch_cross_team_support_count"],
        ),
        max_pass_contradiction_pressure=_payload_decimal(
            "max_pass_contradiction_pressure",
            values["max_pass_contradiction_pressure"],
        ),
        max_watch_contradiction_pressure=_payload_decimal(
            "max_watch_contradiction_pressure",
            values["max_watch_contradiction_pressure"],
        ),
        team_authority_weight=_payload_decimal(
            "team_authority_weight",
            values["team_authority_weight"],
        ),
        claim_memory_weight=_payload_decimal(
            "claim_memory_weight",
            values["claim_memory_weight"],
        ),
        freshness_weight=_payload_decimal("freshness_weight", values["freshness_weight"]),
        support_weight=_payload_decimal("support_weight", values["support_weight"]),
        contradiction_relief_weight=_payload_decimal(
            "contradiction_relief_weight",
            values["contradiction_relief_weight"],
        ),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _row_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorRow:
    values = _require_exact_payload_fields(
        f"rows[{index}]",
        value,
        ROW_PAYLOAD_FIELDS,
    )
    reason_codes_value = _require_payload_list(
        f"rows[{index}].reason_codes",
        values["reason_codes"],
    )
    return ResearchStrategyTeamClaimAuthorityMemoryFloorRow(
        row_label=_payload_string("row_label", values["row_label"]),
        public_team_bucket=_payload_string(
            "public_team_bucket",
            values["public_team_bucket"],
        ),
        public_claim_bucket=_payload_string(
            "public_claim_bucket",
            values["public_claim_bucket"],
        ),
        team_authority_score=_payload_decimal(
            "team_authority_score",
            values["team_authority_score"],
        ),
        claim_memory_score=_payload_decimal(
            "claim_memory_score",
            values["claim_memory_score"],
        ),
        memory_age_seconds=_payload_decimal(
            "memory_age_seconds",
            values["memory_age_seconds"],
        ),
        memory_freshness_score=_payload_decimal(
            "memory_freshness_score",
            values["memory_freshness_score"],
        ),
        cross_team_support_count=_payload_decimal(
            "cross_team_support_count",
            values["cross_team_support_count"],
        ),
        support_score=_payload_decimal("support_score", values["support_score"]),
        contradiction_pressure=_payload_decimal(
            "contradiction_pressure",
            values["contradiction_pressure"],
        ),
        authority_memory_floor_score=_payload_decimal(
            "authority_memory_floor_score",
            values["authority_memory_floor_score"],
        ),
        status=_payload_string("status", values["status"]),
        reason_codes=_payload_reason_codes(
            f"rows[{index}].reason_codes",
            reason_codes_value,
        ),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _reason_code_count_from_payload(
    value: object,
    *,
    index: int,
) -> ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount:
    values = _require_exact_payload_fields(
        f"reason_code_counts[{index}]",
        value,
        REASON_COUNT_PAYLOAD_FIELDS,
    )
    return ResearchStrategyTeamClaimAuthorityMemoryFloorReasonCodeCount(
        reason_code=_payload_string("reason_code", values["reason_code"]),
        count=_payload_decimal("count", values["count"]),
        row_ratio=_payload_decimal("row_ratio", values["row_ratio"]),
        paper_only=_payload_true_flag("paper_only", values["paper_only"]),
        report_only=_payload_true_flag("report_only", values["report_only"]),
        readonly=_payload_true_flag("readonly", values["readonly"]),
    )


def _require_exact_payload_fields(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(expected_fields):
        raise ValueError(f"{label} does not match exact schema")
    if tuple(value) != expected_fields:
        raise ValueError(f"{label} does not match canonical schema field sequence")
    return value


def _require_payload_list(label: str, value: object) -> list[object]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a list")
    return value


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _payload_digest(field_name: str, value: object) -> str:
    text = _payload_string(field_name, value)
    _require_digest(field_name, text)
    return text


def _payload_decimal(field_name: str, value: object) -> Decimal:
    text = _payload_string(field_name, value)
    if PUBLIC_DECIMAL_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    parsed = Decimal(text)
    if parsed.is_zero() and parsed.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return parsed


def _payload_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _payload_decimal(field_name, value)


def _payload_datetime(field_name: str, value: object) -> datetime:
    text = _payload_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(text)
        normalized = _as_utc(field_name, parsed)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime") from exc
    if normalized.isoformat() != text:
        raise ValueError(f"{field_name} must be a canonical UTC datetime")
    return normalized


def _payload_reason_codes(field_name: str, value: list[object]) -> tuple[str, ...]:
    if any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must be a list of strings")
    normalized = _normalize_reason_codes(field_name, tuple(value), allow_empty=False)
    if tuple(value) != normalized:
        raise ValueError(f"{field_name} must be deterministic")
    return normalized


def _payload_true_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_value(value: object, *, include_digest: bool = True) -> object:
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, object] = {}
        for field in fields(value):
            if not include_digest and field.name == "derived_validation_digest":
                continue
            payload[field.name] = _payload_value(
                getattr(value, field.name),
                include_digest=include_digest,
            )
        return payload
    if type(value) is tuple:
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if type(value) is list:
        return [_payload_value(item, include_digest=include_digest) for item in value]
    if type(value) is dict:
        return {
            str(key): _payload_value(item, include_digest=include_digest)
            for key, item in value.items()
        }
    raise ValueError(f"unsupported payload value {value!r}")


def _reject_raw_public_numbers(where: str, value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{where} must use Decimal|string public numeric encoding")
    if type(value) is dict:
        for key, item in value.items():
            _reject_raw_public_numbers(f"{where}.{key}", item)
    elif type(value) is list:
        for index, item in enumerate(value):
            _reject_raw_public_numbers(f"{where}[{index}]", item)


def _reject_unsafe_public_payload(
    where: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name.startswith("private_"):
                raise ValueError(f"{where}.{field.name} is unsafe for public payload")
            _reject_unsafe_public_string(f"{where}.{field.name}", field.name)
            _reject_unsafe_public_payload(f"{where}.{field.name}", field_value)
        return
    if type(value) is dict:
        if not allow_json_containers:
            raise ValueError(f"{where} must not be a public dict")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{where} keys must be strings")
            _reject_unsafe_public_string(f"{where}.{key}", key)
            _reject_unsafe_public_payload(
                f"{where}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if type(value) in (tuple, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{where}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(where, value)


def _reject_unsafe_public_string(where: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{where} contains unsafe public payload content")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: set[str] = set()
    for reason in reason_codes:
        _require_reason_code(field_name, reason)
        normalized.add(reason)
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized, key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, int | str]:
    try:
        return (0, REASON_CODE_SEQUENCE.index(reason_code))
    except ValueError:
        return (1, reason_code)


def _require_exact_type(value: object, expected_type: type[object], where: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{where} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty private reference")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must contain reason codes")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in TEAM_CLAIM_AUTHORITY_MEMORY_FLOOR_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_hard_flags(where: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{where}.{field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_positive_amount(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_amount(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_count(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be an integer count")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use signed zero")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _clamp_probability(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    if value > ONE:
        return ONE
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))
