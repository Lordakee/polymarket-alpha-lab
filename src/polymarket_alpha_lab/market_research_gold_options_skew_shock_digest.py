"""Pure Phase 1 gold options skew shock digest reducer."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
import re
from typing import Any


DEFAULT_MARKET_RESEARCH_GOLD_OPTIONS_SKEW_SHOCK_DIGEST_CONFIG_VERSION = (
    "market-research-gold-options-skew-shock-digest-v0"
)

SKEW_DIRECTIONS = ("put_skew_widening", "call_skew_widening", "inline")
SHOCK_STATUSES = ("pass", "watch", "blocked")
INPUT_REASON_CODES = (
    "gold_options_put_skew_widened",
    "gold_options_call_skew_widened",
    "gold_options_skew_inline",
)
ROW_REASON_CODES = (
    "gold_options_put_skew_shock_blocked",
    "gold_options_call_skew_shock_blocked",
    "gold_options_put_skew_shock_watch",
    "gold_options_call_skew_shock_watch",
    "gold_options_skew_shock_inline",
)
REPORT_REASON_CODES = (
    "gold_options_skew_shock_digest_clear",
    "gold_options_skew_shock_blocked_present",
    "gold_options_skew_shock_watch_present",
    "gold_options_skew_shock_mixed_direction_present",
    "gold_options_put_skew_shock_present",
    "gold_options_call_skew_shock_present",
)

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO_COUNT = Decimal("0")
ZERO_RATIO = Decimal("0.000000")
ONE_RATIO = Decimal("1.000000")
WATCH_ABS_SKEW_SHOCK_RATIO = Decimal("0.020000")
BLOCKED_ABS_SKEW_SHOCK_RATIO = Decimal("0.050000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUS_WEIGHT = {
    "blocked": Decimal("2"),
    "watch": Decimal("1"),
    "pass": Decimal("0"),
}
_CANONICAL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]*$")


__all__ = (
    "DEFAULT_MARKET_RESEARCH_GOLD_OPTIONS_SKEW_SHOCK_DIGEST_CONFIG_VERSION",
    "GoldOptionsSkewShockDigestConfig",
    "GoldOptionsSkewShockObservation",
    "GoldOptionsSkewShockDigestRow",
    "GoldOptionsSkewShockDigestReport",
    "build_market_research_gold_options_skew_shock_digest",
    "market_research_gold_options_skew_shock_digest_payload",
)


@dataclass(frozen=True)
class GoldOptionsSkewShockDigestConfig:
    config_version: str = (
        DEFAULT_MARKET_RESEARCH_GOLD_OPTIONS_SKEW_SHOCK_DIGEST_CONFIG_VERSION
    )
    watch_abs_skew_shock_ratio: Decimal = WATCH_ABS_SKEW_SHOCK_RATIO
    blocked_abs_skew_shock_ratio: Decimal = BLOCKED_ABS_SKEW_SHOCK_RATIO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not GoldOptionsSkewShockDigestConfig:
            raise TypeError(
                "GoldOptionsSkewShockDigestConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not GoldOptionsSkewShockDigestConfig:
            raise ValueError(
                "config must be exactly GoldOptionsSkewShockDigestConfig",
            )
        _require_canonical_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_MARKET_RESEARCH_GOLD_OPTIONS_SKEW_SHOCK_DIGEST_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        object.__setattr__(
            self,
            "watch_abs_skew_shock_ratio",
            _normalize_positive_ratio(
                "watch_abs_skew_shock_ratio",
                self.watch_abs_skew_shock_ratio,
            ),
        )
        object.__setattr__(
            self,
            "blocked_abs_skew_shock_ratio",
            _normalize_positive_ratio(
                "blocked_abs_skew_shock_ratio",
                self.blocked_abs_skew_shock_ratio,
            ),
        )
        if self.blocked_abs_skew_shock_ratio < self.watch_abs_skew_shock_ratio:
            raise ValueError(
                "blocked_abs_skew_shock_ratio must be at least watch threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class GoldOptionsSkewShockObservation:
    source_id: str
    market_slug: str
    expiry_bucket: str
    put_delta_25_iv: Decimal
    call_delta_25_iv: Decimal
    atm_iv: Decimal
    previous_skew_ratio: Decimal
    source_row_count: Decimal
    observed_at: datetime
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not GoldOptionsSkewShockObservation:
            raise TypeError(
                "GoldOptionsSkewShockObservation does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not GoldOptionsSkewShockObservation:
            raise ValueError(
                "observation must be exactly GoldOptionsSkewShockObservation",
            )
        for field_name in ("source_id", "market_slug", "expiry_bucket"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("put_delta_25_iv", "call_delta_25_iv", "atm_iv"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "previous_skew_ratio",
            _normalize_signed_ratio("previous_skew_ratio", self.previous_skew_ratio),
        )
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                INPUT_REASON_CODES,
            ),
        )
        _validate_observation(self)
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class GoldOptionsSkewShockDigestRow:
    source_id: str
    market_slug: str
    expiry_bucket: str
    put_delta_25_iv: Decimal
    call_delta_25_iv: Decimal
    atm_iv: Decimal
    previous_skew_ratio: Decimal
    skew_ratio: Decimal
    skew_shock_ratio: Decimal
    abs_skew_shock_ratio: Decimal
    screening_priority_score: Decimal
    source_row_count: Decimal
    observed_at: datetime
    skew_direction: str
    shock_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not GoldOptionsSkewShockDigestRow:
            raise TypeError(
                "GoldOptionsSkewShockDigestRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not GoldOptionsSkewShockDigestRow:
            raise ValueError("row must be exactly GoldOptionsSkewShockDigestRow")
        for field_name in ("source_id", "market_slug", "expiry_bucket"):
            _require_canonical_string(field_name, getattr(self, field_name))
        for field_name in ("put_delta_25_iv", "call_delta_25_iv", "atm_iv"):
            object.__setattr__(
                self,
                field_name,
                _normalize_positive_ratio(field_name, getattr(self, field_name)),
            )
        for field_name in ("previous_skew_ratio", "skew_ratio", "skew_shock_ratio"):
            object.__setattr__(
                self,
                field_name,
                _normalize_signed_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "abs_skew_shock_ratio",
            _normalize_ratio("abs_skew_shock_ratio", self.abs_skew_shock_ratio),
        )
        object.__setattr__(
            self,
            "screening_priority_score",
            _normalize_ratio("screening_priority_score", self.screening_priority_score),
        )
        if self.screening_priority_score > ONE_RATIO:
            raise ValueError("screening_priority_score must not exceed one")
        object.__setattr__(
            self,
            "source_row_count",
            _normalize_nonnegative_count("source_row_count", self.source_row_count),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        _require_member("skew_direction", self.skew_direction, SKEW_DIRECTIONS)
        _require_member("shock_status", self.shock_status, SHOCK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class GoldOptionsSkewShockDigestReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    max_abs_skew_shock_ratio: Decimal
    average_skew_shock_ratio: Decimal
    top_screening_priority_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    shock_rows: tuple[GoldOptionsSkewShockDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not GoldOptionsSkewShockDigestReport:
            raise TypeError(
                "GoldOptionsSkewShockDigestReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not GoldOptionsSkewShockDigestReport:
            raise ValueError("report must be exactly GoldOptionsSkewShockDigestReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "source_row_count",
            "observation_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_abs_skew_shock_ratio",
            "top_screening_priority_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_ratio(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_skew_shock_ratio",
            _normalize_signed_ratio(
                "average_skew_shock_ratio",
                self.average_skew_shock_ratio,
            ),
        )
        if self.top_screening_priority_score > ONE_RATIO:
            raise ValueError("top_screening_priority_score must not exceed one")
        _require_member("digest_status", self.digest_status, SHOCK_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
        )
        object.__setattr__(
            self,
            "shock_rows",
            _normalize_rows(self.shock_rows),
        )
        _validate_report(self)
        _require_hard_flags("report", self)


def build_market_research_gold_options_skew_shock_digest(
    observations: tuple[GoldOptionsSkewShockObservation, ...],
    *,
    config: GoldOptionsSkewShockDigestConfig | None = None,
    generated_at: datetime | None = None,
) -> GoldOptionsSkewShockDigestReport:
    cfg = config or GoldOptionsSkewShockDigestConfig()
    if type(cfg) is not GoldOptionsSkewShockDigestConfig:
        raise ValueError("config must be exactly GoldOptionsSkewShockDigestConfig")
    _require_hard_flags("config", cfg)
    generated = _as_utc("generated_at", generated_at or datetime.now(UTC))

    source_ids: set[str] = set()
    rows: list[GoldOptionsSkewShockDigestRow] = []
    for observation in observations:
        if type(observation) is not GoldOptionsSkewShockObservation:
            raise ValueError(
                "observations must contain GoldOptionsSkewShockObservation rows",
            )
        if observation.source_id in source_ids:
            raise ValueError("inputs must not contain duplicate source_id values")
        source_ids.add(observation.source_id)
        rows.append(_build_row(observation, cfg))

    shock_rows = tuple(sorted(rows, key=_row_sort_key))
    observation_count = _count_decimal(len(shock_rows))
    source_row_count = _sum_counts(row.source_row_count for row in shock_rows)
    pass_count = _count_decimal(
        sum(1 for row in shock_rows if row.shock_status == "pass"),
    )
    watch_count = _count_decimal(
        sum(1 for row in shock_rows if row.shock_status == "watch"),
    )
    blocked_count = _count_decimal(
        sum(1 for row in shock_rows if row.shock_status == "blocked"),
    )
    max_abs_skew_shock_ratio = max(
        (row.abs_skew_shock_ratio for row in shock_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM)
    average_skew_shock_ratio = _average_ratio(
        tuple(row.skew_shock_ratio for row in shock_rows),
    )
    top_screening_priority_score = max(
        (row.screening_priority_score for row in shock_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM)
    digest_status = _digest_status(shock_rows)
    reason_codes = _report_reason_codes(
        digest_status,
        put_count=_count_decimal(
            sum(1 for row in shock_rows if row.skew_direction == "put_skew_widening"),
        ),
        call_count=_count_decimal(
            sum(1 for row in shock_rows if row.skew_direction == "call_skew_widening"),
        ),
    )

    return GoldOptionsSkewShockDigestReport(
        generated_at=generated,
        config_version=cfg.config_version,
        source_row_count=source_row_count,
        observation_count=observation_count,
        pass_count=pass_count,
        watch_count=watch_count,
        blocked_count=blocked_count,
        max_abs_skew_shock_ratio=max_abs_skew_shock_ratio,
        average_skew_shock_ratio=average_skew_shock_ratio,
        top_screening_priority_score=top_screening_priority_score,
        digest_status=digest_status,
        reason_codes=reason_codes,
        shock_rows=shock_rows,
    )


def market_research_gold_options_skew_shock_digest_payload(
    report: GoldOptionsSkewShockDigestReport,
) -> dict[str, Any]:
    if type(report) is not GoldOptionsSkewShockDigestReport:
        raise ValueError("report must be exactly GoldOptionsSkewShockDigestReport")
    _require_hard_flags("report", report)
    return _json_ready(asdict(report))


def _build_row(
    observation: GoldOptionsSkewShockObservation,
    config: GoldOptionsSkewShockDigestConfig,
) -> GoldOptionsSkewShockDigestRow:
    skew_ratio = _calculate_skew_ratio(
        observation.put_delta_25_iv,
        observation.call_delta_25_iv,
        observation.atm_iv,
    )
    skew_shock_ratio = (skew_ratio - observation.previous_skew_ratio).quantize(
        RATIO_QUANTUM,
    )
    abs_skew_shock_ratio = abs(skew_shock_ratio).quantize(RATIO_QUANTUM)
    direction = _shock_direction(skew_shock_ratio, config.watch_abs_skew_shock_ratio)
    status = _row_status(abs_skew_shock_ratio, config)
    return GoldOptionsSkewShockDigestRow(
        source_id=observation.source_id,
        market_slug=observation.market_slug,
        expiry_bucket=observation.expiry_bucket,
        put_delta_25_iv=observation.put_delta_25_iv,
        call_delta_25_iv=observation.call_delta_25_iv,
        atm_iv=observation.atm_iv,
        previous_skew_ratio=observation.previous_skew_ratio,
        skew_ratio=skew_ratio,
        skew_shock_ratio=skew_shock_ratio,
        abs_skew_shock_ratio=abs_skew_shock_ratio,
        screening_priority_score=_screening_priority_score(
            abs_skew_shock_ratio,
            config.blocked_abs_skew_shock_ratio,
        ),
        source_row_count=observation.source_row_count,
        observed_at=observation.observed_at,
        skew_direction=direction,
        shock_status=status,
        reason_codes=_row_reason_codes(direction, status),
    )


def _row_status(
    abs_skew_shock_ratio: Decimal,
    config: GoldOptionsSkewShockDigestConfig,
) -> str:
    if abs_skew_shock_ratio >= config.blocked_abs_skew_shock_ratio:
        return "blocked"
    if abs_skew_shock_ratio >= config.watch_abs_skew_shock_ratio:
        return "watch"
    return "pass"


def _shock_direction(skew_shock_ratio: Decimal, watch_abs_skew_shock_ratio: Decimal) -> str:
    if abs(skew_shock_ratio) < watch_abs_skew_shock_ratio:
        return "inline"
    if skew_shock_ratio > ZERO_RATIO:
        return "put_skew_widening"
    return "call_skew_widening"


def _input_direction(skew_shock_ratio: Decimal) -> str:
    if skew_shock_ratio > ZERO_RATIO:
        return "put_skew_widening"
    if skew_shock_ratio < ZERO_RATIO:
        return "call_skew_widening"
    return "inline"


def _row_reason_codes(direction: str, status: str) -> tuple[str, ...]:
    if status == "blocked" and direction == "put_skew_widening":
        return ("gold_options_put_skew_shock_blocked",)
    if status == "blocked" and direction == "call_skew_widening":
        return ("gold_options_call_skew_shock_blocked",)
    if status == "watch" and direction == "put_skew_widening":
        return ("gold_options_put_skew_shock_watch",)
    if status == "watch" and direction == "call_skew_widening":
        return ("gold_options_call_skew_shock_watch",)
    return ("gold_options_skew_shock_inline",)


def _digest_status(rows: tuple[GoldOptionsSkewShockDigestRow, ...]) -> str:
    if any(row.shock_status == "blocked" for row in rows):
        return "blocked"
    if any(row.shock_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    digest_status: str,
    *,
    put_count: Decimal,
    call_count: Decimal,
) -> tuple[str, ...]:
    if digest_status == "pass":
        return ("gold_options_skew_shock_digest_clear",)
    reasons: list[str] = []
    if digest_status == "blocked":
        reasons.append("gold_options_skew_shock_blocked_present")
    else:
        reasons.append("gold_options_skew_shock_watch_present")
    if put_count > ZERO_COUNT and call_count > ZERO_COUNT:
        reasons.append("gold_options_skew_shock_mixed_direction_present")
    elif put_count > ZERO_COUNT:
        reasons.append("gold_options_put_skew_shock_present")
    elif call_count > ZERO_COUNT:
        reasons.append("gold_options_call_skew_shock_present")
    return tuple(reasons)


def _row_sort_key(
    row: GoldOptionsSkewShockDigestRow,
) -> tuple[Decimal, Decimal, Decimal, datetime, str, str, str]:
    return (
        -STATUS_WEIGHT[row.shock_status],
        -row.screening_priority_score,
        -row.abs_skew_shock_ratio,
        _reverse_datetime(row.observed_at),
        row.expiry_bucket,
        row.source_id,
        row.market_slug,
    )


def _reverse_datetime(value: datetime) -> datetime:
    return datetime.max.replace(tzinfo=UTC) - (value - datetime.min.replace(tzinfo=UTC))


def _screening_priority_score(
    abs_skew_shock_ratio: Decimal,
    blocked_abs_skew_shock_ratio: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        score = abs_skew_shock_ratio / blocked_abs_skew_shock_ratio
        if score > ONE_RATIO:
            return ONE_RATIO
        return score.quantize(RATIO_QUANTUM)


def _average_ratio(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO_RATIO
    with localcontext(DECIMAL_CONTEXT):
        return (sum(values, ZERO_RATIO) / Decimal(len(values))).quantize(RATIO_QUANTUM)


def _sum_counts(values: Any) -> Decimal:
    total = ZERO_COUNT
    for value in values:
        total += value
    return total.quantize(COUNT_QUANTUM)


def _count_decimal(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _validate_observation(row: GoldOptionsSkewShockObservation) -> None:
    skew_ratio = _calculate_skew_ratio(
        row.put_delta_25_iv,
        row.call_delta_25_iv,
        row.atm_iv,
    )
    skew_shock_ratio = (skew_ratio - row.previous_skew_ratio).quantize(RATIO_QUANTUM)
    if row.reason_codes not in _allowed_input_reason_codes(skew_shock_ratio):
        raise ValueError("reason_codes must match skew shock direction")


def _allowed_input_reason_codes(
    skew_shock_ratio: Decimal,
) -> tuple[tuple[str, ...], ...]:
    direction = _input_direction(skew_shock_ratio)
    direction_reason = {
        "put_skew_widening": "gold_options_put_skew_widened",
        "call_skew_widening": "gold_options_call_skew_widened",
        "inline": "gold_options_skew_inline",
    }[direction]
    if abs(skew_shock_ratio) < WATCH_ABS_SKEW_SHOCK_RATIO and direction != "inline":
        return (
            ("gold_options_skew_inline",),
            (direction_reason,),
        )
    return ((direction_reason,),)


def _validate_row(row: GoldOptionsSkewShockDigestRow) -> None:
    expected_skew_ratio = _calculate_skew_ratio(
        row.put_delta_25_iv,
        row.call_delta_25_iv,
        row.atm_iv,
    )
    if row.skew_ratio != expected_skew_ratio:
        raise ValueError("skew_ratio must match option implied volatility inputs")
    expected_shock = (row.skew_ratio - row.previous_skew_ratio).quantize(RATIO_QUANTUM)
    if row.skew_shock_ratio != expected_shock:
        raise ValueError("skew_shock_ratio must match current and previous skew")
    if row.abs_skew_shock_ratio != abs(row.skew_shock_ratio).quantize(RATIO_QUANTUM):
        raise ValueError("abs_skew_shock_ratio must match skew_shock_ratio")
    if row.reason_codes != _row_reason_codes(row.skew_direction, row.shock_status):
        raise ValueError("reason_codes must match skew direction and shock status")


def _validate_report(report: GoldOptionsSkewShockDigestReport) -> None:
    if report.observation_count != _count_decimal(len(report.shock_rows)):
        raise ValueError("observation_count must match shock_rows")
    if report.pass_count + report.watch_count + report.blocked_count != report.observation_count:
        raise ValueError("status counts must match observation_count")
    if report.source_row_count != _sum_counts(row.source_row_count for row in report.shock_rows):
        raise ValueError("source_row_count must match shock_rows")
    if report.digest_status != _digest_status(report.shock_rows):
        raise ValueError("digest_status must match shock_rows")
    if report.max_abs_skew_shock_ratio != max(
        (row.abs_skew_shock_ratio for row in report.shock_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM):
        raise ValueError("max_abs_skew_shock_ratio must match shock_rows")
    if report.average_skew_shock_ratio != _average_ratio(
        tuple(row.skew_shock_ratio for row in report.shock_rows),
    ):
        raise ValueError("average_skew_shock_ratio must match shock_rows")
    if report.top_screening_priority_score != max(
        (row.screening_priority_score for row in report.shock_rows),
        default=ZERO_RATIO,
    ).quantize(RATIO_QUANTUM):
        raise ValueError("top_screening_priority_score must match shock_rows")


def _calculate_skew_ratio(
    put_delta_25_iv: Decimal,
    call_delta_25_iv: Decimal,
    atm_iv: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return ((put_delta_25_iv - call_delta_25_iv) / atm_iv).quantize(RATIO_QUANTUM)


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _normalize_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(RATIO_QUANTUM)
    if normalized < ZERO_RATIO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_positive_ratio(field_name: str, value: Decimal) -> Decimal:
    normalized = _normalize_ratio(field_name, value)
    if normalized <= ZERO_RATIO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_signed_ratio(field_name: str, value: Decimal) -> Decimal:
    return _require_decimal(field_name, value).quantize(RATIO_QUANTUM)


def _normalize_nonnegative_count(field_name: str, value: Decimal) -> Decimal:
    normalized = _require_decimal(field_name, value).quantize(COUNT_QUANTUM)
    if normalized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    if normalized != value:
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _require_decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return +value
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be finite") from exc


def _require_canonical_string(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be non-empty canonical text")
    if not _CANONICAL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be canonical lowercase text")


def _require_member(field_name: str, value: str, allowed: tuple[str, ...]) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(
    field_name: str,
    values: tuple[str, ...],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    seen: set[str] = set()
    for value in values:
        if type(value) is not str:
            raise ValueError(f"{field_name} must contain strings")
        if value not in allowed:
            raise ValueError(f"{field_name} contains unsupported reason code")
        if value in seen:
            raise ValueError(f"{field_name} must not contain duplicate reason codes")
        seen.add(value)
    return tuple(value for value in allowed if value in seen)


def _normalize_rows(
    rows: tuple[GoldOptionsSkewShockDigestRow, ...],
) -> tuple[GoldOptionsSkewShockDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("shock_rows must be a tuple")
    seen: set[str] = set()
    normalized: list[GoldOptionsSkewShockDigestRow] = []
    for row in rows:
        if type(row) is not GoldOptionsSkewShockDigestRow:
            raise ValueError("shock_rows must contain digest rows")
        if row.source_id in seen:
            raise ValueError("shock_rows must not contain duplicate source_id values")
        seen.add(row.source_id)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = getattr(value, field_name)
        if type(flag) is not bool:
            raise ValueError(f"{label} {field_name} must be a bool")
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        return {key: _json_ready(child) for key, child in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(child) for child in value]
    if isinstance(value, list):
        return [_json_ready(child) for child in value]
    if type(value) is Decimal:
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool or value is None or type(value) is str:
        return value
    raise ValueError("value is not a supported report field")
