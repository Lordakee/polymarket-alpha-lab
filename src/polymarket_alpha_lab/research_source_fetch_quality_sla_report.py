"""Pure public aggregate fetch quality SLA report for research teams."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags
from polymarket_alpha_lab.team_taxonomy import require_team_category_pair, require_team_id


DEFAULT_RESEARCH_SOURCE_FETCH_QUALITY_SLA_CONFIG_VERSION = (
    "research-source-fetch-quality-sla-report-v0"
)

STATUSES = ("pass", "watch", "block")
NO_BATCHES_REASON = "research_source_fetch_quality_sla_no_fetch_batches"
CLEAR_REASON = "research_source_fetch_quality_sla_clear"
LOW_FETCH_SUCCESS_REASON = "research_source_fetch_quality_sla_low_fetch_success"
STALE_FRESHNESS_AGE_REASON = "research_source_fetch_quality_sla_stale_freshness_age"
LOW_PARSE_QUALITY_REASON = "research_source_fetch_quality_sla_low_parse_quality"
CORROBORATION_NOT_READY_REASON = (
    "research_source_fetch_quality_sla_corroboration_not_ready"
)
RETRY_PRESSURE_REASON = "research_source_fetch_quality_sla_retry_pressure"
MANUAL_REVIEW_URGENT_REASON = "research_source_fetch_quality_sla_manual_review_urgent"
REASON_CODES = (
    NO_BATCHES_REASON,
    LOW_FETCH_SUCCESS_REASON,
    STALE_FRESHNESS_AGE_REASON,
    LOW_PARSE_QUALITY_REASON,
    CORROBORATION_NOT_READY_REASON,
    RETRY_PRESSURE_REASON,
    MANUAL_REVIEW_URGENT_REASON,
    CLEAR_REASON,
)
STATUS_RANK = {
    "block": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("2.000000"),
}

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FETCH_SUCCESS_WEIGHT = Decimal("0.200000")
FRESHNESS_WEIGHT = Decimal("0.200000")
PARSE_QUALITY_WEIGHT = Decimal("0.175000")
CORROBORATION_WEIGHT = Decimal("0.175000")
RETRY_PRESSURE_WEIGHT = Decimal("0.125000")
MANUAL_REVIEW_WEIGHT = Decimal("0.125000")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_TERMS = (
    _join_parts("ra", "w"),
    _join_parts("u", "r", "l"),
    _join_parts("te", "xt"),
    _join_parts("net", "work"),
    _join_parts("data", "base"),
    _join_parts("wa", "llet"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("li", "ve"),
    _join_parts("tra", "de"),
    _join_parts("si", "zing"),
    _join_parts("recommen", "dation"),
    _join_parts("acc", "ount"),
    _join_parts("bro", "ker"),
    _join_parts("cre", "den", "tial"),
)


@dataclass(frozen=True)
class ResearchSourceFetchQualitySlaConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_FETCH_QUALITY_SLA_CONFIG_VERSION
    min_fetch_success_watch_ratio: Decimal = Decimal("0.900000")
    min_fetch_success_block_ratio: Decimal = Decimal("0.700000")
    max_freshness_age_watch_seconds: Decimal = Decimal("3600.000000")
    max_freshness_age_block_seconds: Decimal = Decimal("7200.000000")
    min_parse_quality_watch_score: Decimal = Decimal("0.800000")
    min_parse_quality_block_score: Decimal = Decimal("0.600000")
    min_corroboration_readiness_watch_ratio: Decimal = Decimal("0.750000")
    min_corroboration_readiness_block_ratio: Decimal = Decimal("0.500000")
    max_retry_pressure_watch_ratio: Decimal = Decimal("0.200000")
    max_retry_pressure_block_ratio: Decimal = Decimal("0.500000")
    max_manual_review_urgency_watch_ratio: Decimal = Decimal("0.500000")
    max_manual_review_urgency_block_ratio: Decimal = Decimal("0.850000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceFetchQualitySlaConfig may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceFetchQualitySlaConfig:
            raise ValueError("config must be a ResearchSourceFetchQualitySlaConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "min_fetch_success_watch_ratio",
            "min_fetch_success_block_ratio",
            "min_parse_quality_watch_score",
            "min_parse_quality_block_score",
            "min_corroboration_readiness_watch_ratio",
            "min_corroboration_readiness_block_ratio",
            "max_retry_pressure_watch_ratio",
            "max_retry_pressure_block_ratio",
            "max_manual_review_urgency_watch_ratio",
            "max_manual_review_urgency_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_freshness_age_watch_seconds",
            "max_freshness_age_block_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_fetch_success_block_ratio > self.min_fetch_success_watch_ratio:
            raise ValueError("fetch success block threshold must not exceed watch threshold")
        if self.max_freshness_age_block_seconds < self.max_freshness_age_watch_seconds:
            raise ValueError("freshness age block threshold must not be below watch threshold")
        if self.min_parse_quality_block_score > self.min_parse_quality_watch_score:
            raise ValueError("parse quality block threshold must not exceed watch threshold")
        if (
            self.min_corroboration_readiness_block_ratio
            > self.min_corroboration_readiness_watch_ratio
        ):
            raise ValueError(
                "corroboration readiness block threshold must not exceed watch threshold",
            )
        if self.max_retry_pressure_block_ratio < self.max_retry_pressure_watch_ratio:
            raise ValueError("retry pressure block threshold must not be below watch threshold")
        if (
            self.max_manual_review_urgency_block_ratio
            < self.max_manual_review_urgency_watch_ratio
        ):
            raise ValueError(
                "manual review urgency block threshold must not be below watch threshold",
            )
        require_paper_only_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceFetchQualitySlaInput:
    team_id: str
    category_id: str
    fetch_batch_id: str
    attempted_fetch_count: Decimal
    successful_fetch_count: Decimal
    freshness_age_seconds: Decimal
    parse_quality_score: Decimal
    corroborated_claim_count: Decimal
    required_corroborated_claim_count: Decimal
    retry_attempt_count: Decimal
    manual_review_item_count: Decimal
    manual_review_capacity_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceFetchQualitySlaInput may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceFetchQualitySlaInput:
            raise ValueError("input must be a ResearchSourceFetchQualitySlaInput")
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_canonical_string("fetch_batch_id", self.fetch_batch_id)
        object.__setattr__(
            self,
            "attempted_fetch_count",
            _require_positive_count("attempted_fetch_count", self.attempted_fetch_count),
        )
        for field_name in (
            "successful_fetch_count",
            "freshness_age_seconds",
            "corroborated_claim_count",
            "retry_attempt_count",
            "manual_review_item_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_corroborated_claim_count",
            "manual_review_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "parse_quality_score",
            _require_ratio("parse_quality_score", self.parse_quality_score),
        )
        _validate_input(self)
        require_paper_only_flags("input", self)


@dataclass(frozen=True)
class ResearchSourceFetchQualitySlaRow:
    team_id: str
    category_id: str
    fetch_batch_id: str
    attempted_fetch_count: Decimal
    successful_fetch_count: Decimal
    fetch_success_ratio: Decimal
    freshness_age_seconds: Decimal
    parse_quality_score: Decimal
    corroborated_claim_count: Decimal
    required_corroborated_claim_count: Decimal
    corroboration_readiness_ratio: Decimal
    retry_attempt_count: Decimal
    retry_pressure_ratio: Decimal
    manual_review_item_count: Decimal
    manual_review_capacity_count: Decimal
    manual_review_urgency_ratio: Decimal
    quality_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceFetchQualitySlaRow may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceFetchQualitySlaRow:
            raise ValueError("row must be a ResearchSourceFetchQualitySlaRow")
        object.__setattr__(self, "team_id", require_team_id("team_id", self.team_id))
        require_team_category_pair(
            "team_id",
            self.team_id,
            "category_id",
            self.category_id,
        )
        _require_canonical_string("fetch_batch_id", self.fetch_batch_id)
        object.__setattr__(
            self,
            "attempted_fetch_count",
            _require_positive_count("attempted_fetch_count", self.attempted_fetch_count),
        )
        for field_name in (
            "successful_fetch_count",
            "freshness_age_seconds",
            "corroborated_claim_count",
            "retry_attempt_count",
            "manual_review_item_count",
            "quality_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "required_corroborated_claim_count",
            "manual_review_capacity_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fetch_success_ratio",
            "parse_quality_score",
            "corroboration_readiness_ratio",
            "retry_pressure_ratio",
            "manual_review_urgency_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _validate_row(self)
        require_paper_only_flags("row", self)


@dataclass(frozen=True)
class ResearchSourceFetchQualitySlaReport:
    generated_at: datetime
    config_version: str
    batch_count: Decimal
    attempted_fetch_count: Decimal
    successful_fetch_count: Decimal
    fetch_success_ratio: Decimal
    max_freshness_age_seconds: Decimal
    min_parse_quality_score: Decimal
    min_corroboration_readiness_ratio: Decimal
    retry_attempt_count: Decimal
    retry_pressure_ratio: Decimal
    manual_review_item_count: Decimal
    manual_review_capacity_count: Decimal
    manual_review_urgency_ratio: Decimal
    block_batch_count: Decimal
    watch_batch_count: Decimal
    pass_ready_batch_count: Decimal
    pass_ready_attempted_fetch_count: Decimal
    pass_ready_attempted_fetch_ratio: Decimal
    average_quality_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    quality_rows: tuple[ResearchSourceFetchQualitySlaRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls) -> None:
        raise TypeError("ResearchSourceFetchQualitySlaReport may not be subclassed")

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceFetchQualitySlaReport:
            raise ValueError("report must be a ResearchSourceFetchQualitySlaReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "batch_count",
            "attempted_fetch_count",
            "successful_fetch_count",
            "max_freshness_age_seconds",
            "retry_attempt_count",
            "manual_review_item_count",
            "manual_review_capacity_count",
            "block_batch_count",
            "watch_batch_count",
            "pass_ready_batch_count",
            "pass_ready_attempted_fetch_count",
            "average_quality_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fetch_success_ratio",
            "min_parse_quality_score",
            "min_corroboration_readiness_ratio",
            "retry_pressure_ratio",
            "manual_review_urgency_ratio",
            "pass_ready_attempted_fetch_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(self, "quality_rows", _normalize_quality_rows(self.quality_rows))
        _validate_report(self)
        require_paper_only_flags("report", self)
        _require_or_set_digest(self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_fetch_quality_sla_report_payload(self)


def build_research_source_fetch_quality_sla_report(
    inputs: list[ResearchSourceFetchQualitySlaInput]
    | tuple[ResearchSourceFetchQualitySlaInput, ...],
    *,
    config: ResearchSourceFetchQualitySlaConfig,
    generated_at: datetime,
) -> ResearchSourceFetchQualitySlaReport:
    if type(config) is not ResearchSourceFetchQualitySlaConfig:
        raise ValueError("config must be a ResearchSourceFetchQualitySlaConfig")
    require_paper_only_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = _quality_rows(_normalize_inputs(inputs), config=config)
    attempted_fetch_count = _sum_rows(rows, "attempted_fetch_count")
    successful_fetch_count = _sum_rows(rows, "successful_fetch_count")
    retry_attempt_count = _sum_rows(rows, "retry_attempt_count")
    manual_review_item_count = _sum_rows(rows, "manual_review_item_count")
    manual_review_capacity_count = _sum_rows(rows, "manual_review_capacity_count")
    pass_ready_attempted_fetch_count = _status_sum_rows(
        rows,
        "attempted_fetch_count",
        status="pass",
    )
    return ResearchSourceFetchQualitySlaReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        batch_count=_count(len(rows)),
        attempted_fetch_count=attempted_fetch_count,
        successful_fetch_count=successful_fetch_count,
        fetch_success_ratio=_ratio(successful_fetch_count, attempted_fetch_count),
        max_freshness_age_seconds=_max_rows(rows, "freshness_age_seconds"),
        min_parse_quality_score=_min_rows(rows, "parse_quality_score"),
        min_corroboration_readiness_ratio=_min_rows(
            rows,
            "corroboration_readiness_ratio",
        ),
        retry_attempt_count=retry_attempt_count,
        retry_pressure_ratio=_ratio(retry_attempt_count, attempted_fetch_count),
        manual_review_item_count=manual_review_item_count,
        manual_review_capacity_count=manual_review_capacity_count,
        manual_review_urgency_ratio=_ratio(
            manual_review_item_count,
            manual_review_capacity_count,
        ),
        block_batch_count=_count(sum(row.status == "block" for row in rows)),
        watch_batch_count=_count(sum(row.status == "watch" for row in rows)),
        pass_ready_batch_count=_count(sum(row.status == "pass" for row in rows)),
        pass_ready_attempted_fetch_count=pass_ready_attempted_fetch_count,
        pass_ready_attempted_fetch_ratio=_ratio(
            pass_ready_attempted_fetch_count,
            attempted_fetch_count,
        ),
        average_quality_pressure_score=_ratio(
            _sum_rows(rows, "quality_pressure_score"),
            _count(len(rows)),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        quality_rows=rows,
    )


def research_source_fetch_quality_sla_report_payload(
    report: ResearchSourceFetchQualitySlaReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceFetchQualitySlaReport:
        raise ValueError("report must be a ResearchSourceFetchQualitySlaReport")
    require_paper_only_flags("report", report)
    _require_or_set_digest(report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_public_payload(payload)
    _verify_public_digest(payload)
    return payload


def _normalize_inputs(
    value: object,
) -> tuple[ResearchSourceFetchQualitySlaInput, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("inputs must be a list or tuple")
    rows = tuple(value)
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceFetchQualitySlaInput:
            raise ValueError("inputs must contain ResearchSourceFetchQualitySlaInput")
        require_paper_only_flags("input", row)
        key = (row.category_id, row.team_id, row.fetch_batch_id)
        if key in seen:
            raise ValueError("inputs must be unique by team, category, and batch")
        seen.add(key)
    return tuple(sorted(rows, key=lambda row: (row.category_id, row.team_id, row.fetch_batch_id)))


def _quality_rows(
    rows: tuple[ResearchSourceFetchQualitySlaInput, ...],
    *,
    config: ResearchSourceFetchQualitySlaConfig,
) -> tuple[ResearchSourceFetchQualitySlaRow, ...]:
    return tuple(
        sorted(
            (_quality_row(row, config=config) for row in rows),
            key=_row_sort_key,
        ),
    )


def _quality_row(
    row: ResearchSourceFetchQualitySlaInput,
    *,
    config: ResearchSourceFetchQualitySlaConfig,
) -> ResearchSourceFetchQualitySlaRow:
    fetch_success_ratio = _ratio(row.successful_fetch_count, row.attempted_fetch_count)
    corroboration_readiness_ratio = _ratio(
        row.corroborated_claim_count,
        row.required_corroborated_claim_count,
    )
    retry_pressure_ratio = _ratio(row.retry_attempt_count, row.attempted_fetch_count)
    manual_review_urgency_ratio = _ratio(
        row.manual_review_item_count,
        row.manual_review_capacity_count,
    )
    reason_codes = _row_reason_codes(
        row,
        fetch_success_ratio=fetch_success_ratio,
        corroboration_readiness_ratio=corroboration_readiness_ratio,
        retry_pressure_ratio=retry_pressure_ratio,
        manual_review_urgency_ratio=manual_review_urgency_ratio,
        config=config,
    )
    return ResearchSourceFetchQualitySlaRow(
        team_id=row.team_id,
        category_id=row.category_id,
        fetch_batch_id=row.fetch_batch_id,
        attempted_fetch_count=row.attempted_fetch_count,
        successful_fetch_count=row.successful_fetch_count,
        fetch_success_ratio=fetch_success_ratio,
        freshness_age_seconds=row.freshness_age_seconds,
        parse_quality_score=row.parse_quality_score,
        corroborated_claim_count=row.corroborated_claim_count,
        required_corroborated_claim_count=row.required_corroborated_claim_count,
        corroboration_readiness_ratio=corroboration_readiness_ratio,
        retry_attempt_count=row.retry_attempt_count,
        retry_pressure_ratio=retry_pressure_ratio,
        manual_review_item_count=row.manual_review_item_count,
        manual_review_capacity_count=row.manual_review_capacity_count,
        manual_review_urgency_ratio=manual_review_urgency_ratio,
        quality_pressure_score=_quality_pressure_score(
            fetch_success_ratio=fetch_success_ratio,
            freshness_age_seconds=row.freshness_age_seconds,
            max_freshness_age_block_seconds=config.max_freshness_age_block_seconds,
            parse_quality_score=row.parse_quality_score,
            corroboration_readiness_ratio=corroboration_readiness_ratio,
            retry_pressure_ratio=retry_pressure_ratio,
            manual_review_urgency_ratio=manual_review_urgency_ratio,
        ),
        status=_row_status(
            row,
            fetch_success_ratio=fetch_success_ratio,
            corroboration_readiness_ratio=corroboration_readiness_ratio,
            retry_pressure_ratio=retry_pressure_ratio,
            manual_review_urgency_ratio=manual_review_urgency_ratio,
            reason_codes=reason_codes,
            config=config,
        ),
        reason_codes=reason_codes,
    )


def _quality_pressure_score(
    *,
    fetch_success_ratio: Decimal,
    freshness_age_seconds: Decimal,
    max_freshness_age_block_seconds: Decimal,
    parse_quality_score: Decimal,
    corroboration_readiness_ratio: Decimal,
    retry_pressure_ratio: Decimal,
    manual_review_urgency_ratio: Decimal,
) -> Decimal:
    freshness_pressure = min(
        _ratio(freshness_age_seconds, max_freshness_age_block_seconds),
        ONE,
    )
    return _quantize(
        (ONE - fetch_success_ratio) * FETCH_SUCCESS_WEIGHT
        + freshness_pressure * FRESHNESS_WEIGHT
        + (ONE - parse_quality_score) * PARSE_QUALITY_WEIGHT
        + (ONE - corroboration_readiness_ratio) * CORROBORATION_WEIGHT
        + retry_pressure_ratio * RETRY_PRESSURE_WEIGHT
        + manual_review_urgency_ratio * MANUAL_REVIEW_WEIGHT,
    )


def _row_reason_codes(
    row: ResearchSourceFetchQualitySlaInput,
    *,
    fetch_success_ratio: Decimal,
    corroboration_readiness_ratio: Decimal,
    retry_pressure_ratio: Decimal,
    manual_review_urgency_ratio: Decimal,
    config: ResearchSourceFetchQualitySlaConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if fetch_success_ratio <= config.min_fetch_success_watch_ratio:
        reasons.append(LOW_FETCH_SUCCESS_REASON)
    if row.freshness_age_seconds >= config.max_freshness_age_watch_seconds:
        reasons.append(STALE_FRESHNESS_AGE_REASON)
    if row.parse_quality_score <= config.min_parse_quality_watch_score:
        reasons.append(LOW_PARSE_QUALITY_REASON)
    if corroboration_readiness_ratio <= config.min_corroboration_readiness_watch_ratio:
        reasons.append(CORROBORATION_NOT_READY_REASON)
    if retry_pressure_ratio >= config.max_retry_pressure_watch_ratio:
        reasons.append(RETRY_PRESSURE_REASON)
    if manual_review_urgency_ratio >= config.max_manual_review_urgency_watch_ratio:
        reasons.append(MANUAL_REVIEW_URGENT_REASON)
    if not reasons:
        reasons.append(CLEAR_REASON)
    return tuple(reasons)


def _row_status(
    row: ResearchSourceFetchQualitySlaInput,
    *,
    fetch_success_ratio: Decimal,
    corroboration_readiness_ratio: Decimal,
    retry_pressure_ratio: Decimal,
    manual_review_urgency_ratio: Decimal,
    reason_codes: tuple[str, ...],
    config: ResearchSourceFetchQualitySlaConfig,
) -> str:
    if reason_codes == (CLEAR_REASON,):
        return "pass"
    if (
        fetch_success_ratio <= config.min_fetch_success_block_ratio
        or row.freshness_age_seconds >= config.max_freshness_age_block_seconds
        or row.parse_quality_score <= config.min_parse_quality_block_score
        or corroboration_readiness_ratio <= config.min_corroboration_readiness_block_ratio
        or retry_pressure_ratio >= config.max_retry_pressure_block_ratio
        or manual_review_urgency_ratio >= config.max_manual_review_urgency_block_ratio
    ):
        return "block"
    return "watch"


def _row_status_is_consistent(row: ResearchSourceFetchQualitySlaRow) -> bool:
    if row.reason_codes == (CLEAR_REASON,):
        return row.status == "pass"
    return row.status in ("watch", "block")


def _row_sort_key(row: ResearchSourceFetchQualitySlaRow) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.quality_pressure_score,
        row.category_id,
        row.team_id,
        row.fetch_batch_id,
    )


def _report_status(rows: tuple[ResearchSourceFetchQualitySlaRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchSourceFetchQualitySlaRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_BATCHES_REASON,)
    reasons = tuple(
        reason_code
        for reason_code in REASON_CODES
        if reason_code not in (NO_BATCHES_REASON, CLEAR_REASON)
        and any(reason_code in row.reason_codes for row in rows)
    )
    if reasons:
        return reasons
    return (CLEAR_REASON,)


def _normalize_quality_rows(
    value: object,
) -> tuple[ResearchSourceFetchQualitySlaRow, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("quality_rows must be a list or tuple")
    rows = tuple(value)
    previous_key: tuple[Decimal, Decimal, str, str, str] | None = None
    seen: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not ResearchSourceFetchQualitySlaRow:
            raise ValueError("quality_rows must contain ResearchSourceFetchQualitySlaRow")
        require_paper_only_flags("row", row)
        key = (row.category_id, row.team_id, row.fetch_batch_id)
        if key in seen:
            raise ValueError("quality_rows must contain unique team, category, and batch")
        seen.add(key)
        sort_key = _row_sort_key(row)
        if previous_key is not None and sort_key <= previous_key:
            raise ValueError("quality_rows must follow deterministic sequence")
        previous_key = sort_key
    return rows


def _validate_input(row: ResearchSourceFetchQualitySlaInput) -> None:
    if row.successful_fetch_count > row.attempted_fetch_count:
        raise ValueError("successful_fetch_count must not exceed attempted_fetch_count")
    if row.corroborated_claim_count > row.required_corroborated_claim_count:
        raise ValueError(
            "corroborated_claim_count must not exceed required_corroborated_claim_count",
        )
    if row.retry_attempt_count > row.attempted_fetch_count:
        raise ValueError("retry_attempt_count must not exceed attempted_fetch_count")
    if row.manual_review_item_count > row.manual_review_capacity_count:
        raise ValueError("manual_review_item_count must not exceed manual_review_capacity_count")


def _validate_row(row: ResearchSourceFetchQualitySlaRow) -> None:
    _validate_input(
        ResearchSourceFetchQualitySlaInput(
            team_id=row.team_id,
            category_id=row.category_id,
            fetch_batch_id=row.fetch_batch_id,
            attempted_fetch_count=row.attempted_fetch_count,
            successful_fetch_count=row.successful_fetch_count,
            freshness_age_seconds=row.freshness_age_seconds,
            parse_quality_score=row.parse_quality_score,
            corroborated_claim_count=row.corroborated_claim_count,
            required_corroborated_claim_count=row.required_corroborated_claim_count,
            retry_attempt_count=row.retry_attempt_count,
            manual_review_item_count=row.manual_review_item_count,
            manual_review_capacity_count=row.manual_review_capacity_count,
        ),
    )
    if row.fetch_success_ratio != _ratio(
        row.successful_fetch_count,
        row.attempted_fetch_count,
    ):
        raise ValueError("fetch_success_ratio must match fetch counts")
    if row.corroboration_readiness_ratio != _ratio(
        row.corroborated_claim_count,
        row.required_corroborated_claim_count,
    ):
        raise ValueError("corroboration_readiness_ratio must match claim counts")
    if row.retry_pressure_ratio != _ratio(
        row.retry_attempt_count,
        row.attempted_fetch_count,
    ):
        raise ValueError("retry_pressure_ratio must match retry counts")
    if row.manual_review_urgency_ratio != _ratio(
        row.manual_review_item_count,
        row.manual_review_capacity_count,
    ):
        raise ValueError("manual_review_urgency_ratio must match review counts")
    if not _row_status_is_consistent(row):
        raise ValueError("status must match reason_codes")


def _validate_report(report: ResearchSourceFetchQualitySlaReport) -> None:
    if report.batch_count != _count(len(report.quality_rows)):
        raise ValueError("batch_count must match quality_rows")
    if report.attempted_fetch_count != _sum_rows(report.quality_rows, "attempted_fetch_count"):
        raise ValueError("attempted_fetch_count must match quality_rows")
    if report.successful_fetch_count != _sum_rows(report.quality_rows, "successful_fetch_count"):
        raise ValueError("successful_fetch_count must match quality_rows")
    if report.fetch_success_ratio != _ratio(
        report.successful_fetch_count,
        report.attempted_fetch_count,
    ):
        raise ValueError("fetch_success_ratio must match aggregate counts")
    if report.max_freshness_age_seconds != _max_rows(
        report.quality_rows,
        "freshness_age_seconds",
    ):
        raise ValueError("max_freshness_age_seconds must match quality_rows")
    if report.min_parse_quality_score != _min_rows(report.quality_rows, "parse_quality_score"):
        raise ValueError("min_parse_quality_score must match quality_rows")
    if report.min_corroboration_readiness_ratio != _min_rows(
        report.quality_rows,
        "corroboration_readiness_ratio",
    ):
        raise ValueError("min_corroboration_readiness_ratio must match quality_rows")
    if report.retry_attempt_count != _sum_rows(report.quality_rows, "retry_attempt_count"):
        raise ValueError("retry_attempt_count must match quality_rows")
    if report.retry_pressure_ratio != _ratio(
        report.retry_attempt_count,
        report.attempted_fetch_count,
    ):
        raise ValueError("retry_pressure_ratio must match aggregate counts")
    if report.manual_review_item_count != _sum_rows(
        report.quality_rows,
        "manual_review_item_count",
    ):
        raise ValueError("manual_review_item_count must match quality_rows")
    if report.manual_review_capacity_count != _sum_rows(
        report.quality_rows,
        "manual_review_capacity_count",
    ):
        raise ValueError("manual_review_capacity_count must match quality_rows")
    if report.manual_review_urgency_ratio != _ratio(
        report.manual_review_item_count,
        report.manual_review_capacity_count,
    ):
        raise ValueError("manual_review_urgency_ratio must match aggregate counts")
    if report.block_batch_count != _count(sum(row.status == "block" for row in report.quality_rows)):
        raise ValueError("block_batch_count must match quality_rows")
    if report.watch_batch_count != _count(sum(row.status == "watch" for row in report.quality_rows)):
        raise ValueError("watch_batch_count must match quality_rows")
    if report.pass_ready_batch_count != _count(
        sum(row.status == "pass" for row in report.quality_rows),
    ):
        raise ValueError("pass_ready_batch_count must match quality_rows")
    if report.pass_ready_attempted_fetch_count != _status_sum_rows(
        report.quality_rows,
        "attempted_fetch_count",
        status="pass",
    ):
        raise ValueError("pass_ready_attempted_fetch_count must match quality_rows")
    if report.pass_ready_attempted_fetch_ratio != _ratio(
        report.pass_ready_attempted_fetch_count,
        report.attempted_fetch_count,
    ):
        raise ValueError("pass_ready_attempted_fetch_ratio must match aggregate counts")
    if report.average_quality_pressure_score != _ratio(
        _sum_rows(report.quality_rows, "quality_pressure_score"),
        _count(len(report.quality_rows)),
    ):
        raise ValueError("average_quality_pressure_score must match quality_rows")
    if report.reason_codes != _report_reason_codes(report.quality_rows):
        raise ValueError("reason_codes must match quality_rows")
    if report.status != _report_status(report.quality_rows):
        raise ValueError("status must match quality_rows")


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    return Decimal(value).quantize(QUANT)


def _sum_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    return sum((getattr(row, field_name) for row in rows), ZERO).quantize(QUANT)


def _status_sum_rows(
    rows: tuple[ResearchSourceFetchQualitySlaRow, ...],
    field_name: str,
    *,
    status: str,
) -> Decimal:
    return sum(
        (getattr(row, field_name) for row in rows if row.status == status),
        ZERO,
    ).quantize(QUANT)


def _max_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO).quantize(QUANT)


def _min_rows(rows: tuple[object, ...], field_name: str) -> Decimal:
    return min((getattr(row, field_name) for row in rows), default=ZERO).quantize(QUANT)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_status(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in normalized:
        _require_canonical_string("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must not contain duplicates")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    _reject_public_string(field_name, value)


def _reject_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if lowered.startswith(("http://", "https://")):
        raise ValueError(f"{field_name} must be a public-safe identifier")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} must be public-safe")


def _require_or_set_digest(report: ResearchSourceFetchQualitySlaReport) -> None:
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
    elif report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    _require_digest("derived_validation_digest", report.derived_validation_digest)


def _report_values_without_digest(
    report: ResearchSourceFetchQualitySlaReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return payload


def _report_digest_from_values(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest")
    try:
        int(value, 16)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a SHA-256 hex digest") from exc
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")


def _verify_public_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    if digest != _report_digest_from_values(unsigned):
        raise ValueError("derived_validation_digest must match payload")


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
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("JSON value must use Decimal-derived string values")
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


def _reject_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_public_string("payload key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload(item)
        return
    if type(value) is int or isinstance(value, float):
        raise ValueError("public payload must use Decimal-derived string values")
    if type(value) is str:
        _reject_public_string("payload value", value)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_FETCH_QUALITY_SLA_CONFIG_VERSION",
    "STATUSES",
    "ResearchSourceFetchQualitySlaConfig",
    "ResearchSourceFetchQualitySlaInput",
    "ResearchSourceFetchQualitySlaReport",
    "ResearchSourceFetchQualitySlaRow",
    "build_research_source_fetch_quality_sla_report",
    "research_source_fetch_quality_sla_report_payload",
)
