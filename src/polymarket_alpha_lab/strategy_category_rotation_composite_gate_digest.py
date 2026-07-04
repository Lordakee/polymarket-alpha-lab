"""Pure Phase 1 category rotation composite gate digest."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


__all__ = (
    "DEFAULT_STRATEGY_CATEGORY_ROTATION_COMPOSITE_GATE_DIGEST_CONFIG_VERSION",
    "StrategyCategoryRotationCompositeGateDigestConfig",
    "StrategyCategoryRotationCompositeGateDigestReasonCodeCount",
    "StrategyCategoryRotationCompositeGateDigestReport",
    "StrategyCategoryRotationCompositeGateDigestRow",
    "StrategyCategoryRotationCompositeGateSignal",
    "build_strategy_category_rotation_composite_gate_digest",
    "strategy_category_rotation_composite_gate_digest_payload",
)


DEFAULT_STRATEGY_CATEGORY_ROTATION_COMPOSITE_GATE_DIGEST_CONFIG_VERSION = (
    "strategy-category-rotation-composite-gate-digest-v0"
)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SECONDS_PER_DAY = Decimal("86400")
MICROSECONDS_PER_SECOND = Decimal("1000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCKED_STATUS = "blocked"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCKED_STATUS)
STATUS_SORT = {
    PASS_STATUS: Decimal("0.000000"),
    WATCH_STATUS: Decimal("1.000000"),
    BLOCKED_STATUS: Decimal("2.000000"),
}
EMPTY_REASON_CODE = "category_rotation_composite_gate_digest_empty"
PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
SENSITIVE_REASON_RULES = (
    (("api" + "_key", "sk" + "_live", "sec" + "ret", "tok" + "en"), "credential_redacted"),
    (("wal" + "let", "priv" + "ate_key", "0x"), "reference_redacted"),
)
PUBLIC_TEXT_MARKERS = (
    "://",
    "tok" + "en",
    "api" + "_key",
    "sk" + "_live",
    "sec" + "ret",
    "priv" + "ate",
    "wal" + "let",
    "bear" + "er ",
    "pass" + "word",
    "seed" + "_phrase",
    "0x",
)
UNSAFE_TEXT_FRAGMENTS = (
    "aut" + "h",
    "priv" + "ate_key",
    "wal" + "let",
    "acc" + "ount",
    "bal" + "ance",
    "ord" + "er",
    "can" + "cel",
    "re" + "place",
    "exchange" + "_mutation",
)


@dataclass(frozen=True)
class StrategyCategoryRotationCompositeGateDigestConfig:
    config_version: str = (
        DEFAULT_STRATEGY_CATEGORY_ROTATION_COMPOSITE_GATE_DIGEST_CONFIG_VERSION
    )
    max_pass_cost_drag_score: Decimal = Decimal("0.030000")
    max_watch_cost_drag_score: Decimal = Decimal("0.060000")
    max_pass_volatility_pressure_score: Decimal = Decimal("0.300000")
    max_watch_volatility_pressure_score: Decimal = Decimal("0.550000")
    max_pass_resolution_timeline_pressure_score: Decimal = Decimal("0.250000")
    max_watch_resolution_timeline_pressure_score: Decimal = Decimal("0.500000")
    min_pass_liquidity_capacity_score: Decimal = Decimal("0.700000")
    min_watch_liquidity_capacity_score: Decimal = Decimal("0.450000")
    min_pass_research_capacity_score: Decimal = Decimal("0.700000")
    min_watch_research_capacity_score: Decimal = Decimal("0.450000")
    max_pass_signal_age_seconds: Decimal = Decimal("1800.000000")
    max_watch_signal_age_seconds: Decimal = Decimal("3600.000000")
    min_pass_learning_value_score: Decimal = Decimal("0.500000")
    min_watch_learning_value_score: Decimal = Decimal("0.250000")
    minimum_pass_categories: Decimal = Decimal("1.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "max_pass_cost_drag_score",
            "max_watch_cost_drag_score",
            "max_pass_volatility_pressure_score",
            "max_watch_volatility_pressure_score",
            "max_pass_resolution_timeline_pressure_score",
            "max_watch_resolution_timeline_pressure_score",
            "min_pass_liquidity_capacity_score",
            "min_watch_liquidity_capacity_score",
            "min_pass_research_capacity_score",
            "min_watch_research_capacity_score",
            "min_pass_learning_value_score",
            "min_watch_learning_value_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_pass_signal_age_seconds",
            "max_watch_signal_age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "minimum_pass_categories",
            _normalize_nonnegative_count(
                "minimum_pass_categories",
                self.minimum_pass_categories,
            ),
        )
        _require_at_most(
            "max_pass_cost_drag_score",
            self.max_pass_cost_drag_score,
            self.max_watch_cost_drag_score,
        )
        _require_at_most(
            "max_pass_volatility_pressure_score",
            self.max_pass_volatility_pressure_score,
            self.max_watch_volatility_pressure_score,
        )
        _require_at_most(
            "max_pass_resolution_timeline_pressure_score",
            self.max_pass_resolution_timeline_pressure_score,
            self.max_watch_resolution_timeline_pressure_score,
        )
        _require_at_least(
            "min_pass_liquidity_capacity_score",
            self.min_pass_liquidity_capacity_score,
            self.min_watch_liquidity_capacity_score,
        )
        _require_at_least(
            "min_pass_research_capacity_score",
            self.min_pass_research_capacity_score,
            self.min_watch_research_capacity_score,
        )
        _require_at_most(
            "max_pass_signal_age_seconds",
            self.max_pass_signal_age_seconds,
            self.max_watch_signal_age_seconds,
        )
        _require_at_least(
            "min_pass_learning_value_score",
            self.min_pass_learning_value_score,
            self.min_watch_learning_value_score,
        )
        _require_paper_flags("config", self)


@dataclass(frozen=True)
class StrategyCategoryRotationCompositeGateSignal:
    category_id: str
    team_id: str
    signal_observed_at: datetime
    cost_drag_score: Decimal
    volatility_pressure_score: Decimal
    resolution_timeline_pressure_score: Decimal
    liquidity_capacity_score: Decimal
    research_capacity_score: Decimal
    learning_value_score: Decimal
    public_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("category_id", self.category_id)
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(
            self,
            "signal_observed_at",
            _as_utc("signal_observed_at", self.signal_observed_at),
        )
        for field_name in (
            "cost_drag_score",
            "volatility_pressure_score",
            "resolution_timeline_pressure_score",
            "liquidity_capacity_score",
            "research_capacity_score",
            "learning_value_score",
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
            _normalize_reason_codes(self.reason_codes),
        )
        _require_paper_flags("signal", self)
        _reject_unsafe_public_values("signal", self)


@dataclass(frozen=True)
class StrategyCategoryRotationCompositeGateDigestRow:
    rank: Decimal
    category_id: str
    team_id: str
    signal_observed_at: datetime
    signal_age_seconds: Decimal
    cost_drag_score: Decimal
    volatility_pressure_score: Decimal
    resolution_timeline_pressure_score: Decimal
    liquidity_capacity_score: Decimal
    research_capacity_score: Decimal
    learning_value_score: Decimal
    readiness_score: Decimal
    readiness_status: str
    redacted_public_reference: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "rank", _normalize_positive_count("rank", self.rank))
        _require_canonical_string("category_id", self.category_id)
        _require_canonical_string("team_id", self.team_id)
        object.__setattr__(
            self,
            "signal_observed_at",
            _as_utc("signal_observed_at", self.signal_observed_at),
        )
        object.__setattr__(
            self,
            "signal_age_seconds",
            _normalize_nonnegative_decimal(
                "signal_age_seconds",
                self.signal_age_seconds,
            ),
        )
        for field_name in (
            "cost_drag_score",
            "volatility_pressure_score",
            "resolution_timeline_pressure_score",
            "liquidity_capacity_score",
            "research_capacity_score",
            "learning_value_score",
            "readiness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_member("readiness_status", self.readiness_status, STATUSES)
        _require_canonical_string(
            "redacted_public_reference",
            self.redacted_public_reference,
        )
        object.__setattr__(
            self,
            "redacted_public_reference",
            _redact_public_reference(self.redacted_public_reference),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row(self)
        _require_paper_flags("row", self)
        _reject_unsafe_public_values("row", self)


@dataclass(frozen=True)
class StrategyCategoryRotationCompositeGateDigestReasonCodeCount:
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
class StrategyCategoryRotationCompositeGateDigestReport:
    generated_at: datetime
    config_version: str
    category_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    status: str
    passed_category_ids: tuple[str, ...]
    max_readiness_score: Decimal
    min_readiness_score: Decimal
    average_readiness_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyCategoryRotationCompositeGateDigestReasonCodeCount, ...]
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "category_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, STATUSES)
        object.__setattr__(
            self,
            "passed_category_ids",
            _normalize_category_ids("passed_category_ids", self.passed_category_ids),
        )
        for field_name in (
            "max_readiness_score",
            "min_readiness_score",
            "average_readiness_score",
        ):
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
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_paper_flags("report", self)
        _reject_unsafe_public_values("report", self)


def build_strategy_category_rotation_composite_gate_digest(
    categories: Iterable[StrategyCategoryRotationCompositeGateSignal],
    *,
    config: StrategyCategoryRotationCompositeGateDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryRotationCompositeGateDigestReport:
    if type(config) is not StrategyCategoryRotationCompositeGateDigestConfig:
        raise ValueError(
            "config must be a StrategyCategoryRotationCompositeGateDigestConfig",
        )
    _require_paper_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(categories)
    unranked_rows = tuple(
        _digest_row(row, config=config, generated_at=generated_at_utc)
        for row in input_rows
    )
    rows = _rank_rows(unranked_rows)
    return StrategyCategoryRotationCompositeGateDigestReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        category_count=_count(len(rows)),
        pass_count=_status_count(rows, PASS_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        blocked_count=_status_count(rows, BLOCKED_STATUS),
        status=_report_status(rows, config=config),
        passed_category_ids=tuple(
            row.category_id for row in rows if row.readiness_status == PASS_STATUS
        ),
        max_readiness_score=_max_readiness_score(rows),
        min_readiness_score=_min_readiness_score(rows),
        average_readiness_score=_average_readiness_score(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_category_rotation_composite_gate_digest_payload(
    report: StrategyCategoryRotationCompositeGateDigestReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCategoryRotationCompositeGateDigestReport:
        _require_paper_flags("report", report)
        _reject_unsafe_public_values("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_values("payload", report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a StrategyCategoryRotationCompositeGateDigestReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _reject_unsafe_public_values("payload", payload)
    _require_paper_flags("payload", _DictFlags(payload))
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


def _digest_row(
    signal: StrategyCategoryRotationCompositeGateSignal,
    *,
    config: StrategyCategoryRotationCompositeGateDigestConfig,
    generated_at: datetime,
) -> StrategyCategoryRotationCompositeGateDigestRow:
    signal_age_seconds = _signal_age_seconds(signal.signal_observed_at, generated_at)
    reason_codes = _row_reason_codes(
        signal,
        signal_age_seconds=signal_age_seconds,
        config=config,
    )
    status = _row_status(reason_codes)
    return StrategyCategoryRotationCompositeGateDigestRow(
        rank=ONE,
        category_id=signal.category_id,
        team_id=signal.team_id,
        signal_observed_at=signal.signal_observed_at,
        signal_age_seconds=signal_age_seconds,
        cost_drag_score=signal.cost_drag_score,
        volatility_pressure_score=signal.volatility_pressure_score,
        resolution_timeline_pressure_score=signal.resolution_timeline_pressure_score,
        liquidity_capacity_score=signal.liquidity_capacity_score,
        research_capacity_score=signal.research_capacity_score,
        learning_value_score=signal.learning_value_score,
        readiness_score=_readiness_score(
            signal,
            signal_age_seconds=signal_age_seconds,
            status=status,
            config=config,
        ),
        readiness_status=status,
        redacted_public_reference=signal.public_reference,
        reason_codes=reason_codes,
    )


def _rank_rows(
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...],
) -> tuple[StrategyCategoryRotationCompositeGateDigestRow, ...]:
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    return tuple(
        StrategyCategoryRotationCompositeGateDigestRow(
            rank=_count(index),
            category_id=row.category_id,
            team_id=row.team_id,
            signal_observed_at=row.signal_observed_at,
            signal_age_seconds=row.signal_age_seconds,
            cost_drag_score=row.cost_drag_score,
            volatility_pressure_score=row.volatility_pressure_score,
            resolution_timeline_pressure_score=row.resolution_timeline_pressure_score,
            liquidity_capacity_score=row.liquidity_capacity_score,
            research_capacity_score=row.research_capacity_score,
            learning_value_score=row.learning_value_score,
            readiness_score=row.readiness_score,
            readiness_status=row.readiness_status,
            redacted_public_reference=row.redacted_public_reference,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted_rows, start=1)
    )


def _row_reason_codes(
    signal: StrategyCategoryRotationCompositeGateSignal,
    *,
    signal_age_seconds: Decimal,
    config: StrategyCategoryRotationCompositeGateDigestConfig,
) -> tuple[str, ...]:
    reason_codes = list(signal.reason_codes)
    reason_codes.append(
        _threshold_reason_code(
            signal.cost_drag_score,
            pass_threshold=config.max_pass_cost_drag_score,
            watch_threshold=config.max_watch_cost_drag_score,
            lower_is_better=True,
            prefix="cost_drag",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            signal.volatility_pressure_score,
            pass_threshold=config.max_pass_volatility_pressure_score,
            watch_threshold=config.max_watch_volatility_pressure_score,
            lower_is_better=True,
            prefix="volatility_pressure",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            signal.resolution_timeline_pressure_score,
            pass_threshold=config.max_pass_resolution_timeline_pressure_score,
            watch_threshold=config.max_watch_resolution_timeline_pressure_score,
            lower_is_better=True,
            prefix="resolution_timeline",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            signal.liquidity_capacity_score,
            pass_threshold=config.min_pass_liquidity_capacity_score,
            watch_threshold=config.min_watch_liquidity_capacity_score,
            lower_is_better=False,
            prefix="liquidity_capacity",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            signal.research_capacity_score,
            pass_threshold=config.min_pass_research_capacity_score,
            watch_threshold=config.min_watch_research_capacity_score,
            lower_is_better=False,
            prefix="research_capacity",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            signal_age_seconds,
            pass_threshold=config.max_pass_signal_age_seconds,
            watch_threshold=config.max_watch_signal_age_seconds,
            lower_is_better=True,
            prefix="signal_staleness",
        ),
    )
    reason_codes.append(
        _threshold_reason_code(
            signal.learning_value_score,
            pass_threshold=config.min_pass_learning_value_score,
            watch_threshold=config.min_watch_learning_value_score,
            lower_is_better=False,
            prefix="learning_value",
        ),
    )
    status = _row_status(tuple(reason_codes))
    reason_codes.append(f"category_rotation_composite_gate_{status}")
    return _normalize_reason_codes(reason_codes)


def _threshold_reason_code(
    value: Decimal,
    *,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
    lower_is_better: bool,
    prefix: str,
) -> str:
    if lower_is_better:
        if value <= pass_threshold:
            return f"{prefix}_clear"
        if value <= watch_threshold:
            return f"{prefix}_watch"
        return f"{prefix}_blocked"
    if value >= pass_threshold:
        return f"{prefix}_clear"
    if value >= watch_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_blocked"


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return BLOCKED_STATUS
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return WATCH_STATUS
    return PASS_STATUS


def _readiness_score(
    signal: StrategyCategoryRotationCompositeGateSignal,
    *,
    signal_age_seconds: Decimal,
    status: str,
    config: StrategyCategoryRotationCompositeGateDigestConfig,
) -> Decimal:
    if status == BLOCKED_STATUS:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        score = (
            (ONE - signal.cost_drag_score)
            + (ONE - signal.volatility_pressure_score)
            + (ONE - signal.resolution_timeline_pressure_score)
            + signal.liquidity_capacity_score
            + signal.research_capacity_score
            + _nonnegative_decimal(
                ONE - (signal_age_seconds / config.max_watch_signal_age_seconds),
            )
            + signal.learning_value_score
        ) / Decimal("7.000000")
    return _normalize_probability("readiness_score", score)


def _signal_age_seconds(signal_observed_at: datetime, generated_at: datetime) -> Decimal:
    delta = generated_at - _as_utc("signal_observed_at", signal_observed_at)
    seconds = (
        Decimal(delta.days) * SECONDS_PER_DAY
        + Decimal(delta.seconds)
        + (Decimal(delta.microseconds) / MICROSECONDS_PER_SECOND)
    )
    age_seconds = _normalize_decimal("signal_age_seconds", seconds)
    if age_seconds < ZERO:
        raise ValueError("signal_observed_at must not be after generated_at")
    return age_seconds


def _validate_row(row: StrategyCategoryRotationCompositeGateDigestRow) -> None:
    expected_status = _row_status(row.reason_codes)
    if row.readiness_status != expected_status:
        raise ValueError("readiness_status must match reason_codes")
    if f"category_rotation_composite_gate_{row.readiness_status}" not in row.reason_codes:
        raise ValueError("readiness_status must match category gate reason")
    if row.readiness_status == BLOCKED_STATUS and row.readiness_score != ZERO:
        raise ValueError("blocked readiness_score must be zero")


def _validate_report(report: StrategyCategoryRotationCompositeGateDigestReport) -> None:
    rows = report.rows
    if report.category_count != _count(len(rows)):
        raise ValueError("category_count must match rows")
    if report.pass_count != _status_count(rows, PASS_STATUS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, WATCH_STATUS):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, BLOCKED_STATUS):
        raise ValueError("blocked_count must match rows")
    if report.status != _report_status(
        rows,
        config=StrategyCategoryRotationCompositeGateDigestConfig(
            config_version=report.config_version,
            minimum_pass_categories=report.pass_count,
        ),
    ):
        if report.status != _status_from_counts(report):
            raise ValueError("status must match rows")
    if report.passed_category_ids != tuple(
        row.category_id for row in rows if row.readiness_status == PASS_STATUS
    ):
        raise ValueError("passed_category_ids must match rows")
    if report.max_readiness_score != _max_readiness_score(rows):
        raise ValueError("max_readiness_score must match rows")
    if report.min_readiness_score != _min_readiness_score(rows):
        raise ValueError("min_readiness_score must match rows")
    if report.average_readiness_score != _average_readiness_score(rows):
        raise ValueError("average_readiness_score must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    categories: Iterable[StrategyCategoryRotationCompositeGateSignal],
) -> tuple[StrategyCategoryRotationCompositeGateSignal, ...]:
    if isinstance(categories, (str, bytes)):
        raise ValueError("categories must be an iterable")
    try:
        rows = tuple(categories)
    except TypeError as exc:
        raise ValueError("categories must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not StrategyCategoryRotationCompositeGateSignal:
            raise ValueError("categories must contain exact signal rows")
        _require_paper_flags("signal", row)
        if row.category_id in seen:
            raise ValueError("categories must be unique")
        seen.add(row.category_id)
    return rows


def _normalize_rows(
    rows: object,
) -> tuple[StrategyCategoryRotationCompositeGateDigestRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("digest report rows must be a tuple")
    values = tuple(rows)
    seen: set[str] = set()
    for row in values:
        if type(row) is not StrategyCategoryRotationCompositeGateDigestRow:
            raise ValueError("digest report must contain exact rows")
        _require_paper_flags("row", row)
        if row.category_id in seen:
            raise ValueError("rows must contain unique categories")
        seen.add(row.category_id)
    expected_ranks = tuple(_count(index) for index in range(1, len(values) + 1))
    if tuple(row.rank for row in values) != expected_ranks:
        raise ValueError("rows must use consecutive ranks")
    if values != tuple(sorted(values, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sort")
    return values


def _normalize_reason_code_counts(
    rows: object,
) -> tuple[StrategyCategoryRotationCompositeGateDigestReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    values = tuple(rows)
    seen: set[str] = set()
    previous_key: tuple[Decimal, str] | None = None
    for row in values:
        if type(row) is not StrategyCategoryRotationCompositeGateDigestReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact count rows")
        _require_paper_flags("reason_code_count", row)
        if row.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        key = (-row.count, row.reason_code)
        if previous_key is not None and previous_key > key:
            raise ValueError("reason_code_counts must use deterministic sort")
        previous_key = key
        seen.add(row.reason_code)
    return values


def _normalize_category_ids(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    values = tuple(value)
    seen: set[str] = set()
    for category_id in values:
        _require_canonical_string(field_name, category_id)
        if category_id in seen:
            raise ValueError(f"{field_name} must be unique")
        seen.add(category_id)
    return values


def _row_sort_key(
    row: StrategyCategoryRotationCompositeGateDigestRow,
) -> tuple[Decimal, Decimal, str, str]:
    return (
        STATUS_SORT[row.readiness_status],
        -row.readiness_score,
        row.category_id,
        row.team_id,
    )


def _report_status(
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...],
    *,
    config: StrategyCategoryRotationCompositeGateDigestConfig,
) -> str:
    pass_count = _status_count(rows, PASS_STATUS)
    if any(row.readiness_status == BLOCKED_STATUS for row in rows):
        return BLOCKED_STATUS
    if pass_count >= config.minimum_pass_categories and pass_count > ZERO:
        return PASS_STATUS
    return WATCH_STATUS


def _status_from_counts(report: StrategyCategoryRotationCompositeGateDigestReport) -> str:
    if report.blocked_count > ZERO:
        return BLOCKED_STATUS
    if report.pass_count > ZERO:
        return PASS_STATUS
    return WATCH_STATUS


def _report_reason_codes(
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (EMPTY_REASON_CODE,)
    return _normalize_reason_codes(
        tuple(reason_code for row in rows for reason_code in row.reason_codes),
    )


def _reason_code_counts(
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...],
) -> tuple[StrategyCategoryRotationCompositeGateDigestReasonCodeCount, ...]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    return tuple(
        StrategyCategoryRotationCompositeGateDigestReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(
            counter.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _status_count(
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.readiness_status == status))


def _max_readiness_score(
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_probability(
        "max_readiness_score",
        max(row.readiness_score for row in rows),
    )


def _min_readiness_score(
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    return _normalize_probability(
        "min_readiness_score",
        min(row.readiness_score for row in rows),
    )


def _average_readiness_score(
    rows: tuple[StrategyCategoryRotationCompositeGateDigestRow, ...],
) -> Decimal:
    if not rows:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _normalize_probability(
            "average_readiness_score",
            sum(row.readiness_score for row in rows) / Decimal(len(rows)),
        )


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _nonnegative_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return ZERO
    return value


def _require_at_most(
    field_name: str,
    low_value: Decimal,
    high_value: Decimal,
) -> None:
    if low_value > high_value:
        raise ValueError(f"{field_name} must be less than or equal to watch threshold")


def _require_at_least(
    field_name: str,
    high_value: Decimal,
    low_value: Decimal,
) -> None:
    if high_value < low_value:
        raise ValueError(f"{field_name} must be at least watch threshold")


def _normalize_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    quantized = normalized.quantize(QUANTUM)
    if quantized != normalized:
        raise ValueError(f"{field_name} must use six decimal places")
    if quantized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_decimal(field_name: str, value: object) -> None:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


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
    if _has_unsafe_text(value):
        raise ValueError(f"{field_name} has unsafe text")


def _require_public_reference(value: object) -> None:
    if type(value) is not str:
        raise ValueError("public_reference must be a nonblank trimmed string")
    if not value or value.strip() != value:
        raise ValueError("public_reference must be a nonblank trimmed string")


def _require_member(field_name: str, value: object, allowed: tuple[str, ...]) -> None:
    if type(value) is not str or value not in allowed:
        raise ValueError(f"{field_name} must be one of {allowed}")


def _normalize_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    reason_codes = tuple(value)
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
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
    for markers, safe_reason in SENSITIVE_REASON_RULES:
        if any(marker in lowered for marker in markers):
            return safe_reason
    if _has_unsafe_text(lowered):
        return "surface_redacted"
    return value


def _require_reason_code(value: str) -> None:
    if type(value) is not str:
        raise ValueError("reason_codes must contain strings")
    if value != value.lower():
        raise ValueError("reason_codes must be lowercase snake_case strings")
    if value[0] == "_" or value[-1] == "_":
        raise ValueError("reason_codes must be lowercase snake_case strings")
    for part in value.split("_"):
        if not part or not part.isalnum() or part != part.lower():
            raise ValueError("reason_codes must be lowercase snake_case strings")


def _require_paper_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _redact_public_reference(value: str) -> str:
    if _contains_public_marker(value) or _has_unsafe_text(value):
        return f"public_ref_{_stable_ref_id(value)}"
    return value


def _stable_ref_id(value: str) -> str:
    total = sum((index + 1) * ord(character) for index, character in enumerate(value))
    return format(total, "x")


def _json_ready(value: Any, path: str = "") -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value), path)
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{path or 'value'} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{path or 'value'} must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError(f"{path or 'value'} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{path or 'value'} must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if value is None:
        return None
    if type(value) is bool:
        return value
    if isinstance(value, float):
        raise ValueError(f"{path or 'value'} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or 'value'} must use Decimal numeric strings")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            ready[key] = _json_ready(item, item_path)
        return ready
    if isinstance(value, (list, tuple)):
        return [
            _json_ready(item, f"{path}[{index}]" if path else f"value[{index}]")
            for index, item in enumerate(value)
        ]
    raise ValueError(f"{path or 'value'} is not JSON serializable")


def _reject_unsafe_public_values(label: str, value: object, path: str = "") -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_values(label, asdict(value), path)
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
        raise ValueError(f"{path or label} must not be a float")
    if type(value) is int:
        raise ValueError(f"{path or label} must use Decimal numeric strings")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if _has_unsafe_text(key):
                raise ValueError(f"unsafe field in {label}")
            item_path = key if not path else f"{path}.{key}"
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True")
            _reject_unsafe_public_values(label, item, item_path)
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_values(label, item, item_path)
        return
    raise ValueError(f"{path or label} is not JSON serializable")


def _contains_public_marker(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in PUBLIC_TEXT_MARKERS)


def _has_unsafe_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_TEXT_FRAGMENTS)
