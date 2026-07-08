"""Deterministic, read-only research calibration drift alert reports."""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION = (
    "research-calibration-drift-alert-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate",
    "market",
    "slug",
    "question",
    "source_ref",
    "source_url",
    "source_text",
    "http://",
    "https://",
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
    "database",
)
_ROW_REASON_SEQUENCE = (
    "brier_score_drift_block",
    "brier_score_drift_watch",
    "calibration_drift_block",
    "calibration_drift_watch",
    "calibration_drift_pass",
    "expected_calibration_error_drift_block",
    "expected_calibration_error_drift_watch",
    "manual_review_required",
    "settled_count_below_minimum",
)
_REPORT_REASON_SEQUENCE = (
    "no_calibration_drift_observations",
    "calibration_drift_report_block_rows",
    "calibration_drift_report_watch_rows",
    "calibration_drift_report_pass",
)

__all__ = (
    "DEFAULT_RESEARCH_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION",
    "ResearchCalibrationDriftAlertConfig",
    "ResearchCalibrationDriftObservation",
    "ResearchCalibrationDriftAlertRow",
    "ResearchCalibrationDriftAlertDigest",
    "ResearchCalibrationDriftAlertReport",
    "build_research_calibration_drift_alert_report",
    "research_calibration_drift_alert_report_payload",
    "research_calibration_drift_alert_digest_payload",
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
class ResearchCalibrationDriftAlertConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_CALIBRATION_DRIFT_ALERT_CONFIG_VERSION
    watch_brier_score_delta: Decimal = Decimal("0.030000")
    block_brier_score_delta: Decimal = Decimal("0.070000")
    watch_expected_calibration_error_delta: Decimal = Decimal("0.025000")
    block_expected_calibration_error_delta: Decimal = Decimal("0.060000")
    min_settled_count: Decimal = Decimal("20.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCalibrationDriftAlertConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for name in (
            "watch_brier_score_delta",
            "block_brier_score_delta",
            "watch_expected_calibration_error_delta",
            "block_expected_calibration_error_delta",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "min_settled_count",
            _require_nonnegative_count_decimal(
                "min_settled_count",
                self.min_settled_count,
            ),
        )
        if self.watch_brier_score_delta > self.block_brier_score_delta:
            raise ValueError("watch_brier_score_delta must not exceed block_brier_score_delta")
        if (
            self.watch_expected_calibration_error_delta
            > self.block_expected_calibration_error_delta
        ):
            raise ValueError(
                "watch_expected_calibration_error_delta must not exceed "
                "block_expected_calibration_error_delta",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchCalibrationDriftObservation(_FinalPublicDataclass):
    cohort_key: str
    window_start_at: datetime
    window_end_at: datetime
    settled_count: Decimal
    baseline_brier_score: Decimal
    current_brier_score: Decimal
    baseline_expected_calibration_error: Decimal
    current_expected_calibration_error: Decimal
    manual_block_flag: bool = False
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCalibrationDriftObservation, "observation")
        object.__setattr__(
            self,
            "cohort_key",
            _require_public_identifier("cohort_key", self.cohort_key),
        )
        object.__setattr__(
            self,
            "window_start_at",
            _as_utc("window_start_at", self.window_start_at),
        )
        object.__setattr__(
            self,
            "window_end_at",
            _as_utc("window_end_at", self.window_end_at),
        )
        if self.window_end_at <= self.window_start_at:
            raise ValueError("window_end_at must be after window_start_at")
        object.__setattr__(
            self,
            "settled_count",
            _require_nonnegative_count_decimal("settled_count", self.settled_count),
        )
        for name in (
            "baseline_brier_score",
            "current_brier_score",
            "baseline_expected_calibration_error",
            "current_expected_calibration_error",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        if type(self.manual_block_flag) is not bool:
            raise ValueError("manual_block_flag must be a bool")
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_SEQUENCE),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchCalibrationDriftAlertRow(_FinalPublicDataclass):
    cohort_key: str
    window_start_at: datetime
    window_end_at: datetime
    settled_count: Decimal
    baseline_brier_score: Decimal
    current_brier_score: Decimal
    brier_score_delta: Decimal
    absolute_brier_score_delta: Decimal
    baseline_expected_calibration_error: Decimal
    current_expected_calibration_error: Decimal
    expected_calibration_error_delta: Decimal
    absolute_expected_calibration_error_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCalibrationDriftAlertRow, "row")
        object.__setattr__(
            self,
            "cohort_key",
            _require_public_identifier("cohort_key", self.cohort_key),
        )
        object.__setattr__(
            self,
            "window_start_at",
            _as_utc("window_start_at", self.window_start_at),
        )
        object.__setattr__(
            self,
            "window_end_at",
            _as_utc("window_end_at", self.window_end_at),
        )
        if self.window_end_at <= self.window_start_at:
            raise ValueError("window_end_at must be after window_start_at")
        object.__setattr__(
            self,
            "settled_count",
            _require_nonnegative_count_decimal("settled_count", self.settled_count),
        )
        for name in (
            "baseline_brier_score",
            "current_brier_score",
            "absolute_brier_score_delta",
            "baseline_expected_calibration_error",
            "current_expected_calibration_error",
            "absolute_expected_calibration_error_delta",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        for name in (
            "brier_score_delta",
            "expected_calibration_error_delta",
        ):
            object.__setattr__(
                self,
                name,
                _require_bounded_delta_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchCalibrationDriftAlertDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    cohort_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_absolute_brier_score_delta: Decimal
    max_absolute_brier_score_delta: Decimal
    average_absolute_expected_calibration_error_delta: Decimal
    max_absolute_expected_calibration_error_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCalibrationDriftAlertDigest, "digest")
        _normalize_summary_fields(self)
        _validate_summary_counts(self)
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_SEQUENCE),
        )
        if self.status != _summary_status_from_counts(
            block_count=self.block_count,
            watch_count=self.watch_count,
            cohort_count=self.cohort_count,
        ):
            raise ValueError("status must match summary counts")
        if self.reason_codes != _report_reason_codes(
            block_count=self.block_count,
            watch_count=self.watch_count,
            cohort_count=self.cohort_count,
        ):
            raise ValueError("reason_codes must match status")
        _require_hard_flags("digest", self)
        _reject_unsafe_public_payload("digest", self)
        _finalize_digest_payload(self)


@dataclass(frozen=True)
class ResearchCalibrationDriftAlertReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    cohort_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_absolute_brier_score_delta: Decimal
    max_absolute_brier_score_delta: Decimal
    average_absolute_expected_calibration_error_delta: Decimal
    max_absolute_expected_calibration_error_delta: Decimal
    status: str
    reason_codes: tuple[str, ...]
    digest: ResearchCalibrationDriftAlertDigest
    rows: tuple[ResearchCalibrationDriftAlertRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchCalibrationDriftAlertReport, "report")
        _normalize_summary_fields(self)
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_SEQUENCE),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if type(self.digest) is not ResearchCalibrationDriftAlertDigest:
            raise ValueError("digest must be a ResearchCalibrationDriftAlertDigest")
        _validate_report(self)
        _validate_summary_counts(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _finalize_report_payload(self)


def build_research_calibration_drift_alert_report(
    observations: Iterable[object],
    *,
    config: ResearchCalibrationDriftAlertConfig,
    generated_at: datetime,
) -> ResearchCalibrationDriftAlertReport:
    if type(config) is not ResearchCalibrationDriftAlertConfig:
        raise ValueError("config must be a ResearchCalibrationDriftAlertConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.window_end_at > generated_at_utc:
            raise ValueError("window_end_at must not be after generated_at")
    rows = tuple(sorted((_row_from_observation(item, config) for item in items), key=_row_key))
    summary = _summary_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    digest = ResearchCalibrationDriftAlertDigest(**summary)
    return ResearchCalibrationDriftAlertReport(
        **summary,
        digest=digest,
        rows=rows,
    )


def research_calibration_drift_alert_report_payload(
    report: ResearchCalibrationDriftAlertReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchCalibrationDriftAlertReport:
        _require_hard_flags("report", report)
        _validate_payload_digest("report", report.payload)
        return report.payload
    if type(report) is dict:
        _validate_payload_digest("report", report)
        digest_payload = report.get("digest")
        if type(digest_payload) is not dict:
            raise ValueError("digest must be a payload object")
        _validate_payload_digest("digest", digest_payload)
        return report
    raise ValueError("report must be a ResearchCalibrationDriftAlertReport")


def research_calibration_drift_alert_digest_payload(
    digest: ResearchCalibrationDriftAlertDigest | dict[str, Any],
) -> dict[str, Any]:
    if type(digest) is ResearchCalibrationDriftAlertDigest:
        _require_hard_flags("digest", digest)
        _validate_payload_digest("digest", digest.payload)
        return digest.payload
    if type(digest) is dict:
        _validate_payload_digest("digest", digest)
        return digest
    raise ValueError("digest must be a ResearchCalibrationDriftAlertDigest")


def _row_from_observation(
    item: ResearchCalibrationDriftObservation,
    config: ResearchCalibrationDriftAlertConfig,
) -> ResearchCalibrationDriftAlertRow:
    brier_delta = _quantize(item.current_brier_score - item.baseline_brier_score)
    ece_delta = _quantize(
        item.current_expected_calibration_error
        - item.baseline_expected_calibration_error,
    )
    abs_brier_delta = _absolute_decimal(brier_delta)
    abs_ece_delta = _absolute_decimal(ece_delta)
    status, reason_codes = _row_status_and_reasons(
        item=item,
        abs_brier_delta=abs_brier_delta,
        abs_ece_delta=abs_ece_delta,
        config=config,
    )
    return ResearchCalibrationDriftAlertRow(
        cohort_key=item.cohort_key,
        window_start_at=item.window_start_at,
        window_end_at=item.window_end_at,
        settled_count=item.settled_count,
        baseline_brier_score=item.baseline_brier_score,
        current_brier_score=item.current_brier_score,
        brier_score_delta=brier_delta,
        absolute_brier_score_delta=abs_brier_delta,
        baseline_expected_calibration_error=item.baseline_expected_calibration_error,
        current_expected_calibration_error=item.current_expected_calibration_error,
        expected_calibration_error_delta=ece_delta,
        absolute_expected_calibration_error_delta=abs_ece_delta,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    *,
    item: ResearchCalibrationDriftObservation,
    abs_brier_delta: Decimal,
    abs_ece_delta: Decimal,
    config: ResearchCalibrationDriftAlertConfig,
) -> tuple[str, tuple[str, ...]]:
    reasons: list[str] = []
    if item.manual_block_flag:
        return "block", ("calibration_drift_block", "manual_review_required")
    if item.settled_count < config.min_settled_count:
        return "block", ("calibration_drift_block", "settled_count_below_minimum")

    status = "pass"
    if abs_brier_delta >= config.block_brier_score_delta:
        status = "block"
        reasons.append("brier_score_drift_block")
    elif abs_brier_delta >= config.watch_brier_score_delta:
        status = "watch"
        reasons.append("brier_score_drift_watch")

    if abs_ece_delta >= config.block_expected_calibration_error_delta:
        status = "block"
        reasons.append("expected_calibration_error_drift_block")
    elif (
        abs_ece_delta >= config.watch_expected_calibration_error_delta
        and status != "block"
    ):
        status = "watch"
        reasons.append("expected_calibration_error_drift_watch")
    elif abs_ece_delta >= config.watch_expected_calibration_error_delta:
        reasons.append("expected_calibration_error_drift_watch")

    if status == "pass":
        reasons.append("calibration_drift_pass")
    elif status == "watch":
        reasons.append("calibration_drift_watch")
    else:
        reasons.append("calibration_drift_block")
    return status, _normalize_reason_codes(tuple(reasons), _ROW_REASON_SEQUENCE)


def _summary_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchCalibrationDriftAlertRow, ...],
) -> dict[str, Any]:
    block_count = _decimal_count(sum(1 for row in rows if row.status == "block"))
    watch_count = _decimal_count(sum(1 for row in rows if row.status == "watch"))
    cohort_count = _decimal_count(len(rows))
    status = _summary_status_from_counts(
        block_count=block_count,
        watch_count=watch_count,
        cohort_count=cohort_count,
    )
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "cohort_count": cohort_count,
        "pass_count": _decimal_count(sum(1 for row in rows if row.status == "pass")),
        "watch_count": watch_count,
        "block_count": block_count,
        "average_absolute_brier_score_delta": _mean(
            tuple(row.absolute_brier_score_delta for row in rows),
        ),
        "max_absolute_brier_score_delta": _max_decimal(
            tuple(row.absolute_brier_score_delta for row in rows),
        ),
        "average_absolute_expected_calibration_error_delta": _mean(
            tuple(row.absolute_expected_calibration_error_delta for row in rows),
        ),
        "max_absolute_expected_calibration_error_delta": _max_decimal(
            tuple(row.absolute_expected_calibration_error_delta for row in rows),
        ),
        "status": status,
        "reason_codes": _report_reason_codes(
            block_count=block_count,
            watch_count=watch_count,
            cohort_count=cohort_count,
        ),
    }


def _normalize_summary_fields(
    value: ResearchCalibrationDriftAlertDigest | ResearchCalibrationDriftAlertReport,
) -> None:
    object.__setattr__(value, "generated_at", _as_utc("generated_at", value.generated_at))
    object.__setattr__(
        value,
        "config_version",
        _require_public_identifier("config_version", value.config_version),
    )
    for name in ("cohort_count", "pass_count", "watch_count", "block_count"):
        object.__setattr__(
            value,
            name,
            _require_nonnegative_count_decimal(name, getattr(value, name)),
        )
    for name in (
        "average_absolute_brier_score_delta",
        "max_absolute_brier_score_delta",
        "average_absolute_expected_calibration_error_delta",
        "max_absolute_expected_calibration_error_delta",
    ):
        object.__setattr__(
            value,
            name,
            _require_ratio_decimal(name, getattr(value, name)),
        )


def _validate_summary_counts(
    value: ResearchCalibrationDriftAlertDigest | ResearchCalibrationDriftAlertReport,
) -> None:
    if value.pass_count + value.watch_count + value.block_count != value.cohort_count:
        raise ValueError("status counts must match cohort_count")
    if value.max_absolute_brier_score_delta < value.average_absolute_brier_score_delta:
        raise ValueError("max_absolute_brier_score_delta must be at least average")
    if (
        value.max_absolute_expected_calibration_error_delta
        < value.average_absolute_expected_calibration_error_delta
    ):
        raise ValueError(
            "max_absolute_expected_calibration_error_delta must be at least average",
        )


def _validate_report(report: ResearchCalibrationDriftAlertReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_key)):
        raise ValueError("rows must be sorted by cohort key")
    if len({row.cohort_key for row in report.rows}) != len(report.rows):
        raise ValueError("rows must contain unique cohort keys")
    if report.cohort_count != _decimal_count(len(report.rows)):
        raise ValueError("cohort_count must match rows")
    if report.pass_count != _decimal_count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_absolute_brier_score_delta != _mean(
        tuple(row.absolute_brier_score_delta for row in report.rows),
    ):
        raise ValueError("average_absolute_brier_score_delta must match rows")
    if report.max_absolute_brier_score_delta != _max_decimal(
        tuple(row.absolute_brier_score_delta for row in report.rows),
    ):
        raise ValueError("max_absolute_brier_score_delta must match rows")
    if report.average_absolute_expected_calibration_error_delta != _mean(
        tuple(row.absolute_expected_calibration_error_delta for row in report.rows),
    ):
        raise ValueError(
            "average_absolute_expected_calibration_error_delta must match rows",
        )
    if report.max_absolute_expected_calibration_error_delta != _max_decimal(
        tuple(row.absolute_expected_calibration_error_delta for row in report.rows),
    ):
        raise ValueError("max_absolute_expected_calibration_error_delta must match rows")
    if report.status != _summary_status_from_counts(
        block_count=report.block_count,
        watch_count=report.watch_count,
        cohort_count=report.cohort_count,
    ):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(
        block_count=report.block_count,
        watch_count=report.watch_count,
        cohort_count=report.cohort_count,
    ):
        raise ValueError("reason_codes must match rows")
    if not _digest_matches_report(report.digest, report):
        raise ValueError("digest must match report summary")


def _validate_row(row: ResearchCalibrationDriftAlertRow) -> None:
    expected_brier_delta = _quantize(row.current_brier_score - row.baseline_brier_score)
    expected_ece_delta = _quantize(
        row.current_expected_calibration_error
        - row.baseline_expected_calibration_error,
    )
    if row.brier_score_delta != expected_brier_delta:
        raise ValueError("brier_score_delta must match scores")
    if row.expected_calibration_error_delta != expected_ece_delta:
        raise ValueError("expected_calibration_error_delta must match scores")
    if row.absolute_brier_score_delta != _absolute_decimal(row.brier_score_delta):
        raise ValueError("absolute_brier_score_delta must match brier_score_delta")
    if row.absolute_expected_calibration_error_delta != _absolute_decimal(
        row.expected_calibration_error_delta,
    ):
        raise ValueError(
            "absolute_expected_calibration_error_delta must match "
            "expected_calibration_error_delta",
        )
    if row.status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _digest_matches_report(
    digest: ResearchCalibrationDriftAlertDigest,
    report: ResearchCalibrationDriftAlertReport,
) -> bool:
    names = (
        "generated_at",
        "config_version",
        "cohort_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_absolute_brier_score_delta",
        "max_absolute_brier_score_delta",
        "average_absolute_expected_calibration_error_delta",
        "max_absolute_expected_calibration_error_delta",
        "status",
        "reason_codes",
    )
    return all(getattr(digest, name) == getattr(report, name) for name in names)


def _finalize_digest_payload(digest: ResearchCalibrationDriftAlertDigest) -> None:
    base_payload = _digest_payload_base(digest)
    expected_digest = _payload_digest(base_payload)
    supplied = digest.derived_validation_digest
    if supplied == "":
        object.__setattr__(digest, "derived_validation_digest", expected_digest)
    elif supplied != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = dict(base_payload)
    payload["derived_validation_digest"] = digest.derived_validation_digest
    _reject_unsafe_public_payload("digest.payload", payload)
    object.__setattr__(digest, "payload", payload)


def _finalize_report_payload(report: ResearchCalibrationDriftAlertReport) -> None:
    base_payload = _report_payload_base(report)
    expected_digest = _payload_digest(base_payload)
    supplied = report.derived_validation_digest
    if supplied == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
    elif supplied != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = dict(base_payload)
    payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload("report.payload", payload)
    object.__setattr__(report, "payload", payload)


def _digest_payload_base(digest: ResearchCalibrationDriftAlertDigest) -> dict[str, Any]:
    return {
        "generated_at": digest.generated_at.isoformat(),
        "config_version": digest.config_version,
        "cohort_count": _decimal_string(digest.cohort_count),
        "pass_count": _decimal_string(digest.pass_count),
        "watch_count": _decimal_string(digest.watch_count),
        "block_count": _decimal_string(digest.block_count),
        "average_absolute_brier_score_delta": _decimal_string(
            digest.average_absolute_brier_score_delta,
        ),
        "max_absolute_brier_score_delta": _decimal_string(
            digest.max_absolute_brier_score_delta,
        ),
        "average_absolute_expected_calibration_error_delta": _decimal_string(
            digest.average_absolute_expected_calibration_error_delta,
        ),
        "max_absolute_expected_calibration_error_delta": _decimal_string(
            digest.max_absolute_expected_calibration_error_delta,
        ),
        "status": digest.status,
        "reason_codes": list(digest.reason_codes),
        "paper_only": digest.paper_only,
        "report_only": digest.report_only,
        "readonly": digest.readonly,
    }


def _report_payload_base(report: ResearchCalibrationDriftAlertReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "cohort_count": _decimal_string(report.cohort_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "average_absolute_brier_score_delta": _decimal_string(
            report.average_absolute_brier_score_delta,
        ),
        "max_absolute_brier_score_delta": _decimal_string(
            report.max_absolute_brier_score_delta,
        ),
        "average_absolute_expected_calibration_error_delta": _decimal_string(
            report.average_absolute_expected_calibration_error_delta,
        ),
        "max_absolute_expected_calibration_error_delta": _decimal_string(
            report.max_absolute_expected_calibration_error_delta,
        ),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "digest": report.digest.payload,
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_payload(row: ResearchCalibrationDriftAlertRow) -> dict[str, Any]:
    return {
        "cohort_digest": _public_digest(row.cohort_key),
        "window_start_at": row.window_start_at.isoformat(),
        "window_end_at": row.window_end_at.isoformat(),
        "settled_count": _decimal_string(row.settled_count),
        "baseline_brier_score": _decimal_string(row.baseline_brier_score),
        "current_brier_score": _decimal_string(row.current_brier_score),
        "brier_score_delta": _decimal_string(row.brier_score_delta),
        "absolute_brier_score_delta": _decimal_string(row.absolute_brier_score_delta),
        "baseline_expected_calibration_error": _decimal_string(
            row.baseline_expected_calibration_error,
        ),
        "current_expected_calibration_error": _decimal_string(
            row.current_expected_calibration_error,
        ),
        "expected_calibration_error_delta": _decimal_string(
            row.expected_calibration_error_delta,
        ),
        "absolute_expected_calibration_error_delta": _decimal_string(
            row.absolute_expected_calibration_error_delta,
        ),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchCalibrationDriftObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    items = tuple(observations)
    for item in items:
        if type(item) is not ResearchCalibrationDriftObservation:
            raise ValueError(
                "observations must contain ResearchCalibrationDriftObservation values",
            )
        _require_hard_flags("observation", item)
    if len({item.cohort_key for item in items}) != len(items):
        raise ValueError("observations must contain unique cohort keys")
    return items


def _normalize_rows(
    rows: object,
) -> tuple[ResearchCalibrationDriftAlertRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    clean = tuple(rows)
    for row in clean:
        if type(row) is not ResearchCalibrationDriftAlertRow:
            raise ValueError("rows must contain ResearchCalibrationDriftAlertRow values")
        _require_hard_flags("row", row)
    return clean


def _normalize_reason_codes(
    value: object,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    clean: list[str] = []
    allowed = frozenset(allowed_sequence)
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain strings")
        code = _require_public_identifier("reason_codes", item)
        if code not in allowed:
            raise ValueError("reason_codes contains an unknown reason code")
        if code not in clean:
            clean.append(code)
    return tuple(code for code in allowed_sequence if code in clean)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "calibration_drift_block" in reason_codes:
        return "block"
    if "calibration_drift_watch" in reason_codes:
        return "watch"
    return "pass"


def _summary_status_from_counts(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    cohort_count: Decimal,
) -> str:
    if cohort_count == _ZERO or block_count > _ZERO:
        return "block"
    if watch_count > _ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    cohort_count: Decimal,
) -> tuple[str, ...]:
    if cohort_count == _ZERO:
        return ("no_calibration_drift_observations",)
    reasons: list[str] = []
    if block_count > _ZERO:
        reasons.append("calibration_drift_report_block_rows")
    if watch_count > _ZERO:
        reasons.append("calibration_drift_report_watch_rows")
    if not reasons:
        reasons.append("calibration_drift_report_pass")
    return tuple(reasons)


def _row_key(row: ResearchCalibrationDriftAlertRow) -> tuple[str, str, str]:
    return (
        row.cohort_key,
        row.window_start_at.isoformat(),
        row.window_end_at.isoformat(),
    )


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _absolute_decimal(value: Decimal) -> Decimal:
    if value < _ZERO:
        return _quantize(-value)
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if clean > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return clean


def _require_bounded_delta_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < -_ONE:
        raise ValueError(f"{field_name} must be >= -1.000000")
    if clean > _ONE:
        raise ValueError(f"{field_name} must be <= 1.000000")
    return clean


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    if clean != clean.to_integral_value():
        raise ValueError(f"{field_name} must be an integral Decimal")
    return clean


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(value)


def _decimal_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{item.name}",
                getattr(value, item.name),
            )
        return
    if type(value) is str:
        lower_value = value.lower()
        if any(term in lower_value for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("unsafe public payload")
        if not value.is_finite():
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("unsafe public payload")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("unsafe public payload")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError("unsafe public payload")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.key", key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("unsafe public payload")


def _payload_digest(payload: dict[str, Any]) -> str:
    return sha256(_canonical_payload_bytes(payload)).hexdigest()


def _canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _validate_payload_digest(label: str, payload: dict[str, Any]) -> None:
    _reject_unsafe_public_payload(label, payload)
    supplied = payload.get("derived_validation_digest")
    if type(supplied) is not str or _DIGEST_RE.fullmatch(supplied) is None:
        raise ValueError("derived_validation_digest must be a hex digest")
    base_payload = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    if _payload_digest(base_payload) != supplied:
        raise ValueError("derived_validation_digest must match payload fields")


def _public_digest(value: str) -> str:
    return "sha256:" + sha256(value.encode("utf-8")).hexdigest()[:16]
