"""Pure report-only macro asset signal matrix reducer."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any, Iterable


DEFAULT_RESEARCH_MACRO_ASSET_SIGNAL_MATRIX_CONFIG_VERSION = (
    "research-macro-asset-signal-matrix-v0"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    PASS_STATUS: Decimal("2.000000"),
}

HUMAN_RESEARCH_FOCUS = {
    PASS_STATUS: "log_macro_asset_signal_matrix_pass",
    WATCH_STATUS: "review_macro_asset_signal_matrix_watch",
    BLOCK_STATUS: "triage_macro_asset_signal_matrix_block",
}

EMPTY_REASON_CODE = "macro_asset_signal_matrix_empty"
REPORT_PASS_REASON = "macro_asset_signal_matrix_pass"
REPORT_WATCH_REASON = "macro_asset_signal_matrix_watch"
REPORT_BLOCK_REASON = "macro_asset_signal_matrix_block"
ROW_CLEAR_REASON = "macro_signal_clear"
ROW_WATCH_REASON = "macro_signal_watch"
ROW_BLOCK_REASON = "macro_signal_block"

SIGNAL_SCORE_FIELDS = (
    "rates_signal_score",
    "inflation_signal_score",
    "employment_signal_score",
    "central_bank_calendar_score",
    "cross_asset_confirmation_score",
    "uncertainty_score",
)

_PUBLIC_DATACLASS_TYPES: tuple[type[object], ...]

_UNSAFE_PUBLIC_TERM_PARTS = (
    ("raw", "_", "candidate"),
    ("candidate", "_", "id"),
    ("market", "_", "id"),
    ("market", "_", "slug"),
    ("market", "_", "ques", "tion"),
    ("ques", "tion"),
    ("sou", "rce", "_", "ref"),
    ("sou", "rce", "_", "ur", "l"),
    ("sou", "rce", "_", "text"),
    ("sou", "rce", "_", "reference"),
    ("ur", "l"),
    ("d", "sn"),
    ("ta", "ble"),
    ("tok", "en"),
    ("wa", "llet"),
    ("or", "der"),
    ("tr", "ade"),
    ("tr", "ading"),
    ("pos", "ition"),
    ("b", "uy"),
    ("se", "ll"),
    ("recom", "mend"),
    ("recom", "mendation"),
    ("au", "th"),
    ("private", "_", "key"),
    ("api", "_", "key"),
    ("sec", "ret"),
)

__all__ = (
    "DEFAULT_RESEARCH_MACRO_ASSET_SIGNAL_MATRIX_CONFIG_VERSION",
    "MacroAssetSignalMatrixConfig",
    "MacroAssetSignalObservation",
    "MacroAssetSignalMatrixRow",
    "MacroAssetSignalMatrixReasonCodeCount",
    "MacroAssetSignalMatrixReport",
    "build_research_macro_asset_signal_matrix",
    "research_macro_asset_signal_matrix_payload",
    "research_macro_asset_signal_matrix_digest",
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
class MacroAssetSignalMatrixConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MACRO_ASSET_SIGNAL_MATRIX_CONFIG_VERSION
    watch_priority_score: Decimal = Decimal("0.300000")
    block_priority_score: Decimal = Decimal("0.650000")
    signal_watch_threshold: Decimal = Decimal("0.600000")
    signal_block_threshold: Decimal = Decimal("0.800000")
    stale_observation_age_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroAssetSignalMatrixConfig, "config")
        _require_safe_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MACRO_ASSET_SIGNAL_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_priority_score",
            "block_priority_score",
            "signal_watch_threshold",
            "signal_block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "stale_observation_age_seconds",
            _normalize_nonnegative_decimal(
                "stale_observation_age_seconds",
                self.stale_observation_age_seconds,
            ),
        )
        if self.watch_priority_score > self.block_priority_score:
            raise ValueError("watch_priority_score must not exceed block_priority_score")
        if self.signal_watch_threshold > self.signal_block_threshold:
            raise ValueError("signal_watch_threshold must not exceed signal_block_threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MacroAssetSignalObservation(_FinalPublicDataclass):
    asset_class: str
    macro_theme: str
    region: str
    event_family: str
    observed_at: datetime
    rates_signal_score: Decimal
    inflation_signal_score: Decimal
    employment_signal_score: Decimal
    central_bank_calendar_score: Decimal
    cross_asset_confirmation_score: Decimal
    uncertainty_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroAssetSignalObservation, "observation")
        for field_name in ("asset_class", "macro_theme", "region", "event_family"):
            _require_safe_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in SIGNAL_SCORE_FIELDS:
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class MacroAssetSignalMatrixRow(_FinalPublicDataclass):
    asset_class: str
    macro_theme: str
    region: str
    event_family: str
    observed_at: datetime
    observation_age_seconds: Decimal
    rates_signal_score: Decimal
    inflation_signal_score: Decimal
    employment_signal_score: Decimal
    central_bank_calendar_score: Decimal
    cross_asset_confirmation_score: Decimal
    uncertainty_score: Decimal
    priority_score: Decimal
    row_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroAssetSignalMatrixRow, "row")
        for field_name in ("asset_class", "macro_theme", "region", "event_family"):
            _require_safe_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "observation_age_seconds",
            _normalize_nonnegative_decimal(
                "observation_age_seconds",
                self.observation_age_seconds,
            ),
        )
        for field_name in (*SIGNAL_SCORE_FIELDS, "priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MacroAssetSignalMatrixReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MacroAssetSignalMatrixReasonCodeCount,
            "reason_code_count",
        )
        _require_safe_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count_decimal("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MacroAssetSignalMatrixReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    report_status: str
    human_research_focus: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    rates_watch_count: Decimal
    inflation_watch_count: Decimal
    employment_watch_count: Decimal
    central_bank_watch_count: Decimal
    stale_observation_count: Decimal
    max_priority_score: Decimal
    average_priority_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MacroAssetSignalMatrixReasonCodeCount, ...]
    rows: tuple[MacroAssetSignalMatrixRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MacroAssetSignalMatrixReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_safe_public_string("config_version", self.config_version)
        if self.config_version != DEFAULT_RESEARCH_MACRO_ASSET_SIGNAL_MATRIX_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        _require_status("report_status", self.report_status)
        _require_safe_public_string("human_research_focus", self.human_research_focus)
        for field_name in (
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "rates_watch_count",
            "inflation_watch_count",
            "employment_watch_count",
            "central_bank_watch_count",
            "stale_observation_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_priority_score", "average_priority_score"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
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


_PUBLIC_DATACLASS_TYPES = (
    MacroAssetSignalMatrixConfig,
    MacroAssetSignalObservation,
    MacroAssetSignalMatrixRow,
    MacroAssetSignalMatrixReasonCodeCount,
    MacroAssetSignalMatrixReport,
)


def build_research_macro_asset_signal_matrix(
    inputs: Iterable[MacroAssetSignalObservation],
    *,
    config: MacroAssetSignalMatrixConfig,
    generated_at: datetime,
) -> MacroAssetSignalMatrixReport:
    if type(config) is not MacroAssetSignalMatrixConfig:
        raise ValueError("config must be exactly MacroAssetSignalMatrixConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observations = _normalize_inputs(inputs)
    rows = _sort_rows(
        tuple(
            _row_from_observation(
                observation,
                config=config,
                generated_at=generated_at_utc,
            )
            for observation in observations
        ),
    )
    reason_codes = _report_reason_codes(rows)
    status = _report_status(rows)
    return MacroAssetSignalMatrixReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=status,
        human_research_focus=HUMAN_RESEARCH_FOCUS[status],
        row_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        block_count=_status_count(rows, BLOCK_STATUS),
        rates_watch_count=_reason_count(rows, "rates_signal_elevated"),
        inflation_watch_count=_reason_count(rows, "inflation_signal_elevated"),
        employment_watch_count=_reason_count(rows, "employment_signal_elevated"),
        central_bank_watch_count=_reason_count(rows, "central_bank_calendar_watch"),
        stale_observation_count=_reason_count(rows, "observation_stale_watch"),
        max_priority_score=_max_priority_score(rows),
        average_priority_score=_average_priority_score(rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_macro_asset_signal_matrix_payload(
    report: MacroAssetSignalMatrixReport,
) -> dict[str, Any]:
    if type(report) is not MacroAssetSignalMatrixReport:
        raise ValueError("report must be exactly MacroAssetSignalMatrixReport")
    _require_payload_safe_value("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    return payload


def research_macro_asset_signal_matrix_digest(
    report: MacroAssetSignalMatrixReport,
) -> dict[str, Any]:
    payload = research_macro_asset_signal_matrix_payload(report)
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("payload rows must be a list")
    return {
        "generated_at": payload["generated_at"],
        "config_version": payload["config_version"],
        "report_status": payload["report_status"],
        "human_research_focus": payload["human_research_focus"],
        "row_count": payload["row_count"],
        "pass_count": payload["pass_count"],
        "watch_count": payload["watch_count"],
        "block_count": payload["block_count"],
        "reason_codes": payload["reason_codes"],
        "top_rows": rows[:3],
    }


def _row_from_observation(
    observation: MacroAssetSignalObservation,
    *,
    config: MacroAssetSignalMatrixConfig,
    generated_at: datetime,
) -> MacroAssetSignalMatrixRow:
    priority_score = _priority_score(observation)
    age_seconds = _seconds_between(generated_at, observation.observed_at)
    status = _row_status(
        priority_score=priority_score,
        observation=observation,
        config=config,
    )
    return MacroAssetSignalMatrixRow(
        asset_class=observation.asset_class,
        macro_theme=observation.macro_theme,
        region=observation.region,
        event_family=observation.event_family,
        observed_at=observation.observed_at,
        observation_age_seconds=age_seconds,
        rates_signal_score=observation.rates_signal_score,
        inflation_signal_score=observation.inflation_signal_score,
        employment_signal_score=observation.employment_signal_score,
        central_bank_calendar_score=observation.central_bank_calendar_score,
        cross_asset_confirmation_score=observation.cross_asset_confirmation_score,
        uncertainty_score=observation.uncertainty_score,
        priority_score=priority_score,
        row_status=status,
        reason_codes=_row_reason_codes(
            observation.reason_codes,
            observation=observation,
            status=status,
            source_stale=age_seconds > config.stale_observation_age_seconds,
            config=config,
        ),
    )


def _priority_score(observation: MacroAssetSignalObservation) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = (
            observation.rates_signal_score * Decimal("0.250000")
            + observation.inflation_signal_score * Decimal("0.200000")
            + observation.employment_signal_score * Decimal("0.150000")
            + observation.central_bank_calendar_score * Decimal("0.200000")
            + observation.cross_asset_confirmation_score * Decimal("0.150000")
            + observation.uncertainty_score * Decimal("0.050000")
        )
    return _quantize_decimal(value)


def _row_status(
    *,
    priority_score: Decimal,
    observation: MacroAssetSignalObservation,
    config: MacroAssetSignalMatrixConfig,
) -> str:
    if (
        priority_score >= config.block_priority_score
        or observation.rates_signal_score >= config.signal_block_threshold
        or observation.inflation_signal_score >= config.signal_block_threshold
        or observation.employment_signal_score >= config.signal_block_threshold
        or observation.central_bank_calendar_score >= config.signal_block_threshold
    ):
        return BLOCK_STATUS
    if (
        priority_score >= config.watch_priority_score
        or observation.rates_signal_score >= config.signal_watch_threshold
        or observation.inflation_signal_score >= config.signal_watch_threshold
        or observation.employment_signal_score >= config.signal_watch_threshold
        or observation.central_bank_calendar_score >= config.signal_watch_threshold
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    observation: MacroAssetSignalObservation,
    status: str,
    source_stale: bool,
    config: MacroAssetSignalMatrixConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    if observation.rates_signal_score >= config.signal_watch_threshold:
        reason_codes.append("rates_signal_elevated")
    if observation.inflation_signal_score >= config.signal_watch_threshold:
        reason_codes.append("inflation_signal_elevated")
    if observation.employment_signal_score >= config.signal_watch_threshold:
        reason_codes.append("employment_signal_elevated")
    if observation.central_bank_calendar_score >= config.signal_watch_threshold:
        reason_codes.append("central_bank_calendar_watch")
    if source_stale:
        reason_codes.append("observation_stale_watch")
    if status == BLOCK_STATUS:
        reason_codes.append(ROW_BLOCK_REASON)
    elif status == WATCH_STATUS:
        reason_codes.append(ROW_WATCH_REASON)
    else:
        reason_codes.append(ROW_CLEAR_REASON)
    return _normalize_reason_codes(tuple(dict.fromkeys(reason_codes)))


def _normalize_inputs(
    inputs: Iterable[MacroAssetSignalObservation],
) -> tuple[MacroAssetSignalObservation, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable of MacroAssetSignalObservation")
    try:
        observations = tuple(inputs)
    except TypeError as exc:
        raise ValueError(
            "inputs must be an iterable of MacroAssetSignalObservation",
        ) from exc
    seen_keys: set[tuple[str, str, str, str, datetime]] = set()
    for observation in observations:
        if type(observation) is not MacroAssetSignalObservation:
            raise ValueError("inputs must contain MacroAssetSignalObservation values")
        _require_hard_flags("inputs", observation)
        key = (
            observation.asset_class,
            observation.macro_theme,
            observation.region,
            observation.event_family,
            observation.observed_at,
        )
        if key in seen_keys:
            raise ValueError("inputs must not contain duplicate public signal rows")
        seen_keys.add(key)
    return observations


def _normalize_rows(
    rows: tuple[MacroAssetSignalMatrixRow, ...],
) -> tuple[MacroAssetSignalMatrixRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    normalized = tuple(rows)
    seen_keys: set[tuple[str, str, str, str, datetime]] = set()
    for row in normalized:
        if type(row) is not MacroAssetSignalMatrixRow:
            raise ValueError("rows must contain MacroAssetSignalMatrixRow values")
        _require_hard_flags("rows", row)
        key = (row.asset_class, row.macro_theme, row.region, row.event_family, row.observed_at)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate public signal rows")
        seen_keys.add(key)
    if normalized != _sort_rows(normalized):
        raise ValueError("rows must use deterministic sequence")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[MacroAssetSignalMatrixReasonCodeCount, ...],
) -> tuple[MacroAssetSignalMatrixReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    normalized = tuple(counts)
    seen_reason_codes: set[str] = set()
    for count in normalized:
        if type(count) is not MacroAssetSignalMatrixReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain MacroAssetSignalMatrixReasonCodeCount values",
            )
        _require_hard_flags("reason_code_counts", count)
        if count.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(count.reason_code)
    if normalized != _sort_reason_code_counts(normalized):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _sort_rows(
    rows: tuple[MacroAssetSignalMatrixRow, ...],
) -> tuple[MacroAssetSignalMatrixRow, ...]:
    return tuple(
        row
        for _, row in sorted(
            (_row_sort_tuple(row), row)
            for row in rows
        )
    )


def _row_sort_tuple(
    row: MacroAssetSignalMatrixRow,
) -> tuple[Decimal, Decimal, datetime, str, str, str, str]:
    return (
        STATUS_RANK[row.row_status],
        -row.priority_score,
        row.observed_at,
        row.asset_class,
        row.region,
        row.macro_theme,
        row.event_family,
    )


def _sort_reason_code_counts(
    counts: tuple[MacroAssetSignalMatrixReasonCodeCount, ...],
) -> tuple[MacroAssetSignalMatrixReasonCodeCount, ...]:
    return tuple(
        count
        for _, count in sorted(
            ((-count.count, count.reason_code), count)
            for count in counts
        )
    )


def _reason_code_counts(
    rows: tuple[MacroAssetSignalMatrixRow, ...],
) -> tuple[MacroAssetSignalMatrixReasonCodeCount, ...]:
    if not rows:
        return (
            MacroAssetSignalMatrixReasonCodeCount(
                reason_code=EMPTY_REASON_CODE,
                count=ONE,
            ),
        )
    counter: Counter[str] = Counter(
        reason_code for row in rows for reason_code in row.reason_codes
    )
    return _sort_reason_code_counts(
        tuple(
            MacroAssetSignalMatrixReasonCodeCount(
                reason_code=reason_code,
                count=_count_decimal(counter[reason_code]),
            )
            for reason_code in counter
        ),
    )


def _report_reason_codes(rows: tuple[MacroAssetSignalMatrixRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    status = _report_status(rows)
    if status == BLOCK_STATUS:
        return (REPORT_BLOCK_REASON,)
    if status == WATCH_STATUS:
        return (REPORT_WATCH_REASON,)
    return (REPORT_PASS_REASON,)


def _normalize_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if len(normalized) != 1:
        raise ValueError("reason_codes must contain exactly one value")
    _require_safe_public_string("reason_codes", normalized[0])
    allowed = (EMPTY_REASON_CODE, REPORT_PASS_REASON, REPORT_WATCH_REASON, REPORT_BLOCK_REASON)
    if normalized[0] not in allowed:
        raise ValueError("reason_codes must contain known report reason codes")
    return normalized


def _report_status(rows: tuple[MacroAssetSignalMatrixRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.row_status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.row_status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _status_count(rows: tuple[MacroAssetSignalMatrixRow, ...], status: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.row_status == status))


def _reason_count(rows: tuple[MacroAssetSignalMatrixRow, ...], reason_code: str) -> Decimal:
    return _count_decimal(sum(1 for row in rows if reason_code in row.reason_codes))


def _max_priority_score(rows: tuple[MacroAssetSignalMatrixRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.priority_score for row in rows)


def _average_priority_score(rows: tuple[MacroAssetSignalMatrixRow, ...]) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        total = sum((row.priority_score for row in rows), ZERO)
        return _quantize_decimal(total / _count_decimal(len(rows)))


def _validate_row(row: MacroAssetSignalMatrixRow) -> None:
    expected_priority_score = _priority_score(
        MacroAssetSignalObservation(
            asset_class=row.asset_class,
            macro_theme=row.macro_theme,
            region=row.region,
            event_family=row.event_family,
            observed_at=row.observed_at,
            rates_signal_score=row.rates_signal_score,
            inflation_signal_score=row.inflation_signal_score,
            employment_signal_score=row.employment_signal_score,
            central_bank_calendar_score=row.central_bank_calendar_score,
            cross_asset_confirmation_score=row.cross_asset_confirmation_score,
            uncertainty_score=row.uncertainty_score,
            reason_codes=(ROW_CLEAR_REASON,),
        ),
    )
    if row.priority_score != expected_priority_score:
        raise ValueError("priority_score must match signal scores")
    expected_status_reason = {
        PASS_STATUS: ROW_CLEAR_REASON,
        WATCH_STATUS: ROW_WATCH_REASON,
        BLOCK_STATUS: ROW_BLOCK_REASON,
    }[row.row_status]
    if expected_status_reason not in row.reason_codes:
        raise ValueError("row_status must match reason_codes")


def _validate_report(report: MacroAssetSignalMatrixReport) -> None:
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(report.rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, BLOCK_STATUS):
        raise ValueError("block_count must match rows")
    status_total = report.pass_count + report.watch_count + report.block_count
    if status_total != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.rates_watch_count != _reason_count(report.rows, "rates_signal_elevated"):
        raise ValueError("rates_watch_count must match rows")
    if report.inflation_watch_count != _reason_count(report.rows, "inflation_signal_elevated"):
        raise ValueError("inflation_watch_count must match rows")
    if report.employment_watch_count != _reason_count(
        report.rows,
        "employment_signal_elevated",
    ):
        raise ValueError("employment_watch_count must match rows")
    if report.central_bank_watch_count != _reason_count(
        report.rows,
        "central_bank_calendar_watch",
    ):
        raise ValueError("central_bank_watch_count must match rows")
    if report.stale_observation_count != _reason_count(
        report.rows,
        "observation_stale_watch",
    ):
        raise ValueError("stale_observation_count must match rows")
    if report.max_priority_score != _max_priority_score(report.rows):
        raise ValueError("max_priority_score must match rows")
    if report.average_priority_score != _average_priority_score(report.rows):
        raise ValueError("average_priority_score must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.human_research_focus != HUMAN_RESEARCH_FOCUS[report.report_status]:
        raise ValueError("human_research_focus must match report_status")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    normalized = tuple(reason_codes)
    if not normalized:
        raise ValueError("reason_codes must not be empty")
    for reason_code in normalized:
        _require_safe_public_string("reason_codes", reason_code)
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    sorted_reason_codes = tuple(sorted(normalized))
    if normalized != sorted_reason_codes:
        return sorted_reason_codes
    return normalized


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    if earlier > later:
        raise ValueError("observed_at must not exceed generated_at")
    return _quantize_decimal(Decimal(str((later - earlier).total_seconds())))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _quantize_decimal(value)


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _require_status(field_name: str, value: object) -> None:
    _require_safe_public_string(field_name, value)
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_safe_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if "://" in value or "?" in value:
        raise ValueError(f"{field_name} has unsafe public value")
    if _has_unsafe_public_fragment(field_name) or _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} has unsafe public value")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    compact = "".join(character for character in lowered if character.isalnum())
    return any(
        term in lowered or term.replace("_", "") in compact
        for term in ("".join(parts) for parts in _UNSAFE_PUBLIC_TERM_PARTS)
    )


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


def _require_exact_type(value: object, type_: type[object], field_name: str) -> None:
    if type(value) is not type_:
        raise ValueError(f"{field_name} must be exactly {type_.__name__}")


def _require_payload_safe_value(field_name: str, value: object) -> None:
    if isinstance(value, Decimal):
        _require_decimal(field_name, value)
        if value != _quantize_decimal(value):
            raise ValueError(f"{field_name} must be quantized to six decimals")
        return
    if type(value) is datetime:
        normalized = _as_utc(field_name, value)
        if normalized.tzinfo is not UTC:
            raise ValueError(f"{field_name} must be normalized to UTC")
        return
    if is_dataclass(value) and not isinstance(value, type):
        if type(value) not in _PUBLIC_DATACLASS_TYPES:
            raise ValueError(f"{field_name} must be a known public dataclass")
        _require_hard_flags(field_name, value)
        for field in fields(value):
            if _has_unsafe_public_fragment(field.name):
                raise ValueError(f"{field.name} has unsafe public field")
            _require_payload_safe_value(
                f"{field_name}.{field.name}",
                getattr(value, field.name),
            )
        _reconstruct_public_dataclass(field_name, value)
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            _require_payload_safe_value(f"{field_name}[{index}]", item)
        return
    if type(value) is str:
        _require_safe_public_string(field_name, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (list, dict, set):
        raise ValueError(f"{field_name} must remain constructor-normalized")
    if isinstance(value, float) or type(value) is int:
        raise ValueError(f"{field_name} must use Decimal-derived string values")
    raise ValueError(f"{field_name} is not JSON-ready")


def _reconstruct_public_dataclass(field_name: str, value: object) -> None:
    type_ = type(value)
    try:
        type_(**{field.name: getattr(value, field.name) for field in fields(value)})
    except (ArithmeticError, TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must remain constructor-valid") from exc


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if type(value) is tuple:
        return [_payload_value(item) for item in value]
    return value
