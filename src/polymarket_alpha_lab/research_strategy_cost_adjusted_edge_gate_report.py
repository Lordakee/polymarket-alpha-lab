"""Pure cost-adjusted forecast edge gate report for manual research."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_REPORT_CONFIG_VERSION = (
    "research-strategy-cost-adjusted-edge-gate-report-v0"
)
RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_STATUSES = (
    "pass",
    "watch",
    "block",
)

RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "au" + "th",
    "candidate" + "_id",
    "credential",
    "data" + "base",
    "dsn",
    "market" + "_id",
    "market" + "_slug",
    "private",
    "ques" + "tion",
    "secret",
    "source" + "_text",
    "source" + "_url",
    "table",
    "token",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "net" + "work",
    "persist",
    "signing",
    "mutation",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmendation",
    "siz" + "ing",
)

ROW_REASON_CODES = (
    "cost_adjusted_edge_gate_pass",
    "depth_quality_block",
    "depth_quality_watch",
    "forecast_confidence_block",
    "forecast_confidence_watch",
    "latency_quality_block",
    "latency_quality_watch",
    "total_friction_block",
    "total_friction_watch",
    "usable_edge_block",
    "usable_edge_watch",
)
REPORT_REASON_CODES = (
    "cost_adjusted_edge_gate_report_block",
    "cost_adjusted_edge_gate_report_empty",
    "cost_adjusted_edge_gate_report_pass",
    "cost_adjusted_edge_gate_report_watch",
    "depth_quality_review",
    "forecast_confidence_review",
    "latency_quality_review",
    "total_friction_review",
    "usable_edge_review",
)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedEdgeGateConfig:
    config_version: str
    usable_edge_pass_floor: Decimal
    usable_edge_watch_floor: Decimal
    total_friction_pass_ceiling: Decimal
    total_friction_watch_ceiling: Decimal
    forecast_confidence_pass_floor: Decimal
    forecast_confidence_watch_floor: Decimal
    depth_quality_pass_floor: Decimal
    depth_quality_watch_floor: Decimal
    latency_quality_pass_floor: Decimal
    latency_quality_watch_floor: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "usable_edge_pass_floor",
            "usable_edge_watch_floor",
            "total_friction_pass_ceiling",
            "total_friction_watch_ceiling",
            "forecast_confidence_pass_floor",
            "forecast_confidence_watch_floor",
            "depth_quality_pass_floor",
            "depth_quality_watch_floor",
            "latency_quality_pass_floor",
            "latency_quality_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "usable_edge",
            self.usable_edge_pass_floor,
            self.usable_edge_watch_floor,
        )
        _require_ceiling_pair(
            "total_friction",
            self.total_friction_pass_ceiling,
            self.total_friction_watch_ceiling,
        )
        _require_floor_pair(
            "forecast_confidence",
            self.forecast_confidence_pass_floor,
            self.forecast_confidence_watch_floor,
        )
        _require_floor_pair(
            "depth_quality",
            self.depth_quality_pass_floor,
            self.depth_quality_watch_floor,
        )
        _require_floor_pair(
            "latency_quality",
            self.latency_quality_pass_floor,
            self.latency_quality_watch_floor,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedEdgeGateInput:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    candidate_forecast_probability: Decimal
    market_probability: Decimal
    fee_probability_drag: Decimal
    spread_probability_drag: Decimal
    depth_probability_drag: Decimal
    latency_probability_haircut: Decimal
    forecast_confidence_score: Decimal
    depth_quality_score: Decimal
    latency_quality_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "candidate_forecast_probability",
            "market_probability",
            "fee_probability_drag",
            "spread_probability_drag",
            "depth_probability_drag",
            "latency_probability_haircut",
            "forecast_confidence_score",
            "depth_quality_score",
            "latency_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedEdgeGateReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _normalize_nonnegative_count("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategyCostAdjustedEdgeGateRow:
    candidate_id: str
    market_id: str
    market_slug: str
    market_question: str
    source_url: str
    source_text: str
    observed_at: datetime
    candidate_forecast_probability: Decimal
    market_probability: Decimal
    raw_forecast_edge_probability: Decimal
    absolute_forecast_edge_probability: Decimal
    fee_probability_drag: Decimal
    spread_probability_drag: Decimal
    depth_probability_drag: Decimal
    latency_probability_haircut: Decimal
    total_friction_probability: Decimal
    usable_edge_probability: Decimal
    forecast_confidence_score: Decimal
    depth_quality_score: Decimal
    latency_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_url",
            "source_text",
        ):
            _require_private_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "candidate_forecast_probability",
            "market_probability",
            "absolute_forecast_edge_probability",
            "fee_probability_drag",
            "spread_probability_drag",
            "depth_probability_drag",
            "latency_probability_haircut",
            "total_friction_probability",
            "forecast_confidence_score",
            "depth_quality_score",
            "latency_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in ("raw_forecast_edge_probability", "usable_edge_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
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
class ResearchStrategyCostAdjustedEdgeGateReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_absolute_forecast_edge_probability: Decimal
    mean_total_friction_probability: Decimal
    mean_usable_edge_probability: Decimal
    mean_forecast_confidence_score: Decimal
    mean_depth_quality_score: Decimal
    mean_latency_quality_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyCostAdjustedEdgeGateReasonCodeCount, ...]
    rows: tuple[ResearchStrategyCostAdjustedEdgeGateRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_absolute_forecast_edge_probability",
            "mean_total_friction_probability",
            "mean_forecast_confidence_score",
            "mean_depth_quality_score",
            "mean_latency_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_usable_edge_probability",
            _normalize_decimal("mean_usable_edge_probability", self.mean_usable_edge_probability),
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


def build_research_strategy_cost_adjusted_edge_gate_report(
    inputs: Iterable[ResearchStrategyCostAdjustedEdgeGateInput],
    *,
    config: ResearchStrategyCostAdjustedEdgeGateConfig,
    generated_at: datetime,
) -> ResearchStrategyCostAdjustedEdgeGateReport:
    if type(config) is not ResearchStrategyCostAdjustedEdgeGateConfig:
        raise ValueError("config must be a ResearchStrategyCostAdjustedEdgeGateConfig")
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
    return ResearchStrategyCostAdjustedEdgeGateReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_absolute_forecast_edge_probability=_mean(
            tuple(row.absolute_forecast_edge_probability for row in rows),
        ),
        mean_total_friction_probability=_mean(
            tuple(row.total_friction_probability for row in rows),
        ),
        mean_usable_edge_probability=_mean(
            tuple(row.usable_edge_probability for row in rows),
        ),
        mean_forecast_confidence_score=_mean(
            tuple(row.forecast_confidence_score for row in rows),
        ),
        mean_depth_quality_score=_mean(
            tuple(row.depth_quality_score for row in rows),
        ),
        mean_latency_quality_score=_mean(
            tuple(row.latency_quality_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_cost_adjusted_edge_gate_report_payload(
    report: ResearchStrategyCostAdjustedEdgeGateReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyCostAdjustedEdgeGateReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyCostAdjustedEdgeGateReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategyCostAdjustedEdgeGateReport,
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
    row: ResearchStrategyCostAdjustedEdgeGateRow,
) -> dict[str, Any]:
    payload = asdict(row)
    for field_name in (
        "candidate_id",
        "market_id",
        "market_slug",
        "market_question",
        "source_url",
        "source_text",
    ):
        payload.pop(field_name, None)
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
    value: ResearchStrategyCostAdjustedEdgeGateInput,
    *,
    config: ResearchStrategyCostAdjustedEdgeGateConfig,
    generated_at: datetime,
) -> ResearchStrategyCostAdjustedEdgeGateRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    raw_edge = _subtract_decimal(
        value.candidate_forecast_probability,
        value.market_probability,
    )
    absolute_edge = _absolute_decimal(raw_edge)
    total_friction = _sum_decimals(
        (
            value.fee_probability_drag,
            value.spread_probability_drag,
            value.depth_probability_drag,
            value.latency_probability_haircut,
        ),
    )
    usable_edge = _subtract_decimal(absolute_edge, total_friction)
    return ResearchStrategyCostAdjustedEdgeGateRow(
        candidate_id=value.candidate_id,
        market_id=value.market_id,
        market_slug=value.market_slug,
        market_question=value.market_question,
        source_url=value.source_url,
        source_text=value.source_text,
        observed_at=observed_at,
        candidate_forecast_probability=value.candidate_forecast_probability,
        market_probability=value.market_probability,
        raw_forecast_edge_probability=raw_edge,
        absolute_forecast_edge_probability=absolute_edge,
        fee_probability_drag=value.fee_probability_drag,
        spread_probability_drag=value.spread_probability_drag,
        depth_probability_drag=value.depth_probability_drag,
        latency_probability_haircut=value.latency_probability_haircut,
        total_friction_probability=total_friction,
        usable_edge_probability=usable_edge,
        forecast_confidence_score=value.forecast_confidence_score,
        depth_quality_score=value.depth_quality_score,
        latency_quality_score=value.latency_quality_score,
        status=_row_status(
            usable_edge_probability=usable_edge,
            total_friction_probability=total_friction,
            value=value,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            usable_edge_probability=usable_edge,
            total_friction_probability=total_friction,
            value=value,
            config=config,
        ),
    )


def _row_status(
    *,
    usable_edge_probability: Decimal,
    total_friction_probability: Decimal,
    value: ResearchStrategyCostAdjustedEdgeGateInput,
    config: ResearchStrategyCostAdjustedEdgeGateConfig,
) -> str:
    if (
        usable_edge_probability < config.usable_edge_watch_floor
        or total_friction_probability > config.total_friction_watch_ceiling
        or value.forecast_confidence_score < config.forecast_confidence_watch_floor
        or value.depth_quality_score < config.depth_quality_watch_floor
        or value.latency_quality_score < config.latency_quality_watch_floor
    ):
        return "block"
    if (
        usable_edge_probability < config.usable_edge_pass_floor
        or total_friction_probability > config.total_friction_pass_ceiling
        or value.forecast_confidence_score < config.forecast_confidence_pass_floor
        or value.depth_quality_score < config.depth_quality_pass_floor
        or value.latency_quality_score < config.latency_quality_pass_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    usable_edge_probability: Decimal,
    total_friction_probability: Decimal,
    value: ResearchStrategyCostAdjustedEdgeGateInput,
    config: ResearchStrategyCostAdjustedEdgeGateConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if usable_edge_probability < config.usable_edge_watch_floor:
        codes.append("usable_edge_block")
    elif usable_edge_probability < config.usable_edge_pass_floor:
        codes.append("usable_edge_watch")
    if total_friction_probability > config.total_friction_watch_ceiling:
        codes.append("total_friction_block")
    elif total_friction_probability > config.total_friction_pass_ceiling:
        codes.append("total_friction_watch")
    if value.forecast_confidence_score < config.forecast_confidence_watch_floor:
        codes.append("forecast_confidence_block")
    elif value.forecast_confidence_score < config.forecast_confidence_pass_floor:
        codes.append("forecast_confidence_watch")
    if value.depth_quality_score < config.depth_quality_watch_floor:
        codes.append("depth_quality_block")
    elif value.depth_quality_score < config.depth_quality_pass_floor:
        codes.append("depth_quality_watch")
    if value.latency_quality_score < config.latency_quality_watch_floor:
        codes.append("latency_quality_block")
    elif value.latency_quality_score < config.latency_quality_pass_floor:
        codes.append("latency_quality_watch")
    if not codes:
        codes.append("cost_adjusted_edge_gate_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyCostAdjustedEdgeGateRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyCostAdjustedEdgeGateRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("cost_adjusted_edge_gate_report_empty",)
    report_status = _report_status(rows)
    codes = [f"cost_adjusted_edge_gate_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("usable_edge_") for code in row_codes):
        codes.append("usable_edge_review")
    if any(code.startswith("total_friction_") for code in row_codes):
        codes.append("total_friction_review")
    if any(code.startswith("forecast_confidence_") for code in row_codes):
        codes.append("forecast_confidence_review")
    if any(code.startswith("depth_quality_") for code in row_codes):
        codes.append("depth_quality_review")
    if any(code.startswith("latency_quality_") for code in row_codes):
        codes.append("latency_quality_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyCostAdjustedEdgeGateRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.usable_edge_probability,
        -row.total_friction_probability,
        row.forecast_confidence_score,
        row.depth_quality_score,
        row.latency_quality_score,
        row.candidate_id,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyCostAdjustedEdgeGateInput],
) -> tuple[ResearchStrategyCostAdjustedEdgeGateInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyCostAdjustedEdgeGateInput:
            raise ValueError(
                "inputs must contain ResearchStrategyCostAdjustedEdgeGateInput values",
            )
        _require_hard_flags("input", value)
        if value.candidate_id in seen_refs:
            raise ValueError("inputs must not contain duplicate candidate_id values")
        seen_refs.add(value.candidate_id)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyCostAdjustedEdgeGateRow],
) -> tuple[ResearchStrategyCostAdjustedEdgeGateRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyCostAdjustedEdgeGateRow:
            raise ValueError(
                "rows must contain ResearchStrategyCostAdjustedEdgeGateRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.candidate_id in seen_refs:
            raise ValueError("rows must not contain duplicate candidate_id values")
        seen_refs.add(row.candidate_id)
    return normalized


def _validate_row_consistency(
    row: ResearchStrategyCostAdjustedEdgeGateRow,
) -> None:
    expected_raw_edge = _subtract_decimal(
        row.candidate_forecast_probability,
        row.market_probability,
    )
    if row.raw_forecast_edge_probability != expected_raw_edge:
        raise ValueError("raw_forecast_edge_probability does not match probabilities")
    if row.absolute_forecast_edge_probability != _absolute_decimal(expected_raw_edge):
        raise ValueError("absolute_forecast_edge_probability does not match raw edge")
    expected_friction = _sum_decimals(
        (
            row.fee_probability_drag,
            row.spread_probability_drag,
            row.depth_probability_drag,
            row.latency_probability_haircut,
        ),
    )
    if row.total_friction_probability != expected_friction:
        raise ValueError("total_friction_probability does not match friction inputs")
    expected_usable_edge = _subtract_decimal(
        row.absolute_forecast_edge_probability,
        row.total_friction_probability,
    )
    if row.usable_edge_probability != expected_usable_edge:
        raise ValueError("usable_edge_probability does not match row inputs")
    if row.status == "pass" and row.reason_codes != ("cost_adjusted_edge_gate_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyCostAdjustedEdgeGateReport,
) -> None:
    if report.source_row_count != _count(len(report.rows)):
        raise ValueError("source_row_count must match rows")
    if report.source_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match source_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_absolute_forecast_edge_probability != _mean(
        tuple(row.absolute_forecast_edge_probability for row in report.rows),
    ):
        raise ValueError("mean_absolute_forecast_edge_probability must match rows")
    if report.mean_total_friction_probability != _mean(
        tuple(row.total_friction_probability for row in report.rows),
    ):
        raise ValueError("mean_total_friction_probability must match rows")
    if report.mean_usable_edge_probability != _mean(
        tuple(row.usable_edge_probability for row in report.rows),
    ):
        raise ValueError("mean_usable_edge_probability must match rows")
    if report.mean_forecast_confidence_score != _mean(
        tuple(row.forecast_confidence_score for row in report.rows),
    ):
        raise ValueError("mean_forecast_confidence_score must match rows")
    if report.mean_depth_quality_score != _mean(
        tuple(row.depth_quality_score for row in report.rows),
    ):
        raise ValueError("mean_depth_quality_score must match rows")
    if report.mean_latency_quality_score != _mean(
        tuple(row.latency_quality_score for row in report.rows),
    ):
        raise ValueError("mean_latency_quality_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyCostAdjustedEdgeGateReport) -> None:
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
    rows: tuple[ResearchStrategyCostAdjustedEdgeGateRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyCostAdjustedEdgeGateRow, ...],
) -> tuple[ResearchStrategyCostAdjustedEdgeGateReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyCostAdjustedEdgeGateReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
            input_ratio=_divide_decimal(_count(count), denominator),
        )
        for reason_code, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def _normalize_reason_code_counts(
    value: Iterable[ResearchStrategyCostAdjustedEdgeGateReasonCodeCount],
) -> tuple[ResearchStrategyCostAdjustedEdgeGateReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyCostAdjustedEdgeGateReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchStrategyCostAdjustedEdgeGateReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _absolute_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


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
        return value.quantize(RATIO_QUANTUM)


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
    if type(value) is not str or value not in RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_STATUSES:
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


def _require_private_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical string")


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
        return str(value.quantize(RATIO_QUANTUM))
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
    "DEFAULT_RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_COST_ADJUSTED_EDGE_GATE_STATUSES",
    "ResearchStrategyCostAdjustedEdgeGateConfig",
    "ResearchStrategyCostAdjustedEdgeGateInput",
    "ResearchStrategyCostAdjustedEdgeGateReasonCodeCount",
    "ResearchStrategyCostAdjustedEdgeGateRow",
    "ResearchStrategyCostAdjustedEdgeGateReport",
    "build_research_strategy_cost_adjusted_edge_gate_report",
    "research_strategy_cost_adjusted_edge_gate_report_payload",
)
