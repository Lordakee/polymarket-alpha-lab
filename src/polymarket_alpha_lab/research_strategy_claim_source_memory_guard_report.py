"""Pure claim-source memory guard report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_UP, localcontext
import hashlib
import json
from typing import Any, final


__all__ = (
    "CLAIM_SOURCE_MEMORY_GUARD_STATUSES",
    "DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_MEMORY_GUARD_REPORT_CONFIG_VERSION",
    "ResearchStrategyClaimSourceMemoryGuardConfig",
    "ResearchStrategyClaimSourceMemoryGuardInput",
    "ResearchStrategyClaimSourceMemoryGuardReasonCodeCount",
    "ResearchStrategyClaimSourceMemoryGuardReport",
    "ResearchStrategyClaimSourceMemoryGuardRow",
    "build_research_strategy_claim_source_memory_guard_report",
    "research_strategy_claim_source_memory_guard_report_digest",
    "research_strategy_claim_source_memory_guard_report_public_payload",
    "validate_research_strategy_claim_source_memory_guard_report_payload_digest",
)


DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_MEMORY_GUARD_REPORT_CONFIG_VERSION = (
    "research-strategy-claim-source-memory-guard-report-v0"
)
CLAIM_SOURCE_MEMORY_GUARD_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)
HEX_CHARS = frozenset("0123456789abcdef")
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}
COMPONENT_REASON_PRIORITY = (
    "fresh_memory_score_block",
    "source_overlap_ratio_block",
    "distinct_source_count_block",
    "memory_age_block",
    "fresh_memory_score_watch",
    "source_overlap_ratio_watch",
    "distinct_source_count_watch",
    "memory_age_watch",
)
PRIVATE_PUBLIC_FRAGMENTS = (
    "raw",
    "http",
    "://",
    "secret",
    "private",
    "candi" + "date",
    "market",
    "url",
    "text",
    "d" + "sn",
    "ta" + "ble",
    "tok" + "en",
)


class _Missing:
    pass


_MISSING = _Missing()


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceMemoryGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_MEMORY_GUARD_REPORT_CONFIG_VERSION
    )
    min_pass_fresh_memory_score: Decimal = Decimal("0.750000")
    min_watch_fresh_memory_score: Decimal = Decimal("0.500000")
    max_pass_source_overlap_ratio: Decimal = Decimal("0.150000")
    max_watch_source_overlap_ratio: Decimal = Decimal("0.350000")
    min_pass_distinct_source_count: Decimal = Decimal("3.000000")
    min_watch_distinct_source_count: Decimal = Decimal("2.000000")
    max_pass_memory_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_memory_age_seconds: Decimal = Decimal("259200.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchStrategyClaimSourceMemoryGuardConfig is final")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimSourceMemoryGuardConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_CLAIM_SOURCE_MEMORY_GUARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_fresh_memory_score",
            "min_watch_fresh_memory_score",
            "max_pass_source_overlap_ratio",
            "max_watch_source_overlap_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_distinct_source_count",
            "min_watch_distinct_source_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_fresh_memory_score > self.min_pass_fresh_memory_score:
            raise ValueError("min_watch_fresh_memory_score must not exceed pass value")
        if self.max_pass_source_overlap_ratio > self.max_watch_source_overlap_ratio:
            raise ValueError("max_pass_source_overlap_ratio must not exceed watch value")
        if self.min_watch_distinct_source_count > self.min_pass_distinct_source_count:
            raise ValueError("min_watch_distinct_source_count must not exceed pass value")
        if self.max_pass_memory_age_seconds > self.max_watch_memory_age_seconds:
            raise ValueError("max_pass_memory_age_seconds must not exceed watch value")
        _validate_config(self)
        _require_hard_flags("config", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceMemoryGuardInput:
    claim_digest: str
    source_memory_digest: str
    observed_at: datetime
    fresh_memory_score: Decimal
    source_overlap_ratio: Decimal
    distinct_source_count: Decimal
    memory_age_seconds: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchStrategyClaimSourceMemoryGuardInput is final")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimSourceMemoryGuardInput, "input")
        _require_hex_digest("claim_digest", self.claim_digest)
        _require_hex_digest("source_memory_digest", self.source_memory_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "fresh_memory_score",
            _require_ratio_decimal("fresh_memory_score", self.fresh_memory_score),
        )
        object.__setattr__(
            self,
            "source_overlap_ratio",
            _require_ratio_decimal("source_overlap_ratio", self.source_overlap_ratio),
        )
        object.__setattr__(
            self,
            "distinct_source_count",
            _require_nonnegative_whole_decimal(
                "distinct_source_count",
                self.distinct_source_count,
            ),
        )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceMemoryGuardRow:
    claim_digest: str
    source_memory_digest: str
    observed_at: datetime
    fresh_memory_score: Decimal
    source_overlap_ratio: Decimal
    distinct_source_count: Decimal
    memory_age_seconds: Decimal
    stale_memory_risk: Decimal
    source_coverage_score: Decimal
    memory_guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchStrategyClaimSourceMemoryGuardRow is final")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimSourceMemoryGuardRow, "row")
        _require_hex_digest("claim_digest", self.claim_digest)
        _require_hex_digest("source_memory_digest", self.source_memory_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "fresh_memory_score",
            "source_overlap_ratio",
            "stale_memory_risk",
            "source_coverage_score",
            "memory_guard_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "distinct_source_count",
            _require_nonnegative_whole_decimal(
                "distinct_source_count",
                self.distinct_source_count,
            ),
        )
        object.__setattr__(
            self,
            "memory_age_seconds",
            _require_nonnegative_decimal("memory_age_seconds", self.memory_age_seconds),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceMemoryGuardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError(
            "ResearchStrategyClaimSourceMemoryGuardReasonCodeCount is final",
        )

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@final
@dataclass(frozen=True, slots=True)
class ResearchStrategyClaimSourceMemoryGuardReport:
    generated_at: datetime
    config_version: str
    config: ResearchStrategyClaimSourceMemoryGuardConfig
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_memory_guard_score: Decimal | None
    min_fresh_memory_score: Decimal
    max_source_overlap_ratio: Decimal
    max_stale_memory_risk: Decimal
    min_distinct_source_count: Decimal
    status: str
    rows: tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...]
    reason_code_counts: tuple[ResearchStrategyClaimSourceMemoryGuardReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        raise TypeError("ResearchStrategyClaimSourceMemoryGuardReport is final")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchStrategyClaimSourceMemoryGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        object.__setattr__(self, "config", _revalidated_config(self.config))
        if self.config_version != self.config.config_version:
            raise ValueError("config_version must match config")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_memory_guard_score",
            _require_optional_ratio_decimal(
                "average_memory_guard_score",
                self.average_memory_guard_score,
            ),
        )
        for field_name in (
            "min_fresh_memory_score",
            "max_source_overlap_ratio",
            "max_stale_memory_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_distinct_source_count",
            _require_nonnegative_whole_decimal(
                "min_distinct_source_count",
                self.min_distinct_source_count,
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
        expected_digest = _expected_report_digest(self)
        if self.validation_digest:
            _require_hex_digest("validation_digest", self.validation_digest)
            if self.validation_digest != expected_digest:
                raise ValueError("validation_digest must match report payload")
        object.__setattr__(self, "validation_digest", expected_digest)


def build_research_strategy_claim_source_memory_guard_report(
    inputs: Iterable[object],
    *,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
    generated_at: datetime,
) -> ResearchStrategyClaimSourceMemoryGuardReport:
    config = _revalidated_config(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in input_items),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchStrategyClaimSourceMemoryGuardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_memory_guard_score=_average_memory_guard_score(rows),
        min_fresh_memory_score=_minimum_row_value(rows, "fresh_memory_score"),
        max_source_overlap_ratio=_maximum_row_value(rows, "source_overlap_ratio"),
        max_stale_memory_risk=_maximum_row_value(rows, "stale_memory_risk"),
        min_distinct_source_count=_minimum_row_value(rows, "distinct_source_count"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_strategy_claim_source_memory_guard_report_public_payload(
    report: ResearchStrategyClaimSourceMemoryGuardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchStrategyClaimSourceMemoryGuardReport:
        raise ValueError("report must be a ResearchStrategyClaimSourceMemoryGuardReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    _reject_private_public_payload(payload)
    if not validate_research_strategy_claim_source_memory_guard_report_payload_digest(
        payload,
    ):
        raise ValueError("validation_digest must match report payload")
    return payload


def research_strategy_claim_source_memory_guard_report_digest(
    report: ResearchStrategyClaimSourceMemoryGuardReport,
) -> str:
    if type(report) is not ResearchStrategyClaimSourceMemoryGuardReport:
        raise ValueError("report must be a ResearchStrategyClaimSourceMemoryGuardReport")
    _require_hard_flags("report", report)
    _validate_report(report)
    expected_digest = _expected_report_digest(report)
    if report.validation_digest != expected_digest:
        raise ValueError("validation_digest must match report payload")
    return report.validation_digest


def validate_research_strategy_claim_source_memory_guard_report_payload_digest(
    payload: object,
) -> bool:
    if type(payload) is not dict:
        return False
    try:
        _validate_public_payload(payload)
    except (TypeError, ValueError, InvalidOperation):
        return False
    return True


def _row_from_input(
    item: ResearchStrategyClaimSourceMemoryGuardInput,
    *,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> ResearchStrategyClaimSourceMemoryGuardRow:
    stale_memory_risk = _stale_memory_risk(item.memory_age_seconds, config)
    source_coverage_score = _source_coverage_score(item.distinct_source_count, config)
    memory_guard_score = _memory_guard_score(
        fresh_memory_score=item.fresh_memory_score,
        source_overlap_ratio=item.source_overlap_ratio,
        stale_memory_risk=stale_memory_risk,
        source_coverage_score=source_coverage_score,
    )
    status = _row_status(item, config=config)
    return ResearchStrategyClaimSourceMemoryGuardRow(
        claim_digest=item.claim_digest,
        source_memory_digest=item.source_memory_digest,
        observed_at=item.observed_at,
        fresh_memory_score=item.fresh_memory_score,
        source_overlap_ratio=item.source_overlap_ratio,
        distinct_source_count=item.distinct_source_count,
        memory_age_seconds=item.memory_age_seconds,
        stale_memory_risk=stale_memory_risk,
        source_coverage_score=source_coverage_score,
        memory_guard_score=memory_guard_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _stale_memory_risk(
    memory_age_seconds: Decimal,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        risk = memory_age_seconds / config.max_watch_memory_age_seconds
    if risk > ONE:
        return ONE
    return _quantize(risk)


def _source_coverage_score(
    distinct_source_count: Decimal,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = distinct_source_count / config.min_pass_distinct_source_count
    if score > ONE:
        return ONE
    return _quantize(score)


def _memory_guard_score(
    *,
    fresh_memory_score: Decimal,
    source_overlap_ratio: Decimal,
    stale_memory_risk: Decimal,
    source_coverage_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = (
            fresh_memory_score
            + (ONE - source_overlap_ratio)
            + (ONE - stale_memory_risk)
            + source_coverage_score
        ) / Decimal("4")
    return _quantize(score)


def _row_status(
    item: ResearchStrategyClaimSourceMemoryGuardInput,
    *,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> str:
    if (
        item.fresh_memory_score < config.min_watch_fresh_memory_score
        or item.source_overlap_ratio > config.max_watch_source_overlap_ratio
        or item.distinct_source_count < config.min_watch_distinct_source_count
        or item.memory_age_seconds > config.max_watch_memory_age_seconds
    ):
        return "block"
    if (
        item.fresh_memory_score < config.min_pass_fresh_memory_score
        or item.source_overlap_ratio > config.max_pass_source_overlap_ratio
        or item.distinct_source_count < config.min_pass_distinct_source_count
        or item.memory_age_seconds > config.max_pass_memory_age_seconds
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchStrategyClaimSourceMemoryGuardInput,
    *,
    status: str,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> tuple[str, ...]:
    codes = {
        f"claim_source_memory_guard_{status}",
        f"manual_review_claim_source_memory_{status}",
        f"fresh_memory_score_{_fresh_memory_status(item.fresh_memory_score, config)}",
        f"source_overlap_ratio_{_overlap_status(item.source_overlap_ratio, config)}",
        f"distinct_source_count_{_distinct_source_status(item.distinct_source_count, config)}",
        f"memory_age_{_memory_age_status(item.memory_age_seconds, config)}",
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _fresh_memory_status(
    value: Decimal,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> str:
    if value < config.min_watch_fresh_memory_score:
        return "block"
    if value < config.min_pass_fresh_memory_score:
        return "watch"
    return "pass"


def _overlap_status(
    value: Decimal,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> str:
    if value > config.max_watch_source_overlap_ratio:
        return "block"
    if value > config.max_pass_source_overlap_ratio:
        return "watch"
    return "pass"


def _distinct_source_status(
    value: Decimal,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> str:
    if value < config.min_watch_distinct_source_count:
        return "block"
    if value < config.min_pass_distinct_source_count:
        return "watch"
    return "pass"


def _memory_age_status(
    value: Decimal,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> str:
    if value > config.max_watch_memory_age_seconds:
        return "block"
    if value > config.max_pass_memory_age_seconds:
        return "watch"
    return "pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchStrategyClaimSourceMemoryGuardInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    return tuple(_revalidated_input(_coerce_input(value)) for value in values)


def _coerce_input(value: object) -> ResearchStrategyClaimSourceMemoryGuardInput:
    if type(value) is ResearchStrategyClaimSourceMemoryGuardInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchStrategyClaimSourceMemoryGuardInput(
        claim_digest=_field_value(value, "claim_digest"),
        source_memory_digest=_field_value(value, "source_memory_digest"),
        observed_at=_field_value(value, "observed_at"),
        fresh_memory_score=_field_value(value, "fresh_memory_score"),
        source_overlap_ratio=_field_value(value, "source_overlap_ratio"),
        distinct_source_count=_field_value(value, "distinct_source_count"),
        memory_age_seconds=_field_value(value, "memory_age_seconds"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _revalidated_config(
    value: object,
) -> ResearchStrategyClaimSourceMemoryGuardConfig:
    if type(value) is not ResearchStrategyClaimSourceMemoryGuardConfig:
        raise ValueError("config must be a ResearchStrategyClaimSourceMemoryGuardConfig")
    return ResearchStrategyClaimSourceMemoryGuardConfig(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidated_input(
    value: object,
) -> ResearchStrategyClaimSourceMemoryGuardInput:
    if type(value) is not ResearchStrategyClaimSourceMemoryGuardInput:
        raise ValueError("inputs must contain exact guard inputs")
    return ResearchStrategyClaimSourceMemoryGuardInput(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _revalidated_row(
    value: object,
) -> ResearchStrategyClaimSourceMemoryGuardRow:
    if type(value) is not ResearchStrategyClaimSourceMemoryGuardRow:
        raise ValueError("rows must contain exact guard rows")
    return ResearchStrategyClaimSourceMemoryGuardRow(
        **{field.name: getattr(value, field.name) for field in fields(value)},
    )


def _summary_reason_codes(
    rows: tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_claim_source_memory_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("claim_source_memory_guard_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("claim_source_memory_guard_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("claim_source_memory_guard_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_claim_source_memory_inputs",):
        return "block"
    if "claim_source_memory_guard_block" in reason_codes:
        return "block"
    if "claim_source_memory_guard_watch" in reason_codes:
        return "watch"
    return "pass"


def _validate_config(config: ResearchStrategyClaimSourceMemoryGuardConfig) -> None:
    if config.min_watch_fresh_memory_score > config.min_pass_fresh_memory_score:
        raise ValueError("min_watch_fresh_memory_score must not exceed pass value")
    if config.max_pass_source_overlap_ratio > config.max_watch_source_overlap_ratio:
        raise ValueError("max_pass_source_overlap_ratio must not exceed watch value")
    if config.min_watch_distinct_source_count > config.min_pass_distinct_source_count:
        raise ValueError("min_watch_distinct_source_count must not exceed pass value")
    if config.max_pass_memory_age_seconds > config.max_watch_memory_age_seconds:
        raise ValueError("max_pass_memory_age_seconds must not exceed watch value")


def _reason_code_counts(
    rows: tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchStrategyClaimSourceMemoryGuardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyClaimSourceMemoryGuardReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    with localcontext(DECIMAL_CONTEXT):
        ratios = {
            reason_code: _quantize(Decimal(count) / row_count)
            for reason_code, count in counter.items()
        }
    return tuple(
        ResearchStrategyClaimSourceMemoryGuardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=ratios[reason_code],
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_memory_guard_score(
    rows: tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            sum((row.memory_guard_score for row in rows), ZERO) / Decimal(len(rows)),
        )


def _minimum_row_value(
    rows: tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _maximum_row_value(
    rows: tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...],
) -> tuple[ResearchStrategyClaimSourceMemoryGuardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized_rows = tuple(_revalidated_row(row) for row in rows)
    expected = tuple(
        sorted(
            normalized_rows,
            key=_row_sort_key,
        ),
    )
    if normalized_rows != expected:
        raise ValueError("rows must be sorted by status and digest")
    return normalized_rows


def _row_sort_key(
    row: ResearchStrategyClaimSourceMemoryGuardRow,
) -> tuple[object, ...]:
    return (
        STATUS_RANK[row.status],
        row.claim_digest,
        row.source_memory_digest,
        row.observed_at,
        row.fresh_memory_score,
        row.source_overlap_ratio,
        row.distinct_source_count,
        row.memory_age_seconds,
        row.stale_memory_risk,
        row.source_coverage_score,
        row.memory_guard_score,
        row.reason_codes,
    )


def _normalize_reason_code_counts(
    counts: tuple[ResearchStrategyClaimSourceMemoryGuardReasonCodeCount, ...],
) -> tuple[ResearchStrategyClaimSourceMemoryGuardReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchStrategyClaimSourceMemoryGuardReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyClaimSourceMemoryGuardReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    expected = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_row_consistency(row: ResearchStrategyClaimSourceMemoryGuardRow) -> None:
    expected_score = _memory_guard_score(
        fresh_memory_score=row.fresh_memory_score,
        source_overlap_ratio=row.source_overlap_ratio,
        stale_memory_risk=row.stale_memory_risk,
        source_coverage_score=row.source_coverage_score,
    )
    if row.memory_guard_score != expected_score:
        raise ValueError("memory_guard_score must match components")
    expected_status_code = f"claim_source_memory_guard_{row.status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and any(
        code.endswith(("_watch", "_block")) for code in row.reason_codes
    ):
        raise ValueError("status must match component reason_codes")
    if row.status == "watch" and any(
        code.endswith("_block") for code in row.reason_codes
    ):
        raise ValueError("status must match component reason_codes")


def _validate_row_against_config(
    row: ResearchStrategyClaimSourceMemoryGuardRow,
    config: ResearchStrategyClaimSourceMemoryGuardConfig,
) -> None:
    input_reason_codes = tuple(
        code.removeprefix("input_")
        for code in row.reason_codes
        if code.startswith("input_")
    )
    source = ResearchStrategyClaimSourceMemoryGuardInput(
        claim_digest=row.claim_digest,
        source_memory_digest=row.source_memory_digest,
        observed_at=row.observed_at,
        fresh_memory_score=row.fresh_memory_score,
        source_overlap_ratio=row.source_overlap_ratio,
        distinct_source_count=row.distinct_source_count,
        memory_age_seconds=row.memory_age_seconds,
        reason_codes=input_reason_codes,
    )
    expected = _row_from_input(source, config=config)
    for field_name in (
        "stale_memory_risk",
        "source_coverage_score",
        "memory_guard_score",
        "status",
        "reason_codes",
    ):
        if getattr(row, field_name) != getattr(expected, field_name):
            raise ValueError(f"{field_name} must match config-derived row")


def _validate_report_consistency(
    report: ResearchStrategyClaimSourceMemoryGuardReport,
) -> None:
    config = _revalidated_config(report.config)
    for row in report.rows:
        _revalidated_row(row)
        _validate_row_against_config(row, config)
        if row.observed_at > report.generated_at:
            raise ValueError("observed_at must not be after generated_at")
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_memory_guard_score != _average_memory_guard_score(report.rows):
        raise ValueError("average_memory_guard_score must match rows")
    if report.min_fresh_memory_score != _minimum_row_value(
        report.rows,
        "fresh_memory_score",
    ):
        raise ValueError("min_fresh_memory_score must match rows")
    if report.max_source_overlap_ratio != _maximum_row_value(
        report.rows,
        "source_overlap_ratio",
    ):
        raise ValueError("max_source_overlap_ratio must match rows")
    if report.max_stale_memory_risk != _maximum_row_value(
        report.rows,
        "stale_memory_risk",
    ):
        raise ValueError("max_stale_memory_risk must match rows")
    if report.min_distinct_source_count != _minimum_row_value(
        report.rows,
        "distinct_source_count",
    ):
        raise ValueError("min_distinct_source_count must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _validate_report(report: ResearchStrategyClaimSourceMemoryGuardReport) -> None:
    if type(report) is not ResearchStrategyClaimSourceMemoryGuardReport:
        raise ValueError("report must be a ResearchStrategyClaimSourceMemoryGuardReport")
    _require_hard_flags("report", report)
    _validate_report_consistency(report)


def _public_fields(dataclass_type: type[object]) -> tuple[str, ...]:
    return tuple(field.name for field in fields(dataclass_type))


def _require_mapping_schema(
    label: str,
    value: object,
    dataclass_type: type[object],
) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be an exact dict")
    keys = tuple(value)
    if any(type(key) is not str for key in keys):
        raise ValueError(f"{label} keys must be strings")
    expected = _public_fields(dataclass_type)
    if keys != expected:
        raise ValueError(f"{label} must use the exact canonical schema")
    return value


def _validate_public_payload(payload: object) -> None:
    if type(payload) is not dict:
        raise ValueError("payload must be an exact dict")
    _require_mapping_schema("payload", payload, ResearchStrategyClaimSourceMemoryGuardReport)
    _reject_private_public_payload(payload)
    _public_true_flag(payload["paper_only"], "payload.paper_only")
    _public_true_flag(payload["report_only"], "payload.report_only")
    _public_true_flag(payload["readonly"], "payload.readonly")
    validation_digest = payload["validation_digest"]
    _require_hex_digest("validation_digest", validation_digest)
    payload_body = dict(payload)
    payload_body.pop("validation_digest")
    if validation_digest != _digest_payload(payload_body):
        raise ValueError("validation_digest must match report payload")
    _report_from_public_payload(payload)


def _report_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyClaimSourceMemoryGuardReport:
    validation_digest = payload["validation_digest"]
    _require_hex_digest("validation_digest", validation_digest)
    config_payload = _require_mapping_schema(
        "payload.config",
        payload["config"],
        ResearchStrategyClaimSourceMemoryGuardConfig,
    )
    config = _config_from_public_payload(config_payload)
    rows_value = payload["rows"]
    if type(rows_value) is not list:
        raise ValueError("payload.rows must be a list")
    rows = tuple(
        _row_from_public_payload(value, f"payload.rows[{index}]")
        for index, value in enumerate(rows_value)
    )
    counts_value = payload["reason_code_counts"]
    if type(counts_value) is not list:
        raise ValueError("payload.reason_code_counts must be a list")
    reason_code_counts = tuple(
        _reason_code_count_from_public_payload(value, f"payload.reason_code_counts[{index}]")
        for index, value in enumerate(counts_value)
    )
    return ResearchStrategyClaimSourceMemoryGuardReport(
        generated_at=_public_datetime("generated_at", payload["generated_at"]),
        config_version=_public_label("config_version", payload["config_version"]),
        config=config,
        input_count=_public_decimal(
            "input_count",
            payload["input_count"],
            _require_nonnegative_whole_decimal,
        ),
        pass_count=_public_decimal(
            "pass_count",
            payload["pass_count"],
            _require_nonnegative_whole_decimal,
        ),
        watch_count=_public_decimal(
            "watch_count",
            payload["watch_count"],
            _require_nonnegative_whole_decimal,
        ),
        block_count=_public_decimal(
            "block_count",
            payload["block_count"],
            _require_nonnegative_whole_decimal,
        ),
        average_memory_guard_score=_public_optional_decimal(
            "average_memory_guard_score",
            payload["average_memory_guard_score"],
            _require_ratio_decimal,
        ),
        min_fresh_memory_score=_public_decimal(
            "min_fresh_memory_score",
            payload["min_fresh_memory_score"],
            _require_ratio_decimal,
        ),
        max_source_overlap_ratio=_public_decimal(
            "max_source_overlap_ratio",
            payload["max_source_overlap_ratio"],
            _require_ratio_decimal,
        ),
        max_stale_memory_risk=_public_decimal(
            "max_stale_memory_risk",
            payload["max_stale_memory_risk"],
            _require_ratio_decimal,
        ),
        min_distinct_source_count=_public_decimal(
            "min_distinct_source_count",
            payload["min_distinct_source_count"],
            _require_nonnegative_whole_decimal,
        ),
        status=_public_status(payload["status"], "status"),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=_public_reason_codes(payload["reason_codes"], "reason_codes"),
        validation_digest=validation_digest,
        paper_only=_public_true_flag(payload["paper_only"], "paper_only"),
        report_only=_public_true_flag(payload["report_only"], "report_only"),
        readonly=_public_true_flag(payload["readonly"], "readonly"),
    )


def _config_from_public_payload(
    payload: dict[str, Any],
) -> ResearchStrategyClaimSourceMemoryGuardConfig:
    return ResearchStrategyClaimSourceMemoryGuardConfig(
        config_version=_public_label("config_version", payload["config_version"]),
        min_pass_fresh_memory_score=_public_decimal(
            "min_pass_fresh_memory_score",
            payload["min_pass_fresh_memory_score"],
            _require_ratio_decimal,
        ),
        min_watch_fresh_memory_score=_public_decimal(
            "min_watch_fresh_memory_score",
            payload["min_watch_fresh_memory_score"],
            _require_ratio_decimal,
        ),
        max_pass_source_overlap_ratio=_public_decimal(
            "max_pass_source_overlap_ratio",
            payload["max_pass_source_overlap_ratio"],
            _require_ratio_decimal,
        ),
        max_watch_source_overlap_ratio=_public_decimal(
            "max_watch_source_overlap_ratio",
            payload["max_watch_source_overlap_ratio"],
            _require_ratio_decimal,
        ),
        min_pass_distinct_source_count=_public_decimal(
            "min_pass_distinct_source_count",
            payload["min_pass_distinct_source_count"],
            _require_positive_whole_decimal,
        ),
        min_watch_distinct_source_count=_public_decimal(
            "min_watch_distinct_source_count",
            payload["min_watch_distinct_source_count"],
            _require_positive_whole_decimal,
        ),
        max_pass_memory_age_seconds=_public_decimal(
            "max_pass_memory_age_seconds",
            payload["max_pass_memory_age_seconds"],
            _require_positive_decimal,
        ),
        max_watch_memory_age_seconds=_public_decimal(
            "max_watch_memory_age_seconds",
            payload["max_watch_memory_age_seconds"],
            _require_positive_decimal,
        ),
        paper_only=_public_true_flag(payload["paper_only"], "config.paper_only"),
        report_only=_public_true_flag(payload["report_only"], "config.report_only"),
        readonly=_public_true_flag(payload["readonly"], "config.readonly"),
    )


def _row_from_public_payload(value: object, path: str) -> ResearchStrategyClaimSourceMemoryGuardRow:
    payload = _require_mapping_schema(path, value, ResearchStrategyClaimSourceMemoryGuardRow)
    return ResearchStrategyClaimSourceMemoryGuardRow(
        claim_digest=_public_digest(payload["claim_digest"], f"{path}.claim_digest"),
        source_memory_digest=_public_digest(
            payload["source_memory_digest"],
            f"{path}.source_memory_digest",
        ),
        observed_at=_public_datetime(f"{path}.observed_at", payload["observed_at"]),
        fresh_memory_score=_public_decimal(
            f"{path}.fresh_memory_score",
            payload["fresh_memory_score"],
            _require_ratio_decimal,
        ),
        source_overlap_ratio=_public_decimal(
            f"{path}.source_overlap_ratio",
            payload["source_overlap_ratio"],
            _require_ratio_decimal,
        ),
        distinct_source_count=_public_decimal(
            f"{path}.distinct_source_count",
            payload["distinct_source_count"],
            _require_nonnegative_whole_decimal,
        ),
        memory_age_seconds=_public_decimal(
            f"{path}.memory_age_seconds",
            payload["memory_age_seconds"],
            _require_nonnegative_decimal,
        ),
        stale_memory_risk=_public_decimal(
            f"{path}.stale_memory_risk",
            payload["stale_memory_risk"],
            _require_ratio_decimal,
        ),
        source_coverage_score=_public_decimal(
            f"{path}.source_coverage_score",
            payload["source_coverage_score"],
            _require_ratio_decimal,
        ),
        memory_guard_score=_public_decimal(
            f"{path}.memory_guard_score",
            payload["memory_guard_score"],
            _require_ratio_decimal,
        ),
        status=_public_status(payload["status"], f"{path}.status"),
        reason_codes=_public_reason_codes(payload["reason_codes"], f"{path}.reason_codes"),
        paper_only=_public_true_flag(payload["paper_only"], f"{path}.paper_only"),
        report_only=_public_true_flag(payload["report_only"], f"{path}.report_only"),
        readonly=_public_true_flag(payload["readonly"], f"{path}.readonly"),
    )


def _reason_code_count_from_public_payload(
    value: object,
    path: str,
) -> ResearchStrategyClaimSourceMemoryGuardReasonCodeCount:
    payload = _require_mapping_schema(
        path,
        value,
        ResearchStrategyClaimSourceMemoryGuardReasonCodeCount,
    )
    return ResearchStrategyClaimSourceMemoryGuardReasonCodeCount(
        reason_code=_public_reason_code(payload["reason_code"], f"{path}.reason_code"),
        count=_public_decimal(
            f"{path}.count",
            payload["count"],
            _require_positive_whole_decimal,
        ),
        row_ratio=_public_decimal(
            f"{path}.row_ratio",
            payload["row_ratio"],
            _require_ratio_decimal,
        ),
        paper_only=_public_true_flag(payload["paper_only"], f"{path}.paper_only"),
        report_only=_public_true_flag(payload["report_only"], f"{path}.report_only"),
        readonly=_public_true_flag(payload["readonly"], f"{path}.readonly"),
    )


def _public_decimal(
    field_name: str,
    value: object,
    validator: Any,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a canonical Decimal string") from exc
    normalized = validator(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must use canonical Decimal text")
    return normalized


def _public_optional_decimal(
    field_name: str,
    value: object,
    validator: Any,
) -> Decimal | None:
    if value is None:
        return None
    return _public_decimal(field_name, value, validator)


def _public_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if normalized.isoformat() != value:
        raise ValueError(f"{field_name} must be a canonical UTC datetime string")
    return normalized


def _public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a public label")
    _require_public_label(field_name, value)
    return value


def _public_digest(value: object, field_name: str) -> str:
    _require_hex_digest(field_name, value)
    return value


def _public_status(value: object, field_name: str) -> str:
    _require_status(field_name, value)
    return value


def _public_reason_code(value: object, field_name: str) -> str:
    _require_reason_code(field_name, value)
    return value


def _public_reason_codes(value: object, field_name: str) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized = _normalize_reason_codes(field_name, tuple(value), allow_empty=False)
    if list(normalized) != value:
        raise ValueError(f"{field_name} must use the canonical reason-code sequence")
    return normalized


def _public_true_flag(value: object, field_name: str) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _expected_report_digest(
    report: ResearchStrategyClaimSourceMemoryGuardReport,
) -> str:
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload.pop("validation_digest", None)
    _reject_private_public_payload(payload)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _reject_private_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_private_public_text(str(key))
            _reject_private_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_private_public_payload(item)
        return
    if isinstance(value, tuple):
        for item in value:
            _reject_private_public_payload(item)
        return
    if isinstance(value, str):
        _reject_private_public_text(value)


def _reject_private_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in PRIVATE_PUBLIC_FRAGMENTS):
        raise ValueError("public payload must not expose private source material")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not be signed zero")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return +value
        except InvalidOperation as exc:
            raise ValueError(f"{field_name} must fit the fixed Decimal context") from exc


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_ratio_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return _quantize(normalized)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(normalized)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    with localcontext(DECIMAL_CONTEXT):
        integral = normalized.to_integral_value()
    if normalized != integral:
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    with localcontext(DECIMAL_CONTEXT):
        integral = normalized.to_integral_value()
    if normalized != integral:
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count input must be an int")
    if value < 0:
        raise ValueError("count input must be nonnegative")
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            result = value.quantize(QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must fit the fixed Decimal context") from exc
    return ZERO if result.is_zero() else result


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public label")
    lowered = value.lower()
    if any(fragment in lowered for fragment in PRIVATE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public safe")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain lowercase reason codes")
    if any(character not in "abcdefghijklmnopqrstuvwxyz0123456789_" for character in value):
        raise ValueError(f"{field_name} must contain compact reason codes")
    if any(fragment in value for fragment in PRIVATE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must not expose private source material")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized = tuple(dict.fromkeys(values))
    if not normalized and not allow_empty:
        raise ValueError(f"{field_name} must not be empty")
    for value in normalized:
        _require_reason_code(field_name, value)
    return normalized


def _require_hex_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not _is_hex_digest(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")


def _is_hex_digest(value: str) -> bool:
    return len(value) == 64 and all(character in HEX_CHARS for character in value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in CLAIM_SOURCE_MEMORY_GUARD_STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
