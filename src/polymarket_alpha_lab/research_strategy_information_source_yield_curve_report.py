"""Report-only information source yield curve reducer.

The reducer ranks sanitized information source categories by expected yield
over time. It is deterministic, readonly, paper-only, and exposes only safe
public report payloads for analyst review.
"""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_STRATEGY_INFORMATION_SOURCE_YIELD_CURVE_REPORT_CONFIG_VERSION = (
    "research-strategy-information-source-yield-curve-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"

REASON_EMPTY_INPUT = "empty_input"
REASON_YIELD_SCORE_PASS = "yield_score_pass"
REASON_YIELD_SCORE_WATCH = "yield_score_watch"
REASON_YIELD_SCORE_BLOCK = "yield_score_block"
REASON_HIGH_AUTHORITY_CONFIDENCE = "high_authority_confidence"
REASON_HIGH_CONFLICT_REDUCTION = "high_conflict_reduction"
REASON_REVIEW_EFFORT_CONSTRAINT = "review_effort_constraint"

_ROW_REASON_CODE_SEQUENCE = (
    REASON_YIELD_SCORE_PASS,
    REASON_YIELD_SCORE_WATCH,
    REASON_YIELD_SCORE_BLOCK,
    REASON_HIGH_AUTHORITY_CONFIDENCE,
    REASON_HIGH_CONFLICT_REDUCTION,
    REASON_REVIEW_EFFORT_CONSTRAINT,
)
_REPORT_REASON_CODE_SEQUENCE = (
    REASON_EMPTY_INPUT,
    REASON_YIELD_SCORE_PASS,
    REASON_YIELD_SCORE_WATCH,
    REASON_YIELD_SCORE_BLOCK,
    REASON_HIGH_AUTHORITY_CONFIDENCE,
    REASON_HIGH_CONFLICT_REDUCTION,
    REASON_REVIEW_EFFORT_CONSTRAINT,
)
_STATUS_VALUES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_DIGEST_FIELD = "validation_digest"
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_SECONDS_PER_HOUR = Decimal("3600.000000")
_MICROSECOND_DIVISOR = Decimal("1000000.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "market",
    "slug",
    "question",
    "url",
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
    "auth_",
    "auth-",
    "auth ",
    "authentication",
    "credential",
    "secret",
    "private key",
    "order",
    "trade",
    "position",
    "sizing",
    "buy",
    "sell",
    "recommend",
    "live",
    "http://",
    "https://",
    "://",
    "www.",
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
class ResearchStrategyInformationSourceYieldCurveConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_INFORMATION_SOURCE_YIELD_CURVE_REPORT_CONFIG_VERSION
    )
    yield_score_block_threshold: Decimal = Decimal("0.700000")
    yield_score_watch_threshold: Decimal = Decimal("0.450000")
    freshness_decay_window_hours: Decimal = Decimal("24.000000")
    high_authority_confidence_threshold: Decimal = Decimal("0.800000")
    high_conflict_reduction_threshold: Decimal = Decimal("0.700000")
    review_effort_constraint_threshold: Decimal = Decimal("0.650000")
    freshness_weight: Decimal = Decimal("0.350000")
    authority_confidence_weight: Decimal = Decimal("0.300000")
    conflict_reduction_weight: Decimal = Decimal("0.250000")
    review_efficiency_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyInformationSourceYieldCurveConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_INFORMATION_SOURCE_YIELD_CURVE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "yield_score_block_threshold",
            "yield_score_watch_threshold",
            "high_authority_confidence_threshold",
            "high_conflict_reduction_threshold",
            "review_effort_constraint_threshold",
            "freshness_weight",
            "authority_confidence_weight",
            "conflict_reduction_weight",
            "review_efficiency_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshness_decay_window_hours",
            _require_positive_decimal(
                "freshness_decay_window_hours",
                self.freshness_decay_window_hours,
            ),
        )
        if self.yield_score_block_threshold < self.yield_score_watch_threshold:
            raise ValueError(
                "yield_score_block_threshold must be at least "
                "yield_score_watch_threshold",
            )
        weight_sum = _quantize(
            self.freshness_weight
            + self.authority_confidence_weight
            + self.conflict_reduction_weight
            + self.review_efficiency_weight,
        )
        if weight_sum != _ONE:
            raise ValueError("weights must sum to one")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchStrategyInformationSourceYieldCurveInput(_FinalPublicDataclass):
    source_category: str
    last_observed_at: datetime
    authority_confidence_score: Decimal
    conflict_reduction_score: Decimal
    review_effort_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyInformationSourceYieldCurveInput, "input")
        object.__setattr__(
            self,
            "source_category",
            _require_public_identifier("source_category", self.source_category),
        )
        object.__setattr__(
            self,
            "last_observed_at",
            _as_utc("last_observed_at", self.last_observed_at),
        )
        for field_name in (
            "authority_confidence_score",
            "conflict_reduction_score",
            "review_effort_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchStrategyInformationSourceYieldCurveRow(_FinalPublicDataclass):
    source_category: str
    last_observed_at: datetime
    observation_age_hours: Decimal
    freshness_yield_score: Decimal
    authority_confidence_score: Decimal
    conflict_reduction_score: Decimal
    review_effort_score: Decimal
    review_efficiency_score: Decimal
    expected_information_yield_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchStrategyInformationSourceYieldCurveConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchStrategyInformationSourceYieldCurveConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchStrategyInformationSourceYieldCurveRow, "row")
        object.__setattr__(
            self,
            "source_category",
            _require_public_identifier("source_category", self.source_category),
        )
        object.__setattr__(
            self,
            "last_observed_at",
            _as_utc("last_observed_at", self.last_observed_at),
        )
        object.__setattr__(
            self,
            "observation_age_hours",
            _require_nonnegative_decimal("observation_age_hours", self.observation_age_hours),
        )
        for field_name in (
            "freshness_yield_score",
            "authority_confidence_score",
            "conflict_reduction_score",
            "review_effort_score",
            "review_efficiency_score",
            "expected_information_yield_score",
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
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                _ROW_REASON_CODE_SEQUENCE,
            ),
        )
        _validate_row(self, validation_config)
        _require_hard_flags("row", self)
        expected_digest = _digest_from_dataclass(self)
        if self.validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.validation_digest != expected_digest:
            raise ValueError("validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.validation_digest)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchStrategyInformationSourceYieldCurveReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyInformationSourceYieldCurveReasonCodeCount,
            "reason count",
        )
        _require_reason_code("reason_code", self.reason_code, _REPORT_REASON_CODE_SEQUENCE)
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
class ResearchStrategyInformationSourceYieldCurveReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    status: str
    source_category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_expected_information_yield_score: Decimal
    highest_expected_information_yield_score: Decimal
    average_freshness_yield_score: Decimal
    average_authority_confidence_score: Decimal
    average_conflict_reduction_score: Decimal
    average_review_effort_score: Decimal
    rows: tuple[ResearchStrategyInformationSourceYieldCurveRow, ...]
    reason_code_counts: tuple[
        ResearchStrategyInformationSourceYieldCurveReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyInformationSourceYieldCurveReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_INFORMATION_SOURCE_YIELD_CURVE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in (
            "source_category_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_expected_information_yield_score",
            "highest_expected_information_yield_score",
            "average_freshness_yield_score",
            "average_authority_confidence_score",
            "average_conflict_reduction_score",
            "average_review_effort_score",
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
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_report(self)
        _require_hard_flags("report", self)
        expected_digest = _digest_from_dataclass(self)
        if self.validation_digest == "":
            object.__setattr__(self, _DIGEST_FIELD, expected_digest)
        elif self.validation_digest != expected_digest:
            raise ValueError("validation_digest mismatch")
        _require_digest(_DIGEST_FIELD, self.validation_digest)
        _reject_unsafe_public_payload("report", self)

    @property
    def public_payload(self) -> dict[str, object]:
        return research_strategy_information_source_yield_curve_report_public_payload(self)


def build_research_strategy_information_source_yield_curve_report(
    inputs: Sequence[ResearchStrategyInformationSourceYieldCurveInput],
    *,
    generated_at: datetime,
    config: ResearchStrategyInformationSourceYieldCurveConfig | None = None,
) -> ResearchStrategyInformationSourceYieldCurveReport:
    cfg = config or ResearchStrategyInformationSourceYieldCurveConfig()
    if type(cfg) is not ResearchStrategyInformationSourceYieldCurveConfig:
        raise ValueError(
            "config must be a ResearchStrategyInformationSourceYieldCurveConfig",
        )
    _require_hard_flags("config", cfg)
    report_time = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    for value in normalized_inputs:
        if value.last_observed_at > report_time:
            raise ValueError("last_observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_for_input(value, generated_at=report_time, config=cfg) for value in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    reason_code_counts = _reason_code_counts(rows)
    reason_codes = tuple(item.reason_code for item in reason_code_counts)
    if not rows:
        reason_code_counts = (
            ResearchStrategyInformationSourceYieldCurveReasonCodeCount(
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
        "source_category_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, STATUS_PASS)),
        "watch_count": _decimal_count(_status_count(rows, STATUS_WATCH)),
        "block_count": _decimal_count(_status_count(rows, STATUS_BLOCK)),
        "average_expected_information_yield_score": _average_ratio(
            tuple(row.expected_information_yield_score for row in rows),
        ),
        "highest_expected_information_yield_score": max(
            (row.expected_information_yield_score for row in rows),
            default=_ZERO,
        ),
        "average_freshness_yield_score": _average_ratio(
            tuple(row.freshness_yield_score for row in rows),
        ),
        "average_authority_confidence_score": _average_ratio(
            tuple(row.authority_confidence_score for row in rows),
        ),
        "average_conflict_reduction_score": _average_ratio(
            tuple(row.conflict_reduction_score for row in rows),
        ),
        "average_review_effort_score": _average_ratio(
            tuple(row.review_effort_score for row in rows),
        ),
        "rows": rows,
        "reason_code_counts": reason_code_counts,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchStrategyInformationSourceYieldCurveReport(
        **values,
        validation_digest=_digest_from_mapping(values),
    )


def research_strategy_information_source_yield_curve_report_public_payload(
    value: ResearchStrategyInformationSourceYieldCurveReport | Mapping[str, object],
) -> dict[str, object]:
    if type(value) is ResearchStrategyInformationSourceYieldCurveReport:
        _require_hard_flags("report", value)
        payload = _json_ready(value, omit_digest=False)
    elif isinstance(value, Mapping):
        payload = _json_ready(value, omit_digest=False)
    else:
        raise ValueError(
            "value must be a ResearchStrategyInformationSourceYieldCurveReport or dict",
        )
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _validate_payload_statuses(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _validate_payload_digest(payload)
    return payload


def _row_for_input(
    value: ResearchStrategyInformationSourceYieldCurveInput,
    *,
    generated_at: datetime,
    config: ResearchStrategyInformationSourceYieldCurveConfig,
) -> ResearchStrategyInformationSourceYieldCurveRow:
    observation_age_hours = _age_hours(value.last_observed_at, generated_at)
    freshness_yield_score = _freshness_yield_score(observation_age_hours, config)
    review_efficiency_score = _inverse_ratio(value.review_effort_score)
    expected_yield = _expected_information_yield_score(
        freshness_yield_score=freshness_yield_score,
        authority_confidence_score=value.authority_confidence_score,
        conflict_reduction_score=value.conflict_reduction_score,
        review_efficiency_score=review_efficiency_score,
        config=config,
    )
    reason_codes = _row_reason_codes(
        expected_information_yield_score=expected_yield,
        authority_confidence_score=value.authority_confidence_score,
        conflict_reduction_score=value.conflict_reduction_score,
        review_effort_score=value.review_effort_score,
        config=config,
    )
    return ResearchStrategyInformationSourceYieldCurveRow(
        source_category=value.source_category,
        last_observed_at=value.last_observed_at,
        observation_age_hours=observation_age_hours,
        freshness_yield_score=freshness_yield_score,
        authority_confidence_score=value.authority_confidence_score,
        conflict_reduction_score=value.conflict_reduction_score,
        review_effort_score=value.review_effort_score,
        review_efficiency_score=review_efficiency_score,
        expected_information_yield_score=expected_yield,
        status=_row_status(expected_yield, config),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _freshness_yield_score(
    observation_age_hours: Decimal,
    config: ResearchStrategyInformationSourceYieldCurveConfig,
) -> Decimal:
    return _clamp_ratio(
        _ONE - _safe_divide(observation_age_hours, config.freshness_decay_window_hours),
    )


def _expected_information_yield_score(
    *,
    freshness_yield_score: Decimal,
    authority_confidence_score: Decimal,
    conflict_reduction_score: Decimal,
    review_efficiency_score: Decimal,
    config: ResearchStrategyInformationSourceYieldCurveConfig,
) -> Decimal:
    return _quantize(
        freshness_yield_score * config.freshness_weight
        + authority_confidence_score * config.authority_confidence_weight
        + conflict_reduction_score * config.conflict_reduction_weight
        + review_efficiency_score * config.review_efficiency_weight,
    )


def _row_status(
    expected_information_yield_score: Decimal,
    config: ResearchStrategyInformationSourceYieldCurveConfig,
) -> str:
    if expected_information_yield_score >= config.yield_score_block_threshold:
        return STATUS_BLOCK
    if expected_information_yield_score >= config.yield_score_watch_threshold:
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    expected_information_yield_score: Decimal,
    authority_confidence_score: Decimal,
    conflict_reduction_score: Decimal,
    review_effort_score: Decimal,
    config: ResearchStrategyInformationSourceYieldCurveConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    status = _row_status(expected_information_yield_score, config)
    if status == STATUS_BLOCK:
        codes.append(REASON_YIELD_SCORE_BLOCK)
    elif status == STATUS_WATCH:
        codes.append(REASON_YIELD_SCORE_WATCH)
    else:
        codes.append(REASON_YIELD_SCORE_PASS)
    if authority_confidence_score >= config.high_authority_confidence_threshold:
        codes.append(REASON_HIGH_AUTHORITY_CONFIDENCE)
    if conflict_reduction_score >= config.high_conflict_reduction_threshold:
        codes.append(REASON_HIGH_CONFLICT_REDUCTION)
    if review_effort_score >= config.review_effort_constraint_threshold:
        codes.append(REASON_REVIEW_EFFORT_CONSTRAINT)
    return _normalize_reason_codes("reason_codes", tuple(codes), _ROW_REASON_CODE_SEQUENCE)


def _report_status(
    rows: tuple[ResearchStrategyInformationSourceYieldCurveRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _row_sort_key(
    row: ResearchStrategyInformationSourceYieldCurveRow,
) -> tuple[int, Decimal, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        -row.expected_information_yield_score,
        row.source_category,
    )


def _normalize_inputs(
    inputs: Sequence[ResearchStrategyInformationSourceYieldCurveInput],
) -> tuple[ResearchStrategyInformationSourceYieldCurveInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be a sequence")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be a sequence") from exc
    seen_categories: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyInformationSourceYieldCurveInput:
            raise ValueError(
                "inputs must contain only ResearchStrategyInformationSourceYieldCurveInput values",
            )
        _require_hard_flags("input", value)
        if value.source_category in seen_categories:
            raise ValueError("inputs must not contain duplicate source_category values")
        seen_categories.add(value.source_category)
    return normalized


def _normalize_rows(
    rows: Sequence[ResearchStrategyInformationSourceYieldCurveRow],
) -> tuple[ResearchStrategyInformationSourceYieldCurveRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be a sequence") from exc
    seen_categories: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyInformationSourceYieldCurveRow:
            raise ValueError(
                "rows must contain ResearchStrategyInformationSourceYieldCurveRow values",
            )
        _require_hard_flags("row", row)
        if row.source_category in seen_categories:
            raise ValueError("rows must not contain duplicate source_category values")
        seen_categories.add(row.source_category)
    return normalized


def _normalize_reason_code_counts(
    counts: Sequence[ResearchStrategyInformationSourceYieldCurveReasonCodeCount],
) -> tuple[ResearchStrategyInformationSourceYieldCurveReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be a sequence")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be a sequence") from exc
    seen_codes: set[str] = set()
    for count in normalized:
        if type(count) is not ResearchStrategyInformationSourceYieldCurveReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyInformationSourceYieldCurveReasonCodeCount values",
            )
        _require_hard_flags("reason count", count)
        if count.reason_code in seen_codes:
            raise ValueError("reason_code_counts must not contain duplicate codes")
        seen_codes.add(count.reason_code)
    if tuple(sorted(normalized, key=lambda item: item.reason_code)) != normalized:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _validate_row(
    row: ResearchStrategyInformationSourceYieldCurveRow,
    config: ResearchStrategyInformationSourceYieldCurveConfig | None,
) -> None:
    if row.review_efficiency_score != _inverse_ratio(row.review_effort_score):
        raise ValueError("review_efficiency_score must match review_effort_score")
    active_config = config or ResearchStrategyInformationSourceYieldCurveConfig()
    expected_freshness = _freshness_yield_score(
        row.observation_age_hours,
        active_config,
    )
    if row.freshness_yield_score != expected_freshness:
        raise ValueError("freshness_yield_score must match observation_age_hours")
    expected_yield = _expected_information_yield_score(
        freshness_yield_score=row.freshness_yield_score,
        authority_confidence_score=row.authority_confidence_score,
        conflict_reduction_score=row.conflict_reduction_score,
        review_efficiency_score=row.review_efficiency_score,
        config=active_config,
    )
    if row.expected_information_yield_score != expected_yield:
        raise ValueError("expected_information_yield_score does not match inputs")
    if row.status != _row_status(row.expected_information_yield_score, active_config):
        raise ValueError("status does not match expected_information_yield_score")
    expected_codes = _row_reason_codes(
        expected_information_yield_score=row.expected_information_yield_score,
        authority_confidence_score=row.authority_confidence_score,
        conflict_reduction_score=row.conflict_reduction_score,
        review_effort_score=row.review_effort_score,
        config=active_config,
    )
    if row.reason_codes != expected_codes:
        raise ValueError("reason_codes do not match inputs")


def _validate_report(report: ResearchStrategyInformationSourceYieldCurveReport) -> None:
    if report.source_category_count != _decimal_count(len(report.rows)):
        raise ValueError("source_category_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if (
        report.source_category_count
        != report.pass_count + report.watch_count + report.block_count
    ):
        raise ValueError("status counts must match source_category_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_reason_counts = (
            ResearchStrategyInformationSourceYieldCurveReasonCodeCount(
                reason_code=REASON_EMPTY_INPUT,
                count=_ONE,
                row_ratio=_ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")
    if report.average_expected_information_yield_score != _average_ratio(
        tuple(row.expected_information_yield_score for row in report.rows),
    ):
        raise ValueError("average_expected_information_yield_score must match rows")
    if report.highest_expected_information_yield_score != max(
        (row.expected_information_yield_score for row in report.rows),
        default=_ZERO,
    ):
        raise ValueError("highest_expected_information_yield_score must match rows")
    if report.average_freshness_yield_score != _average_ratio(
        tuple(row.freshness_yield_score for row in report.rows),
    ):
        raise ValueError("average_freshness_yield_score must match rows")
    if report.average_authority_confidence_score != _average_ratio(
        tuple(row.authority_confidence_score for row in report.rows),
    ):
        raise ValueError("average_authority_confidence_score must match rows")
    if report.average_conflict_reduction_score != _average_ratio(
        tuple(row.conflict_reduction_score for row in report.rows),
    ):
        raise ValueError("average_conflict_reduction_score must match rows")
    if report.average_review_effort_score != _average_ratio(
        tuple(row.review_effort_score for row in report.rows),
    ):
        raise ValueError("average_review_effort_score must match rows")


def _reason_code_counts(
    rows: tuple[ResearchStrategyInformationSourceYieldCurveRow, ...],
) -> tuple[ResearchStrategyInformationSourceYieldCurveReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _decimal_count(len(rows))
    return tuple(
        ResearchStrategyInformationSourceYieldCurveReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
            row_ratio=_safe_divide(_decimal_count(counts[reason_code]), denominator),
        )
        for reason_code in sorted(counts)
    )


def _status_count(
    rows: tuple[ResearchStrategyInformationSourceYieldCurveRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _safe_divide(sum(values, _ZERO), _decimal_count(len(values)))


def _age_hours(earlier: datetime, later: datetime) -> Decimal:
    delta = later - earlier
    if delta.days < 0:
        raise ValueError("observation age must be nonnegative")
    seconds = Decimal(delta.days * 86400 + delta.seconds)
    if delta.microseconds:
        seconds += Decimal(delta.microseconds) / _MICROSECOND_DIVISOR
    return _quantize(seconds / _SECONDS_PER_HOUR)


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    return _quantize(numerator / denominator)


def _inverse_ratio(value: Decimal) -> Decimal:
    return _quantize(_ONE - value)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < _ZERO:
        return _ZERO
    if normalized > _ONE:
        return _ONE
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a nonnegative int")
    return Decimal(value).quantize(_QUANT)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _require_positive_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized <= _ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    normalized = _quantize(value)
    if normalized < _ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(_QUANT):
        raise ValueError(f"{name} must be a whole-count Decimal")
    return normalized


def _require_public_identifier(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a str")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{name} contains unsafe public text")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public identifier")
    return value


def _require_digest(name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a digest")
    if not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a digest")
    return value


def _require_status(name: str, value: object) -> str:
    if type(value) is not str or value not in _STATUS_VALUES:
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_reason_code(name: str, value: object, allowed: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{name} must be an allowed reason code")
    return value


def _normalize_reason_codes(
    name: str,
    values: Sequence[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence") from exc
    for value in normalized:
        _require_reason_code(name, value, allowed)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    order = {code: index for index, code in enumerate(allowed)}
    return tuple(sorted(normalized, key=order.__getitem__))


def _normalize_report_reason_codes(
    name: str,
    values: Sequence[str],
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{name} must be a sequence")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError(f"{name} must be a sequence") from exc
    for value in normalized:
        _require_reason_code(name, value, _REPORT_REASON_CODE_SEQUENCE)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    if tuple(sorted(normalized)) != normalized:
        raise ValueError(f"{name} must use deterministic sequence")
    return normalized


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _digest_from_dataclass(value: object) -> str:
    return _digest_from_mapping(_json_ready(value, omit_digest=True))


def _digest_from_mapping(value: object) -> str:
    encoded = json.dumps(
        _json_ready(value, omit_digest=True),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: object, *, omit_digest: bool) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), omit_digest=omit_digest)
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool) or value is None:
        return value
    if isinstance(value, int):
        raise ValueError("numeric payload values must use Decimal")
    if isinstance(value, float):
        raise ValueError("numeric payload values must use Decimal")
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if omit_digest and key == _DIGEST_FIELD:
                continue
            ready[key] = _json_ready(item, omit_digest=omit_digest)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item, omit_digest=omit_digest) for item in value]
    if isinstance(value, list):
        return [_json_ready(item, omit_digest=omit_digest) for item in value]
    raise ValueError("value is not JSON serializable")


def _validate_payload_statuses(payload: dict[str, object]) -> None:
    _require_status("payload.status", payload.get("status"))
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _require_status(f"payload.rows[{index}].status", row.get("status"))


def _validate_payload_digest(payload: dict[str, object]) -> None:
    _validate_one_payload_digest("payload", payload)
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _validate_one_payload_digest(f"payload.rows[{index}]", row)


def _validate_one_payload_digest(label: str, payload: dict[str, object]) -> None:
    provided = payload.get(_DIGEST_FIELD)
    _require_digest(f"{label}.{_DIGEST_FIELD}", provided)
    digest_input = dict(payload)
    digest_input.pop(_DIGEST_FIELD, None)
    expected = _digest_from_mapping(digest_input)
    if provided != expected:
        raise ValueError("validation_digest does not match public payload")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(
            label,
            asdict(value),
            allow_json_containers=allow_json_containers,
        )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{label}.{key} must be True")
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, tuple) or (allow_json_containers and isinstance(value, list)):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                f"{label}[{index}]",
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, list):
        raise ValueError(f"{label} must use immutable sequences")
    if type(value) is str:
        if _DIGEST_RE.fullmatch(value):
            return
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, float):
        raise ValueError(f"{label} must not contain floats")


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.casefold()
    return any(fragment in normalized for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_INFORMATION_SOURCE_YIELD_CURVE_REPORT_CONFIG_VERSION",
    "ResearchStrategyInformationSourceYieldCurveConfig",
    "ResearchStrategyInformationSourceYieldCurveInput",
    "ResearchStrategyInformationSourceYieldCurveReasonCodeCount",
    "ResearchStrategyInformationSourceYieldCurveReport",
    "ResearchStrategyInformationSourceYieldCurveRow",
    "build_research_strategy_information_source_yield_curve_report",
    "research_strategy_information_source_yield_curve_report_public_payload",
)
