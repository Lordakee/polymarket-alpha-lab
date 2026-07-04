"""Pure Phase 1 category volatility rotation digest."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_STRATEGY_CATEGORY_VOLATILITY_ROTATION_DIGEST_CONFIG_VERSION",
    "StrategyCategoryVolatilityRotationDigestConfig",
    "StrategyCategoryVolatilityRotationDigestReasonCodeCount",
    "StrategyCategoryVolatilityRotationDigestReport",
    "StrategyCategoryVolatilityRotationDigestRow",
    "StrategyCategoryVolatilityRotationInput",
    "build_strategy_category_volatility_rotation_digest",
    "strategy_category_volatility_rotation_digest_payload",
)


DEFAULT_STRATEGY_CATEGORY_VOLATILITY_ROTATION_DIGEST_CONFIG_VERSION = (
    "strategy-category-volatility-rotation-digest-v0"
)

VALUE_QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")
ZERO = Decimal("0").quantize(VALUE_QUANTUM)
ZERO_COUNT = Decimal("0").quantize(COUNT_QUANTUM)
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
ELIGIBLE_STATE = "eligible"
WATCH_STATE = "watch"
DEPRIORITIZE_STATE = "deprioritize"
ROTATION_STATES = (ELIGIBLE_STATE, WATCH_STATE, DEPRIORITIZE_STATE)
EMPTY_REASON_CODE = "strategy_category_volatility_rotation_digest_empty"
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATE_SORT_VALUE = {
    ELIGIBLE_STATE: Decimal("0"),
    WATCH_STATE: Decimal("1"),
    DEPRIORITIZE_STATE: Decimal("2"),
}
PRESSURE_WEIGHTS = (
    Decimal("0.450000"),
    Decimal("0.350000"),
    Decimal("0.200000"),
)
_CREDENTIAL_MARKERS = (
    "api" + "_key",
    "sk" + "_live",
    "sec" + "ret",
    "tok" + "en",
)
_REFERENCE_MARKERS = (
    "priv" + "ate_key",
    "priv" + "ate",
    "wal" + "let",
    "0x",
)
_PUBLIC_TEXT_MARKERS = (
    "://",
    "tok" + "en=",
    "api" + "_key=",
    "sec" + "ret",
    "priv" + "ate",
    "wal" + "let:",
    "bear" + "er ",
    "pass" + "word",
    "seed" + "_phrase",
    "0x",
)
_UNSAFE_TEXT_FRAGMENTS = (
    "aut" + "h",
    "priv" + "ate_key",
    "wal" + "let",
    "acc" + "ount",
    "bal" + "ance",
    "ord" + "er",
    "can" + "cel",
    "re" + "place",
    "si" + "gn",
    "exchange" + "_mutation",
)


@dataclass(frozen=True)
class StrategyCategoryVolatilityRotationDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CATEGORY_VOLATILITY_ROTATION_DIGEST_CONFIG_VERSION
    )
    minimum_eligible_pressure_score: Decimal = Decimal("0.350000")
    watch_pressure_score: Decimal = Decimal("0.150000")
    maximum_stale_event_ratio: Decimal = Decimal("0.300000")
    watch_stale_event_ratio: Decimal = Decimal("0.500000")
    maximum_unresolved_event_ratio: Decimal = Decimal("0.400000")
    watch_unresolved_event_ratio: Decimal = Decimal("0.650000")
    maximum_sample_age_seconds: Decimal = Decimal("3600")
    watch_sample_age_seconds: Decimal = Decimal("7200")
    minimum_event_count: Decimal = Decimal("3")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "minimum_eligible_pressure_score",
            "watch_pressure_score",
            "maximum_stale_event_ratio",
            "watch_stale_event_ratio",
            "maximum_unresolved_event_ratio",
            "watch_unresolved_event_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_sample_age_seconds",
            "watch_sample_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_value(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_event_count",
            _normalize_positive_count("minimum_event_count", self.minimum_event_count),
        )
        if self.minimum_eligible_pressure_score < self.watch_pressure_score:
            raise ValueError(
                "minimum_eligible_pressure_score must be at least watch_pressure_score",
            )
        _require_at_most(
            "maximum_stale_event_ratio",
            self.maximum_stale_event_ratio,
            self.watch_stale_event_ratio,
        )
        _require_at_most(
            "maximum_unresolved_event_ratio",
            self.maximum_unresolved_event_ratio,
            self.watch_unresolved_event_ratio,
        )
        _require_at_most(
            "maximum_sample_age_seconds",
            self.maximum_sample_age_seconds,
            self.watch_sample_age_seconds,
        )
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyCategoryVolatilityRotationInput:
    category: str
    sample_observed_at: datetime
    event_count: Decimal
    probability_swing_abs: Decimal
    intraday_probability_range: Decimal
    probability_update_count: Decimal
    stale_event_ratio: Decimal
    unresolved_event_ratio: Decimal
    public_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "sample_observed_at",
            _as_utc("sample_observed_at", self.sample_observed_at),
        )
        object.__setattr__(
            self,
            "event_count",
            _normalize_positive_count("event_count", self.event_count),
        )
        object.__setattr__(
            self,
            "probability_update_count",
            _normalize_nonnegative_count(
                "probability_update_count",
                self.probability_update_count,
            ),
        )
        for field_name in (
            "probability_swing_abs",
            "intraday_probability_range",
            "stale_event_ratio",
            "unresolved_event_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_public_reference(self.public_reference)
        object.__setattr__(
            self,
            "public_reference",
            _redact_public_reference(self.public_reference),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_paper_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class StrategyCategoryVolatilityRotationDigestRow:
    rank: Decimal
    category: str
    sample_observed_at: datetime
    event_count: Decimal
    probability_swing_abs: Decimal
    intraday_probability_range: Decimal
    probability_update_count: Decimal
    update_density_score: Decimal
    stale_event_ratio: Decimal
    unresolved_event_ratio: Decimal
    sample_age_seconds: Decimal
    volatility_pressure_score: Decimal
    rotation_state: str
    redacted_public_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_string("category", self.category)
        object.__setattr__(
            self,
            "sample_observed_at",
            _as_utc("sample_observed_at", self.sample_observed_at),
        )
        object.__setattr__(
            self,
            "event_count",
            _normalize_positive_count("event_count", self.event_count),
        )
        object.__setattr__(
            self,
            "probability_update_count",
            _normalize_nonnegative_count(
                "probability_update_count",
                self.probability_update_count,
            ),
        )
        for field_name in (
            "probability_swing_abs",
            "intraday_probability_range",
            "update_density_score",
            "stale_event_ratio",
            "unresolved_event_ratio",
            "volatility_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "sample_age_seconds",
            _normalize_nonnegative_value(
                "sample_age_seconds",
                self.sample_age_seconds,
            ),
        )
        _require_member("rotation_state", self.rotation_state, ROTATION_STATES)
        _require_public_reference(self.redacted_public_reference)
        object.__setattr__(
            self,
            "redacted_public_reference",
            _redact_public_reference(self.redacted_public_reference),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_paper_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class StrategyCategoryVolatilityRotationDigestReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code(self.reason_code)
        object.__setattr__(self, "count", _normalize_positive_count("count", self.count))
        _require_paper_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyCategoryVolatilityRotationDigestReport:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    eligible_count: Decimal
    watch_count: Decimal
    deprioritize_count: Decimal
    top_category: str | None
    max_volatility_pressure_score: Decimal
    min_volatility_pressure_score: Decimal
    average_volatility_pressure_score: Decimal
    digest_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyCategoryVolatilityRotationDigestReasonCodeCount, ...]
    rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_count",
            "eligible_count",
            "watch_count",
            "deprioritize_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        if self.top_category is not None:
            _require_canonical_string("top_category", self.top_category)
        for field_name in (
            "max_volatility_pressure_score",
            "min_volatility_pressure_score",
            "average_volatility_pressure_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("digest_status", self.digest_status, ROTATION_STATES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_paper_flags("report", self)
        _reject_unsafe_public_payload("report", self)


def build_strategy_category_volatility_rotation_digest(
    categories: Iterable[StrategyCategoryVolatilityRotationInput],
    *,
    config: StrategyCategoryVolatilityRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryVolatilityRotationDigestReport:
    if type(config) is not StrategyCategoryVolatilityRotationDigestConfig:
        raise ValueError(
            "config must be a StrategyCategoryVolatilityRotationDigestConfig",
        )
    _require_paper_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    source_rows = _normalize_inputs(categories)
    ranked_rows = _rank_rows(
        tuple(
            _unranked_row(row, config=config, generated_at=generated_at_utc)
            for row in source_rows
        ),
    )
    return StrategyCategoryVolatilityRotationDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        category_count=_count(len(ranked_rows)),
        eligible_count=_count(_state_count(ranked_rows, ELIGIBLE_STATE)),
        watch_count=_count(_state_count(ranked_rows, WATCH_STATE)),
        deprioritize_count=_count(_state_count(ranked_rows, DEPRIORITIZE_STATE)),
        top_category=ranked_rows[0].category if ranked_rows else None,
        max_volatility_pressure_score=_max_pressure_score(ranked_rows),
        min_volatility_pressure_score=_min_pressure_score(ranked_rows),
        average_volatility_pressure_score=_average_pressure_score(ranked_rows),
        digest_status=_digest_status(ranked_rows),
        reason_codes=_report_reason_codes(ranked_rows),
        reason_code_counts=_reason_code_counts(ranked_rows),
        rows=ranked_rows,
    )


def strategy_category_volatility_rotation_digest_payload(
    report: StrategyCategoryVolatilityRotationDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCategoryVolatilityRotationDigestReport:
        _require_paper_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCategoryVolatilityRotationDigestReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_paper_flags("payload", _DictFlags(payload))
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


def _unranked_row(
    row: StrategyCategoryVolatilityRotationInput,
    *,
    config: StrategyCategoryVolatilityRotationDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryVolatilityRotationDigestRow:
    sample_age_seconds = _sample_age_seconds(row.sample_observed_at, generated_at)
    update_density_score = _update_density_score(
        row.probability_update_count,
        row.event_count,
    )
    volatility_pressure_score = _volatility_pressure_score(
        probability_swing_abs=row.probability_swing_abs,
        intraday_probability_range=row.intraday_probability_range,
        update_density_score=update_density_score,
    )
    rotation_state = _rotation_state(
        row,
        sample_age_seconds=sample_age_seconds,
        volatility_pressure_score=volatility_pressure_score,
        config=config,
    )
    return StrategyCategoryVolatilityRotationDigestRow(
        rank=Decimal("1"),
        category=row.category,
        sample_observed_at=row.sample_observed_at,
        event_count=row.event_count,
        probability_swing_abs=row.probability_swing_abs,
        intraday_probability_range=row.intraday_probability_range,
        probability_update_count=row.probability_update_count,
        update_density_score=update_density_score,
        stale_event_ratio=row.stale_event_ratio,
        unresolved_event_ratio=row.unresolved_event_ratio,
        sample_age_seconds=sample_age_seconds,
        volatility_pressure_score=volatility_pressure_score,
        rotation_state=rotation_state,
        redacted_public_reference=_redact_public_reference(row.public_reference),
        reason_codes=_row_reason_codes(
            row,
            sample_age_seconds=sample_age_seconds,
            volatility_pressure_score=volatility_pressure_score,
            rotation_state=rotation_state,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...],
) -> tuple[StrategyCategoryVolatilityRotationDigestRow, ...]:
    sorted_rows = tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.volatility_pressure_score,
                STATE_SORT_VALUE[row.rotation_state],
                row.category,
            ),
        ),
    )
    return tuple(
        StrategyCategoryVolatilityRotationDigestRow(
            rank=_count(index),
            category=row.category,
            sample_observed_at=row.sample_observed_at,
            event_count=row.event_count,
            probability_swing_abs=row.probability_swing_abs,
            intraday_probability_range=row.intraday_probability_range,
            probability_update_count=row.probability_update_count,
            update_density_score=row.update_density_score,
            stale_event_ratio=row.stale_event_ratio,
            unresolved_event_ratio=row.unresolved_event_ratio,
            sample_age_seconds=row.sample_age_seconds,
            volatility_pressure_score=row.volatility_pressure_score,
            rotation_state=row.rotation_state,
            redacted_public_reference=row.redacted_public_reference,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _rotation_state(
    row: StrategyCategoryVolatilityRotationInput,
    *,
    sample_age_seconds: Decimal,
    volatility_pressure_score: Decimal,
    config: StrategyCategoryVolatilityRotationDigestConfig,
) -> str:
    if (
        row.event_count < config.minimum_event_count
        or sample_age_seconds > config.watch_sample_age_seconds
        or row.stale_event_ratio > config.watch_stale_event_ratio
        or row.unresolved_event_ratio > config.watch_unresolved_event_ratio
        or volatility_pressure_score < config.watch_pressure_score
    ):
        return DEPRIORITIZE_STATE
    if (
        volatility_pressure_score >= config.minimum_eligible_pressure_score
        and sample_age_seconds <= config.maximum_sample_age_seconds
        and row.stale_event_ratio <= config.maximum_stale_event_ratio
        and row.unresolved_event_ratio <= config.maximum_unresolved_event_ratio
    ):
        return ELIGIBLE_STATE
    return WATCH_STATE


def _row_reason_codes(
    row: StrategyCategoryVolatilityRotationInput,
    *,
    sample_age_seconds: Decimal,
    volatility_pressure_score: Decimal,
    rotation_state: str,
    config: StrategyCategoryVolatilityRotationDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(row.reason_codes)
    reason_codes.append(
        "event_count_sufficient"
        if row.event_count >= config.minimum_event_count
        else "event_count_low",
    )
    reason_codes.append(
        _threshold_reason_code(
            sample_age_seconds,
            pass_threshold=config.maximum_sample_age_seconds,
            watch_threshold=config.watch_sample_age_seconds,
            lower_is_better=True,
            pass_code="sample_recent",
            watch_code="sample_age_watch",
            low_code="sample_age_deprioritize",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            row.stale_event_ratio,
            pass_threshold=config.maximum_stale_event_ratio,
            watch_threshold=config.watch_stale_event_ratio,
            lower_is_better=True,
            pass_code="stale_event_ratio_clear",
            watch_code="stale_event_ratio_watch",
            low_code="stale_event_ratio_deprioritize",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            row.unresolved_event_ratio,
            pass_threshold=config.maximum_unresolved_event_ratio,
            watch_threshold=config.watch_unresolved_event_ratio,
            lower_is_better=True,
            pass_code="unresolved_event_ratio_clear",
            watch_code="unresolved_event_ratio_watch",
            low_code="unresolved_event_ratio_deprioritize",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            volatility_pressure_score,
            pass_threshold=config.minimum_eligible_pressure_score,
            watch_threshold=config.watch_pressure_score,
            lower_is_better=False,
            pass_code="volatility_pressure_high",
            watch_code="volatility_pressure_watch",
            low_code="volatility_pressure_low",
        ),
    )
    reason_codes.append(f"volatility_pressure_{rotation_state}")
    return _normalize_reason_codes("reason_codes", tuple(reason_codes))


def _threshold_reason_code(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    lower_is_better: bool,
    pass_code: str,
    watch_code: str,
    low_code: str,
) -> str:
    if lower_is_better:
        if value <= pass_threshold:
            return pass_code
        if value <= watch_threshold:
            return watch_code
        return low_code
    if value >= pass_threshold:
        return pass_code
    if value >= watch_threshold:
        return watch_code
    return low_code


def _update_density_score(update_count: Decimal, event_count: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "update_density_score",
            min(update_count, event_count) / event_count,
        )


def _volatility_pressure_score(
    *,
    probability_swing_abs: Decimal,
    intraday_probability_range: Decimal,
    update_density_score: Decimal,
) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "volatility_pressure_score",
            (probability_swing_abs * PRESSURE_WEIGHTS[0])
            + (intraday_probability_range * PRESSURE_WEIGHTS[1])
            + (update_density_score * PRESSURE_WEIGHTS[2]),
        )


def _sample_age_seconds(sample_observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - _as_utc("sample_observed_at", sample_observed_at)
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    age_seconds = _normalize_value("sample_age_seconds", seconds)
    if age_seconds < ZERO:
        raise ValueError("sample_observed_at must not be after generated_at")
    return age_seconds


def _validate_row(row: StrategyCategoryVolatilityRotationDigestRow) -> None:
    if row.update_density_score != _update_density_score(
        row.probability_update_count,
        row.event_count,
    ):
        raise ValueError("update_density_score must match row values")
    if row.volatility_pressure_score != _volatility_pressure_score(
        probability_swing_abs=row.probability_swing_abs,
        intraday_probability_range=row.intraday_probability_range,
        update_density_score=row.update_density_score,
    ):
        raise ValueError("volatility_pressure_score must match row values")
    if f"volatility_pressure_{row.rotation_state}" not in row.reason_codes:
        raise ValueError("rotation_state must match reason_codes")


def _validate_report(report: StrategyCategoryVolatilityRotationDigestReport) -> None:
    if report.category_count != _count(len(report.rows)):
        raise ValueError("category_count must match rows")
    if report.eligible_count != _count(_state_count(report.rows, ELIGIBLE_STATE)):
        raise ValueError("eligible_count must match rows")
    if report.watch_count != _count(_state_count(report.rows, WATCH_STATE)):
        raise ValueError("watch_count must match rows")
    if report.deprioritize_count != _count(
        _state_count(report.rows, DEPRIORITIZE_STATE),
    ):
        raise ValueError("deprioritize_count must match rows")
    expected_top_category = report.rows[0].category if report.rows else None
    if report.top_category != expected_top_category:
        raise ValueError("top_category must match highest-ranked row")
    if report.max_volatility_pressure_score != _max_pressure_score(report.rows):
        raise ValueError("max_volatility_pressure_score must match rows")
    if report.min_volatility_pressure_score != _min_pressure_score(report.rows):
        raise ValueError("min_volatility_pressure_score must match rows")
    if report.average_volatility_pressure_score != _average_pressure_score(report.rows):
        raise ValueError("average_volatility_pressure_score must match rows")
    if report.digest_status != _digest_status(report.rows):
        raise ValueError("digest_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    value: Iterable[StrategyCategoryVolatilityRotationInput],
) -> tuple[StrategyCategoryVolatilityRotationInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("categories must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("categories must be an iterable") from exc
    categories: set[str] = set()
    for row in rows:
        if type(row) is not StrategyCategoryVolatilityRotationInput:
            raise ValueError("categories must contain exact input rows")
        _require_paper_flags("input", row)
        if row.category in categories:
            raise ValueError("categories must be unique")
        categories.add(row.category)
    return rows


def _normalize_rows(
    value: object,
) -> tuple[StrategyCategoryVolatilityRotationDigestRow, ...]:
    if type(value) is not tuple:
        raise ValueError("digest report rows must be a tuple")
    rows = tuple(value)
    for row in rows:
        if type(row) is not StrategyCategoryVolatilityRotationDigestRow:
            raise ValueError("digest report must contain exact rows")
        _require_paper_flags("row", row)
    expected_ranks = tuple(_count(index) for index in range(1, len(rows) + 1))
    if tuple(row.rank for row in rows) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    if rows != tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.volatility_pressure_score,
                STATE_SORT_VALUE[row.rotation_state],
                row.category,
            ),
        ),
    ):
        raise ValueError("rows must be sorted by pressure score and category")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyCategoryVolatilityRotationDigestReasonCodeCount, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    rows = tuple(value)
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in rows:
        if type(row) is not StrategyCategoryVolatilityRotationDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact count rows")
        _require_paper_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic sort")
        previous_key = key
        seen.add(row.reason_code)
    return rows


def _state_count(
    rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...],
    state: str,
) -> int:
    return sum(1 for row in rows if row.rotation_state == state)


def _max_pressure_score(
    rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _q(max(row.volatility_pressure_score for row in rows))


def _min_pressure_score(
    rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _q(min(row.volatility_pressure_score for row in rows))


def _average_pressure_score(
    rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _q(sum(row.volatility_pressure_score for row in rows) / Decimal(len(rows)))


def _digest_status(rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...]) -> str:
    if not rows:
        return DEPRIORITIZE_STATE
    if all(row.rotation_state == ELIGIBLE_STATE for row in rows):
        return ELIGIBLE_STATE
    if all(row.rotation_state == DEPRIORITIZE_STATE for row in rows):
        return DEPRIORITIZE_STATE
    return WATCH_STATE


def _report_reason_codes(
    rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple({reason_code for row in rows for reason_code in row.reason_codes}),
    )


def _reason_code_counts(
    rows: tuple[StrategyCategoryVolatilityRotationDigestRow, ...],
) -> tuple[StrategyCategoryVolatilityRotationDigestReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        StrategyCategoryVolatilityRotationDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_at_most(
    field_name: str,
    low_value: Decimal,
    high_value: Decimal,
) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must be less than or equal to watch threshold")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO_COUNT:
        raise ValueError(f"{field_name} must be above zero")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    quantized = value.quantize(COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < ZERO_COUNT:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_value(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_value(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_value(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _q(value)


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _q(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(VALUE_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_canonical_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a nonblank trimmed string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _require_public_reference(value: object) -> None:
    if type(value) is not str:
        raise ValueError("public_reference must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError("public_reference must be a nonblank trimmed string")


def _redact_public_reference(value: str) -> str:
    if _contains_public_marker(value) or _has_unsafe_text(value):
        return "<redacted>"
    return value


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    normalized: list[str] = []
    for reason_code in reason_codes:
        clean_reason_code = _sanitize_reason_code(reason_code)
        _require_reason_code(clean_reason_code)
        if clean_reason_code not in normalized:
            normalized.append(clean_reason_code)
    return tuple(sorted(normalized))


def _sanitize_reason_code(value: object) -> str:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if not value or value.strip() != value:
        raise ValueError("reason_codes must contain canonical strings")
    lowered = value.lower()
    if any(marker in lowered for marker in _CREDENTIAL_MARKERS):
        return "credential_redacted"
    if any(marker in lowered for marker in _REFERENCE_MARKERS):
        return "reference_redacted"
    if _has_unsafe_text(lowered):
        return "surface_redacted"
    return value


def _require_reason_code(value: str) -> None:
    if value != value.lower():
        raise ValueError("reason_codes must be lowercase snake_case strings")
    if value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal strings")
    if type(value) is str:
        return value
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(nested_value)
        return ready
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value), path)
        return
    if type(value) is str:
        if _contains_public_marker(value) or _has_unsafe_text(value):
            raise ValueError(f"{path or label} has unsafe value")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or label} must be exactly Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or label} must be finite")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or label} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or label} must be timezone-aware")
        return
    if value is None or type(value) is bool:
        return
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal numeric strings")
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_text(key):
                raise ValueError(f"unsafe field in {label}")
            nested_path = key if not path else f"{path}.{key}"
            if key in {"paper_only", "report_only", "readonly"} and nested_value is not True:
                raise ValueError(f"{nested_path} must be True")
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    if isinstance(value, (list, tuple)):
        for index, nested_value in enumerate(value):
            nested_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, nested_value, nested_path)
        return
    raise ValueError("value is not JSON serializable")


def _contains_public_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _PUBLIC_TEXT_MARKERS)


def _has_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in _UNSAFE_TEXT_FRAGMENTS)
