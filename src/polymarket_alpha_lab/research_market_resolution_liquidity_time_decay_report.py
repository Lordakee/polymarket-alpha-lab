"""Report-only resolution-window liquidity time-decay reducer."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from hashlib import sha256
import json
import re
from typing import Any


RESOLUTION_LIQUIDITY_TIME_DECAY_STATUSES = ("pass", "watch", "block")
DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_TIME_DECAY_REPORT_CONFIG_VERSION = (
    "research-market-resolution-liquidity-time-decay-report-v0"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
QUANTUM = Decimal("0.000001")
PUBLIC_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")
REASON_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,127}$")
UNSAFE_PUBLIC_FRAGMENTS = (
    "raw",
    "candidate_id",
    "condition_id",
    "market_id",
    "market-id",
    "market_slug",
    "market-slug",
    "slug",
    "question",
    "source_url",
    "source-url",
    "url",
    "source_text",
    "source-text",
    "dsn",
    "table",
    "token",
    "wal" "let",
    "au" "th",
    "private",
    "secret",
    "credential",
    "or" "der",
    "tra" "de",
    "live",
    "position",
    "siz" "ing",
    "recommendation",
    "buy",
    "sell",
    "submit",
    "cancel",
    "://",
    "?",
)


__all__ = (
    "RESOLUTION_LIQUIDITY_TIME_DECAY_STATUSES",
    "DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_TIME_DECAY_REPORT_CONFIG_VERSION",
    "ResearchMarketResolutionLiquidityTimeDecayConfig",
    "ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount",
    "ResearchMarketResolutionLiquidityTimeDecayReport",
    "ResearchMarketResolutionLiquidityTimeDecayRow",
    "ResearchMarketResolutionLiquidityTimeDecaySnapshot",
    "build_research_market_resolution_liquidity_time_decay_report",
    "research_market_resolution_liquidity_time_decay_report_digest",
    "research_market_resolution_liquidity_time_decay_report_payload",
)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityTimeDecayConfig:
    config_version: str = (
        DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_TIME_DECAY_REPORT_CONFIG_VERSION
    )
    max_pass_book_age_seconds: Decimal = Decimal("300.000000")
    max_watch_book_age_seconds: Decimal = Decimal("1200.000000")
    min_pass_resolution_window_seconds: Decimal = Decimal("3600.000000")
    min_watch_resolution_window_seconds: Decimal = Decimal("900.000000")
    min_pass_depth_retention_ratio: Decimal = Decimal("0.850000")
    min_watch_depth_retention_ratio: Decimal = Decimal("0.500000")
    max_pass_depth_decay_ratio: Decimal = Decimal("0.150000")
    max_watch_depth_decay_ratio: Decimal = Decimal("0.500000")
    max_pass_spread_widening_ratio: Decimal = Decimal("0.020000")
    max_watch_spread_widening_ratio: Decimal = Decimal("0.120000")
    max_pass_time_decay_pressure: Decimal = Decimal("0.200000")
    max_watch_time_decay_pressure: Decimal = Decimal("0.600000")
    min_pass_liquidity_half_life_seconds: Decimal = Decimal("7200.000000")
    min_watch_liquidity_half_life_seconds: Decimal = Decimal("1800.000000")
    pass_decay_score: Decimal = Decimal("0.750000")
    watch_decay_score: Decimal = Decimal("0.450000")
    depth_retention_weight: Decimal = Decimal("0.250000")
    depth_decay_weight: Decimal = Decimal("0.200000")
    spread_widening_weight: Decimal = Decimal("0.150000")
    book_age_weight: Decimal = Decimal("0.100000")
    resolution_window_weight: Decimal = Decimal("0.100000")
    time_decay_pressure_weight: Decimal = Decimal("0.100000")
    liquidity_half_life_weight: Decimal = Decimal("0.100000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityTimeDecayConfig does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionLiquidityTimeDecayConfig, "config")
        _require_public_label("config_version", self.config_version)
        if (
            self.config_version
            != DEFAULT_RESEARCH_MARKET_RESOLUTION_LIQUIDITY_TIME_DECAY_REPORT_CONFIG_VERSION
        ):
            raise ValueError("config_version must be the supported config version")
        for field_name in (
            "max_pass_book_age_seconds",
            "max_watch_book_age_seconds",
            "min_pass_resolution_window_seconds",
            "min_watch_resolution_window_seconds",
            "min_pass_liquidity_half_life_seconds",
            "min_watch_liquidity_half_life_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_positive_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "min_pass_depth_retention_ratio",
            "min_watch_depth_retention_ratio",
            "max_pass_depth_decay_ratio",
            "max_watch_depth_decay_ratio",
            "max_pass_spread_widening_ratio",
            "max_watch_spread_widening_ratio",
            "max_pass_time_decay_pressure",
            "max_watch_time_decay_pressure",
            "pass_decay_score",
            "watch_decay_score",
            "depth_retention_weight",
            "depth_decay_weight",
            "spread_widening_weight",
            "book_age_weight",
            "resolution_window_weight",
            "time_decay_pressure_weight",
            "liquidity_half_life_weight",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        _require_less_than(
            "max_pass_book_age_seconds",
            self.max_pass_book_age_seconds,
            "max_watch_book_age_seconds",
            self.max_watch_book_age_seconds,
        )
        _require_less_than(
            "min_watch_resolution_window_seconds",
            self.min_watch_resolution_window_seconds,
            "min_pass_resolution_window_seconds",
            self.min_pass_resolution_window_seconds,
        )
        _require_less_than(
            "min_watch_depth_retention_ratio",
            self.min_watch_depth_retention_ratio,
            "min_pass_depth_retention_ratio",
            self.min_pass_depth_retention_ratio,
        )
        _require_less_than(
            "max_pass_depth_decay_ratio",
            self.max_pass_depth_decay_ratio,
            "max_watch_depth_decay_ratio",
            self.max_watch_depth_decay_ratio,
        )
        _require_less_than(
            "max_pass_spread_widening_ratio",
            self.max_pass_spread_widening_ratio,
            "max_watch_spread_widening_ratio",
            self.max_watch_spread_widening_ratio,
        )
        _require_less_than(
            "max_pass_time_decay_pressure",
            self.max_pass_time_decay_pressure,
            "max_watch_time_decay_pressure",
            self.max_watch_time_decay_pressure,
        )
        _require_less_than(
            "min_watch_liquidity_half_life_seconds",
            self.min_watch_liquidity_half_life_seconds,
            "min_pass_liquidity_half_life_seconds",
            self.min_pass_liquidity_half_life_seconds,
        )
        _require_less_than(
            "watch_decay_score",
            self.watch_decay_score,
            "pass_decay_score",
            self.pass_decay_score,
        )
        weight_sum = _quantize(
            self.depth_retention_weight
            + self.depth_decay_weight
            + self.spread_widening_weight
            + self.book_age_weight
            + self.resolution_window_weight
            + self.time_decay_pressure_weight
            + self.liquidity_half_life_weight,
        )
        if weight_sum != ONE:
            raise ValueError("decay score weights must sum to 1")
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityTimeDecaySnapshot:
    liquidity_snapshot_key: str
    observed_at: datetime
    resolution_window_seconds: Decimal
    baseline_depth: Decimal
    current_depth: Decimal
    baseline_spread_ratio: Decimal
    current_spread_ratio: Decimal
    liquidity_half_life_seconds: Decimal
    time_decay_pressure: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityTimeDecaySnapshot does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionLiquidityTimeDecaySnapshot,
            "snapshot",
        )
        _require_public_label("liquidity_snapshot_key", self.liquidity_snapshot_key)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        object.__setattr__(
            self,
            "resolution_window_seconds",
            _require_positive_decimal(
                "resolution_window_seconds",
                self.resolution_window_seconds,
            ),
        )
        object.__setattr__(
            self,
            "baseline_depth",
            _require_positive_decimal("baseline_depth", self.baseline_depth),
        )
        object.__setattr__(
            self,
            "current_depth",
            _require_nonnegative_decimal("current_depth", self.current_depth),
        )
        if self.current_depth > self.baseline_depth:
            raise ValueError("current_depth must not exceed baseline_depth")
        for field_name in ("baseline_spread_ratio", "current_spread_ratio"):
            object.__setattr__(
                self,
                field_name,
                _require_ratio_decimal(field_name, getattr(self, field_name)),
            )
        if self.current_spread_ratio < self.baseline_spread_ratio:
            raise ValueError("current_spread_ratio must not be below baseline_spread_ratio")
        object.__setattr__(
            self,
            "liquidity_half_life_seconds",
            _require_positive_decimal(
                "liquidity_half_life_seconds",
                self.liquidity_half_life_seconds,
            ),
        )
        object.__setattr__(
            self,
            "time_decay_pressure",
            _require_ratio_decimal("time_decay_pressure", self.time_decay_pressure),
        )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes("reason_codes", self.reason_codes, allow_empty=True),
        )
        _require_hard_flags("snapshot", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityTimeDecayRow:
    public_decay_ref: str
    observed_at: datetime
    resolution_window_seconds: Decimal
    book_age_seconds: Decimal
    baseline_depth: Decimal
    current_depth: Decimal
    depth_retention_ratio: Decimal
    depth_decay_ratio: Decimal
    baseline_spread_ratio: Decimal
    current_spread_ratio: Decimal
    spread_widening_ratio: Decimal
    liquidity_half_life_seconds: Decimal
    time_decay_pressure: Decimal
    depth_retention_score: Decimal
    depth_decay_score: Decimal
    spread_widening_score: Decimal
    book_age_score: Decimal
    resolution_window_score: Decimal
    time_decay_pressure_score: Decimal
    liquidity_half_life_score: Decimal
    decay_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityTimeDecayRow does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionLiquidityTimeDecayRow, "row")
        _require_public_label("public_decay_ref", self.public_decay_ref)
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for field_name in (
            "resolution_window_seconds",
            "book_age_seconds",
            "baseline_depth",
            "current_depth",
            "spread_widening_ratio",
            "liquidity_half_life_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
            )
        for field_name in (
            "depth_retention_ratio",
            "depth_decay_ratio",
            "baseline_spread_ratio",
            "current_spread_ratio",
            "time_decay_pressure",
            "depth_retention_score",
            "depth_decay_score",
            "spread_widening_score",
            "book_age_score",
            "resolution_window_score",
            "time_decay_pressure_score",
            "liquidity_half_life_score",
            "decay_score",
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
        _reject_unsafe_public_payload(self)
        _validate_row(self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount:
    reason_code: str
    count: Decimal
    row_ratio: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount does not "
            "support subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount,
            "reason_code_count",
        )
        _require_reason_code("reason_code", self.reason_code)
        object.__setattr__(
            self,
            "count",
            _require_positive_decimal("count", self.count),
        )
        object.__setattr__(
            self,
            "row_ratio",
            _require_ratio_decimal("row_ratio", self.row_ratio),
        )
        _require_hard_flags("reason_code_count", self)
        _reject_unsafe_public_payload(self)


@dataclass(frozen=True)
class ResearchMarketResolutionLiquidityTimeDecayReport:
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_decay_score: Decimal | None
    min_depth_retention_ratio: Decimal
    max_depth_decay_ratio: Decimal
    max_spread_widening_ratio: Decimal
    max_book_age_seconds: Decimal
    min_resolution_window_seconds: Decimal
    max_time_decay_pressure: Decimal
    min_liquidity_half_life_seconds: Decimal
    status: str
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...]
    reason_code_counts: tuple[
        ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount,
        ...
    ]
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        raise TypeError(
            "ResearchMarketResolutionLiquidityTimeDecayReport does not support "
            "subclassing",
        )

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketResolutionLiquidityTimeDecayReport, "report")
        object.__setattr__(self, "generated_at", _as_utc("generated_at", self.generated_at))
        _require_public_label("config_version", self.config_version)
        for field_name in ("input_count", "pass_count", "watch_count", "block_count"):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_whole_decimal(field_name, getattr(self, field_name)),
            )
        object.__setattr__(
            self,
            "average_decay_score",
            _require_optional_ratio_decimal("average_decay_score", self.average_decay_score),
        )
        for field_name in (
            "min_depth_retention_ratio",
            "max_depth_decay_ratio",
            "max_spread_widening_ratio",
            "max_book_age_seconds",
            "min_resolution_window_seconds",
            "max_time_decay_pressure",
            "min_liquidity_half_life_seconds",
        ):
            object.__setattr__(
                self,
                field_name,
                _require_nonnegative_decimal(field_name, getattr(self, field_name)),
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
        _reject_unsafe_public_payload(self)
        _validate_report(self)
        expected_digest = _derived_report_digest(self)
        if self.derived_validation_digest:
            _require_hex_digest("derived_validation_digest", self.derived_validation_digest)
            if self.derived_validation_digest != expected_digest:
                raise ValueError("derived_validation_digest must match report fields")
        else:
            object.__setattr__(self, "derived_validation_digest", expected_digest)


def build_research_market_resolution_liquidity_time_decay_report(
    snapshots: Iterable[ResearchMarketResolutionLiquidityTimeDecaySnapshot],
    *,
    config: ResearchMarketResolutionLiquidityTimeDecayConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionLiquidityTimeDecayReport:
    if type(config) is not ResearchMarketResolutionLiquidityTimeDecayConfig:
        raise ValueError(
            "config must be a ResearchMarketResolutionLiquidityTimeDecayConfig",
        )
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    normalized = _normalize_snapshots(snapshots)
    for item in normalized:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    draft_rows = tuple(
        _row_from_snapshot(
            public_decay_ref=f"resolution_liquidity_decay_group_{index:03d}",
            snapshot=item,
            config=config,
            generated_at=generated_at_utc,
        )
        for index, item in enumerate(normalized, start=1)
    )
    rows = _renumber_public_decay_refs(tuple(sorted(draft_rows, key=_public_row_sort_key)))
    reason_codes = _summary_reason_codes(rows)
    return ResearchMarketResolutionLiquidityTimeDecayReport(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        input_count=_decimal_count(len(rows)),
        pass_count=_decimal_count(_status_count(rows, "pass")),
        watch_count=_decimal_count(_status_count(rows, "watch")),
        block_count=_decimal_count(_status_count(rows, "block")),
        average_decay_score=_average_decay_score(rows),
        min_depth_retention_ratio=_minimum_row_value(rows, "depth_retention_ratio"),
        max_depth_decay_ratio=_maximum_row_value(rows, "depth_decay_ratio"),
        max_spread_widening_ratio=_maximum_row_value(rows, "spread_widening_ratio"),
        max_book_age_seconds=_maximum_row_value(rows, "book_age_seconds"),
        min_resolution_window_seconds=_minimum_row_value(
            rows,
            "resolution_window_seconds",
        ),
        max_time_decay_pressure=_maximum_row_value(rows, "time_decay_pressure"),
        min_liquidity_half_life_seconds=_minimum_row_value(
            rows,
            "liquidity_half_life_seconds",
        ),
        status=_summary_status(rows),
        rows=rows,
        reason_code_counts=_reason_code_counts(rows, reason_codes),
        reason_codes=reason_codes,
    )


def research_market_resolution_liquidity_time_decay_report_payload(
    report: ResearchMarketResolutionLiquidityTimeDecayReport,
) -> dict[str, Any]:
    if type(report) is not ResearchMarketResolutionLiquidityTimeDecayReport:
        raise ValueError("report must be a ResearchMarketResolutionLiquidityTimeDecayReport")
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


def research_market_resolution_liquidity_time_decay_report_digest(
    report: ResearchMarketResolutionLiquidityTimeDecayReport,
) -> str:
    if type(report) is not ResearchMarketResolutionLiquidityTimeDecayReport:
        raise ValueError("report must be a ResearchMarketResolutionLiquidityTimeDecayReport")
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


def _row_from_snapshot(
    *,
    public_decay_ref: str,
    snapshot: ResearchMarketResolutionLiquidityTimeDecaySnapshot,
    config: ResearchMarketResolutionLiquidityTimeDecayConfig,
    generated_at: datetime,
) -> ResearchMarketResolutionLiquidityTimeDecayRow:
    book_age_seconds = _age_seconds(generated_at, snapshot.observed_at)
    depth_retention_ratio = _safe_ratio(snapshot.current_depth, snapshot.baseline_depth)
    depth_decay_ratio = _quantize(ONE - depth_retention_ratio)
    spread_widening_ratio = _quantize(
        snapshot.current_spread_ratio - snapshot.baseline_spread_ratio,
    )
    depth_retention_score = _forward_ratio_score(
        depth_retention_ratio,
        config.min_pass_depth_retention_ratio,
    )
    depth_decay_score = _inverse_ratio_score(
        depth_decay_ratio,
        config.max_watch_depth_decay_ratio,
    )
    spread_widening_score = _inverse_ratio_score(
        spread_widening_ratio,
        config.max_watch_spread_widening_ratio,
    )
    book_age_score = _inverse_ratio_score(
        book_age_seconds,
        config.max_watch_book_age_seconds,
    )
    resolution_window_score = _forward_ratio_score(
        snapshot.resolution_window_seconds,
        config.min_pass_resolution_window_seconds,
    )
    time_decay_pressure_score = _inverse_ratio_score(
        snapshot.time_decay_pressure,
        config.max_watch_time_decay_pressure,
    )
    liquidity_half_life_score = _forward_ratio_score(
        snapshot.liquidity_half_life_seconds,
        config.min_pass_liquidity_half_life_seconds,
    )
    decay_score = _decay_score(
        depth_retention_score=depth_retention_score,
        depth_decay_score=depth_decay_score,
        spread_widening_score=spread_widening_score,
        book_age_score=book_age_score,
        resolution_window_score=resolution_window_score,
        time_decay_pressure_score=time_decay_pressure_score,
        liquidity_half_life_score=liquidity_half_life_score,
        config=config,
    )
    status = _row_status(
        book_age_seconds=book_age_seconds,
        resolution_window_seconds=snapshot.resolution_window_seconds,
        depth_retention_ratio=depth_retention_ratio,
        depth_decay_ratio=depth_decay_ratio,
        spread_widening_ratio=spread_widening_ratio,
        time_decay_pressure=snapshot.time_decay_pressure,
        liquidity_half_life_seconds=snapshot.liquidity_half_life_seconds,
        decay_score=decay_score,
        config=config,
    )
    return ResearchMarketResolutionLiquidityTimeDecayRow(
        public_decay_ref=public_decay_ref,
        observed_at=snapshot.observed_at,
        resolution_window_seconds=snapshot.resolution_window_seconds,
        book_age_seconds=book_age_seconds,
        baseline_depth=snapshot.baseline_depth,
        current_depth=snapshot.current_depth,
        depth_retention_ratio=depth_retention_ratio,
        depth_decay_ratio=depth_decay_ratio,
        baseline_spread_ratio=snapshot.baseline_spread_ratio,
        current_spread_ratio=snapshot.current_spread_ratio,
        spread_widening_ratio=spread_widening_ratio,
        liquidity_half_life_seconds=snapshot.liquidity_half_life_seconds,
        time_decay_pressure=snapshot.time_decay_pressure,
        depth_retention_score=depth_retention_score,
        depth_decay_score=depth_decay_score,
        spread_widening_score=spread_widening_score,
        book_age_score=book_age_score,
        resolution_window_score=resolution_window_score,
        time_decay_pressure_score=time_decay_pressure_score,
        liquidity_half_life_score=liquidity_half_life_score,
        decay_score=decay_score,
        status=status,
        reason_codes=_row_reason_codes(
            snapshot=snapshot,
            book_age_seconds=book_age_seconds,
            resolution_window_seconds=snapshot.resolution_window_seconds,
            depth_retention_ratio=depth_retention_ratio,
            depth_decay_ratio=depth_decay_ratio,
            spread_widening_ratio=spread_widening_ratio,
            time_decay_pressure=snapshot.time_decay_pressure,
            liquidity_half_life_seconds=snapshot.liquidity_half_life_seconds,
            decay_score=decay_score,
            config=config,
        ),
    )


def _decay_score(
    *,
    depth_retention_score: Decimal,
    depth_decay_score: Decimal,
    spread_widening_score: Decimal,
    book_age_score: Decimal,
    resolution_window_score: Decimal,
    time_decay_pressure_score: Decimal,
    liquidity_half_life_score: Decimal,
    config: ResearchMarketResolutionLiquidityTimeDecayConfig,
) -> Decimal:
    return _quantize(
        depth_retention_score * config.depth_retention_weight
        + depth_decay_score * config.depth_decay_weight
        + spread_widening_score * config.spread_widening_weight
        + book_age_score * config.book_age_weight
        + resolution_window_score * config.resolution_window_weight
        + time_decay_pressure_score * config.time_decay_pressure_weight
        + liquidity_half_life_score * config.liquidity_half_life_weight,
    )


def _row_status(
    *,
    book_age_seconds: Decimal,
    resolution_window_seconds: Decimal,
    depth_retention_ratio: Decimal,
    depth_decay_ratio: Decimal,
    spread_widening_ratio: Decimal,
    time_decay_pressure: Decimal,
    liquidity_half_life_seconds: Decimal,
    decay_score: Decimal,
    config: ResearchMarketResolutionLiquidityTimeDecayConfig,
) -> str:
    if (
        book_age_seconds > config.max_watch_book_age_seconds
        or resolution_window_seconds < config.min_watch_resolution_window_seconds
        or depth_retention_ratio < config.min_watch_depth_retention_ratio
        or depth_decay_ratio > config.max_watch_depth_decay_ratio
        or spread_widening_ratio > config.max_watch_spread_widening_ratio
        or time_decay_pressure > config.max_watch_time_decay_pressure
        or liquidity_half_life_seconds < config.min_watch_liquidity_half_life_seconds
        or decay_score < config.watch_decay_score
    ):
        return "block"
    if (
        book_age_seconds > config.max_pass_book_age_seconds
        or resolution_window_seconds < config.min_pass_resolution_window_seconds
        or depth_retention_ratio < config.min_pass_depth_retention_ratio
        or depth_decay_ratio > config.max_pass_depth_decay_ratio
        or spread_widening_ratio > config.max_pass_spread_widening_ratio
        or time_decay_pressure > config.max_pass_time_decay_pressure
        or liquidity_half_life_seconds < config.min_pass_liquidity_half_life_seconds
        or decay_score < config.pass_decay_score
    ):
        return "watch"
    return "pass"


def _row_reason_codes(
    *,
    snapshot: ResearchMarketResolutionLiquidityTimeDecaySnapshot,
    book_age_seconds: Decimal,
    resolution_window_seconds: Decimal,
    depth_retention_ratio: Decimal,
    depth_decay_ratio: Decimal,
    spread_widening_ratio: Decimal,
    time_decay_pressure: Decimal,
    liquidity_half_life_seconds: Decimal,
    decay_score: Decimal,
    config: ResearchMarketResolutionLiquidityTimeDecayConfig,
) -> tuple[str, ...]:
    reason_codes = [
        _upper_bound_reason(
            "book_age",
            book_age_seconds,
            config.max_pass_book_age_seconds,
            config.max_watch_book_age_seconds,
        ),
        _lower_bound_reason(
            "decay_score",
            decay_score,
            config.pass_decay_score,
            config.watch_decay_score,
        ),
        _upper_bound_reason(
            "depth_decay",
            depth_decay_ratio,
            config.max_pass_depth_decay_ratio,
            config.max_watch_depth_decay_ratio,
        ),
        _lower_bound_reason(
            "depth_retention",
            depth_retention_ratio,
            config.min_pass_depth_retention_ratio,
            config.min_watch_depth_retention_ratio,
        ),
        _lower_bound_reason(
            "liquidity_half_life",
            liquidity_half_life_seconds,
            config.min_pass_liquidity_half_life_seconds,
            config.min_watch_liquidity_half_life_seconds,
        ),
        _lower_bound_reason(
            "resolution_window",
            resolution_window_seconds,
            config.min_pass_resolution_window_seconds,
            config.min_watch_resolution_window_seconds,
        ),
        _upper_bound_reason(
            "spread_widening",
            spread_widening_ratio,
            config.max_pass_spread_widening_ratio,
            config.max_watch_spread_widening_ratio,
        ),
        _upper_bound_reason(
            "time_decay_pressure",
            time_decay_pressure,
            config.max_pass_time_decay_pressure,
            config.max_watch_time_decay_pressure,
        ),
    ]
    reason_codes.extend(f"input_{reason_code}" for reason_code in snapshot.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _upper_bound_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value > watch_threshold:
        return f"{prefix}_block"
    if value > pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _lower_bound_reason(
    prefix: str,
    value: Decimal,
    pass_threshold: Decimal,
    watch_threshold: Decimal,
) -> str:
    if value < watch_threshold:
        return f"{prefix}_block"
    if value < pass_threshold:
        return f"{prefix}_watch"
    return f"{prefix}_pass"


def _summary_status(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
) -> str:
    if not rows:
        return "block"
    if any(row.status == "block" for row in rows):
        return "block"
    if any(row.status == "watch" for row in rows):
        return "watch"
    return "pass"


def _summary_reason_codes(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
) -> tuple[str, ...]:
    if not rows:
        return ("no_resolution_liquidity_time_decay_snapshots",)
    reason_codes: list[str] = []
    for row in rows:
        reason_codes.extend(row.reason_codes)
    return _normalize_reason_codes("reason_codes", tuple(reason_codes), allow_empty=False)


def _reason_code_counts(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
    reason_codes: tuple[str, ...],
) -> tuple[ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount, ...]:
    if not rows:
        return (
            ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount(
                reason_code=reason_codes[0],
                count=ONE,
                row_ratio=ZERO,
            ),
        )
    row_count = _decimal_count(len(rows))
    counter = Counter(reason_code for row in rows for reason_code in row.reason_codes)
    return tuple(
        ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount(
            reason_code=reason_code,
            count=_decimal_count(counter[reason_code]),
            row_ratio=_safe_ratio(_decimal_count(counter[reason_code]), row_count),
        )
        for reason_code in reason_codes
    )


def _status_count(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.status == status)


def _average_decay_score(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
) -> Decimal | None:
    if not rows:
        return None
    return _quantize(sum((row.decay_score for row in rows), ZERO) / Decimal(len(rows)))


def _maximum_row_value(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
    field_name: str,
) -> Decimal:
    return max((getattr(row, field_name) for row in rows), default=ZERO)


def _minimum_row_value(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
    field_name: str,
) -> Decimal:
    return min((getattr(row, field_name) for row in rows), default=ZERO)


def _validate_row(row: ResearchMarketResolutionLiquidityTimeDecayRow) -> None:
    if row.current_depth > row.baseline_depth:
        raise ValueError("current_depth must not exceed baseline_depth")
    if row.current_spread_ratio < row.baseline_spread_ratio:
        raise ValueError("current_spread_ratio must not be below baseline_spread_ratio")
    if row.depth_retention_ratio != _safe_ratio(row.current_depth, row.baseline_depth):
        raise ValueError("depth_retention_ratio must match depth fields")
    if row.depth_decay_ratio != _quantize(ONE - row.depth_retention_ratio):
        raise ValueError("depth_decay_ratio must match retention ratio")
    if row.spread_widening_ratio != _quantize(
        row.current_spread_ratio - row.baseline_spread_ratio,
    ):
        raise ValueError("spread_widening_ratio must match spread fields")


def _validate_report(report: ResearchMarketResolutionLiquidityTimeDecayReport) -> None:
    rows = report.rows
    expected_values = {
        "input_count": _decimal_count(len(rows)),
        "pass_count": _decimal_count(_status_count(rows, "pass")),
        "watch_count": _decimal_count(_status_count(rows, "watch")),
        "block_count": _decimal_count(_status_count(rows, "block")),
        "average_decay_score": _average_decay_score(rows),
        "min_depth_retention_ratio": _minimum_row_value(rows, "depth_retention_ratio"),
        "max_depth_decay_ratio": _maximum_row_value(rows, "depth_decay_ratio"),
        "max_spread_widening_ratio": _maximum_row_value(rows, "spread_widening_ratio"),
        "max_book_age_seconds": _maximum_row_value(rows, "book_age_seconds"),
        "min_resolution_window_seconds": _minimum_row_value(
            rows,
            "resolution_window_seconds",
        ),
        "max_time_decay_pressure": _maximum_row_value(rows, "time_decay_pressure"),
        "min_liquidity_half_life_seconds": _minimum_row_value(
            rows,
            "liquidity_half_life_seconds",
        ),
        "status": _summary_status(rows),
        "reason_codes": _summary_reason_codes(rows),
        "reason_code_counts": _reason_code_counts(rows, _summary_reason_codes(rows)),
    }
    for field_name, expected in expected_values.items():
        if getattr(report, field_name) != expected:
            raise ValueError(f"{field_name} must match rows")


def _normalize_snapshots(
    snapshots: Iterable[ResearchMarketResolutionLiquidityTimeDecaySnapshot],
) -> tuple[ResearchMarketResolutionLiquidityTimeDecaySnapshot, ...]:
    if isinstance(snapshots, (str, bytes)) or not isinstance(snapshots, Iterable):
        raise ValueError("snapshots must be an iterable")
    normalized: list[ResearchMarketResolutionLiquidityTimeDecaySnapshot] = []
    for snapshot in snapshots:
        if type(snapshot) is not ResearchMarketResolutionLiquidityTimeDecaySnapshot:
            raise ValueError(
                "snapshots must contain ResearchMarketResolutionLiquidityTimeDecaySnapshot",
            )
        _require_hard_flags("snapshot", snapshot)
        normalized.append(snapshot)
    return tuple(normalized)


def _normalize_rows(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
) -> tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a tuple")
    normalized: list[ResearchMarketResolutionLiquidityTimeDecayRow] = []
    for row in rows:
        if type(row) is not ResearchMarketResolutionLiquidityTimeDecayRow:
            raise ValueError("rows must contain ResearchMarketResolutionLiquidityTimeDecayRow")
        _require_hard_flags("row", row)
        normalized.append(row)
    return tuple(normalized)


def _normalize_reason_code_counts(
    counts: tuple[ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount, ...],
) -> tuple[ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount, ...]:
    if type(counts) not in (list, tuple):
        raise ValueError("reason_code_counts must be a tuple")
    normalized: list[ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount] = []
    for count in counts:
        if type(count) is not ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount:
            raise ValueError(
                "reason_code_counts must contain "
                "ResearchMarketResolutionLiquidityTimeDecayReasonCodeCount",
            )
        _require_hard_flags("reason_code_count", count)
        normalized.append(count)
    return tuple(sorted(normalized, key=lambda item: item.reason_code))


def _renumber_public_decay_refs(
    rows: tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...],
) -> tuple[ResearchMarketResolutionLiquidityTimeDecayRow, ...]:
    return tuple(
        replace(
            row,
            public_decay_ref=f"resolution_liquidity_decay_group_{index:03d}",
        )
        for index, row in enumerate(rows, start=1)
    )


def _public_row_sort_key(
    row: ResearchMarketResolutionLiquidityTimeDecayRow,
) -> tuple[object, ...]:
    return (
        _public_status_sort_rank(row.status),
        row.observed_at,
        row.resolution_window_seconds,
        row.book_age_seconds,
        row.baseline_depth,
        row.current_depth,
        row.depth_retention_ratio,
        row.depth_decay_ratio,
        row.baseline_spread_ratio,
        row.current_spread_ratio,
        row.spread_widening_ratio,
        row.liquidity_half_life_seconds,
        row.time_decay_pressure,
        row.depth_retention_score,
        row.depth_decay_score,
        row.spread_widening_score,
        row.book_age_score,
        row.resolution_window_score,
        row.time_decay_pressure_score,
        row.liquidity_half_life_score,
        row.decay_score,
        row.reason_codes,
    )


def _public_status_sort_rank(status: str) -> int:
    if status == "block":
        return 0
    if status == "pass":
        return 1
    if status == "watch":
        return 2
    raise ValueError("status must be pass, watch, or block")


def _require_exact_type(value: object, expected_type: type[object], label: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{label} must be exactly {expected_type.__name__}")


def _require_hard_flags(label: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError(f"paper_only must be True for {label}")
    if getattr(value, "report_only", None) is not True:
        raise ValueError(f"report_only must be True for {label}")
    if getattr(value, "readonly", None) is not True:
        raise ValueError(f"readonly must be True for {label}")


def _require_public_label(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not PUBLIC_LABEL_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a public label")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _require_reason_code(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if not REASON_CODE_RE.fullmatch(value):
        raise ValueError(f"{field_name} must be a reason code")
    if _has_unsafe_public_fragment(value):
        raise ValueError(f"{field_name} contains unsafe public value")
    return value


def _normalize_reason_codes(
    field_name: str,
    reason_codes: tuple[str, ...],
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if type(reason_codes) not in (list, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    normalized: list[str] = []
    for reason_code in reason_codes:
        _require_reason_code(field_name, reason_code)
        if reason_code not in normalized:
            normalized.append(reason_code)
    if not allow_empty and not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return tuple(sorted(normalized))


def _require_status(field_name: str, value: object) -> str:
    if type(value) is not str or value not in RESOLUTION_LIQUIDITY_TIME_DECAY_STATUSES:
        raise ValueError(f"{field_name} must be pass, watch, or block")
    return value


def _require_less_than(
    lower_field_name: str,
    lower_value: Decimal,
    upper_field_name: str,
    upper_value: Decimal,
) -> None:
    if lower_value >= upper_value:
        raise ValueError(f"{lower_field_name} must be less than {upper_field_name}")


def _require_hex_digest(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{field_name} must be a lowercase sha256 hex digest")
    return value


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be a Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    return _quantize(value)


def _require_positive_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized <= ZERO:
        raise ValueError(f"{field_name} must be positive")
    return normalized


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO:
        raise ValueError(f"{field_name} must be nonnegative")
    return normalized


def _require_nonnegative_whole_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_nonnegative_decimal(field_name, value)
    if normalized != normalized.to_integral_value(rounding=ROUND_HALF_EVEN):
        raise ValueError(f"{field_name} must be a whole Decimal")
    return normalized


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    normalized = _require_decimal(field_name, value)
    if normalized < ZERO or normalized > ONE:
        raise ValueError(f"{field_name} must be between zero and one")
    return normalized


def _require_optional_ratio_decimal(field_name: str, value: object) -> Decimal | None:
    if value is None:
        return None
    return _require_ratio_decimal(field_name, value)


def _decimal_count(value: int) -> Decimal:
    if value < 0:
        raise ValueError("count must be nonnegative")
    return Decimal(value).quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(QUANTUM, rounding=ROUND_HALF_EVEN)


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == ZERO:
        return ZERO
    return _clamp_ratio(numerator / denominator)


def _clamp_ratio(value: Decimal) -> Decimal:
    normalized = _quantize(value)
    if normalized < ZERO:
        return ZERO
    if normalized > ONE:
        return ONE
    return normalized


def _inverse_ratio_score(value: Decimal, watch_threshold: Decimal) -> Decimal:
    if value >= watch_threshold:
        return ZERO
    return _clamp_ratio(ONE - (value / watch_threshold))


def _forward_ratio_score(value: Decimal, pass_threshold: Decimal) -> Decimal:
    if value >= pass_threshold:
        return ONE
    return _clamp_ratio(value / pass_threshold)


def _age_seconds(generated_at: datetime, observed_at: datetime) -> Decimal:
    delta = generated_at - observed_at
    microseconds = (
        Decimal(delta.days) * Decimal("86400") * Decimal("1000000")
        + Decimal(delta.seconds) * Decimal("1000000")
        + Decimal(delta.microseconds)
    )
    return _quantize(microseconds / Decimal("1000000"))


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _derived_report_digest(
    report: ResearchMarketResolutionLiquidityTimeDecayReport,
) -> str:
    payload = _payload_value(report)
    if type(payload) is not dict:
        raise ValueError("report payload must be a JSON object")
    payload.pop("derived_validation_digest", None)
    _reject_unsafe_public_payload(payload)
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _payload_value(value: Any) -> Any:
    if value is None:
        return None
    if is_dataclass(value) and not isinstance(value, type):
        ready: dict[str, Any] = {}
        for field in fields(value):
            ready[field.name] = _payload_value(getattr(value, field.name))
        return ready
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
        ready_mapping: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            ready_mapping[key] = _payload_value(item)
        return ready_mapping
    if isinstance(value, (list, tuple)):
        return [_payload_value(item) for item in value]
    raise ValueError("payload value is not JSON serializable")


def _reject_unsafe_public_payload(value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            _reject_unsafe_public_key(field.name)
            _reject_unsafe_public_payload(getattr(value, field.name))
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            _reject_unsafe_public_key(key)
            _reject_unsafe_public_payload(item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(item)
        return
    if type(value) is str and _has_unsafe_public_fragment(value):
        raise ValueError("unsafe public value")


def _reject_unsafe_public_key(key: str) -> None:
    if _has_unsafe_public_fragment(key):
        raise ValueError("unsafe public field")


def _has_unsafe_public_fragment(value: str) -> bool:
    normalized = value.lower()
    return any(fragment in normalized for fragment in UNSAFE_PUBLIC_FRAGMENTS)
