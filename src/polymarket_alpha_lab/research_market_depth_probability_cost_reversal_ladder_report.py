"""Report-only depth probability cost reversal ladder research checks."""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, DecimalException, localcontext
import hashlib
import json
import re
from typing import Any, Iterable


DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_COST_REVERSAL_LADDER_REPORT_CONFIG_VERSION = (
    "research-market-depth-probability-cost-reversal-ladder-report-v1"
)

STATUSES = ("pass", "watch", "block")
_STATUS_SET = frozenset(STATUSES)
_STATUS_WEIGHT = {"block": 0, "watch": 1, "pass": 2}
_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REASON_PRIORITY = (
    "no_depth_probability_cost_inputs",
    "probability_reversal_block",
    "depth_floor_block",
    "cost_drag_block",
    "probability_reversal_watch",
    "depth_floor_watch",
    "cost_drag_watch",
    "depth_probability_cost_ladder_pass",
)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


_UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("can", "didate"),
    _join_parts("ra", "w", "can", "didate"),
    _join_parts("ma", "rket", "id"),
    _join_parts("ma", "rket", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sou", "rce", "url"),
    _join_parts("sou", "rce", "text"),
    _join_parts("d", "s", "n"),
    _join_parts("tab", "le", "name"),
    _join_parts("tok", "en"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmendation"),
    _join_parts("net", "work"),
    _join_parts("live", "tra", "ding"),
    "://",
)
_UNSAFE_PUBLIC_SEPARATOR_RE = re.compile(r"[\s_.\-/]+")
_BLOCK_REASON_CODES = frozenset(
    reason_code for reason_code in _REASON_PRIORITY if reason_code.endswith("_block")
)
_WATCH_REASON_CODES = frozenset(
    reason_code for reason_code in _REASON_PRIORITY if reason_code.endswith("_watch")
)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityCostReversalLadderConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_COST_REVERSAL_LADDER_REPORT_CONFIG_VERSION
    )
    probability_reversal_watch_threshold: Decimal = Decimal("0.100000")
    probability_reversal_block_threshold: Decimal = Decimal("0.250000")
    min_pass_depth: Decimal = Decimal("1000.000000")
    min_watch_depth: Decimal = Decimal("250.000000")
    max_pass_cost_ratio: Decimal = Decimal("0.025000")
    max_watch_cost_ratio: Decimal = Decimal("0.075000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthProbabilityCostReversalLadderConfig does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthProbabilityCostReversalLadderConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_COST_REVERSAL_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "probability_reversal_watch_threshold",
            "probability_reversal_block_threshold",
            "max_pass_cost_ratio",
            "max_watch_cost_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("min_pass_depth", "min_watch_depth"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.probability_reversal_watch_threshold
            >= self.probability_reversal_block_threshold
        ):
            raise ValueError(
                "probability_reversal_watch_threshold must be below block threshold",
            )
        if self.min_pass_depth <= self.min_watch_depth:
            raise ValueError("min_pass_depth must exceed watch depth")
        if self.max_pass_cost_ratio >= self.max_watch_cost_ratio:
            raise ValueError("max_pass_cost_ratio must be below watch cost")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityCostReversalLadderInput:
    public_ladder_ref: str
    observed_at: datetime
    prior_probability: Decimal
    current_probability: Decimal
    available_depth: Decimal
    fee_ratio: Decimal
    spread_ratio: Decimal
    impact_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthProbabilityCostReversalLadderInput does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthProbabilityCostReversalLadderInput,
            "input",
        )
        _require_public_label("public_ladder_ref", self.public_ladder_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("prior_probability", "current_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "available_depth",
            _require_nonnegative_decimal("available_depth", self.available_depth),
        )
        for field_name in ("fee_ratio", "spread_ratio", "impact_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)
        _reject_unsafe_public_payload("input", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityCostReversalLadderRow:
    public_ladder_ref: str
    observed_at: datetime
    prior_probability: Decimal
    current_probability: Decimal
    probability_reversal: Decimal
    available_depth: Decimal
    fee_ratio: Decimal
    spread_ratio: Decimal
    impact_ratio: Decimal
    total_cost_ratio: Decimal
    probability_reversal_score: Decimal
    depth_risk_score: Decimal
    cost_risk_score: Decimal
    ladder_risk_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthProbabilityCostReversalLadderRow does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthProbabilityCostReversalLadderRow,
            "row",
        )
        _require_public_label("public_ladder_ref", self.public_ladder_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "prior_probability",
            "current_probability",
            "fee_ratio",
            "spread_ratio",
            "impact_ratio",
            "probability_reversal_score",
            "depth_risk_score",
            "cost_risk_score",
            "ladder_risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "probability_reversal",
            "available_depth",
            "total_cost_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount "
            "does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount,
            "reason code count",
        )
        _require_public_label("reason_code", self.reason_code)
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
        _require_hard_flags("reason code count", self)
        _reject_unsafe_public_payload("reason code count", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityCostReversalLadderReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_ladder_risk_score: Decimal
    max_ladder_risk_score: Decimal
    max_probability_reversal: Decimal
    max_total_cost_ratio: Decimal
    min_available_depth: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[
        ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount,
        ...,
    ]
    rows: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketDepthProbabilityCostReversalLadderReport does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthProbabilityCostReversalLadderReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_COST_REVERSAL_LADDER_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "average_ladder_risk_score",
            "max_ladder_risk_score",
            "max_probability_reversal",
            "max_total_cost_ratio",
            "min_available_depth",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
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
        if self.derived_validation_digest != _derived_validation_digest(self):
            raise ValueError("derived_validation_digest must match report payload")

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_depth_probability_cost_reversal_ladder_report_payload(self)


def build_research_market_depth_probability_cost_reversal_ladder_report(
    inputs: Iterable[ResearchMarketDepthProbabilityCostReversalLadderInput],
    *,
    config: ResearchMarketDepthProbabilityCostReversalLadderConfig,
    generated_at: datetime,
) -> ResearchMarketDepthProbabilityCostReversalLadderReport:
    if type(config) is not ResearchMarketDepthProbabilityCostReversalLadderConfig:
        raise ValueError(
            "config must be a ResearchMarketDepthProbabilityCostReversalLadderConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs, generated_at_utc)
    rows = tuple(
        sorted(
            (_row_for_input(item, config) for item in normalized_inputs),
            key=_row_key,
        ),
    )
    values: dict[str, object] = {
        "generated_at": generated_at_utc,
        "config_version": config.config_version,
        "input_count": _decimal_count(len(normalized_inputs)),
        "row_count": _decimal_count(len(rows)),
        "pass_count": _status_count(rows, "pass"),
        "watch_count": _status_count(rows, "watch"),
        "block_count": _status_count(rows, "block"),
        "average_ladder_risk_score": _average_ladder_risk_score(rows),
        "max_ladder_risk_score": _max_decimal(rows, "ladder_risk_score"),
        "max_probability_reversal": _max_decimal(rows, "probability_reversal"),
        "max_total_cost_ratio": _max_decimal(rows, "total_cost_ratio"),
        "min_available_depth": _min_decimal(rows, "available_depth"),
        "status": _report_status(rows),
        "reason_codes": _report_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    return ResearchMarketDepthProbabilityCostReversalLadderReport(
        **values,
        derived_validation_digest=_derived_validation_digest(values),
    )


def research_market_depth_probability_cost_reversal_ladder_report_payload(
    value: ResearchMarketDepthProbabilityCostReversalLadderReport | dict[str, Any],
) -> dict[str, Any]:
    if type(value) is ResearchMarketDepthProbabilityCostReversalLadderReport:
        _require_hard_flags("report", value)
        if value.derived_validation_digest != _derived_validation_digest(value):
            raise ValueError("derived_validation_digest must match report payload")
        payload = _json_ready(value)
    elif type(value) is dict:
        payload = _json_ready(value)
    else:
        raise ValueError(
            "value must be a ResearchMarketDepthProbabilityCostReversalLadderReport",
        )
    if type(payload) is not dict:
        raise ValueError("payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    _require_payload_digest(payload)
    return payload


def research_market_depth_probability_cost_reversal_ladder_report_digest(
    report: ResearchMarketDepthProbabilityCostReversalLadderReport,
) -> str:
    if type(report) is not ResearchMarketDepthProbabilityCostReversalLadderReport:
        raise ValueError(
            "report must be a ResearchMarketDepthProbabilityCostReversalLadderReport",
        )
    _require_hard_flags("report", report)
    if report.derived_validation_digest != _derived_validation_digest(report):
        raise ValueError("derived_validation_digest must match report payload")
    return report.derived_validation_digest


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
    item: ResearchMarketDepthProbabilityCostReversalLadderInput,
    config: ResearchMarketDepthProbabilityCostReversalLadderConfig,
) -> ResearchMarketDepthProbabilityCostReversalLadderRow:
    probability_reversal = _abs_decimal(item.current_probability - item.prior_probability)
    total_cost_ratio = _sum_decimal(item.fee_ratio, item.spread_ratio, item.impact_ratio)
    probability_reversal_score = _ratio_ladder_score(
        probability_reversal,
        config.probability_reversal_watch_threshold,
        config.probability_reversal_block_threshold,
    )
    depth_risk_score = _depth_ladder_score(
        item.available_depth,
        config.min_watch_depth,
        config.min_pass_depth,
    )
    cost_risk_score = _ratio_ladder_score(
        total_cost_ratio,
        config.max_pass_cost_ratio,
        config.max_watch_cost_ratio,
    )
    ladder_risk_score = max(
        probability_reversal_score,
        depth_risk_score,
        cost_risk_score,
    )
    reason_codes = _row_reason_codes(
        item=item,
        config=config,
        probability_reversal=probability_reversal,
        total_cost_ratio=total_cost_ratio,
    )
    return ResearchMarketDepthProbabilityCostReversalLadderRow(
        public_ladder_ref=item.public_ladder_ref,
        observed_at=item.observed_at,
        prior_probability=item.prior_probability,
        current_probability=item.current_probability,
        probability_reversal=probability_reversal,
        available_depth=item.available_depth,
        fee_ratio=item.fee_ratio,
        spread_ratio=item.spread_ratio,
        impact_ratio=item.impact_ratio,
        total_cost_ratio=total_cost_ratio,
        probability_reversal_score=probability_reversal_score,
        depth_risk_score=depth_risk_score,
        cost_risk_score=cost_risk_score,
        ladder_risk_score=ladder_risk_score,
        status=_row_status(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    item: ResearchMarketDepthProbabilityCostReversalLadderInput,
    config: ResearchMarketDepthProbabilityCostReversalLadderConfig,
    probability_reversal: Decimal,
    total_cost_ratio: Decimal,
) -> tuple[str, ...]:
    reason_codes: list[str] = []
    if probability_reversal >= config.probability_reversal_block_threshold:
        reason_codes.append("probability_reversal_block")
    elif probability_reversal >= config.probability_reversal_watch_threshold:
        reason_codes.append("probability_reversal_watch")

    if item.available_depth < config.min_watch_depth:
        reason_codes.append("depth_floor_block")
    elif item.available_depth < config.min_pass_depth:
        reason_codes.append("depth_floor_watch")

    if total_cost_ratio > config.max_watch_cost_ratio:
        reason_codes.append("cost_drag_block")
    elif total_cost_ratio > config.max_pass_cost_ratio:
        reason_codes.append("cost_drag_watch")

    if not reason_codes:
        reason_codes.append("depth_probability_cost_ladder_pass")
    for reason_code in item.reason_codes:
        reason_codes.append(f"input_{reason_code}")
    return tuple(reason_codes)


def _row_status(reason_codes: tuple[str, ...]) -> str:
    if any(reason_code in _BLOCK_REASON_CODES for reason_code in reason_codes):
        return "block"
    if any(reason_code in _WATCH_REASON_CODES for reason_code in reason_codes):
        return "watch"
    return "pass"


def _report_status(
    rows: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_depth_probability_cost_inputs",)
    seen: set[str] = set()
    reason_codes: list[str] = []
    for row in rows:
        for reason_code in row.reason_codes:
            if reason_code not in seen:
                seen.add(reason_code)
                reason_codes.append(reason_code)
    return tuple(sorted(reason_codes, key=_reason_key))


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...],
) -> tuple[ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount(
                reason_code="no_depth_probability_cost_inputs",
                count=_ONE,
                row_ratio=_ZERO,
            ),
        )
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = _quantize(counts.get(reason_code, _ZERO) + _ONE)
    row_count = _decimal_count(len(rows))
    return tuple(
        ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount(
            reason_code=reason_code,
            count=count,
            row_ratio=_safe_ratio(count, row_count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: _reason_key(item[0]))
    )


def _normalize_inputs(
    values: Iterable[ResearchMarketDepthProbabilityCostReversalLadderInput],
    generated_at: datetime,
) -> tuple[ResearchMarketDepthProbabilityCostReversalLadderInput, ...]:
    normalized: list[ResearchMarketDepthProbabilityCostReversalLadderInput] = []
    for value in values:
        if type(value) is not ResearchMarketDepthProbabilityCostReversalLadderInput:
            raise ValueError(
                "inputs must contain ResearchMarketDepthProbabilityCostReversalLadderInput",
            )
        _require_hard_flags("input", value)
        if value.observed_at > generated_at:
            raise ValueError("observed_at must not exceed generated_at")
        normalized.append(value)
    return tuple(normalized)


def _normalize_rows(
    values: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...],
) -> tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...]:
    if type(values) is not tuple:
        raise ValueError("rows must be a tuple")
    for value in values:
        if type(value) is not ResearchMarketDepthProbabilityCostReversalLadderRow:
            raise ValueError(
                "rows must contain ResearchMarketDepthProbabilityCostReversalLadderRow",
            )
        _require_hard_flags("row", value)
    return tuple(sorted(values, key=_row_key))


def _normalize_reason_code_counts(
    values: tuple[ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount, ...],
) -> tuple[ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for value in values:
        if (
            type(value)
            is not ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount
        ):
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount",
            )
        _require_hard_flags("reason code count", value)
    return tuple(sorted(values, key=lambda value: _reason_key(value.reason_code)))


def _validate_report(
    report: ResearchMarketDepthProbabilityCostReversalLadderReport,
) -> None:
    rows = report.rows
    if report.input_count != _decimal_count(len(rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _status_count(rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(rows, "block"):
        raise ValueError("block_count must match rows")
    if report.average_ladder_risk_score != _average_ladder_risk_score(rows):
        raise ValueError("average_ladder_risk_score must match rows")
    if report.max_ladder_risk_score != _max_decimal(rows, "ladder_risk_score"):
        raise ValueError("max_ladder_risk_score must match rows")
    if report.max_probability_reversal != _max_decimal(rows, "probability_reversal"):
        raise ValueError("max_probability_reversal must match rows")
    if report.max_total_cost_ratio != _max_decimal(rows, "total_cost_ratio"):
        raise ValueError("max_total_cost_ratio must match rows")
    if report.min_available_depth != _min_decimal(rows, "available_depth"):
        raise ValueError("min_available_depth must match rows")
    if report.status != _report_status(rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows):
        raise ValueError("reason_code_counts must match rows")


def _row_key(row: ResearchMarketDepthProbabilityCostReversalLadderRow) -> tuple[object, ...]:
    return (
        _STATUS_WEIGHT[row.status],
        -row.ladder_risk_score,
        row.public_ladder_ref,
        row.observed_at.isoformat(),
    )


def _reason_key(reason_code: str) -> tuple[object, ...]:
    try:
        return (_REASON_PRIORITY.index(reason_code), reason_code)
    except ValueError:
        return (len(_REASON_PRIORITY), reason_code)


def _status_count(
    rows: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(_ONE for row in rows if row.status == status))


def _average_ladder_risk_score(
    rows: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...],
) -> Decimal:
    if not rows:
        return _ZERO
    return _safe_ratio(_sum_decimal(*(row.ladder_risk_score for row in rows)), _decimal_count(len(rows)))


def _max_decimal(
    rows: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...],
    field_name: str,
) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=_ZERO)


def _min_decimal(
    rows: tuple[ResearchMarketDepthProbabilityCostReversalLadderRow, ...],
    field_name: str,
) -> Decimal:
    return min((getattr(row, field_name) for row in rows), default=_ZERO)


def _ratio_ladder_score(value: Decimal, watch_floor: Decimal, block_floor: Decimal) -> Decimal:
    if value < watch_floor:
        return _ZERO
    if value >= block_floor:
        return _ONE
    return _safe_ratio(value - watch_floor, block_floor - watch_floor)


def _depth_ladder_score(value: Decimal, block_ceiling: Decimal, pass_floor: Decimal) -> Decimal:
    if value >= pass_floor:
        return _ZERO
    if value < block_ceiling:
        return _ONE
    return _safe_ratio(pass_floor - value, pass_floor - block_ceiling)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == _ZERO:
        return _ZERO
    with localcontext() as context:
        context.prec = 64
        return _quantize(numerator / denominator)


def _sum_decimal(*values: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        total = _ZERO
        for value in values:
            total += value
        return _quantize(total)


def _abs_decimal(value: Decimal) -> Decimal:
    return _quantize(abs(value))


def _decimal_count(value: object) -> Decimal:
    return _quantize(Decimal(str(value)))


def _quantize(value: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = 64
        return value.quantize(_QUANT)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO or decimal_value > _ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return decimal_value


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value <= _ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < _ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return decimal_value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    try:
        return _quantize(value)
    except DecimalException as exc:
        raise ValueError(f"{field_name} must be quantizable") from exc


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in _STATUS_SET:
        raise ValueError(f"{field_name} must be pass, watch, or block")


def _require_public_label(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not _PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    _reject_unsafe_text(field_name, value)


def _normalize_reason_codes(
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values and not allow_empty:
        raise ValueError("reason_codes must not be empty")
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require_public_label("reason_code", value)
        if value not in seen:
            seen.add(value)
            normalized.append(value)
    return tuple(normalized)


def _require_sha256_digest(field_name: str, value: object) -> None:
    if type(value) is not str or _DIGEST_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a sha256 digest")


def _require_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    if digest != _derived_validation_digest(payload):
        raise ValueError("derived_validation_digest must match report payload")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    ready = _json_ready(value)
    _reject_unsafe_value(label, ready)


def _reject_unsafe_value(label: str, value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_unsafe_text(label, str(key))
            _reject_unsafe_value(label, item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_value(label, item)
        return
    if isinstance(value, str):
        _reject_unsafe_text(label, value)


def _reject_unsafe_text(label: str, value: str) -> None:
    lowered = value.lower()
    compacted = _UNSAFE_PUBLIC_SEPARATOR_RE.sub("", lowered)
    if any(
        fragment in lowered or fragment in compacted
        for fragment in _UNSAFE_PUBLIC_FRAGMENTS
    ):
        raise ValueError(f"unsafe public value in {label}")


def _json_ready(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: _json_ready(getattr(value, field.name))
            for field in fields(value)
            if not field.name.startswith("_")
        }
    if type(value) is Decimal:
        return format(_quantize(value), "f")
    if type(value) is datetime:
        return value.astimezone(UTC).isoformat()
    if type(value) is tuple:
        return [_json_ready(item) for item in value]
    if type(value) is list:
        return [_json_ready(item) for item in value]
    if type(value) is dict:
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) is bool or value is None or type(value) is str:
        return value
    raise ValueError(f"public payload contains unsupported value {type(value).__name__}")


def _derived_validation_digest(value: object) -> str:
    payload = _json_ready(value)
    if type(payload) is not dict:
        raise ValueError("digest payload must be a JSON object")
    payload_without_digest = dict(payload)
    payload_without_digest.pop("derived_validation_digest", None)
    canonical = json.dumps(
        payload_without_digest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = (
    "DEFAULT_RESEARCH_MARKET_DEPTH_PROBABILITY_COST_REVERSAL_LADDER_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketDepthProbabilityCostReversalLadderConfig",
    "ResearchMarketDepthProbabilityCostReversalLadderInput",
    "ResearchMarketDepthProbabilityCostReversalLadderRow",
    "ResearchMarketDepthProbabilityCostReversalLadderReasonCodeCount",
    "ResearchMarketDepthProbabilityCostReversalLadderReport",
    "build_research_market_depth_probability_cost_reversal_ladder_report",
    "research_market_depth_probability_cost_reversal_ladder_report_payload",
    "research_market_depth_probability_cost_reversal_ladder_report_digest",
)
