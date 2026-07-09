"""Report-only depth probability fee conflict monitor."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
import hashlib
import json
import re
from typing import Any


DEFAULT_CONFIG_VERSION = "research-market-depth-probability-fee-conflict-report-v1"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
DEFAULT_OBSERVED_AT = datetime(1970, 1, 1, tzinfo=UTC)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))

REASON_MISSING_INPUTS = "missing_depth_probability_fee_conflict_inputs"
REASON_POSITIVE_EDGE = "positive_probability_edge"
REASON_NON_POSITIVE_EDGE = "non_positive_probability_edge"
REASON_DEPTH_PENALTY = "depth_shortfall_penalty_applied"
REASON_FEE_WATCH = "fee_drag_watch"
REASON_FEE_BLOCK = "fee_drag_block"
REASON_REQUIRED_EXCEEDS_EDGE = "required_drag_exceeds_probability_edge"
REASON_BELOW_WATCH = "net_probability_edge_below_watch_threshold"
REASON_PASS = "probability_fee_conflict_pass"
REASON_WATCH = "probability_fee_conflict_watch"
REASON_BLOCK = "probability_fee_conflict_block"
REASON_CODES = frozenset(
    (
        REASON_MISSING_INPUTS,
        REASON_POSITIVE_EDGE,
        REASON_NON_POSITIVE_EDGE,
        REASON_DEPTH_PENALTY,
        REASON_FEE_WATCH,
        REASON_FEE_BLOCK,
        REASON_REQUIRED_EXCEEDS_EDGE,
        REASON_BELOW_WATCH,
        REASON_PASS,
        REASON_WATCH,
        REASON_BLOCK,
    ),
)

PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
PUBLIC_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candi" "date" "_id",
    "candi" "date",
    "market" "_id",
    "market" "_slug",
    "sl" "ug",
    "ques" "tion",
    "sou" "rce",
    "u" "rl",
    "http",
    "te" "xt",
    "d" "sn",
    "ta" "ble",
    "tok" "en",
    "wall" "et",
    "ord" "er",
    "tra" "de",
    "li" "ve",
    "exec" "ute",
    "recommend" "ation",
    "siz" "ing",
    "sec" "ret",
    "creden" "tial",
    "private" "_key",
    "api" "_key",
    "au" "th",
)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityFeeConflictConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_net_probability_edge_threshold: Decimal = Decimal("0.025000")
    watch_net_probability_edge_threshold: Decimal = Decimal("0.005000")
    minimum_depth_coverage_ratio: Decimal = Decimal("1.000000")
    depth_shortfall_penalty_rate: Decimal = Decimal("0.040000")
    fee_drag_watch_threshold: Decimal = Decimal("0.020000")
    fee_drag_block_threshold: Decimal = Decimal("0.060000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthProbabilityFeeConflictConfig:
            raise TypeError(
                "ResearchMarketDepthProbabilityFeeConflictConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchMarketDepthProbabilityFeeConflictConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_net_probability_edge_threshold",
            "watch_net_probability_edge_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.pass_net_probability_edge_threshold
            < self.watch_net_probability_edge_threshold
        ):
            raise ValueError(
                "pass_net_probability_edge_threshold must be at least "
                "watch_net_probability_edge_threshold",
            )
        object.__setattr__(
            self,
            "minimum_depth_coverage_ratio",
            _require_positive_decimal(
                "minimum_depth_coverage_ratio",
                self.minimum_depth_coverage_ratio,
            ),
        )
        object.__setattr__(
            self,
            "depth_shortfall_penalty_rate",
            _require_nonnegative_decimal(
                "depth_shortfall_penalty_rate",
                self.depth_shortfall_penalty_rate,
            ),
        )
        for field_name in ("fee_drag_watch_threshold", "fee_drag_block_threshold"):
            object.__setattr__(
                self,
                field_name,
                _require_positive_probability_decimal(
                    field_name,
                    getattr(self, field_name),
                ),
            )
        if self.fee_drag_block_threshold < self.fee_drag_watch_threshold:
            raise ValueError(
                "fee_drag_block_threshold must be at least fee_drag_watch_threshold",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(
            "config",
            self,
            allow_constructor_containers=True,
        )


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityFeeConflictInput:
    research_reference: str
    model_probability: Decimal
    market_probability: Decimal
    fee_rate: Decimal
    bid_ask_spread_rate: Decimal
    depth_coverage_ratio: Decimal
    observed_at: datetime = DEFAULT_OBSERVED_AT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthProbabilityFeeConflictInput:
            raise TypeError(
                "ResearchMarketDepthProbabilityFeeConflictInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchMarketDepthProbabilityFeeConflictInput)
        _require_private_reference("research_reference", self.research_reference)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_rate",
            "bid_ask_spread_rate",
            "depth_coverage_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityFeeConflictReportRow:
    research_digest: str
    rank: Decimal
    observed_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    fee_rate: Decimal
    bid_ask_spread_rate: Decimal
    fee_drag_rate: Decimal
    depth_coverage_ratio: Decimal
    depth_shortfall_penalty: Decimal
    required_probability_drag: Decimal
    net_probability_edge: Decimal
    conflict_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthProbabilityFeeConflictReportRow:
            raise TypeError(
                "ResearchMarketDepthProbabilityFeeConflictReportRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchMarketDepthProbabilityFeeConflictReportRow)
        _require_sha256_digest("research_digest", self.research_digest)
        object.__setattr__(self, "rank", _require_positive_decimal("rank", self.rank))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "market_probability"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "fee_rate",
            "bid_ask_spread_rate",
            "fee_drag_rate",
            "depth_coverage_ratio",
            "depth_shortfall_penalty",
            "required_probability_drag",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("gross_probability_edge", "net_probability_edge"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("conflict_status", self.conflict_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row(self)
        _reject_unsafe_public_payload(
            "row",
            self,
            allow_constructor_containers=True,
        )


@dataclass(frozen=True)
class ResearchMarketDepthProbabilityFeeConflictReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    worst_net_probability_edge: Decimal | None
    average_net_probability_edge: Decimal | None
    max_required_probability_drag: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketDepthProbabilityFeeConflictReportRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketDepthProbabilityFeeConflictReport:
            raise TypeError(
                "ResearchMarketDepthProbabilityFeeConflictReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchMarketDepthProbabilityFeeConflictReport)
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "worst_net_probability_edge",
            "average_net_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_required_probability_drag",
            _require_nonnegative_decimal(
                "max_required_probability_drag",
                self.max_required_probability_drag,
            ),
        )
        _require_status("report_status", self.report_status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, allow_empty=False),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_hard_flags("report", self)
        if self.derived_validation_digest == "":
            _validate_report(self)
            object.__setattr__(
                self,
                "derived_validation_digest",
                _report_validation_digest(self),
            )
        else:
            _require_sha256_digest(
                "derived_validation_digest",
                self.derived_validation_digest,
            )
            if self.derived_validation_digest != _report_validation_digest(self):
                raise ValueError("derived_validation_digest does not match report payload")
            _validate_report(self)
        _require_sha256_digest(
            "derived_validation_digest",
            self.derived_validation_digest,
        )
        _reject_unsafe_public_payload(
            "report",
            _json_ready(self),
            allow_json_containers=True,
        )

    @property
    def payload(self) -> dict[str, Any]:
        return research_market_depth_probability_fee_conflict_report_payload(self)


def build_research_market_depth_probability_fee_conflict_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketDepthProbabilityFeeConflictConfig,
    generated_at: datetime,
) -> ResearchMarketDepthProbabilityFeeConflictReport:
    if type(config) is not ResearchMarketDepthProbabilityFeeConflictConfig:
        raise ValueError(
            "config must be a ResearchMarketDepthProbabilityFeeConflictConfig",
        )
    _require_hard_flags("config", config)
    normalized_inputs = _normalize_inputs(inputs)
    scored_rows = tuple(
        sorted(
            (_unranked_row(item, config=config) for item in normalized_inputs),
            key=_unranked_row_sort_key,
        ),
    )
    rows = tuple(
        ResearchMarketDepthProbabilityFeeConflictReportRow(
            rank=_decimal_count(index),
            **row,
        )
        for index, row in enumerate(scored_rows, start=1)
    )
    net_edges = tuple(row.net_probability_edge for row in rows)
    return ResearchMarketDepthProbabilityFeeConflictReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        worst_net_probability_edge=rows[0].net_probability_edge if rows else None,
        average_net_probability_edge=_average(net_edges),
        max_required_probability_drag=_maximum(
            (row.required_probability_drag for row in rows),
            ZERO,
        ),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_market_depth_probability_fee_conflict_report_payload(
    report: ResearchMarketDepthProbabilityFeeConflictReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketDepthProbabilityFeeConflictReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _report_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketDepthProbabilityFeeConflictReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(
        "payload",
        payload,
        allow_json_containers=True,
    )
    return payload


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


def _unranked_row(
    item: ResearchMarketDepthProbabilityFeeConflictInput,
    *,
    config: ResearchMarketDepthProbabilityFeeConflictConfig,
) -> dict[str, object]:
    gross_probability_edge = _quantize(item.model_probability - item.market_probability)
    fee_drag_rate = _quantize(item.fee_rate + (item.bid_ask_spread_rate / TWO))
    depth_shortfall_penalty = _depth_shortfall_penalty(item, config)
    required_probability_drag = _quantize(fee_drag_rate + depth_shortfall_penalty)
    net_probability_edge = _quantize(
        gross_probability_edge - required_probability_drag,
    )
    conflict_status = _conflict_status(
        gross_probability_edge=gross_probability_edge,
        fee_drag_rate=fee_drag_rate,
        required_probability_drag=required_probability_drag,
        net_probability_edge=net_probability_edge,
        config=config,
    )
    return {
        "research_digest": _research_digest(item.research_reference),
        "observed_at": item.observed_at,
        "model_probability": item.model_probability,
        "market_probability": item.market_probability,
        "gross_probability_edge": gross_probability_edge,
        "fee_rate": item.fee_rate,
        "bid_ask_spread_rate": item.bid_ask_spread_rate,
        "fee_drag_rate": fee_drag_rate,
        "depth_coverage_ratio": item.depth_coverage_ratio,
        "depth_shortfall_penalty": depth_shortfall_penalty,
        "required_probability_drag": required_probability_drag,
        "net_probability_edge": net_probability_edge,
        "conflict_status": conflict_status,
        "reason_codes": _row_reason_codes(
            gross_probability_edge=gross_probability_edge,
            fee_drag_rate=fee_drag_rate,
            depth_shortfall_penalty=depth_shortfall_penalty,
            required_probability_drag=required_probability_drag,
            net_probability_edge=net_probability_edge,
            conflict_status=conflict_status,
            config=config,
        ),
    }


def _depth_shortfall_penalty(
    item: ResearchMarketDepthProbabilityFeeConflictInput,
    config: ResearchMarketDepthProbabilityFeeConflictConfig,
) -> Decimal:
    if item.depth_coverage_ratio >= config.minimum_depth_coverage_ratio:
        return ZERO
    shortfall_ratio = _quantize(
        (config.minimum_depth_coverage_ratio - item.depth_coverage_ratio)
        / config.minimum_depth_coverage_ratio,
    )
    return _quantize(shortfall_ratio * config.depth_shortfall_penalty_rate)


def _conflict_status(
    *,
    gross_probability_edge: Decimal,
    fee_drag_rate: Decimal,
    required_probability_drag: Decimal,
    net_probability_edge: Decimal,
    config: ResearchMarketDepthProbabilityFeeConflictConfig,
) -> str:
    if gross_probability_edge <= ZERO:
        return STATUS_BLOCK
    if fee_drag_rate >= config.fee_drag_block_threshold:
        return STATUS_BLOCK
    if required_probability_drag > gross_probability_edge:
        return STATUS_BLOCK
    if (
        net_probability_edge >= config.pass_net_probability_edge_threshold
        and fee_drag_rate < config.fee_drag_watch_threshold
    ):
        return STATUS_PASS
    if net_probability_edge >= config.watch_net_probability_edge_threshold:
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_reason_codes(
    *,
    gross_probability_edge: Decimal,
    fee_drag_rate: Decimal,
    depth_shortfall_penalty: Decimal,
    required_probability_drag: Decimal,
    net_probability_edge: Decimal,
    conflict_status: str,
    config: ResearchMarketDepthProbabilityFeeConflictConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if gross_probability_edge > ZERO:
        reasons.append(REASON_POSITIVE_EDGE)
    else:
        reasons.append(REASON_NON_POSITIVE_EDGE)
    if depth_shortfall_penalty > ZERO:
        reasons.append(REASON_DEPTH_PENALTY)
    if fee_drag_rate >= config.fee_drag_block_threshold:
        reasons.append(REASON_FEE_BLOCK)
    elif fee_drag_rate >= config.fee_drag_watch_threshold:
        reasons.append(REASON_FEE_WATCH)
    if required_probability_drag > gross_probability_edge:
        reasons.append(REASON_REQUIRED_EXCEEDS_EDGE)
    if conflict_status == STATUS_PASS:
        reasons.append(REASON_PASS)
    elif conflict_status == STATUS_WATCH:
        reasons.append(REASON_WATCH)
    else:
        reasons.append(REASON_BLOCK)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _unranked_row_sort_key(row: Mapping[str, object]) -> tuple[Decimal, Decimal, str]:
    status = row["conflict_status"]
    net_edge = row["net_probability_edge"]
    required_drag = row["required_probability_drag"]
    digest = row["research_digest"]
    if type(status) is not str:
        raise ValueError("conflict_status must be a string")
    if type(net_edge) is not Decimal:
        raise ValueError("net_probability_edge must be a Decimal")
    if type(required_drag) is not Decimal:
        raise ValueError("required_probability_drag must be a Decimal")
    if type(digest) is not str:
        raise ValueError("research_digest must be a string")
    return (_status_rank(status), net_edge, -required_drag, digest)


def _row_sort_key(
    row: ResearchMarketDepthProbabilityFeeConflictReportRow,
) -> tuple[Decimal, Decimal, Decimal, str]:
    return (
        _status_rank(row.conflict_status),
        row.net_probability_edge,
        -row.required_probability_drag,
        row.research_digest,
    )


def _status_rank(status: str) -> Decimal:
    if status == STATUS_BLOCK:
        return Decimal("0.000000")
    if status == STATUS_WATCH:
        return Decimal("1.000000")
    if status == STATUS_PASS:
        return Decimal("2.000000")
    raise ValueError("status must be one of pass, watch, block")


def _report_status(
    rows: tuple[ResearchMarketDepthProbabilityFeeConflictReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.conflict_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.conflict_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketDepthProbabilityFeeConflictReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _status_count(
    rows: tuple[ResearchMarketDepthProbabilityFeeConflictReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.conflict_status == status))


def _validate_row(row: ResearchMarketDepthProbabilityFeeConflictReportRow) -> None:
    if row.gross_probability_edge != _quantize(
        row.model_probability - row.market_probability,
    ):
        raise ValueError("gross_probability_edge must match probabilities")
    expected_fee_drag = _quantize(row.fee_rate + (row.bid_ask_spread_rate / TWO))
    if row.fee_drag_rate != expected_fee_drag:
        raise ValueError("fee_drag_rate must match fee and spread inputs")
    expected_required = _quantize(row.fee_drag_rate + row.depth_shortfall_penalty)
    if row.required_probability_drag != expected_required:
        raise ValueError("required_probability_drag must match components")
    if row.net_probability_edge != _quantize(
        row.gross_probability_edge - row.required_probability_drag,
    ):
        raise ValueError("net_probability_edge must match edge minus drag")
    expected_status_reason = f"probability_fee_conflict_{row.conflict_status}"
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include conflict status")


def _validate_report(report: ResearchMarketDepthProbabilityFeeConflictReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    for index, row in enumerate(report.rows, start=1):
        if row.rank != _decimal_count(index):
            raise ValueError("row ranks must be deterministic")
    net_edges = tuple(row.net_probability_edge for row in report.rows)
    expected_worst = report.rows[0].net_probability_edge if report.rows else None
    if report.worst_net_probability_edge != expected_worst:
        raise ValueError("worst_net_probability_edge must match rows")
    if report.average_net_probability_edge != _average(net_edges):
        raise ValueError("average_net_probability_edge must match rows")
    expected_max_drag = _maximum(
        (row.required_probability_drag for row in report.rows),
        ZERO,
    )
    if report.max_required_probability_drag != expected_max_drag:
        raise ValueError("max_required_probability_drag must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketDepthProbabilityFeeConflictInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be iterable")
    normalized: list[ResearchMarketDepthProbabilityFeeConflictInput] = []
    for item in inputs:
        if type(item) is not ResearchMarketDepthProbabilityFeeConflictInput:
            raise ValueError(
                "inputs must contain ResearchMarketDepthProbabilityFeeConflictInput",
            )
        _require_hard_flags("input", item)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchMarketDepthProbabilityFeeConflictReportRow],
) -> tuple[ResearchMarketDepthProbabilityFeeConflictReportRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketDepthProbabilityFeeConflictReportRow] = []
    for row in rows:
        if type(row) is not ResearchMarketDepthProbabilityFeeConflictReportRow:
            raise ValueError(
                "rows must contain ResearchMarketDepthProbabilityFeeConflictReportRow",
            )
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(sorted(normalized, key=_row_sort_key))


def _require_exact_type(field_name: str, value: object, expected_type: type[object]) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{field_name} must be True for {label}")


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must be non-empty")
    if len(value) > 4096:
        raise ValueError(f"{field_name} is too long")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_ID_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public identifier")
    _reject_unsafe_public_string(field_name, value)
    return value


def _require_sha256_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not SHA256_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a lowercase sha256 digest")
    return value


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be one of pass, watch, block")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized > ONE:
        raise ValueError(f"{field_name} must be no greater than one")
    return normalized


def _require_positive_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_probability_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_optional_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_decimal(field_name, value)


def _normalize_reason_codes(
    reason_codes: Sequence[str],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if isinstance(reason_codes, (str, bytes)) or not isinstance(reason_codes, Sequence):
        raise ValueError("reason_codes must be a sequence")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_public_identifier("reason_code", reason_code)
        if reason_code not in REASON_CODES:
            raise ValueError("reason_code must be supported")
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not normalized and not allow_empty:
        raise ValueError("reason_codes must be non-empty")
    return tuple(sorted(normalized))


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANT)


def _average(values: tuple[Decimal, ...]) -> Decimal | None:
    if not values:
        return None
    return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _maximum(values: Iterable[Decimal], default: Decimal) -> Decimal:
    maximum = default
    for value in values:
        if value > maximum:
            maximum = value
    return _quantize(maximum)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANT, rounding=ROUND_HALF_UP)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _research_digest(value: str) -> str:
    canonical = json.dumps(
        {"ref": value},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _report_values_without_digest(
    report: ResearchMarketDepthProbabilityFeeConflictReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_validation_digest(
    report: ResearchMarketDepthProbabilityFeeConflictReport,
) -> str:
    payload = _json_ready(_report_values_without_digest(report))
    _reject_unsafe_public_payload(
        "digest payload",
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
    allow_constructor_containers: bool = False,
) -> None:
    current_path = path or label
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name, current_path)
            _reject_unsafe_public_payload(
                label,
                getattr(value, field.name),
                field.name if not path else f"{path}.{field.name}",
                allow_constructor_containers=allow_constructor_containers,
            )
        return
    if isinstance(value, Mapping):
        if not allow_json_containers and not allow_constructor_containers:
            raise ValueError(f"{current_path} must remain constructor-normalized")
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key, current_path)
            _reject_unsafe_public_payload(
                label,
                item,
                key if not path else f"{path}.{key}",
                allow_json_containers=allow_json_containers,
                allow_constructor_containers=allow_constructor_containers,
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
                allow_constructor_containers=allow_constructor_containers,
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
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{path}.{key} has unsafe public field")


def _reject_unsafe_public_string(field_name: str, value: str) -> None:
    lowered = value.lower()
    if "://" in lowered or "?" in lowered or "@" in lowered:
        raise ValueError(f"{field_name} has unsafe public value")
    if any(term in lowered for term in UNSAFE_PUBLIC_TERMS):
        raise ValueError(f"{field_name} has unsafe public value")


__all__ = (
    "DEFAULT_CONFIG_VERSION",
    "ResearchMarketDepthProbabilityFeeConflictConfig",
    "ResearchMarketDepthProbabilityFeeConflictInput",
    "ResearchMarketDepthProbabilityFeeConflictReport",
    "ResearchMarketDepthProbabilityFeeConflictReportRow",
    "build_research_market_depth_probability_fee_conflict_report",
    "research_market_depth_probability_fee_conflict_report_payload",
)
