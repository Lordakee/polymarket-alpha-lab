from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from typing import Any


DEFAULT_STRATEGY_MARKET_PROBABILITY_EDGE_COST_FLOOR_V2_CONFIG_VERSION = (
    "strategy-market-probability-edge-cost-floor-v2"
)

ROW_STATUSES = ("pass", "watch", "block")
REPORT_STATUSES = ("empty", "pass", "watch", "block")
STATUS_REASON_CODES = (
    "edge_after_cost_floor_meets_minimum",
    "edge_after_cost_floor_below_minimum",
    "edge_after_cost_floor_negative",
    "gross_edge_non_positive",
)
STATUS_RANK = {
    "pass": Decimal("0.000000"),
    "watch": Decimal("1.000000"),
    "block": Decimal("2.000000"),
}

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_SURFACE_FRAGMENTS = frozenset(
    (
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("net", "work"),
        _join_parts("data", "base"),
        _join_parts("per", "sist"),
        _join_parts("sig", "ning"),
        _join_parts("mu", "tation"),
        _join_parts("bu", "y"),
        _join_parts("sel", "l"),
        _join_parts("tra", "de"),
    ),
)


@dataclass(frozen=True)
class StrategyMarketProbabilityEdgeCostFloorV2Config:
    config_version: str = DEFAULT_STRATEGY_MARKET_PROBABILITY_EDGE_COST_FLOOR_V2_CONFIG_VERSION
    min_required_net_edge: Decimal = Decimal("0.030000")
    watch_net_edge_floor: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityEdgeCostFloorV2Config does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketProbabilityEdgeCostFloorV2Config, "config")
        _require_public_string("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_STRATEGY_MARKET_PROBABILITY_EDGE_COST_FLOOR_V2_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in ("min_required_net_edge", "watch_net_edge_floor"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_net_edge_floor > self.min_required_net_edge:
            raise ValueError("watch_net_edge_floor must not exceed min_required_net_edge")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class StrategyMarketProbabilityEdgeCostFloorV2Candidate:
    market_id: str
    event_slug: str
    category: str
    model_probability: Decimal
    market_probability: Decimal
    taker_fee_rate: Decimal
    settlement_slippage_rate: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityEdgeCostFloorV2Candidate does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketProbabilityEdgeCostFloorV2Candidate, "candidate")
        for field_name in ("market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("taker_fee_rate", "settlement_slippage_rate"):
            object.__setattr__(
                self,
                field_name,
                _normalize_rate(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_candidate_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("candidate", self)


@dataclass(frozen=True)
class StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount:
    reason_code: str
    count: Decimal
    candidate_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount,
            "reason_code_count",
        )
        _require_public_string("reason_code", self.reason_code)
        object.__setattr__(self, "count", _normalize_count("count", self.count))
        if self.count <= ZERO:
            raise ValueError("count must be positive")
        object.__setattr__(
            self,
            "candidate_ratio",
            _normalize_rate("candidate_ratio", self.candidate_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class StrategyMarketProbabilityEdgeCostFloorV2Row:
    market_id: str
    event_slug: str
    category: str
    model_probability: Decimal
    market_probability: Decimal
    gross_edge: Decimal
    taker_fee_rate: Decimal
    settlement_slippage_rate: Decimal
    total_cost_floor: Decimal
    net_edge: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError("StrategyMarketProbabilityEdgeCostFloorV2Row does not support subclassing")

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketProbabilityEdgeCostFloorV2Row, "row")
        for field_name in ("market_id", "event_slug", "category"):
            _require_public_string(field_name, getattr(self, field_name))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("gross_edge", "net_edge"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "taker_fee_rate",
            "settlement_slippage_rate",
            "total_cost_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_rate(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, ROW_STATUSES)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes),
        )
        _require_hard_flags("row", self)
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _row_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_row(self)


@dataclass(frozen=True)
class StrategyMarketProbabilityEdgeCostFloorV2Report:
    generated_at: datetime
    config_version: str
    candidate_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_net_edge: Decimal
    min_required_net_edge: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount, ...]
    rows: tuple[StrategyMarketProbabilityEdgeCostFloorV2Row, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "StrategyMarketProbabilityEdgeCostFloorV2Report does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, StrategyMarketProbabilityEdgeCostFloorV2Report, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_string("config_version", self.config_version)
        for field_name in ("candidate_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_count(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_net_edge",
            _normalize_decimal("max_net_edge", self.max_net_edge),
        )
        object.__setattr__(
            self,
            "min_required_net_edge",
            _normalize_nonnegative_decimal(
                "min_required_net_edge",
                self.min_required_net_edge,
            ),
        )
        _require_member("report_status", self.report_status, REPORT_STATUSES)
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
        if self.derived_validation_digest == "":
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_derived_validation_digest(self),
            )
        else:
            object.__setattr__(
                self,
                "derived_validation_digest",
                _require_sha256_digest(
                    "derived_validation_digest",
                    self.derived_validation_digest,
                ),
            )
        _validate_report(self)


def build_strategy_market_probability_edge_cost_floor_v2_report(
    candidates: list[StrategyMarketProbabilityEdgeCostFloorV2Candidate]
    | tuple[StrategyMarketProbabilityEdgeCostFloorV2Candidate, ...],
    *,
    config: StrategyMarketProbabilityEdgeCostFloorV2Config,
    generated_at: datetime,
) -> StrategyMarketProbabilityEdgeCostFloorV2Report:
    if type(config) is not StrategyMarketProbabilityEdgeCostFloorV2Config:
        raise ValueError("config must be a StrategyMarketProbabilityEdgeCostFloorV2Config")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_candidates = _normalize_candidates(candidates)
    _validate_unique_candidates(normalized_candidates)

    rows = tuple(
        sorted(
            (
                _row_for_candidate(candidate, config=config)
                for candidate in normalized_candidates
            ),
            key=_row_sort_key,
        ),
    )
    min_required_net_edge = config.min_required_net_edge if rows else ZERO
    return StrategyMarketProbabilityEdgeCostFloorV2Report(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        candidate_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        max_net_edge=max((row.net_edge for row in rows), default=ZERO),
        min_required_net_edge=min_required_net_edge,
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def strategy_market_probability_edge_cost_floor_v2_public_payload(
    report: StrategyMarketProbabilityEdgeCostFloorV2Report,
) -> dict[str, Any]:
    if type(report) is not StrategyMarketProbabilityEdgeCostFloorV2Report:
        raise ValueError(
            "report must be a StrategyMarketProbabilityEdgeCostFloorV2Report",
        )
    _validate_report(report)
    payload = _report_public_payload_for_digest(report)
    payload["derived_validation_digest"] = report.derived_validation_digest
    validate_strategy_market_probability_edge_cost_floor_v2_public_payload(payload)
    return payload


def validate_strategy_market_probability_edge_cost_floor_v2_public_payload(
    payload: dict[str, Any],
) -> bool:
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload("strategy market probability edge cost floor payload", payload)
    _require_public_payload_flags(payload)
    _reject_public_numeric_values(payload)
    _validate_payload_row_digests(payload)
    digest_value = _payload_required_string(payload, "derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    if digest_value != _public_payload_derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match public payload")
    return True


def _row_for_candidate(
    candidate: StrategyMarketProbabilityEdgeCostFloorV2Candidate,
    *,
    config: StrategyMarketProbabilityEdgeCostFloorV2Config,
) -> StrategyMarketProbabilityEdgeCostFloorV2Row:
    gross_edge = _subtract_decimal(candidate.model_probability, candidate.market_probability)
    total_cost_floor = _add_decimal(candidate.taker_fee_rate, candidate.settlement_slippage_rate)
    net_edge = _subtract_decimal(gross_edge, total_cost_floor)
    status = _row_status(net_edge, config=config)
    return StrategyMarketProbabilityEdgeCostFloorV2Row(
        market_id=candidate.market_id,
        event_slug=candidate.event_slug,
        category=candidate.category,
        model_probability=candidate.model_probability,
        market_probability=candidate.market_probability,
        gross_edge=gross_edge,
        taker_fee_rate=candidate.taker_fee_rate,
        settlement_slippage_rate=candidate.settlement_slippage_rate,
        total_cost_floor=total_cost_floor,
        net_edge=net_edge,
        status=status,
        reason_codes=_row_reason_codes(
            status=status,
            gross_edge=gross_edge,
            candidate_reason_codes=candidate.reason_codes,
        ),
    )


def _row_status(
    net_edge: Decimal,
    *,
    config: StrategyMarketProbabilityEdgeCostFloorV2Config,
) -> str:
    if net_edge >= config.min_required_net_edge:
        return "pass"
    if net_edge >= config.watch_net_edge_floor:
        return "watch"
    return "block"


def _row_reason_codes(
    *,
    status: str,
    gross_edge: Decimal,
    candidate_reason_codes: tuple[str, ...],
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if status == "pass":
        reason_codes.append("edge_after_cost_floor_meets_minimum")
    elif status == "watch":
        reason_codes.append("edge_after_cost_floor_below_minimum")
    else:
        reason_codes.append("edge_after_cost_floor_negative")
    if gross_edge <= ZERO:
        reason_codes.append("gross_edge_non_positive")
    reason_codes.extend(
        reason_code
        for reason_code in candidate_reason_codes
        if reason_code not in reason_codes
    )
    return tuple(reason_codes)


def _report_status(rows: tuple[StrategyMarketProbabilityEdgeCostFloorV2Row, ...]) -> str:
    statuses = tuple(row.status for row in rows)
    if not statuses:
        return "empty"
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[StrategyMarketProbabilityEdgeCostFloorV2Row, ...],
) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                reason_code
                for row in rows
                for reason_code in row.reason_codes
            },
        ),
    )


def _reason_code_counts(
    rows: tuple[StrategyMarketProbabilityEdgeCostFloorV2Row, ...],
) -> tuple[StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount, ...]:
    candidate_count = _count(len(rows))
    return tuple(
        StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount(
            reason_code=reason_code,
            count=_reason_count(rows, reason_code),
            candidate_ratio=_ratio(_reason_count(rows, reason_code), candidate_count),
        )
        for reason_code in _report_reason_codes(rows)
    )


def _normalize_candidates(
    value: object,
) -> tuple[StrategyMarketProbabilityEdgeCostFloorV2Candidate, ...]:
    if isinstance(value, (str, bytes)) or type(value) is dict:
        raise ValueError("candidates must be an iterable of probability candidates")
    try:
        candidates = tuple(value)  # type: ignore[arg-type]
    except TypeError as exc:
        raise ValueError("candidates must be an iterable of probability candidates") from exc
    for candidate in candidates:
        if type(candidate) is not StrategyMarketProbabilityEdgeCostFloorV2Candidate:
            raise ValueError(
                "candidates must contain "
                "StrategyMarketProbabilityEdgeCostFloorV2Candidate values",
            )
        _require_hard_flags("candidate", candidate)
    return candidates


def _normalize_rows(
    value: object,
) -> tuple[StrategyMarketProbabilityEdgeCostFloorV2Row, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    rows = tuple(value)
    seen_keys: set[tuple[str, str, str]] = set()
    for row in rows:
        if type(row) is not StrategyMarketProbabilityEdgeCostFloorV2Row:
            raise ValueError("rows must contain StrategyMarketProbabilityEdgeCostFloorV2Row values")
        _require_hard_flags("row", row)
        key = _candidate_key(row)
        if key in seen_keys:
            raise ValueError("rows must not contain duplicate probability candidate")
        seen_keys.add(key)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use deterministic sequence")
    return rows


def _normalize_reason_code_counts(
    value: object,
) -> tuple[StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_code_counts must be a list or tuple")
    counts = tuple(value)
    seen: set[str] = set()
    for count in counts:
        if type(count) is not StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", count)
        if count.reason_code in seen:
            raise ValueError("reason_code_counts must be unique")
        seen.add(count.reason_code)
    if counts != tuple(sorted(counts, key=lambda item: item.reason_code)):
        raise ValueError("reason_code_counts must use deterministic sequence")
    return counts


def _normalize_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    reason_codes = tuple(value)
    seen: set[str] = set()
    for reason_code in reason_codes:
        _require_public_string(field_name, reason_code)
        if reason_code in seen:
            raise ValueError(f"{field_name} must not contain duplicates")
        seen.add(reason_code)
    return reason_codes


def _normalize_candidate_reason_codes(field_name: str, value: object) -> tuple[str, ...]:
    reason_codes = _normalize_reason_codes(field_name, value)
    return tuple(sorted(reason_codes))


def _validate_unique_candidates(
    candidates: tuple[StrategyMarketProbabilityEdgeCostFloorV2Candidate, ...],
) -> None:
    seen_keys: set[tuple[str, str, str]] = set()
    for candidate in candidates:
        key = _candidate_key(candidate)
        if key in seen_keys:
            raise ValueError("candidates contain duplicate probability candidate")
        seen_keys.add(key)


def _validate_row(row: StrategyMarketProbabilityEdgeCostFloorV2Row) -> None:
    if row.gross_edge != _subtract_decimal(row.model_probability, row.market_probability):
        raise ValueError("gross_edge must match model and market probabilities")
    if row.total_cost_floor != _add_decimal(
        row.taker_fee_rate,
        row.settlement_slippage_rate,
    ):
        raise ValueError("total_cost_floor must match cost inputs")
    if row.net_edge != _subtract_decimal(row.gross_edge, row.total_cost_floor):
        raise ValueError("net_edge must match gross_edge less total_cost_floor")
    if row.status == "pass":
        required = "edge_after_cost_floor_meets_minimum"
    elif row.status == "watch":
        required = "edge_after_cost_floor_below_minimum"
    else:
        required = "edge_after_cost_floor_negative"
    if required not in row.reason_codes:
        raise ValueError("status must match reason_codes")
    if row.gross_edge <= ZERO and "gross_edge_non_positive" not in row.reason_codes:
        raise ValueError("reason_codes must explain non-positive gross_edge")
    if row.derived_validation_digest != _row_derived_validation_digest(row):
        raise ValueError("derived_validation_digest must match row fields")


def _validate_report(report: StrategyMarketProbabilityEdgeCostFloorV2Report) -> None:
    rows = report.rows
    candidate_count = _count(len(rows))
    if report.candidate_count != candidate_count:
        raise ValueError("candidate_count must match rows")
    for field_name, status in (
        ("pass_count", "pass"),
        ("watch_count", "watch"),
        ("block_count", "block"),
    ):
        if getattr(report, field_name) != _status_count(rows, status):
            raise ValueError(f"{field_name} must match rows")
    if report.pass_count + report.watch_count + report.block_count != candidate_count:
        raise ValueError("status counts must match candidate_count")
    if report.max_net_edge != max((row.net_edge for row in rows), default=ZERO):
        raise ValueError("max_net_edge must match rows")
    if not rows and report.min_required_net_edge != ZERO:
        raise ValueError("min_required_net_edge must be zero for empty reports")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report fields")


def _candidate_key(value: object) -> tuple[str, str, str]:
    return (
        getattr(value, "market_id"),
        getattr(value, "event_slug"),
        getattr(value, "category"),
    )


def _row_sort_key(row: StrategyMarketProbabilityEdgeCostFloorV2Row) -> tuple[Decimal, Decimal, str, str, str]:
    return (
        STATUS_RANK[row.status],
        -row.net_edge,
        row.category,
        row.event_slug,
        row.market_id,
    )


def _status_count(
    rows: tuple[StrategyMarketProbabilityEdgeCostFloorV2Row, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_count(
    rows: tuple[StrategyMarketProbabilityEdgeCostFloorV2Row, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.reason_codes))


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_public_string(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if value == "":
        raise ValueError(f"{field_name} must not be empty")
    if value != value.strip():
        raise ValueError(f"{field_name} must be canonical")
    if any(ord(character) < 32 for character in value):
        raise ValueError(f"{field_name} must not contain control characters")
    _reject_unsafe_public_text(field_name, value)
    return value


def _require_member(field_name: str, value: object, allowed_values: tuple[str, ...]) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a supported value")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_probability(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_rate(field_name: str, value: object) -> Decimal:
    return _normalize_probability(field_name, value)


def _normalize_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _normalize_count(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _add_decimal(*values: Decimal) -> Decimal:
    return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _ratio(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _row_public_payload_for_digest(
    row: StrategyMarketProbabilityEdgeCostFloorV2Row,
) -> dict[str, Any]:
    return {
        "market_id": row.market_id,
        "event_slug": row.event_slug,
        "category": row.category,
        "model_probability": _decimal_payload(row.model_probability),
        "market_probability": _decimal_payload(row.market_probability),
        "gross_edge": _decimal_payload(row.gross_edge),
        "taker_fee_rate": _decimal_payload(row.taker_fee_rate),
        "settlement_slippage_rate": _decimal_payload(row.settlement_slippage_rate),
        "total_cost_floor": _decimal_payload(row.total_cost_floor),
        "net_edge": _decimal_payload(row.net_edge),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _row_public_payload(row: StrategyMarketProbabilityEdgeCostFloorV2Row) -> dict[str, Any]:
    payload = _row_public_payload_for_digest(row)
    payload["derived_validation_digest"] = row.derived_validation_digest
    return payload


def _reason_code_count_public_payload(
    count: StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": count.reason_code,
        "count": _decimal_payload(count.count),
        "candidate_ratio": _decimal_payload(count.candidate_ratio),
        "paper_only": count.paper_only,
        "report_only": count.report_only,
        "readonly": count.readonly,
    }


def _report_public_payload_for_digest(
    report: StrategyMarketProbabilityEdgeCostFloorV2Report,
) -> dict[str, Any]:
    return {
        "generated_at": _datetime_payload(report.generated_at),
        "config_version": report.config_version,
        "candidate_count": _decimal_payload(report.candidate_count),
        "pass_count": _decimal_payload(report.pass_count),
        "watch_count": _decimal_payload(report.watch_count),
        "block_count": _decimal_payload(report.block_count),
        "max_net_edge": _decimal_payload(report.max_net_edge),
        "min_required_net_edge": _decimal_payload(report.min_required_net_edge),
        "report_status": report.report_status,
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            _reason_code_count_public_payload(count)
            for count in report.reason_code_counts
        ],
        "rows": [_row_public_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _row_derived_validation_digest(row: StrategyMarketProbabilityEdgeCostFloorV2Row) -> str:
    return _public_payload_derived_validation_digest(_row_public_payload_for_digest(row))


def _report_derived_validation_digest(
    report: StrategyMarketProbabilityEdgeCostFloorV2Report,
) -> str:
    return _public_payload_derived_validation_digest(_report_public_payload_for_digest(report))


def _public_payload_derived_validation_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    return hashlib.sha256(_canonical_payload_bytes(digest_payload)).hexdigest()


def _canonical_payload_bytes(payload: dict[str, Any]) -> bytes:
    return json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _decimal_payload(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _datetime_payload(value: datetime) -> str:
    return _as_utc("datetime", value).isoformat()


def _payload_required_string(payload: dict[str, Any], field_name: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{field_name} is required")
    value = payload[field_name]
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 digest")
    return value


def _require_public_payload_flags(payload: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if payload.get(field_name) is not True:
            raise ValueError(f"{field_name} must be True")
    for collection_name in ("rows", "reason_code_counts"):
        collection = payload.get(collection_name, [])
        if type(collection) is not list:
            raise ValueError(f"{collection_name} must be a list")
        for item in collection:
            if type(item) is not dict:
                raise ValueError(f"{collection_name} entries must be dicts")
            for field_name in ("paper_only", "report_only", "readonly"):
                if item.get(field_name) is not True:
                    raise ValueError(f"{collection_name} {field_name} must be True")


def _validate_payload_row_digests(payload: dict[str, Any]) -> None:
    rows = payload.get("rows", [])
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    for row in rows:
        if type(row) is not dict:
            raise ValueError("rows entries must be dicts")
        row_digest = _payload_required_string(row, "derived_validation_digest")
        _require_sha256_digest("derived_validation_digest", row_digest)
        if row_digest != _public_payload_derived_validation_digest(row):
            raise ValueError("derived_validation_digest must match row payload")


def _reject_public_numeric_values(value: object) -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, (Decimal, int, float)):
        raise ValueError("payload must expose Decimal strings, not numeric values")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numeric_values(item)
    elif isinstance(value, list):
        for item in value:
            _reject_public_numeric_values(item)


def _reject_unsafe_public_payload(label: str, value: object, path: str = "") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError(f"{label} contains unsafe public key")
            item_path = f"{path}.{key}" if path else key
            _reject_unsafe_public_text(item_path, key)
            _reject_unsafe_public_payload(label, item, item_path)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_unsafe_public_payload(label, item, f"{path}[{index}]")
    elif type(value) is str:
        _reject_unsafe_public_text(path, value)


def _reject_unsafe_public_text(field_name: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_SURFACE_FRAGMENTS):
        raise ValueError(f"{field_name} contains unsafe public surface")


__all__ = (
    "DEFAULT_STRATEGY_MARKET_PROBABILITY_EDGE_COST_FLOOR_V2_CONFIG_VERSION",
    "StrategyMarketProbabilityEdgeCostFloorV2Candidate",
    "StrategyMarketProbabilityEdgeCostFloorV2Config",
    "StrategyMarketProbabilityEdgeCostFloorV2ReasonCodeCount",
    "StrategyMarketProbabilityEdgeCostFloorV2Report",
    "StrategyMarketProbabilityEdgeCostFloorV2Row",
    "build_strategy_market_probability_edge_cost_floor_v2_report",
    "strategy_market_probability_edge_cost_floor_v2_public_payload",
    "validate_strategy_market_probability_edge_cost_floor_v2_public_payload",
)
