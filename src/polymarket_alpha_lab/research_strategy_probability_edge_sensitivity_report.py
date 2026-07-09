"""Pure probability-edge sensitivity report for bounded uncertainty review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_REPORT_CONFIG_VERSION = (
    "research-strategy-probability-edge-sensitivity-report-v0"
)
RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_STATUSES = (
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
    "candidate",
    "condition" + "_id",
    "credential",
    "dsn",
    "market" + "_id",
    "market" + "_slug",
    "private",
    "question",
    "secret",
    "slug",
    "source" + "_url",
    "source" + "_text",
    "table",
    "token",
    "url",
    "wal" + "let",
    "or" + "der",
    "li" + "ve",
    "trad" + "e",
    "trad" + "ing",
    "data" + "base",
    "net" + "work",
    "persist",
    "route",
    "exec" + "ute",
    "exec" + "ution",
    "signing",
    "mutation",
    "position",
    "b" + "uy",
    "se" + "ll",
    "reco" + "mmend",
    "siz" + "ing",
)

ROW_REASON_CODES = (
    "conservative_edge_block",
    "conservative_edge_watch",
    "fragility_block",
    "fragility_watch",
    "freshness_drift_block",
    "freshness_drift_watch",
    "probability_edge_sensitivity_pass",
)
REPORT_REASON_CODES = (
    "conservative_edge_review",
    "fragility_review",
    "freshness_drift_review",
    "probability_edge_sensitivity_report_block",
    "probability_edge_sensitivity_report_empty",
    "probability_edge_sensitivity_report_pass",
    "probability_edge_sensitivity_report_watch",
)
_PUBLIC_REASON_CODE_COUNT_FIELDS = frozenset(
    (
        "reason_code",
        "count",
        "input_ratio",
        "paper_only",
        "report_only",
        "readonly",
    ),
)
_PUBLIC_ROW_FIELDS = frozenset(
    (
        "observed_at",
        "model_probability",
        "quoted_probability",
        "gross_probability_edge",
        "model_uncertainty_bound",
        "fee_spread_haircut",
        "freshness_drift_haircut",
        "resolution_risk_haircut",
        "total_haircut",
        "conservative_probability_edge",
        "fragility_score",
        "status",
        "reason_codes",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
        "row_number",
    ),
)
_PUBLIC_REPORT_FIELDS = frozenset(
    (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "mean_gross_probability_edge",
        "mean_total_haircut",
        "mean_conservative_probability_edge",
        "max_fragility_score",
        "status",
        "reason_codes",
        "reason_code_counts",
        "rows",
        "derived_validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ),
)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeSensitivityConfig:
    config_version: str = (
        DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_REPORT_CONFIG_VERSION
    )
    pass_conservative_edge_floor: Decimal = Decimal("0.030000")
    watch_conservative_edge_floor: Decimal = Decimal("0.010000")
    pass_fragility_ceiling: Decimal = Decimal("0.500000")
    watch_fragility_ceiling: Decimal = Decimal("0.850000")
    freshness_drift_per_hour: Decimal = Decimal("0.001000")
    max_freshness_drift_haircut: Decimal = Decimal("0.100000")
    component_watch_haircut: Decimal = Decimal("0.020000")
    component_block_haircut: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeSensitivityConfig:
            raise ValueError(
                "config must be exactly ResearchStrategyProbabilityEdgeSensitivityConfig",
            )
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "pass_conservative_edge_floor",
            "watch_conservative_edge_floor",
            "pass_fragility_ceiling",
            "watch_fragility_ceiling",
            "freshness_drift_per_hour",
            "max_freshness_drift_haircut",
            "component_watch_haircut",
            "component_block_haircut",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.pass_conservative_edge_floor < self.watch_conservative_edge_floor:
            raise ValueError(
                "pass_conservative_edge_floor must be at least "
                "watch_conservative_edge_floor",
            )
        if self.pass_fragility_ceiling > self.watch_fragility_ceiling:
            raise ValueError(
                "pass_fragility_ceiling must not exceed watch_fragility_ceiling",
            )
        if self.component_block_haircut < self.component_watch_haircut:
            raise ValueError(
                "component_block_haircut must be at least component_watch_haircut",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeSensitivityInput:
    edge_ref: str
    observed_at: datetime
    model_probability: Decimal
    quoted_probability: Decimal
    model_uncertainty_bound: Decimal
    fee_haircut: Decimal
    spread_haircut: Decimal
    freshness_age_hours: Decimal
    resolution_risk_haircut: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeSensitivityInput:
            raise ValueError(
                "input must be exactly ResearchStrategyProbabilityEdgeSensitivityInput",
            )
        _require_input_ref("edge_ref", self.edge_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "quoted_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "model_uncertainty_bound",
            "fee_haircut",
            "spread_haircut",
            "freshness_age_hours",
            "resolution_risk_haircut",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount:
    reason_code: str
    count: Decimal
    input_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount:
            raise ValueError(
                "reason_code_count must be exactly "
                "ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount",
            )
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
class ResearchStrategyProbabilityEdgeSensitivityRow:
    edge_ref: str
    observed_at: datetime
    model_probability: Decimal
    quoted_probability: Decimal
    gross_probability_edge: Decimal
    model_uncertainty_bound: Decimal
    fee_spread_haircut: Decimal
    freshness_drift_haircut: Decimal
    resolution_risk_haircut: Decimal
    total_haircut: Decimal
    conservative_probability_edge: Decimal
    fragility_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeSensitivityRow:
            raise ValueError("row must be exactly ResearchStrategyProbabilityEdgeSensitivityRow")
        _require_input_ref("edge_ref", self.edge_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("model_probability", "quoted_probability"):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "gross_probability_edge",
            "conservative_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "model_uncertainty_bound",
            "fee_spread_haircut",
            "freshness_drift_haircut",
            "resolution_risk_haircut",
            "total_haircut",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "fragility_score",
            _normalize_probability("fragility_score", self.fragility_score),
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
class ResearchStrategyProbabilityEdgeSensitivityReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_gross_probability_edge: Decimal
    mean_total_haircut: Decimal
    mean_conservative_probability_edge: Decimal
    max_fragility_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount, ...]
    rows: tuple[ResearchStrategyProbabilityEdgeSensitivityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        if type(self) is not ResearchStrategyProbabilityEdgeSensitivityReport:
            raise ValueError(
                "report must be exactly ResearchStrategyProbabilityEdgeSensitivityReport",
            )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_gross_probability_edge",
            "mean_conservative_probability_edge",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "mean_total_haircut",
            _normalize_nonnegative_decimal(
                "mean_total_haircut",
                self.mean_total_haircut,
            ),
        )
        object.__setattr__(
            self,
            "max_fragility_score",
            _normalize_probability("max_fragility_score", self.max_fragility_score),
        )
        _require_status("status", self.status)
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, REPORT_REASON_CODES),
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


def build_research_strategy_probability_edge_sensitivity_report(
    inputs: Iterable[ResearchStrategyProbabilityEdgeSensitivityInput],
    *,
    config: ResearchStrategyProbabilityEdgeSensitivityConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilityEdgeSensitivityReport:
    if type(config) is not ResearchStrategyProbabilityEdgeSensitivityConfig:
        raise ValueError(
            "config must be a ResearchStrategyProbabilityEdgeSensitivityConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_inputs(inputs)
    rows = tuple(
        sorted(
            (
                _row_from_input(value, config=config, generated_at=generated_at_utc)
                for value in normalized_inputs
            ),
            key=_row_sort_key,
        ),
    )
    return ResearchStrategyProbabilityEdgeSensitivityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_gross_probability_edge=_mean(tuple(row.gross_probability_edge for row in rows)),
        mean_total_haircut=_mean(tuple(row.total_haircut for row in rows)),
        mean_conservative_probability_edge=_mean(
            tuple(row.conservative_probability_edge for row in rows),
        ),
        max_fragility_score=_max_decimal(tuple(row.fragility_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_probability_edge_sensitivity_report_payload(
    report: ResearchStrategyProbabilityEdgeSensitivityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyProbabilityEdgeSensitivityReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        payload = _public_report_payload(report)
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError(
            "report must be a ResearchStrategyProbabilityEdgeSensitivityReport",
        )
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _validate_public_payload_schema(payload)
    _reject_unsafe_public_payload("payload", payload)
    return payload


def _public_report_payload(
    report: ResearchStrategyProbabilityEdgeSensitivityReport,
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
    row: ResearchStrategyProbabilityEdgeSensitivityRow,
) -> dict[str, Any]:
    payload = asdict(row)
    payload.pop("edge_ref", None)
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
    value: ResearchStrategyProbabilityEdgeSensitivityInput,
    *,
    config: ResearchStrategyProbabilityEdgeSensitivityConfig,
    generated_at: datetime,
) -> ResearchStrategyProbabilityEdgeSensitivityRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    gross_probability_edge = _quantize(value.model_probability - value.quoted_probability)
    fee_spread_haircut = _quantize(value.fee_haircut + value.spread_haircut)
    freshness_drift_haircut = min(
        _quantize(value.freshness_age_hours * config.freshness_drift_per_hour),
        config.max_freshness_drift_haircut,
    )
    total_haircut = _quantize(
        value.model_uncertainty_bound
        + fee_spread_haircut
        + freshness_drift_haircut
        + value.resolution_risk_haircut,
    )
    conservative_probability_edge = _quantize(gross_probability_edge - total_haircut)
    fragility_score = _clamped_divide_decimal(total_haircut, _abs_decimal(gross_probability_edge))
    return ResearchStrategyProbabilityEdgeSensitivityRow(
        edge_ref=value.edge_ref,
        observed_at=observed_at,
        model_probability=value.model_probability,
        quoted_probability=value.quoted_probability,
        gross_probability_edge=gross_probability_edge,
        model_uncertainty_bound=value.model_uncertainty_bound,
        fee_spread_haircut=fee_spread_haircut,
        freshness_drift_haircut=freshness_drift_haircut,
        resolution_risk_haircut=value.resolution_risk_haircut,
        total_haircut=total_haircut,
        conservative_probability_edge=conservative_probability_edge,
        fragility_score=fragility_score,
        status=_row_status(
            conservative_probability_edge=conservative_probability_edge,
            fragility_score=fragility_score,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            conservative_probability_edge=conservative_probability_edge,
            fragility_score=fragility_score,
            freshness_drift_haircut=freshness_drift_haircut,
            config=config,
        ),
    )


def _row_status(
    *,
    conservative_probability_edge: Decimal,
    fragility_score: Decimal,
    config: ResearchStrategyProbabilityEdgeSensitivityConfig,
) -> str:
    if (
        conservative_probability_edge < config.watch_conservative_edge_floor
        or fragility_score > config.watch_fragility_ceiling
    ):
        return "block"
    if (
        conservative_probability_edge < config.pass_conservative_edge_floor
        or fragility_score > config.pass_fragility_ceiling
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    conservative_probability_edge: Decimal,
    fragility_score: Decimal,
    freshness_drift_haircut: Decimal,
    config: ResearchStrategyProbabilityEdgeSensitivityConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if conservative_probability_edge < config.watch_conservative_edge_floor:
        codes.append("conservative_edge_block")
    elif conservative_probability_edge < config.pass_conservative_edge_floor:
        codes.append("conservative_edge_watch")
    if fragility_score > config.watch_fragility_ceiling:
        codes.append("fragility_block")
    elif fragility_score > config.pass_fragility_ceiling:
        codes.append("fragility_watch")
    if freshness_drift_haircut >= config.component_block_haircut:
        codes.append("freshness_drift_block")
    elif freshness_drift_haircut >= config.component_watch_haircut:
        codes.append("freshness_drift_watch")
    if not codes:
        codes.append("probability_edge_sensitivity_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategyProbabilityEdgeSensitivityRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategyProbabilityEdgeSensitivityRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("probability_edge_sensitivity_report_empty",)
    report_status = _report_status(rows)
    codes: list[str] = []
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("conservative_edge_") for code in row_codes):
        codes.append("conservative_edge_review")
    if any(code.startswith("fragility_") for code in row_codes):
        codes.append("fragility_review")
    if any(code.startswith("freshness_drift_") for code in row_codes):
        codes.append("freshness_drift_review")
    codes.append(f"probability_edge_sensitivity_report_{report_status}")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyProbabilityEdgeSensitivityRow,
) -> tuple[int, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.conservative_probability_edge,
        _quantize(ONE - row.fragility_score),
        row.total_haircut,
        row.edge_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyProbabilityEdgeSensitivityInput],
) -> tuple[ResearchStrategyProbabilityEdgeSensitivityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyProbabilityEdgeSensitivityInput:
            raise ValueError(
                "inputs must contain ResearchStrategyProbabilityEdgeSensitivityInput values",
            )
        _require_hard_flags("input", value)
        if value.edge_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate edge_ref values")
        seen_refs.add(value.edge_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyProbabilityEdgeSensitivityRow],
) -> tuple[ResearchStrategyProbabilityEdgeSensitivityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyProbabilityEdgeSensitivityRow:
            raise ValueError(
                "rows must contain ResearchStrategyProbabilityEdgeSensitivityRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.edge_ref in seen_refs:
            raise ValueError("rows must not contain duplicate edge_ref values")
        seen_refs.add(row.edge_ref)
    return normalized


def _validate_row_consistency(
    row: ResearchStrategyProbabilityEdgeSensitivityRow,
) -> None:
    if row.gross_probability_edge != _quantize(
        row.model_probability - row.quoted_probability,
    ):
        raise ValueError("gross_probability_edge must match model and quoted probabilities")
    if row.total_haircut != _quantize(
        row.model_uncertainty_bound
        + row.fee_spread_haircut
        + row.freshness_drift_haircut
        + row.resolution_risk_haircut,
    ):
        raise ValueError("total_haircut must match component haircuts")
    if row.conservative_probability_edge != _quantize(
        row.gross_probability_edge - row.total_haircut,
    ):
        raise ValueError("conservative_probability_edge must match edge less haircuts")
    expected_fragility = _clamped_divide_decimal(
        row.total_haircut,
        _abs_decimal(row.gross_probability_edge),
    )
    if row.fragility_score != expected_fragility:
        raise ValueError("fragility_score must match total haircut divided by gross edge")
    if row.status == "pass" and row.reason_codes != ("probability_edge_sensitivity_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategyProbabilityEdgeSensitivityReport,
) -> None:
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.input_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_gross_probability_edge != _mean(
        tuple(row.gross_probability_edge for row in report.rows),
    ):
        raise ValueError("mean_gross_probability_edge must match rows")
    if report.mean_total_haircut != _mean(tuple(row.total_haircut for row in report.rows)):
        raise ValueError("mean_total_haircut must match rows")
    if report.mean_conservative_probability_edge != _mean(
        tuple(row.conservative_probability_edge for row in report.rows),
    ):
        raise ValueError("mean_conservative_probability_edge must match rows")
    if report.max_fragility_score != _max_decimal(
        tuple(row.fragility_score for row in report.rows),
    ):
        raise ValueError("max_fragility_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(
    report: ResearchStrategyProbabilityEdgeSensitivityReport,
) -> None:
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


def _validate_public_payload_schema(payload: dict[str, Any]) -> None:
    _require_public_keys("payload", payload, _PUBLIC_REPORT_FIELDS)
    _require_public_datetime("payload.generated_at", payload.get("generated_at"))
    _require_canonical_public_string("payload.config_version", payload.get("config_version"))
    for field_name in (
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "max_fragility_score",
    ):
        _normalize_nonnegative_decimal_string(
            f"payload.{field_name}",
            payload.get(field_name),
        )
    for field_name in (
        "mean_gross_probability_edge",
        "mean_total_haircut",
        "mean_conservative_probability_edge",
    ):
        _normalize_decimal_string(f"payload.{field_name}", payload.get(field_name))
    _require_status("payload.status", payload.get("status"))
    _normalize_public_reason_codes(
        "payload.reason_codes",
        payload.get("reason_codes"),
        REPORT_REASON_CODES,
    )
    _validate_public_reason_code_counts(payload.get("reason_code_counts"))
    _validate_public_rows(payload.get("rows"))
    _require_digest(
        "payload.derived_validation_digest",
        payload.get("derived_validation_digest"),
    )


def _validate_public_reason_code_counts(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.reason_code_counts must be a public list")
    for index, item in enumerate(value):
        if type(item) is not dict:
            raise ValueError("payload.reason_code_counts must contain public objects")
        label = f"payload.reason_code_counts[{index}]"
        _require_public_keys(label, item, _PUBLIC_REASON_CODE_COUNT_FIELDS)
        _require_reason_code(f"{label}.reason_code", item.get("reason_code"))
        _normalize_nonnegative_decimal_string(f"{label}.count", item.get("count"))
        _normalize_probability_decimal_string(f"{label}.input_ratio", item.get("input_ratio"))
        _require_hard_flags(label, _DictFlags(item))


def _validate_public_rows(value: object) -> None:
    if type(value) is not list:
        raise ValueError("payload.rows must be a public list")
    for index, item in enumerate(value):
        if type(item) is not dict:
            raise ValueError("payload.rows must contain public objects")
        label = f"payload.rows[{index}]"
        _require_public_keys(label, item, _PUBLIC_ROW_FIELDS)
        _require_public_datetime(f"{label}.observed_at", item.get("observed_at"))
        for field_name in (
            "model_probability",
            "quoted_probability",
            "fragility_score",
        ):
            _normalize_probability_decimal_string(
                f"{label}.{field_name}",
                item.get(field_name),
            )
        for field_name in (
            "gross_probability_edge",
            "conservative_probability_edge",
        ):
            _normalize_decimal_string(f"{label}.{field_name}", item.get(field_name))
        for field_name in (
            "model_uncertainty_bound",
            "fee_spread_haircut",
            "freshness_drift_haircut",
            "resolution_risk_haircut",
            "total_haircut",
            "row_number",
        ):
            _normalize_nonnegative_decimal_string(
                f"{label}.{field_name}",
                item.get(field_name),
            )
        _require_status(f"{label}.status", item.get("status"))
        _normalize_public_reason_codes(
            f"{label}.reason_codes",
            item.get("reason_codes"),
            ROW_REASON_CODES,
        )
        _require_digest(
            f"{label}.derived_validation_digest",
            item.get("derived_validation_digest"),
        )
        _require_hard_flags(label, _DictFlags(item))


def _require_public_keys(
    name: str,
    value: dict[str, Any],
    supported: frozenset[str],
) -> None:
    keys = frozenset(value)
    if keys != supported:
        raise ValueError(f"{name} must contain only public diagnostic fields")


def _normalize_public_reason_codes(
    name: str,
    value: object,
    supported: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{name} must be a public list")
    return _normalize_reason_codes(name, tuple(value), supported)


def _normalize_probability_decimal_string(name: str, value: object) -> Decimal:
    return _normalize_probability(name, _decimal_from_public_string(name, value))


def _normalize_nonnegative_decimal_string(name: str, value: object) -> Decimal:
    return _normalize_nonnegative_decimal(name, _decimal_from_public_string(name, value))


def _normalize_decimal_string(name: str, value: object) -> Decimal:
    return _normalize_decimal(name, _decimal_from_public_string(name, value))


def _decimal_from_public_string(name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{name} must be a Decimal-derived public string")
    try:
        return Decimal(value)
    except Exception as exc:
        raise ValueError(f"{name} must be a Decimal-derived public string") from exc


def _require_public_datetime(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a public datetime string")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a public datetime string") from exc
    _as_utc(name, parsed)


def _status_count(
    rows: tuple[ResearchStrategyProbabilityEdgeSensitivityRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyProbabilityEdgeSensitivityRow, ...],
) -> tuple[ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount(
                reason_code="probability_edge_sensitivity_report_empty",
                count=_count(1),
                input_ratio=ZERO.quantize(RATIO_QUANTUM),
            ),
        )
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount(
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
    value: Iterable[ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount],
) -> tuple[ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left / right)


def _clamped_divide_decimal(left: Decimal, right: Decimal) -> Decimal:
    if right == ZERO:
        return ONE.quantize(RATIO_QUANTUM)
    return _clamp_probability(_divide_decimal(left, right))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return _divide_decimal(_sum_decimals(values), _count(len(values)))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    return max(values).quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(RATIO_QUANTUM)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


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


def _normalize_nonnegative_decimal(name: str, value: object) -> Decimal:
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


def _clamp_probability(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO.quantize(RATIO_QUANTUM)
    if normalized > ONE:
        return ONE.quantize(RATIO_QUANTUM)
    return normalized


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_status(name: str, value: object) -> None:
    if (
        type(value) is not str
        or value not in RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")


def _require_reason_code(name: str, value: object) -> None:
    if type(value) is not str or not value:
        raise ValueError(f"{name} must be a non-empty string")
    _require_canonical_public_string(name, value)
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


def _require_canonical_public_string(name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a canonical public string")
    lowered = value.lower()
    if any(fragment in lowered for fragment in _UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"{name} has unsafe public text")


def _require_input_ref(name: str, value: object) -> None:
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
    "DEFAULT_RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_PROBABILITY_EDGE_SENSITIVITY_STATUSES",
    "ResearchStrategyProbabilityEdgeSensitivityConfig",
    "ResearchStrategyProbabilityEdgeSensitivityInput",
    "ResearchStrategyProbabilityEdgeSensitivityReasonCodeCount",
    "ResearchStrategyProbabilityEdgeSensitivityRow",
    "ResearchStrategyProbabilityEdgeSensitivityReport",
    "build_research_strategy_probability_edge_sensitivity_report",
    "research_strategy_probability_edge_sensitivity_report_payload",
)
