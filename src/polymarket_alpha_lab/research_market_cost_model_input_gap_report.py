"""Pure report-only cost model input gap aggregation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field, fields, is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import json
import re
from typing import Any


DEFAULT_RESEARCH_MARKET_COST_MODEL_INPUT_GAP_CONFIG_VERSION = (
    "research-market-cost-model-input-gap-report-v0"
)

_QUANT = Decimal("0.000001")
_ZERO = Decimal("0.000000")
_ONE = Decimal("1.000000")
_DIGEST_RE = re.compile(r"^[0-9a-f]{64}$")
_PUBLIC_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_STATUSES = frozenset(("pass", "watch", "block"))
_PHASE_FLAG_FIELDS = frozenset(("paper_only", "report_only", "readonly"))
_COMPONENT_SEQUENCE = (
    "fee",
    "spread",
    "slippage",
    "settlement_friction",
    "quote_depth",
)
_INPUT_REASON_SEQUENCE = (
    "manual_gap_review",
    "component_refresh_needed",
    "all_gap_inputs_present",
)
_ROW_REASON_SEQUENCE = (
    *_INPUT_REASON_SEQUENCE,
    "fee_missing_gap_block",
    "fee_missing_gap_watch",
    "fee_stale_gap_block",
    "fee_stale_gap_watch",
    "spread_missing_gap_block",
    "spread_missing_gap_watch",
    "spread_stale_gap_block",
    "spread_stale_gap_watch",
    "slippage_missing_gap_block",
    "slippage_missing_gap_watch",
    "slippage_stale_gap_block",
    "slippage_stale_gap_watch",
    "settlement_friction_missing_gap_block",
    "settlement_friction_missing_gap_watch",
    "settlement_friction_stale_gap_block",
    "settlement_friction_stale_gap_watch",
    "quote_depth_missing_gap_block",
    "quote_depth_missing_gap_watch",
    "quote_depth_stale_gap_block",
    "quote_depth_stale_gap_watch",
    "aggregate_gap_block",
    "aggregate_gap_watch",
    "cost_model_input_gap_block",
    "cost_model_input_gap_watch",
    "cost_model_input_gap_pass",
)
_COMPONENT_REASON_SEQUENCE = tuple(
    reason
    for component in _COMPONENT_SEQUENCE
    for reason in (
        f"{component}_component_gap_block",
        f"{component}_component_gap_watch",
        f"{component}_component_gap_pass",
    )
)
_REPORT_REASON_SEQUENCE = (
    "no_cost_model_input_gap_observations",
    "cost_model_input_gap_report_block_rows",
    "cost_model_input_gap_report_watch_rows",
    "cost_model_input_gap_report_pass",
)
_UNSAFE_PUBLIC_TERMS = (
    "raw",
    "candidate_id",
    "candidate id",
    "condition_id",
    "condition id",
    "market_id",
    "market id",
    "market_slug",
    "market slug",
    "slug",
    "question",
    "http://",
    "https://",
    "url",
    "source_text",
    "source text",
    "dsn",
    "database",
    "table_name",
    "table name",
    "token",
    "secret",
    "auth",
    "credential",
    "private_key",
    "private key",
    "wallet",
    "order",
    "trade",
    "trading",
    "buy",
    "sell",
    "recommend",
    "sizing",
    "position",
    "live",
)

_ROW_RECORD: type[Any]
_COMPONENT_SUMMARY_RECORD: type[Any]
_DIGEST_RECORD: type[Any]
_REPORT_RECORD: type[Any]

__all__ = (
    "DEFAULT_RESEARCH_MARKET_COST_MODEL_INPUT_GAP_CONFIG_VERSION",
    "ResearchMarketCostModelInputGapConfig",
    "ResearchMarketCostModelInputGapObservation",
    "ResearchMarketCostModelInputGapComponentSummary",
    "ResearchMarketCostModelInputGapRow",
    "ResearchMarketCostModelInputGapDigest",
    "ResearchMarketCostModelInputGapReport",
    "build_research_market_cost_model_input_gap_report",
    "research_market_cost_model_input_gap_report_payload",
    "research_market_cost_model_input_gap_digest_payload",
)


class _FinalPublicDataclass:
    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        for base in cls.__bases__:
            if base is not _FinalPublicDataclass and issubclass(
                base,
                _FinalPublicDataclass,
            ):
                raise TypeError(f"{base.__name__} may not be subclassed")


@dataclass(frozen=True)
class ResearchMarketCostModelInputGapConfig(_FinalPublicDataclass):
    config_version: str = DEFAULT_RESEARCH_MARKET_COST_MODEL_INPUT_GAP_CONFIG_VERSION
    watch_component_gap_score: Decimal = Decimal("0.300000")
    block_component_gap_score: Decimal = Decimal("0.750000")
    watch_aggregate_gap_score: Decimal = Decimal("0.250000")
    block_aggregate_gap_score: Decimal = Decimal("0.600000")
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostModelInputGapConfig, "config")
        object.__setattr__(
            self,
            "config_version",
            _require_public_identifier("config_version", self.config_version),
        )
        for name in (
            "watch_component_gap_score",
            "block_component_gap_score",
            "watch_aggregate_gap_score",
            "block_aggregate_gap_score",
        ):
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        _require_threshold_pair(
            "watch_component_gap_score",
            self.watch_component_gap_score,
            "block_component_gap_score",
            self.block_component_gap_score,
        )
        _require_threshold_pair(
            "watch_aggregate_gap_score",
            self.watch_aggregate_gap_score,
            "block_aggregate_gap_score",
            self.block_aggregate_gap_score,
        )
        _require_hard_flags("config", self)
        _reject_unsafe_public_payload("config", self)


@dataclass(frozen=True)
class ResearchMarketCostModelInputGapObservation(_FinalPublicDataclass):
    cost_model_bucket: str
    observed_at: datetime
    fee_missing_score: Decimal
    fee_stale_score: Decimal
    spread_missing_score: Decimal
    spread_stale_score: Decimal
    slippage_missing_score: Decimal
    slippage_stale_score: Decimal
    settlement_friction_missing_score: Decimal
    settlement_friction_stale_score: Decimal
    quote_depth_missing_score: Decimal
    quote_depth_stale_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostModelInputGapObservation, "observation")
        object.__setattr__(
            self,
            "cost_model_bucket",
            _require_public_identifier("cost_model_bucket", self.cost_model_bucket),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in _COMPONENT_SCORE_FIELDS:
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _INPUT_REASON_SEQUENCE),
        )
        _require_hard_flags("observation", self)
        _reject_unsafe_public_payload("observation", self)


@dataclass(frozen=True)
class ResearchMarketCostModelInputGapComponentSummary(_FinalPublicDataclass):
    component: str
    missing_gap_count: Decimal
    stale_gap_count: Decimal
    average_gap_score: Decimal
    max_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(
            self,
            ResearchMarketCostModelInputGapComponentSummary,
            "component_summary",
        )
        object.__setattr__(self, "component", _require_component(self.component))
        for name in (
            "missing_gap_count",
            "stale_gap_count",
            "average_gap_score",
            "max_gap_score",
        ):
            object.__setattr__(
                self,
                name,
                _require_nonnegative_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _COMPONENT_REASON_SEQUENCE),
        )
        _validate_component_summary(self)
        _require_hard_flags("component_summary", self)
        _reject_unsafe_public_payload("component_summary", self)


@dataclass(frozen=True)
class ResearchMarketCostModelInputGapRow(_FinalPublicDataclass):
    cost_model_bucket: str
    observed_at: datetime
    fee_missing_score: Decimal
    fee_stale_score: Decimal
    fee_gap_score: Decimal
    spread_missing_score: Decimal
    spread_stale_score: Decimal
    spread_gap_score: Decimal
    slippage_missing_score: Decimal
    slippage_stale_score: Decimal
    slippage_gap_score: Decimal
    settlement_friction_missing_score: Decimal
    settlement_friction_stale_score: Decimal
    settlement_friction_gap_score: Decimal
    quote_depth_missing_score: Decimal
    quote_depth_stale_score: Decimal
    quote_depth_gap_score: Decimal
    aggregate_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostModelInputGapRow, "row")
        object.__setattr__(
            self,
            "cost_model_bucket",
            _require_public_identifier("cost_model_bucket", self.cost_model_bucket),
        )
        object.__setattr__(self, "observed_at", _as_utc("observed_at", self.observed_at))
        for name in _ROW_SCORE_FIELDS:
            object.__setattr__(
                self,
                name,
                _require_ratio_decimal(name, getattr(self, name)),
            )
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _ROW_REASON_SEQUENCE),
        )
        _validate_row(self)
        _require_hard_flags("row", self)
        _reject_unsafe_public_payload("row", self)


@dataclass(frozen=True)
class ResearchMarketCostModelInputGapDigest(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_aggregate_gap_score: Decimal
    max_aggregate_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostModelInputGapDigest, "digest")
        _normalize_summary_fields(self)
        _validate_summary_counts(self)
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_SEQUENCE),
        )
        if self.status != _summary_status_from_counts(
            block_count=self.block_count,
            watch_count=self.watch_count,
            input_count=self.input_count,
        ):
            raise ValueError("status must match summary counts")
        if self.reason_codes != _report_reason_codes(
            block_count=self.block_count,
            watch_count=self.watch_count,
            input_count=self.input_count,
        ):
            raise ValueError("reason_codes must match status")
        _require_hard_flags("digest", self)
        _reject_unsafe_public_payload("digest", self)
        _finalize_digest_payload(self)


@dataclass(frozen=True)
class ResearchMarketCostModelInputGapReport(_FinalPublicDataclass):
    generated_at: datetime
    config_version: str
    input_count: Decimal
    pass_count: Decimal
    watch_count: Decimal
    block_count: Decimal
    average_aggregate_gap_score: Decimal
    max_aggregate_gap_score: Decimal
    status: str
    reason_codes: tuple[str, ...]
    component_summaries: tuple[ResearchMarketCostModelInputGapComponentSummary, ...]
    digest: ResearchMarketCostModelInputGapDigest
    rows: tuple[ResearchMarketCostModelInputGapRow, ...]
    derived_validation_digest: str = ""
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True
    payload: dict[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        _require_exact_type(self, ResearchMarketCostModelInputGapReport, "report")
        _normalize_summary_fields(self)
        object.__setattr__(self, "status", _require_status(self.status))
        object.__setattr__(
            self,
            "reason_codes",
            _normalize_reason_codes(self.reason_codes, _REPORT_REASON_SEQUENCE),
        )
        object.__setattr__(
            self,
            "component_summaries",
            _normalize_component_summaries(self.component_summaries),
        )
        object.__setattr__(self, "rows", _normalize_rows(self.rows))
        if type(self.digest) is not ResearchMarketCostModelInputGapDigest:
            raise ValueError("digest must be a ResearchMarketCostModelInputGapDigest")
        _validate_report(self)
        _validate_summary_counts(self)
        _require_hard_flags("report", self)
        _reject_unsafe_public_payload("report", self)
        _finalize_report_payload(self)


_COMPONENT_SCORE_FIELDS = tuple(
    f"{component}_{gap_type}_score"
    for component in _COMPONENT_SEQUENCE
    for gap_type in ("missing", "stale")
)
_ROW_SCORE_FIELDS = tuple(
    field_name
    for component in _COMPONENT_SEQUENCE
    for field_name in (
        f"{component}_missing_score",
        f"{component}_stale_score",
        f"{component}_gap_score",
    )
) + ("aggregate_gap_score",)

_ROW_RECORD = ResearchMarketCostModelInputGapRow
_COMPONENT_SUMMARY_RECORD = ResearchMarketCostModelInputGapComponentSummary
_DIGEST_RECORD = ResearchMarketCostModelInputGapDigest
_REPORT_RECORD = ResearchMarketCostModelInputGapReport


def build_research_market_cost_model_input_gap_report(
    observations: Iterable[object],
    *,
    config: ResearchMarketCostModelInputGapConfig,
    generated_at: datetime,
) -> ResearchMarketCostModelInputGapReport:
    if type(config) is not ResearchMarketCostModelInputGapConfig:
        raise ValueError("config must be a ResearchMarketCostModelInputGapConfig")
    _require_hard_flags("config", config)
    generated_at_utc = _as_utc("generated_at", generated_at)
    items = _normalize_observations(observations)
    for item in items:
        if item.observed_at > generated_at_utc:
            raise ValueError("observed_at must not be after generated_at")
    rows = tuple(sorted((_row_from_observation(item, config) for item in items), key=_row_key))
    component_summaries = _component_summaries(rows, config)
    summary = _summary_values(
        generated_at=generated_at_utc,
        config_version=config.config_version,
        rows=rows,
    )
    digest = _DIGEST_RECORD(**summary)
    return _REPORT_RECORD(
        **summary,
        component_summaries=component_summaries,
        digest=digest,
        rows=rows,
    )


def research_market_cost_model_input_gap_report_payload(
    report: ResearchMarketCostModelInputGapReport | dict[str, Any],
) -> dict[str, Any]:
    if type(report) is ResearchMarketCostModelInputGapReport:
        _require_hard_flags("report", report)
        _validate_payload_digest("report", report.payload)
        return report.payload
    if type(report) is dict:
        _validate_payload_digest("report", report)
        digest_payload = report.get("digest")
        if type(digest_payload) is not dict:
            raise ValueError("digest must be a payload object")
        _validate_payload_digest("digest", digest_payload)
        return report
    raise ValueError("report must be a ResearchMarketCostModelInputGapReport")


def research_market_cost_model_input_gap_digest_payload(
    digest: ResearchMarketCostModelInputGapDigest | dict[str, Any],
) -> dict[str, Any]:
    if type(digest) is ResearchMarketCostModelInputGapDigest:
        _require_hard_flags("digest", digest)
        _validate_payload_digest("digest", digest.payload)
        return digest.payload
    if type(digest) is dict:
        _validate_payload_digest("digest", digest)
        return digest
    raise ValueError("digest must be a ResearchMarketCostModelInputGapDigest")


def _row_from_observation(
    item: ResearchMarketCostModelInputGapObservation,
    config: ResearchMarketCostModelInputGapConfig,
) -> ResearchMarketCostModelInputGapRow:
    fee_gap = _component_gap(item, "fee")
    spread_gap = _component_gap(item, "spread")
    slippage_gap = _component_gap(item, "slippage")
    settlement_gap = _component_gap(item, "settlement_friction")
    quote_depth_gap = _component_gap(item, "quote_depth")
    aggregate_gap = _mean(
        (fee_gap, spread_gap, slippage_gap, settlement_gap, quote_depth_gap),
    )
    status, reason_codes = _row_status_and_reasons(
        item,
        aggregate_gap=aggregate_gap,
        config=config,
    )
    return _ROW_RECORD(
        cost_model_bucket=item.cost_model_bucket,
        observed_at=item.observed_at,
        fee_missing_score=item.fee_missing_score,
        fee_stale_score=item.fee_stale_score,
        fee_gap_score=fee_gap,
        spread_missing_score=item.spread_missing_score,
        spread_stale_score=item.spread_stale_score,
        spread_gap_score=spread_gap,
        slippage_missing_score=item.slippage_missing_score,
        slippage_stale_score=item.slippage_stale_score,
        slippage_gap_score=slippage_gap,
        settlement_friction_missing_score=item.settlement_friction_missing_score,
        settlement_friction_stale_score=item.settlement_friction_stale_score,
        settlement_friction_gap_score=settlement_gap,
        quote_depth_missing_score=item.quote_depth_missing_score,
        quote_depth_stale_score=item.quote_depth_stale_score,
        quote_depth_gap_score=quote_depth_gap,
        aggregate_gap_score=aggregate_gap,
        status=status,
        reason_codes=reason_codes,
    )


def _row_status_and_reasons(
    item: ResearchMarketCostModelInputGapObservation,
    *,
    aggregate_gap: Decimal,
    config: ResearchMarketCostModelInputGapConfig,
) -> tuple[str, tuple[str, ...]]:
    status = "pass"
    reasons: list[str] = list(item.reason_codes)
    for component in _COMPONENT_SEQUENCE:
        missing = getattr(item, f"{component}_missing_score")
        stale = getattr(item, f"{component}_stale_score")
        gap_type = "missing" if missing >= stale else "stale"
        dominant = missing if gap_type == "missing" else stale
        status = _append_threshold_reason(
            status,
            reasons,
            value=dominant,
            watch_value=config.watch_component_gap_score,
            block_value=config.block_component_gap_score,
            watch_reason=f"{component}_{gap_type}_gap_watch",
            block_reason=f"{component}_{gap_type}_gap_block",
        )
    status = _append_threshold_reason(
        status,
        reasons,
        value=aggregate_gap,
        watch_value=config.watch_aggregate_gap_score,
        block_value=config.block_aggregate_gap_score,
        watch_reason="aggregate_gap_watch",
        block_reason="aggregate_gap_block",
    )
    if status == "block":
        reasons.append("cost_model_input_gap_block")
    elif status == "watch":
        reasons.append("cost_model_input_gap_watch")
    else:
        reasons.append("cost_model_input_gap_pass")
    return status, _normalize_reason_codes(tuple(reasons), _ROW_REASON_SEQUENCE)


def _append_threshold_reason(
    status: str,
    reasons: list[str],
    *,
    value: Decimal,
    watch_value: Decimal,
    block_value: Decimal,
    watch_reason: str,
    block_reason: str,
) -> str:
    if value >= block_value:
        reasons.append(block_reason)
        return "block"
    if value >= watch_value:
        reasons.append(watch_reason)
        if status != "block":
            return "watch"
    return status


def _component_summaries(
    rows: tuple[ResearchMarketCostModelInputGapRow, ...],
    config: ResearchMarketCostModelInputGapConfig,
) -> tuple[ResearchMarketCostModelInputGapComponentSummary, ...]:
    if not rows:
        return ()
    return tuple(_component_summary(component, rows, config) for component in _COMPONENT_SEQUENCE)


def _component_summary(
    component: str,
    rows: tuple[ResearchMarketCostModelInputGapRow, ...],
    config: ResearchMarketCostModelInputGapConfig,
) -> ResearchMarketCostModelInputGapComponentSummary:
    gaps = tuple(getattr(row, f"{component}_gap_score") for row in rows)
    missing_scores = tuple(getattr(row, f"{component}_missing_score") for row in rows)
    stale_scores = tuple(getattr(row, f"{component}_stale_score") for row in rows)
    max_gap = _max_decimal(gaps)
    if max_gap >= config.block_component_gap_score:
        status = "block"
        reason_codes = (f"{component}_component_gap_block",)
    elif max_gap >= config.watch_component_gap_score:
        status = "watch"
        reason_codes = (f"{component}_component_gap_watch",)
    else:
        status = "pass"
        reason_codes = (f"{component}_component_gap_pass",)
    return _COMPONENT_SUMMARY_RECORD(
        component=component,
        missing_gap_count=_decimal_count(
            sum(1 for score in missing_scores if score >= config.watch_component_gap_score),
        ),
        stale_gap_count=_decimal_count(
            sum(1 for score in stale_scores if score >= config.watch_component_gap_score),
        ),
        average_gap_score=_mean(gaps),
        max_gap_score=max_gap,
        status=status,
        reason_codes=reason_codes,
    )


def _summary_values(
    *,
    generated_at: datetime,
    config_version: str,
    rows: tuple[ResearchMarketCostModelInputGapRow, ...],
) -> dict[str, Any]:
    block_count = _decimal_count(sum(1 for row in rows if row.status == "block"))
    watch_count = _decimal_count(sum(1 for row in rows if row.status == "watch"))
    input_count = _decimal_count(len(rows))
    status = _summary_status_from_counts(
        block_count=block_count,
        watch_count=watch_count,
        input_count=input_count,
    )
    return {
        "generated_at": generated_at,
        "config_version": config_version,
        "input_count": input_count,
        "pass_count": _decimal_count(sum(1 for row in rows if row.status == "pass")),
        "watch_count": watch_count,
        "block_count": block_count,
        "average_aggregate_gap_score": _mean(
            tuple(row.aggregate_gap_score for row in rows),
        ),
        "max_aggregate_gap_score": _max_decimal(
            tuple(row.aggregate_gap_score for row in rows),
        ),
        "status": status,
        "reason_codes": _report_reason_codes(
            block_count=block_count,
            watch_count=watch_count,
            input_count=input_count,
        ),
    }


def _normalize_summary_fields(
    value: ResearchMarketCostModelInputGapDigest | ResearchMarketCostModelInputGapReport,
) -> None:
    object.__setattr__(value, "generated_at", _as_utc("generated_at", value.generated_at))
    object.__setattr__(
        value,
        "config_version",
        _require_public_identifier("config_version", value.config_version),
    )
    for name in (
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_aggregate_gap_score",
        "max_aggregate_gap_score",
    ):
        object.__setattr__(
            value,
            name,
            _require_nonnegative_decimal(name, getattr(value, name)),
        )


def _validate_summary_counts(
    value: ResearchMarketCostModelInputGapDigest | ResearchMarketCostModelInputGapReport,
) -> None:
    if value.pass_count + value.watch_count + value.block_count != value.input_count:
        raise ValueError("status counts must match input_count")
    if value.max_aggregate_gap_score < value.average_aggregate_gap_score:
        raise ValueError("max_aggregate_gap_score must be at least average")


def _validate_report(report: ResearchMarketCostModelInputGapReport) -> None:
    if report.rows != tuple(sorted(report.rows, key=_row_key)):
        raise ValueError("rows must be sorted by cost model bucket")
    if len({row.cost_model_bucket for row in report.rows}) != len(report.rows):
        raise ValueError("rows must contain unique cost model buckets")
    if report.input_count != _decimal_count(len(report.rows)):
        raise ValueError("input_count must match rows")
    if report.pass_count != _decimal_count(sum(1 for row in report.rows if row.status == "pass")):
        raise ValueError("pass_count must match rows")
    if report.watch_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "watch"),
    ):
        raise ValueError("watch_count must match rows")
    if report.block_count != _decimal_count(
        sum(1 for row in report.rows if row.status == "block"),
    ):
        raise ValueError("block_count must match rows")
    if report.average_aggregate_gap_score != _mean(
        tuple(row.aggregate_gap_score for row in report.rows),
    ):
        raise ValueError("average_aggregate_gap_score must match rows")
    if report.max_aggregate_gap_score != _max_decimal(
        tuple(row.aggregate_gap_score for row in report.rows),
    ):
        raise ValueError("max_aggregate_gap_score must match rows")
    if report.component_summaries:
        if tuple(summary.component for summary in report.component_summaries) != (
            _COMPONENT_SEQUENCE
        ):
            raise ValueError("component_summaries must follow component sequence")
    elif report.rows:
        raise ValueError("component_summaries must be populated when rows exist")
    if report.status != _summary_status_from_counts(
        block_count=report.block_count,
        watch_count=report.watch_count,
        input_count=report.input_count,
    ):
        raise ValueError("status must match rows")
    if report.reason_codes != _report_reason_codes(
        block_count=report.block_count,
        watch_count=report.watch_count,
        input_count=report.input_count,
    ):
        raise ValueError("reason_codes must match rows")
    if not _digest_matches_report(report.digest, report):
        raise ValueError("digest must match report summary")


def _validate_row(row: ResearchMarketCostModelInputGapRow) -> None:
    for component in _COMPONENT_SEQUENCE:
        expected_gap = max(
            getattr(row, f"{component}_missing_score"),
            getattr(row, f"{component}_stale_score"),
        )
        if getattr(row, f"{component}_gap_score") != _quantize(expected_gap):
            raise ValueError(f"{component}_gap_score must match component inputs")
    expected_aggregate = _mean(
        tuple(getattr(row, f"{component}_gap_score") for component in _COMPONENT_SEQUENCE),
    )
    if row.aggregate_gap_score != expected_aggregate:
        raise ValueError("aggregate_gap_score must match component gaps")
    if row.status != _row_status_from_reason_codes(row.reason_codes):
        raise ValueError("status must match reason_codes")


def _validate_component_summary(
    summary: ResearchMarketCostModelInputGapComponentSummary,
) -> None:
    if summary.max_gap_score < summary.average_gap_score:
        raise ValueError("max_gap_score must be at least average_gap_score")
    if summary.status == "block" and (
        f"{summary.component}_component_gap_block" not in summary.reason_codes
    ):
        raise ValueError("block component summaries must include a block reason")
    if summary.status == "watch" and (
        f"{summary.component}_component_gap_watch" not in summary.reason_codes
    ):
        raise ValueError("watch component summaries must include a watch reason")
    if summary.status == "pass" and (
        f"{summary.component}_component_gap_pass" not in summary.reason_codes
    ):
        raise ValueError("pass component summaries must include a pass reason")


def _digest_matches_report(
    digest: ResearchMarketCostModelInputGapDigest,
    report: ResearchMarketCostModelInputGapReport,
) -> bool:
    names = (
        "generated_at",
        "config_version",
        "input_count",
        "pass_count",
        "watch_count",
        "block_count",
        "average_aggregate_gap_score",
        "max_aggregate_gap_score",
        "status",
        "reason_codes",
    )
    return all(getattr(digest, name) == getattr(report, name) for name in names)


def _finalize_digest_payload(digest: ResearchMarketCostModelInputGapDigest) -> None:
    base_payload = _digest_payload_base(digest)
    expected_digest = _payload_digest(base_payload)
    supplied = digest.derived_validation_digest
    if supplied == "":
        object.__setattr__(digest, "derived_validation_digest", expected_digest)
    elif supplied != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = dict(base_payload)
    payload["derived_validation_digest"] = digest.derived_validation_digest
    _reject_unsafe_public_payload("digest.payload", payload)
    object.__setattr__(digest, "payload", payload)


def _finalize_report_payload(report: ResearchMarketCostModelInputGapReport) -> None:
    base_payload = _report_payload_base(report)
    expected_digest = _payload_digest(base_payload)
    supplied = report.derived_validation_digest
    if supplied == "":
        object.__setattr__(report, "derived_validation_digest", expected_digest)
    elif supplied != expected_digest:
        raise ValueError("derived_validation_digest must match report fields")
    payload = dict(base_payload)
    payload["derived_validation_digest"] = report.derived_validation_digest
    _reject_unsafe_public_payload("report.payload", payload)
    object.__setattr__(report, "payload", payload)


def _digest_payload_base(digest: ResearchMarketCostModelInputGapDigest) -> dict[str, Any]:
    return {
        "generated_at": digest.generated_at.isoformat(),
        "config_version": digest.config_version,
        "input_count": _decimal_string(digest.input_count),
        "pass_count": _decimal_string(digest.pass_count),
        "watch_count": _decimal_string(digest.watch_count),
        "block_count": _decimal_string(digest.block_count),
        "average_aggregate_gap_score": _decimal_string(
            digest.average_aggregate_gap_score,
        ),
        "max_aggregate_gap_score": _decimal_string(digest.max_aggregate_gap_score),
        "status": digest.status,
        "reason_codes": list(digest.reason_codes),
        "paper_only": digest.paper_only,
        "report_only": digest.report_only,
        "readonly": digest.readonly,
    }


def _report_payload_base(report: ResearchMarketCostModelInputGapReport) -> dict[str, Any]:
    return {
        "generated_at": report.generated_at.isoformat(),
        "config_version": report.config_version,
        "input_count": _decimal_string(report.input_count),
        "pass_count": _decimal_string(report.pass_count),
        "watch_count": _decimal_string(report.watch_count),
        "block_count": _decimal_string(report.block_count),
        "average_aggregate_gap_score": _decimal_string(
            report.average_aggregate_gap_score,
        ),
        "max_aggregate_gap_score": _decimal_string(report.max_aggregate_gap_score),
        "status": report.status,
        "reason_codes": list(report.reason_codes),
        "component_summaries": [
            _component_summary_payload(summary)
            for summary in report.component_summaries
        ],
        "digest": report.digest.payload,
        "rows": [_row_payload(row) for row in report.rows],
        "paper_only": report.paper_only,
        "report_only": report.report_only,
        "readonly": report.readonly,
    }


def _component_summary_payload(
    summary: ResearchMarketCostModelInputGapComponentSummary,
) -> dict[str, Any]:
    return {
        "component": summary.component,
        "missing_gap_count": _decimal_string(summary.missing_gap_count),
        "stale_gap_count": _decimal_string(summary.stale_gap_count),
        "average_gap_score": _decimal_string(summary.average_gap_score),
        "max_gap_score": _decimal_string(summary.max_gap_score),
        "status": summary.status,
        "reason_codes": list(summary.reason_codes),
        "paper_only": summary.paper_only,
        "report_only": summary.report_only,
        "readonly": summary.readonly,
    }


def _row_payload(row: ResearchMarketCostModelInputGapRow) -> dict[str, Any]:
    return {
        "cost_model_bucket_digest": _public_digest(row.cost_model_bucket),
        "observed_at": row.observed_at.isoformat(),
        "fee_missing_score": _decimal_string(row.fee_missing_score),
        "fee_stale_score": _decimal_string(row.fee_stale_score),
        "fee_gap_score": _decimal_string(row.fee_gap_score),
        "spread_missing_score": _decimal_string(row.spread_missing_score),
        "spread_stale_score": _decimal_string(row.spread_stale_score),
        "spread_gap_score": _decimal_string(row.spread_gap_score),
        "slippage_missing_score": _decimal_string(row.slippage_missing_score),
        "slippage_stale_score": _decimal_string(row.slippage_stale_score),
        "slippage_gap_score": _decimal_string(row.slippage_gap_score),
        "settlement_friction_missing_score": _decimal_string(
            row.settlement_friction_missing_score,
        ),
        "settlement_friction_stale_score": _decimal_string(
            row.settlement_friction_stale_score,
        ),
        "settlement_friction_gap_score": _decimal_string(
            row.settlement_friction_gap_score,
        ),
        "quote_depth_missing_score": _decimal_string(row.quote_depth_missing_score),
        "quote_depth_stale_score": _decimal_string(row.quote_depth_stale_score),
        "quote_depth_gap_score": _decimal_string(row.quote_depth_gap_score),
        "aggregate_gap_score": _decimal_string(row.aggregate_gap_score),
        "status": row.status,
        "reason_codes": list(row.reason_codes),
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _normalize_observations(
    observations: Iterable[object],
) -> tuple[ResearchMarketCostModelInputGapObservation, ...]:
    if isinstance(observations, (str, bytes)) or not isinstance(observations, Iterable):
        raise ValueError("observations must be an iterable")
    items = tuple(observations)
    for item in items:
        if type(item) is not ResearchMarketCostModelInputGapObservation:
            raise ValueError(
                "observations must contain ResearchMarketCostModelInputGapObservation values",
            )
        _require_hard_flags("observation", item)
    if len({item.cost_model_bucket for item in items}) != len(items):
        raise ValueError("observations must contain unique cost model buckets")
    return items


def _normalize_rows(rows: object) -> tuple[ResearchMarketCostModelInputGapRow, ...]:
    if type(rows) not in (list, tuple):
        raise ValueError("rows must be a list or tuple")
    clean = tuple(rows)
    for row in clean:
        if type(row) is not ResearchMarketCostModelInputGapRow:
            raise ValueError("rows must contain ResearchMarketCostModelInputGapRow values")
        _require_hard_flags("row", row)
    return clean


def _normalize_component_summaries(
    summaries: object,
) -> tuple[ResearchMarketCostModelInputGapComponentSummary, ...]:
    if type(summaries) not in (list, tuple):
        raise ValueError("component_summaries must be a list or tuple")
    clean = tuple(summaries)
    for summary in clean:
        if type(summary) is not ResearchMarketCostModelInputGapComponentSummary:
            raise ValueError(
                "component_summaries must contain "
                "ResearchMarketCostModelInputGapComponentSummary values",
            )
        _require_hard_flags("component_summary", summary)
    return clean


def _normalize_reason_codes(
    value: object,
    allowed_sequence: tuple[str, ...],
) -> tuple[str, ...]:
    if type(value) not in (list, tuple):
        raise ValueError("reason_codes must be a list or tuple")
    clean: list[str] = []
    allowed = frozenset(allowed_sequence)
    for item in value:
        if type(item) is not str:
            raise ValueError("reason_codes must contain strings")
        code = _require_public_identifier("reason_codes", item)
        if code not in allowed:
            raise ValueError("reason_codes contains an unknown reason code")
        if code not in clean:
            clean.append(code)
    return tuple(code for code in allowed_sequence if code in clean)


def _row_status_from_reason_codes(reason_codes: tuple[str, ...]) -> str:
    if "cost_model_input_gap_block" in reason_codes:
        return "block"
    if "cost_model_input_gap_watch" in reason_codes:
        return "watch"
    return "pass"


def _summary_status_from_counts(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    input_count: Decimal,
) -> str:
    if input_count == _ZERO or block_count > _ZERO:
        return "block"
    if watch_count > _ZERO:
        return "watch"
    return "pass"


def _report_reason_codes(
    *,
    block_count: Decimal,
    watch_count: Decimal,
    input_count: Decimal,
) -> tuple[str, ...]:
    if input_count == _ZERO:
        return ("no_cost_model_input_gap_observations",)
    reasons: list[str] = []
    if block_count > _ZERO:
        reasons.append("cost_model_input_gap_report_block_rows")
    if watch_count > _ZERO:
        reasons.append("cost_model_input_gap_report_watch_rows")
    if not reasons:
        reasons.append("cost_model_input_gap_report_pass")
    return tuple(reasons)


def _row_key(row: ResearchMarketCostModelInputGapRow) -> str:
    return row.cost_model_bucket


def _component_gap(
    item: ResearchMarketCostModelInputGapObservation,
    component: str,
) -> Decimal:
    return _quantize(
        max(
            getattr(item, f"{component}_missing_score"),
            getattr(item, f"{component}_stale_score"),
        ),
    )


def _mean(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return _quantize(sum(values, _ZERO) / Decimal(len(values)))


def _max_decimal(values: tuple[Decimal, ...]) -> Decimal:
    if not values:
        return _ZERO
    return max(values)


def _decimal_count(value: int) -> Decimal:
    return _quantize(Decimal(value))


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(_QUANT)


def _require_ratio_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO or clean > _ONE:
        raise ValueError(f"{field_name} must be between 0.000000 and 1.000000")
    return clean


def _require_nonnegative_decimal(field_name: str, value: object) -> Decimal:
    clean = _require_decimal(field_name, value)
    if clean < _ZERO:
        raise ValueError(f"{field_name} must be >= 0.000000")
    return clean


def _require_decimal(field_name: str, value: object) -> Decimal:
    if type(value) is not Decimal:
        raise ValueError(f"{field_name} must be exactly Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")
    if value.as_tuple().exponent < -6:
        raise ValueError(f"{field_name} must use six decimal places or fewer")
    return _quantize(value)


def _require_threshold_pair(
    watch_name: str,
    watch_value: Decimal,
    block_name: str,
    block_value: Decimal,
) -> None:
    if watch_value > block_value:
        raise ValueError(f"{watch_name} must not exceed {block_name}")


def _decimal_string(value: Decimal) -> str:
    return format(_quantize(value), "f")


def _as_utc(field_name: str, value: object) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value.astimezone(UTC)


def _require_component(value: object) -> str:
    if type(value) is not str or value not in _COMPONENT_SEQUENCE:
        raise ValueError("component must be a supported public component")
    return value


def _require_public_identifier(field_name: str, value: object) -> str:
    if type(value) is not str:
        raise ValueError(f"{field_name} must be a string")
    if _PUBLIC_IDENTIFIER_RE.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be a canonical public identifier")
    _reject_unsafe_public_payload(field_name, value)
    return value


def _require_status(value: object) -> str:
    if type(value) is not str or value not in _STATUSES:
        raise ValueError("status must be pass, watch, or block")
    return value


def _require_exact_type(value: object, expected_type: type[object], field_name: str) -> None:
    if type(value) is not expected_type:
        raise ValueError(f"{field_name} must be exactly {expected_type.__name__}")


def _require_hard_flags(field_name: str, value: object) -> None:
    if getattr(value, "paper_only", None) is not True:
        raise ValueError("paper_only must be True")
    if getattr(value, "report_only", None) is not True:
        raise ValueError("report_only must be True")
    if getattr(value, "readonly", None) is not True:
        raise ValueError("readonly must be True")


def _reject_unsafe_public_payload(label: str, value: object) -> None:
    if is_dataclass(value) and not isinstance(value, type):
        for item in fields(value):
            _reject_unsafe_public_payload(
                f"{label}.{item.name}",
                getattr(value, item.name),
            )
        return
    if type(value) is str:
        lower_value = value.lower()
        if any(term in lower_value for term in _UNSAFE_PUBLIC_TERMS):
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, Decimal):
        if type(value) is not Decimal:
            raise ValueError("unsafe public payload")
        if not value.is_finite():
            raise ValueError("unsafe public payload")
        return
    if isinstance(value, datetime):
        if type(value) is not datetime:
            raise ValueError("unsafe public payload")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("unsafe public payload")
        return
    if value is None or type(value) is bool:
        return
    if type(value) in (int, float):
        raise ValueError("unsafe public payload")
    if isinstance(value, dict):
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.key", key)
            if key in _PHASE_FLAG_FIELDS and item is not True:
                raise ValueError("unsafe public payload")
            _reject_unsafe_public_payload(f"{label}.{key}", item)
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _reject_unsafe_public_payload(label, item)
        return
    raise ValueError("unsafe public payload")


def _public_digest(value: str) -> str:
    return f"sha256:{sha256(value.encode('utf-8')).hexdigest()}"


def _payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return sha256(encoded.encode("utf-8")).hexdigest()


def _validate_payload_digest(label: str, payload: dict[str, Any]) -> None:
    if type(payload) is not dict:
        raise ValueError(f"{label} payload must be a JSON object")
    _reject_unsafe_public_payload(label, payload)
    supplied = payload.get("derived_validation_digest")
    if type(supplied) is not str or _DIGEST_RE.fullmatch(supplied) is None:
        raise ValueError("derived_validation_digest must be a lowercase sha256 digest")
    base_payload = {
        key: value
        for key, value in payload.items()
        if key != "derived_validation_digest"
    }
    if _payload_digest(base_payload) != supplied:
        raise ValueError("derived_validation_digest must match payload fields")
