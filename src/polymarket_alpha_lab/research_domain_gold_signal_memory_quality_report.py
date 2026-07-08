"""Pure report-only gold commodities signal memory quality reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps


DEFAULT_RESEARCH_DOMAIN_GOLD_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION = (
    "research-domain-gold-signal-memory-quality-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
RESEARCH_DOMAIN_GOLD_SIGNAL_MEMORY_QUALITY_REPORT_STATUSES = (
    STATUS_PASS,
    STATUS_WATCH,
    STATUS_BLOCK,
)

NO_INPUTS_REASON = "gold_signal_memory_quality_no_inputs"
PASS_REASON = "gold_signal_memory_quality_pass"
WATCH_REASON = "gold_signal_memory_quality_watch"
BLOCK_REASON = "gold_signal_memory_quality_block"
FRESHNESS_BELOW_WATCH_REASON = "gold_memory_freshness_below_watch"
FRESHNESS_BELOW_PASS_REASON = "gold_memory_freshness_below_pass"
AGE_ABOVE_WATCH_REASON = "gold_memory_age_above_watch"
AGE_ABOVE_PASS_REASON = "gold_memory_age_above_pass"
CONFLICT_ABOVE_WATCH_REASON = "gold_memory_conflict_above_watch"
CONFLICT_ABOVE_PASS_REASON = "gold_memory_conflict_above_pass"
COVERAGE_BELOW_WATCH_REASON = "gold_memory_required_coverage_below_watch"
COVERAGE_BELOW_PASS_REASON = "gold_memory_required_coverage_below_pass"
REQUIRED_INPUTS_MISSING_REASON = "gold_memory_required_inputs_missing"
OBSERVATION_MISSING_REASON = "gold_memory_observation_missing"

REASON_CODE_PRIORITY = (
    NO_INPUTS_REASON,
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    FRESHNESS_BELOW_WATCH_REASON,
    AGE_ABOVE_WATCH_REASON,
    CONFLICT_ABOVE_WATCH_REASON,
    COVERAGE_BELOW_WATCH_REASON,
    FRESHNESS_BELOW_PASS_REASON,
    AGE_ABOVE_PASS_REASON,
    CONFLICT_ABOVE_PASS_REASON,
    COVERAGE_BELOW_PASS_REASON,
    REQUIRED_INPUTS_MISSING_REASON,
    OBSERVATION_MISSING_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
RATIO_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO_COUNT = Decimal("0")
ONE_COUNT = Decimal("1")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
SHA256_HEX_LENGTH = 64

PUBLIC_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789-_")
PUBLIC_REASON_CODE_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_PUBLIC_FRAGMENTS = (
    "candidate",
    "event_id",
    "event_slug",
    "market_id",
    "market_slug",
    "raw_event",
    "raw_market",
    "raw_source",
    "question",
    "slug",
    "url",
    "http://",
    "https://",
    "://",
    "source_text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "live_execution",
    "live execution",
    "execute",
    "private",
    "secret",
    "recommend",
    "sizing",
    "allocation",
)

__all__ = (
    "DEFAULT_RESEARCH_DOMAIN_GOLD_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION",
    "RESEARCH_DOMAIN_GOLD_SIGNAL_MEMORY_QUALITY_REPORT_STATUSES",
    "ResearchDomainGoldSignalMemoryInput",
    "ResearchDomainGoldSignalMemoryQualityConfig",
    "ResearchDomainGoldSignalMemoryQualityReasonCodeCount",
    "ResearchDomainGoldSignalMemoryQualityReport",
    "ResearchDomainGoldSignalMemoryQualityRow",
    "build_research_domain_gold_signal_memory_quality_report",
    "research_domain_gold_signal_memory_quality_report_digest",
    "research_domain_gold_signal_memory_quality_report_payload",
)


@dataclass(frozen=True)
class ResearchDomainGoldSignalMemoryQualityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_DOMAIN_GOLD_SIGNAL_MEMORY_QUALITY_REPORT_CONFIG_VERSION
    )
    max_pass_memory_age_seconds: Decimal = Decimal("43200")
    max_watch_memory_age_seconds: Decimal = Decimal("172800")
    min_pass_freshness_ratio: Decimal = Decimal("0.750000")
    min_watch_freshness_ratio: Decimal = Decimal("0.500000")
    max_pass_conflict_ratio: Decimal = Decimal("0.100000")
    max_watch_conflict_ratio: Decimal = Decimal("0.250000")
    min_pass_required_coverage_ratio: Decimal = Decimal("1.000000")
    min_watch_required_coverage_ratio: Decimal = Decimal("0.750000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainGoldSignalMemoryQualityConfig:
            raise TypeError("ResearchDomainGoldSignalMemoryQualityConfig is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainGoldSignalMemoryQualityConfig:
            raise ValueError(
                "config must be exactly ResearchDomainGoldSignalMemoryQualityConfig",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "max_pass_memory_age_seconds",
            "max_watch_memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_freshness_ratio",
            "min_watch_freshness_ratio",
            "max_pass_conflict_ratio",
            "max_watch_conflict_ratio",
            "min_pass_required_coverage_ratio",
            "min_watch_required_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchDomainGoldSignalMemoryInput:
    catalyst_family: str
    memory_lane: str
    memory_input_count: Decimal
    fresh_memory_input_count: Decimal
    stale_memory_input_count: Decimal
    conflicting_memory_input_count: Decimal
    required_catalyst_count: Decimal
    missing_required_catalyst_count: Decimal
    latest_memory_observed_at: datetime | None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainGoldSignalMemoryInput:
            raise TypeError("ResearchDomainGoldSignalMemoryInput is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainGoldSignalMemoryInput:
            raise ValueError(
                "input must be exactly ResearchDomainGoldSignalMemoryInput",
            )
        object.__setattr__(
            self,
            "catalyst_family",
            _require_public_identifier("catalyst_family", self.catalyst_family),
        )
        object.__setattr__(
            self,
            "memory_lane",
            _require_public_identifier("memory_lane", self.memory_lane),
        )
        for field_name in (
            "memory_input_count",
            "fresh_memory_input_count",
            "stale_memory_input_count",
            "conflicting_memory_input_count",
            "required_catalyst_count",
            "missing_required_catalyst_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "latest_memory_observed_at",
            _as_optional_utc(
                "latest_memory_observed_at",
                self.latest_memory_observed_at,
            ),
        )
        _validate_input(self)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchDomainGoldSignalMemoryQualityRow:
    catalyst_family: str
    memory_lane: str
    memory_input_count: Decimal
    fresh_memory_input_count: Decimal
    stale_memory_input_count: Decimal
    conflicting_memory_input_count: Decimal
    required_catalyst_count: Decimal
    missing_required_catalyst_count: Decimal
    freshness_ratio: Decimal
    conflict_ratio: Decimal
    required_coverage_ratio: Decimal
    memory_age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainGoldSignalMemoryQualityRow:
            raise TypeError("ResearchDomainGoldSignalMemoryQualityRow is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainGoldSignalMemoryQualityRow:
            raise ValueError(
                "row must be exactly ResearchDomainGoldSignalMemoryQualityRow",
            )
        object.__setattr__(
            self,
            "catalyst_family",
            _require_public_identifier("catalyst_family", self.catalyst_family),
        )
        object.__setattr__(
            self,
            "memory_lane",
            _require_public_identifier("memory_lane", self.memory_lane),
        )
        for field_name in (
            "memory_input_count",
            "fresh_memory_input_count",
            "stale_memory_input_count",
            "conflicting_memory_input_count",
            "required_catalyst_count",
            "missing_required_catalyst_count",
            "memory_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "freshness_ratio",
            "conflict_ratio",
            "required_coverage_ratio",
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
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchDomainGoldSignalMemoryQualityReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainGoldSignalMemoryQualityReasonCodeCount:
            raise TypeError("ResearchDomainGoldSignalMemoryQualityReasonCodeCount is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainGoldSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchDomainGoldSignalMemoryQualityReasonCodeCount",
            )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchDomainGoldSignalMemoryQualityReport:
    generated_at: datetime
    config_version: str
    memory_lane_count: Decimal
    memory_input_count: Decimal
    fresh_memory_input_count: Decimal
    stale_memory_input_count: Decimal
    conflicting_memory_input_count: Decimal
    required_catalyst_count: Decimal
    missing_required_catalyst_count: Decimal
    overall_freshness_ratio: Decimal
    overall_conflict_ratio: Decimal
    overall_required_coverage_ratio: Decimal
    max_memory_age_seconds: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchDomainGoldSignalMemoryQualityReasonCodeCount, ...]
    rows: tuple[ResearchDomainGoldSignalMemoryQualityRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchDomainGoldSignalMemoryQualityReport:
            raise TypeError("ResearchDomainGoldSignalMemoryQualityReport is final")

    def __post_init__(self) -> None:
        if type(self) is not ResearchDomainGoldSignalMemoryQualityReport:
            raise ValueError(
                "report must be exactly ResearchDomainGoldSignalMemoryQualityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for field_name in (
            "memory_lane_count",
            "memory_input_count",
            "fresh_memory_input_count",
            "stale_memory_input_count",
            "conflicting_memory_input_count",
            "required_catalyst_count",
            "missing_required_catalyst_count",
            "max_memory_age_seconds",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "overall_freshness_ratio",
            "overall_conflict_ratio",
            "overall_required_coverage_ratio",
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
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload("report payload", payload)
        if type(payload) is not dict:
            raise ValueError("report payload must be a dict")
        return payload


def build_research_domain_gold_signal_memory_quality_report(
    memory_inputs: list[ResearchDomainGoldSignalMemoryInput]
    | tuple[ResearchDomainGoldSignalMemoryInput, ...],
    *,
    config: ResearchDomainGoldSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainGoldSignalMemoryQualityReport:
    if type(config) is not ResearchDomainGoldSignalMemoryQualityConfig:
        raise ValueError(
            "config must be exactly ResearchDomainGoldSignalMemoryQualityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(memory_inputs, generated_at=generated_at_utc)
    rows = _build_rows(normalized_inputs, config, generated_at_utc)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "memory_lane_count": _count(len(rows)),
        "memory_input_count": _sum_rows(rows, "memory_input_count"),
        "fresh_memory_input_count": _sum_rows(rows, "fresh_memory_input_count"),
        "stale_memory_input_count": _sum_rows(rows, "stale_memory_input_count"),
        "conflicting_memory_input_count": _sum_rows(
            rows,
            "conflicting_memory_input_count",
        ),
        "required_catalyst_count": _sum_rows(rows, "required_catalyst_count"),
        "missing_required_catalyst_count": _sum_rows(
            rows,
            "missing_required_catalyst_count",
        ),
        "overall_freshness_ratio": _ratio(
            _sum_rows(rows, "fresh_memory_input_count"),
            _sum_rows(rows, "memory_input_count"),
        ),
        "overall_conflict_ratio": _ratio(
            _sum_rows(rows, "conflicting_memory_input_count"),
            _sum_rows(rows, "memory_input_count"),
        ),
        "overall_required_coverage_ratio": _required_coverage_ratio(
            _sum_rows(rows, "required_catalyst_count"),
            _sum_rows(rows, "missing_required_catalyst_count"),
        ),
        "max_memory_age_seconds": _max_row_decimal(rows, "memory_age_seconds"),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchDomainGoldSignalMemoryQualityReport(
        **values,
        derived_validation_digest=_digest_from_values(values),
    )


def research_domain_gold_signal_memory_quality_report_payload(
    report: ResearchDomainGoldSignalMemoryQualityReport,
) -> dict[str, object]:
    if type(report) is not ResearchDomainGoldSignalMemoryQualityReport:
        raise ValueError(
            "report must be exactly ResearchDomainGoldSignalMemoryQualityReport",
        )
    _require_hard_flags("report", report)
    return report.payload


def research_domain_gold_signal_memory_quality_report_digest(
    report: ResearchDomainGoldSignalMemoryQualityReport,
) -> str:
    if type(report) is not ResearchDomainGoldSignalMemoryQualityReport:
        raise ValueError(
            "report must be exactly ResearchDomainGoldSignalMemoryQualityReport",
        )
    return _digest_from_values(_report_values_without_digest(report))


def _build_rows(
    memory_inputs: tuple[ResearchDomainGoldSignalMemoryInput, ...],
    config: ResearchDomainGoldSignalMemoryQualityConfig,
    generated_at: datetime,
) -> tuple[ResearchDomainGoldSignalMemoryQualityRow, ...]:
    rows = tuple(
        _row_for_input(memory_input, config, generated_at)
        for memory_input in memory_inputs
    )
    return tuple(sorted(rows, key=_row_sort_key))


def _row_for_input(
    memory_input: ResearchDomainGoldSignalMemoryInput,
    config: ResearchDomainGoldSignalMemoryQualityConfig,
    generated_at: datetime,
) -> ResearchDomainGoldSignalMemoryQualityRow:
    freshness_ratio = _ratio(
        memory_input.fresh_memory_input_count,
        memory_input.memory_input_count,
    )
    conflict_ratio = _ratio(
        memory_input.conflicting_memory_input_count,
        memory_input.memory_input_count,
    )
    required_coverage_ratio = _required_coverage_ratio(
        memory_input.required_catalyst_count,
        memory_input.missing_required_catalyst_count,
    )
    memory_age_seconds = (
        ZERO_COUNT
        if memory_input.latest_memory_observed_at is None
        else _age_seconds(generated_at, memory_input.latest_memory_observed_at)
    )
    status = _row_status(
        memory_input=memory_input,
        freshness_ratio=freshness_ratio,
        conflict_ratio=conflict_ratio,
        required_coverage_ratio=required_coverage_ratio,
        memory_age_seconds=memory_age_seconds,
        config=config,
    )
    return ResearchDomainGoldSignalMemoryQualityRow(
        catalyst_family=memory_input.catalyst_family,
        memory_lane=memory_input.memory_lane,
        memory_input_count=memory_input.memory_input_count,
        fresh_memory_input_count=memory_input.fresh_memory_input_count,
        stale_memory_input_count=memory_input.stale_memory_input_count,
        conflicting_memory_input_count=memory_input.conflicting_memory_input_count,
        required_catalyst_count=memory_input.required_catalyst_count,
        missing_required_catalyst_count=memory_input.missing_required_catalyst_count,
        freshness_ratio=freshness_ratio,
        conflict_ratio=conflict_ratio,
        required_coverage_ratio=required_coverage_ratio,
        memory_age_seconds=memory_age_seconds,
        status=status,
        reason_codes=_row_reason_codes(
            memory_input=memory_input,
            freshness_ratio=freshness_ratio,
            conflict_ratio=conflict_ratio,
            required_coverage_ratio=required_coverage_ratio,
            memory_age_seconds=memory_age_seconds,
            status=status,
            config=config,
        ),
    )


def _row_status(
    *,
    memory_input: ResearchDomainGoldSignalMemoryInput,
    freshness_ratio: Decimal,
    conflict_ratio: Decimal,
    required_coverage_ratio: Decimal,
    memory_age_seconds: Decimal,
    config: ResearchDomainGoldSignalMemoryQualityConfig,
) -> str:
    if (
        memory_input.latest_memory_observed_at is None
        or freshness_ratio < config.min_watch_freshness_ratio
        or memory_age_seconds > config.max_watch_memory_age_seconds
        or conflict_ratio > config.max_watch_conflict_ratio
        or required_coverage_ratio < config.min_watch_required_coverage_ratio
    ):
        return STATUS_BLOCK
    if (
        freshness_ratio < config.min_pass_freshness_ratio
        or memory_age_seconds > config.max_pass_memory_age_seconds
        or conflict_ratio > config.max_pass_conflict_ratio
        or required_coverage_ratio < config.min_pass_required_coverage_ratio
        or memory_input.missing_required_catalyst_count > ZERO_COUNT
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    memory_input: ResearchDomainGoldSignalMemoryInput,
    freshness_ratio: Decimal,
    conflict_ratio: Decimal,
    required_coverage_ratio: Decimal,
    memory_age_seconds: Decimal,
    status: str,
    config: ResearchDomainGoldSignalMemoryQualityConfig,
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        return (PASS_REASON,)
    if status == STATUS_BLOCK:
        reasons = [BLOCK_REASON]
        if freshness_ratio < config.min_watch_freshness_ratio:
            reasons.append(FRESHNESS_BELOW_WATCH_REASON)
        if memory_age_seconds > config.max_watch_memory_age_seconds:
            reasons.append(AGE_ABOVE_WATCH_REASON)
        if conflict_ratio > config.max_watch_conflict_ratio:
            reasons.append(CONFLICT_ABOVE_WATCH_REASON)
        if required_coverage_ratio < config.min_watch_required_coverage_ratio:
            reasons.append(COVERAGE_BELOW_WATCH_REASON)
        if memory_input.missing_required_catalyst_count > ZERO_COUNT:
            reasons.append(REQUIRED_INPUTS_MISSING_REASON)
        if memory_input.latest_memory_observed_at is None:
            reasons.append(OBSERVATION_MISSING_REASON)
        return _normalize_reason_codes(tuple(reasons), require_nonempty=True)

    reasons = [WATCH_REASON]
    if freshness_ratio < config.min_pass_freshness_ratio:
        reasons.append(FRESHNESS_BELOW_PASS_REASON)
    if memory_age_seconds > config.max_pass_memory_age_seconds:
        reasons.append(AGE_ABOVE_PASS_REASON)
    if conflict_ratio > config.max_pass_conflict_ratio:
        reasons.append(CONFLICT_ABOVE_PASS_REASON)
    if required_coverage_ratio < config.min_pass_required_coverage_ratio:
        reasons.append(COVERAGE_BELOW_PASS_REASON)
    if memory_input.missing_required_catalyst_count > ZERO_COUNT:
        reasons.append(REQUIRED_INPUTS_MISSING_REASON)
    return _normalize_reason_codes(tuple(reasons), require_nonempty=True)


def _report_status(rows: tuple[ResearchDomainGoldSignalMemoryQualityRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchDomainGoldSignalMemoryQualityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return _normalize_reason_codes(
        tuple(reason for row in rows for reason in row.reason_codes),
        require_nonempty=True,
        deduplicate=True,
    )


def _reason_code_counts(
    rows: tuple[ResearchDomainGoldSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainGoldSignalMemoryQualityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchDomainGoldSignalMemoryQualityReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE_COUNT,
            ),
        )
    counts = Counter(reason for row in rows for reason in row.reason_codes)
    return tuple(
        ResearchDomainGoldSignalMemoryQualityReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODE_PRIORITY.index(item[0]),
        )
    )


def _normalize_inputs(
    value: object,
    *,
    generated_at: datetime,
) -> tuple[ResearchDomainGoldSignalMemoryInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("memory_inputs must be a list or tuple")
    memory_inputs = tuple(value)
    seen: set[tuple[str, str]] = set()
    for memory_input in memory_inputs:
        if type(memory_input) is not ResearchDomainGoldSignalMemoryInput:
            raise ValueError(
                "memory_inputs must contain ResearchDomainGoldSignalMemoryInput",
            )
        _require_hard_flags("input", memory_input)
        if (
            memory_input.latest_memory_observed_at is not None
            and memory_input.latest_memory_observed_at > generated_at
        ):
            raise ValueError("latest_memory_observed_at must not be in the future")
        key = (memory_input.catalyst_family, memory_input.memory_lane)
        if key in seen:
            raise ValueError("catalyst_family and memory_lane pairs must be unique")
        seen.add(key)
    return tuple(
        sorted(
            memory_inputs,
            key=lambda memory_input: (
                memory_input.catalyst_family,
                memory_input.memory_lane,
            ),
        ),
    )


def _validate_config(config: ResearchDomainGoldSignalMemoryQualityConfig) -> None:
    if config.max_pass_memory_age_seconds > config.max_watch_memory_age_seconds:
        raise ValueError(
            "max_pass_memory_age_seconds must be <= max_watch_memory_age_seconds",
        )
    if config.min_pass_freshness_ratio < config.min_watch_freshness_ratio:
        raise ValueError(
            "min_pass_freshness_ratio must be >= min_watch_freshness_ratio",
        )
    if config.max_pass_conflict_ratio > config.max_watch_conflict_ratio:
        raise ValueError(
            "max_pass_conflict_ratio must be <= max_watch_conflict_ratio",
        )
    if (
        config.min_pass_required_coverage_ratio
        < config.min_watch_required_coverage_ratio
    ):
        raise ValueError(
            "min_pass_required_coverage_ratio must be >= "
            "min_watch_required_coverage_ratio",
        )


def _validate_input(memory_input: ResearchDomainGoldSignalMemoryInput) -> None:
    if (
        memory_input.fresh_memory_input_count + memory_input.stale_memory_input_count
        != memory_input.memory_input_count
    ):
        raise ValueError(
            "fresh and stale memory input counts must equal memory_input_count",
        )
    if memory_input.conflicting_memory_input_count > memory_input.memory_input_count:
        raise ValueError(
            "conflicting_memory_input_count must not exceed memory_input_count",
        )
    if memory_input.missing_required_catalyst_count > memory_input.required_catalyst_count:
        raise ValueError(
            "missing_required_catalyst_count must not exceed required_catalyst_count",
        )


def _validate_row(row: ResearchDomainGoldSignalMemoryQualityRow) -> None:
    if row.fresh_memory_input_count + row.stale_memory_input_count != row.memory_input_count:
        raise ValueError(
            "fresh and stale memory input counts must equal memory_input_count",
        )
    if row.conflicting_memory_input_count > row.memory_input_count:
        raise ValueError(
            "conflicting_memory_input_count must not exceed memory_input_count",
        )
    if row.missing_required_catalyst_count > row.required_catalyst_count:
        raise ValueError(
            "missing_required_catalyst_count must not exceed required_catalyst_count",
        )
    if row.freshness_ratio != _ratio(row.fresh_memory_input_count, row.memory_input_count):
        raise ValueError("freshness_ratio must match memory input counts")
    if row.conflict_ratio != _ratio(
        row.conflicting_memory_input_count,
        row.memory_input_count,
    ):
        raise ValueError("conflict_ratio must match memory input counts")
    if row.required_coverage_ratio != _required_coverage_ratio(
        row.required_catalyst_count,
        row.missing_required_catalyst_count,
    ):
        raise ValueError("required_coverage_ratio must match catalyst counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchDomainGoldSignalMemoryQualityReport) -> None:
    rows = report.rows
    if report.memory_lane_count != _count(len(rows)):
        raise ValueError("memory_lane_count must match rows")
    if report.memory_input_count != _sum_rows(rows, "memory_input_count"):
        raise ValueError("memory_input_count must match rows")
    if report.fresh_memory_input_count != _sum_rows(rows, "fresh_memory_input_count"):
        raise ValueError("fresh_memory_input_count must match rows")
    if report.stale_memory_input_count != _sum_rows(rows, "stale_memory_input_count"):
        raise ValueError("stale_memory_input_count must match rows")
    if report.conflicting_memory_input_count != _sum_rows(
        rows,
        "conflicting_memory_input_count",
    ):
        raise ValueError("conflicting_memory_input_count must match rows")
    if report.required_catalyst_count != _sum_rows(rows, "required_catalyst_count"):
        raise ValueError("required_catalyst_count must match rows")
    if report.missing_required_catalyst_count != _sum_rows(
        rows,
        "missing_required_catalyst_count",
    ):
        raise ValueError("missing_required_catalyst_count must match rows")
    if report.overall_freshness_ratio != _ratio(
        _sum_rows(rows, "fresh_memory_input_count"),
        _sum_rows(rows, "memory_input_count"),
    ):
        raise ValueError("overall_freshness_ratio must match rows")
    if report.overall_conflict_ratio != _ratio(
        _sum_rows(rows, "conflicting_memory_input_count"),
        _sum_rows(rows, "memory_input_count"),
    ):
        raise ValueError("overall_conflict_ratio must match rows")
    if report.overall_required_coverage_ratio != _required_coverage_ratio(
        _sum_rows(rows, "required_catalyst_count"),
        _sum_rows(rows, "missing_required_catalyst_count"),
    ):
        raise ValueError("overall_required_coverage_ratio must match rows")
    if report.max_memory_age_seconds != _max_row_decimal(rows, "memory_age_seconds"):
        raise ValueError("max_memory_age_seconds must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes or NO_INPUTS_REASON in reason_codes:
        return STATUS_BLOCK
    if WATCH_REASON in reason_codes:
        return STATUS_WATCH
    if reason_codes == (PASS_REASON,):
        return STATUS_PASS
    raise ValueError("reason_codes must include a status reason")


def _row_sort_key(row: ResearchDomainGoldSignalMemoryQualityRow) -> tuple[int, str, str]:
    return (
        {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}[row.status],
        row.catalyst_family,
        row.memory_lane,
    )


def _status_count(
    rows: tuple[ResearchDomainGoldSignalMemoryQualityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _sum_rows(
    rows: tuple[ResearchDomainGoldSignalMemoryQualityRow, ...],
    field_name: str,
) -> Decimal:
    return _sum_decimal(tuple(getattr(row, field_name) for row in rows))


def _max_row_decimal(
    rows: tuple[ResearchDomainGoldSignalMemoryQualityRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO_COUNT
    return max(getattr(row, field_name) for row in rows)


def _required_coverage_ratio(
    required_catalyst_count: Decimal,
    missing_required_catalyst_count: Decimal,
) -> Decimal:
    if required_catalyst_count == ZERO_COUNT:
        return ZERO_RATIO
    return _ratio(
        required_catalyst_count - missing_required_catalyst_count,
        required_catalyst_count,
    )


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_count(sum(values, ZERO_COUNT))


def _count(value: int) -> Decimal:
    return _quantize_count(Decimal(value))


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    with localcontext(DECIMAL_CONTEXT):
        value = Decimal(delta.days) * SECONDS_PER_DAY + Decimal(delta.seconds)
    if value < ZERO_COUNT:
        raise ValueError("latest_memory_observed_at must not be in the future")
    return _quantize_count(value)


def _normalize_reason_code_counts(
    value: tuple[ResearchDomainGoldSignalMemoryQualityReasonCodeCount, ...],
) -> tuple[ResearchDomainGoldSignalMemoryQualityReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in value:
        if type(item) is not ResearchDomainGoldSignalMemoryQualityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchDomainGoldSignalMemoryQualityReasonCodeCount",
            )
    if len({item.reason_code for item in value}) != len(value):
        raise ValueError("reason_code_counts must not contain duplicates")
    return tuple(
        sorted(
            value,
            key=lambda item: REASON_CODE_PRIORITY.index(item.reason_code),
        ),
    )


def _normalize_rows(
    value: tuple[ResearchDomainGoldSignalMemoryQualityRow, ...],
) -> tuple[ResearchDomainGoldSignalMemoryQualityRow, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not ResearchDomainGoldSignalMemoryQualityRow:
            raise ValueError("rows must contain ResearchDomainGoldSignalMemoryQualityRow")
    return tuple(sorted(value, key=_row_sort_key))


def _normalize_reason_codes(
    value: tuple[str, ...],
    *,
    require_nonempty: bool,
    deduplicate: bool = False,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    if not deduplicate and len(frozenset(value)) != len(value):
        raise ValueError("reason_codes must not contain duplicates")
    for reason_code in value:
        _require_reason_code("reason_code", reason_code)
    unique_values = frozenset(value) if deduplicate else value
    return tuple(
        reason_code
        for reason_code in REASON_CODE_PRIORITY
        if reason_code in unique_values
    )


def _require_status(field_name: str, value: str) -> str:
    if type(value) is not str or value not in (
        STATUS_PASS,
        STATUS_WATCH,
        STATUS_BLOCK,
    ):
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(char not in PUBLIC_REASON_CODE_CHARS for char in value):
        raise ValueError(f"{field_name} must be public-safe")
    if value not in REASON_CODE_PRIORITY:
        raise ValueError(f"{field_name} must be a known reason code")
    return value


def _require_public_identifier(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} must be public-safe")
    if any(char not in PUBLIC_IDENTIFIER_CHARS for char in value):
        raise ValueError(f"{field_name} must be public-safe")
    if lowered != value:
        raise ValueError(f"{field_name} must be canonical")
    return value


def _as_optional_utc(field_name: str, value: datetime | None) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    if value.microsecond != 0:
        raise ValueError(f"{field_name} must be whole-second precision")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_nonnegative_whole_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return _quantize_count(decimal_value)


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{field_name} must be in the unit interval")
    return _quantize_ratio(decimal_value)


def _quantize_count(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(COUNT_QUANTUM)


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name) is not True:
            raise ValueError(f"{label} must keep {flag_name}=True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} payload keys must be strings")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains non public-safe text")


def _require_sha256_digest(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be exactly str")
    if len(value) != SHA256_HEX_LENGTH:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _report_values_without_digest(
    report: ResearchDomainGoldSignalMemoryQualityReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest")
    return values


def _digest_from_values(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload("digest payload", payload)
    encoded = dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")
