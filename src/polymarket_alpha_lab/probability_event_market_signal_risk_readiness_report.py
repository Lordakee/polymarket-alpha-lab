"""Pure read-only market signal risk readiness report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from hashlib import sha256
import json


DEFAULT_PROBABILITY_EVENT_MARKET_SIGNAL_RISK_READINESS_VERSION = (
    "probability-event-market-signal-risk-readiness-report-v0"
)

ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
TWO = Decimal("2.000000")
QUANTUM = Decimal("0.000001")
COUNT_QUANTUM = Decimal("1")

PRICE_JUMP_WATCH = Decimal("0.050000")
PRICE_JUMP_BLOCK = Decimal("0.150000")
DEPTH_COLLAPSE_WATCH = Decimal("0.400000")
DEPTH_COLLAPSE_BLOCK = Decimal("0.750000")
SPREAD_WIDTH_WATCH = Decimal("0.080000")
SPREAD_WIDTH_BLOCK = Decimal("0.150000")
INFO_ASYMMETRY_WATCH = Decimal("0.400000")
INFO_ASYMMETRY_BLOCK = Decimal("0.750000")
ADVERSE_SELECTION_WATCH = Decimal("0.350000")
ADVERSE_SELECTION_BLOCK = Decimal("0.750000")

STATUS_VALUES = ("pass", "watch", "block")
READINESS_REASON_VALUES = (
    "market_signal_risk_readiness_pass",
    "market_signal_risk_readiness_watch",
    "market_signal_risk_readiness_block",
    "market_signal_risk_readiness_no_inputs",
)
ROW_REASON_VALUES = (
    "market_signal_risk_clear",
    "price_jump_watch",
    "price_jump_block",
    "depth_collapse_watch",
    "depth_collapse_block",
    "spread_width_watch",
    "spread_width_block",
    "information_asymmetry_news_lead_watch",
    "information_asymmetry_news_lead_block",
    "maker_adverse_selection_watch",
    "maker_adverse_selection_block",
)
REASON_VALUES = READINESS_REASON_VALUES + ROW_REASON_VALUES
MANUAL_NEXT_STEPS = (
    "continue_probability_event_research_review",
    "refresh_public_sources_before_probability_review",
    "pause_probability_event_until_manual_risk_review",
)
PAYLOAD_KEYS = (
    "config_version",
    "status",
    "event_count",
    "pass_count",
    "watch_count",
    "block_count",
    "max_risk_score",
    "mean_risk_score",
    "reason_codes",
    "reason_code_counts",
    "rows",
    "manual_next_step",
    "paper_only",
    "report_only",
    "readonly",
    "payload_digest",
)
REASON_CODE_COUNT_PAYLOAD_KEYS = (
    "reason_code",
    "count",
    "paper_only",
    "report_only",
    "readonly",
)
ROW_PAYLOAD_KEYS = (
    "event_label",
    "status",
    "market_probability",
    "previous_probability",
    "probability_jump",
    "probability_move_15m",
    "probability_move_1h",
    "top_depth_now",
    "top_depth_baseline",
    "depth_collapse_ratio",
    "spread_width",
    "public_signal_lag_minutes",
    "pre_news_volume_ratio",
    "information_asymmetry_score",
    "maker_fill_imbalance",
    "maker_quote_retreat_ratio",
    "adverse_selection_score",
    "risk_score",
    "reason_codes",
    "paper_only",
    "report_only",
    "readonly",
)

UNSAFE_PUBLIC_TERMS = (
    "http://",
    "https://",
)

__all__ = (
    "DEFAULT_PROBABILITY_EVENT_MARKET_SIGNAL_RISK_READINESS_VERSION",
    "ProbabilityEventMarketSignalRiskReadinessInput",
    "ProbabilityEventMarketSignalRiskReadinessReasonCodeCount",
    "ProbabilityEventMarketSignalRiskReadinessReport",
    "ProbabilityEventMarketSignalRiskReadinessRow",
    "build_probability_event_market_signal_risk_readiness_report",
    "probability_event_market_signal_risk_readiness_payload",
    "probability_event_market_signal_risk_readiness_payload_digest",
)


@dataclass(frozen=True)
class ProbabilityEventMarketSignalRiskReadinessInput:
    event_label: str
    market_probability: Decimal
    previous_probability: Decimal
    probability_move_15m: Decimal
    probability_move_1h: Decimal
    top_depth_now: Decimal
    top_depth_baseline: Decimal
    spread_width: Decimal
    public_signal_lag_minutes: Decimal
    pre_news_volume_ratio: Decimal
    maker_fill_imbalance: Decimal
    maker_quote_retreat_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventMarketSignalRiskReadinessInput does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventMarketSignalRiskReadinessInput, "input")
        object.__setattr__(
            self,
            "event_label",
            _require_public_code("event_label", self.event_label),
        )
        for field_name in (
            "market_probability",
            "previous_probability",
            "probability_move_15m",
            "probability_move_1h",
            "spread_width",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "top_depth_now",
            "public_signal_lag_minutes",
            "pre_news_volume_ratio",
            "maker_fill_imbalance",
            "maker_quote_retreat_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "top_depth_baseline",
            _require_positive_decimal("top_depth_baseline", self.top_depth_baseline),
        )
        _require_hard_flags(self)
        _reject_unsafe_public_value(self)


@dataclass(frozen=True)
class ProbabilityEventMarketSignalRiskReadinessRow:
    event_label: str
    status: str
    market_probability: Decimal
    previous_probability: Decimal
    probability_jump: Decimal
    probability_move_15m: Decimal
    probability_move_1h: Decimal
    top_depth_now: Decimal
    top_depth_baseline: Decimal
    depth_collapse_ratio: Decimal
    spread_width: Decimal
    public_signal_lag_minutes: Decimal
    pre_news_volume_ratio: Decimal
    information_asymmetry_score: Decimal
    maker_fill_imbalance: Decimal
    maker_quote_retreat_ratio: Decimal
    adverse_selection_score: Decimal
    risk_score: Decimal
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventMarketSignalRiskReadinessRow does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventMarketSignalRiskReadinessRow, "row")
        object.__setattr__(
            self,
            "event_label",
            _require_public_code("event_label", self.event_label),
        )
        object.__setattr__(self, "status", _require_status(self.status))
        for field_name in (
            "market_probability",
            "previous_probability",
            "probability_jump",
            "probability_move_15m",
            "probability_move_1h",
            "depth_collapse_ratio",
            "spread_width",
            "information_asymmetry_score",
            "adverse_selection_score",
            "risk_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "top_depth_now",
            "public_signal_lag_minutes",
            "pre_news_volume_ratio",
            "maker_fill_imbalance",
            "maker_quote_retreat_ratio",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "top_depth_baseline",
            _require_positive_decimal("top_depth_baseline", self.top_depth_baseline),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _require_reason_codes(self.reason_codes),
        )
        if self.status != _status_for_reason_codes(self.reason_codes):
            raise ValueError("status must match reason_codes")
        _require_hard_flags(self)
        _validate_row_derivations(self)
        _reject_unsafe_public_value(self)


@dataclass(frozen=True)
class ProbabilityEventMarketSignalRiskReadinessReasonCodeCount:
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventMarketSignalRiskReadinessReasonCodeCount does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ProbabilityEventMarketSignalRiskReadinessReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(
            self,
            "reason_code",
            _require_reason_code("reason_code", self.reason_code),
        )
        object.__setattr__(self, "count", _require_positive_count("count", self.count))
        _require_hard_flags(self)
        _reject_unsafe_public_value(self)


@dataclass(frozen=True)
class ProbabilityEventMarketSignalRiskReadinessReport:
    config_version: str
    status: str
    event_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_risk_score: Decimal
    mean_risk_score: Decimal
    reason_codes: tuple[str, ...]
    reason_code_counts: tuple[ProbabilityEventMarketSignalRiskReadinessReasonCodeCount, ...]
    rows: tuple[ProbabilityEventMarketSignalRiskReadinessRow, ...]
    manual_next_step: str
    payload_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ProbabilityEventMarketSignalRiskReadinessReport does not support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ProbabilityEventMarketSignalRiskReadinessReport, "report")
        object.__setattr__(
            self,
            "config_version",
            _require_public_code("config_version", self.config_version),
        )
        if self.config_version != DEFAULT_PROBABILITY_EVENT_MARKET_SIGNAL_RISK_READINESS_VERSION:
            raise ValueError("config_version must be supported")
        object.__setattr__(self, "status", _require_status(self.status))
        for field_name in ("event_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_risk_score", "mean_risk_score"):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _require_reason_codes(self.reason_codes))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "manual_next_step",
            _require_manual_next_step(self.manual_next_step),
        )
        _require_hard_flags(self)
        _validate_report(self)
        _reject_unsafe_public_value(self)
        digest = _payload_digest(_payload_items(self, payload_digest=""))
        if self.payload_digest == "":
            object.__setattr__(self, "payload_digest", digest)
        elif self.payload_digest != digest:
            raise ValueError("payload_digest must match public payload")
        else:
            _require_digest("payload_digest", self.payload_digest)


def build_probability_event_market_signal_risk_readiness_report(
    inputs: Iterable[ProbabilityEventMarketSignalRiskReadinessInput],
) -> ProbabilityEventMarketSignalRiskReadinessReport:
    rows = tuple(sorted((_row_for_input(item) for item in _normalize_inputs(inputs)), key=_row_key))
    status = _rollup_status(tuple(row.status for row in rows))
    reason_codes = _rollup_reason_codes(rows, status)
    return ProbabilityEventMarketSignalRiskReadinessReport(
        config_version=DEFAULT_PROBABILITY_EVENT_MARKET_SIGNAL_RISK_READINESS_VERSION,
        status=status,
        event_count=_count(len(rows)),
        pass_count=_count(sum(1 for row in rows if row.status == "pass")),
        watch_count=_count(sum(1 for row in rows if row.status == "watch")),
        block_count=_count(sum(1 for row in rows if row.status == "block")),
        max_risk_score=max((row.risk_score for row in rows), default=ZERO),
        mean_risk_score=_mean(row.risk_score for row in rows),
        reason_codes=reason_codes,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        rows=rows,
        manual_next_step=_manual_next_step(status),
    )


def probability_event_market_signal_risk_readiness_payload(
    report: ProbabilityEventMarketSignalRiskReadinessReport,
) -> dict[str, object]:
    if type(report) is not ProbabilityEventMarketSignalRiskReadinessReport:
        raise ValueError("report must be a ProbabilityEventMarketSignalRiskReadinessReport")
    _validate_report(report)
    payload = _payload_items(report, payload_digest=report.payload_digest)
    _validate_public_payload(payload)
    probability_event_market_signal_risk_readiness_payload_digest(payload)
    return payload


def probability_event_market_signal_risk_readiness_payload_digest(
    payload: ProbabilityEventMarketSignalRiskReadinessReport | Mapping[str, object],
) -> str:
    if type(payload) is ProbabilityEventMarketSignalRiskReadinessReport:
        public_payload = probability_event_market_signal_risk_readiness_payload(payload)
    elif isinstance(payload, Mapping):
        public_payload = dict(payload)
    else:
        raise ValueError("payload must be a report or mapping")
    _validate_public_payload(public_payload)
    unsigned = dict(public_payload)
    unsigned["payload_digest"] = ""
    digest = _payload_digest(unsigned)
    if public_payload["payload_digest"] != digest:
        raise ValueError("payload_digest must match public payload")
    return digest


def _row_for_input(
    item: ProbabilityEventMarketSignalRiskReadinessInput,
) -> ProbabilityEventMarketSignalRiskReadinessRow:
    probability_jump = max(
        abs(item.market_probability - item.previous_probability),
        item.probability_move_15m,
        item.probability_move_1h,
    )
    depth_collapse_ratio = _depth_collapse_ratio(item.top_depth_now, item.top_depth_baseline)
    information_asymmetry_score = _information_asymmetry_score(
        item.public_signal_lag_minutes,
        item.pre_news_volume_ratio,
    )
    adverse_selection_score = _adverse_selection_score(
        item.maker_fill_imbalance,
        item.maker_quote_retreat_ratio,
    )
    reason_codes = _row_reason_codes(
        probability_jump=probability_jump,
        depth_collapse_ratio=depth_collapse_ratio,
        spread_width=item.spread_width,
        information_asymmetry_score=information_asymmetry_score,
        adverse_selection_score=adverse_selection_score,
    )
    risk_score = _risk_score_for_reason_codes(reason_codes)
    return ProbabilityEventMarketSignalRiskReadinessRow(
        event_label=item.event_label,
        status=_status_for_reason_codes(reason_codes),
        market_probability=item.market_probability,
        previous_probability=item.previous_probability,
        probability_jump=_quantize(probability_jump),
        probability_move_15m=item.probability_move_15m,
        probability_move_1h=item.probability_move_1h,
        top_depth_now=item.top_depth_now,
        top_depth_baseline=item.top_depth_baseline,
        depth_collapse_ratio=depth_collapse_ratio,
        spread_width=item.spread_width,
        public_signal_lag_minutes=item.public_signal_lag_minutes,
        pre_news_volume_ratio=item.pre_news_volume_ratio,
        information_asymmetry_score=information_asymmetry_score,
        maker_fill_imbalance=item.maker_fill_imbalance,
        maker_quote_retreat_ratio=item.maker_quote_retreat_ratio,
        adverse_selection_score=adverse_selection_score,
        risk_score=risk_score,
        reason_codes=reason_codes,
    )


def _row_reason_codes(
    *,
    probability_jump: Decimal,
    depth_collapse_ratio: Decimal,
    spread_width: Decimal,
    information_asymmetry_score: Decimal,
    adverse_selection_score: Decimal,
) -> tuple[str, ...]:
    reasons: list[str] = []
    _append_threshold_reason(
        reasons,
        probability_jump,
        watch=PRICE_JUMP_WATCH,
        block=PRICE_JUMP_BLOCK,
        watch_code="price_jump_watch",
        block_code="price_jump_block",
    )
    _append_threshold_reason(
        reasons,
        depth_collapse_ratio,
        watch=DEPTH_COLLAPSE_WATCH,
        block=DEPTH_COLLAPSE_BLOCK,
        watch_code="depth_collapse_watch",
        block_code="depth_collapse_block",
    )
    _append_threshold_reason(
        reasons,
        spread_width,
        watch=SPREAD_WIDTH_WATCH,
        block=SPREAD_WIDTH_BLOCK,
        watch_code="spread_width_watch",
        block_code="spread_width_block",
    )
    _append_threshold_reason(
        reasons,
        information_asymmetry_score,
        watch=INFO_ASYMMETRY_WATCH,
        block=INFO_ASYMMETRY_BLOCK,
        watch_code="information_asymmetry_news_lead_watch",
        block_code="information_asymmetry_news_lead_block",
    )
    _append_threshold_reason(
        reasons,
        adverse_selection_score,
        watch=ADVERSE_SELECTION_WATCH,
        block=ADVERSE_SELECTION_BLOCK,
        watch_code="maker_adverse_selection_watch",
        block_code="maker_adverse_selection_block",
    )
    if not reasons:
        reasons.append("market_signal_risk_clear")
    return _require_reason_codes(tuple(sorted(reasons)))


def _validate_row_derivations(
    row: ProbabilityEventMarketSignalRiskReadinessRow,
) -> None:
    expected_probability_jump = _quantize(
        max(
            abs(row.market_probability - row.previous_probability),
            row.probability_move_15m,
            row.probability_move_1h,
        ),
    )
    if row.probability_jump != expected_probability_jump:
        raise ValueError("probability_jump must match row inputs")

    expected_depth_collapse_ratio = _depth_collapse_ratio(
        row.top_depth_now,
        row.top_depth_baseline,
    )
    if row.depth_collapse_ratio != expected_depth_collapse_ratio:
        raise ValueError("depth_collapse_ratio must match row inputs")

    expected_information_asymmetry_score = _information_asymmetry_score(
        row.public_signal_lag_minutes,
        row.pre_news_volume_ratio,
    )
    if row.information_asymmetry_score != expected_information_asymmetry_score:
        raise ValueError("information_asymmetry_score must match row inputs")

    expected_adverse_selection_score = _adverse_selection_score(
        row.maker_fill_imbalance,
        row.maker_quote_retreat_ratio,
    )
    if row.adverse_selection_score != expected_adverse_selection_score:
        raise ValueError("adverse_selection_score must match row inputs")

    expected_reason_codes = _row_reason_codes(
        probability_jump=expected_probability_jump,
        depth_collapse_ratio=expected_depth_collapse_ratio,
        spread_width=row.spread_width,
        information_asymmetry_score=expected_information_asymmetry_score,
        adverse_selection_score=expected_adverse_selection_score,
    )
    if row.reason_codes != expected_reason_codes:
        raise ValueError("reason_codes must match row inputs")

    expected_risk_score = _risk_score_for_reason_codes(expected_reason_codes)
    if row.risk_score != expected_risk_score:
        raise ValueError("risk_score must match row reason_codes")
    if row.status != _status_for_reason_codes(expected_reason_codes):
        raise ValueError("status must match row reason_codes")


def _append_threshold_reason(
    reasons: list[str],
    value: Decimal,
    *,
    watch: Decimal,
    block: Decimal,
    watch_code: str,
    block_code: str,
) -> None:
    if value >= block:
        reasons.append(block_code)
    elif value >= watch:
        reasons.append(watch_code)


def _rollup_status(statuses: tuple[str, ...]) -> str:
    if not statuses:
        return "block"
    if "block" in statuses:
        return "block"
    if "watch" in statuses:
        return "watch"
    return "pass"


def _rollup_reason_codes(
    rows: tuple[ProbabilityEventMarketSignalRiskReadinessRow, ...],
    status: str,
) -> tuple[str, ...]:
    if not rows:
        return ("market_signal_risk_readiness_no_inputs",)
    reasons = [f"market_signal_risk_readiness_{status}"]
    row_reasons = frozenset(reason for row in rows for reason in row.reason_codes)
    for reason in sorted(row_reasons):
        if reason in row_reasons and reason != "market_signal_risk_clear":
            reasons.append(reason)
    return _require_reason_codes(tuple(reasons))


def _reason_code_counts(
    rows: tuple[ProbabilityEventMarketSignalRiskReadinessRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ProbabilityEventMarketSignalRiskReadinessReasonCodeCount, ...]:
    if not rows:
        return (
            ProbabilityEventMarketSignalRiskReadinessReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ProbabilityEventMarketSignalRiskReadinessReasonCodeCount(
            reason_code=reason,
            count=_count(count),
        )
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def _manual_next_step(status: str) -> str:
    if status == "block":
        return "pause_probability_event_until_manual_risk_review"
    if status == "watch":
        return "refresh_public_sources_before_probability_review"
    return "continue_probability_event_research_review"


def _depth_collapse_ratio(top_depth_now: Decimal, top_depth_baseline: Decimal) -> Decimal:
    return _clamp_probability(ONE - (top_depth_now / top_depth_baseline))


def _information_asymmetry_score(
    public_signal_lag_minutes: Decimal,
    pre_news_volume_ratio: Decimal,
) -> Decimal:
    return _clamp_probability(
        (
            (public_signal_lag_minutes / Decimal("54.000000"))
            + _volume_pressure(pre_news_volume_ratio)
        )
        / TWO,
    )


def _volume_pressure(pre_news_volume_ratio: Decimal) -> Decimal:
    if pre_news_volume_ratio <= ZERO:
        return ZERO
    return _clamp_probability(ONE - (ONE / pre_news_volume_ratio))


def _adverse_selection_score(
    maker_fill_imbalance: Decimal,
    maker_quote_retreat_ratio: Decimal,
) -> Decimal:
    return _clamp_probability((maker_fill_imbalance + maker_quote_retreat_ratio) / TWO)


def _risk_score_for_reason_codes(reason_codes: tuple[str, ...]) -> Decimal:
    status = _status_for_reason_codes(reason_codes)
    if status == "block":
        return ONE
    if status == "watch":
        return Decimal("0.500000")
    return ZERO


def _mean(values: Iterable[Decimal]) -> Decimal:
    rows = tuple(values)
    if not rows:
        return ZERO
    return _quantize(sum(rows, ZERO) / Decimal(len(rows)))


def _normalize_inputs(
    inputs: Iterable[ProbabilityEventMarketSignalRiskReadinessInput],
) -> tuple[ProbabilityEventMarketSignalRiskReadinessInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        rows = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ProbabilityEventMarketSignalRiskReadinessInput:
            raise ValueError(
                "inputs must contain ProbabilityEventMarketSignalRiskReadinessInput values",
            )
        _require_hard_flags(row)
        if row.event_label in seen:
            raise ValueError("inputs must not contain duplicate event_label values")
        seen.add(row.event_label)
    return rows


def _normalize_rows(
    rows: Iterable[ProbabilityEventMarketSignalRiskReadinessRow],
) -> tuple[ProbabilityEventMarketSignalRiskReadinessRow, ...]:
    if isinstance(rows, (str, bytes)):
        raise ValueError("rows must be an iterable")
    try:
        values = tuple(rows)
    except TypeError as exc:
        raise ValueError("rows must be an iterable") from exc
    seen: set[str] = set()
    for row in values:
        if type(row) is not ProbabilityEventMarketSignalRiskReadinessRow:
            raise ValueError("rows must contain ProbabilityEventMarketSignalRiskReadinessRow values")
        _require_hard_flags(row)
        if row.event_label in seen:
            raise ValueError("rows must not contain duplicate event_label values")
        seen.add(row.event_label)
    if values != tuple(sorted(values, key=_row_key)):
        raise ValueError("rows must use canonical sequence")
    return values


def _normalize_reason_code_counts(
    counts: Iterable[ProbabilityEventMarketSignalRiskReadinessReasonCodeCount],
) -> tuple[ProbabilityEventMarketSignalRiskReadinessReasonCodeCount, ...]:
    if isinstance(counts, (str, bytes)):
        raise ValueError("reason_code_counts must be an iterable")
    try:
        values = tuple(counts)
    except TypeError as exc:
        raise ValueError("reason_code_counts must be an iterable") from exc
    seen: set[str] = set()
    for item in values:
        if type(item) is not ProbabilityEventMarketSignalRiskReadinessReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ProbabilityEventMarketSignalRiskReadinessReasonCodeCount values",
            )
        _require_hard_flags(item)
        if item.reason_code in seen:
            raise ValueError("reason_code_counts must not contain duplicate reason_code values")
        seen.add(item.reason_code)
    expected = tuple(sorted(values, key=lambda item: (-item.count, item.reason_code)))
    if values != expected:
        raise ValueError("reason_code_counts must use canonical sequence")
    return values


def _row_key(row: ProbabilityEventMarketSignalRiskReadinessRow) -> tuple[int, Decimal, str]:
    return ({"block": 0, "watch": 1, "pass": 2}[row.status], -row.risk_score, row.event_label)


def _status_for_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if any(reason.endswith("_block") for reason in reason_codes):
        return "block"
    if any(reason.endswith("_watch") for reason in reason_codes):
        return "watch"
    if reason_codes == ("market_signal_risk_readiness_no_inputs",):
        return "block"
    return "pass"


def _validate_report(report: ProbabilityEventMarketSignalRiskReadinessReport) -> None:
    _require_exact_type(report, ProbabilityEventMarketSignalRiskReadinessReport, "report")
    _require_hard_flags(report)
    _normalize_rows(report.rows)
    _normalize_reason_code_counts(report.reason_code_counts)
    rows = report.rows
    for row in rows:
        _validate_row_derivations(row)
    if report.event_count != _count(len(rows)):
        raise ValueError("event_count must match rows")
    if report.pass_count != _count(sum(1 for row in rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(sum(1 for row in rows if row.status == "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(sum(1 for row in rows if row.status == "block")):
        raise ValueError("block_count must match rows")
    if report.status != _rollup_status(tuple(row.status for row in rows)):
        raise ValueError("status must match rows")
    if report.reason_codes != _rollup_reason_codes(rows, report.status):
        raise ValueError("reason_codes must match rows")
    if report.reason_code_counts != _reason_code_counts(rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")
    if report.max_risk_score != max((row.risk_score for row in rows), default=ZERO):
        raise ValueError("max_risk_score must match rows")
    if report.mean_risk_score != _mean(row.risk_score for row in rows):
        raise ValueError("mean_risk_score must match rows")
    if report.manual_next_step != _manual_next_step(report.status):
        raise ValueError("manual_next_step must match status")


def _payload_items(
    report: ProbabilityEventMarketSignalRiskReadinessReport,
    *,
    payload_digest: str,
) -> dict[str, object]:
    return {
        "config_version": report.config_version,
        "status": report.status,
        "event_count": _count_text(report.event_count),
        "pass_count": _count_text(report.pass_count),
        "watch_count": _count_text(report.watch_count),
        "block_count": _count_text(report.block_count),
        "max_risk_score": _decimal_text(report.max_risk_score),
        "mean_risk_score": _decimal_text(report.mean_risk_score),
        "reason_codes": list(report.reason_codes),
        "reason_code_counts": [
            {
                "reason_code": row.reason_code,
                "count": _decimal_text(row.count),
                "paper_only": row.paper_only,
                "report_only": row.report_only,
                "readonly": row.readonly,
            }
            for row in report.reason_code_counts
        ],
        "rows": [_row_payload(row) for row in report.rows],
        "manual_next_step": report.manual_next_step,
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
        "payload_digest": payload_digest,
    }


def _row_payload(row: ProbabilityEventMarketSignalRiskReadinessRow) -> dict[str, object]:
    return {
        "event_label": row.event_label,
        "status": row.status,
        "market_probability": _decimal_text(row.market_probability),
        "previous_probability": _decimal_text(row.previous_probability),
        "probability_jump": _decimal_text(row.probability_jump),
        "probability_move_15m": _decimal_text(row.probability_move_15m),
        "probability_move_1h": _decimal_text(row.probability_move_1h),
        "top_depth_now": _decimal_text(row.top_depth_now),
        "top_depth_baseline": _decimal_text(row.top_depth_baseline),
        "depth_collapse_ratio": _decimal_text(row.depth_collapse_ratio),
        "spread_width": _decimal_text(row.spread_width),
        "public_signal_lag_minutes": _decimal_text(row.public_signal_lag_minutes),
        "pre_news_volume_ratio": _decimal_text(row.pre_news_volume_ratio),
        "information_asymmetry_score": _decimal_text(row.information_asymmetry_score),
        "maker_fill_imbalance": _decimal_text(row.maker_fill_imbalance),
        "maker_quote_retreat_ratio": _decimal_text(row.maker_quote_retreat_ratio),
        "adverse_selection_score": _decimal_text(row.adverse_selection_score),
        "risk_score": _decimal_text(row.risk_score),
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _report_from_public_payload(
    payload: Mapping[str, object],
) -> ProbabilityEventMarketSignalRiskReadinessReport:
    mapping = _mapping_from_payload("payload", payload, PAYLOAD_KEYS)
    reason_code_counts = mapping["reason_code_counts"]
    if type(reason_code_counts) is not list:
        raise ValueError("reason_code_counts must be a list")
    rows = mapping["rows"]
    if type(rows) is not list:
        raise ValueError("rows must be a list")
    return ProbabilityEventMarketSignalRiskReadinessReport(
        config_version=_string_from_payload("config_version", mapping["config_version"]),
        status=_string_from_payload("status", mapping["status"]),
        event_count=_decimal_from_payload("event_count", mapping["event_count"]),
        pass_count=_decimal_from_payload("pass_count", mapping["pass_count"]),
        watch_count=_decimal_from_payload("watch_count", mapping["watch_count"]),
        block_count=_decimal_from_payload("block_count", mapping["block_count"]),
        max_risk_score=_decimal_from_payload(
            "max_risk_score",
            mapping["max_risk_score"],
        ),
        mean_risk_score=_decimal_from_payload(
            "mean_risk_score",
            mapping["mean_risk_score"],
        ),
        reason_codes=_reason_codes_from_payload(
            "reason_codes",
            mapping["reason_codes"],
        ),
        reason_code_counts=tuple(
            _reason_code_count_from_payload(value, index=index)
            for index, value in enumerate(reason_code_counts)
        ),
        rows=tuple(
            _row_from_public_payload(value, index=index)
            for index, value in enumerate(rows)
        ),
        manual_next_step=_string_from_payload(
            "manual_next_step",
            mapping["manual_next_step"],
        ),
        payload_digest=_string_from_payload(
            "payload_digest",
            mapping["payload_digest"],
        ),
        paper_only=_bool_from_payload("paper_only", mapping["paper_only"]),
        report_only=_bool_from_payload("report_only", mapping["report_only"]),
        readonly=_bool_from_payload("readonly", mapping["readonly"]),
    )


def _reason_code_count_from_payload(
    value: object,
    *,
    index: int,
) -> ProbabilityEventMarketSignalRiskReadinessReasonCodeCount:
    path = f"reason_code_counts[{index}]"
    mapping = _mapping_from_payload(path, value, REASON_CODE_COUNT_PAYLOAD_KEYS)
    return ProbabilityEventMarketSignalRiskReadinessReasonCodeCount(
        reason_code=_string_from_payload(
            f"{path}.reason_code",
            mapping["reason_code"],
        ),
        count=_decimal_from_payload(f"{path}.count", mapping["count"]),
        paper_only=_bool_from_payload(
            f"{path}.paper_only",
            mapping["paper_only"],
        ),
        report_only=_bool_from_payload(
            f"{path}.report_only",
            mapping["report_only"],
        ),
        readonly=_bool_from_payload(f"{path}.readonly", mapping["readonly"]),
    )


def _row_from_public_payload(
    value: object,
    *,
    index: int,
) -> ProbabilityEventMarketSignalRiskReadinessRow:
    path = f"rows[{index}]"
    mapping = _mapping_from_payload(path, value, ROW_PAYLOAD_KEYS)
    return ProbabilityEventMarketSignalRiskReadinessRow(
        event_label=_string_from_payload(f"{path}.event_label", mapping["event_label"]),
        status=_string_from_payload(f"{path}.status", mapping["status"]),
        market_probability=_decimal_from_payload(
            f"{path}.market_probability",
            mapping["market_probability"],
        ),
        previous_probability=_decimal_from_payload(
            f"{path}.previous_probability",
            mapping["previous_probability"],
        ),
        probability_jump=_decimal_from_payload(
            f"{path}.probability_jump",
            mapping["probability_jump"],
        ),
        probability_move_15m=_decimal_from_payload(
            f"{path}.probability_move_15m",
            mapping["probability_move_15m"],
        ),
        probability_move_1h=_decimal_from_payload(
            f"{path}.probability_move_1h",
            mapping["probability_move_1h"],
        ),
        top_depth_now=_decimal_from_payload(
            f"{path}.top_depth_now",
            mapping["top_depth_now"],
        ),
        top_depth_baseline=_decimal_from_payload(
            f"{path}.top_depth_baseline",
            mapping["top_depth_baseline"],
        ),
        depth_collapse_ratio=_decimal_from_payload(
            f"{path}.depth_collapse_ratio",
            mapping["depth_collapse_ratio"],
        ),
        spread_width=_decimal_from_payload(
            f"{path}.spread_width",
            mapping["spread_width"],
        ),
        public_signal_lag_minutes=_decimal_from_payload(
            f"{path}.public_signal_lag_minutes",
            mapping["public_signal_lag_minutes"],
        ),
        pre_news_volume_ratio=_decimal_from_payload(
            f"{path}.pre_news_volume_ratio",
            mapping["pre_news_volume_ratio"],
        ),
        information_asymmetry_score=_decimal_from_payload(
            f"{path}.information_asymmetry_score",
            mapping["information_asymmetry_score"],
        ),
        maker_fill_imbalance=_decimal_from_payload(
            f"{path}.maker_fill_imbalance",
            mapping["maker_fill_imbalance"],
        ),
        maker_quote_retreat_ratio=_decimal_from_payload(
            f"{path}.maker_quote_retreat_ratio",
            mapping["maker_quote_retreat_ratio"],
        ),
        adverse_selection_score=_decimal_from_payload(
            f"{path}.adverse_selection_score",
            mapping["adverse_selection_score"],
        ),
        risk_score=_decimal_from_payload(f"{path}.risk_score", mapping["risk_score"]),
        reason_codes=_reason_codes_from_payload(
            f"{path}.reason_codes",
            mapping["reason_codes"],
        ),
        paper_only=_bool_from_payload(
            f"{path}.paper_only",
            mapping["paper_only"],
        ),
        report_only=_bool_from_payload(
            f"{path}.report_only",
            mapping["report_only"],
        ),
        readonly=_bool_from_payload(f"{path}.readonly", mapping["readonly"]),
    )


def _mapping_from_payload(
    field_name: str,
    value: object,
    expected_keys: tuple[str, ...],
) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    if len(value) != len(expected_keys) or frozenset(value.keys()) != frozenset(
        expected_keys,
    ):
        raise ValueError(f"{field_name} keys must match public schema")
    return value


def _string_from_payload(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    return value


def _decimal_from_payload(field_name: str, value: object) -> Decimal:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a Decimal string")
    try:
        decimal_value = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field_name} must be a Decimal string") from exc
    if not decimal_value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return decimal_value


def _bool_from_payload(field_name: str, value: object) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a bool")
    return value


def _reason_codes_from_payload(field_name: str, value: object) -> tuple[str, ...]:
    if type(value) is not list:
        raise ValueError(f"{field_name} must be a list")
    return tuple(
        _string_from_payload(f"{field_name}[{index}]", reason_code)
        for index, reason_code in enumerate(value)
    )


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    _mapping_from_payload("payload", payload, PAYLOAD_KEYS)
    _reject_numeric_payload_values(payload)
    _require_digest("payload_digest", payload["payload_digest"])
    _require_hard_flags(_DictFlags(payload))
    _reject_unsafe_public_value(payload)
    unsigned = dict(payload)
    unsigned["payload_digest"] = ""
    if payload["payload_digest"] != _payload_digest(unsigned):
        raise ValueError("payload_digest must match public payload")
    report = _report_from_public_payload(payload)
    if _payload_items(report, payload_digest=report.payload_digest) != dict(payload):
        raise ValueError("public payload must match normalized report")


def _reject_numeric_payload_values(value: object) -> None:
    if isinstance(value, Mapping):
        for item in value.values():
            _reject_numeric_payload_values(item)
        return
    if type(value) is list:
        for item in value:
            _reject_numeric_payload_values(item)
        return
    if type(value) in (int, float, Decimal):
        raise ValueError("payload must contain Decimal strings")


def _payload_digest(payload: Mapping[str, object]) -> str:
    _reject_unsafe_public_value(payload)
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_probability_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(field_name, value))
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _quantize(_require_decimal(field_name, value))
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value():
        raise ValueError(f"{field_name} must be a whole number")
    return normalized.quantize(COUNT_QUANTUM)


def _require_positive_count(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_count(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_public_code(field_name: str, value: object) -> str:
    if type(value) is not str or value == "":
        raise ValueError(f"{field_name} must be a public code")
    for char in value:
        if not (char == "-" or char == "_" or char == "." or char.isdigit() or "a" <= char <= "z"):
            raise ValueError(f"{field_name} must be a public code")
    return value


def _require_status(value: object) -> str:
    if type(value) is not str or value not in STATUS_VALUES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str or value not in REASON_VALUES:
        raise ValueError(f"{field_name} must be supported")
    return value


def _require_reason_codes(values: object) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    if len(set(values)) != len(values):
        raise ValueError("reason_codes must not contain duplicates")
    for value in values:
        _require_reason_code("reason_codes", value)
    return values


def _require_manual_next_step(value: object) -> str:
    if type(value) is not str or value not in MANUAL_NEXT_STEPS:
        raise ValueError("manual_next_step must be supported")
    return value


def _require_digest(field_name: str, value: object) -> str:
    if type(value) is not str or len(value) != 64:
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    for char in value:
        if not (char.isdigit() or "a" <= char <= "f"):
            raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(value: object) -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        flag = value[field_name] if isinstance(value, Mapping) else getattr(value, field_name)
        if flag is not True:
            raise ValueError(f"{field_name} must be True")


def _quantize(value: Decimal) -> Decimal:
    try:
        return value.quantize(QUANTUM, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError("Decimal value must be quantizable") from exc


def _clamp_probability(value: Decimal) -> Decimal:
    quantized = _quantize(value)
    if quantized < ZERO:
        return ZERO
    if quantized > ONE:
        return ONE
    return quantized


def _decimal_text(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _count_text(value: Decimal) -> str:
    return format(value.quantize(COUNT_QUANTUM), "f")


def _count(value: int) -> Decimal:
    return Decimal(value).quantize(COUNT_QUANTUM)


def _reject_unsafe_public_value(value: object) -> None:
    serialized = json.dumps(value, sort_keys=True, default=str).lower()
    restricted_terms = (
        "wal" + "let",
        "au" + "th",
        "private" + "_" + "key",
        "api" + "_" + "key",
        "ke" + "y",
        "sec" + "ret",
        "tok" + "en",
        "sig" + "nature",
        "sig" + "ning",
        "ord" + "er",
        "tra" + "de",
        "pos" + "ition",
        "b" + "uy",
        "s" + "ell",
        "recom" + "mend",
        "adv" + "ice",
        *UNSAFE_PUBLIC_TERMS,
    )
    for term in restricted_terms:
        if term in serialized:
            raise ValueError("public value must not expose restricted surfaces")


@dataclass(frozen=True)
class _DictFlags:
    value: Mapping[str, object]

    @property
    def paper_only(self) -> object:
        return self.value.get("paper_only")

    @property
    def report_only(self) -> object:
        return self.value.get("report_only")

    @property
    def readonly(self) -> object:
        return self.value.get("readonly")
