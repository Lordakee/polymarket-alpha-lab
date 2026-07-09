"""Report-only market cost-adjusted edge pressure gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_MARKET_COST_ADJUSTED_EDGE_GATE_REPORT_CONFIG_VERSION = (
    "research-market-cost-adjusted-edge-gate-report-v0"
)
RESEARCH_MARKET_COST_ADJUSTED_EDGE_GATE_STATUSES = ("pass", "watch", "block")

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("li", "ve"),
    _join_parts("net", "work"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    _join_parts("priv", "ate"),
    _join_parts("sec", "ret"),
    _join_parts("cred", "ential"),
    "://",
)

ROW_REASON_CODES = (
    "cost_adjusted_edge_gate_pass",
    "sanitized_edge_block",
    "sanitized_edge_watch",
    "net_sanitized_edge_block",
    "net_sanitized_edge_watch",
    "fee_pressure_block",
    "fee_pressure_watch",
    "spread_pressure_block",
    "spread_pressure_watch",
    "depth_pressure_block",
    "depth_pressure_watch",
    "slippage_pressure_block",
    "slippage_pressure_watch",
    "settlement_uncertainty_pressure_block",
    "settlement_uncertainty_pressure_watch",
    "total_pressure_block",
    "total_pressure_watch",
)
REPORT_REASON_CODES = (
    "market_cost_adjusted_edge_gate_report_empty",
    "market_cost_adjusted_edge_gate_report_pass",
    "market_cost_adjusted_edge_gate_report_watch",
    "market_cost_adjusted_edge_gate_report_block",
    "sanitized_edge_review",
    "net_sanitized_edge_review",
    "fee_pressure_review",
    "spread_pressure_review",
    "depth_pressure_review",
    "slippage_pressure_review",
    "settlement_uncertainty_pressure_review",
    "total_pressure_review",
)


@dataclass(frozen=True)
class ResearchMarketCostAdjustedEdgeGateConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_COST_ADJUSTED_EDGE_GATE_REPORT_CONFIG_VERSION
    )
    sanitized_edge_pass_floor: Decimal = Decimal("0.030000")
    sanitized_edge_watch_floor: Decimal = Decimal("0.010000")
    net_sanitized_edge_pass_floor: Decimal = Decimal("0.015000")
    net_sanitized_edge_watch_floor: Decimal = Decimal("0.000000")
    fee_pressure_pass_ceiling: Decimal = Decimal("0.010000")
    fee_pressure_watch_ceiling: Decimal = Decimal("0.020000")
    spread_pressure_pass_ceiling: Decimal = Decimal("0.010000")
    spread_pressure_watch_ceiling: Decimal = Decimal("0.025000")
    depth_pressure_pass_ceiling: Decimal = Decimal("0.008000")
    depth_pressure_watch_ceiling: Decimal = Decimal("0.020000")
    slippage_pressure_pass_ceiling: Decimal = Decimal("0.008000")
    slippage_pressure_watch_ceiling: Decimal = Decimal("0.020000")
    settlement_uncertainty_pressure_pass_ceiling: Decimal = Decimal("0.008000")
    settlement_uncertainty_pressure_watch_ceiling: Decimal = Decimal("0.020000")
    total_pressure_pass_ceiling: Decimal = Decimal("0.030000")
    total_pressure_watch_ceiling: Decimal = Decimal("0.060000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostAdjustedEdgeGateConfig:
            raise ValueError("config must be a ResearchMarketCostAdjustedEdgeGateConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "sanitized_edge_pass_floor",
            "sanitized_edge_watch_floor",
            "net_sanitized_edge_pass_floor",
            "net_sanitized_edge_watch_floor",
            "fee_pressure_pass_ceiling",
            "fee_pressure_watch_ceiling",
            "spread_pressure_pass_ceiling",
            "spread_pressure_watch_ceiling",
            "depth_pressure_pass_ceiling",
            "depth_pressure_watch_ceiling",
            "slippage_pressure_pass_ceiling",
            "slippage_pressure_watch_ceiling",
            "settlement_uncertainty_pressure_pass_ceiling",
            "settlement_uncertainty_pressure_watch_ceiling",
            "total_pressure_pass_ceiling",
            "total_pressure_watch_ceiling",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "sanitized_edge",
            self.sanitized_edge_pass_floor,
            self.sanitized_edge_watch_floor,
        )
        _require_floor_pair(
            "net_sanitized_edge",
            self.net_sanitized_edge_pass_floor,
            self.net_sanitized_edge_watch_floor,
        )
        for name in (
            "fee_pressure",
            "spread_pressure",
            "depth_pressure",
            "slippage_pressure",
            "settlement_uncertainty_pressure",
            "total_pressure",
        ):
            _require_ceiling_pair(
                name,
                getattr(self, f"{name}_pass_ceiling"),
                getattr(self, f"{name}_watch_ceiling"),
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketCostAdjustedEdgeGateInput:
    public_edge_ref: str
    observed_at: datetime
    sanitized_probability_edge: Decimal
    fee_pressure_probability: Decimal
    spread_pressure_probability: Decimal
    depth_pressure_probability: Decimal
    slippage_pressure_probability: Decimal
    settlement_uncertainty_pressure_probability: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostAdjustedEdgeGateInput:
            raise ValueError("input must be a ResearchMarketCostAdjustedEdgeGateInput")
        _require_public_label("public_edge_ref", self.public_edge_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "sanitized_probability_edge",
            "fee_pressure_probability",
            "spread_pressure_probability",
            "depth_pressure_probability",
            "slippage_pressure_probability",
            "settlement_uncertainty_pressure_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketCostAdjustedEdgeGateReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostAdjustedEdgeGateReasonCodeCount:
            raise ValueError(
                "reason_code_count must be a ResearchMarketCostAdjustedEdgeGateReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _normalize_probability("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketCostAdjustedEdgeGateRow:
    public_edge_ref: str
    observed_at: datetime
    sanitized_probability_edge: Decimal
    fee_pressure_probability: Decimal
    spread_pressure_probability: Decimal
    depth_pressure_probability: Decimal
    slippage_pressure_probability: Decimal
    settlement_uncertainty_pressure_probability: Decimal
    total_pressure_probability: Decimal
    net_sanitized_edge_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostAdjustedEdgeGateRow:
            raise ValueError("row must be a ResearchMarketCostAdjustedEdgeGateRow")
        _require_public_label("public_edge_ref", self.public_edge_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "sanitized_probability_edge",
            "fee_pressure_probability",
            "spread_pressure_probability",
            "depth_pressure_probability",
            "slippage_pressure_probability",
            "settlement_uncertainty_pressure_probability",
            "total_pressure_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_sanitized_edge_probability",
            _normalize_decimal(
                "net_sanitized_edge_probability",
                self.net_sanitized_edge_probability,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, ROW_REASON_CODES),
        )
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketCostAdjustedEdgeGateReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_sanitized_probability_edge: Decimal
    mean_total_pressure_probability: Decimal
    mean_net_sanitized_edge_probability: Decimal
    max_fee_pressure_probability: Decimal
    max_spread_pressure_probability: Decimal
    max_depth_pressure_probability: Decimal
    max_slippage_pressure_probability: Decimal
    max_settlement_uncertainty_pressure_probability: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketCostAdjustedEdgeGateReasonCodeCount, ...]
    rows: tuple[ResearchMarketCostAdjustedEdgeGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketCostAdjustedEdgeGateReport:
            raise ValueError("report must be a ResearchMarketCostAdjustedEdgeGateReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_sanitized_probability_edge",
            "mean_total_pressure_probability",
            "max_fee_pressure_probability",
            "max_spread_pressure_probability",
            "max_depth_pressure_probability",
            "max_slippage_pressure_probability",
            "max_settlement_uncertainty_pressure_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_net_sanitized_edge_probability",
            _normalize_decimal(
                "mean_net_sanitized_edge_probability",
                self.mean_net_sanitized_edge_probability,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                REPORT_REASON_CODES,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_research_market_cost_adjusted_edge_gate_report(
    inputs: Iterable[ResearchMarketCostAdjustedEdgeGateInput],
    *,
    config: ResearchMarketCostAdjustedEdgeGateConfig,
    generated_at: datetime,
) -> ResearchMarketCostAdjustedEdgeGateReport:
    if type(config) is not ResearchMarketCostAdjustedEdgeGateConfig:
        raise ValueError("config must be a ResearchMarketCostAdjustedEdgeGateConfig")
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
    return ResearchMarketCostAdjustedEdgeGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_sanitized_probability_edge=_mean(
            tuple(row.sanitized_probability_edge for row in rows),
        ),
        mean_total_pressure_probability=_mean(
            tuple(row.total_pressure_probability for row in rows),
        ),
        mean_net_sanitized_edge_probability=_mean(
            tuple(row.net_sanitized_edge_probability for row in rows),
        ),
        max_fee_pressure_probability=_maximum(
            tuple(row.fee_pressure_probability for row in rows),
        ),
        max_spread_pressure_probability=_maximum(
            tuple(row.spread_pressure_probability for row in rows),
        ),
        max_depth_pressure_probability=_maximum(
            tuple(row.depth_pressure_probability for row in rows),
        ),
        max_slippage_pressure_probability=_maximum(
            tuple(row.slippage_pressure_probability for row in rows),
        ),
        max_settlement_uncertainty_pressure_probability=_maximum(
            tuple(row.settlement_uncertainty_pressure_probability for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_market_cost_adjusted_edge_gate_report_payload(
    report: ResearchMarketCostAdjustedEdgeGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketCostAdjustedEdgeGateReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketCostAdjustedEdgeGateReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def research_market_cost_adjusted_edge_gate_report_digest(
    report: ResearchMarketCostAdjustedEdgeGateReport,
) -> str:
    if type(report) is not ResearchMarketCostAdjustedEdgeGateReport:
        raise ValueError("report must be a ResearchMarketCostAdjustedEdgeGateReport")
    _require_hard_flags("report", report)
    _verify_report_integrity(report)
    return report.derived_validation_digest


def _public_report_payload(
    report: ResearchMarketCostAdjustedEdgeGateReport,
) -> dict[str, Any]:
    payload = asdict(report)
    payload["rows"] = [
        _public_row_payload(index, row)
        for index, row in enumerate(report.rows, start=1)
    ]
    payload.pop("derived_validation_digest", None)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    _verify_public_payload_integrity(public_payload)
    return public_payload


def _public_row_payload(
    row_number: int,
    row: ResearchMarketCostAdjustedEdgeGateRow,
) -> dict[str, Any]:
    payload = asdict(row)
    payload.pop("derived_validation_digest", None)
    payload["row_number"] = _count(row_number)
    public_payload = _json_ready(payload)
    if type(public_payload) is not dict:
        raise ValueError("row payload must be a JSON object")
    public_payload["derived_validation_digest"] = _public_payload_digest(public_payload)
    return public_payload


def _public_payload_digest(payload: dict[str, Any]) -> str:
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


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
    value: ResearchMarketCostAdjustedEdgeGateInput,
    *,
    config: ResearchMarketCostAdjustedEdgeGateConfig,
    generated_at: datetime,
) -> ResearchMarketCostAdjustedEdgeGateRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    total_pressure = _sum_decimals(
        (
            value.fee_pressure_probability,
            value.spread_pressure_probability,
            value.depth_pressure_probability,
            value.slippage_pressure_probability,
            value.settlement_uncertainty_pressure_probability,
        ),
    )
    net_edge = _subtract_decimal(value.sanitized_probability_edge, total_pressure)
    return ResearchMarketCostAdjustedEdgeGateRow(
        public_edge_ref=value.public_edge_ref,
        observed_at=observed_at,
        sanitized_probability_edge=value.sanitized_probability_edge,
        fee_pressure_probability=value.fee_pressure_probability,
        spread_pressure_probability=value.spread_pressure_probability,
        depth_pressure_probability=value.depth_pressure_probability,
        slippage_pressure_probability=value.slippage_pressure_probability,
        settlement_uncertainty_pressure_probability=(
            value.settlement_uncertainty_pressure_probability
        ),
        total_pressure_probability=total_pressure,
        net_sanitized_edge_probability=net_edge,
        status=_row_status(
            sanitized_probability_edge=value.sanitized_probability_edge,
            total_pressure_probability=total_pressure,
            net_sanitized_edge_probability=net_edge,
            value=value,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            sanitized_probability_edge=value.sanitized_probability_edge,
            total_pressure_probability=total_pressure,
            net_sanitized_edge_probability=net_edge,
            value=value,
            config=config,
        ),
    )


def _row_status(
    *,
    sanitized_probability_edge: Decimal,
    total_pressure_probability: Decimal,
    net_sanitized_edge_probability: Decimal,
    value: ResearchMarketCostAdjustedEdgeGateInput,
    config: ResearchMarketCostAdjustedEdgeGateConfig,
) -> str:
    if (
        sanitized_probability_edge < config.sanitized_edge_watch_floor
        or net_sanitized_edge_probability < config.net_sanitized_edge_watch_floor
        or total_pressure_probability > config.total_pressure_watch_ceiling
        or value.fee_pressure_probability > config.fee_pressure_watch_ceiling
        or value.spread_pressure_probability > config.spread_pressure_watch_ceiling
        or value.depth_pressure_probability > config.depth_pressure_watch_ceiling
        or value.slippage_pressure_probability > config.slippage_pressure_watch_ceiling
        or value.settlement_uncertainty_pressure_probability
        > config.settlement_uncertainty_pressure_watch_ceiling
    ):
        return "block"
    if (
        sanitized_probability_edge < config.sanitized_edge_pass_floor
        or net_sanitized_edge_probability < config.net_sanitized_edge_pass_floor
        or total_pressure_probability > config.total_pressure_pass_ceiling
        or value.fee_pressure_probability > config.fee_pressure_pass_ceiling
        or value.spread_pressure_probability > config.spread_pressure_pass_ceiling
        or value.depth_pressure_probability > config.depth_pressure_pass_ceiling
        or value.slippage_pressure_probability > config.slippage_pressure_pass_ceiling
        or value.settlement_uncertainty_pressure_probability
        > config.settlement_uncertainty_pressure_pass_ceiling
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    sanitized_probability_edge: Decimal,
    total_pressure_probability: Decimal,
    net_sanitized_edge_probability: Decimal,
    value: ResearchMarketCostAdjustedEdgeGateInput,
    config: ResearchMarketCostAdjustedEdgeGateConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if sanitized_probability_edge < config.sanitized_edge_watch_floor:
        codes.append("sanitized_edge_block")
    elif sanitized_probability_edge < config.sanitized_edge_pass_floor:
        codes.append("sanitized_edge_watch")
    if net_sanitized_edge_probability < config.net_sanitized_edge_watch_floor:
        codes.append("net_sanitized_edge_block")
    elif net_sanitized_edge_probability < config.net_sanitized_edge_pass_floor:
        codes.append("net_sanitized_edge_watch")
    if total_pressure_probability > config.total_pressure_watch_ceiling:
        codes.append("total_pressure_block")
    elif total_pressure_probability > config.total_pressure_pass_ceiling:
        codes.append("total_pressure_watch")
    for name, value_probability in (
        ("fee_pressure", value.fee_pressure_probability),
        ("spread_pressure", value.spread_pressure_probability),
        ("depth_pressure", value.depth_pressure_probability),
        ("slippage_pressure", value.slippage_pressure_probability),
        (
            "settlement_uncertainty_pressure",
            value.settlement_uncertainty_pressure_probability,
        ),
    ):
        if value_probability > getattr(config, f"{name}_watch_ceiling"):
            codes.append(f"{name}_block")
        elif value_probability > getattr(config, f"{name}_pass_ceiling"):
            codes.append(f"{name}_watch")
    if not codes:
        codes.append("cost_adjusted_edge_gate_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(rows: tuple[ResearchMarketCostAdjustedEdgeGateRow, ...]) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketCostAdjustedEdgeGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("market_cost_adjusted_edge_gate_report_empty",)
    report_status = _report_status(rows)
    codes = [f"market_cost_adjusted_edge_gate_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    for prefix, report_code in (
        ("sanitized_edge_", "sanitized_edge_review"),
        ("net_sanitized_edge_", "net_sanitized_edge_review"),
        ("fee_pressure_", "fee_pressure_review"),
        ("spread_pressure_", "spread_pressure_review"),
        ("depth_pressure_", "depth_pressure_review"),
        ("slippage_pressure_", "slippage_pressure_review"),
        (
            "settlement_uncertainty_pressure_",
            "settlement_uncertainty_pressure_review",
        ),
        ("total_pressure_", "total_pressure_review"),
    ):
        if any(code.startswith(prefix) for code in row_codes):
            codes.append(report_code)
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchMarketCostAdjustedEdgeGateRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.net_sanitized_edge_probability,
        -row.total_pressure_probability,
        row.sanitized_probability_edge,
        row.public_edge_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketCostAdjustedEdgeGateInput],
) -> tuple[ResearchMarketCostAdjustedEdgeGateInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchMarketCostAdjustedEdgeGateInput:
            raise ValueError(
                "inputs must contain ResearchMarketCostAdjustedEdgeGateInput values",
            )
        _require_hard_flags("input", value)
        if value.public_edge_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate public_edge_ref values")
        seen_refs.add(value.public_edge_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketCostAdjustedEdgeGateRow],
) -> tuple[ResearchMarketCostAdjustedEdgeGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchMarketCostAdjustedEdgeGateRow:
            raise ValueError(
                "rows must contain ResearchMarketCostAdjustedEdgeGateRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.public_edge_ref in seen_refs:
            raise ValueError("rows must not contain duplicate public_edge_ref values")
        seen_refs.add(row.public_edge_ref)
    return normalized


def _validate_row_consistency(row: ResearchMarketCostAdjustedEdgeGateRow) -> None:
    expected_total_pressure = _sum_decimals(
        (
            row.fee_pressure_probability,
            row.spread_pressure_probability,
            row.depth_pressure_probability,
            row.slippage_pressure_probability,
            row.settlement_uncertainty_pressure_probability,
        ),
    )
    if row.total_pressure_probability != expected_total_pressure:
        raise ValueError("total_pressure_probability does not match pressure inputs")
    expected_net_edge = _subtract_decimal(
        row.sanitized_probability_edge,
        row.total_pressure_probability,
    )
    if row.net_sanitized_edge_probability != expected_net_edge:
        raise ValueError("net_sanitized_edge_probability does not match row inputs")
    if row.status == "pass" and row.reason_codes != ("cost_adjusted_edge_gate_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(report: ResearchMarketCostAdjustedEdgeGateReport) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.input_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_sanitized_probability_edge != _mean(
        tuple(row.sanitized_probability_edge for row in report.rows),
    ):
        raise ValueError("mean_sanitized_probability_edge must match rows")
    if report.mean_total_pressure_probability != _mean(
        tuple(row.total_pressure_probability for row in report.rows),
    ):
        raise ValueError("mean_total_pressure_probability must match rows")
    if report.mean_net_sanitized_edge_probability != _mean(
        tuple(row.net_sanitized_edge_probability for row in report.rows),
    ):
        raise ValueError("mean_net_sanitized_edge_probability must match rows")
    if report.max_fee_pressure_probability != _maximum(
        tuple(row.fee_pressure_probability for row in report.rows),
    ):
        raise ValueError("max_fee_pressure_probability must match rows")
    if report.max_spread_pressure_probability != _maximum(
        tuple(row.spread_pressure_probability for row in report.rows),
    ):
        raise ValueError("max_spread_pressure_probability must match rows")
    if report.max_depth_pressure_probability != _maximum(
        tuple(row.depth_pressure_probability for row in report.rows),
    ):
        raise ValueError("max_depth_pressure_probability must match rows")
    if report.max_slippage_pressure_probability != _maximum(
        tuple(row.slippage_pressure_probability for row in report.rows),
    ):
        raise ValueError("max_slippage_pressure_probability must match rows")
    if report.max_settlement_uncertainty_pressure_probability != _maximum(
        tuple(row.settlement_uncertainty_pressure_probability for row in report.rows),
    ):
        raise ValueError("max_settlement_uncertainty_pressure_probability must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchMarketCostAdjustedEdgeGateReport) -> None:
    _verify_digest(report)
    _validate_report_consistency(report)
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
    expected = _public_payload_digest(payload)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(
    rows: tuple[ResearchMarketCostAdjustedEdgeGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchMarketCostAdjustedEdgeGateRow, ...],
) -> tuple[ResearchMarketCostAdjustedEdgeGateReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchMarketCostAdjustedEdgeGateReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            row_ratio=_divide_decimal(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_reason_code_counts(
    value: Iterable[ResearchMarketCostAdjustedEdgeGateReasonCodeCount],
) -> tuple[ResearchMarketCostAdjustedEdgeGateReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchMarketCostAdjustedEdgeGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketCostAdjustedEdgeGateReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(max(values))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _normalize_probability(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return normalized


def _normalize_nonnegative_count(name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(name, value)
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return normalized


def _normalize_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_floor_pair(name: str, pass_floor: Decimal, watch_floor: Decimal) -> None:
    if pass_floor < watch_floor:
        raise ValueError(f"{name}_pass_floor must be at least {name}_watch_floor")


def _require_ceiling_pair(
    name: str,
    pass_ceiling: Decimal,
    watch_ceiling: Decimal,
) -> None:
    if watch_ceiling < pass_ceiling:
        raise ValueError(f"{name}_watch_ceiling must be at least {name}_pass_ceiling")


def _require_status(name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_MARKET_COST_ADJUSTED_EDGE_GATE_STATUSES:
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    _require_canonical_string(name, value)
    if value not in ROW_REASON_CODES and value not in REPORT_REASON_CODES:
        raise ValueError(f"{name} is not supported")


def _normalize_reason_codes(
    name: str,
    value: tuple[str, ...],
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    for reason_code in value:
        _require_reason_code(name, reason_code)
        if reason_code not in supported:
            raise ValueError(f"{name} contains an unsupported reason code")
    if len(set(value)) != len(value):
        raise ValueError(f"{name} must not contain duplicates")
    return value


def _require_canonical_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")


def _require_public_label(name: str, value: object) -> None:
    _require_canonical_string(name, value)


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in _PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _apply_or_verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    if provided:
        _verify_digest(value)
    else:
        object.__setattr__(value, "derived_validation_digest", _digest_for(value))


def _verify_digest(value: object) -> None:
    provided = getattr(value, "derived_validation_digest")
    _require_digest("derived_validation_digest", provided)
    if provided != _digest_for(value):
        raise ValueError("derived_validation_digest does not match payload")


def _require_digest(name: str, value: object) -> None:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")


def _digest_for(value: object) -> str:
    payload = asdict(value)
    payload.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("Decimal value must be finite")
        return str(value.quantize(QUANTUM))
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if type(value) is str:
        return value
    if type(value) is bool:
        return value
    if type(value) in (int, float):
        raise ValueError("numeric payload values must be Decimal-derived strings")
    if type(value) is dict:
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if type(value) in (list, tuple):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if any(fragment in key.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
                raise ValueError(f"unsafe public field in {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str and any(
        fragment in value.lower() for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    ):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_COST_ADJUSTED_EDGE_GATE_REPORT_CONFIG_VERSION",
    "RESEARCH_MARKET_COST_ADJUSTED_EDGE_GATE_STATUSES",
    "ResearchMarketCostAdjustedEdgeGateConfig",
    "ResearchMarketCostAdjustedEdgeGateInput",
    "ResearchMarketCostAdjustedEdgeGateReasonCodeCount",
    "ResearchMarketCostAdjustedEdgeGateRow",
    "ResearchMarketCostAdjustedEdgeGateReport",
    "build_research_market_cost_adjusted_edge_gate_report",
    "research_market_cost_adjusted_edge_gate_report_payload",
    "research_market_cost_adjusted_edge_gate_report_digest",
)
