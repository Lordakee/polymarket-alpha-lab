"""Public-safe post-settlement calibration queue report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_POST_SETTLEMENT_CALIBRATION_QUEUE_REPORT_CONFIG_VERSION",
    "POST_SETTLEMENT_CALIBRATION_QUEUE_STATUSES",
    "ResearchStrategyPostSettlementCalibrationQueueConfig",
    "ResearchStrategyPostSettlementCalibrationQueueInput",
    "ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount",
    "ResearchStrategyPostSettlementCalibrationQueueReport",
    "ResearchStrategyPostSettlementCalibrationQueueRow",
    "build_research_strategy_post_settlement_calibration_queue_report",
    "research_strategy_post_settlement_calibration_queue_report_payload",
)


DEFAULT_RESEARCH_STRATEGY_POST_SETTLEMENT_CALIBRATION_QUEUE_REPORT_CONFIG_VERSION = (
    "research-strategy-post-settlement-calibration-queue-report-v1"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FEEDBACK_READY_PASS = Decimal("0.800000")
FEEDBACK_READY_WATCH = Decimal("0.500000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
DOMAIN_TEAMS = ("macro", "sports", "crypto", "politics", "equities", "other")
FEEDBACK_BUCKETS = (
    "settled_accuracy",
    "late_resolution",
    "source_trace",
    "operator_review",
    "other",
)
POST_SETTLEMENT_CALIBRATION_QUEUE_STATUSES = ("pass", "watch", "block")
STATUS_WEIGHT = {
    "block": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
QUEUE_MODE_BY_STATUS = {
    "pass": "paper_calibration_monitor_only",
    "watch": "paper_calibration_queue_watch",
    "block": "paper_calibration_queue_block",
}
ROW_REASON_PRIORITY = (
    "resolved_event_feedback_thin_block",
    "feedback_readiness_low_block",
    "calibration_error_pressure_high_block",
    "source_provenance_quality_low_block",
    "domain_team_feedback_stale_block",
    "resolved_event_feedback_thin_watch",
    "feedback_readiness_thin_watch",
    "calibration_error_pressure_elevated_watch",
    "source_provenance_quality_thin_watch",
    "domain_team_feedback_stale_watch",
    "post_settlement_calibration_queue_clear",
)
REPORT_REASON_PRIORITY = (
    "resolved_event_feedback_thin_block",
    "feedback_readiness_low_block",
    "calibration_error_pressure_high_block",
    "source_provenance_quality_low_block",
    "domain_team_feedback_stale_block",
    "resolved_event_feedback_thin_watch",
    "feedback_readiness_thin_watch",
    "calibration_error_pressure_elevated_watch",
    "source_provenance_quality_thin_watch",
    "domain_team_feedback_stale_watch",
)
HEX_CHARS = frozenset("0123456789abcdef")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("cand", "idate"),
    _join_parts("mar", "ket"),
    "slug",
    _join_parts("ques", "tion"),
    _join_parts("u", "rl"),
    _join_parts("source", "_text"),
    _join_parts("data", "base"),
    _join_parts("d", "sn"),
    _join_parts("ta", "ble"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("ord", "er"),
    _join_parts("tra", "de"),
    _join_parts("b", "uy"),
    _join_parts("s", "ell"),
    _join_parts("li", "ve"),
    _join_parts("exec", "ution"),
    "private_key",
    "credential",
    "secret",
    "://",
    "?",
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
class ResearchStrategyPostSettlementCalibrationQueueConfig(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_POST_SETTLEMENT_CALIBRATION_QUEUE_REPORT_CONFIG_VERSION
    )
    min_pass_resolved_event_count: Decimal = Decimal("8.000000")
    min_watch_resolved_event_count: Decimal = Decimal("3.000000")
    max_pass_calibration_error: Decimal = Decimal("0.060000")
    max_watch_calibration_error: Decimal = Decimal("0.140000")
    min_pass_source_provenance_quality: Decimal = Decimal("0.800000")
    min_watch_source_provenance_quality: Decimal = Decimal("0.550000")
    max_pass_team_feedback_age_seconds: Decimal = Decimal("86400.000000")
    max_watch_team_feedback_age_seconds: Decimal = Decimal("604800.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyPostSettlementCalibrationQueueConfig,
            "config",
        )
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_POST_SETTLEMENT_CALIBRATION_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "min_pass_resolved_event_count",
            "min_watch_resolved_event_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_calibration_error",
            "max_watch_calibration_error",
            "min_pass_source_provenance_quality",
            "min_watch_source_provenance_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_team_feedback_age_seconds",
            "max_watch_team_feedback_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.min_watch_resolved_event_count > self.min_pass_resolved_event_count:
            raise ValueError("watch resolved-event threshold must not exceed pass threshold")
        if self.max_pass_calibration_error > self.max_watch_calibration_error:
            raise ValueError("pass calibration threshold must not exceed watch threshold")
        if (
            self.min_watch_source_provenance_quality
            > self.min_pass_source_provenance_quality
        ):
            raise ValueError("watch provenance threshold must not exceed pass threshold")
        if (
            self.max_pass_team_feedback_age_seconds
            > self.max_watch_team_feedback_age_seconds
        ):
            raise ValueError("pass feedback age threshold must not exceed watch threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyPostSettlementCalibrationQueueInput(_FinalPublicDataclass):
    domain_team: str
    feedback_bucket: str
    resolved_event_count: Decimal
    feedback_ready_ratio: Decimal
    calibration_error: Decimal
    source_provenance_quality: Decimal
    team_feedback_age_seconds: Decimal
    observed_at: datetime
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyPostSettlementCalibrationQueueInput,
            "input",
        )
        _require_domain_team("domain_team", self.domain_team)
        _require_feedback_bucket("feedback_bucket", self.feedback_bucket)
        object.__setattr__(
            self,
            "resolved_event_count",
            _require_count_decimal("resolved_event_count", self.resolved_event_count),
        )
        for field_name in (
            "feedback_ready_ratio",
            "calibration_error",
            "source_provenance_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_feedback_age_seconds",
            _require_nonnegative_decimal(
                "team_feedback_age_seconds",
                self.team_feedback_age_seconds,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyPostSettlementCalibrationQueueRow(_FinalPublicDataclass):
    domain_team: str
    feedback_bucket: str
    queue_status: str
    resolved_event_count: Decimal
    feedback_ready_ratio: Decimal
    calibration_error: Decimal
    source_provenance_quality: Decimal
    team_feedback_age_seconds: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyPostSettlementCalibrationQueueRow,
            "row",
        )
        _require_domain_team("domain_team", self.domain_team)
        _require_feedback_bucket("feedback_bucket", self.feedback_bucket)
        _require_status("queue_status", self.queue_status)
        object.__setattr__(
            self,
            "resolved_event_count",
            _require_count_decimal("resolved_event_count", self.resolved_event_count),
        )
        for field_name in (
            "feedback_ready_ratio",
            "calibration_error",
            "source_provenance_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "team_feedback_age_seconds",
            _require_nonnegative_decimal(
                "team_feedback_age_seconds",
                self.team_feedback_age_seconds,
            ),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount(
    _FinalPublicDataclass,
):
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        if self.reason_code.lower() != self.reason_code:
            raise ValueError("reason_code must be lowercase")
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyPostSettlementCalibrationQueueReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    calibration_queue_task_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    task_ratio: Decimal
    min_resolved_event_count: Decimal
    average_feedback_ready_ratio: Decimal
    max_calibration_error: Decimal
    min_source_provenance_quality: Decimal
    max_team_feedback_age_seconds: Decimal
    status: str
    queue_mode: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount,
        ...
    ]
    rows: tuple[ResearchStrategyPostSettlementCalibrationQueueRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchStrategyPostSettlementCalibrationQueueReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_STRATEGY_POST_SETTLEMENT_CALIBRATION_QUEUE_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "calibration_queue_task_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "task_ratio",
            "average_feedback_ready_ratio",
            "max_calibration_error",
            "min_source_provenance_quality",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_resolved_event_count",
            _require_count_decimal(
                "min_resolved_event_count",
                self.min_resolved_event_count,
            ),
        )
        object.__setattr__(
            self,
            "max_team_feedback_age_seconds",
            _require_nonnegative_decimal(
                "max_team_feedback_age_seconds",
                self.max_team_feedback_age_seconds,
            ),
        )
        _require_status("status", self.status)
        _require_public_string("queue_mode", self.queue_mode)
        if self.queue_mode != QUEUE_MODE_BY_STATUS[self.status]:
            raise ValueError("queue_mode must match status")
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
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _validate_report_status(self)
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
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_research_strategy_post_settlement_calibration_queue_report(
    inputs: Iterable[ResearchStrategyPostSettlementCalibrationQueueInput],
    *,
    config: ResearchStrategyPostSettlementCalibrationQueueConfig,
    generated_at: datetime,
) -> ResearchStrategyPostSettlementCalibrationQueueReport:
    if type(config) is not ResearchStrategyPostSettlementCalibrationQueueConfig:
        raise ValueError(
            "config must be a ResearchStrategyPostSettlementCalibrationQueueConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.queue_status for row in rows))
    task_count = _count(sum(1 for row in rows if row.queue_status != "pass"))
    input_count = _count(len(rows))
    return ResearchStrategyPostSettlementCalibrationQueueReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=input_count,
        calibration_queue_task_count=task_count,
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        task_ratio=_ratio(task_count, input_count),
        min_resolved_event_count=_min_decimal(
            tuple(row.resolved_event_count for row in rows),
        ),
        average_feedback_ready_ratio=_ratio(
            _sum_decimal(tuple(row.feedback_ready_ratio for row in rows)),
            input_count,
        ),
        max_calibration_error=_max_decimal(tuple(row.calibration_error for row in rows)),
        min_source_provenance_quality=_min_decimal(
            tuple(row.source_provenance_quality for row in rows),
        ),
        max_team_feedback_age_seconds=_max_decimal(
            tuple(row.team_feedback_age_seconds for row in rows),
        ),
        status=status,
        queue_mode=QUEUE_MODE_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_strategy_post_settlement_calibration_queue_report_payload(
    report: ResearchStrategyPostSettlementCalibrationQueueReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyPostSettlementCalibrationQueueReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError(
        "report must be a ResearchStrategyPostSettlementCalibrationQueueReport",
    )


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


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyPostSettlementCalibrationQueueInput],
) -> tuple[ResearchStrategyPostSettlementCalibrationQueueInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for item in normalized:
        if type(item) is not ResearchStrategyPostSettlementCalibrationQueueInput:
            raise ValueError(
                "inputs must contain ResearchStrategyPostSettlementCalibrationQueueInput",
            )
        _require_hard_flags("input", item)
        key = (item.domain_team, item.feedback_bucket)
        if key in seen:
            raise ValueError("domain_team and feedback_bucket pairs must be unique")
        seen.add(key)
    return normalized


def _row_from_input(
    item: ResearchStrategyPostSettlementCalibrationQueueInput,
    *,
    config: ResearchStrategyPostSettlementCalibrationQueueConfig,
    generated_at: datetime,
) -> ResearchStrategyPostSettlementCalibrationQueueRow:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    reason_codes = _row_reason_codes(item, config=config)
    return ResearchStrategyPostSettlementCalibrationQueueRow(
        domain_team=item.domain_team,
        feedback_bucket=item.feedback_bucket,
        queue_status=_row_status(reason_codes),
        resolved_event_count=item.resolved_event_count,
        feedback_ready_ratio=item.feedback_ready_ratio,
        calibration_error=item.calibration_error,
        source_provenance_quality=item.source_provenance_quality,
        team_feedback_age_seconds=item.team_feedback_age_seconds,
        observed_at=item.observed_at,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchStrategyPostSettlementCalibrationQueueInput,
    *,
    config: ResearchStrategyPostSettlementCalibrationQueueConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if item.resolved_event_count < config.min_watch_resolved_event_count:
        reasons.append("resolved_event_feedback_thin_block")
    elif item.resolved_event_count < config.min_pass_resolved_event_count:
        reasons.append("resolved_event_feedback_thin_watch")

    if item.feedback_ready_ratio < FEEDBACK_READY_WATCH:
        reasons.append("feedback_readiness_low_block")
    elif item.feedback_ready_ratio < FEEDBACK_READY_PASS:
        reasons.append("feedback_readiness_thin_watch")

    if item.calibration_error > config.max_watch_calibration_error:
        reasons.append("calibration_error_pressure_high_block")
    elif item.calibration_error > config.max_pass_calibration_error:
        reasons.append("calibration_error_pressure_elevated_watch")

    if item.source_provenance_quality < config.min_watch_source_provenance_quality:
        reasons.append("source_provenance_quality_low_block")
    elif item.source_provenance_quality < config.min_pass_source_provenance_quality:
        reasons.append("source_provenance_quality_thin_watch")

    if item.team_feedback_age_seconds > config.max_watch_team_feedback_age_seconds:
        reasons.append("domain_team_feedback_stale_block")
    elif item.team_feedback_age_seconds > config.max_pass_team_feedback_age_seconds:
        reasons.append("domain_team_feedback_stale_watch")

    if not reasons:
        reasons.append("post_settlement_calibration_queue_clear")
    return _require_reason_codes(tuple(reasons), require_nonempty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_block") for reason_code in reason_codes):
        return "block"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "block" for status in statuses):
        return "block"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyPostSettlementCalibrationQueueRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("post_settlement_calibration_queue_empty",)
    status = _rollup_status(tuple(row.queue_status for row in rows))
    reason_codes = [
        f"post_settlement_calibration_queue_{'clear' if status == 'pass' else status}",
    ]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code != "post_settlement_calibration_queue_clear"
    )
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[ResearchStrategyPostSettlementCalibrationQueueRow, ...],
) -> tuple[ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount(
            reason_code=reason_code,
            count=count,
            row_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], _reason_priority_index(item[1]), item[1]),
        )
    )


def _row_sort_key(
    row: ResearchStrategyPostSettlementCalibrationQueueRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, Decimal, Decimal, str, str]:
    return (
        -STATUS_WEIGHT[row.queue_status],
        -_count(len(row.reason_codes)),
        row.resolved_event_count,
        row.feedback_ready_ratio,
        -row.calibration_error,
        row.source_provenance_quality,
        row.domain_team,
        row.feedback_bucket,
    )


def _status_count(
    rows: tuple[ResearchStrategyPostSettlementCalibrationQueueRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.queue_status == status))


def _validate_row(row: ResearchStrategyPostSettlementCalibrationQueueRow) -> None:
    if row.queue_status != _row_status(row.reason_codes):
        raise ValueError("queue_status must match reason_codes")


def _validate_report_status(
    report: ResearchStrategyPostSettlementCalibrationQueueReport,
) -> None:
    expected_status = _rollup_status(tuple(row.queue_status for row in report.rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.queue_mode != QUEUE_MODE_BY_STATUS[report.status]:
        raise ValueError("queue_mode must match status")


def _validate_report_materialized_fields(
    report: ResearchStrategyPostSettlementCalibrationQueueReport,
) -> None:
    rows = report.rows
    input_count = _count(len(rows))
    task_count = _count(sum(1 for row in rows if row.queue_status != "pass"))
    checks = {
        "input_count": input_count,
        "calibration_queue_task_count": task_count,
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "task_ratio": _ratio(task_count, input_count),
        "min_resolved_event_count": _min_decimal(
            tuple(row.resolved_event_count for row in rows),
        ),
        "average_feedback_ready_ratio": _ratio(
            _sum_decimal(tuple(row.feedback_ready_ratio for row in rows)),
            input_count,
        ),
        "max_calibration_error": _max_decimal(
            tuple(row.calibration_error for row in rows),
        ),
        "min_source_provenance_quality": _min_decimal(
            tuple(row.source_provenance_quality for row in rows),
        ),
        "max_team_feedback_age_seconds": _max_decimal(
            tuple(row.team_feedback_age_seconds for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[ResearchStrategyPostSettlementCalibrationQueueRow, ...],
) -> tuple[ResearchStrategyPostSettlementCalibrationQueueRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyPostSettlementCalibrationQueueRow:
            raise ValueError(
                "rows must contain ResearchStrategyPostSettlementCalibrationQueueRow",
            )
        _require_hard_flags("row", row)
        key = (row.domain_team, row.feedback_bucket)
        if key in seen:
            raise ValueError("rows domain_team and feedback_bucket pairs must be unique")
        seen.add(key)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status and calibration pressure")
    return normalized


def _require_reason_code_counts(
    rows: tuple[
        ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount,
        ...
    ],
) -> tuple[ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyPostSettlementCalibrationQueueReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if normalized != tuple(
        sorted(
            normalized,
            key=lambda item: (
                -item.count,
                _reason_priority_index(item.reason_code),
                item.reason_code,
            ),
        ),
    ):
        raise ValueError("reason_code_counts must be sorted by count and reason_code")
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_domain_team(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in DOMAIN_TEAMS:
        raise ValueError(f"{field_name} must be a supported domain_team")


def _require_feedback_bucket(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if value not in FEEDBACK_BUCKETS:
        raise ValueError(f"{field_name} must be a supported feedback_bucket")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code.lower() != reason_code:
            raise ValueError("reason_code must be lowercase")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(sorted(normalized, key=_reason_priority_index))


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _require_reason_codes(reason_codes, require_nonempty=True)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (
                0 if reason_code.startswith("post_settlement_calibration_queue_") else 1,
                _reason_priority_index(reason_code),
                reason_code,
            ),
        ),
    )


def _reason_priority_index(reason_code: str) -> int:
    if reason_code in ROW_REASON_PRIORITY:
        return ROW_REASON_PRIORITY.index(reason_code)
    return len(ROW_REASON_PRIORITY)


def _require_status(field_name: str, value: object) -> None:
    if value not in POST_SETTLEMENT_CALIBRATION_QUEUE_STATUSES:
        raise ValueError(
            f"{field_name} must be one of {POST_SETTLEMENT_CALIBRATION_QUEUE_STATUSES}",
        )


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is Decimal:
        return _require_count_decimal("count", value)
    if type(value) is not int or value < 0:
        raise ValueError("count value must be a non-negative integer")
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _sum_decimal(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _derived_validation_digest(
    report: ResearchStrategyPostSettlementCalibrationQueueReport,
) -> str:
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(f"{label} key", key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")
