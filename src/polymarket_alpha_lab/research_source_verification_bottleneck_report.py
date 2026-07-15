"""Pure report-only bottleneck report for research source verification."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_VERIFICATION_BOTTLENECK_REPORT_CONFIG_VERSION = (
    "research-source-verification-bottleneck-report-v0"
)

STATUSES = ("pass", "watch", "block")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
HEX_CHARS = frozenset("0123456789abcdef")

AUTHORITY_COVERAGE_BLOCK_REASON = (
    "research_source_verification_authority_coverage_block"
)
FRESHNESS_LAG_BLOCK_REASON = "research_source_verification_freshness_lag_block"
CONTRADICTION_PRESSURE_BLOCK_REASON = (
    "research_source_verification_contradiction_pressure_block"
)
EXTRACTION_CONFIDENCE_BLOCK_REASON = (
    "research_source_verification_extraction_confidence_block"
)
MISSING_CRITICAL_FIELDS_BLOCK_REASON = (
    "research_source_verification_missing_critical_fields_block"
)
REVIEWER_CAPACITY_BLOCK_REASON = (
    "research_source_verification_reviewer_capacity_block"
)
AUTHORITY_COVERAGE_WATCH_REASON = (
    "research_source_verification_authority_coverage_watch"
)
FRESHNESS_LAG_WATCH_REASON = "research_source_verification_freshness_lag_watch"
CONTRADICTION_PRESSURE_WATCH_REASON = (
    "research_source_verification_contradiction_pressure_watch"
)
EXTRACTION_CONFIDENCE_WATCH_REASON = (
    "research_source_verification_extraction_confidence_watch"
)
MISSING_CRITICAL_FIELDS_WATCH_REASON = (
    "research_source_verification_missing_critical_fields_watch"
)
REVIEWER_CAPACITY_WATCH_REASON = (
    "research_source_verification_reviewer_capacity_watch"
)
CLEAR_REASON = "research_source_verification_clear"
EMPTY_REASON = "research_source_verification_empty"

ROW_REASON_SEQUENCE = (
    AUTHORITY_COVERAGE_BLOCK_REASON,
    FRESHNESS_LAG_BLOCK_REASON,
    CONTRADICTION_PRESSURE_BLOCK_REASON,
    EXTRACTION_CONFIDENCE_BLOCK_REASON,
    MISSING_CRITICAL_FIELDS_BLOCK_REASON,
    REVIEWER_CAPACITY_BLOCK_REASON,
    AUTHORITY_COVERAGE_WATCH_REASON,
    FRESHNESS_LAG_WATCH_REASON,
    CONTRADICTION_PRESSURE_WATCH_REASON,
    EXTRACTION_CONFIDENCE_WATCH_REASON,
    MISSING_CRITICAL_FIELDS_WATCH_REASON,
    REVIEWER_CAPACITY_WATCH_REASON,
    CLEAR_REASON,
)
REPORT_REASON_SEQUENCE = (*ROW_REASON_SEQUENCE, EMPTY_REASON)
REASON_SET = frozenset(REPORT_REASON_SEQUENCE)

UNSAFE_PUBLIC_MARKERS = ("://",)
UNSAFE_PUBLIC_TOKENS = frozenset(
    {
        "apikey",
        "candidate",
        "credential",
        "dsn",
        "email",
        "live",
        "order",
        "password",
        "question",
        "secret",
        "slug",
        "table",
        "tipster",
        "token",
        "trade",
        "wallet",
        "whistleblower",
    },
)
UNSAFE_PUBLIC_TOKEN_PAIRS = frozenset(
    {
        ("anonymous", "source"),
        ("api", "key"),
        ("confidential", "source"),
        ("market", "id"),
        ("market", "slug"),
        ("nonpublic", "source"),
        ("private", "key"),
        ("private", "source"),
        ("source", "handle"),
        ("source", "id"),
        ("source", "identity"),
        ("source", "name"),
        ("source", "text"),
        ("source", "url"),
    },
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_VERIFICATION_BOTTLENECK_REPORT_CONFIG_VERSION",
    "ResearchSourceVerificationBottleneckConfig",
    "ResearchSourceVerificationBottleneckInput",
    "ResearchSourceVerificationBottleneckReport",
    "ResearchSourceVerificationBottleneckRow",
    "build_research_source_verification_bottleneck_report",
    "research_source_verification_bottleneck_report_digest",
    "research_source_verification_bottleneck_report_payload",
)

_ROW_PAYLOAD_FIELDS = (
    "bottleneck_rank",
    "domain_label",
    "verification_queue_label",
    "evidence_family_label",
    "status",
    "bottleneck_pressure_score",
    "required_authority_reference_count",
    "covered_authority_reference_count",
    "authority_coverage_ratio",
    "freshness_lag_seconds",
    "contradiction_signal_count",
    "reviewed_claim_count",
    "contradiction_pressure_ratio",
    "extraction_confidence_score",
    "missing_critical_field_count",
    "available_reviewer_capacity_count",
    "reviewer_capacity_gap_count",
    "reviewer_capacity_gap_ratio",
    "observed_at",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)
_CONFIG_PAYLOAD_FIELDS = (
    "config_version",
    "min_pass_authority_coverage_ratio",
    "min_watch_authority_coverage_ratio",
    "max_pass_freshness_lag_seconds",
    "max_watch_freshness_lag_seconds",
    "max_pass_contradiction_pressure_ratio",
    "max_watch_contradiction_pressure_ratio",
    "min_pass_extraction_confidence_score",
    "min_watch_extraction_confidence_score",
    "max_pass_missing_critical_field_count",
    "max_watch_missing_critical_field_count",
    "min_pass_available_reviewer_capacity_count",
    "min_watch_available_reviewer_capacity_count",
    "paper_only",
    "report_only",
    "readonly",
)
_REPORT_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "input_count",
    "bottleneck_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_authority_coverage_ratio",
    "max_freshness_lag_seconds",
    "max_contradiction_pressure_ratio",
    "min_extraction_confidence_score",
    "total_missing_critical_field_count",
    "min_available_reviewer_capacity_count",
    "status",
    "reason_codes",
    "rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchSourceVerificationBottleneckConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_VERIFICATION_BOTTLENECK_REPORT_CONFIG_VERSION
    )
    min_pass_authority_coverage_ratio: Decimal = Decimal("0.900000")
    min_watch_authority_coverage_ratio: Decimal = Decimal("0.700000")
    max_pass_freshness_lag_seconds: Decimal = Decimal("86400.000000")
    max_watch_freshness_lag_seconds: Decimal = Decimal("259200.000000")
    max_pass_contradiction_pressure_ratio: Decimal = Decimal("0.000000")
    max_watch_contradiction_pressure_ratio: Decimal = Decimal("0.250000")
    min_pass_extraction_confidence_score: Decimal = Decimal("0.900000")
    min_watch_extraction_confidence_score: Decimal = Decimal("0.700000")
    max_pass_missing_critical_field_count: Decimal = Decimal("0.000000")
    max_watch_missing_critical_field_count: Decimal = Decimal("2.000000")
    min_pass_available_reviewer_capacity_count: Decimal = Decimal("2.000000")
    min_watch_available_reviewer_capacity_count: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceVerificationBottleneckConfig, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_VERIFICATION_BOTTLENECK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_authority_coverage_ratio",
            "min_watch_authority_coverage_ratio",
            "max_pass_contradiction_pressure_ratio",
            "max_watch_contradiction_pressure_ratio",
            "min_pass_extraction_confidence_score",
            "min_watch_extraction_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_freshness_lag_seconds",
            "max_watch_freshness_lag_seconds",
            "max_pass_missing_critical_field_count",
            "max_watch_missing_critical_field_count",
            "min_pass_available_reviewer_capacity_count",
            "min_watch_available_reviewer_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourceVerificationBottleneckInput(_FinalDataclass):
    domain_label: str
    verification_queue_label: str
    evidence_family_label: str
    required_authority_reference_count: Decimal
    covered_authority_reference_count: Decimal
    freshness_lag_seconds: Decimal
    contradiction_signal_count: Decimal
    reviewed_claim_count: Decimal
    extraction_confidence_score: Decimal
    missing_critical_field_count: Decimal
    available_reviewer_capacity_count: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceVerificationBottleneckInput, "input")
        for field_name in (
            "domain_label",
            "verification_queue_label",
            "evidence_family_label",
        ):
            _require_public_label(field_name, getattr(self, field_name))
        for field_name in (
            "required_authority_reference_count",
            "covered_authority_reference_count",
            "freshness_lag_seconds",
            "contradiction_signal_count",
            "reviewed_claim_count",
            "missing_critical_field_count",
            "available_reviewer_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "extraction_confidence_score",
            _ratio_decimal(
                "extraction_confidence_score",
                self.extraction_confidence_score,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        if self.covered_authority_reference_count > self.required_authority_reference_count:
            raise ValueError(
                "covered_authority_reference_count must be <= "
                "required_authority_reference_count",
            )
        if self.contradiction_signal_count > self.reviewed_claim_count:
            raise ValueError("contradiction_signal_count must be <= reviewed_claim_count")
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourceVerificationBottleneckRow(_FinalDataclass):
    bottleneck_rank: Decimal
    domain_label: str
    verification_queue_label: str
    evidence_family_label: str
    status: str
    bottleneck_pressure_score: Decimal
    required_authority_reference_count: Decimal
    covered_authority_reference_count: Decimal
    authority_coverage_ratio: Decimal
    freshness_lag_seconds: Decimal
    contradiction_signal_count: Decimal
    reviewed_claim_count: Decimal
    contradiction_pressure_ratio: Decimal
    extraction_confidence_score: Decimal
    missing_critical_field_count: Decimal
    available_reviewer_capacity_count: Decimal
    reviewer_capacity_gap_count: Decimal
    reviewer_capacity_gap_ratio: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchSourceVerificationBottleneckConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchSourceVerificationBottleneckConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchSourceVerificationBottleneckRow, "row")
        object.__setattr__(
            self,
            "bottleneck_rank",
            _count_decimal("bottleneck_rank", self.bottleneck_rank),
        )
        for field_name in (
            "domain_label",
            "verification_queue_label",
            "evidence_family_label",
        ):
            _require_public_label(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        for field_name in (
            "required_authority_reference_count",
            "covered_authority_reference_count",
            "freshness_lag_seconds",
            "contradiction_signal_count",
            "reviewed_claim_count",
            "missing_critical_field_count",
            "available_reviewer_capacity_count",
            "reviewer_capacity_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "bottleneck_pressure_score",
            "authority_coverage_ratio",
            "contradiction_pressure_ratio",
            "extraction_confidence_score",
            "reviewer_capacity_gap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes(self.reason_codes, ROW_REASON_SEQUENCE, require_nonempty=True),
        )
        if self.status != _status_from_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _validate_row(self, config=validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchSourceVerificationBottleneckReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchSourceVerificationBottleneckConfig
    input_count: Decimal
    bottleneck_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_coverage_ratio: Decimal
    max_freshness_lag_seconds: Decimal
    max_contradiction_pressure_ratio: Decimal
    min_extraction_confidence_score: Decimal
    total_missing_critical_field_count: Decimal
    min_available_reviewer_capacity_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourceVerificationBottleneckRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceVerificationBottleneckReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_VERIFICATION_BOTTLENECK_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_exact_type(
            self.config,
            ResearchSourceVerificationBottleneckConfig,
            "config",
        )
        _require_hard_flags("config", self.config)
        _validate_config(self.config)
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "input_count",
            "bottleneck_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_freshness_lag_seconds",
            "total_missing_critical_field_count",
            "min_available_reviewer_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_authority_coverage_ratio",
            "max_contradiction_pressure_ratio",
            "min_extraction_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _reason_codes(
                self.reason_codes,
                REPORT_REASON_SEQUENCE,
                require_nonempty=True,
            ),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        _set_or_validate_digest(self)
        _reject_unsafe_public_payload("report", self)


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        if "paper_only" not in self.value:
            return None
        return self.value["paper_only"]

    @property
    def report_only(self) -> object:
        if "report_only" not in self.value:
            return None
        return self.value["report_only"]

    @property
    def readonly(self) -> object:
        if "readonly" not in self.value:
            return None
        return self.value["readonly"]


def build_research_source_verification_bottleneck_report(
    inputs: Iterable[ResearchSourceVerificationBottleneckInput],
    *,
    config: ResearchSourceVerificationBottleneckConfig,
    generated_at: datetime,
) -> ResearchSourceVerificationBottleneckReport:
    _require_exact_type(config, ResearchSourceVerificationBottleneckConfig, "config")
    _require_hard_flags("config", config)
    _validate_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(inputs)
    base_rows = tuple(_row_from_input(item, config) for item in input_rows)
    rows = tuple(
        _with_rank(row, rank, config=config)
        for rank, row in enumerate(sorted(base_rows, key=_row_sort_key), start=1)
    )
    bottleneck_count = _count(
        sum(1 for row in rows if row.status in ("watch", "block")),
    )
    return ResearchSourceVerificationBottleneckReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        input_count=_count(len(rows)),
        bottleneck_count=bottleneck_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        average_authority_coverage_ratio=_mean_decimal(
            tuple(row.authority_coverage_ratio for row in rows),
        ),
        max_freshness_lag_seconds=_max_decimal(
            tuple(row.freshness_lag_seconds for row in rows),
        ),
        max_contradiction_pressure_ratio=_max_decimal(
            tuple(row.contradiction_pressure_ratio for row in rows),
        ),
        min_extraction_confidence_score=_min_decimal(
            tuple(row.extraction_confidence_score for row in rows),
        ),
        total_missing_critical_field_count=_sum_row_decimal(
            rows,
            "missing_critical_field_count",
        ),
        min_available_reviewer_capacity_count=_min_decimal(
            tuple(row.available_reviewer_capacity_count for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_verification_bottleneck_report_payload(
    report: ResearchSourceVerificationBottleneckReport | Mapping[str, object],
) -> dict[str, object]:
    if type(report) is ResearchSourceVerificationBottleneckReport:
        _require_hard_flags("report", report)
        payload = _json_ready(asdict(report))
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        payload = _report_payload_from_mapping(payload)
    elif type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        payload = _report_payload_from_mapping(report)
    else:
        raise ValueError(
            "report must be a ResearchSourceVerificationBottleneckReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("report payload", _MappingFlags(payload))
    _reject_unsafe_public_payload("report payload", payload)
    if "derived_validation_digest" not in payload:
        raise ValueError("derived_validation_digest must be present")
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    if digest != _digest_from_payload(payload):
        raise ValueError("derived_validation_digest does not match report payload")
    return payload


def research_source_verification_bottleneck_report_digest(
    report: ResearchSourceVerificationBottleneckReport | Mapping[str, object],
) -> str:
    payload = research_source_verification_bottleneck_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    return digest


def _row_from_input(
    item: ResearchSourceVerificationBottleneckInput,
    config: ResearchSourceVerificationBottleneckConfig,
) -> ResearchSourceVerificationBottleneckRow:
    authority_coverage_ratio = _ratio(
        item.covered_authority_reference_count,
        item.required_authority_reference_count,
    )
    contradiction_pressure_ratio = _ratio(
        item.contradiction_signal_count,
        item.reviewed_claim_count,
    )
    reviewer_capacity_gap_count = _positive_gap(
        config.min_pass_available_reviewer_capacity_count,
        item.available_reviewer_capacity_count,
    )
    reason_codes = _row_reason_codes(
        item=item,
        authority_coverage_ratio=authority_coverage_ratio,
        contradiction_pressure_ratio=contradiction_pressure_ratio,
        config=config,
    )
    return ResearchSourceVerificationBottleneckRow(
        bottleneck_rank=ONE,
        domain_label=item.domain_label,
        verification_queue_label=item.verification_queue_label,
        evidence_family_label=item.evidence_family_label,
        status=_status_from_reason_codes(reason_codes),
        bottleneck_pressure_score=_bottleneck_pressure_score(
            item=item,
            authority_coverage_ratio=authority_coverage_ratio,
            contradiction_pressure_ratio=contradiction_pressure_ratio,
            config=config,
        ),
        required_authority_reference_count=item.required_authority_reference_count,
        covered_authority_reference_count=item.covered_authority_reference_count,
        authority_coverage_ratio=authority_coverage_ratio,
        freshness_lag_seconds=item.freshness_lag_seconds,
        contradiction_signal_count=item.contradiction_signal_count,
        reviewed_claim_count=item.reviewed_claim_count,
        contradiction_pressure_ratio=contradiction_pressure_ratio,
        extraction_confidence_score=item.extraction_confidence_score,
        missing_critical_field_count=item.missing_critical_field_count,
        available_reviewer_capacity_count=item.available_reviewer_capacity_count,
        reviewer_capacity_gap_count=reviewer_capacity_gap_count,
        reviewer_capacity_gap_ratio=_ratio(
            reviewer_capacity_gap_count,
            config.min_pass_available_reviewer_capacity_count,
        ),
        observed_at=item.observed_at,
        reason_codes=reason_codes,
        validation_config=config,
    )


def _with_rank(
    row: ResearchSourceVerificationBottleneckRow,
    rank: int,
    *,
    config: ResearchSourceVerificationBottleneckConfig,
) -> ResearchSourceVerificationBottleneckRow:
    return ResearchSourceVerificationBottleneckRow(
        bottleneck_rank=_count(rank),
        domain_label=row.domain_label,
        verification_queue_label=row.verification_queue_label,
        evidence_family_label=row.evidence_family_label,
        status=row.status,
        bottleneck_pressure_score=row.bottleneck_pressure_score,
        required_authority_reference_count=row.required_authority_reference_count,
        covered_authority_reference_count=row.covered_authority_reference_count,
        authority_coverage_ratio=row.authority_coverage_ratio,
        freshness_lag_seconds=row.freshness_lag_seconds,
        contradiction_signal_count=row.contradiction_signal_count,
        reviewed_claim_count=row.reviewed_claim_count,
        contradiction_pressure_ratio=row.contradiction_pressure_ratio,
        extraction_confidence_score=row.extraction_confidence_score,
        missing_critical_field_count=row.missing_critical_field_count,
        available_reviewer_capacity_count=row.available_reviewer_capacity_count,
        reviewer_capacity_gap_count=row.reviewer_capacity_gap_count,
        reviewer_capacity_gap_ratio=row.reviewer_capacity_gap_ratio,
        observed_at=row.observed_at,
        reason_codes=row.reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    item: ResearchSourceVerificationBottleneckInput,
    authority_coverage_ratio: Decimal,
    contradiction_pressure_ratio: Decimal,
    config: ResearchSourceVerificationBottleneckConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_low_threshold_reason(
        reasons,
        metric=authority_coverage_ratio,
        pass_limit=config.min_pass_authority_coverage_ratio,
        block_limit=config.min_watch_authority_coverage_ratio,
        watch_code=AUTHORITY_COVERAGE_WATCH_REASON,
        block_code=AUTHORITY_COVERAGE_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.freshness_lag_seconds,
        pass_limit=config.max_pass_freshness_lag_seconds,
        block_limit=config.max_watch_freshness_lag_seconds,
        watch_code=FRESHNESS_LAG_WATCH_REASON,
        block_code=FRESHNESS_LAG_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=contradiction_pressure_ratio,
        pass_limit=config.max_pass_contradiction_pressure_ratio,
        block_limit=config.max_watch_contradiction_pressure_ratio,
        watch_code=CONTRADICTION_PRESSURE_WATCH_REASON,
        block_code=CONTRADICTION_PRESSURE_BLOCK_REASON,
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.extraction_confidence_score,
        pass_limit=config.min_pass_extraction_confidence_score,
        block_limit=config.min_watch_extraction_confidence_score,
        watch_code=EXTRACTION_CONFIDENCE_WATCH_REASON,
        block_code=EXTRACTION_CONFIDENCE_BLOCK_REASON,
    )
    _append_high_threshold_reason(
        reasons,
        metric=item.missing_critical_field_count,
        pass_limit=config.max_pass_missing_critical_field_count,
        block_limit=config.max_watch_missing_critical_field_count,
        watch_code=MISSING_CRITICAL_FIELDS_WATCH_REASON,
        block_code=MISSING_CRITICAL_FIELDS_BLOCK_REASON,
    )
    _append_low_threshold_reason(
        reasons,
        metric=item.available_reviewer_capacity_count,
        pass_limit=config.min_pass_available_reviewer_capacity_count,
        block_limit=config.min_watch_available_reviewer_capacity_count,
        watch_code=REVIEWER_CAPACITY_WATCH_REASON,
        block_code=REVIEWER_CAPACITY_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(CLEAR_REASON)
    reason_set = frozenset(reasons)
    return tuple(reason for reason in ROW_REASON_SEQUENCE if reason in reason_set)


def _append_high_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    pass_limit: Decimal,
    block_limit: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric > block_limit:
        reasons.append(block_code)
    elif metric > pass_limit:
        reasons.append(watch_code)


def _append_low_threshold_reason(
    reasons: list[str],
    *,
    metric: Decimal,
    pass_limit: Decimal,
    block_limit: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if metric < block_limit:
        reasons.append(block_code)
    elif metric < pass_limit:
        reasons.append(watch_code)


def _bottleneck_pressure_score(
    *,
    item: ResearchSourceVerificationBottleneckInput,
    authority_coverage_ratio: Decimal,
    contradiction_pressure_ratio: Decimal,
    config: ResearchSourceVerificationBottleneckConfig,
) -> Decimal:
    return _max_decimal(
        (
            _low_threshold_pressure(
                authority_coverage_ratio,
                config.min_pass_authority_coverage_ratio,
                config.min_watch_authority_coverage_ratio,
            ),
            _high_threshold_pressure(
                item.freshness_lag_seconds,
                config.max_pass_freshness_lag_seconds,
                config.max_watch_freshness_lag_seconds,
            ),
            _high_threshold_pressure(
                contradiction_pressure_ratio,
                config.max_pass_contradiction_pressure_ratio,
                config.max_watch_contradiction_pressure_ratio,
            ),
            _low_threshold_pressure(
                item.extraction_confidence_score,
                config.min_pass_extraction_confidence_score,
                config.min_watch_extraction_confidence_score,
            ),
            _high_threshold_pressure(
                item.missing_critical_field_count,
                config.max_pass_missing_critical_field_count,
                config.max_watch_missing_critical_field_count,
            ),
            _low_threshold_pressure(
                item.available_reviewer_capacity_count,
                config.min_pass_available_reviewer_capacity_count,
                config.min_watch_available_reviewer_capacity_count,
            ),
        ),
    )


def _high_threshold_pressure(
    value: Decimal,
    pass_limit: Decimal,
    block_limit: Decimal,
) -> Decimal:
    if value <= pass_limit:
        return ZERO
    if value >= block_limit:
        return ONE
    if block_limit == pass_limit:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((value - pass_limit) / (block_limit - pass_limit))


def _low_threshold_pressure(
    value: Decimal,
    pass_limit: Decimal,
    block_limit: Decimal,
) -> Decimal:
    if value >= pass_limit:
        return ZERO
    if value <= block_limit:
        return ONE
    if pass_limit == block_limit:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio((pass_limit - value) / (pass_limit - block_limit))


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchSourceVerificationBottleneckRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceVerificationBottleneckRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    reasons: set[str] = set()
    for row in rows:
        reasons.update(row.reason_codes)
    return tuple(reason for reason in ROW_REASON_SEQUENCE if reason in reasons)


def _normalize_inputs(
    inputs: Iterable[ResearchSourceVerificationBottleneckInput],
) -> tuple[ResearchSourceVerificationBottleneckInput, ...]:
    if isinstance(inputs, (str, bytes, Mapping)):
        raise ValueError("inputs must be an iterable of bottleneck inputs")
    try:
        iterator = iter(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of bottleneck inputs") from exc
    normalized: list[ResearchSourceVerificationBottleneckInput] = []
    seen_keys: set[tuple[str, str, str]] = set()
    for item in iterator:
        _require_exact_type(item, ResearchSourceVerificationBottleneckInput, "input")
        _require_hard_flags("input", item)
        key = (
            item.domain_label,
            item.verification_queue_label,
            item.evidence_family_label,
        )
        if key in seen_keys:
            raise ValueError("duplicate source verification bottleneck input")
        seen_keys.add(key)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchSourceVerificationBottleneckRow, ...]:
    if type(rows) not in (tuple, list):
        raise ValueError("rows must be a tuple or list")
    normalized = tuple(rows)
    for row in normalized:
        _require_exact_type(row, ResearchSourceVerificationBottleneckRow, "row")
        _require_hard_flags("row", row)
    return normalized


def _row_sort_key(
    row: ResearchSourceVerificationBottleneckRow,
) -> tuple[
    int,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    Decimal,
    str,
    str,
    str,
]:
    return (
        STATUS_RANK[row.status],
        row.bottleneck_pressure_score.copy_negate(),
        row.authority_coverage_ratio,
        row.freshness_lag_seconds.copy_negate(),
        row.contradiction_pressure_ratio.copy_negate(),
        row.extraction_confidence_score,
        row.missing_critical_field_count.copy_negate(),
        row.available_reviewer_capacity_count,
        row.domain_label,
        row.verification_queue_label,
        row.evidence_family_label,
    )


def _status_count(
    rows: tuple[ResearchSourceVerificationBottleneckRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _validate_config(config: ResearchSourceVerificationBottleneckConfig) -> None:
    _require_exact_type(config, ResearchSourceVerificationBottleneckConfig, "config")
    _require_public_string("config_version", config.config_version)
    if (
        config.config_version
        != DEFAULT_RESEARCH_SOURCE_VERIFICATION_BOTTLENECK_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    for field_name in (
        "min_pass_authority_coverage_ratio",
        "min_watch_authority_coverage_ratio",
        "max_pass_contradiction_pressure_ratio",
        "max_watch_contradiction_pressure_ratio",
        "min_pass_extraction_confidence_score",
        "min_watch_extraction_confidence_score",
    ):
        _require_canonical_ratio_decimal(field_name, getattr(config, field_name))
    for field_name in (
        "max_pass_freshness_lag_seconds",
        "max_watch_freshness_lag_seconds",
        "max_pass_missing_critical_field_count",
        "max_watch_missing_critical_field_count",
        "min_pass_available_reviewer_capacity_count",
        "min_watch_available_reviewer_capacity_count",
    ):
        _require_canonical_count_decimal(field_name, getattr(config, field_name))
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    if config.min_watch_authority_coverage_ratio > config.min_pass_authority_coverage_ratio:
        raise ValueError(
            "min_watch_authority_coverage_ratio must be <= "
            "min_pass_authority_coverage_ratio",
        )
    if config.max_watch_freshness_lag_seconds < config.max_pass_freshness_lag_seconds:
        raise ValueError(
            "max_watch_freshness_lag_seconds must be >= "
            "max_pass_freshness_lag_seconds",
        )
    if (
        config.max_watch_contradiction_pressure_ratio
        < config.max_pass_contradiction_pressure_ratio
    ):
        raise ValueError(
            "max_watch_contradiction_pressure_ratio must be >= "
            "max_pass_contradiction_pressure_ratio",
        )
    if (
        config.min_watch_extraction_confidence_score
        > config.min_pass_extraction_confidence_score
    ):
        raise ValueError(
            "min_watch_extraction_confidence_score must be <= "
            "min_pass_extraction_confidence_score",
        )
    if (
        config.max_watch_missing_critical_field_count
        < config.max_pass_missing_critical_field_count
    ):
        raise ValueError(
            "max_watch_missing_critical_field_count must be >= "
            "max_pass_missing_critical_field_count",
        )
    if (
        config.min_watch_available_reviewer_capacity_count
        > config.min_pass_available_reviewer_capacity_count
    ):
        raise ValueError(
            "min_watch_available_reviewer_capacity_count must be <= "
            "min_pass_available_reviewer_capacity_count",
        )


def _validate_row(
    row: ResearchSourceVerificationBottleneckRow,
    *,
    config: ResearchSourceVerificationBottleneckConfig | None,
) -> None:
    _require_exact_type(row, ResearchSourceVerificationBottleneckRow, "row")
    for field_name in (
        "domain_label",
        "verification_queue_label",
        "evidence_family_label",
    ):
        _require_public_label(field_name, getattr(row, field_name))
    _require_status("status", row.status)
    _reason_codes(row.reason_codes, ROW_REASON_SEQUENCE, require_nonempty=True)
    _require_hard_flags("row", row)
    _reject_unsafe_public_payload("row", row)
    for field_name in (
        "bottleneck_rank",
        "required_authority_reference_count",
        "covered_authority_reference_count",
        "freshness_lag_seconds",
        "contradiction_signal_count",
        "reviewed_claim_count",
        "missing_critical_field_count",
        "available_reviewer_capacity_count",
        "reviewer_capacity_gap_count",
    ):
        _require_canonical_count_decimal(field_name, getattr(row, field_name))
    for field_name in (
        "bottleneck_pressure_score",
        "authority_coverage_ratio",
        "contradiction_pressure_ratio",
        "extraction_confidence_score",
        "reviewer_capacity_gap_ratio",
    ):
        _require_canonical_ratio_decimal(field_name, getattr(row, field_name))
    _as_utc("observed_at", row.observed_at)
    if row.observed_at.tzinfo is not UTC or row.observed_at.fold != 0:
        raise ValueError("observed_at must be canonical UTC")
    if config is None:
        config = ResearchSourceVerificationBottleneckConfig()
    _require_exact_type(
        config,
        ResearchSourceVerificationBottleneckConfig,
        "validation_config",
    )
    _require_hard_flags("validation_config", config)
    _validate_config(config)
    if row.bottleneck_rank < ONE:
        raise ValueError("bottleneck_rank must be positive")
    if row.covered_authority_reference_count > row.required_authority_reference_count:
        raise ValueError(
            "covered_authority_reference_count must be <= "
            "required_authority_reference_count",
        )
    if row.contradiction_signal_count > row.reviewed_claim_count:
        raise ValueError("contradiction_signal_count must be <= reviewed_claim_count")
    if row.authority_coverage_ratio != _ratio(
        row.covered_authority_reference_count,
        row.required_authority_reference_count,
    ):
        raise ValueError("authority_coverage_ratio must match authority counts")
    if row.contradiction_pressure_ratio != _ratio(
        row.contradiction_signal_count,
        row.reviewed_claim_count,
    ):
        raise ValueError("contradiction_pressure_ratio must match contradiction counts")
    item = ResearchSourceVerificationBottleneckInput(
        domain_label=row.domain_label,
        verification_queue_label=row.verification_queue_label,
        evidence_family_label=row.evidence_family_label,
        required_authority_reference_count=row.required_authority_reference_count,
        covered_authority_reference_count=row.covered_authority_reference_count,
        freshness_lag_seconds=row.freshness_lag_seconds,
        contradiction_signal_count=row.contradiction_signal_count,
        reviewed_claim_count=row.reviewed_claim_count,
        extraction_confidence_score=row.extraction_confidence_score,
        missing_critical_field_count=row.missing_critical_field_count,
        available_reviewer_capacity_count=row.available_reviewer_capacity_count,
        observed_at=row.observed_at,
    )
    expected_gap_count = _positive_gap(
        config.min_pass_available_reviewer_capacity_count,
        item.available_reviewer_capacity_count,
    )
    if row.reviewer_capacity_gap_count != expected_gap_count:
        raise ValueError("reviewer_capacity_gap_count must match reviewer capacity")
    expected_gap_ratio = _ratio(
        expected_gap_count,
        config.min_pass_available_reviewer_capacity_count,
    )
    if row.reviewer_capacity_gap_ratio != expected_gap_ratio:
        raise ValueError("reviewer_capacity_gap_ratio must match reviewer capacity")
    expected_reason_codes = _row_reason_codes(
        item=item,
        authority_coverage_ratio=row.authority_coverage_ratio,
        contradiction_pressure_ratio=row.contradiction_pressure_ratio,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    expected_status = _status_from_reason_codes(expected_reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match row inputs")
    expected_pressure_score = _bottleneck_pressure_score(
        item=item,
        authority_coverage_ratio=row.authority_coverage_ratio,
        contradiction_pressure_ratio=row.contradiction_pressure_ratio,
        config=config,
    )
    if row.bottleneck_pressure_score != expected_pressure_score:
        raise ValueError("bottleneck_pressure_score must match row inputs")


def _validate_report(report: ResearchSourceVerificationBottleneckReport) -> None:
    for row in report.rows:
        _validate_row(row, config=report.config)
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must be sorted deterministically")
    if tuple(row.bottleneck_rank for row in report.rows) != tuple(
        _count(rank) for rank in range(1, len(report.rows) + 1)
    ):
        raise ValueError("bottleneck_rank must match deterministic row order")
    row_keys = tuple(
        (
            row.domain_label,
            row.verification_queue_label,
            row.evidence_family_label,
        )
        for row in report.rows
    )
    if len(set(row_keys)) != len(row_keys):
        raise ValueError("rows must not contain duplicate source verification keys")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    bottleneck_count = _count(
        sum(1 for row in report.rows if row.status in ("watch", "block")),
    )
    if report.bottleneck_count != bottleneck_count:
        raise ValueError("bottleneck_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_authority_coverage_ratio != _mean_decimal(
        tuple(row.authority_coverage_ratio for row in report.rows),
    ):
        raise ValueError("average_authority_coverage_ratio must match rows")
    if report.max_freshness_lag_seconds != _max_decimal(
        tuple(row.freshness_lag_seconds for row in report.rows),
    ):
        raise ValueError("max_freshness_lag_seconds must match rows")
    if report.max_contradiction_pressure_ratio != _max_decimal(
        tuple(row.contradiction_pressure_ratio for row in report.rows),
    ):
        raise ValueError("max_contradiction_pressure_ratio must match rows")
    if report.min_extraction_confidence_score != _min_decimal(
        tuple(row.extraction_confidence_score for row in report.rows),
    ):
        raise ValueError("min_extraction_confidence_score must match rows")
    if report.total_missing_critical_field_count != _sum_row_decimal(
        report.rows,
        "missing_critical_field_count",
    ):
        raise ValueError("total_missing_critical_field_count must match rows")
    if report.min_available_reviewer_capacity_count != _min_decimal(
        tuple(row.available_reviewer_capacity_count for row in report.rows),
    ):
        raise ValueError("min_available_reviewer_capacity_count must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _reason_codes(
    value: object,
    allowed: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    for reason_code in value:
        if type(reason_code) is not str or reason_code not in REASON_SET:
            raise ValueError("reason_codes must contain supported public reasons")
        if reason_code not in allowed:
            raise ValueError("reason_codes must be valid for this surface")
    normalized = tuple(reason for reason in allowed if reason in value)
    if normalized != value:
        raise ValueError("reason_codes must be unique and sorted")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value.strip() or value != value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_public_label(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if type(value) is not str or PUBLIC_LABEL_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC).replace(fold=0)


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return value


def _count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return _quantize(decimal_value)


def _ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_canonical_count_decimal(field_name: str, value: object) -> None:
    canonical = _count_decimal(field_name, value)
    decimal_value = _decimal(field_name, value)
    if decimal_value.as_tuple() != canonical.as_tuple():
        raise ValueError(f"{field_name} must use canonical Decimal precision")


def _require_canonical_ratio_decimal(field_name: str, value: object) -> None:
    canonical = _ratio_decimal(field_name, value)
    decimal_value = _decimal(field_name, value)
    if decimal_value.as_tuple() != canonical.as_tuple():
        raise ValueError(f"{field_name} must use canonical Decimal precision")


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("value must fit canonical Decimal precision") from exc


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(QUANTUM)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO:
        return ZERO
    if value >= ONE:
        return ONE
    return _quantize(value)


def _positive_gap(required: Decimal, actual: Decimal) -> Decimal:
    if actual >= required:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(required - actual)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO) / _count(len(values))).quantize(QUANTUM)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _sum_row_decimal(
    rows: tuple[ResearchSourceVerificationBottleneckRow, ...],
    field_name: str,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = ZERO
        for row in rows:
            total += getattr(row, field_name)
        return _quantize(total)


def _report_payload_from_mapping(
    payload: dict[str, object],
) -> dict[str, object]:
    _require_payload_fields("report payload", payload, _REPORT_PAYLOAD_FIELDS)
    validation_config = _config_from_payload(payload["config"])
    report = ResearchSourceVerificationBottleneckReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_string(
            "config_version",
            payload["config_version"],
        ),
        config=validation_config,
        input_count=_payload_decimal("input_count", payload["input_count"]),
        bottleneck_count=_payload_decimal(
            "bottleneck_count",
            payload["bottleneck_count"],
        ),
        pass_count=_payload_decimal("pass_count", payload["pass_count"]),
        watch_count=_payload_decimal("watch_count", payload["watch_count"]),
        block_count=_payload_decimal("block_count", payload["block_count"]),
        average_authority_coverage_ratio=_payload_decimal(
            "average_authority_coverage_ratio",
            payload["average_authority_coverage_ratio"],
        ),
        max_freshness_lag_seconds=_payload_decimal(
            "max_freshness_lag_seconds",
            payload["max_freshness_lag_seconds"],
        ),
        max_contradiction_pressure_ratio=_payload_decimal(
            "max_contradiction_pressure_ratio",
            payload["max_contradiction_pressure_ratio"],
        ),
        min_extraction_confidence_score=_payload_decimal(
            "min_extraction_confidence_score",
            payload["min_extraction_confidence_score"],
        ),
        total_missing_critical_field_count=_payload_decimal(
            "total_missing_critical_field_count",
            payload["total_missing_critical_field_count"],
        ),
        min_available_reviewer_capacity_count=_payload_decimal(
            "min_available_reviewer_capacity_count",
            payload["min_available_reviewer_capacity_count"],
        ),
        status=_payload_string("status", payload["status"]),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        rows=_payload_rows(payload["rows"], config=validation_config),
        derived_validation_digest=_payload_string(
            "derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )
    ready = _json_ready(asdict(report))
    if type(ready) is not dict or ready != payload:
        raise ValueError("report payload must match public schema")
    return ready


def _config_from_payload(
    value: object,
) -> ResearchSourceVerificationBottleneckConfig:
    if type(value) is not dict:
        raise ValueError("config payload must match public schema")
    _require_payload_fields("config payload", value, _CONFIG_PAYLOAD_FIELDS)
    return ResearchSourceVerificationBottleneckConfig(
        config_version=_payload_string("config_version", value["config_version"]),
        min_pass_authority_coverage_ratio=_payload_decimal(
            "min_pass_authority_coverage_ratio",
            value["min_pass_authority_coverage_ratio"],
        ),
        min_watch_authority_coverage_ratio=_payload_decimal(
            "min_watch_authority_coverage_ratio",
            value["min_watch_authority_coverage_ratio"],
        ),
        max_pass_freshness_lag_seconds=_payload_decimal(
            "max_pass_freshness_lag_seconds",
            value["max_pass_freshness_lag_seconds"],
        ),
        max_watch_freshness_lag_seconds=_payload_decimal(
            "max_watch_freshness_lag_seconds",
            value["max_watch_freshness_lag_seconds"],
        ),
        max_pass_contradiction_pressure_ratio=_payload_decimal(
            "max_pass_contradiction_pressure_ratio",
            value["max_pass_contradiction_pressure_ratio"],
        ),
        max_watch_contradiction_pressure_ratio=_payload_decimal(
            "max_watch_contradiction_pressure_ratio",
            value["max_watch_contradiction_pressure_ratio"],
        ),
        min_pass_extraction_confidence_score=_payload_decimal(
            "min_pass_extraction_confidence_score",
            value["min_pass_extraction_confidence_score"],
        ),
        min_watch_extraction_confidence_score=_payload_decimal(
            "min_watch_extraction_confidence_score",
            value["min_watch_extraction_confidence_score"],
        ),
        max_pass_missing_critical_field_count=_payload_decimal(
            "max_pass_missing_critical_field_count",
            value["max_pass_missing_critical_field_count"],
        ),
        max_watch_missing_critical_field_count=_payload_decimal(
            "max_watch_missing_critical_field_count",
            value["max_watch_missing_critical_field_count"],
        ),
        min_pass_available_reviewer_capacity_count=_payload_decimal(
            "min_pass_available_reviewer_capacity_count",
            value["min_pass_available_reviewer_capacity_count"],
        ),
        min_watch_available_reviewer_capacity_count=_payload_decimal(
            "min_watch_available_reviewer_capacity_count",
            value["min_watch_available_reviewer_capacity_count"],
        ),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
    )


def _payload_rows(
    value: object,
    *,
    config: ResearchSourceVerificationBottleneckConfig,
) -> tuple[ResearchSourceVerificationBottleneckRow, ...]:
    if type(value) is not list:
        raise ValueError("rows must match public schema")
    return tuple(_row_from_payload(row, config=config) for row in value)


def _row_from_payload(
    value: object,
    *,
    config: ResearchSourceVerificationBottleneckConfig,
) -> ResearchSourceVerificationBottleneckRow:
    if type(value) is not dict:
        raise ValueError("row payload must match public schema")
    _require_payload_fields("row payload", value, _ROW_PAYLOAD_FIELDS)
    return ResearchSourceVerificationBottleneckRow(
        bottleneck_rank=_payload_decimal(
            "bottleneck_rank",
            value["bottleneck_rank"],
        ),
        domain_label=_payload_string("domain_label", value["domain_label"]),
        verification_queue_label=_payload_string(
            "verification_queue_label",
            value["verification_queue_label"],
        ),
        evidence_family_label=_payload_string(
            "evidence_family_label",
            value["evidence_family_label"],
        ),
        status=_payload_string("status", value["status"]),
        bottleneck_pressure_score=_payload_decimal(
            "bottleneck_pressure_score",
            value["bottleneck_pressure_score"],
        ),
        required_authority_reference_count=_payload_decimal(
            "required_authority_reference_count",
            value["required_authority_reference_count"],
        ),
        covered_authority_reference_count=_payload_decimal(
            "covered_authority_reference_count",
            value["covered_authority_reference_count"],
        ),
        authority_coverage_ratio=_payload_decimal(
            "authority_coverage_ratio",
            value["authority_coverage_ratio"],
        ),
        freshness_lag_seconds=_payload_decimal(
            "freshness_lag_seconds",
            value["freshness_lag_seconds"],
        ),
        contradiction_signal_count=_payload_decimal(
            "contradiction_signal_count",
            value["contradiction_signal_count"],
        ),
        reviewed_claim_count=_payload_decimal(
            "reviewed_claim_count",
            value["reviewed_claim_count"],
        ),
        contradiction_pressure_ratio=_payload_decimal(
            "contradiction_pressure_ratio",
            value["contradiction_pressure_ratio"],
        ),
        extraction_confidence_score=_payload_decimal(
            "extraction_confidence_score",
            value["extraction_confidence_score"],
        ),
        missing_critical_field_count=_payload_decimal(
            "missing_critical_field_count",
            value["missing_critical_field_count"],
        ),
        available_reviewer_capacity_count=_payload_decimal(
            "available_reviewer_capacity_count",
            value["available_reviewer_capacity_count"],
        ),
        reviewer_capacity_gap_count=_payload_decimal(
            "reviewer_capacity_gap_count",
            value["reviewer_capacity_gap_count"],
        ),
        reviewer_capacity_gap_ratio=_payload_decimal(
            "reviewer_capacity_gap_ratio",
            value["reviewer_capacity_gap_ratio"],
        ),
        observed_at=_payload_datetime("observed_at", value["observed_at"]),
        reason_codes=_payload_reason_codes("reason_codes", value["reason_codes"]),
        paper_only=value["paper_only"],
        report_only=value["report_only"],
        readonly=value["readonly"],
        validation_config=config,
    )


def _require_payload_fields(
    label: str,
    value: object,
    expected_fields: tuple[str, ...],
) -> None:
    if type(value) is not dict or tuple(value) != expected_fields:
        raise ValueError(f"{label} must match public schema")


def _payload_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must match public schema")
    return value


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must match public schema")
    try:
        return Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must match public schema") from exc


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must match public schema")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must match public schema") from exc


def _payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str for item in value):
        raise ValueError(f"{field_name} must match public schema")
    return tuple(value)


def _set_or_validate_digest(report: ResearchSourceVerificationBottleneckReport) -> None:
    expected_digest = _digest_from_values(_report_values_without_digest(report))
    digest = report.derived_validation_digest
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    if digest:
        _require_sha256("derived_validation_digest", digest)
        if digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        return
    object.__setattr__(report, "derived_validation_digest", expected_digest)


def _report_values_without_digest(
    report: ResearchSourceVerificationBottleneckReport,
) -> dict[str, object]:
    payload: dict[str, object] = {}
    for field in fields(report):
        if field.name != "derived_validation_digest":
            payload[field.name] = getattr(report, field.name)
    return payload


def _digest_from_values(values: Mapping[str, object]) -> str:
    ready = _json_ready(values)
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload("digest payload", ready)
    canonical_payload = json.dumps(
        ready,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical_payload.encode("utf-8")).hexdigest()


def _digest_from_payload(payload: Mapping[str, object]) -> str:
    ready = _json_ready(payload)
    if type(ready) is not dict:
        raise ValueError("digest payload must be a JSON object")
    payload_without_digest = {
        key: item
        for key, item in ready.items()
        if key != "derived_validation_digest"
    }
    return _digest_from_values(payload_without_digest)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, payload: object) -> None:
    for key, value in _iter_public_items(payload):
        _reject_unsafe_public_text(f"{label}.{key}", key)
        if type(value) is str:
            _reject_unsafe_public_text(f"{label}.{key}", value)


def _iter_public_items(
    payload: object,
    active_container_ids: set[int] | None = None,
) -> tuple[tuple[str, object], ...]:
    if active_container_ids is None:
        active_container_ids = set()
    if is_dataclass(payload) and not isinstance(payload, type):
        return _iter_public_items(asdict(payload), active_container_ids)
    if isinstance(payload, Mapping):
        container_id = id(payload)
        if container_id in active_container_ids:
            raise ValueError("public payload must not contain cycles")
        active_container_ids.add(container_id)
        try:
            items: list[tuple[str, object]] = []
            for key, value in payload.items():
                if type(key) is not str:
                    raise ValueError("public payload keys must be strings")
                items.append((key, value))
                items.extend(_iter_public_items(value, active_container_ids))
            return tuple(items)
        finally:
            active_container_ids.remove(container_id)
    if isinstance(payload, (list, tuple)):
        container_id = id(payload)
        if container_id in active_container_ids:
            raise ValueError("public payload must not contain cycles")
        active_container_ids.add(container_id)
        try:
            items = []
            for item in payload:
                items.extend(_iter_public_items(item, active_container_ids))
            return tuple(items)
        finally:
            active_container_ids.remove(container_id)
    return ()


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(marker in normalized for marker in UNSAFE_PUBLIC_MARKERS):
        raise ValueError(f"unsafe public surface in {label}")
    tokens = tuple(re.findall(r"[a-z0-9]+", normalized))
    if any(token in UNSAFE_PUBLIC_TOKENS for token in tokens):
        raise ValueError(f"unsafe public surface in {label}")
    if any(
        pair in UNSAFE_PUBLIC_TOKEN_PAIRS
        for pair in zip(tokens, tokens[1:], strict=False)
    ):
        raise ValueError(f"unsafe public surface in {label}")
