"""Pure paper/report/readonly resolution watch queue for human research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_RESOLUTION_WATCH_QUEUE_CONFIG_VERSION = (
    "research-resolution-watch-queue-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64)

STATUSES = ("pass", "watch", "block")
STATUS_SORT_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
SAFETY_FLAG_NAMES = ("paper_only", "report_only", "readonly")

ROW_REASON_CODES = (
    "resolution_watch_queue_pass",
    "resolution_watch_queue_watch",
    "resolution_watch_queue_block",
    "settlement_monitoring_watch",
    "settlement_monitoring_block",
    "resolution_quality_watch",
    "resolution_quality_block",
    "rule_risk_watch",
    "rule_risk_block",
    "review_readiness_watch",
    "review_readiness_block",
)
REPORT_REASON_CODES = (
    "resolution_watch_queue_no_items",
    "resolution_watch_queue_clear",
    "resolution_watch_queue_watch_present",
    "resolution_watch_queue_block_present",
    "settlement_monitoring_watch_present",
    "settlement_monitoring_block_present",
    "resolution_quality_watch_present",
    "resolution_quality_block_present",
    "rule_risk_watch_present",
    "rule_risk_block_present",
    "review_readiness_watch_present",
    "review_readiness_block_present",
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw_candidate",
    "candidate_id",
    "market_id",
    "market_slug",
    "market_question",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "http",
    "https",
    "www.",
    "url=",
    "url",
    "dsn",
    "postgres",
    "supabase",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "position",
    "buy",
    "sell",
    "recommendation",
    "recommend",
)

__all__ = (
    "DEFAULT_RESEARCH_RESOLUTION_WATCH_QUEUE_CONFIG_VERSION",
    "ResearchResolutionWatchQueueConfig",
    "ResearchResolutionWatchQueueItem",
    "ResearchResolutionWatchQueueRow",
    "ResearchResolutionWatchQueueReport",
    "build_research_resolution_watch_queue",
    "research_resolution_watch_queue_payload",
    "validate_research_resolution_watch_queue_public_payload",
)


@dataclass(frozen=True)
class ResearchResolutionWatchQueueConfig:
    config_version: str = DEFAULT_RESEARCH_RESOLUTION_WATCH_QUEUE_CONFIG_VERSION
    max_pass_combined_watch_score: Decimal = Decimal("0.250000")
    max_watch_combined_watch_score: Decimal = Decimal("0.550000")
    max_pass_settlement_monitoring_priority_score: Decimal = Decimal("0.250000")
    max_watch_settlement_monitoring_priority_score: Decimal = Decimal("0.600000")
    max_pass_resolution_quality_risk_score: Decimal = Decimal("0.250000")
    max_watch_resolution_quality_risk_score: Decimal = Decimal("0.550000")
    max_pass_rule_risk_score: Decimal = Decimal("0.250000")
    max_watch_rule_risk_score: Decimal = Decimal("0.550000")
    min_pass_review_readiness_score: Decimal = Decimal("0.850000")
    min_watch_review_readiness_score: Decimal = Decimal("0.600000")
    settlement_monitoring_weight: Decimal = Decimal("0.300000")
    resolution_quality_weight: Decimal = Decimal("0.300000")
    rule_risk_weight: Decimal = Decimal("0.200000")
    review_readiness_gap_weight: Decimal = Decimal("0.200000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchResolutionWatchQueueConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionWatchQueueConfig:
            raise ValueError("config must be a ResearchResolutionWatchQueueConfig")
        object.__setattr__(
            self,
            "config_version",
            _require_safe_public_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_RESEARCH_RESOLUTION_WATCH_QUEUE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_combined_watch_score",
            "max_watch_combined_watch_score",
            "max_pass_settlement_monitoring_priority_score",
            "max_watch_settlement_monitoring_priority_score",
            "max_pass_resolution_quality_risk_score",
            "max_watch_resolution_quality_risk_score",
            "max_pass_rule_risk_score",
            "max_watch_rule_risk_score",
            "min_pass_review_readiness_score",
            "min_watch_review_readiness_score",
            "settlement_monitoring_weight",
            "resolution_quality_weight",
            "rule_risk_weight",
            "review_readiness_gap_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config_thresholds(self)
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchResolutionWatchQueueItem:
    research_item_reference: str
    settlement_monitoring_status: str
    settlement_monitoring_priority_score: Decimal
    resolution_quality_risk_score: Decimal
    rule_risk_score: Decimal
    review_readiness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchResolutionWatchQueueItem does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionWatchQueueItem:
            raise ValueError("item must be a ResearchResolutionWatchQueueItem")
        object.__setattr__(
            self,
            "research_item_reference",
            _require_safe_public_string(
                "research_item_reference",
                self.research_item_reference,
            ),
        )
        _require_member(
            "settlement_monitoring_status",
            self.settlement_monitoring_status,
            STATUSES,
        )
        for field_name in (
            "settlement_monitoring_priority_score",
            "resolution_quality_risk_score",
            "rule_risk_score",
            "review_readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("item", self)
        _reject_unsafe_public_payload("item", self)


@dataclass(frozen=True)
class ResearchResolutionWatchQueueRow:
    research_item_reference: str
    settlement_monitoring_status: str
    settlement_monitoring_priority_score: Decimal
    resolution_quality_risk_score: Decimal
    rule_risk_score: Decimal
    review_readiness_score: Decimal
    review_readiness_gap_score: Decimal
    combined_watch_score: Decimal
    desensitized_monitoring_priority: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchResolutionWatchQueueRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionWatchQueueRow:
            raise ValueError("row must be a ResearchResolutionWatchQueueRow")
        object.__setattr__(
            self,
            "research_item_reference",
            _require_safe_public_string(
                "research_item_reference",
                self.research_item_reference,
            ),
        )
        _require_member(
            "settlement_monitoring_status",
            self.settlement_monitoring_status,
            STATUSES,
        )
        for field_name in (
            "settlement_monitoring_priority_score",
            "resolution_quality_risk_score",
            "rule_risk_score",
            "review_readiness_score",
            "review_readiness_gap_score",
            "combined_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "desensitized_monitoring_priority",
            _normalize_count_decimal(
                "desensitized_monitoring_priority",
                self.desensitized_monitoring_priority,
            ),
        )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchResolutionWatchQueueReport:
    generated_at: datetime
    config_version: str
    item_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_combined_watch_score: Decimal
    average_combined_watch_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchResolutionWatchQueueRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("ResearchResolutionWatchQueueReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchResolutionWatchQueueReport:
            raise ValueError("report must be a ResearchResolutionWatchQueueReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_safe_public_string("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_RESEARCH_RESOLUTION_WATCH_QUEUE_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("item_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_combined_watch_score",
            "average_combined_watch_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)


def build_research_resolution_watch_queue(
    items: object,
    *,
    config: ResearchResolutionWatchQueueConfig,
    generated_at: datetime,
) -> ResearchResolutionWatchQueueReport:
    if type(config) is not ResearchResolutionWatchQueueConfig:
        raise ValueError("config must be a ResearchResolutionWatchQueueConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    provisional_rows = tuple(_row_for_item(row, config) for row in _normalize_items(items))
    sorted_rows = tuple(sorted(provisional_rows, key=_row_sort_key))
    rows = tuple(
        _row_with_priority(row, _count_decimal(index))
        for index, row in enumerate(sorted_rows, start=1)
    )
    return ResearchResolutionWatchQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        item_count=_count_decimal(len(rows)),
        pass_count=_count_decimal(sum(row.status == "pass" for row in rows)),
        watch_count=_count_decimal(sum(row.status == "watch" for row in rows)),
        block_count=_count_decimal(sum(row.status == "block" for row in rows)),
        max_combined_watch_score=_max_score(rows),
        average_combined_watch_score=_average_score(rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_resolution_watch_queue_payload(
    report: ResearchResolutionWatchQueueReport,
) -> dict[str, Any]:
    if type(report) is not ResearchResolutionWatchQueueReport:
        raise ValueError("report must be a ResearchResolutionWatchQueueReport")
    _require_hard_flags("report", report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    validate_research_resolution_watch_queue_public_payload(payload)
    return payload


def validate_research_resolution_watch_queue_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _reject_public_numerics(payload)
    _validate_public_statuses(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    without_digest = dict(payload)
    without_digest.pop("derived_validation_digest", None)
    expected_digest = _digest_payload(without_digest)
    if digest != expected_digest:
        raise ValueError("derived_validation_digest does not match public payload")
    return True


@dataclass(frozen=True)
class _DictFlags:
    value: dict[str, Any]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")


def _row_for_item(
    row: ResearchResolutionWatchQueueItem,
    config: ResearchResolutionWatchQueueConfig,
) -> ResearchResolutionWatchQueueRow:
    review_readiness_gap_score = _q(ONE - row.review_readiness_score)
    combined_watch_score = _q(
        (row.settlement_monitoring_priority_score * config.settlement_monitoring_weight)
        + (row.resolution_quality_risk_score * config.resolution_quality_weight)
        + (row.rule_risk_score * config.rule_risk_weight)
        + (review_readiness_gap_score * config.review_readiness_gap_weight),
    )
    status = _row_status(
        row=row,
        review_readiness_gap_score=review_readiness_gap_score,
        combined_watch_score=combined_watch_score,
        config=config,
    )
    return ResearchResolutionWatchQueueRow(
        research_item_reference=row.research_item_reference,
        settlement_monitoring_status=row.settlement_monitoring_status,
        settlement_monitoring_priority_score=row.settlement_monitoring_priority_score,
        resolution_quality_risk_score=row.resolution_quality_risk_score,
        rule_risk_score=row.rule_risk_score,
        review_readiness_score=row.review_readiness_score,
        review_readiness_gap_score=review_readiness_gap_score,
        combined_watch_score=combined_watch_score,
        desensitized_monitoring_priority=ZERO,
        status=status,
        reason_codes=_row_reason_codes(row=row, combined_watch_score=combined_watch_score, config=config),
    )


def _row_status(
    *,
    row: ResearchResolutionWatchQueueItem,
    review_readiness_gap_score: Decimal,
    combined_watch_score: Decimal,
    config: ResearchResolutionWatchQueueConfig,
) -> str:
    del review_readiness_gap_score
    if (
        row.settlement_monitoring_status == "block"
        or row.settlement_monitoring_priority_score
        > config.max_watch_settlement_monitoring_priority_score
        or row.resolution_quality_risk_score
        > config.max_watch_resolution_quality_risk_score
        or row.rule_risk_score > config.max_watch_rule_risk_score
        or row.review_readiness_score < config.min_watch_review_readiness_score
        or combined_watch_score > config.max_watch_combined_watch_score
    ):
        return "block"
    if (
        row.settlement_monitoring_status == "watch"
        or row.settlement_monitoring_priority_score
        > config.max_pass_settlement_monitoring_priority_score
        or row.resolution_quality_risk_score
        > config.max_pass_resolution_quality_risk_score
        or row.rule_risk_score > config.max_pass_rule_risk_score
        or row.review_readiness_score < config.min_pass_review_readiness_score
        or combined_watch_score > config.max_pass_combined_watch_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    row: ResearchResolutionWatchQueueItem,
    combined_watch_score: Decimal,
    config: ResearchResolutionWatchQueueConfig,
) -> tuple[str, ...]:
    status = _row_status(
        row=row,
        review_readiness_gap_score=_q(ONE - row.review_readiness_score),
        combined_watch_score=combined_watch_score,
        config=config,
    )
    reason_codes: list[str] = [f"resolution_watch_queue_{status}"]
    if status == "pass":
        return tuple(reason_codes)
    settlement_reason = _settlement_monitoring_reason(row, config)
    if settlement_reason is not None:
        reason_codes.append(settlement_reason)
    quality_reason = _upper_component_reason(
        value=row.resolution_quality_risk_score,
        pass_threshold=config.max_pass_resolution_quality_risk_score,
        watch_threshold=config.max_watch_resolution_quality_risk_score,
        watch_code="resolution_quality_watch",
        block_code="resolution_quality_block",
    )
    if quality_reason is not None:
        reason_codes.append(quality_reason)
    rule_reason = _upper_component_reason(
        value=row.rule_risk_score,
        pass_threshold=config.max_pass_rule_risk_score,
        watch_threshold=config.max_watch_rule_risk_score,
        watch_code="rule_risk_watch",
        block_code="rule_risk_block",
    )
    if rule_reason is not None:
        reason_codes.append(rule_reason)
    readiness_reason = _lower_component_reason(
        value=row.review_readiness_score,
        pass_threshold=config.min_pass_review_readiness_score,
        watch_threshold=config.min_watch_review_readiness_score,
        watch_code="review_readiness_watch",
        block_code="review_readiness_block",
    )
    if readiness_reason is not None:
        reason_codes.append(readiness_reason)
    return tuple(reason_codes)


def _settlement_monitoring_reason(
    row: ResearchResolutionWatchQueueItem,
    config: ResearchResolutionWatchQueueConfig,
) -> str | None:
    if (
        row.settlement_monitoring_status == "block"
        or row.settlement_monitoring_priority_score
        > config.max_watch_settlement_monitoring_priority_score
    ):
        return "settlement_monitoring_block"
    if (
        row.settlement_monitoring_status == "watch"
        or row.settlement_monitoring_priority_score
        > config.max_pass_settlement_monitoring_priority_score
    ):
        return "settlement_monitoring_watch"
    return None


def _upper_component_reason(
    *,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> str | None:
    if value > watch_threshold:
        return block_code
    if value > pass_threshold:
        return watch_code
    return None


def _lower_component_reason(
    *,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    watch_code: str,
    block_code: str,
) -> str | None:
    if value < watch_threshold:
        return block_code
    if value < pass_threshold:
        return watch_code
    return None


def _row_with_priority(
    row: ResearchResolutionWatchQueueRow,
    desensitized_monitoring_priority: Decimal,
) -> ResearchResolutionWatchQueueRow:
    return ResearchResolutionWatchQueueRow(
        research_item_reference=row.research_item_reference,
        settlement_monitoring_status=row.settlement_monitoring_status,
        settlement_monitoring_priority_score=row.settlement_monitoring_priority_score,
        resolution_quality_risk_score=row.resolution_quality_risk_score,
        rule_risk_score=row.rule_risk_score,
        review_readiness_score=row.review_readiness_score,
        review_readiness_gap_score=row.review_readiness_gap_score,
        combined_watch_score=row.combined_watch_score,
        desensitized_monitoring_priority=desensitized_monitoring_priority,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_sort_key(row: ResearchResolutionWatchQueueRow) -> tuple[int, Decimal, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        -row.combined_watch_score,
        row.research_item_reference,
    )


def _report_status(rows: tuple[ResearchResolutionWatchQueueRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchResolutionWatchQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("resolution_watch_queue_no_items",)
    reason_codes: list[str] = []
    if any(row.status == "block" for row in rows):
        reason_codes.append("resolution_watch_queue_block_present")
    if any(row.status == "watch" for row in rows):
        reason_codes.append("resolution_watch_queue_watch_present")
    for block_code, watch_code in (
        ("settlement_monitoring_block", "settlement_monitoring_watch"),
        ("resolution_quality_block", "resolution_quality_watch"),
        ("rule_risk_block", "rule_risk_watch"),
        ("review_readiness_block", "review_readiness_watch"),
    ):
        if any(block_code in row.reason_codes for row in rows):
            reason_codes.append(f"{block_code}_present")
        elif any(watch_code in row.reason_codes for row in rows):
            reason_codes.append(f"{watch_code}_present")
    if not reason_codes:
        reason_codes.append("resolution_watch_queue_clear")
    return tuple(reason_codes)


def _normalize_items(
    values: object,
) -> tuple[ResearchResolutionWatchQueueItem, ...]:
    if type(values) not in (list, tuple):
        raise ValueError("items must be a list or tuple")
    normalized: list[ResearchResolutionWatchQueueItem] = []
    seen: set[str] = set()
    for value in values:
        if type(value) is ResearchResolutionWatchQueueItem:
            item = value
        elif type(value) is ResearchResolutionWatchQueueRow:
            item = ResearchResolutionWatchQueueItem(
                research_item_reference=value.research_item_reference,
                settlement_monitoring_status=value.settlement_monitoring_status,
                settlement_monitoring_priority_score=value.settlement_monitoring_priority_score,
                resolution_quality_risk_score=value.resolution_quality_risk_score,
                rule_risk_score=value.rule_risk_score,
                review_readiness_score=value.review_readiness_score,
            )
        else:
            raise ValueError(
                "items must be ResearchResolutionWatchQueueItem or "
                "ResearchResolutionWatchQueueRow",
            )
        _require_hard_flags("item", item)
        if item.research_item_reference in seen:
            raise ValueError("duplicate research_item_reference")
        seen.add(item.research_item_reference)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(values: object) -> tuple[ResearchResolutionWatchQueueRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    rows = tuple(values)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must be sorted by watch priority")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchResolutionWatchQueueRow:
            raise ValueError("rows must contain ResearchResolutionWatchQueueRow")
        _require_hard_flags("row", row)
        if row.research_item_reference in seen:
            raise ValueError("duplicate research_item_reference")
        seen.add(row.research_item_reference)
    return rows


def _normalize_reason_codes(
    field_name: str,
    value: object,
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must be unique")
    for reason_code in reason_codes:
        _require_member(field_name, reason_code, allowed)
        _reject_unsafe_public_string(field_name, reason_code)
    return reason_codes


def _validate_config_thresholds(config: ResearchResolutionWatchQueueConfig) -> None:
    if config.max_pass_combined_watch_score > config.max_watch_combined_watch_score:
        raise ValueError(
            "max_pass_combined_watch_score must not exceed watch threshold",
        )
    if (
        config.max_pass_settlement_monitoring_priority_score
        > config.max_watch_settlement_monitoring_priority_score
    ):
        raise ValueError(
            "max_pass_settlement_monitoring_priority_score must not exceed watch threshold",
        )
    if (
        config.max_pass_resolution_quality_risk_score
        > config.max_watch_resolution_quality_risk_score
    ):
        raise ValueError(
            "max_pass_resolution_quality_risk_score must not exceed watch threshold",
        )
    if config.max_pass_rule_risk_score > config.max_watch_rule_risk_score:
        raise ValueError("max_pass_rule_risk_score must not exceed watch threshold")
    if config.min_pass_review_readiness_score < config.min_watch_review_readiness_score:
        raise ValueError(
            "min_pass_review_readiness_score must be at least watch threshold",
        )


def _validate_row(row: ResearchResolutionWatchQueueRow) -> None:
    if row.review_readiness_gap_score != _q(ONE - row.review_readiness_score):
        raise ValueError("review_readiness_gap_score must match review_readiness_score")
    if row.reason_codes[0] != f"resolution_watch_queue_{row.status}":
        raise ValueError("reason_codes must include row status")


def _validate_report(report: ResearchResolutionWatchQueueReport) -> None:
    rows = report.rows
    if report.item_count != _count_decimal(len(rows)):
        raise ValueError("item_count must match rows")
    if report.pass_count != _count_decimal(sum(row.status == "pass" for row in rows)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count_decimal(sum(row.status == "watch" for row in rows)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count_decimal(sum(row.status == "block" for row in rows)):
        raise ValueError("block_count must match rows")
    if report.max_combined_watch_score != _max_score(rows):
        raise ValueError("max_combined_watch_score must match rows")
    if report.average_combined_watch_score != _average_score(rows):
        raise ValueError("average_combined_watch_score must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    for index, row in enumerate(rows, start=1):
        if row.desensitized_monitoring_priority != _count_decimal(index):
            raise ValueError("desensitized_monitoring_priority must match row order")


def _validate_public_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if key in {"status", "settlement_monitoring_status"}:
                _require_member(key, item, STATUSES)
            _validate_public_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_statuses(item)


def _weight_sum(config: ResearchResolutionWatchQueueConfig) -> Decimal:
    return _q(
        config.settlement_monitoring_weight
        + config.resolution_quality_weight
        + config.rule_risk_weight
        + config.review_readiness_gap_weight,
    )


def _max_score(rows: tuple[ResearchResolutionWatchQueueRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.combined_watch_score for row in rows)


def _average_score(rows: tuple[ResearchResolutionWatchQueueRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    total = sum((row.combined_watch_score for row in rows), ZERO)
    with localcontext(DECIMAL_CONTEXT):
        return (total / _count_decimal(len(rows))).quantize(QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < QUANTUM.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    return _q(value)


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_safe_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "" or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical public string")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be supported")


def _require_hard_flags(field_name: str, value: object) -> None:
    for flag_name in SAFETY_FLAG_NAMES:
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{field_name} {flag_name} must be True")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {field_name}")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        _reject_unsafe_public_string(path or label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            nested_path = key if not path else f"{path}.{key}"
            _reject_unsafe_public_string(f"{label} key", key)
            if key in SAFETY_FLAG_NAMES and item is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if type(value) in (Decimal, float, int):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None or type(value) is bool or type(value) is str:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    raise ValueError("value is not JSON serializable")


def _derived_validation_digest(report: ResearchResolutionWatchQueueReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    _reject_unsafe_public_payload("digest payload", payload)
    _reject_public_numerics(payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
