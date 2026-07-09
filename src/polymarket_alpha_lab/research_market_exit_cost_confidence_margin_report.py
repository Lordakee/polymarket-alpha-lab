"""Pure report-only exit cost confidence margin report."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Context, Decimal, ROUND_HALF_EVEN, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "MARKET_EXIT_COST_CONFIDENCE_MARGIN_STATUSES",
    "DEFAULT_RESEARCH_MARKET_EXIT_COST_CONFIDENCE_MARGIN_REPORT_CONFIG_VERSION",
    "ResearchMarketExitCostConfidenceMarginConfig",
    "ResearchMarketExitCostConfidenceMarginObservation",
    "ResearchMarketExitCostConfidenceMarginReasonCodeCount",
    "ResearchMarketExitCostConfidenceMarginReport",
    "ResearchMarketExitCostConfidenceMarginRow",
    "build_research_market_exit_cost_confidence_margin_report",
    "research_market_exit_cost_confidence_margin_report_digest",
    "research_market_exit_cost_confidence_margin_report_payload",
)


DEFAULT_RESEARCH_MARKET_EXIT_COST_CONFIDENCE_MARGIN_REPORT_CONFIG_VERSION = (
    "research-market-exit-cost-confidence-margin-report-v0"
)

MARKET_EXIT_COST_CONFIDENCE_MARGIN_STATUSES = ("pass", "watch", "block")
STATUS_PASS = "pass"
STATUS_WATCH = "watch"
STATUS_BLOCK = "block"
MISSING_INPUTS_REASON = "missing_exit_cost_confidence_margin_observations"
QUANTUM = Decimal("0.000001")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
THREE = Decimal("3.000000")
DECIMAL_CONTEXT = Context(prec=64, rounding=ROUND_HALF_EVEN)
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
PRIVATE_REF_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,512}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
PHASE_FLAG_FIELDS = ("paper_only", "report_only", "readonly")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "-", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ma", "rket", "-", "sl", "ug"),
    _join_parts("sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "url"),
    _join_parts("sour", "ce", "_", "text"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("au", "th"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    "://",
)


class _FinalDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalDataclass and issubclass(base, _FinalDataclass):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketExitCostConfidenceMarginConfig(_FinalDataclass):
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_EXIT_COST_CONFIDENCE_MARGIN_REPORT_CONFIG_VERSION
    )
    pass_min_confidence_score: Decimal = Decimal("0.750000")
    watch_min_confidence_score: Decimal = Decimal("0.550000")
    pass_max_exit_cost_rate: Decimal = Decimal("0.030000")
    block_max_exit_cost_rate: Decimal = Decimal("0.080000")
    pass_min_confidence_margin: Decimal = Decimal("0.720000")
    block_min_confidence_margin: Decimal = Decimal("0.500000")
    liquidity_buffer_weight: Decimal = Decimal("0.050000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitCostConfidenceMarginConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EXIT_COST_CONFIDENCE_MARGIN_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "pass_min_confidence_score",
            "watch_min_confidence_score",
            "pass_max_exit_cost_rate",
            "block_max_exit_cost_rate",
            "pass_min_confidence_margin",
            "block_min_confidence_margin",
            "liquidity_buffer_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        if self.watch_min_confidence_score <= ZERO:
            raise ValueError("watch_min_confidence_score must be positive")
        _require_at_least(
            "pass_min_confidence_score",
            self.pass_min_confidence_score,
            self.watch_min_confidence_score,
        )
        if self.pass_max_exit_cost_rate <= ZERO:
            raise ValueError("pass_max_exit_cost_rate must be positive")
        if self.block_max_exit_cost_rate <= self.pass_max_exit_cost_rate:
            raise ValueError(
                "block_max_exit_cost_rate must exceed pass_max_exit_cost_rate",
            )
        _require_at_least(
            "pass_min_confidence_margin",
            self.pass_min_confidence_margin,
            self.block_min_confidence_margin,
        )
        if self.block_min_confidence_margin <= ZERO:
            raise ValueError("block_min_confidence_margin must be positive")
        if self.liquidity_buffer_weight <= ZERO:
            raise ValueError("liquidity_buffer_weight must be positive")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketExitCostConfidenceMarginObservation(_FinalDataclass):
    internal_research_ref: str
    observed_at: datetime
    exit_fee_rate: Decimal
    exit_spread_rate: Decimal
    exit_slippage_rate: Decimal
    liquidity_confidence_score: Decimal
    evidence_confidence_score: Decimal
    resolution_confidence_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExitCostConfidenceMarginObservation,
            "observation",
        )
        _require_private_reference("internal_research_ref", self.internal_research_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "exit_fee_rate",
            "exit_spread_rate",
            "exit_slippage_rate",
            "liquidity_confidence_score",
            "evidence_confidence_score",
            "resolution_confidence_score",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_probability_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("observation", self)


@dataclass(frozen=True)
class ResearchMarketExitCostConfidenceMarginRow(_FinalDataclass):
    public_row_ref: str
    internal_research_ref_digest: str
    observed_at: datetime
    exit_fee_rate: Decimal
    exit_spread_rate: Decimal
    exit_slippage_rate: Decimal
    liquidity_confidence_score: Decimal
    evidence_confidence_score: Decimal
    resolution_confidence_score: Decimal
    liquidity_buffer_rate: Decimal
    total_exit_cost_rate: Decimal
    confidence_score: Decimal
    confidence_margin: Decimal
    status: str
    reason_codes: tuple[str, ...]
    row_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitCostConfidenceMarginRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        _require_hex_digest(
            "internal_research_ref_digest",
            self.internal_research_ref_digest,
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "exit_fee_rate",
            "exit_spread_rate",
            "exit_slippage_rate",
            "liquidity_confidence_score",
            "evidence_confidence_score",
            "resolution_confidence_score",
            "liquidity_buffer_rate",
            "total_exit_cost_rate",
            "confidence_score",
            "confidence_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "exit_fee_rate",
            "exit_spread_rate",
            "exit_slippage_rate",
            "liquidity_confidence_score",
            "evidence_confidence_score",
            "resolution_confidence_score",
            "liquidity_buffer_rate",
            "total_exit_cost_rate",
            "confidence_score",
        ):
            _require_probability_decimal(field_name, getattr(self, field_name))
        _require_status("status", self.status)
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("row", self)
        _validate_row(self)
        expected_digest = _row_validation_digest(self)
        if self.row_validation_digest:
            _require_hex_digest("row_validation_digest", self.row_validation_digest)
            if self.row_validation_digest != expected_digest:
                raise ValueError("row_validation_digest must match row fields")
        else:
            object.__setattr__(self, "row_validation_digest", expected_digest)


@dataclass(frozen=True)
class ResearchMarketExitCostConfidenceMarginReasonCodeCount(_FinalDataclass):
    reason_code: str
    count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketExitCostConfidenceMarginReasonCodeCount,
            "reason_code_count",
        )
        object.__setattr__(self, "reason_code", _normalize_reason_code(self.reason_code))
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketExitCostConfidenceMarginReport(_FinalDataclass):
    generated_at: datetime
    config_version: str
    observation_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    max_exit_cost_rate: Decimal
    min_confidence_margin: Decimal
    average_exit_cost_rate: Decimal | None
    average_confidence_score: Decimal | None
    average_confidence_margin: Decimal | None
    status: str
    rows: tuple[ResearchMarketExitCostConfidenceMarginRow, ...]
    reason_code_counts: tuple[ResearchMarketExitCostConfidenceMarginReasonCodeCount, ...]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketExitCostConfidenceMarginReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_EXIT_COST_CONFIDENCE_MARGIN_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "observation_count",
            "pass_count",
            "watch_count",
            "block_count",
            "max_exit_cost_rate",
            "min_confidence_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "average_exit_cost_rate",
            "average_confidence_score",
            "average_confidence_margin",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_optional_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(self, "reason_codes", _normalize_reason_codes(self.reason_codes))
        _require_hard_flags("report", self)
        _validate_report(self)
        expected_digest = _report_validation_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_exit_cost_confidence_margin_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketExitCostConfidenceMarginConfig,
    generated_at: datetime,
) -> ResearchMarketExitCostConfidenceMarginReport:
    if type(config) is not ResearchMarketExitCostConfidenceMarginConfig:
        raise ValueError("config must be a ResearchMarketExitCostConfidenceMarginConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    rows_without_refs = tuple(_row_from_observation(item, config=config) for item in items)
    sorted_rows = tuple(
        sorted(
            rows_without_refs,
            key=lambda row: (
                _status_sort_value(row.status),
                row.confidence_margin,
                -row.total_exit_cost_rate,
                row.internal_research_ref_digest,
                row.observed_at.isoformat(),
            ),
        ),
    )
    rows = tuple(
        _replace_row_ref(row, public_row_ref=f"exit_cost_confidence_margin_row_{index:03d}")
        for index, row in enumerate(sorted_rows, start=1)
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketExitCostConfidenceMarginReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        observation_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, STATUS_PASS)),
        watch_count=_decimal_count(_status_count(rows, STATUS_WATCH)),
        block_count=_decimal_count(_status_count(rows, STATUS_BLOCK)),
        max_exit_cost_rate=_maximum_row_value(rows, "total_exit_cost_rate"),
        min_confidence_margin=_minimum_row_value(rows, "confidence_margin"),
        average_exit_cost_rate=_average_row_value(rows, "total_exit_cost_rate"),
        average_confidence_score=_average_row_value(rows, "confidence_score"),
        average_confidence_margin=_average_row_value(rows, "confidence_margin"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_exit_cost_confidence_margin_report_payload(
    report: ResearchMarketExitCostConfidenceMarginReport | Mapping[str, object],
) -> dict[str, Any]:
    if type(report) is ResearchMarketExitCostConfidenceMarginReport:
        _require_hard_flags("report", report)
        expected_digest = _report_validation_digest(report)
        if report.derived_validation_digest != expected_digest:
            raise ValueError("derived_validation_digest must match report fields")
        payload = _report_payload(report)
        _validate_public_payload(payload)
        return payload
    if type(report) is dict:
        _validate_public_payload(report)
        return dict(report)
    raise ValueError(
        "report must be a ResearchMarketExitCostConfidenceMarginReport or payload dict",
    )


def research_market_exit_cost_confidence_margin_report_digest(
    report: ResearchMarketExitCostConfidenceMarginReport,
) -> str:
    if type(report) is not ResearchMarketExitCostConfidenceMarginReport:
        raise ValueError("report must be a ResearchMarketExitCostConfidenceMarginReport")
    _require_hard_flags("report", report)
    expected_digest = _report_validation_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


def _row_from_observation(
    observation: ResearchMarketExitCostConfidenceMarginObservation,
    *,
    config: ResearchMarketExitCostConfidenceMarginConfig,
) -> ResearchMarketExitCostConfidenceMarginRow:
    liquidity_buffer_rate = _quantize(
        (ONE - observation.liquidity_confidence_score) * config.liquidity_buffer_weight,
    )
    total_exit_cost_rate = _quantize(
        observation.exit_fee_rate
        + observation.exit_spread_rate
        + observation.exit_slippage_rate
        + liquidity_buffer_rate,
    )
    confidence_score = _ratio(
        observation.liquidity_confidence_score
        + observation.evidence_confidence_score
        + observation.resolution_confidence_score,
        THREE,
    )
    confidence_margin = _quantize(confidence_score - total_exit_cost_rate)
    status = _row_status(
        total_exit_cost_rate=total_exit_cost_rate,
        confidence_score=confidence_score,
        confidence_margin=confidence_margin,
        config=config,
    )
    return ResearchMarketExitCostConfidenceMarginRow(
        public_row_ref="exit_cost_confidence_margin_row_pending",
        internal_research_ref_digest=_private_reference_digest(
            observation.internal_research_ref,
        ),
        observed_at=observation.observed_at,
        exit_fee_rate=observation.exit_fee_rate,
        exit_spread_rate=observation.exit_spread_rate,
        exit_slippage_rate=observation.exit_slippage_rate,
        liquidity_confidence_score=observation.liquidity_confidence_score,
        evidence_confidence_score=observation.evidence_confidence_score,
        resolution_confidence_score=observation.resolution_confidence_score,
        liquidity_buffer_rate=liquidity_buffer_rate,
        total_exit_cost_rate=total_exit_cost_rate,
        confidence_score=confidence_score,
        confidence_margin=confidence_margin,
        status=status,
        reason_codes=_row_reason_codes(
            total_exit_cost_rate=total_exit_cost_rate,
            confidence_score=confidence_score,
            confidence_margin=confidence_margin,
            liquidity_buffer_rate=liquidity_buffer_rate,
            input_reason_codes=observation.reason_codes,
            config=config,
        ),
    )


def _replace_row_ref(
    row: ResearchMarketExitCostConfidenceMarginRow,
    *,
    public_row_ref: str,
) -> ResearchMarketExitCostConfidenceMarginRow:
    return ResearchMarketExitCostConfidenceMarginRow(
        public_row_ref=public_row_ref,
        internal_research_ref_digest=row.internal_research_ref_digest,
        observed_at=row.observed_at,
        exit_fee_rate=row.exit_fee_rate,
        exit_spread_rate=row.exit_spread_rate,
        exit_slippage_rate=row.exit_slippage_rate,
        liquidity_confidence_score=row.liquidity_confidence_score,
        evidence_confidence_score=row.evidence_confidence_score,
        resolution_confidence_score=row.resolution_confidence_score,
        liquidity_buffer_rate=row.liquidity_buffer_rate,
        total_exit_cost_rate=row.total_exit_cost_rate,
        confidence_score=row.confidence_score,
        confidence_margin=row.confidence_margin,
        status=row.status,
        reason_codes=row.reason_codes,
    )


def _row_status(
    *,
    total_exit_cost_rate: Decimal,
    confidence_score: Decimal,
    confidence_margin: Decimal,
    config: ResearchMarketExitCostConfidenceMarginConfig,
) -> str:
    if (
        confidence_score >= config.pass_min_confidence_score
        and total_exit_cost_rate <= config.pass_max_exit_cost_rate
        and confidence_margin >= config.pass_min_confidence_margin
    ):
        return STATUS_PASS
    if (
        confidence_score < config.watch_min_confidence_score
        or total_exit_cost_rate >= config.block_max_exit_cost_rate
        or confidence_margin <= config.block_min_confidence_margin
    ):
        return STATUS_BLOCK
    return STATUS_WATCH


def _row_reason_codes(
    *,
    total_exit_cost_rate: Decimal,
    confidence_score: Decimal,
    confidence_margin: Decimal,
    liquidity_buffer_rate: Decimal,
    input_reason_codes: tuple[str, ...],
    config: ResearchMarketExitCostConfidenceMarginConfig,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if confidence_margin >= config.pass_min_confidence_margin:
        reasons.append("confidence_margin_pass")
    elif confidence_margin <= config.block_min_confidence_margin:
        reasons.append("confidence_margin_block")
    else:
        reasons.append("confidence_margin_watch")
    if confidence_score >= config.pass_min_confidence_score:
        reasons.append("confidence_score_high")
    elif confidence_score >= config.watch_min_confidence_score:
        reasons.append("confidence_score_watch_band")
    else:
        reasons.append("confidence_score_below_watch_band")
    if total_exit_cost_rate <= config.pass_max_exit_cost_rate:
        reasons.append("exit_cost_within_pass_band")
    elif total_exit_cost_rate >= config.block_max_exit_cost_rate:
        reasons.append("exit_cost_above_block_band")
    else:
        reasons.append("exit_cost_watch_band")
    if liquidity_buffer_rate > ZERO:
        reasons.append("liquidity_buffer_applied")
    for reason_code in input_reason_codes:
        reasons.append(f"input_{reason_code}")
    return tuple(sorted(set(reasons)))


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketExitCostConfidenceMarginObservation, ...]:
    if isinstance(observations, (str, bytes)):
        raise ValueError("observations must be an iterable of observation records")
    normalized: list[ResearchMarketExitCostConfidenceMarginObservation] = []
    seen_refs: set[str] = set()
    for item in observations:
        if type(item) is not ResearchMarketExitCostConfidenceMarginObservation:
            raise ValueError(
                "observations must contain "
                "ResearchMarketExitCostConfidenceMarginObservation",
            )
        _require_hard_flags("observation", item)
        if item.internal_research_ref in seen_refs:
            raise ValueError("internal_research_ref values must be unique")
        seen_refs.add(item.internal_research_ref)
        normalized.append(item)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchMarketExitCostConfidenceMarginRow, ...],
) -> tuple[ResearchMarketExitCostConfidenceMarginRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketExitCostConfidenceMarginRow:
            raise ValueError(
                "rows must contain ResearchMarketExitCostConfidenceMarginRow values",
            )
        _require_hard_flags("row", row)
    expected_refs = tuple(
        f"exit_cost_confidence_margin_row_{index:03d}"
        for index in range(1, len(rows) + 1)
    )
    actual_refs = tuple(row.public_row_ref for row in rows)
    if rows and actual_refs != expected_refs:
        raise ValueError("rows must use sequential public_row_ref values")
    return rows


def _normalize_reason_code_counts(
    rows: tuple[ResearchMarketExitCostConfidenceMarginReasonCodeCount, ...],
) -> tuple[ResearchMarketExitCostConfidenceMarginReasonCodeCount, ...]:
    if type(rows) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for row in rows:
        if type(row) is not ResearchMarketExitCostConfidenceMarginReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketExitCostConfidenceMarginReasonCodeCount values",
            )
        _require_hard_flags("reason_code_count", row)
    sorted_rows = tuple(sorted(rows, key=lambda row: row.reason_code))
    if rows != sorted_rows:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return rows


def _reason_code_counts(
    rows: tuple[ResearchMarketExitCostConfidenceMarginRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketExitCostConfidenceMarginReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketExitCostConfidenceMarginReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
            ),
        )
    counts: Counter[str] = Counter()
    for row in rows:
        counts.update(row.reason_codes)
    return tuple(
        ResearchMarketExitCostConfidenceMarginReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
        )
        for reason_code, count in sorted(counts.items(), key=lambda item: item[0])
    )


def _summary_reason_codes(
    rows: tuple[ResearchMarketExitCostConfidenceMarginRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return (MISSING_INPUTS_REASON,)
    if all(row.status == STATUS_PASS for row in rows):
        return ("confidence_margin_pass",)
    return tuple(sorted({reason for row in rows for reason in row.reason_codes}))


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == (MISSING_INPUTS_REASON,):
        return STATUS_BLOCK
    if any(
        reason_code.endswith("_block") or "_block_" in reason_code
        for reason_code in reason_codes
    ):
        return STATUS_BLOCK
    if any(reason_code.endswith("_watch") or "_watch_" in reason_code for reason_code in reason_codes):
        return STATUS_WATCH
    return STATUS_PASS


def _status_count(
    rows: tuple[ResearchMarketExitCostConfidenceMarginRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _status_sort_value(status: str) -> int:
    if status == STATUS_BLOCK:
        return 0
    if status == STATUS_WATCH:
        return 1
    return 2


def _maximum_row_value(
    rows: tuple[ResearchMarketExitCostConfidenceMarginRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketExitCostConfidenceMarginRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _average_row_value(
    rows: tuple[ResearchMarketExitCostConfidenceMarginRow, ...],
    field_name: str,
) -> Decimal | None:
    if not rows:
        return None
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(sum((getattr(row, field_name) for row in rows), ZERO) / len(rows))


def _validate_row(row: ResearchMarketExitCostConfidenceMarginRow) -> None:
    expected_total = _quantize(
        row.exit_fee_rate
        + row.exit_spread_rate
        + row.exit_slippage_rate
        + row.liquidity_buffer_rate,
    )
    if row.total_exit_cost_rate != expected_total:
        raise ValueError("total_exit_cost_rate must match cost fields")
    expected_confidence = _ratio(
        row.liquidity_confidence_score
        + row.evidence_confidence_score
        + row.resolution_confidence_score,
        THREE,
    )
    if row.confidence_score != expected_confidence:
        raise ValueError("confidence_score must match confidence fields")
    if row.confidence_margin != _quantize(row.confidence_score - row.total_exit_cost_rate):
        raise ValueError("confidence_margin must match confidence less cost")


def _validate_report(report: ResearchMarketExitCostConfidenceMarginReport) -> None:
    if report.observation_count != _decimal_count(len(report.rows)):
        raise ValueError("observation_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, STATUS_PASS)):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, STATUS_WATCH)):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, STATUS_BLOCK)):
        raise ValueError("block_count must match rows")
    if report.max_exit_cost_rate != _maximum_row_value(report.rows, "total_exit_cost_rate"):
        raise ValueError("max_exit_cost_rate must match rows")
    if report.min_confidence_margin != _minimum_row_value(report.rows, "confidence_margin"):
        raise ValueError("min_confidence_margin must match rows")
    if report.average_exit_cost_rate != _average_row_value(report.rows, "total_exit_cost_rate"):
        raise ValueError("average_exit_cost_rate must match rows")
    if report.average_confidence_score != _average_row_value(report.rows, "confidence_score"):
        raise ValueError("average_confidence_score must match rows")
    if report.average_confidence_margin != _average_row_value(report.rows, "confidence_margin"):
        raise ValueError("average_confidence_margin must match rows")
    if report.reason_codes != _summary_reason_codes(report.rows):
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(report.reason_codes):
        raise ValueError("status must match reason_codes")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _row_validation_digest(row: ResearchMarketExitCostConfidenceMarginRow) -> str:
    values = _row_payload(row, include_digest=False)
    return _payload_digest(values)


def _report_validation_digest(report: ResearchMarketExitCostConfidenceMarginReport) -> str:
    values = _report_payload(report, include_digest=False)
    return _payload_digest(values)


def _private_reference_digest(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _payload_digest(payload: Mapping[str, Any]) -> str:
    _reject_unsafe_public_payload(payload)
    encoded = json.dumps(
        payload,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _report_payload(
    report: ResearchMarketExitCostConfidenceMarginReport,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "observation_count": _decimal_string(report.observation_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "max_exit_cost_rate": _decimal_string(report.max_exit_cost_rate),
        "min_confidence_margin": _decimal_string(report.min_confidence_margin),
        "average_exit_cost_rate": _optional_decimal_string(report.average_exit_cost_rate),
        "average_confidence_score": _optional_decimal_string(
            report.average_confidence_score,
        ),
        "average_confidence_margin": _optional_decimal_string(
            report.average_confidence_margin,
        ),
        "status": report.status,
        "rows": [_row_payload(row) for row in report.rows],
        "reason_code_counts": [
            _reason_code_count_payload(row) for row in report.reason_code_counts
        ],
        "reason_codes": list(report.reason_codes),
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }
    if include_digest:
        payload["derived_validation_digest"] = report.derived_validation_digest
    return payload


def _row_payload(
    row: ResearchMarketExitCostConfidenceMarginRow,
    *,
    include_digest: bool = True,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "public_row_ref": row.public_row_ref,
        "internal_research_ref_digest": row.internal_research_ref_digest,
        "observed_at": row.observed_at.isoformat(),
        "exit_fee_rate": _decimal_string(row.exit_fee_rate),
        "exit_spread_rate": _decimal_string(row.exit_spread_rate),
        "exit_slippage_rate": _decimal_string(row.exit_slippage_rate),
        "liquidity_confidence_score": _decimal_string(row.liquidity_confidence_score),
        "evidence_confidence_score": _decimal_string(row.evidence_confidence_score),
        "resolution_confidence_score": _decimal_string(row.resolution_confidence_score),
        "liquidity_buffer_rate": _decimal_string(row.liquidity_buffer_rate),
        "total_exit_cost_rate": _decimal_string(row.total_exit_cost_rate),
        "confidence_score": _decimal_string(row.confidence_score),
        "confidence_margin": _decimal_string(row.confidence_margin),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }
    if include_digest:
        payload["row_validation_digest"] = row.row_validation_digest
    return payload


def _reason_code_count_payload(
    row: ResearchMarketExitCostConfidenceMarginReasonCodeCount,
) -> dict[str, Any]:
    return {
        "reason_code": row.reason_code,
        "count": _decimal_string(row.count),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _validate_public_payload(payload: Mapping[str, object]) -> None:
    if type(payload) is not dict:
        raise ValueError("report payload must be a dict")
    _reject_unsafe_public_payload(payload)
    _require_no_public_numeric_literals(payload)
    _require_public_payload_hard_flags(payload)
    _require_public_payload_statuses(payload)
    digest = payload.get("derived_validation_digest")
    if type(digest) is not str or not HEX_DIGEST_RE.fullmatch(digest):
        raise ValueError("derived_validation_digest must be a sha256 hex digest")
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    if _payload_digest(digest_payload) != digest:
        raise ValueError("derived_validation_digest must match report fields")


def _require_public_payload_hard_flags(value: object) -> None:
    if isinstance(value, Mapping):
        for field_name in PHASE_FLAG_FIELDS:
            if field_name in value and value[field_name] is not True:
                raise ValueError(f"{field_name} must be True")
        for item in value.values():
            _require_public_payload_hard_flags(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_hard_flags(item)


def _require_public_payload_statuses(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key == "status":
                _require_status("status", item)
            _require_public_payload_statuses(item)
        return
    if isinstance(value, list):
        for item in value:
            _require_public_payload_statuses(item)


def _require_no_public_numeric_literals(value: object) -> None:
    if type(value) in (int, float, Decimal):
        raise ValueError("public numeric values must be Decimal-derived strings")
    if isinstance(value, Mapping):
        for item in value.values():
            _require_no_public_numeric_literals(item)
    elif isinstance(value, list):
        for item in value:
            _require_no_public_numeric_literals(item)


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _reject_unsafe_public_text(str(key))
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, str):
        _reject_unsafe_public_text(value)


def _reject_unsafe_public_text(value: str) -> None:
    lowered = value.lower()
    if any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS):
        raise ValueError("unsafe public payload surface")


def _as_utc(field_name: str, value: datetime) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    return value


def _require_private_reference(field_name: str, value: object) -> str:
    if type(value) is not str or not PRIVATE_REF_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a non-empty private reference")
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
        raise ValueError(f"{field_name} must be no greater than 1.000000")
    return normalized


def _require_optional_nonnegative_decimal(
    field_name: str,
    value: object,
) -> Decimal | None:
    if value is None:
        return None
    return _require_nonnegative_decimal(field_name, value)


def _require_below(field_name: str, value: Decimal, higher_value: Decimal) -> None:
    if value >= higher_value:
        raise ValueError(f"{field_name} must be below paired threshold")


def _require_at_least(field_name: str, value: Decimal, lower_value: Decimal) -> None:
    if value < lower_value:
        raise ValueError(f"{field_name} must be at least paired threshold")


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in MARKET_EXIT_COST_CONFIDENCE_MARGIN_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str or not HEX_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a sha256 hex digest")
    return value


def _require_hard_flags(label: str, value: object) -> None:
    for field_name in PHASE_FLAG_FIELDS:
        if getattr(value, field_name, None) is not True:
            raise ValueError(f"{label} {field_name} must be True")


def _normalize_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    if type(reason_codes) is not tuple:
        raise ValueError("reason_codes must be a tuple")
    return tuple(sorted({_normalize_reason_code(reason_code) for reason_code in reason_codes}))


def _normalize_reason_code(reason_code: object) -> str:
    if type(reason_code) is not str or not REASON_CODE_RE.fullmatch(reason_code):
        raise ValueError("reason_code must be a lowercase reason code")
    return reason_code


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    with localcontext(DECIMAL_CONTEXT):
        return _quantize(numerator / denominator)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _decimal_string(value: Decimal) -> str:
    return str(_quantize(value))


def _optional_decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return _decimal_string(value)
