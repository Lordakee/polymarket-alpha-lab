"""Public probability and cost dislocation monitor report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_DISLOCATION_MONITOR_CONFIG_VERSION = (
    "research-market-probability-cost-dislocation-monitor-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)
STATUS_WEIGHT = {
    STATUS_BLOCK: Decimal("0.000000"),
    STATUS_WATCH: Decimal("1.000000"),
    STATUS_PASS: Decimal("2.000000"),
}

REASON_PREFIX = "probability_cost_dislocation_monitor_"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"
CLEAR_REASON = f"{REASON_PREFIX}clear"
PROBABILITY_GAP_WATCH_REASON = f"{REASON_PREFIX}probability_gap_watch"
PROBABILITY_GAP_BLOCK_REASON = f"{REASON_PREFIX}probability_gap_block"
COST_PRESSURE_WATCH_REASON = f"{REASON_PREFIX}cost_pressure_watch"
COST_PRESSURE_BLOCK_REASON = f"{REASON_PREFIX}cost_pressure_block"
NET_DISLOCATION_WATCH_REASON = f"{REASON_PREFIX}net_dislocation_watch"
NET_DISLOCATION_BLOCK_REASON = f"{REASON_PREFIX}net_dislocation_block"
DISLOCATION_SCORE_WATCH_REASON = f"{REASON_PREFIX}dislocation_score_watch"
DISLOCATION_SCORE_BLOCK_REASON = f"{REASON_PREFIX}dislocation_score_block"

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
PUBLIC_SIGNAL_REF_MARKER = "public-signal"


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "-", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("sour", "ce", "-", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    _join_parts("sub", "mit"),
    _join_parts("can", "cel"),
    _join_parts("li", "ve"),
    "://",
    "?",
)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostDislocationMonitorConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_DISLOCATION_MONITOR_CONFIG_VERSION
    )
    watch_probability_gap_ratio: Decimal = Decimal("0.050000")
    block_probability_gap_ratio: Decimal = Decimal("0.120000")
    watch_cost_pressure_ratio: Decimal = Decimal("0.030000")
    block_cost_pressure_ratio: Decimal = Decimal("0.080000")
    watch_net_dislocation_ratio: Decimal = Decimal("0.020000")
    block_net_dislocation_ratio: Decimal = Decimal("0.070000")
    watch_dislocation_score: Decimal = Decimal("0.300000")
    block_dislocation_score: Decimal = Decimal("0.700000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostDislocationMonitorConfig does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostDislocationMonitorConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_DISLOCATION_MONITOR_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_probability_gap_ratio",
            "block_probability_gap_ratio",
            "watch_cost_pressure_ratio",
            "block_cost_pressure_ratio",
            "watch_net_dislocation_ratio",
            "block_net_dislocation_ratio",
            "watch_dislocation_score",
            "block_dislocation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_probability_gap_ratio",
            self.watch_probability_gap_ratio,
            "block_probability_gap_ratio",
            self.block_probability_gap_ratio,
        )
        _require_less_than(
            "watch_cost_pressure_ratio",
            self.watch_cost_pressure_ratio,
            "block_cost_pressure_ratio",
            self.block_cost_pressure_ratio,
        )
        _require_less_than(
            "watch_net_dislocation_ratio",
            self.watch_net_dislocation_ratio,
            "block_net_dislocation_ratio",
            self.block_net_dislocation_ratio,
        )
        _require_less_than(
            "watch_dislocation_score",
            self.watch_dislocation_score,
            "block_dislocation_score",
            self.block_dislocation_score,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostDislocationMonitorInput:
    public_signal_ref: str
    observed_at: datetime
    estimated_probability: Decimal
    displayed_probability: Decimal
    fee_ratio: Decimal
    spread_ratio: Decimal
    slippage_ratio: Decimal
    confidence_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostDislocationMonitorInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostDislocationMonitorInput,
            "input",
        )
        object.__setattr__(
            self,
            "public_signal_ref",
            _require_public_label("public_signal_ref", self.public_signal_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "estimated_probability",
            "displayed_probability",
            "fee_ratio",
            "spread_ratio",
            "slippage_ratio",
            "confidence_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostDislocationMonitorRow:
    public_signal_ref: str
    observed_at: datetime
    estimated_probability: Decimal
    displayed_probability: Decimal
    probability_gap_ratio: Decimal
    fee_ratio: Decimal
    spread_ratio: Decimal
    slippage_ratio: Decimal
    cost_pressure_ratio: Decimal
    net_dislocation_ratio: Decimal
    confidence_ratio: Decimal
    dislocation_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostDislocationMonitorRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostDislocationMonitorRow,
            "row",
        )
        object.__setattr__(
            self,
            "public_signal_ref",
            _require_public_label("public_signal_ref", self.public_signal_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "estimated_probability",
            "displayed_probability",
            "probability_gap_ratio",
            "fee_ratio",
            "spread_ratio",
            "slippage_ratio",
            "cost_pressure_ratio",
            "net_dislocation_ratio",
            "confidence_ratio",
            "dislocation_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostDislocationMonitorReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    probability_gap_watch_count: Decimal
    cost_pressure_watch_count: Decimal
    net_dislocation_watch_count: Decimal
    max_probability_gap_ratio: Decimal
    max_cost_pressure_ratio: Decimal
    max_net_dislocation_ratio: Decimal
    average_dislocation_score: Decimal | None
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketProbabilityCostDislocationMonitorRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostDislocationMonitorReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostDislocationMonitorReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "probability_gap_watch_count",
            "cost_pressure_watch_count",
            "net_dislocation_watch_count",
            "max_probability_gap_ratio",
            "max_cost_pressure_ratio",
            "max_net_dislocation_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if self.average_dislocation_score is not None:
            object.__setattr__(
                self,
                "average_dislocation_score",
                _require_ratio_decimal(
                    "average_dislocation_score",
                    self.average_dislocation_score,
                ),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(
                "reason_codes",
                self.reason_codes,
                allow_empty=False,
            ),
        )
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _validate_report(self)
        if self.derived_validation_digest != _report_derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def public_payload(self) -> dict[str, Any]:
        return research_market_probability_cost_dislocation_monitor_public_payload(self)


def build_research_market_probability_cost_dislocation_monitor_report(
    inputs: Iterable[ResearchMarketProbabilityCostDislocationMonitorInput],
    *,
    config: ResearchMarketProbabilityCostDislocationMonitorConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilityCostDislocationMonitorReport:
    if type(config) is not ResearchMarketProbabilityCostDislocationMonitorConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilityCostDislocationMonitorConfig",
        )
    _require_hard_flags("config", config)
    generated_at = _as_utc("generated_at", generated_at)
    normalized = _normalize_inputs(inputs, generated_at)
    rows = tuple(
        sorted(
            (_row_for_input(item, config=config) for item in normalized),
            key=_row_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at,
        "config_version": config.config_version,
        "input_count": _decimal_count(len(normalized)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "probability_gap_watch_count": _threshold_at_least_count(
            rows,
            "probability_gap_ratio",
            config.watch_probability_gap_ratio,
        ),
        "cost_pressure_watch_count": _threshold_at_least_count(
            rows,
            "cost_pressure_ratio",
            config.watch_cost_pressure_ratio,
        ),
        "net_dislocation_watch_count": _threshold_at_least_count(
            rows,
            "net_dislocation_ratio",
            config.watch_net_dislocation_ratio,
        ),
        "max_probability_gap_ratio": _max_decimal(rows, "probability_gap_ratio"),
        "max_cost_pressure_ratio": _max_decimal(rows, "cost_pressure_ratio"),
        "max_net_dislocation_ratio": _max_decimal(rows, "net_dislocation_ratio"),
        "average_dislocation_score": _average_decimal(
            row.dislocation_score for row in rows
        ),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketProbabilityCostDislocationMonitorReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_market_probability_cost_dislocation_monitor_public_payload(
    report: ResearchMarketProbabilityCostDislocationMonitorReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketProbabilityCostDislocationMonitorReport:
        raise ValueError(
            "report must be a ResearchMarketProbabilityCostDislocationMonitorReport",
        )
    _require_hard_flags("report", report)
    _validate_report(report)
    if report.derived_validation_digest != _report_derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")
    payload = _json_ready(report)
    if type(payload) is not dict:
        raise ValueError("public_payload must be a JSON object")
    _require_hard_flags("public_payload", _DictFlags(payload))
    _reject_unsafe_public_payload("public_payload", payload)
    return payload


def research_market_probability_cost_dislocation_monitor_digest(
    report: ResearchMarketProbabilityCostDislocationMonitorReport,
) -> str:
    if type(report) is not ResearchMarketProbabilityCostDislocationMonitorReport:
        raise ValueError(
            "report must be a ResearchMarketProbabilityCostDislocationMonitorReport",
        )
    return research_market_probability_cost_dislocation_monitor_public_payload(report)[
        "derived_validation_digest"
    ]


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


def _row_for_input(
    item: ResearchMarketProbabilityCostDislocationMonitorInput,
    *,
    config: ResearchMarketProbabilityCostDislocationMonitorConfig,
) -> ResearchMarketProbabilityCostDislocationMonitorRow:
    probability_gap_ratio = _absolute_delta(
        item.estimated_probability,
        item.displayed_probability,
    )
    cost_pressure_ratio = _sum_ratio(
        item.fee_ratio,
        item.spread_ratio,
        item.slippage_ratio,
    )
    net_dislocation_ratio = _net_after_cost(
        probability_gap_ratio,
        cost_pressure_ratio,
    )
    dislocation_score = _capped_ratio(
        net_dislocation_ratio,
        config.block_net_dislocation_ratio,
    )
    component_codes = _component_reason_codes(
        probability_gap_ratio=probability_gap_ratio,
        cost_pressure_ratio=cost_pressure_ratio,
        net_dislocation_ratio=net_dislocation_ratio,
        dislocation_score=dislocation_score,
        config=config,
    )
    status = _row_status(component_codes)
    return ResearchMarketProbabilityCostDislocationMonitorRow(
        public_signal_ref=item.public_signal_ref,
        observed_at=item.observed_at,
        estimated_probability=item.estimated_probability,
        displayed_probability=item.displayed_probability,
        probability_gap_ratio=probability_gap_ratio,
        fee_ratio=item.fee_ratio,
        spread_ratio=item.spread_ratio,
        slippage_ratio=item.slippage_ratio,
        cost_pressure_ratio=cost_pressure_ratio,
        net_dislocation_ratio=net_dislocation_ratio,
        confidence_ratio=item.confidence_ratio,
        dislocation_score=dislocation_score,
        status=status,
        reason_codes=_row_reason_codes(status, component_codes, item.reason_codes),
    )


def _component_reason_codes(
    *,
    probability_gap_ratio: Decimal,
    cost_pressure_ratio: Decimal,
    net_dislocation_ratio: Decimal,
    dislocation_score: Decimal,
    config: ResearchMarketProbabilityCostDislocationMonitorConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if probability_gap_ratio >= config.block_probability_gap_ratio:
        codes.append(PROBABILITY_GAP_BLOCK_REASON)
    elif probability_gap_ratio >= config.watch_probability_gap_ratio:
        codes.append(PROBABILITY_GAP_WATCH_REASON)
    if cost_pressure_ratio >= config.block_cost_pressure_ratio:
        codes.append(COST_PRESSURE_BLOCK_REASON)
    elif cost_pressure_ratio >= config.watch_cost_pressure_ratio:
        codes.append(COST_PRESSURE_WATCH_REASON)
    if net_dislocation_ratio >= config.block_net_dislocation_ratio:
        codes.append(NET_DISLOCATION_BLOCK_REASON)
    elif net_dislocation_ratio >= config.watch_net_dislocation_ratio:
        codes.append(NET_DISLOCATION_WATCH_REASON)
    if dislocation_score >= config.block_dislocation_score:
        codes.append(DISLOCATION_SCORE_BLOCK_REASON)
    elif dislocation_score >= config.watch_dislocation_score:
        codes.append(DISLOCATION_SCORE_WATCH_REASON)
    return tuple(codes)


def _row_status(component_codes: tuple[str, ...]) -> str:
    if any(code.endswith("_block") for code in component_codes):
        return STATUS_BLOCK
    if any(code.endswith("_watch") for code in component_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _row_reason_codes(
    status: str,
    component_codes: tuple[str, ...],
    input_codes: tuple[str, ...],
) -> tuple[str, ...]:
    if status == STATUS_PASS:
        codes = (CLEAR_REASON,)
    else:
        codes = tuple(f"input_{code}" for code in input_codes) + component_codes
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(set(codes))),
        allow_empty=False,
    )


def _report_status(
    rows: tuple[ResearchMarketProbabilityCostDislocationMonitorRow, ...],
) -> str:
    if not rows or any(row.status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityCostDislocationMonitorRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (NO_INPUTS_REASON,)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted({code for row in rows for code in row.reason_codes})),
        allow_empty=False,
    )


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityCostDislocationMonitorRow, ...],
) -> tuple[ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counts = Counter(code for row in rows for code in row.reason_codes)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount(
            reason_code=code,
            count=_decimal_count(count),
            row_ratio=_safe_divide(_decimal_count(count), row_count),
        )
        for code, count in sorted(counts.items())
    )


def _normalize_inputs(
    inputs: Iterable[ResearchMarketProbabilityCostDislocationMonitorInput],
    generated_at: datetime,
) -> tuple[ResearchMarketProbabilityCostDislocationMonitorInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for item in normalized:
        if type(item) is not ResearchMarketProbabilityCostDislocationMonitorInput:
            raise ValueError(
                "inputs must contain ResearchMarketProbabilityCostDislocationMonitorInput",
            )
        _require_hard_flags("input", item)
        if item.observed_at > generated_at:
            raise ValueError("observed_at must not be after generated_at")
        if item.public_signal_ref in seen_refs:
            raise ValueError("public_signal_ref must be unique")
        seen_refs.add(item.public_signal_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchMarketProbabilityCostDislocationMonitorRow],
) -> tuple[ResearchMarketProbabilityCostDislocationMonitorRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    for row in normalized:
        if type(row) is not ResearchMarketProbabilityCostDislocationMonitorRow:
            raise ValueError(
                "rows must contain ResearchMarketProbabilityCostDislocationMonitorRow",
            )
        _require_hard_flags("row", row)
        _validate_row(row)
    return tuple(sorted(normalized, key=_row_key))


def _normalize_reason_code_counts(
    items: Iterable[ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount],
) -> tuple[ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount, ...]:
    if isinstance(items, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        normalized = tuple(items)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for item in normalized:
        if type(item) is not ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", item)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _row_key(
    row: ResearchMarketProbabilityCostDislocationMonitorRow,
) -> tuple[Decimal, Decimal, str]:
    return (STATUS_WEIGHT[row.status], -row.dislocation_score, row.public_signal_ref)


def _status_count(
    rows: tuple[ResearchMarketProbabilityCostDislocationMonitorRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.status == status))


def _threshold_at_least_count(
    rows: tuple[ResearchMarketProbabilityCostDislocationMonitorRow, ...],
    field_name: str,
    threshold: Decimal,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if getattr(row, field_name) >= threshold))


def _average_decimal(values: Iterable[Decimal]) -> Decimal | None:
    normalized = tuple(values)
    if not normalized:
        return None
    return _safe_divide(sum(normalized, ZERO), _decimal_count(len(normalized)))


def _max_decimal(
    rows: tuple[ResearchMarketProbabilityCostDislocationMonitorRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return _require_nonnegative_decimal(
        field_name,
        max(getattr(row, field_name) for row in rows),
    )


def _validate_row(row: ResearchMarketProbabilityCostDislocationMonitorRow) -> None:
    if row.probability_gap_ratio != _absolute_delta(
        row.estimated_probability,
        row.displayed_probability,
    ):
        raise ValueError("probability_gap_ratio must match probabilities")
    if row.cost_pressure_ratio != _sum_ratio(
        row.fee_ratio,
        row.spread_ratio,
        row.slippage_ratio,
    ):
        raise ValueError("cost_pressure_ratio must match fee spread and slippage")
    if row.net_dislocation_ratio != _net_after_cost(
        row.probability_gap_ratio,
        row.cost_pressure_ratio,
    ):
        raise ValueError("net_dislocation_ratio must match probability gap after cost")
    if row.status == STATUS_PASS and row.reason_codes != (CLEAR_REASON,):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_BLOCK and not any(
        code.endswith("_block") for code in row.reason_codes
    ):
        raise ValueError("status must match reason_codes")
    if row.status == STATUS_WATCH and not any(
        code.endswith("_watch") for code in row.reason_codes
    ):
        raise ValueError("status must match reason_codes")


def _validate_report(
    report: ResearchMarketProbabilityCostDislocationMonitorReport,
) -> None:
    rows = report.rows
    if rows != tuple(sorted(rows, key=_row_key)):
        raise ValueError("rows must be deterministic")
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    if report.pass_count + report.watch_count + report.block_count != report.row_count:
        raise ValueError("status counts must match row_count")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")
    if report.max_probability_gap_ratio != _max_decimal(rows, "probability_gap_ratio"):
        raise ValueError("max_probability_gap_ratio must match rows")
    if report.max_cost_pressure_ratio != _max_decimal(rows, "cost_pressure_ratio"):
        raise ValueError("max_cost_pressure_ratio must match rows")
    if report.max_net_dislocation_ratio != _max_decimal(rows, "net_dislocation_ratio"):
        raise ValueError("max_net_dislocation_ratio must match rows")
    if report.average_dislocation_score != _average_decimal(
        row.dislocation_score for row in rows
    ):
        raise ValueError("average_dislocation_score must match rows")


def _absolute_delta(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        delta = abs(left - right)
    return _require_ratio_decimal("probability_gap_ratio", delta)


def _sum_ratio(*values: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        total = sum(values, ZERO)
    return _require_ratio_decimal("cost_pressure_ratio", total)


def _net_after_cost(probability_gap_ratio: Decimal, cost_pressure_ratio: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        value = probability_gap_ratio - cost_pressure_ratio
    if value < ZERO:
        value = ZERO
    return _require_ratio_decimal("net_dislocation_ratio", value)


def _capped_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    if numerator >= denominator:
        return ONE
    return _safe_divide(numerator, denominator)


def _safe_divide(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    with localcontext(DECIMAL_CONTEXT):
        return _require_ratio_decimal("ratio", numerator / denominator)


def _report_derived_validation_digest(
    report: ResearchMarketProbabilityCostDislocationMonitorReport,
) -> str:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return _derived_validation_digest(values)


def _derived_validation_digest(values: dict[str, object]) -> str:
    payload = _json_ready(values)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    _reject_unsafe_public_payload("digest", payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: object) -> object:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if type(value) is Decimal:
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, Decimal):
        raise ValueError("JSON Decimal value must be exactly Decimal")
    if type(value) is datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, datetime):
        raise ValueError("JSON datetime value must be exactly datetime")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is bool:
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) is str:
        return value
    if isinstance(value, dict):
        ready: dict[str, object] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _normalize_reason_codes(
    field_name: str,
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError(f"{field_name} must be a list or tuple")
    codes = tuple(value)
    if not allow_empty and not codes:
        raise ValueError(f"{field_name} must not be empty")
    for code in codes:
        _require_reason_code(field_name, code)
    if len(set(codes)) != len(codes):
        raise ValueError(f"{field_name} must be unique")
    if tuple(sorted(codes)) != codes:
        raise ValueError(f"{field_name} must be sorted")
    return codes


def _require_reason_code(field_name: str, value: object) -> None:
    if type(value) is not str or not value or value.strip() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if value.lower() != value:
        raise ValueError(f"{field_name} must contain canonical reason codes")
    if not all(character.islower() or character.isdigit() or character == "_" for character in value):
        raise ValueError(f"{field_name} must contain canonical reason codes")
    _reject_unsafe_public_string(field_name, value)
    if not (
        value.startswith(REASON_PREFIX)
        or value.startswith("public_")
        or value.startswith("input_public_")
    ):
        raise ValueError(f"{field_name} must contain public monitor reason codes")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "-"):
            raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_public_string(field_name, value)
    if field_name == "public_signal_ref" and PUBLIC_SIGNAL_REF_MARKER not in value:
        raise ValueError(f"{field_name} must be a public synthetic signal reference")
    return value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _normalize_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return decimal_value


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    with localcontext(DECIMAL_CONTEXT):
        try:
            return value.quantize(QUANTUM)
        except InvalidOperation as exc:
            raise ValueError("Decimal value is outside supported precision") from exc


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_less_than(
    lower_name: str,
    lower: Decimal,
    upper_name: str,
    upper: Decimal,
) -> None:
    if lower >= upper:
        raise ValueError(f"{lower_name} must be less than {upper_name}")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")


def _require_hard_flags(label: str, value: object) -> None:
    for flag_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, flag_name, None) is not True:
            raise ValueError(f"{label} {flag_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_string(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_string(label, key)
            _reject_unsafe_public_payload(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)


def _reject_unsafe_public_string(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_DISLOCATION_MONITOR_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketProbabilityCostDislocationMonitorConfig",
    "ResearchMarketProbabilityCostDislocationMonitorInput",
    "ResearchMarketProbabilityCostDislocationMonitorReasonCodeCount",
    "ResearchMarketProbabilityCostDislocationMonitorReport",
    "ResearchMarketProbabilityCostDislocationMonitorRow",
    "build_research_market_probability_cost_dislocation_monitor_report",
    "research_market_probability_cost_dislocation_monitor_digest",
    "research_market_probability_cost_dislocation_monitor_public_payload",
)
