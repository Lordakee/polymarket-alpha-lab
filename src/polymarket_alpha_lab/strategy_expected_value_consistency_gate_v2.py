"""Phase 1 readonly expected-value consistency gate."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


__all__ = (
    "DEFAULT_STRATEGY_EXPECTED_VALUE_CONSISTENCY_GATE_V2_CONFIG_VERSION",
    "StrategyExpectedValueConsistencyGateV2Config",
    "StrategyExpectedValueConsistencyGateV2Input",
    "StrategyExpectedValueConsistencyGateV2ReasonCodeCount",
    "StrategyExpectedValueConsistencyGateV2Report",
    "StrategyExpectedValueConsistencyGateV2Row",
    "build_strategy_expected_value_consistency_gate_v2_report",
    "strategy_expected_value_consistency_gate_v2_payload",
)


DEFAULT_STRATEGY_EXPECTED_VALUE_CONSISTENCY_GATE_V2_CONFIG_VERSION = (
    "strategy-expected-value-consistency-gate-v2"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
STATUSES = ("pass", "watch", "blocked")
STATUS_WEIGHT = {
    "blocked": Decimal("2.000000"),
    "watch": Decimal("1.000000"),
    "pass": Decimal("0.000000"),
}
NEXT_STEP_BY_STATUS = {
    "pass": "paper_monitor_only",
    "watch": "review_expected_value_assumptions",
    "blocked": "block_expected_value_posture",
}
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
ROW_REASON_PRIORITY = (
    "evc_break_even_below_market_blocked",
    "evc_net_expected_value_negative_blocked",
    "evc_liquidity_exit_penalty_high_blocked",
    "evc_resolution_risk_high_blocked",
    "evc_capital_lockup_days_high_blocked",
    "evc_capital_lockup_penalty_high_blocked",
    "evc_fee_adjusted_break_even_premium_high_watch",
    "evc_net_expected_value_thin_watch",
    "evc_forecast_market_edge_thin_watch",
    "evc_liquidity_exit_penalty_elevated_watch",
    "evc_resolution_risk_elevated_watch",
    "evc_capital_lockup_elevated_watch",
    "evc_consistency_clear",
)
REPORT_REASON_PRIORITY = (
    "evc_break_even_below_market_blocked",
    "evc_net_expected_value_negative_blocked",
    "evc_liquidity_exit_penalty_high_blocked",
    "evc_resolution_risk_high_blocked",
    "evc_capital_lockup_days_high_blocked",
    "evc_capital_lockup_penalty_high_blocked",
    "evc_fee_adjusted_break_even_premium_high_watch",
    "evc_net_expected_value_thin_watch",
    "evc_forecast_market_edge_thin_watch",
    "evc_liquidity_exit_penalty_elevated_watch",
    "evc_resolution_risk_elevated_watch",
    "evc_capital_lockup_elevated_watch",
)
HEX_CHARS = frozenset("0123456789abcdef")


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise ValueError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class StrategyExpectedValueConsistencyGateV2Config(_FinalPublicDataclass):
    config_version: str = (
        DEFAULT_STRATEGY_EXPECTED_VALUE_CONSISTENCY_GATE_V2_CONFIG_VERSION
    )
    minimum_pass_net_expected_value: Decimal = Decimal("0.020000")
    minimum_watch_net_expected_value: Decimal = Decimal("0.000000")
    maximum_fee_adjusted_break_even_premium: Decimal = Decimal("0.050000")
    maximum_liquidity_exit_penalty: Decimal = Decimal("0.050000")
    maximum_resolution_risk_probability: Decimal = Decimal("0.100000")
    maximum_capital_lockup_penalty: Decimal = Decimal("0.030000")
    maximum_capital_lockup_days: Decimal = Decimal("45.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyExpectedValueConsistencyGateV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_EXPECTED_VALUE_CONSISTENCY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "minimum_pass_net_expected_value",
            "minimum_watch_net_expected_value",
            "maximum_fee_adjusted_break_even_premium",
            "maximum_liquidity_exit_penalty",
            "maximum_resolution_risk_probability",
            "maximum_capital_lockup_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "maximum_capital_lockup_days",
            _require_nonnegative_decimal(
                "maximum_capital_lockup_days",
                self.maximum_capital_lockup_days,
            ),
        )
        if self.minimum_watch_net_expected_value > self.minimum_pass_net_expected_value:
            raise ValueError(
                "minimum_watch_net_expected_value must not exceed pass threshold",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyExpectedValueConsistencyGateV2Input(_FinalPublicDataclass):
    candidate_id: str
    market_slug: str
    forecast_probability: Decimal
    market_probability: Decimal
    fee_adjusted_break_even_probability: Decimal
    liquidity_exit_penalty: Decimal
    resolution_risk_probability: Decimal
    capital_lockup_penalty: Decimal
    capital_lockup_days: Decimal
    observed_at: datetime
    source_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyExpectedValueConsistencyGateV2Input, "input")
        for field_name in ("candidate_id", "market_slug", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_adjusted_break_even_probability",
            "liquidity_exit_penalty",
            "resolution_risk_probability",
            "capital_lockup_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "capital_lockup_days",
            _require_nonnegative_decimal("capital_lockup_days", self.capital_lockup_days),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class StrategyExpectedValueConsistencyGateV2Row(_FinalPublicDataclass):
    candidate_id: str
    market_slug: str
    gate_status: str
    forecast_probability: Decimal
    market_probability: Decimal
    fee_adjusted_break_even_probability: Decimal
    fee_adjusted_break_even_premium: Decimal
    raw_probability_edge: Decimal
    liquidity_exit_penalty: Decimal
    resolution_risk_probability: Decimal
    capital_lockup_penalty: Decimal
    capital_lockup_days: Decimal
    total_penalty_probability: Decimal
    penalty_adjusted_break_even_probability: Decimal
    net_expected_value_probability: Decimal
    observed_at: datetime
    source_config_version: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyExpectedValueConsistencyGateV2Row, "row")
        for field_name in ("candidate_id", "market_slug", "source_config_version"):
            _require_public_string(field_name, getattr(self, field_name))
        _require_status("gate_status", self.gate_status)
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_adjusted_break_even_probability",
            "liquidity_exit_penalty",
            "resolution_risk_probability",
            "capital_lockup_penalty",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_adjusted_break_even_premium",
            "raw_probability_edge",
            "net_expected_value_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_signed_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "capital_lockup_days",
            "total_penalty_probability",
            "penalty_adjusted_break_even_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes, require_nonempty=True),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class StrategyExpectedValueConsistencyGateV2ReasonCodeCount(_FinalPublicDataclass):
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyExpectedValueConsistencyGateV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "candidate_ratio",
            _require_ratio_decimal("candidate_ratio", self.candidate_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyExpectedValueConsistencyGateV2Report(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    min_net_expected_value_probability: Decimal
    max_penalty_adjusted_break_even_probability: Decimal
    max_liquidity_exit_penalty: Decimal
    max_resolution_risk_probability: Decimal
    max_capital_lockup_days: Decimal
    status: str
    recommended_next_step: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyExpectedValueConsistencyGateV2ReasonCodeCount, ...]
    rows: tuple[StrategyExpectedValueConsistencyGateV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyExpectedValueConsistencyGateV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_EXPECTED_VALUE_CONSISTENCY_GATE_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "blocked_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_count_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "min_net_expected_value_probability",
            _require_signed_probability_decimal(
                "min_net_expected_value_probability",
                self.min_net_expected_value_probability,
            ),
        )
        for field_name in (
            "max_penalty_adjusted_break_even_probability",
            "max_capital_lockup_days",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_liquidity_exit_penalty",
            "max_resolution_risk_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        _require_public_string("recommended_next_step", self.recommended_next_step)
        if self.recommended_next_step != NEXT_STEP_BY_STATUS[self.status]:
            raise ValueError("recommended_next_step must match status")
        object.__setattr__(
            self,
            "reason_codes",
            _require_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _require_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _require_rows(self.rows))
        _validate_report_status(self)
        if self.derived_validation_digest:
            _require_sha256("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != _derived_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _derived_validation_digest(self),
            )
        _validate_report_materialized_fields(self)
        _reject_unsafe_public_payload("report", self)
        _require_hard_flags("report", self)


def build_strategy_expected_value_consistency_gate_v2_report(
    candidates: Iterable[StrategyExpectedValueConsistencyGateV2Input],
    *,
    config: StrategyExpectedValueConsistencyGateV2Config,
    generated_at: datetime,
) -> StrategyExpectedValueConsistencyGateV2Report:
    if type(config) is not StrategyExpectedValueConsistencyGateV2Config:
        raise ValueError(
            "config must be a StrategyExpectedValueConsistencyGateV2Config",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    inputs = _normalize_inputs(candidates)
    rows = tuple(
        sorted(
            (
                _row_from_input(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in inputs
            ),
            key=_row_sort_key,
        ),
    )
    status = _rollup_status(tuple(row.gate_status for row in rows))
    return StrategyExpectedValueConsistencyGateV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        blocked_count=_status_count(rows, "blocked"),
        min_net_expected_value_probability=_min_decimal(
            tuple(row.net_expected_value_probability for row in rows),
        ),
        max_penalty_adjusted_break_even_probability=_max_decimal(
            tuple(row.penalty_adjusted_break_even_probability for row in rows),
        ),
        max_liquidity_exit_penalty=_max_decimal(
            tuple(row.liquidity_exit_penalty for row in rows),
        ),
        max_resolution_risk_probability=_max_decimal(
            tuple(row.resolution_risk_probability for row in rows),
        ),
        max_capital_lockup_days=_max_decimal(tuple(row.capital_lockup_days for row in rows)),
        status=status,
        recommended_next_step=NEXT_STEP_BY_STATUS[status],
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_expected_value_consistency_gate_v2_payload(
    report: StrategyExpectedValueConsistencyGateV2Report | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is StrategyExpectedValueConsistencyGateV2Report:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        return payload
    if type(report) is dict:
        _reject_unsafe_public_payload("payload", report)
        _reject_public_numeric_values(report)
        payload = _json_ready(report)
        if not isinstance(payload, dict):
            raise ValueError("report payload must be an object")
        _require_hard_flags("payload", _PayloadFlags(payload))
        supplied_digest = payload.get("derived_validation_digest")
        if type(supplied_digest) is not str:
            raise ValueError("derived_validation_digest is required")
        _require_sha256("derived_validation_digest", supplied_digest)
        if supplied_digest != _payload_validation_digest(payload):
            raise ValueError("derived_validation_digest does not match report payload")
        return payload
    raise ValueError("report must be a StrategyExpectedValueConsistencyGateV2Report")


@dataclass(frozen=True)
class _PayloadFlags:
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


def _normalize_inputs(
    candidates: Iterable[StrategyExpectedValueConsistencyGateV2Input],
) -> tuple[StrategyExpectedValueConsistencyGateV2Input, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be an iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be an iterable") from exc
    seen: set[str] = set()
    for item in items:
        if type(item) is not StrategyExpectedValueConsistencyGateV2Input:
            raise ValueError(
                "candidates must contain StrategyExpectedValueConsistencyGateV2Input",
            )
        _require_hard_flags("input", item)
        if item.candidate_id in seen:
            raise ValueError("candidate_id values must be unique")
        seen.add(item.candidate_id)
    return items


def _row_from_input(
    item: StrategyExpectedValueConsistencyGateV2Input,
    *,
    config: StrategyExpectedValueConsistencyGateV2Config,
    generated_at: datetime,
) -> StrategyExpectedValueConsistencyGateV2Row:
    if item.observed_at > generated_at:
        raise ValueError("observed_at must not be in the future")
    break_even_premium = _quantize(
        item.fee_adjusted_break_even_probability - item.market_probability,
    )
    raw_edge = _quantize(item.forecast_probability - item.market_probability)
    total_penalty = _quantize(
        item.liquidity_exit_penalty
        + item.resolution_risk_probability
        + item.capital_lockup_penalty,
    )
    penalty_adjusted_break_even = _quantize(
        item.fee_adjusted_break_even_probability + total_penalty,
    )
    net_expected_value = _quantize(
        item.forecast_probability - penalty_adjusted_break_even,
    )
    reason_codes = _row_reason_codes(
        item,
        break_even_premium=break_even_premium,
        raw_edge=raw_edge,
        net_expected_value=net_expected_value,
        config=config,
    )
    return StrategyExpectedValueConsistencyGateV2Row(
        candidate_id=item.candidate_id,
        market_slug=item.market_slug,
        gate_status=_row_status(reason_codes),
        forecast_probability=item.forecast_probability,
        market_probability=item.market_probability,
        fee_adjusted_break_even_probability=item.fee_adjusted_break_even_probability,
        fee_adjusted_break_even_premium=break_even_premium,
        raw_probability_edge=raw_edge,
        liquidity_exit_penalty=item.liquidity_exit_penalty,
        resolution_risk_probability=item.resolution_risk_probability,
        capital_lockup_penalty=item.capital_lockup_penalty,
        capital_lockup_days=item.capital_lockup_days,
        total_penalty_probability=total_penalty,
        penalty_adjusted_break_even_probability=penalty_adjusted_break_even,
        net_expected_value_probability=net_expected_value,
        observed_at=item.observed_at,
        source_config_version=item.source_config_version,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: StrategyExpectedValueConsistencyGateV2Input,
    *,
    break_even_premium: Decimal,
    raw_edge: Decimal,
    net_expected_value: Decimal,
    config: StrategyExpectedValueConsistencyGateV2Config,
) -> tuple[str, ...]:
    reasons = list(item.reason_codes)
    if item.fee_adjusted_break_even_probability < item.market_probability:
        reasons.append("evc_break_even_below_market_blocked")
    elif break_even_premium > config.maximum_fee_adjusted_break_even_premium:
        reasons.append("evc_fee_adjusted_break_even_premium_high_watch")

    if net_expected_value < ZERO:
        reasons.append("evc_net_expected_value_negative_blocked")
    elif net_expected_value < config.minimum_pass_net_expected_value:
        reasons.append("evc_net_expected_value_thin_watch")

    if raw_edge <= config.minimum_watch_net_expected_value:
        reasons.append("evc_forecast_market_edge_thin_watch")

    liquidity_watch_threshold = _quantize(
        config.maximum_liquidity_exit_penalty * Decimal("0.800000"),
    )
    if item.liquidity_exit_penalty > config.maximum_liquidity_exit_penalty:
        reasons.append("evc_liquidity_exit_penalty_high_blocked")
    elif item.liquidity_exit_penalty > liquidity_watch_threshold:
        reasons.append("evc_liquidity_exit_penalty_elevated_watch")

    resolution_watch_threshold = _quantize(
        config.maximum_resolution_risk_probability * Decimal("0.800000"),
    )
    if item.resolution_risk_probability > config.maximum_resolution_risk_probability:
        reasons.append("evc_resolution_risk_high_blocked")
    elif item.resolution_risk_probability > resolution_watch_threshold:
        reasons.append("evc_resolution_risk_elevated_watch")

    lockup_days_watch_threshold = _quantize(
        config.maximum_capital_lockup_days * Decimal("0.800000"),
    )
    lockup_penalty_watch_threshold = _quantize(
        config.maximum_capital_lockup_penalty * Decimal("0.800000"),
    )
    if item.capital_lockup_days > config.maximum_capital_lockup_days:
        reasons.append("evc_capital_lockup_days_high_blocked")
    elif (
        config.maximum_capital_lockup_days > ZERO
        and item.capital_lockup_days > lockup_days_watch_threshold
    ):
        reasons.append("evc_capital_lockup_elevated_watch")
    if item.capital_lockup_penalty > config.maximum_capital_lockup_penalty:
        reasons.append("evc_capital_lockup_penalty_high_blocked")
    elif item.capital_lockup_penalty > lockup_penalty_watch_threshold:
        reasons.append("evc_capital_lockup_elevated_watch")

    if not any(reason.startswith("evc_") for reason in reasons):
        reasons.append("evc_consistency_clear")
    return _require_reason_codes(tuple(dict.fromkeys(reasons)), require_nonempty=True)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code.endswith("_blocked") for reason_code in reason_codes):
        return "blocked"
    if any(reason_code.endswith("_watch") for reason_code in reason_codes):
        return "watch"
    return "pass"


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if any(status == "blocked" for status in statuses):
        return "blocked"
    if any(status == "watch" for status in statuses):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyExpectedValueConsistencyGateV2Row, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("ev_consistency_gate_empty",)
    status = _rollup_status(tuple(row.gate_status for row in rows))
    reason_codes = [f"ev_consistency_gate_{'clear' if status == 'pass' else status}"]
    row_reasons = frozenset(
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code.startswith("evc_") and reason_code != "evc_consistency_clear"
    )
    for reason_code in REPORT_REASON_PRIORITY:
        if reason_code in row_reasons:
            reason_codes.append(reason_code)
    for reason_code in sorted(row_reasons - frozenset(REPORT_REASON_PRIORITY)):
        reason_codes.append(reason_code)
    return tuple(reason_codes)


def _reason_code_counts(
    rows: tuple[StrategyExpectedValueConsistencyGateV2Row, ...],
) -> tuple[StrategyExpectedValueConsistencyGateV2ReasonCodeCount, ...]:
    if not rows:
        return ()
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    denominator = _count(len(rows))
    return tuple(
        StrategyExpectedValueConsistencyGateV2ReasonCodeCount(
            reason_code=reason_code,
            count=count,
            candidate_ratio=_ratio(count, denominator),
        )
        for count, reason_code in sorted(
            ((_count(count), reason_code) for reason_code, count in counter.items()),
            key=lambda item: (-item[0], item[1]),
        )
    )


def _row_sort_key(row: StrategyExpectedValueConsistencyGateV2Row) -> tuple[Decimal, Decimal, str]:
    return (
        -STATUS_WEIGHT[row.gate_status],
        row.net_expected_value_probability,
        row.candidate_id,
    )


def _status_count(
    rows: tuple[StrategyExpectedValueConsistencyGateV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.gate_status == status))


def _validate_row(row: StrategyExpectedValueConsistencyGateV2Row) -> None:
    expected_premium = _quantize(
        row.fee_adjusted_break_even_probability - row.market_probability,
    )
    if row.fee_adjusted_break_even_premium != expected_premium:
        raise ValueError("fee_adjusted_break_even_premium must match break-even less market")
    expected_raw_edge = _quantize(row.forecast_probability - row.market_probability)
    if row.raw_probability_edge != expected_raw_edge:
        raise ValueError("raw_probability_edge must match forecast less market")
    expected_total_penalty = _quantize(
        row.liquidity_exit_penalty
        + row.resolution_risk_probability
        + row.capital_lockup_penalty,
    )
    if row.total_penalty_probability != expected_total_penalty:
        raise ValueError("total_penalty_probability must match penalty assumptions")
    expected_adjusted_break_even = _quantize(
        row.fee_adjusted_break_even_probability + row.total_penalty_probability,
    )
    if row.penalty_adjusted_break_even_probability != expected_adjusted_break_even:
        raise ValueError(
            "penalty_adjusted_break_even_probability must match break-even plus penalties",
        )
    expected_net_expected_value = _quantize(
        row.forecast_probability - row.penalty_adjusted_break_even_probability,
    )
    if row.net_expected_value_probability != expected_net_expected_value:
        raise ValueError("net_expected_value_probability must match forecast less break-even")
    if row.gate_status != _row_status(row.reason_codes):
        raise ValueError("gate_status must match reason_codes")


def _validate_report_status(report: StrategyExpectedValueConsistencyGateV2Report) -> None:
    expected_status = _rollup_status(tuple(row.gate_status for row in report.rows))
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.recommended_next_step != NEXT_STEP_BY_STATUS[report.status]:
        raise ValueError("recommended_next_step must match status")


def _validate_report_materialized_fields(
    report: StrategyExpectedValueConsistencyGateV2Report,
) -> None:
    rows = report.rows
    checks = {
        "candidate_count": _count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "blocked_count": _status_count(rows, "blocked"),
        "min_net_expected_value_probability": _min_decimal(
            tuple(row.net_expected_value_probability for row in rows),
        ),
        "max_penalty_adjusted_break_even_probability": _max_decimal(
            tuple(row.penalty_adjusted_break_even_probability for row in rows),
        ),
        "max_liquidity_exit_penalty": _max_decimal(
            tuple(row.liquidity_exit_penalty for row in rows),
        ),
        "max_resolution_risk_probability": _max_decimal(
            tuple(row.resolution_risk_probability for row in rows),
        ),
        "max_capital_lockup_days": _max_decimal(
            tuple(row.capital_lockup_days for row in rows),
        ),
    }
    for field_name, expected in checks.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _require_rows(
    rows: tuple[StrategyExpectedValueConsistencyGateV2Row, ...],
) -> tuple[StrategyExpectedValueConsistencyGateV2Row, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyExpectedValueConsistencyGateV2Row:
            raise ValueError("rows must contain StrategyExpectedValueConsistencyGateV2Row")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_sort_key)):
        raise ValueError("rows must be sorted by status, net expected value, and candidate_id")
    return normalized


def _require_reason_code_counts(
    rows: tuple[StrategyExpectedValueConsistencyGateV2ReasonCodeCount, ...],
) -> tuple[StrategyExpectedValueConsistencyGateV2ReasonCodeCount, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in normalized:
        if type(row) is not StrategyExpectedValueConsistencyGateV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain StrategyExpectedValueConsistencyGateV2ReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", row)
    if normalized != tuple(
        sorted(normalized, key=lambda item: (-item.count, item.reason_code)),
    ):
        raise ValueError("reason_code_counts must be sorted by count and reason_code")
    if len({row.reason_code for row in normalized}) != len(normalized):
        raise ValueError("reason_code_counts reason_code values must be unique")
    return normalized


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical non-empty string")
    if any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must not contain whitespace")
    _reject_unsafe_public_text(field_name, value)


def _require_reason_codes(
    reason_codes: tuple[str, ...],
    *,
    require_nonempty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError("reason_codes must be an iterable")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable") from exc
    if require_nonempty and not normalized:
        raise ValueError("reason_codes must be non-empty")
    for reason_code in normalized:
        _require_public_string("reason_code", reason_code)
        if reason_code.lower() != reason_code:
            raise ValueError("reason_code must be lowercase")
    if len(set(normalized)) != len(normalized):
        raise ValueError("reason_codes must be unique")
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (
                1 if reason_code.startswith("evc_") else 0,
                (
                    ROW_REASON_PRIORITY.index(reason_code)
                    if reason_code in ROW_REASON_PRIORITY
                    else len(ROW_REASON_PRIORITY)
                ),
                reason_code,
            ),
        ),
    )


def _require_report_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = _require_reason_codes(reason_codes, require_nonempty=True)
    return tuple(
        sorted(
            normalized,
            key=lambda reason_code: (
                0 if reason_code.startswith("ev_consistency_gate_") else 1,
                (
                    REPORT_REASON_PRIORITY.index(reason_code)
                    if reason_code in REPORT_REASON_PRIORITY
                    else len(REPORT_REASON_PRIORITY)
                ),
                reason_code,
            ),
        ),
    )


def _require_status(field_name: str, value: object) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be one of {STATUSES}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_signed_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < Decimal("-1.000000") or normalized > ONE:
        raise ValueError(f"{field_name} must be between -1 and 1")
    return normalized


def _require_count_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be non-negative")
    return normalized


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _count(value: int | Decimal) -> Decimal:
    if type(value) is Decimal:
        return _require_count_decimal("count", value)
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _min_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _derived_validation_digest(
    report: StrategyExpectedValueConsistencyGateV2Report,
) -> str:
    payload = _json_ready(report)
    if not isinstance(payload, dict):
        raise ValueError("report payload must be an object")
    return _payload_validation_digest(payload)


def _payload_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        digest_payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_sha256(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in HEX_CHARS for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is bool:
        return value
    if type(value) is str:
        _reject_unsafe_public_text("payload", value)
        return value
    if type(value) in (int, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_text("payload key", key)
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numeric_values(value: object) -> None:
    if type(value) in (Decimal, int, float):
        raise ValueError("public numeric payload values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_text(f"{label} key", key)
            if key in PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _reject_unsafe_public_text(label, value)


def _reject_unsafe_public_text(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public surface in {label}")
