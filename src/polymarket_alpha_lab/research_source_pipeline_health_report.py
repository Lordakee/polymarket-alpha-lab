"""Pure report-only research source pipeline health reducer.

The reducer combines caller-supplied source registry, scraping scope,
freshness, audit trail, and collection priority signals. It is deterministic
and has no network, scraping, database, persistence, trading, or auth surface.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_SOURCE_PIPELINE_HEALTH_REPORT_CONFIG_VERSION = (
    "research-source-pipeline-health-report-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
SOURCE_CATEGORIES = (
    "analysis",
    "community",
    "data_vendor",
    "news",
    "official",
    "regulator",
    "regulatory",
    "research",
    "venue",
)
COLLECTION_PRIORITIES = (
    "defer_collection",
    "prioritize_collection",
    "collect_before_research_use",
)

NO_INPUTS_REASON = "source_pipeline_health_no_inputs"
PASS_REASON = "pipeline_health_pass"
WATCH_REASON = "pipeline_health_watch"
BLOCK_REASON = "pipeline_health_block"

REASON_CODE_SEQUENCE = (
    "registry_status_block",
    "registry_status_watch",
    "scraping_scope_status_block",
    "scraping_scope_status_watch",
    "source_freshness_status_block",
    "source_freshness_status_watch",
    "source_age_missing",
    "source_age_above_block_threshold",
    "source_age_above_watch_threshold",
    "audit_trail_status_block",
    "audit_trail_status_watch",
    "collection_status_block",
    "collection_status_watch",
    "collection_priority_collect_before_research_use",
    "collection_priority_prioritized",
    "pipeline_health_score_below_block_threshold",
    "pipeline_health_score_below_pass_threshold",
    BLOCK_REASON,
    WATCH_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)
REASON_CODE_RANK = {reason_code: index for index, reason_code in enumerate(REASON_CODE_SEQUENCE)}

PUBLIC_PAYLOAD_FIELDS = (
    "generated_at",
    "config_version",
    "status",
    "input_count",
    "row_count",
    "pass_count",
    "watch_count",
    "block_count",
    "attention_count",
    "attention_ratio",
    "registry_block_count",
    "scraping_scope_block_count",
    "source_freshness_block_count",
    "audit_trail_block_count",
    "collection_block_count",
    "max_source_age_seconds",
    "reason_codes",
    "rows",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)
PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST = PUBLIC_PAYLOAD_FIELDS[:-1]
ROW_PAYLOAD_FIELDS = (
    "pipeline_ref",
    "source_category",
    "registry_status",
    "scraping_scope_status",
    "source_freshness_status",
    "audit_trail_status",
    "collection_status",
    "registry_reliability_score",
    "source_freshness_score",
    "audit_trail_score",
    "collection_priority_score",
    "source_age_seconds",
    "collection_priority",
    "pipeline_health_score",
    "status",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
    "derived_validation_digest",
)

UNSAFE_KEY_FRAGMENTS = (
    "raw_candidate",
    "raw-candidate",
    "raw candidate",
    "candidate_id",
    "candidate id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "question",
    "source_ref",
    "source ref",
    "source_url",
    "source url",
    "source_text",
    "source text",
    "dsn",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
)
UNSAFE_TEXT_FRAGMENTS = (
    *UNSAFE_KEY_FRAGMENTS,
    "raw candidate id",
    "candidate-",
    "market-",
    "http://",
    "https://",
    "www.",
    "://",
    "buy",
    "sell",
    "recommend",
    "recommendation",
)

__all__ = (
    "DEFAULT_RESEARCH_SOURCE_PIPELINE_HEALTH_REPORT_CONFIG_VERSION",
    "ResearchSourcePipelineHealthConfig",
    "ResearchSourcePipelineHealthInput",
    "ResearchSourcePipelineHealthReport",
    "ResearchSourcePipelineHealthRow",
    "STATUSES",
    "build_research_source_pipeline_health_report",
    "research_source_pipeline_health_report_payload",
    "validate_research_source_pipeline_health_report_payload",
)


@dataclass(frozen=True)
class ResearchSourcePipelineHealthConfig:
    config_version: str = DEFAULT_RESEARCH_SOURCE_PIPELINE_HEALTH_REPORT_CONFIG_VERSION
    pass_pipeline_health_score: Decimal = Decimal("0.750000")
    block_pipeline_health_score: Decimal = Decimal("0.500000")
    watch_source_age_seconds: Decimal = Decimal("86400.000000")
    block_source_age_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePipelineHealthConfig:
            raise TypeError("ResearchSourcePipelineHealthConfig does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourcePipelineHealthConfig, "config")
        _require_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_SOURCE_PIPELINE_HEALTH_REPORT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("pass_pipeline_health_score", "block_pipeline_health_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_pipeline_health_score >= self.pass_pipeline_health_score:
            raise ValueError(
                "block_pipeline_health_score must be below pass_pipeline_health_score",
            )
        for field_name in ("watch_source_age_seconds", "block_source_age_seconds"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_source_age_seconds >= self.block_source_age_seconds:
            raise ValueError(
                "watch_source_age_seconds must be below block_source_age_seconds",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchSourcePipelineHealthInput:
    pipeline_item_ref: str
    source_category: str
    registry_status: str
    scraping_scope_status: str
    source_freshness_status: str
    audit_trail_status: str
    collection_status: str
    registry_reliability_score: Decimal
    source_freshness_score: Decimal
    audit_trail_score: Decimal
    collection_priority_score: Decimal
    source_age_seconds: Decimal | None
    collection_priority: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePipelineHealthInput:
            raise TypeError("ResearchSourcePipelineHealthInput does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourcePipelineHealthInput, "input")
        _require_public_identifier("pipeline_item_ref", self.pipeline_item_ref)
        _reject_unsafe_public_text("pipeline_item_ref", self.pipeline_item_ref)
        _require_member("source_category", self.source_category, SOURCE_CATEGORIES)
        for field_name in (
            "registry_status",
            "scraping_scope_status",
            "source_freshness_status",
            "audit_trail_status",
            "collection_status",
        ):
            _require_member(field_name, getattr(self, field_name), STATUSES)
        for field_name in (
            "registry_reliability_score",
            "source_freshness_score",
            "audit_trail_score",
            "collection_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        _reject_unsafe_public_text("collection_priority", self.collection_priority)
        _require_member("collection_priority", self.collection_priority, COLLECTION_PRIORITIES)
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchSourcePipelineHealthRow:
    pipeline_ref: str
    source_category: str
    registry_status: str
    scraping_scope_status: str
    source_freshness_status: str
    audit_trail_status: str
    collection_status: str
    registry_reliability_score: Decimal
    source_freshness_score: Decimal
    audit_trail_score: Decimal
    collection_priority_score: Decimal
    source_age_seconds: Decimal | None
    collection_priority: str
    pipeline_health_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePipelineHealthRow:
            raise TypeError("ResearchSourcePipelineHealthRow does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourcePipelineHealthRow, "row")
        _require_public_string("pipeline_ref", self.pipeline_ref)
        _reject_unsafe_public_text("pipeline_ref", self.pipeline_ref)
        _require_member("source_category", self.source_category, SOURCE_CATEGORIES)
        for field_name in (
            "registry_status",
            "scraping_scope_status",
            "source_freshness_status",
            "audit_trail_status",
            "collection_status",
            "status",
        ):
            _require_member(field_name, getattr(self, field_name), STATUSES)
        for field_name in (
            "registry_reliability_score",
            "source_freshness_score",
            "audit_trail_score",
            "collection_priority_score",
            "pipeline_health_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "source_age_seconds",
                self.source_age_seconds,
            ),
        )
        _reject_unsafe_public_text("collection_priority", self.collection_priority)
        _require_member("collection_priority", self.collection_priority, COLLECTION_PRIORITIES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class ResearchSourcePipelineHealthReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attention_count: Decimal
    attention_ratio: Decimal
    registry_block_count: Decimal
    scraping_scope_block_count: Decimal
    source_freshness_block_count: Decimal
    audit_trail_block_count: Decimal
    collection_block_count: Decimal
    max_source_age_seconds: Decimal | None
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchSourcePipelineHealthRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourcePipelineHealthReport:
            raise TypeError("ResearchSourcePipelineHealthReport does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchSourcePipelineHealthReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        _require_member("status", self.status, STATUSES)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attention_count",
            "registry_block_count",
            "scraping_scope_block_count",
            "source_freshness_block_count",
            "audit_trail_block_count",
            "collection_block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "attention_ratio",
            _normalize_ratio_decimal("attention_ratio", self.attention_ratio),
        )
        object.__setattr__(
            self,
            "max_source_age_seconds",
            _normalize_optional_nonnegative_decimal(
                "max_source_age_seconds",
                self.max_source_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_research_source_pipeline_health_report(
    inputs: Iterable[ResearchSourcePipelineHealthInput],
    *,
    config: ResearchSourcePipelineHealthConfig,
    generated_at: datetime,
) -> ResearchSourcePipelineHealthReport:
    if type(config) is not ResearchSourcePipelineHealthConfig:
        raise ValueError("config must be a ResearchSourcePipelineHealthConfig")
    _require_hard_flags("config", config)
    _reject_unsafe_public_payload("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    values = _normalize_inputs(inputs)

    unranked_rows = tuple(_row_from_input(value, config=config) for value in values)
    sorted_rows = tuple(sorted(unranked_rows, key=_row_sort_key))
    rows = tuple(
        _row_with_public_ref(row, index)
        for index, row in enumerate(sorted_rows, start=1)
    )
    row_count = _decimal_count(len(rows))
    attention_count = _status_count(rows, "watch") + _status_count(rows, "block")

    return ResearchSourcePipelineHealthReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_decimal_count(len(values)),
        row_count=row_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        attention_count=attention_count,
        attention_ratio=_safe_ratio(attention_count, row_count),
        registry_block_count=_component_status_count(rows, "registry_status", "block"),
        scraping_scope_block_count=_component_status_count(
            rows,
            "scraping_scope_status",
            "block",
        ),
        source_freshness_block_count=_component_status_count(
            rows,
            "source_freshness_status",
            "block",
        ),
        audit_trail_block_count=_component_status_count(
            rows,
            "audit_trail_status",
            "block",
        ),
        collection_block_count=_component_status_count(rows, "collection_status", "block"),
        max_source_age_seconds=_max_optional_decimal(
            row.source_age_seconds for row in rows
        ),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_source_pipeline_health_report_payload(
    report: ResearchSourcePipelineHealthReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is dict:
        _reject_unsafe_public_payload("public payload", report)
        validate_research_source_pipeline_health_report_payload(report)
        return dict(report)
    if type(report) is not ResearchSourcePipelineHealthReport:
        raise ValueError("report must be a ResearchSourcePipelineHealthReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    _validate_report(report)
    payload = _report_public_payload_without_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_research_source_pipeline_health_report_payload(payload)
    return payload


def validate_research_source_pipeline_health_report_payload(payload: object) -> bool:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _require_exact_keys("payload", payload, PUBLIC_PAYLOAD_FIELDS)
    _require_public_datetime_string("generated_at", payload["generated_at"])
    _require_public_string("config_version", payload["config_version"])
    _require_member("status", payload["status"], STATUSES)
    for field_name in (
        "input_count",
        "row_count",
        "pass_count",
        "watch_count",
        "block_count",
        "attention_count",
        "registry_block_count",
        "scraping_scope_block_count",
        "source_freshness_block_count",
        "audit_trail_block_count",
        "collection_block_count",
    ):
        _decimal_from_payload_string(field_name, payload[field_name], require_integral=True)
    _decimal_from_payload_string("attention_ratio", payload["attention_ratio"])
    _optional_decimal_from_payload_string(
        "max_source_age_seconds",
        payload["max_source_age_seconds"],
    )
    _normalize_public_reason_codes("reason_codes", payload["reason_codes"])
    _validate_payload_rows(payload["rows"])
    _require_payload_hard_flags("payload", payload)
    expected_digest = _payload_derived_validation_digest(
        {
            field_name: payload[field_name]
            for field_name in PUBLIC_PAYLOAD_FIELDS_WITHOUT_DIGEST
        },
    )
    if payload["derived_validation_digest"] != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")
    _validate_payload_report_consistency(payload)
    return True


def _row_from_input(
    value: ResearchSourcePipelineHealthInput,
    *,
    config: ResearchSourcePipelineHealthConfig,
) -> ResearchSourcePipelineHealthRow:
    health_score = _pipeline_health_score(value)
    reason_codes = _reason_codes_for_input(
        value,
        pipeline_health_score=health_score,
        config=config,
    )
    return ResearchSourcePipelineHealthRow(
        pipeline_ref=value.pipeline_item_ref,
        source_category=value.source_category,
        registry_status=value.registry_status,
        scraping_scope_status=value.scraping_scope_status,
        source_freshness_status=value.source_freshness_status,
        audit_trail_status=value.audit_trail_status,
        collection_status=value.collection_status,
        registry_reliability_score=value.registry_reliability_score,
        source_freshness_score=value.source_freshness_score,
        audit_trail_score=value.audit_trail_score,
        collection_priority_score=value.collection_priority_score,
        source_age_seconds=value.source_age_seconds,
        collection_priority=value.collection_priority,
        pipeline_health_score=health_score,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_with_public_ref(
    row: ResearchSourcePipelineHealthRow,
    index: int,
) -> ResearchSourcePipelineHealthRow:
    return ResearchSourcePipelineHealthRow(
        pipeline_ref=f"redacted-pipeline-source-{index:06d}",
        source_category=row.source_category,
        registry_status=row.registry_status,
        scraping_scope_status=row.scraping_scope_status,
        source_freshness_status=row.source_freshness_status,
        audit_trail_status=row.audit_trail_status,
        collection_status=row.collection_status,
        registry_reliability_score=row.registry_reliability_score,
        source_freshness_score=row.source_freshness_score,
        audit_trail_score=row.audit_trail_score,
        collection_priority_score=row.collection_priority_score,
        source_age_seconds=row.source_age_seconds,
        collection_priority=row.collection_priority,
        pipeline_health_score=row.pipeline_health_score,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _reason_codes_for_input(
    value: ResearchSourcePipelineHealthInput,
    *,
    pipeline_health_score: Decimal,
    config: ResearchSourcePipelineHealthConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_component_status_reason(reasons, "registry_status", value.registry_status)
    _append_component_status_reason(
        reasons,
        "scraping_scope_status",
        value.scraping_scope_status,
    )
    _append_component_status_reason(
        reasons,
        "source_freshness_status",
        value.source_freshness_status,
    )
    if value.source_age_seconds is None:
        reasons.append("source_age_missing")
    elif value.source_age_seconds >= config.block_source_age_seconds:
        reasons.append("source_age_above_block_threshold")
    elif value.source_age_seconds >= config.watch_source_age_seconds:
        reasons.append("source_age_above_watch_threshold")
    _append_component_status_reason(reasons, "audit_trail_status", value.audit_trail_status)
    _append_component_status_reason(reasons, "collection_status", value.collection_status)
    if value.collection_priority == "collect_before_research_use":
        reasons.append("collection_priority_collect_before_research_use")
    elif value.collection_priority == "prioritize_collection":
        reasons.append("collection_priority_prioritized")
    if pipeline_health_score < config.block_pipeline_health_score:
        reasons.append("pipeline_health_score_below_block_threshold")
    elif pipeline_health_score < config.pass_pipeline_health_score:
        reasons.append("pipeline_health_score_below_pass_threshold")

    preliminary_status = _status_from_reason_codes(tuple(reasons))
    if preliminary_status == "block":
        reasons.append(BLOCK_REASON)
    elif preliminary_status == "watch":
        reasons.append(WATCH_REASON)
    else:
        reasons.append(PASS_REASON)
    return tuple(reasons)


def _append_component_status_reason(
    reasons: list[str],
    field_name: str,
    status: str,
) -> None:
    if status == "block":
        reasons.append(f"{field_name}_block")
    elif status == "watch":
        reasons.append(f"{field_name}_watch")


def _pipeline_health_score(value: ResearchSourcePipelineHealthInput) -> Decimal:
    return min(
        value.registry_reliability_score,
        value.source_freshness_score,
        value.audit_trail_score,
    )


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(
        reason_code.endswith("_block")
        or reason_code
        in (
            "source_age_above_block_threshold",
            "collection_priority_collect_before_research_use",
            "pipeline_health_score_below_block_threshold",
            BLOCK_REASON,
        )
        for reason_code in reason_codes
    ):
        return "block"
    if any(
        reason_code.endswith("_watch")
        or reason_code
        in (
            "source_age_missing",
            "source_age_above_watch_threshold",
            "collection_priority_prioritized",
            "pipeline_health_score_below_pass_threshold",
            WATCH_REASON,
        )
        for reason_code in reason_codes
    ):
        return "watch"
    return "pass"


def _normalize_inputs(
    values: Iterable[ResearchSourcePipelineHealthInput],
) -> tuple[ResearchSourcePipelineHealthInput, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchSourcePipelineHealthInput:
            raise ValueError("inputs must contain ResearchSourcePipelineHealthInput values")
        _require_hard_flags("input", value)
        _reject_unsafe_public_payload("input", value)
        if value.pipeline_item_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate pipeline_item_ref values")
        seen_refs.add(value.pipeline_item_ref)
    return normalized


def _normalize_rows(
    values: Iterable[ResearchSourcePipelineHealthRow],
) -> tuple[ResearchSourcePipelineHealthRow, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchSourcePipelineHealthRow:
            raise ValueError("rows must contain ResearchSourcePipelineHealthRow values")
        _require_hard_flags("row", row)
        _reject_unsafe_public_payload("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic order")
    if len({row.pipeline_ref for row in rows}) != len(rows):
        raise ValueError("rows must have unique pipeline_ref values")
    return rows


def _row_sort_key(
    row: ResearchSourcePipelineHealthRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        -row.pipeline_health_score,
        -row.collection_priority_score,
        -_optional_sort_decimal(row.source_age_seconds),
        row.source_category,
        row.pipeline_ref,
    )


def _optional_sort_decimal(value: Decimal | None) -> Decimal:
    if value is None:
        return Decimal("999999999999999999.000000")
    return value


def _report_status(rows: tuple[ResearchSourcePipelineHealthRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchSourcePipelineHealthRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reason_codes = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    }
    if not reason_codes:
        return (PASS_REASON,)
    return tuple(sorted(reason_codes, key=_reason_code_sort_key))


def _reason_code_sort_key(reason_code: str) -> tuple[int, str]:
    return (REASON_CODE_RANK.get(reason_code, len(REASON_CODE_RANK)), reason_code)


def _status_count(rows: tuple[ResearchSourcePipelineHealthRow, ...], status: str) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _component_status_count(
    rows: tuple[ResearchSourcePipelineHealthRow, ...],
    field_name: str,
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) == status))


def _max_optional_decimal(values: Iterable[Decimal | None]) -> Decimal | None:
    present_values = tuple(value for value in values if value is not None)
    if not present_values:
        return None
    return max(present_values)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _validate_row(row: ResearchSourcePipelineHealthRow) -> None:
    expected_score = min(
        row.registry_reliability_score,
        row.source_freshness_score,
        row.audit_trail_score,
    )
    if row.pipeline_health_score != expected_score:
        raise ValueError("pipeline_health_score must match source quality scores")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and row.reason_codes != (PASS_REASON,):
        raise ValueError("pass rows must use pass reason code only")
    if row.status != "pass" and PASS_REASON in row.reason_codes:
        raise ValueError("non-pass rows must not include pass reason code")
    if row.status == "block" and BLOCK_REASON not in row.reason_codes:
        raise ValueError("block rows must include pipeline health block reason")
    if row.status == "watch" and WATCH_REASON not in row.reason_codes:
        raise ValueError("watch rows must include pipeline health watch reason")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: ResearchSourcePipelineHealthReport) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.attention_count != report.watch_count + report.block_count:
        raise ValueError("attention_count must match watch and block counts")
    if report.attention_ratio != _safe_ratio(report.attention_count, report.row_count):
        raise ValueError("attention_ratio must match attention_count and row_count")
    if report.registry_block_count != _component_status_count(
        report.rows,
        "registry_status",
        "block",
    ):
        raise ValueError("registry_block_count must match rows")
    if report.scraping_scope_block_count != _component_status_count(
        report.rows,
        "scraping_scope_status",
        "block",
    ):
        raise ValueError("scraping_scope_block_count must match rows")
    if report.source_freshness_block_count != _component_status_count(
        report.rows,
        "source_freshness_status",
        "block",
    ):
        raise ValueError("source_freshness_block_count must match rows")
    if report.audit_trail_block_count != _component_status_count(
        report.rows,
        "audit_trail_status",
        "block",
    ):
        raise ValueError("audit_trail_block_count must match rows")
    if report.collection_block_count != _component_status_count(
        report.rows,
        "collection_status",
        "block",
    ):
        raise ValueError("collection_block_count must match rows")
    if report.max_source_age_seconds != _max_optional_decimal(
        row.source_age_seconds for row in report.rows
    ):
        raise ValueError("max_source_age_seconds must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _validate_payload_report_consistency(payload: dict[str, Any]) -> None:
    rows = tuple(_row_from_payload(row) for row in payload["rows"])
    ResearchSourcePipelineHealthReport(
        generated_at=_datetime_from_payload_string("generated_at", payload["generated_at"]),
        config_version=payload["config_version"],
        status=payload["status"],
        input_count=_decimal_from_payload_string(
            "input_count",
            payload["input_count"],
            require_integral=True,
        ),
        row_count=_decimal_from_payload_string(
            "row_count",
            payload["row_count"],
            require_integral=True,
        ),
        pass_count=_decimal_from_payload_string(
            "pass_count",
            payload["pass_count"],
            require_integral=True,
        ),
        watch_count=_decimal_from_payload_string(
            "watch_count",
            payload["watch_count"],
            require_integral=True,
        ),
        block_count=_decimal_from_payload_string(
            "block_count",
            payload["block_count"],
            require_integral=True,
        ),
        attention_count=_decimal_from_payload_string(
            "attention_count",
            payload["attention_count"],
            require_integral=True,
        ),
        attention_ratio=_decimal_from_payload_string(
            "attention_ratio",
            payload["attention_ratio"],
        ),
        registry_block_count=_decimal_from_payload_string(
            "registry_block_count",
            payload["registry_block_count"],
            require_integral=True,
        ),
        scraping_scope_block_count=_decimal_from_payload_string(
            "scraping_scope_block_count",
            payload["scraping_scope_block_count"],
            require_integral=True,
        ),
        source_freshness_block_count=_decimal_from_payload_string(
            "source_freshness_block_count",
            payload["source_freshness_block_count"],
            require_integral=True,
        ),
        audit_trail_block_count=_decimal_from_payload_string(
            "audit_trail_block_count",
            payload["audit_trail_block_count"],
            require_integral=True,
        ),
        collection_block_count=_decimal_from_payload_string(
            "collection_block_count",
            payload["collection_block_count"],
            require_integral=True,
        ),
        max_source_age_seconds=_optional_decimal_from_payload_string(
            "max_source_age_seconds",
            payload["max_source_age_seconds"],
        ),
        reason_codes=tuple(payload["reason_codes"]),
        rows=rows,
        derived_validation_digest=payload["derived_validation_digest"],
        paper_only=payload["paper_only"],
        report_only=payload["report_only"],
        readonly=payload["readonly"],
    )


def _validate_payload_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("rows must be a list")
    seen_refs: set[str] = set()
    for row in value:
        if type(row) is not dict:
            raise ValueError("row must be a JSON object")
        _require_exact_keys("row", row, ROW_PAYLOAD_FIELDS)
        _require_public_string("pipeline_ref", row["pipeline_ref"])
        _require_member("source_category", row["source_category"], SOURCE_CATEGORIES)
        for field_name in (
            "registry_status",
            "scraping_scope_status",
            "source_freshness_status",
            "audit_trail_status",
            "collection_status",
            "status",
        ):
            _require_member(field_name, row[field_name], STATUSES)
        for field_name in (
            "registry_reliability_score",
            "source_freshness_score",
            "audit_trail_score",
            "collection_priority_score",
            "pipeline_health_score",
        ):
            _decimal_from_payload_string(field_name, row[field_name])
        _optional_decimal_from_payload_string(
            "source_age_seconds",
            row["source_age_seconds"],
        )
        _require_member("collection_priority", row["collection_priority"], COLLECTION_PRIORITIES)
        _normalize_public_reason_codes("reason_codes", row["reason_codes"])
        _require_payload_hard_flags("row", row)
        _require_sha256_digest("derived_validation_digest", row["derived_validation_digest"])
        if row["pipeline_ref"] in seen_refs:
            raise ValueError("rows must be unique by pipeline_ref")
        seen_refs.add(row["pipeline_ref"])


def _row_from_payload(row: dict[str, Any]) -> ResearchSourcePipelineHealthRow:
    return ResearchSourcePipelineHealthRow(
        pipeline_ref=row["pipeline_ref"],
        source_category=row["source_category"],
        registry_status=row["registry_status"],
        scraping_scope_status=row["scraping_scope_status"],
        source_freshness_status=row["source_freshness_status"],
        audit_trail_status=row["audit_trail_status"],
        collection_status=row["collection_status"],
        registry_reliability_score=_decimal_from_payload_string(
            "registry_reliability_score",
            row["registry_reliability_score"],
        ),
        source_freshness_score=_decimal_from_payload_string(
            "source_freshness_score",
            row["source_freshness_score"],
        ),
        audit_trail_score=_decimal_from_payload_string(
            "audit_trail_score",
            row["audit_trail_score"],
        ),
        collection_priority_score=_decimal_from_payload_string(
            "collection_priority_score",
            row["collection_priority_score"],
        ),
        source_age_seconds=_optional_decimal_from_payload_string(
            "source_age_seconds",
            row["source_age_seconds"],
        ),
        collection_priority=row["collection_priority"],
        pipeline_health_score=_decimal_from_payload_string(
            "pipeline_health_score",
            row["pipeline_health_score"],
        ),
        status=row["status"],
        reason_codes=tuple(row["reason_codes"]),
        derived_validation_digest=row["derived_validation_digest"],
        paper_only=row["paper_only"],
        report_only=row["report_only"],
        readonly=row["readonly"],
    )


def _report_public_payload_without_digest(
    report: ResearchSourcePipelineHealthReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "status": report.status,
        "input_count": str(report.input_count),
        "row_count": str(report.row_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "attention_count": str(report.attention_count),
        "attention_ratio": str(report.attention_ratio),
        "registry_block_count": str(report.registry_block_count),
        "scraping_scope_block_count": str(report.scraping_scope_block_count),
        "source_freshness_block_count": str(report.source_freshness_block_count),
        "audit_trail_block_count": str(report.audit_trail_block_count),
        "collection_block_count": str(report.collection_block_count),
        "max_source_age_seconds": (
            str(report.max_source_age_seconds)
            if report.max_source_age_seconds is not None
            else None
        ),
        "reason_codes": list(report.reason_codes),
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_public_payload(row: ResearchSourcePipelineHealthRow) -> dict[str, Any]:
    return {
        "pipeline_ref": row.pipeline_ref,
        "source_category": row.source_category,
        "registry_status": row.registry_status,
        "scraping_scope_status": row.scraping_scope_status,
        "source_freshness_status": row.source_freshness_status,
        "audit_trail_status": row.audit_trail_status,
        "collection_status": row.collection_status,
        "registry_reliability_score": str(row.registry_reliability_score),
        "source_freshness_score": str(row.source_freshness_score),
        "audit_trail_score": str(row.audit_trail_score),
        "collection_priority_score": str(row.collection_priority_score),
        "source_age_seconds": (
            str(row.source_age_seconds) if row.source_age_seconds is not None else None
        ),
        "collection_priority": row.collection_priority,
        "pipeline_health_score": str(row.pipeline_health_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
        "derived_validation_digest": row.derived_validation_digest,
    }


def _row_public_payload_without_digest(
    row: ResearchSourcePipelineHealthRow,
) -> dict[str, Any]:
    payload = _row_public_payload(row)
    payload.pop("derived_validation_digest")
    return payload


def _row_derived_validation_digest(row: ResearchSourcePipelineHealthRow) -> str:
    return _payload_derived_validation_digest(_row_public_payload_without_digest(row))


def _report_derived_validation_digest(report: ResearchSourcePipelineHealthReport) -> str:
    return _payload_derived_validation_digest(_report_public_payload_without_digest(report))


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    return sha256(
        (
            "research_source_pipeline_health_report|"
            + json.dumps(payload, sort_keys=True, separators=(",", ":"))
        ).encode("utf-8"),
    ).hexdigest()


def _require_exact_keys(
    label: str,
    value: dict[Any, Any],
    expected_fields: tuple[str, ...],
) -> None:
    for field_name in expected_fields:
        if field_name not in value:
            raise ValueError(f"{label}.{field_name} is required")
    extra_fields = sorted(set(value) - set(expected_fields))
    if extra_fields:
        raise ValueError(f"unexpected public payload field: {extra_fields[0]}")


def _require_payload_hard_flags(label: str, value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value[field_name] is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_exact_type(value: object, expected_type: type, label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public identifier")
    if value[0] in "._-":
        raise ValueError(f"{field_name} must start with an alphanumeric character")
    return value


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty canonical string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    _require_public_string(field_name, value)
    if value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must contain at least one value")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
    if reason_codes != tuple(sorted(reason_codes, key=_reason_code_sort_key)):
        raise ValueError(f"{field_name} must use deterministic reason order")
    return reason_codes


def _normalize_public_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(field_name, tuple(value))


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_optional_nonnegative_decimal(field_name, value)
    if normalized is None:
        raise ValueError(f"{field_name} must be a Decimal")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_from_payload_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    _require_public_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_public_datetime_string(field_name: str, value: object) -> None:
    _datetime_from_payload_string(field_name, value)


def _decimal_from_payload_string(
    field_name: str,
    value: object,
    *,
    require_integral: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    _require_public_string(field_name, value)
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if require_integral and decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal string")
    return _quantize(decimal_value)


def _optional_decimal_from_payload_string(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _decimal_from_payload_string(field_name, value)


def _require_sha256_digest(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_key(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return


def _reject_unsafe_public_key(label: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_KEY_FRAGMENTS):
        raise ValueError(f"unsafe public field in {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.casefold()
    if any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public text in {label}")
