"""Report-only probability exit-cost tail reducer."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, localcontext
from hashlib import sha256
import json
from typing import Any


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_EXIT_COST_TAIL_CONFIG_VERSION",
    "ResearchMarketProbabilityExitCostTailConfig",
    "ResearchMarketProbabilityExitCostTailInput",
    "ResearchMarketProbabilityExitCostTailReasonCodeCount",
    "ResearchMarketProbabilityExitCostTailReport",
    "ResearchMarketProbabilityExitCostTailRow",
    "build_research_market_probability_exit_cost_tail_report",
    "research_market_probability_exit_cost_tail_report_payload",
)


DEFAULT_RESEARCH_MARKET_PROBABILITY_EXIT_COST_TAIL_CONFIG_VERSION = (
    "research-market-probability-exit-cost-tail-report-v1"
)
DECIMAL_CONTEXT = Context(prec=64)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_MISSING_INPUTS = "missing_probability_exit_cost_tail_inputs"
REASON_PASS = "probability_exit_cost_tail_pass"
REASON_WATCH = "probability_exit_cost_tail_watch"
REASON_BLOCK = "probability_exit_cost_tail_block"
REASON_EDGE_NON_POSITIVE = "model_probability_not_above_market_probability"
REASON_NET_BUFFER_WATCH = "net_probability_tail_buffer_watch"
REASON_NET_BUFFER_BLOCK = "net_probability_tail_buffer_block"
REASON_TOTAL_COST_WATCH = "total_exit_cost_tail_watch"
REASON_TOTAL_COST_BLOCK = "total_exit_cost_tail_block"
REASON_TAIL_COST_TO_EDGE_WATCH = "tail_cost_to_edge_ratio_watch"
REASON_TAIL_COST_TO_EDGE_BLOCK = "tail_cost_to_edge_ratio_block"
REASON_PROBABILITY_TAIL_WATCH = "probability_tail_pressure_watch"
REASON_PROBABILITY_TAIL_BLOCK = "probability_tail_pressure_block"
REASON_CODES = (
    REASON_MISSING_INPUTS,
    REASON_PASS,
    REASON_WATCH,
    REASON_BLOCK,
    REASON_EDGE_NON_POSITIVE,
    REASON_NET_BUFFER_WATCH,
    REASON_NET_BUFFER_BLOCK,
    REASON_TOTAL_COST_WATCH,
    REASON_TOTAL_COST_BLOCK,
    REASON_TAIL_COST_TO_EDGE_WATCH,
    REASON_TAIL_COST_TO_EDGE_BLOCK,
    REASON_PROBABILITY_TAIL_WATCH,
    REASON_PROBABILITY_TAIL_BLOCK,
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
    _join_parts("candidate", "_", "id"),
    "credential",
    _join_parts("d", "s", "n"),
    _join_parts("exec", "ution"),
    _join_parts("live", "_", "trading"),
    _join_parts("mar", "ket", "_", "id"),
    _join_parts("mar", "ket", "_", "slug"),
    _join_parts("private", "_", "key"),
    _join_parts("que", "stion"),
    _join_parts("raw", "_", "candidate"),
    _join_parts("raw", "_", "market"),
    "secret",
    _join_parts("source", "_", "text"),
    _join_parts("source", "_", "url"),
    _join_parts("table", "_", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
)


@dataclass(frozen=True)
class ResearchMarketProbabilityExitCostTailConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_EXIT_COST_TAIL_CONFIG_VERSION
    )
    pass_net_probability_after_tail_rate: Decimal = Decimal("0.030000")
    watch_net_probability_after_tail_rate: Decimal = Decimal("0.005000")
    watch_total_exit_cost_tail_rate: Decimal = Decimal("0.035000")
    block_total_exit_cost_tail_rate: Decimal = Decimal("0.080000")
    watch_tail_cost_to_edge_ratio: Decimal = Decimal("0.500000")
    block_tail_cost_to_edge_ratio: Decimal = Decimal("1.000000")
    watch_probability_tail_risk_rate: Decimal = Decimal("0.100000")
    block_probability_tail_risk_rate: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityExitCostTailConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityExitCostTailConfig, "config")
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_EXIT_COST_TAIL_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_net_probability_after_tail_rate",
            "watch_net_probability_after_tail_rate",
            "watch_total_exit_cost_tail_rate",
            "block_total_exit_cost_tail_rate",
            "watch_tail_cost_to_edge_ratio",
            "block_tail_cost_to_edge_ratio",
            "watch_probability_tail_risk_rate",
            "block_probability_tail_risk_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.pass_net_probability_after_tail_rate
            < self.watch_net_probability_after_tail_rate
        ):
            raise ValueError(
                "pass_net_probability_after_tail_rate must be at least "
                "watch_net_probability_after_tail_rate",
            )
        _require_ascending(
            "total_exit_cost_tail_rate",
            self.watch_total_exit_cost_tail_rate,
            self.block_total_exit_cost_tail_rate,
        )
        _require_ascending(
            "tail_cost_to_edge_ratio",
            self.watch_tail_cost_to_edge_ratio,
            self.block_tail_cost_to_edge_ratio,
        )
        _require_ascending(
            "probability_tail_risk_rate",
            self.watch_probability_tail_risk_rate,
            self.block_probability_tail_risk_rate,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityExitCostTailInput:
    private_research_reference: str
    observed_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    expected_exit_cost_rate: Decimal
    tail_exit_cost_rate: Decimal
    probability_tail_risk_rate: Decimal
    cost_uncertainty_buffer_rate: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityExitCostTailInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityExitCostTailInput, "input")
        _require_private_reference(
            "private_research_reference",
            self.private_research_reference,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "expected_exit_cost_rate",
            "tail_exit_cost_rate",
            "cost_uncertainty_buffer_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "probability_tail_risk_rate",
            _probability_decimal(
                "probability_tail_risk_rate",
                self.probability_tail_risk_rate,
            ),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityExitCostTailRow:
    signal_digest: str
    observed_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    expected_exit_cost_rate: Decimal
    tail_exit_cost_rate: Decimal
    probability_tail_risk_rate: Decimal
    cost_uncertainty_buffer_rate: Decimal
    total_exit_cost_tail_rate: Decimal
    net_probability_after_tail_rate: Decimal
    tail_cost_to_edge_ratio: Decimal
    tail_cost_buffer_coverage_ratio: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityExitCostTailRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityExitCostTailRow, "row")
        _require_sha256_digest("signal_digest", self.signal_digest)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_probability_edge",
            "expected_exit_cost_rate",
            "tail_exit_cost_rate",
            "probability_tail_risk_rate",
            "cost_uncertainty_buffer_rate",
            "total_exit_cost_tail_rate",
            "tail_cost_to_edge_ratio",
            "tail_cost_buffer_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_probability_after_tail_rate",
            _decimal("net_probability_after_tail_rate", self.net_probability_after_tail_rate),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row_consistency(self)
        _set_or_validate_digest(self, "row")
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityExitCostTailReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityExitCostTailReasonCodeCount does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityExitCostTailReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _count_decimal("count", self.count))
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityExitCostTailReport:
    generated_at: datetime
    config_version: str
    status: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_gross_probability_edge: Decimal
    max_total_exit_cost_tail_rate: Decimal
    min_net_probability_after_tail_rate: Decimal
    max_tail_cost_to_edge_ratio: Decimal
    max_probability_tail_risk_rate: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketProbabilityExitCostTailReasonCodeCount, ...]
    rows: tuple[ResearchMarketProbabilityExitCostTailRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityExitCostTailReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketProbabilityExitCostTailReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_EXIT_COST_TAIL_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_status("status", self.status)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_gross_probability_edge",
            "max_total_exit_cost_tail_rate",
            "min_net_probability_after_tail_rate",
            "max_tail_cost_to_edge_ratio",
            "max_probability_tail_risk_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        _set_or_validate_digest(self, "report")
        _validate_report_consistency(self)
        _reject_unsafe_public_payload("report", self)


def build_research_market_probability_exit_cost_tail_report(
    inputs: Iterable[ResearchMarketProbabilityExitCostTailInput],
    *,
    generated_at: datetime,
    config: ResearchMarketProbabilityExitCostTailConfig | None = None,
) -> ResearchMarketProbabilityExitCostTailReport:
    generated_at_utc = _as_utc("generated_at", generated_at)
    active_config = ResearchMarketProbabilityExitCostTailConfig() if config is None else config
    if type(active_config) is not ResearchMarketProbabilityExitCostTailConfig:
        raise ValueError("config must be ResearchMarketProbabilityExitCostTailConfig")
    _require_hard_flags("config", active_config)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=active_config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    status = _report_status(rows)
    return ResearchMarketProbabilityExitCostTailReport(
        generated_at=generated_at_utc,
        config_version=active_config.config_version,
        status=status,
        input_count=_decimal_from_count(len(rows)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_gross_probability_edge=_mean_decimal(
            row.gross_probability_edge for row in rows
        ),
        max_total_exit_cost_tail_rate=max(
            (row.total_exit_cost_tail_rate for row in rows),
            default=ZERO,
        ),
        min_net_probability_after_tail_rate=min(
            (row.net_probability_after_tail_rate for row in rows),
            default=ZERO,
        ),
        max_tail_cost_to_edge_ratio=max(
            (row.tail_cost_to_edge_ratio for row in rows),
            default=ZERO,
        ),
        max_probability_tail_risk_rate=max(
            (row.probability_tail_risk_rate for row in rows),
            default=ZERO,
        ),
        reason_codes=_report_reason_codes(rows, status),
        reason_code_counts=_reason_code_counts(rows),
        rows=rows,
    )


def research_market_probability_exit_cost_tail_report_payload(
    report: ResearchMarketProbabilityExitCostTailReport | Mapping[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketProbabilityExitCostTailReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready_without_digest_validation(report)
        _require_payload_digest(payload)
    elif type(report) is dict:
        _require_hard_flags("payload", _MappingFlags(report))
        _reject_public_numerics(report)
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        payload = _json_ready_mapping(report)
        _require_payload_digest(payload)
    else:
        raise ValueError(
            "report must be a ResearchMarketProbabilityExitCostTailReport",
        )
    return _freeze_json_object(payload)


class FrozenJsonObject(dict[str, Any]):
    def __init__(self, value: dict[str, Any]) -> None:
        super().__init__(value)

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("payload is immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("payload is immutable")

    def clear(self) -> None:
        raise TypeError("payload is immutable")

    def pop(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("payload is immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("payload is immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("payload is immutable")

    def __ior__(self, other: object) -> "FrozenJsonObject":
        raise TypeError("payload is immutable")


class FrozenJsonArray(tuple[Any, ...]):
    def __eq__(self, other: object) -> bool:
        if isinstance(other, (list, tuple)):
            return tuple(self) == tuple(other)
        return False

    def append(self, value: Any) -> None:
        raise TypeError("payload is immutable")

    def extend(self, values: Any) -> None:
        raise TypeError("payload is immutable")


@dataclass(frozen=True)
class _MappingFlags:
    value: Mapping[str, Any]

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
    item: ResearchMarketProbabilityExitCostTailInput,
    *,
    config: ResearchMarketProbabilityExitCostTailConfig,
) -> ResearchMarketProbabilityExitCostTailRow:
    gross_probability_edge = _quantize(item.model_probability - item.market_probability)
    if gross_probability_edge < ZERO:
        gross_probability_edge = ZERO
    total_exit_cost_tail_rate = _quantize(
        item.expected_exit_cost_rate
        + item.tail_exit_cost_rate
        + item.cost_uncertainty_buffer_rate,
    )
    net_probability_after_tail_rate = _quantize(
        gross_probability_edge - total_exit_cost_tail_rate,
    )
    tail_cost_to_edge_ratio = _safe_ratio(
        total_exit_cost_tail_rate,
        gross_probability_edge,
    )
    tail_cost_buffer_coverage_ratio = _safe_ratio(
        gross_probability_edge,
        total_exit_cost_tail_rate,
    )
    reason_codes = _row_reason_codes(
        gross_probability_edge=gross_probability_edge,
        net_probability_after_tail_rate=net_probability_after_tail_rate,
        total_exit_cost_tail_rate=total_exit_cost_tail_rate,
        tail_cost_to_edge_ratio=tail_cost_to_edge_ratio,
        probability_tail_risk_rate=item.probability_tail_risk_rate,
        config=config,
    )
    return ResearchMarketProbabilityExitCostTailRow(
        signal_digest=_private_reference_digest(item.private_research_reference),
        observed_at=item.observed_at,
        model_probability=item.model_probability,
        market_probability=item.market_probability,
        gross_probability_edge=gross_probability_edge,
        expected_exit_cost_rate=item.expected_exit_cost_rate,
        tail_exit_cost_rate=item.tail_exit_cost_rate,
        probability_tail_risk_rate=item.probability_tail_risk_rate,
        cost_uncertainty_buffer_rate=item.cost_uncertainty_buffer_rate,
        total_exit_cost_tail_rate=total_exit_cost_tail_rate,
        net_probability_after_tail_rate=net_probability_after_tail_rate,
        tail_cost_to_edge_ratio=tail_cost_to_edge_ratio,
        tail_cost_buffer_coverage_ratio=tail_cost_buffer_coverage_ratio,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    gross_probability_edge: Decimal,
    net_probability_after_tail_rate: Decimal,
    total_exit_cost_tail_rate: Decimal,
    tail_cost_to_edge_ratio: Decimal,
    probability_tail_risk_rate: Decimal,
    config: ResearchMarketProbabilityExitCostTailConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    if gross_probability_edge <= ZERO:
        detail_reasons.append(REASON_EDGE_NON_POSITIVE)
    detail_reasons.extend(
        _low_value_reason(
            value=net_probability_after_tail_rate,
            watch_value=config.pass_net_probability_after_tail_rate,
            block_value=config.watch_net_probability_after_tail_rate,
            watch_reason=REASON_NET_BUFFER_WATCH,
            block_reason=REASON_NET_BUFFER_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=total_exit_cost_tail_rate,
            watch_value=config.watch_total_exit_cost_tail_rate,
            block_value=config.block_total_exit_cost_tail_rate,
            watch_reason=REASON_TOTAL_COST_WATCH,
            block_reason=REASON_TOTAL_COST_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=tail_cost_to_edge_ratio,
            watch_value=config.watch_tail_cost_to_edge_ratio,
            block_value=config.block_tail_cost_to_edge_ratio,
            watch_reason=REASON_TAIL_COST_TO_EDGE_WATCH,
            block_reason=REASON_TAIL_COST_TO_EDGE_BLOCK,
        ),
    )
    detail_reasons.extend(
        _high_value_reason(
            value=probability_tail_risk_rate,
            watch_value=config.watch_probability_tail_risk_rate,
            block_value=config.block_probability_tail_risk_rate,
            watch_reason=REASON_PROBABILITY_TAIL_WATCH,
            block_reason=REASON_PROBABILITY_TAIL_BLOCK,
        ),
    )
    if any(reason.endswith("_block") for reason in detail_reasons) or (
        REASON_EDGE_NON_POSITIVE in detail_reasons
    ):
        return _normalize_reason_codes((REASON_BLOCK, *detail_reasons))
    if detail_reasons:
        return _normalize_reason_codes((REASON_WATCH, *detail_reasons))
    return (REASON_PASS,)


def _low_value_reason(
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value < block_value:
        return (block_reason,)
    if value < watch_value:
        return (watch_reason,)
    return ()


def _high_value_reason(
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> tuple[str, ...]:
    if value >= block_value:
        return (block_reason,)
    if value >= watch_value:
        return (watch_reason,)
    return ()


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if reason_codes[0] == REASON_BLOCK:
        return STATUS_BLOCK
    if reason_codes[0] == REASON_WATCH:
        return STATUS_WATCH
    return STATUS_PASS


def _report_status(rows: tuple[ResearchMarketProbabilityExitCostTailRow, ...]) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityExitCostTailRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons: set[str] = set()
    for row in rows:
        if row.status == status:
            reasons.update(row.reason_codes)
    return _normalize_reason_codes(tuple(sorted(reasons, key=REASON_CODES.index)))


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityExitCostTailRow, ...],
) -> tuple[ResearchMarketProbabilityExitCostTailReasonCodeCount, ...]:
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchMarketProbabilityExitCostTailReasonCodeCount(
            reason_code=reason_code,
            count=count,
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: REASON_CODES.index(item[0]),
        )
    )


def _row_sort_key(
    row: ResearchMarketProbabilityExitCostTailRow,
) -> tuple[Decimal, Decimal, Decimal, datetime, str]:
    return (
        STATUS_SORT_RANK[row.status],
        -row.tail_cost_to_edge_ratio,
        row.net_probability_after_tail_rate,
        row.observed_at,
        row.signal_digest,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketProbabilityExitCostTailInput],
) -> tuple[ResearchMarketProbabilityExitCostTailInput, ...]:
    if isinstance(inputs, (str, bytes, dict)):
        raise ValueError("inputs must be an iterable of input rows")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable of input rows") from exc
    seen: set[tuple[str, datetime]] = set()
    for item in normalized:
        if type(item) is not ResearchMarketProbabilityExitCostTailInput:
            raise ValueError(
                "inputs must contain ResearchMarketProbabilityExitCostTailInput",
            )
        _require_hard_flags("input", item)
        key = (item.private_research_reference, item.observed_at)
        if key in seen:
            raise ValueError("inputs must be unique by private reference and time")
        seen.add(key)
    return normalized


def _normalize_rows(
    rows: object,
) -> tuple[ResearchMarketProbabilityExitCostTailRow, ...]:
    if not isinstance(rows, tuple):
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketProbabilityExitCostTailRow:
            raise ValueError("rows must contain ResearchMarketProbabilityExitCostTailRow")
    return rows


def _normalize_reason_code_counts(
    counts: object,
) -> tuple[ResearchMarketProbabilityExitCostTailReasonCodeCount, ...]:
    if not isinstance(counts, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    seen: set[str] = set()
    for item in counts:
        if type(item) is not ResearchMarketProbabilityExitCostTailReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityExitCostTailReasonCodeCount",
            )
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must be unique by reason_code")
        seen.add(item.reason_code)
    expected = tuple(sorted(counts, key=lambda item: REASON_CODES.index(item.reason_code)))
    if counts != expected:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return counts


def _normalize_reason_codes(reason_codes: object) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, tuple):
        raise ValueError("reason_codes must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code("reason_code", reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    return tuple(sorted(normalized, key=REASON_CODES.index))


def _validate_row_consistency(row: ResearchMarketProbabilityExitCostTailRow) -> None:
    expected_edge = _quantize(row.model_probability - row.market_probability)
    if expected_edge < ZERO:
        expected_edge = ZERO
    expected_total = _quantize(
        row.expected_exit_cost_rate
        + row.tail_exit_cost_rate
        + row.cost_uncertainty_buffer_rate,
    )
    expected_net = _quantize(expected_edge - expected_total)
    expected_ratio = _safe_ratio(expected_total, expected_edge)
    expected_coverage = _safe_ratio(expected_edge, expected_total)
    if row.gross_probability_edge != expected_edge:
        raise ValueError("gross_probability_edge must match row inputs")
    if row.total_exit_cost_tail_rate != expected_total:
        raise ValueError("total_exit_cost_tail_rate must match row inputs")
    if row.net_probability_after_tail_rate != expected_net:
        raise ValueError("net_probability_after_tail_rate must match row inputs")
    if row.tail_cost_to_edge_ratio != expected_ratio:
        raise ValueError("tail_cost_to_edge_ratio must match row inputs")
    if row.tail_cost_buffer_coverage_ratio != expected_coverage:
        raise ValueError("tail_cost_buffer_coverage_ratio must match row inputs")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketProbabilityExitCostTailReport,
) -> None:
    if report.input_count != _decimal_from_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_gross_probability_edge != _mean_decimal(
        row.gross_probability_edge for row in report.rows
    ):
        raise ValueError("average_gross_probability_edge must match rows")
    if report.max_total_exit_cost_tail_rate != max(
        (row.total_exit_cost_tail_rate for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_total_exit_cost_tail_rate must match rows")
    if report.min_net_probability_after_tail_rate != min(
        (row.net_probability_after_tail_rate for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("min_net_probability_after_tail_rate must match rows")
    if report.max_tail_cost_to_edge_ratio != max(
        (row.tail_cost_to_edge_ratio for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_tail_cost_to_edge_ratio must match rows")
    if report.max_probability_tail_risk_rate != max(
        (row.probability_tail_risk_rate for row in report.rows),
        default=ZERO,
    ):
        raise ValueError("max_probability_tail_risk_rate must match rows")
    expected_status = _report_status(report.rows)
    if report.status != expected_status:
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows):
        raise ValueError("reason_code_counts must match rows")


def _status_count(
    rows: tuple[ResearchMarketProbabilityExitCostTailRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_count(sum(ONE for row in rows if row.status == status))


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    return _quantize(sum(items, ZERO) / _decimal_from_count(len(items)))


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        if numerator == ZERO:
            return ZERO
        return Decimal("1000000.000000")
    return _quantize(numerator / denominator)


def _decimal_from_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _private_reference_digest(value: str) -> str:
    _require_private_reference("private_research_reference", value)
    return sha256(value.encode("utf-8")).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value:
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > 128:
        raise ValueError(f"{field_name} is too long")
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(character not in allowed for character in value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if len(value) > 4096:
        raise ValueError(f"{field_name} is too long")
    return value


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _probability_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(field_name, value)
    if decimal_value > ONE:
        raise ValueError(f"{field_name} must be at most 1.000000")
    return decimal_value


def _count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _nonnegative_decimal(field_name, value)
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole Decimal")
    return decimal_value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(QUANTUM)


def _require_ascending(name: str, watch_value: Decimal, block_value: Decimal) -> None:
    if block_value <= watch_value:
        raise ValueError(f"{name} block threshold must exceed watch threshold")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass/watch/block")


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or value not in REASON_CODE_SET:
        raise ValueError(f"{field_name} must be a supported reason code")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _set_or_validate_digest(value: object, label: str) -> None:
    current = getattr(value, "derived_validation_digest")
    if type(current) is not str:
        raise ValueError("derived_validation_digest must be a string")
    expected = _digest_for_public_object(value)
    if current == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_sha256_digest("derived_validation_digest", current)
    if current != expected:
        raise ValueError(f"derived_validation_digest does not match {label} payload")


def _digest_for_public_object(value: object) -> str:
    payload = _json_ready_without_digest_validation(value)
    payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        payload,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    canonical = json.dumps(
        payload_without_digest,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    expected = sha256(canonical.encode("utf-8")).hexdigest()
    if digest != expected:
        raise ValueError("derived_validation_digest does not match payload")


def _json_ready_without_digest_validation(value: object) -> dict[str, Any]:
    if not is_dataclass(value):
        raise ValueError("payload value must be a dataclass")
    ready = _json_ready(asdict(value))
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _json_ready_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    ready = _json_ready(value)
    if type(ready) is not dict:
        raise ValueError("payload must be a JSON object")
    return ready


def _json_ready(value: Any) -> Any:
    if type(value) is Decimal:
        return format(value, ".6f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if is_dataclass(value):
        return _json_ready(asdict(value))
    if isinstance(value, Mapping):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if type(value) in (str, bool) or value is None:
        return value
    raise ValueError(f"payload contains unsupported value {type(value).__name__}")


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numerics(item)
        return
    if type(value) in (Decimal, datetime, int, float):
        raise ValueError("public payload must use JSON-safe string numerics")


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if is_dataclass(value):
        for field in fields(value):
            if field.name == "derived_validation_digest":
                continue
            _reject_unsafe_public_fragment(f"{label}.{field.name}", field.name)
            _reject_unsafe_public_payload(
                f"{label}.{field.name}",
                getattr(value, field.name),
                allow_json_containers=allow_json_containers,
            )
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("public payload keys must be strings")
            _reject_unsafe_public_fragment(f"{label}.{key}", key)
            _reject_unsafe_public_payload(
                f"{label}.{key}",
                item,
                allow_json_containers=True,
            )
        return
    if isinstance(value, (list, tuple)):
        if not allow_json_containers and not isinstance(value, tuple):
            raise ValueError("public payload containers must be immutable")
        for item in value:
            _reject_unsafe_public_payload(
                label,
                item,
                allow_json_containers=allow_json_containers,
            )
        return
    if type(value) is str:
        _reject_unsafe_public_fragment(label, value)


def _reject_unsafe_public_fragment(label: str, value: str) -> None:
    lowered = value.lower()
    for fragment in UNSAFE_PUBLIC_FRAGMENTS:
        if fragment in lowered:
            raise ValueError(f"unsafe public field or value in {label}")
