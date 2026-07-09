"""Public-safe specialist review capacity pressure forecast report."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_REVIEW_CAPACITY_FORECAST_REPORT_CONFIG_VERSION",
    "PUBLIC_STATUSES",
    "ResearchTeamReviewCapacityForecastConfig",
    "ResearchTeamReviewCapacityForecastInput",
    "ResearchTeamReviewCapacityForecastReasonCodeCount",
    "ResearchTeamReviewCapacityForecastReport",
    "ResearchTeamReviewCapacityForecastRow",
    "build_research_team_review_capacity_forecast_report",
    "research_team_review_capacity_forecast_report_payload",
)


DEFAULT_RESEARCH_TEAM_REVIEW_CAPACITY_FORECAST_REPORT_CONFIG_VERSION = (
    "research-team-review-capacity-forecast-report-v0"
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
PUBLIC_STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

CLEAR_REASON = "review_capacity_pressure_clear"
NO_INPUTS_REASON = "no_review_domains"
REPORT_PASS_REASON = "review_capacity_pressure_report_pass"
REPORT_WATCH_REASON = "review_capacity_pressure_report_watch"
REPORT_BLOCK_REASON = "review_capacity_pressure_report_block"
CAPACITY_WATCH_REASON = "weighted_capacity_pressure_watch"
CAPACITY_BLOCK_REASON = "weighted_capacity_pressure_block"
QUEUE_WATCH_REASON = "queue_load_watch"
QUEUE_BLOCK_REASON = "queue_load_block"
STALE_MEMORY_WATCH_REASON = "stale_memory_watch"
STALE_MEMORY_BLOCK_REASON = "stale_memory_block"
CALIBRATION_WATCH_REASON = "calibration_backlog_watch"
CALIBRATION_BLOCK_REASON = "calibration_backlog_block"
CORRECTION_DEBT_WATCH_REASON = "correction_debt_watch"
CORRECTION_DEBT_BLOCK_REASON = "correction_debt_block"

REASON_CODE_SEQUENCE = (
    NO_INPUTS_REASON,
    REPORT_BLOCK_REASON,
    CAPACITY_BLOCK_REASON,
    QUEUE_BLOCK_REASON,
    STALE_MEMORY_BLOCK_REASON,
    CALIBRATION_BLOCK_REASON,
    CORRECTION_DEBT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    CAPACITY_WATCH_REASON,
    QUEUE_WATCH_REASON,
    STALE_MEMORY_WATCH_REASON,
    CALIBRATION_WATCH_REASON,
    CORRECTION_DEBT_WATCH_REASON,
    REPORT_PASS_REASON,
    CLEAR_REASON,
)

UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "market_id",
    "marketid",
    "market_slug",
    "marketslug",
    "market_question",
    "question",
    "source_url",
    "source_text",
    "source",
    "url",
    "://",
    "dsn",
    "table_name",
    "table",
    "token",
    "wallet",
    "auth",
    "order",
    "trade",
    "live",
    "network",
    "database",
    "recommend",
    "sizing",
    "secret",
    "password",
    "credential",
    "private_key",
    "api_key",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_REVIEW_CAPACITY_FORECAST_REPORT_CONFIG_VERSION
    )
    watch_capacity_pressure_ratio: Decimal = Decimal("0.700000")
    block_capacity_pressure_ratio: Decimal = Decimal("1.000000")
    watch_queue_pressure_ratio: Decimal = Decimal("0.750000")
    block_queue_pressure_ratio: Decimal = Decimal("1.000000")
    watch_stale_memory_pressure_ratio: Decimal = Decimal("0.500000")
    block_stale_memory_pressure_ratio: Decimal = Decimal("1.000000")
    watch_calibration_backlog_pressure_ratio: Decimal = Decimal("0.250000")
    block_calibration_backlog_pressure_ratio: Decimal = Decimal("0.750000")
    watch_correction_debt_pressure_ratio: Decimal = Decimal("0.250000")
    block_correction_debt_pressure_ratio: Decimal = Decimal("0.500000")
    queue_load_weight: Decimal = Decimal("1.000000")
    stale_memory_weight: Decimal = Decimal("1.250000")
    calibration_backlog_weight: Decimal = Decimal("0.500000")
    correction_debt_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewCapacityForecastConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "watch_capacity_pressure_ratio",
            "block_capacity_pressure_ratio",
            "watch_queue_pressure_ratio",
            "block_queue_pressure_ratio",
            "watch_stale_memory_pressure_ratio",
            "block_stale_memory_pressure_ratio",
            "watch_calibration_backlog_pressure_ratio",
            "block_calibration_backlog_pressure_ratio",
            "watch_correction_debt_pressure_ratio",
            "block_correction_debt_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "queue_load_weight",
            "stale_memory_weight",
            "calibration_backlog_weight",
            "correction_debt_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_threshold_order(
            "watch_capacity_pressure_ratio",
            self.watch_capacity_pressure_ratio,
            "block_capacity_pressure_ratio",
            self.block_capacity_pressure_ratio,
        )
        _require_threshold_order(
            "watch_queue_pressure_ratio",
            self.watch_queue_pressure_ratio,
            "block_queue_pressure_ratio",
            self.block_queue_pressure_ratio,
        )
        _require_threshold_order(
            "watch_stale_memory_pressure_ratio",
            self.watch_stale_memory_pressure_ratio,
            "block_stale_memory_pressure_ratio",
            self.block_stale_memory_pressure_ratio,
        )
        _require_threshold_order(
            "watch_calibration_backlog_pressure_ratio",
            self.watch_calibration_backlog_pressure_ratio,
            "block_calibration_backlog_pressure_ratio",
            self.block_calibration_backlog_pressure_ratio,
        )
        _require_threshold_order(
            "watch_correction_debt_pressure_ratio",
            self.watch_correction_debt_pressure_ratio,
            "block_correction_debt_pressure_ratio",
            self.block_correction_debt_pressure_ratio,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastInput(_FinalPublicDataclass):
    team_key: str
    domain: str
    current_queue_load: Decimal
    stale_memory_count: Decimal
    calibration_backlog_count: Decimal
    correction_debt_count: Decimal
    available_analyst_capacity: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewCapacityForecastInput, "input")
        object.__setattr__(
            self,
            "team_key",
            _require_public_string("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "domain",
            _require_public_string("domain", self.domain),
        )
        for field_name in (
            "current_queue_load",
            "stale_memory_count",
            "calibration_backlog_count",
            "correction_debt_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_analyst_capacity",
            _require_positive_decimal(
                "available_analyst_capacity",
                self.available_analyst_capacity,
            ),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastRow(_FinalPublicDataclass):
    team_key: str
    domain: str
    current_queue_load: Decimal
    stale_memory_count: Decimal
    calibration_backlog_count: Decimal
    correction_debt_count: Decimal
    available_analyst_capacity: Decimal
    queue_pressure_ratio: Decimal
    stale_memory_pressure_ratio: Decimal
    calibration_backlog_pressure_ratio: Decimal
    correction_debt_pressure_ratio: Decimal
    weighted_review_load: Decimal
    capacity_pressure_ratio: Decimal
    capacity_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewCapacityForecastRow, "row")
        object.__setattr__(
            self,
            "team_key",
            _require_public_string("team_key", self.team_key),
        )
        object.__setattr__(
            self,
            "domain",
            _require_public_string("domain", self.domain),
        )
        for field_name in (
            "current_queue_load",
            "stale_memory_count",
            "calibration_backlog_count",
            "correction_debt_count",
            "queue_pressure_ratio",
            "stale_memory_pressure_ratio",
            "calibration_backlog_pressure_ratio",
            "correction_debt_pressure_ratio",
            "weighted_review_load",
            "capacity_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_analyst_capacity",
            _require_positive_decimal(
                "available_analyst_capacity",
                self.available_analyst_capacity,
            ),
        )
        _require_status("capacity_status", self.capacity_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    domain_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamReviewCapacityForecastReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "domain_ratio",
            _require_nonnegative_decimal("domain_ratio", self.domain_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamReviewCapacityForecastReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    capacity_status: str
    report_status: str
    domain_count: Decimal
    pass_domain_count: Decimal
    watch_domain_count: Decimal
    block_domain_count: Decimal
    total_current_queue_load: Decimal
    total_stale_memory_count: Decimal
    total_calibration_backlog_count: Decimal
    total_correction_debt_count: Decimal
    total_available_analyst_capacity: Decimal
    weighted_capacity_pressure_ratio: Decimal
    max_capacity_pressure_ratio: Decimal
    rows: tuple[ResearchTeamReviewCapacityForecastRow, ...]
    reason_code_counts: tuple[ResearchTeamReviewCapacityForecastReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamReviewCapacityForecastReport, "report")
        object.__setattr__(
            self,
            "generated_at",
            _require_utc_datetime("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        _require_status("capacity_status", self.capacity_status)
        _require_status("report_status", self.report_status)
        if self.capacity_status != self.report_status:
            raise ValueError("capacity_status must match report_status")
        for field_name in (
            "domain_count",
            "pass_domain_count",
            "watch_domain_count",
            "block_domain_count",
            "total_current_queue_load",
            "total_stale_memory_count",
            "total_calibration_backlog_count",
            "total_correction_debt_count",
            "total_available_analyst_capacity",
            "weighted_capacity_pressure_ratio",
            "max_capacity_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.rows) is not tuple:
            raise ValueError("rows must be a tuple")
        for row in self.rows:
            if type(row) is not ResearchTeamReviewCapacityForecastRow:
                raise ValueError(
                    "rows must contain ResearchTeamReviewCapacityForecastRow",
                )
            _require_hard_flags("row", row)
        if type(self.reason_code_counts) is not tuple:
            raise ValueError("reason_code_counts must be a tuple")
        for item in self.reason_code_counts:
            if type(item) is not ResearchTeamReviewCapacityForecastReasonCodeCount:
                raise ValueError(
                    "reason_code_counts must contain "
                    "ResearchTeamReviewCapacityForecastReasonCodeCount",
                )
            _require_hard_flags("reason_code_count", item)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, require_nonempty=True),
        )
        if type(self.payload_digest) is not str:
            raise ValueError("payload_digest must be a string")
        current_digest = self.payload_digest
        object.__setattr__(self, "payload_digest", "")
        expected_digest = _digest_payload(_report_payload_without_digest(self))
        if current_digest and current_digest != expected_digest:
            raise ValueError("payload_digest does not match report payload")
        object.__setattr__(self, "payload_digest", expected_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)

    @property
    def payload(self) -> dict[str, Any]:
        return research_team_review_capacity_forecast_report_payload(self)


def build_research_team_review_capacity_forecast_report(
    input_rows: Any,
    *,
    generated_at: datetime,
    config: ResearchTeamReviewCapacityForecastConfig | None = None,
) -> ResearchTeamReviewCapacityForecastReport:
    cfg = config or ResearchTeamReviewCapacityForecastConfig()
    if type(cfg) is not ResearchTeamReviewCapacityForecastConfig:
        raise ValueError("config must be a ResearchTeamReviewCapacityForecastConfig")
    _require_hard_flags("config", cfg)
    rows = tuple(_row_from_item(item, cfg) for item in _normalize_items(input_rows))
    ranked_rows = tuple(sorted(rows, key=_row_rank_key))
    domain_count = _count(len(ranked_rows))
    pass_domain_count = _count(
        sum(1 for row in ranked_rows if row.capacity_status == STATUS_PASS),
    )
    watch_domain_count = _count(
        sum(1 for row in ranked_rows if row.capacity_status == STATUS_WATCH),
    )
    block_domain_count = _count(
        sum(1 for row in ranked_rows if row.capacity_status == STATUS_BLOCK),
    )
    total_current_queue_load = _sum_decimal(
        row.current_queue_load for row in ranked_rows
    )
    total_stale_memory_count = _sum_decimal(
        row.stale_memory_count for row in ranked_rows
    )
    total_calibration_backlog_count = _sum_decimal(
        row.calibration_backlog_count for row in ranked_rows
    )
    total_correction_debt_count = _sum_decimal(
        row.correction_debt_count for row in ranked_rows
    )
    total_available_analyst_capacity = _sum_decimal(
        row.available_analyst_capacity for row in ranked_rows
    )
    report_status = _report_status(
        has_inputs=bool(ranked_rows),
        block_domain_count=block_domain_count,
        watch_domain_count=watch_domain_count,
    )
    return ResearchTeamReviewCapacityForecastReport(
        generated_at=generated_at,
        config_version=cfg.config_version,
        capacity_status=report_status,
        report_status=report_status,
        domain_count=domain_count,
        pass_domain_count=pass_domain_count,
        watch_domain_count=watch_domain_count,
        block_domain_count=block_domain_count,
        total_current_queue_load=total_current_queue_load,
        total_stale_memory_count=total_stale_memory_count,
        total_calibration_backlog_count=total_calibration_backlog_count,
        total_correction_debt_count=total_correction_debt_count,
        total_available_analyst_capacity=total_available_analyst_capacity,
        weighted_capacity_pressure_ratio=_ratio(
            _sum_decimal(row.weighted_review_load for row in ranked_rows),
            total_available_analyst_capacity,
        ),
        max_capacity_pressure_ratio=max(
            (row.capacity_pressure_ratio for row in ranked_rows),
            default=ZERO,
        ),
        rows=ranked_rows,
        reason_code_counts=_reason_code_counts(ranked_rows),
        reason_codes=_report_reason_codes(report_status, ranked_rows),
    )


def research_team_review_capacity_forecast_report_payload(
    report: ResearchTeamReviewCapacityForecastReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamReviewCapacityForecastReport:
        _require_hard_flags("report", report)
        payload = _report_payload_without_digest(report)
        payload["payload_digest"] = report.payload_digest
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        payload = _json_ready(report)
        if type(payload) is not dict:
            raise ValueError("public payload must be a JSON object")
        _validate_public_payload(payload)
        return payload
    raise ValueError("report must be a ResearchTeamReviewCapacityForecastReport")


def _row_from_item(
    item: object,
    config: ResearchTeamReviewCapacityForecastConfig,
) -> ResearchTeamReviewCapacityForecastRow:
    if type(item) is ResearchTeamReviewCapacityForecastRow:
        _require_hard_flags("row", item)
        return item
    if type(item) is not ResearchTeamReviewCapacityForecastInput:
        raise ValueError(
            "input_rows must contain ResearchTeamReviewCapacityForecastInput",
        )
    _require_hard_flags("input", item)
    queue_pressure_ratio = _ratio(
        item.current_queue_load,
        item.available_analyst_capacity,
    )
    stale_memory_pressure_ratio = _ratio(
        item.stale_memory_count,
        item.available_analyst_capacity,
    )
    calibration_backlog_pressure_ratio = _ratio(
        item.calibration_backlog_count,
        item.available_analyst_capacity,
    )
    correction_debt_pressure_ratio = _ratio(
        item.correction_debt_count,
        item.available_analyst_capacity,
    )
    weighted_review_load = _weighted_review_load(item, config)
    capacity_pressure_ratio = _ratio(
        weighted_review_load,
        item.available_analyst_capacity,
    )
    capacity_status = _row_status(
        config,
        capacity_pressure_ratio=capacity_pressure_ratio,
        queue_pressure_ratio=queue_pressure_ratio,
        stale_memory_pressure_ratio=stale_memory_pressure_ratio,
        calibration_backlog_pressure_ratio=calibration_backlog_pressure_ratio,
        correction_debt_pressure_ratio=correction_debt_pressure_ratio,
    )
    return ResearchTeamReviewCapacityForecastRow(
        team_key=item.team_key,
        domain=item.domain,
        current_queue_load=item.current_queue_load,
        stale_memory_count=item.stale_memory_count,
        calibration_backlog_count=item.calibration_backlog_count,
        correction_debt_count=item.correction_debt_count,
        available_analyst_capacity=item.available_analyst_capacity,
        queue_pressure_ratio=queue_pressure_ratio,
        stale_memory_pressure_ratio=stale_memory_pressure_ratio,
        calibration_backlog_pressure_ratio=calibration_backlog_pressure_ratio,
        correction_debt_pressure_ratio=correction_debt_pressure_ratio,
        weighted_review_load=weighted_review_load,
        capacity_pressure_ratio=capacity_pressure_ratio,
        capacity_status=capacity_status,
        reason_codes=_row_reason_codes(
            config,
            capacity_pressure_ratio=capacity_pressure_ratio,
            queue_pressure_ratio=queue_pressure_ratio,
            stale_memory_pressure_ratio=stale_memory_pressure_ratio,
            calibration_backlog_pressure_ratio=calibration_backlog_pressure_ratio,
            correction_debt_pressure_ratio=correction_debt_pressure_ratio,
        ),
    )


def _weighted_review_load(
    item: ResearchTeamReviewCapacityForecastInput,
    config: ResearchTeamReviewCapacityForecastConfig,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(
            "weighted_review_load",
            (item.current_queue_load * config.queue_load_weight)
            + (item.stale_memory_count * config.stale_memory_weight)
            + (item.calibration_backlog_count * config.calibration_backlog_weight)
            + (item.correction_debt_count * config.correction_debt_weight),
        )


def _row_status(
    config: ResearchTeamReviewCapacityForecastConfig,
    *,
    capacity_pressure_ratio: Decimal,
    queue_pressure_ratio: Decimal,
    stale_memory_pressure_ratio: Decimal,
    calibration_backlog_pressure_ratio: Decimal,
    correction_debt_pressure_ratio: Decimal,
) -> str:
    if (
        capacity_pressure_ratio >= config.block_capacity_pressure_ratio
        or queue_pressure_ratio >= config.block_queue_pressure_ratio
        or stale_memory_pressure_ratio >= config.block_stale_memory_pressure_ratio
        or calibration_backlog_pressure_ratio
        >= config.block_calibration_backlog_pressure_ratio
        or correction_debt_pressure_ratio >= config.block_correction_debt_pressure_ratio
    ):
        return STATUS_BLOCK
    if (
        capacity_pressure_ratio >= config.watch_capacity_pressure_ratio
        or queue_pressure_ratio >= config.watch_queue_pressure_ratio
        or stale_memory_pressure_ratio >= config.watch_stale_memory_pressure_ratio
        or calibration_backlog_pressure_ratio
        >= config.watch_calibration_backlog_pressure_ratio
        or correction_debt_pressure_ratio >= config.watch_correction_debt_pressure_ratio
    ):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    config: ResearchTeamReviewCapacityForecastConfig,
    *,
    capacity_pressure_ratio: Decimal,
    queue_pressure_ratio: Decimal,
    stale_memory_pressure_ratio: Decimal,
    calibration_backlog_pressure_ratio: Decimal,
    correction_debt_pressure_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_pressure_reason(
        reasons,
        capacity_pressure_ratio,
        watch_threshold=config.watch_capacity_pressure_ratio,
        block_threshold=config.block_capacity_pressure_ratio,
        watch_reason=CAPACITY_WATCH_REASON,
        block_reason=CAPACITY_BLOCK_REASON,
    )
    _append_pressure_reason(
        reasons,
        queue_pressure_ratio,
        watch_threshold=config.watch_queue_pressure_ratio,
        block_threshold=config.block_queue_pressure_ratio,
        watch_reason=QUEUE_WATCH_REASON,
        block_reason=QUEUE_BLOCK_REASON,
    )
    _append_pressure_reason(
        reasons,
        stale_memory_pressure_ratio,
        watch_threshold=config.watch_stale_memory_pressure_ratio,
        block_threshold=config.block_stale_memory_pressure_ratio,
        watch_reason=STALE_MEMORY_WATCH_REASON,
        block_reason=STALE_MEMORY_BLOCK_REASON,
    )
    _append_pressure_reason(
        reasons,
        calibration_backlog_pressure_ratio,
        watch_threshold=config.watch_calibration_backlog_pressure_ratio,
        block_threshold=config.block_calibration_backlog_pressure_ratio,
        watch_reason=CALIBRATION_WATCH_REASON,
        block_reason=CALIBRATION_BLOCK_REASON,
    )
    _append_pressure_reason(
        reasons,
        correction_debt_pressure_ratio,
        watch_threshold=config.watch_correction_debt_pressure_ratio,
        block_threshold=config.block_correction_debt_pressure_ratio,
        watch_reason=CORRECTION_DEBT_WATCH_REASON,
        block_reason=CORRECTION_DEBT_BLOCK_REASON,
    )
    if not reasons:
        reasons.append(CLEAR_REASON)
    return _normalize_reason_codes(tuple(reasons), require_nonempty=True)


def _append_pressure_reason(
    reasons: list[str],
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
    watch_reason: str,
    block_reason: str,
) -> None:
    if value >= block_threshold:
        reasons.append(block_reason)
        return
    if value >= watch_threshold:
        reasons.append(watch_reason)


def _report_status(
    *,
    has_inputs: bool,
    block_domain_count: Decimal,
    watch_domain_count: Decimal,
) -> str:
    if not has_inputs:
        return STATUS_PASS
    if block_domain_count > ZERO:
        return STATUS_BLOCK
    if watch_domain_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    report_status: str,
    rows: tuple[ResearchTeamReviewCapacityForecastRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    reasons: list[str] = [
        {
            STATUS_BLOCK: REPORT_BLOCK_REASON,
            STATUS_WATCH: REPORT_WATCH_REASON,
            STATUS_PASS: REPORT_PASS_REASON,
        }[report_status],
    ]
    for reason_code in REASON_CODE_SEQUENCE:
        if reason_code in {
            CLEAR_REASON,
            NO_INPUTS_REASON,
            REPORT_BLOCK_REASON,
            REPORT_WATCH_REASON,
            REPORT_PASS_REASON,
        }:
            continue
        if any(reason_code in row.reason_codes for row in rows):
            reasons.append(reason_code)
    return _normalize_reason_codes(tuple(reasons), require_nonempty=True)


def _reason_code_counts(
    rows: tuple[ResearchTeamReviewCapacityForecastRow, ...],
) -> tuple[ResearchTeamReviewCapacityForecastReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    domain_count = _count(len(rows))
    return tuple(
        ResearchTeamReviewCapacityForecastReasonCodeCount(
            reason_code=reason_code,
            count=_count(counter[reason_code]),
            domain_ratio=_ratio(_count(counter[reason_code]), domain_count),
        )
        for reason_code in REASON_CODE_SEQUENCE
        if counter[reason_code]
    )


def _normalize_items(input_rows: Any) -> tuple[object, ...]:
    if type(input_rows) is not tuple and type(input_rows) is not list:
        raise ValueError("input_rows must be a tuple or list")
    if len(input_rows) == 1 and (
        type(input_rows[0]) is tuple or type(input_rows[0]) is list
    ):
        return tuple(input_rows[0])
    return tuple(input_rows)


def _row_rank_key(row: ResearchTeamReviewCapacityForecastRow) -> tuple[object, ...]:
    status_rank = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}
    return (
        status_rank[row.capacity_status],
        -row.capacity_pressure_ratio,
        row.team_key,
        row.domain,
    )


def _report_payload_without_digest(
    report: ResearchTeamReviewCapacityForecastReport,
) -> dict[str, Any]:
    return {
        "generated_at": _json_ready(report.generated_at),
        "config_version": report.config_version,
        "capacity_status": report.capacity_status,
        "report_status": report.report_status,
        "domain_count": _decimal_payload(report.domain_count),
        "pass_domain_count": _decimal_payload(report.pass_domain_count),
        "watch_domain_count": _decimal_payload(report.watch_domain_count),
        "block_domain_count": _decimal_payload(report.block_domain_count),
        "total_current_queue_load": _decimal_payload(report.total_current_queue_load),
        "total_stale_memory_count": _decimal_payload(report.total_stale_memory_count),
        "total_calibration_backlog_count": _decimal_payload(
            report.total_calibration_backlog_count,
        ),
        "total_correction_debt_count": _decimal_payload(
            report.total_correction_debt_count,
        ),
        "total_available_analyst_capacity": _decimal_payload(
            report.total_available_analyst_capacity,
        ),
        "weighted_capacity_pressure_ratio": _decimal_payload(
            report.weighted_capacity_pressure_ratio,
        ),
        "max_capacity_pressure_ratio": _decimal_payload(
            report.max_capacity_pressure_ratio,
        ),
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(item) for item in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _row_payload(row: ResearchTeamReviewCapacityForecastRow) -> dict[str, Any]:
    return {
        "team_key": row.team_key,
        "domain": row.domain,
        "current_queue_load": _decimal_payload(row.current_queue_load),
        "stale_memory_count": _decimal_payload(row.stale_memory_count),
        "calibration_backlog_count": _decimal_payload(row.calibration_backlog_count),
        "correction_debt_count": _decimal_payload(row.correction_debt_count),
        "available_analyst_capacity": _decimal_payload(
            row.available_analyst_capacity,
        ),
        "queue_pressure_ratio": _decimal_payload(row.queue_pressure_ratio),
        "stale_memory_pressure_ratio": _decimal_payload(
            row.stale_memory_pressure_ratio,
        ),
        "calibration_backlog_pressure_ratio": _decimal_payload(
            row.calibration_backlog_pressure_ratio,
        ),
        "correction_debt_pressure_ratio": _decimal_payload(
            row.correction_debt_pressure_ratio,
        ),
        "weighted_review_load": _decimal_payload(row.weighted_review_load),
        "capacity_pressure_ratio": _decimal_payload(row.capacity_pressure_ratio),
        "capacity_status": row.capacity_status,
        "reason_codes": list(row.reason_codes),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _reason_code_count_payload(
    item: ResearchTeamReviewCapacityForecastReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": item.reason_code,
        "count": _decimal_payload(item.count),
        "domain_ratio": _decimal_payload(item.domain_ratio),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_public_payload(payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _PayloadFlags(payload))
    _reject_flag_downgrades("public payload", payload)
    _validate_payload_statuses(payload)
    digest = payload.get("payload_digest")
    _require_digest("payload_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("payload_digest", None)
    expected_digest = _digest_payload(unsigned_payload)
    if digest != expected_digest:
        raise ValueError("payload_digest does not match public payload")


def _validate_payload_statuses(payload: dict[str, Any]) -> None:
    capacity_status = payload.get("capacity_status")
    report_status = payload.get("report_status")
    _require_status("capacity_status", capacity_status)
    _require_status("report_status", report_status)
    if capacity_status != report_status:
        raise ValueError("capacity_status must match report_status")
    rows = payload.get("rows")
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain public objects")
        _require_status("capacity_status", row.get("capacity_status"))


@dataclass(frozen=True)
class _PayloadFlags:
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


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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
        return _decimal_payload(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        return _require_utc_datetime("datetime", value).isoformat()
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("JSON public numeric values must be Decimal-derived strings")
    if type(value) is str:
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


def _decimal_payload(value: Decimal) -> str:
    return str(_quantize_decimal("payload decimal", value))


def _sum_decimal(values: Any) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize_decimal("sum", total)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal("ratio", numerator / denominator)


def _count(value: int) -> Decimal:
    return _quantize_decimal("count", Decimal(value))


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a non-empty public string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public material")
    return value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    decimal_value = value.quantize(DECIMAL_QUANTUM)
    if decimal_value != value:
        raise ValueError(f"{field_name} must use the required decimal precision")
    return decimal_value


def _quantize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value.quantize(DECIMAL_QUANTUM)


def _require_utc_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_threshold_order(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if block_value < watch_value:
        raise ValueError(f"{block_name} must be at least {watch_name}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in PUBLIC_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_reason_code(field_name: str, value: object) -> str:
    public_value = _require_public_string(field_name, value)
    if public_value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")
    return public_value


def _normalize_reason_codes(
    value: object,
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if require_nonempty and not value:
        raise ValueError("reason_codes must not be empty")
    seen: set[str] = set()
    normalized: list[str] = []
    for reason_code in value:
        public_reason_code = _require_reason_code("reason_codes", reason_code)
        if public_reason_code in seen:
            raise ValueError("reason_codes must be unique")
        seen.add(public_reason_code)
        normalized.append(public_reason_code)
    return tuple(
        reason_code
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _reject_flag_downgrades(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_flag_downgrades(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(label, item)


def _reject_public_numerics(value: object) -> None:
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
