"""Pure report-only source memory authority floor reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime, timedelta
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION = (
    "research-strategy-source-memory-authority-floor-report-v0"
)

SOURCE_MEMORY_AUTHORITY_FLOOR_STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

NO_INPUTS_REASON = "no_source_memory_authority_inputs"
PASS_REASON = "source_memory_authority_floor_pass"
WATCH_REASON = "source_memory_authority_floor_watch"
BLOCK_REASON = "source_memory_authority_floor_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    BLOCK_REASON,
    "memory_signal_strength_block",
    "authority_score_block",
    "memory_age_block",
    "corroboration_count_block",
    "contradiction_pressure_block",
    WATCH_REASON,
    "memory_signal_strength_watch",
    "authority_score_watch",
    "memory_age_watch",
    "corroboration_count_watch",
    "contradiction_pressure_watch",
    PASS_REASON,
)

PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
DECIMAL_STRING_RE = re.compile(r"^[0-9]+\.[0-9]{6}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate://",
    "candidate_ref",
    "market_id",
    "market_slug",
    "market=",
    "source_url",
    "source_text",
    "raw_text",
    "http://",
    "https://",
    "www.",
    "dsn",
    "postgres://",
    "table",
    "token",
)

TOP_LEVEL_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_authority_floor_score",
        "min_memory_signal_strength",
        "min_authority_score",
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
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "row_label",
        "public_research_bucket",
        "memory_signal_strength",
        "authority_score",
        "memory_age_seconds",
        "freshness_score",
        "corroboration_count",
        "corroboration_score",
        "contradiction_pressure",
        "authority_floor_score",
        "status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
REASON_COUNT_PAYLOAD_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "row_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)

__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION",
    "SOURCE_MEMORY_AUTHORITY_FLOOR_STATUSES",
    "ResearchStrategySourceMemoryAuthorityFloorConfig",
    "ResearchStrategySourceMemoryAuthorityFloorInput",
    "ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount",
    "ResearchStrategySourceMemoryAuthorityFloorReport",
    "ResearchStrategySourceMemoryAuthorityFloorRow",
    "build_research_strategy_source_memory_authority_floor_report",
    "research_strategy_source_memory_authority_floor_report_digest",
    "research_strategy_source_memory_authority_floor_report_payload",
    "validate_research_strategy_source_memory_authority_floor_report_payload",
)


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceMemoryAuthorityFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
    )
    min_pass_memory_signal_strength: Decimal = Decimal("0.750000")
    min_watch_memory_signal_strength: Decimal = Decimal("0.500000")
    min_pass_authority_score: Decimal = Decimal("0.800000")
    min_watch_authority_score: Decimal = Decimal("0.550000")
    max_pass_memory_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("259200.000000")
    max_pass_contradiction_pressure: Decimal = Decimal("0.150000")
    max_watch_contradiction_pressure: Decimal = Decimal("0.350000")
    min_pass_corroboration_count: Decimal = Decimal("2.000000")
    min_watch_corroboration_count: Decimal = Decimal("1.000000")
    memory_signal_weight: Decimal = Decimal("0.300000")
    authority_score_weight: Decimal = Decimal("0.300000")
    freshness_weight: Decimal = Decimal("0.150000")
    corroboration_weight: Decimal = Decimal("0.150000")
    contradiction_relief_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMemoryAuthorityFloorConfig:
            raise TypeError(
                "ResearchStrategySourceMemoryAuthorityFloorConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMemoryAuthorityFloorConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_memory_signal_strength",
            "min_watch_memory_signal_strength",
            "min_pass_authority_score",
            "min_watch_authority_score",
            "max_pass_contradiction_pressure",
            "max_watch_contradiction_pressure",
            "memory_signal_weight",
            "authority_score_weight",
            "freshness_weight",
            "corroboration_weight",
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
            "min_pass_corroboration_count",
            "min_watch_corroboration_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_count_or_amount(field_name, getattr(self, field_name)),
            )
        if self.min_watch_memory_signal_strength > self.min_pass_memory_signal_strength:
            raise ValueError("memory signal watch threshold must not exceed pass threshold")
        if self.min_watch_authority_score > self.min_pass_authority_score:
            raise ValueError("authority score watch threshold must not exceed pass threshold")
        if self.max_pass_memory_age_seconds > self.max_watch_memory_age_seconds:
            raise ValueError("memory age pass threshold must not exceed watch threshold")
        if self.max_pass_contradiction_pressure > self.max_watch_contradiction_pressure:
            raise ValueError(
                "contradiction pressure pass threshold must not exceed watch threshold",
            )
        if self.min_watch_corroboration_count > self.min_pass_corroboration_count:
            raise ValueError("corroboration watch threshold must not exceed pass threshold")
        weight_sum = _quantize(
            self.memory_signal_weight
            + self.authority_score_weight
            + self.freshness_weight
            + self.corroboration_weight
            + self.contradiction_relief_weight,
        )
        if weight_sum != ONE:
            raise ValueError("floor score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceMemoryAuthorityFloorInput:
    private_candidate_ref: str
    public_research_bucket: str
    memory_signal_strength: Decimal
    authority_score: Decimal
    memory_age_seconds: Decimal
    corroboration_count: Decimal
    contradiction_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMemoryAuthorityFloorInput:
            raise TypeError(
                "ResearchStrategySourceMemoryAuthorityFloorInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMemoryAuthorityFloorInput, "input")
        _require_private_string("private_candidate_ref", self.private_candidate_ref)
        _require_public_identifier("public_research_bucket", self.public_research_bucket)
        for field_name in (
            "memory_signal_strength",
            "authority_score",
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
            _normalize_nonnegative_amount("memory_age_seconds", self.memory_age_seconds),
        )
        object.__setattr__(
            self,
            "corroboration_count",
            _normalize_nonnegative_count("corroboration_count", self.corroboration_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceMemoryAuthorityFloorRow:
    row_label: str
    public_research_bucket: str
    memory_signal_strength: Decimal
    authority_score: Decimal
    memory_age_seconds: Decimal
    freshness_score: Decimal
    corroboration_count: Decimal
    corroboration_score: Decimal
    contradiction_pressure: Decimal
    authority_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMemoryAuthorityFloorRow:
            raise TypeError(
                "ResearchStrategySourceMemoryAuthorityFloorRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMemoryAuthorityFloorRow, "row")
        _require_public_identifier("row_label", self.row_label)
        if not self.row_label.startswith("redacted-source-memory-authority-floor-"):
            raise ValueError("row_label must be redacted")
        _require_public_identifier("public_research_bucket", self.public_research_bucket)
        for field_name in (
            "memory_signal_strength",
            "authority_score",
            "freshness_score",
            "corroboration_score",
            "contradiction_pressure",
            "authority_floor_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _normalize_nonnegative_amount("memory_age_seconds", self.memory_age_seconds),
        )
        object.__setattr__(
            self,
            "corroboration_count",
            _normalize_nonnegative_count("corroboration_count", self.corroboration_count),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount:
            raise TypeError(
                "ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount "
                "does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True, slots=True)
class ResearchStrategySourceMemoryAuthorityFloorReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_authority_floor_score: Decimal | None
    min_memory_signal_strength: Decimal
    min_authority_score: Decimal
    max_memory_age_seconds: Decimal
    max_contradiction_pressure: Decimal
    status: str
    rows: tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...]
    reason_code_counts: tuple[
        ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount,
        ...,
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchStrategySourceMemoryAuthorityFloorReport:
            raise TypeError(
                "ResearchStrategySourceMemoryAuthorityFloorReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategySourceMemoryAuthorityFloorReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_authority_floor_score",
            _normalize_optional_probability(
                "average_authority_floor_score",
                self.average_authority_floor_score,
            ),
        )
        for field_name in (
            "min_memory_signal_strength",
            "min_authority_score",
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
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        _require_digest("derived_validation_digest", self.derived_validation_digest)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_strategy_source_memory_authority_floor_report_payload(self)


def build_research_strategy_source_memory_authority_floor_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategySourceMemoryAuthorityFloorConfig,
    generated_at: datetime,
) -> ResearchStrategySourceMemoryAuthorityFloorReport:
    if type(config) is not ResearchStrategySourceMemoryAuthorityFloorConfig:
        raise ValueError(
            "config must be a ResearchStrategySourceMemoryAuthorityFloorConfig",
        )
    config = _revalidate_config(config)
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in input_items),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategySourceMemoryAuthorityFloorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_authority_floor_score=_average_row_value(rows, "authority_floor_score"),
        min_memory_signal_strength=_minimum_row_value(rows, "memory_signal_strength"),
        min_authority_score=_minimum_row_value(rows, "authority_score"),
        max_memory_age_seconds=_maximum_row_value(rows, "memory_age_seconds"),
        max_contradiction_pressure=_maximum_row_value(rows, "contradiction_pressure"),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_source_memory_authority_floor_report_payload(
    report: ResearchStrategySourceMemoryAuthorityFloorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategySourceMemoryAuthorityFloorReport:
        raise ValueError(
            "report must be a ResearchStrategySourceMemoryAuthorityFloorReport",
        )
    _require_hard_flags("report", report)
    _validate_materialized_report(report)
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _validate_public_payload(payload)
    _validate_payload_shape(payload)
    return payload


def research_strategy_source_memory_authority_floor_report_digest(
    report: ResearchStrategySourceMemoryAuthorityFloorReport,
) -> str:
    payload = research_strategy_source_memory_authority_floor_report_payload(report)
    digest = payload["derived_validation_digest"]
    if type(digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    _require_digest("derived_validation_digest", digest)
    return digest


def validate_research_strategy_source_memory_authority_floor_report_payload(
    payload: object,
) -> bool:
    if not isinstance(payload, dict):
        return False
    try:
        _validate_public_payload(payload)
        _validate_payload_shape(payload)
        _revalidate_payload(payload)
        digest = payload.get("derived_validation_digest")
        if type(digest) is not str:
            return False
        _require_digest("derived_validation_digest", digest)
        unsigned = dict(payload)
        unsigned.pop("derived_validation_digest")
        encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":"))
        return sha256(encoded.encode("utf-8")).hexdigest() == digest
    except (TypeError, ValueError):
        return False


def _row_from_input(
    item: ResearchStrategySourceMemoryAuthorityFloorInput,
    *,
    config: ResearchStrategySourceMemoryAuthorityFloorConfig,
) -> ResearchStrategySourceMemoryAuthorityFloorRow:
    freshness_score = _freshness_score(item.memory_age_seconds, config)
    corroboration_score = _corroboration_score(item.corroboration_count, config)
    authority_floor_score = _authority_floor_score(
        memory_signal_strength=item.memory_signal_strength,
        authority_score=item.authority_score,
        freshness_score=freshness_score,
        corroboration_score=corroboration_score,
        contradiction_pressure=item.contradiction_pressure,
        config=config,
    )
    status = _row_status(item, config=config)
    return ResearchStrategySourceMemoryAuthorityFloorRow(
        row_label=(
            "redacted-source-memory-authority-floor-"
            f"{_private_ref_digest(item.private_candidate_ref)[:16]}"
        ),
        public_research_bucket=item.public_research_bucket,
        memory_signal_strength=item.memory_signal_strength,
        authority_score=item.authority_score,
        memory_age_seconds=item.memory_age_seconds,
        freshness_score=freshness_score,
        corroboration_count=item.corroboration_count,
        corroboration_score=corroboration_score,
        contradiction_pressure=item.contradiction_pressure,
        authority_floor_score=authority_floor_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _freshness_score(
    memory_age_seconds: Decimal,
    config: ResearchStrategySourceMemoryAuthorityFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = ONE - (memory_age_seconds / config.max_watch_memory_age_seconds)
    if score < ZERO:
        return ZERO
    if score > ONE:
        return ONE
    return _quantize(score)


def _corroboration_score(
    corroboration_count: Decimal,
    config: ResearchStrategySourceMemoryAuthorityFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = corroboration_count / config.min_pass_corroboration_count
    if score > ONE:
        return ONE
    return _quantize(score)


def _authority_floor_score(
    *,
    memory_signal_strength: Decimal,
    authority_score: Decimal,
    freshness_score: Decimal,
    corroboration_score: Decimal,
    contradiction_pressure: Decimal,
    config: ResearchStrategySourceMemoryAuthorityFloorConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            memory_signal_strength * config.memory_signal_weight
            + authority_score * config.authority_score_weight
            + freshness_score * config.freshness_weight
            + corroboration_score * config.corroboration_weight
            + (ONE - contradiction_pressure) * config.contradiction_relief_weight
        )
    return _quantize(value)


def _row_status(
    item: ResearchStrategySourceMemoryAuthorityFloorInput,
    *,
    config: ResearchStrategySourceMemoryAuthorityFloorConfig,
) -> str:
    if (
        item.memory_signal_strength < config.min_watch_memory_signal_strength
        or item.authority_score < config.min_watch_authority_score
        or item.memory_age_seconds > config.max_watch_memory_age_seconds
        or item.corroboration_count < config.min_watch_corroboration_count
        or item.contradiction_pressure > config.max_watch_contradiction_pressure
    ):
        return "block"
    if (
        item.memory_signal_strength < config.min_pass_memory_signal_strength
        or item.authority_score < config.min_pass_authority_score
        or item.memory_age_seconds > config.max_pass_memory_age_seconds
        or item.corroboration_count < config.min_pass_corroboration_count
        or item.contradiction_pressure > config.max_pass_contradiction_pressure
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategySourceMemoryAuthorityFloorInput,
    *,
    status: str,
    config: ResearchStrategySourceMemoryAuthorityFloorConfig,
) -> tuple[str, ...]:
    codes = {
        f"source_memory_authority_floor_{status}",
        f"memory_signal_strength_{_minimum_status(item.memory_signal_strength, config.min_pass_memory_signal_strength, config.min_watch_memory_signal_strength)}",
        f"authority_score_{_minimum_status(item.authority_score, config.min_pass_authority_score, config.min_watch_authority_score)}",
        f"memory_age_{_maximum_status(item.memory_age_seconds, config.max_pass_memory_age_seconds, config.max_watch_memory_age_seconds)}",
        f"corroboration_count_{_minimum_status(item.corroboration_count, config.min_pass_corroboration_count, config.min_watch_corroboration_count)}",
        f"contradiction_pressure_{_maximum_status(item.contradiction_pressure, config.max_pass_contradiction_pressure, config.max_watch_contradiction_pressure)}",
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _minimum_status(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value < watch_threshold:
        return "block"
    if value < pass_threshold:
        return "watch"
    return "pass"


def _maximum_status(value: Decimal, pass_threshold: Decimal, watch_threshold: Decimal) -> str:
    if value > watch_threshold:
        return "block"
    if value > pass_threshold:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategySourceMemoryAuthorityFloorInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> ResearchStrategySourceMemoryAuthorityFloorInput:
    if type(value) is ResearchStrategySourceMemoryAuthorityFloorInput:
        return _revalidate_input(value)
    raise ValueError("inputs must contain ResearchStrategySourceMemoryAuthorityFloorInput")


def _revalidate_config(
    config: ResearchStrategySourceMemoryAuthorityFloorConfig,
) -> ResearchStrategySourceMemoryAuthorityFloorConfig:
    if type(config) is not ResearchStrategySourceMemoryAuthorityFloorConfig:
        raise ValueError(
            "config must be a ResearchStrategySourceMemoryAuthorityFloorConfig",
        )
    return ResearchStrategySourceMemoryAuthorityFloorConfig(
        **{field.name: getattr(config, field.name) for field in fields(config)},
    )


def _revalidate_input(
    value: ResearchStrategySourceMemoryAuthorityFloorInput,
) -> ResearchStrategySourceMemoryAuthorityFloorInput:
    if type(value) is not ResearchStrategySourceMemoryAuthorityFloorInput:
        raise ValueError(
            "input must be a ResearchStrategySourceMemoryAuthorityFloorInput",
        )
    return ResearchStrategySourceMemoryAuthorityFloorInput(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _normalize_rows(
    rows: object,
) -> tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchStrategySourceMemoryAuthorityFloorRow] = []
    for row in rows:
        if type(row) is not ResearchStrategySourceMemoryAuthorityFloorRow:
            raise ValueError("rows must contain ResearchStrategySourceMemoryAuthorityFloorRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    sorted_rows = tuple(sorted(normalized, key=_row_sort_key))
    if tuple(normalized) != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return sorted_rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        normalized.append(count)
    sorted_counts = tuple(sorted(normalized, key=lambda count: _reason_sort_key(count.reason_code)))
    if tuple(normalized) != sorted_counts:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return sorted_counts


def _summary_reason_codes(
    rows: tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    present = {
        code
        for row in rows
        for code in row.reason_codes
        if not code.startswith("input_")
    }
    if any(row.status != "pass" for row in rows):
        present.discard(PASS_REASON)
        present = {code for code in present if not code.endswith("_pass")}
    return tuple(sorted(present, key=_reason_sort_key))


def _summary_status(
    rows: tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...],
) -> str:
    if not rows or any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter(
        code for row in rows for code in row.reason_codes if code in reason_codes
    )
    total = _decimal_count(len(rows))
    return tuple(
        ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_ratio(_decimal_count(counter[reason_code]), total),
        )
        for reason_code in reason_codes
        if counter[reason_code] > 0
    )


def _status_count(
    rows: tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _row_sort_key(
    row: ResearchStrategySourceMemoryAuthorityFloorRow,
) -> tuple[str, int, str]:
    return (
        row.public_research_bucket,
        SOURCE_MEMORY_AUTHORITY_FLOOR_STATUSES.index(row.status),
        row.row_label,
    )


def _average_row_value(
    rows: tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((getattr(row, field_name) for row in rows), ZERO) / Decimal(len(rows)))


def _minimum_row_value(
    rows: tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchStrategySourceMemoryAuthorityFloorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _validate_row_consistency(row: ResearchStrategySourceMemoryAuthorityFloorRow) -> None:
    expected_status_codes = tuple(
        code
        for code in row.reason_codes
        if code
        in {
            PASS_REASON,
            WATCH_REASON,
            BLOCK_REASON,
        }
    )
    if expected_status_codes != (f"source_memory_authority_floor_{row.status}",):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchStrategySourceMemoryAuthorityFloorReport,
) -> None:
    rows = report.rows
    expected_input_count = _decimal_count(len(rows))
    if report.input_count != expected_input_count:
        raise ValueError("input_count must match rows")
    expected_counts = {
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
    }
    for field_name, expected in expected_counts.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.average_authority_floor_score != _average_row_value(
        rows,
        "authority_floor_score",
    ):
        raise ValueError("average_authority_floor_score must match rows")
    if report.min_memory_signal_strength != _minimum_row_value(
        rows,
        "memory_signal_strength",
    ):
        raise ValueError("min_memory_signal_strength must match rows")
    if report.min_authority_score != _minimum_row_value(rows, "authority_score"):
        raise ValueError("min_authority_score must match rows")
    if report.max_memory_age_seconds != _maximum_row_value(rows, "memory_age_seconds"):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.max_contradiction_pressure != _maximum_row_value(
        rows,
        "contradiction_pressure",
    ):
        raise ValueError("max_contradiction_pressure must match rows")
    if report.status != _summary_status(rows):
        raise ValueError("status must match rows")
    expected_reason_codes = _summary_reason_codes(rows)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, expected_reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _payload_value(value: object) -> Any:
    if is_dataclass(value):
        return {item.name: _payload_value(getattr(value, item.name)) for item in fields(value)}
    if type(value) is Decimal:
        return _format_decimal(value)
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    if type(value) in {str, bool} or value is None:
        return value
    raise ValueError(f"unsupported payload value type: {type(value).__name__}")


def _report_digest(report: ResearchStrategySourceMemoryAuthorityFloorReport) -> str:
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _validate_public_payload(payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_public_payload(value: Any, *, label: str = "payload") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} keys must be strings")
            _reject_unsafe_public_string(f"{label} key", key)
            _validate_public_payload(item, label=key)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_payload(item, label=label)
        return
    if type(value) in {int, float, Decimal}:
        raise ValueError(f"{label} must not contain raw numeric values")
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if type(value) is bool or value is None:
        return
    raise ValueError(f"{label} contains unsupported public value")


def _validate_payload_shape(payload: dict[str, Any]) -> None:
    if frozenset(payload) != TOP_LEVEL_PAYLOAD_FIELDS:
        raise ValueError("payload has unexpected fields")
    _require_payload_flags(payload)
    _require_canonical_datetime_string("generated_at", payload["generated_at"])
    _require_supported_config_version(payload["config_version"])
    _require_status("status", payload["status"])
    _require_digest("derived_validation_digest", payload["derived_validation_digest"])
    for field_name in (
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "min_memory_signal_strength",
        "min_authority_score",
        "max_memory_age_seconds",
        "max_contradiction_pressure",
    ):
        _require_decimal_string(field_name, payload[field_name])
    if payload["average_authority_floor_score"] is not None:
        _require_decimal_string(
            "average_authority_floor_score",
            payload["average_authority_floor_score"],
        )
    _require_reason_code_list("reason_codes", payload["reason_codes"], allow_empty=False)
    if type(payload["rows"]) is not list:
        raise ValueError("rows must be a list")
    for row in payload["rows"]:
        _validate_row_payload_shape(row)
    if type(payload["reason_code_counts"]) is not list:
        raise ValueError("reason_code_counts must be a list")
    for count in payload["reason_code_counts"]:
        _validate_reason_count_payload_shape(count)


def _validate_row_payload_shape(row: object) -> None:
    if not isinstance(row, dict) or frozenset(row) != ROW_PAYLOAD_FIELDS:
        raise ValueError("row payload has unexpected fields")
    _require_payload_flags(row)
    _require_public_identifier("row_label", row["row_label"])
    if not row["row_label"].startswith("redacted-source-memory-authority-floor-"):
        raise ValueError("row_label must be redacted")
    _require_public_identifier("public_research_bucket", row["public_research_bucket"])
    _require_status("status", row["status"])
    for field_name in (
        "memory_signal_strength",
        "authority_score",
        "memory_age_seconds",
        "freshness_score",
        "corroboration_count",
        "corroboration_score",
        "contradiction_pressure",
        "authority_floor_score",
    ):
        _require_decimal_string(field_name, row[field_name])
    _require_reason_code_list(
        "row reason_codes",
        row["reason_codes"],
        allow_empty=False,
    )


def _validate_reason_count_payload_shape(count: object) -> None:
    if not isinstance(count, dict) or frozenset(count) != REASON_COUNT_PAYLOAD_FIELDS:
        raise ValueError("reason count payload has unexpected fields")
    _require_payload_flags(count)
    _require_reason_code("reason_code", count["reason_code"])
    _require_decimal_string("count", count["count"])
    _require_decimal_string("row_ratio", count["row_ratio"])


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_reason_code_list(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    for reason_code in value:
        _require_reason_code(field_name, reason_code)
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must be nonempty")
    normalized = _normalize_reason_codes(
        field_name,
        tuple(value),
        allow_empty=allow_empty,
    )
    if value != list(normalized):
        raise ValueError(f"{field_name} must be deterministically ordered")


def _require_decimal_string(field_name: str, value: object) -> None:
    if type(value) is not str or not DECIMAL_STRING_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a canonical Decimal string")


def _require_canonical_datetime_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    if parsed.utcoffset() != timedelta(0) or parsed.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")


def _require_supported_config_version(value: object) -> None:
    _require_public_identifier("config_version", value)
    if (
        value
        != DEFAULT_RESEARCH_STRATEGY_SOURCE_MEMORY_AUTHORITY_FLOOR_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")


def _revalidate_payload(payload: dict[str, Any]) -> None:
    rows = tuple(
        ResearchStrategySourceMemoryAuthorityFloorRow(
            row_label=row["row_label"],
            public_research_bucket=row["public_research_bucket"],
            memory_signal_strength=Decimal(row["memory_signal_strength"]),
            authority_score=Decimal(row["authority_score"]),
            memory_age_seconds=Decimal(row["memory_age_seconds"]),
            freshness_score=Decimal(row["freshness_score"]),
            corroboration_count=Decimal(row["corroboration_count"]),
            corroboration_score=Decimal(row["corroboration_score"]),
            contradiction_pressure=Decimal(row["contradiction_pressure"]),
            authority_floor_score=Decimal(row["authority_floor_score"]),
            status=row["status"],
            reason_codes=tuple(row["reason_codes"]),
        )
        for row in payload["rows"]
    )
    reason_code_counts = tuple(
        ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount(
            reason_code=count["reason_code"],
            count=Decimal(count["count"]),
            row_ratio=Decimal(count["row_ratio"]),
        )
        for count in payload["reason_code_counts"]
    )
    ResearchStrategySourceMemoryAuthorityFloorReport(
        generated_at=datetime.fromisoformat(payload["generated_at"]),
        config_version=payload["config_version"],
        input_count=Decimal(payload["input_count"]),
        pass_count=Decimal(payload["pass_count"]),
        watch_count=Decimal(payload["watch_count"]),
        block_count=Decimal(payload["block_count"]),
        average_authority_floor_score=(
            None
            if payload["average_authority_floor_score"] is None
            else Decimal(payload["average_authority_floor_score"])
        ),
        min_memory_signal_strength=Decimal(payload["min_memory_signal_strength"]),
        min_authority_score=Decimal(payload["min_authority_score"]),
        max_memory_age_seconds=Decimal(payload["max_memory_age_seconds"]),
        max_contradiction_pressure=Decimal(payload["max_contradiction_pressure"]),
        status=payload["status"],
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=tuple(payload["reason_codes"]),
        derived_validation_digest=payload["derived_validation_digest"],
    )


def _validate_materialized_report(
    report: ResearchStrategySourceMemoryAuthorityFloorReport,
) -> None:
    if type(report.generated_at) is not datetime:
        raise ValueError("generated_at must be a datetime")
    if report.generated_at.tzinfo is not UTC:
        raise ValueError("generated_at must be canonical UTC")
    _require_supported_config_version(report.config_version)
    for field_name in (
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "min_memory_signal_strength",
        "min_authority_score",
        "max_memory_age_seconds",
        "max_contradiction_pressure",
    ):
        _require_materialized_decimal(field_name, getattr(report, field_name))
    if report.average_authority_floor_score is not None:
        _require_materialized_decimal(
            "average_authority_floor_score",
            report.average_authority_floor_score,
        )
    if type(report.rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in report.rows:
        if type(row) is not ResearchStrategySourceMemoryAuthorityFloorRow:
            raise ValueError("rows must contain ResearchStrategySourceMemoryAuthorityFloorRow")
        _require_hard_flags("row", row)
        for field_name in (
            "memory_signal_strength",
            "authority_score",
            "memory_age_seconds",
            "freshness_score",
            "corroboration_count",
            "corroboration_score",
            "contradiction_pressure",
            "authority_floor_score",
        ):
            _require_materialized_decimal(field_name, getattr(row, field_name))
        if type(row.reason_codes) is not tuple:
            raise ValueError("row reason_codes must be a tuple")
    if type(report.reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in report.reason_code_counts:
        if type(count) is not ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySourceMemoryAuthorityFloorReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        _require_materialized_decimal("count", count.count)
        _require_materialized_decimal("row_ratio", count.row_ratio)
    if type(report.reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    _require_status("status", report.status)
    _require_digest("derived_validation_digest", report.derived_validation_digest)


def _require_materialized_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError(f"{field_name} must be a finite Decimal")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    if value.as_tuple().exponent != QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must be quantized to six decimal places")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    _validate_public_payload(_payload_value(value), label=label)


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")


def _private_ref_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)


def _require_private_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{field_name} must be a nonempty string")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a reason code")
    _reject_unsafe_public_string(field_name, value)


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized), key=_reason_sort_key))


def _reason_sort_key(reason_code: str) -> tuple[int, str]:
    try:
        return (REASON_CODE_SEQUENCE.index(reason_code), reason_code)
    except ValueError:
        return (len(REASON_CODE_SEQUENCE), reason_code)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in SOURCE_MEMORY_AUTHORITY_FLOOR_STATUSES:
        raise ValueError(f"{field_name} must be one of {SOURCE_MEMORY_AUTHORITY_FLOOR_STATUSES}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    with localcontext(DECIMAL_CONTEXT):
        normalized = (+value).quantize(QUANTUM)
    if normalized.is_zero() and normalized.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_optional_probability(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _normalize_probability(field_name, value)


def _normalize_nonnegative_amount(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_count_or_amount(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_amount(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_positive_count_or_amount(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count source must be a nonnegative int")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        normalized = value.quantize(QUANTUM)
    return ZERO if normalized.is_zero() else normalized


def _format_decimal(value: Decimal) -> str:
    return f"{_quantize(value):.6f}"


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
