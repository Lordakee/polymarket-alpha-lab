"""Pure research scoring for candidate event catalysts."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from typing import Any


__all__ = (
    "ResearchCatalystImpactEventInput",
    "ResearchCatalystImpactReasonCodeCount",
    "ResearchCatalystImpactScoreRow",
    "ResearchCatalystImpactScorerConfig",
    "ResearchCatalystImpactScorerReport",
    "build_research_catalyst_impact_scorer_report",
    "research_catalyst_impact_scorer_report_payload",
)


DEFAULT_CONFIG_VERSION = "research-catalyst-impact-scorer-report-v0"
CATALYST_KINDS = (
    "policy_release",
    "macro_data",
    "sports_node",
    "company_event",
    "chain_event",
    "settlement_window",
)
STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0")
ONE = Decimal("1")
TWO = Decimal("2")
QUANTUM = Decimal("0.000001")
INTEGER_QUANTUM = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)
DEFAULT_PASS_IMPACT_SCORE = Decimal("0.700000")
DEFAULT_WATCH_IMPACT_SCORE = Decimal("0.400000")

_UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate",
    "mar" + "ket",
    "sou" + "rce",
    "u" + "rl",
    "te" + "xt",
    "d" + "sn",
    "ta" + "ble",
    "to" + "ken",
    "://",
)
_RESTRICTED_PUBLIC_FRAGMENTS = (
    "b" + "uy",
    "s" + "ell",
    "pos" + "ition",
    "rec" + "ommend",
)


class _Missing:
    pass


_MISSING = _Missing()


@dataclass(frozen=True)
class ResearchCatalystImpactScorerConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_impact_score: Decimal = DEFAULT_PASS_IMPACT_SCORE
    watch_impact_score: Decimal = DEFAULT_WATCH_IMPACT_SCORE
    min_confirmation_count: Decimal = Decimal("2")
    min_official_confirmation_score: Decimal = Decimal("0.600000")
    min_settlement_buffer_minutes: Decimal = Decimal("30")
    min_reaction_buffer_minutes: Decimal = Decimal("15")
    timing_weight: Decimal = Decimal("0.350000")
    confirmation_weight: Decimal = Decimal("0.250000")
    impact_weight: Decimal = Decimal("0.250000")
    settlement_weight: Decimal = Decimal("0.150000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCatalystImpactScorerConfig:
            raise TypeError(
                "ResearchCatalystImpactScorerConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCatalystImpactScorerConfig:
            raise ValueError("config must be exactly ResearchCatalystImpactScorerConfig")
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_impact_score",
            "watch_impact_score",
            "min_official_confirmation_score",
            "timing_weight",
            "confirmation_weight",
            "impact_weight",
            "settlement_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_impact_score <= self.watch_impact_score:
            raise ValueError("pass_impact_score must be greater than watch_impact_score")
        object.__setattr__(
            self,
            "min_confirmation_count",
            _require_positive_whole_decimal(
                "min_confirmation_count",
                self.min_confirmation_count,
            ),
        )
        for field_name in (
            "min_settlement_buffer_minutes",
            "min_reaction_buffer_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        weight_sum = _quantize(
            self.timing_weight
            + self.confirmation_weight
            + self.impact_weight
            + self.settlement_weight,
        )
        if weight_sum != ONE:
            raise ValueError(
                "timing_weight, confirmation_weight, impact_weight, and "
                "settlement_weight must sum to 1",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_value("config", self, allow_containers=True)


@dataclass(frozen=True)
class ResearchCatalystImpactEventInput:
    event_id: str
    catalyst_kind: str
    time_until_event_minutes: Decimal
    time_until_settlement_minutes: Decimal
    confirmation_count: Decimal
    official_confirmation_score: Decimal
    impact_relevance_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCatalystImpactEventInput:
            raise TypeError(
                "ResearchCatalystImpactEventInput does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCatalystImpactEventInput:
            raise ValueError("event must be exactly ResearchCatalystImpactEventInput")
        _require_public_identifier("event_id", self.event_id)
        _require_member("catalyst_kind", self.catalyst_kind, CATALYST_KINDS)
        for field_name in (
            "time_until_event_minutes",
            "time_until_settlement_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confirmation_count",
            _require_nonnegative_whole_decimal(
                "confirmation_count",
                self.confirmation_count,
            ),
        )
        for field_name in (
            "official_confirmation_score",
            "impact_relevance_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("event", self)
        _reject_unsafe_public_value("event", self, allow_containers=True)


@dataclass(frozen=True)
class ResearchCatalystImpactScoreRow:
    event_id: str
    catalyst_kind: str
    time_until_event_minutes: Decimal
    time_until_settlement_minutes: Decimal
    confirmation_count: Decimal
    official_confirmation_score: Decimal
    impact_relevance_score: Decimal
    timing_score: Decimal
    confirmation_score: Decimal
    settlement_window_score: Decimal
    impact_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCatalystImpactScoreRow:
            raise TypeError(
                "ResearchCatalystImpactScoreRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCatalystImpactScoreRow:
            raise ValueError("row must be exactly ResearchCatalystImpactScoreRow")
        _require_public_identifier("event_id", self.event_id)
        _require_member("catalyst_kind", self.catalyst_kind, CATALYST_KINDS)
        for field_name in (
            "time_until_event_minutes",
            "time_until_settlement_minutes",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confirmation_count",
            _require_nonnegative_whole_decimal(
                "confirmation_count",
                self.confirmation_count,
            ),
        )
        for field_name in (
            "official_confirmation_score",
            "impact_relevance_score",
            "timing_score",
            "confirmation_score",
            "settlement_window_score",
            "impact_score",
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
        _validate_score_row_consistency(self)
        _reject_unsafe_public_value("row", self, allow_containers=True)


@dataclass(frozen=True)
class ResearchCatalystImpactReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCatalystImpactReasonCodeCount:
            raise TypeError(
                "ResearchCatalystImpactReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCatalystImpactReasonCodeCount:
            raise ValueError(
                "reason code count must be exactly "
                "ResearchCatalystImpactReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_whole_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_value("reason_code_count", self, allow_containers=True)


@dataclass(frozen=True)
class ResearchCatalystImpactScorerReport:
    generated_at: datetime
    config_version: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_impact_score: Decimal | None
    status: str
    rows: tuple[ResearchCatalystImpactScoreRow, ...]
    reason_code_counts: tuple[ResearchCatalystImpactReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchCatalystImpactScorerReport:
            raise TypeError(
                "ResearchCatalystImpactScorerReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchCatalystImpactScorerReport:
            raise ValueError("report must be exactly ResearchCatalystImpactScorerReport")
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "event_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_impact_score",
            _require_optional_probability_decimal(
                "average_impact_score",
                self.average_impact_score,
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
        _validate_report_consistency(self)
        _reject_unsafe_public_value("report", self, allow_containers=True)

    @property
    def payload(self) -> dict[str, Any]:
        return research_catalyst_impact_scorer_report_payload(self)


def build_research_catalyst_impact_scorer_report(
    events: Iterable[object],
    *,
    config: ResearchCatalystImpactScorerConfig,
    generated_at: datetime,
) -> ResearchCatalystImpactScorerReport:
    if type(config) is not ResearchCatalystImpactScorerConfig:
        raise ValueError("config must be a ResearchCatalystImpactScorerConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    event_items = _normalize_events(events)
    rows = tuple(
        _score_event(event_item, config=config)
        for event_item in sorted(event_items, key=lambda item: item.event_id)
    )
    reason_codes = _summary_reason_codes(rows)

    return ResearchCatalystImpactScorerReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        event_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_impact_score=_average_impact_score(rows),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_catalyst_impact_scorer_report_payload(
    report: ResearchCatalystImpactScorerReport,
) -> dict[str, Any]:
    if type(report) is not ResearchCatalystImpactScorerReport:
        raise ValueError("report must be a ResearchCatalystImpactScorerReport")
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    _reject_unsafe_public_value("payload", payload, allow_containers=True)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    return payload


def _normalize_events(events: Iterable[object]) -> tuple[ResearchCatalystImpactEventInput, ...]:
    if isinstance(events, (str, bytes)):
        raise ValueError("events must be an iterable")
    try:
        values = tuple(events)
    except TypeError as exc:
        raise ValueError("events must be an iterable") from exc
    return tuple(_coerce_event(value) for value in values)


def _coerce_event(value: object) -> ResearchCatalystImpactEventInput:
    if type(value) is ResearchCatalystImpactEventInput:
        _require_hard_flags("event", value)
        return value
    _require_hard_flags("event", value)
    return ResearchCatalystImpactEventInput(
        event_id=_field_value(value, "event_id"),
        catalyst_kind=_field_value(value, "catalyst_kind"),
        time_until_event_minutes=_field_value(value, "time_until_event_minutes"),
        time_until_settlement_minutes=_field_value(
            value,
            "time_until_settlement_minutes",
        ),
        confirmation_count=_field_value(value, "confirmation_count"),
        official_confirmation_score=_field_value(value, "official_confirmation_score"),
        impact_relevance_score=_field_value(value, "impact_relevance_score"),
        reason_codes=_field_value(value, "reason_codes", default=()),
        paper_only=_field_value(value, "paper_only"),
        report_only=_field_value(value, "report_only"),
        readonly=_field_value(value, "readonly"),
    )


def _score_event(
    event: ResearchCatalystImpactEventInput,
    *,
    config: ResearchCatalystImpactScorerConfig,
) -> ResearchCatalystImpactScoreRow:
    timing_score = _timing_score(event, config)
    confirmation_score = _confirmation_score(event, config)
    settlement_window_score = _settlement_window_score(event, config)
    impact_score = _impact_score(
        timing_score=timing_score,
        confirmation_score=confirmation_score,
        impact_relevance_score=event.impact_relevance_score,
        settlement_window_score=settlement_window_score,
        config=config,
    )
    status = _row_status(
        event,
        impact_score=impact_score,
        timing_score=timing_score,
        config=config,
    )
    return ResearchCatalystImpactScoreRow(
        event_id=event.event_id,
        catalyst_kind=event.catalyst_kind,
        time_until_event_minutes=event.time_until_event_minutes,
        time_until_settlement_minutes=event.time_until_settlement_minutes,
        confirmation_count=event.confirmation_count,
        official_confirmation_score=event.official_confirmation_score,
        impact_relevance_score=event.impact_relevance_score,
        timing_score=timing_score,
        confirmation_score=confirmation_score,
        settlement_window_score=settlement_window_score,
        impact_score=impact_score,
        status=status,
        reason_codes=_row_reason_codes(
            event,
            timing_score=timing_score,
            settlement_window_score=settlement_window_score,
            status=status,
            config=config,
        ),
    )


def _timing_score(
    event: ResearchCatalystImpactEventInput,
    config: ResearchCatalystImpactScorerConfig,
) -> Decimal:
    if event.time_until_event_minutes >= event.time_until_settlement_minutes:
        return ZERO
    if event.time_until_event_minutes < config.min_reaction_buffer_minutes:
        return _quantize(event.time_until_event_minutes / config.min_reaction_buffer_minutes)
    return ONE


def _confirmation_score(
    event: ResearchCatalystImpactEventInput,
    config: ResearchCatalystImpactScorerConfig,
) -> Decimal:
    count_score = min(ONE, event.confirmation_count / config.min_confirmation_count)
    return _quantize((count_score + event.official_confirmation_score) / TWO)


def _settlement_window_score(
    event: ResearchCatalystImpactEventInput,
    config: ResearchCatalystImpactScorerConfig,
) -> Decimal:
    if event.time_until_event_minutes >= event.time_until_settlement_minutes:
        return ZERO
    remaining_after_event = event.time_until_settlement_minutes - event.time_until_event_minutes
    if remaining_after_event < config.min_settlement_buffer_minutes:
        return _quantize(remaining_after_event / config.min_settlement_buffer_minutes)
    return ONE


def _impact_score(
    *,
    timing_score: Decimal,
    confirmation_score: Decimal,
    impact_relevance_score: Decimal,
    settlement_window_score: Decimal,
    config: ResearchCatalystImpactScorerConfig,
) -> Decimal:
    return _quantize(
        (timing_score * config.timing_weight)
        + (confirmation_score * config.confirmation_weight)
        + (impact_relevance_score * config.impact_weight)
        + (settlement_window_score * config.settlement_weight),
    )


def _row_status(
    event: ResearchCatalystImpactEventInput,
    *,
    impact_score: Decimal,
    timing_score: Decimal,
    config: ResearchCatalystImpactScorerConfig,
) -> str:
    if timing_score == ZERO or impact_score < config.watch_impact_score:
        return "block"
    if impact_score < config.pass_impact_score:
        return "watch"
    if event.confirmation_count < config.min_confirmation_count:
        return "watch"
    if event.official_confirmation_score < config.min_official_confirmation_score:
        return "watch"
    return "pass"


def _row_reason_codes(
    event: ResearchCatalystImpactEventInput,
    *,
    timing_score: Decimal,
    settlement_window_score: Decimal,
    status: str,
    config: ResearchCatalystImpactScorerConfig,
) -> tuple[str, ...]:
    reason_codes: list[str] = [f"research_catalyst_impact_{status}"]
    if event.time_until_event_minutes >= event.time_until_settlement_minutes:
        reason_codes.append(f"{event.catalyst_kind}_after_settlement")
    elif timing_score < ONE:
        reason_codes.append("inside_reaction_buffer")
    else:
        reason_codes.append(f"{event.catalyst_kind}_timing_aligned")

    if event.confirmation_count < config.min_confirmation_count:
        reason_codes.append("confirmation_below_threshold")
    else:
        reason_codes.append("confirmation_threshold_met")

    if event.official_confirmation_score < config.min_official_confirmation_score:
        reason_codes.append("official_confirmation_low")
    else:
        reason_codes.append("official_confirmation_met")

    if event.impact_relevance_score >= config.pass_impact_score:
        reason_codes.append("impact_relevance_high")
    elif event.impact_relevance_score >= config.watch_impact_score:
        reason_codes.append("impact_relevance_medium")
    else:
        reason_codes.append("impact_relevance_low")

    if settlement_window_score == ZERO:
        reason_codes.append("settlement_window_closed")
    elif settlement_window_score < ONE:
        reason_codes.append("settlement_window_tight")
    else:
        reason_codes.append("settlement_window_clear")

    reason_codes.extend(f"input_{reason_code}" for reason_code in event.reason_codes)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(reason_codes),
        allow_empty=False,
    )


def _summary_reason_codes(
    rows: tuple[ResearchCatalystImpactScoreRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_research_events",)
    if any(row.status == "block" for row in rows):
        return tuple(sorted({code for row in rows for code in row.reason_codes}))
    if all(row.status == "pass" for row in rows):
        return ("research_catalyst_impact_pass",)
    return tuple(sorted({code for row in rows for code in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("no_research_events",):
        return "block"
    if "research_catalyst_impact_block" in reason_codes:
        return "block"
    if "research_catalyst_impact_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchCatalystImpactScoreRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchCatalystImpactReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchCatalystImpactReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchCatalystImpactReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _average_impact_score(
    rows: tuple[ResearchCatalystImpactScoreRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.impact_score for row in rows), ZERO) / Decimal(len(rows)))


def _status_count(rows: tuple[ResearchCatalystImpactScoreRow, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _normalize_rows(
    rows: object,
) -> tuple[ResearchCatalystImpactScoreRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchCatalystImpactScoreRow:
            raise ValueError("rows must contain ResearchCatalystImpactScoreRow values")
        _require_hard_flags("row", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.event_id))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted by event_id")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchCatalystImpactReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchCatalystImpactReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchCatalystImpactReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda count: count.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _validate_score_row_consistency(row: ResearchCatalystImpactScoreRow) -> None:
    if row.time_until_event_minutes >= row.time_until_settlement_minutes:
        if row.timing_score != ZERO or row.settlement_window_score != ZERO:
            raise ValueError("timing_score must match event and settlement timing")
    if row.status == "pass" and row.impact_score < DEFAULT_PASS_IMPACT_SCORE:
        raise ValueError("impact_score must support pass status")
    if row.status == "watch" and row.impact_score < DEFAULT_WATCH_IMPACT_SCORE:
        raise ValueError("impact_score must support watch status")
    if row.status == "block" and row.impact_score >= DEFAULT_PASS_IMPACT_SCORE:
        if f"{row.catalyst_kind}_after_settlement" not in row.reason_codes:
            raise ValueError("impact_score must support block status")


def _validate_report_consistency(report: ResearchCatalystImpactScorerReport) -> None:
    if report.event_count != _decimal_count(len(report.rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_impact_score != _average_impact_score(report.rows):
        raise ValueError("average_impact_score must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _payload_value(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _payload_value(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, tuple):
        return [_payload_value(item) for item in value]
    if isinstance(value, list):
        return [_payload_value(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _payload_value(item) for key, item in value.items()}
    return value


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
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


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return _quantize(decimal)


def _require_positive_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if decimal != decimal.quantize(INTEGER_QUANTUM):
        raise ValueError(f"{field_name} must be a whole count")
    return decimal


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_nonnegative_decimal(field_name, value)
    if decimal != decimal.quantize(INTEGER_QUANTUM):
        raise ValueError(f"{field_name} must be a whole count")
    return decimal


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    decimal = _require_decimal(field_name, value)
    if decimal < ZERO or decimal > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal)


def _require_optional_probability_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_probability_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count value must be an int")
    if value < 0:
        raise ValueError("count value must be nonnegative")
    return Decimal(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    _reject_unsafe_string(field_name, value)


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonempty canonical string")
    if value.lower() != value:
        raise ValueError(f"{field_name} must be lowercase")
    for char in value:
        if not (char.islower() or char.isdigit() or char == "_"):
            raise ValueError(f"{field_name} must use lowercase snake case")
    _reject_unsafe_string(field_name, value)


def _require_member(
    field_name: str,
    value: object,
    allowed_values: tuple[str, ...],
) -> None:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be one of {allowed_values}")
    _reject_unsafe_string(field_name, value)


def _require_status(field_name: str, value: object) -> None:
    _require_member(field_name, value, STATUSES)


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


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = _field_value(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _reject_unsafe_public_value(
    label: str,
    value: object,
    *,
    allow_containers: bool,
) -> None:
    if isinstance(value, str):
        _reject_unsafe_string(label, value)
        return
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_string(label, field.name)
            _reject_unsafe_public_value(
                label,
                getattr(value, field.name),
                allow_containers=True,
            )
        return
    if allow_containers and isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_public_value(label, str(key), allow_containers=True)
            _reject_unsafe_public_value(label, item, allow_containers=True)
        return
    if allow_containers and isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_value(label, item, allow_containers=True)


def _reject_unsafe_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public content")
    if any(fragment in lowered for fragment in _RESTRICTED_PUBLIC_FRAGMENTS):
        raise ValueError(f"{field_name} contains restricted research language")
