"""Pure signal-to-cost alignment report for manual review."""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
from json import dumps
from typing import Any, Iterable


DEFAULT_RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_REPORT_CONFIG_VERSION = (
    "research-strategy-signal-to-cost-alignment-report-v0"
)
RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_STATUSES = (
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
    "credential",
    "private",
    "secret",
    "token",
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
    "reco" + "mmendation",
    "siz" + "ing",
    "notional",
    "position",
    "stake",
    "quantity",
)

ROW_REASON_CODES = (
    "cost_friction_block",
    "cost_friction_watch",
    "evidence_quality_block",
    "evidence_quality_watch",
    "freshness_block",
    "freshness_watch",
    "friction_assumption_quality_block",
    "friction_assumption_quality_watch",
    "net_signal_block",
    "net_signal_watch",
    "signal_to_cost_alignment_pass",
    "signal_to_cost_ratio_block",
    "signal_to_cost_ratio_watch",
)
REPORT_REASON_CODES = (
    "cost_friction_review",
    "evidence_quality_review",
    "freshness_review",
    "friction_assumption_quality_review",
    "net_signal_review",
    "signal_to_cost_alignment_report_block",
    "signal_to_cost_alignment_report_empty",
    "signal_to_cost_alignment_report_pass",
    "signal_to_cost_alignment_report_watch",
    "signal_to_cost_ratio_review",
)


@dataclass(frozen=True)
class ResearchStrategySignalToCostAlignmentConfig:
    config_version: str
    net_signal_pass_floor: Decimal
    net_signal_watch_floor: Decimal
    signal_to_cost_ratio_pass_floor: Decimal
    signal_to_cost_ratio_watch_floor: Decimal
    total_cost_friction_pass_ceiling: Decimal
    total_cost_friction_watch_ceiling: Decimal
    evidence_quality_pass_floor: Decimal
    evidence_quality_watch_floor: Decimal
    friction_assumption_quality_pass_floor: Decimal
    friction_assumption_quality_watch_floor: Decimal
    freshness_pass_floor: Decimal
    freshness_watch_floor: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in (
            "net_signal_pass_floor",
            "net_signal_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "signal_to_cost_ratio_pass_floor",
            "signal_to_cost_ratio_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "total_cost_friction_pass_ceiling",
            "total_cost_friction_watch_ceiling",
            "evidence_quality_pass_floor",
            "evidence_quality_watch_floor",
            "friction_assumption_quality_pass_floor",
            "friction_assumption_quality_watch_floor",
            "freshness_pass_floor",
            "freshness_watch_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_floor_pair(
            "net_signal",
            self.net_signal_pass_floor,
            self.net_signal_watch_floor,
        )
        _require_floor_pair(
            "signal_to_cost_ratio",
            self.signal_to_cost_ratio_pass_floor,
            self.signal_to_cost_ratio_watch_floor,
        )
        _require_ceiling_pair(
            "total_cost_friction",
            self.total_cost_friction_pass_ceiling,
            self.total_cost_friction_watch_ceiling,
        )
        _require_floor_pair(
            "evidence_quality",
            self.evidence_quality_pass_floor,
            self.evidence_quality_watch_floor,
        )
        _require_floor_pair(
            "friction_assumption_quality",
            self.friction_assumption_quality_pass_floor,
            self.friction_assumption_quality_watch_floor,
        )
        _require_floor_pair(
            "freshness",
            self.freshness_pass_floor,
            self.freshness_watch_floor,
        )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchStrategySignalToCostAlignmentInput:
    alignment_case_ref: str
    strategy_ref: str
    observed_at: datetime
    evidence_signal_strength: Decimal
    fee_probability_drag: Decimal
    spread_probability_drag: Decimal
    slippage_probability_drag: Decimal
    settlement_friction_probability_drag: Decimal
    evidence_quality_score: Decimal
    friction_assumption_quality_score: Decimal
    freshness_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("alignment_case_ref", "strategy_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_signal_strength",
            "fee_probability_drag",
            "spread_probability_drag",
            "slippage_probability_drag",
            "settlement_friction_probability_drag",
            "evidence_quality_score",
            "friction_assumption_quality_score",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchStrategySignalToCostAlignmentReasonCodeCount:
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
            _normalize_nonnegative_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "input_ratio",
            _normalize_probability("input_ratio", self.input_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchStrategySignalToCostAlignmentRow:
    alignment_case_ref: str
    strategy_ref: str
    observed_at: datetime
    evidence_signal_strength: Decimal
    fee_probability_drag: Decimal
    spread_probability_drag: Decimal
    slippage_probability_drag: Decimal
    settlement_friction_probability_drag: Decimal
    total_cost_friction_probability: Decimal
    net_signal_strength: Decimal
    signal_to_cost_ratio: Decimal
    evidence_quality_score: Decimal
    friction_assumption_quality_score: Decimal
    freshness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        for field_name in ("alignment_case_ref", "strategy_ref"):
            _require_canonical_public_string(field_name, getattr(self, field_name))
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "evidence_signal_strength",
            "fee_probability_drag",
            "spread_probability_drag",
            "slippage_probability_drag",
            "settlement_friction_probability_drag",
            "total_cost_friction_probability",
            "evidence_quality_score",
            "friction_assumption_quality_score",
            "freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "net_signal_strength",
            _normalize_decimal("net_signal_strength", self.net_signal_strength),
        )
        object.__setattr__(
            self,
            "signal_to_cost_ratio",
            _normalize_nonnegative_decimal(
                "signal_to_cost_ratio",
                self.signal_to_cost_ratio,
            ),
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
class ResearchStrategySignalToCostAlignmentReport:
    generated_at: datetime
    config_version: str
    input_row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    mean_evidence_signal_strength: Decimal
    mean_total_cost_friction_probability: Decimal
    mean_net_signal_strength: Decimal
    mean_signal_to_cost_ratio: Decimal
    mean_evidence_quality_score: Decimal
    mean_friction_assumption_quality_score: Decimal
    mean_freshness_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchStrategySignalToCostAlignmentReasonCodeCount, ...]
    rows: tuple[ResearchStrategySignalToCostAlignmentRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_public_string("config_version", self.config_version)
        for field_name in ("input_row_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _normalize_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_evidence_signal_strength",
            "mean_total_cost_friction_probability",
            "mean_evidence_quality_score",
            "mean_friction_assumption_quality_score",
            "mean_freshness_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_probability(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "mean_net_signal_strength",
            "mean_signal_to_cost_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _normalize_decimal(field_name, getattr(self, field_name)),
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


def build_research_strategy_signal_to_cost_alignment_report(
    inputs: Iterable[ResearchStrategySignalToCostAlignmentInput],
    *,
    config: ResearchStrategySignalToCostAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategySignalToCostAlignmentReport:
    if type(config) is not ResearchStrategySignalToCostAlignmentConfig:
        raise ValueError(
            "config must be a ResearchStrategySignalToCostAlignmentConfig",
        )
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
    return ResearchStrategySignalToCostAlignmentReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_row_count=_count(len(rows)),
        pass_count=_status_count(rows, "pass"),
        watch_count=_status_count(rows, "watch"),
        block_count=_status_count(rows, "block"),
        mean_evidence_signal_strength=_mean(
            tuple(row.evidence_signal_strength for row in rows),
        ),
        mean_total_cost_friction_probability=_mean(
            tuple(row.total_cost_friction_probability for row in rows),
        ),
        mean_net_signal_strength=_mean(tuple(row.net_signal_strength for row in rows)),
        mean_signal_to_cost_ratio=_mean(tuple(row.signal_to_cost_ratio for row in rows)),
        mean_evidence_quality_score=_mean(tuple(row.evidence_quality_score for row in rows)),
        mean_friction_assumption_quality_score=_mean(
            tuple(row.friction_assumption_quality_score for row in rows),
        ),
        mean_freshness_score=_mean(tuple(row.freshness_score for row in rows)),
        status=_report_status(rows),
        reason_codes=_report_reason_codes(rows),
        reason_code_counts=_reason_code_counts_from_rows(rows),
        rows=rows,
    )


def research_strategy_signal_to_cost_alignment_report_payload(
    report: ResearchStrategySignalToCostAlignmentReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchStrategySignalToCostAlignmentReport:
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
        raise ValueError(
            "report must be a ResearchStrategySignalToCostAlignmentReport",
        )
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
    value: ResearchStrategySignalToCostAlignmentInput,
    *,
    config: ResearchStrategySignalToCostAlignmentConfig,
    generated_at: datetime,
) -> ResearchStrategySignalToCostAlignmentRow:
    observed_at = _as_utc("observed_at", value.observed_at)
    if observed_at > generated_at:
        raise ValueError("observed_at must not be after generated_at")
    total_cost_friction_probability = _sum_decimals(
        (
            value.fee_probability_drag,
            value.spread_probability_drag,
            value.slippage_probability_drag,
            value.settlement_friction_probability_drag,
        ),
    )
    net_signal_strength = _subtract_decimal(
        value.evidence_signal_strength,
        total_cost_friction_probability,
    )
    signal_to_cost_ratio = _divide_decimal(
        value.evidence_signal_strength,
        total_cost_friction_probability,
    )
    return ResearchStrategySignalToCostAlignmentRow(
        alignment_case_ref=value.alignment_case_ref,
        strategy_ref=value.strategy_ref,
        observed_at=observed_at,
        evidence_signal_strength=value.evidence_signal_strength,
        fee_probability_drag=value.fee_probability_drag,
        spread_probability_drag=value.spread_probability_drag,
        slippage_probability_drag=value.slippage_probability_drag,
        settlement_friction_probability_drag=value.settlement_friction_probability_drag,
        total_cost_friction_probability=total_cost_friction_probability,
        net_signal_strength=net_signal_strength,
        signal_to_cost_ratio=signal_to_cost_ratio,
        evidence_quality_score=value.evidence_quality_score,
        friction_assumption_quality_score=value.friction_assumption_quality_score,
        freshness_score=value.freshness_score,
        status=_row_status(
            net_signal_strength=net_signal_strength,
            signal_to_cost_ratio=signal_to_cost_ratio,
            total_cost_friction_probability=total_cost_friction_probability,
            value=value,
            config=config,
        ),
        reason_codes=_row_reason_codes(
            net_signal_strength=net_signal_strength,
            signal_to_cost_ratio=signal_to_cost_ratio,
            total_cost_friction_probability=total_cost_friction_probability,
            value=value,
            config=config,
        ),
    )


def _row_status(
    *,
    net_signal_strength: Decimal,
    signal_to_cost_ratio: Decimal,
    total_cost_friction_probability: Decimal,
    value: ResearchStrategySignalToCostAlignmentInput,
    config: ResearchStrategySignalToCostAlignmentConfig,
) -> str:
    if (
        net_signal_strength < config.net_signal_watch_floor
        or signal_to_cost_ratio < config.signal_to_cost_ratio_watch_floor
        or total_cost_friction_probability > config.total_cost_friction_watch_ceiling
        or value.evidence_quality_score < config.evidence_quality_watch_floor
        or value.friction_assumption_quality_score
        < config.friction_assumption_quality_watch_floor
        or value.freshness_score < config.freshness_watch_floor
    ):
        return "block"
    if (
        net_signal_strength < config.net_signal_pass_floor
        or signal_to_cost_ratio < config.signal_to_cost_ratio_pass_floor
        or total_cost_friction_probability > config.total_cost_friction_pass_ceiling
        or value.evidence_quality_score < config.evidence_quality_pass_floor
        or value.friction_assumption_quality_score
        < config.friction_assumption_quality_pass_floor
        or value.freshness_score < config.freshness_pass_floor
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    net_signal_strength: Decimal,
    signal_to_cost_ratio: Decimal,
    total_cost_friction_probability: Decimal,
    value: ResearchStrategySignalToCostAlignmentInput,
    config: ResearchStrategySignalToCostAlignmentConfig,
) -> tuple[str, ...]:
    codes: list[str] = []
    if total_cost_friction_probability > config.total_cost_friction_watch_ceiling:
        codes.append("cost_friction_block")
    elif total_cost_friction_probability > config.total_cost_friction_pass_ceiling:
        codes.append("cost_friction_watch")
    if value.evidence_quality_score < config.evidence_quality_watch_floor:
        codes.append("evidence_quality_block")
    elif value.evidence_quality_score < config.evidence_quality_pass_floor:
        codes.append("evidence_quality_watch")
    if value.freshness_score < config.freshness_watch_floor:
        codes.append("freshness_block")
    elif value.freshness_score < config.freshness_pass_floor:
        codes.append("freshness_watch")
    if value.friction_assumption_quality_score < config.friction_assumption_quality_watch_floor:
        codes.append("friction_assumption_quality_block")
    elif value.friction_assumption_quality_score < config.friction_assumption_quality_pass_floor:
        codes.append("friction_assumption_quality_watch")
    if net_signal_strength < config.net_signal_watch_floor:
        codes.append("net_signal_block")
    elif net_signal_strength < config.net_signal_pass_floor:
        codes.append("net_signal_watch")
    if signal_to_cost_ratio < config.signal_to_cost_ratio_watch_floor:
        codes.append("signal_to_cost_ratio_block")
    elif signal_to_cost_ratio < config.signal_to_cost_ratio_pass_floor:
        codes.append("signal_to_cost_ratio_watch")
    if not codes:
        codes.append("signal_to_cost_alignment_pass")
    return _normalize_reason_codes("reason_codes", tuple(codes), ROW_REASON_CODES)


def _report_status(
    rows: tuple[ResearchStrategySignalToCostAlignmentRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _report_reason_codes(
    rows: tuple[ResearchStrategySignalToCostAlignmentRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("signal_to_cost_alignment_report_empty",)
    report_status = _report_status(rows)
    codes = [f"signal_to_cost_alignment_report_{report_status}"]
    row_codes = tuple(code for row in rows for code in row.reason_codes)
    if any(code.startswith("cost_friction_") for code in row_codes):
        codes.append("cost_friction_review")
    if any(code.startswith("evidence_quality_") for code in row_codes):
        codes.append("evidence_quality_review")
    if any(code.startswith("freshness_") for code in row_codes):
        codes.append("freshness_review")
    if any(code.startswith("friction_assumption_quality_") for code in row_codes):
        codes.append("friction_assumption_quality_review")
    if any(code.startswith("net_signal_") for code in row_codes):
        codes.append("net_signal_review")
    if any(code.startswith("signal_to_cost_ratio_") for code in row_codes):
        codes.append("signal_to_cost_ratio_review")
    return _normalize_reason_codes("reason_codes", tuple(codes), REPORT_REASON_CODES)


def _row_sort_key(
    row: ResearchStrategySignalToCostAlignmentRow,
) -> tuple[int, Decimal, Decimal, Decimal, Decimal, Decimal, str]:
    return (
        {"block": 0, "watch": 1, "pass": 2}[row.status],
        row.net_signal_strength,
        row.signal_to_cost_ratio,
        -row.total_cost_friction_probability,
        row.evidence_quality_score,
        row.friction_assumption_quality_score,
        row.alignment_case_ref,
    )


def _normalize_inputs(
    inputs: Iterable[ResearchStrategySignalToCostAlignmentInput],
) -> tuple[ResearchStrategySignalToCostAlignmentInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        normalized = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen_refs: set[str] = set()
    for value in normalized:
        if type(value) is not ResearchStrategySignalToCostAlignmentInput:
            raise ValueError(
                "inputs must contain ResearchStrategySignalToCostAlignmentInput values",
            )
        _require_hard_flags("input", value)
        if value.alignment_case_ref in seen_refs:
            raise ValueError("inputs must not contain duplicate alignment_case_ref values")
        seen_refs.add(value.alignment_case_ref)
    return normalized


def _normalize_rows(
    rows: Iterable[ResearchStrategySignalToCostAlignmentRow],
) -> tuple[ResearchStrategySignalToCostAlignmentRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        normalized = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen_refs: set[str] = set()
    for row in normalized:
        if type(row) is not ResearchStrategySignalToCostAlignmentRow:
            raise ValueError(
                "rows must contain ResearchStrategySignalToCostAlignmentRow values",
            )
        _require_hard_flags("row", row)
        _verify_digest(row)
        if row.alignment_case_ref in seen_refs:
            raise ValueError("rows must not contain duplicate alignment_case_ref values")
        seen_refs.add(row.alignment_case_ref)
    return normalized


def _validate_row_consistency(
    row: ResearchStrategySignalToCostAlignmentRow,
) -> None:
    expected_cost = _sum_decimals(
        (
            row.fee_probability_drag,
            row.spread_probability_drag,
            row.slippage_probability_drag,
            row.settlement_friction_probability_drag,
        ),
    )
    if row.total_cost_friction_probability != expected_cost:
        raise ValueError("total_cost_friction_probability does not match inputs")
    expected_net_signal = _subtract_decimal(
        row.evidence_signal_strength,
        row.total_cost_friction_probability,
    )
    if row.net_signal_strength != expected_net_signal:
        raise ValueError("net_signal_strength does not match row inputs")
    expected_ratio = _divide_decimal(
        row.evidence_signal_strength,
        row.total_cost_friction_probability,
    )
    if row.signal_to_cost_ratio != expected_ratio:
        raise ValueError("signal_to_cost_ratio does not match row inputs")
    if row.status == "pass" and row.reason_codes != ("signal_to_cost_alignment_pass",):
        raise ValueError("pass rows must only contain pass reason code")
    if row.status == "watch" and not any(code.endswith("_watch") for code in row.reason_codes):
        raise ValueError("watch rows must contain watch reason code")
    if row.status == "block" and not any(code.endswith("_block") for code in row.reason_codes):
        raise ValueError("block rows must contain block reason code")


def _validate_report_consistency(
    report: ResearchStrategySignalToCostAlignmentReport,
) -> None:
    if report.input_row_count != _count(len(report.rows)):
        raise ValueError("input_row_count must match rows")
    if report.input_row_count != report.pass_count + report.watch_count + report.block_count:
        raise ValueError("status counts must match input_row_count")
    if report.pass_count != _status_count(report.rows, "pass"):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _status_count(report.rows, "watch"):
        raise ValueError("watch_count must match rows")
    if report.block_count != _status_count(report.rows, "block"):
        raise ValueError("block_count must match rows")
    if report.mean_evidence_signal_strength != _mean(
        tuple(row.evidence_signal_strength for row in report.rows),
    ):
        raise ValueError("mean_evidence_signal_strength must match rows")
    if report.mean_total_cost_friction_probability != _mean(
        tuple(row.total_cost_friction_probability for row in report.rows),
    ):
        raise ValueError("mean_total_cost_friction_probability must match rows")
    if report.mean_net_signal_strength != _mean(
        tuple(row.net_signal_strength for row in report.rows),
    ):
        raise ValueError("mean_net_signal_strength must match rows")
    if report.mean_signal_to_cost_ratio != _mean(
        tuple(row.signal_to_cost_ratio for row in report.rows),
    ):
        raise ValueError("mean_signal_to_cost_ratio must match rows")
    if report.mean_evidence_quality_score != _mean(
        tuple(row.evidence_quality_score for row in report.rows),
    ):
        raise ValueError("mean_evidence_quality_score must match rows")
    if report.mean_friction_assumption_quality_score != _mean(
        tuple(row.friction_assumption_quality_score for row in report.rows),
    ):
        raise ValueError("mean_friction_assumption_quality_score must match rows")
    if report.mean_freshness_score != _mean(tuple(row.freshness_score for row in report.rows)):
        raise ValueError("mean_freshness_score must match rows")
    if report.status != _report_status(report.rows):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts_from_rows(report.rows):
        raise ValueError("reason_code_counts must match rows")
    if tuple(sorted(report.rows, key=_row_sort_key)) != report.rows:
        raise ValueError("rows must use deterministic sequence")


def _verify_report_integrity(report: ResearchStrategySignalToCostAlignmentReport) -> None:
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


def _status_count(
    rows: tuple[ResearchStrategySignalToCostAlignmentRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _reason_code_counts_from_rows(
    rows: tuple[ResearchStrategySignalToCostAlignmentRow, ...],
) -> tuple[ResearchStrategySignalToCostAlignmentReasonCodeCount, ...]:
    if not rows:
        return ()
    counts: dict[str, int] = {}
    for row in rows:
        for reason_code in row.reason_codes:
            counts[reason_code] = counts.get(reason_code, 0) + 1
    denominator = _count(len(rows))
    return tuple(
        ResearchStrategySignalToCostAlignmentReasonCodeCount(
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
    value: Iterable[ResearchStrategySignalToCostAlignmentReasonCodeCount],
) -> tuple[ResearchStrategySignalToCostAlignmentReasonCodeCount, ...]:
    if isinstance(value, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        rows = tuple(value)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    for row in rows:
        if type(row) is not ResearchStrategySignalToCostAlignmentReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchStrategySignalToCostAlignmentReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    return rows


def _sum_decimals(values: tuple[Decimal, ...]) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum(values, ZERO))


def _subtract_decimal(left: Decimal, right: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(left - right)


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
    if type(value) is not str or value not in RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_STATUSES:
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
    "DEFAULT_RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_REPORT_CONFIG_VERSION",
    "RESEARCH_STRATEGY_SIGNAL_TO_COST_ALIGNMENT_STATUSES",
    "ResearchStrategySignalToCostAlignmentConfig",
    "ResearchStrategySignalToCostAlignmentInput",
    "ResearchStrategySignalToCostAlignmentReasonCodeCount",
    "ResearchStrategySignalToCostAlignmentRow",
    "ResearchStrategySignalToCostAlignmentReport",
    "build_research_strategy_signal_to_cost_alignment_report",
    "research_strategy_signal_to_cost_alignment_report_payload",
)
