"""Report-only fee-liquidity break-even edge threshold snapshot."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
import hashlib
import json
import re
from typing import Any, Mapping, Sequence


DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_BREAK_EVEN_CONFIG_VERSION = (
    "research-market-fee-liquidity-break-even-report"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_TWO = Decimal("2.000000")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_EDGE_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_TERMS = tuple(
    "".join(parts)
    for parts in (
        ("candi", "date", "_", "id"),
        ("candi", "date"),
        ("mar", "ket", "_", "id"),
        ("mar", "ket", "_", "sl", "ug"),
        ("sl", "ug"),
        ("ques", "tion"),
        ("u", "rl"),
        ("te", "xt"),
        ("d", "sn"),
        ("ta", "ble"),
        ("to", "ken"),
        ("wal", "let"),
        ("or", "der"),
        ("tr", "ade"),
        ("li", "ve"),
        ("exe", "cute"),
        ("reco", "mmend"),
        ("si", "zing"),
    )
)
_REASON_CODE_SEQUENCE = (
    "empty_observations",
    "fee_component",
    "spread_component",
    "depth_shortfall_component",
    "slippage_component",
    "settlement_component",
    "break_even_pass",
    "break_even_watch",
    "break_even_block",
)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityBreakEvenConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_BREAK_EVEN_CONFIG_VERSION
    depth_shortfall_penalty_rate: Decimal = Decimal("0.020000")
    pass_threshold: Decimal = Decimal("0.020000")
    block_threshold: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityBreakEvenConfig:
            raise TypeError(
                "ResearchMarketFeeLiquidityBreakEvenConfig does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityBreakEvenConfig:
            raise ValueError(
                "config must be exactly ResearchMarketFeeLiquidityBreakEvenConfig",
            )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_BREAK_EVEN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "depth_shortfall_penalty_rate",
            "pass_threshold",
            "block_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_threshold <= self.pass_threshold:
            raise ValueError("block_threshold must exceed pass_threshold")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityBreakEvenObservation:
    taker_fee_rate: Decimal
    quoted_spread: Decimal
    depth_score: Decimal
    slippage_buffer: Decimal
    settlement_friction: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityBreakEvenObservation:
            raise TypeError(
                "ResearchMarketFeeLiquidityBreakEvenObservation does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityBreakEvenObservation:
            raise ValueError(
                "observation must be exactly "
                "ResearchMarketFeeLiquidityBreakEvenObservation",
            )
        for field_name in (
            "taker_fee_rate",
            "quoted_spread",
            "depth_score",
            "slippage_buffer",
            "settlement_friction",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityBreakEvenRow:
    taker_fee_cost: Decimal
    spread_cost: Decimal
    depth_cost: Decimal
    slippage_buffer_cost: Decimal
    settlement_friction_cost: Decimal
    break_even_edge_threshold: Decimal
    edge_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityBreakEvenRow:
            raise TypeError(
                "ResearchMarketFeeLiquidityBreakEvenRow does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityBreakEvenRow:
            raise ValueError(
                "row must be exactly ResearchMarketFeeLiquidityBreakEvenRow",
            )
        for field_name in (
            "taker_fee_cost",
            "spread_cost",
            "depth_cost",
            "slippage_buffer_cost",
            "settlement_friction_cost",
            "break_even_edge_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_edge_status("edge_status", self.edge_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketFeeLiquidityBreakEvenReport:
    generated_at: datetime
    config_version: str
    edge_status: str
    sample_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_break_even_edge_threshold: Decimal
    max_break_even_edge_threshold: Decimal
    rows: tuple[ResearchMarketFeeLiquidityBreakEvenRow, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeLiquidityBreakEvenReport:
            raise TypeError(
                "ResearchMarketFeeLiquidityBreakEvenReport does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketFeeLiquidityBreakEvenReport:
            raise ValueError(
                "report must be exactly ResearchMarketFeeLiquidityBreakEvenReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_BREAK_EVEN_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_edge_status("edge_status", self.edge_status)
        for field_name in ("sample_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_break_even_edge_threshold",
            "max_break_even_edge_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def payload(self) -> dict[str, object]:
        payload = _json_ready(asdict(self))
        _reject_unsafe_public_payload(
            "ResearchMarketFeeLiquidityBreakEvenReport.payload",
            payload,
            allow_json_containers=True,
        )
        if type(payload) is not dict:
            raise ValueError("payload must be a dict")
        return payload


def build_research_market_fee_liquidity_break_even_report(
    observations: Sequence[ResearchMarketFeeLiquidityBreakEvenObservation],
    *,
    generated_at: datetime,
    config: ResearchMarketFeeLiquidityBreakEvenConfig | None = None,
) -> ResearchMarketFeeLiquidityBreakEvenReport:
    """Build a local report-only break-even edge threshold snapshot."""

    if config is None:
        config = ResearchMarketFeeLiquidityBreakEvenConfig()
    if type(config) is not ResearchMarketFeeLiquidityBreakEvenConfig:
        raise ValueError("config must be a ResearchMarketFeeLiquidityBreakEvenConfig")
    generated_at = _as_utc("generated_at", generated_at)
    normalized_observations = _normalize_observations(observations)
    rows = tuple(
        _row_for_observation(observation, config)
        for observation in normalized_observations
    )
    reason_codes = _report_reason_codes(rows)
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "edge_status": _report_status(rows),
        "sample_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_break_even_edge_threshold": _average(
            tuple(row.break_even_edge_threshold for row in rows),
        ),
        "max_break_even_edge_threshold": max(
            (row.break_even_edge_threshold for row in rows),
            default=_ZERO,
        ),
        "rows": rows,
        "reason_codes": reason_codes,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketFeeLiquidityBreakEvenReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def _row_for_observation(
    observation: ResearchMarketFeeLiquidityBreakEvenObservation,
    config: ResearchMarketFeeLiquidityBreakEvenConfig,
) -> ResearchMarketFeeLiquidityBreakEvenRow:
    taker_fee_cost = observation.taker_fee_rate
    spread_cost = _quantize(observation.quoted_spread / _TWO)
    depth_cost = _quantize(
        (_ONE - observation.depth_score) * config.depth_shortfall_penalty_rate,
    )
    slippage_buffer_cost = observation.slippage_buffer
    settlement_friction_cost = observation.settlement_friction
    break_even_edge_threshold = _quantize(
        taker_fee_cost
        + spread_cost
        + depth_cost
        + slippage_buffer_cost
        + settlement_friction_cost,
    )
    edge_status = _row_status(
        break_even_edge_threshold=break_even_edge_threshold,
        config=config,
    )
    return ResearchMarketFeeLiquidityBreakEvenRow(
        taker_fee_cost=taker_fee_cost,
        spread_cost=spread_cost,
        depth_cost=depth_cost,
        slippage_buffer_cost=slippage_buffer_cost,
        settlement_friction_cost=settlement_friction_cost,
        break_even_edge_threshold=break_even_edge_threshold,
        edge_status=edge_status,
        reason_codes=_row_reason_codes(
            taker_fee_cost=taker_fee_cost,
            spread_cost=spread_cost,
            depth_cost=depth_cost,
            slippage_buffer_cost=slippage_buffer_cost,
            settlement_friction_cost=settlement_friction_cost,
            edge_status=edge_status,
        ),
    )


def _row_status(
    *,
    break_even_edge_threshold: Decimal,
    config: ResearchMarketFeeLiquidityBreakEvenConfig,
) -> str:
    if break_even_edge_threshold >= config.block_threshold:
        return "block"
    if break_even_edge_threshold <= config.pass_threshold:
        return "pass"
    return "watch"


def _row_reason_codes(
    *,
    taker_fee_cost: Decimal,
    spread_cost: Decimal,
    depth_cost: Decimal,
    slippage_buffer_cost: Decimal,
    settlement_friction_cost: Decimal,
    edge_status: str,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if taker_fee_cost > _ZERO:
        reason_codes.append("fee_component")
    if spread_cost > _ZERO:
        reason_codes.append("spread_component")
    if depth_cost > _ZERO:
        reason_codes.append("depth_shortfall_component")
    if slippage_buffer_cost > _ZERO:
        reason_codes.append("slippage_component")
    if settlement_friction_cost > _ZERO:
        reason_codes.append("settlement_component")
    reason_codes.append(f"break_even_{edge_status}")
    return _normalize_reason_codes(tuple(reason_codes))


def _report_status(rows: tuple[ResearchMarketFeeLiquidityBreakEvenRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.edge_status == "block" for row in rows):
        return "block"
    if any(row.edge_status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeLiquidityBreakEvenRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("empty_observations",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reason_codes))


def _status_count(
    rows: tuple[ResearchMarketFeeLiquidityBreakEvenRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.edge_status == status)


def _validate_row_consistency(row: ResearchMarketFeeLiquidityBreakEvenRow) -> None:
    expected_threshold = _quantize(
        row.taker_fee_cost
        + row.spread_cost
        + row.depth_cost
        + row.slippage_buffer_cost
        + row.settlement_friction_cost,
    )
    if row.break_even_edge_threshold != expected_threshold:
        raise ValueError("break_even_edge_threshold must match cost components")
    expected_status_code = f"break_even_{row.edge_status}"
    if expected_status_code not in row.reason_codes:
        raise ValueError("reason_codes must include edge status")


def _validate_report_consistency(report: ResearchMarketFeeLiquidityBreakEvenReport) -> None:
    if report.sample_count != _decimal_count(len(report.rows)):
        raise ValueError("sample_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.average_break_even_edge_threshold != _average(
        tuple(row.break_even_edge_threshold for row in report.rows),
    ):
        raise ValueError("average_break_even_edge_threshold must match rows")
    expected_max_threshold = max(
        (row.break_even_edge_threshold for row in report.rows),
        default=_ZERO,
    )
    if report.max_break_even_edge_threshold != expected_max_threshold:
        raise ValueError("max_break_even_edge_threshold must match rows")
    if report.edge_status != _report_status(report.rows):
        raise ValueError("edge_status must match row statuses")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_observations(
    observations: Sequence[ResearchMarketFeeLiquidityBreakEvenObservation],
) -> tuple[ResearchMarketFeeLiquidityBreakEvenObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Sequence):
        raise ValueError("observations must be a sequence")
    normalized: list[ResearchMarketFeeLiquidityBreakEvenObservation] = []
    for item in observations:
        if type(item) is not ResearchMarketFeeLiquidityBreakEvenObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketFeeLiquidityBreakEvenObservation",
            )
        normalized.append(item)
    return tuple(
        sorted(
            normalized,
            key=lambda item: (
                item.taker_fee_rate,
                item.quoted_spread,
                item.depth_score,
                item.slippage_buffer,
                item.settlement_friction,
            ),
        ),
    )


def _normalize_rows(
    rows: Sequence[ResearchMarketFeeLiquidityBreakEvenRow],
) -> tuple[ResearchMarketFeeLiquidityBreakEvenRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketFeeLiquidityBreakEvenRow] = []
    for row in rows:
        if type(row) is not ResearchMarketFeeLiquidityBreakEvenRow:
            raise ValueError("rows must contain ResearchMarketFeeLiquidityBreakEvenRow")
        normalized.append(row)
    return tuple(
        sorted(
            normalized,
            key=lambda row: (
                row.break_even_edge_threshold,
                row.taker_fee_cost,
                row.spread_cost,
                row.depth_cost,
                row.slippage_buffer_cost,
                row.settlement_friction_cost,
            ),
        ),
    )


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_edge_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in _EDGE_STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not _DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    return _require_nonnegative_decimal(field_name, value)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < _ZERO or normalized > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(_QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT, rounding=ROUND_HALF_UP)


def _normalize_reason_codes(reason_codes: Sequence[str]) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in _REASON_CODE_SEQUENCE:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(
        reason_code
        for reason_code in _REASON_CODE_SEQUENCE
        if reason_code in normalized
    )


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _report_values_without_digest(
    report: ResearchMarketFeeLiquidityBreakEvenReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    payload = _json_ready(values)
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        payload,
        allow_json_containers=True,
    )
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal payload value must be finite")
        return str(value)
    if type(value) is datetime:
        return _as_utc("datetime payload value", value).isoformat()
    if type(value) is bool or type(value) is str:
        return value
    if type(value) is int or isinstance(value, float):
        raise ValueError("numeric payload values must be Decimal strings")
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    path: str = "",
    *,
    allow_json_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if type(value) is list and not allow_json_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(
                label,
                item,
                f"{current_path}[{index}]",
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_string(current_path, value)
        return
    if (
        value is None
        or type(value) is bool
        or type(value) is Decimal
        or type(value) is datetime
    ):
        return
    raise ValueError(f"{current_path} is not a supported public payload value")


def _reject_unsafe_public_key(key: str, path: str) -> None:
    lowered = key.lower()
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in _UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_FEE_LIQUIDITY_BREAK_EVEN_CONFIG_VERSION",
    "ResearchMarketFeeLiquidityBreakEvenConfig",
    "ResearchMarketFeeLiquidityBreakEvenObservation",
    "ResearchMarketFeeLiquidityBreakEvenReport",
    "ResearchMarketFeeLiquidityBreakEvenRow",
    "build_research_market_fee_liquidity_break_even_report",
)
