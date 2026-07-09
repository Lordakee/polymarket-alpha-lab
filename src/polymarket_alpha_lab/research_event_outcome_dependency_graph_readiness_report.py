"""Report-only event outcome dependency graph readiness report.

The report scores whether outcome dependency mappings are ready for manual
review. It is a deterministic, readonly artifact and exposes no database,
network, scraping, trading, wallet, order, or persistence surface.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import InitVar, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_EVENT_OUTCOME_DEPENDENCY_GRAPH_READINESS_CONFIG_VERSION = (
    "research-event-outcome-dependency-graph-readiness-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_DEPENDENCY_MAP_READY = "dependency_map_ready"
REASON_MANUAL_REVIEW_REQUESTED = "manual_review_requested"
REASON_DEPENDENCY_DETAIL_MISSING = "dependency_detail_missing"
REASON_OUTCOME_TIMING_UNCLEAR = "outcome_timing_unclear"
REASON_DEPENDENCY_COMPLETENESS_BLOCK = "dependency_completeness_block"
REASON_AUTHORITY_BLOCK = "authority_block"
REASON_TIMING_CLARITY_BLOCK = "timing_clarity_block"
REASON_CONTRADICTION_PRESSURE_BLOCK = "contradiction_pressure_block"
REASON_AMBIGUITY_RISK_BLOCK = "ambiguity_risk_block"
REASON_VERIFICATION_COVERAGE_BLOCK = "verification_coverage_block"
REASON_READINESS_SCORE_BLOCK = "readiness_score_block"
REASON_DEPENDENCY_COMPLETENESS_WATCH = "dependency_completeness_watch"
REASON_AUTHORITY_WATCH = "authority_watch"
REASON_TIMING_CLARITY_WATCH = "timing_clarity_watch"
REASON_CONTRADICTION_PRESSURE_WATCH = "contradiction_pressure_watch"
REASON_AMBIGUITY_RISK_WATCH = "ambiguity_risk_watch"
REASON_VERIFICATION_COVERAGE_WATCH = "verification_coverage_watch"
REASON_READINESS_SCORE_WATCH = "readiness_score_watch"
REASON_DEPENDENCY_GRAPH_READY_PASS = "dependency_graph_ready_pass"

_UPSTREAM_REASON_CODE_SEQUENCE = (
    REASON_DEPENDENCY_MAP_READY,
    REASON_MANUAL_REVIEW_REQUESTED,
    REASON_DEPENDENCY_DETAIL_MISSING,
    REASON_OUTCOME_TIMING_UNCLEAR,
)
_GENERATED_ROW_REASON_CODE_SEQUENCE = (
    REASON_DEPENDENCY_COMPLETENESS_BLOCK,
    REASON_AUTHORITY_BLOCK,
    REASON_TIMING_CLARITY_BLOCK,
    REASON_CONTRADICTION_PRESSURE_BLOCK,
    REASON_AMBIGUITY_RISK_BLOCK,
    REASON_VERIFICATION_COVERAGE_BLOCK,
    REASON_READINESS_SCORE_BLOCK,
    REASON_DEPENDENCY_COMPLETENESS_WATCH,
    REASON_AUTHORITY_WATCH,
    REASON_TIMING_CLARITY_WATCH,
    REASON_CONTRADICTION_PRESSURE_WATCH,
    REASON_AMBIGUITY_RISK_WATCH,
    REASON_VERIFICATION_COVERAGE_WATCH,
    REASON_READINESS_SCORE_WATCH,
    REASON_DEPENDENCY_GRAPH_READY_PASS,
)
_ROW_REASON_CODE_SEQUENCE = (
    *_UPSTREAM_REASON_CODE_SEQUENCE,
    *_GENERATED_ROW_REASON_CODE_SEQUENCE,
)
_REASON_CODE_SEQUENCE = (REASON_EMPTY_INPUT, *_ROW_REASON_CODE_SEQUENCE)
_BLOCK_REASON_CODES = frozenset(
    (
        REASON_DEPENDENCY_COMPLETENESS_BLOCK,
        REASON_AUTHORITY_BLOCK,
        REASON_TIMING_CLARITY_BLOCK,
        REASON_CONTRADICTION_PRESSURE_BLOCK,
        REASON_AMBIGUITY_RISK_BLOCK,
        REASON_VERIFICATION_COVERAGE_BLOCK,
        REASON_READINESS_SCORE_BLOCK,
    ),
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_FIELD = "derived_validation_digest"
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PRIVATE_DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
    "source",
    "source_url",
    "source-url",
    "source url",
    "source_text",
    "source-text",
    "source text",
    "dsn",
    "database",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "private key",
    "live",
    "http://",
    "https://",
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
class ResearchEventOutcomeDependencyGraphReadinessConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_EVENT_OUTCOME_DEPENDENCY_GRAPH_READINESS_CONFIG_VERSION
    )
    pass_min_readiness_score: Decimal = Decimal("0.800000")
    watch_min_readiness_score: Decimal = Decimal("0.600000")
    min_pass_dependency_completeness_score: Decimal = Decimal("0.850000")
    min_watch_dependency_completeness_score: Decimal = Decimal("0.600000")
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.550000")
    min_pass_timing_clarity_score: Decimal = Decimal("0.750000")
    min_watch_timing_clarity_score: Decimal = Decimal("0.500000")
    max_pass_contradiction_pressure_score: Decimal = Decimal("0.200000")
    max_watch_contradiction_pressure_score: Decimal = Decimal("0.450000")
    max_pass_ambiguity_risk_score: Decimal = Decimal("0.200000")
    max_watch_ambiguity_risk_score: Decimal = Decimal("0.450000")
    min_pass_verification_coverage_score: Decimal = Decimal("0.800000")
    min_watch_verification_coverage_score: Decimal = Decimal("0.550000")
    dependency_completeness_weight: Decimal = Decimal("0.250000")
    authority_weight: Decimal = Decimal("0.200000")
    timing_clarity_weight: Decimal = Decimal("0.150000")
    contradiction_certainty_weight: Decimal = Decimal("0.150000")
    ambiguity_clarity_weight: Decimal = Decimal("0.100000")
    verification_coverage_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventOutcomeDependencyGraphReadinessConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_OUTCOME_DEPENDENCY_GRAPH_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_min_readiness_score",
            "watch_min_readiness_score",
            "min_pass_dependency_completeness_score",
            "min_watch_dependency_completeness_score",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "min_pass_timing_clarity_score",
            "min_watch_timing_clarity_score",
            "max_pass_contradiction_pressure_score",
            "max_watch_contradiction_pressure_score",
            "max_pass_ambiguity_risk_score",
            "max_watch_ambiguity_risk_score",
            "min_pass_verification_coverage_score",
            "min_watch_verification_coverage_score",
            "dependency_completeness_weight",
            "authority_weight",
            "timing_clarity_weight",
            "contradiction_certainty_weight",
            "ambiguity_clarity_weight",
            "verification_coverage_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_min_readiness_score < self.watch_min_readiness_score:
            raise ValueError(
                "pass_min_readiness_score must be at least watch_min_readiness_score",
            )
        if (
            self.min_pass_dependency_completeness_score
            < self.min_watch_dependency_completeness_score
        ):
            raise ValueError(
                "min_pass_dependency_completeness_score must be at least "
                "min_watch_dependency_completeness_score",
            )
        if self.min_pass_authority_score < self.min_watch_authority_score:
            raise ValueError(
                "min_pass_authority_score must be at least min_watch_authority_score",
            )
        if self.min_pass_timing_clarity_score < self.min_watch_timing_clarity_score:
            raise ValueError(
                "min_pass_timing_clarity_score must be at least "
                "min_watch_timing_clarity_score",
            )
        if (
            self.max_pass_contradiction_pressure_score
            > self.max_watch_contradiction_pressure_score
        ):
            raise ValueError(
                "max_pass_contradiction_pressure_score must not exceed "
                "max_watch_contradiction_pressure_score",
            )
        if self.max_pass_ambiguity_risk_score > self.max_watch_ambiguity_risk_score:
            raise ValueError(
                "max_pass_ambiguity_risk_score must not exceed "
                "max_watch_ambiguity_risk_score",
            )
        if (
            self.min_pass_verification_coverage_score
            < self.min_watch_verification_coverage_score
        ):
            raise ValueError(
                "min_pass_verification_coverage_score must be at least "
                "min_watch_verification_coverage_score",
            )
        weight_sum = _quantize(
            self.dependency_completeness_weight
            + self.authority_weight
            + self.timing_clarity_weight
            + self.contradiction_certainty_weight
            + self.ambiguity_clarity_weight
            + self.verification_coverage_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("dependency graph readiness weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchEventOutcomeDependencyGraphReadinessInput(_FinalPublicDataclass):
    review_item_ref: str
    dependency_completeness_score: Decimal
    authority_score: Decimal
    timing_clarity_score: Decimal
    contradiction_pressure_score: Decimal
    ambiguity_risk_score: Decimal
    verification_coverage_score: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventOutcomeDependencyGraphReadinessInput,
            "input",
        )
        object.__setattr__(
            self,
            "review_item_ref",
            _require_private_ref("review_item_ref", self.review_item_ref),
        )
        for field_name in (
            "dependency_completeness_score",
            "authority_score",
            "timing_clarity_score",
            "contradiction_pressure_score",
            "ambiguity_risk_score",
            "verification_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_upstream_reason_codes(self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchEventOutcomeDependencyGraphReadinessPublicNote(_FinalPublicDataclass):
    key: str
    value: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventOutcomeDependencyGraphReadinessPublicNote,
            "note",
        )
        object.__setattr__(self, "key", _require_public_identifier("key", self.key))
        object.__setattr__(self, "value", _require_public_text("value", self.value))
        _require_hard_flags("public note", self)
        _reject_unsafe_public_payload("public note", self)


@dataclass(frozen=True)
class ResearchEventOutcomeDependencyGraphReadinessRow(_FinalPublicDataclass):
    review_item_digest: str
    dependency_completeness_score: Decimal
    dependency_gap_score: Decimal
    authority_score: Decimal
    authority_gap_score: Decimal
    timing_clarity_score: Decimal
    timing_gap_score: Decimal
    contradiction_pressure_score: Decimal
    contradiction_certainty_score: Decimal
    ambiguity_risk_score: Decimal
    ambiguity_clarity_score: Decimal
    verification_coverage_score: Decimal
    verification_gap_score: Decimal
    readiness_score: Decimal
    observed_at: datetime
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchEventOutcomeDependencyGraphReadinessConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchEventOutcomeDependencyGraphReadinessConfig | None,
    ) -> None:
        _require_exact_type(
            self,
            ResearchEventOutcomeDependencyGraphReadinessRow,
            "row",
        )
        object.__setattr__(
            self,
            "review_item_digest",
            _require_private_digest("review_item_digest", self.review_item_digest),
        )
        for field_name in (
            "dependency_completeness_score",
            "dependency_gap_score",
            "authority_score",
            "authority_gap_score",
            "timing_clarity_score",
            "timing_gap_score",
            "contradiction_pressure_score",
            "contradiction_certainty_score",
            "ambiguity_risk_score",
            "ambiguity_clarity_score",
            "verification_coverage_score",
            "verification_gap_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_row_reason_codes(self.reason_codes),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REASON_CODE_SEQUENCE)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_count_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", self)


@dataclass(frozen=True)
class ResearchEventOutcomeDependencyGraphReadinessReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_readiness_score: Decimal
    min_readiness_score: Decimal
    min_dependency_completeness_score: Decimal
    min_authority_score: Decimal
    min_timing_clarity_score: Decimal
    max_contradiction_pressure_score: Decimal
    max_ambiguity_risk_score: Decimal
    min_verification_coverage_score: Decimal
    rows: tuple[ResearchEventOutcomeDependencyGraphReadinessRow, ...]
    reason_code_counts: tuple[
        ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    public_notes: tuple[ResearchEventOutcomeDependencyGraphReadinessPublicNote, ...] = ()
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventOutcomeDependencyGraphReadinessReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_EVENT_OUTCOME_DEPENDENCY_GRAPH_READINESS_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_readiness_score",
            "min_readiness_score",
            "min_dependency_completeness_score",
            "min_authority_score",
            "min_timing_clarity_score",
            "max_contradiction_pressure_score",
            "max_ambiguity_risk_score",
            "min_verification_coverage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "public_notes", _normalize_public_notes(self.public_notes))
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, object]:
        return research_event_outcome_dependency_graph_readiness_report_payload(self)


def build_research_event_outcome_dependency_graph_readiness_report(
    inputs: Sequence[ResearchEventOutcomeDependencyGraphReadinessInput],
    *,
    generated_at: datetime,
    config: ResearchEventOutcomeDependencyGraphReadinessConfig | None = None,
    public_notes: Sequence[ResearchEventOutcomeDependencyGraphReadinessPublicNote] = (),
) -> ResearchEventOutcomeDependencyGraphReadinessReport:
    """Build a deterministic, readonly dependency readiness report."""

    cfg = config or ResearchEventOutcomeDependencyGraphReadinessConfig()
    if type(cfg) is not ResearchEventOutcomeDependencyGraphReadinessConfig:
        raise ValueError(
            "config must be a ResearchEventOutcomeDependencyGraphReadinessConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for row in normalized_inputs:
        if row.observed_at > report_time:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(row, cfg) for row in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(row.reason_code for row in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        reason_codes = (REASON_EMPTY_INPUT,)
    values: dict[str, object] = {
        "generated_at": report_time,
        "config_version": cfg.config_version,
        "status": _report_status(rows),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_readiness_score": _average_ratio(
            tuple(row.readiness_score for row in rows),
        ),
        "min_readiness_score": min(
            (row.readiness_score for row in rows),
            default=_ZERO,
        ),
        "min_dependency_completeness_score": min(
            (row.dependency_completeness_score for row in rows),
            default=_ZERO,
        ),
        "min_authority_score": min(
            (row.authority_score for row in rows),
            default=_ZERO,
        ),
        "min_timing_clarity_score": min(
            (row.timing_clarity_score for row in rows),
            default=_ZERO,
        ),
        "max_contradiction_pressure_score": max(
            (row.contradiction_pressure_score for row in rows),
            default=_ZERO,
        ),
        "max_ambiguity_risk_score": max(
            (row.ambiguity_risk_score for row in rows),
            default=_ZERO,
        ),
        "min_verification_coverage_score": min(
            (row.verification_coverage_score for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "public_notes": _normalize_public_notes(public_notes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchEventOutcomeDependencyGraphReadinessReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_event_outcome_dependency_graph_readiness_report_payload(
    value: ResearchEventOutcomeDependencyGraphReadinessReport | dict[str, object],
) -> dict[str, object]:
    if type(value) is ResearchEventOutcomeDependencyGraphReadinessReport:
        _require_hard_flags("report", value)
        payload = _report_payload(value)
    elif type(value) is dict:
        payload = _copy_json_object(value)
    else:
        raise ValueError(
            "value must be a ResearchEventOutcomeDependencyGraphReadinessReport or dict",
        )
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    row: ResearchEventOutcomeDependencyGraphReadinessInput,
    config: ResearchEventOutcomeDependencyGraphReadinessConfig,
) -> ResearchEventOutcomeDependencyGraphReadinessRow:
    dependency_gap = _inverse_ratio(row.dependency_completeness_score)
    authority_gap = _inverse_ratio(row.authority_score)
    timing_gap = _inverse_ratio(row.timing_clarity_score)
    contradiction_certainty = _inverse_ratio(row.contradiction_pressure_score)
    ambiguity_clarity = _inverse_ratio(row.ambiguity_risk_score)
    verification_gap = _inverse_ratio(row.verification_coverage_score)
    readiness_score = _readiness_score(
        dependency_completeness_score=row.dependency_completeness_score,
        authority_score=row.authority_score,
        timing_clarity_score=row.timing_clarity_score,
        contradiction_certainty_score=contradiction_certainty,
        ambiguity_clarity_score=ambiguity_clarity,
        verification_coverage_score=row.verification_coverage_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        upstream_reason_codes=row.reason_codes,
        dependency_completeness_score=row.dependency_completeness_score,
        authority_score=row.authority_score,
        timing_clarity_score=row.timing_clarity_score,
        contradiction_pressure_score=row.contradiction_pressure_score,
        ambiguity_risk_score=row.ambiguity_risk_score,
        verification_coverage_score=row.verification_coverage_score,
        readiness_score=readiness_score,
        config=config,
    )
    return ResearchEventOutcomeDependencyGraphReadinessRow(
        review_item_digest=_private_ref_digest(row.review_item_ref),
        dependency_completeness_score=row.dependency_completeness_score,
        dependency_gap_score=dependency_gap,
        authority_score=row.authority_score,
        authority_gap_score=authority_gap,
        timing_clarity_score=row.timing_clarity_score,
        timing_gap_score=timing_gap,
        contradiction_pressure_score=row.contradiction_pressure_score,
        contradiction_certainty_score=contradiction_certainty,
        ambiguity_risk_score=row.ambiguity_risk_score,
        ambiguity_clarity_score=ambiguity_clarity,
        verification_coverage_score=row.verification_coverage_score,
        verification_gap_score=verification_gap,
        readiness_score=readiness_score,
        observed_at=row.observed_at,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _row_reason_codes(
    *,
    upstream_reason_codes: tuple[str, ...],
    dependency_completeness_score: Decimal,
    authority_score: Decimal,
    timing_clarity_score: Decimal,
    contradiction_pressure_score: Decimal,
    ambiguity_risk_score: Decimal,
    verification_coverage_score: Decimal,
    readiness_score: Decimal,
    config: ResearchEventOutcomeDependencyGraphReadinessConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if dependency_completeness_score < config.min_watch_dependency_completeness_score:
        reason_codes.append(REASON_DEPENDENCY_COMPLETENESS_BLOCK)
    elif dependency_completeness_score < config.min_pass_dependency_completeness_score:
        reason_codes.append(REASON_DEPENDENCY_COMPLETENESS_WATCH)
    if authority_score < config.min_watch_authority_score:
        reason_codes.append(REASON_AUTHORITY_BLOCK)
    elif authority_score < config.min_pass_authority_score:
        reason_codes.append(REASON_AUTHORITY_WATCH)
    if timing_clarity_score < config.min_watch_timing_clarity_score:
        reason_codes.append(REASON_TIMING_CLARITY_BLOCK)
    elif timing_clarity_score < config.min_pass_timing_clarity_score:
        reason_codes.append(REASON_TIMING_CLARITY_WATCH)
    if contradiction_pressure_score > config.max_watch_contradiction_pressure_score:
        reason_codes.append(REASON_CONTRADICTION_PRESSURE_BLOCK)
    elif contradiction_pressure_score > config.max_pass_contradiction_pressure_score:
        reason_codes.append(REASON_CONTRADICTION_PRESSURE_WATCH)
    if ambiguity_risk_score > config.max_watch_ambiguity_risk_score:
        reason_codes.append(REASON_AMBIGUITY_RISK_BLOCK)
    elif ambiguity_risk_score > config.max_pass_ambiguity_risk_score:
        reason_codes.append(REASON_AMBIGUITY_RISK_WATCH)
    if verification_coverage_score < config.min_watch_verification_coverage_score:
        reason_codes.append(REASON_VERIFICATION_COVERAGE_BLOCK)
    elif verification_coverage_score < config.min_pass_verification_coverage_score:
        reason_codes.append(REASON_VERIFICATION_COVERAGE_WATCH)
    if readiness_score < config.watch_min_readiness_score:
        reason_codes.append(REASON_READINESS_SCORE_BLOCK)
    elif readiness_score < config.pass_min_readiness_score:
        reason_codes.append(REASON_READINESS_SCORE_WATCH)
    generated = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
    )
    if not generated:
        reason_codes.append(REASON_DEPENDENCY_GRAPH_READY_PASS)
    return _normalize_row_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return STATUS_BLOCK
    if REASON_DEPENDENCY_GRAPH_READY_PASS in reason_codes:
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    rows: tuple[ResearchEventOutcomeDependencyGraphReadinessRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchEventOutcomeDependencyGraphReadinessRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchEventOutcomeDependencyGraphReadinessRow,
) -> tuple[int, Decimal, str]:
    return (_status_rank(row.status), row.readiness_score, row.review_item_digest)


def _status_rank(value: str) -> int:
    return {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[value]


def _reason_code_counts(
    rows: tuple[ResearchEventOutcomeDependencyGraphReadinessRow, ...],
) -> tuple[ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount, ...]:
    total = _decimal_count(len(rows))
    counts: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return tuple(
        ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_ratio(_decimal_count(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _readiness_score(
    *,
    dependency_completeness_score: Decimal,
    authority_score: Decimal,
    timing_clarity_score: Decimal,
    contradiction_certainty_score: Decimal,
    ambiguity_clarity_score: Decimal,
    verification_coverage_score: Decimal,
    config: ResearchEventOutcomeDependencyGraphReadinessConfig,
) -> Decimal:
    score = (
        dependency_completeness_score * config.dependency_completeness_weight
        + authority_score * config.authority_weight
        + timing_clarity_score * config.timing_clarity_weight
        + contradiction_certainty_score * config.contradiction_certainty_weight
        + ambiguity_clarity_score * config.ambiguity_clarity_weight
        + verification_coverage_score * config.verification_coverage_weight
    )
    return _clamp_ratio(score)


def _validate_row(
    row: ResearchEventOutcomeDependencyGraphReadinessRow,
    config: ResearchEventOutcomeDependencyGraphReadinessConfig | None,
) -> None:
    if config is not None:
        if type(config) is not ResearchEventOutcomeDependencyGraphReadinessConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchEventOutcomeDependencyGraphReadinessConfig",
            )
        if row.dependency_gap_score != _inverse_ratio(
            row.dependency_completeness_score,
        ):
            raise ValueError(
                "dependency_gap_score must match dependency_completeness_score",
            )
        if row.authority_gap_score != _inverse_ratio(row.authority_score):
            raise ValueError("authority_gap_score must match authority_score")
        if row.timing_gap_score != _inverse_ratio(row.timing_clarity_score):
            raise ValueError("timing_gap_score must match timing_clarity_score")
        if row.contradiction_certainty_score != _inverse_ratio(
            row.contradiction_pressure_score,
        ):
            raise ValueError(
                "contradiction_certainty_score must match "
                "contradiction_pressure_score",
            )
        if row.ambiguity_clarity_score != _inverse_ratio(row.ambiguity_risk_score):
            raise ValueError("ambiguity_clarity_score must match ambiguity_risk_score")
        if row.verification_gap_score != _inverse_ratio(
            row.verification_coverage_score,
        ):
            raise ValueError(
                "verification_gap_score must match verification_coverage_score",
            )
        expected_readiness = _readiness_score(
            dependency_completeness_score=row.dependency_completeness_score,
            authority_score=row.authority_score,
            timing_clarity_score=row.timing_clarity_score,
            contradiction_certainty_score=row.contradiction_certainty_score,
            ambiguity_clarity_score=row.ambiguity_clarity_score,
            verification_coverage_score=row.verification_coverage_score,
            config=config,
        )
        if row.readiness_score != expected_readiness:
            raise ValueError("readiness_score must match component scores")
        upstream_reason_codes = tuple(
            reason_code
            for reason_code in row.reason_codes
            if reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        )
        expected_reasons = _row_reason_codes(
            upstream_reason_codes=upstream_reason_codes,
            dependency_completeness_score=row.dependency_completeness_score,
            authority_score=row.authority_score,
            timing_clarity_score=row.timing_clarity_score,
            contradiction_pressure_score=row.contradiction_pressure_score,
            ambiguity_risk_score=row.ambiguity_risk_score,
            verification_coverage_score=row.verification_coverage_score,
            readiness_score=row.readiness_score,
            config=config,
        )
        if row.reason_codes != expected_reasons:
            raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if (
        REASON_DEPENDENCY_GRAPH_READY_PASS in row.reason_codes
        and row.reason_codes[-1] != REASON_DEPENDENCY_GRAPH_READY_PASS
    ):
        raise ValueError("pass reason must not be mixed with risk reasons")


def _validate_report(report: ResearchEventOutcomeDependencyGraphReadinessReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.average_readiness_score != _average_ratio(
        tuple(row.readiness_score for row in report.rows),
    ):
        raise ValueError("average_readiness_score must match rows")
    if report.min_readiness_score != min(
        (row.readiness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_readiness_score must match rows")
    if report.min_dependency_completeness_score != min(
        (row.dependency_completeness_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_dependency_completeness_score must match rows")
    if report.min_authority_score != min(
        (row.authority_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_authority_score must match rows")
    if report.min_timing_clarity_score != min(
        (row.timing_clarity_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_timing_clarity_score must match rows")
    if report.max_contradiction_pressure_score != max(
        (row.contradiction_pressure_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_contradiction_pressure_score must match rows")
    if report.max_ambiguity_risk_score != max(
        (row.ambiguity_risk_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("max_ambiguity_risk_score must match rows")
    if report.min_verification_coverage_score != min(
        (row.verification_coverage_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("min_verification_coverage_score must match rows")
    expected_counts = _reason_code_counts(report.rows)
    expected_codes = tuple(row.reason_code for row in expected_counts)
    if not report.rows:
        expected_counts = (
            ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
        expected_codes = (REASON_EMPTY_INPUT,)
    if report.reason_code_counts != expected_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != expected_codes:
        raise ValueError("reason_codes must match reason_code_counts")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")


def _normalize_inputs(
    inputs: Sequence[ResearchEventOutcomeDependencyGraphReadinessInput],
) -> tuple[ResearchEventOutcomeDependencyGraphReadinessInput, ...]:
    if type(inputs) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    normalized = tuple(inputs)
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchEventOutcomeDependencyGraphReadinessInput:
            raise ValueError(
                "inputs must contain "
                "ResearchEventOutcomeDependencyGraphReadinessInput",
            )
        _require_hard_flags("input", row)
        digest = _private_ref_digest(row.review_item_ref)
        if digest in seen:
            raise ValueError("inputs must be unique by review item digest")
        seen.add(digest)
    return normalized


def _normalize_rows(
    rows: tuple[ResearchEventOutcomeDependencyGraphReadinessRow, ...],
) -> tuple[ResearchEventOutcomeDependencyGraphReadinessRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventOutcomeDependencyGraphReadinessRow:
            raise ValueError(
                "rows must contain ResearchEventOutcomeDependencyGraphReadinessRow",
            )
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must use deterministic ordering")
    digests = tuple(row.review_item_digest for row in normalized)
    if len(set(digests)) != len(digests):
        raise ValueError("rows must have unique review item digests")
    return normalized


def _normalize_reason_code_counts(
    rows: tuple[ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount, ...],
) -> tuple[ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount",
            )
        _require_hard_flags("reason count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must use deterministic ordering")
    if len(set(row.reason_code for row in normalized)) != len(normalized):
        raise ValueError("reason_code_counts must not contain duplicates")
    return normalized


def _normalize_public_notes(
    public_notes: Sequence[ResearchEventOutcomeDependencyGraphReadinessPublicNote],
) -> tuple[ResearchEventOutcomeDependencyGraphReadinessPublicNote, ...]:
    if type(public_notes) not in (list, tuple):
        raise ValueError("public_notes must be a list or tuple")
    normalized = tuple(public_notes)
    for note in normalized:
        if type(note) is not ResearchEventOutcomeDependencyGraphReadinessPublicNote:
            raise ValueError(
                "public_notes must contain "
                "ResearchEventOutcomeDependencyGraphReadinessPublicNote",
            )
        _require_hard_flags("public note", note)
    keys = tuple(note.key for note in normalized)
    if keys != tuple(sorted(keys)):
        raise ValueError("public_notes must be sorted by key")
    if len(set(keys)) != len(keys):
        raise ValueError("public_notes must have unique keys")
    return normalized


def _normalize_upstream_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code(
            "reason_codes",
            reason_code,
            _UPSTREAM_REASON_CODE_SEQUENCE,
        )
    normalized = tuple(
        reason_code
        for reason_code in _UPSTREAM_REASON_CODE_SEQUENCE
        if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    return normalized


def _normalize_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _ROW_REASON_CODE_SEQUENCE)
    normalized = tuple(
        reason_code for reason_code in _ROW_REASON_CODE_SEQUENCE if reason_code in value
    )
    if normalized != value:
        raise ValueError("reason_codes must be unique and deterministic")
    if REASON_DEPENDENCY_GRAPH_READY_PASS in value:
        generated = tuple(
            reason_code
            for reason_code in value
            if reason_code in _GENERATED_ROW_REASON_CODE_SEQUENCE
        )
        if generated != (REASON_DEPENDENCY_GRAPH_READY_PASS,):
            raise ValueError("reason_codes cannot mix pass with risk reasons")
    return normalized


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    for reason_code in value:
        _require_reason_code("reason_codes", reason_code, _REASON_CODE_SEQUENCE)
    if len(set(value)) != len(value):
        raise ValueError("reason_codes must be unique and deterministic")
    return value


def _report_payload(
    report: ResearchEventOutcomeDependencyGraphReadinessReport,
) -> dict[str, object]:
    payload = _report_payload_without_digest(
        generated_at=report.generated_at,
        config_version=report.config_version,
        status=report.status,
        row_count=report.row_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        average_readiness_score=report.average_readiness_score,
        min_readiness_score=report.min_readiness_score,
        min_dependency_completeness_score=report.min_dependency_completeness_score,
        min_authority_score=report.min_authority_score,
        min_timing_clarity_score=report.min_timing_clarity_score,
        max_contradiction_pressure_score=report.max_contradiction_pressure_score,
        max_ambiguity_risk_score=report.max_ambiguity_risk_score,
        min_verification_coverage_score=report.min_verification_coverage_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
        reason_codes=report.reason_codes,
        public_notes=report.public_notes,
        paper_only=report.paper_only,
        report_only=report.report_only,
        readonly=report.readonly,
    )
    payload[_DIGEST_FIELD] = report.derived_validation_digest
    return payload


def _report_payload_without_digest(**values: object) -> dict[str, object]:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    return payload


def _report_digest(report: ResearchEventOutcomeDependencyGraphReadinessReport) -> str:
    return _report_digest_from_values(
        {
            "generated_at": report.generated_at,
            "config_version": report.config_version,
            "status": report.status,
            "row_count": report.row_count,
            "pass_count": report.pass_count,
            "watch_count": report.watch_count,
            "block_count": report.block_count,
            "average_readiness_score": report.average_readiness_score,
            "min_readiness_score": report.min_readiness_score,
            "min_dependency_completeness_score": (
                report.min_dependency_completeness_score
            ),
            "min_authority_score": report.min_authority_score,
            "min_timing_clarity_score": report.min_timing_clarity_score,
            "max_contradiction_pressure_score": (
                report.max_contradiction_pressure_score
            ),
            "max_ambiguity_risk_score": report.max_ambiguity_risk_score,
            "min_verification_coverage_score": report.min_verification_coverage_score,
            "rows": report.rows,
            "reason_code_counts": report.reason_code_counts,
            "reason_codes": report.reason_codes,
            "public_notes": report.public_notes,
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload_digest(payload: dict[str, object]) -> None:
    digest = payload.get(_DIGEST_FIELD)
    _require_digest(_DIGEST_FIELD, digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop(_DIGEST_FIELD, None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest mismatch")


def _validate_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status" and item not in _STATUS_VALUES:
                raise ValueError("status must be pass, watch, or block")
            _validate_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_payload_statuses(item)


def _copy_json_object(value: dict[str, object]) -> dict[str, object]:
    copied = _copy_json_value(value)
    if type(copied) is not dict:
        raise ValueError("payload must be a JSON object")
    return copied


def _copy_json_value(value: object) -> object:
    if value is None or type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        copied: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            copied[key] = _copy_json_value(item)
        return copied
    if isinstance(value, list):
        return [_copy_json_value(item) for item in value]
    raise ValueError("payload contains unsupported JSON value")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            ready[field.name] = _json_ready(getattr(value, field.name))
        return ready
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
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


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} has unsafe public value")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty private text")
    if len(value) > 2048:
        raise ValueError(f"{field_name} must not exceed 2048 characters")
    return value


def _private_ref_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _require_private_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _PRIVATE_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a redacted sha256 digest")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_public_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value or not value:
        raise ValueError(f"{field_name} must be non-empty public text")
    if len(value) > 512:
        raise ValueError(f"{field_name} must not exceed 512 characters")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a reason code")
    _require_public_identifier(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported reason code")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _inverse_ratio(value: Decimal) -> Decimal:
    return _clamp_ratio(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


__all__ = (
    "DEFAULT_RESEARCH_EVENT_OUTCOME_DEPENDENCY_GRAPH_READINESS_CONFIG_VERSION",
    "ResearchEventOutcomeDependencyGraphReadinessConfig",
    "ResearchEventOutcomeDependencyGraphReadinessInput",
    "ResearchEventOutcomeDependencyGraphReadinessPublicNote",
    "ResearchEventOutcomeDependencyGraphReadinessReasonCodeCount",
    "ResearchEventOutcomeDependencyGraphReadinessReport",
    "ResearchEventOutcomeDependencyGraphReadinessRow",
    "build_research_event_outcome_dependency_graph_readiness_report",
    "research_event_outcome_dependency_graph_readiness_report_payload",
)
