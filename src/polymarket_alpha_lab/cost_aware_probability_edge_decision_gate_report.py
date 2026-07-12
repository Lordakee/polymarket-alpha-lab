"""Manual-first cost-aware probability edge decision gate report."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_COST_AWARE_PROBABILITY_EDGE_DECISION_GATE_CONFIG_VERSION",
    "CostAwareProbabilityEdgeDecisionGateConfig",
    "CostAwareProbabilityEdgeDecisionGateInput",
    "CostAwareProbabilityEdgeDecisionGateReasonCodeCount",
    "CostAwareProbabilityEdgeDecisionGateReport",
    "CostAwareProbabilityEdgeDecisionGateRow",
    "build_cost_aware_probability_edge_decision_gate_report",
    "cost_aware_probability_edge_decision_gate_report_digest",
    "cost_aware_probability_edge_decision_gate_report_payload",
)


DEFAULT_COST_AWARE_PROBABILITY_EDGE_DECISION_GATE_CONFIG_VERSION = (
    "cost-aware-probability-edge-decision-gate-report-v0"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
OPERATOR_REVIEW_CONTEXT = "manual_first_cost_aware_probability_edge_review"

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCKED = "blocked"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCKED)
STATUS_SORT_RANK = {
    STATUS_BLOCKED: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_cost_aware_probability_edge_decision_gate_inputs"
REASON_PASS = "cost_aware_probability_edge_decision_gate_pass"
REASON_WATCH = "cost_aware_probability_edge_decision_gate_watch"
REASON_BLOCKED = "cost_aware_probability_edge_decision_gate_blocked"
REASON_REPORT_PASS = "cost_aware_probability_edge_decision_gate_report_pass"
REASON_REPORT_WATCH = "cost_aware_probability_edge_decision_gate_report_watch"
REASON_REPORT_BLOCKED = "cost_aware_probability_edge_decision_gate_report_blocked"
REASON_NET_EDGE_WATCH = "net_edge_watch"
REASON_NET_EDGE_BLOCKED = "net_edge_blocked"
REASON_TOTAL_COST_WATCH = "total_cost_watch"
REASON_TOTAL_COST_BLOCKED = "total_cost_blocked"
REASON_SPREAD_WATCH = "spread_watch"
REASON_SPREAD_BLOCKED = "spread_blocked"
REASON_DEPTH_WATCH = "depth_watch"
REASON_DEPTH_BLOCKED = "depth_blocked"
REASON_CAPITAL_LOCKUP_WATCH = "capital_lockup_watch"
REASON_CAPITAL_LOCKUP_BLOCKED = "capital_lockup_blocked"
REASON_RESOLUTION_RISK_WATCH = "resolution_risk_watch"
REASON_RESOLUTION_RISK_BLOCKED = "resolution_risk_blocked"
REASON_NET_EDGE_REVIEW = "net_edge_review"
REASON_TOTAL_COST_REVIEW = "total_cost_review"
REASON_SPREAD_REVIEW = "spread_review"
REASON_DEPTH_REVIEW = "depth_review"
REASON_CAPITAL_LOCKUP_REVIEW = "capital_lockup_review"
REASON_RESOLUTION_RISK_REVIEW = "resolution_risk_review"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_PASS,
    REASON_WATCH,
    REASON_BLOCKED,
    REASON_REPORT_PASS,
    REASON_REPORT_WATCH,
    REASON_REPORT_BLOCKED,
    REASON_NET_EDGE_WATCH,
    REASON_NET_EDGE_BLOCKED,
    REASON_TOTAL_COST_WATCH,
    REASON_TOTAL_COST_BLOCKED,
    REASON_SPREAD_WATCH,
    REASON_SPREAD_BLOCKED,
    REASON_DEPTH_WATCH,
    REASON_DEPTH_BLOCKED,
    REASON_CAPITAL_LOCKUP_WATCH,
    REASON_CAPITAL_LOCKUP_BLOCKED,
    REASON_RESOLUTION_RISK_WATCH,
    REASON_RESOLUTION_RISK_BLOCKED,
    REASON_NET_EDGE_REVIEW,
    REASON_TOTAL_COST_REVIEW,
    REASON_SPREAD_REVIEW,
    REASON_DEPTH_REVIEW,
    REASON_CAPITAL_LOCKUP_REVIEW,
    REASON_RESOLUTION_RISK_REVIEW,
)
REASON_CODE_SET = frozenset(REASON_CODES)
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    "://",
    "@",
    "=",
    _join_parts("api", "_", "key"),
    _join_parts("au", "th"),
    _join_parts("buy"),
    _join_parts("candidate", "_", "id"),
    "credential",
    _join_parts("d", "s", "n"),
    _join_parts("intent"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "slug"),
    _join_parts("private", "_", "key"),
    _join_parts("que", "stion"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("raw", "_", "market"),
    "secret",
    _join_parts("sell"),
    _join_parts("sign"),
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("submit"),
    _join_parts("table", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("siz", "e"),
    _join_parts("reco", "mmend"),
)


class CostAwareProbabilityEdgeDecisionGatePayload(dict[str, object]):
    """Immutable JSON-ready public payload."""

    def __readonly(self, *args: object, **kwargs: object) -> None:
        raise TypeError("payload is immutable")

    __setitem__ = __readonly
    __delitem__ = __readonly
    clear = __readonly
    pop = __readonly
    popitem = __readonly
    setdefault = __readonly
    update = __readonly


class _FrozenList(tuple[object, ...]):
    def append(self, value: object) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Iterable[object]) -> None:
        raise TypeError("payload is immutable")

    def insert(self, index: int, value: object) -> None:
        raise TypeError("payload is immutable")

    def remove(self, value: object) -> None:
        raise TypeError("payload is immutable")

    def pop(self, index: int = -1) -> object:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def sort(self, *args: object, **kwargs: object) -> None:
        raise TypeError("payload is immutable")

    def reverse(self) -> None:
        raise TypeError("payload is immutable")


@dataclass(frozen=True)
class CostAwareProbabilityEdgeDecisionGateConfig:
    config_version: str = (
        DEFAULT_COST_AWARE_PROBABILITY_EDGE_DECISION_GATE_CONFIG_VERSION
    )
    pass_net_edge: Decimal = Decimal("0.040000")
    watch_net_edge: Decimal = Decimal("0.015000")
    watch_total_cost: Decimal = Decimal("0.030000")
    blocked_total_cost: Decimal = Decimal("0.060000")
    watch_spread: Decimal = Decimal("0.015000")
    blocked_spread: Decimal = Decimal("0.050000")
    pass_depth: Decimal = Decimal("1.000000")
    blocked_depth: Decimal = Decimal("0.500000")
    watch_capital_lockup: Decimal = Decimal("0.060000")
    blocked_capital_lockup: Decimal = Decimal("0.150000")
    watch_resolution_risk: Decimal = Decimal("0.020000")
    blocked_resolution_risk: Decimal = Decimal("0.080000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CostAwareProbabilityEdgeDecisionGateConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAwareProbabilityEdgeDecisionGateConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_COST_AWARE_PROBABILITY_EDGE_DECISION_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_net_edge",
            "watch_net_edge",
            "watch_total_cost",
            "blocked_total_cost",
            "watch_spread",
            "blocked_spread",
            "pass_depth",
            "blocked_depth",
            "watch_capital_lockup",
            "blocked_capital_lockup",
            "watch_resolution_risk",
            "blocked_resolution_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.pass_net_edge < self.watch_net_edge:
            raise ValueError("pass_net_edge must be at least watch_net_edge")
        _require_ascending("total_cost", self.watch_total_cost, self.blocked_total_cost)
        _require_ascending("spread", self.watch_spread, self.blocked_spread)
        _require_descending("depth", self.pass_depth, self.blocked_depth)
        _require_ascending(
            "capital_lockup",
            self.watch_capital_lockup,
            self.blocked_capital_lockup,
        )
        _require_ascending(
            "resolution_risk",
            self.watch_resolution_risk,
            self.blocked_resolution_risk,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class CostAwareProbabilityEdgeDecisionGateInput:
    private_research_reference: str
    observed_at: datetime
    gross_probability_edge: Decimal
    total_cost: Decimal
    spread: Decimal
    depth: Decimal
    capital_lockup: Decimal
    resolution_risk: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CostAwareProbabilityEdgeDecisionGateInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAwareProbabilityEdgeDecisionGateInput, "input")
        _require_private_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_probability_edge",
            "total_cost",
            "spread",
            "depth",
            "capital_lockup",
            "resolution_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class CostAwareProbabilityEdgeDecisionGateRow:
    signal_digest: str
    observed_at: datetime
    gross_edge: Decimal
    total_cost: Decimal
    net_edge: Decimal
    spread: Decimal
    depth: Decimal
    capital_lockup: Decimal
    resolution_risk: Decimal
    status: str
    reason_codes: tuple[str, ...]
    operator_review_context: str = OPERATOR_REVIEW_CONTEXT
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CostAwareProbabilityEdgeDecisionGateRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAwareProbabilityEdgeDecisionGateRow, "row")
        _require_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "gross_edge",
            "total_cost",
            "spread",
            "depth",
            "capital_lockup",
            "resolution_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "net_edge", _decimal("net_edge", self.net_edge))
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_operator_review_context(self.operator_review_context)
        _require_hard_flags("row", self)
        _apply_or_verify_digest(self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class CostAwareProbabilityEdgeDecisionGateReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CostAwareProbabilityEdgeDecisionGateReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            CostAwareProbabilityEdgeDecisionGateReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _count_decimal("count", self.count))
        object.__setattr__(self, "row_ratio", _probability_decimal("row_ratio", self.row_ratio))
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class CostAwareProbabilityEdgeDecisionGateReport:
    generated_at: datetime
    config_version: str
    operator_review_context: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    blocked_count: Decimal
    mean_gross_edge: Decimal
    mean_total_cost: Decimal
    mean_net_edge: Decimal
    min_net_edge: Decimal
    max_spread: Decimal
    min_depth: Decimal
    max_capital_lockup: Decimal
    max_resolution_risk: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[CostAwareProbabilityEdgeDecisionGateReasonCodeCount, ...]
    rows: tuple[CostAwareProbabilityEdgeDecisionGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "CostAwareProbabilityEdgeDecisionGateReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, CostAwareProbabilityEdgeDecisionGateReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_COST_AWARE_PROBABILITY_EDGE_DECISION_GATE_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_operator_review_context(self.operator_review_context)
        for field_name in ("input_count", "pass_count", "watch_count", "blocked_count"):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_gross_edge",
            "mean_total_cost",
            "max_spread",
            "min_depth",
            "max_capital_lockup",
            "max_resolution_risk",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "mean_net_edge", _decimal("mean_net_edge", self.mean_net_edge))
        object.__setattr__(self, "min_net_edge", _decimal("min_net_edge", self.min_net_edge))
        _require_status("status", self.status)
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
        _require_hard_flags("report", self)
        _apply_or_verify_digest(self)
        _validate_report_consistency(self)


def build_cost_aware_probability_edge_decision_gate_report(
    inputs: Iterable[CostAwareProbabilityEdgeDecisionGateInput],
    *,
    generated_at: datetime,
    config: CostAwareProbabilityEdgeDecisionGateConfig | None = None,
) -> CostAwareProbabilityEdgeDecisionGateReport:
    """Build a deterministic read-only manual operator review report."""

    if config is None:
        config = CostAwareProbabilityEdgeDecisionGateConfig()
    if type(config) is not CostAwareProbabilityEdgeDecisionGateConfig:
        raise ValueError("config must be a CostAwareProbabilityEdgeDecisionGateConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config)
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return CostAwareProbabilityEdgeDecisionGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        operator_review_context=OPERATOR_REVIEW_CONTEXT,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        blocked_count=_status_count(rows, STATUS_BLOCKED),
        mean_gross_edge=_mean(tuple(row.gross_edge for row in rows)),
        mean_total_cost=_mean(tuple(row.total_cost for row in rows)),
        mean_net_edge=_mean(tuple(row.net_edge for row in rows)),
        min_net_edge=_minimum(tuple(row.net_edge for row in rows)),
        max_spread=_maximum(tuple(row.spread for row in rows)),
        min_depth=_minimum(tuple(row.depth for row in rows)),
        max_capital_lockup=_maximum(tuple(row.capital_lockup for row in rows)),
        max_resolution_risk=_maximum(tuple(row.resolution_risk for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def cost_aware_probability_edge_decision_gate_report_payload(
    report: CostAwareProbabilityEdgeDecisionGateReport | Mapping[str, Any],
) -> CostAwareProbabilityEdgeDecisionGatePayload:
    if type(report) is CostAwareProbabilityEdgeDecisionGateReport:
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif isinstance(report, Mapping):
        payload = _json_ready(dict(report))
        if not isinstance(payload, dict):
            raise ValueError("report payload must be a JSON object")
        _verify_public_payload(payload)
    else:
        raise ValueError(
            "report must be a CostAwareProbabilityEdgeDecisionGateReport or payload",
        )
    _reject_unsafe_public_payload("payload", payload)
    return _freeze_payload(payload)


def cost_aware_probability_edge_decision_gate_report_digest(
    report: CostAwareProbabilityEdgeDecisionGateReport,
) -> str:
    if type(report) is not CostAwareProbabilityEdgeDecisionGateReport:
        raise ValueError("report must be a CostAwareProbabilityEdgeDecisionGateReport")
    _verify_report_integrity(report)
    return report.derived_validation_digest


def _row_from_input(
    value: CostAwareProbabilityEdgeDecisionGateInput,
    *,
    config: CostAwareProbabilityEdgeDecisionGateConfig,
) -> CostAwareProbabilityEdgeDecisionGateRow:
    _require_hard_flags("input", value)
    net_edge = _subtract(value.gross_probability_edge, value.total_cost)
    status, reason_codes = _row_status_and_reason_codes(
        net_edge=net_edge,
        total_cost=value.total_cost,
        spread=value.spread,
        depth=value.depth,
        capital_lockup=value.capital_lockup,
        resolution_risk=value.resolution_risk,
        config=config,
    )
    return CostAwareProbabilityEdgeDecisionGateRow(
        signal_digest=_signal_digest(value),
        observed_at=value.observed_at,
        gross_edge=value.gross_probability_edge,
        total_cost=value.total_cost,
        net_edge=net_edge,
        spread=value.spread,
        depth=value.depth,
        capital_lockup=value.capital_lockup,
        resolution_risk=value.resolution_risk,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reason_codes(
    *,
    net_edge: Decimal,
    total_cost: Decimal,
    spread: Decimal,
    depth: Decimal,
    capital_lockup: Decimal,
    resolution_risk: Decimal,
    config: CostAwareProbabilityEdgeDecisionGateConfig,
) -> tuple[str, tuple[str, ...]]:
    blocked: list[str] = []
    watched: list[str] = []
    if net_edge < config.watch_net_edge:
        blocked.append(REASON_NET_EDGE_BLOCKED)
    elif net_edge < config.pass_net_edge:
        watched.append(REASON_NET_EDGE_WATCH)
    if total_cost >= config.blocked_total_cost:
        blocked.append(REASON_TOTAL_COST_BLOCKED)
    elif total_cost >= config.watch_total_cost:
        watched.append(REASON_TOTAL_COST_WATCH)
    if spread >= config.blocked_spread:
        blocked.append(REASON_SPREAD_BLOCKED)
    elif spread >= config.watch_spread:
        watched.append(REASON_SPREAD_WATCH)
    if depth <= config.blocked_depth:
        blocked.append(REASON_DEPTH_BLOCKED)
    elif depth < config.pass_depth:
        watched.append(REASON_DEPTH_WATCH)
    if capital_lockup >= config.blocked_capital_lockup:
        blocked.append(REASON_CAPITAL_LOCKUP_BLOCKED)
    elif capital_lockup >= config.watch_capital_lockup:
        watched.append(REASON_CAPITAL_LOCKUP_WATCH)
    if resolution_risk >= config.blocked_resolution_risk:
        blocked.append(REASON_RESOLUTION_RISK_BLOCKED)
    elif resolution_risk >= config.watch_resolution_risk:
        watched.append(REASON_RESOLUTION_RISK_WATCH)
    if blocked:
        return STATUS_BLOCKED, (REASON_BLOCKED, *tuple(blocked))
    if watched:
        return STATUS_WATCH, (REASON_WATCH, *tuple(watched))
    return STATUS_PASS, (REASON_PASS,)


def _report_status(rows: tuple[CostAwareProbabilityEdgeDecisionGateRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCKED
    if any(row.status == STATUS_BLOCKED for row in rows):
        return STATUS_BLOCKED
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[CostAwareProbabilityEdgeDecisionGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    codes: list[str] = []
    status = _report_status(rows)
    if status == STATUS_BLOCKED:
        codes.append(REASON_REPORT_BLOCKED)
    elif status == STATUS_WATCH:
        codes.append(REASON_REPORT_WATCH)
    else:
        codes.append(REASON_REPORT_PASS)
    row_codes = {code for row in rows for code in row.reason_codes}
    if REASON_NET_EDGE_BLOCKED in row_codes or REASON_NET_EDGE_WATCH in row_codes:
        codes.append(REASON_NET_EDGE_REVIEW)
    if REASON_TOTAL_COST_BLOCKED in row_codes or REASON_TOTAL_COST_WATCH in row_codes:
        codes.append(REASON_TOTAL_COST_REVIEW)
    if REASON_SPREAD_BLOCKED in row_codes or REASON_SPREAD_WATCH in row_codes:
        codes.append(REASON_SPREAD_REVIEW)
    if REASON_DEPTH_BLOCKED in row_codes or REASON_DEPTH_WATCH in row_codes:
        codes.append(REASON_DEPTH_REVIEW)
    if (
        REASON_CAPITAL_LOCKUP_BLOCKED in row_codes
        or REASON_CAPITAL_LOCKUP_WATCH in row_codes
    ):
        codes.append(REASON_CAPITAL_LOCKUP_REVIEW)
    if (
        REASON_RESOLUTION_RISK_BLOCKED in row_codes
        or REASON_RESOLUTION_RISK_WATCH in row_codes
    ):
        codes.append(REASON_RESOLUTION_RISK_REVIEW)
    return (codes[0], *tuple(sorted(codes[1:])))


def _reason_code_counts_from_rows(
    rows: tuple[CostAwareProbabilityEdgeDecisionGateRow, ...],
) -> tuple[CostAwareProbabilityEdgeDecisionGateReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        CostAwareProbabilityEdgeDecisionGateReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            row_ratio=_ratio(_count(count), denominator),
        )
        for reason_code, count in sorted(counts.items())
    )


def _public_report_payload(
    report: CostAwareProbabilityEdgeDecisionGateReport,
) -> dict[str, Any]:
    payload = _json_ready(_report_public_digest_input(report))
    if not isinstance(payload, dict):
        raise ValueError("report payload must be a JSON object")
    payload["derived_validation_digest"] = report.derived_validation_digest
    _verify_public_payload(payload)
    return payload


def _verify_public_payload(payload: Mapping[str, Any]) -> None:
    _reject_unsafe_public_payload("payload", payload)
    digest = payload.get("derived_validation_digest")
    _require_digest("derived_validation_digest", digest)
    digest_input = _mutable_json(payload)
    if not isinstance(digest_input, dict):
        raise ValueError("report payload must be a JSON object")
    digest_input.pop("derived_validation_digest", None)
    expected = _payload_digest(digest_input)
    if digest != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _freeze_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return CostAwareProbabilityEdgeDecisionGatePayload(
            {key: _freeze_payload(item) for key, item in value.items()},
        )
    if isinstance(value, list | tuple):
        return _FrozenList(_freeze_payload(item) for item in value)
    return value


def _mutable_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _mutable_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_mutable_json(item) for item in value]
    return value


def _normalize_inputs(
    inputs: Iterable[CostAwareProbabilityEdgeDecisionGateInput],
) -> tuple[CostAwareProbabilityEdgeDecisionGateInput, ...]:
    if isinstance(inputs, CostAwareProbabilityEdgeDecisionGateInput):
        raise ValueError("inputs must be an iterable of inputs")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of inputs") from exc
    for value in normalized:
        if type(value) is not CostAwareProbabilityEdgeDecisionGateInput:
            raise ValueError("inputs must contain CostAwareProbabilityEdgeDecisionGateInput")
        _require_hard_flags("input", value)
    return normalized


def _normalize_rows(
    rows: tuple[CostAwareProbabilityEdgeDecisionGateRow, ...],
) -> tuple[CostAwareProbabilityEdgeDecisionGateRow, ...]:
    if isinstance(rows, CostAwareProbabilityEdgeDecisionGateRow):
        raise ValueError("rows must be an iterable of rows")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of rows") from exc
    for row in normalized:
        if type(row) is not CostAwareProbabilityEdgeDecisionGateRow:
            raise ValueError("rows must contain CostAwareProbabilityEdgeDecisionGateRow")
        _require_hard_flags("row", row)
        _verify_digest(row)
    if tuple(sorted(normalized, key=_row_sort_key)) != normalized:
        raise ValueError("rows must be sorted by status and digest")
    return normalized


def _normalize_reason_code_counts(
    counts: tuple[CostAwareProbabilityEdgeDecisionGateReasonCodeCount, ...],
) -> tuple[CostAwareProbabilityEdgeDecisionGateReasonCodeCount, ...]:
    if isinstance(counts, CostAwareProbabilityEdgeDecisionGateReasonCodeCount):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for value in normalized:
        if type(value) is not CostAwareProbabilityEdgeDecisionGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "CostAwareProbabilityEdgeDecisionGateReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", value)
    if tuple(sorted(normalized, key=lambda value: value.reason_code)) != normalized:
        raise ValueError("reason_code_counts must be sorted")
    return normalized


def _row_sort_key(row: CostAwareProbabilityEdgeDecisionGateRow) -> tuple[Decimal, str]:
    return (STATUS_SORT_RANK[row.status], row.signal_digest)


def _validate_row_consistency(row: CostAwareProbabilityEdgeDecisionGateRow) -> None:
    if row.net_edge != _subtract(row.gross_edge, row.total_cost):
        raise ValueError("net_edge must equal gross_edge minus total_cost")
    if row.reason_codes[0] == REASON_PASS and row.status != STATUS_PASS:
        raise ValueError("pass reason code must match status")
    if row.reason_codes[0] == REASON_WATCH and row.status != STATUS_WATCH:
        raise ValueError("watch reason code must match status")
    if row.reason_codes[0] == REASON_BLOCKED and row.status != STATUS_BLOCKED:
        raise ValueError("blocked reason code must match status")


def _validate_report_consistency(report: CostAwareProbabilityEdgeDecisionGateReport) -> None:
    rows = report.rows
    if report.input_count != _count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.blocked_count != _status_count(rows, STATUS_BLOCKED):
        raise ValueError("blocked_count must match rows")
    if report.mean_gross_edge != _mean(tuple(row.gross_edge for row in rows)):
        raise ValueError("mean_gross_edge must match rows")
    if report.mean_total_cost != _mean(tuple(row.total_cost for row in rows)):
        raise ValueError("mean_total_cost must match rows")
    if report.mean_net_edge != _mean(tuple(row.net_edge for row in rows)):
        raise ValueError("mean_net_edge must match rows")
    if report.min_net_edge != _minimum(tuple(row.net_edge for row in rows)):
        raise ValueError("min_net_edge must match rows")
    if report.max_spread != _maximum(tuple(row.spread for row in rows)):
        raise ValueError("max_spread must match rows")
    if report.min_depth != _minimum(tuple(row.depth for row in rows)):
        raise ValueError("min_depth must match rows")
    if report.max_capital_lockup != _maximum(tuple(row.capital_lockup for row in rows)):
        raise ValueError("max_capital_lockup must match rows")
    if report.max_resolution_risk != _maximum(tuple(row.resolution_risk for row in rows)):
        raise ValueError("max_resolution_risk must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(rows):
        raise ValueError("reason_code_counts must match rows")
    for row in rows:
        _verify_digest(row)


def _verify_report_integrity(report: CostAwareProbabilityEdgeDecisionGateReport) -> None:
    _validate_report_consistency(report)
    _verify_digest(report)
    for row in report.rows:
        _verify_digest(row)


def _status_count(
    rows: tuple[CostAwareProbabilityEdgeDecisionGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _ratio(_sum(values), _count(len(values)))


def _maximum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return max(values)


def _minimum(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return min(values)


def _sum(values: tuple[Decimal, ...]) -> Decimal:
    total = ZERO
    for value in values:
        total = _add(total, value)
    return total


def _add(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left + right)


def _subtract(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    if type(value) is not int:
        raise ValueError("count must be an int")
    if value < 0:
        raise ValueError("count must be nonnegative")
    return _quantize(Decimal(value))


def _decimal(field_name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _nonnegative_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _probability_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be at most one")
    return normalized


def _count_decimal(field_name: str, value: Decimal) -> Decimal:
    normalized = _nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be an integer Decimal")
    return normalized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal value cannot be quantized") from exc


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _apply_or_verify_digest(
    value: CostAwareProbabilityEdgeDecisionGateRow
    | CostAwareProbabilityEdgeDecisionGateReport,
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
    value: CostAwareProbabilityEdgeDecisionGateRow
    | CostAwareProbabilityEdgeDecisionGateReport,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: CostAwareProbabilityEdgeDecisionGateRow
    | CostAwareProbabilityEdgeDecisionGateReport,
) -> str:
    if type(value) is CostAwareProbabilityEdgeDecisionGateReport:
        return _payload_digest(_report_public_digest_input(value))
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    return _payload_digest(digest_input)


def _report_public_digest_input(
    report: CostAwareProbabilityEdgeDecisionGateReport,
) -> dict[str, Any]:
    digest_input = asdict(report)
    digest_input.pop("derived_validation_digest", None)
    rows = []
    for row in digest_input["rows"]:
        row.pop("signal_digest", None)
        rows.append(row)
    digest_input["rows"] = rows
    return digest_input


def _payload_digest(value: Mapping[str, Any]) -> str:
    payload = _json_ready(value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return sha256(encoded).hexdigest()


def _signal_digest(value: CostAwareProbabilityEdgeDecisionGateInput) -> str:
    payload = {
        "observed_at": value.observed_at,
        "gross_probability_edge": value.gross_probability_edge,
        "total_cost": value.total_cost,
        "spread": value.spread,
        "depth": value.depth,
        "capital_lockup": value.capital_lockup,
        "resolution_risk": value.resolution_risk,
    }
    return _payload_digest(payload)


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or type(value) in (str, bool):
        return value
    raise ValueError("payload value is not JSON-ready")


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable of strings")
    try:
        normalized = tuple(reason_codes)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable of strings") from exc
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in normalized:
        _require_reason_code(field_name, reason_code)
    return normalized


def _require_reason_code(field_name: str, value: str) -> None:
    _require_public_identifier(field_name, value)
    if value not in REASON_CODE_SET:
        raise ValueError(f"{field_name} is not a supported reason code")


def _require_status(field_name: str, value: str) -> None:
    if value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or blocked")


def _require_operator_review_context(value: str) -> None:
    _require_public_identifier("operator_review_context", value)
    if value != OPERATOR_REVIEW_CONTEXT:
        raise ValueError("operator_review_context must be manual-first review context")


def _require_public_identifier(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    for character in value:
        if not (
            character.isascii()
            and (character.isalnum() or character in {"_", "-", "."})
        ):
            raise ValueError(f"{field_name} must be a public identifier")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _require_private_reference(field_name: str, value: str) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_ascending(field_name: str, low: Decimal, high: Decimal) -> None:
    if low > high:
        raise ValueError(f"{field_name} thresholds must be ascending")


def _require_descending(field_name: str, high: Decimal, low: Decimal) -> None:
    if high < low:
        raise ValueError(f"{field_name} thresholds must be descending")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _reject_unsafe_public_payload(label: str, value: Any) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public field")
            if _has_unsafe_public_fragment(key):
                raise ValueError("unsafe public field")
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, str) and _has_unsafe_public_fragment(value):
        raise ValueError("unsafe public field")
