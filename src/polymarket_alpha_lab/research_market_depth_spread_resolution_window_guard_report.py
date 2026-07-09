"""Report-only market depth, spread, and resolution window guard."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal, localcontext
from hashlib import sha256
import json
import re
from typing import Any


__all__ = (
    "MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_STATUSES",
    "DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_REPORT_CONFIG_VERSION",
    "ResearchMarketDepthSpreadResolutionWindowGuardConfig",
    "ResearchMarketDepthSpreadResolutionWindowGuardInput",
    "ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount",
    "ResearchMarketDepthSpreadResolutionWindowGuardReport",
    "ResearchMarketDepthSpreadResolutionWindowGuardRow",
    "build_research_market_depth_spread_resolution_window_guard_report",
    "research_market_depth_spread_resolution_window_guard_report_digest",
    "research_market_depth_spread_resolution_window_guard_report_payload",
)


DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_REPORT_CONFIG_VERSION = (
    "research-market-depth-spread-resolution-window-guard-report-v0"
)
MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_STATUSES = ("pass", "watch", "block")
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_.-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z0-9][a-z0-9_]{0,127}$")
HEX_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")


def _join_parts(*parts: str) -> str:
    return "".join(parts)


UNSAFE_PUBLIC_FRAGMENTS = (
    _join_parts("ra", "w"),
    _join_parts("can", "didate", "_", "id"),
    _join_parts("condition", "_", "id"),
    _join_parts("ma", "rket", "_", "id"),
    _join_parts("ma", "rket", "_", "sl", "ug"),
    _join_parts("ques", "tion"),
    _join_parts("sour", "ce", "_", "ur", "l"),
    _join_parts("sour", "ce", "_", "tex", "t"),
    _join_parts("d", "sn"),
    _join_parts("tab", "le", "_", "name"),
    _join_parts("to", "ken"),
    _join_parts("wal", "let"),
    _join_parts("or", "der"),
    _join_parts("tra", "de"),
    _join_parts("li", "ve"),
    _join_parts("reco", "mmend"),
    _join_parts("siz", "ing"),
    _join_parts("bu", "y"),
    _join_parts("se", "ll"),
    _join_parts("ap", "i", "_", "key"),
    _join_parts("priv", "ate", "_", "key"),
    _join_parts("au", "th"),
    "://",
    "?",
    "@",
    "=",
)
COMPONENT_REASON_PRIORITY = (
    "guard_available_depth_block",
    "guard_spread_width_block",
    "guard_resolution_window_block",
    "guard_available_depth_watch",
    "guard_spread_width_watch",
    "guard_resolution_window_watch",
)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadResolutionWindowGuardConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_REPORT_CONFIG_VERSION
    )
    minimum_pass_available_depth: Decimal = Decimal("1000.000000")
    minimum_watch_available_depth: Decimal = Decimal("250.000000")
    maximum_pass_spread_width_ratio: Decimal = Decimal("0.030000")
    maximum_watch_spread_width_ratio: Decimal = Decimal("0.080000")
    minimum_pass_resolution_window_hours: Decimal = Decimal("48.000000")
    minimum_watch_resolution_window_hours: Decimal = Decimal("12.000000")
    minimum_pass_guard_score: Decimal = Decimal("0.750000")
    minimum_watch_guard_score: Decimal = Decimal("0.450000")
    available_depth_weight: Decimal = Decimal("0.350000")
    spread_width_weight: Decimal = Decimal("0.350000")
    resolution_window_weight: Decimal = Decimal("0.300000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthSpreadResolutionWindowGuardConfig,
            "config",
        )
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must match supported value")
        for field_name in (
            "minimum_pass_available_depth",
            "minimum_watch_available_depth",
            "minimum_pass_resolution_window_hours",
            "minimum_watch_resolution_window_hours",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "maximum_pass_spread_width_ratio",
            "maximum_watch_spread_width_ratio",
            "minimum_pass_guard_score",
            "minimum_watch_guard_score",
            "available_depth_weight",
            "spread_width_weight",
            "resolution_window_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.minimum_pass_available_depth < self.minimum_watch_available_depth:
            raise ValueError("minimum_pass_available_depth must be at least watch")
        if self.maximum_pass_spread_width_ratio > self.maximum_watch_spread_width_ratio:
            raise ValueError("maximum_pass_spread_width_ratio must not exceed watch")
        if (
            self.minimum_pass_resolution_window_hours
            < self.minimum_watch_resolution_window_hours
        ):
            raise ValueError("minimum_pass_resolution_window_hours must be at least watch")
        if self.minimum_pass_guard_score < self.minimum_watch_guard_score:
            raise ValueError("minimum_pass_guard_score must be at least watch")
        if _weight_sum(self) != ONE:
            raise ValueError("weights must sum to 1.000000")
        _require_hard_flags("config", self)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadResolutionWindowGuardInput:
    private_signal_ref: str
    observed_at: datetime
    available_depth: Decimal
    spread_width_ratio: Decimal
    resolution_window_hours: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthSpreadResolutionWindowGuardInput, "input")
        _require_private_ref("private_signal_ref", self.private_signal_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "available_depth",
            _require_nonnegative_decimal("available_depth", self.available_depth),
        )
        object.__setattr__(
            self,
            "spread_width_ratio",
            _require_ratio_decimal("spread_width_ratio", self.spread_width_ratio),
        )
        object.__setattr__(
            self,
            "resolution_window_hours",
            _require_nonnegative_decimal(
                "resolution_window_hours",
                self.resolution_window_hours,
            ),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("input", self)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadResolutionWindowGuardRow:
    public_row_ref: str
    observed_at: datetime
    available_depth: Decimal
    available_depth_score: Decimal
    spread_width_ratio: Decimal
    spread_width_score: Decimal
    resolution_window_hours: Decimal
    resolution_window_score: Decimal
    available_depth_weight: Decimal
    spread_width_weight: Decimal
    resolution_window_weight: Decimal
    guard_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthSpreadResolutionWindowGuardRow, "row")
        _require_public_label("public_row_ref", self.public_row_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in ("available_depth", "resolution_window_hours"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "available_depth_score",
            "spread_width_ratio",
            "spread_width_score",
            "resolution_window_score",
            "available_depth_weight",
            "spread_width_weight",
            "resolution_window_weight",
            "guard_score",
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
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("row", self)
        _validate_row_consistency(self)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(self, "count", _require_positive_whole_decimal("count", self.count))
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)


@dataclass(frozen=True)
class ResearchMarketDepthSpreadResolutionWindowGuardReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    row_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    thin_depth_count: Decimal
    wide_spread_count: Decimal
    narrow_resolution_window_count: Decimal
    average_guard_score: Decimal | None
    min_available_depth: Decimal
    max_spread_width_ratio: Decimal
    min_resolution_window_hours: Decimal
    status: str
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...]
    reason_code_counts: tuple[
        ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketDepthSpreadResolutionWindowGuardReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in (
            "input_count",
            "row_count",
            "pass_count",
            "watch_count",
            "block_count",
            "thin_depth_count",
            "wide_spread_count",
            "narrow_resolution_window_count",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_guard_score",
            _require_optional_ratio_decimal("average_guard_score", self.average_guard_score),
        )
        object.__setattr__(
            self,
            "min_available_depth",
            _require_nonnegative_decimal("min_available_depth", self.min_available_depth),
        )
        object.__setattr__(
            self,
            "max_spread_width_ratio",
            _require_ratio_decimal("max_spread_width_ratio", self.max_spread_width_ratio),
        )
        object.__setattr__(
            self,
            "min_resolution_window_hours",
            _require_nonnegative_decimal(
                "min_resolution_window_hours",
                self.min_resolution_window_hours,
            ),
        )
        _require_status("status", self.status)
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        object.__setattr__(
            self,
            "reason_code_counts",
            _normalize_reason_code_counts(self.reason_code_counts),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=False),
        )
        _require_hard_flags("report", self)
        _validate_report_consistency(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_depth_spread_resolution_window_guard_report(
    inputs: Iterable[object],
    *,
    config: ResearchMarketDepthSpreadResolutionWindowGuardConfig,
    generated_at: datetime,
) -> ResearchMarketDepthSpreadResolutionWindowGuardReport:
    if type(config) is not ResearchMarketDepthSpreadResolutionWindowGuardConfig:
        raise ValueError(
            "config must be a ResearchMarketDepthSpreadResolutionWindowGuardConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    input_items = _normalize_inputs(inputs)
    for item in input_items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(
        _row_from_input(
            item,
            public_row_ref=f"depth_spread_window_group_{index:03d}",
            config=config,
        )
        for index, item in enumerate(
            sorted(input_items, key=lambda value: value.private_signal_ref),
            start=1,
        )
    )
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketDepthSpreadResolutionWindowGuardReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(input_items)),
        row_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        thin_depth_count=_decimal_count(_reason_count(rows, "guard_available_depth")),
        wide_spread_count=_decimal_count(_reason_count(rows, "guard_spread_width")),
        narrow_resolution_window_count=_decimal_count(
            _reason_count(rows, "guard_resolution_window"),
        ),
        average_guard_score=_average_guard_score(rows),
        min_available_depth=_minimum_row_value(rows, "available_depth"),
        max_spread_width_ratio=_maximum_row_value(rows, "spread_width_ratio"),
        min_resolution_window_hours=_minimum_row_value(rows, "resolution_window_hours"),
        status=_summary_status(reason_codes),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_depth_spread_resolution_window_guard_report_payload(
    report: ResearchMarketDepthSpreadResolutionWindowGuardReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketDepthSpreadResolutionWindowGuardReport:
        raise ValueError(
            "report must be a ResearchMarketDepthSpreadResolutionWindowGuardReport",
        )
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    _require_hard_flags("payload", _DictFlags(payload))
    _reject_unsafe_public_payload(payload)
    return payload


def research_market_depth_spread_resolution_window_guard_report_digest(
    report: ResearchMarketDepthSpreadResolutionWindowGuardReport,
) -> str:
    if type(report) is not ResearchMarketDepthSpreadResolutionWindowGuardReport:
        raise ValueError(
            "report must be a ResearchMarketDepthSpreadResolutionWindowGuardReport",
        )
    _require_hard_flags("report", report)
    expected_digest = _derived_report_digest(report)
    if report.derived_validation_digest != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    return expected_digest


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
    item: ResearchMarketDepthSpreadResolutionWindowGuardInput,
    *,
    public_row_ref: str,
    config: ResearchMarketDepthSpreadResolutionWindowGuardConfig,
) -> ResearchMarketDepthSpreadResolutionWindowGuardRow:
    available_depth_score = _positive_score(
        item.available_depth,
        config.minimum_pass_available_depth,
    )
    spread_width_score = _inverse_score(
        item.spread_width_ratio,
        config.maximum_watch_spread_width_ratio,
    )
    resolution_window_score = _positive_score(
        item.resolution_window_hours,
        config.minimum_pass_resolution_window_hours,
    )
    guard_score = _guard_score(
        available_depth_score=available_depth_score,
        spread_width_score=spread_width_score,
        resolution_window_score=resolution_window_score,
        config=config,
    )
    status = _row_status(
        available_depth=item.available_depth,
        spread_width_ratio=item.spread_width_ratio,
        resolution_window_hours=item.resolution_window_hours,
        guard_score=guard_score,
        config=config,
    )
    return ResearchMarketDepthSpreadResolutionWindowGuardRow(
        public_row_ref=public_row_ref,
        observed_at=item.observed_at,
        available_depth=item.available_depth,
        available_depth_score=available_depth_score,
        spread_width_ratio=item.spread_width_ratio,
        spread_width_score=spread_width_score,
        resolution_window_hours=item.resolution_window_hours,
        resolution_window_score=resolution_window_score,
        available_depth_weight=config.available_depth_weight,
        spread_width_weight=config.spread_width_weight,
        resolution_window_weight=config.resolution_window_weight,
        guard_score=guard_score,
        status=status,
        reason_codes=_row_reason_codes(item, status=status, config=config),
    )


def _positive_score(value: Decimal, pass_threshold: Decimal) -> Decimal:
    if pass_threshold <= ZERO:
        raise ValueError("pass_threshold must be positive")
    with localcontext() as context:
        context.prec = 28
        score = value / pass_threshold
    if score > ONE:
        return ONE
    if score < ZERO:
        return ZERO
    return _quantize(score)


def _inverse_score(value: Decimal, zero_at: Decimal) -> Decimal:
    if zero_at <= ZERO:
        raise ValueError("zero_at must be positive")
    with localcontext() as context:
        context.prec = 28
        score = ONE - (value / zero_at)
    if score > ONE:
        return ONE
    if score < ZERO:
        return ZERO
    return _quantize(score)


def _guard_score(
    *,
    available_depth_score: Decimal,
    spread_width_score: Decimal,
    resolution_window_score: Decimal,
    config: ResearchMarketDepthSpreadResolutionWindowGuardConfig,
) -> Decimal:
    return _quantize(
        available_depth_score * config.available_depth_weight
        + spread_width_score * config.spread_width_weight
        + resolution_window_score * config.resolution_window_weight,
    )


def _row_status(
    *,
    available_depth: Decimal,
    spread_width_ratio: Decimal,
    resolution_window_hours: Decimal,
    guard_score: Decimal,
    config: ResearchMarketDepthSpreadResolutionWindowGuardConfig,
) -> str:
    if (
        available_depth < config.minimum_watch_available_depth
        or spread_width_ratio > config.maximum_watch_spread_width_ratio
        or resolution_window_hours < config.minimum_watch_resolution_window_hours
        or guard_score < config.minimum_watch_guard_score
    ):
        return "block"
    if (
        available_depth < config.minimum_pass_available_depth
        or spread_width_ratio > config.maximum_pass_spread_width_ratio
        or resolution_window_hours < config.minimum_pass_resolution_window_hours
        or guard_score < config.minimum_pass_guard_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    item: ResearchMarketDepthSpreadResolutionWindowGuardInput,
    *,
    status: str,
    config: ResearchMarketDepthSpreadResolutionWindowGuardConfig,
) -> tuple[str, ...]:
    codes = {
        f"guard_status_{status}",
        _low_value_reason(
            prefix="guard_available_depth",
            value=item.available_depth,
            pass_threshold=config.minimum_pass_available_depth,
            block_threshold=config.minimum_watch_available_depth,
        ),
        _high_value_reason(
            prefix="guard_spread_width",
            value=item.spread_width_ratio,
            pass_threshold=config.maximum_pass_spread_width_ratio,
            block_threshold=config.maximum_watch_spread_width_ratio,
        ),
        _low_value_reason(
            prefix="guard_resolution_window",
            value=item.resolution_window_hours,
            pass_threshold=config.minimum_pass_resolution_window_hours,
            block_threshold=config.minimum_watch_resolution_window_hours,
        ),
    }
    for code in item.reason_codes:
        codes.add(f"input_{code}")
    return tuple(sorted(codes))


def _low_value_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value < block_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _high_value_reason(
    *,
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    block_threshold: Decimal,
) -> str:
    if value > block_threshold:
        return f"{prefix}_block"
    if value > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _normalize_inputs(
    inputs: Iterable[object],
) -> tuple[ResearchMarketDepthSpreadResolutionWindowGuardInput, ...]:
    if isinstance(inputs, (str, bytes)):
        raise ValueError("inputs must be an iterable")
    try:
        values = tuple(inputs)
    except TypeError as exc:
        raise ValueError("inputs must be an iterable") from exc
    seen: set[str] = set()
    for value in values:
        if type(value) is not ResearchMarketDepthSpreadResolutionWindowGuardInput:
            raise ValueError(
                "inputs must contain ResearchMarketDepthSpreadResolutionWindowGuardInput",
            )
        _require_hard_flags("input", value)
        if value.private_signal_ref in seen:
            raise ValueError("private_signal_ref values must be unique")
        seen.add(value.private_signal_ref)
    return values


def _summary_reason_codes(
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("guard_no_inputs",)
    if all(row.status == "pass" for row in rows):
        return ("guard_pass",)
    codes: list[str] = []
    if any(row.status == "block" for row in rows):
        codes.append("guard_block")
    elif any(row.status == "watch" for row in rows):
        codes.append("guard_watch")
    row_codes = {code for row in rows for code in row.reason_codes}
    for code in COMPONENT_REASON_PRIORITY:
        if code in row_codes:
            codes.append(code)
    return tuple(codes)


def _summary_status(reason_codes: tuple[str, ...]) -> str:
    if reason_codes == ("guard_no_inputs",):
        return "block"
    if "guard_block" in reason_codes:
        return "block"
    if "guard_watch" in reason_codes:
        return "watch"
    return "pass"


def _reason_code_counts(
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(row.reason_codes)
    row_count = Decimal(len(rows))
    return tuple(
        ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(count),
            row_ratio=_quantize(Decimal(count) / row_count),
        )
        for reason_code, count in sorted(counter.items(), key=lambda item: item[0])
    )


def _average_guard_score(
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.guard_score for row in rows), ZERO) / Decimal(len(rows)))


def _maximum_row_value(
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return max(getattr(row, field_name) for row in rows)


def _minimum_row_value(
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...],
    field_name: str,
) -> Decimal:
    if not rows:
        return ZERO
    return min(getattr(row, field_name) for row in rows)


def _status_count(
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _reason_count(
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...],
    prefix: str,
) -> int:
    return sum(
        1
        for row in rows
        if f"{prefix}_watch" in row.reason_codes or f"{prefix}_block" in row.reason_codes
    )


def _validate_row_consistency(
    row: ResearchMarketDepthSpreadResolutionWindowGuardRow,
) -> None:
    if f"guard_status_{row.status}" not in row.reason_codes:
        raise ValueError("reason_codes must include row status")
    weight_sum = _quantize(
        row.available_depth_weight + row.spread_width_weight + row.resolution_window_weight,
    )
    if weight_sum != ONE:
        raise ValueError("weights must sum to 1.000000")
    expected_score = _quantize(
        row.available_depth_score * row.available_depth_weight
        + row.spread_width_score * row.spread_width_weight
        + row.resolution_window_score * row.resolution_window_weight,
    )
    if row.guard_score != expected_score:
        raise ValueError("guard_score must match component scores")


def _validate_report_consistency(
    report: ResearchMarketDepthSpreadResolutionWindowGuardReport,
) -> None:
    if report.rows != tuple(sorted(report.rows, key=lambda row: row.public_row_ref)):
        raise ValueError("rows must be sorted by public_row_ref")
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.row_count != _decimal_count(len(report.rows)):
        raise ValueError("row_count must match rows")
    if report.pass_count != _decimal_count(_status_count(report.rows, "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(_status_count(report.rows, "watch")):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(_status_count(report.rows, "block")):
        raise ValueError("block_count must match rows")
    if report.thin_depth_count != _decimal_count(
        _reason_count(report.rows, "guard_available_depth"),
    ):
        raise ValueError("thin_depth_count must match rows")
    if report.wide_spread_count != _decimal_count(
        _reason_count(report.rows, "guard_spread_width"),
    ):
        raise ValueError("wide_spread_count must match rows")
    if report.narrow_resolution_window_count != _decimal_count(
        _reason_count(report.rows, "guard_resolution_window"),
    ):
        raise ValueError("narrow_resolution_window_count must match rows")
    if report.average_guard_score != _average_guard_score(report.rows):
        raise ValueError("average_guard_score must match rows")
    if report.min_available_depth != _minimum_row_value(report.rows, "available_depth"):
        raise ValueError("min_available_depth must match rows")
    if report.max_spread_width_ratio != _maximum_row_value(report.rows, "spread_width_ratio"):
        raise ValueError("max_spread_width_ratio must match rows")
    if report.min_resolution_window_hours != _minimum_row_value(
        report.rows,
        "resolution_window_hours",
    ):
        raise ValueError("min_resolution_window_hours must match rows")
    expected_reasons = _summary_reason_codes(report.rows)
    if report.reason_codes != expected_reasons:
        raise ValueError("reason_codes must match rows")
    if report.status != _summary_status(expected_reasons):
        raise ValueError("status must match rows")
    if report.reason_code_counts != _reason_code_counts(report.rows, report.reason_codes):
        raise ValueError("reason_code_counts must match rows")


def _normalize_rows(
    rows: tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...],
) -> tuple[ResearchMarketDepthSpreadResolutionWindowGuardRow, ...]:
    if type(rows) is not tuple:
        raise ValueError("rows must be a tuple")
    seen: set[str] = set()
    for row in rows:
        if type(row) is not ResearchMarketDepthSpreadResolutionWindowGuardRow:
            raise ValueError("rows must contain ResearchMarketDepthSpreadResolutionWindowGuardRow")
        _require_hard_flags("row", row)
        if row.public_row_ref in seen:
            raise ValueError("public_row_ref values must be unique")
        seen.add(row.public_row_ref)
    return rows


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount, ...],
) -> tuple[ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount, ...]:
    if type(counts) is not tuple:
        raise ValueError("reason_code_counts must be a tuple")
    for count in counts:
        if type(count) is not ResearchMarketDepthSpreadResolutionWindowGuardReasonCodeCount:
            raise ValueError("reason_code_counts must contain reason count values")
        _require_hard_flags("reason_code_count", count)
    sorted_counts = tuple(sorted(counts, key=lambda item: item.reason_code))
    if counts != sorted_counts:
        raise ValueError("reason_code_counts must be sorted by reason_code")
    return counts


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be a {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"{label} paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"{label} report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"{label} readonly must be True")


def _require_status(name: str, value: object) -> str:
    if (
        type(value) is not str
        or value not in MARKET_DEPTH_SPREAD_RESOLUTION_WINDOW_GUARD_STATUSES
    ):
        raise ValueError(f"{name} must be pass, watch, or block")
    return value


def _require_public_label(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a public label")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _require_private_ref(name: str, value: object) -> str:
    if type(value) is not str or not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{name} must be a private ref")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{name} has unsafe private text")
    return value


def _require_reason_code(name: str, value: object) -> str:
    if type(value) is not str or not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{name} must be a reason code")
    if _contains_unsafe_public_text(value):
        raise ValueError(f"{name} has unsafe public text")
    return value


def _normalize_reason_codes(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(values) is not tuple:
        raise ValueError(f"{name} must be a tuple")
    normalized = tuple(dict.fromkeys(_require_reason_code(name, value) for value in values))
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    return normalized


def _require_decimal(name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{name} must be finite")
    return value


def _require_positive_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    quantized_value = _quantize(decimal_value)
    if quantized_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    return quantized_value


def _require_nonnegative_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    return _quantize(decimal_value)


def _require_ratio_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO or decimal_value > ONE:
        raise ValueError(f"{name} must be between 0 and 1")
    return _quantize(decimal_value)


def _require_optional_ratio_decimal(name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(name, value)


def _require_nonnegative_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value < ZERO:
        raise ValueError(f"{name} must be nonnegative")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return _quantize(decimal_value)


def _require_positive_whole_decimal(name: str, value: object) -> Decimal:
    decimal_value = _require_decimal(name, value)
    if decimal_value <= ZERO:
        raise ValueError(f"{name} must be positive")
    if decimal_value != decimal_value.to_integral_value():
        raise ValueError(f"{name} must be a whole Decimal")
    return _quantize(decimal_value)


def _require_hex_digest(name: str, value: object) -> str:
    if type(value) is not str or not HEX_DIGEST_RE.fullmatch(value):
        raise ValueError(f"{name} must be a SHA-256 hex digest")
    return value


def _as_utc(name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{name} must be exactly datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must be timezone-aware")
    return value.astimezone(UTC)


def _weight_sum(config: ResearchMarketDepthSpreadResolutionWindowGuardConfig) -> Decimal:
    return _quantize(
        config.available_depth_weight
        + config.spread_width_weight
        + config.resolution_window_weight,
    )


def _decimal_count(value: int) -> Decimal:
    return Decimal(value).quantize(QUANTUM)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM)


def _contains_unsafe_public_text(value: str) -> bool:
    lowered = value.lower()
    return any(fragment in lowered for fragment in UNSAFE_PUBLIC_FRAGMENTS)


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        return _payload_value(asdict(value))
    if isinstance(value, Decimal):
        if type(value) is not Decimal or not value.is_finite():
            raise ValueError("payload Decimal must be finite")
        return str(_quantize(value))
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("payload datetime must be exactly datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("payload datetime must be timezone-aware")
        return value.astimezone(UTC).isoformat()
    if isinstance(value, float):
        raise ValueError("payload value must not be a float")
    if type(value) is int:
        raise ValueError("payload numeric value must use Decimal")
    if type(value) is str:
        if _contains_unsafe_public_text(value):
            raise ValueError("payload has unsafe public text")
        return value
    if type(value) is bool:
        return value
    if isinstance(value, dict):
        ready: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _contains_unsafe_public_text(key):
                raise ValueError("payload has unsafe public field")
            ready[key] = _payload_value(item)
        return ready
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _derived_report_digest(
    report: ResearchMarketDepthSpreadResolutionWindowGuardReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return sha256(encoded.encode("utf-8")).hexdigest()


def _reject_unsafe_public_payload(value: object) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("payload keys must be strings")
            if _contains_unsafe_public_text(key):
                raise ValueError("payload has unsafe public field")
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _contains_unsafe_public_text(value):
        raise ValueError("payload has unsafe public text")
