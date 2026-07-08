"""Pure EV input quality report reducer for manual review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_EV_INPUT_QUALITY_REPORT_CONFIG_VERSION = (
    "research-strategy-ev-input-quality-report-v0"
)
RESEARCH_STRATEGY_EV_INPUT_QUALITY_STATUSES = ("pass", "watch", "block")

COUNT_QUANTUM = Decimal("1")
RATIO_QUANTUM = Decimal("0.000001")
ZERO = Decimal("0")
ONE = Decimal("1")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)

ROW_REASON_CODES = (
    "cost_inputs_block",
    "cost_inputs_watch",
    "ev_input_quality_pass",
    "liquidity_block",
    "liquidity_watch",
    "probability_calibration_block",
    "probability_calibration_missing_resolution",
    "probability_calibration_watch",
    "resolution_rule_block",
    "resolution_rule_watch",
    "source_confidence_block",
    "source_confidence_watch",
)
_WATCH_SENTINEL_CODES = frozenset(
    {
        "probability_calibration_missing_resolution",
    },
)
REPORT_REASON_CODES = (
    "cost_input_review",
    "input_quality_block",
    "input_quality_pass",
    "input_quality_watch",
    "liquidity_review",
    "probability_calibration_review",
    "resolution_rule_review",
    "source_confidence_review",
)
_PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")
_UNSAFE_PUBLIC_FRAGMENTS = (
    "auth",
    "candidate",
    "condition_" + "id",
    "credential",
    "dsn",
    "http",
    "market_" + "id",
    "market_" + "slug",
    "private",
    "question",
    "secret",
    "slug",
    "source_" + "text",
    "source_" + "url",
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
    "signing",
    "mutation",
    "b" + "uy",
    "se" + "ll",
)


@dataclass(frozen=True)
class ResearchStrategyEvInputQualityConfig:
    config_version: str
    calibration_watch_error_threshold: Decimal
    calibration_block_error_threshold: Decimal
    cost_watch_probability_threshold: Decimal
    cost_block_probability_threshold: Decimal
    liquidity_watch_score_floor: Decimal
    liquidity_block_score_floor: Decimal
    source_confidence_watch_score_floor: Decimal
    source_confidence_block_score_floor: Decimal
    resolution_rule_watch_score_floor: Decimal
    resolution_rule_block_score_floor: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "calibration_watch_error_threshold",
            "calibration_block_error_threshold",
            "cost_watch_probability_threshold",
            "cost_block_probability_threshold",
            "liquidity_watch_score_floor",
            "liquidity_block_score_floor",
            "source_confidence_watch_score_floor",
            "source_confidence_block_score_floor",
            "resolution_rule_watch_score_floor",
            "resolution_rule_block_score_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_threshold_pair(
            "calibration threshold",
            self.calibration_watch_error_threshold,
            self.calibration_block_error_threshold,
        )
        _require_threshold_pair(
            "cost threshold",
            self.cost_watch_probability_threshold,
            self.cost_block_probability_threshold,
        )
        _require_floor_pair(
            "liquidity threshold",
            self.liquidity_watch_score_floor,
            self.liquidity_block_score_floor,
        )
        _require_floor_pair(
            "source confidence threshold",
            self.source_confidence_watch_score_floor,
            self.source_confidence_block_score_floor,
        )
        _require_floor_pair(
            "resolution rule threshold",
            self.resolution_rule_watch_score_floor,
            self.resolution_rule_block_score_floor,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategyEvInputQualityInput:
    ev_case_ref: str
    strategy_ref: str
    market_slug: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    resolved_probability: Decimal | None
    fee_probability_cost: Decimal
    spread_probability_cost: Decimal
    slippage_probability_cost: Decimal
    liquidity_score: Decimal
    source_confidence_score: Decimal
    resolution_rule_completeness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("ev_case_ref", "strategy_ref", "market_slug"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_probability_cost",
            "spread_probability_cost",
            "slippage_probability_cost",
            "liquidity_score",
            "source_confidence_score",
            "resolution_rule_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.resolved_probability is not None:
            object.__setattr__(
                self,
                "resolved_probability",
                _normalize_resolved_probability(
                    "resolved_probability",
                    self.resolved_probability,
                ),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategyEvInputQualityRow:
    ev_case_ref: str
    strategy_ref: str
    market_group_ref: str
    observed_at: datetime
    forecast_probability: Decimal
    market_probability: Decimal
    resolved_probability: Decimal | None
    forecast_market_gap_probability: Decimal
    probability_calibration_error: Decimal
    fee_probability_cost: Decimal
    spread_probability_cost: Decimal
    slippage_probability_cost: Decimal
    total_cost_probability: Decimal
    liquidity_score: Decimal
    source_confidence_score: Decimal
    resolution_rule_completeness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("ev_case_ref", "strategy_ref", "market_group_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "forecast_probability",
            "market_probability",
            "fee_probability_cost",
            "spread_probability_cost",
            "slippage_probability_cost",
            "liquidity_score",
            "source_confidence_score",
            "resolution_rule_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        if self.resolved_probability is not None:
            object.__setattr__(
                self,
                "resolved_probability",
                _normalize_resolved_probability(
                    "resolved_probability",
                    self.resolved_probability,
                ),
            )
        for field_name in (
            "forecast_market_gap_probability",
            "probability_calibration_error",
            "total_cost_probability",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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
class ResearchStrategyEvInputQualityReport:
    generated_at: datetime
    config_version: str
    source_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_probability_calibration_error: Decimal
    mean_total_cost_probability: Decimal
    mean_liquidity_score: Decimal
    mean_source_confidence_score: Decimal
    mean_resolution_rule_completeness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[tuple[str, Decimal], ...]
    rows: tuple[ResearchStrategyEvInputQualityRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("source_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_probability_calibration_error",
            "mean_total_cost_probability",
            "mean_liquidity_score",
            "mean_source_confidence_score",
            "mean_resolution_rule_completeness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
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


def build_research_strategy_ev_input_quality_report(
    inputs: Iterable[ResearchStrategyEvInputQualityInput],
    *,
    config: ResearchStrategyEvInputQualityConfig,
    generated_at: datetime,
) -> ResearchStrategyEvInputQualityReport:
    if type(config) is not ResearchStrategyEvInputQualityConfig:
        raise ValueError("config must be a ResearchStrategyEvInputQualityConfig")
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
    return ResearchStrategyEvInputQualityReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        source_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_probability_calibration_error=_mean(
            tuple(
                row.probability_calibration_error
                for row in rows
                if row.resolved_probability is not None
            ),
        ),
        mean_total_cost_probability=_mean(tuple(row.total_cost_probability for row in rows)),
        mean_liquidity_score=_mean(tuple(row.liquidity_score for row in rows)),
        mean_source_confidence_score=_mean(tuple(row.source_confidence_score for row in rows)),
        mean_resolution_rule_completeness_score=_mean(
            tuple(row.resolution_rule_completeness_score for row in rows),
        ),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_ev_input_quality_report_payload(
    report: ResearchStrategyEvInputQualityReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategyEvInputQualityReport:
        _require_hard_flags("report", report)
        _verify_report_integrity(report)
        _reject_unsafe_public_payload("report", report)
        payload = _json_ready(asdict(report))
    elif type(report) is dict:
        _require_hard_flags("payload", _DictFlags(report))
        _reject_unsafe_public_payload("payload", report)
        _verify_public_payload_integrity(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchStrategyEvInputQualityReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload("payload", payload)
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


def _row_from_input(
    value: ResearchStrategyEvInputQualityInput,
    *,
    config: ResearchStrategyEvInputQualityConfig,
    generated_at: datetime,
) -> ResearchStrategyEvInputQualityRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    return ResearchStrategyEvInputQualityRow(
        ev_case_ref=value.ev_case_ref,
        strategy_ref=value.strategy_ref,
        market_group_ref=_public_market_group_ref(value.market_slug),
        observed_at=observed_at,
        forecast_probability=value.forecast_probability,
        market_probability=value.market_probability,
        resolved_probability=value.resolved_probability,
        forecast_market_gap_probability=_abs_decimal(
            _subtract_decimal(value.forecast_probability, value.market_probability),
        ),
        probability_calibration_error=_probability_calibration_error(value),
        fee_probability_cost=value.fee_probability_cost,
        spread_probability_cost=value.spread_probability_cost,
        slippage_probability_cost=value.slippage_probability_cost,
        total_cost_probability=_sum_decimals(
            (
                value.fee_probability_cost,
                value.spread_probability_cost,
                value.slippage_probability_cost,
            ),
        ),
        liquidity_score=value.liquidity_score,
        source_confidence_score=value.source_confidence_score,
        resolution_rule_completeness_score=value.resolution_rule_completeness_score,
        status=_row_status(value, config),
        reason_codes=_row_reason_codes(value, config),
    )


def _public_market_group_ref(market_slug: str) -> str:
    _require_canonical_public_string("market_slug", market_slug)
    return f"market_group_{sha256(market_slug.encode('utf-8')).hexdigest()[:16]}"


def _row_status(
    value: ResearchStrategyEvInputQualityInput,
    config: ResearchStrategyEvInputQualityConfig,
) -> str:
    codes = _row_reason_codes(value, config)
    if any(code.endswith("_block") for code in codes):
        return "block"
    if len(codes) != 1 or codes[0] != "ev_input_quality_pass":
        return "watch"
    return "pass"


def _row_reason_codes(
    value: ResearchStrategyEvInputQualityInput,
    config: ResearchStrategyEvInputQualityConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    calibration_error = _probability_calibration_error(value)
    total_cost = _sum_decimals(
        (
            value.fee_probability_cost,
            value.spread_probability_cost,
            value.slippage_probability_cost,
        ),
    )
    if value.resolved_probability is None:
        codes.append("probability_calibration_missing_resolution")
    elif calibration_error >= config.calibration_block_error_threshold:
        codes.append("probability_calibration_block")
    elif calibration_error >= config.calibration_watch_error_threshold:
        codes.append("probability_calibration_watch")
    if total_cost >= config.cost_block_probability_threshold:
        codes.append("cost_inputs_block")
    elif total_cost >= config.cost_watch_probability_threshold:
        codes.append("cost_inputs_watch")
    if value.liquidity_score < config.liquidity_block_score_floor:
        codes.append("liquidity_block")
    elif value.liquidity_score < config.liquidity_watch_score_floor:
        codes.append("liquidity_watch")
    if value.source_confidence_score < config.source_confidence_block_score_floor:
        codes.append("source_confidence_block")
    elif value.source_confidence_score < config.source_confidence_watch_score_floor:
        codes.append("source_confidence_watch")
    if value.resolution_rule_completeness_score < config.resolution_rule_block_score_floor:
        codes.append("resolution_rule_block")
    elif value.resolution_rule_completeness_score < config.resolution_rule_watch_score_floor:
        codes.append("resolution_rule_watch")
    if not codes:
        codes.append("ev_input_quality_pass")
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), ROW_REASON_CODES)


def _report_status(rows: tuple[ResearchStrategyEvInputQualityRow, ...]) -> str:
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(rows: tuple[ResearchStrategyEvInputQualityRow, ...]) -> tuple[str, ...]:
    if not rows or all(row.status == "pass" for row in rows):
        return ("input_quality_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("input_quality_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("input_quality_watch")
    if any(
        code.startswith("probability_calibration_") and code != "probability_calibration_missing_resolution"
        or code == "probability_calibration_missing_resolution"
        for row in rows
        for code in row.reason_codes
    ):
        codes.append("probability_calibration_review")
    if any(code.startswith("cost_inputs_") for row in rows for code in row.reason_codes):
        codes.append("cost_input_review")
    if any(code.startswith("liquidity_") for row in rows for code in row.reason_codes):
        codes.append("liquidity_review")
    if any(
        code.startswith("source_confidence_") for row in rows for code in row.reason_codes
    ):
        codes.append("source_confidence_review")
    if any(
        code.startswith("resolution_rule_") for row in rows for code in row.reason_codes
    ):
        codes.append("resolution_rule_review")
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategyEvInputQualityRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        -row.probability_calibration_error,
        -row.total_cost_probability,
        row.liquidity_score,
        row.source_confidence_score,
        row.resolution_rule_completeness_score,
        row.ev_case_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategyEvInputQualityInput],
) -> tuple[ResearchStrategyEvInputQualityInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategyEvInputQualityInput:
            raise ValueError(
                "inputs must contain only ResearchStrategyEvInputQualityInput values",
            )
        _require_hard_flags("input", value)
        if value.ev_case_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate ev_case_ref values")
        seen_refs.add(value.ev_case_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategyEvInputQualityRow],
) -> tuple[ResearchStrategyEvInputQualityRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategyEvInputQualityRow:
            raise ValueError("rows must contain ResearchStrategyEvInputQualityRow values")
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.ev_case_ref in seen_refs:
            raise ValueError("rows must not contain duplicate ev_case_ref values")
        seen_refs.add(row.ev_case_ref)
    return normalized


def _validate_row_consistency(row: ResearchStrategyEvInputQualityRow) -> None:
    expected_gap = _abs_decimal(
        _subtract_decimal(row.forecast_probability, row.market_probability),
    )
    if row.forecast_market_gap_probability != expected_gap:
        raise ValueError("forecast_market_gap_probability does not match probabilities")
    if row.probability_calibration_error != _row_calibration_error(row):
        raise ValueError("probability_calibration_error does not match probabilities")
    expected_cost = _sum_decimals(
        (
            row.fee_probability_cost,
            row.spread_probability_cost,
            row.slippage_probability_cost,
        ),
    )
    if row.total_cost_probability != expected_cost:
        raise ValueError("total_cost_probability does not match cost inputs")
    if row.status == "pass" and row.reason_codes != ("ev_input_quality_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(
        code.endswith("_watch") or code in _WATCH_SENTINEL_CODES
        for code in row.reason_codes
    ):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(report: ResearchStrategyEvInputQualityReport) -> None:
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
    if report.mean_probability_calibration_error != _mean(
        tuple(
            row.probability_calibration_error
            for row in report.rows
            if row.resolved_probability is not None
        ),
    ):
        raise ValueError("mean_probability_calibration_error must match rows")
    if report.mean_total_cost_probability != _mean(
        tuple(row.total_cost_probability for row in report.rows),
    ):
        raise ValueError("mean_total_cost_probability must match rows")
    if report.mean_liquidity_score != _mean(tuple(row.liquidity_score for row in report.rows)):
        raise ValueError("mean_liquidity_score must match rows")
    if report.mean_source_confidence_score != _mean(
        tuple(row.source_confidence_score for row in report.rows),
    ):
        raise ValueError("mean_source_confidence_score must match rows")
    if report.mean_resolution_rule_completeness_score != _mean(
        tuple(row.resolution_rule_completeness_score for row in report.rows),
    ):
        raise ValueError("mean_resolution_rule_completeness_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategyEvInputQualityReport) -> None:
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
    digest_input = dict(payload)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    expected = sha256(encoded).hexdigest()
    if provided != expected:
        raise ValueError("derived_validation_digest does not match public payload")


def _status_count(rows: tuple[ResearchStrategyEvInputQualityRow, ...], status: str) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategyEvInputQualityRow, ...],
) -> tuple[tuple[str, Decimal], ...]:
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    return tuple(
        (reason_code, _count(count))
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _normalize_reason_code_counts(
    value: Iterable[tuple[str, Decimal]],
) -> tuple[tuple[str, Decimal], ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    normalized: list[tuple[str, Decimal]] = []
    for row in rows:
        if type(row) is not tuple or len(row) != 2:
            raise ValueError("reason_code_counts must contain reason_code count tuples")
        reason_code, count = row
        _require_reason_code("reason_code_counts reason_code", reason_code)
        if reason_code not in ROW_REASON_CODES:
            raise ValueError("reason_code_counts reason_code is not supported")
        normalized.append(
            (
                reason_code,
                _normalize_nonnegative_count("reason_code_counts count", count),
            ),
        )
    return tuple(normalized)


def _probability_calibration_error(value: ResearchStrategyEvInputQualityInput) -> Decimal:
    if value.resolved_probability is None:
        return ZERO.quantize(RATIO_QUANTUM)
    return _abs_decimal(_subtract_decimal(value.resolved_probability, value.forecast_probability))


def _row_calibration_error(row: ResearchStrategyEvInputQualityRow) -> Decimal:
    if row.resolved_probability is None:
        return ZERO.quantize(RATIO_QUANTUM)
    return _abs_decimal(_subtract_decimal(row.resolved_probability, row.forecast_probability))


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO.quantize(RATIO_QUANTUM)
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO) / Decimal(len(values)))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


def _abs_decimal(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(abs(value))


def _apply_or_verify_digest(
    value: ResearchStrategyEvInputQualityRow | ResearchStrategyEvInputQualityReport,
) -> None:
    expected = _derived_digest(value)
    provided = value.derived_validation_digest
    if provided == "":
        object.__setattr__(value, "derived_validation_digest", expected)
        return
    _require_digest("derived_validation_digest", provided)
    if provided != expected:
        raise ValueError("derived_validation_digest does not match derived fields")


def _verify_digest(
    value: ResearchStrategyEvInputQualityRow | ResearchStrategyEvInputQualityReport,
) -> None:
    _require_digest("derived_validation_digest", value.derived_validation_digest)
    if value.derived_validation_digest != _derived_digest(value):
        raise ValueError("derived_validation_digest does not match derived fields")


def _derived_digest(
    value: ResearchStrategyEvInputQualityRow | ResearchStrategyEvInputQualityReport,
) -> str:
    digest_input = asdict(value)
    digest_input.pop("derived_validation_digest", None)
    encoded = dumps(
        _json_ready(digest_input),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return sha256(encoded).hexdigest()


def _json_ready(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return format(_quantize(value), "f")
    if isinstance(value, datetime):
        return _as_utc("datetime", value).isoformat()
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    raise ValueError("value is not JSON serializable")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_payload(label, asdict(value))
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _require_canonical_public_string("public_payload_key", key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) in (list, tuple):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    if type(value) is str:
        _require_canonical_public_string(label, value)
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError(f"{label} must be a Decimal")
        if not value.is_finite():
            raise ValueError(f"{label} must be finite")
        return
    if isinstance(value, datetime):
        _as_utc(label, value)
        return
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        raise ValueError(f"{label} must use Decimal-derived strings")
    if isinstance(value, float):
        raise ValueError(f"{label} must not be a float")
    raise ValueError(f"{label} is not JSON serializable")


def _normalize_reason_codes(
    field_name: str,
    value: Iterable[str],
    allowed: tuple[str, ...],
) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be an iterable")
    try:
        reason_codes = tuple(value)
    except TypeError as exc:
        raise ValueError(f"{field_name} must be an iterable") from exc
    if not reason_codes:
        raise ValueError(f"{field_name} must not be empty")
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in allowed:
            raise ValueError(f"{field_name} is not supported")
    if len(set(reason_codes)) != len(reason_codes):
        raise ValueError(f"{field_name} must not contain duplicates")
    if reason_codes != tuple(sorted(reason_codes)):
        raise ValueError(f"{field_name} must use deterministic sequence")
    return reason_codes


def _require_reason_code(field_name: str, value: object) -> None:
    _require_canonical_public_string(field_name, value)
    if value.startswith("_") or value.endswith("_") or "__" in value:
        raise ValueError(f"{field_name} must be a canonical reason code")
    for character in value:
        if not (character.islower() or character.isdigit() or character == "_"):
            raise ValueError(f"{field_name} must be a canonical reason code")


def _require_status(field_name: str, value: object) -> None:
    if type(value) is not str or value not in RESEARCH_STRATEGY_EV_INPUT_QUALITY_STATUSES:
        raise ValueError(f"{field_name} must be a known status")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{field_name} must be paper_only")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{field_name} must be report_only")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{field_name} must be readonly")


def _require_canonical_public_string(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not value or value.strip() != value:
        raise ValueError(f"{field_name} must be a canonical nonblank string")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public content")


def _has_unsafe_public_fragment(value: str) -> bool:
    lowered = value.lower().replace("-", "_").replace(" ", "_")
    compact = "".join(character for character in lowered if character.isalnum())
    return any(fragment in lowered or fragment in compact for fragment in _UNSAFE_PUBLIC_FRAGMENTS)


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_threshold_pair(label: str, watch_threshold: Decimal, block_threshold: Decimal) -> None:
    if watch_threshold > block_threshold:
        raise ValueError(f"{label} watch threshold must not exceed block threshold")


def _require_floor_pair(label: str, watch_floor: Decimal, block_floor: Decimal) -> None:
    if block_floor > watch_floor:
        raise ValueError(f"{label} block threshold must not exceed watch threshold")


def _normalize_resolved_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_probability(field_name, value)
    if normalized not in (ZERO.quantize(RATIO_QUANTUM), ONE.quantize(RATIO_QUANTUM)):
        raise ValueError(f"{field_name} must be zero or one")
    return normalized


def _normalize_probability(field_name: str, value: object) -> Decimal:
    normalized = _normalize_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _normalize_nonnegative_count(field_name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{field_name} must be integral")
    return decimal_value.quantize(COUNT_QUANTUM)


def _normalize_decimal(field_name: str, value: object) -> Decimal:
    return _quantize(_require_decimal(field_name, value))


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return value.quantize(RATIO_QUANTUM)


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _require_digest(field_name: str, value: object) -> None:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for character in value:
        if character not in "0123456789abcdef":
            raise ValueError(f"{field_name} must be a sha256 hex digest")


__all__ = (
    "DEFAULT_RESEARCH_STRATEGY_EV_INPUT_QUALITY_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_EV_INPUT_QUALITY_STATUSES",
    "ResearchStrategyEvInputQualityConfig",
    "ResearchStrategyEvInputQualityInput",
    "ResearchStrategyEvInputQualityRow",
    "ResearchStrategyEvInputQualityReport",
    "build_research_strategy_ev_input_quality_report",
    "research_strategy_ev_input_quality_report_payload",
)
