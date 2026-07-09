"""Public-safe specialist team calibration drift report reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_DRIFT_REPORT_CONFIG_VERSION = (
    "research-team-specialist-calibration-drift-report-v0"
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
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}

PASS_ROW_REASON_CODE = "specialist_calibration_drift_clear"
EMPTY_REPORT_REASON_CODE = "specialist_calibration_drift_no_teams"
REPORT_PASS_REASON_CODE = "specialist_calibration_drift_report_pass"
REPORT_WATCH_REASON_CODE = "specialist_calibration_drift_report_watch"
REPORT_BLOCK_REASON_CODE = "specialist_calibration_drift_report_block"

RECENT_OUTCOMES_BLOCK_REASON = "specialist_recent_outcomes_below_minimum"
CALIBRATION_ERROR_BLOCK_REASON = "specialist_calibration_error_block"
STALE_MEMORY_BLOCK_REASON = "specialist_stale_memory_block"
BIAS_FLAG_BLOCK_REASON = "specialist_bias_flag_block"
CORRECTION_FOLLOW_THROUGH_BLOCK_REASON = (
    "specialist_correction_follow_through_block"
)
SOURCE_COVERAGE_BLOCK_REASON = "specialist_source_coverage_block"
WORKLOAD_PRESSURE_BLOCK_REASON = "specialist_workload_pressure_block"

CALIBRATION_ERROR_WATCH_REASON = "specialist_calibration_error_watch"
STALE_MEMORY_WATCH_REASON = "specialist_stale_memory_watch"
BIAS_FLAG_WATCH_REASON = "specialist_bias_flag_watch"
CORRECTION_FOLLOW_THROUGH_WATCH_REASON = (
    "specialist_correction_follow_through_watch"
)
SOURCE_COVERAGE_WATCH_REASON = "specialist_source_coverage_watch"
WORKLOAD_PRESSURE_WATCH_REASON = "specialist_workload_pressure_watch"

BLOCK_REASON_CODES = (
    RECENT_OUTCOMES_BLOCK_REASON,
    CALIBRATION_ERROR_BLOCK_REASON,
    STALE_MEMORY_BLOCK_REASON,
    BIAS_FLAG_BLOCK_REASON,
    CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
    SOURCE_COVERAGE_BLOCK_REASON,
    WORKLOAD_PRESSURE_BLOCK_REASON,
)
WATCH_REASON_CODES = (
    CALIBRATION_ERROR_WATCH_REASON,
    STALE_MEMORY_WATCH_REASON,
    BIAS_FLAG_WATCH_REASON,
    CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
    SOURCE_COVERAGE_WATCH_REASON,
    WORKLOAD_PRESSURE_WATCH_REASON,
)
ROW_REASON_CODES = BLOCK_REASON_CODES + WATCH_REASON_CODES + (PASS_ROW_REASON_CODE,)
REPORT_REASON_PREFIX_BY_STATUS = {
    "pass": REPORT_PASS_REASON_CODE,
    "watch": REPORT_WATCH_REASON_CODE,
    "block": REPORT_BLOCK_REASON_CODE,
}
REPORT_REASON_CODES = (
    EMPTY_REPORT_REASON_CODE,
    REPORT_PASS_REASON_CODE,
    REPORT_WATCH_REASON_CODE,
    REPORT_BLOCK_REASON_CODE,
) + BLOCK_REASON_CODES + WATCH_REASON_CODES
REASON_CODE_COUNT_PRIORITY = (
    EMPTY_REPORT_REASON_CODE,
    *BLOCK_REASON_CODES,
    *WATCH_REASON_CODES,
    PASS_ROW_REASON_CODE,
)

HEX_CHARS = frozenset("0123456789abcdef")
SAFE_IDENTIFIER_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789_")
UNSAFE_IDENTIFIER_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
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
        "buy",
        "sell",
        "recommend",
        "position",
    ),
)
UNSAFE_PUBLIC_KEY_FRAGMENTS = frozenset(
    (
        "raw",
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
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
        "buy",
        "sell",
        "recommend",
        "position",
    ),
)
UNSAFE_PUBLIC_VALUE_FRAGMENTS = frozenset(
    (
        "http://",
        "https://",
        "source_url",
        "source_text",
        "dsn",
        "token",
        "secret",
        "auth",
        "wallet",
        "order",
        "trade",
        "trading",
        "buy",
        "sell",
        "recommend",
        "position",
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
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationDriftConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_DRIFT_REPORT_CONFIG_VERSION
    )
    min_recent_resolved_outcome_count: Decimal = Decimal("10")
    watch_calibration_error_rate: Decimal = Decimal("0.060000")
    block_calibration_error_rate: Decimal = Decimal("0.120000")
    max_pass_stale_memory_signal_count: Decimal = Decimal("0")
    max_watch_stale_memory_signal_count: Decimal = Decimal("2")
    max_pass_bias_flag_count: Decimal = Decimal("0")
    max_watch_bias_flag_count: Decimal = Decimal("1")
    min_pass_correction_follow_through_ratio: Decimal = Decimal("0.900000")
    min_watch_correction_follow_through_ratio: Decimal = Decimal("0.700000")
    min_pass_source_family_count: Decimal = Decimal("3")
    min_watch_source_family_count: Decimal = Decimal("2")
    max_pass_workload_pressure_score: Decimal = Decimal("0.500000")
    max_watch_workload_pressure_score: Decimal = Decimal("0.800000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationDriftConfig,
            "config",
        )
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_DRIFT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_recent_resolved_outcome_count",
            "max_pass_stale_memory_signal_count",
            "max_watch_stale_memory_signal_count",
            "max_pass_bias_flag_count",
            "max_watch_bias_flag_count",
            "min_pass_source_family_count",
            "min_watch_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_calibration_error_rate",
            "block_calibration_error_rate",
            "min_pass_correction_follow_through_ratio",
            "min_watch_correction_follow_through_ratio",
            "max_pass_workload_pressure_score",
            "max_watch_workload_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationDriftInput(_FinalPublicDataclass):
    team_key: str
    team_domain: str
    observed_at: datetime
    recent_resolved_outcome_count: Decimal
    calibration_error_rate: Decimal
    stale_memory_signal_count: Decimal
    bias_flag_count: Decimal
    pending_correction_count: Decimal
    correction_follow_through_ratio: Decimal
    source_family_count: Decimal
    workload_pressure_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCalibrationDriftInput, "input")
        _require_safe_identifier("team_key", self.team_key)
        _require_safe_identifier("team_domain", self.team_domain)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "recent_resolved_outcome_count",
            "stale_memory_signal_count",
            "bias_flag_count",
            "pending_correction_count",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_error_rate",
            "correction_follow_through_ratio",
            "workload_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationDriftRow(_FinalPublicDataclass):
    team_key: str
    team_domain: str
    status: str
    generated_at: datetime
    observed_at: datetime
    observation_age_seconds: Decimal
    recent_resolved_outcome_count: Decimal
    calibration_error_rate: Decimal
    stale_memory_signal_count: Decimal
    bias_flag_count: Decimal
    pending_correction_count: Decimal
    correction_follow_through_ratio: Decimal
    source_family_count: Decimal
    workload_pressure_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCalibrationDriftRow, "row")
        _require_safe_identifier("team_key", self.team_key)
        _require_safe_identifier("team_domain", self.team_domain)
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
        for field_name in (
            "recent_resolved_outcome_count",
            "stale_memory_signal_count",
            "bias_flag_count",
            "pending_correction_count",
            "source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "calibration_error_rate",
            "correction_follow_through_ratio",
            "workload_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _require_row_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchTeamSpecialistCalibrationDriftReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    team_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchTeamSpecialistCalibrationDriftReasonCodeCount,
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
class ResearchTeamSpecialistCalibrationDriftReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    specialist_team_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    drift_team_count: Decimal
    stale_memory_team_count: Decimal
    bias_flag_team_count: Decimal
    correction_gap_team_count: Decimal
    source_coverage_gap_team_count: Decimal
    workload_pressure_team_count: Decimal
    total_recent_resolved_outcome_count: Decimal
    average_calibration_error_rate: Decimal
    max_calibration_error_rate: Decimal
    min_correction_follow_through_ratio: Decimal
    min_source_family_count: Decimal
    max_workload_pressure_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchTeamSpecialistCalibrationDriftReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchTeamSpecialistCalibrationDriftRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchTeamSpecialistCalibrationDriftReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_text("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_DRIFT_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "specialist_team_count",
            "pass_count",
            "watch_count",
            "block_count",
            "drift_team_count",
            "stale_memory_team_count",
            "bias_flag_team_count",
            "correction_gap_team_count",
            "source_coverage_gap_team_count",
            "workload_pressure_team_count",
            "total_recent_resolved_outcome_count",
            "min_source_family_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_calibration_error_rate",
            "max_calibration_error_rate",
            "min_correction_follow_through_ratio",
            "max_workload_pressure_score",
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
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)


def build_research_team_specialist_calibration_drift_report(
    calibration_items: Iterable[ResearchTeamSpecialistCalibrationDriftInput],
    *,
    config: ResearchTeamSpecialistCalibrationDriftConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistCalibrationDriftReport:
    if type(config) is not ResearchTeamSpecialistCalibrationDriftConfig:
        raise ValueError(
            "config must be a ResearchTeamSpecialistCalibrationDriftConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_calibration_items(calibration_items)
    rows = tuple(
        sorted(
            (
                _row_for_calibration_item(
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
    return ResearchTeamSpecialistCalibrationDriftReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        specialist_team_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        drift_team_count=_reason_team_count(
            rows,
            CALIBRATION_ERROR_BLOCK_REASON,
            CALIBRATION_ERROR_WATCH_REASON,
        ),
        stale_memory_team_count=_reason_team_count(
            rows,
            STALE_MEMORY_BLOCK_REASON,
            STALE_MEMORY_WATCH_REASON,
        ),
        bias_flag_team_count=_reason_team_count(
            rows,
            BIAS_FLAG_BLOCK_REASON,
            BIAS_FLAG_WATCH_REASON,
        ),
        correction_gap_team_count=_reason_team_count(
            rows,
            CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
            CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
        ),
        source_coverage_gap_team_count=_reason_team_count(
            rows,
            SOURCE_COVERAGE_BLOCK_REASON,
            SOURCE_COVERAGE_WATCH_REASON,
        ),
        workload_pressure_team_count=_reason_team_count(
            rows,
            WORKLOAD_PRESSURE_BLOCK_REASON,
            WORKLOAD_PRESSURE_WATCH_REASON,
        ),
        total_recent_resolved_outcome_count=_sum_decimal(
            tuple(row.recent_resolved_outcome_count for row in rows),
            count=True,
        ),
        average_calibration_error_rate=_mean_decimal(
            tuple(row.calibration_error_rate for row in rows),
        ),
        max_calibration_error_rate=_max_decimal(
            tuple(row.calibration_error_rate for row in rows),
        ),
        min_correction_follow_through_ratio=_min_decimal(
            tuple(row.correction_follow_through_ratio for row in rows),
        ),
        min_source_family_count=_min_decimal(
            tuple(row.source_family_count for row in rows),
            count=True,
        ),
        max_workload_pressure_score=_max_decimal(
            tuple(row.workload_pressure_score for row in rows),
        ),
        status=status,
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_team_specialist_calibration_drift_report_payload(
    report: ResearchTeamSpecialistCalibrationDriftReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchTeamSpecialistCalibrationDriftReport:
        _require_hard_flags("report", report)
        _validate_report_materialized_fields(report)
        if report.derived_validation_digest != _derived_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _report_payload(report)
        _reject_unsafe_public_payload("payload", payload)
        _reject_public_numeric_values(payload)
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        _require_hard_flags("payload", _PayloadFlags(report))
        supplied_digest = report.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        _require_public_payload_schema(report)
        return report
    raise ValueError("report must be a ResearchTeamSpecialistCalibrationDriftReport")


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


def _require_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_public_keys("payload", payload, PUBLIC_PAYLOAD_KEYS)
    generated_at = _require_public_datetime_string(
        "generated_at",
        payload["generated_at"],
    )
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_DRIFT_REPORT_CONFIG_VERSION
    ):
        raise ValueError("config_version must be the supported config version")
    _require_status("status", payload["status"])
    for field_name in PUBLIC_PAYLOAD_COUNT_FIELDS:
        _require_public_count_string(field_name, payload[field_name])
    for field_name in PUBLIC_PAYLOAD_RATIO_FIELDS:
        _require_public_ratio_string(field_name, payload[field_name])
    _require_public_reason_codes(
        "reason_codes",
        payload["reason_codes"],
        report=True,
    )
    for item in _require_public_dict_list(
        "reason_code_counts",
        payload["reason_code_counts"],
    ):
        _require_public_reason_code_count_payload(item)
    for row in _require_public_dict_list("rows", payload["rows"]):
        _require_public_row_payload(row, generated_at=generated_at)
    _validate_public_payload_materialized_fields(payload)


def _require_public_reason_code_count_payload(payload: dict[str, Any]) -> None:
    _require_exact_public_keys(
        "reason_code_count",
        payload,
        PUBLIC_REASON_CODE_COUNT_KEYS,
    )
    _require_hard_flags("reason_code_count", _PayloadFlags(payload))
    _require_public_text("reason_code", payload["reason_code"])
    if payload["reason_code"] not in REASON_CODE_COUNT_PRIORITY:
        raise ValueError("reason_code must be supported")
    _require_public_count_string("count", payload["count"])
    _require_public_ratio_string("team_ratio", payload["team_ratio"])


def _require_public_row_payload(
    payload: dict[str, Any],
    *,
    generated_at: datetime,
) -> None:
    _require_exact_public_keys("row", payload, PUBLIC_ROW_KEYS)
    _require_hard_flags("row", _PayloadFlags(payload))
    _require_public_short_digest("team_digest", payload["team_digest"])
    _require_public_short_digest("domain_digest", payload["domain_digest"])
    _require_status("status", payload["status"])
    row_generated_at = _require_public_datetime_string(
        "row generated_at",
        payload["generated_at"],
    )
    if row_generated_at != generated_at:
        raise ValueError("row generated_at must match payload generated_at")
    observed_at = _require_public_datetime_string("observed_at", payload["observed_at"])
    if observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    _require_public_nonnegative_string(
        "observation_age_seconds",
        payload["observation_age_seconds"],
    )
    for field_name in PUBLIC_ROW_COUNT_FIELDS:
        _require_public_count_string(field_name, payload[field_name])
    for field_name in PUBLIC_ROW_RATIO_FIELDS:
        _require_public_ratio_string(field_name, payload[field_name])
    reason_codes = _require_public_reason_codes(
        "row reason_codes",
        payload["reason_codes"],
        report=False,
    )
    if payload["status"] != _row_status(reason_codes):
        raise ValueError("row status must match reason_codes")
    expected_age = _datetime_delta_seconds(generated_at, observed_at)
    if str(expected_age) != payload["observation_age_seconds"]:
        raise ValueError("observation_age_seconds must match generated_at and observed_at")


def _validate_public_payload_materialized_fields(payload: dict[str, Any]) -> None:
    rows = _require_public_dict_list("rows", payload["rows"])
    row_statuses = tuple(row["status"] for row in rows)
    row_reason_codes = tuple(tuple(row["reason_codes"]) for row in rows)
    checks = {
        "specialist_team_count": _count(len(rows)),
        "pass_count": _count(sum(status == "pass" for status in row_statuses)),
        "watch_count": _count(sum(status == "watch" for status in row_statuses)),
        "block_count": _count(sum(status == "block" for status in row_statuses)),
        "drift_team_count": _payload_reason_team_count(
            row_reason_codes,
            CALIBRATION_ERROR_BLOCK_REASON,
            CALIBRATION_ERROR_WATCH_REASON,
        ),
        "stale_memory_team_count": _payload_reason_team_count(
            row_reason_codes,
            STALE_MEMORY_BLOCK_REASON,
            STALE_MEMORY_WATCH_REASON,
        ),
        "bias_flag_team_count": _payload_reason_team_count(
            row_reason_codes,
            BIAS_FLAG_BLOCK_REASON,
            BIAS_FLAG_WATCH_REASON,
        ),
        "correction_gap_team_count": _payload_reason_team_count(
            row_reason_codes,
            CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
            CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
        ),
        "source_coverage_gap_team_count": _payload_reason_team_count(
            row_reason_codes,
            SOURCE_COVERAGE_BLOCK_REASON,
            SOURCE_COVERAGE_WATCH_REASON,
        ),
        "workload_pressure_team_count": _payload_reason_team_count(
            row_reason_codes,
            WORKLOAD_PRESSURE_BLOCK_REASON,
            WORKLOAD_PRESSURE_WATCH_REASON,
        ),
        "total_recent_resolved_outcome_count": _sum_decimal(
            tuple(
                _require_public_count_string(
                    "recent_resolved_outcome_count",
                    row["recent_resolved_outcome_count"],
                )
                for row in rows
            ),
            count=True,
        ),
        "average_calibration_error_rate": _mean_decimal(
            tuple(
                _require_public_ratio_string(
                    "calibration_error_rate",
                    row["calibration_error_rate"],
                )
                for row in rows
            ),
        ),
        "max_calibration_error_rate": _max_decimal(
            tuple(
                _require_public_ratio_string(
                    "calibration_error_rate",
                    row["calibration_error_rate"],
                )
                for row in rows
            ),
        ),
        "min_correction_follow_through_ratio": _min_decimal(
            tuple(
                _require_public_ratio_string(
                    "correction_follow_through_ratio",
                    row["correction_follow_through_ratio"],
                )
                for row in rows
            ),
        ),
        "min_source_family_count": _min_decimal(
            tuple(
                _require_public_count_string(
                    "source_family_count",
                    row["source_family_count"],
                )
                for row in rows
            ),
            count=True,
        ),
        "max_workload_pressure_score": _max_decimal(
            tuple(
                _require_public_ratio_string(
                    "workload_pressure_score",
                    row["workload_pressure_score"],
                )
                for row in rows
            ),
        ),
    }
    for field_name, expected in checks.items():
        if payload[field_name] != str(expected):
            raise ValueError(f"{field_name} must match rows")
    if payload["status"] != _rollup_status(row_statuses):
        raise ValueError("status must match rows")
    if tuple(payload["reason_codes"]) != _payload_report_reason_codes(
        row_reason_codes,
    ):
        raise ValueError("reason_codes must match rows")
    if _public_payload_reason_code_counts(row_reason_codes) != tuple(
        (item["reason_code"], item["count"], item["team_ratio"])
        for item in payload["reason_code_counts"]
    ):
        raise ValueError("reason_code_counts must match rows")


def _payload_reason_team_count(
    row_reason_codes: tuple[tuple[str, ...], ...],
    *reason_codes: str,
) -> Decimal:
    return _count(
        sum(
            any(reason_code in reasons for reason_code in reason_codes)
            for reasons in row_reason_codes
        ),
    )


def _payload_report_reason_codes(
    row_reason_codes: tuple[tuple[str, ...], ...],
) -> tuple[str, ...]:
    if not row_reason_codes:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(_row_status(reasons) for reasons in row_reason_codes))
    report_reason_codes = [REPORT_REASON_PREFIX_BY_STATUS[status]]
    row_reasons = frozenset(
        reason_code
        for reasons in row_reason_codes
        for reason_code in reasons
        if reason_code != PASS_ROW_REASON_CODE
    )
    for reason_code in BLOCK_REASON_CODES + WATCH_REASON_CODES:
        if reason_code in row_reasons:
            report_reason_codes.append(reason_code)
    return tuple(report_reason_codes)


def _public_payload_reason_code_counts(
    row_reason_codes: tuple[tuple[str, ...], ...],
) -> tuple[tuple[str, str, str], ...]:
    if not row_reason_codes:
        return ((EMPTY_REPORT_REASON_CODE, str(_count(1)), str(ONE_RATIO)),)
    counter: Counter[str] = Counter()
    for reason_codes in row_reason_codes:
        for reason_code in reason_codes:
            counter[reason_code] += 1
    denominator = _count(len(row_reason_codes))
    priority = {
        reason_code: index
        for index, reason_code in enumerate(REASON_CODE_COUNT_PRIORITY)
    }
    return tuple(
        (reason_code, str(count), str(_ratio(count, denominator)))
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
        )
    )


def _require_exact_public_keys(
    label: str,
    payload: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(payload)
    unexpected_keys = sorted(actual_keys - expected_keys)
    if unexpected_keys:
        raise ValueError(f"unexpected public payload field: {unexpected_keys[0]}")
    missing_keys = sorted(expected_keys - actual_keys)
    if missing_keys:
        raise ValueError(f"{label} missing public payload field: {missing_keys[0]}")


def _require_public_dict_list(field_name: str, value: object) -> list[dict[str, Any]]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    normalized: list[dict[str, Any]] = []
    for item in value:
        if type(item) is not dict:
            raise ValueError(f"{field_name} must contain public payload objects")
        normalized.append(item)
    return normalized


def _require_public_reason_codes(
    field_name: str,
    value: object,
    *,
    report: bool,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes = tuple(value)
    if report:
        return _require_report_reason_codes(reason_codes)
    return _require_row_reason_codes(reason_codes)


def _require_public_count_string(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal_from_public_string(field_name, value)
    normalized = _require_count_decimal(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_nonnegative_string(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal_from_public_string(field_name, value)
    normalized = _require_nonnegative_decimal(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _require_public_ratio_string(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal_from_public_string(field_name, value)
    normalized = _require_ratio_decimal(field_name, decimal_value)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return normalized


def _decimal_from_public_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        return Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc


def _require_public_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a UTC datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a UTC datetime string") from exc
    normalized = _as_utc(field_name, parsed)
    if value != normalized.isoformat():
        raise ValueError(f"{field_name} must be a UTC datetime string")
    return normalized


def _require_public_short_digest(field_name: str, value: object) -> None:
    if type(value) is not str or not value.startswith("sha256:"):
        raise ValueError(f"{field_name} must be a public sha256 digest")
    suffix = value.removeprefix("sha256:")
    if len(suffix) != 16 or any(character not in HEX_CHARS for character in suffix):
        raise ValueError(f"{field_name} must be a public sha256 digest")


def _normalize_calibration_items(
    calibration_items: Iterable[ResearchTeamSpecialistCalibrationDriftInput],
) -> tuple[ResearchTeamSpecialistCalibrationDriftInput, ...]:
    if isinstance(calibration_items, (str, bytes)):
        raise ValueError("calibration_items must be an iterable")
    try:
        items = tuple(calibration_items)
    except TypeError as exc:
        raise ValueError("calibration_items must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not ResearchTeamSpecialistCalibrationDriftInput:
            raise ValueError(
                "calibration_items must contain "
                "ResearchTeamSpecialistCalibrationDriftInput",
            )
        _require_hard_flags("input", item)
        if item.team_key in seen:
            raise ValueError("team_key values must be unique")
        seen.add(item.team_key)
    return items


def _row_for_calibration_item(
    item: ResearchTeamSpecialistCalibrationDriftInput,
    *,
    config: ResearchTeamSpecialistCalibrationDriftConfig,
    generated_at: datetime,
) -> ResearchTeamSpecialistCalibrationDriftRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(item, config=config)
    return ResearchTeamSpecialistCalibrationDriftRow(
        team_key=item.team_key,
        team_domain=item.team_domain,
        status=_row_status(reason_codes),
        generated_at=generated_at,
        observed_at=item.observed_at,
        observation_age_seconds=_datetime_delta_seconds(generated_at, item.observed_at),
        recent_resolved_outcome_count=item.recent_resolved_outcome_count,
        calibration_error_rate=item.calibration_error_rate,
        stale_memory_signal_count=item.stale_memory_signal_count,
        bias_flag_count=item.bias_flag_count,
        pending_correction_count=item.pending_correction_count,
        correction_follow_through_ratio=item.correction_follow_through_ratio,
        source_family_count=item.source_family_count,
        workload_pressure_score=item.workload_pressure_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchTeamSpecialistCalibrationDriftInput,
    *,
    config: ResearchTeamSpecialistCalibrationDriftConfig,
) -> tuple[str, ...]:
    if item.recent_resolved_outcome_count < config.min_recent_resolved_outcome_count:
        return (RECENT_OUTCOMES_BLOCK_REASON,)

    reason_codes: list[str] = []
    if item.calibration_error_rate >= config.block_calibration_error_rate:
        reason_codes.append(CALIBRATION_ERROR_BLOCK_REASON)
    elif item.calibration_error_rate >= config.watch_calibration_error_rate:
        reason_codes.append(CALIBRATION_ERROR_WATCH_REASON)

    if item.stale_memory_signal_count > config.max_watch_stale_memory_signal_count:
        reason_codes.append(STALE_MEMORY_BLOCK_REASON)
    elif item.stale_memory_signal_count > config.max_pass_stale_memory_signal_count:
        reason_codes.append(STALE_MEMORY_WATCH_REASON)

    if item.bias_flag_count > config.max_watch_bias_flag_count:
        reason_codes.append(BIAS_FLAG_BLOCK_REASON)
    elif item.bias_flag_count > config.max_pass_bias_flag_count:
        reason_codes.append(BIAS_FLAG_WATCH_REASON)

    if (
        item.correction_follow_through_ratio
        < config.min_watch_correction_follow_through_ratio
    ):
        reason_codes.append(CORRECTION_FOLLOW_THROUGH_BLOCK_REASON)
    elif (
        item.correction_follow_through_ratio
        < config.min_pass_correction_follow_through_ratio
    ):
        reason_codes.append(CORRECTION_FOLLOW_THROUGH_WATCH_REASON)

    if item.source_family_count < config.min_watch_source_family_count:
        reason_codes.append(SOURCE_COVERAGE_BLOCK_REASON)
    elif item.source_family_count < config.min_pass_source_family_count:
        reason_codes.append(SOURCE_COVERAGE_WATCH_REASON)

    if item.workload_pressure_score > config.max_watch_workload_pressure_score:
        reason_codes.append(WORKLOAD_PRESSURE_BLOCK_REASON)
    elif item.workload_pressure_score > config.max_pass_workload_pressure_score:
        reason_codes.append(WORKLOAD_PRESSURE_WATCH_REASON)

    if not reason_codes:
        reason_codes.append(PASS_ROW_REASON_CODE)
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
    rows: tuple[ResearchTeamSpecialistCalibrationDriftRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REPORT_REASON_CODE,)
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = [REPORT_REASON_PREFIX_BY_STATUS[status]]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != PASS_ROW_REASON_CODE
    )
    for reason_code in BLOCK_REASON_CODES + WATCH_REASON_CODES:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchTeamSpecialistCalibrationDriftRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationDriftReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchTeamSpecialistCalibrationDriftReasonCodeCount(
                reason_code=EMPTY_REPORT_REASON_CODE,
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
        ResearchTeamSpecialistCalibrationDriftReasonCodeCount(
            reason_code=reason_code,
            count=count,
            team_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], priority.get(item[1], 999), item[1]),
    )
)

PUBLIC_PAYLOAD_KEYS = frozenset(
    (
        "generated_at",
        "config_version",
        "specialist_team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "drift_team_count",
        "stale_memory_team_count",
        "bias_flag_team_count",
        "correction_gap_team_count",
        "source_coverage_gap_team_count",
        "workload_pressure_team_count",
        "total_recent_resolved_outcome_count",
        "average_calibration_error_rate",
        "max_calibration_error_rate",
        "min_correction_follow_through_ratio",
        "min_source_family_count",
        "max_workload_pressure_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_PAYLOAD_COUNT_FIELDS = frozenset(
    (
        "specialist_team_count",
        "pass_count",
        "watch_count",
        "block_count",
        "drift_team_count",
        "stale_memory_team_count",
        "bias_flag_team_count",
        "correction_gap_team_count",
        "source_coverage_gap_team_count",
        "workload_pressure_team_count",
        "total_recent_resolved_outcome_count",
        "min_source_family_count",
    ),
)
PUBLIC_PAYLOAD_RATIO_FIELDS = frozenset(
    (
        "average_calibration_error_rate",
        "max_calibration_error_rate",
        "min_correction_follow_through_ratio",
        "max_workload_pressure_score",
    ),
)
PUBLIC_REASON_CODE_COUNT_KEYS = frozenset(
    (
        "reason_code",
        "count",
        "team_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_ROW_KEYS = frozenset(
    (
        "team_digest",
        "domain_digest",
        "status",
        "generated_at",
        "observed_at",
        "observation_age_seconds",
        "recent_resolved_outcome_count",
        "calibration_error_rate",
        "stale_memory_signal_count",
        "bias_flag_count",
        "pending_correction_count",
        "correction_follow_through_ratio",
        "source_family_count",
        "workload_pressure_score",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
PUBLIC_ROW_COUNT_FIELDS = frozenset(
    (
        "recent_resolved_outcome_count",
        "stale_memory_signal_count",
        "bias_flag_count",
        "pending_correction_count",
        "source_family_count",
    ),
)
PUBLIC_ROW_RATIO_FIELDS = frozenset(
    (
        "calibration_error_rate",
        "correction_follow_through_ratio",
        "workload_pressure_score",
    ),
)


def _row_sort_key(
    row: ResearchTeamSpecialistCalibrationDriftRow,
) -> tuple[Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.status],
        -_row_severity_score(row),
        -row.calibration_error_rate,
        row.team_domain,
        row.team_key,
    )


def _row_severity_score(row: ResearchTeamSpecialistCalibrationDriftRow) -> Decimal:
    severity = STATUS_WEIGHT[row.status]
    severity += _count(sum(reason != PASS_ROW_REASON_CODE for reason in row.reason_codes))
    severity += row.calibration_error_rate
    severity += row.workload_pressure_score
    return _quantize_ratio(severity)


def _status_count(
    rows: tuple[ResearchTeamSpecialistCalibrationDriftRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(row.status == status for row in rows))


def _reason_team_count(
    rows: tuple[ResearchTeamSpecialistCalibrationDriftRow, ...],
    *reason_codes: str,
) -> Decimal:
    return _count(
        sum(any(reason_code in row.reason_codes for reason_code in reason_codes) for row in rows),
    )


def _validate_config(config: ResearchTeamSpecialistCalibrationDriftConfig) -> None:
    if config.watch_calibration_error_rate > config.block_calibration_error_rate:
        raise ValueError(
            "block_calibration_error_rate must be at least watch_calibration_error_rate",
        )
    if (
        config.max_pass_stale_memory_signal_count
        > config.max_watch_stale_memory_signal_count
    ):
        raise ValueError(
            "max_watch_stale_memory_signal_count must be at least "
            "max_pass_stale_memory_signal_count",
        )
    if config.max_pass_bias_flag_count > config.max_watch_bias_flag_count:
        raise ValueError(
            "max_watch_bias_flag_count must be at least max_pass_bias_flag_count",
        )
    if (
        config.min_watch_correction_follow_through_ratio
        > config.min_pass_correction_follow_through_ratio
    ):
        raise ValueError(
            "min_watch_correction_follow_through_ratio must not exceed "
            "min_pass_correction_follow_through_ratio",
        )
    if config.min_watch_source_family_count > config.min_pass_source_family_count:
        raise ValueError(
            "min_watch_source_family_count must not exceed min_pass_source_family_count",
        )
    if config.max_pass_workload_pressure_score > config.max_watch_workload_pressure_score:
        raise ValueError(
            "max_watch_workload_pressure_score must be at least "
            "max_pass_workload_pressure_score",
        )


def _validate_row(row: ResearchTeamSpecialistCalibrationDriftRow) -> None:
    if row.observed_at > row.generated_at:
        raise ValueError("observed_at must not be in the future")
    if row.observation_age_seconds != _datetime_delta_seconds(
        row.generated_at,
        row.observed_at,
    ):
        raise ValueError("observation_age_seconds must match generated_at and observed_at")
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_materialized_fields(
    report: ResearchTeamSpecialistCalibrationDriftReport,
) -> None:
    rows = report.rows
    checks = {
        "specialist_team_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "drift_team_count": _reason_team_count(
            rows,
            CALIBRATION_ERROR_BLOCK_REASON,
            CALIBRATION_ERROR_WATCH_REASON,
        ),
        "stale_memory_team_count": _reason_team_count(
            rows,
            STALE_MEMORY_BLOCK_REASON,
            STALE_MEMORY_WATCH_REASON,
        ),
        "bias_flag_team_count": _reason_team_count(
            rows,
            BIAS_FLAG_BLOCK_REASON,
            BIAS_FLAG_WATCH_REASON,
        ),
        "correction_gap_team_count": _reason_team_count(
            rows,
            CORRECTION_FOLLOW_THROUGH_BLOCK_REASON,
            CORRECTION_FOLLOW_THROUGH_WATCH_REASON,
        ),
        "source_coverage_gap_team_count": _reason_team_count(
            rows,
            SOURCE_COVERAGE_BLOCK_REASON,
            SOURCE_COVERAGE_WATCH_REASON,
        ),
        "workload_pressure_team_count": _reason_team_count(
            rows,
            WORKLOAD_PRESSURE_BLOCK_REASON,
            WORKLOAD_PRESSURE_WATCH_REASON,
        ),
        "total_recent_resolved_outcome_count": _sum_decimal(
            tuple(row.recent_resolved_outcome_count for row in rows),
            count=True,
        ),
        "average_calibration_error_rate": _mean_decimal(
            tuple(row.calibration_error_rate for row in rows),
        ),
        "max_calibration_error_rate": _max_decimal(
            tuple(row.calibration_error_rate for row in rows),
        ),
        "min_correction_follow_through_ratio": _min_decimal(
            tuple(row.correction_follow_through_ratio for row in rows),
        ),
        "min_source_family_count": _min_decimal(
            tuple(row.source_family_count for row in rows),
            count=True,
        ),
        "max_workload_pressure_score": _max_decimal(
            tuple(row.workload_pressure_score for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchTeamSpecialistCalibrationDriftRow, ...],
) -> tuple[ResearchTeamSpecialistCalibrationDriftRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistCalibrationDriftRow:
            raise ValueError("rows must contain ResearchTeamSpecialistCalibrationDriftRow")
        _require_hard_flags("row", row)
        if row.team_key in seen:
            raise ValueError("rows must contain unique team_key values")
        seen.add(row.team_key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and team_key")
    return normalized


def _require_reason_code_counts(
    rows: tuple[ResearchTeamSpecialistCalibrationDriftReasonCodeCount, ...],
) -> tuple[ResearchTeamSpecialistCalibrationDriftReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchTeamSpecialistCalibrationDriftReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchTeamSpecialistCalibrationDriftReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_row_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_text("reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    if normalized != tuple(reason for reason in ROW_REASON_CODES if reason in normalized):
        raise ValueError("reason_codes must be sorted")
    if PASS_ROW_REASON_CODE in normalized and len(normalized) != 1:
        raise ValueError("pass reason_codes must not be mixed with drift reasons")
    return normalized


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_text("reason_code", reason_code)
        if reason_code not in REPORT_REASON_CODES:
            raise ValueError("reason_code must be supported")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_safe_identifier(field_name: str, value: object) -> None:
    _require_public_text(field_name, value)
    if any(character not in SAFE_IDENTIFIER_CHARS for character in value):
        raise ValueError(f"{field_name} must be lowercase snake case")
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_IDENTIFIER_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _require_public_text(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_value(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized.quantize(COUNT_QUANTUM)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be non-negative")
    return _quantize_ratio(normalized)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE_RATIO:
        raise ValueError(f"{field_name} must be no greater than 1")
    return normalized


def _quantize_ratio(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO_COUNT:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (numerator / denominator).quantize(RATIO_QUANTUM)


def _datetime_delta_seconds(later: datetime, earlier: datetime) -> Decimal:
    delta = later - earlier
    micros = (
        Decimal(delta.days) * Decimal("86400000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize_ratio(micros / MICROSECONDS_PER_SECOND)


def _sum_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        if type(value) is not Decimal:
            raise ValueError("sum values must be Decimal")
        total += value
    return total.quantize(COUNT_QUANTUM if count else RATIO_QUANTUM)


def _mean_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _max_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    if not values:
        return ZERO_COUNT if count else ZERO_RATIO
    value = max(values)
    return value.quantize(COUNT_QUANTUM if count else RATIO_QUANTUM)


def _min_decimal(values: tuple[Decimal, ...], *, count: bool = False) -> Decimal:
    if not values:
        return ZERO_COUNT if count else ZERO_RATIO
    value = min(values)
    return value.quantize(COUNT_QUANTUM if count else RATIO_QUANTUM)


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _derived_validation_digest(
    report: ResearchTeamSpecialistCalibrationDriftReport,
) -> str:
    payload = _report_payload_base(report)
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = _strip_digest(payload)
    canonical = json.dumps(
        digest_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _strip_digest(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_digest(item)
            for key, item in sorted(value.items())
            if key != "derived_validation_digest"
        }
    if isinstance(value, list):
        return [_strip_digest(item) for item in value]
    return value


def _report_payload(report: ResearchTeamSpecialistCalibrationDriftReport) -> dict[str, Any]:
    payload = _report_payload_base(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _report_payload_base(
    report: ResearchTeamSpecialistCalibrationDriftReport,
) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "specialist_team_count": str(report.specialist_team_count),
        "pass_count": str(report.pass_count),
        "watch_count": str(report.watch_count),
        "block_count": str(report.block_count),
        "drift_team_count": str(report.drift_team_count),
        "stale_memory_team_count": str(report.stale_memory_team_count),
        "bias_flag_team_count": str(report.bias_flag_team_count),
        "correction_gap_team_count": str(report.correction_gap_team_count),
        "source_coverage_gap_team_count": str(report.source_coverage_gap_team_count),
        "workload_pressure_team_count": str(report.workload_pressure_team_count),
        "total_recent_resolved_outcome_count": str(
            report.total_recent_resolved_outcome_count,
        ),
        "average_calibration_error_rate": str(report.average_calibration_error_rate),
        "max_calibration_error_rate": str(report.max_calibration_error_rate),
        "min_correction_follow_through_ratio": str(
            report.min_correction_follow_through_ratio,
        ),
        "min_source_family_count": str(report.min_source_family_count),
        "max_workload_pressure_score": str(report.max_workload_pressure_score),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _reason_code_count_payload(
    row: ResearchTeamSpecialistCalibrationDriftReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": str(row.count),
        "team_ratio": str(row.team_ratio),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_payload(row: ResearchTeamSpecialistCalibrationDriftRow) -> dict[str, Any]:
    return {
        "team_digest": _public_digest(row.team_key),
        "domain_digest": _public_digest(row.team_domain),
        "status": row.status,
        "generated_at": row.generated_at.isoformat(),
        "observed_at": row.observed_at.isoformat(),
        "observation_age_seconds": str(row.observation_age_seconds),
        "recent_resolved_outcome_count": str(row.recent_resolved_outcome_count),
        "calibration_error_rate": str(row.calibration_error_rate),
        "stale_memory_signal_count": str(row.stale_memory_signal_count),
        "bias_flag_count": str(row.bias_flag_count),
        "pending_correction_count": str(row.pending_correction_count),
        "correction_follow_through_ratio": str(row.correction_follow_through_ratio),
        "source_family_count": str(row.source_family_count),
        "workload_pressure_score": str(row.workload_pressure_score),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float):
        raise ValueError("public payload numeric values must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public key")
            _reject_unsafe_public_key("public key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True")
            _reject_unsafe_public_payload(key, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_value(label, value)


def _reject_unsafe_public_key(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_KEY_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _reject_unsafe_public_value(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_VALUE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public text")


def _public_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:16]


__all__ = (
    "DEFAULT_RESEARCH_TEAM_SPECIALIST_CALIBRATION_DRIFT_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchTeamSpecialistCalibrationDriftConfig",
    "ResearchTeamSpecialistCalibrationDriftInput",
    "ResearchTeamSpecialistCalibrationDriftReasonCodeCount",
    "ResearchTeamSpecialistCalibrationDriftReport",
    "ResearchTeamSpecialistCalibrationDriftRow",
    "build_research_team_specialist_calibration_drift_report",
    "research_team_specialist_calibration_drift_report_payload",
)
