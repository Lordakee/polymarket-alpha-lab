"""Pure research cost-threshold policy for Polymarket candidate screening.

The policy is deterministic and side-effect free. It only converts
caller-supplied research candidates into pass/watch/block review states.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from typing import Any


DEFAULT_RESEARCH_COST_THRESHOLD_CONFIG_VERSION = "research-cost-threshold-policy-v0"

_QUANTUM = Decimal("0.000001")
_COUNT_QUANTUM = Decimal("1")
_ZERO = Decimal("0.000000")
_STATUSES = ("pass", "watch", "block")
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_HEX_CHARS = frozenset("0123456789abcdef")

_PASS_REASON = "research_cost_threshold_pass"
_WATCH_REASON = "cost_ratio_at_or_above_watch"
_BLOCK_REASON = "cost_ratio_at_or_above_block"
_EMPTY_REASON = "research_cost_threshold_empty"
_REASON_PRIORITY = (
    _BLOCK_REASON,
    _WATCH_REASON,
    _PASS_REASON,
    _EMPTY_REASON,
)


@dataclass(frozen=True)
class ResearchCostThresholdConfig:
    config_version: str = DEFAULT_RESEARCH_COST_THRESHOLD_CONFIG_VERSION
    watch_cost_to_edge_ratio: Decimal = Decimal("0.300000")
    block_cost_to_edge_ratio: Decimal = Decimal("0.500000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("config_version", self.config_version)
        object.__setattr__(
            self,
            "watch_cost_to_edge_ratio",
            _normalize_nonnegative_decimal(
                "watch_cost_to_edge_ratio",
                self.watch_cost_to_edge_ratio,
            ),
        )
        object.__setattr__(
            self,
            "block_cost_to_edge_ratio",
            _normalize_nonnegative_decimal(
                "block_cost_to_edge_ratio",
                self.block_cost_to_edge_ratio,
            ),
        )
        if self.block_cost_to_edge_ratio < self.watch_cost_to_edge_ratio:
            raise ValueError("block_cost_to_edge_ratio must be at least watch threshold")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchCostThresholdCandidate:
    candidate_reference: str
    market_reference: str
    observed_at: datetime
    probability_edge: Decimal
    polymarket_taker_fee_probability: Decimal
    spread_probability: Decimal
    gas_cost: Decimal
    deposit_cost: Decimal
    settlement_cost: Decimal
    expected_notional: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_text("candidate_reference", self.candidate_reference)
        _require_text("market_reference", self.market_reference)
        object.__setattr__(
            self,
            "candidate_reference",
            _redacted_reference(
                "research_ref_",
                f"{self.candidate_reference}\0{self.market_reference}",
            ),
        )
        object.__setattr__(
            self,
            "market_reference",
            _redacted_reference("market_ref_", self.market_reference),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_edge",
            _normalize_positive_decimal("probability_edge", self.probability_edge),
        )
        for field_name in (
            "polymarket_taker_fee_probability",
            "spread_probability",
            "gas_cost",
            "deposit_cost",
            "settlement_cost",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "expected_notional",
            _normalize_positive_decimal("expected_notional", self.expected_notional),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _stable_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class ResearchCostThresholdRow:
    research_reference: str
    observed_at: datetime
    probability_edge: Decimal
    polymarket_taker_fee_probability: Decimal
    spread_probability: Decimal
    fixed_cost_probability: Decimal
    total_cost_probability: Decimal
    cost_to_edge_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_redacted_reference("research_reference", self.research_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "probability_edge",
            _normalize_positive_decimal("probability_edge", self.probability_edge),
        )
        for field_name in (
            "polymarket_taker_fee_probability",
            "spread_probability",
            "fixed_cost_probability",
            "total_cost_probability",
            "cost_to_edge_ratio",
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
            _stable_reason_codes("reason_codes", self.reason_codes),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchCostThresholdReport:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_cost_to_edge_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchCostThresholdRow, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_text("config_version", self.config_version)
        for field_name in (
            "candidate_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_cost_to_edge_ratio",
            _normalize_nonnegative_decimal(
                "max_cost_to_edge_ratio",
                self.max_cost_to_edge_ratio,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reason_codes(self.reason_codes),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _validate_report(self)
        _require_hard_flags("report", self)


def build_research_cost_threshold_report(
    candidates: Iterable[object],
    *,
    config: ResearchCostThresholdConfig,
    generated_at: datetime,
) -> ResearchCostThresholdReport:
    if type(config) is not ResearchCostThresholdConfig:
        raise ValueError("config must be a ResearchCostThresholdConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    rows = tuple(
        sorted(
            (
                _row_from_candidate(
                    item,
                    config=config,
                    generated_at=generated_at_utc,
                )
                for item in _normalize_candidates(candidates)
            ),
            key=_row_key,
        ),
    )
    return ResearchCostThresholdReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        max_cost_to_edge_ratio=_max_decimal(row.cost_to_edge_ratio for row in rows),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_cost_threshold_policy_payload(
    report: ResearchCostThresholdReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchCostThresholdReport:
        _require_hard_flags("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchCostThresholdReport")
    if type(payload) is not dict:
        raise ValueError("public payload must be an object")
    _require_payload_flags(payload)
    _reject_public_payload_leaks(payload)
    return payload


def _row_from_candidate(
    candidate: ResearchCostThresholdCandidate,
    *,
    config: ResearchCostThresholdConfig,
    generated_at: datetime,
) -> ResearchCostThresholdRow:
    if candidate.observed_at > generated_at:
        raise ValueError("observed_at must not follow generated_at")
    fixed_cost_probability = _ratio(
        candidate.gas_cost + candidate.deposit_cost + candidate.settlement_cost,
        candidate.expected_notional,
    )
    total_cost_probability = _quantize(
        candidate.polymarket_taker_fee_probability
        + candidate.spread_probability
        + fixed_cost_probability,
    )
    cost_to_edge_ratio = _ratio(total_cost_probability, candidate.probability_edge)
    status = _row_status(cost_to_edge_ratio, config)
    reason_codes = _stable_reason_codes(
        "reason_codes",
        (*candidate.reason_codes, _status_reason(status)),
    )
    return ResearchCostThresholdRow(
        research_reference=candidate.candidate_reference,
        observed_at=candidate.observed_at,
        probability_edge=candidate.probability_edge,
        polymarket_taker_fee_probability=candidate.polymarket_taker_fee_probability,
        spread_probability=candidate.spread_probability,
        fixed_cost_probability=fixed_cost_probability,
        total_cost_probability=total_cost_probability,
        cost_to_edge_ratio=cost_to_edge_ratio,
        status=status,
        reason_codes=reason_codes,
    )


def _normalize_candidates(
    candidates: Iterable[object],
) -> tuple[ResearchCostThresholdCandidate, ...]:
    if isinstance(candidates, (str, bytes)):
        raise ValueError("candidates must be iterable")
    try:
        items = tuple(candidates)
    except TypeError as exc:
        raise ValueError("candidates must be iterable") from exc
    seen_references: set[str] = set()
    for item in items:
        if type(item) is not ResearchCostThresholdCandidate:
            raise ValueError(
                "candidates must contain ResearchCostThresholdCandidate values",
            )
        _require_hard_flags("candidate", item)
        if item.candidate_reference in seen_references:
            raise ValueError("duplicate research reference")
        seen_references.add(item.candidate_reference)
    return items


def _normalize_rows(rows: object) -> tuple[ResearchCostThresholdRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    normalized = tuple(rows)
    for row in normalized:
        if type(row) is not ResearchCostThresholdRow:
            raise ValueError("rows must contain ResearchCostThresholdRow values")
        _require_hard_flags("row", row)
    if normalized != tuple(sorted(normalized, key=_row_key)):
        raise ValueError("rows must be sorted")
    if len({row.research_reference for row in normalized}) != len(normalized):
        raise ValueError("rows must be unique")
    return normalized


def _validate_row(row: ResearchCostThresholdRow) -> None:
    expected_total_cost = _quantize(
        row.polymarket_taker_fee_probability
        + row.spread_probability
        + row.fixed_cost_probability,
    )
    if row.total_cost_probability != expected_total_cost:
        raise ValueError("total_cost_probability must match cost components")
    if row.cost_to_edge_ratio != _ratio(row.total_cost_probability, row.probability_edge):
        raise ValueError("cost_to_edge_ratio must match total cost and edge")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")
    if row.status == "pass" and _PASS_REASON not in row.reason_codes:
        raise ValueError("pass rows must include pass reason")
    if row.status == "watch" and _WATCH_REASON not in row.reason_codes:
        raise ValueError("watch rows must include watch reason")
    if row.status == "block" and _BLOCK_REASON not in row.reason_codes:
        raise ValueError("block rows must include block reason")


def _validate_report(report: ResearchCostThresholdReport) -> None:
    rows = report.rows
    if report.candidate_count != _count(len(rows)):
        raise ValueError("candidate_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.max_cost_to_edge_ratio != _max_decimal(
        row.cost_to_edge_ratio for row in rows
    ):
        raise ValueError("max_cost_to_edge_ratio must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")


def _row_status(
    cost_to_edge_ratio: Decimal,
    config: ResearchCostThresholdConfig,
) -> str:
    if cost_to_edge_ratio >= config.block_cost_to_edge_ratio:
        return "block"
    if cost_to_edge_ratio >= config.watch_cost_to_edge_ratio:
        return "watch"
    return "pass"


def _status_reason(status: str) -> str:
    if status == "block":
        return _BLOCK_REASON
    if status == "watch":
        return _WATCH_REASON
    return _PASS_REASON


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if _BLOCK_REASON in reason_codes:
        return "block"
    if _WATCH_REASON in reason_codes:
        return "watch"
    return "pass"


def _report_status(rows: tuple[ResearchCostThresholdRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchCostThresholdRow, ...]) -> tuple[str, ...]:
    if not rows:
        return (_EMPTY_REASON,)
    observed = {
        reason_code
        for row in rows
        for reason_code in row.reason_codes
        if reason_code in _REASON_PRIORITY
    }
    if not observed:
        return (_PASS_REASON,)
    return tuple(reason for reason in _REASON_PRIORITY if reason in observed)


def _row_key(
    row: ResearchCostThresholdRow,
) -> tuple[int, Decimal, datetime, str]:
    return (
        _STATUS_WEIGHT[row.status],
        -row.cost_to_edge_ratio,
        row.observed_at,
        row.research_reference,
    )


def _normalize_report_reason_codes(value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    previous_index = -1
    for reason_code in reason_codes:
        _require_text("reason_codes", reason_code)
        if reason_code not in _REASON_PRIORITY:
            raise ValueError("reason_codes must be known")
        if reason_code in seen:
            raise ValueError("reason_codes must be unique")
        reason_index = _REASON_PRIORITY.index(reason_code)
        if reason_index <= previous_index:
            raise ValueError("reason_codes must use priority sequence")
        seen.add(reason_code)
        previous_index = reason_index
    return reason_codes


def _stable_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not tuple:
        raise ValueError(f"{field_name} must be a tuple")
    for item in value:
        _require_text(field_name, item)
    return tuple(sorted(set(value)))


def _max_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return _ZERO
    return max(items)


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    return _quantize(numerator / denominator)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(_COUNT_QUANTUM)


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


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal")
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be an exact Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _normalize_count(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    quantized = value.quantize(_COUNT_QUANTUM)
    if quantized != value:
        raise ValueError(f"{field_name} must be integral")
    if quantized < Decimal("0"):
        raise ValueError(f"{field_name} must be nonnegative")
    return quantized


def _quantize(value: Decimal) -> Decimal:
    with localcontext(_DECIMAL_CONTEXT):
        return value.quantize(_QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_text(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must be canonical text")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _redacted_reference(prefix: str, value: str) -> str:
    digest = sha256(f"{prefix}\0{value}".encode("utf-8")).hexdigest()[:16]
    return f"{prefix}{digest}"


def _require_redacted_reference(field_name: str, value: object) -> None:
    prefix = "research_ref_"
    if type(value) is not str:
        raise ValueError(f"{field_name} must be redacted")
    if not value.startswith(prefix):
        raise ValueError(f"{field_name} must be redacted")
    suffix = value[len(prefix) :]
    if len(suffix) != 16 or any(char not in _HEX_CHARS for char in suffix):
        raise ValueError(f"{field_name} must be redacted")


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("public payload Decimal value must be exact and finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("public payload datetime value must be exact")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("public payload datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, bool):
        return value
    if isinstance(value, (float, int)):
        raise ValueError("public payload must not contain float or int values")
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("public payload value is not JSON serializable")


def _require_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True for public payload")


def _reject_public_payload_leaks(payload: dict[str, Any]) -> None:
    _reject_public_payload_item(payload, key_path=())


def _reject_public_payload_item(value: object, *, key_path: tuple[str, ...]) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_public_text(key)
            if key.lower().endswith("status"):
                if item not in _STATUSES:
                    raise ValueError("public payload status must be pass, watch, or block")
            _reject_public_payload_item(item, key_path=(*key_path, key))
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_payload_item(item, key_path=key_path)
        return
    if isinstance(value, str):
        _reject_public_text(value)


def _reject_public_text(value: str) -> None:
    lowered = value.lower()
    for fragment in _public_forbidden_fragments():
        if fragment in lowered:
            raise ValueError("public payload contains restricted research surface")


def _public_forbidden_fragments() -> tuple[str, ...]:
    return tuple(
        _word(value)
        for value in (
            "63616e6469646174655f6964",
            "6d61726b65745f6964",
            "6d61726b65745f736c7567",
            "6d61726b65745f7175657374696f6e",
            "736f757263655f726566",
            "736f757263655f75726c",
            "736f757263655f74657874",
            "64736e",
            "7461626c65",
            "746f6b656e",
            "77616c6c6574",
            "61757468",
            "6f72646572",
            "7472616465",
            "706f736974696f6e",
            "627579",
            "73656c6c",
            "7265636f6d6d656e646174696f6e",
            "7175657374696f6e",
        )
    )


def _word(hex_value: str) -> str:
    return bytes.fromhex(hex_value).decode("utf-8")


__all__ = (
    "DEFAULT_RESEARCH_COST_THRESHOLD_CONFIG_VERSION",
    "ResearchCostThresholdCandidate",
    "ResearchCostThresholdConfig",
    "ResearchCostThresholdReport",
    "ResearchCostThresholdRow",
    "build_research_cost_threshold_report",
    "research_cost_threshold_policy_payload",
)
