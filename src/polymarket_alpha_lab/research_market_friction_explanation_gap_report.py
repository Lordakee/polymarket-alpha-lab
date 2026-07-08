"""Pure public report for friction changes lacking fresh explanations."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
from typing import Any


__all__ = (
    "ResearchMarketFrictionExplanationGapConfig",
    "ResearchMarketFrictionExplanationGapObservation",
    "ResearchMarketFrictionExplanationGapReasonCodeCount",
    "ResearchMarketFrictionExplanationGapReport",
    "ResearchMarketFrictionExplanationGapRow",
    "build_research_market_friction_explanation_gap_report",
    "research_market_friction_explanation_gap_report_digest",
    "research_market_friction_explanation_gap_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-market-friction-explanation-gap-report-v0"
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
UNSAFE_TEXT_FRAGMENTS = (
    "marketslug",
    "marketid",
    "conditionid",
    "sourceid",
    "sourceurl",
    "url",
)
STATUS_RANK = {"block": 0, "watch": 1, "pass": 2}


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchMarketFrictionExplanationGapConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    watch_gap_score_threshold: Decimal = Decimal("0.250000")
    block_gap_score_threshold: Decimal = Decimal("0.700000")
    spread_watch_bps: Decimal = Decimal("50.000000")
    spread_block_bps: Decimal = Decimal("150.000000")
    depth_drop_watch_ratio: Decimal = Decimal("0.250000")
    depth_drop_block_ratio: Decimal = Decimal("0.500000")
    quote_staleness_watch_seconds: Decimal = Decimal("300.000000")
    quote_staleness_block_seconds: Decimal = Decimal("900.000000")
    catalyst_watch_pressure: Decimal = Decimal("0.500000")
    catalyst_block_pressure: Decimal = Decimal("0.800000")
    fresh_evidence_seconds: Decimal = Decimal("3600.000000")
    stale_evidence_seconds: Decimal = Decimal("86400.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFrictionExplanationGapConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("config_version", self.config_version)
        for field_name in (
            "watch_gap_score_threshold",
            "block_gap_score_threshold",
            "depth_drop_watch_ratio",
            "depth_drop_block_ratio",
            "catalyst_watch_pressure",
            "catalyst_block_pressure",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "spread_watch_bps",
            "spread_block_bps",
            "quote_staleness_watch_seconds",
            "quote_staleness_block_seconds",
            "fresh_evidence_seconds",
            "stale_evidence_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_ascending_pair(
            "watch_gap_score_threshold",
            self.watch_gap_score_threshold,
            "block_gap_score_threshold",
            self.block_gap_score_threshold,
        )
        _require_ascending_pair(
            "spread_watch_bps",
            self.spread_watch_bps,
            "spread_block_bps",
            self.spread_block_bps,
        )
        _require_ascending_pair(
            "depth_drop_watch_ratio",
            self.depth_drop_watch_ratio,
            "depth_drop_block_ratio",
            self.depth_drop_block_ratio,
        )
        _require_ascending_pair(
            "quote_staleness_watch_seconds",
            self.quote_staleness_watch_seconds,
            "quote_staleness_block_seconds",
            self.quote_staleness_block_seconds,
        )
        _require_ascending_pair(
            "catalyst_watch_pressure",
            self.catalyst_watch_pressure,
            "catalyst_block_pressure",
            self.catalyst_block_pressure,
        )
        _require_ascending_pair(
            "fresh_evidence_seconds",
            self.fresh_evidence_seconds,
            "stale_evidence_seconds",
            self.stale_evidence_seconds,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketFrictionExplanationGapObservation:
    friction_group: str
    observed_at: datetime
    aggregate_spread_bps: Decimal
    depth_drop_ratio: Decimal
    quote_staleness_seconds: Decimal
    catalyst_pressure: Decimal
    evidence_freshness_seconds: Decimal
    explanation_count: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFrictionExplanationGapObservation does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("friction_group", self.friction_group)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_spread_bps",
            "quote_staleness_seconds",
            "evidence_freshness_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("depth_drop_ratio", "catalyst_pressure"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "explanation_count",
            _require_nonnegative_whole_decimal("explanation_count", self.explanation_count),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketFrictionExplanationGapRow:
    friction_group: str
    observed_at: datetime
    aggregate_spread_bps: Decimal
    depth_drop_ratio: Decimal
    quote_staleness_seconds: Decimal
    catalyst_pressure: Decimal
    evidence_freshness_seconds: Decimal
    explanation_count: Decimal
    spread_pressure_score: Decimal
    depth_pressure_score: Decimal
    quote_staleness_pressure_score: Decimal
    catalyst_pressure_score: Decimal
    friction_pressure_score: Decimal
    evidence_gap_score: Decimal
    gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFrictionExplanationGapRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_public_string("friction_group", self.friction_group)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "aggregate_spread_bps",
            "quote_staleness_seconds",
            "evidence_freshness_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "explanation_count",
            _require_nonnegative_whole_decimal("explanation_count", self.explanation_count),
        )
        for field_name in (
            "depth_drop_ratio",
            "catalyst_pressure",
            "spread_pressure_score",
            "depth_pressure_score",
            "quote_staleness_pressure_score",
            "catalyst_pressure_score",
            "friction_pressure_score",
            "evidence_gap_score",
            "gap_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_gap_row(self)


@dataclass(frozen=True)
class ResearchMarketFrictionExplanationGapReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFrictionExplanationGapReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketFrictionExplanationGapReport:
    generated_at: datetime
    config_version: str
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_gap_score: Decimal
    average_gap_score: Decimal | None
    status: str
    rows: tuple[ResearchMarketFrictionExplanationGapRow, ...]
    reason_code_counts: tuple[ResearchMarketFrictionExplanationGapReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketFrictionExplanationGapReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_gap_score",
            _require_probability_decimal("max_gap_score", self.max_gap_score),
        )
        object.__setattr__(
            self,
            "average_gap_score",
            _require_optional_probability_decimal(
                "average_gap_score",
                self.average_gap_score,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_gap_report(self)


def build_research_market_friction_explanation_gap_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketFrictionExplanationGapConfig,
    generated_at: datetime,
) -> ResearchMarketFrictionExplanationGapReport:
    if type(config) is not ResearchMarketFrictionExplanationGapConfig:
        raise ValueError("config must be a ResearchMarketFrictionExplanationGapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    observation_rows = _normalize_observations(observations)
    seen_groups: set[str] = set()
    for item in observation_rows:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
        if item.friction_group in seen_groups:
            raise ValueError("duplicate friction_group")
        seen_groups.add(item.friction_group)

    rows = tuple(
        sorted(
            (_row_from_observation(item, config=config) for item in observation_rows),
            key=_row_sort_key,
        ),
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchMarketFrictionExplanationGapReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        max_gap_score=_max_gap_score(rows),
        average_gap_score=_average_gap_score(rows),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_friction_explanation_gap_report_payload(
    report: ResearchMarketFrictionExplanationGapReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketFrictionExplanationGapReport:
        raise ValueError("report must be a ResearchMarketFrictionExplanationGapReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def research_market_friction_explanation_gap_report_digest(
    report: ResearchMarketFrictionExplanationGapReport,
) -> str:
    payload = research_market_friction_explanation_gap_report_payload(report)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _row_from_observation(
    item: ResearchMarketFrictionExplanationGapObservation,
    *,
    config: ResearchMarketFrictionExplanationGapConfig,
) -> ResearchMarketFrictionExplanationGapRow:
    spread_pressure_score = _threshold_pressure(
        item.aggregate_spread_bps,
        watch_threshold=config.spread_watch_bps,
        block_threshold=config.spread_block_bps,
    )
    depth_pressure_score = _threshold_pressure(
        item.depth_drop_ratio,
        watch_threshold=config.depth_drop_watch_ratio,
        block_threshold=config.depth_drop_block_ratio,
    )
    quote_staleness_pressure_score = _threshold_pressure(
        item.quote_staleness_seconds,
        watch_threshold=config.quote_staleness_watch_seconds,
        block_threshold=config.quote_staleness_block_seconds,
    )
    catalyst_pressure_score = _threshold_pressure(
        item.catalyst_pressure,
        watch_threshold=config.catalyst_watch_pressure,
        block_threshold=config.catalyst_block_pressure,
    )
    friction_pressure_score = max(
        spread_pressure_score,
        depth_pressure_score,
        quote_staleness_pressure_score,
        item.catalyst_pressure,
    )
    evidence_gap_score = _evidence_gap_score(item, config=config)
    gap_score = _quantize(friction_pressure_score * evidence_gap_score)
    status = _gap_status(gap_score, config=config)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        status=status,
        gap_score=gap_score,
    )

    return ResearchMarketFrictionExplanationGapRow(
        friction_group=item.friction_group,
        observed_at=item.observed_at,
        aggregate_spread_bps=item.aggregate_spread_bps,
        depth_drop_ratio=item.depth_drop_ratio,
        quote_staleness_seconds=item.quote_staleness_seconds,
        catalyst_pressure=item.catalyst_pressure,
        evidence_freshness_seconds=item.evidence_freshness_seconds,
        explanation_count=item.explanation_count,
        spread_pressure_score=spread_pressure_score,
        depth_pressure_score=depth_pressure_score,
        quote_staleness_pressure_score=quote_staleness_pressure_score,
        catalyst_pressure_score=catalyst_pressure_score,
        friction_pressure_score=friction_pressure_score,
        evidence_gap_score=evidence_gap_score,
        gap_score=gap_score,
        status=status,
        reason_codes=reason_codes,
    )


def _threshold_pressure(
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> Decimal:
    if value < watch_threshold:
        return ZERO
    if value >= block_threshold:
        return ONE
    return _quantize((value - watch_threshold) / (block_threshold - watch_threshold))


def _evidence_gap_score(
    item: ResearchMarketFrictionExplanationGapObservation,
    *,
    config: ResearchMarketFrictionExplanationGapConfig,
) -> Decimal:
    if item.explanation_count == ZERO:
        return ONE
    if item.evidence_freshness_seconds <= config.fresh_evidence_seconds:
        return ZERO
    if item.evidence_freshness_seconds >= config.stale_evidence_seconds:
        return ONE
    return _quantize(
        (item.evidence_freshness_seconds - config.fresh_evidence_seconds)
        / (config.stale_evidence_seconds - config.fresh_evidence_seconds),
    )


def _gap_status(
    gap_score: Decimal,
    *,
    config: ResearchMarketFrictionExplanationGapConfig,
) -> str:
    if gap_score >= config.block_gap_score_threshold:
        return "block"
    if gap_score >= config.watch_gap_score_threshold:
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketFrictionExplanationGapObservation,
    *,
    config: ResearchMarketFrictionExplanationGapConfig,
    status: str,
    gap_score: Decimal,
) -> tuple[str, ...]:
    reason_codes: set[str] = {f"explanation_gap_{status}"}
    reason_codes.add(
        "explanations_present" if item.explanation_count > ZERO else "missing_explanations",
    )
    reason_codes.add(
        "evidence_fresh"
        if item.evidence_freshness_seconds <= config.fresh_evidence_seconds
        else "evidence_stale",
    )
    _add_threshold_reason(
        reason_codes,
        "aggregate_spread",
        item.aggregate_spread_bps,
        watch_threshold=config.spread_watch_bps,
        block_threshold=config.spread_block_bps,
    )
    _add_threshold_reason(
        reason_codes,
        "depth_drop",
        item.depth_drop_ratio,
        watch_threshold=config.depth_drop_watch_ratio,
        block_threshold=config.depth_drop_block_ratio,
    )
    _add_threshold_reason(
        reason_codes,
        "quote_staleness",
        item.quote_staleness_seconds,
        watch_threshold=config.quote_staleness_watch_seconds,
        block_threshold=config.quote_staleness_block_seconds,
    )
    _add_threshold_reason(
        reason_codes,
        "catalyst_pressure",
        item.catalyst_pressure,
        watch_threshold=config.catalyst_watch_pressure,
        block_threshold=config.catalyst_block_pressure,
    )
    if gap_score == ZERO:
        reason_codes.discard("aggregate_spread_watch")
        reason_codes.discard("depth_drop_watch")
        reason_codes.discard("quote_staleness_watch")
        reason_codes.discard("catalyst_pressure_watch")
    for reason_code in item.reason_codes:
        reason_codes.add(f"input_{reason_code}")
    return tuple(sorted(reason_codes))


def _add_threshold_reason(
    reason_codes: set[str],
    prefix: str,
    value: Decimal,
    *,
    watch_threshold: Decimal,
    block_threshold: Decimal,
) -> None:
    if value >= block_threshold:
        reason_codes.add(f"{prefix}_block")
    elif value >= watch_threshold:
        reason_codes.add(f"{prefix}_watch")


def _summary_reason_codes(
    rows: tuple[ResearchMarketFrictionExplanationGapRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_friction_explanation_gap_no_observations",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(rows: tuple[ResearchMarketFrictionExplanationGapRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketFrictionExplanationGapRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketFrictionExplanationGapReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketFrictionExplanationGapReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketFrictionExplanationGapReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _normalize_observations(
    values: Iterable[object],
) -> tuple[ResearchMarketFrictionExplanationGapObservation, ...]:
    if isinstance(values, (str, bytes)):
        raise ValueError("observations must be an iterable")
    try:
        rows = tuple(values)
    except TypeError as exc:
        raise ValueError("observations must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchMarketFrictionExplanationGapObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketFrictionExplanationGapObservation values",
            )
        _require_hard_flags("observation", row)
    return rows


def _normalize_rows(
    rows: tuple[ResearchMarketFrictionExplanationGapRow, ...],
) -> tuple[ResearchMarketFrictionExplanationGapRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketFrictionExplanationGapRow:
            raise ValueError(
                "rows must contain ResearchMarketFrictionExplanationGapRow values",
            )
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by status and friction_group")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketFrictionExplanationGapReasonCodeCount, ...],
) -> tuple[ResearchMarketFrictionExplanationGapReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketFrictionExplanationGapReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketFrictionExplanationGapReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _row_sort_key(row: ResearchMarketFrictionExplanationGapRow) -> tuple[int, str]:
    return (STATUS_RANK[row.status], row.friction_group)


def _max_gap_score(rows: tuple[ResearchMarketFrictionExplanationGapRow, ...]) -> Decimal:
    if not rows:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(row.gap_score for row in rows)


def _average_gap_score(
    rows: tuple[ResearchMarketFrictionExplanationGapRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.gap_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(
    rows: tuple[ResearchMarketFrictionExplanationGapRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _validate_gap_row(row: ResearchMarketFrictionExplanationGapRow) -> None:
    expected_status: str
    if row.gap_score >= Decimal("0.700000"):
        expected_status = "block"
    elif row.gap_score >= Decimal("0.250000"):
        expected_status = "watch"
    else:
        expected_status = "pass"
    if row.status != expected_status:
        raise ValueError("status must match gap_score")
    if f"explanation_gap_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must match status")


def _validate_gap_report(report: ResearchMarketFrictionExplanationGapReport) -> None:
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.max_gap_score != _max_gap_score(report.rows):
        raise ValueError("max_gap_score must match rows")
    if report.average_gap_score != _average_gap_score(report.rows):
        raise ValueError("average_gap_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.rows):
        raise ValueError("status must match rows")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _payload_value(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(normalized)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_positive_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count source must be an int")
    if value < 0:
        raise ValueError("count source must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(RATIO_QUANTUM)


def _require_ascending_pair(
    lower_name: str,
    lower_value: Decimal,
    upper_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{lower_name} must be less than {upper_name}")


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty public string")
    normalized = "".join(character for character in value.lower() if character.isalnum())
    if any(fragment in normalized for fragment in UNSAFE_TEXT_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe text")


def _normalize_reason_codes(
    field_name: str,
    values: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for value in values:
        _require_reason_code(field_name, value)
        normalized.append(value)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must be nonempty")
    return tuple(sorted(set(normalized)))


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be nonempty code text")
    allowed = "abcdefghijklmnopqrstuvwxyz0123456789_"
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must contain deterministic code text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")
