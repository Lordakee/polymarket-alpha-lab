"""Pure report-only signal health checks for event categories."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_EVENT_CATEGORY_SIGNAL_HEALTH_CONFIG_VERSION = (
    "research-event-category-signal-health-report-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

NO_INPUTS_REASON = "research_event_category_signal_health_block_no_inputs"
MISSING_CATEGORY_REASON = "research_event_category_signal_health_block_missing_category"
PASS_REASON = "research_event_category_signal_health_pass"
WATCH_REASON = "research_event_category_signal_health_watch"
BLOCK_REASON = "research_event_category_signal_health_block"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

DEFAULT_TARGET_CATEGORIES = (
    "basketball",
    "commodities",
    "crypto",
    "equities",
    "football",
    "politics",
)

_STATUS_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("raw", "_"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("candidate", "_", "id"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("s", "lug"),
    _join_parts("question"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("http"),
    _join_parts(":", "/", "/"),
    _join_parts("dsn"),
    _join_parts("table"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("liv", "e"),
    _join_parts("siz", "ing"),
    _join_parts("pos", "ition"),
    _join_parts("b", "uy"),
    _join_parts("s", "ell"),
    _join_parts("rec", "ommend"),
)

__all__ = (
    "DEFAULT_RESEARCH_EVENT_CATEGORY_SIGNAL_HEALTH_CONFIG_VERSION",
    "ResearchEventCategorySignalHealthConfig",
    "ResearchEventCategorySignalHealthInput",
    "ResearchEventCategorySignalHealthReasonCodeCount",
    "ResearchEventCategorySignalHealthReport",
    "ResearchEventCategorySignalHealthRow",
    "build_research_event_category_signal_health_report",
    "research_event_category_signal_health_report_digest",
    "research_event_category_signal_health_report_payload",
)


@dataclass(frozen=True)
class ResearchEventCategorySignalHealthConfig:
    config_version: str = DEFAULT_RESEARCH_EVENT_CATEGORY_SIGNAL_HEALTH_CONFIG_VERSION
    target_categories: tuple[str, ...] = DEFAULT_TARGET_CATEGORIES
    pass_min_signal_health_score: Decimal = Decimal("0.800000")
    watch_min_signal_health_score: Decimal = Decimal("0.550000")
    pass_max_source_age_seconds: Decimal = Decimal("86400.000000")
    block_min_source_age_seconds: Decimal = Decimal("604800.000000")
    min_source_count: Decimal = Decimal("2.000000")
    block_below_dimension_ratio: Decimal = Decimal("0.400000")
    source_weight: Decimal = Decimal("0.250000")
    mechanics_weight: Decimal = Decimal("0.250000")
    memory_weight: Decimal = Decimal("0.250000")
    resolution_weight: Decimal = Decimal("0.250000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategorySignalHealthConfig:
            raise TypeError(
                "ResearchEventCategorySignalHealthConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategorySignalHealthConfig:
            raise ValueError(
                "config must be exactly ResearchEventCategorySignalHealthConfig",
            )
        _require_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "target_categories",
            _normalize_public_string_tuple(
                "target_categories",
                self.target_categories,
                allow_empty=False,
                require_sorted=True,
            ),
        )
        for field_name in (
            "pass_min_signal_health_score",
            "watch_min_signal_health_score",
            "block_below_dimension_ratio",
            "source_weight",
            "mechanics_weight",
            "memory_weight",
            "resolution_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "pass_max_source_age_seconds",
            "block_min_source_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_source_count",
            _require_positive_whole_decimal("min_source_count", self.min_source_count),
        )
        if self.pass_min_signal_health_score <= self.watch_min_signal_health_score:
            raise ValueError(
                "pass_min_signal_health_score must exceed watch_min_signal_health_score",
            )
        if self.block_min_source_age_seconds <= self.pass_max_source_age_seconds:
            raise ValueError(
                "block_min_source_age_seconds must exceed pass_max_source_age_seconds",
            )
        weight_sum = _quantize(
            self.source_weight
            + self.mechanics_weight
            + self.memory_weight
            + self.resolution_weight,
        )
        if weight_sum != ONE:
            raise ValueError("dimension weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchEventCategorySignalHealthInput:
    category: str
    source_freshness_ratio: Decimal
    freshest_source_age_seconds: Decimal
    corroborating_source_count: Decimal
    mechanics_health_ratio: Decimal
    team_memory_coverage_ratio: Decimal
    resolution_clarity_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategorySignalHealthInput:
            raise TypeError(
                "ResearchEventCategorySignalHealthInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategorySignalHealthInput:
            raise ValueError("input must be exactly ResearchEventCategorySignalHealthInput")
        _require_public_string("category", self.category)
        for field_name in (
            "source_freshness_ratio",
            "mechanics_health_ratio",
            "team_memory_coverage_ratio",
            "resolution_clarity_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshest_source_age_seconds",
            _require_nonnegative_decimal(
                "freshest_source_age_seconds",
                self.freshest_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "corroborating_source_count",
            _require_nonnegative_whole_decimal(
                "corroborating_source_count",
                self.corroborating_source_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchEventCategorySignalHealthRow:
    category: str
    public_status: str
    input_count: Decimal
    source_freshness_ratio: Decimal
    source_age_health_ratio: Decimal
    source_count_health_ratio: Decimal
    source_health_ratio: Decimal
    freshest_source_age_seconds: Decimal
    corroborating_source_count: Decimal
    mechanics_health_ratio: Decimal
    team_memory_coverage_ratio: Decimal
    resolution_clarity_ratio: Decimal
    signal_health_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategorySignalHealthRow:
            raise TypeError(
                "ResearchEventCategorySignalHealthRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategorySignalHealthRow:
            raise ValueError("row must be exactly ResearchEventCategorySignalHealthRow")
        _require_public_string("category", self.category)
        _require_public_status("public_status", self.public_status)
        object.__setattr__(
            self,
            "input_count",
            _require_nonnegative_whole_decimal("input_count", self.input_count),
        )
        for field_name in (
            "source_freshness_ratio",
            "source_age_health_ratio",
            "source_count_health_ratio",
            "source_health_ratio",
            "mechanics_health_ratio",
            "team_memory_coverage_ratio",
            "resolution_clarity_ratio",
            "signal_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "freshest_source_age_seconds",
            _require_nonnegative_decimal(
                "freshest_source_age_seconds",
                self.freshest_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "corroborating_source_count",
            _require_nonnegative_whole_decimal(
                "corroborating_source_count",
                self.corroborating_source_count,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        expected_status_reason = f"research_event_category_signal_health_{self.public_status}"
        if self.public_status == STATUS_BLOCK and self.input_count == ZERO:
            if MISSING_CATEGORY_REASON not in self.reason_codes:
                raise ValueError("public_status must match reason_codes")
        elif expected_status_reason not in self.reason_codes:
            raise ValueError("public_status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchEventCategorySignalHealthReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategorySignalHealthReasonCodeCount:
            raise TypeError(
                "ResearchEventCategorySignalHealthReasonCodeCount does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategorySignalHealthReasonCodeCount:
            raise ValueError(
                "reason count must be exactly "
                "ResearchEventCategorySignalHealthReasonCodeCount",
            )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_whole_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)
        _reject_unsafe_public_payload("reason count", _payload_value(asdict(self)))


@dataclass(frozen=True)
class ResearchEventCategorySignalHealthReport:
    generated_at: datetime
    config_version: str
    report_status: str
    category_count: Decimal
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_source_count: Decimal
    mechanics_gap_count: Decimal
    memory_gap_count: Decimal
    resolution_gap_count: Decimal
    average_signal_health_score: Decimal
    rows: tuple[ResearchEventCategorySignalHealthRow, ...]
    reason_code_counts: tuple[ResearchEventCategorySignalHealthReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchEventCategorySignalHealthReport:
            raise TypeError(
                "ResearchEventCategorySignalHealthReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchEventCategorySignalHealthReport:
            raise ValueError("report must be exactly ResearchEventCategorySignalHealthReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_public_status("report_status", self.report_status)
        for field_name in (
            "category_count",
            "input_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_source_count",
            "mechanics_gap_count",
            "memory_gap_count",
            "resolution_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_signal_health_score",
            _require_ratio_decimal(
                "average_signal_health_score",
                self.average_signal_health_score,
            ),
        )
        object.__setattr__(self, "rows", _require_row_tuple("rows", self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_count_tuple("reason_code_counts", self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes("reason_codes", self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", _payload_value(asdict(self)))

    @property
    def payload(self) -> dict[str, Any]:
        return research_event_category_signal_health_report_payload(self)


def build_research_event_category_signal_health_report(
    rows: object,
    *,
    config: ResearchEventCategorySignalHealthConfig | None = None,
    generated_at: datetime,
) -> ResearchEventCategorySignalHealthReport:
    cfg = config or ResearchEventCategorySignalHealthConfig()
    if type(cfg) is not ResearchEventCategorySignalHealthConfig:
        raise TypeError("config must be exactly ResearchEventCategorySignalHealthConfig")
    _require_hard_flags("config", cfg)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_input_rows(rows)
    target_categories = frozenset(cfg.target_categories)
    unknown_categories = tuple(
        sorted(row.category for row in input_rows if row.category not in target_categories),
    )
    if unknown_categories:
        raise ValueError("input category must be present in target_categories")

    grouped: dict[str, list[ResearchEventCategorySignalHealthInput]] = {
        category: [] for category in cfg.target_categories
    }
    for row in input_rows:
        grouped[row.category].append(row)

    report_rows = tuple(
        _build_category_row(
            category=category,
            rows=tuple(grouped[category]),
            config=cfg,
        )
        for category in cfg.target_categories
    )
    reason_counts = _reason_code_counts(report_rows)
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": cfg.config_version,
        "report_status": _report_status(report_rows),
        "category_count": _count_decimal(report_rows),
        "input_count": _sum_decimal(row.input_count for row in report_rows),
        "pass_count": _sum_if(report_rows, lambda row: row.public_status == STATUS_PASS),
        "watch_count": _sum_if(report_rows, lambda row: row.public_status == STATUS_WATCH),
        "block_count": _sum_if(report_rows, lambda row: row.public_status == STATUS_BLOCK),
        "stale_source_count": _sum_if(
            report_rows,
            lambda row: "source_age_block" in row.reason_codes
            or "source_age_watch" in row.reason_codes,
        ),
        "mechanics_gap_count": _sum_if(
            report_rows,
            lambda row: "mechanics_health_block" in row.reason_codes
            or "mechanics_health_watch" in row.reason_codes,
        ),
        "memory_gap_count": _sum_if(
            report_rows,
            lambda row: "team_memory_block" in row.reason_codes
            or "team_memory_watch" in row.reason_codes,
        ),
        "resolution_gap_count": _sum_if(
            report_rows,
            lambda row: "resolution_clarity_block" in row.reason_codes
            or "resolution_clarity_watch" in row.reason_codes,
        ),
        "average_signal_health_score": _average(
            row.signal_health_score for row in report_rows
        ),
        "rows": report_rows,
        "reason_code_counts": reason_counts,
        "reason_codes": tuple(item.reason_code for item in reason_counts),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values["derived_validation_digest"] = _derived_validation_digest(values)
    return ResearchEventCategorySignalHealthReport(**values)


def research_event_category_signal_health_report_payload(
    report: ResearchEventCategorySignalHealthReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventCategorySignalHealthReport:
        _require_hard_flags("report", report)
        payload = _payload_value(asdict(report))
        _reject_unsafe_public_payload("report payload", payload)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("report payload", report)
        _require_payload_flags(report)
        payload = _payload_value(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _require_payload_digest(payload)
        return payload
    raise TypeError("report must be exactly ResearchEventCategorySignalHealthReport")


def research_event_category_signal_health_report_digest(
    report: ResearchEventCategorySignalHealthReport,
) -> dict[str, Any]:
    if type(report) is not ResearchEventCategorySignalHealthReport:
        raise TypeError("report must be exactly ResearchEventCategorySignalHealthReport")
    payload = research_event_category_signal_health_report_payload(report)
    return {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "report_status": payload["report_status"],
        "category_count": payload["category_count"],
        "input_count": payload["input_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "reason_codes": payload["reason_codes"],
        "derived_validation_digest": payload["derived_validation_digest"],
    }


def _build_category_row(
    *,
    category: str,
    rows: tuple[ResearchEventCategorySignalHealthInput, ...],
    config: ResearchEventCategorySignalHealthConfig,
) -> ResearchEventCategorySignalHealthRow:
    if not rows:
        return ResearchEventCategorySignalHealthRow(
            category=category,
            public_status=STATUS_BLOCK,
            input_count=ZERO,
            source_freshness_ratio=ZERO,
            source_age_health_ratio=ZERO,
            source_count_health_ratio=ZERO,
            source_health_ratio=ZERO,
            freshest_source_age_seconds=ZERO,
            corroborating_source_count=ZERO,
            mechanics_health_ratio=ZERO,
            team_memory_coverage_ratio=ZERO,
            resolution_clarity_ratio=ZERO,
            signal_health_score=ZERO,
            reason_codes=(
                MISSING_CATEGORY_REASON,
                "mechanics_health_block",
                "resolution_clarity_block",
                "source_count_block",
                "source_freshness_block",
                "team_memory_block",
            ),
        )

    source_freshness_ratio = _average(row.source_freshness_ratio for row in rows)
    freshest_source_age_seconds = min(row.freshest_source_age_seconds for row in rows)
    corroborating_source_count = _sum_decimal(row.corroborating_source_count for row in rows)
    source_age_health_ratio = _source_age_health_ratio(
        freshest_source_age_seconds,
        config,
    )
    source_count_health_ratio = _ratio(
        corroborating_source_count,
        config.min_source_count,
    )
    source_health_ratio = _average(
        (source_freshness_ratio, source_age_health_ratio, source_count_health_ratio),
    )
    mechanics_health_ratio = _average(row.mechanics_health_ratio for row in rows)
    team_memory_coverage_ratio = _average(
        row.team_memory_coverage_ratio for row in rows
    )
    resolution_clarity_ratio = _average(row.resolution_clarity_ratio for row in rows)
    signal_health_score = _signal_health_score(
        source_health_ratio=source_health_ratio,
        mechanics_health_ratio=mechanics_health_ratio,
        team_memory_coverage_ratio=team_memory_coverage_ratio,
        resolution_clarity_ratio=resolution_clarity_ratio,
        config=config,
    )
    public_status = _category_status(
        source_health_ratio=source_health_ratio,
        source_age_health_ratio=source_age_health_ratio,
        mechanics_health_ratio=mechanics_health_ratio,
        team_memory_coverage_ratio=team_memory_coverage_ratio,
        resolution_clarity_ratio=resolution_clarity_ratio,
        signal_health_score=signal_health_score,
        config=config,
    )
    return ResearchEventCategorySignalHealthRow(
        category=category,
        public_status=public_status,
        input_count=_count_decimal(rows),
        source_freshness_ratio=source_freshness_ratio,
        source_age_health_ratio=source_age_health_ratio,
        source_count_health_ratio=source_count_health_ratio,
        source_health_ratio=source_health_ratio,
        freshest_source_age_seconds=freshest_source_age_seconds,
        corroborating_source_count=corroborating_source_count,
        mechanics_health_ratio=mechanics_health_ratio,
        team_memory_coverage_ratio=team_memory_coverage_ratio,
        resolution_clarity_ratio=resolution_clarity_ratio,
        signal_health_score=signal_health_score,
        reason_codes=_row_reason_codes(
            public_status=public_status,
            source_freshness_ratio=source_freshness_ratio,
            source_age_health_ratio=source_age_health_ratio,
            source_count_health_ratio=source_count_health_ratio,
            mechanics_health_ratio=mechanics_health_ratio,
            team_memory_coverage_ratio=team_memory_coverage_ratio,
            resolution_clarity_ratio=resolution_clarity_ratio,
            config=config,
            input_reason_codes=tuple(
                reason_code for row in rows for reason_code in row.reason_codes
            ),
        ),
    )


def _category_status(
    *,
    source_health_ratio: Decimal,
    source_age_health_ratio: Decimal,
    mechanics_health_ratio: Decimal,
    team_memory_coverage_ratio: Decimal,
    resolution_clarity_ratio: Decimal,
    signal_health_score: Decimal,
    config: ResearchEventCategorySignalHealthConfig,
) -> str:
    dimensions = (
        source_health_ratio,
        mechanics_health_ratio,
        team_memory_coverage_ratio,
        resolution_clarity_ratio,
    )
    if (
        source_age_health_ratio == ZERO
        or any(value < config.block_below_dimension_ratio for value in dimensions)
        or signal_health_score < config.watch_min_signal_health_score
    ):
        return STATUS_BLOCK
    if (
        signal_health_score < config.pass_min_signal_health_score
        or source_age_health_ratio < ONE
        or any(value < config.pass_min_signal_health_score for value in dimensions)
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    *,
    public_status: str,
    source_freshness_ratio: Decimal,
    source_age_health_ratio: Decimal,
    source_count_health_ratio: Decimal,
    mechanics_health_ratio: Decimal,
    team_memory_coverage_ratio: Decimal,
    resolution_clarity_ratio: Decimal,
    config: ResearchEventCategorySignalHealthConfig,
    input_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"research_event_category_signal_health_{public_status}"}
    reason_codes.add(
        _dimension_reason(
            "source_freshness",
            source_freshness_ratio,
            pass_threshold=config.pass_min_signal_health_score,
            block_threshold=config.block_below_dimension_ratio,
        ),
    )
    reason_codes.add(
        _source_age_reason(
            source_age_health_ratio,
            pass_threshold=ONE,
            block_threshold=config.block_below_dimension_ratio,
        ),
    )
    reason_codes.add(
        _dimension_reason(
            "source_count",
            source_count_health_ratio,
            pass_threshold=ONE,
            block_threshold=config.block_below_dimension_ratio,
        ),
    )
    reason_codes.add(
        _dimension_reason(
            "mechanics_health",
            mechanics_health_ratio,
            pass_threshold=config.pass_min_signal_health_score,
            block_threshold=config.block_below_dimension_ratio,
        ),
    )
    reason_codes.add(
        _dimension_reason(
            "team_memory",
            team_memory_coverage_ratio,
            pass_threshold=config.pass_min_signal_health_score,
            block_threshold=config.block_below_dimension_ratio,
        ),
    )
    reason_codes.add(
        _dimension_reason(
            "resolution_clarity",
            resolution_clarity_ratio,
            pass_threshold=config.pass_min_signal_health_score,
            block_threshold=config.block_below_dimension_ratio,
        ),
    )
    for reason_code in input_reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _dimension_reason(
    stem: str,
    value: Decimal,
    *,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value < block_threshold:
        return f"{stem}_block"
    if value < pass_threshold:
        return f"{stem}_watch"
    return f"{stem}_pass"


def _source_age_reason(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value <= ZERO:
        return "source_age_block"
    if value < block_threshold:
        return "source_age_block"
    if value < pass_threshold:
        return "source_age_watch"
    return "source_age_pass"


def _source_age_health_ratio(
    value: Decimal,
    config: ResearchEventCategorySignalHealthConfig,
) -> Decimal:
    if value <= config.pass_max_source_age_seconds:
        return ONE
    if value >= config.block_min_source_age_seconds:
        return ZERO
    span = config.block_min_source_age_seconds - config.pass_max_source_age_seconds
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(ONE - ((value - config.pass_max_source_age_seconds) / span))


def _signal_health_score(
    *,
    source_health_ratio: Decimal,
    mechanics_health_ratio: Decimal,
    team_memory_coverage_ratio: Decimal,
    resolution_clarity_ratio: Decimal,
    config: ResearchEventCategorySignalHealthConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(
            (source_health_ratio * config.source_weight)
            + (mechanics_health_ratio * config.mechanics_weight)
            + (team_memory_coverage_ratio * config.memory_weight)
            + (resolution_clarity_ratio * config.resolution_weight),
        )


def _normalize_input_rows(
    rows: object,
) -> tuple[ResearchEventCategorySignalHealthInput, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    return tuple(_coerce_input_row(row) for row in tuple(rows))


def _coerce_input_row(value: object) -> ResearchEventCategorySignalHealthInput:
    if type(value) is ResearchEventCategorySignalHealthInput:
        _require_hard_flags("input", value)
        return value
    _require_hard_flags("input", value)
    return ResearchEventCategorySignalHealthInput(
        category=_field_value(value, "category"),
        source_freshness_ratio=_field_value(value, "source_freshness_ratio"),
        freshest_source_age_seconds=_field_value(value, "freshest_source_age_seconds"),
        corroborating_source_count=_field_value(value, "corroborating_source_count"),
        mechanics_health_ratio=_field_value(value, "mechanics_health_ratio"),
        team_memory_coverage_ratio=_field_value(value, "team_memory_coverage_ratio"),
        resolution_clarity_ratio=_field_value(value, "resolution_clarity_ratio"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _field_value(value: object, field_name: str, default: object = None) -> Any:
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not None:
        return default
    raise ValueError(f"row must provide {field_name}")


def _report_status(rows: tuple[ResearchEventCategorySignalHealthRow, ...]) -> str:
    if any(row.public_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.public_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _reason_code_counts(
    rows: tuple[ResearchEventCategorySignalHealthRow, ...],
) -> tuple[ResearchEventCategorySignalHealthReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    total = _count_decimal(rows)
    return tuple(
        ResearchEventCategorySignalHealthReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(count),
            row_ratio=_ratio(_count_decimal(count), total),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _validate_report_consistency(report: ResearchEventCategorySignalHealthReport) -> None:
    rows = report.rows
    if report.category_count != _count_decimal(rows):
        raise ValueError("category_count must match rows")
    if report.input_count != _sum_decimal(row.input_count for row in rows):
        raise ValueError("input_count must match rows")
    if report.pass_count != _sum_if(rows, lambda row: row.public_status == STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _sum_if(rows, lambda row: row.public_status == STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _sum_if(rows, lambda row: row.public_status == STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_signal_health_score != _average(
        row.signal_health_score for row in rows
    ):
        raise ValueError("average_signal_health_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    expected_reason_counts = _reason_code_counts(rows)
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in expected_reason_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    if report.derived_validation_digest != _derived_validation_digest(asdict(report)):
        raise ValueError("derived_validation_digest does not match report payload")


def _require_row_tuple(
    field_name: str,
    value: object,
) -> tuple[ResearchEventCategorySignalHealthRow, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for row in value:
        if type(row) is not ResearchEventCategorySignalHealthRow:
            raise TypeError(f"{field_name} must contain ResearchEventCategorySignalHealthRow")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(value, key=lambda row: row.category))
    if value != sorted_rows:
        raise ValueError(f"{field_name} must be sorted by category")
    return value


def _require_reason_count_tuple(
    field_name: str,
    value: object,
) -> tuple[ResearchEventCategorySignalHealthReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    for item in value:
        if type(item) is not ResearchEventCategorySignalHealthReasonCodeCount:
            raise TypeError(
                f"{field_name} must contain "
                "ResearchEventCategorySignalHealthReasonCodeCount",
            )
        _require_hard_flags("reason count", item)
    sorted_items = tuple(sorted(value, key=lambda item: (-item.count, item.reason_code)))
    if value != sorted_items:
        raise ValueError(f"{field_name} must be sorted by count and reason_code")
    return value


def _normalize_public_string_tuple(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
    require_sorted: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    if not allow_empty and not value:
        raise ValueError(f"{field_name} must not be empty")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    if require_sorted and normalized != tuple(sorted(normalized)):
        raise ValueError(f"{field_name} must be sorted")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(normalized))


def _normalize_report_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise TypeError(f"{field_name} must be exactly tuple")
    normalized = tuple(_require_public_string(field_name, item) for item in value)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return normalized


def _require_public_status(field_name: str, value: object) -> str:
    value = _require_public_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty public string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must use public identifier characters")
    if any(fragment in value for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO or value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    value = _require_decimal(field_name, value)
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(value)


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_decimal(field_name, value)
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize(value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    value = _require_nonnegative_whole_decimal(field_name, value)
    if value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise TypeError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if not hasattr(value, field_name):
            raise ValueError(f"{label} must expose {field_name}")
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _require_payload_flags(value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"payload {field_name} must be True")


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise TypeError(f"{field_name} must be exactly str")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    return value


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match report payload")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise TypeError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count_decimal(value: object) -> Decimal:
    return _quantize(Decimal(len(value) if not isinstance(value, int) else value))


def _sum_decimal(values: Iterable[Decimal]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _sum_if(
    rows: tuple[ResearchEventCategorySignalHealthRow, ...],
    predicate: Callable[[ResearchEventCategorySignalHealthRow], bool],
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if predicate(row)))


def _average(values: Iterable[Decimal]) -> Decimal:
    normalized = tuple(values)
    if not normalized:
        return ZERO
    return _ratio(_sum_decimal(normalized), _count_decimal(normalized))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(min(ONE, numerator / denominator))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _payload_value(value: object) -> Any:
    if type(value) is Decimal:
        return f"{value.quantize(QUANT)}"
    if type(value) is datetime:
        return _datetime_payload(value)
    if type(value) in (str, bool) or value is None:
        return value
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return _payload_value(asdict(value))
    raise TypeError(f"unsupported payload value: {type(value).__name__}")


def _datetime_payload(value: datetime) -> str:
    value = _as_utc("datetime", value)
    return value.isoformat().replace("+00:00", "Z")


def _derived_validation_digest(values: object) -> str:
    payload = _payload_value(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
    elif isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public value")
