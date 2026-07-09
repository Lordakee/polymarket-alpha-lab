"""Public probability cost confidence floor report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN
import hashlib
import json
from typing import Any


DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_CONFIDENCE_FLOOR_REPORT_CONFIG_VERSION = (
    "research-market-probability-cost-confidence-floor-report-v0"
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

REASON_PREFIX = "probability_cost_confidence_floor_"
NO_INPUTS_REASON = REASON_PREFIX + "no_inputs"
CLEAR_REASON = REASON_PREFIX + "clear"
REPORT_PASS_REASON = REASON_PREFIX + STATUS_PASS
REPORT_WATCH_REASON = REASON_PREFIX + STATUS_WATCH
REPORT_BLOCK_REASON = REASON_PREFIX + STATUS_BLOCK
TOTAL_COST_WATCH_REASON = REASON_PREFIX + "total_cost_watch"
TOTAL_COST_BLOCK_REASON = REASON_PREFIX + "total_cost_block"
CONFIDENCE_WATCH_REASON = REASON_PREFIX + "confidence_watch"
CONFIDENCE_BLOCK_REASON = REASON_PREFIX + "confidence_block"
COST_ADJUSTED_GAP_WATCH_REASON = REASON_PREFIX + "cost_adjusted_gap_watch"
COST_ADJUSTED_GAP_BLOCK_REASON = REASON_PREFIX + "cost_adjusted_gap_block"

QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
SIXTY_FOUR = 64


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
    _join_parts("sou", "rce", "_", "ur", "l"),
    _join_parts("sou", "rce", "-", "ur", "l"),
    _join_parts("sou", "rce", "_", "te", "xt"),
    _join_parts("sou", "rce", "-", "te", "xt"),
    _join_parts("d", "sn"),
    _join_parts("d", "b"),
    _join_parts("data", "base"),
    _join_parts("net", "work"),
    _join_parts("tab", "le"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("tra", "ding"),
    _join_parts("pos", "ition"),
    _join_parts("siz", "ing"),
    _join_parts("reco", "mmend"),
    _join_parts("reco", "mmendation"),
    _join_parts("sec", "ret"),
    _join_parts("pri", "vate", "_", "key"),
    _join_parts("a", "pi", "_", "key"),
    "://",
    "?",
)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostConfidenceFloorReportConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_CONFIDENCE_FLOOR_REPORT_CONFIG_VERSION
    )
    watch_total_cost_ratio: Decimal = Decimal("0.030000")
    block_total_cost_ratio: Decimal = Decimal("0.080000")
    watch_confidence_floor_ratio: Decimal = Decimal("0.650000")
    block_confidence_floor_ratio: Decimal = Decimal("0.500000")
    watch_cost_adjusted_gap_floor_ratio: Decimal = Decimal("0.020000")
    block_cost_adjusted_gap_floor_ratio: Decimal = Decimal("0.000000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostConfidenceFloorReportConfig does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostConfidenceFloorReportConfig,
            "config",
        )
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_CONFIDENCE_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "watch_total_cost_ratio",
            "block_total_cost_ratio",
            "watch_confidence_floor_ratio",
            "block_confidence_floor_ratio",
            "watch_cost_adjusted_gap_floor_ratio",
            "block_cost_adjusted_gap_floor_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "watch_total_cost_ratio",
            self.watch_total_cost_ratio,
            "block_total_cost_ratio",
            self.block_total_cost_ratio,
        )
        if self.block_confidence_floor_ratio >= self.watch_confidence_floor_ratio:
            raise ValueError(
                "block_confidence_floor_ratio must be below watch_confidence_floor_ratio",
            )
        if (
            self.block_cost_adjusted_gap_floor_ratio
            > self.watch_cost_adjusted_gap_floor_ratio
        ):
            raise ValueError(
                "block_cost_adjusted_gap_floor_ratio must not exceed "
                "watch_cost_adjusted_gap_floor_ratio",
            )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostConfidenceFloorInput:
    public_signal_ref: str
    observed_at: datetime
    research_probability: Decimal
    public_probability: Decimal
    fee_cost_ratio: Decimal
    spread_cost_ratio: Decimal
    slippage_cost_ratio: Decimal
    confidence_ratio: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostConfidenceFloorInput does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostConfidenceFloorInput,
            "input",
        )
        object.__setattr__(
            self,
            "public_signal_ref",
            _require_public_label("public_signal_ref", self.public_signal_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "research_probability",
            "public_probability",
            "fee_cost_ratio",
            "spread_cost_ratio",
            "slippage_cost_ratio",
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
class ResearchMarketProbabilityCostConfidenceFloorRow:
    public_signal_ref: str
    observed_at: datetime
    research_probability: Decimal
    public_probability: Decimal
    probability_gap_ratio: Decimal
    fee_cost_ratio: Decimal
    spread_cost_ratio: Decimal
    slippage_cost_ratio: Decimal
    total_cost_ratio: Decimal
    cost_adjusted_gap_ratio: Decimal
    confidence_ratio: Decimal
    confidence_floor_gap_ratio: Decimal
    confidence_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostConfidenceFloorRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostConfidenceFloorRow,
            "row",
        )
        object.__setattr__(
            self,
            "public_signal_ref",
            _require_public_label("public_signal_ref", self.public_signal_ref),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "research_probability",
            "public_probability",
            "probability_gap_ratio",
            "fee_cost_ratio",
            "spread_cost_ratio",
            "slippage_cost_ratio",
            "total_cost_ratio",
            "cost_adjusted_gap_ratio",
            "confidence_ratio",
            "confidence_floor_gap_ratio",
            "confidence_floor_score",
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
        if self.status != _status_from_reasons(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(
            self,
            "count",
            _require_positive_count_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketProbabilityCostConfidenceFloorReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    total_cost_watch_count: Decimal
    confidence_floor_watch_count: Decimal
    cost_adjusted_gap_floor_watch_count: Decimal
    max_total_cost_ratio: Decimal
    min_confidence_ratio: Decimal
    min_cost_adjusted_gap_ratio: Decimal
    average_confidence_floor_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount, ...]
    rows: tuple[ResearchMarketProbabilityCostConfidenceFloorRow, ...]
    derived_validation_digest: str
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketProbabilityCostConfidenceFloorReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketProbabilityCostConfidenceFloorReport,
            "report",
        )
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        object.__setattr__(
            self,
            "config_version",
            _require_public_label("config_version", self.config_version),
        )
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_CONFIDENCE_FLOOR_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "total_cost_watch_count",
            "confidence_floor_watch_count",
            "cost_adjusted_gap_floor_watch_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "max_total_cost_ratio",
            "min_confidence_ratio",
            "min_cost_adjusted_gap_ratio",
            "average_confidence_floor_score",
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
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        _require_sha256_digest("derived_validation_digest", self.derived_validation_digest)
        _validate_report(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        expected_digest = _report_digest_from_values(_report_values_without_digest(self))
        if self.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest does not match report payload")

    @property
    def public_payload(self) -> dict[str, object]:
        return research_market_probability_cost_confidence_floor_report_payload(self)


def build_research_market_probability_cost_confidence_floor_report(
    signals: Iterable[ResearchMarketProbabilityCostConfidenceFloorInput],
    *,
    config: ResearchMarketProbabilityCostConfidenceFloorReportConfig,
    generated_at: datetime,
) -> ResearchMarketProbabilityCostConfidenceFloorReport:
    if type(config) is not ResearchMarketProbabilityCostConfidenceFloorReportConfig:
        raise ValueError(
            "config must be a ResearchMarketProbabilityCostConfidenceFloorReportConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_rows = _normalize_inputs(signals)
    rows = tuple(
        sorted(
            (_row_from_input(item, config=config) for item in input_rows),
            key=_row_sort_key,
        ),
    )
    values = _report_values_from_rows(
        rows,
        config_version=config.config_version,
        generated_at=generated_at_utc,
        input_count=_count(len(input_rows)),
    )
    return ResearchMarketProbabilityCostConfidenceFloorReport(
        **values,
        derived_validation_digest=_report_digest_from_values(values),
    )


def research_market_probability_cost_confidence_floor_report_payload(
    report: ResearchMarketProbabilityCostConfidenceFloorReport,
) -> dict[str, object]:
    if type(report) is not ResearchMarketProbabilityCostConfidenceFloorReport:
        raise ValueError(
            "report must be a ResearchMarketProbabilityCostConfidenceFloorReport",
        )
    expected_digest = _report_digest_from_values(_report_values_without_digest(report))
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest does not match report payload")
    _validate_report(report)
    _require_hard_flags("report", report)
    payload = _json_ready(
        {
            **_report_values_without_digest(report),
            "derived_validation_digest": report.derived_validation_digest,
        },
    )
    if type(payload) is not dict:
        raise ValueError("payload must be a dict")
    _reject_unsafe_public_payload(
        "research_market_probability_cost_confidence_floor_report_payload",
        payload,
        allow_json_containers=True,
    )
    return payload


def research_market_probability_cost_confidence_floor_report_digest(
    report: ResearchMarketProbabilityCostConfidenceFloorReport,
) -> str:
    payload = research_market_probability_cost_confidence_floor_report_payload(report)
    trimmed = dict(payload)
    trimmed.pop("derived_validation_digest")
    return _digest_json_ready_values(trimmed)


def _row_from_input(
    item: ResearchMarketProbabilityCostConfidenceFloorInput,
    *,
    config: ResearchMarketProbabilityCostConfidenceFloorReportConfig,
) -> ResearchMarketProbabilityCostConfidenceFloorRow:
    probability_gap_ratio = _quantize(abs(item.research_probability - item.public_probability))
    total_cost_ratio = _quantize(
        item.fee_cost_ratio + item.spread_cost_ratio + item.slippage_cost_ratio,
    )
    cost_adjusted_gap_ratio = _max_decimal(probability_gap_ratio - total_cost_ratio, ZERO)
    confidence_floor_gap_ratio = _max_decimal(
        config.watch_confidence_floor_ratio - item.confidence_ratio,
        ZERO,
    )
    confidence_floor_score = _quantize(cost_adjusted_gap_ratio * item.confidence_ratio)
    reason_codes = _row_reason_codes(
        item,
        config=config,
        total_cost_ratio=total_cost_ratio,
        cost_adjusted_gap_ratio=cost_adjusted_gap_ratio,
    )
    return ResearchMarketProbabilityCostConfidenceFloorRow(
        public_signal_ref=item.public_signal_ref,
        observed_at=item.observed_at,
        research_probability=item.research_probability,
        public_probability=item.public_probability,
        probability_gap_ratio=probability_gap_ratio,
        fee_cost_ratio=item.fee_cost_ratio,
        spread_cost_ratio=item.spread_cost_ratio,
        slippage_cost_ratio=item.slippage_cost_ratio,
        total_cost_ratio=total_cost_ratio,
        cost_adjusted_gap_ratio=cost_adjusted_gap_ratio,
        confidence_ratio=item.confidence_ratio,
        confidence_floor_gap_ratio=confidence_floor_gap_ratio,
        confidence_floor_score=confidence_floor_score,
        status=_status_from_reasons(reason_codes),
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    item: ResearchMarketProbabilityCostConfidenceFloorInput,
    *,
    config: ResearchMarketProbabilityCostConfidenceFloorReportConfig,
    total_cost_ratio: Decimal,
    cost_adjusted_gap_ratio: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    for reason_code in item.reason_codes:
        reasons.append("input_" + reason_code)
    if total_cost_ratio >= config.block_total_cost_ratio:
        reasons.append(TOTAL_COST_BLOCK_REASON)
    elif total_cost_ratio >= config.watch_total_cost_ratio:
        reasons.append(TOTAL_COST_WATCH_REASON)
    if item.confidence_ratio < config.block_confidence_floor_ratio:
        reasons.append(CONFIDENCE_BLOCK_REASON)
    elif item.confidence_ratio < config.watch_confidence_floor_ratio:
        reasons.append(CONFIDENCE_WATCH_REASON)
    if cost_adjusted_gap_ratio <= config.block_cost_adjusted_gap_floor_ratio:
        reasons.append(COST_ADJUSTED_GAP_BLOCK_REASON)
    elif cost_adjusted_gap_ratio <= config.watch_cost_adjusted_gap_floor_ratio:
        reasons.append(COST_ADJUSTED_GAP_WATCH_REASON)
    status = _status_from_reasons(tuple(reasons))
    if status == STATUS_PASS:
        reasons.append(CLEAR_REASON)
    else:
        reasons.append(REASON_PREFIX + status)
    return _normalize_reason_codes(
        "reason_codes",
        tuple(sorted(reasons)),
        allow_empty=False,
    )


def _report_values_from_rows(
    rows: tuple[ResearchMarketProbabilityCostConfidenceFloorRow, ...],
    *,
    config_version: str,
    generated_at: datetime,
    input_count: Decimal,
) -> dict[str, object]:
    if not rows:
        reason_code_counts = (
            ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
            ),
        )
        return {
            "generated_at": generated_at,
            "config_version": config_version,
            "input_count": input_count,
            "row_count": ZERO,
            "pass_count": ZERO,
            "watch_count": ZERO,
            "block_count": ZERO,
            "total_cost_watch_count": ZERO,
            "confidence_floor_watch_count": ZERO,
            "cost_adjusted_gap_floor_watch_count": ZERO,
            "max_total_cost_ratio": ZERO,
            "min_confidence_ratio": ZERO,
            "min_cost_adjusted_gap_ratio": ZERO,
            "average_confidence_floor_score": ZERO,
            "status": STATUS_BLOCK,
            "reason_codes": (NO_INPUTS_REASON,),
            "reason_code_counts": reason_code_counts,
            "rows": (),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        }
    reason_codes = _report_reason_codes(rows)
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "input_count": input_count,
        "row_count": _count(len(rows)),
        "pass_count": _status_count(rows, STATUS_PASS),
        "watch_count": _status_count(rows, STATUS_WATCH),
        "block_count": _status_count(rows, STATUS_BLOCK),
        "total_cost_watch_count": _count(
            sum(
                1
                for row in rows
                if TOTAL_COST_WATCH_REASON in row.reason_codes
                or TOTAL_COST_BLOCK_REASON in row.reason_codes
            ),
        ),
        "confidence_floor_watch_count": _count(
            sum(
                1
                for row in rows
                if CONFIDENCE_WATCH_REASON in row.reason_codes
                or CONFIDENCE_BLOCK_REASON in row.reason_codes
            ),
        ),
        "cost_adjusted_gap_floor_watch_count": _count(
            sum(
                1
                for row in rows
                if COST_ADJUSTED_GAP_WATCH_REASON in row.reason_codes
                or COST_ADJUSTED_GAP_BLOCK_REASON in row.reason_codes
            ),
        ),
        "max_total_cost_ratio": _max_decimal(*(row.total_cost_ratio for row in rows)),
        "min_confidence_ratio": _min_decimal(*(row.confidence_ratio for row in rows)),
        "min_cost_adjusted_gap_ratio": _min_decimal(
            *(row.cost_adjusted_gap_ratio for row in rows),
        ),
        "average_confidence_floor_score": _mean(
            tuple(row.confidence_floor_score for row in rows),
        ),
        "status": _rollup_status(tuple(row.status for row in rows)),
        "reason_codes": reason_codes,
        "reason_code_counts": _reason_code_counts(rows),
        "rows": rows,
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def _validate_report(report: ResearchMarketProbabilityCostConfidenceFloorReport) -> None:
    rows = _normalize_rows(report.rows)
    expected = _report_values_from_rows(
        rows,
        config_version=report.config_version,
        generated_at=report.generated_at,
        input_count=_count(len(rows)),
    )
    for field_name, expected_value in expected.items():
        if getattr(report, field_name) != expected_value:
            raise ValueError(f"{field_name} does not match rows")


def _report_values_without_digest(
    report: ResearchMarketProbabilityCostConfidenceFloorReport,
) -> dict[str, object]:
    return {
        "generated_at": report.generated_at,
        "config_version": report.config_version,
        "input_count": report.input_count,
        "row_count": report.row_count,
        "pass_count": report.pass_count,
        "watch_count": report.watch_count,
        "block_count": report.block_count,
        "total_cost_watch_count": report.total_cost_watch_count,
        "confidence_floor_watch_count": report.confidence_floor_watch_count,
        "cost_adjusted_gap_floor_watch_count": report.cost_adjusted_gap_floor_watch_count,
        "max_total_cost_ratio": report.max_total_cost_ratio,
        "min_confidence_ratio": report.min_confidence_ratio,
        "min_cost_adjusted_gap_ratio": report.min_cost_adjusted_gap_ratio,
        "average_confidence_floor_score": report.average_confidence_floor_score,
        "status": report.status,
        "reason_codes": report.reason_codes,
        "reason_code_counts": report.reason_code_counts,
        "rows": report.rows,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _report_digest_from_values(values: Mapping[str, object]) -> str:
    return _digest_json_ready_values(_json_ready(values))


def _digest_json_ready_values(values: object) -> str:
    _reject_unsafe_public_payload(
        "derived_validation_digest payload",
        values,
        allow_json_containers=True,
    )
    canonical = json.dumps(values, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _json_ready(value: Any) -> Any:
    if _is_public_dataclass(value):
        return _json_ready(_dataclass_values(value))
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if type(value) is Decimal:
        return format(value, "f")
    if type(value) is datetime:
        return value.isoformat()
    if type(value) in {str, bool} or value is None:
        return value
    raise ValueError(f"unsupported payload value {type(value).__name__}")


def _dataclass_values(value: object) -> dict[str, object]:
    if type(value) is ResearchMarketProbabilityCostConfidenceFloorReportConfig:
        return {
            "config_version": value.config_version,
            "watch_total_cost_ratio": value.watch_total_cost_ratio,
            "block_total_cost_ratio": value.block_total_cost_ratio,
            "watch_confidence_floor_ratio": value.watch_confidence_floor_ratio,
            "block_confidence_floor_ratio": value.block_confidence_floor_ratio,
            "watch_cost_adjusted_gap_floor_ratio": value.watch_cost_adjusted_gap_floor_ratio,
            "block_cost_adjusted_gap_floor_ratio": value.block_cost_adjusted_gap_floor_ratio,
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is ResearchMarketProbabilityCostConfidenceFloorInput:
        return {
            "public_signal_ref": value.public_signal_ref,
            "observed_at": value.observed_at,
            "research_probability": value.research_probability,
            "public_probability": value.public_probability,
            "fee_cost_ratio": value.fee_cost_ratio,
            "spread_cost_ratio": value.spread_cost_ratio,
            "slippage_cost_ratio": value.slippage_cost_ratio,
            "confidence_ratio": value.confidence_ratio,
            "reason_codes": value.reason_codes,
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is ResearchMarketProbabilityCostConfidenceFloorRow:
        return {
            "public_signal_ref": value.public_signal_ref,
            "observed_at": value.observed_at,
            "research_probability": value.research_probability,
            "public_probability": value.public_probability,
            "probability_gap_ratio": value.probability_gap_ratio,
            "fee_cost_ratio": value.fee_cost_ratio,
            "spread_cost_ratio": value.spread_cost_ratio,
            "slippage_cost_ratio": value.slippage_cost_ratio,
            "total_cost_ratio": value.total_cost_ratio,
            "cost_adjusted_gap_ratio": value.cost_adjusted_gap_ratio,
            "confidence_ratio": value.confidence_ratio,
            "confidence_floor_gap_ratio": value.confidence_floor_gap_ratio,
            "confidence_floor_score": value.confidence_floor_score,
            "status": value.status,
            "reason_codes": value.reason_codes,
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount:
        return {
            "reason_code": value.reason_code,
            "count": value.count,
            "paper_only": value.paper_only,
            "report_only": value.report_only,
            "readonly": value.readonly,
        }
    if type(value) is ResearchMarketProbabilityCostConfidenceFloorReport:
        return {
            **_report_values_without_digest(value),
            "derived_validation_digest": value.derived_validation_digest,
        }
    raise ValueError(f"unsupported payload dataclass {type(value).__name__}")


def _normalize_inputs(
    signals: Iterable[ResearchMarketProbabilityCostConfidenceFloorInput],
) -> tuple[ResearchMarketProbabilityCostConfidenceFloorInput, ...]:
    values = tuple(signals)
    for item in values:
        if type(item) is not ResearchMarketProbabilityCostConfidenceFloorInput:
            raise ValueError("signals must contain exact input rows")
        _require_hard_flags("input", item)
    return values


def _normalize_rows(
    rows: tuple[ResearchMarketProbabilityCostConfidenceFloorRow, ...],
) -> tuple[ResearchMarketProbabilityCostConfidenceFloorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketProbabilityCostConfidenceFloorRow:
            raise ValueError("rows must contain exact row dataclasses")
        _require_hard_flags("row", row)
    if rows != tuple(sorted(rows, key=_row_sort_key)):
        raise ValueError("rows must use canonical sequence")
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount, ...],
) -> tuple[ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in counts:
        if type(item) is not ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount:
            raise ValueError("reason_code_counts must contain exact count rows")
        _require_hard_flags("reason_code_count", item)
    if counts != tuple(sorted(counts, key=lambda item: (-item.count, item.reason_code))):
        raise ValueError("reason_code_counts must use canonical sequence")
    return counts


def _row_sort_key(row: ResearchMarketProbabilityCostConfidenceFloorRow) -> tuple[Decimal, Decimal, str]:
    return (
        STATUS_WEIGHT[row.status],
        -row.confidence_floor_score,
        row.public_signal_ref,
    )


def _status_from_reasons(reason_codes: tuple[str, ...]) -> str:
    floor_reason_codes = tuple(
        reason_code
        for reason_code in reason_codes
        if reason_code.startswith(REASON_PREFIX)
    )
    if any(reason_code.endswith("_block") for reason_code in floor_reason_codes):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") for reason_code in floor_reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return STATUS_BLOCK
    if STATUS_BLOCK in statuses:
        return STATUS_BLOCK
    if STATUS_WATCH in statuses:
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketProbabilityCostConfidenceFloorRow, ...],
    status: str,
) -> Decimal:
    return _count(sum(1 for row in rows if row.status == status))


def _report_reason_codes(
    rows: tuple[ResearchMarketProbabilityCostConfidenceFloorRow, ...],
) -> tuple[str, ...]:
    rollup_status = _rollup_status(tuple(row.status for row in rows))
    codes = {REASON_PREFIX + rollup_status}
    for row in rows:
        codes.update(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(sorted(codes)), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketProbabilityCostConfidenceFloorRow, ...],
) -> tuple[ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount, ...]:
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount(
            reason_code=reason_code,
            count=_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{name} must be a non-empty canonical string")
    _reject_unsafe_public_payload(name, value)
    return value


def _require_reason_code(name: str, value: str) -> str:
    if type(value) is not str:
        raise ValueError(f"{name} must be a string")
    if value != value.strip() or not value:
        raise ValueError(f"{name} must be a non-empty canonical string")
    _reject_unsafe_public_payload(name, value)
    return value


def _normalize_reason_codes(
    name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(_require_reason_code(name, code) for code in reason_codes)
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{name} must not contain duplicates")
    if normalized != tuple(sorted(normalized)):
        raise ValueError(f"{name} must use canonical sequence")
    return normalized


def _require_status(name: str, value: str) -> str:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{name} must be one of pass/watch/block")
    return value


def _require_decimal(name: str, value: Decimal) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)
    except InvalidOperation as exc:
        raise ValueError("decimal value must support six decimal places") from exc


def _require_ratio_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _quantize(_require_decimal(name, value))
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{name} must be between zero and one")
    return normalized


def _require_nonnegative_count_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _quantize(_require_decimal(name, value))
    if normalized < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if normalized != normalized.to_integral_value().quantize(QUANTUM):
        raise ValueError(f"{name} must be a whole count")
    return normalized


def _require_positive_count_decimal(name: str, value: Decimal) -> Decimal:
    normalized = _require_nonnegative_count_decimal(name, value)
    if normalized <= ZERO:
        raise ValueError(f"{name} must be positive")
    return normalized


def _count(value: int) -> Decimal:
    if type(value) is not int or value < 0:
        raise ValueError("count must be a nonnegative integer")
    return Decimal(value).quantize(QUANTUM)


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return ZERO
    return _quantize(sum(values, ZERO) / _count(len(values)))


def _max_decimal(*values: Decimal) -> Decimal:
    if not values:
        return ZERO
    return _quantize(max(values))


def _min_decimal(*values: Decimal) -> Decimal:
    if not values:
        return ZERO
    return _quantize(min(values))


def _require_less_than(
    left_name: str,
    left_value: Decimal,
    right_name: str,
    right_value: Decimal,
) -> None:
    if left_value >= right_value:
        raise ValueError(f"{left_name} must be below {right_name}")


def _as_utc(name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_hard_flags(name: str, value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{name} {field_name} must be True")


def _require_sha256_digest(name: str, value: str) -> str:
    if type(value) is not str or len(value) != SIXTY_FOUR:
        raise ValueError(f"{name} must be a sha256 hex digest")
    if any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a sha256 hex digest")
    return value


def _is_public_dataclass(value: object) -> bool:
    return type(value) in {
        ResearchMarketProbabilityCostConfidenceFloorReportConfig,
        ResearchMarketProbabilityCostConfidenceFloorInput,
        ResearchMarketProbabilityCostConfidenceFloorRow,
        ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount,
        ResearchMarketProbabilityCostConfidenceFloorReport,
    }


def _reject_unsafe_public_payload(
    name: str,
    value: object,
    *,
    allow_json_containers: bool = False,
) -> None:
    if _is_public_dataclass(value):
        _reject_unsafe_public_payload(
            name,
            _dataclass_values(value),
            allow_json_containers=True,
        )
        return
    if allow_json_containers and isinstance(value, Mapping):
        for key, nested_value in value.items():
            _reject_unsafe_public_payload(name, str(key))
            if key == "derived_validation_digest":
                _require_sha256_digest(str(key), nested_value)  # type: ignore[arg-type]
                continue
            _reject_unsafe_public_payload(
                f"{name}.{key}",
                nested_value,
                allow_json_containers=True,
            )
        return
    if allow_json_containers and isinstance(value, (list, tuple)):
        for nested_value in value:
            _reject_unsafe_public_payload(
                name,
                nested_value,
                allow_json_containers=True,
            )
        return
    if type(value) is str:
        lowered = value.lower()
        if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
            raise ValueError(f"{name} contains unsafe public payload")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_PROBABILITY_COST_CONFIDENCE_FLOOR_REPORT_CONFIG_VERSION",
    "STATUSES",
    "ResearchMarketProbabilityCostConfidenceFloorReportConfig",
    "ResearchMarketProbabilityCostConfidenceFloorInput",
    "ResearchMarketProbabilityCostConfidenceFloorReasonCodeCount",
    "ResearchMarketProbabilityCostConfidenceFloorReport",
    "ResearchMarketProbabilityCostConfidenceFloorRow",
    "build_research_market_probability_cost_confidence_floor_report",
    "research_market_probability_cost_confidence_floor_report_digest",
    "research_market_probability_cost_confidence_floor_report_payload",
)
