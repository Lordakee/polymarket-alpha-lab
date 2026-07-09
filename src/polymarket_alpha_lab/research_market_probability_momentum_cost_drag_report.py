"""Pure report-only probability momentum cost-drag reducer."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_MOMENTUM_COST_DRAG_CONFIG_VERSION",
    "MARKET_PROBABILITY_MOMENTUM_COST_DRAG_STATUSES",
    "MarketProbabilityMomentumCostDragConfig",
    "MarketProbabilityMomentumCostDragObservation",
    "MarketProbabilityMomentumCostDragReasonCodeCount",
    "MarketProbabilityMomentumCostDragReport",
    "MarketProbabilityMomentumCostDragRow",
    "build_research_market_probability_momentum_cost_drag_report",
    "research_market_probability_momentum_cost_drag_report_payload",
    "validate_research_market_probability_momentum_cost_drag_report_payload",
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_MOMENTUM_COST_DRAG_CONFIG_VERSION = (
    "research-market-probability-momentum-cost-drag-report-v1"
)
MARKET_PROBABILITY_MOMENTUM_COST_DRAG_STATUSES = ("pass", "watch", "block")
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64)

PASS_STATUS = "pass"
WATCH_STATUS = "watch"
BLOCK_STATUS = "block"
STATUSES = (PASS_STATUS, WATCH_STATUS, BLOCK_STATUS)
STATUS_RANK = {
    BLOCK_STATUS: Decimal("0"),
    WATCH_STATUS: Decimal("1"),
    PASS_STATUS: Decimal("2"),
}
MISSING_INPUTS_REASON = "probability_momentum_cost_drag_missing_inputs"


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_TERMS = (
    "://",
    "?",
    "@",
    "=",
    _join_parts("api", "_", "key"),
    _join_parts("au", "th"),
    _join_parts("candidate"),
    _join_parts("candidate", "_", "reference"),
    _join_parts("candidate", "_", "id"),
    _join_parts("connection"),
    _join_parts("database"),
    _join_parts("d", "sn"),
    _join_parts("exec", "ute"),
    _join_parts("exec", "ution"),
    _join_parts("li", "ve"),
    _join_parts("market", "_", "id"),
    _join_parts("market", "_", "reference"),
    _join_parts("market", "_", "slug"),
    _join_parts("network"),
    _join_parts("private", "_", "key"),
    _join_parts("ques", "tion"),
    _join_parts("raw"),
    _join_parts("reco", "mmend"),
    _join_parts("secret"),
    _join_parts("siz", "ing"),
    _join_parts("slug"),
    _join_parts("source"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("ta", "ble"),
    _join_parts("table", "_", "name"),
    _join_parts("text"),
    _join_parts("tok", "en"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("url"),
    _join_parts("wal", "let"),
)
HARD_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
REPORT_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "status",
        "input_count",
        "row_count",
        "block_count",
        "watch_count",
        "pass_count",
        "average_gross_momentum_abs",
        "average_total_cost_drag",
        "average_net_momentum_abs",
        "max_gross_momentum_abs",
        "max_total_cost_drag",
        "max_net_momentum_abs",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        *HARD_FLAG_FIELDS,
    ),
)
ROW_PAYLOAD_FIELDS = frozenset(
    (
        "signal_digest",
        "triage_rank",
        "observed_at",
        "prior_probability",
        "current_probability",
        "gross_momentum_abs",
        "momentum_direction",
        "fee_drag",
        "spread_drag",
        "slippage_buffer",
        "liquidity_depth_drag",
        "confidence_haircut",
        "total_cost_drag",
        "net_momentum_abs",
        "status",
        "reason_codes",
        *HARD_FLAG_FIELDS,
    ),
)
REASON_CODE_COUNT_PAYLOAD_FIELDS = frozenset(("reason_code", "count", *HARD_FLAG_FIELDS))
REPORT_DECIMAL_PAYLOAD_FIELDS = (
    "input_count",
    "row_count",
    "block_count",
    "watch_count",
    "pass_count",
    "average_gross_momentum_abs",
    "average_total_cost_drag",
    "average_net_momentum_abs",
    "max_gross_momentum_abs",
    "max_total_cost_drag",
    "max_net_momentum_abs",
)
ROW_DECIMAL_PAYLOAD_FIELDS = (
    "triage_rank",
    "prior_probability",
    "current_probability",
    "gross_momentum_abs",
    "fee_drag",
    "spread_drag",
    "slippage_buffer",
    "liquidity_depth_drag",
    "confidence_haircut",
    "total_cost_drag",
    "net_momentum_abs",
)
ROW_PROBABILITY_PAYLOAD_FIELDS = (
    "prior_probability",
    "current_probability",
    "gross_momentum_abs",
    "fee_drag",
    "spread_drag",
    "slippage_buffer",
    "liquidity_depth_drag",
    "confidence_haircut",
    "total_cost_drag",
    "net_momentum_abs",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} subclass is not allowed")


@dataclass(frozen=True)
class MarketProbabilityMomentumCostDragConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_MOMENTUM_COST_DRAG_CONFIG_VERSION
    )
    watch_net_momentum: Decimal = Decimal("0.020000")
    pass_net_momentum: Decimal = Decimal("0.060000")
    watch_total_cost_drag: Decimal = Decimal("0.030000")
    block_total_cost_drag: Decimal = Decimal("0.080000")
    watch_component_drag: Decimal = Decimal("0.015000")
    block_component_drag: Decimal = Decimal("0.040000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityMomentumCostDragConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        for field_name in (
            "watch_net_momentum",
            "pass_net_momentum",
            "watch_total_cost_drag",
            "block_total_cost_drag",
            "watch_component_drag",
            "block_component_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_net_momentum <= self.watch_net_momentum:
            raise ValueError("pass_net_momentum must exceed watch_net_momentum")
        if self.block_total_cost_drag <= self.watch_total_cost_drag:
            raise ValueError("block_total_cost_drag must exceed watch_total_cost_drag")
        if self.block_component_drag <= self.watch_component_drag:
            raise ValueError("block_component_drag must exceed watch_component_drag")
        _require_hard_flags(self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class MarketProbabilityMomentumCostDragObservation(_FinalDataclass):
    private_candidate_reference: str
    private_market_reference: str
    observed_at: datetime
    prior_probability: Decimal
    current_probability: Decimal
    fee_drag: Decimal
    spread_drag: Decimal
    slippage_buffer: Decimal
    liquidity_depth_drag: Decimal
    confidence_haircut: Decimal
    upstream_reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityMomentumCostDragObservation, "observation")
        for field_name in ("private_candidate_reference", "private_market_reference"):
            _require_private_reference(field_name, getattr(self, field_name))
        object.__setattr__(
            self,
            "observed_at",
            _as_utc("observed_at", self.observed_at),
        )
        for field_name in (
            "prior_probability",
            "current_probability",
            "fee_drag",
            "spread_drag",
            "slippage_buffer",
            "liquidity_depth_drag",
            "confidence_haircut",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "upstream_reason_codes",
            _normalize_reason_codes(self.upstream_reason_codes),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketProbabilityMomentumCostDragRow(_FinalDataclass):
    signal_digest: str
    triage_rank: Decimal
    observed_at: datetime
    prior_probability: Decimal
    current_probability: Decimal
    gross_momentum_abs: Decimal
    momentum_direction: str
    fee_drag: Decimal
    spread_drag: Decimal
    slippage_buffer: Decimal
    liquidity_depth_drag: Decimal
    confidence_haircut: Decimal
    total_cost_drag: Decimal
    net_momentum_abs: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityMomentumCostDragRow, "row")
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(
            self,
            "triage_rank",
            _normalize_positive_decimal("triage_rank", self.triage_rank),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_probability",
            "current_probability",
            "gross_momentum_abs",
            "fee_drag",
            "spread_drag",
            "slippage_buffer",
            "liquidity_depth_drag",
            "confidence_haircut",
            "total_cost_drag",
            "net_momentum_abs",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_momentum_direction(self.momentum_direction)
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class MarketProbabilityMomentumCostDragReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            MarketProbabilityMomentumCostDragReasonCodeCount,
            "reason_count",
        )
        _require_public_identifier("reason_code", self.reason_code)
        if _contains_unsafe_public_term(self.reason_code):
            raise ValueError("reason_code has unsafe public payload")
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_decimal("count", self.count),
        )
        _require_hard_flags(self)


@dataclass(frozen=True)
class MarketProbabilityMomentumCostDragReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    row_count: Decimal
    block_count: Decimal
    watch_count: Decimal
    pass_count: Decimal
    average_gross_momentum_abs: Decimal
    average_total_cost_drag: Decimal
    average_net_momentum_abs: Decimal
    max_gross_momentum_abs: Decimal
    max_total_cost_drag: Decimal
    max_net_momentum_abs: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[MarketProbabilityMomentumCostDragReasonCodeCount, ...]
    rows: tuple[MarketProbabilityMomentumCostDragRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, MarketProbabilityMomentumCostDragReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        _require_status("status", self.status)
        for field_name in (
            "input_count",
            "row_count",
            "block_count",
            "watch_count",
            "pass_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_gross_momentum_abs",
            "average_total_cost_drag",
            "average_net_momentum_abs",
            "max_gross_momentum_abs",
            "max_total_cost_drag",
            "max_net_momentum_abs",
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
        _validate_report_consistency(self)
        _require_hard_flags(self)
        _reject_unsafe_public_payload("report", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_derived_validation_digest(self):
                raise ValueError(
                    "derived_validation_digest does not match public payload",
                )


def build_research_market_probability_momentum_cost_drag_report(
    observations: Iterable[MarketProbabilityMomentumCostDragObservation],
    *,
    config: MarketProbabilityMomentumCostDragConfig,
    generated_at: datetime,
) -> MarketProbabilityMomentumCostDragReport:
    if type(config) is not MarketProbabilityMomentumCostDragConfig:
        raise ValueError("config must be a MarketProbabilityMomentumCostDragConfig")
    generated_at = _as_utc("generated_at", generated_at)
    _require_hard_flags(config)
    normalized = _normalize_observations(observations)
    unranked_rows = tuple(
        _row_from_observation(value, config=config, generated_at=generated_at)
        for value in normalized
    )
    rows = _rank_rows(unranked_rows)
    return MarketProbabilityMomentumCostDragReport(
        generated_at=generated_at,
        config_version=config.config_version,
        status=_report_status(rows),
        input_count=_count_decimal(len(normalized)),
        row_count=_count_decimal(len(rows)),
        block_count=_status_count(rows, BLOCK_STATUS),
        watch_count=_status_count(rows, WATCH_STATUS),
        pass_count=_status_count(rows, PASS_STATUS),
        average_gross_momentum_abs=_average_row_decimal(rows, "gross_momentum_abs"),
        average_total_cost_drag=_average_row_decimal(rows, "total_cost_drag"),
        average_net_momentum_abs=_average_row_decimal(rows, "net_momentum_abs"),
        max_gross_momentum_abs=_max_row_decimal(rows, "gross_momentum_abs"),
        max_total_cost_drag=_max_row_decimal(rows, "total_cost_drag"),
        max_net_momentum_abs=_max_row_decimal(rows, "net_momentum_abs"),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_probability_momentum_cost_drag_report_payload(
    report: MarketProbabilityMomentumCostDragReport,
) -> dict[str, Any]:
    if type(report) is not MarketProbabilityMomentumCostDragReport:
        raise ValueError("report must be a MarketProbabilityMomentumCostDragReport")
    _require_hard_flags(report)
    _reject_unsafe_public_payload("report", report)
    payload = _json_value(report)
    if type(payload) is not dict:
        raise ValueError("report must serialize to a JSON object")
    validate_research_market_probability_momentum_cost_drag_report_payload(payload)
    return payload


def validate_research_market_probability_momentum_cost_drag_report_payload(
    payload: dict[str, Any],
) -> dict[str, Any]:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_non_json_payload_values("payload", payload)
    _require_payload_hard_flags(payload)
    _reject_unsafe_public_payload("payload", payload)
    provided_digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", provided_digest)
    if provided_digest != _payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest does not match public payload")
    _validate_report_payload_schema(payload)
    return payload


def _validate_report_payload_schema(payload: dict[str, Any]) -> None:
    _require_exact_payload_fields("payload", payload, REPORT_PAYLOAD_FIELDS)
    normalized = MarketProbabilityMomentumCostDragReport(
        generated_at=_payload_datetime("generated_at", payload["generated_at"]),
        config_version=_payload_public_identifier(
            "config_version",
            payload["config_version"],
        ),
        status=_payload_status("status", payload["status"]),
        input_count=_payload_count_decimal("input_count", payload["input_count"]),
        row_count=_payload_count_decimal("row_count", payload["row_count"]),
        block_count=_payload_count_decimal("block_count", payload["block_count"]),
        watch_count=_payload_count_decimal("watch_count", payload["watch_count"]),
        pass_count=_payload_count_decimal("pass_count", payload["pass_count"]),
        average_gross_momentum_abs=_payload_probability_decimal(
            "average_gross_momentum_abs",
            payload["average_gross_momentum_abs"],
        ),
        average_total_cost_drag=_payload_probability_decimal(
            "average_total_cost_drag",
            payload["average_total_cost_drag"],
        ),
        average_net_momentum_abs=_payload_probability_decimal(
            "average_net_momentum_abs",
            payload["average_net_momentum_abs"],
        ),
        max_gross_momentum_abs=_payload_probability_decimal(
            "max_gross_momentum_abs",
            payload["max_gross_momentum_abs"],
        ),
        max_total_cost_drag=_payload_probability_decimal(
            "max_total_cost_drag",
            payload["max_total_cost_drag"],
        ),
        max_net_momentum_abs=_payload_probability_decimal(
            "max_net_momentum_abs",
            payload["max_net_momentum_abs"],
        ),
        reason_codes=_payload_reason_codes(
            "reason_codes",
            payload["reason_codes"],
        ),
        reason_code_counts=tuple(
            _payload_reason_code_count(
                f"reason_code_counts[{index}]",
                value,
            )
            for index, value in enumerate(
                _payload_list("reason_code_counts", payload["reason_code_counts"]),
            )
        ),
        rows=tuple(
            _payload_row(f"rows[{index}]", value)
            for index, value in enumerate(_payload_list("rows", payload["rows"]))
        ),
        paper_only=_payload_hard_flag("paper_only", payload["paper_only"]),
        report_only=_payload_hard_flag("report_only", payload["report_only"]),
        readonly=_payload_hard_flag("readonly", payload["readonly"]),
    )
    expected = _json_value(normalized)
    expected.pop("derived_validation_digest", None)
    observed = dict(payload)
    observed.pop("derived_validation_digest", None)
    if observed != expected:
        raise ValueError("payload must use deterministic public schema")


def _payload_reason_code_count(
    label: str,
    value: object,
) -> MarketProbabilityMomentumCostDragReasonCodeCount:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    _require_exact_payload_fields(label, value, REASON_CODE_COUNT_PAYLOAD_FIELDS)
    return MarketProbabilityMomentumCostDragReasonCodeCount(
        reason_code=_payload_public_identifier("reason_code", value["reason_code"]),
        count=_payload_count_decimal("count", value["count"]),
        paper_only=_payload_hard_flag("paper_only", value["paper_only"]),
        report_only=_payload_hard_flag("report_only", value["report_only"]),
        readonly=_payload_hard_flag("readonly", value["readonly"]),
    )


def _payload_row(label: str, value: object) -> MarketProbabilityMomentumCostDragRow:
    if type(value) is not dict:
        raise ValueError(f"{label} must be a dict")
    _require_exact_payload_fields(label, value, ROW_PAYLOAD_FIELDS)
    return MarketProbabilityMomentumCostDragRow(
        signal_digest=_payload_digest("signal_digest", value["signal_digest"]),
        triage_rank=_payload_positive_decimal("triage_rank", value["triage_rank"]),
        observed_at=_payload_datetime("observed_at", value["observed_at"]),
        prior_probability=_payload_probability_decimal(
            "prior_probability",
            value["prior_probability"],
        ),
        current_probability=_payload_probability_decimal(
            "current_probability",
            value["current_probability"],
        ),
        gross_momentum_abs=_payload_probability_decimal(
            "gross_momentum_abs",
            value["gross_momentum_abs"],
        ),
        momentum_direction=_payload_momentum_direction(
            "momentum_direction",
            value["momentum_direction"],
        ),
        fee_drag=_payload_probability_decimal("fee_drag", value["fee_drag"]),
        spread_drag=_payload_probability_decimal("spread_drag", value["spread_drag"]),
        slippage_buffer=_payload_probability_decimal(
            "slippage_buffer",
            value["slippage_buffer"],
        ),
        liquidity_depth_drag=_payload_probability_decimal(
            "liquidity_depth_drag",
            value["liquidity_depth_drag"],
        ),
        confidence_haircut=_payload_probability_decimal(
            "confidence_haircut",
            value["confidence_haircut"],
        ),
        total_cost_drag=_payload_probability_decimal(
            "total_cost_drag",
            value["total_cost_drag"],
        ),
        net_momentum_abs=_payload_probability_decimal(
            "net_momentum_abs",
            value["net_momentum_abs"],
        ),
        status=_payload_status("status", value["status"]),
        reason_codes=_payload_reason_codes("reason_codes", value["reason_codes"]),
        paper_only=_payload_hard_flag("paper_only", value["paper_only"]),
        report_only=_payload_hard_flag("report_only", value["report_only"]),
        readonly=_payload_hard_flag("readonly", value["readonly"]),
    )


def _payload_list(field_name: str, value: object) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return value


def _payload_datetime(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 datetime string") from exc
    return _as_utc(field_name, parsed)


def _payload_public_identifier(field_name: str, value: object) -> str:
    _require_public_identifier(field_name, value)
    return value


def _payload_digest(field_name: str, value: object) -> str:
    _require_sha256_digest(field_name, value)
    return value


def _payload_status(field_name: str, value: object) -> str:
    _require_status(field_name, value)
    return value


def _payload_momentum_direction(field_name: str, value: object) -> str:
    _require_momentum_direction(value)
    return value


def _payload_hard_flag(field_name: str, value: object) -> bool:
    if value is not True:
        raise ValueError(f"{field_name} must be True")
    return True


def _payload_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    reason_codes = tuple(value)
    normalized = _normalize_reason_codes(reason_codes)
    if reason_codes != normalized:
        raise ValueError(f"{field_name} must use deterministic sequence")
    return normalized


def _payload_count_decimal(field_name: str, value: object) -> Decimal:
    parsed = _payload_nonnegative_decimal(field_name, value)
    if parsed != parsed.to_integral_value():
        raise ValueError(f"{field_name} must be a whole-number decimal string")
    return parsed


def _payload_positive_decimal(field_name: str, value: object) -> Decimal:
    parsed = _payload_decimal(field_name, value)
    if parsed <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return parsed


def _payload_probability_decimal(field_name: str, value: object) -> Decimal:
    parsed = _payload_nonnegative_decimal(field_name, value)
    if parsed > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return parsed


def _payload_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    parsed = _payload_decimal(field_name, value)
    if parsed < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return parsed


def _payload_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a decimal string")
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize_decimal(parsed)
    if f"{normalized:.6f}" != value:
        raise ValueError(f"{field_name} must be a canonical decimal string")
    return normalized


def _require_exact_payload_fields(
    label: str,
    value: dict[str, Any],
    expected: frozenset[str],
) -> None:
    if frozenset(value) != expected:
        raise ValueError(f"{label} must use exact public payload fields")


def _reject_non_json_payload_values(label: str, value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError(f"{label} must not contain JSON numeric values")
    if type(value) in (str, bool) or value is None:
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} must contain only string keys")
            _reject_non_json_payload_values(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_non_json_payload_values(label, item)
        return
    raise ValueError(f"{label} has unsupported JSON value")


def _row_from_observation(
    value: MarketProbabilityMomentumCostDragObservation,
    *,
    config: MarketProbabilityMomentumCostDragConfig,
    generated_at: datetime,
) -> MarketProbabilityMomentumCostDragRow:
    if value.observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    gross_momentum_abs = _abs_decimal(value.current_probability - value.prior_probability)
    total_cost_drag = _total_cost_drag(
        value.fee_drag,
        value.spread_drag,
        value.slippage_buffer,
        value.liquidity_depth_drag,
        value.confidence_haircut,
    )
    net_momentum_abs = _net_momentum_abs(gross_momentum_abs, total_cost_drag)
    direction = _momentum_direction(value.prior_probability, value.current_probability)
    components = (
        value.fee_drag,
        value.spread_drag,
        value.slippage_buffer,
        value.liquidity_depth_drag,
        value.confidence_haircut,
    )
    status = _row_status(
        net_momentum_abs=net_momentum_abs,
        total_cost_drag=total_cost_drag,
        component_drags=components,
        config=config,
    )
    return MarketProbabilityMomentumCostDragRow(
        signal_digest=_signal_digest(
            value.private_candidate_reference,
            value.private_market_reference,
        ),
        triage_rank=ONE,
        observed_at=value.observed_at,
        prior_probability=value.prior_probability,
        current_probability=value.current_probability,
        gross_momentum_abs=gross_momentum_abs,
        momentum_direction=direction,
        fee_drag=value.fee_drag,
        spread_drag=value.spread_drag,
        slippage_buffer=value.slippage_buffer,
        liquidity_depth_drag=value.liquidity_depth_drag,
        confidence_haircut=value.confidence_haircut,
        total_cost_drag=total_cost_drag,
        net_momentum_abs=net_momentum_abs,
        status=status,
        reason_codes=_row_reason_codes(
            value.upstream_reason_codes,
            momentum_direction=direction,
            net_momentum_abs=net_momentum_abs,
            total_cost_drag=total_cost_drag,
            status=status,
            fee_drag=value.fee_drag,
            spread_drag=value.spread_drag,
            slippage_buffer=value.slippage_buffer,
            liquidity_depth_drag=value.liquidity_depth_drag,
            confidence_haircut=value.confidence_haircut,
            config=config,
        ),
    )


def _rank_rows(
    rows: tuple[MarketProbabilityMomentumCostDragRow, ...],
) -> tuple[MarketProbabilityMomentumCostDragRow, ...]:
    return tuple(
        MarketProbabilityMomentumCostDragRow(
            signal_digest=row.signal_digest,
            triage_rank=_count_decimal(index),
            observed_at=row.observed_at,
            prior_probability=row.prior_probability,
            current_probability=row.current_probability,
            gross_momentum_abs=row.gross_momentum_abs,
            momentum_direction=row.momentum_direction,
            fee_drag=row.fee_drag,
            spread_drag=row.spread_drag,
            slippage_buffer=row.slippage_buffer,
            liquidity_depth_drag=row.liquidity_depth_drag,
            confidence_haircut=row.confidence_haircut,
            total_cost_drag=row.total_cost_drag,
            net_momentum_abs=row.net_momentum_abs,
            status=row.status,
            reason_codes=row.reason_codes,
        )
        for index, row in enumerate(sorted(rows, key=_row_sort_key), start=1)
    )


def _row_status(
    *,
    net_momentum_abs: Decimal,
    total_cost_drag: Decimal,
    component_drags: tuple[Decimal, ...],
    config: MarketProbabilityMomentumCostDragConfig,
) -> str:
    if (
        net_momentum_abs < config.watch_net_momentum
        or total_cost_drag >= config.block_total_cost_drag
        or any(value >= config.block_component_drag for value in component_drags)
    ):
        return BLOCK_STATUS
    if (
        net_momentum_abs < config.pass_net_momentum
        or total_cost_drag >= config.watch_total_cost_drag
        or any(value >= config.watch_component_drag for value in component_drags)
    ):
        return WATCH_STATUS
    return PASS_STATUS


def _row_reason_codes(
    upstream_reason_codes: tuple[str, ...],
    *,
    momentum_direction: str,
    net_momentum_abs: Decimal,
    total_cost_drag: Decimal,
    status: str,
    fee_drag: Decimal,
    spread_drag: Decimal,
    slippage_buffer: Decimal,
    liquidity_depth_drag: Decimal,
    confidence_haircut: Decimal,
    config: MarketProbabilityMomentumCostDragConfig,
) -> tuple[str, ...]:
    reason_codes = list(upstream_reason_codes)
    reason_codes.append(f"probability_momentum_cost_drag_status_{status}")
    reason_codes.append(f"probability_momentum_cost_drag_direction_{momentum_direction}")
    if net_momentum_abs >= config.pass_net_momentum:
        reason_codes.append("probability_momentum_cost_drag_net_momentum_pass")
        reason_codes.append("probability_momentum_cost_drag_meaningful_after_drag")
    elif net_momentum_abs >= config.watch_net_momentum:
        reason_codes.append("probability_momentum_cost_drag_net_momentum_watch")
        reason_codes.append("probability_momentum_cost_drag_partly_meaningful_after_drag")
    else:
        reason_codes.append("probability_momentum_cost_drag_net_momentum_block")
        reason_codes.append("probability_momentum_cost_drag_costs_overwhelm_momentum")
    if total_cost_drag >= config.block_total_cost_drag:
        reason_codes.append("probability_momentum_cost_drag_total_drag_block")
    elif total_cost_drag >= config.watch_total_cost_drag:
        reason_codes.append("probability_momentum_cost_drag_total_drag_watch")
    for name, value in (
        ("fee_drag", fee_drag),
        ("spread_drag", spread_drag),
        ("slippage_buffer", slippage_buffer),
        ("liquidity_depth_drag", liquidity_depth_drag),
        ("confidence_haircut", confidence_haircut),
    ):
        if value >= config.block_component_drag:
            reason_codes.append(f"probability_momentum_cost_drag_{name}_block")
        elif value >= config.watch_component_drag:
            reason_codes.append(f"probability_momentum_cost_drag_{name}_watch")
    return _normalize_reason_codes(tuple(reason_codes))


def _normalize_observations(
    observations: Iterable[MarketProbabilityMomentumCostDragObservation],
) -> tuple[MarketProbabilityMomentumCostDragObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    normalized = tuple(observations)
    for value in normalized:
        if type(value) is not MarketProbabilityMomentumCostDragObservation:
            raise ValueError(
                "observations must contain MarketProbabilityMomentumCostDragObservation",
            )
        _require_hard_flags(value)
    return normalized


def _normalize_rows(
    rows: Iterable[MarketProbabilityMomentumCostDragRow],
) -> tuple[MarketProbabilityMomentumCostDragRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Iterable):
        raise ValueError("rows must be an iterable")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not MarketProbabilityMomentumCostDragRow:
            raise ValueError("rows must contain MarketProbabilityMomentumCostDragRow")
        _require_hard_flags(row)
    expected = tuple(sorted(normalized, key=_row_sort_key))
    if normalized != expected:
        raise ValueError("rows must use deterministic sequence")
    if tuple(row.triage_rank for row in normalized) != tuple(
        _count_decimal(index) for index in range(1, len(normalized) + 1)
    ):
        raise ValueError("rows must use sequential triage ranks")
    return normalized


def _normalize_reason_code_counts(
    counts: Iterable[MarketProbabilityMomentumCostDragReasonCodeCount],
) -> tuple[MarketProbabilityMomentumCostDragReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)) or not isinstance(counts, Iterable):
        raise ValueError("reason_code_counts must be an iterable")
    normalized = tuple(counts)
    seen: set[str] = set()
    for count in normalized:
        if type(count) is not MarketProbabilityMomentumCostDragReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "MarketProbabilityMomentumCostDragReasonCodeCount",
            )
        _require_hard_flags(count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must not repeat")
        seen.add(count.reason_code)
    expected = tuple(sorted(normalized, key=lambda item: (-item.count, item.reason_code)))
    if normalized != expected:
        raise ValueError("reason_code_counts must use deterministic sequence")
    return normalized


def _validate_row_consistency(row: MarketProbabilityMomentumCostDragRow) -> None:
    status_reason = f"probability_momentum_cost_drag_status_{row.status}"
    if status_reason not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    expected_gross = _abs_decimal(row.current_probability - row.prior_probability)
    if row.gross_momentum_abs != expected_gross:
        raise ValueError("gross_momentum_abs must match probabilities")
    expected_total = _total_cost_drag(
        row.fee_drag,
        row.spread_drag,
        row.slippage_buffer,
        row.liquidity_depth_drag,
        row.confidence_haircut,
    )
    if row.total_cost_drag != expected_total:
        raise ValueError("total_cost_drag must match components")
    if row.net_momentum_abs != _net_momentum_abs(
        row.gross_momentum_abs,
        row.total_cost_drag,
    ):
        raise ValueError("net_momentum_abs must match gross momentum and drag")
    if row.momentum_direction != _momentum_direction(
        row.prior_probability,
        row.current_probability,
    ):
        raise ValueError("momentum_direction must match probabilities")


def _validate_report_consistency(report: MarketProbabilityMomentumCostDragReport) -> None:
    if report.input_count != report.row_count:
        raise ValueError("input_count must match row_count")
    if report.row_count != _count_decimal(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.block_count + report.watch_count + report.pass_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.average_gross_momentum_abs != _average_row_decimal(
        report.rows,
        "gross_momentum_abs",
    ):
        raise ValueError("average_gross_momentum_abs must match rows")
    if report.average_total_cost_drag != _average_row_decimal(
        report.rows,
        "total_cost_drag",
    ):
        raise ValueError("average_total_cost_drag must match rows")
    if report.average_net_momentum_abs != _average_row_decimal(
        report.rows,
        "net_momentum_abs",
    ):
        raise ValueError("average_net_momentum_abs must match rows")
    if report.max_gross_momentum_abs != _max_row_decimal(
        report.rows,
        "gross_momentum_abs",
    ):
        raise ValueError("max_gross_momentum_abs must match rows")
    if report.max_total_cost_drag != _max_row_decimal(report.rows, "total_cost_drag"):
        raise ValueError("max_total_cost_drag must match rows")
    if report.max_net_momentum_abs != _max_row_decimal(report.rows, "net_momentum_abs"):
        raise ValueError("max_net_momentum_abs must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _report_status(rows: tuple[MarketProbabilityMomentumCostDragRow, ...]) -> str:
    if not rows:
        return BLOCK_STATUS
    if any(row.status == BLOCK_STATUS for row in rows):
        return BLOCK_STATUS
    if any(row.status == WATCH_STATUS for row in rows):
        return WATCH_STATUS
    return PASS_STATUS


def _report_reason_codes(
    rows: tuple[MarketProbabilityMomentumCostDragRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _reason_code_counts(
    rows: tuple[MarketProbabilityMomentumCostDragRow, ...],
) -> tuple[MarketProbabilityMomentumCostDragReasonCodeCount, ...]:
    if not rows:
        return (
            MarketProbabilityMomentumCostDragReasonCodeCount(
                reason_code=MISSING_INPUTS_REASON,
                count=ONE,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize_decimal(counts.get(reason_code, ZERO) + ONE)
    return tuple(
        sorted(
            (
                MarketProbabilityMomentumCostDragReasonCodeCount(
                    reason_code=reason_code,
                    count=count,
                )
                for reason_code, count in counts.items()
            ),
            key=lambda item: (-item.count, item.reason_code),
        ),
    )


def _row_sort_key(
    row: MarketProbabilityMomentumCostDragRow,
) -> tuple[Decimal, Decimal, Decimal, Decimal, str]:
    return (
        STATUS_RANK[row.status],
        row.net_momentum_abs,
        -row.total_cost_drag,
        -row.gross_momentum_abs,
        row.signal_digest,
    )


def _status_count(
    rows: tuple[MarketProbabilityMomentumCostDragRow, ...],
    status: str,
) -> Decimal:
    return _count_decimal(sum(1 for row in rows if row.status == status))


def _max_row_decimal(
    rows: tuple[MarketProbabilityMomentumCostDragRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    return max(getattr(row, field_name) for row in rows)


def _average_row_decimal(
    rows: tuple[MarketProbabilityMomentumCostDragRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return _quantize_decimal(ZERO)
    total = ZERO
    for row in rows:
        total = _quantize_decimal(total + getattr(row, field_name))
    with localcontext(DECIMAL_CONTEXT):
        return _quantize_decimal(total / Decimal(len(rows)))


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize_decimal(abs(value))


def _total_cost_drag(*values: Decimal) -> Decimal:
    total = ZERO
    for value in values:
        total = _quantize_decimal(total + value)
    if total > ONE:
        raise ValueError("total_cost_drag must be between 0 and 1")
    return total


def _net_momentum_abs(gross_momentum_abs: Decimal, total_cost_drag: Decimal) -> Decimal:
    return _quantize_decimal(max(gross_momentum_abs - total_cost_drag, ZERO))


def _momentum_direction(
    prior_probability: Decimal,
    current_probability: Decimal,
) -> str:
    if current_probability > prior_probability:
        return "up"
    if current_probability < prior_probability:
        return "down"
    return "flat"


def _signal_digest(private_candidate_reference: str, private_market_reference: str) -> str:
    value = f"{private_candidate_reference}\x1f{private_market_reference}"
    return sha256(value.encode("utf-8")).hexdigest()


def _count_decimal(value: int) -> Decimal:
    return _quantize_decimal(Decimal(value))


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _normalize_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize_decimal(value)


def _quantize_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be UTC-aware")
    return value.astimezone(UTC)


def _require_private_reference(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_public_identifier(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if len(value) > 128:
        raise ValueError(f"{field_name} must be at most 128 characters")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public identifier")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_momentum_direction(value: object) -> None:
    if type(value) is not str or value not in ("up", "down", "flat"):
        raise ValueError("momentum_direction must be up, down, or flat")


def _normalize_reason_codes(reason_codes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Iterable):
        raise ValueError("reason_codes must be an iterable")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if _contains_unsafe_public_term(reason_code):
            raise ValueError("reason_code has unsafe public payload")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized))


def _require_hard_flags(value: object) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_payload_hard_flags(value: dict[str, Any]) -> None:
    _require_payload_object_hard_flags(value)
    _require_nested_payload_hard_flags(value)


def _require_payload_object_hard_flags(value: dict[str, Any]) -> None:
    for field_name in HARD_FLAG_FIELDS:
        if value.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")


def _require_nested_payload_hard_flags(value: object) -> None:
    if isinstance(value, dict):
        if any(field_name in value for field_name in HARD_FLAG_FIELDS):
            _require_payload_object_hard_flags(value)
        for item in value.values():
            _require_nested_payload_hard_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_nested_payload_hard_flags(item)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    allowed = set("0123456789abcdef")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be a {expected_type.__name__}")


def _json_value(value: object) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_value(asdict(value))
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if type(value) is Decimal:
        return f"{value:.6f}"
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"unsupported public payload value: {type(value).__name__}")


def _report_derived_validation_digest(
    report: MarketProbabilityMomentumCostDragReport,
) -> str:
    value = asdict(report)
    value.pop("derived_validation_digest", None)
    return _canonical_payload_digest(_json_value(value))


def _payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    value = dict(payload)
    value.pop("derived_validation_digest", None)
    return _canonical_payload_digest(value)


def _canonical_payload_digest(payload: dict[str, Any]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        value = asdict(value)
    if isinstance(value, dict):
        for key, item in value.items():
            if _contains_unsafe_public_term(str(key)):
                raise ValueError(f"{label} has unsafe public payload")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str) and _contains_unsafe_public_term(value):
        raise ValueError(f"{label} has unsafe public payload")


def _contains_unsafe_public_term(value: str) -> bool:
    lowered = value.lower()
    return any(term in lowered for term in _UNSAFE_PUBLIC_TERMS)
