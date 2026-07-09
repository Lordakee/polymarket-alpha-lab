"""Public-safe domain team calibration score trend report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_TEAM_DOMAIN_CALIBRATION_SCORE_TREND_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamDomainCalibrationScoreTrendConfig",
    "ResearchTeamDomainCalibrationScoreTrendInput",
    "ResearchTeamDomainCalibrationScoreTrendReasonCodeCount",
    "ResearchTeamDomainCalibrationScoreTrendReport",
    "ResearchTeamDomainCalibrationScoreTrendRow",
    "build_research_team_domain_calibration_score_trend_report",
    "research_team_domain_calibration_score_trend_report_payload",
)


DEFAULT_RESEARCH_TEAM_DOMAIN_CALIBRATION_SCORE_TREND_REPORT_CONFIG_VERSION = (
    "research-team-domain-calibration-score-trend-report-v0"
)

STATUSES = ("pass", "watch", "block")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
MICROSECONDS_PER_SECOND = Decimal("1000000")

STATUS_WEIGHT = {
    "block": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}

CLEAR_REASON = "domain_calibration_score_trend_clear"
EMPTY_REASON = "domain_calibration_score_trend_no_domains"
REPORT_PASS_REASON = "domain_calibration_score_trend_report_pass"
REPORT_WATCH_REASON = "domain_calibration_score_trend_report_watch"
REPORT_BLOCK_REASON = "domain_calibration_score_trend_report_block"
LOW_OUTCOME_REASON = "resolved_outcome_learning_below_minimum"
SCORE_WATCH_REASON = "domain_calibration_score_watch"
SCORE_BLOCK_REASON = "domain_calibration_score_block"
ERROR_WATCH_REASON = "forecast_error_worsening_watch"
ERROR_BLOCK_REASON = "forecast_error_worsening_block"
PLAYBOOK_WATCH_REASON = "playbook_adoption_watch"
PLAYBOOK_BLOCK_REASON = "playbook_adoption_block"
STALE_MEMORY_WATCH_REASON = "stale_memory_correction_watch"
STALE_MEMORY_BLOCK_REASON = "stale_memory_correction_block"
CAPACITY_WATCH_REASON = "review_capacity_pressure_watch"
CAPACITY_BLOCK_REASON = "review_capacity_pressure_block"

BLOCK_REASON_CODES = (
    LOW_OUTCOME_REASON,
    SCORE_BLOCK_REASON,
    ERROR_BLOCK_REASON,
    PLAYBOOK_BLOCK_REASON,
    STALE_MEMORY_BLOCK_REASON,
    CAPACITY_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    SCORE_WATCH_REASON,
    ERROR_WATCH_REASON,
    PLAYBOOK_WATCH_REASON,
    STALE_MEMORY_WATCH_REASON,
    CAPACITY_WATCH_REASON,
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (CLEAR_REASON,)
REPORT_REASON_BY_STATUS = {
    "pass": REPORT_PASS_REASON,
    "watch": REPORT_WATCH_REASON,
    "block": REPORT_BLOCK_REASON,
}
REPORT_REASON_CODES = (
    EMPTY_REASON,
    REPORT_PASS_REASON,
    REPORT_WATCH_REASON,
    REPORT_BLOCK_REASON,
) + BLOCK_REASON_CODES + WATCH_REASON_CODES
REASON_CODE_COUNT_PRIORITY = (
    EMPTY_REASON,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
    CLEAR_REASON,
)

SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_IDENTIFIER_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "live",
        "execute",
        "execution",
        "route",
        "buy",
        "sell",
        "size",
        "sizing",
        "recommend",
        "recommendation",
        "position",
    ),
)
UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "http://",
        "https://",
        "://",
        "url",
        "source",
        "source_text",
        "dsn",
        "table",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "live",
        "execute",
        "execution",
        "route",
        "buy",
        "sell",
        "size",
        "sizing",
        "recommend",
        "recommendation",
        "position",
        "password",
        "credential",
        "private_key",
        "api_key",
    ),
)

REPORT_PAYLOAD_KEYS = frozenset(
    (
        "average_calibration_score_trend",
        "average_playbook_adoption_rate",
        "average_stale_memory_correction_rate",
        "block_count",
        "capacity_pressure_team_count",
        "config_version",
        "domain_team_count",
        "forecast_error_worsening_team_count",
        "generated_at",
        "max_forecast_error_delta",
        "max_review_capacity_pressure_score",
        "min_calibration_score_trend",
        "paper_only",
        "pass_count",
        "payload_digest",
        "playbook_gap_team_count",
        "readonly",
        "reason_code_counts",
        "reason_codes",
        "report_only",
        "rows",
        "stale_memory_gap_team_count",
        "status",
        "total_resolved_outcome_count",
        "watch_count",
    ),
)
REPORT_NUMERIC_PAYLOAD_KEYS = frozenset(
    (
        "average_calibration_score_trend",
        "average_playbook_adoption_rate",
        "average_stale_memory_correction_rate",
        "block_count",
        "capacity_pressure_team_count",
        "domain_team_count",
        "forecast_error_worsening_team_count",
        "max_forecast_error_delta",
        "max_review_capacity_pressure_score",
        "min_calibration_score_trend",
        "pass_count",
        "playbook_gap_team_count",
        "stale_memory_gap_team_count",
        "total_resolved_outcome_count",
        "watch_count",
    ),
)
ROW_PAYLOAD_KEYS = frozenset(
    (
        "calibration_score_trend",
        "current_forecast_error_rate",
        "domain_digest",
        "forecast_error_delta",
        "generated_at",
        "observation_age_seconds",
        "observed_at",
        "outcome_learning_score",
        "paper_only",
        "playbook_adoption_rate",
        "prior_forecast_error_rate",
        "readonly",
        "reason_codes",
        "report_only",
        "resolved_outcome_count",
        "review_capacity_pressure_score",
        "stale_memory_correction_rate",
        "status",
        "team_digest",
    ),
)
ROW_NUMERIC_PAYLOAD_KEYS = frozenset(
    (
        "calibration_score_trend",
        "current_forecast_error_rate",
        "forecast_error_delta",
        "observation_age_seconds",
        "outcome_learning_score",
        "playbook_adoption_rate",
        "prior_forecast_error_rate",
        "resolved_outcome_count",
        "review_capacity_pressure_score",
        "stale_memory_correction_rate",
    ),
)
REASON_CODE_COUNT_PAYLOAD_KEYS = frozenset(
    (
        "count",
        "paper_only",
        "readonly",
        "reason_code",
        "report_only",
        "team_ratio",
    ),
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
class ResearchTeamDomainCalibrationScoreTrendConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_DOMAIN_CALIBRATION_SCORE_TREND_REPORT_CONFIG_VERSION
    )
    min_resolved_outcome_count: Decimal = Decimal("5")
    watch_calibration_score_floor: Decimal = Decimal("0.700000")
    block_calibration_score_floor: Decimal = Decimal("0.550000")
    watch_forecast_error_worsening: Decimal = Decimal("0.030000")
    block_forecast_error_worsening: Decimal = Decimal("0.080000")
    min_pass_playbook_adoption_rate: Decimal = Decimal("0.850000")
    min_watch_playbook_adoption_rate: Decimal = Decimal("0.650000")
    min_pass_stale_memory_correction_rate: Decimal = Decimal("0.900000")
    min_watch_stale_memory_correction_rate: Decimal = Decimal("0.700000")
    max_pass_review_capacity_pressure_score: Decimal = Decimal("0.700000")
    max_watch_review_capacity_pressure_score: Decimal = Decimal("0.900000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainCalibrationScoreTrendConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_CALIBRATION_SCORE_TREND_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "min_resolved_outcome_count",
            _require_count_decimal(
                "min_resolved_outcome_count",
                self.min_resolved_outcome_count,
            ),
        )
        for field_name in (
            "watch_calibration_score_floor",
            "block_calibration_score_floor",
            "watch_forecast_error_worsening",
            "block_forecast_error_worsening",
            "min_pass_playbook_adoption_rate",
            "min_watch_playbook_adoption_rate",
            "min_pass_stale_memory_correction_rate",
            "min_watch_stale_memory_correction_rate",
            "max_pass_review_capacity_pressure_score",
            "max_watch_review_capacity_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamDomainCalibrationScoreTrendInput(_FinalPublicDataclass):
    team_key: str
    domain_key: str
    observed_at: datetime
    resolved_outcome_count: Decimal
    outcome_learning_score: Decimal
    prior_forecast_error_rate: Decimal
    current_forecast_error_rate: Decimal
    playbook_adoption_rate: Decimal
    stale_memory_correction_rate: Decimal
    review_capacity_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainCalibrationScoreTrendInput, "input")
        _require_safe_identifier("team_key", self.team_key)
        _require_safe_identifier("domain_key", self.domain_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolved_outcome_count",
            _require_count_decimal("resolved_outcome_count", self.resolved_outcome_count),
        )
        for field_name in (
            "outcome_learning_score",
            "prior_forecast_error_rate",
            "current_forecast_error_rate",
            "playbook_adoption_rate",
            "stale_memory_correction_rate",
            "review_capacity_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamDomainCalibrationScoreTrendRow(_FinalPublicDataclass):
    team_key: str
    domain_key: str
    status: str
    generated_at: datetime
    observed_at: datetime
    observation_age_seconds: Decimal
    resolved_outcome_count: Decimal
    outcome_learning_score: Decimal
    prior_forecast_error_rate: Decimal
    current_forecast_error_rate: Decimal
    forecast_error_delta: Decimal
    playbook_adoption_rate: Decimal
    stale_memory_correction_rate: Decimal
    review_capacity_pressure_score: Decimal
    calibration_score_trend: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainCalibrationScoreTrendRow, "row")
        _require_safe_identifier("team_key", self.team_key)
        _require_safe_identifier("domain_key", self.domain_key)
        _require_status("status", self.status)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _require_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        object.__setattr__(
            self,
            "resolved_outcome_count",
            _require_count_decimal("resolved_outcome_count", self.resolved_outcome_count),
        )
        for field_name in (
            "outcome_learning_score",
            "prior_forecast_error_rate",
            "current_forecast_error_rate",
            "playbook_adoption_rate",
            "stale_memory_correction_rate",
            "review_capacity_pressure_score",
            "calibration_score_trend",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "forecast_error_delta",
            _require_delta_decimal("forecast_error_delta", self.forecast_error_delta),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamDomainCalibrationScoreTrendReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamDomainCalibrationScoreTrendReasonCodeCount,
            "reason_code_count",
        )
        _require_public_text("reason_code", self.reason_code)
        if self.reason_code not in REASON_CODE_COUNT_PRIORITY:
            raise ValueError("reason_code must be supported")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "team_ratio",
            _require_ratio_decimal("team_ratio", self.team_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchTeamDomainCalibrationScoreTrendReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    domain_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    forecast_error_worsening_team_count: Decimal
    playbook_gap_team_count: Decimal
    stale_memory_gap_team_count: Decimal
    capacity_pressure_team_count: Decimal
    total_resolved_outcome_count: Decimal
    average_calibration_score_trend: Decimal
    min_calibration_score_trend: Decimal
    max_forecast_error_delta: Decimal
    average_playbook_adoption_rate: Decimal
    average_stale_memory_correction_rate: Decimal
    max_review_capacity_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamDomainCalibrationScoreTrendReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamDomainCalibrationScoreTrendRow, ...]
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamDomainCalibrationScoreTrendReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_text("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_DOMAIN_CALIBRATION_SCORE_TREND_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "domain_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "forecast_error_worsening_team_count",
            "playbook_gap_team_count",
            "stale_memory_gap_team_count",
            "capacity_pressure_team_count",
            "total_resolved_outcome_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_score_trend",
            "min_calibration_score_trend",
            "max_forecast_error_delta",
            "average_playbook_adoption_rate",
            "average_stale_memory_correction_rate",
            "max_review_capacity_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _require_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        _require_hard_flags("report", self)
        if self.payload_digest:
            _require_sha256("payload_digest", self.payload_digest)
            if self.payload_digest != _derived_payload_digest(self):
                raise ValueError("payload_digest does not match report payload")
        else:
            object.__setattr__(self, "payload_digest", _derived_payload_digest(self))
        _validate_report_materialized_fields(self)


def build_research_team_domain_calibration_score_trend_report(
    trend_items: Iterable[ResearchTeamDomainCalibrationScoreTrendInput],
    *,
    config: ResearchTeamDomainCalibrationScoreTrendConfig,
    generated_at: datetime,
) -> ResearchTeamDomainCalibrationScoreTrendReport:
    if type(config) is not ResearchTeamDomainCalibrationScoreTrendConfig:
        raise ValueError(
            "config must be a ResearchTeamDomainCalibrationScoreTrendConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_trend_items(trend_items)
    rows = tuple(
        sorted(
            (
                _row_for_trend_item(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in items
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.status for row in rows))
    return ResearchTeamDomainCalibrationScoreTrendReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        domain_team_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        forecast_error_worsening_team_count=_reason_team_count(
            rows,
            ERROR_BLOCK_REASON,
            ERROR_WATCH_REASON,
        ),
        playbook_gap_team_count=_reason_team_count(
            rows,
            PLAYBOOK_BLOCK_REASON,
            PLAYBOOK_WATCH_REASON,
        ),
        stale_memory_gap_team_count=_reason_team_count(
            rows,
            STALE_MEMORY_BLOCK_REASON,
            STALE_MEMORY_WATCH_REASON,
        ),
        capacity_pressure_team_count=_reason_team_count(
            rows,
            CAPACITY_BLOCK_REASON,
            CAPACITY_WATCH_REASON,
        ),
        total_resolved_outcome_count=_sum_decimal(
            tuple(row.resolved_outcome_count for row in rows),
            count=True,
        ),
        average_calibration_score_trend=_mean_decimal(
            tuple(row.calibration_score_trend for row in rows),
        ),
        min_calibration_score_trend=_min_decimal(
            tuple(row.calibration_score_trend for row in rows),
        ),
        max_forecast_error_delta=_max_decimal(
            tuple(max(row.forecast_error_delta, ZERO_RATIO) for row in rows),
        ),
        average_playbook_adoption_rate=_mean_decimal(
            tuple(row.playbook_adoption_rate for row in rows),
        ),
        average_stale_memory_correction_rate=_mean_decimal(
            tuple(row.stale_memory_correction_rate for row in rows),
        ),
        max_review_capacity_pressure_score=_max_decimal(
            tuple(row.review_capacity_pressure_score for row in rows),
        ),
        status=status,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_domain_calibration_score_trend_report_payload(
    report: ResearchTeamDomainCalibrationScoreTrendReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamDomainCalibrationScoreTrendReport:
        _require_hard_flags("report", report)
        _validate_report_materialized_fields(report)
        if report.payload_digest != _derived_payload_digest(report):
            raise ValueError("payload_digest does not match report payload")
        payload = _report_payload(report)
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        _require_hard_flags("payload", _PayloadFlags(report))
        _validate_public_payload_shape(report)
        supplied_digest = report.get("payload_digest")
        if type(supplied_digest) is not str:
            raise ValueError("payload_digest is required")
        _require_sha256("payload_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(report):
            raise ValueError("payload_digest does not match report payload")
        return report
    raise ValueError("report must be a ResearchTeamDomainCalibrationScoreTrendReport")


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


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_payload_keys("payload", payload, REPORT_PAYLOAD_KEYS)
    if (
        _require_payload_text("config_version", payload["config_version"])
        != DEFAULT_RESEARCH_TEAM_DOMAIN_CALIBRATION_SCORE_TREND_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_payload_text("generated_at", payload["generated_at"])
    _require_status("status", _require_payload_text("status", payload["status"]))
    _require_sha256(
        "payload_digest",
        _require_payload_text("payload_digest", payload["payload_digest"]),
    )
    for field_name in REPORT_NUMERIC_PAYLOAD_KEYS:
        _require_payload_decimal(field_name, payload[field_name])
    _require_payload_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        REPORT_REASON_CODES,
    )
    reason_code_counts = payload["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    for reason_code_count in reason_code_counts:
        _validate_public_reason_code_count(reason_code_count)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        _validate_public_payload_row(row)


def _validate_public_reason_code_count(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("reason_code_counts must contain JSON objects")
    _require_payload_keys(
        "reason_code_count",
        value,
        REASON_CODE_COUNT_PAYLOAD_KEYS,
    )
    _require_hard_flags("reason_code_count", _PayloadFlags(value))
    reason_code = _require_payload_text("reason_code", value["reason_code"])
    if reason_code not in REASON_CODE_COUNT_PRIORITY:
        raise ValueError("reason_code must be supported")
    _require_payload_decimal("count", value["count"])
    _require_payload_decimal("team_ratio", value["team_ratio"])


def _validate_public_payload_row(value: object) -> None:
    if type(value) is not dict:
        raise ValueError("rows must contain JSON objects")
    _require_payload_keys("row", value, ROW_PAYLOAD_KEYS)
    _require_hard_flags("row", _PayloadFlags(value))
    _require_status("status", _require_payload_text("status", value["status"]))
    _require_payload_text("generated_at", value["generated_at"])
    _require_payload_text("observed_at", value["observed_at"])
    _require_prefixed_sha256("team_digest", value["team_digest"])
    _require_prefixed_sha256("domain_digest", value["domain_digest"])
    for field_name in ROW_NUMERIC_PAYLOAD_KEYS:
        _require_payload_decimal(field_name, value[field_name])
    _require_payload_reason_codes(
        "reason_codes",
        value["reason_codes"],
        ROW_REASON_CODES,
    )


def _require_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} keys must match report payload schema")


def _require_payload_text(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return _require_public_text(field_name, value)


def _require_payload_decimal(field_name: str, value: object) -> Decimal:
    decimal_text = _require_payload_text(field_name, value)
    try:
        decimal_value = Decimal(decimal_text)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _require_prefixed_sha256(field_name: str, value: object) -> None:
    digest = _require_payload_text(field_name, value)
    if not digest.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a public sha256 digest")
    _require_sha256(field_name, digest.removeprefix("sha256:"))


def _require_payload_reason_codes(
    field_name: str,
    value: object,
    allowed_reason_codes: tuple[str, ...],
) -> None:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    for reason_code in value:
        _require_public_text("reason_code", reason_code)
        if reason_code not in allowed_reason_codes:
            raise ValueError("reason_codes must be supported")


def _normalize_trend_items(
    trend_items: Iterable[ResearchTeamDomainCalibrationScoreTrendInput],
) -> tuple[ResearchTeamDomainCalibrationScoreTrendInput, ...]:
    if isinstance(trend_items, (str, bytes)):
        raise ValueError("trend_items must be an iterable")
    try:
        items = tuple(trend_items)
    except TypeError as exc:
        raise ValueError("trend_items must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in items:
        if type(item) is not ResearchTeamDomainCalibrationScoreTrendInput:
            raise ValueError(
                "trend_items must contain ResearchTeamDomainCalibrationScoreTrendInput",
            )
        _require_hard_flags("input", item)
        key = (item.team_key, item.domain_key)
        if key in seen:
            raise ValueError("team_key and domain_key values must be unique")
        seen.add(key)
    return items


def _row_for_trend_item(
    item: ResearchTeamDomainCalibrationScoreTrendInput,
    *,
    config: ResearchTeamDomainCalibrationScoreTrendConfig,
    generated_at: datetime,
) -> ResearchTeamDomainCalibrationScoreTrendRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    forecast_error_delta = _error_delta(
        item.current_forecast_error_rate,
        item.prior_forecast_error_rate,
    )
    calibration_score_trend = _calibration_score_trend(
        item,
        forecast_error_delta=forecast_error_delta,
    )
    reason_codes = _row_reason_codes(
        item,
        config=config,
        calibration_score_trend=calibration_score_trend,
        forecast_error_delta=forecast_error_delta,
    )
    return ResearchTeamDomainCalibrationScoreTrendRow(
        team_key=item.team_key,
        domain_key=item.domain_key,
        status=_row_status(reason_codes),
        generated_at=generated_at,
        observed_at=item.observed_at,
        observation_age_seconds=_datetime_delta_seconds(generated_at, item.observed_at),
        resolved_outcome_count=item.resolved_outcome_count,
        outcome_learning_score=item.outcome_learning_score,
        prior_forecast_error_rate=item.prior_forecast_error_rate,
        current_forecast_error_rate=item.current_forecast_error_rate,
        forecast_error_delta=forecast_error_delta,
        playbook_adoption_rate=item.playbook_adoption_rate,
        stale_memory_correction_rate=item.stale_memory_correction_rate,
        review_capacity_pressure_score=item.review_capacity_pressure_score,
        calibration_score_trend=calibration_score_trend,
        reason_codes=reason_codes,
    )


def _calibration_score_trend(
    item: ResearchTeamDomainCalibrationScoreTrendInput,
    *,
    forecast_error_delta: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _calibration_score_from_values(
            outcome_learning_score=item.outcome_learning_score,
            forecast_error_delta=forecast_error_delta,
            playbook_adoption_rate=item.playbook_adoption_rate,
            stale_memory_correction_rate=item.stale_memory_correction_rate,
            review_capacity_pressure_score=item.review_capacity_pressure_score,
        )


def _calibration_score_from_values(
    *,
    outcome_learning_score: Decimal,
    forecast_error_delta: Decimal,
    playbook_adoption_rate: Decimal,
    stale_memory_correction_rate: Decimal,
    review_capacity_pressure_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        forecast_component = ONE_RATIO - max(forecast_error_delta, ZERO_RATIO)
        capacity_component = ONE_RATIO - review_capacity_pressure_score
        raw_score = (
            outcome_learning_score
            + forecast_component
            + playbook_adoption_rate
            + stale_memory_correction_rate
            + capacity_component
        ) / Decimal("5")
        return max(ZERO_RATIO, min(ONE_RATIO, raw_score)).quantize(RATIO_QUANTUM)


def _row_reason_codes(
    item: ResearchTeamDomainCalibrationScoreTrendInput,
    *,
    config: ResearchTeamDomainCalibrationScoreTrendConfig,
    calibration_score_trend: Decimal,
    forecast_error_delta: Decimal,
) -> tuple[str, ...]:
    if item.resolved_outcome_count < config.min_resolved_outcome_count:
        return (LOW_OUTCOME_REASON,)

    reason_codes: list[str] = []
    if calibration_score_trend <= config.block_calibration_score_floor:
        reason_codes.append(SCORE_BLOCK_REASON)
    elif calibration_score_trend < config.watch_calibration_score_floor:
        reason_codes.append(SCORE_WATCH_REASON)

    if forecast_error_delta >= config.block_forecast_error_worsening:
        reason_codes.append(ERROR_BLOCK_REASON)
    elif forecast_error_delta >= config.watch_forecast_error_worsening:
        reason_codes.append(ERROR_WATCH_REASON)

    if item.playbook_adoption_rate < config.min_watch_playbook_adoption_rate:
        reason_codes.append(PLAYBOOK_BLOCK_REASON)
    elif item.playbook_adoption_rate < config.min_pass_playbook_adoption_rate:
        reason_codes.append(PLAYBOOK_WATCH_REASON)

    if item.stale_memory_correction_rate < config.min_watch_stale_memory_correction_rate:
        reason_codes.append(STALE_MEMORY_BLOCK_REASON)
    elif item.stale_memory_correction_rate < config.min_pass_stale_memory_correction_rate:
        reason_codes.append(STALE_MEMORY_WATCH_REASON)

    if item.review_capacity_pressure_score > config.max_watch_review_capacity_pressure_score:
        reason_codes.append(CAPACITY_BLOCK_REASON)
    elif item.review_capacity_pressure_score > config.max_pass_review_capacity_pressure_score:
        reason_codes.append(CAPACITY_WATCH_REASON)

    if not reason_codes:
        reason_codes.append(CLEAR_REASON)
    return tuple(
        reason_code for reason_code in ROW_REASON_CODES if reason_code in reason_codes
    )


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchTeamDomainCalibrationScoreTrendRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [REPORT_REASON_BY_STATUS[status]]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != CLEAR_REASON
    )
    for reason_code in BLOCK_REASON_CODES + WATCH_REASON_CODES:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamDomainCalibrationScoreTrendRow, ...],
) -> tuple[ResearchTeamDomainCalibrationScoreTrendReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamDomainCalibrationScoreTrendReasonCodeCount(
                reason_code=EMPTY_REASON,
                count=_count(1),
                team_ratio=ONE_RATIO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        for reason_code in row.reason_codes:
            counter[reason_code] += 1
    denominator = _count(len(rows))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(REASON_CODE_COUNT_PRIORITY)
    }
    return tuple(
        ResearchTeamDomainCalibrationScoreTrendReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            team_ratio=_ratio(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: priority[item[0]],
        )
    )


def _status_count(
    rows: tuple[ResearchTeamDomainCalibrationScoreTrendRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_team_count(
    rows: tuple[ResearchTeamDomainCalibrationScoreTrendRow, ...],
    block_reason: str,
    watch_reason: str,
) -> Decimal:
    return _count(
        sum(
            1
            for row in rows
            if block_reason in row.reason_codes or watch_reason in row.reason_codes
        ),
    )


def _row_sort_key(
    row: ResearchTeamDomainCalibrationScoreTrendRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -max(row.forecast_error_delta, ZERO_RATIO),
        row.calibration_score_trend,
        row.domain_key,
        row.team_key,
    )


def _validate_config(config: ResearchTeamDomainCalibrationScoreTrendConfig) -> None:
    if config.block_calibration_score_floor > config.watch_calibration_score_floor:
        raise ValueError("block_calibration_score_floor must not exceed watch threshold")
    if config.block_forecast_error_worsening < config.watch_forecast_error_worsening:
        raise ValueError("block_forecast_error_worsening must be at least watch threshold")
    if config.min_watch_playbook_adoption_rate > config.min_pass_playbook_adoption_rate:
        raise ValueError("min_watch_playbook_adoption_rate must not exceed pass threshold")
    if (
        config.min_watch_stale_memory_correction_rate
        > config.min_pass_stale_memory_correction_rate
    ):
        raise ValueError(
            "min_watch_stale_memory_correction_rate must not exceed pass threshold",
        )
    if (
        config.max_watch_review_capacity_pressure_score
        < config.max_pass_review_capacity_pressure_score
    ):
        raise ValueError(
            "max_watch_review_capacity_pressure_score must be at least pass threshold",
        )


def _validate_row(row: ResearchTeamDomainCalibrationScoreTrendRow) -> None:
    if row.forecast_error_delta != _error_delta(
        row.current_forecast_error_rate,
        row.prior_forecast_error_rate,
    ):
        raise ValueError("forecast_error_delta must match current and prior errors")
    expected_score = _calibration_score_from_values(
        outcome_learning_score=row.outcome_learning_score,
        forecast_error_delta=row.forecast_error_delta,
        playbook_adoption_rate=row.playbook_adoption_rate,
        stale_memory_correction_rate=row.stale_memory_correction_rate,
        review_capacity_pressure_score=row.review_capacity_pressure_score,
    )
    if row.calibration_score_trend != expected_score:
        raise ValueError("calibration_score_trend must match score inputs")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamDomainCalibrationScoreTrendReport,
) -> None:
    rows = report.rows
    if report.domain_team_count != _count(len(rows)):
        raise ValueError("domain_team_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.forecast_error_worsening_team_count != _reason_team_count(
        rows,
        ERROR_BLOCK_REASON,
        ERROR_WATCH_REASON,
    ):
        raise ValueError("forecast_error_worsening_team_count must match rows")
    if report.playbook_gap_team_count != _reason_team_count(
        rows,
        PLAYBOOK_BLOCK_REASON,
        PLAYBOOK_WATCH_REASON,
    ):
        raise ValueError("playbook_gap_team_count must match rows")
    if report.stale_memory_gap_team_count != _reason_team_count(
        rows,
        STALE_MEMORY_BLOCK_REASON,
        STALE_MEMORY_WATCH_REASON,
    ):
        raise ValueError("stale_memory_gap_team_count must match rows")
    if report.capacity_pressure_team_count != _reason_team_count(
        rows,
        CAPACITY_BLOCK_REASON,
        CAPACITY_WATCH_REASON,
    ):
        raise ValueError("capacity_pressure_team_count must match rows")
    if report.total_resolved_outcome_count != _sum_decimal(
        tuple(row.resolved_outcome_count for row in rows),
        count=True,
    ):
        raise ValueError("total_resolved_outcome_count must match rows")
    if report.average_calibration_score_trend != _mean_decimal(
        tuple(row.calibration_score_trend for row in rows),
    ):
        raise ValueError("average_calibration_score_trend must match rows")
    if report.min_calibration_score_trend != _min_decimal(
        tuple(row.calibration_score_trend for row in rows),
    ):
        raise ValueError("min_calibration_score_trend must match rows")
    if report.max_forecast_error_delta != _max_decimal(
        tuple(max(row.forecast_error_delta, ZERO_RATIO) for row in rows),
    ):
        raise ValueError("max_forecast_error_delta must match rows")
    if report.average_playbook_adoption_rate != _mean_decimal(
        tuple(row.playbook_adoption_rate for row in rows),
    ):
        raise ValueError("average_playbook_adoption_rate must match rows")
    if report.average_stale_memory_correction_rate != _mean_decimal(
        tuple(row.stale_memory_correction_rate for row in rows),
    ):
        raise ValueError("average_stale_memory_correction_rate must match rows")
    if report.max_review_capacity_pressure_score != _max_decimal(
        tuple(row.review_capacity_pressure_score for row in rows),
    ):
        raise ValueError("max_review_capacity_pressure_score must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(rows, key=_row_sort_key)) != rows:
        raise ValueError("rows must be sorted")


def _require_rows(
    rows: tuple[ResearchTeamDomainCalibrationScoreTrendRow, ...],
) -> tuple[ResearchTeamDomainCalibrationScoreTrendRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchTeamDomainCalibrationScoreTrendRow:
            raise ValueError("rows must contain ResearchTeamDomainCalibrationScoreTrendRow")
        _require_hard_flags("row", row)
    return rows


def _require_reason_code_counts(
    reason_code_counts: tuple[
        ResearchTeamDomainCalibrationScoreTrendReasonCodeCount,
        ...,
    ],
) -> tuple[ResearchTeamDomainCalibrationScoreTrendReasonCodeCount, ...]:
    if type(reason_code_counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in reason_code_counts:
        if type(item) is not ResearchTeamDomainCalibrationScoreTrendReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamDomainCalibrationScoreTrendReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    return reason_code_counts


def _require_row_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must be nonempty")
    for reason_code in value:
        _require_public_text("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_codes must be supported")
    if tuple(reason_code for reason_code in ROW_REASON_CODES if reason_code in value) != value:
        raise ValueError("reason_codes must be sorted")
    if CLEAR_REASON in value and len(value) != 1:
        raise ValueError("clear reason must be exclusive")
    return value


def _require_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not value:
        raise ValueError("reason_codes must be nonempty")
    for reason_code in value:
        _require_public_text("reason_code", reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_codes must be supported")
    return value


def _require_status(field_name: str, value: str) -> None:
    _require_public_text(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_safe_identifier(field_name: str, value: str) -> None:
    _require_public_text(field_name, value)
    if not value:
        raise ValueError(f"{field_name} must be nonempty")
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} must be a safe public identifier")
    lower_value = value.lower()
    if any(fragment in lower_value for fragment in UNSAFE_IDENTIFIER_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


def _require_public_text(field_name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value.strip() != value:
        raise ValueError(f"{field_name} must be stripped")
    if "\n" in value or "\r" in value or "\t" in value:
        raise ValueError(f"{field_name} must be single-line")
    return value


def _require_count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != _require_decimal(field_name, value):
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _require_ratio_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must not exceed one")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_delta_decimal(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value).quantize(RATIO_QUANTUM)


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return +value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    with localcontext(DECIMAL_CONTEXT):
        return (
            Decimal(delta.days * 86400 + delta.seconds)
            + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
        ).quantize(RATIO_QUANTUM)


def _error_delta(current: Decimal, prior: Decimal) -> Decimal:
    return (current - prior).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _sum_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    total = sum(values, ZERO_COUNT)
    if count:
        return total.quantize(COUNT_QUANTUM)
    return total.quantize(RATIO_QUANTUM)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return min(values).quantize(RATIO_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    return max(values).quantize(RATIO_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _report_payload(
    report: ResearchTeamDomainCalibrationScoreTrendReport,
) -> dict[str, Any]:
    payload = _json_ready(asdict(report))
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    redacted_rows = []
    for row in report.rows:
        row_payload = _json_ready(asdict(row))
        if type(row_payload) is not dict:
            raise ValueError("row payload must be a JSON object")
        team_key = str(row_payload.pop("team_key"))
        domain_key = str(row_payload.pop("domain_key"))
        row_payload["team_digest"] = _public_digest("team", team_key)
        row_payload["domain_digest"] = _public_digest("domain", domain_key)
        redacted_rows.append(_sort_json_object(row_payload))
    payload["rows"] = redacted_rows
    return _sort_json_object(payload)


def _payload_without_digest(report: ResearchTeamDomainCalibrationScoreTrendReport) -> dict[str, Any]:
    payload = _report_payload(report)
    payload["payload_digest"] = ""
    return payload


def _derived_payload_digest(report: ResearchTeamDomainCalibrationScoreTrendReport) -> str:
    return _payload_validation_digest(_payload_without_digest(report))


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    comparable = _json_ready(payload)
    if type(comparable) is not dict:
        raise ValueError("payload must be a JSON object")
    comparable["payload_digest"] = ""
    payload_text = json.dumps(
        _sort_json_object(comparable),
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(payload_text.encode("utf-8")).hexdigest()


def _public_digest(label: str, value: str) -> str:
    return "sha256:" + sha256(f"{label}:{value}".encode("utf-8")).hexdigest()


def _json_ready(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return _sort_json_object(
            {str(key): _json_ready(item) for key, item in value.items()},
        )
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _sort_json_object(value: dict[str, Any]) -> dict[str, Any]:
    return {key: value[key] for key in sorted(value)}


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = str(key).lower()
            if any(fragment in lower_key for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public surface")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        if any(fragment in lower_value for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{label} contains unsafe public surface")
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            field_name = field.name
            if field_name in {"team_key", "domain_key"}:
                continue
            if any(fragment in field_name.lower() for fragment in UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"{label} contains unsafe public surface")
            _reject_unsafe_public_payload(label, getattr(value, field_name))


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _require_sha256(field_name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
