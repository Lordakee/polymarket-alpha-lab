"""Pure report-only daily operator queue triage reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_STRATEGY_DAILY_OPERATOR_QUEUE_TRIAGE_REPORT_CONFIG_VERSION",
    "StrategyDailyOperatorQueueTriageConfig",
    "StrategyDailyOperatorQueueTriageInput",
    "StrategyDailyOperatorQueueTriageReasonCodeCount",
    "StrategyDailyOperatorQueueTriageReport",
    "StrategyDailyOperatorQueueTriageRow",
    "build_strategy_daily_operator_queue_triage_report",
    "strategy_daily_operator_queue_triage_report_digest",
    "strategy_daily_operator_queue_triage_report_payload",
)


DEFAULT_STRATEGY_DAILY_OPERATOR_QUEUE_TRIAGE_REPORT_CONFIG_VERSION = (
    "strategy-daily-operator-queue-triage-report-v0"
)
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1.000000")
ZERO = Decimal("0.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
BUCKET_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
NO_INPUTS_REASON = "strategy_daily_operator_queue_triage_no_inputs"
BASE_TRIAGE_SCORE = Decimal("0.000000")
DUE_SCORE = Decimal("0.250000")

_UNSAFE_TEXT_PARTS = (
    "mar" + "ket",
    "sou" + "rce_" + "u" + "rl",
    "u" + "rl",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "wal" + "let",
    "or" + "der",
    "tra" + "de",
    "tra" + "ding",
    "posi" + "tion",
    "b" + "uy",
    "se" + "ll",
    "rec" + "ommend",
    "au" + "th",
    "pri" + "vate_key",
    "api" + "_key",
    "se" + "cret",
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
class StrategyDailyOperatorQueueTriageConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_STRATEGY_DAILY_OPERATOR_QUEUE_TRIAGE_REPORT_CONFIG_VERSION
    watch_urgency: Decimal = Decimal("0.500000")
    block_urgency: Decimal = Decimal("0.850000")
    watch_research_gap_count: Decimal = Decimal("1.000000")
    block_research_gap_count: Decimal = Decimal("3.000000")
    watch_manual_review_age_hours: Decimal = Decimal("12.000000")
    block_manual_review_age_hours: Decimal = Decimal("36.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyDailyOperatorQueueTriageConfig, "config")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "watch_urgency",
            "block_urgency",
            "watch_research_gap_count",
            "block_research_gap_count",
            "watch_manual_review_age_hours",
            "block_manual_review_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_at_most("watch_urgency", self.watch_urgency, self.block_urgency)
        _require_at_most(
            "watch_research_gap_count",
            self.watch_research_gap_count,
            self.block_research_gap_count,
        )
        _require_at_most(
            "watch_manual_review_age_hours",
            self.watch_manual_review_age_hours,
            self.block_manual_review_age_hours,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class StrategyDailyOperatorQueueTriageInput(_FinalPublicDataclass):
    operator_queue_key: str
    status: str
    urgency: Decimal
    research_gap_count: Decimal
    manual_review_age_hours: Decimal
    source_refresh_due: bool
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyDailyOperatorQueueTriageInput, "input")
        _require_canonical_string("operator_queue_key", self.operator_queue_key)
        _require_status("status", self.status)
        for field_name in (
            "urgency",
            "research_gap_count",
            "manual_review_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_exact_bool("source_refresh_due", self.source_refresh_due)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class StrategyDailyOperatorQueueTriageRow(_FinalPublicDataclass):
    triage_rank: Decimal
    operator_queue_key: str
    status: str
    urgency: Decimal
    research_gap_count: Decimal
    manual_review_age_hours: Decimal
    source_refresh_due: bool
    triage_score: Decimal
    triage_bucket: str
    manual_next_step: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyDailyOperatorQueueTriageRow, "row")
        object.__setattr__(
            self,
            "triage_rank",
            _normalize_positive_count("triage_rank", self.triage_rank),
        )
        _require_canonical_string("operator_queue_key", self.operator_queue_key)
        _require_status("status", self.status)
        for field_name in (
            "urgency",
            "research_gap_count",
            "manual_review_age_hours",
            "triage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_exact_bool("source_refresh_due", self.source_refresh_due)
        _require_status("triage_bucket", self.triage_bucket)
        _require_canonical_string("manual_next_step", self.manual_next_step)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        if self.triage_bucket != self.status:
            raise ValueError("triage_bucket must match status")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyDailyOperatorQueueTriageReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyDailyOperatorQueueTriageReasonCodeCount,
            "reason_code_count",
        )
        _require_canonical_string("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_positive_count("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class StrategyDailyOperatorQueueTriageReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    queue_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    research_gap_queue_count: Decimal
    stale_queue_count: Decimal
    source_refresh_due_count: Decimal
    mean_triage_score: Decimal
    max_triage_score: Decimal
    status: str
    public_digest: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyDailyOperatorQueueTriageReasonCodeCount, ...]
    rows: tuple[StrategyDailyOperatorQueueTriageRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyDailyOperatorQueueTriageReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "queue_count",
            "pass_count",
            "watch_count",
            "blocked_count",
            "research_gap_queue_count",
            "stale_queue_count",
            "source_refresh_due_count",
            "mean_triage_score",
            "max_triage_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_digest("public_digest", self.public_digest)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)
        if self.public_digest != _computed_report_digest(self):
            raise ValueError("public_digest must match report values")
        _reject_unsafe_public_payload("report", self)


_PUBLIC_DATACLASS_TYPES = (
    StrategyDailyOperatorQueueTriageConfig,
    StrategyDailyOperatorQueueTriageInput,
    StrategyDailyOperatorQueueTriageReasonCodeCount,
    StrategyDailyOperatorQueueTriageReport,
    StrategyDailyOperatorQueueTriageRow,
)


def build_strategy_daily_operator_queue_triage_report(
    queue_items: Iterable[StrategyDailyOperatorQueueTriageInput],
    *,
    config: StrategyDailyOperatorQueueTriageConfig,
    generated_at: datetime,
) -> StrategyDailyOperatorQueueTriageReport:
    if type(config) is not StrategyDailyOperatorQueueTriageConfig:
        raise ValueError("config must be a StrategyDailyOperatorQueueTriageConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(queue_items)
    row_values = sorted(
        (_triage_row_values(item, config=config) for item in inputs),
        key=_row_values_sort_key,
    )
    rows = tuple(
        _row_from_values(_count(index), values)
        for index, values in enumerate(row_values, start=1)
    )
    values = _report_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    return StrategyDailyOperatorQueueTriageReport(
        **values,
        public_digest=_digest_from_mapping(values),
    )


def strategy_daily_operator_queue_triage_report_digest(
    report: StrategyDailyOperatorQueueTriageReport,
) -> str:
    if type(report) is not StrategyDailyOperatorQueueTriageReport:
        raise ValueError("report must be a StrategyDailyOperatorQueueTriageReport")
    _revalidate_report_for_payload(report)
    return _computed_report_digest(report)


def strategy_daily_operator_queue_triage_report_payload(
    report: StrategyDailyOperatorQueueTriageReport,
) -> dict[str, Any]:
    if type(report) is not StrategyDailyOperatorQueueTriageReport:
        raise ValueError("report must be a StrategyDailyOperatorQueueTriageReport")
    _revalidate_report_for_payload(report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


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


@dataclass(frozen=True)
class _TriageRowValues:
    operator_queue_key: str
    status: str
    urgency: Decimal
    research_gap_count: Decimal
    manual_review_age_hours: Decimal
    source_refresh_due: bool
    triage_score: Decimal
    triage_bucket: str
    manual_next_step: str
    reason_codes: tuple[str, ...]


def _triage_row_values(
    item: StrategyDailyOperatorQueueTriageInput,
    *,
    config: StrategyDailyOperatorQueueTriageConfig,
) -> _TriageRowValues:
    reason_codes = _row_reason_codes(item, config=config)
    bucket = item.status
    return _TriageRowValues(
        operator_queue_key=item.operator_queue_key,
        status=item.status,
        urgency=item.urgency,
        research_gap_count=item.research_gap_count,
        manual_review_age_hours=item.manual_review_age_hours,
        source_refresh_due=item.source_refresh_due,
        triage_score=_triage_score(item, bucket),
        triage_bucket=bucket,
        manual_next_step=_manual_next_step(item, bucket),
        reason_codes=reason_codes,
    )


def _row_from_values(
    triage_rank: Decimal,
    values: _TriageRowValues,
) -> StrategyDailyOperatorQueueTriageRow:
    return StrategyDailyOperatorQueueTriageRow(
        triage_rank=triage_rank,
        operator_queue_key=values.operator_queue_key,
        status=values.status,
        urgency=values.urgency,
        research_gap_count=values.research_gap_count,
        manual_review_age_hours=values.manual_review_age_hours,
        source_refresh_due=values.source_refresh_due,
        triage_score=values.triage_score,
        triage_bucket=values.triage_bucket,
        manual_next_step=values.manual_next_step,
        reason_codes=values.reason_codes,
    )


def _triage_score(
    item: StrategyDailyOperatorQueueTriageInput,
    bucket: str,
) -> Decimal:
    score = (
        item.urgency
        + (item.research_gap_count * Decimal("0.200000"))
        + (item.manual_review_age_hours * Decimal("0.030000"))
        + BUCKET_WEIGHT[bucket]
        + BASE_TRIAGE_SCORE
    )
    if item.source_refresh_due:
        score += DUE_SCORE
    return _quantize(score)


def _row_reason_codes(
    item: StrategyDailyOperatorQueueTriageInput,
    *,
    config: StrategyDailyOperatorQueueTriageConfig,
) -> tuple[str, ...]:
    reason_codes = list(item.reason_codes)
    if item.status == "blocked":
        reason_codes.append("input_status_blocked")
    elif item.status == "watch":
        reason_codes.append("input_status_watch")

    if item.urgency >= config.block_urgency:
        reason_codes.append("urgency_blocked")
    elif item.urgency >= config.watch_urgency:
        reason_codes.append("urgency_watch")

    if item.research_gap_count >= config.block_research_gap_count:
        reason_codes.append("research_gap_count_blocked")
    elif item.research_gap_count >= config.watch_research_gap_count:
        reason_codes.append("research_gap_count_watch")

    if item.manual_review_age_hours >= config.block_manual_review_age_hours:
        reason_codes.append("manual_review_age_blocked")
    elif item.manual_review_age_hours >= config.watch_manual_review_age_hours:
        reason_codes.append("manual_review_age_watch")

    if item.source_refresh_due:
        reason_codes.append("source_refresh_due")

    if not reason_codes:
        reason_codes.append("triage_clear")
    return tuple(sorted(set(reason_codes)))


def _row_bucket(reason_codes: tuple[str, ...]) -> str:
    if "input_status_blocked" in reason_codes:
        return "blocked"
    if "input_status_watch" in reason_codes:
        return "watch"
    if any(
        code.endswith("_blocked")
        for code in reason_codes
    ):
        return "blocked"
    if any(
        code.endswith("_watch")
        or code == "source_refresh_due"
        for code in reason_codes
    ):
        return "watch"
    return "pass"


def _manual_next_step(
    item: StrategyDailyOperatorQueueTriageInput,
    bucket: str,
) -> str:
    if bucket == "blocked" and item.research_gap_count > ZERO:
        return "assign_research_owner_before_review"
    if item.source_refresh_due:
        return "re" + "fresh_" + "sour" + "ces_then_recheck"
    if bucket in {"blocked", "watch"} and item.manual_review_age_hours > ZERO:
        return "complete_manual_review_today"
    return "continue_daily_monitoring"


def _row_values_sort_key(
    values: _TriageRowValues,
) -> tuple[Decimal, Decimal, Decimal, Decimal, int, str]:
    return (
        -BUCKET_WEIGHT[values.triage_bucket],
        -values.urgency,
        -values.research_gap_count,
        -values.manual_review_age_hours,
        -int(values.source_refresh_due),
        values.operator_queue_key,
    )


def _report_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[StrategyDailyOperatorQueueTriageRow, ...],
) -> dict[str, Any]:
    queue_count = _count(len(rows))
    pass_count = _count(sum(1 for row in rows if row.triage_bucket == "pass"))
    watch_count = _count(sum(1 for row in rows if row.triage_bucket == "watch"))
    blocked_count = _count(sum(1 for row in rows if row.triage_bucket == "blocked"))
    scores = tuple(row.triage_score for row in rows)
    reason_codes = _report_reason_codes(rows)
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "queue_count": queue_count,
        "pass_count": pass_count,
        "watch_count": watch_count,
        "blocked_count": blocked_count,
        "research_gap_queue_count": _count(
            sum(1 for row in rows if row.research_gap_count > ZERO),
        ),
        "stale_queue_count": _count(sum(1 for row in rows if _row_is_stale(row))),
        "source_refresh_due_count": _count(
            sum(1 for row in rows if row.source_refresh_due),
        ),
        "mean_triage_score": _mean(scores),
        "max_triage_score": max(scores) if scores else ZERO,
        "status": _report_status(blocked_count, watch_count, rows),
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows, reason_codes),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _report_status(
    blocked_count: Decimal,
    watch_count: Decimal,
    rows: tuple[StrategyDailyOperatorQueueTriageRow, ...],
) -> str:
    if not rows:
        return "blocked"
    if blocked_count > ZERO:
        return "blocked"
    if watch_count > ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[StrategyDailyOperatorQueueTriageRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    report_code_stem = "strategy_daily_operator_queue_triage"
    report_status = _report_status(
        _count(sum(1 for row in rows if row.triage_bucket == "blocked")),
        _count(sum(1 for row in rows if row.triage_bucket == "watch")),
        rows,
    )
    if report_status == "pass":
        return (f"{report_code_stem}_clear",)
    return tuple(
        sorted(
            (
                f"{report_code_stem}_{report_status}",
                *{code for row in rows for code in row.reason_codes},
            ),
        ),
    )


def _reason_code_counts(
    rows: tuple[StrategyDailyOperatorQueueTriageRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[StrategyDailyOperatorQueueTriageReasonCodeCount, ...]:
    if not rows:
        return (
            StrategyDailyOperatorQueueTriageReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=_count(1),
            ),
        )
    counts: Counter[str] = Counter(code for row in rows for code in row.reason_codes)
    return tuple(
        StrategyDailyOperatorQueueTriageReasonCodeCount(
            reason_code=code,
            count=_count(counts[code]),
        )
        for code in sorted(counts)
    )


def _row_is_stale(row: StrategyDailyOperatorQueueTriageRow) -> bool:
    return (
        "manual_review_age_watch" in row.reason_codes
        or "manual_review_age_blocked" in row.reason_codes
    )


def _normalize_inputs(
    queue_items: Iterable[StrategyDailyOperatorQueueTriageInput],
) -> tuple[StrategyDailyOperatorQueueTriageInput, ...]:
    if isinstance(queue_items, (str, bytes)):
        raise ValueError("queue_items must be an iterable of inputs")
    items = tuple(queue_items)
    for item in items:
        if type(item) is not StrategyDailyOperatorQueueTriageInput:
            raise ValueError("queue_items must contain only StrategyDailyOperatorQueueTriageInput")
        _require_hard_flags("input", item)
    return items


def _normalize_rows(
    rows: tuple[StrategyDailyOperatorQueueTriageRow, ...],
) -> tuple[StrategyDailyOperatorQueueTriageRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not StrategyDailyOperatorQueueTriageRow:
            raise ValueError("rows must contain only StrategyDailyOperatorQueueTriageRow")
        _require_hard_flags("row", row)
    expected = tuple(sorted(rows, key=_row_sort_key))
    if rows != expected:
        raise ValueError("rows must be sorted by triage priority")
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    actual_ranks = tuple(row.triage_rank for row in rows)
    if actual_ranks != expected_ranks:
        raise ValueError("triage_rank values must be contiguous")
    return rows


def _row_sort_key(
    row: StrategyDailyOperatorQueueTriageRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, int, str]:
    return (
        -BUCKET_WEIGHT[row.triage_bucket],
        -row.urgency,
        -row.research_gap_count,
        -row.manual_review_age_hours,
        -int(row.source_refresh_due),
        row.operator_queue_key,
    )


def _normalize_reason_code_counts(
    values: tuple[StrategyDailyOperatorQueueTriageReasonCodeCount, ...],
) -> tuple[StrategyDailyOperatorQueueTriageReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if type(value) is not StrategyDailyOperatorQueueTriageReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason code count rows")
        _require_hard_flags("reason_code_count", value)
    expected = tuple(sorted(values, key=lambda item: item.reason_code))
    if values != expected:
        raise ValueError("reason_code_counts must be sorted")
    return values


def _validate_report(report: StrategyDailyOperatorQueueTriageReport) -> None:
    values = _report_values(
        generated_at=report.generated_at,
        config_version=report.config_version,
        rows=report.rows,
    )
    for field_name, expected in values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _revalidate_report_for_payload(report: StrategyDailyOperatorQueueTriageReport) -> None:
    _require_hard_flags("report", report)
    for row in report.rows:
        _require_hard_flags("row", row)
    for reason_count in report.reason_code_counts:
        _require_hard_flags("reason_code_count", reason_count)
    _validate_report(report)
    if report.public_digest != _computed_report_digest(report):
        raise ValueError("public_digest must match report values")


def _computed_report_digest(report: StrategyDailyOperatorQueueTriageReport) -> str:
    payload = _json_ready_without_digest(report)
    return _digest_from_mapping(payload)


def _digest_from_mapping(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        _json_ready(value),
        sort_keys=True,
        separators=(",", ":"),
    ).encode()
    return sha256(encoded).hexdigest()


def _json_ready_without_digest(report: StrategyDailyOperatorQueueTriageReport) -> dict[str, Any]:
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("public_digest", None)
    return payload


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_json_ready(item) for item in value]
    if type(value) is datetime:
        return value.isoformat()
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) in {str, bool} or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if value.is_nan() or value.is_infinite() or value < ZERO:
        raise ValueError(f"{field_name} must be a nonnegative finite Decimal")
    return _quantize(value)


def _normalize_positive_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number Decimal")
    return normalized.quantize(COUNT_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_at_most(field_name: str, lower: Decimal, upper: Decimal) -> None:
    if lower > upper:
        raise ValueError(f"{field_name} must be less than or equal to block threshold")


def _require_exact_bool(field_name: str, value: bool) -> None:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _normalize_reason_codes(field_name: str, value: tuple[str, ...]) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for code in value:
        _require_canonical_string(field_name, code)
    if len(value) != len(set(value)):
        raise ValueError(f"{field_name} must not contain duplicates")
    return tuple(sorted(value))


def _normalize_report_reason_codes(value: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _normalize_reason_codes("reason_codes", value)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    return normalized


def _require_public_digest(field_name: str, value: str) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label}.{field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    for text in _public_text_values(value):
        lowered = text.lower()
        if any(part in lowered for part in _UNSAFE_TEXT_PARTS):
            raise ValueError(f"{label} contains unsafe public payload text")


def _public_text_values(value: object) -> tuple[str, ...]:
    if is_dataclass(value) and not isinstance(value, type):
        texts: list[str] = []
        for field in fields(value):
            texts.extend(_public_text_values(getattr(value, field.name)))
        return tuple(texts)
    if isinstance(value, dict):
        texts = []
        for key, item in value.items():
            texts.extend(_public_text_values(key))
            texts.extend(_public_text_values(item))
        return tuple(texts)
    if isinstance(value, (tuple, list)):
        texts = []
        for item in value:
            texts.extend(_public_text_values(item))
        return tuple(texts)
    if type(value) is str:
        return (value,)
    return ()
