"""Pure report-only aggregate event-domain coverage gap report."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "EVENT_DOMAIN_COVERAGE_GAP_LANES",
    "ResearchEventDomainCoverageGapConfig",
    "ResearchEventDomainCoverageGapObservation",
    "ResearchEventDomainCoverageGapReport",
    "ResearchEventDomainCoverageGapRow",
    "STATUSES",
    "build_research_event_domain_coverage_gap_report",
    "research_event_domain_coverage_gap_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-event-domain-coverage-gap-report-v0"
EVENT_DOMAIN_COVERAGE_GAP_LANES = (
    "politics",
    "macro",
    "crypto",
    "rates",
    "fx",
    "tech",
    "energy",
    "weather",
    "sports",
)
LANE_SORT = {
    lane: Decimal(index)
    for index, lane in enumerate(EVENT_DOMAIN_COVERAGE_GAP_LANES)
}

PASS = "pass"
WATCH = "watch"
BLOCK = "block"
STATUSES = (PASS, WATCH, BLOCK)
STATUS_SORT = {BLOCK: Decimal("0"), WATCH: Decimal("1"), PASS: Decimal("2")}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")

REASON_CODE_SEQUENCE = (
    "coverage_scarcity_block",
    "stale_memory_block",
    "source_gap_block",
    "review_load_block",
    "escalation_urgency_block",
    "coverage_scarcity_watch",
    "stale_memory_watch",
    "source_gap_watch",
    "review_load_watch",
    "escalation_urgency_watch",
    "coverage_gap_clear",
)

REPORT_NUMERIC_FIELDS = (
    "lane_count",
    "domain_bucket_count",
    "pass_count",
    "watch_count",
    "block_count",
    "average_gap_pressure_score",
    "max_gap_pressure_score",
    "min_coverage_ratio",
    "max_memory_age_hours",
    "total_source_gap_count",
    "max_review_load_ratio",
    "max_escalation_urgency_score",
)
ROW_NUMERIC_FIELDS = (
    "coverage_ratio",
    "memory_age_hours",
    "source_gap_count",
    "review_load_ratio",
    "escalation_urgency_score",
    "coverage_scarcity_pressure",
    "stale_memory_pressure",
    "source_gap_pressure",
    "review_load_pressure",
    "gap_pressure_score",
)
PUBLIC_LABEL_RE = re.compile(r"^[a-z][a-z0-9-]{1,127}$")
FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate_id",
    "candidate-id",
    "candidateid",
    "event_id",
    "event-id",
    "eventid",
    "market_id",
    "market-id",
    "marketid",
    "market_question",
    "market-question",
    "marketquestion",
    "question",
    "source_id",
    "source-id",
    "sourceid",
    "source_url",
    "source-url",
    "sourceurl",
    "source_text",
    "source-text",
    "sourcetext",
    "condition_id",
    "condition-id",
    "conditionid",
    "dsn",
    "table_name",
    "table-name",
    "tablename",
    "db_table",
    "db-table",
    "dbtable",
    "://",
    "http://",
    "https://",
    "www.",
    "slug",
    "wallet",
    "order",
    "trade",
    "buy",
    "sell",
    "position",
    "network",
    "database",
    "auth",
    "token",
    "private_key",
    "secret",
    "credential",
    "signing",
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
class ResearchEventDomainCoverageGapConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_CONFIG_VERSION
    coverage_watch_floor: Decimal = Decimal("0.800000")
    coverage_block_floor: Decimal = Decimal("0.500000")
    memory_watch_age_hours: Decimal = Decimal("48.000000")
    memory_block_age_hours: Decimal = Decimal("168.000000")
    source_gap_watch_count: Decimal = Decimal("1")
    source_gap_block_count: Decimal = Decimal("3")
    review_load_watch_threshold: Decimal = Decimal("0.750000")
    review_load_block_threshold: Decimal = Decimal("1.000000")
    escalation_urgency_watch_threshold: Decimal = Decimal("0.400000")
    escalation_urgency_block_threshold: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventDomainCoverageGapConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "coverage_watch_floor",
            "coverage_block_floor",
            "review_load_watch_threshold",
            "review_load_block_threshold",
            "escalation_urgency_watch_threshold",
            "escalation_urgency_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "memory_watch_age_hours",
            "memory_block_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_measure(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "source_gap_watch_count",
            "source_gap_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        if self.coverage_block_floor >= self.coverage_watch_floor:
            raise ValueError("coverage_watch_floor must exceed coverage_block_floor")
        if self.memory_block_age_hours <= self.memory_watch_age_hours:
            raise ValueError(
                "memory_block_age_hours must exceed memory_watch_age_hours",
            )
        if self.source_gap_block_count <= self.source_gap_watch_count:
            raise ValueError(
                "source_gap_block_count must exceed source_gap_watch_count",
            )
        if self.review_load_block_threshold <= self.review_load_watch_threshold:
            raise ValueError(
                "review_load_block_threshold must exceed "
                "review_load_watch_threshold",
            )
        if (
            self.escalation_urgency_block_threshold
            <= self.escalation_urgency_watch_threshold
        ):
            raise ValueError(
                "escalation_urgency_block_threshold must exceed "
                "escalation_urgency_watch_threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchEventDomainCoverageGapObservation(_FinalPublicDataclass):
    lane: str
    domain_bucket: str
    coverage_ratio: Decimal
    memory_age_hours: Decimal
    source_gap_count: Decimal
    review_load_ratio: Decimal
    escalation_urgency_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchEventDomainCoverageGapObservation,
            "observation",
        )
        _require_lane(self.lane)
        _require_public_aggregate_label("domain_bucket", self.domain_bucket)
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_ratio("coverage_ratio", self.coverage_ratio),
        )
        object.__setattr__(
            self,
            "memory_age_hours",
            _normalize_nonnegative_measure(
                "memory_age_hours",
                self.memory_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_count("source_gap_count", self.source_gap_count),
        )
        object.__setattr__(
            self,
            "review_load_ratio",
            _normalize_nonnegative_measure(
                "review_load_ratio",
                self.review_load_ratio,
            ),
        )
        object.__setattr__(
            self,
            "escalation_urgency_score",
            _normalize_ratio(
                "escalation_urgency_score",
                self.escalation_urgency_score,
            ),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchEventDomainCoverageGapRow(_FinalPublicDataclass):
    lane: str
    domain_bucket: str
    coverage_ratio: Decimal
    memory_age_hours: Decimal
    source_gap_count: Decimal
    review_load_ratio: Decimal
    escalation_urgency_score: Decimal
    coverage_scarcity_pressure: Decimal
    stale_memory_pressure: Decimal
    source_gap_pressure: Decimal
    review_load_pressure: Decimal
    gap_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventDomainCoverageGapRow, "row")
        _require_lane(self.lane)
        _require_public_aggregate_label("domain_bucket", self.domain_bucket)
        object.__setattr__(
            self,
            "coverage_ratio",
            _normalize_ratio("coverage_ratio", self.coverage_ratio),
        )
        object.__setattr__(
            self,
            "memory_age_hours",
            _normalize_nonnegative_measure(
                "memory_age_hours",
                self.memory_age_hours,
            ),
        )
        object.__setattr__(
            self,
            "source_gap_count",
            _normalize_count("source_gap_count", self.source_gap_count),
        )
        object.__setattr__(
            self,
            "review_load_ratio",
            _normalize_nonnegative_measure(
                "review_load_ratio",
                self.review_load_ratio,
            ),
        )
        for field_name in (
            "escalation_urgency_score",
            "coverage_scarcity_pressure",
            "stale_memory_pressure",
            "source_gap_pressure",
            "review_load_pressure",
            "gap_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchEventDomainCoverageGapReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    lane_count: Decimal
    domain_bucket_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_gap_pressure_score: Decimal
    max_gap_pressure_score: Decimal
    min_coverage_ratio: Decimal
    max_memory_age_hours: Decimal
    total_source_gap_count: Decimal
    max_review_load_ratio: Decimal
    max_escalation_urgency_score: Decimal
    status: str
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchEventDomainCoverageGapRow, ...]
    derived_payload_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchEventDomainCoverageGapReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "lane_count",
            "domain_bucket_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_source_gap_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_gap_pressure_score",
            "max_gap_pressure_score",
            "min_coverage_ratio",
            "max_escalation_urgency_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_memory_age_hours",
            "max_review_load_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_measure(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_digest_or_empty(self.derived_payload_digest)
        _require_hard_flags("report", self)


def build_research_event_domain_coverage_gap_report(
    observations: tuple[ResearchEventDomainCoverageGapObservation, ...],
    *,
    generated_at: datetime,
    config: ResearchEventDomainCoverageGapConfig | None = None,
) -> ResearchEventDomainCoverageGapReport:
    cfg = ResearchEventDomainCoverageGapConfig() if config is None else config
    _require_exact_type(cfg, ResearchEventDomainCoverageGapConfig, "config")
    generated_at_utc = _as_utc("generated_at", generated_at)

    rows = tuple(_row_from_observation(observation, cfg) for observation in observations)
    _reject_duplicate_rows(rows)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    status = _rollup_status(tuple(row.status for row in sorted_rows))
    reason_code_counts = _reason_code_counts(sorted_rows)

    report_without_digest = ResearchEventDomainCoverageGapReport(
        generated_at=generated_at_utc,
        config_version=cfg.config_version,
        lane_count=_count_decimal(len({row.lane for row in sorted_rows})),
        domain_bucket_count=_count_decimal(
            len({(row.lane, row.domain_bucket) for row in sorted_rows}),
        ),
        pass_count=_count_decimal(
            sum(1 for row in sorted_rows if row.status == PASS),
        ),
        watch_count=_count_decimal(
            sum(1 for row in sorted_rows if row.status == WATCH),
        ),
        block_count=_count_decimal(
            sum(1 for row in sorted_rows if row.status == BLOCK),
        ),
        average_gap_pressure_score=_average(
            tuple(row.gap_pressure_score for row in sorted_rows),
        ),
        max_gap_pressure_score=_max_ratio(
            tuple(row.gap_pressure_score for row in sorted_rows),
        ),
        min_coverage_ratio=_min_ratio(
            tuple(row.coverage_ratio for row in sorted_rows),
        ),
        max_memory_age_hours=_max_measure(
            tuple(row.memory_age_hours for row in sorted_rows),
        ),
        total_source_gap_count=_sum_counts(
            tuple(row.source_gap_count for row in sorted_rows),
        ),
        max_review_load_ratio=_max_measure(
            tuple(row.review_load_ratio for row in sorted_rows),
        ),
        max_escalation_urgency_score=_max_ratio(
            tuple(row.escalation_urgency_score for row in sorted_rows),
        ),
        status=status,
        reason_code_counts=reason_code_counts,
        rows=sorted_rows,
        derived_payload_digest="",
    )
    digest = _payload_digest(_payload_without_digest(report_without_digest))
    return ResearchEventDomainCoverageGapReport(
        **{
            **_dataclass_values(report_without_digest),
            "derived_payload_digest": digest,
        },
    )


def research_event_domain_coverage_gap_report_payload(
    report: ResearchEventDomainCoverageGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchEventDomainCoverageGapReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        _reject_unsafe_payload("report payload", payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_payload("report payload", report)
        _require_payload_flags(report)
        if "derived_payload_digest" not in report:
            raise ValueError("derived_payload_digest is required")
        expected_digest = _payload_digest(_payload_without_digest(report))
        if report["derived_payload_digest"] != expected_digest:
            raise ValueError("derived_payload_digest does not match report payload")
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("report payload must be a JSON object")
        return payload
    raise ValueError("report must be a ResearchEventDomainCoverageGapReport")


def _row_from_observation(
    observation: ResearchEventDomainCoverageGapObservation,
    config: ResearchEventDomainCoverageGapConfig,
) -> ResearchEventDomainCoverageGapRow:
    _require_exact_type(
        observation,
        ResearchEventDomainCoverageGapObservation,
        "observation",
    )
    coverage_scarcity_pressure = _clamp_ratio(
        ONE_RATIO - observation.coverage_ratio,
    )
    stale_memory_pressure = _safe_pressure_ratio(
        observation.memory_age_hours,
        config.memory_block_age_hours,
    )
    source_gap_pressure = _safe_pressure_ratio(
        observation.source_gap_count,
        config.source_gap_block_count,
    )
    review_load_pressure = _safe_pressure_ratio(
        observation.review_load_ratio,
        config.review_load_block_threshold,
    )
    gap_pressure_score = _average(
        (
            coverage_scarcity_pressure,
            stale_memory_pressure,
            source_gap_pressure,
            review_load_pressure,
            observation.escalation_urgency_score,
        ),
    )
    reason_codes = _row_reason_codes(observation, config)
    return ResearchEventDomainCoverageGapRow(
        lane=observation.lane,
        domain_bucket=observation.domain_bucket,
        coverage_ratio=observation.coverage_ratio,
        memory_age_hours=observation.memory_age_hours,
        source_gap_count=observation.source_gap_count,
        review_load_ratio=observation.review_load_ratio,
        escalation_urgency_score=observation.escalation_urgency_score,
        coverage_scarcity_pressure=coverage_scarcity_pressure,
        stale_memory_pressure=stale_memory_pressure,
        source_gap_pressure=source_gap_pressure,
        review_load_pressure=review_load_pressure,
        gap_pressure_score=gap_pressure_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchEventDomainCoverageGapObservation,
    config: ResearchEventDomainCoverageGapConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.coverage_ratio <= config.coverage_block_floor:
        reason_codes.append("coverage_scarcity_block")
    elif observation.coverage_ratio < config.coverage_watch_floor:
        reason_codes.append("coverage_scarcity_watch")

    if observation.memory_age_hours >= config.memory_block_age_hours:
        reason_codes.append("stale_memory_block")
    elif observation.memory_age_hours >= config.memory_watch_age_hours:
        reason_codes.append("stale_memory_watch")

    if observation.source_gap_count >= config.source_gap_block_count:
        reason_codes.append("source_gap_block")
    elif observation.source_gap_count >= config.source_gap_watch_count:
        reason_codes.append("source_gap_watch")

    if observation.review_load_ratio >= config.review_load_block_threshold:
        reason_codes.append("review_load_block")
    elif observation.review_load_ratio >= config.review_load_watch_threshold:
        reason_codes.append("review_load_watch")

    if observation.escalation_urgency_score >= config.escalation_urgency_block_threshold:
        reason_codes.append("escalation_urgency_block")
    elif observation.escalation_urgency_score >= config.escalation_urgency_watch_threshold:
        reason_codes.append("escalation_urgency_watch")

    if not reason_codes:
        return ("coverage_gap_clear",)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in set(reason_codes)
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return BLOCK
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH
    return PASS


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == BLOCK for status in statuses):
        return BLOCK
    if any(status == WATCH for status in statuses):
        return WATCH
    return PASS


def _reason_code_counts(
    rows: tuple[ResearchEventDomainCoverageGapRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        (reason_code, _count_decimal(counter[reason_code]))
        for reason_code in REASON_CODE_SEQUENCE
        if counter[reason_code]
    )


def _row_sort_key(
    row: ResearchEventDomainCoverageGapRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_SORT[row.status], LANE_SORT[row.lane], row.domain_bucket)


def _reject_duplicate_rows(
    rows: tuple[ResearchEventDomainCoverageGapRow, ...],
) -> None:
    seen: set[tuple[str, str]] = set()
    for row in rows:
        key = (row.lane, row.domain_bucket)
        if key in seen:
            raise ValueError("duplicate lane/domain_bucket observations are not allowed")
        seen.add(key)


def _validate_row_consistency(row: ResearchEventDomainCoverageGapRow) -> None:
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("row status does not match reason_codes")
    if row.status == PASS and row.reason_codes != ("coverage_gap_clear",):
        raise ValueError("pass row must use coverage_gap_clear")


def _normalize_rows(
    rows: tuple[ResearchEventDomainCoverageGapRow, ...],
) -> tuple[ResearchEventDomainCoverageGapRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        _require_exact_type(row, ResearchEventDomainCoverageGapRow, "row")
    return rows


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if not isinstance(reason_codes, tuple) or not reason_codes:
        raise ValueError("reason_codes must be a non-empty tuple")
    for reason_code in reason_codes:
        _require_public_string("reason_code", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"unknown reason_code: {reason_code}")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in set(reason_codes)
    )


def _normalize_reason_code_counts(
    reason_code_counts: tuple[tuple[str, Decimal], ...],
) -> tuple[tuple[str, Decimal], ...]:
    if not isinstance(reason_code_counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[tuple[str, Decimal]] = []
    seen: set[str] = set()
    for item in reason_code_counts:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("reason_code_counts entries must be pairs")
        reason_code, count = item
        _require_public_string("reason_code", reason_code)
        if reason_code not in REASON_CODE_SEQUENCE:
            raise ValueError(f"unknown reason_code: {reason_code}")
        if reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicates")
        seen.add(reason_code)
        normalized.append((reason_code, _normalize_count("reason_code_count", count)))
    return tuple(
        item
        for reason_code in REASON_CODE_SEQUENCE
        for item in normalized
        if item[0] == reason_code
    )


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_ratio(sum(values, ZERO_RATIO) / Decimal(len(values)))


def _safe_pressure_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator <= ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    if value <= ZERO_RATIO:
        return ZERO_RATIO
    if value >= ONE_RATIO:
        return ONE_RATIO
    return _quantize_ratio(value)


def _sum_counts(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_COUNT
    return _normalize_count("total_source_gap_count", sum(values, ZERO_COUNT))


def _max_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _normalize_ratio("max_ratio", max(values))


def _min_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _normalize_ratio("min_ratio", min(values))


def _max_measure(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return _normalize_nonnegative_measure("max_measure", max(values))


def _count_decimal(value: int) -> Decimal:
    return _normalize_count("count", Decimal(value))


def _normalize_ratio(name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_RATIO or decimal_value > ONE_RATIO:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize_ratio(decimal_value)


def _normalize_nonnegative_measure(name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize_ratio(decimal_value)


def _normalize_count(name: str, value: Decimal) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO_COUNT:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{name} must be an integral Decimal")
    return decimal_value.quantize(COUNT_QUANTUM)


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(RATIO_QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal value could not be quantized") from exc


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_lane(value: str) -> None:
    if value not in EVENT_DOMAIN_COVERAGE_GAP_LANES:
        raise ValueError(
            "lane must be one of "
            + ", ".join(EVENT_DOMAIN_COVERAGE_GAP_LANES),
        )


def _require_public_aggregate_label(name: str, value: str) -> None:
    _require_public_string(name, value)
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public aggregate label")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} must be a public aggregate label")


def _require_public_string(name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must not be empty")


def _require_status(name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_exact_type(value: object, expected_type: type[object], name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{name} must be exactly {expected_type.__name__}")


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_digest_or_empty(value: str) -> None:
    if type(value) is not str:
        raise ValueError("derived_payload_digest must be a string")
    if value == "":
        return
    if len(value) != 64:
        raise ValueError("derived_payload_digest must be 64 hex characters")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError("derived_payload_digest must be 64 hex characters") from exc


def _dataclass_values(value: ResearchEventDomainCoverageGapReport) -> dict[str, Any]:
    return {field.name: getattr(value, field.name) for field in fields(value)}


def _payload_without_digest(value: object) -> dict[str, Any]:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    payload = dict(payload)
    payload.pop("derived_payload_digest", None)
    return payload


def _payload_digest(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(rendered.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("payload Decimal values must use exact Decimal")
        if not value.is_finite():
            raise ValueError("payload Decimal values must be finite")
        return str(value)
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("payload numerics must be Decimal-derived strings")
    if type(value) is float:
        raise ValueError("payload must not contain floats")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_payload(label, _json_ready(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            _reject_unsafe_text(label, key)
            _reject_unsafe_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_text(label, value)
        return
    if type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{label} numerics must be Decimal-derived strings")
    if isinstance(value, (float, Decimal)):
        raise ValueError(f"{label} must use JSON-ready Decimal strings")


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{label} contains an unsafe public surface")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for flag_name in FLAG_FIELDS:
        if payload.get(flag_name) is not True:
            raise ValueError(f"{flag_name} must be True")
    rows = payload.get("rows", [])
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        for flag_name in FLAG_FIELDS:
            if row.get(flag_name) is not True:
                raise ValueError(f"row {flag_name} must be True")
