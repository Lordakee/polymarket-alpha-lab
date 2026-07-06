"""Phase 1 paper-only cost break-even probability report.

This module reduces caller-supplied in-memory inputs into a deterministic
read-only report. It performs no external I/O and exposes no execution surface.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_STRATEGY_COST_BREAK_EVEN_REPORT_V2_CONFIG_VERSION = (
    "strategy-cost-break-even-report-v2"
)
DECIMAL_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DAYS_IN_YEAR = Decimal("365")
STATUSES = ("clear", "watch", "blocked")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
UNSAFE_PUBLIC_FRAGMENTS = (
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
class StrategyCostBreakEvenReportV2Config:
    config_version: str
    watch_net_edge_threshold_probability: Decimal
    max_observation_age_seconds: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_net_edge_threshold_probability",
            _normalize_nonnegative_decimal(
                "watch_net_edge_threshold_probability",
                self.watch_net_edge_threshold_probability,
            ),
        )
        object.__setattr__(
            self,
            "max_observation_age_seconds",
            _normalize_nonnegative_decimal(
                "max_observation_age_seconds",
                self.max_observation_age_seconds,
            ),
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyCostBreakEvenReportV2Input:
    candidate_ref: str
    market_ref: str
    observed_at: datetime
    forecast_probability: Decimal
    displayed_probability: Decimal
    taker_fee_rate: Decimal
    bid_ask_spread_probability: Decimal
    expected_slippage_probability: Decimal
    settlement_delay_days: Decimal
    annualized_capital_lockup_rate: Decimal
    confidence_haircut_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_ref", "market_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "displayed_probability",
            "taker_fee_rate",
            "bid_ask_spread_probability",
            "expected_slippage_probability",
            "annualized_capital_lockup_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "settlement_delay_days",
            _normalize_nonnegative_decimal(
                "settlement_delay_days",
                self.settlement_delay_days,
            ),
        )
        object.__setattr__(
            self,
            "confidence_haircut_rate",
            _normalize_probability_open_ceiling(
                "confidence_haircut_rate",
                self.confidence_haircut_rate,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyCostBreakEvenReportV2Row:
    candidate_ref: str
    market_ref: str
    observed_at: datetime
    forecast_probability: Decimal
    displayed_probability: Decimal
    gross_forecast_edge_probability: Decimal
    taker_fee_rate: Decimal
    taker_fee_cost_probability: Decimal
    bid_ask_spread_cost_probability: Decimal
    expected_slippage_probability: Decimal
    settlement_delay_days: Decimal
    annualized_capital_lockup_rate: Decimal
    settlement_delay_capital_lockup_probability: Decimal
    direct_cost_probability: Decimal
    confidence_haircut_rate: Decimal
    confidence_haircut_cost_probability: Decimal
    minimum_forecast_edge_probability: Decimal
    net_forecast_edge_probability: Decimal
    age_seconds: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("candidate_ref", "market_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "displayed_probability",
            "taker_fee_rate",
            "bid_ask_spread_cost_probability",
            "expected_slippage_probability",
            "annualized_capital_lockup_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "confidence_haircut_rate",
            _normalize_probability_open_ceiling(
                "confidence_haircut_rate",
                self.confidence_haircut_rate,
            ),
        )
        for field_name in (
            "gross_forecast_edge_probability",
            "net_forecast_edge_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_cost_probability",
            "settlement_delay_days",
            "settlement_delay_capital_lockup_probability",
            "direct_cost_probability",
            "confidence_haircut_cost_probability",
            "minimum_forecast_edge_probability",
            "age_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class StrategyCostBreakEvenReportV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: int
    row_count: int
    clear_count: int
    watch_count: int
    blocked_count: int
    highest_minimum_forecast_edge_probability: Decimal | None
    average_minimum_forecast_edge_probability: Decimal | None
    rows: tuple[StrategyCostBreakEvenReportV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "row_count",
            "clear_count",
            "watch_count",
            "blocked_count",
        ):
            _require_nonnegative_int(field_name, getattr(self, field_name))
        for field_name in (
            "highest_minimum_forecast_edge_probability",
            "average_minimum_forecast_edge_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_optional_nonnegative_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_strategy_cost_break_even_report_v2(
    inputs: Iterable[StrategyCostBreakEvenReportV2Input],
    *,
    config: StrategyCostBreakEvenReportV2Config,
    generated_at: datetime,
) -> StrategyCostBreakEvenReportV2Report:
    if type(config) is not StrategyCostBreakEvenReportV2Config:
        raise ValueError("config must be a StrategyCostBreakEvenReportV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    value,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    minimum_edges = tuple(row.minimum_forecast_edge_probability for row in rows)
    return StrategyCostBreakEvenReportV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=len(normalized_inputs),
        row_count=len(rows),
        clear_count=_status_count(rows, "clear"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        highest_minimum_forecast_edge_probability=max(minimum_edges)
        if minimum_edges
        else None,
        average_minimum_forecast_edge_probability=_average_decimal(minimum_edges)
        if minimum_edges
        else None,
        rows=rows,
    )


def strategy_cost_break_even_report_v2_payload(
    report: StrategyCostBreakEvenReportV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyCostBreakEvenReportV2Report:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a StrategyCostBreakEvenReportV2Report")
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


def _row_from_input(
    value: StrategyCostBreakEvenReportV2Input,
    *,
    config: StrategyCostBreakEvenReportV2Config,
    generated_at: datetime,
) -> StrategyCostBreakEvenReportV2Row:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    gross_edge = _subtract_decimal(value.forecast_probability, value.displayed_probability)
    taker_fee_cost = _multiply_decimal(value.displayed_probability, value.taker_fee_rate)
    settlement_delay_cost = _divide_decimal(
        _multiply_decimal(
            _multiply_decimal(
                value.displayed_probability,
                value.annualized_capital_lockup_rate,
            ),
            value.settlement_delay_days,
        ),
        DAYS_IN_YEAR,
    )
    direct_cost = _sum_decimals(
        (
            taker_fee_cost,
            value.bid_ask_spread_probability,
            value.expected_slippage_probability,
            settlement_delay_cost,
        ),
    )
    minimum_edge = _minimum_edge_after_confidence_haircut(
        direct_cost,
        value.confidence_haircut_rate,
    )
    confidence_haircut_cost = _subtract_decimal(minimum_edge, direct_cost)
    net_edge = _subtract_decimal(gross_edge, minimum_edge)
    age_seconds = _seconds_between(generated_at, observed_at)
    status = _status_for(
        net_forecast_edge_probability=net_edge,
        age_seconds=age_seconds,
        config=config,
    )
    return StrategyCostBreakEvenReportV2Row(
        candidate_ref=value.candidate_ref,
        market_ref=value.market_ref,
        observed_at=observed_at,
        forecast_probability=value.forecast_probability,
        displayed_probability=value.displayed_probability,
        gross_forecast_edge_probability=gross_edge,
        taker_fee_rate=value.taker_fee_rate,
        taker_fee_cost_probability=taker_fee_cost,
        bid_ask_spread_cost_probability=value.bid_ask_spread_probability,
        expected_slippage_probability=value.expected_slippage_probability,
        settlement_delay_days=value.settlement_delay_days,
        annualized_capital_lockup_rate=value.annualized_capital_lockup_rate,
        settlement_delay_capital_lockup_probability=settlement_delay_cost,
        direct_cost_probability=direct_cost,
        confidence_haircut_rate=value.confidence_haircut_rate,
        confidence_haircut_cost_probability=confidence_haircut_cost,
        minimum_forecast_edge_probability=minimum_edge,
        net_forecast_edge_probability=net_edge,
        age_seconds=age_seconds,
        status=status,
        reason_codes=_reason_codes_for(
            net_forecast_edge_probability=net_edge,
            confidence_haircut_rate=value.confidence_haircut_rate,
            settlement_delay_cost=settlement_delay_cost,
            age_seconds=age_seconds,
            status=status,
            config=config,
        ),
    )


def _status_for(
    *,
    net_forecast_edge_probability: Decimal,
    age_seconds: Decimal,
    config: StrategyCostBreakEvenReportV2Config,
) -> str:
    if net_forecast_edge_probability <= ZERO:
        return "blocked"
    if (
        age_seconds > config.max_observation_age_seconds
        or net_forecast_edge_probability < config.watch_net_edge_threshold_probability
    ):
        return "watch"
    return "clear"


def _reason_codes_for(
    *,
    net_forecast_edge_probability: Decimal,
    confidence_haircut_rate: Decimal,
    settlement_delay_cost: Decimal,
    age_seconds: Decimal,
    status: str,
    config: StrategyCostBreakEvenReportV2Config,
) -> tuple[str, ...]:
    codes: list[str] = []
    if status == "blocked":
        codes.append("below_minimum_forecast_edge")
    elif net_forecast_edge_probability < config.watch_net_edge_threshold_probability:
        codes.append("thin_net_forecast_edge")
    else:
        codes.append("break_even_edge_cleared")
    if age_seconds > config.max_observation_age_seconds:
        codes.append("stale_observation")
    if confidence_haircut_rate > ZERO:
        codes.append("confidence_haircut_applied")
    if settlement_delay_cost > ZERO:
        codes.append("settlement_delay_capital_lockup")
    return _normalize_reason_codes("reason_codes", tuple(codes))


def _row_sort_key(
    row: StrategyCostBreakEvenReportV2Row,
) -> tuple[int, Decimal, Decimal, str, str]:
    return (
        {"blocked": 0, "watch": 1, "clear": 2}[row.status],
        row.net_forecast_edge_probability,
        -row.minimum_forecast_edge_probability,
        row.market_ref,
        row.candidate_ref,
    )


def _normalize_inputs(
    inputs: Iterable[StrategyCostBreakEvenReportV2Input],
) -> tuple[StrategyCostBreakEvenReportV2Input, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not StrategyCostBreakEvenReportV2Input:
            raise ValueError(
                "inputs must contain only StrategyCostBreakEvenReportV2Input values",
            )
        _require_hard_flags("input", value)
        if value.candidate_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate candidate_ref values")
        seen_refs.add(value.candidate_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[StrategyCostBreakEvenReportV2Row],
) -> tuple[StrategyCostBreakEvenReportV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    candidate_refs = tuple(row.candidate_ref for row in normalized)
    if len(set(candidate_refs)) != len(candidate_refs):
        raise ValueError("rows must not contain duplicate candidate_ref values")
    for row in normalized:
        if type(row) is not StrategyCostBreakEvenReportV2Row:
            raise ValueError("rows must contain StrategyCostBreakEvenReportV2Row values")
        _require_hard_flags("row", row)
        _verify_digest(row)
    return normalized


def _validate_row_consistency(row: StrategyCostBreakEvenReportV2Row) -> None:
    expected_gross_edge = _subtract_decimal(
        row.forecast_probability,
        row.displayed_probability,
    )
    if row.gross_forecast_edge_probability != expected_gross_edge:
        raise ValueError("gross_forecast_edge_probability does not match probabilities")
    expected_taker_fee_cost = _multiply_decimal(
        row.displayed_probability,
        row.taker_fee_rate,
    )
    if row.taker_fee_cost_probability != expected_taker_fee_cost:
        raise ValueError("taker_fee_cost_probability does not match displayed probability")
    expected_settlement_delay_cost = _divide_decimal(
        _multiply_decimal(
            _multiply_decimal(
                row.displayed_probability,
                row.annualized_capital_lockup_rate,
            ),
            row.settlement_delay_days,
        ),
        DAYS_IN_YEAR,
    )
    if row.settlement_delay_capital_lockup_probability != expected_settlement_delay_cost:
        raise ValueError(
            "settlement_delay_capital_lockup_probability does not match inputs",
        )
    expected_direct_cost = _sum_decimals(
        (
            row.taker_fee_cost_probability,
            row.bid_ask_spread_cost_probability,
            row.expected_slippage_probability,
            row.settlement_delay_capital_lockup_probability,
        ),
    )
    if row.direct_cost_probability != expected_direct_cost:
        raise ValueError("direct_cost_probability does not match cost components")
    expected_minimum_edge = _minimum_edge_after_confidence_haircut(
        row.direct_cost_probability,
        row.confidence_haircut_rate,
    )
    if row.minimum_forecast_edge_probability != expected_minimum_edge:
        raise ValueError("minimum_forecast_edge_probability does not match costs")
    expected_haircut_cost = _subtract_decimal(
        row.minimum_forecast_edge_probability,
        row.direct_cost_probability,
    )
    if row.confidence_haircut_cost_probability != expected_haircut_cost:
        raise ValueError("confidence_haircut_cost_probability does not match inputs")
    expected_net_edge = _subtract_decimal(
        row.gross_forecast_edge_probability,
        row.minimum_forecast_edge_probability,
    )
    if row.net_forecast_edge_probability != expected_net_edge:
        raise ValueError("net_forecast_edge_probability does not match break-even edge")


def _validate_report_consistency(report: StrategyCostBreakEvenReportV2Report) -> None:
    if report.row_count != len(report.rows):
        raise ValueError("row_count must match rows")
    if report.candidate_count != report.row_count:
        raise ValueError("candidate_count must match row_count")
    if report.row_count != report.clear_count + report.watch_count + report.blocked_count:
        raise ValueError("status counts must match row_count")
    if report.clear_count != _status_count(report.rows, "clear"):
        raise ValueError("clear_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(report.rows, "blocked"):
        raise ValueError("blocked_count must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic ordering")
    minimum_edges = tuple(row.minimum_forecast_edge_probability for row in report.rows)
    if not minimum_edges:
        if report.highest_minimum_forecast_edge_probability is not None:
            raise ValueError("highest_minimum_forecast_edge_probability must be None")
        if report.average_minimum_forecast_edge_probability is not None:
            raise ValueError("average_minimum_forecast_edge_probability must be None")
        return
    if report.highest_minimum_forecast_edge_probability != max(minimum_edges):
        raise ValueError("highest_minimum_forecast_edge_probability must match rows")
    if report.average_minimum_forecast_edge_probability != _average_decimal(minimum_edges):
        raise ValueError("average_minimum_forecast_edge_probability must match rows")


def _verify_report_integrity(report: StrategyCostBreakEvenReportV2Report) -> None:
    _validate_report_consistency(report)
    _verify_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _verify_public_payload_integrity(payload: dict[str, Any]) -> None:
    _verify_public_payload_digest("payload", payload)
    rows = payload.get("rows")
    if rows is None:
        return
    if type(rows) is not list:
        raise ValueError("payload.rows must be a list")
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise ValueError("payload.rows must contain JSON objects")
        _verify_public_payload_digest(f"payload.rows[{index}]", row)


def _verify_public_payload_digest(label: str, payload: dict[str, Any]) -> None:
    provided = payload.get("derived_validation_digest")
    _require_digest(f"{label}.derived_validation_digest", provided)
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(rows: tuple[StrategyCostBreakEvenReportV2Row, ...], status: str) -> int:
    return sum(1 for row in rows if row.status == status)


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    return _quantize(sum(values, ZERO))


def _average_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        raise ValueError("values must not be empty")
    return _divide_decimal(_sum_decimals(values), Decimal(len(values)))


def _minimum_edge_after_confidence_haircut(
    direct_cost_probability: Decimal,
    confidence_haircut_rate: Decimal,
) -> Decimal:
    return _divide_decimal(direct_cost_probability, ONE - confidence_haircut_rate)


def _seconds_between(later: datetime, earlier: datetime) -> Decimal:
    total_seconds = _as_utc("later", later) - _as_utc("earlier", earlier)
    return _quantize(Decimal(str(total_seconds.total_seconds())))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left - right)


def _multiply_decimal(left: Decimal, right: Decimal) -> Decimal:
    return _quantize(left * right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        raise ValueError("division denominator must be nonzero")
    return _quantize(left / right)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_nonnegative_int(field_name: str, value: object) -> None:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be an int")
    if value < 0:
        raise ValueError(f"{field_name} must be nonnegative")


def _require_decimal(field_name: str, value: object) -> None:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    _require_decimal(field_name, value)
    return _quantize(value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _normalize_nonnegative_decimal(field_name, value)


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must not exceed 1")
    return normalized


def _normalize_probability_open_ceiling(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized >= ONE:
        raise ValueError(f"{field_name} must be less than 1")
    return normalized


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must use deterministic ordering")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_public_string(field_name, value)
    if value.startswith("_") or value.endswith("_") or "__" in value:
        raise ValueError(f"{field_name} must be a canonical reason code")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "_"):
            raise ValueError(f"{field_name} must be a canonical reason code")


def _apply_or_verify_digest(
    value: StrategyCostBreakEvenReportV2Row | StrategyCostBreakEvenReportV2Report,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: StrategyCostBreakEvenReportV2Row | StrategyCostBreakEvenReportV2Report,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: StrategyCostBreakEvenReportV2Row | StrategyCostBreakEvenReportV2Report,
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    payload = _json_ready(digest_input)
    encoded = dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    compact = "".join(character for character in lowered if character.isalnum())
    return any(
        fragment in lowered or fragment in compact
        for fragment in UNSAFE_PUBLIC_FRAGMENTS
    )


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    _allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            item_path = field.name if not path else f"{path}.{field.name}"
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                item_path,
            )
        return
    if type(value) is dict:
        if not _allow_json_containers and path:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            item_path = key if not path else f"{path}.{key}"
            _require_canonical_public_string("public_payload_key", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{item_path} must be True for {label}")
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                _allow_json_containers=True,
            )
        return
    if type(value) is list:
        if not _allow_json_containers and path:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(
                label,
                item,
                item_path,
                _allow_json_containers=True,
            )
        return
    if type(value) is tuple:
        for index, item in enumerate(value):
            item_path = f"{path}[{index}]" if path else f"{label}[{index}]"
            _reject_unsafe_public_payload(label, item, item_path)
        return
    if type(value) is str:
        _require_canonical_public_string(current_path, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{current_path} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{current_path} must be finite")
        return
    if isinstance(value, datetime):
        _as_utc(current_path, value)
        return
    if value is None or type(value) in (bool, int):
        return
    if isinstance(value, float):
        raise ValueError(f"{current_path} must not be a float")
    raise ValueError(f"{current_path} is not JSON serializable")


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) in (str, int, bool):
        return value
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    raise ValueError("value is not JSON-ready")


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(DECIMAL_QUANTUM, rounding=ROUND_HALF_EVEN)


__all__ = (
    "DEFAULT_STRATEGY_COST_BREAK_EVEN_REPORT_V2_CONFIG_VERSION",
    "DECIMAL_QUANTUM",
    "STATUSES",
    "StrategyCostBreakEvenReportV2Config",
    "StrategyCostBreakEvenReportV2Input",
    "StrategyCostBreakEvenReportV2Report",
    "StrategyCostBreakEvenReportV2Row",
    "build_strategy_cost_break_even_report_v2",
    "strategy_cost_break_even_report_v2_payload",
)
