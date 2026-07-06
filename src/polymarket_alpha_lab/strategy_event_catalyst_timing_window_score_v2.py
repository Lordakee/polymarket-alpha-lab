"""Pure Phase 1 catalyst timing window score report."""

from __future__ import annotations

from collections.abc import Iterable as _Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json


DEFAULT_STRATEGY_EVENT_CATALYST_TIMING_WINDOW_SCORE_V2_CONFIG_VERSION = (
    "strategy-event-catalyst-timing-window-score-v2"
)

_QUANT = Decimal("0.000001")
_COUNT_QUANT = Decimal("1")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_WATCH = Decimal("0.500000")
_SECONDS_PER_HOUR = Decimal("3600.000000")
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

_STATUSES = ("pass", "watch", "blocked")
_EMPTY_REPORT_REASON = "catalyst_timing_window_score_empty"
_PASS_REPORT_REASON = "catalyst_timing_window_score_passed"
_BLOCK_REPORT_REASON = "catalyst_timing_window_score_blocked_rows"
_WATCH_REPORT_REASON = "catalyst_timing_window_score_watch_rows"

_UNSAFE_PUBLIC_TEXT_FRAGMENTS = (
    "live",
    "auth",
    "wallet",
    "order",
    "network",
    "database",
    "persist",
    "signing",
    "mutation",
    "buy",
    "sell",
    "trade",
)


@dataclass(frozen=True)
class StrategyEventCatalystTimingWindowScoreV2Config:
    config_version: str = (
        DEFAULT_STRATEGY_EVENT_CATALYST_TIMING_WINDOW_SCORE_V2_CONFIG_VERSION
    )
    min_pass_event_lead_hours: Decimal = Decimal("24.000000")
    min_watch_event_lead_hours: Decimal = Decimal("6.000000")
    max_pass_catalyst_age_hours: Decimal = Decimal("6.000000")
    max_watch_catalyst_age_hours: Decimal = Decimal("24.000000")
    min_pass_catalyst_strength_score: Decimal = Decimal("0.700000")
    min_watch_catalyst_strength_score: Decimal = Decimal("0.400000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyEventCatalystTimingWindowScoreV2Config:
            raise TypeError(
                "StrategyEventCatalystTimingWindowScoreV2Config does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventCatalystTimingWindowScoreV2Config:
            raise ValueError(
                "config must be exactly StrategyEventCatalystTimingWindowScoreV2Config",
            )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_STRATEGY_EVENT_CATALYST_TIMING_WINDOW_SCORE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported version")
        for field_name in (
            "min_pass_event_lead_hours",
            "min_watch_event_lead_hours",
            "max_pass_catalyst_age_hours",
            "max_watch_catalyst_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_catalyst_strength_score",
            "min_watch_catalyst_strength_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _validate_config(self)
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyEventCatalystTimingWindowScoreV2Input:
    candidate_reference: str
    market_slug: str
    evaluated_at: datetime
    event_start_at: datetime
    catalyst_observed_at: datetime
    catalyst_strength_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyEventCatalystTimingWindowScoreV2Input:
            raise TypeError(
                "StrategyEventCatalystTimingWindowScoreV2Input does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventCatalystTimingWindowScoreV2Input:
            raise ValueError(
                "input must be exactly StrategyEventCatalystTimingWindowScoreV2Input",
            )
        object.__setattr__(
            self,
            "candidate_reference",
            _require_public_string("candidate_reference", self.candidate_reference),
        )
        object.__setattr__(
            self,
            "market_slug",
            _require_public_string("market_slug", self.market_slug),
        )
        for field_name in ("evaluated_at", "event_start_at", "catalyst_observed_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "catalyst_strength_score",
            _normalize_ratio_decimal(
                "catalyst_strength_score",
                self.catalyst_strength_score,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyEventCatalystTimingWindowScoreV2Row:
    redacted_candidate_reference: str
    market_slug: str
    evaluated_at: datetime
    event_start_at: datetime
    catalyst_observed_at: datetime
    catalyst_strength_score: Decimal
    hours_until_event: Decimal
    catalyst_age_hours: Decimal
    catalyst_window_score: Decimal
    stale_catalyst_decay_score: Decimal
    near_resolution_risk_score: Decimal
    catalyst_timing_window_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyEventCatalystTimingWindowScoreV2Row:
            raise TypeError(
                "StrategyEventCatalystTimingWindowScoreV2Row does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventCatalystTimingWindowScoreV2Row:
            raise ValueError(
                "row must be exactly StrategyEventCatalystTimingWindowScoreV2Row",
            )
        _require_redacted_reference(self.redacted_candidate_reference)
        object.__setattr__(
            self,
            "market_slug",
            _require_public_string("market_slug", self.market_slug),
        )
        for field_name in ("evaluated_at", "event_start_at", "catalyst_observed_at"):
            object.__setattr__(
                self,
                field_name,
                _as_utc(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "catalyst_strength_score",
            _normalize_ratio_decimal(
                "catalyst_strength_score",
                self.catalyst_strength_score,
            ),
        )
        for field_name in (
            "hours_until_event",
            "catalyst_age_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "catalyst_window_score",
            "stale_catalyst_decay_score",
            "near_resolution_risk_score",
            "catalyst_timing_window_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyEventCatalystTimingWindowScoreV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    average_catalyst_timing_window_score: Decimal
    top_catalyst_timing_window_score: Decimal
    min_hours_until_event: Decimal | None
    max_catalyst_age_hours: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not StrategyEventCatalystTimingWindowScoreV2Report:
            raise TypeError(
                "StrategyEventCatalystTimingWindowScoreV2Report does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not StrategyEventCatalystTimingWindowScoreV2Report:
            raise ValueError(
                "report must be exactly StrategyEventCatalystTimingWindowScoreV2Report",
            )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_string("config_version", self.config_version),
        )
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_catalyst_timing_window_score",
            "top_catalyst_timing_window_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_hours_until_event", "max_catalyst_age_hours"):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _derived_validation_digest(self)
        if self.derived_validation_digest:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)

    @property
    def payload(self) -> dict[str, object]:
        return strategy_event_catalyst_timing_window_score_v2_payload(self)


def build_strategy_event_catalyst_timing_window_score_v2(
    candidates: _Iterable[object],
    *,
    config: StrategyEventCatalystTimingWindowScoreV2Config,
    generated_at: datetime,
) -> StrategyEventCatalystTimingWindowScoreV2Report:
    if type(config) is not StrategyEventCatalystTimingWindowScoreV2Config:
        raise ValueError(
            "config must be a StrategyEventCatalystTimingWindowScoreV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_candidates(candidates)
    rows = tuple(
        sorted(
            (
                _build_row(candidate, config=config, generated_at=generated_at_utc)
                for candidate in inputs
            ),
            key=lambda row: (row.market_slug, row.redacted_candidate_reference),
        ),
    )
    status = _report_status(rows)
    return StrategyEventCatalystTimingWindowScoreV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count_decimal(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        average_catalyst_timing_window_score=_average_row_score(rows),
        top_catalyst_timing_window_score=_top_row_score(rows),
        min_hours_until_event=_min_row_decimal(rows, "hours_until_event"),
        max_catalyst_age_hours=_max_row_decimal(rows, "catalyst_age_hours"),
        status=status,
        reason_codes=_report_reason_codes(rows, status),
        rows=rows,
    )


def strategy_event_catalyst_timing_window_score_v2_payload(
    report: StrategyEventCatalystTimingWindowScoreV2Report,
) -> dict[str, object]:
    if type(report) is not StrategyEventCatalystTimingWindowScoreV2Report:
        raise ValueError(
            "report must be a StrategyEventCatalystTimingWindowScoreV2Report",
        )
    _require_hard_flags("report", report)
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("payload must be a mapping")
    validate_strategy_event_catalyst_timing_window_score_v2_public_payload(payload)
    return payload


def validate_strategy_event_catalyst_timing_window_score_v2_public_payload(
    value: object,
) -> None:
    _reject_unsafe_public_payload("public payload", value)


def _build_row(
    candidate: StrategyEventCatalystTimingWindowScoreV2Input,
    *,
    config: StrategyEventCatalystTimingWindowScoreV2Config,
    generated_at: datetime,
) -> StrategyEventCatalystTimingWindowScoreV2Row:
    _validate_candidate_times(candidate, generated_at)
    hours_until_event = max(_hours_between(generated_at, candidate.event_start_at), _ZERO)
    catalyst_age_hours = _hours_between(candidate.catalyst_observed_at, generated_at)
    catalyst_window_score = _high_good_score(
        hours_until_event,
        pass_floor=config.min_pass_event_lead_hours,
        watch_floor=config.min_watch_event_lead_hours,
    )
    stale_catalyst_decay_score = _low_good_score(
        catalyst_age_hours,
        pass_ceiling=config.max_pass_catalyst_age_hours,
        watch_ceiling=config.max_watch_catalyst_age_hours,
    )
    near_resolution_risk_score = _high_good_score(
        hours_until_event,
        pass_floor=config.min_pass_event_lead_hours,
        watch_floor=config.min_watch_event_lead_hours,
    )
    score = _average_decimal(
        (
            catalyst_window_score,
            stale_catalyst_decay_score,
            near_resolution_risk_score,
            candidate.catalyst_strength_score,
        ),
    )
    reason_codes = _stable_reason_codes(
        (
            *candidate.reason_codes,
            _component_reason(
                "catalyst_window",
                catalyst_window_score,
            ),
            _component_reason(
                "stale_catalyst_decay",
                stale_catalyst_decay_score,
            ),
            _component_reason(
                "near_resolution_risk",
                near_resolution_risk_score,
            ),
            _component_reason(
                "catalyst_strength",
                _high_good_score(
                    candidate.catalyst_strength_score,
                    pass_floor=config.min_pass_catalyst_strength_score,
                    watch_floor=config.min_watch_catalyst_strength_score,
                ),
            ),
        ),
    )
    return StrategyEventCatalystTimingWindowScoreV2Row(
        redacted_candidate_reference=_redacted_reference(candidate.candidate_reference),
        market_slug=candidate.market_slug,
        evaluated_at=candidate.evaluated_at,
        event_start_at=candidate.event_start_at,
        catalyst_observed_at=candidate.catalyst_observed_at,
        catalyst_strength_score=candidate.catalyst_strength_score,
        hours_until_event=hours_until_event,
        catalyst_age_hours=catalyst_age_hours,
        catalyst_window_score=catalyst_window_score,
        stale_catalyst_decay_score=stale_catalyst_decay_score,
        near_resolution_risk_score=near_resolution_risk_score,
        catalyst_timing_window_score=score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _validate_candidate_times(
    candidate: StrategyEventCatalystTimingWindowScoreV2Input,
    generated_at: datetime,
) -> None:
    if candidate.evaluated_at > generated_at:
        raise ValueError("evaluated_at must not be after generated_at")
    if candidate.catalyst_observed_at > generated_at:
        raise ValueError("catalyst_observed_at must not be after generated_at")


def _component_reason(prefix: str, score: Decimal) -> str:
    if score == _ONE:
        return f"{prefix}_pass"
    if score == _WATCH:
        return f"{prefix}_watch"
    return f"{prefix}_blocked"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_blocked") for code in reason_codes):
        return "blocked"
    if any(code.endswith("_watch") for code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...],
) -> str:
    if not rows:
        return "blocked"
    if any(row.status == "blocked" for row in rows):
        return "blocked"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REPORT_REASON,)
    if status == "blocked":
        return (_BLOCK_REPORT_REASON,)
    if status == "watch":
        return (_WATCH_REPORT_REASON,)
    return (_PASS_REPORT_REASON,)


def _status_count(
    rows: tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _average_row_score(
    rows: tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _average_decimal(tuple(row.catalyst_timing_window_score for row in rows))


def _top_row_score(
    rows: tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return max(row.catalyst_timing_window_score for row in rows)


def _min_row_decimal(
    rows: tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return min(getattr(row, field_name) for row in rows)


def _max_row_decimal(
    rows: tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    return max(getattr(row, field_name) for row in rows)


def _validate_config(config: StrategyEventCatalystTimingWindowScoreV2Config) -> None:
    if config.min_watch_event_lead_hours > config.min_pass_event_lead_hours:
        raise ValueError("min_watch_event_lead_hours must not exceed pass threshold")
    if config.max_pass_catalyst_age_hours > config.max_watch_catalyst_age_hours:
        raise ValueError("max_pass_catalyst_age_hours must not exceed watch threshold")
    if config.min_watch_catalyst_strength_score > config.min_pass_catalyst_strength_score:
        raise ValueError(
            "min_watch_catalyst_strength_score must not exceed pass threshold",
        )


def _validate_row(row: StrategyEventCatalystTimingWindowScoreV2Row) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.status != expected_status:
        raise ValueError("status must match reason_codes")
    expected_score = _average_decimal(
        (
            row.catalyst_window_score,
            row.stale_catalyst_decay_score,
            row.near_resolution_risk_score,
            row.catalyst_strength_score,
        ),
    )
    if row.catalyst_timing_window_score != expected_score:
        raise ValueError("catalyst_timing_window_score must match component scores")


def _validate_report(report: StrategyEventCatalystTimingWindowScoreV2Report) -> None:
    rows = report.rows
    if report.candidate_count != _count_decimal(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if (
        report.pass_count + report.watch_count + report.blocked_count
        != report.candidate_count
    ):
        raise ValueError("status counts must sum to candidate_count")
    if report.average_catalyst_timing_window_score != _average_row_score(rows):
        raise ValueError("average_catalyst_timing_window_score must match rows")
    if report.top_catalyst_timing_window_score != _top_row_score(rows):
        raise ValueError("top_catalyst_timing_window_score must match rows")
    if report.min_hours_until_event != _min_row_decimal(rows, "hours_until_event"):
        raise ValueError("min_hours_until_event must match rows")
    if report.max_catalyst_age_hours != _max_row_decimal(rows, "catalyst_age_hours"):
        raise ValueError("max_catalyst_age_hours must match rows")
    expected_status = _report_status(rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows, expected_status):
        raise ValueError("reason_codes must match rows")
    expected_rows = tuple(
        sorted(
            rows,
            key=lambda row: (row.market_slug, row.redacted_candidate_reference),
        ),
    )
    if rows != expected_rows:
        raise ValueError("rows must be sorted")


def _normalize_candidates(
    candidates: _Iterable[object],
) -> tuple[StrategyEventCatalystTimingWindowScoreV2Input, ...]:
    if isinstance(candidates, (str, bytes)) or not hasattr(candidates, "__iter__"):
        raise ValueError("candidates must be an iterable")
    normalized = tuple(candidates)
    seen: set[str] = set()
    for candidate in normalized:
        if type(candidate) is not StrategyEventCatalystTimingWindowScoreV2Input:
            raise ValueError(
                "candidates must contain StrategyEventCatalystTimingWindowScoreV2Input",
            )
        _require_hard_flags("input", candidate)
        if candidate.candidate_reference in seen:
            raise ValueError("candidate_reference values must be unique")
        seen.add(candidate.candidate_reference)
    return normalized


def _normalize_rows(
    value: object,
) -> tuple[StrategyEventCatalystTimingWindowScoreV2Row, ...]:
    if type(value) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in value:
        if type(row) is not StrategyEventCatalystTimingWindowScoreV2Row:
            raise ValueError(
                "rows must contain StrategyEventCatalystTimingWindowScoreV2Row",
            )
        _require_hard_flags("row", row)
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical string")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_redacted_reference(value: object) -> None:
    if type(value) is not str:
        raise ValueError("redacted_candidate_reference must be a string")
    prefix = "candidate_ref_"
    digest = value.removeprefix(prefix)
    if (
        value.startswith(prefix)
        and len(digest) == 16
        and all(character in "0123456789abcdef" for character in digest)
    ):
        return
    raise ValueError("redacted_candidate_reference must be redacted")


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    normalized: list[str] = []
    for item in value:
        reason_code = _require_reason_code(field_name, item)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
        normalized.append(reason_code)
    return tuple(normalized)


def _require_reason_code(field_name: str, value: object) -> str:
    _require_public_string(field_name, value)
    if type(value) is not str or value != value.lower():
        raise ValueError(f"{field_name} must contain canonical reason codes")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError(f"{field_name} must contain canonical reason codes")
    return value


def _stable_reason_codes(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    normalized: list[str] = []
    for value in values:
        reason_code = _require_reason_code("reason_codes", value)
        if reason_code not in seen:
            normalized.append(reason_code)
            seen.add(reason_code)
    return tuple(normalized)


def _normalize_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_count_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value != value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    if value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return value.quantize(_COUNT_QUANT)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < _QUANT.as_tuple().exponent:
        raise ValueError(f"{field_name} must not exceed six decimal places")
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANT)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANT)


def _high_good_score(
    value: Decimal,
    *,
    pass_floor: Decimal,
    watch_floor: Decimal,
) -> Decimal:
    if value >= pass_floor:
        return _ONE
    if value >= watch_floor:
        return _WATCH
    return _ZERO


def _low_good_score(
    value: Decimal,
    *,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> Decimal:
    if value <= pass_ceiling:
        return _ONE
    if value <= watch_ceiling:
        return _WATCH
    return _ZERO


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    with localcontext(_DECIMAL_CONTEXT):
        return (sum(values, _ZERO) / Decimal(len(values))).quantize(_QUANT)


def _hours_between(start: datetime, end: datetime) -> Decimal:
    seconds = Decimal(str((end - start).total_seconds()))
    with localcontext(_DECIMAL_CONTEXT):
        return (seconds / _SECONDS_PER_HOUR).quantize(_QUANT)


def _redacted_reference(value: str) -> str:
    digest = sha256(value.encode("utf-8")).hexdigest()[:16]
    return f"candidate_ref_{digest}"


def _require_sha256_digest(field_name: str, value: object) -> None:
    _require_public_string(field_name, value)
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _derived_validation_digest(
    report: StrategyEventCatalystTimingWindowScoreV2Report,
) -> str:
    payload = _payload_value(report, skip_digest=True)
    validate_strategy_event_catalyst_timing_window_score_v2_public_payload(payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _payload_value(value: object, *, skip_digest: bool = False) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        payload: dict[str, object] = {}
        for field in fields(value):
            if field.name.startswith("_"):
                continue
            if skip_digest and field.name == "derived_validation_digest":
                continue
            payload[field.name] = _payload_value(
                getattr(value, field.name),
                skip_digest=skip_digest,
            )
        return payload
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("payload datetime", value).isoformat()
    if type(value) is tuple:
        return [_payload_value(item, skip_digest=skip_digest) for item in value]
    if type(value) is list:
        return [_payload_value(item, skip_digest=skip_digest) for item in value]
    if type(value) is dict:
        return {
            _payload_key(key): _payload_value(item, skip_digest=skip_digest)
            for key, item in value.items()
        }
    if value is None or type(value) in (str, bool):
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric values must be Decimal-derived strings")
    raise ValueError("payload contains unsupported value")


def _payload_key(value: object) -> str:
    if type(value) is not str:
        raise ValueError("payload keys must be strings")
    _reject_unsafe_public_text("payload key", value)
    return value


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"unsafe public payload in {label}")
            _reject_unsafe_public_text(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float) or type(value) is Decimal:
        raise ValueError("public numeric values must be Decimal-derived strings")
    if type(value) is str:
        _reject_unsafe_public_text(label, value)
        return
    raise ValueError(f"unsafe public payload in {label}")


def _reject_unsafe_public_text(label: str, value: str) -> None:
    lowered = value.lower()
    if value.strip() != value:
        raise ValueError(f"unsafe public payload in {label}")
    if "://" in lowered or "?" in lowered:
        raise ValueError(f"unsafe public payload in {label}")
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_TEXT_FRAGMENTS):
        raise ValueError(f"unsafe public payload in {label}")
