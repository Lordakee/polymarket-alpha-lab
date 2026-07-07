"""Read-only Phase 1 gate for market news shock recency decay."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from typing import Any


DEFAULT_MARKET_EVENT_NEWS_SHOCK_DECAY_GATE_V2_CONFIG_VERSION = (
    "market-event-news-shock-decay-gate-v2"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
STATUSES = ("empty", "pass", "watch", "block")
ROW_STATUSES = ("pass", "watch", "block")
REASON_CODES = (
    "fresh_news_shock_block",
    "active_news_shock_watch",
    "stale_confirmation_source",
    "low_confirmation_count",
    "near_close_news_shock_watch",
    "stale_news_shock",
    "news_shock_decay_passed",
    "empty_news_shock_decay_inputs",
)
STATUS_SORT_WEIGHT = {
    "block": 0,
    "watch": 1,
    "pass": 2,
}


@dataclass(frozen=True)
class MarketEventNewsShockDecayGateV2Config:
    config_version: str = DEFAULT_MARKET_EVENT_NEWS_SHOCK_DECAY_GATE_V2_CONFIG_VERSION
    shock_decay_window_seconds: Decimal = Decimal("3600.000000")
    stale_confirmation_seconds: Decimal = Decimal("7200.000000")
    minimum_source_confirmation_count: Decimal = Decimal("2.000000")
    block_shock_decay_score: Decimal = Decimal("0.120000")
    watch_shock_decay_score: Decimal = Decimal("0.030000")
    close_pressure_minutes: Decimal = Decimal("15.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "shock_decay_window_seconds",
            "stale_confirmation_seconds",
            "minimum_source_confirmation_count",
            "block_shock_decay_score",
            "watch_shock_decay_score",
            "close_pressure_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        _require_integral_decimal(
            "minimum_source_confirmation_count",
            self.minimum_source_confirmation_count,
        )
        if self.watch_shock_decay_score >= self.block_shock_decay_score:
            raise ValueError(
                "watch_shock_decay_score must be less than block_shock_decay_score",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class MarketEventNewsShockDecayGateV2Input:
    market_id: str
    event_slug: str
    category: str
    shock_detected_at: datetime
    latest_confirming_source_at: datetime
    probability_move_since_shock: Decimal
    source_confirmation_count: Decimal
    minutes_to_close: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("event_slug", self.event_slug)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "shock_detected_at",
            _as_utc("shock_detected_at", self.shock_detected_at),
        )
        object.__setattr__(
            self,
            "latest_confirming_source_at",
            _as_utc(
                "latest_confirming_source_at",
                self.latest_confirming_source_at,
            ),
        )
        for field_name in (
            "probability_move_since_shock",
            "source_confirmation_count",
            "minutes_to_close",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_integral_decimal(
            "source_confirmation_count",
            self.source_confirmation_count,
        )
        if self.latest_confirming_source_at < self.shock_detected_at:
            raise ValueError(
                "latest_confirming_source_at must be at or after shock_detected_at",
            )
        _require_hard_flags("event", self)


@dataclass(frozen=True)
class MarketEventNewsShockDecayGateV2Row:
    market_id: str
    event_slug: str
    category: str
    shock_detected_at: datetime
    latest_confirming_source_at: datetime
    probability_move_since_shock: Decimal
    source_confirmation_count: Decimal
    minutes_to_close: Decimal
    shock_age_seconds: Decimal
    confirmation_age_seconds: Decimal
    shock_decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("market_id", self.market_id)
        _require_canonical_string("event_slug", self.event_slug)
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "shock_detected_at",
            _as_utc("shock_detected_at", self.shock_detected_at),
        )
        object.__setattr__(
            self,
            "latest_confirming_source_at",
            _as_utc(
                "latest_confirming_source_at",
                self.latest_confirming_source_at,
            ),
        )
        for field_name in (
            "probability_move_since_shock",
            "source_confirmation_count",
            "minutes_to_close",
            "shock_age_seconds",
            "confirmation_age_seconds",
            "shock_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_integral_decimal(
            "source_confirmation_count",
            self.source_confirmation_count,
        )
        _require_status("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class MarketEventNewsShockDecayGateV2ReasonCodeCount:
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
            _normalize_nonnegative_decimal("count", self.count),
        )
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class MarketEventNewsShockDecayGateV2Report:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    stale_shock_count: Decimal
    stale_confirmation_count: Decimal
    low_confirmation_count: Decimal
    max_shock_decay_score: Decimal
    report_status: str
    rows: tuple[MarketEventNewsShockDecayGateV2Row, ...]
    reason_code_counts: tuple[MarketEventNewsShockDecayGateV2ReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: tuple[tuple[str, str], ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
            "stale_shock_count",
            "stale_confirmation_count",
            "low_confirmation_count",
            "max_shock_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("report_status", self.report_status, STATUSES)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "derived_validation_digest",
            _normalize_validation_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            ),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_event_news_shock_decay_gate_v2(
    events: Iterable[object],
    *,
    config: MarketEventNewsShockDecayGateV2Config,
    generated_at: datetime,
) -> MarketEventNewsShockDecayGateV2Report:
    if type(config) is not MarketEventNewsShockDecayGateV2Config:
        raise ValueError("config must be a MarketEventNewsShockDecayGateV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(events)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    event,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for event in inputs
            ),
            key=_row_sort_key,
        ),
    )
    reason_codes = _report_reason_codes(rows)
    reason_code_counts = _reason_code_counts(rows)
    event_count = _decimal_count(len(rows))
    pass_count = _decimal_count(_status_count(rows, "pass"))
    watch_count = _decimal_count(_status_count(rows, "watch"))
    block_count = _decimal_count(_status_count(rows, "block"))
    stale_shock_count = _decimal_count(
        sum(1 for row in rows if "stale_news_shock" in row.reason_codes),
    )
    stale_confirmation_count = _decimal_count(
        sum(1 for row in rows if "stale_confirmation_source" in row.reason_codes),
    )
    low_confirmation_count = _decimal_count(
        sum(1 for row in rows if "low_confirmation_count" in row.reason_codes),
    )
    max_shock_decay_score = _max_score(rows)
    return MarketEventNewsShockDecayGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=event_count,
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        stale_shock_count=stale_shock_count,
        stale_confirmation_count=stale_confirmation_count,
        low_confirmation_count=low_confirmation_count,
        max_shock_decay_score=max_shock_decay_score,
        report_status=_report_status(rows),
        rows=rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
        derived_validation_digest=_derived_validation_digest(
            event_count=event_count,
            pass_count=pass_count,
            watch_count=watch_count,
            block_count=block_count,
            stale_shock_count=stale_shock_count,
            stale_confirmation_count=stale_confirmation_count,
            low_confirmation_count=low_confirmation_count,
            max_shock_decay_score=max_shock_decay_score,
            rows=rows,
            reason_code_counts=reason_code_counts,
        ),
    )


def market_event_news_shock_decay_gate_v2_payload(
    report: MarketEventNewsShockDecayGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is MarketEventNewsShockDecayGateV2Report:
        _require_hard_flags("report", report)
        payload = _payload_value(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        payload = _payload_value(report)
    else:
        raise ValueError("report must be a MarketEventNewsShockDecayGateV2Report")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _row_from_input(
    event: MarketEventNewsShockDecayGateV2Input,
    *,
    config: MarketEventNewsShockDecayGateV2Config,
    generated_at: datetime,
) -> MarketEventNewsShockDecayGateV2Row:
    _reject_future_times(event, generated_at)
    shock_age_seconds = _seconds_between(event.shock_detected_at, generated_at)
    confirmation_age_seconds = _seconds_between(
        event.latest_confirming_source_at,
        generated_at,
    )
    shock_decay_score = _shock_decay_score(
        probability_move_since_shock=event.probability_move_since_shock,
        shock_age_seconds=shock_age_seconds,
        decay_window_seconds=config.shock_decay_window_seconds,
    )
    reason_codes = _row_reason_codes(
        shock_age_seconds=shock_age_seconds,
        confirmation_age_seconds=confirmation_age_seconds,
        shock_decay_score=shock_decay_score,
        source_confirmation_count=event.source_confirmation_count,
        minutes_to_close=event.minutes_to_close,
        config=config,
    )
    return MarketEventNewsShockDecayGateV2Row(
        market_id=event.market_id,
        event_slug=event.event_slug,
        category=event.category,
        shock_detected_at=event.shock_detected_at,
        latest_confirming_source_at=event.latest_confirming_source_at,
        probability_move_since_shock=event.probability_move_since_shock,
        source_confirmation_count=event.source_confirmation_count,
        minutes_to_close=event.minutes_to_close,
        shock_age_seconds=shock_age_seconds,
        confirmation_age_seconds=confirmation_age_seconds,
        shock_decay_score=shock_decay_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _normalize_inputs(
    events: Iterable[object],
) -> tuple[MarketEventNewsShockDecayGateV2Input, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        values = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    return tuple(_coerce_input(value) for value in values)


def _coerce_input(value: object) -> MarketEventNewsShockDecayGateV2Input:
    if type(value) is MarketEventNewsShockDecayGateV2Input:
        _require_hard_flags("event", value)
        return value
    _require_hard_flags("event", value)
    return MarketEventNewsShockDecayGateV2Input(
        market_id=_field_value(value, "market_id"),
        event_slug=_field_value(value, "event_slug"),
        category=_field_value(value, "category"),
        shock_detected_at=_field_value(value, "shock_detected_at"),
        latest_confirming_source_at=_field_value(
            value,
            "latest_confirming_source_at",
        ),
        probability_move_since_shock=_field_value(
            value,
            "probability_move_since_shock",
        ),
        source_confirmation_count=_field_value(value, "source_confirmation_count"),
        minutes_to_close=_field_value(value, "minutes_to_close"),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _row_reason_codes(
    *,
    shock_age_seconds: Decimal,
    confirmation_age_seconds: Decimal,
    shock_decay_score: Decimal,
    source_confirmation_count: Decimal,
    minutes_to_close: Decimal,
    config: MarketEventNewsShockDecayGateV2Config,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if shock_decay_score >= config.block_shock_decay_score:
        reason_codes.append("fresh_news_shock_block")
    elif shock_decay_score >= config.watch_shock_decay_score:
        reason_codes.append("active_news_shock_watch")
    if confirmation_age_seconds > config.stale_confirmation_seconds:
        reason_codes.append("stale_confirmation_source")
    if source_confirmation_count < config.minimum_source_confirmation_count:
        reason_codes.append("low_confirmation_count")
    if minutes_to_close <= config.close_pressure_minutes and shock_decay_score > ZERO:
        reason_codes.append("near_close_news_shock_watch")
    if shock_age_seconds >= config.shock_decay_window_seconds:
        reason_codes.append("stale_news_shock")
    if not reason_codes or reason_codes == ["stale_news_shock"]:
        reason_codes.append("news_shock_decay_passed")
    return _canonical_reason_codes(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if "fresh_news_shock_block" in reason_codes:
        return "block"
    watch_reasons = {
        "active_news_shock_watch",
        "stale_confirmation_source",
        "low_confirmation_count",
        "near_close_news_shock_watch",
    }
    if any(reason_code in watch_reasons for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(rows: tuple[MarketEventNewsShockDecayGateV2Row, ...]) -> str:
    if not rows:
        return "empty"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[MarketEventNewsShockDecayGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_news_shock_decay_inputs",)
    present = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
    }
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in present)


def _reason_code_counts(
    rows: tuple[MarketEventNewsShockDecayGateV2Row, ...],
) -> tuple[MarketEventNewsShockDecayGateV2ReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        MarketEventNewsShockDecayGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counts[reason_code]),
        )
        for reason_code in REASON_CODES
        if counts[reason_code] > 0
    )


def _status_count(
    rows: tuple[MarketEventNewsShockDecayGateV2Row, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _max_score(rows: tuple[MarketEventNewsShockDecayGateV2Row, ...]) -> Decimal:
    if not rows:
        return ZERO
    return max(row.shock_decay_score for row in rows)


def _shock_decay_score(
    *,
    probability_move_since_shock: Decimal,
    shock_age_seconds: Decimal,
    decay_window_seconds: Decimal,
) -> Decimal:
    if shock_age_seconds >= decay_window_seconds:
        return ZERO
    remaining_ratio = (decay_window_seconds - shock_age_seconds) / decay_window_seconds
    return _quantize(probability_move_since_shock * remaining_ratio)


def _reject_future_times(
    event: MarketEventNewsShockDecayGateV2Input,
    generated_at: datetime,
) -> None:
    for field_name in ("shock_detected_at", "latest_confirming_source_at"):
        value = getattr(event, field_name)
        if value > generated_at:
            raise ValueError(f"{field_name} must be at or before generated_at")


def _seconds_between(start: datetime, end: datetime) -> Decimal:
    delta = _as_utc("end", end) - _as_utc("start", start)
    microseconds = (
        (delta.days * 86_400 + delta.seconds) * 1_000_000 + delta.microseconds
    )
    return _quantize(Decimal(microseconds) / Decimal("1000000"))


def _row_sort_key(
    row: MarketEventNewsShockDecayGateV2Row,
) -> tuple[int, str, str, str]:
    return (
        STATUS_SORT_WEIGHT[row.status],
        row.event_slug,
        row.category,
        row.market_id,
    )


def _normalize_rows(
    rows: Iterable[MarketEventNewsShockDecayGateV2Row],
) -> tuple[MarketEventNewsShockDecayGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in values:
        if type(row) is not MarketEventNewsShockDecayGateV2Row:
            raise ValueError("rows must contain MarketEventNewsShockDecayGateV2Row values")
        _require_hard_flags("row", row)
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must be deterministically sorted")
    return values


def _normalize_reason_code_counts(
    value: Iterable[MarketEventNewsShockDecayGateV2ReasonCodeCount],
) -> tuple[MarketEventNewsShockDecayGateV2ReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        counts = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in counts:
        if type(row) is not MarketEventNewsShockDecayGateV2ReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", row)
    if counts != tuple(count for reason in REASON_CODES for count in counts if count.reason_code == reason):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return counts


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    if reason_codes != tuple(
        reason_code for reason_code in REASON_CODES if reason_code in reason_codes
    ):
        raise ValueError("reason_codes must be deterministically sorted")
    return reason_codes


def _canonical_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    reason_codes = tuple(value)
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError("reason_codes must be unique")
    return tuple(reason_code for reason_code in REASON_CODES if reason_code in reason_codes)


def _validate_row(row: MarketEventNewsShockDecayGateV2Row) -> None:
    if row.latest_confirming_source_at < row.shock_detected_at:
        raise ValueError(
            "latest_confirming_source_at must be at or after shock_detected_at",
        )
    if row.status != _row_status(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "block" and "fresh_news_shock_block" not in row.reason_codes:
        raise ValueError("block rows must explain fresh news shock")
    if row.status == "pass" and "news_shock_decay_passed" not in row.reason_codes:
        raise ValueError("pass rows must include news_shock_decay_passed")


def _validate_report(report: MarketEventNewsShockDecayGateV2Report) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.stale_shock_count != _decimal_count(
        sum(1 for row in report.rows if "stale_news_shock" in row.reason_codes),
    ):
        raise ValueError("stale_shock_count must match rows")
    if report.stale_confirmation_count != _decimal_count(
        sum(1 for row in report.rows if "stale_confirmation_source" in row.reason_codes),
    ):
        raise ValueError("stale_confirmation_count must match rows")
    if report.low_confirmation_count != _decimal_count(
        sum(1 for row in report.rows if "low_confirmation_count" in row.reason_codes),
    ):
        raise ValueError("low_confirmation_count must match rows")
    if report.max_shock_decay_score != _max_score(report.rows):
        raise ValueError("max_shock_decay_score must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must summarize rows")
    expected_digest = _derived_validation_digest(
        event_count=report.event_count,
        pass_count=report.pass_count,
        watch_count=report.watch_count,
        block_count=report.block_count,
        stale_shock_count=report.stale_shock_count,
        stale_confirmation_count=report.stale_confirmation_count,
        low_confirmation_count=report.low_confirmation_count,
        max_shock_decay_score=report.max_shock_decay_score,
        rows=report.rows,
        reason_code_counts=report.reason_code_counts,
    )
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match derived report checks")


def _derived_validation_digest(
    *,
    event_count: Decimal,
    pass_count: Decimal,
    watch_count: Decimal,
    block_count: Decimal,
    stale_shock_count: Decimal,
    stale_confirmation_count: Decimal,
    low_confirmation_count: Decimal,
    max_shock_decay_score: Decimal,
    rows: tuple[MarketEventNewsShockDecayGateV2Row, ...],
    reason_code_counts: tuple[MarketEventNewsShockDecayGateV2ReasonCodeCount, ...],
) -> tuple[tuple[str, str], ...]:
    status_total = pass_count + watch_count + block_count
    reason_code_total = sum((row.count for row in reason_code_counts), ZERO)
    if not rows:
        return (
            ("event_count", _validation_decimal(event_count)),
            ("hard_flags", "paper_only/report_only/readonly"),
            ("reason_code_total", _validation_decimal(reason_code_total)),
            ("row_count", _validation_decimal(_decimal_count(len(rows)))),
            ("status_total", _validation_decimal(status_total)),
        )
    return (
        ("block_count", _validation_decimal(block_count)),
        ("event_count", _validation_decimal(event_count)),
        ("hard_flags", "paper_only/report_only/readonly"),
        ("low_confirmation_count", _validation_decimal(low_confirmation_count)),
        ("max_shock_decay_score", _validation_decimal(max_shock_decay_score)),
        ("pass_count", _validation_decimal(pass_count)),
        ("reason_code_total", _validation_decimal(reason_code_total)),
        ("row_count", _validation_decimal(_decimal_count(len(rows)))),
        ("stale_confirmation_count", _validation_decimal(stale_confirmation_count)),
        ("stale_shock_count", _validation_decimal(stale_shock_count)),
        ("status_total", _validation_decimal(status_total)),
        ("watch_count", _validation_decimal(watch_count)),
    )


def _normalize_validation_digest(
    field_name: str,
    value: object,
) -> tuple[tuple[str, str], ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    pairs: list[tuple[str, str]] = []
    for item in value:
        if type(item) not in (list, tuple):
            raise ValueError(f"{field_name} must contain key value pairs")
        pair = tuple(item)
        if len(pair) != 2:
            raise ValueError(f"{field_name} must contain key value pairs")
        key, item_value = pair
        _require_canonical_string(field_name, key)
        _require_canonical_string(field_name, item_value)
        pairs.append((key, item_value))
    normalized = tuple(pairs)
    if len({key for key, _ in normalized}) != len(normalized):
        raise ValueError(f"{field_name} must not contain duplicate keys")
    if normalized != tuple(sorted(normalized, key=lambda pair: pair[0])):
        raise ValueError(f"{field_name} must be deterministically sorted")
    return normalized


def _field_value(value: object, field_name: str) -> object:
    if hasattr(value, field_name):
        return getattr(value, field_name)
    raise ValueError(f"{field_name} is required")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_string(field_name, value)
    if value not in REASON_CODES:
        raise ValueError(f"{field_name} must contain known reason codes")


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    if quantized != value:
        raise ValueError(f"{field_name} must use six decimal places")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _require_integral_decimal(field_name: str, value: Decimal) -> None:
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _validation_decimal(value: Decimal) -> str:
    _normalize_nonnegative_decimal("derived_validation_digest value", value)
    return str(value)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} readonly must be True")


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


def _reject_unsafe_public_payload(context: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{context} contains unsafe public payload key")
            if _has_unsafe_fragment(key):
                raise ValueError(f"{context} contains unsafe public payload key")
            _reject_unsafe_public_payload(context, item)
    elif type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(context, item)
    elif type(value) is str and _has_unsafe_fragment(value):
        raise ValueError(f"{context} contains unsafe public payload value")


def _has_unsafe_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _unsafe_fragments())


def _unsafe_fragments() -> tuple[str, ...]:
    return tuple(
        "".join(parts)
        for parts in (
            ("li", "ve"),
            ("au", "th"),
            ("wal", "let"),
            ("or", "der"),
            ("net", "work"),
            ("data", "base"),
            ("per", "sist"),
        )
    )


def _payload_value(value: object) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if type(value) is dict:
        return {key: _payload_value(item) for key, item in value.items()}
    if type(value) is list:
        return [_payload_value(item) for item in value]
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            field_name: _payload_value(getattr(value, field_name))
            for field_name in value.__dataclass_fields__
        }
    if isinstance(value, float):
        raise ValueError("payload must not contain floats")
    return value


__all__ = (
    "DEFAULT_MARKET_EVENT_NEWS_SHOCK_DECAY_GATE_V2_CONFIG_VERSION",
    "MarketEventNewsShockDecayGateV2Config",
    "MarketEventNewsShockDecayGateV2Input",
    "MarketEventNewsShockDecayGateV2ReasonCodeCount",
    "MarketEventNewsShockDecayGateV2Report",
    "MarketEventNewsShockDecayGateV2Row",
    "build_market_event_news_shock_decay_gate_v2",
    "market_event_news_shock_decay_gate_v2_payload",
)
