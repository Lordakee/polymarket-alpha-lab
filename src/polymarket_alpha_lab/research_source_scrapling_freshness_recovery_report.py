"""Pure report-only reducer for Scrapling freshness recovery checks."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_UP, localcontext
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_CONFIG_VERSION = (
    "research-source-scrapling-freshness-recovery-report-v0"
)
RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_STATUSES = (
    "pass",
    "watch",
    "block",
)

QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400.000000")
MICROSECONDS_PER_SECOND = Decimal("1000000.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_UP)

PASS_REASON = "freshness_recovery_pass"
NO_INPUTS_REASON = "freshness_recovery_no_inputs"
REPORT_BLOCK_REASON = "freshness_recovery_report_block"
REPORT_WATCH_REASON = "freshness_recovery_report_watch"
REASON_CODE_SEQUENCE = (
    "recovery_missing_block",
    "recovery_latency_block",
    "recovery_latency_watch",
    "recovery_success_ratio_block",
    "recovery_success_ratio_watch",
    "fallback_retry_pressure_block",
    "fallback_retry_pressure_watch",
    "recovered_ratio_block",
    "recovered_ratio_watch",
    NO_INPUTS_REASON,
    REPORT_BLOCK_REASON,
    REPORT_WATCH_REASON,
    PASS_REASON,
)

PUBLIC_BUCKET_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "www.",
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source_url",
    "source-text",
    "source_text",
    "url",
    "dsn",
    "table",
    "token",
    "wallet",
    "order",
    "trade",
    "network",
    "database",
    "secret",
    "password",
    "private_key",
    "api_key",
    "authentication",
    "authorization",
    "auth",
    "bearer",
    "credential",
    "recommendation",
    "sizing",
    "live_surface",
)


@dataclass(frozen=True)
class ResearchSourceScraplingFreshnessRecoveryConfig:
    config_version: str = (
        DEFAULT_RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_CONFIG_VERSION
    )
    watch_recovered_ratio: Decimal = Decimal("0.800000")
    block_recovered_ratio: Decimal = Decimal("0.500000")
    watch_recovery_latency_seconds: Decimal = Decimal("1800.000000")
    block_recovery_latency_seconds: Decimal = Decimal("7200.000000")
    min_recovery_success_pass_ratio: Decimal = Decimal("0.800000")
    min_recovery_success_block_ratio: Decimal = Decimal("0.400000")
    max_fallback_retry_pass_ratio: Decimal = Decimal("0.250000")
    max_fallback_retry_block_ratio: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFreshnessRecoveryConfig:
            raise TypeError(
                "ResearchSourceScraplingFreshnessRecoveryConfig does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingFreshnessRecoveryConfig:
            raise ValueError(
                "config must be exactly "
                "ResearchSourceScraplingFreshnessRecoveryConfig",
            )
        _require_public_bucket("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_recovered_ratio",
            "block_recovered_ratio",
            "min_recovery_success_pass_ratio",
            "min_recovery_success_block_ratio",
            "max_fallback_retry_pass_ratio",
            "max_fallback_retry_block_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_recovery_latency_seconds",
            "block_recovery_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_recovered_ratio < self.block_recovered_ratio:
            raise ValueError("watch_recovered_ratio must not be below block threshold")
        if self.watch_recovery_latency_seconds > self.block_recovery_latency_seconds:
            raise ValueError(
                "watch_recovery_latency_seconds must not exceed block threshold",
            )
        if (
            self.min_recovery_success_pass_ratio
            < self.min_recovery_success_block_ratio
        ):
            raise ValueError(
                "min_recovery_success_pass_ratio must not be below block threshold",
            )
        if (
            self.max_fallback_retry_pass_ratio
            > self.max_fallback_retry_block_ratio
        ):
            raise ValueError(
                "max_fallback_retry_pass_ratio must not exceed block threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFreshnessRecoveryObservation:
    recovery_bucket: str
    first_stale_at: datetime
    recovered_at: datetime | None
    attempted_refresh_count: Decimal
    successful_refresh_count: Decimal
    fallback_retry_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFreshnessRecoveryObservation:
            raise TypeError(
                "ResearchSourceScraplingFreshnessRecoveryObservation does not "
                "support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingFreshnessRecoveryObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchSourceScraplingFreshnessRecoveryObservation",
            )
        object.__setattr__(
            self,
            "recovery_bucket",
            _require_public_bucket("recovery_bucket", self.recovery_bucket),
        )
        object.__setattr__(
            self,
            "first_stale_at",
            _as_utc("first_stale_at", self.first_stale_at),
        )
        object.__setattr__(
            self,
            "recovered_at",
            _as_optional_utc("recovered_at", self.recovered_at),
        )
        for field_name in (
            "attempted_refresh_count",
            "successful_refresh_count",
            "fallback_retry_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.attempted_refresh_count == ZERO:
            raise ValueError("attempted_refresh_count must be positive")
        if self.successful_refresh_count > self.attempted_refresh_count:
            raise ValueError(
                "successful_refresh_count must not exceed attempted_refresh_count",
            )
        if self.fallback_retry_count > self.attempted_refresh_count:
            raise ValueError(
                "fallback_retry_count must not exceed attempted_refresh_count",
            )
        if self.recovered_at is not None and self.recovered_at < self.first_stale_at:
            raise ValueError("recovered_at must not be before first_stale_at")
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFreshnessRecoveryReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason code count", self)


@dataclass(frozen=True)
class ResearchSourceScraplingFreshnessRecoveryRow:
    recovery_bucket: str
    first_stale_at: datetime
    recovered_at: datetime | None
    recovered: bool
    stale_age_seconds: Decimal
    recovery_latency_seconds: Decimal
    attempted_refresh_count: Decimal
    successful_refresh_count: Decimal
    fallback_retry_count: Decimal
    recovery_success_ratio: Decimal
    fallback_retry_pressure_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFreshnessRecoveryRow:
            raise TypeError(
                "ResearchSourceScraplingFreshnessRecoveryRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingFreshnessRecoveryRow:
            raise ValueError(
                "row must be exactly ResearchSourceScraplingFreshnessRecoveryRow",
            )
        object.__setattr__(
            self,
            "recovery_bucket",
            _require_public_bucket("recovery_bucket", self.recovery_bucket),
        )
        object.__setattr__(
            self,
            "first_stale_at",
            _as_utc("first_stale_at", self.first_stale_at),
        )
        object.__setattr__(
            self,
            "recovered_at",
            _as_optional_utc("recovered_at", self.recovered_at),
        )
        _require_bool("recovered", self.recovered)
        for field_name in (
            "stale_age_seconds",
            "recovery_latency_seconds",
            "attempted_refresh_count",
            "successful_refresh_count",
            "fallback_retry_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recovery_success_ratio",
            "fallback_retry_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchSourceScraplingFreshnessRecoveryReport:
    generated_at: datetime
    config_version: str
    status: str
    recovery_bucket_count: Decimal
    recovered_count: Decimal
    unrecovered_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    attempted_refresh_count: Decimal
    successful_refresh_count: Decimal
    fallback_retry_count: Decimal
    recovered_ratio: Decimal
    recovery_success_ratio: Decimal
    fallback_retry_pressure_ratio: Decimal
    max_stale_age_seconds: Decimal
    max_recovery_latency_seconds: Decimal
    average_recovery_latency_seconds: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchSourceScraplingFreshnessRecoveryReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchSourceScraplingFreshnessRecoveryRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchSourceScraplingFreshnessRecoveryReport:
            raise TypeError(
                "ResearchSourceScraplingFreshnessRecoveryReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchSourceScraplingFreshnessRecoveryReport:
            raise ValueError(
                "report must be exactly "
                "ResearchSourceScraplingFreshnessRecoveryReport",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_bucket("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "recovery_bucket_count",
            "recovered_count",
            "unrecovered_count",
            "pass_count",
            "watch_count",
            "block_count",
            "attempted_refresh_count",
            "successful_refresh_count",
            "fallback_retry_count",
            "max_stale_age_seconds",
            "max_recovery_latency_seconds",
            "average_recovery_latency_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "recovered_ratio",
            "recovery_success_ratio",
            "fallback_retry_pressure_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _report_digest(self)
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
        elif self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report payload")
        _require_digest("derived_validation_digest", self.derived_validation_digest)

    @property
    def payload(self) -> dict[str, Any]:
        return research_source_scrapling_freshness_recovery_report_payload(self)


def build_research_source_scrapling_freshness_recovery_report(
    observations: Iterable[ResearchSourceScraplingFreshnessRecoveryObservation],
    *,
    config: ResearchSourceScraplingFreshnessRecoveryConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingFreshnessRecoveryReport:
    if type(config) is not ResearchSourceScraplingFreshnessRecoveryConfig:
        raise ValueError(
            "config must be exactly "
            "ResearchSourceScraplingFreshnessRecoveryConfig",
        )
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    for item in normalized:
        if item.first_stale_at > generated_at_utc:
            raise ValueError("first_stale_at must not be after generated_at")
        if item.recovered_at is not None and item.recovered_at > generated_at_utc:
            raise ValueError("recovered_at must not be after generated_at")

    rows = tuple(_row_from_observation(item, config, generated_at_utc) for item in normalized)
    bucket_count = _count_decimal(len(rows))
    recovered_count = _count_decimal(sum(1 for row in rows if row.recovered))
    unrecovered_count = _count_decimal(sum(1 for row in rows if not row.recovered))
    attempted_count = sum((row.attempted_refresh_count for row in rows), ZERO)
    successful_count = sum((row.successful_refresh_count for row in rows), ZERO)
    retry_count = sum((row.fallback_retry_count for row in rows), ZERO)
    status = _aggregate_status(tuple(row.status for row in rows))
    reason_codes = _report_reason_codes(
        rows,
        recovered_ratio=_safe_ratio(recovered_count, bucket_count),
        status=status,
        config=config,
    )

    return ResearchSourceScraplingFreshnessRecoveryReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        status=status,
        recovery_bucket_count=bucket_count,
        recovered_count=recovered_count,
        unrecovered_count=unrecovered_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        attempted_refresh_count=attempted_count,
        successful_refresh_count=successful_count,
        fallback_retry_count=retry_count,
        recovered_ratio=_safe_ratio(recovered_count, bucket_count),
        recovery_success_ratio=_safe_ratio(successful_count, attempted_count),
        fallback_retry_pressure_ratio=_safe_ratio(retry_count, attempted_count),
        max_stale_age_seconds=max((row.stale_age_seconds for row in rows), default=ZERO),
        max_recovery_latency_seconds=max(
            (row.recovery_latency_seconds for row in rows),
            default=ZERO,
        ),
        average_recovery_latency_seconds=_safe_ratio(
            sum((row.recovery_latency_seconds for row in rows), ZERO),
            bucket_count,
        ),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(reason_codes),
        rows=rows,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def research_source_scrapling_freshness_recovery_report_payload(
    report: ResearchSourceScraplingFreshnessRecoveryReport,
) -> dict[str, Any]:
    if type(report) is not ResearchSourceScraplingFreshnessRecoveryReport:
        raise ValueError(
            "report must be exactly "
            "ResearchSourceScraplingFreshnessRecoveryReport",
        )
    _validate_report_consistency(report)
    expected_digest = _report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report payload")
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    validate_research_source_scrapling_freshness_recovery_public_payload(payload)
    return payload


def validate_research_source_scrapling_freshness_recovery_report_digest(
    report: ResearchSourceScraplingFreshnessRecoveryReport,
) -> None:
    research_source_scrapling_freshness_recovery_report_payload(report)


def validate_research_source_scrapling_freshness_recovery_public_payload(
    payload: dict[str, Any],
) -> None:
    if type(payload) is not dict:
        raise ValueError("public payload must be a JSON object")
    _reject_unsafe_public_payload("public payload", payload)
    _reject_public_numerics(payload)
    _require_hard_flags("public payload", _DictFlags(payload))
    _reject_flag_downgrades(payload)
    _validate_public_statuses(payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    if digest != _digest_payload(unsigned_payload):
        raise ValueError("derived_validation_digest must match public payload")


def _row_from_observation(
    item: ResearchSourceScraplingFreshnessRecoveryObservation,
    config: ResearchSourceScraplingFreshnessRecoveryConfig,
    generated_at: datetime,
) -> ResearchSourceScraplingFreshnessRecoveryRow:
    recovered = item.recovered_at is not None
    stale_age_seconds = _age_seconds(generated_at, item.first_stale_at)
    recovery_latency_seconds = (
        _age_seconds(item.recovered_at, item.first_stale_at)
        if item.recovered_at is not None
        else stale_age_seconds
    )
    success_ratio = _safe_ratio(
        item.successful_refresh_count,
        item.attempted_refresh_count,
    )
    retry_ratio = _safe_ratio(
        item.fallback_retry_count,
        item.attempted_refresh_count,
    )
    reason_codes = _row_reason_codes(
        recovered=recovered,
        recovery_latency_seconds=recovery_latency_seconds,
        success_ratio=success_ratio,
        retry_ratio=retry_ratio,
        config=config,
    )
    return ResearchSourceScraplingFreshnessRecoveryRow(
        recovery_bucket=item.recovery_bucket,
        first_stale_at=item.first_stale_at,
        recovered_at=item.recovered_at,
        recovered=recovered,
        stale_age_seconds=stale_age_seconds,
        recovery_latency_seconds=recovery_latency_seconds,
        attempted_refresh_count=item.attempted_refresh_count,
        successful_refresh_count=item.successful_refresh_count,
        fallback_retry_count=item.fallback_retry_count,
        recovery_success_ratio=success_ratio,
        fallback_retry_pressure_ratio=retry_ratio,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        paper_only=True,
        report_only=True,
        readonly=True,
    )


def _row_reason_codes(
    *,
    recovered: bool,
    recovery_latency_seconds: Decimal,
    success_ratio: Decimal,
    retry_ratio: Decimal,
    config: ResearchSourceScraplingFreshnessRecoveryConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if not recovered:
        reason_codes.append("recovery_missing_block")
    elif recovery_latency_seconds > config.block_recovery_latency_seconds:
        reason_codes.append("recovery_latency_block")
    elif recovery_latency_seconds > config.watch_recovery_latency_seconds:
        reason_codes.append("recovery_latency_watch")

    if success_ratio < config.min_recovery_success_block_ratio:
        reason_codes.append("recovery_success_ratio_block")
    elif success_ratio < config.min_recovery_success_pass_ratio:
        reason_codes.append("recovery_success_ratio_watch")

    if retry_ratio > config.max_fallback_retry_block_ratio:
        reason_codes.append("fallback_retry_pressure_block")
    elif retry_ratio > config.max_fallback_retry_pass_ratio:
        reason_codes.append("fallback_retry_pressure_watch")

    if not reason_codes:
        reason_codes.append(PASS_REASON)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _report_reason_codes(
    rows: tuple[ResearchSourceScraplingFreshnessRecoveryRow, ...],
    *,
    recovered_ratio: Decimal,
    status: str,
    config: ResearchSourceScraplingFreshnessRecoveryConfig,
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON, REPORT_BLOCK_REASON)

    reason_codes = [
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_REASON
    ]
    if recovered_ratio < config.block_recovered_ratio:
        reason_codes.append("recovered_ratio_block")
    elif recovered_ratio < config.watch_recovered_ratio:
        reason_codes.append("recovered_ratio_watch")

    if status == "pass":
        reason_codes.append(PASS_REASON)
    elif status == "watch":
        reason_codes.append(REPORT_WATCH_REASON)
    else:
        reason_codes.append(REPORT_BLOCK_REASON)
    return _normalize_reason_codes("reason_codes", tuple(dict.fromkeys(reason_codes)))


def _normalize_observations(
    observations: Iterable[ResearchSourceScraplingFreshnessRecoveryObservation],
) -> tuple[ResearchSourceScraplingFreshnessRecoveryObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        normalized = tuple(observations)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceScraplingFreshnessRecoveryObservation:
            raise ValueError(
                "observations must contain "
                "ResearchSourceScraplingFreshnessRecoveryObservation",
            )
        _require_hard_flags("observation", item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.recovery_bucket,
                item.first_stale_at.isoformat(),
                "" if item.recovered_at is None else item.recovered_at.isoformat(),
                item.attempted_refresh_count,
                item.successful_refresh_count,
                item.fallback_retry_count,
            ),
        ),
    )


def _normalize_rows(
    rows: tuple[ResearchSourceScraplingFreshnessRecoveryRow, ...],
) -> tuple[ResearchSourceScraplingFreshnessRecoveryRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchSourceScraplingFreshnessRecoveryRow:
            raise ValueError(
                "rows must contain ResearchSourceScraplingFreshnessRecoveryRow",
            )
        _require_hard_flags("row", row)
    return tuple(sorted(normalized, key=lambda row: row.recovery_bucket))


def _validate_row_consistency(
    row: ResearchSourceScraplingFreshnessRecoveryRow,
) -> None:
    if row.recovered != (row.recovered_at is not None):
        raise ValueError("recovered must match recovered_at")
    if row.recovered_at is not None and row.recovered_at < row.first_stale_at:
        raise ValueError("recovered_at must not be before first_stale_at")
    if row.successful_refresh_count > row.attempted_refresh_count:
        raise ValueError(
            "successful_refresh_count must not exceed attempted_refresh_count",
        )
    if row.fallback_retry_count > row.attempted_refresh_count:
        raise ValueError(
            "fallback_retry_count must not exceed attempted_refresh_count",
        )
    if row.recovery_success_ratio != _safe_ratio(
        row.successful_refresh_count,
        row.attempted_refresh_count,
    ):
        raise ValueError("recovery_success_ratio must match counts")
    if row.fallback_retry_pressure_ratio != _safe_ratio(
        row.fallback_retry_count,
        row.attempted_refresh_count,
    ):
        raise ValueError("fallback_retry_pressure_ratio must match counts")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchSourceScraplingFreshnessRecoveryReport,
) -> None:
    rows = report.rows
    if report.recovery_bucket_count != _count_decimal(len(rows)):
        raise ValueError("recovery_bucket_count must match rows")
    if report.recovered_count != _count_decimal(sum(1 for row in rows if row.recovered)):
        raise ValueError("recovered_count must match rows")
    if report.unrecovered_count != _count_decimal(sum(1 for row in rows if not row.recovered)):
        raise ValueError("unrecovered_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    attempted_count = sum((row.attempted_refresh_count for row in rows), ZERO)
    successful_count = sum((row.successful_refresh_count for row in rows), ZERO)
    retry_count = sum((row.fallback_retry_count for row in rows), ZERO)
    if report.attempted_refresh_count != attempted_count:
        raise ValueError("attempted_refresh_count must match rows")
    if report.successful_refresh_count != successful_count:
        raise ValueError("successful_refresh_count must match rows")
    if report.fallback_retry_count != retry_count:
        raise ValueError("fallback_retry_count must match rows")
    if report.recovered_ratio != _safe_ratio(report.recovered_count, report.recovery_bucket_count):
        raise ValueError("recovered_ratio must match rows")
    if report.recovery_success_ratio != _safe_ratio(successful_count, attempted_count):
        raise ValueError("recovery_success_ratio must match rows")
    if report.fallback_retry_pressure_ratio != _safe_ratio(retry_count, attempted_count):
        raise ValueError("fallback_retry_pressure_ratio must match rows")
    if report.max_stale_age_seconds != max(
        (row.stale_age_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_stale_age_seconds must match rows")
    if report.max_recovery_latency_seconds != max(
        (row.recovery_latency_seconds for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_recovery_latency_seconds must match rows")
    if report.average_recovery_latency_seconds != _safe_ratio(
        sum((row.recovery_latency_seconds for row in rows), ZERO),
        report.recovery_bucket_count,
    ):
        raise ValueError("average_recovery_latency_seconds must match rows")
    if report.status != _aggregate_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.reason_codes):
        raise ValueError("reason_code_counts must match reason_codes")


def _reason_code_counts(
    reason_codes: tuple[str, ...],
) -> tuple[ResearchSourceScraplingFreshnessRecoveryReasonCodeCount, ...]:
    counts = Counter(reason_codes)
    return tuple(
        ResearchSourceScraplingFreshnessRecoveryReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
            paper_only=True,
            report_only=True,
            readonly=True,
        )
        for reason_code in REASON_CODE_SEQUENCE
        if reason_code in counts
    )


def _normalize_reason_code_counts(
    counts: tuple[ResearchSourceScraplingFreshnessRecoveryReasonCodeCount, ...],
) -> tuple[ResearchSourceScraplingFreshnessRecoveryReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchSourceScraplingFreshnessRecoveryReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchSourceScraplingFreshnessRecoveryReasonCodeCount",
            )
        _require_hard_flags("reason code count", item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: REASON_CODE_SEQUENCE.index(item.reason_code),
        ),
    )


def _normalize_reason_codes(field_name: str, reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    for reason_code in normalized:
        _require_reason_code("reason_code", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(reason_code for reason_code in REASON_CODE_SEQUENCE if reason_code in normalized)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _aggregate_status(statuses: tuple[str, ...]) -> str:
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _status_count(
    rows: tuple[ResearchSourceScraplingFreshnessRecoveryRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _age_seconds(end: datetime, start: datetime) -> Decimal:
    delta = end - start
    microseconds = (
        Decimal(delta.days) * SECONDS_PER_DAY * MICROSECONDS_PER_SECOND
        + Decimal(delta.seconds) * MICROSECONDS_PER_SECOND
        + Decimal(delta.microseconds)
    )
    return _quantize(microseconds / MICROSECONDS_PER_SECOND)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count_decimal(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    if type(value) is not Decimal or not value.is_finite():
        raise ValueError("value must be a finite Decimal")
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANT)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_ratio(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _as_optional_utc(field_name: str, value: object) -> datetime | None:
    if value is None:
        return None
    return _as_utc(field_name, value)


def _require_public_bucket(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_BUCKET_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public text")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in REASON_CODE_SEQUENCE:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_STATUSES:
        raise ValueError(f"{field_name} must be a supported status")
    return value


def _require_bool(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


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


def _report_digest(report: ResearchSourceScraplingFreshnessRecoveryReport) -> str:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    return _digest_payload(payload)


def _digest_payload(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
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
            raise ValueError("JSON datetime value must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) in (float, int):
        raise ValueError("JSON value must use Decimal-derived strings")
    if isinstance(value, (str, bool)):
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


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        if _has_unsafe_fragment(value):
            raise ValueError(f"unsafe public value in {label}")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_public_numerics(value: object) -> None:
    if type(value) in (float, int):
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_flag_downgrades(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_flag_downgrades(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_flag_downgrades(item)


def _validate_public_statuses(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key.endswith("status"):
                _require_status(key, item)
            _validate_public_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _validate_public_statuses(item)


def _has_unsafe_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)


__all__ = (
    "DEFAULT_RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_CONFIG_VERSION",
    "RESEARCH_SOURCE_SCRAPLING_FRESHNESS_RECOVERY_REPORT_STATUSES",
    "ResearchSourceScraplingFreshnessRecoveryConfig",
    "ResearchSourceScraplingFreshnessRecoveryObservation",
    "ResearchSourceScraplingFreshnessRecoveryRow",
    "ResearchSourceScraplingFreshnessRecoveryReport",
    "build_research_source_scrapling_freshness_recovery_report",
    "research_source_scrapling_freshness_recovery_report_payload",
    "validate_research_source_scrapling_freshness_recovery_public_payload",
    "validate_research_source_scrapling_freshness_recovery_report_digest",
)
