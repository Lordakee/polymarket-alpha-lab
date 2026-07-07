"""Pure research-only market outlier detector."""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Any

from polymarket_alpha_lab.team_paper_guard import require_paper_only_flags


DEFAULT_RESEARCH_MARKET_OUTLIER_DETECTOR_CONFIG_VERSION = (
    "research-market-outlier-detector-v0"
)

STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
STATUSES = (STATUS_PASS, STATUS_WATCH, STATUS_BLOCK)

REPORT_ACTIONS = {
    STATUS_PASS: "pass_report_only_research_market_outlier_detector",
    STATUS_WATCH: "watch_report_only_research_market_outlier_detector",
    STATUS_BLOCK: "block_report_only_research_market_outlier_detector",
}

REASON_PREFIX = "research_market_outlier_detector_"
BASE_RATE_DRIFT_REASON = f"{REASON_PREFIX}base_rate_drift"
PUBLIC_ATTENTION_GAP_REASON = f"{REASON_PREFIX}public_attention_gap"
CROWD_OVERREACTION_REASON = f"{REASON_PREFIX}crowd_overreaction"
LOW_EVIDENCE_QUALITY_REASON = f"{REASON_PREFIX}low_evidence_quality"
PASS_REASON = f"{REASON_PREFIX}pass"
NO_INPUTS_REASON = f"{REASON_PREFIX}no_inputs"

ROW_REASON_SEQUENCE = (
    BASE_RATE_DRIFT_REASON,
    PUBLIC_ATTENTION_GAP_REASON,
    CROWD_OVERREACTION_REASON,
    LOW_EVIDENCE_QUALITY_REASON,
    PASS_REASON,
)
REPORT_REASON_SEQUENCE = (
    BASE_RATE_DRIFT_REASON,
    PUBLIC_ATTENTION_GAP_REASON,
    CROWD_OVERREACTION_REASON,
    LOW_EVIDENCE_QUALITY_REASON,
    PASS_REASON,
    NO_INPUTS_REASON,
)

DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
QUANT = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
FOUR = Decimal("4.000000")

UNSAFE_PUBLIC_FRAGMENTS = frozenset(
    (
        "raw_",
        "_identifier",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "sourceurl",
        "sourcetext",
        "http",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "recommendation",
        "buy",
        "sell",
    ),
)


@dataclass(frozen=True)
class ResearchMarketOutlierDetectorConfig:
    config_version: str = DEFAULT_RESEARCH_MARKET_OUTLIER_DETECTOR_CONFIG_VERSION
    base_rate_drift_watch_threshold: Decimal = Decimal("0.100000")
    base_rate_drift_block_threshold: Decimal = Decimal("0.250000")
    attention_gap_watch_threshold: Decimal = Decimal("0.200000")
    attention_gap_block_threshold: Decimal = Decimal("0.400000")
    overreaction_watch_threshold: Decimal = Decimal("0.150000")
    overreaction_block_threshold: Decimal = Decimal("0.250000")
    evidence_quality_watch_floor: Decimal = Decimal("0.500000")
    evidence_quality_block_floor: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketOutlierDetectorConfig:
            raise TypeError("ResearchMarketOutlierDetectorConfig does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketOutlierDetectorConfig:
            raise ValueError("config must be exactly ResearchMarketOutlierDetectorConfig")
        _require_canonical_string("config_version", self.config_version)
        for field_name in (
            "base_rate_drift_watch_threshold",
            "base_rate_drift_block_threshold",
            "attention_gap_watch_threshold",
            "attention_gap_block_threshold",
            "overreaction_watch_threshold",
            "overreaction_block_threshold",
            "evidence_quality_watch_floor",
            "evidence_quality_block_floor",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_ordered_thresholds(
            "base_rate_drift_block_threshold",
            self.base_rate_drift_watch_threshold,
            self.base_rate_drift_block_threshold,
        )
        _require_ordered_thresholds(
            "attention_gap_block_threshold",
            self.attention_gap_watch_threshold,
            self.attention_gap_block_threshold,
        )
        _require_ordered_thresholds(
            "overreaction_block_threshold",
            self.overreaction_watch_threshold,
            self.overreaction_block_threshold,
        )
        if self.evidence_quality_block_floor > self.evidence_quality_watch_floor:
            raise ValueError(
                "evidence_quality_block_floor must not exceed evidence_quality_watch_floor",
            )
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketOutlierDetectorInputRow:
    raw_candidate_identifier: str
    raw_market_identifier: str
    public_bucket: str
    base_rate_probability: Decimal
    current_probability: Decimal
    public_attention_score: Decimal
    research_attention_score: Decimal
    probability_move_score: Decimal
    evidence_move_score: Decimal
    evidence_quality_score: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketOutlierDetectorInputRow:
            raise TypeError("ResearchMarketOutlierDetectorInputRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketOutlierDetectorInputRow:
            raise ValueError("input row must be exactly ResearchMarketOutlierDetectorInputRow")
        _require_private_string("raw_candidate_identifier", self.raw_candidate_identifier)
        _require_private_string("raw_market_identifier", self.raw_market_identifier)
        _require_public_label("public_bucket", self.public_bucket)
        for field_name in (
            "base_rate_probability",
            "current_probability",
            "public_attention_score",
            "research_attention_score",
            "probability_move_score",
            "evidence_move_score",
            "evidence_quality_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_hard_flags("input row", self)


@dataclass(frozen=True)
class ResearchMarketOutlierDetectorRow:
    outlier_ref: str
    public_bucket: str
    base_rate_probability: Decimal
    current_probability: Decimal
    public_attention_score: Decimal
    research_attention_score: Decimal
    probability_move_score: Decimal
    evidence_move_score: Decimal
    evidence_quality_score: Decimal
    base_rate_drift: Decimal
    attention_gap: Decimal
    overreaction_score: Decimal
    evidence_quality_gap: Decimal
    anomaly_score: Decimal
    row_status: str
    redacted_outlier_reasons: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketOutlierDetectorRow:
            raise TypeError("ResearchMarketOutlierDetectorRow does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketOutlierDetectorRow:
            raise ValueError("row must be exactly ResearchMarketOutlierDetectorRow")
        _require_outlier_ref("outlier_ref", self.outlier_ref)
        _require_public_label("public_bucket", self.public_bucket)
        for field_name in (
            "base_rate_probability",
            "current_probability",
            "public_attention_score",
            "research_attention_score",
            "probability_move_score",
            "evidence_move_score",
            "evidence_quality_score",
            "base_rate_drift",
            "attention_gap",
            "overreaction_score",
            "evidence_quality_gap",
            "anomaly_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("row_status", self.row_status)
        object.__setattr__(
            self,
            "redacted_outlier_reasons",
            _normalize_row_reasons(self.redacted_outlier_reasons),
        )
        _validate_row(self)
        _require_hard_flags("row", self)


@dataclass(frozen=True)
class ResearchMarketOutlierDetectorReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketOutlierDetectorReasonCodeCount:
            raise TypeError(
                "ResearchMarketOutlierDetectorReasonCodeCount does not support subclassing",
            )

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketOutlierDetectorReasonCodeCount:
            raise ValueError(
                "reason count must be exactly ResearchMarketOutlierDetectorReasonCodeCount",
            )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_count_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason count", self)


@dataclass(frozen=True)
class ResearchMarketOutlierDetectorReport:
    generated_at: datetime
    config_version: str
    report_status: str
    report_action: str
    input_count: Decimal
    outlier_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    base_rate_drift_count: Decimal
    attention_gap_count: Decimal
    crowd_overreaction_count: Decimal
    low_evidence_quality_count: Decimal
    max_anomaly_score: Decimal
    average_evidence_quality_score: Decimal
    rows: tuple[ResearchMarketOutlierDetectorRow, ...]
    reason_code_counts: tuple[ResearchMarketOutlierDetectorReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if cls is not ResearchMarketOutlierDetectorReport:
            raise TypeError("ResearchMarketOutlierDetectorReport does not support subclassing")

    def __post_init__(self) -> None:
        if type(self) is not ResearchMarketOutlierDetectorReport:
            raise ValueError("report must be exactly ResearchMarketOutlierDetectorReport")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_canonical_string("config_version", self.config_version)
        _require_status("report_status", self.report_status)
        _require_canonical_string("report_action", self.report_action)
        for field_name in (
            "input_count",
            "outlier_count",
            "pass_count",
            "watch_count",
            "block_count",
            "base_rate_drift_count",
            "attention_gap_count",
            "crowd_overreaction_count",
            "low_evidence_quality_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_count_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in ("max_anomaly_score", "average_evidence_quality_score"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_report_reasons(self.reason_codes),
        )
        _validate_report(self)
        _reject_unsafe_public_surface("report", self)
        _require_hard_flags("report", self)


def build_research_market_outlier_detector(
    input_rows: list[ResearchMarketOutlierDetectorInputRow]
    | tuple[ResearchMarketOutlierDetectorInputRow, ...],
    *,
    config: ResearchMarketOutlierDetectorConfig,
    generated_at: datetime,
) -> ResearchMarketOutlierDetectorReport:
    if type(config) is not ResearchMarketOutlierDetectorConfig:
        raise ValueError("config must be a ResearchMarketOutlierDetectorConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized_inputs = _normalize_input_rows(input_rows)
    rows = tuple(_row_from_input(row, config=config) for row in normalized_inputs)
    ranked_rows = _ranked_rows(rows)

    if not ranked_rows:
        reason_code_counts = (
            ResearchMarketOutlierDetectorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
        reason_codes = (NO_INPUTS_REASON,)
    else:
        reason_code_counts = _reason_code_counts(ranked_rows)
        reason_codes = tuple(item.reason_code for item in reason_code_counts)

    input_count = _count(len(ranked_rows))
    pass_count = _count(sum(1 for row in ranked_rows if row.row_status == STATUS_PASS))
    watch_count = _count(sum(1 for row in ranked_rows if row.row_status == STATUS_WATCH))
    block_count = _count(sum(1 for row in ranked_rows if row.row_status == STATUS_BLOCK))
    report_status = _report_status(
        has_inputs=bool(ranked_rows),
        watch_count=watch_count,
        block_count=block_count,
    )

    return ResearchMarketOutlierDetectorReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        report_status=report_status,
        report_action=REPORT_ACTIONS[report_status],
        input_count=input_count,
        outlier_count=_count(
            sum(1 for row in ranked_rows if row.row_status != STATUS_PASS),
        ),
        pass_count=pass_count,
        watch_count=watch_count,
        block_count=block_count,
        base_rate_drift_count=_reason_count(ranked_rows, BASE_RATE_DRIFT_REASON),
        attention_gap_count=_reason_count(ranked_rows, PUBLIC_ATTENTION_GAP_REASON),
        crowd_overreaction_count=_reason_count(ranked_rows, CROWD_OVERREACTION_REASON),
        low_evidence_quality_count=_reason_count(ranked_rows, LOW_EVIDENCE_QUALITY_REASON),
        max_anomaly_score=max((row.anomaly_score for row in ranked_rows), default=ZERO),
        average_evidence_quality_score=_ratio(
            _sum_decimal(row.evidence_quality_score for row in ranked_rows),
            input_count,
        ),
        rows=ranked_rows,
        reason_code_counts=reason_code_counts,
        reason_codes=reason_codes,
    )


def research_market_outlier_detector_payload(
    report: ResearchMarketOutlierDetectorReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketOutlierDetectorReport:
        _require_hard_flags("report", report)
        _reject_unsafe_public_surface("report", report)
        payload = _json_ready(report)
    elif type(report) is dict:
        _reject_unsafe_public_surface("payload", report)
        _reject_public_numerics(report)
        payload = _json_ready(report)
    else:
        raise ValueError("report must be a ResearchMarketOutlierDetectorReport")
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_public_numerics(payload)
    _reject_unsafe_public_surface("payload", payload)
    return payload


def _row_from_input(
    row: ResearchMarketOutlierDetectorInputRow,
    *,
    config: ResearchMarketOutlierDetectorConfig,
) -> ResearchMarketOutlierDetectorRow:
    base_rate_drift = _abs_decimal(row.current_probability - row.base_rate_probability)
    attention_gap = _positive_difference(
        row.public_attention_score,
        row.research_attention_score,
    )
    overreaction_score = _positive_difference(
        row.probability_move_score,
        row.evidence_move_score,
    )
    evidence_quality_gap = _quantize(ONE - row.evidence_quality_score)
    anomaly_score = _ratio(
        base_rate_drift + attention_gap + overreaction_score + evidence_quality_gap,
        FOUR,
    )
    reasons = _row_reasons(
        base_rate_drift=base_rate_drift,
        attention_gap=attention_gap,
        overreaction_score=overreaction_score,
        evidence_quality_score=row.evidence_quality_score,
        config=config,
    )
    return ResearchMarketOutlierDetectorRow(
        outlier_ref=_outlier_ref(row.raw_candidate_identifier, row.raw_market_identifier),
        public_bucket=row.public_bucket,
        base_rate_probability=row.base_rate_probability,
        current_probability=row.current_probability,
        public_attention_score=row.public_attention_score,
        research_attention_score=row.research_attention_score,
        probability_move_score=row.probability_move_score,
        evidence_move_score=row.evidence_move_score,
        evidence_quality_score=row.evidence_quality_score,
        base_rate_drift=base_rate_drift,
        attention_gap=attention_gap,
        overreaction_score=overreaction_score,
        evidence_quality_gap=evidence_quality_gap,
        anomaly_score=anomaly_score,
        row_status=_row_status(
            base_rate_drift=base_rate_drift,
            attention_gap=attention_gap,
            overreaction_score=overreaction_score,
            evidence_quality_score=row.evidence_quality_score,
            reasons=reasons,
            config=config,
        ),
        redacted_outlier_reasons=reasons,
    )


def _normalize_input_rows(
    rows: list[ResearchMarketOutlierDetectorInputRow]
    | tuple[ResearchMarketOutlierDetectorInputRow, ...],
) -> tuple[ResearchMarketOutlierDetectorInputRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("input rows must be a list or tuple")
    normalized = tuple(rows)
    seen: set[tuple[str, str]] = set()
    for row in normalized:
        if type(row) is not ResearchMarketOutlierDetectorInputRow:
            raise ValueError("input rows must contain ResearchMarketOutlierDetectorInputRow")
        _require_hard_flags("input row", row)
        key = (row.raw_candidate_identifier, row.raw_market_identifier)
        if key in seen:
            raise ValueError("input rows must not contain duplicate raw rows")
        seen.add(key)
    return normalized


def _row_reasons(
    *,
    base_rate_drift: Decimal,
    attention_gap: Decimal,
    overreaction_score: Decimal,
    evidence_quality_score: Decimal,
    config: ResearchMarketOutlierDetectorConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if base_rate_drift >= config.base_rate_drift_watch_threshold:
        reasons.append(BASE_RATE_DRIFT_REASON)
    if attention_gap >= config.attention_gap_watch_threshold:
        reasons.append(PUBLIC_ATTENTION_GAP_REASON)
    if overreaction_score >= config.overreaction_watch_threshold:
        reasons.append(CROWD_OVERREACTION_REASON)
    if evidence_quality_score <= config.evidence_quality_watch_floor:
        reasons.append(LOW_EVIDENCE_QUALITY_REASON)
    if not reasons:
        reasons.append(PASS_REASON)
    return tuple(reason for reason in ROW_REASON_SEQUENCE if reason in reasons)


def _row_status(
    *,
    base_rate_drift: Decimal,
    attention_gap: Decimal,
    overreaction_score: Decimal,
    evidence_quality_score: Decimal,
    reasons: tuple[str, ...],
    config: ResearchMarketOutlierDetectorConfig,
) -> str:
    if (
        base_rate_drift >= config.base_rate_drift_block_threshold
        or attention_gap >= config.attention_gap_block_threshold
        or overreaction_score >= config.overreaction_block_threshold
        or evidence_quality_score <= config.evidence_quality_block_floor
    ):
        return STATUS_BLOCK
    if reasons == (PASS_REASON,):
        return STATUS_PASS
    return STATUS_WATCH


def _report_status(
    *,
    has_inputs: bool,
    watch_count: Decimal,
    block_count: Decimal,
) -> str:
    if not has_inputs or block_count > ZERO:
        return STATUS_BLOCK
    if watch_count > ZERO:
        return STATUS_WATCH
    return STATUS_PASS


def _ranked_rows(
    rows: tuple[ResearchMarketOutlierDetectorRow, ...],
) -> tuple[ResearchMarketOutlierDetectorRow, ...]:
    return tuple(
        sorted(
            rows,
            key=lambda row: (
                _status_rank(row.row_status),
                -row.anomaly_score,
                row.public_bucket,
                row.outlier_ref,
            ),
        ),
    )


def _status_rank(value: str) -> int:
    return {
        STATUS_BLOCK: 0,
        STATUS_WATCH: 1,
        STATUS_PASS: 2,
    }[value]


def _reason_code_counts(
    rows: tuple[ResearchMarketOutlierDetectorRow, ...],
) -> tuple[ResearchMarketOutlierDetectorReasonCodeCount, ...]:
    total = _count(len(rows))
    counts: dict[str, Decimal] = {}
    for row in rows:
        for reason_code in row.redacted_outlier_reasons:
            counts[reason_code] = counts.get(reason_code, ZERO) + ONE
    return tuple(
        ResearchMarketOutlierDetectorReasonCodeCount(
            reason_code=reason_code,
            count=_count(counts[reason_code]),
            row_ratio=_ratio(counts[reason_code], total),
        )
        for reason_code in REPORT_REASON_SEQUENCE
        if reason_code in counts
    )


def _reason_count(
    rows: tuple[ResearchMarketOutlierDetectorRow, ...],
    reason_code: str,
) -> Decimal:
    return _count(sum(1 for row in rows if reason_code in row.redacted_outlier_reasons))


def _validate_row(row: ResearchMarketOutlierDetectorRow) -> None:
    if row.base_rate_drift != _abs_decimal(row.current_probability - row.base_rate_probability):
        raise ValueError("base_rate_drift must match probability inputs")
    if row.attention_gap != _positive_difference(
        row.public_attention_score,
        row.research_attention_score,
    ):
        raise ValueError("attention_gap must match attention inputs")
    if row.overreaction_score != _positive_difference(
        row.probability_move_score,
        row.evidence_move_score,
    ):
        raise ValueError("overreaction_score must match movement inputs")
    if row.evidence_quality_gap != _quantize(ONE - row.evidence_quality_score):
        raise ValueError("evidence_quality_gap must match evidence_quality_score")
    if row.anomaly_score != _ratio(
        row.base_rate_drift + row.attention_gap + row.overreaction_score + row.evidence_quality_gap,
        FOUR,
    ):
        raise ValueError("anomaly_score must match row components")
    if row.redacted_outlier_reasons == (PASS_REASON,) and row.row_status != STATUS_PASS:
        raise ValueError("row_status must match redacted_outlier_reasons")
    if row.redacted_outlier_reasons != (PASS_REASON,) and row.row_status == STATUS_PASS:
        raise ValueError("row_status must match redacted_outlier_reasons")


def _validate_report(report: ResearchMarketOutlierDetectorReport) -> None:
    if report.report_action != REPORT_ACTIONS[report.report_status]:
        raise ValueError("report_action must match report_status")
    if report.rows != _ranked_rows(report.rows):
        raise ValueError("rows must be sorted deterministically")
    if report.input_count != _count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.outlier_count != _count(
        sum(1 for row in report.rows if row.row_status != STATUS_PASS),
    ):
        raise ValueError("outlier_count must match rows")
    if report.pass_count != _count(sum(1 for row in report.rows if row.row_status == STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _count(
        sum(1 for row in report.rows if row.row_status == STATUS_WATCH),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _count(
        sum(1 for row in report.rows if row.row_status == STATUS_BLOCK),
    ):
        raise ValueError("block_count must match rows")
    if report.base_rate_drift_count != _reason_count(report.rows, BASE_RATE_DRIFT_REASON):
        raise ValueError("base_rate_drift_count must match rows")
    if report.attention_gap_count != _reason_count(report.rows, PUBLIC_ATTENTION_GAP_REASON):
        raise ValueError("attention_gap_count must match rows")
    if report.crowd_overreaction_count != _reason_count(report.rows, CROWD_OVERREACTION_REASON):
        raise ValueError("crowd_overreaction_count must match rows")
    if report.low_evidence_quality_count != _reason_count(report.rows, LOW_EVIDENCE_QUALITY_REASON):
        raise ValueError("low_evidence_quality_count must match rows")
    expected_max_anomaly = max((row.anomaly_score for row in report.rows), default=ZERO)
    if report.max_anomaly_score != expected_max_anomaly:
        raise ValueError("max_anomaly_score must match rows")
    if report.average_evidence_quality_score != _ratio(
        _sum_decimal(row.evidence_quality_score for row in report.rows),
        report.input_count,
    ):
        raise ValueError("average_evidence_quality_score must match rows")
    expected_reason_counts = _reason_code_counts(report.rows)
    if not report.rows:
        expected_reason_counts = (
            ResearchMarketOutlierDetectorReasonCodeCount(
                reason_code=NO_INPUTS_REASON,
                count=ONE,
                row_ratio=ONE,
            ),
        )
    if report.reason_code_counts != expected_reason_counts:
        raise ValueError("reason_code_counts must match rows")
    if report.reason_codes != tuple(item.reason_code for item in report.reason_code_counts):
        raise ValueError("reason_codes must match reason_code_counts")
    expected_status = _report_status(
        has_inputs=bool(report.rows),
        watch_count=report.watch_count,
        block_count=report.block_count,
    )
    if report.report_status != expected_status:
        raise ValueError("report_status must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketOutlierDetectorRow, ...],
) -> tuple[ResearchMarketOutlierDetectorRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketOutlierDetectorRow:
            raise ValueError("rows must contain ResearchMarketOutlierDetectorRow")
        _require_hard_flags("row", row)
    return rows


def _normalize_reason_code_counts(
    values: tuple[ResearchMarketOutlierDetectorReasonCodeCount, ...],
) -> tuple[ResearchMarketOutlierDetectorReasonCodeCount, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for item in values:
        if type(item) is not ResearchMarketOutlierDetectorReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain ResearchMarketOutlierDetectorReasonCodeCount",
            )
        _require_hard_flags("reason count", item)
    normalized = tuple(
        reason_code
        for reason_code in REPORT_REASON_SEQUENCE
        if reason_code in {item.reason_code for item in values}
    )
    if normalized != tuple(item.reason_code for item in values):
        raise ValueError("reason_code_counts must be deterministically sorted")
    return values


def _normalize_row_reasons(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("redacted_outlier_reasons must be a tuple")
    if not values:
        raise ValueError("redacted_outlier_reasons must not be empty")
    for value in values:
        _require_reason_code("redacted_outlier_reasons", value)
        if value not in ROW_REASON_SEQUENCE:
            raise ValueError("redacted_outlier_reasons must be row reason codes")
    normalized = tuple(reason_code for reason_code in ROW_REASON_SEQUENCE if reason_code in values)
    if normalized != values or len(set(values)) != len(values):
        raise ValueError("redacted_outlier_reasons must be deterministic and unique")
    if PASS_REASON in values and values != (PASS_REASON,):
        raise ValueError("redacted_outlier_reasons cannot mix pass with other reasons")
    return values


def _normalize_report_reasons(values: tuple[str, ...]) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    if not values:
        raise ValueError("reason_codes must not be empty")
    for value in values:
        _require_reason_code("reason_codes", value)
    normalized = tuple(reason_code for reason_code in REPORT_REASON_SEQUENCE if reason_code in values)
    if normalized != values or len(set(values)) != len(values):
        raise ValueError("reason_codes must be deterministic and unique")
    return values


def _require_status(field_name: str, value: str) -> None:
    if type(value) is not str or value not in STATUSES:
        raise ValueError(f"{field_name} must be a valid status")


def _require_reason_code(field_name: str, value: str) -> None:
    if type(value) is not str or value not in REPORT_REASON_SEQUENCE:
        raise ValueError(f"{field_name} must be a known reason code")


def _require_hard_flags(label: str, value: object) -> None:
    require_paper_only_flags(label, value)


def _require_private_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_canonical_string(field_name: str, value: object) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    if value != value.strip() or any(character.isspace() for character in value):
        raise ValueError(f"{field_name} must be canonical")
    if not all(character.islower() or character.isdigit() or character in "_-" for character in value):
        raise ValueError(f"{field_name} must be canonical")
    return value


def _require_public_label(field_name: str, value: object) -> str:
    _require_canonical_string(field_name, value)
    _reject_unsafe_public_fragment(field_name, value)
    return value


def _require_outlier_ref(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    prefix = "outlier_"
    if not value.startswith(prefix) or len(value) != len(prefix) + 12:
        raise ValueError(f"{field_name} must be a redacted outlier reference")
    suffix = value[len(prefix) :]
    if any(character not in "0123456789abcdef" for character in suffix):
        raise ValueError(f"{field_name} must be a redacted outlier reference")
    return value


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{field_name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_nonnegative_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_finite_decimal(field_name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    quantized = _quantize(decimal_value)
    if quantized != decimal_value:
        raise ValueError(f"{field_name} must use six decimal places")
    return quantized


def _require_positive_count_decimal(field_name: str, value: object) -> Decimal:
    decimal_value = _require_nonnegative_count_decimal(field_name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return decimal_value


def _require_finite_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return value


def _require_ordered_thresholds(field_name: str, watch_threshold: Decimal, block_threshold: Decimal) -> None:
    if block_threshold < watch_threshold:
        raise ValueError(f"{field_name} must be at least the watch threshold")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _outlier_ref(raw_candidate_identifier: str, raw_market_identifier: str) -> str:
    digest = hashlib.sha256(
        f"{raw_candidate_identifier}|{raw_market_identifier}".encode("utf-8"),
    ).hexdigest()[:12]
    return f"outlier_{digest}"


def _positive_difference(high_value: Decimal, low_value: Decimal) -> Decimal:
    difference = high_value - low_value
    if difference <= ZERO:
        return ZERO
    return _quantize(difference)


def _abs_decimal(value: Decimal) -> Decimal:
    if value < ZERO:
        return _quantize(-value)
    return _quantize(value)


def _sum_decimal(values: object) -> Decimal:
    total = ZERO
    for value in values:
        total += value
    return _quantize(total)


def _count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    try:
        with localcontext(DECIMAL_CONTEXT):
            return value.quantize(QUANT)
    except InvalidOperation as exc:
        raise ValueError("Decimal value cannot be quantized") from exc


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


def _json_ready(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _json_ready(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("JSON Decimal value must be exactly Decimal")
        if not value.is_finite():
            raise ValueError("JSON Decimal value must be finite")
        return str(value)
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("JSON datetime value must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("JSON datetime value must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("JSON value must not be a float")
    if type(value) is int:
        raise ValueError("JSON numeric value must use Decimal")
    if type(value) in (str, bool):
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready[key] = _json_ready(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    raise ValueError("value is not JSON serializable")


def _reject_public_numerics(value: object) -> None:
    if isinstance(value, float) or type(value) is int:
        raise ValueError("public payload numerics must be Decimal-derived strings")
    if isinstance(value, dict):
        for item in value.values():
            _reject_public_numerics(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_public_numerics(item)


def _reject_unsafe_public_surface(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        _reject_unsafe_public_surface(label, asdict(value))
        return
    if type(value) is str:
        _reject_unsafe_public_fragment(label, value)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_fragment(label, key)
            if key in {"paper_only", "report_only", "readonly"} and item is not True:
                raise ValueError(f"{key} must be True for {label}")
            _reject_unsafe_public_surface(label, item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_surface(label, item)


def _reject_unsafe_public_fragment(label: str, value: str) -> None:
    normalized = value.lower()
    if any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError(f"unsafe public value in {label}")


__all__ = (
    "DEFAULT_RESEARCH_MARKET_OUTLIER_DETECTOR_CONFIG_VERSION",
    "ResearchMarketOutlierDetectorConfig",
    "ResearchMarketOutlierDetectorInputRow",
    "ResearchMarketOutlierDetectorReasonCodeCount",
    "ResearchMarketOutlierDetectorReport",
    "ResearchMarketOutlierDetectorRow",
    "build_research_market_outlier_detector",
    "research_market_outlier_detector_payload",
)
