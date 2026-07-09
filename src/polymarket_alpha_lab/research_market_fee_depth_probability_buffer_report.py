"""Report-only fee depth probability buffer."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, fields, is_dataclass
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal
import hashlib
import json
import re
from typing import Any


DEFAULT_CONFIG_VERSION = "research-market-fee-depth-probability-buffer-report-v1"
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
DEFAULT_OBSERVED_AT = datetime(1970, 1, 1, tzinfo=UTC)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = frozenset((STATUS_PASS, STATUS_WATCH, STATUS_BLOCK))

REASON_MISSING_INPUTS = "missing_fee_depth_probability_buffer_inputs"
REASON_POSITIVE_EDGE = "positive_probability_edge"
REASON_NON_POSITIVE_EDGE = "non_positive_probability_edge"
REASON_FEE = "fee_buffer_applied"
REASON_SPREAD = "spread_buffer_applied"
REASON_DEPTH = "depth_shortfall_buffer_applied"
REASON_UNCERTAINTY = "probability_uncertainty_buffer_applied"
REASON_REQUIRED_BLOCK = "required_probability_buffer_blocks_edge"
REASON_REQUIRED_EXCEEDS_EDGE = "required_probability_buffer_exceeds_edge"
REASON_BELOW_WATCH = "net_probability_buffer_below_watch_threshold"
REASON_PASS = "probability_buffer_pass"
REASON_WATCH = "probability_buffer_watch"
REASON_BLOCK = "probability_buffer_block"
REASON_CODES = frozenset(
    (
        REASON_MISSING_INPUTS,
        REASON_POSITIVE_EDGE,
        REASON_NON_POSITIVE_EDGE,
        REASON_FEE,
        REASON_SPREAD,
        REASON_DEPTH,
        REASON_UNCERTAINTY,
        REASON_REQUIRED_BLOCK,
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
    "candidate" "_id",
    "candi" "date",
    "market" "_id",
    "market" "_slug",
    "sl" "ug",
    "ques" "tion",
    "u" "rl",
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
REPORT_PUBLIC_PAYLOAD_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_net_probability_buffer",
        "top_net_probability_buffer",
        "max_required_probability_buffer",
        "report_status",
        "reason_codes",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
ROW_PUBLIC_PAYLOAD_FIELDS = frozenset(
    (
        "research_digest",
        "rank",
        "observed_at",
        "model_probability",
        "market_probability",
        "gross_probability_edge",
        "fee_buffer",
        "spread_buffer",
        "depth_shortfall_buffer",
        "probability_uncertainty_buffer",
        "required_probability_buffer",
        "net_probability_buffer",
        "buffer_status",
        "reason_codes",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchMarketFeeDepthProbabilityBufferConfig:
    config_version: str = DEFAULT_CONFIG_VERSION
    pass_net_probability_buffer_threshold: Decimal = Decimal("0.020000")
    watch_net_probability_buffer_threshold: Decimal = Decimal("0.005000")
    minimum_depth_coverage_ratio: Decimal = Decimal("1.000000")
    depth_shortfall_buffer_rate: Decimal = Decimal("0.030000")
    block_required_probability_buffer_threshold: Decimal = Decimal("0.090000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeDepthProbabilityBufferConfig:
            raise TypeError(
                "ResearchMarketFeeDepthProbabilityBufferConfig does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type(
            "config",
            self,
            ResearchMarketFeeDepthProbabilityBufferConfig,
        )
        _require_public_identifier("config_version", self.config_version)
        if self.config_version != DEFAULT_CONFIG_VERSION:
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "pass_net_probability_buffer_threshold",
            "watch_net_probability_buffer_threshold",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        if (
            self.pass_net_probability_buffer_threshold
            < self.watch_net_probability_buffer_threshold
        ):
            raise ValueError(
                "pass_net_probability_buffer_threshold must be at least "
                "watch_net_probability_buffer_threshold",
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
            "depth_shortfall_buffer_rate",
            _require_nonnegative_decimal(
                "depth_shortfall_buffer_rate",
                self.depth_shortfall_buffer_rate,
            ),
        )
        object.__setattr__(
            self,
            "block_required_probability_buffer_threshold",
            _require_positive_decimal(
                "block_required_probability_buffer_threshold",
                self.block_required_probability_buffer_threshold,
            ),
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(
            "config",
            self,
            allow_constructor_containers=True,
        )


@dataclass(frozen=True)
class ResearchMarketFeeDepthProbabilityBufferInput:
    research_reference: str
    model_probability: Decimal
    market_probability: Decimal
    fee_rate: Decimal
    bid_ask_spread_rate: Decimal
    depth_coverage_ratio: Decimal
    probability_uncertainty_buffer_rate: Decimal
    observed_at: datetime = DEFAULT_OBSERVED_AT
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeDepthProbabilityBufferInput:
            raise TypeError(
                "ResearchMarketFeeDepthProbabilityBufferInput does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("input", self, ResearchMarketFeeDepthProbabilityBufferInput)
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
            "probability_uncertainty_buffer_rate",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketFeeDepthProbabilityBufferReportRow:
    research_digest: str
    rank: Decimal
    observed_at: datetime
    model_probability: Decimal
    market_probability: Decimal
    gross_probability_edge: Decimal
    fee_buffer: Decimal
    spread_buffer: Decimal
    depth_shortfall_buffer: Decimal
    probability_uncertainty_buffer: Decimal
    required_probability_buffer: Decimal
    net_probability_buffer: Decimal
    buffer_status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeDepthProbabilityBufferReportRow:
            raise TypeError(
                "ResearchMarketFeeDepthProbabilityBufferReportRow does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("row", self, ResearchMarketFeeDepthProbabilityBufferReportRow)
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
            "fee_buffer",
            "spread_buffer",
            "depth_shortfall_buffer",
            "probability_uncertainty_buffer",
            "required_probability_buffer",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("gross_probability_edge", "net_probability_buffer"):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("buffer_status", self.buffer_status)
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
class ResearchMarketFeeDepthProbabilityBufferReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_net_probability_buffer: Decimal | None
    top_net_probability_buffer: Decimal | None
    max_required_probability_buffer: Decimal
    report_status: str
    reason_codes: tuple[str, ...]
    rows: tuple[ResearchMarketFeeDepthProbabilityBufferReportRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketFeeDepthProbabilityBufferReport:
            raise TypeError(
                "ResearchMarketFeeDepthProbabilityBufferReport does not support "
                "subclassing",
            )

    def __post_init__(self) -> None:
        _require_exact_type("report", self, ResearchMarketFeeDepthProbabilityBufferReport)
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
            "average_net_probability_buffer",
            "top_net_probability_buffer",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "max_required_probability_buffer",
            _require_nonnegative_decimal(
                "max_required_probability_buffer",
                self.max_required_probability_buffer,
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
        return research_market_fee_depth_probability_buffer_report_payload(self)


def build_research_market_fee_depth_probability_buffer_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketFeeDepthProbabilityBufferConfig,
    generated_at: datetime,
) -> ResearchMarketFeeDepthProbabilityBufferReport:
    if type(config) is not ResearchMarketFeeDepthProbabilityBufferConfig:
        raise ValueError(
            "config must be a ResearchMarketFeeDepthProbabilityBufferConfig",
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
        ResearchMarketFeeDepthProbabilityBufferReportRow(
            rank=_decimal_count(index),
            **row,
        )
        for index, row in enumerate(scored_rows, start=1)
    )
    return ResearchMarketFeeDepthProbabilityBufferReport(
        generated_at=_as_utc("generated_at", generated_at),
        config_version=config.config_version,
        input_count=_decimal_count(len(normalized_inputs)),
        pass_count=_status_count(rows, STATUS_PASS),
        watch_count=_status_count(rows, STATUS_WATCH),
        block_count=_status_count(rows, STATUS_BLOCK),
        average_net_probability_buffer=_average(
            tuple(row.net_probability_buffer for row in rows),
        ),
        top_net_probability_buffer=rows[0].net_probability_buffer if rows else None,
        max_required_probability_buffer=_maximum(
            (row.required_probability_buffer for row in rows),
            ZERO,
        ),
        report_status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        rows=rows,
    )


def research_market_fee_depth_probability_buffer_report_payload(
    report: ResearchMarketFeeDepthProbabilityBufferReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketFeeDepthProbabilityBufferReport:
        _require_hard_flags("report", report)
        if report.derived_validation_digest != _report_validation_digest(report):
            raise ValueError("derived_validation_digest does not match report payload")
        payload = _json_ready(report)
    elif type(report) is dict:
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchMarketFeeDepthProbabilityBufferReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(
        "payload",
        payload,
        allow_json_containers=True,
    )
    _validate_public_payload_shape(payload)
    _validate_public_payload_digest(payload)
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
    item: ResearchMarketFeeDepthProbabilityBufferInput,
    *,
    config: ResearchMarketFeeDepthProbabilityBufferConfig,
) -> dict[str, object]:
    gross_probability_edge = _quantize(item.model_probability - item.market_probability)
    fee_buffer = item.fee_rate
    spread_buffer = _quantize(item.bid_ask_spread_rate / TWO)
    depth_shortfall_buffer = _depth_shortfall_buffer(item, config)
    probability_uncertainty_buffer = item.probability_uncertainty_buffer_rate
    required_probability_buffer = _quantize(
        fee_buffer
        + spread_buffer
        + depth_shortfall_buffer
        + probability_uncertainty_buffer,
    )
    net_probability_buffer = _quantize(
        gross_probability_edge - required_probability_buffer,
    )
    buffer_status = _buffer_status(
        gross_probability_edge=gross_probability_edge,
        required_probability_buffer=required_probability_buffer,
        net_probability_buffer=net_probability_buffer,
        config=config,
    )
    return {
        "research_digest": _research_digest(item.research_reference),
        "observed_at": item.observed_at,
        "model_probability": item.model_probability,
        "market_probability": item.market_probability,
        "gross_probability_edge": gross_probability_edge,
        "fee_buffer": fee_buffer,
        "spread_buffer": spread_buffer,
        "depth_shortfall_buffer": depth_shortfall_buffer,
        "probability_uncertainty_buffer": probability_uncertainty_buffer,
        "required_probability_buffer": required_probability_buffer,
        "net_probability_buffer": net_probability_buffer,
        "buffer_status": buffer_status,
        "reason_codes": _row_reason_codes(
            gross_probability_edge=gross_probability_edge,
            fee_buffer=fee_buffer,
            spread_buffer=spread_buffer,
            depth_shortfall_buffer=depth_shortfall_buffer,
            probability_uncertainty_buffer=probability_uncertainty_buffer,
            required_probability_buffer=required_probability_buffer,
            net_probability_buffer=net_probability_buffer,
            buffer_status=buffer_status,
            config=config,
        ),
    }


def _depth_shortfall_buffer(
    item: ResearchMarketFeeDepthProbabilityBufferInput,
    config: ResearchMarketFeeDepthProbabilityBufferConfig,
) -> Decimal:
    if item.depth_coverage_ratio >= config.minimum_depth_coverage_ratio:
        return ZERO
    shortfall_ratio = _quantize(
        (config.minimum_depth_coverage_ratio - item.depth_coverage_ratio)
        / config.minimum_depth_coverage_ratio,
    )
    return _quantize(shortfall_ratio * config.depth_shortfall_buffer_rate)


def _buffer_status(
    *,
    gross_probability_edge: Decimal,
    required_probability_buffer: Decimal,
    net_probability_buffer: Decimal,
    config: ResearchMarketFeeDepthProbabilityBufferConfig,
) -> str:
    if required_probability_buffer >= config.block_required_probability_buffer_threshold:
        return STATUS_BLOCK
    if gross_probability_edge <= ZERO:
        return STATUS_BLOCK
    if net_probability_buffer >= config.pass_net_probability_buffer_threshold:
        return STATUS_PASS
    if net_probability_buffer >= config.watch_net_probability_buffer_threshold:
        return STATUS_WATCH
    return STATUS_BLOCK


def _row_reason_codes(
    *,
    gross_probability_edge: Decimal,
    fee_buffer: Decimal,
    spread_buffer: Decimal,
    depth_shortfall_buffer: Decimal,
    probability_uncertainty_buffer: Decimal,
    required_probability_buffer: Decimal,
    net_probability_buffer: Decimal,
    buffer_status: str,
    config: ResearchMarketFeeDepthProbabilityBufferConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if gross_probability_edge > ZERO:
        reasons.append(REASON_POSITIVE_EDGE)
    else:
        reasons.append(REASON_NON_POSITIVE_EDGE)
    if fee_buffer > ZERO:
        reasons.append(REASON_FEE)
    if spread_buffer > ZERO:
        reasons.append(REASON_SPREAD)
    if depth_shortfall_buffer > ZERO:
        reasons.append(REASON_DEPTH)
    if probability_uncertainty_buffer > ZERO:
        reasons.append(REASON_UNCERTAINTY)
    if required_probability_buffer >= config.block_required_probability_buffer_threshold:
        reasons.append(REASON_REQUIRED_BLOCK)
    if required_probability_buffer > gross_probability_edge:
        reasons.append(REASON_REQUIRED_EXCEEDS_EDGE)
    if net_probability_buffer < config.watch_net_probability_buffer_threshold:
        reasons.append(REASON_BELOW_WATCH)
    if buffer_status == STATUS_PASS:
        reasons.append(REASON_PASS)
    elif buffer_status == STATUS_WATCH:
        reasons.append(REASON_WATCH)
    else:
        reasons.append(REASON_BLOCK)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _unranked_row_sort_key(row: Mapping[str, object]) -> tuple[Decimal, Decimal, str]:
    net_buffer = row["net_probability_buffer"]
    required_buffer = row["required_probability_buffer"]
    digest = row["research_digest"]
    if type(net_buffer) is not Decimal:
        raise ValueError("net_probability_buffer must be a Decimal")
    if type(required_buffer) is not Decimal:
        raise ValueError("required_probability_buffer must be a Decimal")
    if type(digest) is not str:
        raise ValueError("research_digest must be a string")
    return (-net_buffer, required_buffer, digest)


def _row_sort_key(
    row: ResearchMarketFeeDepthProbabilityBufferReportRow,
) -> tuple[Decimal, Decimal, str]:
    return (-row.net_probability_buffer, row.required_probability_buffer, row.research_digest)


def _report_status(
    rows: tuple[ResearchMarketFeeDepthProbabilityBufferReportRow, ...],
) -> str:
    if not rows:
        return STATUS_BLOCK
    if any(row.buffer_status == STATUS_BLOCK for row in rows):
        return STATUS_BLOCK
    if any(row.buffer_status == STATUS_WATCH for row in rows):
        return STATUS_WATCH
    return STATUS_PASS


def _report_reason_codes(
    rows: tuple[ResearchMarketFeeDepthProbabilityBufferReportRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (REASON_MISSING_INPUTS,)
    reasons: list[str] = []
    for row in rows:
        reasons.extend(row.reason_codes)
    return _normalize_reason_codes(tuple(reasons), allow_empty=False)


def _status_count(
    rows: tuple[ResearchMarketFeeDepthProbabilityBufferReportRow, ...],
    status: str,
) -> Decimal:
    return _decimal_count(sum(1 for row in rows if row.buffer_status == status))


def _validate_row(row: ResearchMarketFeeDepthProbabilityBufferReportRow) -> None:
    if row.gross_probability_edge != _quantize(
        row.model_probability - row.market_probability,
    ):
        raise ValueError("gross_probability_edge must match probabilities")
    expected_required = _quantize(
        row.fee_buffer
        + row.spread_buffer
        + row.depth_shortfall_buffer
        + row.probability_uncertainty_buffer,
    )
    if row.required_probability_buffer != expected_required:
        raise ValueError("required_probability_buffer must match components")
    if row.net_probability_buffer != _quantize(
        row.gross_probability_edge - row.required_probability_buffer,
    ):
        raise ValueError("net_probability_buffer must match edge minus buffer")
    expected_status_reason = f"probability_buffer_{row.buffer_status}"
    if expected_status_reason not in row.reason_codes:
        raise ValueError("reason_codes must include buffer status")


def _validate_report(report: ResearchMarketFeeDepthProbabilityBufferReport) -> None:
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _status_count(report.rows, STATUS_PASS):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, STATUS_WATCH):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, STATUS_BLOCK):
        raise ValueError("block_count must match rows")
    net_buffers = tuple(row.net_probability_buffer for row in report.rows)
    if report.average_net_probability_buffer != _average(net_buffers):
        raise ValueError("average_net_probability_buffer must match rows")
    expected_top = report.rows[0].net_probability_buffer if report.rows else None
    if report.top_net_probability_buffer != expected_top:
        raise ValueError("top_net_probability_buffer must match rows")
    expected_max_buffer = _maximum(
        (row.required_probability_buffer for row in report.rows),
        ZERO,
    )
    if report.max_required_probability_buffer != expected_max_buffer:
        raise ValueError("max_required_probability_buffer must match rows")
    if report.report_status != _report_status(report.rows):
        raise ValueError("report_status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketFeeDepthProbabilityBufferInput, ...]:
    if isinstance(inputs, (str, bytes)) or not isinstance(inputs, Iterable):
        raise ValueError("inputs must be iterable")
    normalized: list[ResearchMarketFeeDepthProbabilityBufferInput] = []
    for item in inputs:
        if type(item) is not ResearchMarketFeeDepthProbabilityBufferInput:
            raise ValueError(
                "inputs must contain ResearchMarketFeeDepthProbabilityBufferInput",
            )
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: Sequence[ResearchMarketFeeDepthProbabilityBufferReportRow],
) -> tuple[ResearchMarketFeeDepthProbabilityBufferReportRow, ...]:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise ValueError("rows must be a sequence")
    normalized: list[ResearchMarketFeeDepthProbabilityBufferReportRow] = []
    for row in rows:
        if type(row) is not ResearchMarketFeeDepthProbabilityBufferReportRow:
            raise ValueError(
                "rows must contain ResearchMarketFeeDepthProbabilityBufferReportRow",
            )
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
    report: ResearchMarketFeeDepthProbabilityBufferReport,
) -> dict[str, Any]:
    values = asdict(report)
    values.pop("derived_validation_digest", None)
    return values


def _report_validation_digest(
    report: ResearchMarketFeeDepthProbabilityBufferReport,
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


def _validate_public_payload_digest(payload: dict[str, Any]) -> None:
    digest = payload.get("derived_validation_digest")
    _require_sha256_digest("derived_validation_digest", digest)
    unsigned_payload = dict(payload)
    unsigned_payload.pop("derived_validation_digest", None)
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    if hashlib.sha256(canonical.encode("utf-8")).hexdigest() != digest:
        raise ValueError("derived_validation_digest does not match report payload")


def _validate_public_payload_shape(payload: dict[str, Any]) -> None:
    _require_payload_keys("payload", payload, REPORT_PUBLIC_PAYLOAD_FIELDS)
    _require_payload_datetime_string("generated_at", payload["generated_at"])
    _require_public_identifier("config_version", payload["config_version"])
    if payload["config_version"] != DEFAULT_CONFIG_VERSION:
        raise ValueError("config_version must be the supported config version")
    for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
        _require_payload_decimal_string(
            field_name,
            payload[field_name],
            nonnegative=True,
        )
    for field_name in (
        "average_net_probability_buffer",
        "top_net_probability_buffer",
    ):
        if payload[field_name] is not None:
            _require_payload_decimal_string(field_name, payload[field_name])
    _require_payload_decimal_string(
        "max_required_probability_buffer",
        payload["max_required_probability_buffer"],
        nonnegative=True,
    )
    _require_status("report_status", payload["report_status"])
    _require_normalized_reason_payload("reason_codes", payload["reason_codes"])
    rows = payload["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a JSON list")
    for index, row in enumerate(rows):
        _validate_public_row_payload(index, row)


def _validate_public_row_payload(index: int, row: object) -> None:
    if type(row) is not dict:
        raise ValueError("rows must contain JSON objects")
    label = f"rows[{index}]"
    _require_payload_keys(label, row, ROW_PUBLIC_PAYLOAD_FIELDS)
    _require_sha256_digest(f"{label}.research_digest", row["research_digest"])
    _require_payload_decimal_string(f"{label}.rank", row["rank"], positive=True)
    _require_payload_datetime_string(f"{label}.observed_at", row["observed_at"])
    for field_name in ("model_probability", "market_probability"):
        _require_payload_decimal_string(
            f"{label}.{field_name}",
            row[field_name],
            probability=True,
        )
    for field_name in (
        "fee_buffer",
        "spread_buffer",
        "depth_shortfall_buffer",
        "probability_uncertainty_buffer",
        "required_probability_buffer",
    ):
        _require_payload_decimal_string(
            f"{label}.{field_name}",
            row[field_name],
            nonnegative=True,
        )
    for field_name in ("gross_probability_edge", "net_probability_buffer"):
        _require_payload_decimal_string(f"{label}.{field_name}", row[field_name])
    _require_status(f"{label}.buffer_status", row["buffer_status"])
    _require_normalized_reason_payload(
        f"{label}.reason_codes",
        row["reason_codes"],
    )
    _require_hard_flags(label, _DictFlags(row))


def _require_payload_keys(
    label: str,
    payload: Mapping[str, Any],
    expected_keys: frozenset[str],
) -> None:
    actual_keys = frozenset(payload)
    unexpected_keys = sorted(actual_keys - expected_keys)
    if unexpected_keys:
        raise ValueError(
            f"{label} has unexpected public payload field: {unexpected_keys[0]}",
        )
    missing_keys = sorted(expected_keys - actual_keys)
    if missing_keys:
        raise ValueError(f"{label} is missing public payload field: {missing_keys[0]}")


def _require_payload_datetime_string(field_name: str, value: object) -> datetime:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be an ISO datetime string")
    _reject_unsafe_public_string(field_name, value)
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO datetime string") from exc
    return _as_utc(field_name, parsed)


def _require_payload_decimal_string(
    field_name: str,
    value: object,
    *,
    nonnegative: bool = False,
    positive: bool = False,
    probability: bool = False,
) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    _reject_unsafe_public_string(field_name, value)
    try:
        parsed = Decimal(value)
    except Exception as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not parsed.is_finite():
        raise ValueError(f"{field_name} must be finite")
    normalized = _quantize(parsed)
    if str(normalized) != value:
        raise ValueError(f"{field_name} must be a six-place Decimal string")
    if nonnegative and normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if positive and normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    if probability and (normalized < ZERO or normalized > ONE):
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_normalized_reason_payload(
    field_name: str,
    value: object,
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a JSON list")
    normalized = _normalize_reason_codes(value, allow_empty=False)
    if tuple(value) != normalized:
        raise ValueError(f"{field_name} must be normalized")
    return normalized


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
    "ResearchMarketFeeDepthProbabilityBufferConfig",
    "ResearchMarketFeeDepthProbabilityBufferInput",
    "ResearchMarketFeeDepthProbabilityBufferReport",
    "ResearchMarketFeeDepthProbabilityBufferReportRow",
    "build_research_market_fee_depth_probability_buffer_report",
    "research_market_fee_depth_probability_buffer_report_payload",
)
