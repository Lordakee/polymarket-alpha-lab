"""Report-only probability calibration benchmark dashboard."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable


DEFAULT_RESEARCH_PROBABILITY_CALIBRATION_BENCHMARK_DASHBOARD_CONFIG_VERSION = (
    "research-probability-calibration-benchmark-dashboard-v0"
)

PUBLIC_STATUSES = ("pass", "watch", "block")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
VALIDATION_DIGEST_ALGORITHM = "sha256"
HEX_DIGITS = frozenset("0123456789abcdef")
REASON_CODES = (
    "benchmark_sample_pass",
    "benchmark_sample_block",
    "benchmark_brier_pass",
    "benchmark_brier_watch",
    "benchmark_ece_pass",
    "benchmark_ece_watch",
    "benchmark_hard_review_clear",
    "benchmark_hard_review_flag",
    "benchmark_calibration_pass",
    "benchmark_calibration_watch",
    "benchmark_calibration_block",
    "dashboard_all_benchmarks_pass",
    "dashboard_benchmark_watch",
    "dashboard_benchmark_block",
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
class ResearchProbabilityCalibrationBenchmarkDashboardConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_PROBABILITY_CALIBRATION_BENCHMARK_DASHBOARD_CONFIG_VERSION
    )
    min_settled_count: Decimal = Decimal("30.000000")
    brier_watch_threshold: Decimal = Decimal("0.200000")
    expected_calibration_error_watch_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityCalibrationBenchmarkDashboardConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        object.__setattr__(
            self,
            "min_settled_count",
            _normalize_count_decimal("min_settled_count", self.min_settled_count),
        )
        object.__setattr__(
            self,
            "brier_watch_threshold",
            _normalize_probability_decimal(
                "brier_watch_threshold",
                self.brier_watch_threshold,
            ),
        )
        object.__setattr__(
            self,
            "expected_calibration_error_watch_threshold",
            _normalize_probability_decimal(
                "expected_calibration_error_watch_threshold",
                self.expected_calibration_error_watch_threshold,
            ),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchProbabilityCalibrationBenchmarkObservation(_FinalPublicDataclass):
    benchmark_label: str
    forecast_count: Decimal
    settled_count: Decimal
    brier_score: Decimal
    expected_calibration_error: Decimal
    hard_review_flag: bool = False
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityCalibrationBenchmarkObservation,
            "observation",
        )
        _require_public_identifier("benchmark_label", self.benchmark_label)
        _reject_unsafe_public_payload("benchmark_label", self.benchmark_label)
        for field_name in ("forecast_count", "settled_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("brier_score", "expected_calibration_error"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.settled_count > self.forecast_count:
            raise ValueError("settled_count must not exceed forecast_count")
        if type(self.hard_review_flag) is not bool:
            raise ValueError("hard_review_flag must be a bool")
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchProbabilityCalibrationBenchmarkDashboardRow(_FinalPublicDataclass):
    benchmark_label: str
    public_status: str
    forecast_count: Decimal
    settled_count: Decimal
    brier_score: Decimal
    expected_calibration_error: Decimal
    hard_review_flag: bool
    reason_codes: tuple[str, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityCalibrationBenchmarkDashboardRow,
            "row",
        )
        _require_public_identifier("benchmark_label", self.benchmark_label)
        _reject_unsafe_public_payload("benchmark_label", self.benchmark_label)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in ("forecast_count", "settled_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("brier_score", "expected_calibration_error"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        if type(self.hard_review_flag) is not bool:
            raise ValueError("hard_review_flag must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _row_validation_digest(self),
            ),
        )


@dataclass(frozen=True)
class ResearchProbabilityCalibrationBenchmarkReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityCalibrationBenchmarkReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class ResearchProbabilityCalibrationBenchmarkDashboardReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    public_status: str
    benchmark_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_forecast_count: Decimal
    total_settled_count: Decimal
    average_brier_score: Decimal
    average_expected_calibration_error: Decimal
    max_brier_score: Decimal
    max_expected_calibration_error: Decimal
    hard_review_flag_count: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchProbabilityCalibrationBenchmarkReasonCodeCount, ...]
    rows: tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...]
    validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchProbabilityCalibrationBenchmarkDashboardReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_member("public_status", self.public_status, PUBLIC_STATUSES)
        for field_name in (
            "benchmark_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_forecast_count",
            "total_settled_count",
            "hard_review_flag_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_brier_score",
            "average_expected_calibration_error",
            "max_brier_score",
            "max_expected_calibration_error",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report_consistency(self)
        _require_hard_flags(self)
        object.__setattr__(
            self,
            "validation_digest",
            _normalize_validation_digest(
                "validation_digest",
                self.validation_digest,
                _report_validation_digest(self),
            ),
        )


_PUBLIC_DATACLASS_TYPES = (
    ResearchProbabilityCalibrationBenchmarkDashboardConfig,
    ResearchProbabilityCalibrationBenchmarkObservation,
    ResearchProbabilityCalibrationBenchmarkDashboardRow,
    ResearchProbabilityCalibrationBenchmarkReasonCodeCount,
    ResearchProbabilityCalibrationBenchmarkDashboardReport,
)


def build_research_probability_calibration_benchmark_dashboard(
    observations: Iterable[ResearchProbabilityCalibrationBenchmarkObservation],
    *,
    config: ResearchProbabilityCalibrationBenchmarkDashboardConfig,
    generated_at: datetime,
) -> ResearchProbabilityCalibrationBenchmarkDashboardReport:
    if type(config) is not ResearchProbabilityCalibrationBenchmarkDashboardConfig:
        raise ValueError(
            "config must be a ResearchProbabilityCalibrationBenchmarkDashboardConfig",
        )
    _require_hard_flags(config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_observations(observations)
    rows = tuple(
        sorted(
            (
                _row_from_observation(
                    observation,
                    config=config,
                )
                for observation in normalized
            ),
            key=lambda row: row.benchmark_label,
        ),
    )
    return ResearchProbabilityCalibrationBenchmarkDashboardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        public_status=_report_status(rows),
        benchmark_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        total_forecast_count=_sum_row_decimal(rows, "forecast_count"),
        total_settled_count=_sum_row_decimal(rows, "settled_count"),
        average_brier_score=_average_row_decimal(rows, "brier_score"),
        average_expected_calibration_error=_average_row_decimal(
            rows,
            "expected_calibration_error",
        ),
        max_brier_score=_max_row_decimal(rows, "brier_score"),
        max_expected_calibration_error=_max_row_decimal(
            rows,
            "expected_calibration_error",
        ),
        hard_review_flag_count=_count_decimal(
            sum(1 for row in rows if row.hard_review_flag),
        ),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_probability_calibration_benchmark_dashboard_payload(
    report: ResearchProbabilityCalibrationBenchmarkDashboardReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchProbabilityCalibrationBenchmarkDashboardReport:
        _validate_report_runtime(report)
        payload = _json_value(asdict(report), allow_decimal=True)
    elif type(report) is dict:
        payload = _json_value(report, allow_decimal=False)
    else:
        raise ValueError(
            "report must be a ResearchProbabilityCalibrationBenchmarkDashboardReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _reject_unsafe_public_payload(
        "research probability calibration benchmark dashboard payload",
        payload,
    )
    _require_payload_flags(payload)
    _validate_payload_digest(payload)
    return payload


def research_probability_calibration_benchmark_dashboard_digest(
    report: ResearchProbabilityCalibrationBenchmarkDashboardReport | dict[str, Any],
) -> dict[str, Any]:
    payload = research_probability_calibration_benchmark_dashboard_payload(report)
    digest = {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "public_status": payload["public_status"],
        "benchmark_count": payload["benchmark_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "total_forecast_count": payload["total_forecast_count"],
        "total_settled_count": payload["total_settled_count"],
        "average_brier_score": payload["average_brier_score"],
        "average_expected_calibration_error": payload[
            "average_expected_calibration_error"
        ],
        "max_brier_score": payload["max_brier_score"],
        "max_expected_calibration_error": payload["max_expected_calibration_error"],
        "hard_review_flag_count": payload["hard_review_flag_count"],
        "reason_codes": payload["reason_codes"],
        "reason_code_counts": payload["reason_code_counts"],
        "report_validation_digest": payload["validation_digest"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    _reject_unsafe_public_payload(
        "research probability calibration benchmark dashboard digest",
        digest,
    )
    digest["digest_validation_digest"] = _digest_validation_digest(digest)
    return digest


def _row_from_observation(
    observation: ResearchProbabilityCalibrationBenchmarkObservation,
    *,
    config: ResearchProbabilityCalibrationBenchmarkDashboardConfig,
) -> ResearchProbabilityCalibrationBenchmarkDashboardRow:
    reason_codes = _row_reason_codes(observation, config=config)
    return ResearchProbabilityCalibrationBenchmarkDashboardRow(
        benchmark_label=observation.benchmark_label,
        public_status=_row_status(reason_codes),
        forecast_count=observation.forecast_count,
        settled_count=observation.settled_count,
        brier_score=observation.brier_score,
        expected_calibration_error=observation.expected_calibration_error,
        hard_review_flag=observation.hard_review_flag,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    observation: ResearchProbabilityCalibrationBenchmarkObservation,
    *,
    config: ResearchProbabilityCalibrationBenchmarkDashboardConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if observation.settled_count < config.min_settled_count:
        reason_codes.append("benchmark_sample_block")
    else:
        reason_codes.append("benchmark_sample_pass")
    if observation.brier_score > config.brier_watch_threshold:
        reason_codes.append("benchmark_brier_watch")
    else:
        reason_codes.append("benchmark_brier_pass")
    if (
        observation.expected_calibration_error
        > config.expected_calibration_error_watch_threshold
    ):
        reason_codes.append("benchmark_ece_watch")
    else:
        reason_codes.append("benchmark_ece_pass")
    if observation.hard_review_flag:
        reason_codes.append("benchmark_hard_review_flag")
    else:
        reason_codes.append("benchmark_hard_review_clear")
    reason_codes.append(f"benchmark_calibration_{_row_status(tuple(reason_codes))}")
    return _normalize_reason_codes(tuple(reason_codes))


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if (
        "benchmark_sample_block" in reason_codes
        or "benchmark_hard_review_flag" in reason_codes
        or "benchmark_calibration_block" in reason_codes
    ):
        return "block"
    if (
        "benchmark_brier_watch" in reason_codes
        or "benchmark_ece_watch" in reason_codes
        or "benchmark_calibration_watch" in reason_codes
    ):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...],
) -> str:
    statuses = tuple(row.public_status for row in rows)
    if not statuses or "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...],
) -> tuple[str, ...]:
    values = {reason_code for row in rows for reason_code in row.reason_codes}
    status = _report_status(rows)
    if status == "block":
        values.add("dashboard_benchmark_block")
    elif status == "watch":
        values.add("dashboard_benchmark_watch")
    else:
        values.add("dashboard_all_benchmarks_pass")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in values)


def _reason_code_counts(
    rows: tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...],
) -> tuple[ResearchProbabilityCalibrationBenchmarkReasonCodeCount, ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    for reason_code in _report_reason_codes(rows):
        if reason_code.startswith("dashboard_"):
            counts[reason_code] = 1
    return tuple(
        ResearchProbabilityCalibrationBenchmarkReasonCodeCount(
            reason_code=reason_code,
            count=_count_decimal(counts[reason_code]),
        )
        for reason_code in REASON_CODES
        if reason_code in counts
    )


def _normalize_observations(
    observations: Iterable[ResearchProbabilityCalibrationBenchmarkObservation],
) -> tuple[ResearchProbabilityCalibrationBenchmarkObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    seen_labels: set[str] = set()
    for observation in normalized:
        if type(observation) is not ResearchProbabilityCalibrationBenchmarkObservation:
            raise ValueError(
                "observations must contain "
                "ResearchProbabilityCalibrationBenchmarkObservation",
            )
        _require_hard_flags(observation)
        if observation.benchmark_label in seen_labels:
            raise ValueError("observations must contain one row per benchmark_label")
        seen_labels.add(observation.benchmark_label)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchProbabilityCalibrationBenchmarkDashboardRow],
) -> tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    previous_label = ""
    for row in normalized:
        if type(row) is not ResearchProbabilityCalibrationBenchmarkDashboardRow:
            raise ValueError(
                "rows must contain ResearchProbabilityCalibrationBenchmarkDashboardRow",
            )
        _require_hard_flags(row)
        if previous_label and row.benchmark_label <= previous_label:
            raise ValueError("rows must be deterministic by benchmark_label")
        previous_label = row.benchmark_label
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[ResearchProbabilityCalibrationBenchmarkReasonCodeCount],
) -> tuple[ResearchProbabilityCalibrationBenchmarkReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    previous_index = -1
    seen: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchProbabilityCalibrationBenchmarkReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchProbabilityCalibrationBenchmarkReasonCodeCount",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(item.reason_code)
        try:
            reason_index = REASON_CODES.index(item.reason_code)
        except ValueError as exc:
            raise ValueError("reason_code_counts must use known reason codes") from exc
        if reason_index <= previous_index:
            raise ValueError("reason_code_counts must be deterministic")
        previous_index = reason_index
    return normalized


def _validate_row_consistency(
    row: ResearchProbabilityCalibrationBenchmarkDashboardRow,
) -> None:
    if row.settled_count > row.forecast_count:
        raise ValueError("settled_count must not exceed forecast_count")
    if row.public_status != _row_status(row.reason_codes):
        raise ValueError("public_status must match reason_codes")


def _validate_report_consistency(
    report: ResearchProbabilityCalibrationBenchmarkDashboardReport,
) -> None:
    if report.benchmark_count != _count_decimal(len(report.rows)):
        raise ValueError("benchmark_count must match rows")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.public_status != _report_status(report.rows):
        raise ValueError("public_status must match rows")
    for field_name in ("forecast_count", "settled_count"):
        report_field_name = "total_" + field_name
        if getattr(report, report_field_name) != _sum_row_decimal(
            report.rows,
            field_name,
        ):
            raise ValueError(f"{report_field_name} must match rows")
    for field_name in ("brier_score", "expected_calibration_error"):
        report_field_name = "average_" + field_name
        if getattr(report, report_field_name) != _average_row_decimal(
            report.rows,
            field_name,
        ):
            raise ValueError(f"{report_field_name} must match rows")
        max_field_name = "max_" + field_name
        if getattr(report, max_field_name) != _max_row_decimal(report.rows, field_name):
            raise ValueError(f"{max_field_name} must match rows")
    if report.hard_review_flag_count != _count_decimal(
        sum(1 for row in report.rows if row.hard_review_flag),
    ):
        raise ValueError("hard_review_flag_count must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _validate_report_runtime(
    report: ResearchProbabilityCalibrationBenchmarkDashboardReport,
) -> None:
    _require_hard_flags(report)
    _as_utc("generated_at", report.generated_at)
    _require_public_identifier("config_version", report.config_version)
    _require_member("public_status", report.public_status, PUBLIC_STATUSES)
    _normalize_rows(report.rows)
    for row in report.rows:
        if row.validation_digest != _row_validation_digest(row):
            raise ValueError("validation_digest must match row")
    _validate_report_consistency(report)
    if report.validation_digest != _report_validation_digest(report):
        raise ValueError("validation_digest must match report")


def _validate_payload_digest(payload: dict[str, Any]) -> None:
    rows = _payload_rows(payload)
    row_digests = tuple(_payload_row_digest(row) for row in rows)
    for row, row_digest in zip(rows, row_digests, strict=True):
        if _payload_required_digest(row, "validation_digest") != row_digest:
            raise ValueError("validation_digest must match payload row")
    if _payload_required_digest(payload, "validation_digest") != _payload_report_digest(
        payload,
        row_digests,
    ):
        raise ValueError("validation_digest must match payload")
    _validate_payload_consistency(payload, rows)


def _validate_payload_consistency(
    payload: dict[str, Any],
    rows: tuple[dict[str, Any], ...],
) -> None:
    if _payload_required_decimal(payload, "benchmark_count") != _count_decimal(len(rows)):
        raise ValueError("benchmark_count must match payload rows")
    for status, field_name in (
        ("pass", "pass_count"),
        ("watch", "watch_count"),
        ("block", "block_count"),
    ):
        if _payload_required_decimal(payload, field_name) != _payload_status_count(
            rows,
            status,
        ):
            raise ValueError(f"{field_name} must match payload rows")
    if _payload_required_member(payload, "public_status", PUBLIC_STATUSES) != (
        _payload_report_status(rows)
    ):
        raise ValueError("public_status must match payload rows")
    if _payload_required_reason_codes(payload, "reason_codes") != _payload_report_reason_codes(
        rows,
    ):
        raise ValueError("reason_codes must match payload rows")
    if _payload_required_reason_code_counts(payload) != _payload_reason_code_counts(rows):
        raise ValueError("reason_code_counts must match payload rows")
    for field_name in ("forecast_count", "settled_count"):
        if _payload_required_decimal(payload, "total_" + field_name) != sum(
            (_payload_required_decimal(row, field_name) for row in rows),
            ZERO,
        ):
            raise ValueError(f"total_{field_name} must match payload rows")
    for field_name in ("brier_score", "expected_calibration_error"):
        if _payload_required_decimal(payload, "average_" + field_name) != _payload_average(
            rows,
            field_name,
        ):
            raise ValueError(f"average_{field_name} must match payload rows")
        if _payload_required_decimal(payload, "max_" + field_name) != _payload_max(
            rows,
            field_name,
        ):
            raise ValueError(f"max_{field_name} must match payload rows")
    if _payload_required_decimal(payload, "hard_review_flag_count") != _count_decimal(
        sum(1 for row in rows if _payload_required_bool(row, "hard_review_flag")),
    ):
        raise ValueError("hard_review_flag_count must match payload rows")


def _payload_report_status(rows: tuple[dict[str, Any], ...]) -> str:
    statuses = tuple(
        _payload_required_member(row, "public_status", PUBLIC_STATUSES) for row in rows
    )
    if not statuses or "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _payload_report_reason_codes(rows: tuple[dict[str, Any], ...]) -> tuple[str, ...]:
    values = {
        reason_code
        for row in rows
        for reason_code in _payload_required_reason_codes(row, "reason_codes")
    }
    status = _payload_report_status(rows)
    if status == "block":
        values.add("dashboard_benchmark_block")
    elif status == "watch":
        values.add("dashboard_benchmark_watch")
    else:
        values.add("dashboard_all_benchmarks_pass")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in values)


def _payload_reason_code_counts(
    rows: tuple[dict[str, Any], ...],
) -> tuple[dict[str, str | bool], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in _payload_required_reason_codes(row, "reason_codes"):
            counts[reason_code] = counts.get(reason_code, 0) + 1
    for reason_code in _payload_report_reason_codes(rows):
        if reason_code.startswith("dashboard_"):
            counts[reason_code] = 1
    return tuple(
        {
            "reason_code": reason_code,
            "count": _decimal_payload(_count_decimal(counts[reason_code])),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
        for reason_code in REASON_CODES
        if reason_code in counts
    )


def _payload_required_reason_code_counts(
    payload: dict[str, Any],
) -> tuple[dict[str, str | bool], ...]:
    values = payload.get("reason_code_counts")
    if not isinstance(values, list):
        raise ValueError("reason_code_counts must be a list")
    normalized: list[dict[str, str | bool]] = []
    previous_index = -1
    seen: set[str] = set()
    for value in values:
        if type(value) is not dict:
            raise ValueError("reason_code_counts must contain JSON objects")
        _require_payload_flags(value)
        reason_code = _payload_required_reason_code(value, "reason_code")
        if reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(reason_code)
        try:
            reason_index = REASON_CODES.index(reason_code)
        except ValueError as exc:
            raise ValueError("reason_code_counts must use known reason codes") from exc
        if reason_index <= previous_index:
            raise ValueError("reason_code_counts must be deterministic")
        previous_index = reason_index
        normalized.append(
            {
                "reason_code": reason_code,
                "count": _decimal_payload(_payload_required_decimal(value, "count")),
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    return tuple(normalized)


def _json_value(value: Any, *, allow_decimal: bool) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError("JSON value contains unsupported public dataclass")
        return {
            field.name: _json_value(getattr(value, field.name), allow_decimal=allow_decimal)
            for field in fields(value)
        }
    if type(value) is Decimal:
        if not allow_decimal:
            raise ValueError("JSON numeric value must use Decimal-derived strings")
        return _decimal_payload(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is datetime:
        return _datetime_payload(value)
    if type(value) is bool:
        return value
    if isinstance(value, (float, int)):
        raise ValueError("JSON numeric value must use Decimal-derived strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_value(item, allow_decimal=allow_decimal)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_value(item, allow_decimal=allow_decimal) for item in value]
    raise ValueError("value is not JSON serializable")


def _payload_rows(payload: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    rows = payload.get("rows")
    if not isinstance(rows, list):
        raise ValueError("rows must be a list")
    normalized: list[dict[str, Any]] = []
    previous_label = ""
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows must contain JSON objects")
        label = _payload_required_label(row)
        if previous_label and label <= previous_label:
            raise ValueError("rows must be deterministic by benchmark_label")
        previous_label = label
        _payload_required_member(row, "public_status", PUBLIC_STATUSES)
        _payload_required_decimal(row, "forecast_count")
        _payload_required_decimal(row, "settled_count")
        _payload_required_decimal(row, "brier_score")
        _payload_required_decimal(row, "expected_calibration_error")
        _payload_required_bool(row, "hard_review_flag")
        _payload_required_reason_codes(row, "reason_codes")
        _require_payload_flags(row)
        normalized.append(row)
    return tuple(normalized)


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _payload_required_label(payload: dict[str, Any]) -> str:
    value = _payload_required_string(payload, "benchmark_label")
    _reject_unsafe_public_payload("benchmark_label", value)
    return value


def _payload_required_member(
    payload: dict[str, Any],
    field_name: str,
    allowed_values: tuple[str, ...],
) -> str:
    value = _payload_required_string(payload, field_name)
    _require_member(field_name, value, allowed_values)
    return value


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    _require_public_identifier(field_name, value)
    return value


def _payload_required_bool(payload: dict[str, Any], field_name: str) -> bool:
    value = payload.get(field_name)
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _payload_required_decimal(payload: dict[str, Any], field_name: str) -> Decimal:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    try:
        decimal_value = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must use Decimal-derived string values") from exc
    canonical = _decimal_payload(_normalize_nonnegative_decimal(field_name, decimal_value))
    if value != canonical:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return Decimal(canonical)


def _payload_required_datetime(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    parsed = datetime.fromisoformat(value)
    if parsed != _as_utc(field_name, parsed):
        raise ValueError(f"{field_name} must be UTC")
    return parsed.isoformat()


def _payload_required_reason_codes(
    payload: dict[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a list")
    return _normalize_reason_codes(tuple(value))


def _payload_required_reason_code(payload: dict[str, Any], field_name: str) -> str:
    value = _payload_required_string(payload, field_name)
    _require_reason_code(field_name, value)
    return value


def _payload_required_digest(payload: dict[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    _require_validation_digest(field_name, value)
    return value


def _payload_status_count(rows: tuple[dict[str, Any], ...], status: str) -> Decimal:
    return _count_decimal(
        sum(1 for row in rows if _payload_required_member(row, "public_status", PUBLIC_STATUSES) == status),
    )


def _payload_average(rows: tuple[dict[str, Any], ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(
        sum((_payload_required_decimal(row, field_name) for row in rows), ZERO)
        / _count_decimal(len(rows)),
    )


def _payload_max(rows: tuple[dict[str, Any], ...], field_name: str) -> Decimal:
    if not rows:
        return ZERO
    return max(_payload_required_decimal(row, field_name) for row in rows)


def _payload_row_digest(payload: dict[str, Any]) -> str:
    digest_payload = {
        key: payload[key]
        for key in (
            "benchmark_label",
            "public_status",
            "forecast_count",
            "settled_count",
            "brier_score",
            "expected_calibration_error",
            "hard_review_flag",
            "reason_codes",
            "paper_only",
            "report_only",
            "readonly",
        )
    }
    return _hash_payload(digest_payload)


def _payload_report_digest(
    payload: dict[str, Any],
    row_digests: tuple[str, ...],
) -> str:
    digest_payload = {
        key: payload[key]
        for key in (
            "generated_at",
            "config_version",
            "public_status",
            "benchmark_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_forecast_count",
            "total_settled_count",
            "average_brier_score",
            "average_expected_calibration_error",
            "max_brier_score",
            "max_expected_calibration_error",
            "hard_review_flag_count",
            "reason_codes",
            "reason_code_counts",
            "paper_only",
            "report_only",
            "readonly",
        )
    }
    digest_payload["row_validation_digests"] = list(row_digests)
    return _hash_payload(digest_payload)


def _row_validation_digest(
    row: ResearchProbabilityCalibrationBenchmarkDashboardRow,
) -> str:
    return _hash_payload(
        {
            "benchmark_label": row.benchmark_label,
            "public_status": row.public_status,
            "forecast_count": _decimal_payload(row.forecast_count),
            "settled_count": _decimal_payload(row.settled_count),
            "brier_score": _decimal_payload(row.brier_score),
            "expected_calibration_error": _decimal_payload(
                row.expected_calibration_error,
            ),
            "hard_review_flag": row.hard_review_flag,
            "reason_codes": list(row.reason_codes),
            "paper_only": row.paper_only,
            "report_only": row.report_only,
            "readonly": row.readonly,
        },
    )


def _report_validation_digest(
    report: ResearchProbabilityCalibrationBenchmarkDashboardReport,
) -> str:
    return _hash_payload(
        {
            "generated_at": _datetime_payload(report.generated_at),
            "config_version": report.config_version,
            "public_status": report.public_status,
            "benchmark_count": _decimal_payload(report.benchmark_count),
            "pass_count": _decimal_payload(report.pass_count),
            "watch_count": _decimal_payload(report.watch_count),
            "block_count": _decimal_payload(report.block_count),
            "total_forecast_count": _decimal_payload(report.total_forecast_count),
            "total_settled_count": _decimal_payload(report.total_settled_count),
            "average_brier_score": _decimal_payload(report.average_brier_score),
            "average_expected_calibration_error": _decimal_payload(
                report.average_expected_calibration_error,
            ),
            "max_brier_score": _decimal_payload(report.max_brier_score),
            "max_expected_calibration_error": _decimal_payload(
                report.max_expected_calibration_error,
            ),
            "hard_review_flag_count": _decimal_payload(report.hard_review_flag_count),
            "reason_codes": list(report.reason_codes),
            "reason_code_counts": _json_value(
                report.reason_code_counts,
                allow_decimal=True,
            ),
            "row_validation_digests": [
                row.validation_digest for row in report.rows
            ],
            "paper_only": report.paper_only,
            "report_only": report.report_only,
            "readonly": report.readonly,
        },
    )


def _digest_validation_digest(payload: dict[str, Any]) -> str:
    return _hash_payload(payload)


def _hash_payload(payload: object) -> str:
    _reject_unsafe_public_payload("validation payload", payload)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _count_decimal(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value).quantize(DECIMAL_QUANTUM)


def _status_count(
    rows: tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.public_status == status))


def _sum_row_decimal(
    rows: tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...],
    field_name: str,
) -> Decimal:
    return _quantize(sum((getattr(row, field_name) for row in rows), ZERO))


def _average_row_decimal(
    rows: tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _quantize(
        sum((getattr(row, field_name) for row in rows), ZERO) / _count_decimal(len(rows)),
    )


def _max_row_decimal(
    rows: tuple[ResearchProbabilityCalibrationBenchmarkDashboardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be {expected_type.__name__}")


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return _quantize(normalized)


def _normalize_positive_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_count_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return +value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(DECIMAL_QUANTUM)


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public identifier")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789._:-"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic public text")


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")


def _normalize_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    normalized: set[str] = set()
    for value in values:
        _require_reason_code("reason_codes", value)
        normalized.add(value)
    if not normalized:
        raise ValueError("reason_codes must be nonempty")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in normalized)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be deterministic code text")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _normalize_validation_digest(
    field_name: str,
    value: object,
    expected_digest: str,
) -> str:
    if value == "":
        return expected_digest
    _require_validation_digest(field_name, value)
    if value != expected_digest:
        raise ValueError(f"{field_name} must match payload")
    return value


def _require_validation_digest(field_name: str, value: object) -> None:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in HEX_DIGITS for character in value)
    ):
        raise ValueError(f"{field_name} must be a sha256 validation digest")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{path or label} has unsafe public payload")
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _has_unsafe_public_fragment(value):
            raise ValueError(f"{path or label} has unsafe public value")
        return
    if type(value) is Decimal:
        _normalize_nonnegative_decimal(path or label, value)
        return
    if isinstance(value, Decimal):
        raise ValueError(f"{path or label} must be exactly Decimal")
    if type(value) is datetime:
        _as_utc(path or label, value)
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, (float, int)):
        raise ValueError(f"{path or label} must use Decimal-derived string values")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            if _has_unsafe_public_fragment(key):
                raise ValueError(f"unsafe public field in {label}: {key}")
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in _unsafe_public_fragments())


def _unsafe_public_fragments() -> tuple[str, ...]:
    return (
        "acco" "unt",
        "au" "th",
        "bal" "ance",
        "b" "uy",
        "candidate" "_" "id",
        "cancel",
        "cred" "ential",
        "d" "sn",
        "market" "_" "id",
        "market" "_" "slug",
        "ord" "er",
        "pos" "ition",
        "private" "_" "key",
        "ques" "tion",
        "raw" "_" "candidate",
        "reco" "mmend",
        "replace",
        "s" "ell",
        "sign",
        "source" "_" "ref",
        "source" "_" "reference",
        "source" "_" "text",
        "source" "_" "url",
        "ta" "ble",
        "to" "ken",
        "tra" "de",
        "tra" "ding",
        "u" "rl",
        "wal" "let",
    )
