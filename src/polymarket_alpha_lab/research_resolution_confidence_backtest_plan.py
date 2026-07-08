"""Public, read-only plan for resolution-confidence backtest research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
import hashlib
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import (
    json_ready_no_floats,
    reject_unsafe_surface_fields,
    require_paper_only_flags,
)


DEFAULT_RESEARCH_RESOLUTION_CONFIDENCE_BACKTEST_PLAN_CONFIG_VERSION = (
    "research-resolution-confidence-backtest-plan-v0"
)

DECIMAL_CONTEXT = Context(prec=64)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
STATUSES = frozenset(("pass", "watch", "block"))
AREA_ORDER = (
    "historical_resolution_samples",
    "resolution_label_completeness",
    "confidence_bucket_coverage",
    "confidence_error_review",
    "human_research_queue",
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "auth",
        "buy",
        "candidate",
        "dsn",
        "live",
        "market",
        "order",
        "position",
        "question",
        "raw",
        "recommend",
        "ref",
        "sell",
        "slug",
        "source",
        "table",
        "text",
        "token",
        "trade",
        "url",
        "wallet",
    ),
)


@dataclass(frozen=True)
class ResearchResolutionConfidenceBacktestPlanConfig:
    config_version: str = (
        DEFAULT_RESEARCH_RESOLUTION_CONFIDENCE_BACKTEST_PLAN_CONFIG_VERSION
    )
    min_closed_resolution_count: Decimal = Decimal("50.000000")
    min_confidence_bucket_count: Decimal = Decimal("5.000000")
    min_bucket_resolution_count: Decimal = Decimal("10.000000")
    max_confidence_error_watch: Decimal = Decimal("0.100000")
    max_confidence_error_block: Decimal = Decimal("0.200000")
    max_ambiguous_resolution_ratio_watch: Decimal = Decimal("0.100000")
    max_ambiguous_resolution_ratio_block: Decimal = Decimal("0.250000")
    max_missing_resolution_ratio_watch: Decimal = Decimal("0.050000")
    max_missing_resolution_ratio_block: Decimal = Decimal("0.150000")
    min_independent_review_count: Decimal = Decimal("2.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionConfidenceBacktestPlanConfig:
            raise ValueError("config must be exact")
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_RESOLUTION_CONFIDENCE_BACKTEST_PLAN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in (
            "min_closed_resolution_count",
            "min_confidence_bucket_count",
            "min_bucket_resolution_count",
            "min_independent_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
            _require_positive_decimal(field_name, getattr(self, field_name))
        for field_name in (
            "max_confidence_error_watch",
            "max_confidence_error_block",
            "max_ambiguous_resolution_ratio_watch",
            "max_ambiguous_resolution_ratio_block",
            "max_missing_resolution_ratio_watch",
            "max_missing_resolution_ratio_block",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.max_confidence_error_block <= self.max_confidence_error_watch:
            raise ValueError("max_confidence_error_block must exceed watch threshold")
        if (
            self.max_ambiguous_resolution_ratio_block
            <= self.max_ambiguous_resolution_ratio_watch
        ):
            raise ValueError(
                "max_ambiguous_resolution_ratio_block must exceed watch threshold",
            )
        if (
            self.max_missing_resolution_ratio_block
            <= self.max_missing_resolution_ratio_watch
        ):
            raise ValueError(
                "max_missing_resolution_ratio_block must exceed watch threshold",
            )
        require_paper_only_flags(
            "research resolution confidence backtest plan config",
            self,
        )
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchResolutionConfidenceBacktestPlanInput:
    public_event_key: str
    event_family: str
    closed_resolution_count: Decimal
    resolved_label_count: Decimal
    ambiguous_resolution_count: Decimal
    missing_resolution_count: Decimal
    confidence_bucket_count: Decimal
    smallest_bucket_resolution_count: Decimal
    mean_absolute_confidence_error: Decimal
    independent_review_count: Decimal
    manual_review_required: bool
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionConfidenceBacktestPlanInput:
            raise ValueError("plan_input must be exact")
        _require_canonical_string("public_event_key", self.public_event_key)
        _require_canonical_string("event_family", self.event_family)
        for field_name in (
            "closed_resolution_count",
            "resolved_label_count",
            "ambiguous_resolution_count",
            "missing_resolution_count",
            "confidence_bucket_count",
            "smallest_bucket_resolution_count",
            "independent_review_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_absolute_confidence_error",
            _normalize_probability(
                "mean_absolute_confidence_error",
                self.mean_absolute_confidence_error,
            ),
        )
        if type(self.manual_review_required) is not bool:
            raise ValueError("manual_review_required must be a bool")
        _validate_input(self)
        require_paper_only_flags(
            "research resolution confidence backtest plan input",
            self,
        )
        _reject_unsafe_public_payload("plan_input", self)


@dataclass(frozen=True)
class ResearchResolutionConfidenceBacktestPlanRow:
    area: str
    status: str
    observed_value: Decimal
    required_value: Decimal
    gap_ratio: Decimal
    queue_priority: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionConfidenceBacktestPlanRow:
            raise ValueError("row must be exact")
        _require_member("area", self.area, AREA_ORDER)
        _require_member("status", self.status, STATUSES)
        for field_name in ("observed_value", "required_value"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("gap_ratio", "queue_priority"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        require_paper_only_flags(
            "research resolution confidence backtest plan row",
            self,
        )
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchResolutionConfidenceBacktestPlanReport:
    generated_at: datetime
    config_version: str
    area_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    human_research_queue: tuple[ResearchResolutionConfidenceBacktestPlanRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionConfidenceBacktestPlanReport:
            raise ValueError("report must be exact")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_RESOLUTION_CONFIDENCE_BACKTEST_PLAN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be supported")
        for field_name in ("area_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "human_research_queue",
            _normalize_queue(self.human_research_queue),
        )
        _validate_report(self)
        require_paper_only_flags(
            "research resolution confidence backtest plan report",
            self,
        )
        _reject_unsafe_public_payload("report", self)
        _set_or_validate_derived_validation_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_resolution_confidence_backtest_plan_payload(self)


def build_research_resolution_confidence_backtest_plan(
    plan_input: ResearchResolutionConfidenceBacktestPlanInput,
    *,
    config: ResearchResolutionConfidenceBacktestPlanConfig,
    generated_at: datetime,
) -> ResearchResolutionConfidenceBacktestPlanReport:
    if type(plan_input) is not ResearchResolutionConfidenceBacktestPlanInput:
        raise ValueError("plan_input must be a ResearchResolutionConfidenceBacktestPlanInput")
    if type(config) is not ResearchResolutionConfidenceBacktestPlanConfig:
        raise ValueError("config must be a ResearchResolutionConfidenceBacktestPlanConfig")
    generated_at_utc = _as_utc("generated_at", generated_at)
    require_paper_only_flags(
        "research resolution confidence backtest plan input",
        plan_input,
    )
    require_paper_only_flags(
        "research resolution confidence backtest plan config",
        config,
    )
    _reject_unsafe_public_payload("plan_input", plan_input)
    _reject_unsafe_public_payload("config", config)
    queue = (
        _historical_resolution_samples_row(plan_input, config),
        _resolution_label_completeness_row(plan_input, config),
        _confidence_bucket_coverage_row(plan_input, config),
        _confidence_error_review_row(plan_input, config),
        _human_research_queue_row(plan_input, config),
    )
    return ResearchResolutionConfidenceBacktestPlanReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        area_count=Decimal(len(queue)),
        pass_count=_status_count(queue, "pass"),
        watch_count=_status_count(queue, "watch"),
        block_count=_status_count(queue, "block"),
        status=_report_status(queue),
        reason_codes=_report_reason_codes(queue),
        human_research_queue=queue,
    )


def research_resolution_confidence_backtest_plan_payload(
    report: ResearchResolutionConfidenceBacktestPlanReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionConfidenceBacktestPlanReport:
        raise ValueError(
            "report must be a ResearchResolutionConfidenceBacktestPlanReport",
        )
    require_paper_only_flags(
        "research resolution confidence backtest plan report",
        report,
    )
    reject_unsafe_surface_fields(
        "research resolution confidence backtest plan report",
        report,
    )
    _reject_unsafe_public_payload("report", report)
    _require_expected_digest(report)
    payload = json_ready_no_floats(asdict(report))
    if not isinstance(payload, dict):
        raise ValueError("payload must be a JSON object")
    reject_unsafe_surface_fields(
        "research resolution confidence backtest plan payload",
        payload,
    )
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _historical_resolution_samples_row(
    plan_input: ResearchResolutionConfidenceBacktestPlanInput,
    config: ResearchResolutionConfidenceBacktestPlanConfig,
) -> ResearchResolutionConfidenceBacktestPlanRow:
    observed = plan_input.closed_resolution_count
    required = config.min_closed_resolution_count
    if observed == ZERO:
        status = "block"
        reason_codes = ("historical_resolution_samples_block",)
    elif observed < required:
        status = "watch"
        reason_codes = ("historical_resolution_samples_watch",)
    else:
        status = "pass"
        reason_codes = ("historical_resolution_samples_pass",)
    gap_ratio = _shortfall_ratio(observed, required)
    return _row(
        area="historical_resolution_samples",
        status=status,
        observed_value=observed,
        required_value=required,
        gap_ratio=gap_ratio,
        reason_codes=reason_codes,
    )


def _resolution_label_completeness_row(
    plan_input: ResearchResolutionConfidenceBacktestPlanInput,
    config: ResearchResolutionConfidenceBacktestPlanConfig,
) -> ResearchResolutionConfidenceBacktestPlanRow:
    total = (
        plan_input.resolved_label_count
        + plan_input.ambiguous_resolution_count
        + plan_input.missing_resolution_count
    )
    ambiguous_ratio = _ratio(plan_input.ambiguous_resolution_count, total)
    missing_ratio = _ratio(plan_input.missing_resolution_count, total)
    gap_ratio = max(ambiguous_ratio, missing_ratio)
    reason_codes: list[str] = []
    status = "pass"
    if plan_input.resolved_label_count == ZERO:
        reason_codes.append("resolved_label_count_block")
        status = "block"
    if missing_ratio >= config.max_missing_resolution_ratio_block:
        reason_codes.append("missing_resolution_ratio_block")
        status = "block"
    elif missing_ratio > config.max_missing_resolution_ratio_watch:
        reason_codes.append("missing_resolution_ratio_watch")
        if status != "block":
            status = "watch"
    if ambiguous_ratio >= config.max_ambiguous_resolution_ratio_block:
        reason_codes.append("ambiguous_resolution_ratio_block")
        status = "block"
    elif ambiguous_ratio > config.max_ambiguous_resolution_ratio_watch:
        reason_codes.append("ambiguous_resolution_ratio_watch")
        if status != "block":
            status = "watch"
    if not reason_codes:
        reason_codes.append("resolution_label_completeness_pass")
    return _row(
        area="resolution_label_completeness",
        status=status,
        observed_value=plan_input.resolved_label_count,
        required_value=total,
        gap_ratio=gap_ratio,
        reason_codes=tuple(reason_codes),
    )


def _confidence_bucket_coverage_row(
    plan_input: ResearchResolutionConfidenceBacktestPlanInput,
    config: ResearchResolutionConfidenceBacktestPlanConfig,
) -> ResearchResolutionConfidenceBacktestPlanRow:
    reason_codes: list[str] = []
    status = "pass"
    if plan_input.confidence_bucket_count == ZERO:
        reason_codes.append("confidence_bucket_count_block")
        status = "block"
    elif plan_input.confidence_bucket_count < config.min_confidence_bucket_count:
        reason_codes.append("confidence_bucket_count_watch")
        status = "watch"
    if plan_input.smallest_bucket_resolution_count == ZERO:
        reason_codes.append("bucket_resolution_count_block")
        status = "block"
    elif plan_input.smallest_bucket_resolution_count < config.min_bucket_resolution_count:
        reason_codes.append("bucket_resolution_count_watch")
        if status != "block":
            status = "watch"
    if not reason_codes:
        reason_codes.append("confidence_bucket_coverage_pass")
    bucket_gap = _shortfall_ratio(
        plan_input.confidence_bucket_count,
        config.min_confidence_bucket_count,
    )
    size_gap = _shortfall_ratio(
        plan_input.smallest_bucket_resolution_count,
        config.min_bucket_resolution_count,
    )
    return _row(
        area="confidence_bucket_coverage",
        status=status,
        observed_value=plan_input.confidence_bucket_count,
        required_value=config.min_confidence_bucket_count,
        gap_ratio=max(bucket_gap, size_gap),
        reason_codes=tuple(reason_codes),
    )


def _confidence_error_review_row(
    plan_input: ResearchResolutionConfidenceBacktestPlanInput,
    config: ResearchResolutionConfidenceBacktestPlanConfig,
) -> ResearchResolutionConfidenceBacktestPlanRow:
    observed = plan_input.mean_absolute_confidence_error
    if observed >= config.max_confidence_error_block:
        status = "block"
        reason_codes = ("confidence_error_block",)
    elif observed > config.max_confidence_error_watch:
        status = "watch"
        reason_codes = ("confidence_error_watch",)
    else:
        status = "pass"
        reason_codes = ("confidence_error_pass",)
    return _row(
        area="confidence_error_review",
        status=status,
        observed_value=observed,
        required_value=config.max_confidence_error_watch,
        gap_ratio=_excess_ratio(observed, config.max_confidence_error_watch),
        reason_codes=reason_codes,
    )


def _human_research_queue_row(
    plan_input: ResearchResolutionConfidenceBacktestPlanInput,
    config: ResearchResolutionConfidenceBacktestPlanConfig,
) -> ResearchResolutionConfidenceBacktestPlanRow:
    observed = plan_input.independent_review_count
    required = config.min_independent_review_count
    reason_codes: list[str] = []
    status = "pass"
    if observed == ZERO:
        reason_codes.append("human_review_count_block")
        status = "block"
    elif observed < required:
        reason_codes.append("human_review_count_watch")
        status = "watch"
    if plan_input.manual_review_required:
        reason_codes.append("manual_review_required")
        if status != "block":
            status = "watch"
    if not reason_codes:
        reason_codes.append("human_research_queue_pass")
    return _row(
        area="human_research_queue",
        status=status,
        observed_value=observed,
        required_value=required,
        gap_ratio=_shortfall_ratio(observed, required),
        reason_codes=tuple(reason_codes),
    )


def _row(
    *,
    area: str,
    status: str,
    observed_value: Decimal,
    required_value: Decimal,
    gap_ratio: Decimal,
    reason_codes: tuple[str, ...],
) -> ResearchResolutionConfidenceBacktestPlanRow:
    return ResearchResolutionConfidenceBacktestPlanRow(
        area=area,
        status=status,
        observed_value=observed_value,
        required_value=required_value,
        gap_ratio=gap_ratio,
        queue_priority=_queue_priority(status, gap_ratio),
        reason_codes=reason_codes,
    )


def _queue_priority(status: str, gap_ratio: Decimal) -> Decimal:
    if status == "block":
        base = Decimal("0.750000")
    elif status == "watch":
        base = Decimal("0.500000")
    else:
        base = ZERO
    with localcontext(DECIMAL_CONTEXT):
        priority = base + (gap_ratio / Decimal("4.000000"))
    if priority > ONE:
        return ONE
    return _quantize_decimal(priority)


def _status_count(
    queue: tuple[ResearchResolutionConfidenceBacktestPlanRow, ...],
    status: str,
) -> Decimal:
    return Decimal(sum(1 for row in queue if row.status == status))


def _report_status(queue: tuple[ResearchResolutionConfidenceBacktestPlanRow, ...]) -> str:
    if any(row.status == "block" for row in queue):
        return "block"
    if any(row.status == "watch" for row in queue):
        return "watch"
    return "pass"


def _report_reason_codes(
    queue: tuple[ResearchResolutionConfidenceBacktestPlanRow, ...],
) -> tuple[str, ...]:
    has_block = any(row.status == "block" for row in queue)
    has_watch = any(row.status == "watch" for row in queue)
    if has_block and has_watch:
        return (
            "blocked_resolution_confidence_backtest_area",
            "watch_resolution_confidence_backtest_area",
        )
    if has_block:
        return ("blocked_resolution_confidence_backtest_area",)
    if has_watch:
        return ("watch_resolution_confidence_backtest_area",)
    return ("resolution_confidence_backtest_plan_pass",)


def _validate_input(plan_input: ResearchResolutionConfidenceBacktestPlanInput) -> None:
    label_total = (
        plan_input.resolved_label_count
        + plan_input.ambiguous_resolution_count
        + plan_input.missing_resolution_count
    )
    if label_total > plan_input.closed_resolution_count:
        raise ValueError("resolution label counts must not exceed closed count")
    if plan_input.closed_resolution_count == ZERO and label_total > ZERO:
        raise ValueError("closed_resolution_count must support label counts")


def _validate_report(report: ResearchResolutionConfidenceBacktestPlanReport) -> None:
    queue = report.human_research_queue
    if tuple(row.area for row in queue) != AREA_ORDER:
        raise ValueError("human_research_queue must match area order")
    expected_area_count = Decimal(len(queue))
    expected_pass_count = _status_count(queue, "pass")
    expected_watch_count = _status_count(queue, "watch")
    expected_block_count = _status_count(queue, "block")
    if report.area_count != expected_area_count:
        raise ValueError("area_count must match queue")
    if report.pass_count != expected_pass_count:
        raise ValueError("pass_count must match queue")
    if report.watch_count != expected_watch_count:
        raise ValueError("watch_count must match queue")
    if report.block_count != expected_block_count:
        raise ValueError("block_count must match queue")
    expected_status = _report_status(queue)
    if report.status != expected_status:
        raise ValueError("status must match queue")
    expected_reason_codes = _report_reason_codes(queue)
    if report.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match queue")


def _normalize_queue(
    value: object,
) -> tuple[ResearchResolutionConfidenceBacktestPlanRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("human_research_queue must be a tuple")
    if type(value) is not tuple:
        raise ValueError("human_research_queue must be a tuple")
    queue = tuple(value)
    for row in queue:
        if type(row) is not ResearchResolutionConfidenceBacktestPlanRow:
            raise ValueError(
                "human_research_queue must contain "
                "ResearchResolutionConfidenceBacktestPlanRow values",
            )
    return queue


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a tuple of strings")
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple of strings")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must contain at least one code")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_canonical_string(field_name, reason_code)
    return reason_codes


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(DECIMAL_QUANTUM)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


def _require_positive_decimal(field_name: str, value: Decimal) -> None:
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be stripped")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_-.")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...] | frozenset[str]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {', '.join(sorted(allowed))}")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be an exact datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    offset = value.utcoffset()
    if offset is None:
        raise ValueError(f"{field_name} must have a valid UTC offset")
    return value.astimezone(UTC)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        ratio = numerator / denominator
    if ratio < ZERO:
        return ZERO
    if ratio > ONE:
        return ONE
    return _quantize_decimal(ratio)


def _shortfall_ratio(observed: Decimal, required: Decimal) -> Decimal:
    if required <= ZERO or observed >= required:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal((required - observed) / required)


def _excess_ratio(observed: Decimal, allowed: Decimal) -> Decimal:
    if observed <= allowed:
        return ZERO
    if allowed == ZERO:
        return ONE
    with localcontext(DECIMAL_CONTEXT):
        ratio = (observed - allowed) / allowed
    if ratio > ONE:
        return ONE
    return _quantize_decimal(ratio)


def _set_or_validate_derived_validation_digest(
    report: ResearchResolutionConfidenceBacktestPlanReport,
) -> None:
    current = report.derived_validation_digest
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _derived_validation_digest(report)
    if current == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_digest(current)
    if current != expected:
        raise ValueError("derived_validation_digest must match report contents")


def _require_expected_digest(report: ResearchResolutionConfidenceBacktestPlanReport) -> None:
    _validate_report(report)
    _require_digest(report.derived_validation_digest)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report contents")


def _require_digest(value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchResolutionConfidenceBacktestPlanReport,
) -> str:
    material = asdict(report)
    material["derived_validation_digest"] = ""
    ready = json_ready_no_floats(material)
    encoded = json.dumps(ready, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    reject_unsafe_surface_fields(label, value)
    for text_value in _iter_string_values(value):
        normalized = text_value.lower()
        if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"unsafe public value in {label}")


def _iter_string_values(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        return _iter_string_values(asdict(value))
    if isinstance(value, dict):
        items: list[str] = []
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            items.append(key)
            items.extend(_iter_string_values(item))
        return tuple(items)
    if isinstance(value, (list, tuple)):
        items = []
        for item in value:
            items.extend(_iter_string_values(item))
        return tuple(items)
    if type(value) is str:
        return (value,)
    return ()


__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_CONFIDENCE_BACKTEST_PLAN_CONFIG_VERSION",
    "ResearchResolutionConfidenceBacktestPlanConfig",
    "ResearchResolutionConfidenceBacktestPlanInput",
    "ResearchResolutionConfidenceBacktestPlanReport",
    "ResearchResolutionConfidenceBacktestPlanRow",
    "build_research_resolution_confidence_backtest_plan",
    "research_resolution_confidence_backtest_plan_payload",
)
