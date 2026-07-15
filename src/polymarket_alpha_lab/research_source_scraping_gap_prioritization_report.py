"""Pure public gap-priority report for research collection planning."""

from __future__ import annotations

from dataclasses import InitVar, asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_SOURCE_SCRAPING_GAP_PRIORITIZATION_CONFIG_VERSION = (
    "research-source-scraping-gap-prioritization-v0"
)

STATUSES = ("pass", "watch", "block")
NO_GAPS_REASON = "research_source_scraping_gap_prioritization_no_gaps"
CLEAR_REASON = "research_source_scraping_gap_prioritization_clear"
STALE_FRESHNESS_REASON = "research_source_scraping_gap_prioritization_stale_freshness"
WEAK_INDEPENDENCE_REASON = "research_source_scraping_gap_prioritization_weak_independence"
THIN_DOMAIN_REASON = "research_source_scraping_gap_prioritization_thin_domain_coverage"
CONTRADICTION_REASON = "research_source_scraping_gap_prioritization_contradiction_exposure"
URGENCY_REASON = "research_source_scraping_gap_prioritization_analyst_urgency"
REASON_CODES = (
    NO_GAPS_REASON,
    STALE_FRESHNESS_REASON,
    WEAK_INDEPENDENCE_REASON,
    THIN_DOMAIN_REASON,
    CONTRADICTION_REASON,
    URGENCY_REASON,
    CLEAR_REASON,
)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FRESHNESS_WEIGHT = Decimal("0.250000")
INDEPENDENCE_WEIGHT = Decimal("0.200000")
DOMAIN_WEIGHT = Decimal("0.200000")
CONTRADICTION_WEIGHT = Decimal("0.200000")
URGENCY_WEIGHT = Decimal("0.150000")

CONFIG_PUBLIC_PAYLOAD_FIELDS = (
    "config_version",
    "freshness_watch_age_seconds",
    "freshness_block_age_seconds",
    "independence_watch_floor",
    "independence_block_floor",
    "domain_coverage_watch_floor",
    "domain_coverage_block_floor",
    "contradiction_watch_ratio",
    "contradiction_block_ratio",
    "analyst_urgency_watch_ratio",
    "analyst_urgency_block_ratio",
    "paper_only",
    "report_only",
    "readonly",
)
REPORT_PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "config",
    "gap_count",
    "collection_gap_count",
    "block_gap_count",
    "watch_gap_count",
    "max_freshest_source_age_seconds",
    "min_independent_source_ratio",
    "min_domain_coverage_ratio",
    "max_contradiction_exposure_ratio",
    "max_analyst_urgency_ratio",
    "average_priority_score",
    "status",
    "reason_codes",
    "priority_rows",
    "derived_validation_digest",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PUBLIC_PAYLOAD_FIELDS = (
    "public_gap_key",
    "domain_key",
    "collection_gap_count",
    "freshest_source_age_seconds",
    "freshness_pressure_score",
    "independent_source_ratio",
    "independence_gap_score",
    "domain_coverage_ratio",
    "domain_gap_score",
    "contradiction_exposure_ratio",
    "analyst_urgency_ratio",
    "priority_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("candidate", "_", "id"),
    _join_parts("candidate", "-"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "slug"),
    _join_parts("market", "-"),
    _join_parts("que", "stion"),
    _join_parts("u", "r", "l"),
    _join_parts("te", "xt"),
    _join_parts("d", "s", "n"),
    _join_parts("table", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tr", "ade"),
    _join_parts("h", "t", "t", "p"),
    _join_parts("postgres", "://"),
    _join_parts("private", "-", "source"),
    _join_parts("source", "_", "id"),
    _join_parts("internal", "-", "endpoint"),
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} must not be subclassed")


@dataclass(frozen=True)
class ResearchSourceScrapingGapPrioritizationConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_SOURCE_SCRAPING_GAP_PRIORITIZATION_CONFIG_VERSION
    freshness_watch_age_seconds: Decimal = Decimal("1800.000000")
    freshness_block_age_seconds: Decimal = Decimal("7200.000000")
    independence_watch_floor: Decimal = Decimal("0.600000")
    independence_block_floor: Decimal = Decimal("0.250000")
    domain_coverage_watch_floor: Decimal = Decimal("0.700000")
    domain_coverage_block_floor: Decimal = Decimal("0.400000")
    contradiction_watch_ratio: Decimal = Decimal("0.400000")
    contradiction_block_ratio: Decimal = Decimal("0.750000")
    analyst_urgency_watch_ratio: Decimal = Decimal("0.500000")
    analyst_urgency_block_ratio: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingGapPrioritizationConfig, "config")
        _require_supported_config_version(self.config_version)
        for field_name in (
            "freshness_watch_age_seconds",
            "freshness_block_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "independence_watch_floor",
            "independence_block_floor",
            "domain_coverage_watch_floor",
            "domain_coverage_block_floor",
            "contradiction_watch_ratio",
            "contradiction_block_ratio",
            "analyst_urgency_watch_ratio",
            "analyst_urgency_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        if self.freshness_block_age_seconds < self.freshness_watch_age_seconds:
            raise ValueError("freshness_block_age_seconds must not be below watch age")
        if self.independence_block_floor > self.independence_watch_floor:
            raise ValueError("independence_block_floor must not exceed watch floor")
        if self.domain_coverage_block_floor > self.domain_coverage_watch_floor:
            raise ValueError("domain_coverage_block_floor must not exceed watch floor")
        if self.contradiction_block_ratio < self.contradiction_watch_ratio:
            raise ValueError("contradiction_block_ratio must not be below watch ratio")
        if self.analyst_urgency_block_ratio < self.analyst_urgency_watch_ratio:
            raise ValueError("analyst_urgency_block_ratio must not be below watch ratio")
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceScrapingGapPrioritizationInput(_FinalPublicDataclass):
    public_gap_key: str
    domain_key: str
    collection_gap_count: Decimal
    freshest_source_age_seconds: Decimal
    independent_source_ratio: Decimal
    domain_coverage_ratio: Decimal
    contradiction_exposure_ratio: Decimal
    analyst_urgency_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingGapPrioritizationInput, "input")
        object.__setattr__(
            self,
            "public_gap_key",
            _require_public_key("public_gap_key", self.public_gap_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_key("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "collection_gap_count",
            _require_positive_count("collection_gap_count", self.collection_gap_count),
        )
        object.__setattr__(
            self,
            "freshest_source_age_seconds",
            _require_nonnegative_decimal(
                "freshest_source_age_seconds",
                self.freshest_source_age_seconds,
            ),
        )
        for field_name in (
            "independent_source_ratio",
            "domain_coverage_ratio",
            "contradiction_exposure_ratio",
            "analyst_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceScrapingGapPrioritizationRow(_FinalPublicDataclass):
    public_gap_key: str
    domain_key: str
    collection_gap_count: Decimal
    freshest_source_age_seconds: Decimal
    freshness_pressure_score: Decimal
    independent_source_ratio: Decimal
    independence_gap_score: Decimal
    domain_coverage_ratio: Decimal
    domain_gap_score: Decimal
    contradiction_exposure_ratio: Decimal
    analyst_urgency_ratio: Decimal
    priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    validation_config: InitVar[
        ResearchSourceScrapingGapPrioritizationConfig | None
    ] = None

    def __post_init__(
        self,
        validation_config: ResearchSourceScrapingGapPrioritizationConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchSourceScrapingGapPrioritizationRow, "row")
        object.__setattr__(
            self,
            "public_gap_key",
            _require_public_key("public_gap_key", self.public_gap_key),
        )
        object.__setattr__(
            self,
            "domain_key",
            _require_public_key("domain_key", self.domain_key),
        )
        object.__setattr__(
            self,
            "collection_gap_count",
            _require_positive_count(
                "collection_gap_count",
                self.collection_gap_count,
            ),
        )
        object.__setattr__(
            self,
            "freshest_source_age_seconds",
            _require_nonnegative_decimal(
                "freshest_source_age_seconds",
                self.freshest_source_age_seconds,
            ),
        )
        for field_name in (
            "freshness_pressure_score",
            "independent_source_ratio",
            "independence_gap_score",
            "domain_coverage_ratio",
            "domain_gap_score",
            "contradiction_exposure_ratio",
            "analyst_urgency_ratio",
            "priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self, validation_config)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceScrapingGapPrioritizationReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    config: ResearchSourceScrapingGapPrioritizationConfig
    gap_count: Decimal
    collection_gap_count: Decimal
    block_gap_count: Decimal
    watch_gap_count: Decimal
    max_freshest_source_age_seconds: Decimal
    min_independent_source_ratio: Decimal
    min_domain_coverage_ratio: Decimal
    max_contradiction_exposure_ratio: Decimal
    max_analyst_urgency_ratio: Decimal
    average_priority_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    priority_rows: tuple[ResearchSourceScrapingGapPrioritizationRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourceScrapingGapPrioritizationReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_supported_config_version(self.config_version)
        if type(self.config) is not ResearchSourceScrapingGapPrioritizationConfig:
            raise ValueError(
                "config must be a ResearchSourceScrapingGapPrioritizationConfig",
            )
        _revalidate_config(self.config)
        require_paper_only_flags("config", self.config)
        if self.config.config_version != self.config_version:
            raise ValueError("config_version must match config")
        for field_name in (
            "gap_count",
            "collection_gap_count",
            "block_gap_count",
            "watch_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_freshest_source_age_seconds",
            _require_nonnegative_decimal(
                "max_freshest_source_age_seconds",
                self.max_freshest_source_age_seconds,
            ),
        )
        for field_name in (
            "min_independent_source_ratio",
            "min_domain_coverage_ratio",
            "max_contradiction_exposure_ratio",
            "max_analyst_urgency_ratio",
            "average_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "priority_rows",
            _normalize_priority_rows(self.priority_rows, config=self.config),
        )
        _validate_report(self)
        _require_or_set_digest(self)
        require_paper_only_flags("report", self)


def build_research_source_scraping_gap_prioritization_report(
    inputs: list[ResearchSourceScrapingGapPrioritizationInput]
    | tuple[ResearchSourceScrapingGapPrioritizationInput, ...],
    *,
    config: ResearchSourceScrapingGapPrioritizationConfig,
    generated_at: datetime,
) -> ResearchSourceScrapingGapPrioritizationReport:
    if type(config) is not ResearchSourceScrapingGapPrioritizationConfig:
        raise ValueError(
            "config must be a ResearchSourceScrapingGapPrioritizationConfig",
        )
    _revalidate_config(config)
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _priority_rows(_normalize_inputs(inputs), config=config)
    return ResearchSourceScrapingGapPrioritizationReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        config=config,
        gap_count=_count(len(rows)),
        collection_gap_count=_sum_rows(rows, "collection_gap_count"),
        block_gap_count=_count(sum(row.status == "block" for row in rows)),
        watch_gap_count=_count(sum(row.status == "watch" for row in rows)),
        max_freshest_source_age_seconds=_max_rows(rows, "freshest_source_age_seconds"),
        min_independent_source_ratio=_min_rows(rows, "independent_source_ratio"),
        min_domain_coverage_ratio=_min_rows(rows, "domain_coverage_ratio"),
        max_contradiction_exposure_ratio=_max_rows(rows, "contradiction_exposure_ratio"),
        max_analyst_urgency_ratio=_max_rows(rows, "analyst_urgency_ratio"),
        average_priority_score=_ratio(_sum_rows(rows, "priority_score"), _count(len(rows))),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        priority_rows=rows,
    )


def research_source_scraping_gap_prioritization_report_payload(
    report: ResearchSourceScrapingGapPrioritizationReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScrapingGapPrioritizationReport:
        raise ValueError(
            "report must be a ResearchSourceScrapingGapPrioritizationReport",
        )
    require_paper_only_flags("report", report)
    _validate_report(report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_scraping_gap_prioritization_public_payload(payload)
    return payload


def validate_research_source_scraping_gap_prioritization_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    try:
        _reject_public_payload(payload)
    except RecursionError as exc:
        raise ValueError("public payload nesting is too deep") from exc
    _verify_public_digest(payload)
    _validate_public_payload_schema(payload)
    return True


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceScrapingGapPrioritizationInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceScrapingGapPrioritizationInput:
            raise ValueError(
                "inputs must contain ResearchSourceScrapingGapPrioritizationInput",
            )
        _revalidate_input(row)
        require_paper_only_flags("input", row)
        if row.public_gap_key in seen:
            raise ValueError("inputs must be unique by public_gap_key")
        seen.add(row.public_gap_key)
    return tuple(sorted(rows, key=lambda row: (row.domain_key, row.public_gap_key)))


def _revalidate_input(
    value: ResearchSourceScrapingGapPrioritizationInput,
) -> None:
    canonical = ResearchSourceScrapingGapPrioritizationInput(
        public_gap_key=value.public_gap_key,
        domain_key=value.domain_key,
        collection_gap_count=value.collection_gap_count,
        freshest_source_age_seconds=value.freshest_source_age_seconds,
        independent_source_ratio=value.independent_source_ratio,
        domain_coverage_ratio=value.domain_coverage_ratio,
        contradiction_exposure_ratio=value.contradiction_exposure_ratio,
        analyst_urgency_ratio=value.analyst_urgency_ratio,
        paper_only=value.paper_only,
        report_only=value.report_only,
        readonly=value.readonly,
    )
    if _json_ready(value) != _json_ready(canonical):
        raise ValueError("input fields must retain canonical values")


def _priority_rows(
    rows: tuple[ResearchSourceScrapingGapPrioritizationInput, ...],
    *,
    config: ResearchSourceScrapingGapPrioritizationConfig,
) -> tuple[ResearchSourceScrapingGapPrioritizationRow, ...]:
    return tuple(
        sorted(
            (_priority_row(row, config=config) for row in rows),
            key=_row_sort_key,
        ),
    )


def _priority_row(
    row: ResearchSourceScrapingGapPrioritizationInput,
    *,
    config: ResearchSourceScrapingGapPrioritizationConfig,
) -> ResearchSourceScrapingGapPrioritizationRow:
    freshness_pressure_score = _freshness_pressure_score(row, config=config)
    independence_gap_score = _complement_ratio(row.independent_source_ratio)
    domain_gap_score = _complement_ratio(row.domain_coverage_ratio)
    reason_codes = _row_reason_codes(row, config=config)
    return ResearchSourceScrapingGapPrioritizationRow(
        public_gap_key=row.public_gap_key,
        domain_key=row.domain_key,
        collection_gap_count=row.collection_gap_count,
        freshest_source_age_seconds=row.freshest_source_age_seconds,
        freshness_pressure_score=freshness_pressure_score,
        independent_source_ratio=row.independent_source_ratio,
        independence_gap_score=independence_gap_score,
        domain_coverage_ratio=row.domain_coverage_ratio,
        domain_gap_score=domain_gap_score,
        contradiction_exposure_ratio=row.contradiction_exposure_ratio,
        analyst_urgency_ratio=row.analyst_urgency_ratio,
        priority_score=_priority_score(
            freshness_pressure_score=freshness_pressure_score,
            independence_gap_score=independence_gap_score,
            domain_gap_score=domain_gap_score,
            contradiction_exposure_ratio=row.contradiction_exposure_ratio,
            analyst_urgency_ratio=row.analyst_urgency_ratio,
        ),
        status=_row_status(row, reason_codes=reason_codes, config=config),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _freshness_pressure_score(
    row: ResearchSourceScrapingGapPrioritizationInput
    | ResearchSourceScrapingGapPrioritizationRow,
    *,
    config: ResearchSourceScrapingGapPrioritizationConfig,
) -> Decimal:
    return min(
        _ratio(row.freshest_source_age_seconds, config.freshness_block_age_seconds),
        ONE,
    )


def _priority_score(
    *,
    freshness_pressure_score: Decimal,
    independence_gap_score: Decimal,
    domain_gap_score: Decimal,
    contradiction_exposure_ratio: Decimal,
    analyst_urgency_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return (
            freshness_pressure_score * FRESHNESS_WEIGHT
            + independence_gap_score * INDEPENDENCE_WEIGHT
            + domain_gap_score * DOMAIN_WEIGHT
            + contradiction_exposure_ratio * CONTRADICTION_WEIGHT
            + analyst_urgency_ratio * URGENCY_WEIGHT
        ).quantize(QUANT)


def _row_reason_codes(
    row: ResearchSourceScrapingGapPrioritizationInput
    | ResearchSourceScrapingGapPrioritizationRow,
    *,
    config: ResearchSourceScrapingGapPrioritizationConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if row.freshest_source_age_seconds >= config.freshness_watch_age_seconds:
        reasons.append(STALE_FRESHNESS_REASON)
    if row.independent_source_ratio <= config.independence_watch_floor:
        reasons.append(WEAK_INDEPENDENCE_REASON)
    if row.domain_coverage_ratio <= config.domain_coverage_watch_floor:
        reasons.append(THIN_DOMAIN_REASON)
    if row.contradiction_exposure_ratio >= config.contradiction_watch_ratio:
        reasons.append(CONTRADICTION_REASON)
    if row.analyst_urgency_ratio >= config.analyst_urgency_watch_ratio:
        reasons.append(URGENCY_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _row_status(
    row: ResearchSourceScrapingGapPrioritizationInput
    | ResearchSourceScrapingGapPrioritizationRow,
    *,
    reason_codes: tuple[str, ...],
    config: ResearchSourceScrapingGapPrioritizationConfig,
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if (
        row.freshest_source_age_seconds >= config.freshness_block_age_seconds
        or row.independent_source_ratio <= config.independence_block_floor
        or row.domain_coverage_ratio <= config.domain_coverage_block_floor
        or row.contradiction_exposure_ratio >= config.contradiction_block_ratio
        or row.analyst_urgency_ratio >= config.analyst_urgency_block_ratio
    ):
        return "block"
    return "watch"


def _row_sort_key(
    row: ResearchSourceScrapingGapPrioritizationRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_RANK[row.status],
        row.priority_score.copy_negate(),
        row.domain_key,
        row.public_gap_key,
    )


def _report_status(rows: tuple[ResearchSourceScrapingGapPrioritizationRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceScrapingGapPrioritizationRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_GAPS_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code not in (NO_GAPS_REASON, CLEAR_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _normalize_priority_rows(
    value: object,
    *,
    config: ResearchSourceScrapingGapPrioritizationConfig,
) -> tuple[ResearchSourceScrapingGapPrioritizationRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("priority_rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[Decimal, Decimal, str, str] | None = None
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchSourceScrapingGapPrioritizationRow:
            raise ValueError(
                "priority_rows must contain ResearchSourceScrapingGapPrioritizationRow",
            )
        _revalidate_row(row, config)
        require_paper_only_flags("row", row)
        if row.public_gap_key in seen:
            raise ValueError("priority_rows must contain unique public_gap_key values")
        seen.add(row.public_gap_key)
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("priority_rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _validate_row(
    row: ResearchSourceScrapingGapPrioritizationRow,
    config: ResearchSourceScrapingGapPrioritizationConfig | None,
) -> None:
    if row.independence_gap_score != _complement_ratio(
        row.independent_source_ratio,
    ):
        raise ValueError("independence_gap_score must match independent_source_ratio")
    if row.domain_gap_score != _complement_ratio(row.domain_coverage_ratio):
        raise ValueError("domain_gap_score must match domain_coverage_ratio")
    if config is not None:
        if type(config) is not ResearchSourceScrapingGapPrioritizationConfig:
            raise ValueError(
                "validation_config must be a "
                "ResearchSourceScrapingGapPrioritizationConfig",
            )
        require_paper_only_flags("validation_config", config)
        if row.freshness_pressure_score != _freshness_pressure_score(
            row,
            config=config,
        ):
            raise ValueError(
                "freshness_pressure_score must match freshest_source_age_seconds",
            )
    if row.priority_score != _priority_score(
        freshness_pressure_score=row.freshness_pressure_score,
        independence_gap_score=row.independence_gap_score,
        domain_gap_score=row.domain_gap_score,
        contradiction_exposure_ratio=row.contradiction_exposure_ratio,
        analyst_urgency_ratio=row.analyst_urgency_ratio,
    ):
        raise ValueError("priority_score must match row components")
    if config is None:
        raise ValueError("validation_config is required to validate row derivatives")
    expected_reason_codes = _row_reason_codes(row, config=config)
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")
    if row.status != _row_status(
        row,
        reason_codes=expected_reason_codes,
        config=config,
    ):
        raise ValueError("status must match row inputs")


def _validate_report(report: ResearchSourceScrapingGapPrioritizationReport) -> None:
    _revalidate_config(report.config)
    for row in report.priority_rows:
        _revalidate_row(row, report.config)
        _validate_row(row, report.config)
    if report.gap_count != _count(len(report.priority_rows)):
        raise ValueError("gap_count must match priority_rows")
    if report.collection_gap_count != _sum_rows(report.priority_rows, "collection_gap_count"):
        raise ValueError("collection_gap_count must match priority_rows")
    if report.block_gap_count != _count(sum(row.status == "block" for row in report.priority_rows)):
        raise ValueError("block_gap_count must match priority_rows")
    if report.watch_gap_count != _count(sum(row.status == "watch" for row in report.priority_rows)):
        raise ValueError("watch_gap_count must match priority_rows")
    if report.max_freshest_source_age_seconds != _max_rows(
        report.priority_rows,
        "freshest_source_age_seconds",
    ):
        raise ValueError("max_freshest_source_age_seconds must match priority_rows")
    if report.min_independent_source_ratio != _min_rows(
        report.priority_rows,
        "independent_source_ratio",
    ):
        raise ValueError("min_independent_source_ratio must match priority_rows")
    if report.min_domain_coverage_ratio != _min_rows(
        report.priority_rows,
        "domain_coverage_ratio",
    ):
        raise ValueError("min_domain_coverage_ratio must match priority_rows")
    if report.max_contradiction_exposure_ratio != _max_rows(
        report.priority_rows,
        "contradiction_exposure_ratio",
    ):
        raise ValueError("max_contradiction_exposure_ratio must match priority_rows")
    if report.max_analyst_urgency_ratio != _max_rows(
        report.priority_rows,
        "analyst_urgency_ratio",
    ):
        raise ValueError("max_analyst_urgency_ratio must match priority_rows")
    if report.average_priority_score != _ratio(
        _sum_rows(report.priority_rows, "priority_score"),
        _count(len(report.priority_rows)),
    ):
        raise ValueError("average_priority_score must match priority_rows")
    if report.reason_codes != _report_reason_codes(report.priority_rows):
        raise ValueError("reason_codes must match priority_rows")
    if report.status != _report_status(report.priority_rows):
        raise ValueError("status must match priority_rows")


def _revalidate_row(
    row: ResearchSourceScrapingGapPrioritizationRow,
    config: ResearchSourceScrapingGapPrioritizationConfig,
) -> None:
    if type(row) is not ResearchSourceScrapingGapPrioritizationRow:
        raise ValueError(
            "row must be a ResearchSourceScrapingGapPrioritizationRow",
        )
    canonical = ResearchSourceScrapingGapPrioritizationRow(
        **{
            field_name: getattr(row, field_name)
            for field_name in ROW_PUBLIC_PAYLOAD_FIELDS
        },
        validation_config=config,
    )
    if _json_ready(row) != _json_ready(canonical):
        raise ValueError("row fields must retain canonical values")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return _quantize_decimal("count value", Decimal(value))


def _sum_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum((getattr(row, field_name) for row in rows), ZERO)
    return _require_nonnegative_decimal(
        field_name,
        total,
    )


def _max_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return max(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    )


def _min_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return min(
        _require_nonnegative_decimal(field_name, getattr(row, field_name))
        for row in rows
    )


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    previous_index = -1
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be known")
        index = REASON_CODES.index(reason_code)
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        if index <= previous_index:
            raise ValueError("reason_codes must follow deterministic sequence")
        previous_index = index
        seen.add(reason_code)
    return reason_codes


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_key(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    if any(_contains_unsafe_public_fragment(part) for part in (field_name, value)):
        raise ValueError(f"{field_name} must be public-safe")
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must use public-safe characters")
    return value


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_supported_config_version(value: object) -> None:
    _require_canonical_string("config_version", value)
    if value != DEFAULT_RESEARCH_SOURCE_SCRAPING_GAP_PRIORITIZATION_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")


def _revalidate_config(
    value: ResearchSourceScrapingGapPrioritizationConfig,
) -> None:
    if type(value) is not ResearchSourceScrapingGapPrioritizationConfig:
        raise ValueError(
            "config must be a ResearchSourceScrapingGapPrioritizationConfig",
        )
    canonical = ResearchSourceScrapingGapPrioritizationConfig(
        **{
            field_name: getattr(value, field_name)
            for field_name in CONFIG_PUBLIC_PAYLOAD_FIELDS
        },
    )
    if _json_ready(value) != _json_ready(canonical):
        raise ValueError("config fields must retain canonical values")


def _require_ratio(field_name: str, value: object) -> Decimal:
    ratio = _require_nonnegative_raw_decimal(field_name, value)
    if ratio > ONE:
        raise ValueError(f"{field_name} must not exceed one")
    return _quantize_decimal(field_name, ratio)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    raw = _require_nonnegative_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    with localcontext(DECIMAL_CONTEXT):
        integral = raw.to_integral_value()
    if raw != integral:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize_decimal(field_name, raw)


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    raw = _require_nonnegative_raw_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        integral = raw.to_integral_value()
    if raw != integral:
        raise ValueError(f"{field_name} must be a whole Decimal")
    return _quantize_decimal(field_name, raw)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    raw = _require_nonnegative_raw_decimal(field_name, value)
    if raw <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    normalized = _quantize_decimal(field_name, raw)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    return _quantize_decimal(
        field_name,
        _require_nonnegative_raw_decimal(field_name, value),
    )


def _require_nonnegative_raw_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.is_zero() and value.is_signed():
        raise ValueError(f"{field_name} must not use negative zero")
    if value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value


def _quantize_decimal(field_name: str, value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must fit the decimal context") from exc


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    numerator_value = _require_nonnegative_decimal("ratio numerator", numerator)
    denominator_value = _require_nonnegative_decimal("ratio denominator", denominator)
    if denominator_value == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator_value / denominator_value).quantize(QUANT)


def _complement_ratio(value: Decimal) -> Decimal:
    ratio = _require_ratio("ratio complement value", value)
    with localcontext(DECIMAL_CONTEXT):
        return (ONE - ratio).quantize(QUANT)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_or_set_digest(report: ResearchSourceScrapingGapPrioritizationReport) -> None:
    if type(report.derived_validation_digest) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _report_digest(report)
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected)
        return
    _require_sha256_digest(
        "derived_validation_digest",
        report.derived_validation_digest,
    )
    if report.derived_validation_digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _report_digest(report: ResearchSourceScrapingGapPrioritizationReport) -> str:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _canonical_digest(payload)


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = _require_sha256_digest(
        "derived_validation_digest",
        payload.get("derived_validation_digest"),
    )
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    if digest != _canonical_digest(unsigned):
        raise ValueError("derived_validation_digest does not match public payload")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_fields("payload", payload, REPORT_PUBLIC_PAYLOAD_FIELDS)
    config = _config_from_public_payload(payload["config"])
    report = ResearchSourceScrapingGapPrioritizationReport(
        generated_at=_public_payload_datetime(
            "payload.generated_at",
            payload["generated_at"],
        ),
        config_version=_require_payload_string(
            "payload.config_version",
            payload["config_version"],
        ),
        config=config,
        gap_count=_public_payload_count("payload.gap_count", payload["gap_count"]),
        collection_gap_count=_public_payload_count(
            "payload.collection_gap_count",
            payload["collection_gap_count"],
        ),
        block_gap_count=_public_payload_count(
            "payload.block_gap_count",
            payload["block_gap_count"],
        ),
        watch_gap_count=_public_payload_count(
            "payload.watch_gap_count",
            payload["watch_gap_count"],
        ),
        max_freshest_source_age_seconds=_public_payload_nonnegative_decimal(
            "payload.max_freshest_source_age_seconds",
            payload["max_freshest_source_age_seconds"],
        ),
        min_independent_source_ratio=_public_payload_ratio(
            "payload.min_independent_source_ratio",
            payload["min_independent_source_ratio"],
        ),
        min_domain_coverage_ratio=_public_payload_ratio(
            "payload.min_domain_coverage_ratio",
            payload["min_domain_coverage_ratio"],
        ),
        max_contradiction_exposure_ratio=_public_payload_ratio(
            "payload.max_contradiction_exposure_ratio",
            payload["max_contradiction_exposure_ratio"],
        ),
        max_analyst_urgency_ratio=_public_payload_ratio(
            "payload.max_analyst_urgency_ratio",
            payload["max_analyst_urgency_ratio"],
        ),
        average_priority_score=_public_payload_ratio(
            "payload.average_priority_score",
            payload["average_priority_score"],
        ),
        status=_require_payload_string("payload.status", payload["status"]),
        reason_codes=_public_payload_reason_codes(
            "payload.reason_codes",
            payload["reason_codes"],
        ),
        priority_rows=tuple(
            _row_from_public_payload(item, index=index, config=config)
            for index, item in enumerate(
                _require_payload_list(
                    "payload.priority_rows",
                    payload["priority_rows"],
                ),
            )
        ),
        derived_validation_digest=_require_payload_string(
            "payload.derived_validation_digest",
            payload["derived_validation_digest"],
        ),
        paper_only=_require_payload_true(
            "payload.paper_only",
            payload["paper_only"],
        ),
        report_only=_require_payload_true(
            "payload.report_only",
            payload["report_only"],
        ),
        readonly=_require_payload_true("payload.readonly", payload["readonly"]),
    )
    if _json_ready(report) != payload:
        raise ValueError("payload must use the canonical public schema")


def _config_from_public_payload(
    value: object,
) -> ResearchSourceScrapingGapPrioritizationConfig:
    label = "payload.config"
    payload = _require_payload_object(label, value)
    _require_payload_fields(label, payload, CONFIG_PUBLIC_PAYLOAD_FIELDS)
    return ResearchSourceScrapingGapPrioritizationConfig(
        config_version=_require_payload_string(
            f"{label}.config_version",
            payload["config_version"],
        ),
        freshness_watch_age_seconds=_public_payload_positive_decimal(
            f"{label}.freshness_watch_age_seconds",
            payload["freshness_watch_age_seconds"],
        ),
        freshness_block_age_seconds=_public_payload_positive_decimal(
            f"{label}.freshness_block_age_seconds",
            payload["freshness_block_age_seconds"],
        ),
        independence_watch_floor=_public_payload_ratio(
            f"{label}.independence_watch_floor",
            payload["independence_watch_floor"],
        ),
        independence_block_floor=_public_payload_ratio(
            f"{label}.independence_block_floor",
            payload["independence_block_floor"],
        ),
        domain_coverage_watch_floor=_public_payload_ratio(
            f"{label}.domain_coverage_watch_floor",
            payload["domain_coverage_watch_floor"],
        ),
        domain_coverage_block_floor=_public_payload_ratio(
            f"{label}.domain_coverage_block_floor",
            payload["domain_coverage_block_floor"],
        ),
        contradiction_watch_ratio=_public_payload_ratio(
            f"{label}.contradiction_watch_ratio",
            payload["contradiction_watch_ratio"],
        ),
        contradiction_block_ratio=_public_payload_ratio(
            f"{label}.contradiction_block_ratio",
            payload["contradiction_block_ratio"],
        ),
        analyst_urgency_watch_ratio=_public_payload_ratio(
            f"{label}.analyst_urgency_watch_ratio",
            payload["analyst_urgency_watch_ratio"],
        ),
        analyst_urgency_block_ratio=_public_payload_ratio(
            f"{label}.analyst_urgency_block_ratio",
            payload["analyst_urgency_block_ratio"],
        ),
        paper_only=_require_payload_true(
            f"{label}.paper_only",
            payload["paper_only"],
        ),
        report_only=_require_payload_true(
            f"{label}.report_only",
            payload["report_only"],
        ),
        readonly=_require_payload_true(f"{label}.readonly", payload["readonly"]),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
    config: ResearchSourceScrapingGapPrioritizationConfig,
) -> ResearchSourceScrapingGapPrioritizationRow:
    label = f"payload.priority_rows[{index}]"
    payload = _require_payload_object(label, value)
    _require_payload_fields(label, payload, ROW_PUBLIC_PAYLOAD_FIELDS)
    return ResearchSourceScrapingGapPrioritizationRow(
        public_gap_key=_require_payload_string(
            f"{label}.public_gap_key",
            payload["public_gap_key"],
        ),
        domain_key=_require_payload_string(
            f"{label}.domain_key",
            payload["domain_key"],
        ),
        collection_gap_count=_public_payload_positive_count(
            f"{label}.collection_gap_count",
            payload["collection_gap_count"],
        ),
        freshest_source_age_seconds=_public_payload_nonnegative_decimal(
            f"{label}.freshest_source_age_seconds",
            payload["freshest_source_age_seconds"],
        ),
        freshness_pressure_score=_public_payload_ratio(
            f"{label}.freshness_pressure_score",
            payload["freshness_pressure_score"],
        ),
        independent_source_ratio=_public_payload_ratio(
            f"{label}.independent_source_ratio",
            payload["independent_source_ratio"],
        ),
        independence_gap_score=_public_payload_ratio(
            f"{label}.independence_gap_score",
            payload["independence_gap_score"],
        ),
        domain_coverage_ratio=_public_payload_ratio(
            f"{label}.domain_coverage_ratio",
            payload["domain_coverage_ratio"],
        ),
        domain_gap_score=_public_payload_ratio(
            f"{label}.domain_gap_score",
            payload["domain_gap_score"],
        ),
        contradiction_exposure_ratio=_public_payload_ratio(
            f"{label}.contradiction_exposure_ratio",
            payload["contradiction_exposure_ratio"],
        ),
        analyst_urgency_ratio=_public_payload_ratio(
            f"{label}.analyst_urgency_ratio",
            payload["analyst_urgency_ratio"],
        ),
        priority_score=_public_payload_ratio(
            f"{label}.priority_score",
            payload["priority_score"],
        ),
        status=_require_payload_string(f"{label}.status", payload["status"]),
        reason_codes=_public_payload_reason_codes(
            f"{label}.reason_codes",
            payload["reason_codes"],
        ),
        paper_only=_require_payload_true(
            f"{label}.paper_only",
            payload["paper_only"],
        ),
        report_only=_require_payload_true(
            f"{label}.report_only",
            payload["report_only"],
        ),
        readonly=_require_payload_true(f"{label}.readonly", payload["readonly"]),
        validation_config=config,
    )


def _require_payload_fields(
    label: str,
    payload: dict[str, Any],
    expected_fields: tuple[str, ...],
) -> None:
    if tuple(payload) != expected_fields:
        raise ValueError(f"{label} fields must match the public schema")


def _require_payload_object(label: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    return value


def _require_payload_list(label: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{label} must be a JSON array")
    return value


def _require_payload_string(label: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{label} must be a string")
    return value


def _require_payload_true(label: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{label} must be True")
    return True


def _public_payload_decimal(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:
        raise ValueError(f"{label} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{label} must be finite")
    return parsed


def _public_payload_positive_decimal(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    normalized = _require_positive_decimal(
        label,
        _public_payload_decimal(label, text),
    )
    if str(normalized) != text:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _public_payload_nonnegative_decimal(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    normalized = _require_nonnegative_decimal(
        label,
        _public_payload_decimal(label, text),
    )
    if str(normalized) != text:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _public_payload_ratio(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    normalized = _require_ratio(label, _public_payload_decimal(label, text))
    if str(normalized) != text:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _public_payload_count(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    normalized = _require_nonnegative_count(
        label,
        _public_payload_decimal(label, text),
    )
    if str(normalized) != text:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _public_payload_positive_count(label: str, value: object) -> Decimal:
    text = _require_payload_string(label, value)
    normalized = _require_positive_count(
        label,
        _public_payload_decimal(label, text),
    )
    if str(normalized) != text:
        raise ValueError(f"{label} must be a canonical Decimal string")
    return normalized


def _public_payload_datetime(label: str, value: object) -> datetime:
    text = _require_payload_string(label, value)
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 datetime string") from exc
    normalized = _as_utc(label, parsed)
    if normalized.isoformat() != text:
        raise ValueError(f"{label} must be a canonical UTC datetime string")
    return normalized


def _public_payload_reason_codes(label: str, value: object) -> tuple[str, ...]:
    return tuple(
        _require_payload_string(f"{label}[{index}]", item)
        for index, item in enumerate(_require_payload_list(label, value))
    )


def _canonical_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_sha256_digest(label: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise ValueError(f"{label} must be a lowercase sha256 hex digest")
    return value


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be a Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("JSON datetime value", value).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_payload(
    value: object,
    active_container_ids: set[int] | None = None,
    label: str = "payload",
) -> None:
    if active_container_ids is None:
        active_container_ids = set()
    if isinstance(value, dict):
        if type(value) is not dict:
            raise ValueError(f"{label} must be a JSON object")
        container_id = id(value)
        if container_id in active_container_ids:
            raise ValueError("public payload must not contain cyclic values")
        active_container_ids.add(container_id)
        try:
            for key, item in value.items():
                if type(key) is not str:
                    raise ValueError("public payload keys must be strings")
                if _contains_unsafe_public_fragment(key):
                    raise ValueError("public payload contains unsafe key")
                if (
                    key in {"paper_only", "report_only", "readonly"}
                    and item is not True
                ):
                    raise ValueError(f"{key} must be True")
                _reject_public_payload(
                    item,
                    active_container_ids,
                    f"{label}.{key}",
                )
        finally:
            active_container_ids.remove(container_id)
        return
    if isinstance(value, list):
        if type(value) is not list:
            raise ValueError(f"{label} must be a JSON array")
        container_id = id(value)
        if container_id in active_container_ids:
            raise ValueError("public payload must not contain cyclic values")
        active_container_ids.add(container_id)
        try:
            for index, item in enumerate(value):
                _reject_public_payload(
                    item,
                    active_container_ids,
                    f"{label}[{index}]",
                )
        finally:
            active_container_ids.remove(container_id)
        return
    if type(value) in (int, float) or isinstance(value, Decimal):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, str):
        if type(value) is not str:
            raise ValueError(f"{label} must be a string")
        if _contains_unsafe_public_fragment(value):
            raise ValueError("public payload contains unsafe value")
        return
    if value is None or type(value) is bool:
        return
    raise ValueError("public payload values must be JSON-compatible")


def _contains_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPING_GAP_PRIORITIZATION_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceScrapingGapPrioritizationConfig",
    "ResearchSourceScrapingGapPrioritizationInput",
    "ResearchSourceScrapingGapPrioritizationReport",
    "ResearchSourceScrapingGapPrioritizationRow",
    "build_research_source_scraping_gap_prioritization_report",
    "research_source_scraping_gap_prioritization_report_payload",
    "validate_research_source_scraping_gap_prioritization_public_payload",
)
