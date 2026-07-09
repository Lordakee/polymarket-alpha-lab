"""Report-only probability liquidity decay floor checks."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import InitVar, asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_DECAY_FLOOR_CONFIG_VERSION = (
    "research-market-probability-liquidity-decay-floor-report-v1"
)

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_SORT_RANK = {STATUS_BLOCK: 0, STATUS_WATCH: 1, STATUS_PASS: 2}

PASS_REASON = "liquidity_decay_floor_pass"
WATCH_REASON = "liquidity_decay_floor_watch"
BLOCK_REASON = "liquidity_decay_floor_block"
FLOOR_EDGE_WATCH_REASON = "floor_edge_watch"
FLOOR_EDGE_BLOCK_REASON = "floor_edge_block"
LIQUIDITY_DECAY_WATCH_REASON = "liquidity_decay_watch"
LIQUIDITY_DECAY_BLOCK_REASON = "liquidity_decay_block"
FEE_DRAG_WATCH_REASON = "fee_drag_watch"
FEE_DRAG_BLOCK_REASON = "fee_drag_block"

REASON_CODE_SEQUENCE = (
    BLOCK_REASON,
    FLOOR_EDGE_BLOCK_REASON,
    LIQUIDITY_DECAY_BLOCK_REASON,
    FEE_DRAG_BLOCK_REASON,
    WATCH_REASON,
    FLOOR_EDGE_WATCH_REASON,
    LIQUIDITY_DECAY_WATCH_REASON,
    FEE_DRAG_WATCH_REASON,
    PASS_REASON,
)
REASON_CODE_SET = frozenset(REASON_CODE_SEQUENCE)

__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_DECAY_FLOOR_CONFIG_VERSION",
    "ResearchMarketProbabilityLiquidityDecayFloorConfig",
    "ResearchMarketProbabilityLiquidityDecayFloorInput",
    "ResearchMarketProbabilityLiquidityDecayFloorRow",
    "ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount",
    "ResearchMarketProbabilityLiquidityDecayFloorReport",
    "build_research_market_probability_liquidity_decay_floor_report",
    "research_market_probability_liquidity_decay_floor_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityDecayFloorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_DECAY_FLOOR_CONFIG_VERSION
    )
    watch_floor_probability_edge: Decimal = Decimal("0.020000")
    block_floor_probability_edge: Decimal = Decimal("0.000000")
    watch_liquidity_decay_score: Decimal = Decimal("0.400000")
    block_liquidity_decay_score: Decimal = Decimal("0.600000")
    watch_fee_probability_drag: Decimal = Decimal("0.015000")
    block_fee_probability_drag: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityLiquidityDecayFloorConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityDecayFloorConfig,
            "config",
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_DECAY_FLOOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_floor_probability_edge",
            "block_floor_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_delta(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "watch_liquidity_decay_score",
            "block_liquidity_decay_score",
            "watch_fee_probability_drag",
            "block_fee_probability_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        if self.block_floor_probability_edge >= self.watch_floor_probability_edge:
            raise ValueError(
                "block_floor_probability_edge must be below "
                "watch_floor_probability_edge",
            )
        if self.block_liquidity_decay_score <= self.watch_liquidity_decay_score:
            raise ValueError(
                "block_liquidity_decay_score must exceed "
                "watch_liquidity_decay_score",
            )
        if self.block_fee_probability_drag <= self.watch_fee_probability_drag:
            raise ValueError(
                "block_fee_probability_drag must exceed watch_fee_probability_drag",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityDecayFloorInput:
    case_digest: str
    research_probability: Decimal
    market_probability: Decimal
    depth_score: Decimal
    liquidity_score: Decimal
    freshness_score: Decimal
    fee_probability_drag: Decimal = ZERO
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityLiquidityDecayFloorInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityDecayFloorInput,
            "input",
        )
        _require_sha256_digest("case_digest", self.case_digest)
        for field_name in (
            "research_probability",
            "market_probability",
            "depth_score",
            "liquidity_score",
            "freshness_score",
            "fee_probability_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityDecayFloorRow:
    case_digest: str
    research_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    depth_score: Decimal
    liquidity_score: Decimal
    freshness_score: Decimal
    liquidity_decay_score: Decimal
    fee_probability_drag: Decimal
    floor_probability_edge: Decimal
    status: str
    reason_codes: tuple[str, ...]
    validation_config: InitVar[
        ResearchMarketProbabilityLiquidityDecayFloorConfig | None
    ] = None
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityLiquidityDecayFloorRow does not support "
            "subclassing",
        )

    def __post_init__(
        self,
        validation_config: ResearchMarketProbabilityLiquidityDecayFloorConfig | None,
    ) -> None:
        _require_exact_type(self, ResearchMarketProbabilityLiquidityDecayFloorRow, "row")
        active_config = (
            ResearchMarketProbabilityLiquidityDecayFloorConfig()
            if validation_config is None
            else validation_config
        )
        if type(active_config) is not ResearchMarketProbabilityLiquidityDecayFloorConfig:
            raise ValueError(
                "validation_config must be "
                "ResearchMarketProbabilityLiquidityDecayFloorConfig",
            )
        _require_hard_flags("validation_config", active_config)
        _require_sha256_digest("case_digest", self.case_digest)
        for field_name in (
            "research_probability",
            "market_probability",
            "depth_score",
            "liquidity_score",
            "freshness_score",
            "liquidity_decay_score",
            "fee_probability_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("gross_probability_edge", "floor_probability_edge"):
            object.__setattr__(
                self,
                field_name,
                _decimal_delta(field_name, getattr(self, field_name)),
            )
        _require_member("status", self.status, frozenset(STATUSES))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes),
        )
        _validate_row_consistency(self, config=active_config)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount:
    reason_code: str
    row_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount,
            "reason code count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "row_count",
            _count_decimal("row_count", self.row_count),
        )
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityLiquidityDecayFloorReport:
    generated_at: datetime
    config_version: str
    report_status: str
    case_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_gross_probability_edge: Decimal
    average_floor_probability_edge: Decimal
    min_floor_probability_edge: Decimal
    average_liquidity_decay_score: Decimal
    max_liquidity_decay_score: Decimal
    rows: tuple[ResearchMarketProbabilityLiquidityDecayFloorRow, ...]
    reason_code_counts: tuple[
        ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount,
        ...,
    ]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityLiquidityDecayFloorReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityLiquidityDecayFloorReport,
            "report",
        )
        object.__setattr__(
            self,
            "generated_at",
            _as_utc("generated_at", self.generated_at),
        )
        _require_public_identifier("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_DECAY_FLOOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        _require_member("report_status", self.report_status, frozenset(STATUSES))
        for field_name in (
            "case_count",
            "pass_count",
            "watch_count",
            "block_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_gross_probability_edge",
            "average_floor_probability_edge",
            "min_floor_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _decimal_delta(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_liquidity_decay_score",
            "max_liquidity_decay_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _unit_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        _validate_report_consistency(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _digest_for_value(_report_values_without_digest(self))
        if self.derived_validation_digest == "":
            object.__setattr__(self, "derived_validation_digest", expected_digest)
            return
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")


def build_research_market_probability_liquidity_decay_floor_report(
    rows: Iterable[ResearchMarketProbabilityLiquidityDecayFloorInput],
    *,
    generated_at: datetime,
    config: ResearchMarketProbabilityLiquidityDecayFloorConfig | None = None,
) -> ResearchMarketProbabilityLiquidityDecayFloorReport:
    """Build a deterministic readonly probability liquidity decay floor report."""

    active_config = (
        ResearchMarketProbabilityLiquidityDecayFloorConfig()
        if config is None
        else config
    )
    if type(active_config) is not ResearchMarketProbabilityLiquidityDecayFloorConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilityLiquidityDecayFloorConfig",
        )
    _require_hard_flags("config", active_config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(rows)
    report_rows = tuple(
        sorted(
            (_row_for_input(item, config=active_config) for item in normalized_inputs),
            key=_row_sort_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": active_config.config_version,
        "report_status": _report_status(report_rows),
        "case_count": _decimal_from_int(len(report_rows)),
        "pass_count": _status_count(report_rows, STATUS_PASS),
        "watch_count": _status_count(report_rows, STATUS_WATCH),
        "block_count": _status_count(report_rows, STATUS_BLOCK),
        "average_gross_probability_edge": _mean_decimal(
            row.gross_probability_edge for row in report_rows
        ),
        "average_floor_probability_edge": _mean_decimal(
            row.floor_probability_edge for row in report_rows
        ),
        "min_floor_probability_edge": min(
            (row.floor_probability_edge for row in report_rows),
            default=ZERO,
        ),
        "average_liquidity_decay_score": _mean_decimal(
            row.liquidity_decay_score for row in report_rows
        ),
        "max_liquidity_decay_score": max(
            (row.liquidity_decay_score for row in report_rows),
            default=ZERO,
        ),
        "rows": report_rows,
        "reason_code_counts": _reason_code_counts(report_rows),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketProbabilityLiquidityDecayFloorReport(
        **values,
        derived_validation_digest=_digest_for_value(values),
    )


def research_market_probability_liquidity_decay_floor_report_payload(
    report: ResearchMarketProbabilityLiquidityDecayFloorReport | Mapping[str, Any],
) -> "FrozenJsonObject":
    if type(report) is ResearchMarketProbabilityLiquidityDecayFloorReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _reject_unsafe_public_payload("payload", report, allow_json_containers=True)
        _reject_public_numerics(report)
        _require_hard_flags("payload", _MappingFlags(report))
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketProbabilityLiquidityDecayFloorReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_payload_digest(payload)
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("payload", payload, allow_json_containers=True)
    _reject_public_numerics(payload)
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


def _row_for_input(
    item: ResearchMarketProbabilityLiquidityDecayFloorInput,
    *,
    config: ResearchMarketProbabilityLiquidityDecayFloorConfig,
) -> ResearchMarketProbabilityLiquidityDecayFloorRow:
    gross_probability_edge = _quantize(
        item.research_probability - item.market_probability,
    )
    liquidity_decay_score = _liquidity_decay_score(item)
    floor_probability_edge = _floor_probability_edge(
        gross_probability_edge=gross_probability_edge,
        liquidity_decay_score=liquidity_decay_score,
        fee_probability_drag=item.fee_probability_drag,
    )
    reason_codes = _reason_codes_for_values(
        floor_probability_edge=floor_probability_edge,
        liquidity_decay_score=liquidity_decay_score,
        fee_probability_drag=item.fee_probability_drag,
        config=config,
    )
    return ResearchMarketProbabilityLiquidityDecayFloorRow(
        case_digest=item.case_digest,
        research_probability=item.research_probability,
        market_probability=item.market_probability,
        gross_probability_edge=gross_probability_edge,
        depth_score=item.depth_score,
        liquidity_score=item.liquidity_score,
        freshness_score=item.freshness_score,
        liquidity_decay_score=liquidity_decay_score,
        fee_probability_drag=item.fee_probability_drag,
        floor_probability_edge=floor_probability_edge,
        status=_status_from_reason_codes(reason_codes),
        reason_codes=reason_codes,
        validation_config=config,
    )


def _liquidity_decay_score(
    item: ResearchMarketProbabilityLiquidityDecayFloorInput
    | ResearchMarketProbabilityLiquidityDecayFloorRow,
) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return _quantize(
            ((ONE - item.depth_score) + (ONE - item.liquidity_score) + (ONE - item.freshness_score))
            / Decimal("3"),
        )


def _floor_probability_edge(
    *,
    gross_probability_edge: Decimal,
    liquidity_decay_score: Decimal,
    fee_probability_drag: Decimal,
) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        decay_drag = abs(gross_probability_edge) * liquidity_decay_score
        return _quantize(gross_probability_edge - fee_probability_drag - decay_drag)


def _reason_codes_for_values(
    *,
    floor_probability_edge: Decimal,
    liquidity_decay_score: Decimal,
    fee_probability_drag: Decimal,
    config: ResearchMarketProbabilityLiquidityDecayFloorConfig,
) -> tuple[str, ...]:
    detail_reasons: list[str] = []
    has_block = False

    if floor_probability_edge <= config.block_floor_probability_edge:
        detail_reasons.append(FLOOR_EDGE_BLOCK_REASON)
        has_block = True
    elif floor_probability_edge <= config.watch_floor_probability_edge:
        detail_reasons.append(FLOOR_EDGE_WATCH_REASON)

    if liquidity_decay_score >= config.block_liquidity_decay_score:
        detail_reasons.append(LIQUIDITY_DECAY_BLOCK_REASON)
        has_block = True
    elif liquidity_decay_score >= config.watch_liquidity_decay_score:
        detail_reasons.append(LIQUIDITY_DECAY_WATCH_REASON)

    if fee_probability_drag >= config.block_fee_probability_drag:
        detail_reasons.append(FEE_DRAG_BLOCK_REASON)
        has_block = True
    elif fee_probability_drag >= config.watch_fee_probability_drag:
        detail_reasons.append(FEE_DRAG_WATCH_REASON)

    if has_block:
        return _normalize_reason_codes((BLOCK_REASON, *detail_reasons))
    if detail_reasons:
        return _normalize_reason_codes((WATCH_REASON, *detail_reasons))
    return (PASS_REASON,)


def _status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if BLOCK_REASON in reason_codes:
        return STATUS_BLOCK
    if WATCH_REASON in reason_codes:
        return STATUS_WATCH
    return STATUS_PASS


def _validate_row_consistency(
    row: ResearchMarketProbabilityLiquidityDecayFloorRow,
    *,
    config: ResearchMarketProbabilityLiquidityDecayFloorConfig,
) -> None:
    if row.gross_probability_edge != _quantize(
        row.research_probability - row.market_probability,
    ):
        raise ValueError("gross_probability_edge must match probabilities")
    if row.liquidity_decay_score != _liquidity_decay_score(row):
        raise ValueError("liquidity_decay_score must match input scores")
    if row.floor_probability_edge != _floor_probability_edge(
        gross_probability_edge=row.gross_probability_edge,
        liquidity_decay_score=row.liquidity_decay_score,
        fee_probability_drag=row.fee_probability_drag,
    ):
        raise ValueError("floor_probability_edge must match decay floor fields")
    expected_reason_codes = _reason_codes_for_values(
        floor_probability_edge=row.floor_probability_edge,
        liquidity_decay_score=row.liquidity_decay_score,
        fee_probability_drag=row.fee_probability_drag,
        config=config,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match decay floor fields")
    if row.status != _status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_report_consistency(
    report: ResearchMarketProbabilityLiquidityDecayFloorReport,
) -> None:
    rows = report.rows
    if report.case_count != _decimal_from_int(len(rows)):
        raise ValueError("case_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.average_gross_probability_edge != _mean_decimal(
        row.gross_probability_edge for row in rows
    ):
        raise ValueError("average_gross_probability_edge must match rows")
    if report.average_floor_probability_edge != _mean_decimal(
        row.floor_probability_edge for row in rows
    ):
        raise ValueError("average_floor_probability_edge must match rows")
    if report.min_floor_probability_edge != min(
        (row.floor_probability_edge for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_floor_probability_edge must match rows")
    if report.average_liquidity_decay_score != _mean_decimal(
        row.liquidity_decay_score for row in rows
    ):
        raise ValueError("average_liquidity_decay_score must match rows")
    if report.max_liquidity_decay_score != max(
        (row.liquidity_decay_score for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_liquidity_decay_score must match rows")
    if report.report_status != _report_status(rows):
        raise ValueError("report_status must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _normalize_inputs(
    value: Iterable[ResearchMarketProbabilityLiquidityDecayFloorInput],
) -> tuple[ResearchMarketProbabilityLiquidityDecayFloorInput, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of decay floor inputs")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of decay floor inputs") from exc
    seen_case_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketProbabilityLiquidityDecayFloorInput:
            raise ValueError(
                "rows must contain ResearchMarketProbabilityLiquidityDecayFloorInput",
            )
        _require_hard_flags("input", row)
        if row.case_digest in seen_case_digests:
            raise ValueError("case_digest values must be unique")
        seen_case_digests.add(row.case_digest)
    return tuple(sorted(rows, key=lambda row: row.case_digest))


def _normalize_rows(
    value: Iterable[ResearchMarketProbabilityLiquidityDecayFloorRow],
) -> tuple[ResearchMarketProbabilityLiquidityDecayFloorRow, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("rows must be an iterable of decay floor rows")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("rows must be an iterable of decay floor rows") from exc
    seen_case_digests: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketProbabilityLiquidityDecayFloorRow:
            raise ValueError(
                "rows must contain ResearchMarketProbabilityLiquidityDecayFloorRow",
            )
        _require_hard_flags("row", row)
        if row.case_digest in seen_case_digests:
            raise ValueError("row case_digest values must be unique")
        seen_case_digests.add(row.case_digest)
    sorted_rows = tuple(sorted(rows, key=_row_sort_key))
    if rows != sorted_rows:
        raise ValueError("rows must be sorted deterministically")
    return rows


def _normalize_reason_code_counts(
    value: Iterable[ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount],
) -> tuple[ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen_reason_codes: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount",
            )
        _require_hard_flags("reason code count", row)
        if row.reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts reason_code values must be unique")
        seen_reason_codes.add(row.reason_code)
    sorted_rows = tuple(sorted(rows, key=_reason_code_count_sort_key))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted deterministically")
    return rows


def _normalize_reason_codes(value: Iterable[str]) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_codes must be an iterable of reason codes")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_codes must be an iterable of reason codes") from exc
    if not reason_codes:
        raise ValueError("reason_codes must not be empty")
    seen_reason_codes: set[str] = set()
    for reason_code in reason_codes:
        _require_reason_code("reason_codes", reason_code)
        if reason_code in seen_reason_codes:
            raise ValueError("reason_codes must be unique")
        seen_reason_codes.add(reason_code)
    sorted_reason_codes = tuple(
        sorted(reason_codes, key=lambda code: REASON_CODE_SEQUENCE.index(code))
    )
    if reason_codes != sorted_reason_codes:
        raise ValueError("reason_codes must be sorted deterministically")
    return reason_codes


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityLiquidityDecayFloorRow, ...],
) -> tuple[ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount, ...]:
    counts = {
        reason_code: sum(ONE for row in rows if reason_code in row.reason_codes)
        for reason_code in REASON_CODE_SEQUENCE
    }
    return tuple(
        ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount(
            reason_code=reason_code,
            row_count=row_count,
        )
        for reason_code, row_count in counts.items()
        if row_count != ZERO
    )


def _report_status(
    rows: tuple[ResearchMarketProbabilityLiquidityDecayFloorRow, ...],
) -> str:
    if any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketProbabilityLiquidityDecayFloorRow, ...],
    status: str,
) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row.status == status))


def _row_sort_key(row: ResearchMarketProbabilityLiquidityDecayFloorRow) -> tuple[object, ...]:
    return (
        STATUS_SORT_RANK[row.status],
        row.floor_probability_edge,
        -row.liquidity_decay_score,
        row.case_digest,
    )


def _reason_code_count_sort_key(
    row: ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount,
) -> int:
    return REASON_CODE_SEQUENCE.index(row.reason_code)


def _mean_decimal(values: Iterable[Decimal]) -> Decimal:
    items = tuple(values)
    if not items:
        return ZERO
    with localcontext() as context:
        context.prec = 64
        return _quantize(sum(items, ZERO) / Decimal(len(items)))


def _decimal_from_int(value: int) -> Decimal:
    return _count_decimal("count", Decimal(value))


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _unit_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _decimal_delta(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < Decimal("-1.000000") or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between negative one and one")
    return decimal_value


def _count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be a whole count")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    return _quantize(value)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext() as context:
            context.prec = 64
            return value.quantize(QUANTUM)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("decimal value must be finite and quantizable") from exc


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_IDENTIFIER_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a SHA-256 digest")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a reason code")
    _require_member(field_name, value, REASON_CODE_SET)
    return value


def _require_member(field_name: str, value: object, allowed_values: frozenset[str]) -> str:
    if type(value) is not str or value not in allowed_values:
        raise ValueError(f"{field_name} must be a known value")
    return value


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if _field_value(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


_MISSING = object()


def _field_value(value: object, field_name: str, *, default: object = _MISSING) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            if field.name == field_name:
                return getattr(value, field_name)
    if hasattr(value, field_name):
        return getattr(value, field_name)
    if default is not _MISSING:
        return default
    raise ValueError(f"{field_name} is required")


def _report_values_without_digest(
    report: ResearchMarketProbabilityLiquidityDecayFloorReport,
) -> dict[str, object]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _digest_for_value(value: object) -> str:
    ready = _json_ready(value)
    rendered = json.dumps(
        ready,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest_value = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest_value)
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    expected_digest = _digest_for_value(payload_without_digest)
    if digest_value != expected_digest:
        raise ValueError("derived_validation_digest must match payload fields")


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_payload_keys(
        "report payload",
        payload,
        _payload_keys(ResearchMarketProbabilityLiquidityDecayFloorReport),
    )
    _require_payload_flags("report payload", payload)
    generated_at = _datetime_string("generated_at", payload["generated_at"])
    if generated_at.isoformat() != payload["generated_at"]:
        raise ValueError("generated_at must use public payload schema")
    _require_public_identifier("config_version", payload["config_version"])
    if (
        payload["config_version"]
        != DEFAULT_RESEARCH_MARKET_PROBABILITY_LIQUIDITY_DECAY_FLOOR_CONFIG_VERSION
    ):
        raise ValueError("config_version must use public payload schema")
    if type(payload["report_status"]) is not str or payload["report_status"] not in STATUSES:
        raise ValueError("report_status must use public payload schema")
    case_count = _count_decimal_string("case_count", payload["case_count"])
    pass_count = _count_decimal_string("pass_count", payload["pass_count"])
    watch_count = _count_decimal_string("watch_count", payload["watch_count"])
    block_count = _count_decimal_string("block_count", payload["block_count"])
    average_gross_probability_edge = _delta_decimal_string(
        "average_gross_probability_edge",
        payload["average_gross_probability_edge"],
    )
    average_floor_probability_edge = _delta_decimal_string(
        "average_floor_probability_edge",
        payload["average_floor_probability_edge"],
    )
    min_floor_probability_edge = _delta_decimal_string(
        "min_floor_probability_edge",
        payload["min_floor_probability_edge"],
    )
    average_liquidity_decay_score = _unit_decimal_string(
        "average_liquidity_decay_score",
        payload["average_liquidity_decay_score"],
    )
    max_liquidity_decay_score = _unit_decimal_string(
        "max_liquidity_decay_score",
        payload["max_liquidity_decay_score"],
    )
    _require_sha256_digest(
        "derived_validation_digest",
        payload["derived_validation_digest"],
    )

    rows = _validate_public_rows_schema(payload["rows"])
    reason_code_counts = _validate_public_reason_code_counts_schema(
        payload["reason_code_counts"],
    )

    expected_report_status = STATUS_PASS
    if any(row["status"] == STATUS_BLOCK for row in rows):
        expected_report_status = STATUS_BLOCK
    elif any(row["status"] == STATUS_WATCH for row in rows):
        expected_report_status = STATUS_WATCH
    if payload["report_status"] != expected_report_status:
        raise ValueError("report_status must use public payload schema")
    if case_count != _decimal_from_int(len(rows)):
        raise ValueError("case_count must use public payload schema")
    if pass_count != _public_status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must use public payload schema")
    if watch_count != _public_status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must use public payload schema")
    if block_count != _public_status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must use public payload schema")
    if average_gross_probability_edge != _mean_decimal(
        row["gross_probability_edge"] for row in rows
    ):
        raise ValueError("average_gross_probability_edge must use public payload schema")
    if average_floor_probability_edge != _mean_decimal(
        row["floor_probability_edge"] for row in rows
    ):
        raise ValueError("average_floor_probability_edge must use public payload schema")
    if min_floor_probability_edge != min(
        (row["floor_probability_edge"] for row in rows),
        default=ZERO,
    ):
        raise ValueError("min_floor_probability_edge must use public payload schema")
    if average_liquidity_decay_score != _mean_decimal(
        row["liquidity_decay_score"] for row in rows
    ):
        raise ValueError("average_liquidity_decay_score must use public payload schema")
    if max_liquidity_decay_score != max(
        (row["liquidity_decay_score"] for row in rows),
        default=ZERO,
    ):
        raise ValueError("max_liquidity_decay_score must use public payload schema")
    if reason_code_counts != _public_reason_code_counts(rows):
        raise ValueError("reason_code_counts must use public payload schema")


def _validate_public_rows_schema(value: object) -> tuple[dict[str, Any], ...]:
    if type(value) is not list:
        raise ValueError("rows must use public payload schema")
    rows = tuple(_validate_public_row_schema(item) for item in value)
    seen_case_digests: set[str] = set()
    for row in rows:
        case_digest = row["case_digest"]
        if case_digest in seen_case_digests:
            raise ValueError("rows must use public payload schema")
        seen_case_digests.add(case_digest)
    if rows != tuple(sorted(rows, key=_public_row_sort_key)):
        raise ValueError("rows must use public payload schema")
    return rows


def _validate_public_row_schema(value: object) -> dict[str, Any]:
    row = _require_payload_object("row", value)
    _require_payload_keys(
        "row",
        row,
        _payload_keys(ResearchMarketProbabilityLiquidityDecayFloorRow),
    )
    _require_payload_flags("row", row)
    case_digest = _require_sha256_digest("case_digest", row["case_digest"])
    research_probability = _unit_decimal_string(
        "research_probability",
        row["research_probability"],
    )
    market_probability = _unit_decimal_string(
        "market_probability",
        row["market_probability"],
    )
    gross_probability_edge = _delta_decimal_string(
        "gross_probability_edge",
        row["gross_probability_edge"],
    )
    depth_score = _unit_decimal_string("depth_score", row["depth_score"])
    liquidity_score = _unit_decimal_string(
        "liquidity_score",
        row["liquidity_score"],
    )
    freshness_score = _unit_decimal_string(
        "freshness_score",
        row["freshness_score"],
    )
    liquidity_decay_score = _unit_decimal_string(
        "liquidity_decay_score",
        row["liquidity_decay_score"],
    )
    fee_probability_drag = _unit_decimal_string(
        "fee_probability_drag",
        row["fee_probability_drag"],
    )
    floor_probability_edge = _delta_decimal_string(
        "floor_probability_edge",
        row["floor_probability_edge"],
    )
    status_value = row["status"]
    if type(status_value) is not str or status_value not in STATUSES:
        raise ValueError("status must use public payload schema")
    status = status_value
    reason_codes = _reason_codes_from_payload(row["reason_codes"])

    if gross_probability_edge != _quantize(research_probability - market_probability):
        raise ValueError("gross_probability_edge must use public payload schema")
    expected_liquidity_decay_score = _quantize(
        ((ONE - depth_score) + (ONE - liquidity_score) + (ONE - freshness_score))
        / Decimal("3"),
    )
    if liquidity_decay_score != expected_liquidity_decay_score:
        raise ValueError("liquidity_decay_score must use public payload schema")
    if floor_probability_edge != _floor_probability_edge(
        gross_probability_edge=gross_probability_edge,
        liquidity_decay_score=liquidity_decay_score,
        fee_probability_drag=fee_probability_drag,
    ):
        raise ValueError("floor_probability_edge must use public payload schema")
    if status != _status_from_reason_codes(reason_codes):
        raise ValueError("status must use public payload schema")

    return {
        "case_digest": case_digest,
        "research_probability": research_probability,
        "market_probability": market_probability,
        "gross_probability_edge": gross_probability_edge,
        "depth_score": depth_score,
        "liquidity_score": liquidity_score,
        "freshness_score": freshness_score,
        "liquidity_decay_score": liquidity_decay_score,
        "fee_probability_drag": fee_probability_drag,
        "floor_probability_edge": floor_probability_edge,
        "status": status,
        "reason_codes": reason_codes,
    }


def _validate_public_reason_code_counts_schema(
    value: object,
) -> tuple[tuple[str, Decimal], ...]:
    if type(value) is not list:
        raise ValueError("reason_code_counts must use public payload schema")
    rows = tuple(_validate_public_reason_code_count_schema(item) for item in value)
    seen_reason_codes: set[str] = set()
    for reason_code, _row_count in rows:
        if reason_code in seen_reason_codes:
            raise ValueError("reason_code_counts must use public payload schema")
        seen_reason_codes.add(reason_code)
    if rows != tuple(sorted(rows, key=lambda item: REASON_CODE_SEQUENCE.index(item[0]))):
        raise ValueError("reason_code_counts must use public payload schema")
    return rows


def _validate_public_reason_code_count_schema(value: object) -> tuple[str, Decimal]:
    row = _require_payload_object("reason_code_count", value)
    _require_payload_keys(
        "reason_code_count",
        row,
        _payload_keys(ResearchMarketProbabilityLiquidityDecayFloorReasonCodeCount),
    )
    _require_payload_flags("reason_code_count", row)
    return (
        _require_reason_code("reason_code", row["reason_code"]),
        _count_decimal_string("row_count", row["row_count"]),
    )


def _public_reason_code_counts(
    rows: tuple[dict[str, Any], ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts = {
        reason_code: sum(ONE for row in rows if reason_code in row["reason_codes"])
        for reason_code in REASON_CODE_SEQUENCE
    }
    return tuple(
        (reason_code, row_count)
        for reason_code, row_count in counts.items()
        if row_count != ZERO
    )


def _public_status_count(rows: tuple[dict[str, Any], ...], status: str) -> Decimal:
    return _decimal_from_int(sum(1 for row in rows if row["status"] == status))


def _public_row_sort_key(row: dict[str, Any]) -> tuple[object, ...]:
    return (
        STATUS_SORT_RANK[row["status"]],
        row["floor_probability_edge"],
        -row["liquidity_decay_score"],
        row["case_digest"],
    )


def _payload_keys(expected_type: type[object]) -> frozenset[str]:
    return frozenset(field.name for field in fields(expected_type))


def _require_payload_object(label: str, value: object) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{label} must use public payload schema")
    return value


def _require_payload_keys(
    label: str,
    value: dict[str, Any],
    expected_keys: frozenset[str],
) -> None:
    if frozenset(value) != expected_keys:
        raise ValueError(f"{label} must use public payload schema")


def _require_payload_flags(label: str, value: dict[str, Any]) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if value.get(field_name) is not True:
            raise ValueError(f"{label} must use public payload schema")


def _reason_codes_from_payload(value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError("reason_codes must use public payload schema")
    return _normalize_reason_codes(value)


def _datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must use public payload schema")
    try:
        return _as_utc(field_name, datetime.fromisoformat(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must use public payload schema") from exc


def _count_decimal_string(field_name: str, value: object) -> Decimal:
    return _count_decimal(field_name, _decimal_string(field_name, value))


def _unit_decimal_string(field_name: str, value: object) -> Decimal:
    return _unit_decimal(field_name, _decimal_string(field_name, value))


def _delta_decimal_string(field_name: str, value: object) -> Decimal:
    return _decimal_delta(field_name, _decimal_string(field_name, value))


def _decimal_string(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    quantized_value = _quantize(decimal_value)
    if str(quantized_value) != value:
        raise ValueError(f"{field_name} must be a canonical Decimal string")
    return quantized_value


def _json_ready(value: object) -> object:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, float):
        raise ValueError("payload must not contain float values")
    return value


def _freeze_json_object(value: dict[str, Any]) -> FrozenJsonObject:
    return FrozenJsonObject({key: _freeze_json_value(item) for key, item in value.items()})


def _freeze_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _freeze_json_object(value)
    if isinstance(value, list):
        return FrozenJsonArray(_freeze_json_value(item) for item in value)
    return value


def _reject_public_numerics(value: object) -> None:
    if type(value) is bool or value is None or isinstance(value, str):
        return
    if type(value) is int or isinstance(value, float) or isinstance(value, Decimal):
        raise ValueError("public payload numeric values must be Decimal strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_payload(
    label: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    del allow_json_containers
    for fragment in _unsafe_fragments():
        if fragment in label.lower():
            raise ValueError("unsafe public payload field")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_payload(field.name, getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key).lower()
            if any(fragment in key_text for fragment in _unsafe_fragments()):
                raise ValueError("unsafe public payload field")
            _reject_unsafe_public_payload(key_text, item, allow_json_containers=True)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item, allow_json_containers=True)
        return
    if isinstance(value, str):
        lowered = value.lower()
        if any(fragment in lowered for fragment in _unsafe_fragments()):
            raise ValueError("unsafe public payload field")


def _unsafe_fragments() -> tuple[str, ...]:
    return (
        "_".join(("candidate", "id")),
        "candidate",
        "raw",
        "_".join(("raw", "candidate")),
        "_".join(("raw", "market")),
        "_".join(("market", "id")),
        "_".join(("market", "slug")),
        "slug",
        "question",
        "url",
        "://",
        "".join(("w", "ww.")),
        "".join(("sour", "ce")),
        "_".join(("source", "url")),
        "_".join(("source", "text")),
        "".join(("d", "s", "n")),
        "".join(("data", "base")),
        "_".join(("api", "key")),
        "".join(("cred", "ential")),
        "".join(("sec", "ret")),
        "".join(("exec", "ute")),
        "".join(("exec", "ution")),
        "table",
        "_".join(("table", "name")),
        "".join(("to", "ken")),
        "".join(("wal", "let")),
        "".join(("or", "der")),
        "".join(("tr", "ade")),
        "".join(("siz", "ing")),
        "".join(("reco", "mmendation")),
        "".join(("au", "th")),
        "".join(("net", "work")),
        "".join(("li", "ve")),
    )
